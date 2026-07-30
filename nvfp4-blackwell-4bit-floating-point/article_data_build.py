#!/usr/bin/env python3
"""
article_data_build.py — NVFP4 on Blackwell: What 4-Bit Floating Point Actually Delivers
===================================================================================
X article by @Mayhem4Markets — detailed technical analysis of NVIDIA's NVFP4 format
"""
import json, os, sys
_article_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()

DATA = {
    "title": "NVFP4 on Blackwell：4 位浮点究竟带来了什么",
    "summary": [
        {"key": "核心数据", "body": "比 FP8 高 2-3 倍吞吐，比 BF16 少 3.5 倍内存，大模型精度损失 1-2 个百分点以内"},
        {"key": "E2M1 格式", "body": "1 符号位 + 2 指数位 + 1 尾数位 = 15 个不同值，两级缩放策略每 16 元素块共享 1 个 FP8 缩放因子"},
        {"key": "四大算法支柱", "body": "Random Hadamard Transform + 2D 块缩放 + 随机舍入 + 选择性高精度层，缺一不可"},
    ],
    "lead": [
        "NVIDIA 的 Blackwell GPU 通过名为 NVFP4 的格式引入了原生 4 位浮点计算硬件支持。**结果是切实的：比 FP8 高 2-3 倍吞吐，比 BF16 少 3.5 倍内存，大模型精度在 1-2 个百分点以内。** 这不是营销话术——独立基准、预印本研究、社区测试均已确认。一个 4780 亿参数的模型在 BF16 下需要 960 GB，用 NVFP4 只需 270 GB——这意味着四张 96 GB 工作站显卡可以运行它，还留有 20 万 token 上下文窗口的空间。在消费级硬件上，RTX 5090 运行 Qwen3.6-35B 可达 175 tokens/s，能耗比 BF16 低 41%。",
    ],
    "sections": [
        {
            "type": "h2",
            "title": "NVFP4 如何用 4 位表示神经网络值",
            "paras": [
                "NVFP4 使用 **E2M1 浮点格式**：1 个符号位、2 个指数位、1 个尾数位。16 种位模式编码 15 个不同的值：零、正负 0.5、1.0、1.5、2.0、3.0、4.0 和 6.0。**4 位本身无法覆盖神经网络中的值范围，NVFP4 通过两级缩放策略来解决。** 每 16 个元素块共享一个 FP8 E4M3 缩放因子，整个张量有一个 FP32 全局缩放。实际值 = 全局缩放 × 块缩放 × 块内 FP4 值 × 缩放因子。",
                "存储代价为每 16 个值 9 字节（4.5 位/元素）。相比 OCP MXFP4 标准的 4.25 位，NVFP4 有 6% 的存储开销。**这个开销换来两样东西：更小的块（16 vs 32 元素）为不均匀分布提供更紧凑的缩放；FP8 缩放因子相比 MXFP4 的 E8M0 纯幂缩放有 8 倍尾数精度。** 结果是在 LLM 基准上困惑度低 0.3-0.5。",
                "供应商锁定提醒：NVFP4 是 NVIDIA 专有格式。MXFP4 是 AMD、Intel、ARM 支持的开放 OCP 标准。两者都在 Blackwell Tensor Core 上运行，但 NVFP4 的 checkpoint 不能移植到非 NVIDIA 硬件。",
            ],
        },
        {
            "type": "h2",
            "title": "Blackwell Tensor Core：原生 FP4 硬件",
            "paras": [
                "Blackwell 的第五代 Tensor Core 原生执行 FP4 矩阵乘累加运算。它们消费 NVFP4 输入，产生 FP32、BF16 或 FP8 输出。**反量化发生在 Tensor Core 内部，无需单独的反量化核函数。** 数据中心（B200、GB200）和消费级（RTX 5090、RTX PRO 6000）Blackwell GPU 使用相同的 Tensor Core 硬件。",
                "第二代 Transformer Engine 通过微张量缩放管理 FP4 量化，在子张量级别动态调整精度。这实际上使 FP4 Tensor Core 性能、参数带宽和每 GPU 模型容量相比 FP8 翻倍。",
                "吞吐量数字真实但需要解读。NVIDIA 称 NVFP4 比 FP8 高 2-3 倍。独立微基准研究发现 Blackwell 比 H200 混合精度吞吐高 1.56 倍。B200 上独立 GEMM 核基准达到 1,547 TFLOPS，仅为理论峰值 6,553 TFLOPS 的 24%——当前核函数还有大量优化空间。",
            ],
        },
        {
            "type": "h2",
            "title": "内存：在相同 VRAM 中装下更大模型",
            "paras": [
                "NVFP4 相比 BF16 减少 3.5 倍内存，相比 FP8 减少 1.8 倍。四张 96 GB 工作站卡（共 384 GB）可运行高达 7000 亿参数的模型，还留有 KV 缓存空间。Qwen3.6-35B 从 70 GB 缩小到 25 GB，能装进单张消费级 GPU。NVFP4 同样适用于 KV 缓存——相比 FP8 提供 50% 的减少，在相同内存预算下实现 2 倍上下文长度或批大小，在 prefill 密集型场景最高可提升 3 倍首 token 延迟。",
            ],
        },
        {
            "type": "h2",
            "title": "精度：4 位的代价到底是多少",
            "paras": [
                "**大模型的新闻是好的。** DeepSeek-R1-0528 通过训练后量化到 NVFP4，7 个基准的退化不到 1%。DeepSeek R1 671B 在 MATH500、AIME24、GPQA-D 和 GSM8K 上的退化在 0-1.2 个百分点之间。一个 120 亿参数模型完全以 NVFP4 预训练 10 万亿 tokens，MMLU-pro 准确率 62.58%，几乎匹配 FP8 预训练的 62.62%。",
                "**小模型损失更多。** 消费级 GPU 基准报告 2-4% 的质量退化。训练后量化对包含复杂训练管线（SFT、RL、模型融合）的小模型造成不可忽视的精度下降。",
                "NVIDIA 的解决方案是**量化感知蒸馏（QAD）**。冻结的 BF16 教师模型通过最小化输出 token 分布之间的 KL 散度来训练 NVFP4 学生。QAD 在 LLM 和视觉语言模型上都能可靠恢复接近 BF16 的精度。有趣的是，**使用原始模型作为教师优于使用更大的教师**，与传统蒸馏直觉相反。",
            ],
        },
        {
            "type": "h2",
            "title": "4 位训练：四个算法支柱缺一不可",
            "paras": [
                "NVFP4 不仅用于推理。NVIDIA 展示了 120 亿参数模型稳定 4 位预训练（10 万亿 tokens），这是公开记载的最长 4 位精度训练运行。**四个算法组件全部必须：**",
                "**Random Hadamard Transforms：** 通过将异常信息在量化前分散到整个向量，约束块级异常值。**2D 块缩放：** 对权重矩阵同时应用行级和列级缩放。**随机舍入（用于梯度）：** 提供无偏估计——舍入误差在大量运算中相互抵消。**选择性高精度层：** 最后四个 Transformer 块保留在 BF16。",
                "缺少任何一项训练都会早期发散。**随机舍入必须专门应用于梯度，而不是激活或权重。** 当 NVFP4 训练不完全匹配更高精度损失时，在训练结束前切换到 BF16（学习率衰减前不久）可以弥合差距。",
            ],
        },
        {
            "type": "h2",
            "title": "软件栈支持",
            "paras": [
                "NVFP4 支持贯穿整个推理和训练栈：TensorRT-LLM 支持数据中心和工作站 Blackwell；vLLM 通过 llm-compressor 库提供 NVFP4 支持；Hugging Face 托管预量化 checkpoint（GLM-5.2、Nemotron 系列、DeepSeek V4 Pro/Flash、Qwen3.6、MiniMax-M3 等）。训练方面，TransformerEngine 提供融合 FP4 量化与 GEMM 核函数，CUTLASS 提供 NVFP4 GEMM 模板，PyTorch torchao 通过 diffusers 集成为扩散模型提供 NVFP4 支持。",
                "一个实际限制：**GeForce Blackwell（SM120/SM121）上的 NVFP4 需要 CUDA 13.0+ 和驱动 580+。DeepGEMM FP4 核函数目前仅限数据中心（SM100），与消费级和工作站卡（SM12x）不兼容。**",
            ],
        },
        {
            "type": "h2",
            "title": "NVFP4 的局限",
            "paras": [
                "优势虽真实但有边界。在 decode 阶段（内存受限），NVFP4 激活量化收益有限。RTX 5090 上仅权重量化的 NVFP4-W4A16 在 decode 中可能反而超越全量化 NVFP4-W4A4，因为成熟的 FP16 GEMM 核能击败早期的 FP4 核。",
                "**缩放布局不兼容是一个反复出现的工程问题。** CUTLASS、DeepGEMM、FlashInfer 使用不同的缩放布局。以错误布局加载权重会产生静默错误的结果。MX-FP4 与 NVFP4 的混淆加剧了这个问题：为 MX-FP4 编写的核函数可能期望 NVFP4 布局，将 FP8 缩放因子当作 FP6 读取会损坏每个块。",
                "**FP4 注意力仍是一个活跃研究领域。** SageAttention3 在 NVFP4 注意力上达到 99.52% 的余弦相似度，但精度风险高于 FP4 GEMM。当注意力占主导或 prefill 是瓶颈时，更低精度带来的收益有限。NVFP4 更小块大小（16 vs MXFP4 的 32）的硬件成本也不是零——Tensor Core 的相对面积开销约 12%。",
            ],
        },
        {
            "type": "h2",
            "title": "何时使用 NVFP4",
            "paras": [
                "**使用 NVFP4 的场景：** 内存压力限制部署、KV 缓存容量约束上下文长度、计算密集型 prefill 占工作负载主导。3.5 倍内存减少使原本需要多 GPU 配置的模型成为可能。吞吐提升在大批量和 prefill 场景中最重要。",
                "**坚持 FP8 的场景：** 精度信心和核函数成熟度比峰值吞吐更重要。FP8 有更长的生产部署历史、更成熟的核函数，不需要 NVFP4 训练所需的四项算法干预。最强劲的用例是在工作站硬件上装下非常大的模型、通过 KV 缓存量化服务长上下文工作负载、以及最大化计算密集型推理的吞吐。最弱的用例是小模型推理、decode 密集型工作负载、以及缩放布局不兼容带来工程风险的自定义核函数开发。",
                "**总的来说，NVFP4 是一个重大进步，Blackwell GPU 可以利用它以最小的精度损失减少内存开销。**",
            ],
        },
    ],
    "conclusion": [
        "这篇 X 长文对 NVFP4 的覆盖极度务实——没有夸大其词，也没有低估局限。**核心结论：在内存受限的场景下，NVFP4 是真正的 game changer；在 decode-heavy 或小模型场景下，收益有限。** 那 12% 的 Tensor Core 面积开销和 6% 的存储开销是 NVIDIA 为精度做的取舍，并在 MXFP4 的开放标准和 NVFP4 的性能优势之间做出了明确的选择。",
        "**最具洞察力的部分：四个算法支柱缺一不可。** HashHadamard Transform 约束异常值、2D 块缩放、随机舍入（仅用于梯度！）、最后 4 层保留 BF16——这套组合让 4 位预训练从不可能变成可能。任何想尝试低精度训练的人都可以从中受益。",
        "**独立观点：** 当前 NVFP4 的最大瓶颈不是精度而是软件生态。24% 的 GEMM 峰值利用率（相比 H100 上 FP8 通常能到 60-70%）说明核函数优化空间极大。结合 DeepGEMM 仅限于数据中心这一事实，消费级 GPU 上的 NVFP4 故事还有很大改进空间。",
    ],
    "reference_url": "https://x.com/Mayhem4Markets/status/2081909466606305656",
    "figs": [
        {"src": "fig01.jpg", "caption": "NVFP4 on Blackwell: 4 位浮点究竟带来了什么——主题图"},
        {"src": "fig02.jpg", "caption": "NVFP4 E2M1 格式与两级缩放策略的可视化解释"},
        {"src": "fig06.jpg", "caption": "NVFP4 内存节省对比：3.5 倍于 BF16，1.8 倍于 FP8"},
        {"src": "fig04.jpg", "caption": "精度基准对比：大模型在 NVFP4 下的退化在 1-2 个百分点以内"},
    ],
}

out_path = os.path.join(_article_dir, "article_data.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)
print(f"✅ 写入: {len(DATA['sections'])} sections, {sum(len(s.get('paras',[])) for s in DATA['sections'])} paras")