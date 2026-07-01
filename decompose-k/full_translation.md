# Decompose-K：从 torch.compile 到手写 Triton Kernel——瘦长 K 矩阵乘法的优化

本文源码：shreyansh26/MLSys-Experiments/decompose-k
Decompose-K 和 custom-op 自动调优的工作流来自 PyTorch Conference 演讲：Elias Ellison & Paul Zhang（Meta）。本文是作者基于此思路的实现、验证和基准测试。

## 瘦长 K 主导的 Matmul 问题

标准矩阵乘法 C[M, N] = A[M, K] @ B[K, N] 的并行性来自将 M × N 输出切块。每个程序负责一个 BLOCK_M × BLOCK_N 的 tile，在 K 维度上流式累积。当 M 和 N 都很大时效果良好——有足够多的独立工作填满所有 SM。

问题场景是 M 和 N 极小、K 极大的瘦长矩阵乘法。例如 M = N = 16, K = 32768，或解码时的 MoE 路由 GEMM 如 [T, 7168] @ [7168, 256]，T 可能小到 1。此时输出只有 16×16 = 256 个元素，仅有一两个 tile。GPU 有 132 个 SM 闲着，看着一两个程序串行走完长度为 32768 的规约。Matmul 是规约受限的，但标准切块在唯一的大维度 K 上几乎没有暴露并行性。

Decompose-K 直击这个问题：如果唯一的大的维度是 K，那就把 K 拆开，在拆开的块上并行化。

## Decompose-K 方案

将 K 分成 S 个独立块，计算 S 个部分 GEMM，再加总：

```
A[M, K] @ B[K, N] → partials[S, M, N] → sum(partials, dim=0)
```

每个部分是一个 K/S 规模的 matmul，S 个部分彼此独立，自然地变成 batch dimension = S 的 batched matmul（bmm）。

PyTorch 实现：
```python
def decomposeK(a, b, k_splits):
    m, k = a.shape
    n = b.shape[1]
    k_parts = k // k_splits
    a_reshaped = a.reshape(m, k_splits, k_parts).permute(1, 0, 2)
    b_reshaped = b.reshape(k_splits, k_parts, n)
    result = torch.bmm(a_reshaped, b_reshaped, out_dtype=torch.float32)
    reduced_result = result.sum(dim=0)
    return reduced_result.to(a.dtype)
```

对于 M=N=16, K=32768, S=64：a_reshaped 变为 [64, 16, 512]，b_reshaped 变为 [64, 512, 16]。bmm 现在有 64 个独立 matmul 而非原来的 1 个，调度器可将它们分布到 SM上。每个部分只累积 512 的规约而不是 32768。

本质上是 split-K，但以 bmm + reduction 的形式在张量层面表达，而非用原子加法写入单个输出 tile。

## 为什么它对 Epilogue 友好

使用原子加法写入输出的 split-K 设计有一个问题：如果要在累积过程中融合点运算（如 ReLU），输出 tile 在所有 split 完成之前不是最终的，因此不能提前应用 ReLU。需要额外的 pass。

Decompose-K 将部分结果保存在独立的 [S, M, N] 缓冲区中，做显式规约。这意味着规约步骤是每个输出元素变为最终值的自然时机，epilogue 可以直接折叠进规约的 store 操作：

```
acc = sum over splits of partials
acc = relu(acc)     # 融合进同一个 kernel
store C[m, n] = acc
```

无需额外的点运算 pass，对内存受限的小输出是真实收益（约 1.2-1.4x）。

## 适用场景

Decompose-K 在以下情况下有优势：
- K 极大且 M/N 较小（如 M=N=16..64, K=8192..32768）
- 对延迟敏感、固定 shape 比通用 GEMM 更重要的场景
- 可以融合 ReLU 等 epilogue
- 当 M 和 N 已足够大（能填满 GPU）、K 较小、K 不能被候选 split 数整除、或额外的 [S,M,N] 缓冲区及规约成本占主导时，不值得使用

## 基线：torch.compile

直接写 decomposeK 并用 Inductor 编译。最优模式为 `max-autotune-no-cudagraphs`（开启模板自动调优但跳过 CUDA graph，避免对小调用造成开销）。

### Inductor 实际生成了什么？

编译 decomposeK 会生成两个操作：
1. 外部 bmm kernel（cuBLAS 批处理），写入 fp32 部分结果缓冲区
2. 一个 Triton 点运算 kernel：合并 sum + cast

如果写 `relu(mm(a, b))` 让 Inductor 决定：小 K（256）时生成单个融合 matmul template（ReLU 融合进 store 后缀）；大 K（32768）时 Inductor 自动选择 Decompose-K 路径（`decompose_k_mm_64_split_5`），生成 bmm + reduction + 独立 ReLU 三个部分。ReLU 以独立点运算 kernel 在规约之后执行——这就是手写 kernel 可以收回的融合机会。

## 手写 Triton Kernel

分两阶段：部分 matmul + 规约/epilogue。

### 阶段 1：部分 Matmul
2D 发射网格：program_id(0) 索引 MxN 输出 tile，program_id(1) 索引 split。每个程序为一个 split 计算一个 BLOCK_M×BLOCK_N 的 tile，只累积其 K//SPLIT_K 的规约片段。累积器为 fp32。无原子操作——每个 (split_id, tile) 对拥有 partials 缓冲区的独立区域。

