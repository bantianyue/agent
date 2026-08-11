# -*- coding: utf-8 -*-
"""sglang 重建 FINAL：图文与原文100%一致。
图文流严格复刻 _tweet.json 的 article.content.blocks 顺序。
图用 fig_after 挂到原文指定段落之后。h2标题/段落/代码块全部对齐原文。
"""
import json, os, sys

DIR = os.path.dirname(os.path.abspath(__file__))
trans = json.load(open(os.path.join(DIR, "_translations.json"), encoding="utf-8"))
# 译文key -> 按原文 text-only 顺序
T = {int(k): v for k, v in trans.items()}

DATA = {
    "title": "用 SGLang 和 Torch Profiler 剖析 LLM 推理：从 trace 里读懂生产瓶颈",
    "lead": [
        "在生产环境喂一个 LLM 服务时，CPU 侧和 GPU 侧到底在各自忙些什么？本博客用 SGLang 自带的 Torch Profiler 集成对单个请求做启动-剖析-回放，把 prefill 和 decode 的每个内核、每次拷贝、每段同步摊开在 Perfetto trace 里。",
        "目标是训练自己读 trace 的直觉：从重复的核心里认出 GDN/全注意力块，从瘦长的矩阵向量里看到 batch=1 decode 的带宽瓶颈，从张量尺寸里推断内核选择。这里用单张 NVIDIA L4 GPU 上的 Qwen3.5-0.8B，算力较弱的机器也能跟做。",
    ],
    "summary": [
        {"key":"核心方法","body":"用 SGLang 的 profiling 端点对单个请求做 warmup+剖析，将 prefill 与 decode 拆成两个 trace，在 Perfetto 里按 CPU/GPU 两行阅读。"},
        {"key":"关键发现","body":"prefill 由重复的 GDN+全注意力块主导、末尾是巨贵的词表投影 GEMV；而 batch=1 的 decode 被一系列瘦 GEMV 主导，内存带宽受限而非计算受限。"},
        {"key":"实用直觉","body":"读 trace 要结合模型布局：6 组(GDN+FFN)+注意力 的架构在 profiler 里表现为成组重复峰值；内核名要对照张量形状（如词表投影 grid=248320/8）才能读懂。"},
    ],
    "sections": [
        {
            "type": "h2", "title": "先理解模型",
            "paras": [
                "在打开剖析器之前，先弄清我们预期看到哪些模式/层。这次运行的关键模型统计：",
                "参数 0.8B · 隐藏维度 1024 · 嵌入维度 248k · 层数 24 · 上下文长度 262k tokens",
                "Qwen3.5-0.8B 的层布局是 6 组，每组为 3 个 (Gated DeltaNet + FFN) 后接 1 个 (Gated Attention + FFN)——这个重复结构会直接反映在 trace 的峰值形态里。",
                "使用 bf16 时，权重大约占 1.6 GB。",
                "代码：0.8B 参数 × 2 字节 = 1.6 GB",
                "对 batch size 为 1 的解码，可以先做一次数学 roofline 检查，预判会遇到哪类瓶颈：",
                "代码：memory bandwidth = 300 GB/s / weights per token = 1.6 GB / bandwidth-limited 吞吐 = 300/1.6",
                "计算上限远高于带宽上限，因此在看任何 trace 之前就能假设：batch=1 的 decode 瓶颈更接近内存受限而非计算受限。",
            ],
            "code_blocks_after": ["fig01"]  # 占位避免误用，实际下面手写
        },
    ],
}

# ---- 由于 inline code 块与 fig_after 需要 render 模板支持的精确位置，改用显式构建 ----
# 直接重写结构化 DATA（每节 paras 为字符串列表；fig_after 为 dict: 段索引->[图]）
# code 块用专门的标记段（render 模板需支持 code 段落）

# 简单起见：正文直接用 <pre> 形式的代码块如何渲染？查模板对code支持。
print("todo")
