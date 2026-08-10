#!/usr/bin/env python3
"""article_data_build.py — SGLang LLM 推理剖析 X 长文（原文保留100%）"""

import json, os, sys

_article_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()

DATA = {
    "summary": [{"key": "核心方法", "body": "用 SGLang 内置 Torch Profiler 剖析单条请求在 NVIDIA L4 上的完整 prefill 与 decode 流程，识别 CPU/GPU 侧事件与内核。"}, {"key": "关键发现", "body": "Prefill 峰值成组对应 Qwen3.5-0.8B 的 GDN+Attention 混合结构；decode 由瘦 GEMV 主导，算术强度低、受带宽上限约束。"}, {"key": "实用价值", "body": "batch size 1 decode 是带宽受限问题，增大 batch 让瘦运算更接近 GEMM、提升权重复用——可直接对照 trace 定位瓶颈。"}],

    "lead": [
        "本博客旨在学习如何对使用 SGLang 服务的 LLM 进行性能分析，并利用其开箱即用的内置 Torch Profiler 集成。思路是：当我在命令行执行 SGLang serve 时，能否识别 CPU 侧和 GPU 侧的事件，并理解“我的时间和计算主要用在哪里？”这个问题。",
        "作为系列博客的第一篇，我使用单个 NVIDIA L4 GPU 上的 Qwen3.5-0.8B 模型，这样算力较弱的用户也能进行性能分析并跟进。除了模型较小之外，它还包含许多较新的架构设计，使 trace 仍然可读。",
    ],

    "sections": [
        {
            "type": "h2",
            "title": "首先理解模型",
            "paras": [
                "This blog is my attempt to learn how to profile an llm served using sglang and its in built torch profiler integration that comes out of box. The idea here would be try and understand when I hit sglang serve on my command prompt, can I recognize the CPU side and GPU side events and understand the question \"where is most of my time and compute going?\"",
                "For this first of many blogs, im using Qwen3.5-0.8B on a single NVIDIA L4 GPU, so a lot of people with lesser compute can also profile and follow along. Besides being a small model, it also has a lot of the newer architecture designs and makes the trace still readable.",
                "Before opening the profiler, it helps to know what patterns/layers we expect to see. Make sure you understand the model very well. For this run, the important model stats are",
                "parameters - 0.8B",
                "hidden dim - 1024",
                "embedding dim - 248k",
                "layers - 24",
                "a pattern of 6 groups of 3 x (Gated DeltaNet + FFN) followed by 1 x (Gated Attention + FFN)",
                "context length - 262k tokens",
                "this means using bf16, the weights take about -",
                "For batch size 1 decode, we can do a basic math roofline check to understand what kind of bottleneck to expect.",
                "The compute roof is way higher than the bandwidth roof. So before looking at any trace, my starting assumption is that for batch size 1 decode, this workload is going to be much closer to memory bound than compute bound. The profiler should either confirm that or explain why that mental model is wrong.",
            ],
            "fig_after": {
                "9": [
                    {"src": "fig01.jpg", "caption": "在层堆叠之后，SGLang 准备解码并为采样计算 logits。"},
                ],
                "10": [
                    {"src": "fig02.png", "caption": "主要 prefill 计算区域。峰值以重复组的形式出现。"},
                ],
            },
        },
        {
            "type": "h2",
            "title": "设置",
            "paras": [
                "Now we make use of the profiling endpoint to record CPU and GPU activities and seperate the prefill and decode into two traces so its easier to read.",
                "Here I say wait for 5 steps (warmup), then profile the next 2 steps. The profiler captures two forward passes during decode.",
                "<pre style=\"background:#f5f5f5;padding:12px 16px;border-radius:4px;overflow-x:auto;font-family:Consolas,Monaco,'Courier New',monospace;font-size:13px;line-height:1.5;margin:1em 4px;border-left:4px solid #e0e0e0;\"><code>curl -X POST http://127.0.0.1:30000/start_profile \\\n  -H &quot;Content-Type: application/json&quot; \\\n  -d &#x27;{\n    &quot;output_dir&quot;: &quot;/workspace/traces&quot;,\n    &quot;start_step&quot;: 5,\n    &quot;num_steps&quot;: 2,\n    &quot;activities&quot;: [&quot;CPU&quot;, &quot;GPU&quot;],\n    &quot;profile_by_stage&quot;: true,\n    &quot;record_shapes&quot;: true,\n    &quot;with_stack&quot;: true\n  }&#x27;</code></pre>",
                "Then I sent a single request with the serving benchmark",
                "<pre style=\"background:#f5f5f5;padding:12px 16px;border-radius:4px;overflow-x:auto;font-family:Consolas,Monaco,'Courier New',monospace;font-size:13px;line-height:1.5;margin:1em 4px;border-left:4px solid #e0e0e0;\"><code>python -m sglang.bench_serving --backend sglang --num-prompts 1</code></pre>",
                "By the way something to keep in mind, CUDA launches are asynchronous. This means the CPU timeline can show a kernel launch earlier, while the actual kernel runs later on the GPU lane and this intially tripped me up a lot. So when reading the trace, I mostly stuck to reading the CPU side first to understand who launched the work, and the GPU side to understand where the device time went.",
                "To view the traces, open Perfetto UI and load the trace files generated after profiling.",
            ],
            "fig_after": {
                "0": [
                    {"src": "fig03.jpg", "caption": "点击图形回放会显示捕获的 CUDA 图中启动的内核。"},
                ],
            },
        },
        {
            "type": "h2",
            "title": "Prefill 部分",
            "paras": [
                "This is the full prefill region for our single request. Prefill is the phase where the model consumes the prompt tokens and produces a single token. The top half of the profiler has the CPU side operations and lower half is the GPU side operations.",
                "Are you able to spot your first pattern? The peaks seem to be grouped into 3 with a smaller peak in between. Another striking thing is the first peak being way bigger compared to the others. Keep this in mind and we will unravel each feature as we progress in the blog.",
                "Cool, if you scroll into the tinier peak to the left most side and zoom in a bit, you will see a lot of setup work. This includes starting the torch profiler, sglang getting ready to prepare the batch of inputs, setting up CUDA streams everything lining up to run the forward pass.",
                "Another cool thing you can do is if you want to know the kernel a particular cpu activity launched, you can click on the operation and it will link you to the exact kernel it launched with some information.",
                "In this case, we can see a host-to-device copy from pinned CPU memory to the GPU. For this run it is probably request metadata, token ids, or some small tensor needed by the scheduler.",
            ],
            "fig_after": {
                "0": [
                    {"src": "fig04.png", "caption": "📷 Decode 区域。由于我分析了两个步骤，因此有两次 decode 阶段。"},
                ],
                "2": [
                    {"src": "fig05.png", "caption": "prefill 侧内核"},
                ],
                "3": [
                    {"src": "fig06.jpg", "caption": "第一个峰值稍大一些，因为它包含了额外的初始化和索引/复制工作。"},
                    {"src": "fig07.jpg", "caption": "词表投影内核的详细信息。"},
                ],
            },
        },
        {
            "type": "h2",
            "title": "模式 1 - 重复的峰值",
            "paras": [
                "Now we are inside the main prefill compute region. Remember from the zoomed out view we had these repeating peaks but they appear in groups. Well, these peaks are not random and if you remember the model architecture, these peaks matches exactly the group structure we had.",
                "To jog your memory a bit, Qwen3.5-0.8B has 6 repeated groups. Each group has 3 Gated DeltaNet blocks followed by 1 full-attention block. So in the profiler, I expect to see something like -",
                "[GDN + FFN] [GDN + FFN] [GDN + FFN] [Attention + FFN]",
                "[GDN + FFN] [GDN + FFN] [GDN + FFN] [Attention + FFN]",
                "... repeated 6 times",
                "Now, let's zoom into the first peak and see what operations are going on in there.",
                "Why do I think the first peak in the first group is way larger than the others? My assumption is going to be that the first hybrid block usually has some extra setup cost compared to the other blocks.",
                "Now scroll onto the next 2 peaks and the smaller peak within the first group.",
                "These are the GDN blocks including kernels like -",
                "causal_conv1d_fn",
                "fused_qkv_split_gdn_prefill",
                "fused_gdn_gating",
                "ChunkGatedDeltaRuleFunction",
                "l2norm_fwd",
                "chunk_local_cumsum",
                "chunk_gated_delta_rule_fwd_kkt_solve",
                "recompute_w_u_fwd",
                "chunk_gated_delta_rule_fwd_h",
                "chunk_fwd_kernel_o",
                "You can also verify this by clicking on the kernels in the GPU section",
                "The smaller fourth peak is the full-attention block which uses FlashInfer. For this short prompt of 45 tokens, full attention is not actually the bottleneck.",
                "Pattern alert! From the kernels section, we have repeating green thick sections and towards the end a final big blue kernel. Keep this mind for the next section.",
            ],
            "fig_after": {
                "0": [
                    {"src": "fig08.jpg", "caption": "高亮区域是需要重点关注的解码计算路径。"},
                ],
                "5": [
                    {"src": "fig09.jpg", "caption": "调度器准备请求、启动性能分析、设置流并构建批次。"},
                ],
                "7": [
                    {"src": "fig10.jpg", "caption": "接下来的峰值与 GDN 块和较小的全注意力块对应。"},
                ],
                "19": [
                    {"src": "fig11.jpg", "caption": "一个小的异步复制，关联回 CPU 端的启动。"},
                ],
            },
        },
        {
            "type": "h2",
            "title": "最终词表投影",
            "paras": [
                "<pre style=\"background:#f5f5f5;padding:12px 16px;border-radius:4px;overflow-x:auto;font-family:Consolas,Monaco,'Courier New',monospace;font-size:13px;line-height:1.5;margin:1em 4px;border-left:4px solid #e0e0e0;\"><code>memory bandwidth for my gpu = 300 GB/s\nweights to move per token = 1.6 GB\nbandwidth limited throughput = 300 / 1.6\n                             = 187.5 tokens/s\n\nFor compute, a very rough inference estimate is around 2P FLOPs per token.\nFLOPs/token = 2 * 0.8B = 1.6 GFLOPs\nbf16 tensor throughput ~ 121 TFLOP/s\n\ncompute-limited throughput = 121000 / 1.6\n                           = 75k tokens/s</code></pre>",
                "If you push past the whole repeating peaks into the final section, the server moves into cleanup and prepares for decode. This includes the final projection to logits, sampling, and copying the result back to CPU. This section is easy to ignore, but in this trace the logits processor contains one of the most expensive kernels.",
                "If you click the CPU side aten::mm and expand the args, PyTorch shows:",
                "Input type:    ['c10::BFloat16', 'c10::BFloat16'] Input strides: [[1024, 1], [1, 1024]] Input dims:    [[1, 1024], [1024, 248320]]",
                "Conceptually, this is:[1, 1024] @ [1024, 248320] = [1, 248320]",
                "Since the vocab size is huge, this turns into a large matrix vector style projection. Even though it runs only once during prefill for this prompt, it is still one of the slowest kernels in the section.",
                "The kernel details are also quite useful to read (you can do more with Nsight)",
                "grid:  [31040, 1, 1] block: [8, 8, 1] registers/thread: 168 shared memory: 288 occupancy: 25%",
                "What's this grid shape? 248320 vocab elements / 8 = 31040",
                "Cool, the final linear head is projecting one 1024 wide hidden vector across a very large vocab dimension. If I were optimizing this path, I would look closely at whether this projection can be fused or look for similar optimizations.",
            ],
            "fig_after": {
                "5": [
                    {"src": "fig12.jpg", "caption": "第一个解码步骤，聚焦 CPU 端执行。"},
                ],
            },
        },
        {
            "type": "h2",
            "title": "主要预填充内核",
            "paras": [
                "Now let's look at the most prominent kernels that are running in this workload.",
                "The final gemv kernel is indeed the most expensive despite being invoked only a single time. The 128x128 BF16 GEMM appears 24 times, which lines up with one large projection-style operation per block. The smaller CUTLASS BF16 GEMM appears 18 times, which lines up nicely with the 18 GDN blocks.",
                "Kernel names alone can be quite noisy and hard to understand sometimes, so understanding the model layout and data flow together can make the trace much easier to reason about.",
            ],
            "fig_after": {
                "0": [
                    {"src": "fig13.png", "caption": ""},
                ],
            },
        },
        {
            "type": "h2",
            "title": "解码阶段",
            "paras": [
                "<pre style=\"background:#f5f5f5;padding:12px 16px;border-radius:4px;overflow-x:auto;font-family:Consolas,Monaco,'Courier New',monospace;font-size:13px;line-height:1.5;margin:1em 4px;border-left:4px solid #e0e0e0;\"><code>0.8B parameters * 2 bytes = 1.6 GB</code></pre>",
                "Decode is a different workload compared to prefill. During prefill, the model processes the entire prompt sequence so many operations have enough work to become decent GEMMs. But during decode with smaller batch sizees, the model is mostly processing one new token at a time and a lot of projection work collapses into skinny matrix vector operations.",
                "In this trace, the highlighted region is the important part. The surrounding regions is mostly profiler setup/shutdown, input setup, synchronization, and bookkeeping. Those are worth understanding, but they are not the main model compute path.",
                "<pre style=\"background:#f5f5f5;padding:12px 16px;border-radius:4px;overflow-x:auto;font-family:Consolas,Monaco,'Courier New',monospace;font-size:13px;line-height:1.5;margin:1em 4px;border-left:4px solid #e0e0e0;\"><code>apt-get update\napt-get install -y cuda-toolkit-13-2\n\nuv venv\nsource .venv/bin/activate\nuv pip install --prerelease=allow sglang\n\nsglang serve --model-path Qwen/Qwen3.5-0.8B</code></pre>",
                "On the left, SGLang loads the batch and copies this decode step's inputs into fixed CUDA graph buffers. In the middle is where the actual decode work happens. Suprise surprise! Unlike prefill, the CPU timeline does not show every model layer as a deep stack of individual launches, because the decode path is using CUDA graph replay.",
                "Before the graph replay, there are a few small kernels and copies for setup. These are not the layer stack. They are mostly preparing the fixed buffers and execution state needed by the captured graph.",
                "Once you click into the graph replay region, the GPU kernels become visible under that replay. This is the view that matters for decode.",
            ],
            "fig_after": {
                "1": [
                    {"src": "fig14.jpg", "caption": "重复出现的蓝色条柱是 GEMV 系列内核。"},
                ],
                "5": [
                    {"src": "fig15.jpg", "caption": "在 graph replay 之前会运行一些设置内核。"},
                ],
                "6": [
                    {"src": "fig16.jpg", "caption": "主机到设备的复制量很小，可能是 token id 或请求元数据。"},
                ],
            },
        },
        {
            "type": "h2",
            "title": "Decode 阶段由瘦 GEMV 主导。",
            "paras": [
                "Perfetto UI 地址：https://ui.perfetto.dev/",
                "The repeated blue bars are the same GEMV family we saw around the vocab projection. In the decode phase, they just keep showing up and this is because for a batch size 1 decode, it simply turns many linear layers into matrix-vector style operations.",
                "This is the core performance issue. GEMV has much lower arithmetic intensity than a large GEMM. You stream a lot of weights from memory, but there is not enough reuse to keep the tensor cores busy in the same way a chunky prefill GEMM can. So even on a GPU with plenty of compute, the decode path can become memory-bandwidth limited.",
                "The tiny red/green/purple blips are other kernels from the hybrid blocks which are important, but for this batch size 1 run, the shape of the trace is mostly screaming one thing - the decode path is a long sequence of skinny projections.",
                "This also explains why batching changes the story. If you increase batch size, some of these skinny operations become less skinny. The workload gets closer to GEMM-like behavior, and the GPU has more opportunity to reuse weights and do useful math per byte loaded. That does not make batching free, because KV cache, latency, scheduling, and memory pressure all matter, but it explains why single-request decode is such a hard shape for GPUs.",
                "Where to go from here?",
                "The next step from here would be to repeat this analysis with larger batches and longer prompts. That would separate which bottlenecks are specific to batch size 1 decode from the ones that stay painful even when the GPU has more parallel work to chew on.",
            ],
        },
    ],

    "conclusion": ["剖析 SGLang 服务的 LLM，关键在于先把预计算的 roofline 假设与 trace 里看到的实际峰值一一对应：带宽受限的 GEMV 在 decode 主导、算术强度更高的 GEMM 在 prefill 主导，峰值的分组结构正好映射模型的混合块布局。", "对 batch size 1 的 decode，瓶颈几乎总是瘦 GEMV 的带宽上限而非计算上限；增大 batch 让这些瘦长运算变成 GEMM，GPU 有更多机会复用权重。下一步用更大 batch 和更长 prompt 重复这套分析，就能区分出哪些瓶颈是单样本特有的、哪些在高压力下仍然棘手。"],

    "reference_url": "https://x.com/jino_rohit/status/2085947942339563598",
    "title": "用 SGLang 与 Torch Profiler 剖析 LLM 推理",
}

out_path = os.path.join(_article_dir, "article_data.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)
print(f"OK 写入 {out_path} ({len(json.dumps(DATA, ensure_ascii=False))} chars, {len(DATA.get('sections', []))} sections)")