### 阶段 2：规约 + 融合 Epilogue
每个输出 tile 一个程序，遍历所有 SPLIT_K 的部分结果到 tile 形状的累积器中，如需要则应用 ReLU，然后 store。这正是 Inductor 的 Decompose-K lowering 不做的事。

但有趣的是：这个手写 kernel 实际上并没有比 Inductor 快。

## Custom-op 自动调优：让 Inductor 选择分解方案

Inductor 暴露了 `register_custom_op_autotuning` API，可以传入一个操作的多种分解方案列表，让编译器按 shape 基准测试并选择胜者。目标操作可以是 `torch.ops.aten.mm.default`，从而拦截编译图中每个 `torch.mm` 的 lowering。

候选方案包括普通 mm + 每个合法 split 数对应的 Decompose-K 分解。`dispatch_on` + `split_points` 允许按动态 shape 分范围调优：解码（T=1）和预填充（T 大）可以从同一个编译图获得不同 kernel。

结果：手写 Triton kernel 在所有 shape 上都输了——Inductor 对同样 Decompose-K 数学的 lowering 比手写 kernel 中位数快约 8-13%。原因在于规约器。手写规约器按输出 tile 形状：一个程序拥有一个 BLOCK_M×BLOCK_N tile 的 2D 累积器，串行遍历 split 维度。当输出极小时，一个程序串行读取所有 SPLIT_K 部分结果——规约并行性被绑定到了输出切块上，这是错误的方向。

## 优化的 Triton Kernel

保持两阶段结构但重写规约器并扩展自动调优搜索，四项改动：

### 1. 规约器围绕 split 轴重构
将输出矩阵展平成 1D 元素索引 x = m*N + n，把 split 作为 2D 向量规约的规约轴。每个规约程序拥有 XBLOCK 个展平输出元素，加载它们的所有 RBLOCK(=SPLIT_K) 部分结果，用 `tl.sum` 在 split 轴上规约。这样规约切块与 matmul 切块解耦。

### 2. Flat contiguous 快速路径
对连续的 row-major 张量，地址计算简化为 `partials + r * stride_ps + x`——无需恢复 (m, n) 的除法和取模。

### 3. 匹配微小 tile 的 Warp 数
16x16 输出 tile 只有 256 个 fp32 累积器，4 个 warp 过多。优化配置包含 1-2 warp 的 tile（16x16x64）和 4 warp 的较大 tile（64x32, 64x64）。

### 4. 更多 split 候选
显式尝试 2 的幂次计数（2,4,8,16,32,64,128,256）。

### 优化后：打赢了

向量化规约器将 median 从 0.917x 提升到 1.026x（相对于 custom-op 路径），约 11% 的摆幅，完全来自规约并行化和 ReLU 融合。

## 基准测试设置

- 网格：M=N ∈ {16,32,48,64} × K ∈ {8192,12288,16384,20480,24576,28672,32768}——每个 suite 28 个 shape
- 每个 shape 独立编译（`torch._dynamo.reset()` + `dynamic=False`），确保各点反映 Inductor 对该 shape 的最佳 kernel
- 延迟来自 `triton.testing.do_bench(fn, warmup=10, rep=50, return_mode="median")`
- 两个 suite：epilogue-bf16（BF16 matmul + 融合 ReLU）和 matmul-bf16（纯 BF16 matmul）

## 结果

关键数字（epilogue-bf16 suite，do_bench median, ms）：

| M=N | K | eager mm+relu | compiled mm+relu | custom-op | Decompose-K fused |
|-----|---|---------------|------------------|-----------|-------------------|
| 16 | 8192 | 0.0156 | 0.0120 | 0.0092 | 0.0092 |
| 16 | 32768 | 0.0159 | 0.0147 | 0.0108 | 0.0104 |
| 32 | 16384 | 0.0175 | 0.0145 | 0.0107 | 0.0105 |
| 64 | 32768 | 0.0195 | 0.0165 | 0.0139 | 0.0135 |

融合 Decompose-K 始终是最快列，比 eager 快约 1.5-1.7x，比 compiled mm+relu 快约 1.2-1.4x。仅融合收益（同一 Decompose-K 配置下 ReLU 分开 vs 融合）稳定在 1.19x-1.4x。

## 要点总结

1. Decompose-K 是结构性的修复——当唯一的大维度是 K 时，拆分它将一个长串行规约变成 S 个并行部分 GEMM 加一个规约
2. 它对 epilogue 友好——显式规约的 store 是融合 ReLU 的自然位置，收益约 1.2-1.4x
3. torch.compile 已知道这个技巧——在大 K 时 Inductor 自动选择 Decompose-K，但将 epilogue 作为独立 kernel 发出
4. Custom-op 自动调优是强基线——给 Inductor 一个分解列表就击败了 naive 手写 kernel
5. 击败它需要正确的规约器——围绕 split 轴重构规约、匹配 warp 数与 tile 大小、融合 ReLU
6. 手写 kernel 的收益只有几个百分点——对大多数场景，正确使用的 torch.compile 就足够

原文博客：https://shreyansh26.github.io/post/2026-06-21_decompose-k-triton/
