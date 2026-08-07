#!/usr/bin/env python3
"""article_data_build.py — RL at 1T Scale 原文全保留模式"""

import json, os, sys

_article_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()

CODE_STYLE = (
    'style="background:#f5f5f5;padding:12px 16px;border-radius:4px;overflow-x:auto;'
    'font-family:Consolas,Monaco,\'Courier New\',monospace;font-size:13px;'
    'line-height:1.5;margin:1em 4px;border-left:4px solid #e0e0e0;"'
)

RUN_CMD = "uv run rl @ examples/glm5_llmd/rl.toml --output-dir /shared/outputs/glm5-llmd"

# 图片语义图注（原文无 figcaption，这些是正文按节讨论的示意图，图注简要描述主题）
CAP_HERO = "GLM-5 在 SWE 任务上的训练表现：131k 序列长度、小于 5 分钟步时间、256 rollout 批大小，仅用 28 个 H200 节点"
CAP_ASYNC = "异步 RL 架构示意：trainer 与 inference 分离，策略权重在优化器步完成后即时更新"
CAP_WEIGHT = "推理侧权重即时更新与 KV 缓存示意：前缀缓存不重置、新 rollout 用 KV-cache salt 重新填充"
CAP_WIDEEP = "Wide EP 宽专家并行配置示意：大规模专家并行叠加 32 路数据并行 rank"
CAP_PD = "Prefill 与 Decode 分离部署示意：长 prefill 请求不再阻塞 decode worker，各节点可预测延迟推进"
CAP_ROUTING = "请求路由示意：结合 KV 缓存复用、队列深度、负载的实时评分路由"
CAP_R3 = "Router Replay（R3）示意：捕获推理路由决策并在 trainer 上回放，KL 失配降低一个数量级"
CAP_FSDP = "FSDP 全分片数据并行示意：参数、梯度与优化器状态跨 DP rank 分片，按需聚合"
CAP_EP = "专家并行（EP）示意：专家不跨 EP 度聚合，token 经 all2all 分发与合并"
CAP_CP = "上下文并行（CP）与 GLM-5 DSA 自定义实现示意：序列保持分片，K/V 投影后收集，稀疏索引高效算注意力"
CAP_FP8 = "块缩放 FP8 训练示意（DeepGEMM 内核）：统一 trainer 与 inference 精度，降低 KL 失配"

