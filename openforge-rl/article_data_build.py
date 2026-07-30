#!/usr/bin/env python3
"""
article_data_build.py — OpenForgeRL: Train Harness-native Agents in Any Environment
arXiv 2607.21557 — 精简编译，论文类 60% 阈值。图文对应关系参照原文 blocks 顺序。
"""
import json, os, sys

_article_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()

DATA = {
    "title": "微软 OpenForge RL：任意 Harness 中端到端训练 Agent，Claw 和 GUI 全面超越同规模模型",

    "summary": [
        {"key": "核心思路", "body": "通过轻量级代理 + Kubernetes 编排器，将任何 Harness 的推理过程与标准 RL 框架（veRL）解耦，实现端到端训练"},
        {"key": "实验覆盖", "body": "Claw 工具使用（Qwen3-30B-A3B MoE）+ GUI 浏览器/桌面控制（Qwen3-VL-8B），6 个基准全面超越同规模开源模型，GUI 场景匹配或超越数倍规模模型"},
        {"key": "分析发现", "body": "简单 Harness 更容易学习；多 Harness 训练比单一 Harness 更好；RL 提升自验证、工具覆盖和任务完成能力，但错误恢复仍然薄弱"},
    ],

    "lead": [
        "现代 AI Agent 很少是裸语言模型——它们被包裹在日益复杂的推理 Harness 中：Claude Code、Codex、OpenClaw 等脚手架负责管理多轮交互、工具调用和上下文，将模型连接到外部系统。然而，这些 Harness 使推理变成了有状态、多进程的过程，**开放的 RL 框架无法原生表达**。",
        "OpenForge RL 提出了一个简洁的解决方案：**通过代理 + Kubernetes 编排器，将任何 Harness 与任何环境配对，接入标准 RL 代码库。** 在 Claw 工具使用和 GUI 浏览器/桌面控制两个场景中，同规模模型在几乎所有基准上全面超越开源基线。",
    ],

    "sections": [
        {
            "type": "h2",
            "title": "核心问题：Harness 让端到端训练变得困难",
            "paras": [
                "带 Harness 的 Agent 虽然功能强大，但端到端改进对开源研究社区来说遥不可及，原因有两个：",
                "**第一，Harness 与训练栈不兼容。** Harness 把推理变成了有状态、多进程的过程（嵌套工具调用、子 Agent、长程上下文管理），而开放训练栈（veRL、Slime 等）假设 rollouts 是简单的单轮生成或轻量工具调用。开源努力往往需要为训练重新实现一个简化版的 Harness，造成「训练-部署不匹配」。",
                "**第二，Harness 需要容器化环境。** 运行 Harness 需要专用的容器化环境，这些环境不能和控制节点共置，但大多数开放 RL 框架假设 rollouts 在训练器本地运行。这些差距导致专有 Harness 系统越来越领先于研究社区可以训练和研究的范围。",
            ],
        },
        {
            "type": "h2",
            "title": "OpenForge RL：方法与架构",
            "paras": [
                "OpenForge RL 是解决上述问题的开源框架，核心是两个轻量级组件：",
            ],
        },
        {
            "type": "h3",
            "title": "轻量级代理：解耦训练与推理",
            "paras": [
                "代理包装推理服务器（如 vLLM），拦截由 rollout 容器发出的所有生成请求。当 rollout 完成时，代理收集终端奖励和提示-响应对，通过自动轨迹重建将其转换为标准训练样本，兼容任何 RL 代码库（如 veRL）。这样，任何 Harness 都可以运行自己的任意推理，而不需要修改训练循环。",
                "对于基于组的算法（如 GRPO），通过比较同一组内不同轨迹的平均奖励来计算 advantage。",
            ],
        },
        {
            "type": "h3",
            "title": "Kubernetes 编排器：远程容器扩展",
            "paras": [
                "基于 Orchard 构建，Kubernetes 编排器在云提供商（如 Microsoft Azure）上创建、管理和删除 rollout 容器，实现弹性扩展。针对三个实际挑战的解决方案：",
                "**异步 rollout 与超时**：每个 rollout 远程运行，单个无响应会阻塞整个训练批次。通过 wall-clock 超时来终止卡住的作业，训练继续收集剩余 rollouts 的结果。",
                "**错误处理**：因网络问题、Harness 崩溃或超时而失败的轨迹，丢弃所有样本而非使用部分信号。",
                "**资源管理**：弹性创建和删除容器，不超载训练节点。",
            ],
        },
        {
                    "type": "h2",
                    "title": "架构概览：概念图",
                    "paras": [
                        "OpenForge RL 的核心概念如左图所示：一个编排器在云提供商上创建远程沙箱，每个沙箱中运行完整的 Harness 推理。代理包装推理服务器，拦截由 rollout 容器发出的所有生成请求，并在 rollout 完成后收集轨迹和奖励，重建为训练样本。",
                    ],
                    "figs": [
                        {"src": "x1.png", "caption": "Figure 1: OpenForge RL 概念图。代理将 Harness 的推理过程解耦并记录为训练数据。"},
                    ],
                },
                {
                    "type": "h2",
                    "title": "架构概览：系统架构",
                    "paras": [
                        "OpenForge RL 的完整系统架构如下图所示。Kubernetes 编排器在云提供商上创建和管理远程沙箱，代理将推理服务器与训练引擎解耦，使得任何 Harness 都可以运行自己的任意推理，而不需要修改训练循环。",
                    ],
                    "figs": [
                        {"src": "x2.png", "caption": "Figure 2: OpenForge RL 架构概览。代理 + Kubernetes 编排器将任何 Harness 连接到标准 RL 代码库。"},
                    ],
                },
                {
                    "type": "h2",
                    "title": "数据合成管道：流程概览",
                    "paras": [
                        "本文的目标是在超越编程的多种环境中端到端训练基于 Harness 的 Agent，如浏览器和桌面使用。与编程不同，这些领域提供的训练任务、Harness 和 RL 就绪环境要少得多。因此，论文构建了一个简单的管道来合成为数据稀缺领域（如 claw 日常工具使用和计算机使用）的 SFT 和 RL 任务。下图展示了合成管道的整体流程：",
                    ],
                    "figs": [
                        {"src": "x3.png", "caption": "Figure 3: 数据/任务合成管道概览。"},
                    ],
                },
                {
                    "type": "h2",
                    "title": "数据合成管道：任务分布",
                    "paras": [
                        "管道模拟人类策划任务的方式：给定目标领域和任务数量，并行生成 Agent 来（1）基于现实场景提出候选指令；（2）修剪低质量和重复任务；（3）为每个任务构建可执行环境和验证脚本；（4）通过独立开放 LLM/VLM 的 rollout 测试任务；（5）修补缺陷直至通过所有检查。下图展示了训练任务的分布情况：",
                    ],
                    "figs": [
                        {"src": "x4.png", "caption": "Figure 4: 训练任务分布。覆盖 Claw 和 GUI 两个场景。"},
                    ],
                },
        {
            "type": "h2",
            "title": "Claw Agent：工具使用场景",
            "paras": [
                "在文本工具使用场景中，使用 Qwen3-30B-A3B-Thinking 作为骨干模型，在四种 Harness（ReACT、ZeroClaw、OpenClaw、Codex）上训练。通过自动数据合成管道生成任务，从 MiniMax-M2.5 蒸馏 SFT 轨迹，再通过 GRPO 进行 RL 训练（8 × B200 GPU，batch size=8，group size=8）。",
            ],
        },
        {
            "type": "h3",
            "title": "Claw 结果",
            "paras": [
                "OpenForge-Claw 在三个基准上全面超越同规模模型：",
                "**ClawEval**：pass@3 达到 31.7，pass@3 在三次尝试中成功率为 55.9。",
                "**QwenClawBench**：pass@1 达到 33.7。",
                "**MCPAtlas**：pass@1 达到 28.1。",
                "SFT+RL 相比纯 SFT 在鲁棒性和平均成功率上有显著提升，验证了 RL 框架的有效性。",
            ],
        },
        {
            "type": "h2",
            "title": "GUI Agent：多模态浏览器和桌面控制",
            "paras": [
                "在多模态 GUI 场景中，使用 Qwen3-VL-8B-Thinking 作为骨干模型，训练 Kimi-Agent 风格的计算机使用 Agent 和 Molmo-Web 风格的浏览器 Agent。SFT 从 Kimi-K2.5 蒸馏，RL 同样使用 GRPO。",
            ],
        },
        {
            "type": "h3",
            "title": "GUI 结果",
            "paras": [
                "OpenForge-GUI 在三个基准上全面超越同规模模型：",
                "**OSWorld-Verified**：平均成功率 37.7，测试计算机使用场景。",
                "**Online-Mind2Web**：平均成功率 63.0，测试浏览器使用场景。",
                "**WebVoyager**：平均成功率 72.3，测试浏览器使用场景。",
                "值得注意的是，MolmoWeb 使用了超过 200K 任务进行训练，而 OpenForge-GUI 仅用 2.5K 任务就在 Online-Mind2Web 上超越它，在 WebVoyager 上保持竞争力。SFT+RL 相比纯 SFT 在所有三个基准上都有实质性提升。",
            ],
        },
        {
            "type": "h2",
            "title": "分析：Harness 选择与 RL 如何塑造 Agent",
            "paras": [
                "论文围绕三个问题进行了深入分析：",
            ],
        },
        {
            "type": "h3",
            "title": "不同 Harness 的学习难度差异",
            "paras": [
                "在四种 Harness 上的评估显示两个趋势：**支持直接添加自定义工具的 Harness（ReACT 和 ZeroClaw）达到最高性能**；SFT+RL 在每个 Harness 上都带来大幅提升，但 OpenClaw 提升有限——它的提示和上下文远长于其他 Harness。这验证了先前的发现：更简单、设计更好的工具和控制流对 Agent 性能至关重要。",
            ],
        },
        {
            "type": "h3",
            "title": "训练向未见过 Harness 的泛化",
            "paras": [
                "比较两个模型：一个只在 ZeroClaw 上训练，另一个在 ZeroClaw + OpenClaw + Codex 上训练。结果有两个关键发现：",
                "**单一 Harness 训练已能泛化**：只在 ZeroClaw 上训练的模型，在未见过 OpenClaw 上提升 +3.3，在未见过 Codex 上提升 +4.6。",
                "**多 Harness 训练更好**：在所有三个 Harness 上训练的模型效果最好，在复杂 Harness 上提升最大（OpenClaw +9.5，Codex +20.3），甚至 ZeroClaw 自身上也超过了单一训练（48.5 vs 46.0）。",
            ],
        },
        {
            "type": "h3",
            "title": "RL 在 SFT 之上学到了什么",
            "paras": [
                "通过比较 100 条 SFT 和 SFT+RL 轨迹，发现了三个关键变化：",
                "**工具使用优化**：通用 shell 调用从 22.6% 降到 13.9%，转向专用服务工具。图 5a 展示了完整的工具调用分布变化。",
                "**Agentic 能力提升**：RL 增强了错误恢复、自验证和工具覆盖范围。图 5b 的雷达图展示了五种关键能力的变化。",
                "**错误恢复仍然薄弱**：即使在 RL 之后，错误恢复仍然是最弱的能力。论文假设这类能力仅靠 RL 难以获得，可能需要专门的数据或训练方法。",
            ],
            "figs": [
                {"src": "x5.png", "caption": "Figure 5a: ZeroClaw 下工具调用统计。RL 减少通用 shell 调用，转向专用工具。"},
                {"src": "x6.png", "caption": "Figure 5b: Codex 下行为分析雷达图。RL 提升自验证、工具覆盖和错误恢复能力。"},
            ],
        },
    ],

    "conclusion": [
        "OpenForge RL 的核心贡献是提供了一个**开放的框架，让任何 Harness × 任何环境都可以用标准 RL 代码库进行端到端训练**。",
        "Claw 和 GUI 两个场景的实验表明，仅用几百到几千个自动策划的任务，就能训练出超越同规模开源模型、甚至在 GUI 场景中匹配或超越数倍规模模型的 Agent。更重要的是，**在真实部署 Harness 中训练让我们能够分析 Harness 选择和 RL 如何塑造 Agent 行为**——这是此前开源工作无法轻易做到的。",
        "代码、数据和模型将开源，有望降低在真实 Harness 和环境中训练和研究 Agent 的门槛。",
    ],
    "reference_url": "https://arxiv.org/html/2607.21557v1",
}

# ========== 写入逻辑 ==========
os.makedirs(_article_dir, exist_ok=True)
out = os.path.join(_article_dir, "article_data.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)
print(f"✅ 写入 {out} ({len(json.dumps(DATA, ensure_ascii=False))} chars, {len(DATA['sections'])} sections)")