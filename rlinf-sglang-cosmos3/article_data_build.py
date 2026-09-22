#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""article_data_build.py - rlinf-sglang-cosmos3

来源: https://www.sglang.io/blog/rlinf-sglang-cosmos3
正文结构真相源: 源文 article DOM 顺序（h2 4 / h3 7 / h4 2 / p / ul / ol / table 2 / img 5
+ 首屏 three.js 交互图 1 张，已按原图重截为静态 PNG 作 图6）。
图位真相源: 源文 DOM 中文档流顺序。
  fig00 = cosmos3-architecture（图1，源文图注为技术报告出处）
  fig01/02/03 = 5000 步 SFT 的三张 loss 曲线（图2/图3/图4）
  fig04 = SglangEmbodiedWorker / SglangServer / LIBERO 模拟器数据流（图5，源文无图注，
          按源文 img alt 文字给出说明）
  fig05 = 首屏 Cosmos3-Nano 评测吞吐可视化（图6，源文为 three.js canvas，无 img 标签，
          按 aria-label 文字给出说明）
表格: 源文 2 张结果表全部保留真实数值，以 section.table 输出在各小标题下。
列表: 源文 ul/ol 结构保留（项目符号用彩色圆点 span，编号用同色序号）。
"""

import os

S = []


def h2(t):
    S.append({"type": "h2", "title": t, "paras": [], "fig_after": {}})


def h3(t):
    S.append({"type": "h3", "title": t, "paras": [], "fig_after": {}})


def t(x):
    S[-1]["paras"].append(x)


def fig(src, cap=""):
    k = str(len(S[-1]["paras"]) - 1)
    if int(k) < 0:
        raise SystemExit("fig 出现在节首，无前置段落: " + src)
    S[-1]["fig_after"].setdefault(k, []).append({"src": src, "caption": cap})


def table(d):
    S[-1]["table"] = d


DOT = '<span style="font-size:7px;line-height:1;vertical-align:middle;color:#0F4C81;">●</span>&nbsp;'


def bullet(x):
    t(DOT + x)


def num(n, x):
    t(f'<strong style="color:#0F4C81;">{n}</strong>&nbsp;' + x)


# ============================================================ 01 Cosmos3
h2("01 Cosmos3：RLinf 具身技术栈的一次升级")
t("Cosmos3 是 NVIDIA 的全模态模型，能原生理解和生成文本、图像、视频、环境音频与动作，目标是提供统一的多模态能力，建模物理世界并生成动作。")
t("架构上，Cosmos 3 采用 Mixture-of-Transformers（MoT）双塔设计，由自回归 Transformer 与扩散 Transformer 组成。")
bullet("自回归 Transformer 负责多模态理解与推理。")
bullet("扩散 Transformer 负责多模态内容生成。")
t("两座塔共享统一的注意力层与 3D mRoPE（3D 多模态旋转位置编码）位置表示，让模型能在多种模态之间建立共享的时空表示，并跨模态边界建模时空结构。")
fig("fig00.png", "图1：（来源：Cosmos3 技术报告，https://arxiv.org/pdf/2606.02800）")
t("Cosmos 3 有 Edge、Nano、Super 三种尺寸。下面描述的整套训练与评测都使用 Cosmos3-Nano。")
t("Cosmos3-Nano 是一个 16B 参数的 MoT 模型，核心沿用 Qwen3-VL-8B 的架构：36 层 Transformer、hidden size 4096、32 个注意力头、8 个 KV 头。")
t("Cosmos3-Nano 并不是完全从零训练。自回归 Transformer 直接复用 Qwen3-VL-8B 的预训练权重，扩散 Transformer 则由 Qwen3-VL-8B 的权重初始化，并在 Cosmos3 的训练过程中继续优化。")
t("目前 Cosmos3 在 RLinf 里的技术配置如下：")
bullet("SFT 训练跑在 RLinf 已有的 FSDP2 训练后端上。")
bullet("评测使用 SGLang 作为推理后端。")
t("Cosmos3 是一个相当复杂的新多模态与动作模型，接进一套已有的具身训练框架本身就是有代表性的工程实践：RLinf 要支持的不再是常规推理任务，而是覆盖多模态理解、动作生成与仿真评测的完整具身工作流。")

# ============================================================ 02 模型 SFT
h2("02 模型 SFT：在 RLinf 既有框架上做轻量接入")

h3("1. 基于适配器的轻量接入：把模型实现与训练框架解耦")
t("Cosmos3 是一个 OmniMoT 模型，架构已经在 NVIDIA 的 cosmos-framework 里开源。对于一个已经有完整官方实现的新模型，接入成本最高的一环不是“能不能跑起来”，而是在不额外维护第二份模型实现的前提下，接进已有的训练框架。")
t("RLinf 没有重写 Cosmos3 的模型架构，而是把 Cosmos3 当作外部的 Hugging Face 模型，通过一层适配器引入。")
t("模型的构建与初始化仍然由 Cosmos 自己的配置系统负责，RLinf 只是在模型外面加了一层薄封装，把 Cosmos3 的接口映射到 RLinf 的接口上。")
t("Cosmos3 的 SFT 跑在 RLinf 已有的 FSDP2 训练后端上，不需要为 Cosmos3 单独搭一套训练循环，checkpoint 的保存与加载、日志和监控都复用 RLinf 现有机制。")
t("核心价值：尽可能完整复用 Cosmos3 的官方实现，不必在 RLinf 里再写一份模型代码。")
t("模型适配与训练框架解耦之后，后续模型有了一条更干净、成本更低的接入路径：直接复用现有训练栈，不需要改动 RLinf 的训练后端。")

h3("2. Cosmos3-Nano 在 RLinf 上的 SFT，训练精度对齐官方实现")
t("数据集用的是 NVIDIA 开源的 LIBERO_LeRobot_v3，包含机器人操作任务的多模态轨迹数据：主视角与腕部相机的 RGB 图像、机器人状态（8 维），以及对应的机器人动作（7 维）。动作表示为 3 维平移 + 3 维轴角旋转 + 夹爪。")
t("加载 LIBERO_LeRobot_v3 之后，Cosmos3 在数据处理阶段即时转换并归一化动作表示：原始的 3 维轴角观测转成 6 维旋转表示（Rot6D），原始的 7 维动作转成 10 维动作表示，再做分位数归一化。")
t("相比轴角，Rot6D 避开了 ±π 附近的不连续，动作空间表示更平滑连续，扩散模型更容易稳定学到动作分布，生成的机器人动作质量也更高。")
t("当前 SFT 实验使用的是 NVIDIA 官方 LIBERO_LeRobot_v3 数据集，视频以 10 FPS 录制。换成其他 LIBERO 数据集或自建数据集时，要留意帧率和相关超参数是否仍与当前 Cosmos3 配置匹配。")
t("Cosmos3 在 RLinf 上跑 5000 步 SFT 的结果如下（与官方 Cosmos3 实现 https://github.com/NVIDIA/cosmos 对齐）：")
fig("fig01.png", "图2：Cosmos3-Nano 在 LIBERO_LeRobot_v3 上 5000 步 SFT 的整体训练 loss")
fig("fig02.png", "图3：Cosmos3-Nano 在 SFT 过程中的动作流匹配 loss")
fig("fig03.png", "图4：Cosmos3-Nano 在 SFT 过程中的视觉流匹配 loss")
t("在 LIBERO_LeRobot_v3 上跑完 5000 步 SFT 后，Cosmos3-Nano 的整体训练 loss 稳定收敛，说明 RLinf 上的 Cosmos3-Nano 接入能有效学到 LIBERO 数据里的视觉分布与动作分布。")

# ============================================================ 03 评测
h2("03 评测：调度解耦与流水线执行")
t("Cosmos3-Nano 在 LIBERO_LeRobot_v3 上微调完成后，下一步就是在仿真里评测训练好的模型，验证实际生成机器人动作的效果。")

h3("1. 任务调度与推理调度解耦：让 RLinf 和 SGLang 各司其职")
t("RLinf 目前支持用 SGLang 作为 Cosmos3 评测的推理后端，SGLang 作为独立的推理服务运行，负责模型推理和并发请求处理。在 RLinf 这一侧，每个计算组件由一个 Worker 管理，Worker 负责该组件的生命周期，以及与其他组件之间的数据交换。")
t("关键设计决策：RLinf 不接管 SGLang 内部的推理调度。")
t("SGLang 本身已经有成熟的推理优化、自己的 Router 和请求调度。RLinf 再在上面叠加生命周期管理或调度，可能干扰 SGLang 自身的调度，拖累推理性能。")
t("RLinf 因此采用非侵入式的 SGLang Worker 架构：")
bullet("RLinf 负责任务编排与数据流。")
bullet("SGLang 负责推理及其自身调度。")
t("SGLang Worker 在初始化时启动 SGLang 推理进程，之后主要负责 RLinf 与 SGLang 之间的数据适配和请求转发，不介入 SGLang 内部的模型推理与请求调度。")
t("当其他 Worker 发起推理请求时，SGLang Worker 先把输入转换成 SGLang 期望的格式，直接发给 SGLang 服务，然后等待推理任务完成。推理结束后，SGLang Worker 取回模型输出、转换回来，再交给下一个 Worker。整个过程中，RLinf 都不干预 SGLang 内部的模型推理、请求调度和 Router 机制。")
t("RLinf 的任务调度与 SGLang 的推理调度就此解耦：RLinf 掌握整体任务流，SGLang 掌握自己的推理效率，两套系统集成干净，SGLang 已有的推理优化也完整保留。")

h3("2. 让 CPU 仿真与 GPU 推理重叠，提高硬件利用率与评测吞吐")
t("仿真和推理属于同一条任务链，吃的算力却不一样：Cosmos3 的 LIBERO 评测里，LIBERO 模拟器主要用 CPU 做环境仿真，SGLang 用 GPU 做模型推理。两者严格串行时，仿真与推理阶段之间会出现明显空转，CPU 和 GPU 都没吃满。")
t("问题因此从“模型能不能跑起来”，变成了：怎么让不同的计算阶段真正并行起来？")
t("做法是评测流程里的流水线执行机制：给定一批评测任务，拆成多个 batch 放到多条流水线上，让不同 batch 在各 Worker 之间交错执行，尽可能把 LIBERO 仿真和 SGLang 推理重叠起来。")
fig("fig04.png", "图5：SglangEmbodiedWorker、SglangServer 与 LIBERO 模拟器之间的数据流")
t("以 LIBERO-10 为例：单台 8 卡服务器上跑一次完整评测，覆盖 10 个任务 × 50 个 demo = 500 个 episode。")
t("RLinf 会启动 128 个并行仿真环境，每个环境负责 4 个仿真任务；任务数无法被并行环境数整除时，用任务补齐保持并行执行宽度不变。128 个环境均匀分布在 8 张 GPU 上，每张卡 16 个，并行执行。这 128 个并行环境还可继续拆成 N 条流水线，每条流水线处理 128 // N 个环境：流水线内部，任务依次经过 LIBERO 仿真、SGLang 推理、LIBERO 动作执行；流水线之间则按流水线方式交错调度。")
num(1, "LIBERO 模拟器先并行运行各个环境，收集当前观测。")
num(2, "RLinf 把多个环境的图像等观测拼成一个 batch，发给 SGLang。")
num(3, "SGLang 用多批、高并发的推理能力同时处理大量请求，生成对应的下一步动作。")
num(4, "RLinf 取回推理结果，把每个动作送回对应的 LIBERO 环境执行，环境再产生下一步观测，进入下一轮推理。")
t("这个循环一直重复，直到所有 episode 评测完成。")
t("评测过程由此变成并行 LIBERO 仿真、RLinf 流水线调度与高并发 SGLang 推理之间的协作：CPU 上的环境仿真与 GPU 上的模型推理在时间上重叠，计算阶段之间的等待被压缩，硬件利用率和评测吞吐同时提高。")

h3("3. 结果：相对单批基线最高 3.33 倍吞吐")
t("把 RLinf 的流水线调度与 SGLang 的高并发推理结合，对当前的 Cosmos3 仿真评测负载做了优化，端到端结果如下：")
fig("fig05.png", "图6：Cosmos3-Nano 在 SGLang 上的评测吞吐，128 集 / 32 环境最高 1.80 倍，500 集 / 128 环境最高 3.33 倍（相对各自基线）")

h3("128 集、32 个仿真环境")
table({
    "head": ["每个请求的观测数", "pipeline_stage_num", "相对吞吐"],
    "rows": [
        ["1", "4", "1.00x"],
        ["2", "2", "1.66x"],
        ["4", "1", "1.80x"],
    ],
})

h3("完整 500 集、128 个仿真环境")
table({
    "head": ["每个请求的观测数", "pipeline_stage_num", "相对吞吐"],
    "rows": [
        ["1", "16", "1.00x"],
        ["2", "8", "1.70x"],
        ["4", "4", "2.67x"],
        ["8", "2", "3.33x"],
        ["16", "1", "2.33x"],
    ],
})
t("第一列是每个请求打包发给 SGLang 的观测数，pipeline_stage_num 是任务被拆成的流水线数量，两者乘积保持恒定。完整 500 集评测的吞吐达到单批基线的 3.33 倍。")

# ============================================================ 04 结语章
h2("04 RLinf × SGLang × Cosmos3：从“多支持一个模型”到“端到端完整具身链路”")
t("接入 Cosmos3 从来不只是让 RLinf“多支持一个模型”。这次工作里，Cosmos3 在 RLinf 里成了一条完整链路，覆盖模型接入、SFT 训练、SGLang 推理与仿真评测，展示的不是对某一个模型的支持，而是 RLinf 怎么以轻量方式持续接入不断演进的具身模型，把训练、推理、评测融进一条端到端流程，再用系统级调度把整体效率往上推。")
t("对具身 AI 来说，基础设施的价值同样不止于“让模型跑起来”，而在于把模型、训练、推理、仿真和任务执行组织成一个能协同高效运转的系统，这也是 RLinf 在具身 AI 与 Agent 基础设施上持续推进的核心方向。")
t("想了解更多，可以访问 RLinf 仓库：https://github.com/RLinf/RLinf（欢迎点星、关注与反馈）")
t("Cosmos3 SFT 文档：https://rlinf.readthedocs.io/en/latest/rst_source/examples/embodied/sft_cosmos3.html")
t("Cosmos3 SGLang 评测文档：https://rlinf.readthedocs.io/en/latest/rst_source/evaluations/guides/cosmos3_sglang.html")

DATA = {
    "title": "RLinf × SGLang：Cosmos3 从微调接入到高效并行评测",
    "summary": [
        {"key": "接入方式", "body": "RLinf 把 Cosmos3 当作外部 Hugging Face 模型，经一层适配器引入，不重写模型实现，SFT 直接复用既有 FSDP2 训练后端。"},
        {"key": "训练对齐", "body": "用官方 LIBERO_LeRobot_v3 数据集跑 5000 步 SFT，动作转成 10 维 Rot6D 表示并做分位数归一化，训练精度对齐官方实现。"},
        {"key": "吞吐提升", "body": "任务调度与推理调度解耦，CPU 仿真与 GPU 推理流水线重叠，完整 500 集评测相对单批基线最高达到 3.33 倍吞吐。"},
    ],
    "lead": [
        "具身智能模型持续演进，模型本身只是完整开发链路里的一环。一个新的 World Action Model（WAM）从模型接入、训练，到推理与仿真评测，都需要一套能快速适配、又能高效跑满的基础设施。",
        "RLinf 此前已经支持 DreamZero 这类世界模型，这次接入 NVIDIA Cosmos 3，并以 SGLang-Diffusion（下称 SGLang）作为推理后端，把 SFT、推理服务与仿真评测串成一条端到端链路。**Cosmos3-Nano 在 RLinf 上的 SFT 训练精度对齐官方实现，而强化后的 SGLang 多批推理与流水线并行评测，把评测吞吐拉到 3.33 倍。**",
        "以这次 Cosmos3-Nano 接入为例，梳理从微调到高吞吐并行评测这条路径上的关键设计决策，以及 RLinf 的流水线调度如何继续推高评测效率。",
    ],
    "sections": S,
    "conclusion": [
        "**接入一个新模型的价值，不在于模型列表又长了一行，而在于整条链路能不能真跑快。**",
        "最关键的一步，是 RLinf 不接管 SGLang 的内部调度：任务编排留在 RLinf，推理效率交给 SGLang，两边互不干扰；再把评测任务拆成多条流水线，让 CPU 上的仿真与 GPU 上的推理在时间上重叠，空转被吃掉，吞吐自然上去，完整 500 集评测因此从单批基线提升到 3.33 倍。",
        "对做具身模型和 Agent 的团队，这里可复用的经验是：新模型接入尽量走适配器、复用既有训练栈；而“仿真 + 推理”这类混合负载，优先考虑流水线重叠，而不是单纯堆硬件。",
    ],
    "reference_url": "https://www.sglang.io/blog/rlinf-sglang-cosmos3",
}

_article_dir = os.sys.argv[1] if len(os.sys.argv) > 1 else os.getcwd()
out_path = os.path.join(_article_dir, "article_data.json")
import json
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)
print(f"OK 写入 {out_path} ({len(json.dumps(DATA, ensure_ascii=False))} chars, {len(DATA.get('sections', []))} sections)")
