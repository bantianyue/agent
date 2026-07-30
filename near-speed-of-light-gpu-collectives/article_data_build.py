#!/usr/bin/env python3
"""
article_data_build.py — Every Microsecond Matters
arXiv:2607.16100 — GPU collective latency optimization
"""
import json, os, sys
_article_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()

DATA = {
    "summary": [
        {"key": "接近光速下限", "body": "GB200 4 GPU 上小消息 AllReduce 从 11.0μs 降至 2.37μs，距硬件 SoL 下限仅差 7%"},
        {"key": "无屏障同步", "body": "LL 协议、哨兵同步、双缓冲、LL128 Atomic 四种技术消除全局内存屏障，每屏障节省 >1μs"},
        {"key": "端到端收益", "body": "Llama-3.1-70B 推理 ITL 降低 8.7%，每 μs 延迟消除节省约 0.9% 推理成本；cuSOLVERMp 加速 2.3×"},
    ],
    "lead": [
        "GPU 集体通信通常以带宽为优化目标，但长上下文解码密集型 LLM 推理越来越受延迟限制。**在 4 块 GB200 GPU 上，一次小消息 AllReduce 的延迟从 NCCL ring 的 11.0μs 降到了 2.37μs，距硬件 Speed-of-Light（SoL）下限仅差 7%。** 这是怎么做到的？",
    ],
    "sections": [
        {
            "type": "h2",
            "title": "为什么延迟比带宽更重要",
            "paras": [
                "LLM 推理中，服务大型模型需要多块 GPU，许多小型集体操作直接位于 token 生成的关键路径上。长上下文推理时，KV 缓存随序列长度增长，batch size 减小以适配设备内存。结果，AllReduce 等集体操作以相对较小的消息大小频繁调用——**延迟而非带宽成为主导瓶颈。** vLLM、SGLang、TensorRT-LLM 等推理框架已把通信延迟作为一级优化目标。",
                "低延迟集体不仅对 LLM 推理重要，对传统科学计算同样关键。许多模拟器和求解器在紧密同步的阶段中频繁执行小型全局归约。即使在最好的现有实现中，性能仍远高于硬件 SoL 下限。",
            ],
        },
        {
            "type": "h2",
            "title": "内存屏障的代价",
            "paras": [
                "检查现有最先进框架中的 one-shot 和 two-shot AllReduce 实现后，本文观察到——无论采用 push 还是 pull 通信——这些设计通常依赖显式内存屏障来同步对等节点和在线程块级信号数据就绪。",
                "使用 NCCL 的 ncclLsaBarrierSession 测量屏障开销，**每次屏障的延迟超过 1μs。** 在许多 AllReduce 内核中需要两个这样的屏障。当四 GPU 上小消息 AllReduce 在约 5μs 内完成时，两次屏障调用就占总延迟的 40%。**消除这些屏障可以带来显著的性能收益。**",
            ],
        },
        {
            "type": "h2",
            "title": "四种无屏障同步技术",
            "paras": [
                "本文采用 push 模式，并引入四种技术来消除全局内存屏障，每种针对不同消息大小区间。",
            ],
        },
        {
            "type": "h3",
            "title": "LL 协议：极小消息",
            "paras": [
                "LL 源自 NCCL 的 LL 协议，也用于 NVSHMEM 和 MSCCL++。传统同步使用显式标志和强制排序来信号数据到达。**LL 去掉了信号步骤，将 8 字节标志与 8 字节数据打包，用 16 字节原子存储一起传输，** 使接收方通过直接检查标志就能判断数据就绪。代价是有效负载带宽减半、scratch 缓冲区使用翻倍，因此 LL 最适合极小的消息。",
            ],
        },
        {
            "type": "h3",
            "title": "哨兵同步：中等消息",
            "paras": [
                "接收 scratch 缓冲区初始化为哨兵值（如 -NaN），数据直接写入，接收方轮询直到值从哨兵变化。与 LL 相比，**哨兵方法保留完整有效带宽，使用更少的 scratch 空间，** 对中等消息更高效。缺点是需要每次迭代前重置缓冲区，且传输值不能等于哨兵值。",
            ],
        },
        {
            "type": "h3",
            "title": "双向通信与双缓冲",
            "paras": [
                "LL 和哨兵同步解决了单次交换的显式屏障问题，但当消息分多次迭代传输时仍不够。**双向通信与双缓冲技术**的核心思想：每个 rank 与给定对等节点每迭代最多通信一次，从对等节点接收数据隐式地作为下一次发送的许可——类似于基于信用的流控制。这允许多次归约迭代而无需昂贵的全局内存屏障。",
            ],
        },
        {
            "type": "h3",
            "title": "LL128 Atomic AllReduce：创新算法",
            "paras": [
                "这是本文提出的全新 two-shot AllReduce 算法，依赖原子加法而非显式标志。**ReduceScatter 阶段：** 输入分为 N 个 chunk，线程以 8 行为一组处理 128 字节（一个缓存行）。每组的 flag carrier 将其元素设为 1，所有线程对目标 rank 的 scratch 缓冲区执行 atomic add。NVLink 保证缓存行级别原子执行。",
                "**AllGather 阶段：** 当缓存行 flag 等于 rank 数 N 时表示所有 rank 都已贡献。CTA 轮询 scratch 缓冲区直到 flag 等于 N，然后恢复数据写入输出。该算法仅需 D/N 的 scratch 空间，FP32 每 128 字节仅 4 额外字节（≈3% 开销）。限制：需要 NVLink 缓存行级原子加法，仅支持单/半精度加法，结果非确定性。",
            ],
        },
        {
            "type": "h2",
            "title": "微基准测试结果",
            "paras": [
                "在多种 GPU 配置上测试：4×GB200、8×H100、8×H200、8×B200。**在 4×GB200 上，小消息（256 字节）AllReduce 延迟从 NCCL 的 11.0μs 降至 2.37μs——距硬件 SoL 下限仅差 7%。** 在 8×H100 上，从 18.0μs 降至 5.6μs。",
                "**LL128 atomic 在中等消息（4KB-256KB）上最优**，平衡了带宽效率和低延迟。极小消息（<2KB）用 one-shot LL，更大消息用 two-shot 哨兵。随 GPU 数从 4 增至 8，延迟增长接近对数级而非线性，证明无屏障设计有效控制了同步开销。",
            ],
        },
        {
            "type": "h2",
            "title": "端到端应用验证",
            "paras": [
                "**vLLM 推理（Llama-3.1-70B，4×GB200）：** 低延迟内核将 ITL 从 28.7ms 降至 26.2ms（**降低 8.7%**），吞吐量提升 9.5%。每 μs AllReduce 延迟消除约降低 0.9% 的推理成本，在万亿 token 规模下累积成显著的成本降低。",
                "**cuSOLVERMp（8×H100）：** 求解 10000×10000 广义对称定特征值问题，mp_sygvd 执行时间从 1.82 秒降至 0.78 秒（**加速 2.3×**）。加速来自小型集体操作延迟降低，这些操作在紧密同步的求解器阶段中位于关键路径上。",
            ],
        },
    ],
    "conclusion": [
        "本文系统地分析了 GPU 集体通信中延迟的来源，提出了四种消除全局内存屏障的技术，构建了接近硬件 SoL 下限的低延迟 AllReduce 实现。**核心贡献不在单项技术，而在组合：LL 协议 + 哨兵同步 + 双缓冲 + LL128 Atomic，每项针对不同的消息大小区间，共同覆盖从 256 字节到 1MB 的消息范围。**",
        "在 LLM 推理（vLLM）和科学计算（cuSOLVERMp）两个截然不同的领域中都验证了收益——延迟优化的集体通信不是 AI 专用技术，而是跨 HPC 和 AI 的通用需求。",
        "**独立观点：** 7% 的 SoL 差距令人印象深刻，但更值得关注的是方法论的转变——从「加更多带宽」转向「消除不必要的同步」。CUDA 原子操作在 NVLink 缓存行级别的语义保证，被巧妙地复用于同步而非仅用于计算，是一个值得学习的系统设计思路。",
    ],
    "reference_url": "https://arxiv.org/abs/2607.16100",
    "title": "每微秒都重要：GPU 集体通信如何逼近光速延迟下限，LLM 推理 ITL 降低 8.7%",
}

out_path = os.path.join(_article_dir, "article_data.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)
print(f"✅ 写入 {out_path} ({len(json.dumps(DATA, ensure_ascii=False))} chars, {len(DATA.get('sections', []))} sections)")