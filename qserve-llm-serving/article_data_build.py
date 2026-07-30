#!/usr/bin/env python3
"""
article_data_build.py — QServe: W4A8KV4 Quantization and System Co-design for Efficient LLM Serving
精简编译模式，基于 arXiv 2405.04532 (QServe, MIT)。
"""
import json, os, sys

_article_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()

DATA = {
    "title": "QServe: W4A8KV4 量化 + 系统协同设计，LLM 推理吞吐最高提升 3.5 倍",

    "summary": [
        {"key": "核心问题", "body": "现有 INT4 量化方法在 GPU 上反量化开销高达 20-90%，导致理论性能增益无法实现——一个 CUDA core 操作等于 50 个 INT4 tensor core MAC"},
        {"key": "W4A8KV4", "body": "提出 QoQ 算法（4-bit 权重、8-bit 激活、4-bit KV cache），通过渐进式分组量化让所有 GEMM 在 INT8 tensor core 上执行，避免主循环反量化瓶颈"},
        {"key": "系统优化", "body": "计算感知权重重排减少指针运算开销、寄存器级并行加速反量化、SmoothAttention 缓解 KV4 精度损失，L40S 上吞吐超过 A100 的 TensorRT-LLM"},
    ],

    "lead": [
        "量化是加速 LLM 推理的关键技术。但现有 INT4 量化方案有一个被忽视的问题：**GPU 上反量化的运行时开销高达 20-90%**，导致理论上的低精度加速比在实践中完全无法兑现。",
        "MIT 团队在 QServe 中提出了 **W4A8KV4 精度组合（QoQ 算法）+ 系统级协同设计**，首次在数据中心 GPU 上实现了 INT4 量化端到端加速。在 A100 上比 TensorRT-LLM 的最优配置高 **1.2-2.4 倍**，在 L40S 上甚至超过 TensorRT-LLM 在 A100 上的吞吐。",
    ],

    "sections": [
        {
            "type": "h2",
            "title": "动机分析：为什么现有 INT4 量化没加速",
            "paras": [
                "论文首先通过 Roof-line 模型分析了不同精度组合的理论吞吐上限。对于 LLM 推理的解码阶段，当 batch size 较小时，GEMM 是 memory-bound，W4A16（权重小，内存占用低）表现更好；当 batch size 较大时，GEMM 变成 compute-bound，W8A8（INT8 tensor core 吞吐量更高）更快。**W4A8 天然地能在所有 batch size 下兼顾两者的优势**——只要所有计算能在 INT8 tensor core 上执行。",
                "Roof-line 分析还揭示了另一个维度：KV cache 量化。Attention 在解码阶段占 50%+ 运行时间（batch=64 时），Attention 本质上是批量 GEMV，计算强度恒为 1 MAC/element，内存带宽由 KV cache 访问主导。KV4 比 KV8 峰值性能翻倍，因此 KV4 对整个系统的加速潜力巨大。",
                "但为什么不选更激进的 W4A4？论文揭示了关键瓶颈：**主循环反量化开销**。在 GPU 的 GEMM 内核中，输出静止（output stationary）数据流有一个包含 100 多次迭代的顺序主循环。",
                "W4A16 需要将 INT4 权重反量化为 FP16（在 CUDA core 上执行），W4A4（如 Atom）需要将 INT32 部分和反量化为 FP32（也在 CUDA core 上）。**A100 上 CUDA core 的峰值性能只有 INT4 tensor core 的 2%**——执行一次反量化相当于 50 个 tensor core MAC 的成本。此外，W4A4 需要两套寄存器（FP32 + INT32），寄存器压力增大导致活跃 warp 数减少，进一步放大延迟隐藏问题。",
            ],
            "figs": [
                {"src": "figure_3-motivation_roofline.png", "caption": "A100 Roof-line 分析：W4A8 在所有 batch size 下都比 W4A16 和 W8A8 有更高的理论吞吐上限。"},
                {"src": "figure_3-motivation_gemm-flow-compare-2x2.png", "caption": "不同精度方案的 GEMM 主循环对比：W8A8 和 FP16 全在 tensor core 上，W4A16 和 W4A4 都需要 CUDA core 反量化。"},
                {"src": "figure_2-background_gemm-flow.png", "caption": "Tensor core GEMM 的输出静止数据流示意图：每个 thread block 计算 tile，沿 reduction 维度顺序迭代。"},
            ],
        },
        {
            "type": "h2",
            "title": "QoQ 算法：W4A8KV4 渐进式分组量化",
            "paras": [
                "QoQ（Quattuor-Octō-Quattuor，拉丁语 4-8-4）算法的核心设计是**渐进式分组量化（Progressive Group Quantization）**。传统 W4A4 需要 per-group 量化权重和激活，并在主循环内反量化 INT32 部分和。QoQ 的做法是：",
                "**第一步**，将权重先量化到 8 位（per-channel FP16 scale，带保护范围 [-119, 119]）。**第二步**，再将这 8 位中间值量化到 4 位。这种两级设计的关键好处是：**所有 GEMM 计算都在 INT8 tensor core 上执行**，主循环内没有反量化操作。",
                "对于 4 位 KV cache 量化带来的精度损失，论文提出了 **SmoothAttention**——将激活量化的挑战从 Key 转移到 Query（Query 不被量化），从而有效缓解精度下降。",
                "在多种 LLM（Llama-3、Qwen1.5、Mixtral 等）上验证，W4A8KV4 的精度几乎无损，困惑度退化小于 0.5。相比 W4A4 方法（如 QuaRot）有显著精度优势。",
            ],
            "figs": [
                {"src": "figure_4-algorithm_quant-exp-two-step.png", "caption": "渐进式分组量化的两步骤：先量化到 8 位（per-channel），再量化到 4 位（per-group），确保全部计算在 INT8 tensor core 上。"},
                {"src": "figure_4-algorithm_llm-block.png", "caption": "QServe 的 LLM block 架构：GEMM 层在 INT8 tensor core 上执行 W4A8 计算，Attention 层在 CUDA core 上执行 FP16 计算。"},
                {"src": "figure_4-algorithm_rotation.png", "caption": "QuaRot 在线旋转 vs QoQ 渐进式量化的精度对比。"},
                {"src": "figure_4-algorithm_smooth.png", "caption": "SmoothAttention 原理：将 Key 的量化难度转移到 Query（不被量化），缓解 KV4 精度损失。"},
            ],
        },
        {
            "type": "h2",
            "title": "计算感知权重重排（Compute-Aware Weight Reorder）",
            "paras": [
                "W4A8 GEMM 面临一个微妙的 GPU 架构问题：**ldmatrix 指令在存储和计算数据类型不同时无法使用**。因为 Tensor Core GEMM intrinsics 要求每个线程获得跨步内存布局（strided layout），而 ldmatrix 只能在存储和计算数据类型相同时自动完成数据分发。",
                "当权重的存储类型为 INT4、计算类型为 INT8 时，ldmatrix 会按字节数而不是元素数分发数据，导致线程 0 拿到自己和线程 1 的数据，线程 1 拿到线程 2 和 3 的数据——数据与计算需求不匹配。",
                "解决方案非常直接：**按计算时的使用顺序重新排列权重**。将整个 GEMM 问题划分为 32×32 的 tile，把每个线程需要使用的 32 个输入通道拼接成一个 128-bit 字连续存储。由于权重是静态的，这种重排不会引入运行时开销。它不仅将指针运算开销降到与 ldmatrix 相同的水平，还保证了 128-bit/thread 的高带宽内存传输。",
            ],
            "figs": [
                {"src": "figure_5-system_weight_reorder.png", "caption": "计算感知权重重排示意图：按线程的使用顺序重新排列，消除 ldmatrix 不兼容带来的指针运算和带宽问题。"},
                {"src": "figure_5-system_dequant_u4tou8.png", "caption": "UINT4 到 UINT8 的高效解包：通过寄存器级并行，仅用三个逻辑操作完成四路并行反量化。"},
            ],
        },
        {
            "type": "h2",
            "title": "KV4 Attention 加速与整体系统",
            "paras": [
                "Attention 在解码阶段占 50%+ 的运行时间（batch=64 时）。LLM 解码的 Attention 本质上是批量 GEMV 操作，计算强度恒为 1 MAC/element，**内存带宽由 KV cache 访问主导**。KV4 相比 KV8 将峰值性能提升 2 倍。",
                "QServe 的 KV cache 管理采用 **per-head、动态量化**（区别于 vLLM/TensorRT-LLM 的 per-tensor 静态量化），为每个 head 独立存储 FP16 scale 和 zero point，在保持 KV4 低内存占用的同时维持精度。",
                "通过将 Attention 的计算强度拐点后移，QServe 确保 KV4 attention 始终处于 memory-bound 区域，使低比特量化有效提升吞吐。系统还支持 page-based KV cache 和 in-flight batching。",
                "端到端评估覆盖了 7 种广泛使用的 LLM（Llama-3-8B/70B、Qwen1.5-72B、Mixtral 8x7B 等），在 A100 和 L40S 上与 TensorRT-LLM 的 FP16/W8A8/W4A16 配置进行全面对比。",
            ],
            "figs": [
                {"src": "figure_4-algorithm_kvcache.png", "caption": "KV4 量化与 per-head 动态 scale 存储的设计示意图。"},
                {"src": "figure_6-evaluation_main_speed.png", "caption": "QServe 与 TensorRT-LLM、Atom、QuaRot 的端到端吞吐对比：A100 上 1.2-2.4x，L40S 上 1.5-3.5x。"},
                {"src": "figure_6-evaluation_speed_same_batch.png", "caption": "相同 batch size 下 QServe 在 L40S 上超过 TensorRT-LLM 在 A100 上的吞吐。"},
            ],
        },
    ],

    "conclusion": [
        "QServe 用 W4A8KV4 精度组合 + 系统协同设计，成功解决了 INT4 量化在 GPU 上的反量化开销问题。**核心洞察是：GPU 推理效率的关键瓶颈不在于 tensor core 的吞吐量，而在于 CUDA core 上运行的辅助操作（反量化、指针运算）。**",
        "QoQ 算法通过渐进式分组量化将所有 GEMM 放在 INT8 tensor core 上执行，计算感知权重重排将指针运算降到最低，SmoothAttention 保证了 KV4 的精度。最终效果：**QServe 在 L40S 上的吞吐超过 TensorRT-LLM 在 A100 上的表现**——考虑到 A100 价格是 L40S 的 3 倍，这个结果令人印象深刻。",
        "代码已开源：github.com/mit-han-lab/omniserve",
    ],

    "reference_url": "https://arxiv.org/abs/2405.04532",
}

# ── 写入 article_data.json ──
out_path = os.path.join(_article_dir, "article_data.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)
print(f"✅ 写入 {out_path} ({len(json.dumps(DATA, ensure_ascii=False))} chars, {len(DATA.get('sections', []))} sections)")