DATA = {
    "summary": [
        {"key": "核心成果", "body": "prime-rl 0.6.0 在仅 28 个 H200 节点上，以高达 131k 序列长度、小于 5 分钟步时间、256 rollout 批大小训练 GLM-5。"},
        {"key": "异步RL", "body": "trainer 与 inference 分离，推理策略在优化器步完成后即时更新，避免长尾 rollout 拖垮 GPU 利用率。"},
        {"key": "双侧优化", "body": "推理侧 Wide EP + P/D 分离 + Router Replay（R3）；训练侧 FSDP + EP + CP + 块缩放 FP8。"},
    ],

    "lead": [
        "今天我们发布 prime-rl 0.6.0 版本。该版本使我们（以及你）能够以最高效率在繁重的 Agentic 工作负载上训练万亿参数规模的模型。我们一直在不懈地优化 RL 基础设施，以最大化大型 MoE 模型上的性能，降低在 Agentic 工作流上对 OSS 模型进行后训练所需的成本、时间和痛苦。我们能够在仅 28 个 H200 节点上，以高达 131k 的序列长度、小于 5 分钟的 step 时间和 256 个 rollout 的 batch size，在 SWE 任务上训练 GLM-5。",
        "在本文中，我们将介绍促成这些结果的所有优化，从低精度推理和训练，到 prefill 和 decode 分离式推理部署。我们将以 zai-org/GLM-5.1 作为模型示例，但我们的优化适用于任何大型混合专家（MoE）模型，例如 moonshotai/Kimi-K2.7-Code、nvidia/NVIDIA-Nemotron-3-Ultra-550B-A55B-BF16 等。",
    ],

    "sections": [
        {
            "type": "h2",
            "title": "Agentic RL 的第一性原理",
            "paras": [
                "使用 prime-rl，在 Slurm 集群上只需一条命令即可运行 GLM-5.1 训练：",
                f'<pre {CODE_STYLE}><code>{RUN_CMD}</code></pre>',
                "prime-rl 从零开始构建，旨在支持高效的 Agentic 后训练，采用异步 RL。Agentic 任务通常存在长尾异常值；这些 rollout 可能需要几个小时，尤其是长周期编码任务。如果等到这些 rollout 完成后再更新策略，会导致 GPU 利用率不足并损害性能。异步 RL 通过允许在 trainer 部署上的优化器 step 完成后立即更新推理策略来解决这一问题。在异步 RL 中，trainer 和 inference 是分离的，可以独立优化。",
                "trainer 和 inference 之间存在一个固有的同步点——策略更新。每次优化器 step 后，rollout 策略会用新权重更新。在 prime-rl 中，新权重一可用就立刻更新。为了不拖慢推理，已分发的 rollout 不会重置活跃前缀缓存——这些 rollout 由各种策略生成的 token 组成，KV 缓存也由多个版本产生。然而，新的 rollout，即使与旧的共享前缀，也会重新填充自己的 KV 缓存；我们使用 KV-cache salt 来强制这一点。最后，如果请求由过旧的策略生成，会被直接丢弃；通过 max_off_policy_steps 值控制。",
                "这些交互从系统优化的角度提出了一个有趣的问题：如何优化 trainer 和 inference 两个系统，同时保持它们兼容。",
                "在接下来的章节中，我们将剖析这两个系统以及我们所做的优化。",
            ],
            "fig_after": {
                "2": [
                    {"src": "fig01.png", "caption": CAP_HERO},
                    {"src": "fig02.png", "caption": CAP_ASYNC},
                ],
                "3": [{"src": "fig03.png", "caption": CAP_WEIGHT}],
            },
        },
        {
            "type": "h2",
            "title": "Inference",
            "paras": [
                "Inference 是 RL 训练生命周期中的关键部分。这是模型与环境的交互之处，产生被评估并赋予奖励的 rollout。其中一些能力已存在于推理框架中；其他的我们与 vLLM、Dynamo 等框架密切合作，只有一个目标：为社区提供经过验证、易于使用的最高性能推理配方。",
            ],
        },
        {
            "type": "h3",
            "title": "FP8 Inference",
            "paras": [
                "推理吞吐通常是 RL 系统的瓶颈。推理吞吐在 prefill 和 decode 部署上都从更低精度中受益匪浅。我们大量使用 FP8 推理，配合 DeepEP 和 DeepGEMM 的优化内核，实现更低的延迟和更高的吞吐。",
            ],
        },
        {
            "type": "h3",
            "title": "Wide Expert Parallelism（宽专家并行）",
            "paras": [
                "在其他关于推理性能的文章中，你可能注意到很多关注点都在最小化延迟、为用户实现最高交互性。RL 并非如此——我们的主要目标是最大化吞吐，同时将延迟保持在一定范围内（稍后详述）。",
                "实现这一目标的最佳配置之一是 Wide EP——大规模专家并行，通常跨 ≥32 个 GPU。为最大化吞吐，我们将这一策略与大数据并行 rank 结合，例如 32，创建一大组 GPU，每个持有独立的专家，各自作为独立的端点提供服务。同步按层进行，分别在 dispatch 和 combine 操作中完成。",
            ],
            "fig_after": {
                "1": [{"src": "fig04.png", "caption": CAP_WIDEEP}],
            },
        },
        {
            "type": "h3",
            "title": "Prefill 与 Decode 分离",
            "paras": [
                "Prefill 吞吐是 agentic rollout 的一大瓶颈——某些 model↔env 组合产生的 prefill:decode token 比高达 4:1。如果让同一批推理 worker 同时服务 prefill 和 decode 请求，会增加端到端延迟，显著削弱 PipelineRL 的优势。",
                "如前所述，RL 的优先级是最大化推理吞吐，而非最小化延迟。然而，如果推理批次被 prefill 请求主导导致延迟剧增，可以观察到完成的推理 rollout 出现「分组」现象，导致 trainer 和 inference step 的重叠度很低。",
                "使用 prime-rl 可以无缝使用 P/D 分离。当 prefill 和 decode worker 分离时，长 prefill 请求（冗长的工具输出等）不会阻塞 decode worker，使它们能以可预测的延迟推进。这能更快地完成模型的 turn，工具调用更快到达沙箱执行，如此循环，有时跨越数百个 turn。",
            ],
            "fig_after": {
                "2": [{"src": "fig05.png", "caption": CAP_PD}],
            },
        },
        {
            "type": "h3",
            "title": "KV 缓存管理",
            "paras": [
                "最大化吞吐需要高并发，这反过来需要大量的 KV 缓存空间。如果没有足够的空间，会发生 KV 缓存抖动和前缀缓存命中率低，从而降低吞吐。prime-rl 紧跟推理框架的新特性并端到端支持它们——其中一个例子就是 KV 缓存卸载。",
                "我们使用原生的 vLLM 卸载和 Mooncake，支持分层的 KV 缓存卸载到 CPU 和磁盘。有了更多的 KV 缓存空间，我们可以提高并发度，摊销更多 trainer 成本。",
                "这两种方法之间主要有两处差异：vLLM 原生卸载是一种简单的方法，为每个 worker（DP rank）创建一个单独的 CPU/磁盘池；只有该 worker 能从这个缓存加载。而 Mooncake Store 作为一个集中式存储，将来自所有客户端（节点）的 RAM/磁盘汇集成一个大池，任何节点上的任何推理 worker 都能访问——这提供了显著优势，尤其是在使用更复杂的路由策略时。",
            ],
        },
        {
            "type": "h3",
            "title": "请求路由",
            "paras": [
                "为把所有环节串起来，推理请求需要被高效路由，以实现高效的前缀复用、负载感知路由等。",
                "prime-rl 中的默认路由选项是我们 fork 的 vllm-router，一个极小、轻量的方案，能以最小的配置开销提供强劲的性能。根据你的需求，你可以选择为负载均衡、KV 缓存复用或其他目标优化的路由策略。",
                "我们还支持将 NVIDIA Dynamo router 作为即插即用的替代方案。这使我们能为更大规模运行开发和部署更复杂的路由策略。这些策略结合不同因素，如 KV 缓存复用、队列深度、KV 缓存利用率或当前负载，基于推理 worker 的实时指标为每个 worker 计算得分。然后根据策略及其得分选择 worker。",
                "结合作为集中式 KV 缓存卸载层的 Mooncake Store，这能在跨副本实现前缀缓存命中的同时公平地分配负载并对实时推理指标做出响应。",
            ],
            "fig_after": {
                "3": [{"src": "fig06.png", "caption": CAP_ROUTING}],
            },
        },
        {
            "type": "h3",
            "title": "Router replay（R3）",
            "paras": [
                "Trainer↔inference 的不匹配会悄无声息地毁掉你的 RL 训练。为应对这一点，你可以使用 router replay——prime-rl 中的 R3。它通过捕获推理期间做出的路由决策，并直接在 trainer 上回放它们来工作。这有效地将 trainer 和 inference 之间的 KL 失配降低一个数量级，带来更稳定的训练。",
                "这并非免费——在大规模部署中，路由专家数据可达数十 Gbps，给处理造成很大压力。这曾给我们带来不少麻烦，但现在 prime-rl 能在处理这些数据的同时服务数千个并发的 agentic rollout。",
                "路由专家是一个形状为 [num_layers, top_k, seq_len] 的大流量，很快能增长到数百 GB，这给 Python 处理带来很大负担——即使像把响应转成 Python 字典这样看似简单的操作，也会造成显著的 event-loop 延迟和 CPU 瓶颈。为消除这一开销，prime-rl 将路由专家视为不透明载荷，唯一处理由深度优化的 PyTorch 操作完成，减轻了 CPU 压力。",
                "Router Replay 与其他推理优化完全兼容，包括 P/D 分离，让你能轻松部署生产级技术栈。",
            ],
            "fig_after": {
                "0": [{"src": "fig07.png", "caption": CAP_R3}],
            },
        },
        {
            "type": "h2",
            "title": "Training",
            "paras": [
                "我们的 trainer 基于 torchtitan——一个高性能、纯 PyTorch 的大规模训练代码库。我们从 torchtitan 借鉴了大量 trainer 代码，涵盖 FSDP、EP 和各种其他抽象，同时加入我们自己的改进。",
            ],
        },
        {
            "type": "h3",
            "title": "并行策略",
            "paras": [
                "prime-rl 主要依赖 3 维并行：确切地说是 FSDP、CP 和 EP。每种都有各自的用例、优势和缺点。要让大规模运行顺利进行，你需要以不同程度组合使用它们。在我们的 GLM-5 案例研究中，三者都用上了。",
                "下面简单回顾一下它们。",
                "FSDP。全分片数据并行（FSDP）是我们的基线分布式策略。参数、梯度和优化器状态跨数据并行 rank 分片，并在前向和反向传播中按需聚合。对于 1T+ 参数的模型，这是分摊完整优化器状态或参数内存占用的必要条件。我们使用 PyTorch 的 fully_shard (FSDP2) 作为 FSDP 实现；这使得它易于与其他策略组合。",
                "专家并行（EP）。即使在 FSDP 之后，大模型层在 FSDP 全聚合后仍然过大，无法有效装入单 GPU HBM。以 78 层、800B 参数和 float32 主权重为例，单层全聚合大约需要 (800B × 4) / 78 ≈ 40GB 缓冲区。在 1 层 FSDP 重叠的情况下，仅活动层权重就需要约 80GB 内存。",
                "这正是 EP 的用武之地：我们不再全聚合整个层，而是设置一个单独的内部 EP 度，例如 EP=8，在该范围内不会聚合专家。相反，token 将使用 all2all 原语进行分发和合并。由于专家是层内存占用的主要来源，这显著减少了活动内存。",
                "在 prime-rl 中我们允许两种独立的 EP 配置——torch-native all2all 和 DeepEP。根据我们的观察，torch-native 在单节点 EP 范围（即 EP=8）内吞吐略好，但跨节点时性能显著下降。这时使用 DeepEP 会快得多。",
            ],
            "fig_after": {
                "2": [{"src": "fig08.png", "caption": CAP_FSDP}],
                "4": [{"src": "fig09.png", "caption": CAP_EP}],
            },
        },
        {
            "type": "h3",
            "title": "上下文并行（CP）与 GLM-5 DSA",
            "paras": [
                "上下文并行（CP）。在 131k+ 序列长度下，中间激活（而非参数）成为主要内存成本。上下文并行跨 rank 分片序列维度，以降低每个 GPU 的激活量。",
                "在 prime-rl 中，我们为所有自定义模型支持上下文并行。我们支持两种主要的上下文并行方式：Ring Attention——批次在整个模型前向中按序列分片。当到达核心注意力时，每个 rank 持有自己的 Q、K 和 V 分片，同时以环式模式处理其他 rank 的 K 和 V。Ulysses——与 ring attention 一样，数据在整个模型前向中按序列长度分片。当到达注意力时，all2all 操作将布局从序列分片翻转为头分片，然后在头维度上计算注意力。注意力计算完成后，布局再用另一个 all2all 换回。这与大多数非标准注意力（线性注意力、Mamba 等）配合良好，是我们的默认方案。",
                "然而，也有一些例外——其中之一就是 GLM-5 中使用的 DSA。",
                "对于无法用 Ulysses 和 Ring Attention 并行化的注意力模型，我们编写自定义的上下文并行实现，GLM-5 就是其中之一。",
                "我们的上下文并行实现保持序列分片并计算投影。之后，K 和 V 被收集——由于它们被投影到潜在空间，这很廉价——以便索引器能够看到完整序列。索引器为全局序列计算稀疏索引，核心注意力在这些索引上计算。由于 DSA 具有固定的 top_k，其成本也是固定的（除了 KV 的内存成本，如前所述，可忽略不计）。",
                "这种方案每个注意力层只需一次 all-gather 集合通信，使成本保持在最低。",
            ],
            "fig_after": {
                "5": [{"src": "fig10.png", "caption": CAP_CP}],
            },
        },
        {
            "type": "h3",
            "title": "GLM-5 DSA 内核",
            "paras": [
                "为高效计算 DSA，我们使用自定义内核，大量基于参考实现并针对我们的需求进行了适配，提供快速的前向和反向。",
            ],
        },
        {
            "type": "h3",
            "title": "FP8 训练",
            "paras": [
                "如前所述，训练器与推理之间的不匹配可能会损害训练效果。为应对这一点，我们使用 DeepGEMM 内核来执行块缩放 FP8，如 DeepSeek V3 所提出的。与普遍看法相反，由于量化开销，这实际上并不会提高吞吐量（除非在特定配置下）；然而，它大幅降低了训练器与推理之间的 KL 不匹配，因为两者现在使用相同的精度，甚至在某些情况下使用相同的内核。这进而使训练更加稳定。",
            ],
            "fig_after": {
                "0": [{"src": "fig11.png", "caption": CAP_FP8}],
            },
        },
        {
            "type": "h2",
            "title": "未来的工作",
            "paras": [
                "我们继续探索其他改进 RL 引擎性能的方法，积极与其他框架合作——尤其是 vLLM、Dynamo 和 llm-d 加快推理侧，或 PyTorch 打造极速的 trainer——探索投机解码、NVFP4 训练和推理等技术，以及容错、弹性扩展、子秒级 train↔inference 大模型权重传输等基础设施改进。",
            ],
        },
        {
            "type": "h2",
            "title": "我们在招人！",
            "paras": [
                "大规模 agentic RL，在我们看来，是当今 AI 中最激动人心的系统挑战之一。构建高效的 RL 技术栈需要优化大量组件，既要单独优化又要作为整体系统优化：训练、推理、请求路由、权重广播、在途权重更新、环境、代码执行沙箱，以及更多。",
                "在规模下，每一处开销都很重要。成功源于理解这些系统如何交互、识别瓶颈，并毫不松懈地在整个技术栈中推动效率。",
                "如果你对此感兴趣，希望日常工作涉及大规模构建和优化这些系统、实验新的分布式训练和推理技术，并从数千个 GPU 中榨出最后一丝性能，我们很乐意收到你的来信。",
            ],
        },
    ],

    "conclusion": [
        "prime-rl 0.6.0 证明了大规模 agentic RL 的效率提升来自对推理与训练两套系统的联合优化。推理侧以吞吐为第一目标——Wide EP 大规模并行、P/D 分离让长 prefill 不阻塞解码、Router Replay 把训练与推理的 KL 失配降一个数量级。",
        "训练侧用 FSDP + EP + CP 三维并行支撑万亿参数 MoE，并用块缩放 FP8 统一 train↔inference 精度，让训练更稳定。这些优化以 GLM-5.1 为例，但可平移至 Kimi-K2.7-Code、Nemotron-3-Ultra 等任意大型 MoE 模型。",
    ],

    "reference_url": "https://www.primeintellect.ai/blog/rl-at-1t-scale",
    "title": "1T 规模下的 RL：prime-rl 性能深度解析",
}

out_path = os.path.join(_article_dir, "article_data.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)
print(f"OK 写入 {out_path} ({len(json.dumps(DATA, ensure_ascii=False))} chars, {len(DATA.get('sections', []))} sections)")
