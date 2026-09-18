#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
article_data_build.py —— Kimi K3 DSpark（vLLM Blog 2026-09-15）

来源：https://vllm.ai/blog/2026-09-15-kimi-k3-dspark

图位：blocks.jsonl 的 after_para 是全局段序，derive_fig_after 需要 after_section
      （本页抽取结果不含该字段），故此处按源 DOM 顺序手写 fig_after（已在渲染后
      用 check-fig-layout.py 复核）。图文件按 blocks 顺序命名 fig00..fig03。

用法（在文章目录内）：
    python write-article-data.py <dir>
    python render-article.py <dir>
    python add-portal.py <dir>
"""

import json, os, sys

_article_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()

# 源文代码块（docker run 部署命令，逐字保留，来自 blocks.jsonl 的 code 块）
_CODE = r"""docker run --gpus all \
  --privileged --ipc=host -p 8000:8000 \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  -e GLOO_SOCKET_IFNAME=$IFACE_NAME \
  -e NCCL_SOCKET_IFNAME=$IFACE_NAME \
  -e VLLM_ALLREDUCE_USE_FLASHINFER=1 \
  -e VLLM_ENGINE_READY_TIMEOUT_S=3600 \
  -e VLLM_USE_V2_MODEL_RUNNER=1 \
  -e VLLM_USE_RUST_FRONTEND=1 \
  vllm/vllm-openai:latest moonshotai/Kimi-K3 \
  --trust-remote-code \
  --gpu-memory-utilization 0.95 \
  --tensor-parallel-size 16 \
  --nnodes 2 \
  --node-rank 0 \
  --master-addr $HEAD_IP \
  --load-format fastsafetensors \
  --no-enable-flashinfer-autotune \
  --max-model-len 1048576 \
  --kv-cache-dtype fp8 \
  --attention-config '{"use_prefill_query_quantization":true,"mla_prefill_backend":"TOKENSPEED_MLA"}' \
  --enable-prefix-caching \
  --attention-backend TOKENSPEED_MLA \
  --prefix-match-unit 128 \
  --reasoning-parser kimi_k3 \
  --language-model-only \
  --speculative-config '{"model":"RedHatAI/Kimi-K3-speculator.dspark", "num_speculative_tokens":8, "method":"dspark", "draft_sample_method":"probabilistic", "rejection_sample_method":"block"}'"""

_DOT = '<span style="color:#0F4C81;font-size:7px;line-height:1;vertical-align:middle;">\u25cf</span>&nbsp;'
_C = '<code style="background:#f3f4f5;padding:2px 5px;border-radius:3px;color:#0F4C81;">'


def code_inline(s):
    return _C + s + "</code>"


DATA = {
    "title": "为 Kimi K3 训出最快的 DSpark：GB300 NVL72 上的多节点投机解码训练",

    "summary": [
        {"key": "核心成果", "body": "Speculators 把 DSpark 草稿模型的训练扩展到 2.8 万亿参数的 Kimi K3，数学推理上单流交互性从约 110 升到约 435 tok/s/用户。"},
        {"key": "关键机制", "body": "DSpark 保留 DFlash 的单次并行骨干，加一个 Markov logit-bias 头做顺序校正，再加一个置信头按负载调度验证长度。"},
        {"key": "工程支撑", "body": "新增 MooncakeHiddenStatesConnector 打通跨节点隐状态传输，三节点一组（两推理一训练）拿到最佳吞吐。"},
    ],

    "lead": [],

    "sections": [
        {
            "type": "",
            "title": "",
            "paras": [
                "六月，DeepSeek 发布了 DSpark，这是对 DFlash 块级投机解码算法的一次扩展。新算法承诺更强的 token 间连贯性，因此能拿到更长的接受长度。但对开源社区来说，真正的问题永远是同一个：它能不能被训练、被打包、被部署，而且不需要一个博士生全程守着 checkpoint？",
                "靠着 vLLM 项目的 **Speculators 训练库**，答案是响亮的「能」。用 Speculators 可以按标准、Hugging Face 兼容的格式轻松训练、打包、部署 DSpark 草稿模型，vLLM 能直接加载。这套实现已经在 **Qwen3.6-35B-A3B**、**Gemma-4-31B-it**、**GLM-5.2** 等模型上验证过。我们把训练库扩展到了 Kimi K3 这个 2.8 万亿参数的前沿模型。新的 DSpark speculator 在数学推理任务上把单流交互性从约 110 提升到约 435 tok/s/用户，并在并发负载下、相同交互性水平上带来最高 **约 3.5 倍的输出吞吐**。",
            ],
            "fig_after": {
                "1": [{"src": "fig00.png", "caption": "图1：Kimi K3 在有/无 DSpark speculator 情况下的输出吞吐与交互性对比。该 speculator 在数学推理负载上同时提升了单流交互性与聚合输出吞吐。"}],
            },
        },
        {
            "type": "h2",
            "title": "什么是 DSpark？",
            "paras": [
                "大语言模型每做一次前向传播只生成一个 token。投机解码让一个轻量草稿模型先提出若干 token，再由完整的目标模型一次性验证，以此加速这个过程。",
                "EAGLE-3 是一个很强的基线，但它仍然是自回归草稿：提出七个 token 就要走七步顺序草稿。DFlash 改为在一次非因果骨干传播中预测整个块，报告的加速比 EAGLE-3 高出 2.5 倍以上。",
                "代价在于并行位置之间无法互相作为条件。对「Thank you!」这样的提示，模型可能在第 1 位上同时看好「Of」和「No」、在下一位置上同时看好「course」和「problem」，于是拼出「Of problem」这种错配。而验证会在第一个被拒绝的 token 处停止，一个错误就会让剩下的后缀一起作废，DSpark 论文把这个问题称作**后缀衰减**（suffix decay）。",
                "DSpark 保留了 DFlash 的并行骨干，同时加入两个轻量组件：",
                _DOT + "**Markov logit-bias 头**顺序采样 token，并用上一个被选中的 token 调整每个位置的 logits。它的低秩转移矩阵无需再做一次 transformer 传播，就恢复了重要的局部依赖。",
                _DOT + "**置信头**估计每个 token 会被接受的概率。一个硬件感知的调度器依据这些估计值来决策：负载轻时验证更长的前缀，系统繁忙时剪掉不太可能被接受的后缀。",
                "因此 DSpark 通过继承单次骨干传播，保住了并行草稿的主要优势，同时找回了自回归生成的几分连贯性。在 Qwen3 系列目标模型上，它报告的接受序列比 DFlash 长 16% 到 18%、比 EAGLE-3 长 27% 到 31%。在 DeepSeek-V4 的生产服务中，相同吞吐下每个用户的生成速度比此前的 MTP-1 基线提升了 60% 到 85%。",
            ],
            "fig_after": {
                "6": [{"src": "fig01.png", "caption": "图2：DSpark 在一次并行草稿块之后接上顺序校正与置信度打分，并在送入目标模型验证之前做硬件感知的前缀调度。"}],
            },
        },
        {
            "type": "h2",
            "title": "推理阶段的性能",
            "paras": [
                "DSpark 的半自回归设计只有在额外的顺序开销仍远小于再做一次草稿模型前向传播时，才能改善推理性能。开源的 **Kimi K3 DSpark speculator** 使用一个 5 层、50 亿参数的草稿模型，每个解码步提出 8 个 token。",
                "在九个评测域上，它的宏平均接受长度为每轮验证 4.11 个 token。结构化任务上表现最强：数学推理 6.42 个 token，HumanEval 4.96 个，翻译 4.65 个。在请求数较低时，加速尤其明显。",
                "这个模型对长上下文提示格外好用。在 LongBench-v2 这类有挑战的领域数据集上，我们的 Kimi K3 DSpark 在 37.8 万 token 的提示上做到每个解码迭代最多 5.31 个输出 token。即使放到更宽的工作负载上，排名前 10% 的请求也达到了每次迭代至少 3.76 个 token，说明在真正长的上下文下依然能维持很深的投机运行。",
                "随着并发请求增加，它也能有效扩展。并发从 1 提到 16，聚合输出吞吐从每秒 177 个 token 提到 683 个。",
                "更关键的是，负载之下响应起步依然很快。尽管并发请求数变成 16 倍，首 token 时间中位数只增加了 100 毫秒，从 379 毫秒升到 479 毫秒。",
                "部署很简单，按官方 vLLM recipe 针对你的硬件和用例配置即可：",
                "__CODE__bash::" + _CODE,
            ],
            "fig_after": {},
        },
        {
            "type": "h2",
            "title": "硬件环境",
            "paras": [
                "这个模型是在 Verda 慷慨提供的 GB300 机柜上训练的。Verda 是一家欧洲 AI 云厂商，从数据中心到托管服务端到端自持整套技术栈，并且 100% 使用可再生能源。Verda 是欧洲最早部署 GB300 NVL72 机柜的服务商之一，其内部 AI Lab 也在同一批机柜上做推理研究。",
                "这台 GB300 机柜保持 NVIDIA 参考设计，裸金属运行、不做虚拟化，操作系统是 Ubuntu 24.04.4 LTS，跑在 NVIDIA 的 64K 页内核 6.14 上。",
                "Verda 把优化精力集中在最要紧的系统级配置上，让研究者能拿到前沿级的环境。系统使用 NVIDIA 610.57.04 开源内核 GPU 驱动（R610）；除 CUDA 13.1 和 12.9 之外还装了 CUDA 13.4.0 Developer Preview，NCCL 2.31.2 在系统范围内可用。",
                "选 CUDA 13.4.0 是因为它带来了新的 Blackwell 编程特性，也因为它是最早包含 Rubin 支持（" + code_inline("sm_107") + "）的工具链。这能保证今天在 GB300 上编写、剖析的代码，可以面向下一代硬件构建而不出现意外的兼容问题。基于硬件计数器的 GPU 剖析也无需 root 权限即可使用，每位研究者都能对训练和推理负载做剖析。",
                "我们一直在与 Verda 合作，帮助开源训练与推理基础设施跟上最新的 GPU 架构，当前重点是从 GB300 到 VR200 的机柜级系统。很高兴看到这次合作的成果逐渐成形。",
            ],
            "fig_after": {},
        },
        {
            "type": "h2",
            "title": "大规模提取隐状态",
            "paras": [
                "投机解码的草稿模型虽然小，却很有威力，原因之一是它们通常把目标模型的隐状态作为输入来指导预测。这极大改善了它们的工作上下文，也让草稿模型能够把预测紧密对齐到目标模型。",
                "需要注意的是，训练这些草稿模型需要一份数据集，其中既有隐状态输入，也有目标模型的 log 概率输出。好在 vLLM 有一套隐状态提取系统，可以按需为数据集样本取出目标模型的内部隐状态。这套系统使用一个哑草稿模型，复用 vLLM 的草稿模型管线接收目标隐状态，并把它们插入一个哑注意力层的 KV cache。之后，实现 " + code_inline("KVConnector") + " 接口的类就能把隐状态取出并传出 vLLM。目前 vLLM 自带一个 " + code_inline("ExampleHiddenStatesConnector") + " 做的正是这件事：把隐状态异步写入磁盘。",
                "这套系统在单节点的「vLLM 加训练」配置下工作得很好。例如把节点上一半 GPU 用于训练，另一半用 vLLM 服务目标模型并按需提取隐状态。这套系统在 Speculators 和 vLLM 里已经稳定支持了好几个月。但面对 Kimi K3 这样的 2.8 万亿参数模型，即使权重做了 4 bit 量化，最先进的加速器也开始撞上显存上限。我们需要一套能超出单节点训练、支持训练与隐状态提取解耦的系统。",
                "带着这些要求，我们做了 " + code_inline("MooncakeHiddenStatesConnector") + "，它以 Mooncake 传输引擎为后端，在进程之间、跨节点流式传输隐状态。新系统用一个 Mooncake 主代理进程管理与 vLLM 以及注册为客户端各训练实例之间的通信。配置完成后，训练进程可以向 vLLM 前端发请求，并在响应里拿到一个 Mooncake store key。这个 key 再交给 Mooncake master，由它撮合一次从 vLLM 引擎到 Speculators dataloader 的传输。整个过程由 Mooncake 服务端自动管理，传输方式取决于配置：可以用高速 RDMA，也可以用普通 TCP，在相同或不同节点的进程之间传数据。",
            ],
            "fig_after": {
                "2": [{"src": "fig02.png", "caption": "图3：Mooncake 连接器把控制路径与隐状态数据路径分开，vLLM 与 Speculators dataloader 之间用 RDMA 或 TCP 传输。"}],
            },
        },
        {
            "type": "h2",
            "title": "训练 Kimi K3 DSpark",
            "paras": [
                "有了新的 " + code_inline("MooncakeHiddenStatesConnector") + "，我们就有了一套能扩展到大规模、多节点训练的系统。即使把 Kimi K3 量化到 4 bit，这个模型至少仍需要两个 GB300 节点（每节点四块 GPU）来服务。我们试验了不同的训练与 vLLM 配置，发现三节点一组（两个做推理、一个做训练）能给出最好的吞吐。带 Mooncake connector 的 Speculators 还有一个好处：独立扩大或缩小任一组件都非常容易，方便拿到最佳性能。",
            ],
            "fig_after": {
                "0": [{"src": "fig03.png", "caption": "图4：十二节点的 Kimi K3 DSpark 训练拓扑，推理侧是解耦的 vLLM 服务；每组四节点里，一个四 GPU 节点用于训练、两个四 GPU 节点用于 vLLM 推理，隐状态经 Mooncake 传输。"}],
            },
        },
        {
            "type": "h2",
            "title": "相关链接",
            "paras": [
                "DSpark 论文：https://arxiv.org/abs/2607.05147",
                "EAGLE-3 论文：https://arxiv.org/abs/2503.01840",
                "DFlash 论文：https://arxiv.org/abs/2602.06036",
                "Speculators 训练库：https://github.com/vllm-project/speculators",
                "Kimi K3 DSpark speculator 模型：https://huggingface.co/RedHatAI/Kimi-K3-speculator.dspark",
                "Qwen3.6-35B-A3B speculator 模型：https://huggingface.co/RedHatAI/Qwen3.6-35B-A3B-speculator.dspark",
                "Gemma-4-31B-it speculator 模型：https://huggingface.co/RedHatAI/gemma-4-31B-it-speculator.dspark",
                "GLM-5.2 speculator 模型：https://huggingface.co/RedHatAI/GLM-5.2-speculator.dspark",
                "Kimi K3 的 vLLM 部署 recipe：https://recipes.vllm.ai/moonshotai/Kimi-K3",
                "vLLM 社区 Slack：https://slack.vllm.ai/",
            ],
            "fig_after": {},
        },
    ],

    "conclusion": [
        "**DSpark 真正的看点不是又一个投机解码算法，而是草稿模型终于能被当成常规工程产物来交付。** 从 DFlash 的单次并行骨干，到用 Markov logit-bias 头补回局部依赖、用置信头按负载决定验证多长，每一步改动都在为部署让路，而不是为论文指标让路。",
        "值得记住的是取舍落在哪里：并行草稿消掉了顺序延迟，代价是位置之间失去条件依赖，DSpark 用两个轻量组件把这份代价压到可接受的范围。数据侧同理，一个 5 层、50 亿参数的草稿模型之所以能对齐 2.8 万亿参数的目标模型，靠的是把目标模型的隐状态喂进来，而这需要一套能跨节点流式传输隐状态的基础设施。",
        "对做推理服务的人，MooncakeHiddenStatesConnector 这类打通训练与推理数据通路的活比单点算法更值得抄：三节点一组（两推理一训练）就能把训练跑起来，两个组件还能各自独立扩缩容。隐状态提取从单节点走向解耦之后，超大模型的草稿模型不再只是大厂的专属玩法，50 亿参数的草稿模型配上 4 bit 量化的目标模型，普通团队也能在自己的机柜上复现这条链路。",
    ],

    "reference_url": "https://vllm.ai/blog/2026-09-15-kimi-k3-dspark",

    "caption_translations": {
        "fig00": "图1：Kimi K3 在有/无 DSpark speculator 情况下的输出吞吐与交互性对比。该 speculator 在数学推理负载上同时提升了单流交互性与聚合输出吞吐。",
        "fig01": "图2：DSpark 在一次并行草稿块之后接上顺序校正与置信度打分，并在送入目标模型验证之前做硬件感知的前缀调度。",
        "fig02": "图3：Mooncake 连接器把控制路径与隐状态数据路径分开，vLLM 与 Speculators dataloader 之间用 RDMA 或 TCP 传输。",
        "fig03": "图4：十二节点的 Kimi K3 DSpark 训练拓扑，推理侧是解耦的 vLLM 服务；每组四节点里，一个四 GPU 节点用于训练、两个四 GPU 节点用于 vLLM 推理，隐状态经 Mooncake 传输。",
    },
}

out_path = os.path.join(_article_dir, "article_data.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)
print(f"OK {out_path} ({len(json.dumps(DATA, ensure_ascii=False))} chars, {len(DATA.get('sections', []))} sections)")
