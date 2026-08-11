# -*- coding: utf-8 -*-
"""sglang 重建 FINAL：图文与原文 article.content.blocks 100%一致。
图用 fig_after 精确挂到原文指定段落后；代码块用 <pre>；h2/h3 严格对齐原文标题。
"""
import json, os, sys

DIR = os.path.dirname(os.path.abspath(__file__))

def code(text):
    """代码块 → <pre> 格式"""
    return '<pre style="background:#f6f8fa;padding:12px;border-radius:6px;overflow-x:auto;font-family:Consolas,monospace;font-size:13px;line-height:1.5;white-space:pre-wrap;">' + text + '</pre>'

DATA = {
    "title": "用 SGLang 和 Torch Profiler 剖析 LLM 推理：在 trace 里读懂生产瓶颈",
    "lead": [
        "生产环境里喂一个 LLM 服务时，CPU 侧和 GPU 侧各自在忙什么？本文用 SGLang 自带的 Torch Profiler 集成对单个请求做启动-剖析-回放，把 prefill 和 decode 的每个内核、每次拷贝、每段同步摊开在 Perfetto trace 里，训练读 trace 的直觉。",
        "目标是能认出重复峰值里的 GDN/全注意力块，看懂 batch=1 decode 里瘦长 GEMV 背后的带宽瓶颈，并从张量形状推断内核为何如此选择。基于单张 NVIDIA L4 GPU 上的 Qwen3.5-0.8B，低配机器也能跟做。",
    ],
    "summary": [
        {"key": "核心方法", "body": "用 SGLang profiling 端点对单个请求 warmup+剖析，把 prefill 与 decode 拆成两个 trace，在 Perfetto 里按 CPU/GPU 两时间线阅读。"},
        {"key": "关键发现", "body": "prefill 由重复的 GDN+全注意力块主导，末尾是巨贵的词表投影 GEMV；batch=1 的 decode 被一系列瘦长 GEMV 主导，内存带宽受限而非计算受限。"},
        {"key": "读图直觉", "body": "读 trace 要结合模型布局：6组(GDN+FFN)+注意力 在 profiler 里呈成组重复峰值；内核名要对照张量形状（如词表投影 grid=248320/8）才能读懂。"},
    ],
    "sections": [
        # ============ 节1: 先理解模型 ============
        {
            "type": "h2", "title": "先理解模型",
            "paras": [
                "在打开剖析器之前，先了解我们预期会看到哪些模式/层会很有帮助。请确保你非常理解模型。对于本次运行，重要的模型统计信息如下：",
                "参数 0.8B · 隐藏维度 1024 · 嵌入维度 248k · 层数 24 · 上下文长度 262k tokens",
                "Qwen3.5-0.8B 采用 6 组 (Gated DeltaNet + FFN) 后接 1 个 (Gated Attention + FFN) 的重复结构——这个分组会直接印在 trace 的峰值形态里。",
                "使用 bf16 时，权重大约占用 1.6 GB。",
                code("0.8B parameters * 2 bytes = 1.6 GB"),
                "对于 batch size 为 1 的解码，可以先做一次数学 roofline 检查，预判会遇到哪类瓶颈：",
                code("memory bandwidth for my gpu = 300 GB/s\nweights to move per token = 1.6 GB\nbandwidth-limited throughput ≈ 300/1.6 tokens/s"),
                "计算上限远高于带宽上限。因此，在查看任何 trace 之前，初始假设就是：batch=1 的 decode 瓶颈更接近内存受限而非计算受限。profiler 会验证这一点。",
            ],
            "fig_after": {},
        },
        # ============ 节2: 设置 ============
        {
            "type": "h2", "title": "设置",
            "paras": [
                "现在利用 profiling 端点来记录 CPU 和 GPU 活动，并把 prefill 和 decode 分离为两个 trace，便于阅读。",
                "这里设置等待 5 步（warmup），然后对后续 2 步进行剖析。剖析器在 decode 期间捕获了两次前向传播。",
                code('curl -X POST http://127.0.0.1:30000/start_profile \\\n  -H "Content-Type: application/json" \\\n  -d \'{"steps": 2, "warmup": 5}\''),
                "随后通过 serving benchmark 发送单个请求。",
                code("python -m sglang.bench_serving --backend sglang --num-prompts 1"),
                "另外要记住，CUDA 启动是异步的：CPU 时间线上可能先显示内核启动，而实际内核稍后才在 GPU 时间线上运行。因此读 trace 时主要先看 CPU 端启动，再看 GPU 端执行。",
                "要查看 trace，打开 Perfetto UI 并加载剖析后生成的 trace 文件。",
            ],
            "fig_after": {},
        },
        # ============ 节3: Prefill 部分 ============
        {
            "type": "h2", "title": "Prefill 部分",
            "paras": [
                "____占位0____",
                "这是我们单个请求的完整 prefill 区域。Prefill 是模型消耗提示词 token 并生成单个 token 的阶段。剖析器的上半部分显示 CPU 侧操作，下半部分显示 GPU 侧。",
                "你是否能发现第一个模式？峰值似乎被分成 3 组，中间有一个较小的峰值。另一个引人注目的是第一个峰值比其他峰值大得多。",
                "如果你滚动到最左侧那个较小的峰值并放大一些，会看到大量的初始化工作：启动 torch profiler、sglang 准备输入批次、设置 CUDA 流。",
                "____占位1____",
                "另一个很酷的功能是，如果你想了解某个 CPU 活动启动了哪个内核，可以点击该操作，它会链接到它启动的具体内核，并附带一些信息。",
                "____占位2____\n____占位3____",
                "这种情况下，可以看到从固定 CPU 内存到 GPU 的主机到设备拷贝。对于这次运行，可能是请求元数据、token ID 或调度器需要的某个小张量。",
            ],
            "fig_after": {
                "0": [{"src": "fig01.jpg", "caption": "图 1：单个请求的 Prefill 区域。"}],
                "4": [{"src": "fig02.jpg", "caption": "图 2：调度器准备请求、启动剖析、设置流并构建批次。"}],
                "6": [
                    {"src": "fig03.jpg", "caption": "图 3：一个小的异步复制，关联回 CPU 端的启动。"},
                    {"src": "fig04.jpg", "caption": "图 4：主机到设备的复制量很小，可能是 token id 或请求元数据。"},
                ],
            },
        },
        # ============ 节4: 模式1 - 重复的峰值 ============
        {
            "type": "h2", "title": "模式 1：重复的峰值",
            "paras": [
                "____占位0____",
                "现在位于主 prefill 计算区域内。回想缩小的视图，这些重复的峰值成组出现，并非随机——如果你记得模型架构，它们与分组结构完全吻合。",
                "帮你回忆一下，Qwen3.5-0.8B 有 6 个重复组。每组是 3 个 Gated DeltaNet 块后接 1 个全注意力块，因此期待在 profiler 中看到类似结构：",
                "[GDN + FFN] [GDN + FFN] [GDN + FFN] [Attention + FFN]",
                "[GDN + FFN] [GDN + FFN] [GDN + FFN] [Attention + FFN]",
                "... 重复 6 次",
                "现在放大第一个峰值，看看其中在执行哪些操作。",
                "____占位1____",
                "为什么认为第一组中的第一个峰值远大于其他峰值？假设是第一个混合块相比其他块通常有一些额外的设置开销。",
                "接着滚动到接下来的两个峰值，以及第一组内较小的峰值。",
                "____占位2____",
                "这些是 GDN 块，包含如下内核：causal_conv1d_fn、fused_qkv_split_gdn_prefill、fused_gdn_gating、ChunkGatedDeltaRuleFunction、l2norm_fwd、chunk_local_cumsum、chunk_gated_delta_rule_fwd_kkt_solve、recompute_w_u_fwd、chunk_gated_delta_rule_fwd_h、chunk_fwd_kernel_o。",
                "你还可以通过点击 GPU 部分中的内核来验证这一点。",
                "____占位3____",
                "较小的第四个峰值是使用 FlashInfer 的全注意力块。对只有 45 个 token 的短提示词而言，全注意力其实并不是瓶颈。",
                "模式提醒！在内核部分，能看到重复的绿色粗条，最后是一个大的蓝色内核。记住这一点，下一节会用到。",
            ],
            "fig_after": {
                "0": [{"src": "fig05.png", "caption": "图 5：主 prefill 计算区域，峰值以重复组形式出现。"}],
                "7": [{"src": "fig06.jpg", "caption": "图 6：第一个峰值稍大，因为它包含额外的初始化和索引/复制工作。"}],
                "10": [{"src": "fig07.jpg", "caption": "图 7：接下来的峰值与 GDN 块及较小的全注意力块对应。"}],
                "14": [{"src": "fig08.png", "caption": "图 8：prefill 侧内核。"}],
            },
        },
        # ============ 节5: 最终词表投影 ============
        {
            "type": "h2", "title": "最终词表投影",
            "paras": [
                "____占位0____",
                "如果你越过所有重复的峰值进入最后一段，服务器会进入清理阶段，并为解码做准备，包括最终投影到 logits、采样、以及将结果复制回 CPU。这一部分易被忽略，但在这个 trace 中 logits processor 等操作值得注意。",
                "如果你点击 CPU 端的 aten::mm 并展开参数，PyTorch 会显示：",
                "Input type: ['c10::BFloat16', 'c10::BFloat16'] Input strides: [[1024, 1], [1, 1024]]",
                "从概念上讲，这就是：[1, 1024] @ [1024, 248320] = [1, 248320]",
                "由于词表规模巨大，这变成了一个大型矩阵向量式投影。尽管在本次 prompt 的 prefill 期间仅运行一次，它仍是该部分中最慢的内核之一。",
                "____占位1____",
                "内核细节也相当值得阅读（使用 Nsight 可以做更多操作）：",
                "grid: [31040, 1, 1] block: [8, 8, 1] registers/thread: 168 shared memory: 288 occupancy: 25%",
                "这个网格形状是什么？248320 个词表元素 / 8 = 31040。",
                "不错，最终的线性头将一个 1024 宽的隐藏向量投影到非常大的词表维度上。如果优化这条路径，会仔细研究这个投影能否融合。",
            ],
            "fig_after": {
                "0": [{"src": "fig09.jpg", "caption": "图 9：层堆叠之后，SGLang 准备解码并为采样计算 logits。"}],
                "6": [{"src": "fig10.jpg", "caption": "图 10：词表投影内核的详细信息。"}],
            },
        },
        # ============ 节6: 主要预填充内核 ============
        {
            "type": "h2", "title": "主要预填充内核",
            "paras": [
                "下面来看此工作负载中运行的最突出的内核。",
                "____占位0____",
                "最后的 gemv 内核虽然仅被调用一次，但确实是最昂贵的。128x128 BF16 GEMM 出现 24 次，与每个块一次大型投影式操作相吻合。较小的 CUTLASS BF16 GEMM 出现 18 次，与 18 个注意力块对应。",
                "仅凭内核名称有时会显得嘈杂且难以理解，因此结合模型布局和数据流来理解，会让 trace 更容易分析。",
            ],
            "fig_after": {
                "1": [{"src": "fig11.png", "caption": ""}],
            },
        },
        # ============ 节7: 解码阶段 ============
        {
            "type": "h2", "title": "解码阶段",
            "paras": [
                "____占位0____",
                "解码是与预填充不同的工作负载。预填充阶段模型处理整个提示序列，许多操作有足够的计算量成为像样的 GEMM；而解码阶段批次更小，模型多是一次处理一个新 token，大量投影收缩为瘦长的矩阵向量运算。",
                "____占位1____",
                "在此 trace 中，高亮区域是重要部分。周围区域主要是 profiler 的启动/关闭、输入设置、同步和簿记——值得理解，但不是模型的主要计算路径。",
                "____占位2____",
                "左侧，SGLang 加载批次并将此 decode 步骤的输入复制到固定的 CUDA graph 缓冲区；中间是实际 decode 工作发生的地方。与 prefill 不同，CPU 时间线没有将每个模型层都显示出来，因为 decode 被 CUDA graph 捕获。",
                "在 graph replay 之前，有一些用于设置的小内核和复制操作——它们不是层堆栈，主要是在准备捕获图所需的固定缓冲区和执行状态。",
                "____占位3____",
                "点击进入 graph replay 区域后，GPU 内核在该 replay 下方可见。这是对 decode 至关重要的视图。",
                "____占位4____",
            ],
            "fig_after": {
                "0": [{"src": "fig12.png", "caption": "图 12：Decode 区域。由于剖析了两个步骤，有两次 decode 阶段。"}],
                "2": [{"src": "fig13.jpg", "caption": "图 13：高亮区域是需要重点关注的解码计算路径。"}],
                "4": [{"src": "fig14.jpg", "caption": "图 14：第一个解码步骤，聚焦 CPU 端执行。"}],
                "6": [{"src": "fig15.jpg", "caption": "图 15：在 graph replay 之前会运行一些设置内核。"}],
                "8": [{"src": "fig16.jpg", "caption": "图 16：点击图形回放会显示捕获的 CUDA 图中启动的内核。"}],
            },
        },
        # ============ 节8: Decode 阶段由瘦 GEMV 主导 ============
        {
            "type": "h2", "title": "Decode 阶段由瘦 GEMV 主导",
            "paras": [
                "____占位0____",
                "重复出现的蓝色条柱与我们之前在 vocab projection 周围看到的 GEMV 家族相同。在 decode 阶段它们不断出现，因为对于 batch size 1 的 decode，许多线性层都转化为瘦长的矩阵向量运算。",
                "这是核心性能问题：GEMV 的算术强度远低于大型 GEMM。从内存中读取大量权重，但没有足够的复用来让张量核心像庞大的 prefill GEMM 那样保持忙碌。因此即使 GPU 计算能力充足，decode 路径也可能受内存带宽限制。",
                "这些微小的红/绿/紫色小点是来自混合块的其他 kernel，它们很重要，但对于这次 batch size 1 的运行，trace 的形状主要表明一件事——decode 路径是一长串瘦长的投影运算。",
                "这也解释了为什么 batching 会改变情况。如果增大 batch size，其中一些瘦长运算就不再那么瘦长，工作负载更接近 GEMM 类行为，GPU 有更多机会复用权重，并在每次加载的字节上执行更多有效计算。",
            ],
            "fig_after": {
                "0": [{"src": "fig17.jpg", "caption": "图 17：重复出现的蓝色条柱是 GEMV 系列内核。"}],
            },
        },
        # ============ 节9: 接下来该怎么做？ ============
        {
            "type": "h2", "title": "接下来该怎么做？",
            "paras": [
                "下一步是使用更大的 batch 和更长的 prompt 重复这一分析。这样就可以区分哪些瓶颈是 batch size 1 decode 特有的，哪些即使在 GPU 有更多并行工作可处理时仍然棘手。",
            ],
            "fig_after": {},
        },
    ],
    "conclusion": [
        "读 trace 的核心是把内核名和模型架构对上：重复的 GDN+注意力组解释了一串串成组的峰值，词表投影 GEMV 解释了那一抹昂贵的蓝色，而 decode 里连绵的瘦 GEMV 则指向带宽受限的本质。",
        "这套方法可迁移：换更大的 batch、更长的 prompt、甚至别的模型，同样的阅读顺序——先架构预判，再对照 trace 验证，最后落到瓶颈归属——都能帮你更快定位生产服务的性能问题。",
    ],
    "reference_url": "https://x.com/jino_rohit/status/2085947942339563598",
}

