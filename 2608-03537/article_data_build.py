#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, os, sys

_article_dir = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.getcwd())

DATA = {
    "title": "ComFuse：把 GEMM 和内存密集子图揉进同一个内核，最高 1.24x 超 TorchInductor",
    "summary": [
        {"key": "核心洞察", "body": "下游内存密集操作能和 GEMM 并发执行、被藏到计算背后——但现有编译器把计算/内存算子分开优化，融合边界僵化"},
        {"key": "ComFuse 方案", "body": "Stage-Stream 执行模型流水协调 MatMul 与 reduction；空间数据共享跨 CTA 交换中间值；再支持背靠背 GEMM（B2BGEMM）融合"},
        {"key": "结果", "body": "post-norm 等负载全面优于 TorchInductor，最高 1.24x，三种 pattern 平均 1.07-1.09x，融合模式更灵活且自动降级免手工内核"},
    ],
    "lead": [
        "现代深度学习负载（推荐模型、大模型）的计算图越来越复杂，同时包含**计算密集算子**（GEMM）与**内存密集子图**（elementwise、reduction）。但主流 DL 编译器通常**把这两类分开优化**，形成僵硬的融合边界，限制跨算子优化与片上数据复用。",
        "ComFuse 抓住一个机会：**下游内存密集操作可以和计算密集算子并发执行，被完全藏到计算背后**。它把这个机会自动化，生成融合内核处理「计算密集算子 + 依赖丰富、内存密集的 elementwise-reduction 子图」，还支持背靠背 GEMM（B2BGEMM）融合——在多种负载上持续优于 TorchInductor，最高 1.24x。",
    ],
    "sections": [
        {
            "type": "h2",
            "title": "问题：计算与内存算子被分裂优化",
            "paras": [
                "传统编译器面向 GEMM 用 Tensor Core 深度优化，面向 elementwise/reduction 则走另一套图优化与内核生成——**两类算子在编译层被割裂**，每个 kernel 都让中间值进出一次全局内存，丢失跨算子重用机会。",
                "现代 GPU（如 Hopper/Blackwell）支持**跨 CTA 的空间数据共享**：中间值能在片上跨 CTA 边界交换，不需要落回全局内存。这为「计算-内存联合融合」打开了新可能，尤其是下游 elementwise/reduction 要消费跨多个 tile 的 MatMul 输出时。",
                "自动利用这种并发与共享，会引出新的编译难题：怎么切分、怎么调度、怎么处理跨 tile 的 reduction 同步边界——这是 ComFuse 要解决的。",
            ],
            "fig_after": {
                "0": [{"src": "fig00.png", "caption": "Figure 1：跨数据边界的计算密集与内存密集算子联合融合。"}],
                "1": [{"src": "fig01.png", "caption": "Figure 2：MatMul + RMSNorm 子图结构中的数据流。"}]
            }
        },
        {
            "type": "h2",
            "title": "核心：Stage-Stream 执行模型",
            "paras": [
                "ComFuse 的骨干是一个 **Stage-Stream 执行模型**：把 MatMul 算作一个阶段（stage），把下游的内存密集子图（elementwise + reduction）算作另一个阶段，用**流水调度（pipeline schedule）协调 reduction 执行与 MatMul**。",
                "关键点在于**图内计算（Intra-DAG）**与**图间链接（Inter-DAG chaining）**的分工：每个阶段内部按 DAG 调度，阶段之间通过可复用的片上缓冲衔接，从而让内存密集阶段的执行被上一阶段的计算**遮住（hidden）**。",
                "针对跨 tile 的 Reduction 同步，ComFuse 采用 **三级 reduction 方案**：由于 epilogue 的 reduction 只沿一个逻辑维度聚合，同步边界被限制在 tile 的一个局部子集，而不是整张张量——这让并发成为可能，而不需要等全局同步。",
            ],
            "fig_after": {
                "1": [{"src": "fig02.png", "caption": "Figure 3：Stage-Stream 执行模型的实例：MatMul + LayerNorm。"}],
                "2": [{"src": "fig03.png", "caption": "Figure 4：Stage-Stream 执行模型中的三级 reduction 方案。"}]
            }
        },
        {
            "type": "h2",
            "title": "扩展：背靠背 GEMM（B2BGEMM）融合",
            "paras": [
                "ComFuse 进一步支持 **B2BGEMM（back-to-back GEMM）** 融合，把两个连续 GEMM 的 compute-memory 交互也纳入一致性调度，扩展了它可以覆盖的复杂模式。",
                "实现上分**数据流调度（Dataflow Scheduling）**、**生产者 warp 组（Producer Warp Group）**和**消费者 warp 组（Consumer Warp Group）**：生产者把第一个 GEMM 的 tile 交给消费者时，内存密集/第二 GEMM 重叠进行，避免中间落回全局内存。",
                "这使 ComFuse 不止处理「MatMul + epilogue」，还能处理更一般的**计算-内存交替模式**，适用面更广。",
            ],
            "fig_after": {
                "1": [{"src": "fig04.png", "caption": "Figure 5：B2BGEMM 并行任务调度。"}]
            }
        },
        {
            "type": "h2",
            "title": "编译栈：从高层子程序到融合内核",
            "paras": [
                "ComFuse 是一套**自动化编译系统**：把高层 tensor 子程序自动降级（lower）为优化过的融合内核，减少手工内核工程。",
                "编译栈分几步：**代码翻译（Code Translate）** → **前端映射（Frontend Mapping）** → **reduction 子图切分（Reduction Subgraph Splitting）** → **后端映射（Backend Mapping）**。",
                "前端负责识别可融合的计算-内存结构并建模数据流；子图切分把复杂的 reduction 依赖拆成适合流水并发的形式；后端把调度方案映射到具体 CUDA/CUTLASS 结构上。用户给出高层算子即可，无需手写融合内核。",
            ],
            "fig_after": {
                "1": [{"src": "fig05.png", "caption": "Figure 6：ComFuse 编译栈。"}]
            }
        },
        {
            "type": "h2",
            "title": "实验：全面跑赢 TorchInductor",
            "paras": [
                "在 post-norm 及多种复杂计算场景下，**ComFuse 生成的融合内核全面优于 TorchInductor**：在所有评估工作负载上持续胜出，**最高 1.24x 加速**。",
                "三种代表性 pattern 下，ComFuse 的平均加速分别为 **1.08x、1.09x、1.07x**——速度提升稳定的同时，还能表达 TorchInductor 不支持的更灵活融合模式。",
                "论文还评估了 Self-Attention、Target-Attention、DLRM Bottom MLP 等端到端场景，证明融合收益不只在孤立 microbenchmark，也落到真实模型结构中。",
            ],
            "fig_after": {
                "1": [{"src": "fig06.png", "caption": "Figure 7：Stage-Stream 执行模型的总体性能对比。"}],
                "2": [{"src": "fig07.png", "caption": "Figure 8：Stage-Stream 执行模型的残差时间性能对比（残差时间 = 总时间 − MatMul 时间），凸显被隐藏部分的收益。"}]
            }
        },
        {
            "type": "h2",
            "title": "更多场景验证",
            "paras": [
                "在 Self-Attention、Target-Attention 与 DLRM Bottom MLP 上，ComFuse 都展示了超越 TorchInductor 的融合性能——说明它不只针对单一模板，而是能吃到多种「计算-内存」交互结构。",
                "这套方法的收益本质来自两点：**把内存密集执行藏进 GEMM 计算**，以及**用跨 CTA 的片上数据共享省掉全局内存往返**。这也正是现代 GPU 架构上融合编译器该走的两个方向。",
            ],
            "fig_after": {
                "1": [{"src": "fig08.png", "caption": "Figure 9：Self-Attention 性能。"}, {"src": "fig09.png", "caption": "Figure 10：Target-Attention 性能。"}, {"src": "fig10.png", "caption": "Figure 11：DLRM Bottom MLP 的性能。"}]
            }
        },
        {
            "type": "h2",
            "title": "结论",
            "paras": [
                "ComFuse 证明：编译器不该把计算密集和内存密集算子当作两套毫不相干的世界。**利用现代 GPU 的跨 CTA 片上共享 + 流水调度，内存密集子图可以被完全藏到 GEMM 背后**，融合收益既真实又可自动获得。",
                "对跑大模型 post-norm、推荐模型 DLRM、attention 这类「GEMM 后面拖着一长串 elementwise/reduction」的团队，把这类模式交给这种自动融合编译，比手写 CUTLASS epilogue 更省力、也更灵活。",
            ],
        },
    ],
    "conclusion": [
        "ComFuse 的启示是把「operator fusion」从同类算子之间，扩展到**跨计算/内存类别**的联合融合：不是把所有东西塞进一个大 kernel，而是让内存密集部分**偷跑在 GEMM 计算背后**，再靠跨 CTA 的片上共享省掉中间张量的全局往返。",
        "结果是稳定且可复现的——全面超过 TorchInductor、最高 1.24x、平均 1.07-1.09x，还支持 B2BGEMM 这类更复杂的计算-内存交互，且全程自动从高层算子降级，免去手工内核工程。对融合编译器来说，这是一条值得跟进的成熟路线。",
    ],
    "reference_url": "https://arxiv.org/abs/2608.03537v1",
    "title": "ComFuse：把 GEMM 和内存密集子图揉进同一个内核，最高 1.24x 超 TorchInductor",
}

out_path = os.path.join(_article_dir, "article_data.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)
print(f"✅ 写入 {out_path} ({len(json.dumps(DATA, ensure_ascii=False))} chars, {len(DATA['sections'])} sections)")
