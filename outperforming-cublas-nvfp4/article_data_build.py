# -*- coding: utf-8 -*-
"""NVFP4 cuBLAS 超越 blog 100% 保留版 build（程序化生成）"""
import json, os, sys

DATA = {
 "title": "在 NVFP4 上跑赢 cuBLAS：一次从零手写 Blackwell GEMM 的极限优化",
 "lead": [
  "两年前，我写过一篇关于在H100上超越cuBLAS性能的博客。那其实是我踏入GPU世界的第一步。没想到它会走红并引发一场小革命。我很高兴看到好几个人为Blackwell做了同样的事：",
  "gau-nernst 写了一篇出色的 tcgen05 博客。",
  "Daniel Vegamyhre 用 MXFP8 达到了 99%。",
  "Paul Chan 用 BF16 击败了 cuBLAS。",
  "Ali 和 Modular 团队也做到了。",
  "Daniel 和 Paul 甚至将 Hilbert 曲线用到了他们的 Blackwell 调度器中。",
  "有一段时间，我觉得没必要再写一篇。但现在我准备好写续篇了——带着新的想法，而且这次我们有比 Hilbert 曲线更好的东西！",
  "以下是我们在 GB300 节点上使用 CUDA 13.1 得到的最终数据：",
  "所有代码均可在 Github 此处获取。",
  "我们将首先为 GB300 从头构建一个 NVFP4 GEMM，一如既往地使用纯 CUDA 和内联 PTX，不依赖任何框架。我们将首先关注经典的 8192 x 8192 x 8192 形状，性能比 cuBLAS 高出 4.7%。我们还会展示其他一些形状的结果。",
  "我们选择 NVFP4，因为它比其他 dtypes 更具挑战性。随着 tensor-core 指令速度提升，流水线的其余部分难以跟上喂给它们的速度。这正是我们展示最极致 GPU 性能技巧的地方。此外，整个内核 100% 由 Claude 生成（后文详述）。",
  "我希望这能激励人们掌握自己的内核，而不是将其视为黑盒。一切不过是又一段代码。"
 ],
 "summary": [
  {
   "key": "核心成果",
   "body": "从零手写 NVFP4 GEMM，在 GB300 上比 cuBLAS 快 4.7%，四个测法全部领先。内核 100% 由 Claude 生成。"
  },
  {
   "key": "方法",
   "body": "纯 CUDA + 内联 PTX，零框架依赖。用七 warp 四角色、K=96/256 MMA、TMEM 累加、L2 双 cache 感知调度。"
  },
  {
   "key": "关键优化",
   "body": "从读 %laneid、扩 K=256 tile、双累加缓冲，到 int8 256-bit 存储、缓存提示、折叠死尾，每一步量化 PFLOP/s。"
  }
 ],
 "sections": [
  {
   "type": "h3",
   "title": "我此前 H100 博客的 Blackwell 续篇；这次我们有比 Hilbert Curves 更好的东西 :)",
   "paras": [
    "两年前，我写过一篇关于在H100上超越cuBLAS性能的博客。那其实是我踏入GPU世界的第一步。没想到它会走红并引发一场小革命。我很高兴看到好几个人为Blackwell做了同样的事：",
    "gau-nernst 写了一篇出色的 tcgen05 博客。",
    "Daniel Vegamyhre 用 MXFP8 达到了 99%。",
    "Paul Chan 用 BF16 击败了 cuBLAS。",
    "Ali 和 Modular 团队也做到了。",
    "Daniel 和 Paul 甚至将 Hilbert 曲线用到了他们的 Blackwell 调度器中。",
    "有一段时间，我觉得没必要再写一篇。但现在我准备好写续篇了——带着新的想法，而且这次我们有比 Hilbert 曲线更好的东西！",
    "感谢阅读 Pranjal 的 Substack！免费订阅以接收新文章并支持我的工作。",
    "以下是我们在 GB300 节点上使用 CUDA 13.1 得到的最终数据：",
    "所有代码均可在 Github 此处获取。",
    "我们将首先为 GB300 从头构建一个 NVFP4 GEMM，一如既往地使用纯 CUDA 和内联 PTX，不依赖任何框架。我们将首先关注经典的 8192 x 8192 x 8192 形状，性能比 cuBLAS 高出 4.7%。我们还会展示其他一些形状的结果。",
    "我们选择 NVFP4，因为它比其他 dtypes 更具挑战性。随着 tensor-core 指令速度提升，流水线的其余部分难以跟上喂给它们的速度。这正是我们展示最极致 GPU 性能技巧的地方。此外，整个内核 100% 由 Claude 生成（后文详述）。",
    "我希望这能激励人们掌握自己的内核，而不是将其视为黑盒。一切不过是又一段代码。"
   ],
   "fig_after": {
    "8": [
     {
      "src": "fig01.png",
      "caption": ""
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "优化阶梯",
   "paras": [],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "什么是 NVFP4？",
   "paras": [
    "NVFP4 即 NVIDIA 的 4 位浮点格式。每个矩阵值以 4 位 E2M1 格式存储：",
    "1 个符号位",
    "2 个指数位",
    "1 个尾数位",
    "可表示的数值大小为 0、0.5、1、1.5、2、3、4 和 6。这个范围本身对于有用的张量来说太小了，因此沿 K 方向每 16 个值共享一个 8 位 UE4M3 缩放因子（将每个值乘以该数即可得到反量化值）。",
    "这使得每个值的有效存储成本为 4.5 位。",
    "从原始 BF16 值中得到这些非常简单：取每个 16 值块中的最大绝对值，除以 6（E2M1 的最大值），即得到缩放因子。然后每个值按该缩放因子进行归一化以适配 FP4。这样可确保我们设置的缩放因子使得每个值至多为 6。",
    "Blackwell 可以直接使用这种格式。tcgen05.mma 指令读取 E2M1 值及其缩放因子，在张量核心内部应用缩放，并累加到 FP32。无需单独的反量化循环。"
   ],
   "fig_after": {
    "3": [
     {
      "src": "fig03.png",
      "caption": ""
     }
    ],
    "0": [
     {
      "src": "fig02.png",
      "caption": ""
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "构建一个可用的 Blackwell 内核",
   "paras": [
    "基本的 Blackwell kernel 与 Hopper 有很大不同。Blackwell 张量核心比 Hopper 张量核心更加“异步”。Hopper 线程需要分配多个寄存器来保存张量核心操作的输出。在操作运行期间，线程可以自由地做其他事情，但由于缺乏空闲寄存器，实际上很难做任何有用的事情。",
    "Blackwell 将这些累加器移入独立的 SM 上内存——张量内存（Tensor Memory，TMEM），从而让 CUDA 线程可以自由地执行其他工作。",
    "我不会在这里重新讲解每条 Blackwell 指令。上面链接的文章已经很好地完成了这项工作。相反，我会先快速开发一个 Blackwell 风格的原型，其中已经具备若干重要细节，同时仍与 cuBLAS 存在较大差距。本节读起来更像是对这些基础技术的一次快速通关，之后我们会更有趣。",
    "我通常这样可视化内核：将其视为数据流，展示每个操作数的驻留位置以及它如何流经 HBM、shared memory、tensor cores、Tensor Memory 和 registers。"
   ],
   "fig_after": {
    "3": [
     {
      "src": "fig04.png",
      "caption": ""
     }
    ]
   }
  },
  {
   "type": "h3",
   "title": "七个 warp，四种角色",
   "paras": [
    "每个 CTA 有 224 个线程，即 7 个 warp。Warp 5 和 6 将数据加载到 shared memory 队列，warp 4 消费它们并发出 MMA，warp 0-3 将 MMA 结果存储到 global memory。",
    "<pre style=\"background-color:#f6f8fa;padding:12px;border-radius:6px;overflow-x:auto;font-family:Consolas,Menlo,monospace;font-size:13px;\"><code>Warps  Role\n-----  --------------------------------------------------------------------------------\n0-3    Read FP32 accumulators from TMEM, convert to FP16, and store\n4      Copy scale factors from SMEM to TMEM and issue every MMA (which outputs to TMEM)\n5      Load A and B into shared memory with TMA\n6      Load A and B scale factors into shared memory with TMA</code></pre>",
    "与 Hopper 一样，每个 warp 使用 mbarrier 与其他 warp 同步，并使用 Shared Memory 或 Tensor Memory（新）交换数据。"
   ],
   "fig_after": {}
  },
  {
   "type": "h3",
   "title": "K=96 的 MMA",
   "paras": [
    "GB300 引入了比 GB200 版本更大的 MMA shape。K = 64 --> 96，增大了 50%，但在最大 shape 下消耗相同的 cycle 数。",
    "<pre style=\"background-color:#f6f8fa;padding:12px;border-radius:6px;overflow-x:auto;font-family:Consolas,Menlo,monospace;font-size:13px;\"><code>M    N    K   Cycles  Performance at 2 GHz\n---  ---  --  ------  --------------------\n256  128  64  64      10.0 PFLOP/s\n256  128  96  78      12.3 PFLOP/s\n256  256  64  128     10.0 PFLOP/s\n256  256  96  128     15.0 PFLOP/s</code></pre>",
    "因此，我们自然需要使用尽可能大的 tile size，即 256 x 256。"
   ],
   "fig_after": {}
  },
  {
   "type": "h3",
   "title": "每个输出 tile 两个 CTA",
   "paras": [
    "Blackwell 有一种特殊的方式执行 2-CTA tensor core 指令，原生支持更大的 tile size（与 Hopper 相比，Hopper 只是对操作数进行 multicast）。这使同一 cluster 中 2 个 SM 上运行的 2 个 CTA 能够协作执行更大的 tensor core 操作。这使我们的 tile size 从 128 x N 增加到 256 x N。",
    "<pre style=\"background-color:#f6f8fa;padding:12px;border-radius:6px;overflow-x:auto;font-family:Consolas,Menlo,monospace;font-size:13px;\"><code>tcgen05.mma.cta_group::2.kind::mxf4nvf4.block_scale.scale_vec::4X\n  [%0], %1, %2, %3, [%5], [%6], acc;</code></pre>",
    "在此模式下，读取 A 和 B 所需的 shared memory 在两个 CTA 之间拆分，最后输出也由两个 CTA 各分一半：",
    "请注意，每个 load 在 2 个 SM 之间均等分片，但 B 矩阵的 scale factors 需要复制（我推测是为了更快的硬件访问）。",
    "其工作方式如下：两个 CTA 运行相同的两个生产者角色，并以 192 值阶段步进 K（打包两个 K=96 MMA，接下来将介绍）：",
    "<pre style=\"background-color:#f6f8fa;padding:12px;border-radius:6px;overflow-x:auto;font-family:Consolas,Menlo,monospace;font-size:13px;\"><code>// Runs in both CTAs.\nint m_cta = tile_m + 128 * cta_rank;\nint n_cta = tile_n + 128 * cta_rank;\n\nif (warp_id == 5 && (threadIdx.x % 32) == 0) {\n    for (int k = 0; k < K; k += 192) {\n        wait(ab_free[ab_slot]);\n        if (cta_rank == 0)\n            expect_tx(ab_ready[ab_slot],\n                      2 * (128 * 96 + 128 * 96)); // 2 CTAs x (A + B)\n        tma_load(a_smem[ab_slot], (m_cta, k)); // packed: 128 x 192\n        tma_load(b_smem[ab_slot], (n_cta, k)); // packed: 128 x 192\n        ab_slot = (ab_slot + 1) % 6;\n    }\n}\n\nif (warp_id == 6 && (threadIdx.x % 32) == 0) {\n    for (int k = 0; k < K; k += 192) {\n        wait(sf_free[sf_slot]);\n        if (cta_rank == 0)\n            expect_tx(sf_ready[sf_slot],\n                      2 * (128 * 12 + 256 * 12)); // 2 CTAs x (SFA + SFB)\n        tma_load_4d(sfa_smem[sf_slot], (m_cta, k)); // logical: 128 x 12 scales\n        tma_load_4d_multicast(\n                    sfb_smem[sf_slot],\n                    (tile_n, k, cta_rank),\n                    both_ctas);                  // logical half: 128 x 12\n        sf_slot = (sf_slot + 1) % 7;\n    }\n}</code></pre>",
    "注意：对于 Scale B，每个 CTA 加载 3,072 字节槽位的一半，并将其多播给对端 CTA。这比让每个 CTA 加载整个槽位快 0.3%。",
    "NVFP4 每个字节打包两个值，因此每个 128 x 192 FP4 tile 是一次\n128 x 96 字节的 TMA 加载。缩放因子按 128 x 12 的组加载，每行 12 个元素。接下来看看为什么 12 是合理的，以及 4d TMA 是怎么回事。"
   ],
   "fig_after": {
    "2": [
     {
      "src": "fig05.png",
      "caption": ""
     }
    ]
   }
  },
  {
   "type": "h3",
   "title": "缩放因子需要特殊处理",
   "paras": [
    "MMA 通过 SMEM 描述符读取 A 和 B，但其缩放因子必须位于 TMEM 中。以下指令将它们复制到那里：",
    "tcgen05.cp.cta_group::2.32x128b.warpx4 [%0], %1;",
    "HBM 缓冲区使用与 cuBLASLt 相同的标准 VEC16 缩放布局；没有内核特定的重新打包。我们向 TMA 将该缓冲区描述为四个维度：外层块、四个 K 缩放值组成的一组、该组内部的缩放值，以及 128 个连续行字节。因此，一个 3 x 4 x 128 字节的盒子会落入 32x128b.warpx4 所期望的逻辑 128 x 12 SMEM tile。关于这种特殊 swizzling 的更多细节，请参考 gau-nernst 的 tcgen05 博客——它不会直接影响我们的算法。",
    "对我们来说更重要的计算是，一个 K=96 MMA 每行消耗六个缩放字节。如果我们一次暂存两个 MMA，且 tcgen05.cp 移动 512 字节的 tile：",
    "A 缩放值：128 行 x 6 x 2 字节 = 1,536 字节 = 3 个 cp tile\nB 缩放值：256 行 x 6 x 2 字节 = 3,072 字节 = 6 个 cp tile",
    "将 2 个 MMA 分组，是为了充分利用 tcgen05.cp 的 512 字节复制范围——这是最优选择。",
    "K=192 的 TMA tile size 直接来自这一运算。",
    "由此产生的三个 SFA 副本和六个 SFB 副本恰好占据 36 个 TMEM 列。",
    "Warp 4 同时消耗一个 scale 槽位和一个 A/B 槽位，并以 192 值阶段推进 K：",
    "<pre style=\"background-color:#f6f8fa;padding:12px;border-radius:6px;overflow-x:auto;font-family:Consolas,Menlo,monospace;font-size:13px;\"><code>if (cta_rank == 0 && warp_id == 4 &&\n    (threadIdx.x % 32) == 0) {\n    wait(acc_free, d_parity);\n\n    for (int k = 0; k < K; k += 192) {\n        wait(sf_ready[sf_slot]);\n        copy_3_sfa_and_6_sfb_tiles_to_tmem(sf_slot);\n        commit(sf_free[sf_slot]);\n\n        wait(ab_ready[ab_slot]);\n        mma_k96(k);\n        mma_k96(k + 96);\n        commit(ab_free[ab_slot]);\n\n        sf_slot = (sf_slot + 1) % 7;\n        ab_slot = (ab_slot + 1) % 6;\n    }\n    commit_multicast(acc_ready, both_ctas);\n}</code></pre>",
    "图中展示的 tile size 选择是合理的——一切都对齐得很好。",
    "几个有趣的要点：",
    "两个 commit 调用都是异步的 tcgen05.commit 操作，携带一个 mbarrier 到达。它们不会立即发生，而是在相应的 cp 或 mma 调用完成后发生。",
    "注意，单个 warp 同时发出 tcgen05.cp 和 tcgen05.mma。根据 PTX 的 tcgen05 内存一致性规则，tcgen05.cp 到 tcgen05.mma 是显式流水线化的。我们不必等待 mma 完成后再发出另一个会覆盖同一 TMEM 空间中 scale 因子的 cp。这是安全的，因为 mma 之后的 commit 会隐式执行 tcgen05.fence::before_thread_sync，将两个 MMA 排序到随后的复制之前。这建立了张量核心所遵循的顺序。"
   ],
   "fig_after": {
    "9": [
     {
      "src": "fig06.png",
      "caption": ""
     }
    ]
   }
  },
  {
   "type": "h3",
   "title": "从 TMEM 读取",
   "paras": [
    "对于 256 x 256 的 tile，每个 CTA 在 TMEM 中接收一个 128 x 256 的 FP32 输出，即 256 列。我们使用一个位于 [0, 256) 列的累加器缓冲区，以及位于 [256, 292) 列的一个可复用 36 列 scale 区域。TMEM 的 512 列中其余 220 列未使用（但之后会派上用场）。",
    "Warp 0-3 负责排空操作。每个 warp 拥有 32 行，而两个 CTA 在将整个 tile 从 TMEM 加载到寄存器后，共同向 acc_free 提供到达信号：",
    "<pre style=\"background-color:#f6f8fa;padding:12px;border-radius:6px;overflow-x:auto;font-family:Consolas,Menlo,monospace;font-size:13px;\"><code>if (warp_id < 4) {\n    wait(acc_ready);\n\n    for (int band = 0; band < 8; ++band) {\n        float acc_regs[32]; // 32 registers per lane\n        tmem_load_x32(tmem_base + 32 * band, acc_regs);\n\n        if (band == 7) {\n            wait_for_tmem_loads();\n            arrive(acc_free);\n        }\n        store_fp16(acc_regs, output_row, 32 * band);\n    }\n}</code></pre>",
    "因此，重要的循环不是一个生产者接一个消费者，而是三个独立的握手同时进行：TMA 填充 SMEM 环形缓冲区，某个 warp 搬运 scales 并启动 MMA，epilogue 只有在将累加器全部从 TMEM 加载出来后才返回累加器。",
    "如果觉得这太难理解，不妨再看一遍这个数据流图："
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig07.png",
      "caption": ""
     }
    ],
    "4": [
     {
      "src": "fig08.png",
      "caption": ""
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "优化 1：直接读取 %laneid",
   "paras": [
    "多个 warp 角色需要 warp 中恰好一个线程。例如，warp 4 看起来像这样：",
    "<pre style=\"background-color:#f6f8fa;padding:12px;border-radius:6px;overflow-x:auto;font-family:Consolas,Menlo,monospace;font-size:13px;\"><code>if (cta_rank == 0 && warp_id == 4 && threadIdx.x % 32 == 0) {\n    run_mma_role();\n}</code></pre>",
    "这样写非常自然。然而，如果改为直接读取 %laneid 特殊寄存器，速度会惊人地提升 77.5%（什么？！）",
    "<pre style=\"background-color:#f6f8fa;padding:12px;border-radius:6px;overflow-x:auto;font-family:Consolas,Menlo,monospace;font-size:13px;\"><code>__device__ __forceinline__ uint32_t lane_id() {\n    uint32_t lane;\n    asm(\"mov.u32 %0, %%laneid;\" : \"=r\"(lane));\n    return lane;\n}\nif (cta_rank == 0 && warp_id == 4 && lane_id() == 0) {\n    run_mma_role();\n}</code></pre>",
    "这两个条件在数学上是等价的，但 ptxas 并不会以相同的方式编译它们。我在全部五个单 lane 位置做了同样的替换。它使 kernel 从 3.271 提升到 5.806 PFLOP/s！",
    "要理解这一差距，了解 uniform 寄存器会有所帮助。普通的\nGPU 寄存器为 warp 中的 32 个 lane 各保存一个独立的值。uniform 寄存器为整个 warp 保存一个值，uniform 数据通路可以用它计算一次，而不用在全部 32 个 lane 中重复相同的工作。",
    "我们的SMEM描述符、TMEM地址、屏障地址和循环状态都是\nwarp-uniform的。理想情况下，ptxas会让它们走这条更便宜的路径。从\nthreadIdx.x（一个每线程值）开始检查，会让编译器丢失部分这种证明（尽管它可以做得更好！）。",
    "然后它会插入R2UR SASS指令，将值从常规寄存器复制到统一寄存器，再加上跟踪哪些通道（lanes）处于活动状态的指令。直接使用%laneid形式能被更好地识别：这个版本少了135条R2UR指令，SASS也短了848行。"
   ],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "优化 2：K=256 + 流水线",
   "paras": [
    "到目前为止，每个A/B TMA tile覆盖128 x 192的形状。我们的下一个目标是将其增加到128 x 256。",
    "192与K=96配合得很好。但如果我们将内部维度设为128字节宽，TMA操作可以更高效。然而这会导致tile不均匀，并且需要非常小心地进行屏障调整：",
    "这个图看起来比上一个复杂一些。但核心流程很简单：等待你需要的资源，用完后立即释放。",
    "MMA等待A/B和缩放因子A/B，一旦MMA完成，就可以释放相应的缓冲区。但由于缓冲区大小不同，顺序必须手动安排。由于我们有固定的K=768，我们可以手动展开一切，并尽可能快地释放/排队请求，而没有任何开销。",
    "这张图是对屏障细节的最佳解释——如果你感兴趣，我建议仔细看看。",
    "例如，当MMA5完成时，我们可以立即释放AB1。然而，我们选择先发出SF3。事实证明，先发出cp是很重要的——它打破了cp和mma的串行化。一个自然而然的问题是：为什么不用另一个warp来做cp并添加更多的mbarriers？在很多情况下，我们没有额外的warp（由于CLC），而且在FP4机制下mbarriers也有一定的开销。",
    "TMA 与 MMA 的分区边界不再一致，因此 MMA2 需要同时读取 AB0 和 AB1 的部分内容。",
    "上面一行是 TMA 写入操作数的方式；下面一行是张量核心读取完全相同字节的方式。两个橙色 MMA 直接跨越到下一个 128 字节窗口。",
    "PTX 专门为这种情况提供了一种描述符模式：针对 48 字节 K 维度的绝对地址模式。这可以在 tcgen05.mma 调用的指令描述符中指定。",
    "<pre style=\"background-color:#f6f8fa;padding:12px;border-radius:6px;overflow-x:auto;font-family:Consolas,Menlo,monospace;font-size:13px;\"><code>desc =\n      encode(AB0 + 96)       // first 32 B begin in AB0\n    | encode(AB1) << 16      // final 16 B comes from AB1\n    | FIXED_K96_SW128_BITS;</code></pre>",
    "这使性能从 5.806 PFLOP/s 提升到 6.676 PFLOP/s，提升了 15.0%！"
   ],
   "fig_after": {
    "1": [
     {
      "src": "fig09.png",
      "caption": ""
     }
    ],
    "6": [
     {
      "src": "fig10.png",
      "caption": ""
     }
    ]
   }
  },
  {
   "type": "h3",
   "title": "共享内存核算",
   "paras": [
    "<pre style=\"background-color:#f6f8fa;padding:12px;border-radius:6px;overflow-x:auto;font-family:Consolas,Menlo,monospace;font-size:13px;\"><code>1,024 B          barrier header + padding\n6 x 16,384 B       A ring\n6 x 16,384 B       B ring\n7 x  1,536 B       A scale-factor ring\n      512 B        alignment padding\n7 x  3,072 B       B scale-factor ring\n----------------\n230,400 B          total per SM</code></pre>",
    "每个 CTA 使用 232,448 可用字节中的 230,400 字节：99.1%。",
    "六个 A/B 阶段和七个缩放阶段使 TMA 保持领先于 MMA warp。\n减少一个 A/B 阶段会损失 12% 性能；减少一个缩放阶段会损失 1.2% 性能。"
   ],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "优化 3：重叠两个累加器缓冲区",
   "paras": [
    "我们的加载和 MMA 现在已经很好地并行化了。但 MMA warp 仍然需要等待 epilogue 清空其 TMEM 输出缓冲区，然后才能开始处理下一个 tile。理想情况下，我们希望存储 2 个这样的缓冲区，这样张量核心线程就无需等待 consumer warp 读取并释放它，而是立即开始下一个 MMA 循环。",
    "但如果这样做，就没有剩余空间来存放缩放因子（它们也需要放在\nTMEM 中）：",
    "2×256 个累加器列 + 36 个缩放列 = 548 > 512",
    "解决方案是将两个输出 tile 重叠 36 列（548 - 512）。因此\nMMA 只需要等待消费者排空重叠边缘\n而不是旧缓冲区的全部 256 列。我们延迟同步\n而不是完全移除它。",
    "Warp 0-3 处理此排空（每行一个线程）。",
    "<pre style=\"background-color:#f6f8fa;padding:12px;border-radius:6px;overflow-x:auto;font-family:Consolas,Menlo,monospace;font-size:13px;\"><code>if (warp_id < 4) {\n    wait(acc_ready);\n\n    for (int i = 0; i < 8; ++i) {\n        int band = (d_parity == 0) ? 7 - i : i;  // overlap first\n        float out[32];\n        tmem_load_x32(tmem_base + 32 * band, out);\n\n        if (i == 1) {\n            wait_for_tmem_loads();\n            arrive(acc_free);\n        }\n        store_fp16(out, output_row, 32 * band);\n    }\n}</code></pre>",
    "从 TMEM 到寄存器的加载只有 32 列宽。需要时我们可以加载更多，但这已足以达到最佳性能。我们只使用 32 个寄存器，这相当廉价，且不需要 Hopper 所需的定制寄存器分配。",
    "有一件事没成功：我们只需要在读取 36 列后发出 acc_free 信号，但我们是在 64 列之后才发出。我尝试将加载完全展开为多种尺寸，并在 36 列时提前释放，但速度慢了 0.5%。所以我保留了更简单的版本。",
    "最后再看一次完整流程会很有帮助。输出 tile 仍是 256×256，但 A/B 阶段填满其完整的 128 字节 SMEM 窗口，TMEM 现在同时承载两个输出 tile：",
    "这将内核从 6.676 提升到 6.822 PFLOP/s，提升了 2.2%。"
   ],
   "fig_after": {
    "3": [
     {
      "src": "fig11.png",
      "caption": ""
     }
    ],
    "8": [
     {
      "src": "fig12.png",
      "caption": ""
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "优化 4：int8！",
   "paras": [
    "至此，我们已经从优化进入了微优化阶段。",
    "从 Blackwell 开始，CUDA 支持 256 位加载/存储——基本上 int4 现在有了更强大的变体：int8。它实际上叫做 longlong4_32a。我更倾向于直接使用 PTX 指令：",
    "<pre style=\"background-color:#f6f8fa;padding:12px;border-radius:6px;overflow-x:auto;font-family:Consolas,Menlo,monospace;font-size:13px;\"><code>\"st.global.v8.b32 [%0], \"\n\"{%1, %2, %3, %4, %5, %6, %7, %8};\"</code></pre>",
    "这将内核从 6.822 提升到 7.331 PFLOP/s，提升了 7.5%——而且我们已经达到 cuBLAS 的 100.3%！"
   ],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "优化 5：缓存提示",
   "paras": [
    "存储宽度只是指令的一半。相同的存储还携带\n输出缓存策略：",
    "<pre style=\"background-color:#f6f8fa;padding:12px;border-radius:6px;overflow-x:auto;font-family:Consolas,Menlo,monospace;font-size:13px;\"><code>st.global.L1::no_allocate.L2::evict_first.v8.b32 [%0], \n{%1, %2, %3, %4, %5, %6, %7, %8};</code></pre>",
    "输出只写入一次，且此内核不会再次读取。\nL1::no_allocate 阻止这些存储分配 L1 缓存行，\n否则它们会与输入流水线竞争。数据仍然经过\nL2，因此 L2::evict_first 使这些缓存行成为首个被驱逐的候选，\n为可复用输入留出更多空间。",
    "这让我们从 7.331 提升到 7.418 PFLOP/s，提升了 1.2%。"
   ],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "优化 6：更好的编译器提示",
   "paras": [
    "- __global__ __cluster_dims__(2, 1, 1) __launch_bounds__(224, 1) kernel(...) {}",
    "这就是我们启动内核的方式。Cluster dims 告诉编译器集群大小，launch bounds 告诉它内核最多使用 224 个线程。不过，现在出现了一个新的性能提示：",
    "+ __global__ __block_size__((224, 1, 1)) __cluster_dims__(2, 1, 1)\n+   __launch_bounds__(224, 1) kernel(...) {}",
    "`__block_size__(224)` 表示恰好 224 个线程。这在 PTX 指南中被称为 reqntid 性能指令。",
    "当 ptxas 无法证明完整的 warp 能到达每个集合点时，它会插入收敛保护。不过，新的性能指令解决了这个问题，减少了 BSSY/BSYNC SASS 指令对，并将寄存器占用从 62 个降到 52 个！",
    "在重建链中，这只是 0.3% 的吞吐提升，从 7.418 到\n7.441 PFLOP/s，但生成代码的清理效果是真实的。"
   ],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "优化 7：跳过无效尾部",
   "paras": [
    "主循环自然地每 K=768 重复一次：三个 K=256 的 A/B 阶段、四个\nK=192 scale 阶段和八个 K=96 的 MMA 全部对齐。K=8192 在十个完整组后留下一个\n512 元素的尾部。基线仍然运行一个完整的\n尾部组，因此其最后八个 MMA 如下所示：",
    "MMA 0  1  2  3  4       5             6  7\n    96 96 96 96 96   32 real + 64 zero   all zero",
    "这不是主机端的额外填充。TMA 的越界填充提供了\n零，但张量核仍然会花时间进行乘法运算。",
    "为了解决这个问题，我保持快速 K=768 循环不变，并添加了一个显式的尾部组：",
    "<pre style=\"background-color:#f6f8fa;padding:12px;border-radius:6px;overflow-x:auto;font-family:Consolas,Menlo,monospace;font-size:13px;\"><code>int full_groups = K / 768;\nint remainder = K % 768;\n\nrun_k768_groups(full_groups);\nif (remainder != 0) {\n    int tail_mmas = ceil_div(remainder, 96);\n    run_tail_group(tail_mmas);\n}</code></pre>",
    "其他 warp 跳过相同的环形条目和屏障；否则在这里很容易造成死锁。",
    "K=8192内核现在计算K=8256而非K=8448。这将性能从7.441 PFLOP/s提升到7.493 PFLOP/s，提升了0.7%。"
   ],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "优化 8：使用 K64 折叠尾部",
   "paras": [
    "精确输入不再填充到K=768，但其最后的张量核心指令仍然是K=96。对于K=8192，我们可以通过混合K96和K64指令来实现精确：",
    "<pre style=\"background-color:#f6f8fa;padding:12px;border-radius:6px;overflow-x:auto;font-family:Consolas,Menlo,monospace;font-size:13px;\"><code>Full-group tail:    11 x 768                         = 8448\nK96-only tail:     10 x 768 + 6 x 96                 = 8256\nfolded K64 tail:   10 x 768 + 4 x 96 + 2 x 64        = 8192</code></pre>",
    "这种特化将发布审计从7.493提升到7.564 PFLOP/s，\n又提升了0.9%。",
    "此时，我们直接针对8192 x 8192 x 8192形状手写优化。现在，让我们转向针对GPU手写优化。"
   ],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "硬件感知调度",
   "paras": [
    "我们的基线调度器以简单的行主序遍历输出网格。这对其中一个矩阵获得非常好的L2缓存命中，但对另一个矩阵没有。在我之前的H100工作日志中，我们将邻近的tile分组为pockets，以改善两个矩阵的L2重用：",
    "相同颜色的tile在所有可用SM上同时运行。这意味着它们可以享受读取所需A/B矩阵相同部分的缓存好处。",
    "让我们看看这个想法表现如何：",
    "<pre style=\"background-color:#f6f8fa;padding:12px;border-radius:6px;overflow-x:auto;font-family:Consolas,Menlo,monospace;font-size:13px;\"><code>Tile order   PFLOP/s\n-----------  -------\nRow major    7.570\n8x8 pockets  7.508</code></pre>",
    "我们的理论是合理的，但不太清楚为什么这会表现不佳。为了解决这个问题，我们首先需要了解有关L2缓存的一些隐藏硬件细节。我们将建立一个理论，并用它让8x8 pockets在实践中发挥作用。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig13.png",
      "caption": ""
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "L2实际上是两个缓存",
   "paras": [
    "GB300 是同一个 package 中的两个 die。其 152 个 SM 分成两组，每组分别靠近 128 MB L2 的大约一半。",
    "这里 “side” 有两种不同的含义：",
    "每个物理地址都有一个由 address hash 选择的 home side。",
    "每个 SM 都有一个由包含该 SM 的 die 决定的 near side。",
    "这些标签无需匹配。如果 side 0 上的 SM 请求一个 home side 为 side 1 的 line，cold read 会跨越 die-to-die 链路。",
    "<pre style=\"background-color:#f6f8fa;padding:12px;border-radius:6px;overflow-x:auto;font-family:Consolas,Menlo,monospace;font-size:13px;\"><code>Requester relative to the line's home side  atomicAdd Latency\n------------------------------------------  -----------------\nNear                                        148 ns\nFar                                         344 ns</code></pre>",
    "为了暴露 hop，我使用了一条依赖的 atomicAdd 链：每个返回值\n馈送到下一个地址，不留下任何 memory-level parallelism 来隐藏\n延迟。一次远程 round trip 慢 ~2.3x。",
    "然而，这并不会直接让 GEMM 更快，因为我们的 TMA queue 让许多请求保持 in flight，并且很好地隐藏了 hop。更有趣的是，这如何直接影响有效 L2 cache 大小。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig14.png",
      "caption": ""
     }
    ]
   }
  },
  {
   "type": "h3",
   "title": "L2缓存如何划分",
   "paras": [
    "分区 L2 cache 的想法并不广为人知，但互联网上有足够多的碎片可以把它拼凑起来。NVIDIA 首先在 A100 白皮书中描述了它，\nCitadel 对其进行了 microbenchmark，我在上次博客中简要提到过，而 Aroun 实际上在 QuickRunCUDA 中为 Blackwell 做了地址计算——我已将其移植。",
    "地址映射如下：",
    "side = parity(physical_address & 0x1EF000) ^ slab_phase;",
    "每4KB内存段将完全落在side 0或side 1上。每个对齐的8KB跨度也包含每个side的一个段。该映射在2MB slab内是确定性的，但不同的2MB slab可能具有互补映射（即近侧和远侧翻转）。",
    "对于GEMM，我们不需要深入探究具体哪个映射到哪里，只需将SM分成两组，以便它们可以独占使用自己“专属”的L2缓存空间。这种分组可以通过检查同一地址上的内存延迟来找到。"
   ],
   "fig_after": {
    "2": [
     {
      "src": "fig15.png",
      "caption": ""
     }
    ]
   }
  },
  {
   "type": "h3",
   "title": "并非所有GPU生而平等",
   "paras": [
    "首先，一个重要细节：对于152个SM，你可能期望每个GPU在L2侧上按76:76分割。有些确实如此，但分割比例并不固定。以下是我见过的比例：",
    "<pre style=\"background-color:#f6f8fa;padding:12px;border-radius:6px;overflow-x:auto;font-family:Consolas,Menlo,monospace;font-size:13px;\"><code>SMs on side 0 / side 1  Two-CTA clusters\n----------------------  ----------------\n76 / 76                 38 / 38\n72 / 80                 36 / 40\n74 / 78                 37 / 39</code></pre>",
    "集群中的2个SM始终落在同一侧，但并非平均分割。所以每个GPU都略有不同，甚至可能在其中看到不同的“有效”L2缓存大小。功耗问题并不是GPU性能差异的唯一原因！"
   ],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "优化9：8x8，但具备L2感知",
   "paras": [
    "失败的8x8实验准确告诉我们缺少什么。局部排序可以获得更大的L2缓存命中，但如果没有协调，它们可能只是相互颠簸。有两个正交因素：",
    "所有权决定重用发生的位置。一个SM侧获得每次重复。",
    "对 A tile 的读取。",
    "顺序决定何时发生复用。在每一侧内，8x8 pockets 使",
    "下一次使用保持在附近。",
    "对于一个输出 tile，",
    "C[m,n] = sum_k A[m,k] * B[n,k]",
    "固定 m 跨 N 复用 A[m,:] 和 SFA。因此我将每个\n输出行 m 分配给一个请求方侧。B 和 SFB 保持共享，因为每个 N\ntile 被两侧的 M 行所需。",
    "这并不会自动将 A 放入一个物理 L2 半区。每个 A row 的 home address 仍然大致 50/50，因此一些 first touch 会跨越链路。改变的是谁回来：只有该 row 的 owner side 的 clusters 会重新读取它。一个冷 line 可能是远程的，但其后续的 N 复用保持在单个 requester 群体内，而不是在两个半区中建立有效的驻留。",
    "当规模为 8192 的立方时，输出网格是 32 x 32 tiles。在 CPU 侧，我们预先计算每个 cluster 的循环次数，将整个 M 行分配给两个 side pools，然后以 8x8 pockets 遍历每个 pool。我们将这个调度存储在 route table 中，每个 SM 可以查询它来知道要计算哪个 tile。该表只有几 KB，每个 256x 256 tile 对应一个条目。"
   ],
   "fig_after": {}
  },
  {
   "type": "h3",
   "title": "收益",
   "paras": [
    "<pre style=\"background-color:#f6f8fa;padding:12px;border-radius:6px;overflow-x:auto;font-family:Consolas,Menlo,monospace;font-size:13px;\"><code>Strategy                    PFLOP/s\n--------------------------  -------\nRow-major                   7.570\n8x8 pockets / Hilbert       7.508\n8x8 pockets + L2 ownership  7.646</code></pre>"
   ],
   "fig_after": {}
  },
  {
   "type": "h3",
   "title": "每种形状都有对应方案",
   "paras": [
    "每种形状最适合的调度方案略有不同。",
    "这并不意味着我们在每种形状上都比 cuBLAS 更快。（事实上，对于几种形状，我的代码并未超越它。）但这凸显了为每种形状“编译”你的 kernel 的可能性。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig16.png",
      "caption": ""
     }
    ]
   }
  },
  {
   "type": "h3",
   "title": "最后一个微优化",
   "paras": [
    "`redux.sync` 指令可以稍微绕一下，用它提示编译器：调度信息也可以存储在统一寄存器中。",
    "<pre style=\"background-color:#f6f8fa;padding:12px;border-radius:6px;overflow-x:auto;font-family:Consolas,Menlo,monospace;font-size:13px;\"><code>uint32_t tile = route_table[table_offset + t];\nuint32_t uniform_tile;\nasm(\"redux.sync.min.u32 %0, %1, 0xffffffff;\"\n    : \"=r\"(uniform_tile) : \"r\"(tile));</code></pre>",
    "路由解码和地址运算可以保持在统一路径上，这种方式始终更优。这对性能的影响可忽略不计，但能保持 SASS 的整洁。我添加此操作仅因为它极难被发现，希望 PTX 能内置更好的编译器提示。"
   ],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "基准测试方法",
   "paras": [
    "for (...) kernel(A, B, C);",
    "轮换输入。每次启动使用不同的 A 和 B 副本，因此 kernel 无法在 L2 中看到自己之前的输入。",
    "多轮。我们的 kernel 与 cuBLASLt 交替进行五轮，并轮换每次先运行的一方。每轮中连续启动 25 个 kernel，输入轮换，取它们的均值。",
    "冷却 GPU。每个定时 arm 有至少八秒的冷却时间。目标是让 GPU 在下一轮之前达到冷却状态。如果未达到（空闲 GPU 时钟尚未恢复到初始状态），我们继续休眠并轮询，直到达到。",
    "内核基准测试没有唯一正确的方法。功耗受限的内核，数值总会有些波动。只需找到一种方法，通过降低每次测量的方差，让你对增量改进有信心。这里我将展示 4 种对我们的内核进行基准测试的方法，每种方法都展示出对 cuBLAS 的不同优势：",
    "<pre style=\"background-color:#f6f8fa;padding:12px;border-radius:6px;overflow-x:auto;font-family:Consolas,Menlo,monospace;font-size:13px;\"><code>Method                       Ours (PFLOP/s)  cuBLASLt (PFLOP/s)  Ratio\n---------------------------  --------------  ------------------  -------\nCurrent protocol             7.653           7.307               1.0473x\nTriton-style with L2 clears  7.179           6.711               1.0698x\nClock locked to 1305 MHz     6.734           6.245               1.0783x\nSustained 60-second blocks   6.424           6.181               1.0392x</code></pre>",
    "当前这一行是全文通篇使用的协议。持续测试给出的优势最小，而锁定时钟则暴露出最大的每周期差异。我将当前协议用于标题数字，因为我觉得它更能代表真实工作负载。"
   ],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "结论",
   "paras": [
    "我们从零编写了一个 NVFP4 矩阵乘法内核，比 cuBLAS 快 4.7% —— 这是我所知的最佳基线。也许最有趣的优化是最后一个，因为它利用 Nvidia GPU 中 L2 缓存的内部细节来开发更快的调度算法。\nAMD GPU 也有这个特性 —— 但他们对此非常公开，并且经常在设计时考虑到这一点。",
    "尽管我很想写更多文章，但沉迷于算法的时代已经结束。未来，我将更多分享如何最好地使用 AI agents（智能体）来优化 GPU 性能。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig17.png",
      "caption": ""
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "资源",
   "paras": [
    "Claude Code",
    "PTX 指南",
    "我的 H100 矩阵乘法工作日志",
    "gau-nernst 的 tcgen05 笔记",
    "ademeure 的 QuickRunCUDA 侧感知实验",
    "Daniel 的 MXFP8 博客",
    "Paul Chan 在 BF16 上超越 cuBLAS",
    "Ali 和 Modular 团队超越 cuBLAS",
    "感谢阅读 Pranjal 的 Substack！免费订阅以接收新文章并支持我的工作。"
   ],
   "fig_after": {}
  }
 ],
 "conclusion": [
  "在 Blackwell 上打败闭源 cuBLAS，靠的不是玄学，而是把每一处硬件细节量化成 PFLOP/s 的一步步优化。作者从读 %laneid 直接提速 77.5%，到意识到 L2 其实是两块分区 cache——这提醒我们，性能工程的边界往往藏在规格书一行字（或没写）的地方。",
  "整篇内核由 Claude 生成这个事实本身，也是一个信号：编写底层计算内核的范式正在改变，人与 AI 协作写 kernel 的时代已经到来。"
 ],
 "reference_url": "https://cudaforfun.substack.com/p/outperforming-cublas-on-nvfp4"
}

with open("article_data.json", "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=1)
print(f"section={len(DATA['sections'])} 段={sum(len(s['paras']) for s in DATA['sections'])} 结论={len(DATA['conclusion'])}")
