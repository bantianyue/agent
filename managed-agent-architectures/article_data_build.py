#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, os, sys

_article_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()

DATA = {
    "summary": [
        {"key": "核心变化", "body": "托管 harness 把编排从应用代码搬进配置，开发者只在托管抽象表达不出想要的行为时，才需要自己拥有 agent 循环"},
        {"key": "被搬进平台的六件事", "body": "声明式 agent 定义、不可变版本与具名端点、会话内切换模型、工具外置、技能外置、围绕 agent 循环的外层优化循环"},
        {"key": "该交出去多少", "body": "前沿实验室能同时改模型与 harness，但通用托管 harness 未必最适合你的产品；围绕具体产品定制的 harness 仍有胜出机会"},
    ],
    "lead": [
        "OpenAI 把 Codex harness 以 Agents API 的形式开放出来，Anthropic 用 Claude Managed Agents 讲了同一件事：前沿实验室开始把模型与 harness 放在一起做，并声称这正是他们能做出更好 harness 的原因。",
        "这些托管 harness 里装了什么，决定了你该把 agent 栈交出去多少。从声明式 agent 定义、面向 agent 的发布工程，到会话内换模型、外置的工具与技能，再到围绕 agent 循环的第二层优化循环，下面逐层来看。",
    ],
    "sections": [
        {
            "type": "h2",
            "title": "托管 Agent 服务的兴起",
            "paras": [
                "最近 OpenAI 发布了 Agents API，让开发者可以通过 API 使用托管版的 Codex harness。市面上最强的 agent harness 之一，如今变成了一块开发者可以用来构建应用的基础设施。",
                "这次发布背后有一个重要的架构主张。OpenAI 表示，想用上新模型能力，往往需要同时改动 harness，因此他们计划让 Codex harness 与模型一起维护和迭代。Anthropic 用 Claude Managed Agents 提出了同样的说法。",
                "前沿实验室正在把模型和 harness 放在一起做。更重要的是，他们宣称：因为掌握模型，所以能做出更好的 harness；又因为掌握 harness，所以或许能做出更好的模型。",
                "提供托管 agent 基础设施的公司不止 OpenAI 和 Anthropic。AWS 有 AgentCore Harness，微软有 Foundry Agent Service，Vercel 则从另一个方向切入同一层，用 AI SDK 和一套专门围绕 agent harness 运行的基础设施。与 OpenAI、Anthropic 不同，AWS 和微软提供的托管 harness 并不要求底层模型也来自同一家厂商。",
                "这给 agent 开发者留下两个相关的架构问题：agent 循环里还有多少该由你自己拥有？harness 是否必须来自做模型的那家公司？",
                "先看清这些平台在托管 harness 里装了什么，才能判断自己的 agent 栈愿意交出去多少。",
            ],
        },
        {
            "type": "h2",
            "title": "1. Agent 被当作声明式资源",
            "paras": [
                "最清晰的模式之一，是把 agent 本身当作一种声明式资源。OpenAI 的 Agents API 只要一次 API 调用就能创建一个 Codex agent，在调用里指定任务、模型、工具、环境与多 agent 设置。声明之下的那套 harness 由 OpenAI 运行，不需要开发者自己实现循环。",
                "AWS AgentCore Harness 把同一个思路推得更远。AWS 允许开发者在单次调用里覆盖模型或工具，而不改动底层的 harness 定义。万一托管抽象限制太多，还可以把 harness 导出成 Strands 代码，改由 AgentCore Runtime 运行。",
                "微软在 Foundry Agent Service 里有类似的分层：prompt agent 从一份声明启动，hosted agent 则允许开发者提供自己的实现。",
                "托管 harness 把编排从应用代码搬进了配置，和当年 Kubernetes 与 Helm 给基础设施带来的转变很像。只有当托管 harness 表达不出你想要的行为时，开发者才需要自己拥有 agent 循环。",
            ],
        },
        {
            "type": "h2",
            "title": "2. 面向 Agent 的发布工程",
            "paras": [
                "当 agent 从本地实验走向真正的生产使用，它们需要自己的发布流程。AWS 给 AgentCore harness 提供不可变版本与具名端点，于是更新模型、工具或技能都会产生一个新版本，而不是就地修改现有版本。",
                "AgentCore 还支持用生产流量在 agent 版本之间做 A/B 测试。一个测试可以比较两种提示词，另一个可以比较不同模型，甚至完全不同的 agent 配置。",
                "微软在 Foundry Agent Service 里构建了类似的部署原语：agent 可以被版本化，并发布在稳定端点之后，而不是把一个可变的开发配置直接暴露给应用。",
                "OpenAI 处理版本化的边界略有不同。Agents API 让开发者在模型发布时按版本使用 Codex harness 的能力，而 harness 本身由 OpenAI 维护和更新。这与 AWS 给开发者自己那份 agent 配置提供不可变版本并不相同，但它为应用底下的 harness 建立了独立的发布生命周期。",
            ],
        },
        {
            "type": "h2",
            "title": "3. 模型选择可以发生在会话内部",
            "paras": [
                "传统上，agent 架构会把模型绑定到 agent 上，换模型就意味着改 agent 配置。一些托管 harness 开始把两者分开，让 agent 会话保持不变，底下的模型可以换。",
                "AgentCore Harness 允许同一套 harness 使用 Bedrock 模型、OpenAI、Gemini 或其他兼容厂商。AWS 还允许在同一个会话的不同轮次之间切换模型，且不丢失对话。一个例子是：用一个模型做规划，用另一个模型做执行。",
                "微软在 Foundry Agent Service 里采取了类似做法。它的 model router 可以在同一段对话里为每个请求挑选不同模型，把简单的轮次路由给更便宜的模型，把更复杂的工作交给更强的模型。",
                "在这两种做法里，模型选择与 agent 定义之间的耦合都在变松。运行时可以直接决定下一段工作交给哪个模型，既不需要重建对话，也不需要改动应用接口。",
                "这就打开了按任务类型、价格、延迟或实测性能来路由的空间。一次 agent 会话可以为不同工作使用多个模型，而不用改变自己的身份或应用接口。",
            ],
        },
        {
            "type": "h2",
            "title": "4. 工具正在从 Agent 里移出去",
            "paras": [
                "新的 Codex Agents API 已经把工具当作可以独立于 harness 被发现和加载的资源。agent 可以连接 MCP 服务器、自定义函数与内置工具，而 OpenAI 的 tool search 只在需要时才加载相关工具定义，而不是把全部工具面塞进上下文。",
                "微软用 Foundry Toolboxes 把这种分离推得更远。一个组织可以独立于具体 agent 定义一组工具，并通过托管的 MCP 端点暴露出去，认证与治理都在 toolbox 这一层处理。",
                "AWS 用 AgentCore Gateway 采取了类似做法。API 与 MCP 服务器可以放在共享基础设施之后，被许多不同的 agent 消费。",
                "agent 可以变而工具层不变，工具层也可以变而不必重新部署每个用到它的 agent。认证与访问策略可以跟着工具走，而不必在每个 agent 里各实现一遍。",
                "规模一大，把同一批系统分别接进每个 agent 就是浪费。GitHub 访问不该实现 50 遍，Salesforce、内部数据库、公司搜索同样不该。这些平台正在把公共集成搬进可被许多 agent 消费的共享基础设施。",
            ],
        },
        {
            "type": "h2",
            "title": "5. 技能可以独立于 Agent 定义存在",
            "paras": [
                "和直接嵌在 agent 里的提示词不同，技能可以与使用它的 agent 分开维护。harness 可以在需要时发现并加载这些技能，而不是把所有指令都塞进 agent 定义。",
                "Codex 有这套模式的一个具体版本。Agents API 的 OpenAI 托管沙箱可以配置文件、包、技能与插件，API 自带的示例就把一个技能目录写进了 agent 的环境配置。",
                "AWS AgentCore Skills 把指令与配套资源打包成可复用的单元，挂在 harness 上。它们可以来自 Git、S3，或 AWS 的托管目录。",
                "这把「做一件事的流程」与「执行它的 agent」分开了。一家公司可以为竞品调研维护一个技能、为故障排查维护另一个技能，然后把这些技能开放给许多不同的 agent。",
                "有了托管 agent 框架，agent 定义可以保持相对精简，更多能力放在外面单独维护。",
            ],
        },
        {
            "type": "h2",
            "title": "6. 围绕 Agent 循环的优化循环",
            "paras": [
                "微软的 Agent Optimizer 会评估一个现成的 agent，并生成替代配置。它可以改指令、改工具描述、改技能，或者推荐换一个模型。",
                "这些候选配置会先经过评估，再由开发者决定是否采用。AWS 正在 AgentCore 里组装类似的机制：生产轨迹与评估结果可以产出对提示词或工具描述改动的建议，改动随后可以用真实流量对照当前版本做测试。",
                "这样一来，这些框架把 agent 循环放进了一个评估并改动 agent 自身的第二层循环里。外层循环用生产中的表现生成新的 agent 配置，并让它与当前版本对比。新配置仍需人工批准才会启用，但平台已经可以自行生成并评估它。",
                "至少在目前，OpenAI 没有在 Agents API 里开放同样面向客户的优化循环。但它在一个更低的层级做着相关的优化：持续改进 Codex harness 本身，并让带版本的 harness 能力随新模型一起发布。",
            ],
        },
        {
            "type": "h2",
            "title": "7. 把 Harness 当作 API 边界",
            "paras": [
                "Anthropic 把 Claude Managed Agents 的一个重要设计目标讲得很明确：开发者应当面向稳定接口编程，而 Anthropic 保留改动底层实现的能力。",
                "OpenAI 在 Agents API 上采取类似做法。开发者调用的是托管服务，而 OpenAI 运营着它所说的持续演进的 Codex harness。OpenAI 表示会与模型一起维护并持续改进 harness，让新的 harness 能力随模型发布按版本可用。",
                "托管 harness 放在厂商 API 之后的，远不止推理。它在处理单个任务时可能发起许多次模型调用、中途调用工具，或使用子 agent，而不会把每个内部决策都暴露给应用。Codex 还在 harness 内部处理上下文压缩，因此应用可以跨越多个上下文窗口，而不必自己实现这套机制。",
                "于是 OpenAI 或 Anthropic 可以把模型与 harness 的改进一起交付。举例来说，一项新的模型能力可以与上下文管理或工具使用的改动同时到来，而无需每个应用开发者各自更新自己的编排。",
            ],
        },
        {
            "type": "h2",
            "title": "谁才该真正拥有 Agent 循环？",
            "paras": [
                "托管 agent API 把开发者的边界从模型 API 上移到 agent harness。当模型本身发生变化时，厂商现在有余地改动模型周围的机械结构。",
                "前沿实验室在这里有独特的优势，因为他们能把模型与 harness 一起做。上下文管理、工具使用、规划以及循环的其他部分，可以随它们所支持的那批模型能力一起交付。",
                "但这并不意味着厂商一定能为你的应用做出最好的 harness。围绕某个具体产品设计的 harness，可以利用自己的工作流、工具、数据和约束，这是通用托管 harness 做不到的。",
                "对某些产品来说，这些优化的价值可能超过「harness 与模型一起开发」带来的好处。",
            ],
        },
    ],
    "conclusion": [
        "**这一次的变化不是模型更强，而是开发者的边界从模型 API 上移到了 agent harness。** 边界一上移，厂商就有空间在模型演进的同时改动模型周围的机械结构：一次任务里发起许多次模型调用、中途调用工具、使用子 agent，甚至把上下文压缩也收进 harness 内部。对应用来说，编排代码变少了，代价是把循环内部的一部分控制权交了出去。",
        "值得留意的是各家在这六件事上的分岔：声明式定义、版本与端点、会话内换模型、工具外置、技能外置、外层优化循环，AWS 与微软在这些方向上都比 OpenAI 走得更远，OpenAI 则把 harness 的演进留在自己手里。对做 agent 产品的人来说，判断标准其实很简单：凡是平台能声明、能版本化、能共享的部分，交出去更划算；凡是依赖你自己工作流、数据与约束的部分，自己拥有更划算。",
    ],
    "reference_url": "https://x.com/JoshARosen/status/2098420569242800306",
    "title": "托管 Agent 架构：前沿实验室为什么要重写 Agent 循环",
}

out_path = os.path.join(_article_dir, "article_data.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)
print("OK wrote", out_path, len(DATA.get("sections", [])), "sections")