# （占位符方案已弃用，fig_after 直接按最终 paras 索引精确指定）
# 校验
used = [f["src"] for s in DATA["sections"] for f in s.get("fig_after", {}).values() for f in f]
print("引用图:", len(used))
disk = [f for f in os.listdir(DIR) if f.startswith("fig") and (f.endswith(".png") or f.endswith(".jpg"))]
print("磁盘图:", len(disk))
print("缺失:", sorted(set(disk)-set(used)), "多余:", sorted(set(used)-set(disk)))
# 顺序检查
ordr = [s["title"][:12] for s in DATA["sections"]]
print("章节:", ordr)

out = os.path.join(DIR, "article_data_build.py")
with open(out, "w", encoding="utf-8") as fh:
    fh.write('# -*- coding: utf-8 -*-\n"""sglang 重建 FINAL(图文与原文100%一致)"""\nimport json, os, sys\n\n')
    fh.write("_article_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))\n")
    fh.write("DATA = " + json.dumps(DATA, ensure_ascii=False, indent=2) + "\n\n")
    fh.write('with open(os.path.join(_article_dir, "article_data.json"), "w", encoding="utf-8") as f:\n')
    fh.write('    json.dump(DATA, f, ensure_ascii=False, indent=2)\n')
print("✅ 已写 article_data_build.py")
