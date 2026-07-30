#!/usr/bin/env python3
"""
article_data_build.py — The new rules of context engineering for Claude 5 generation models
基于 Claude Blog + X post by Thariq (Anthropic)。
"""
import json, os, sys

_article_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()

DATA = {
    "title": "Claude 5 时代的上下文工程新规则：Anthropic 砍掉了 80% 的系统提示词",

    "summary": [
        {"key": "核心转变", "body": "Claude 5 代模型不再需要大量约束性规则，Anthropic 删掉了 Claude Code 80% 的系统提示词，评估指标无损失"},
        {"key": "六大转变", "body": "从「给规则」到「让模型判断」，从「给示例」到「设计接口」，从「全堆在前面」到「渐进式披露」等六个关键转变"},
        {"key": "实践建议", "body": "CLAUDE.md 保持轻量，Skill 用渐进式披露，用代码和测试集作为参考而非纯文本描述"},
    ],

    "lead": [
        "当模型越来越强，系统提示词该写得更详细还是更精简？Anthropic 的答案是：**砍掉 80%**。",
        "Thariq（Anthropic 技术成员）分享了一组 Claude Code 团队的最新实践。核心结论是为 Claude Opus 5 和 Fable 5 等新一代模型，可以移除超过 80% 的系统提示词，**编码评估指标没有任何下降**。核心洞察是：Claude 5 代模型自己有了更好的判断力，过去用来约束模型的「护栏」现在反而成了束缚。",
    ],

    "sections": [
        {
            "type": "h2",
            "title": "解绑 Claude：过度约束的问题",
            "paras": [
                "团队在审查内部使用记录时发现，同一个请求中经常出现互相矛盾的指令——系统提示词说「适当留下文档」，Skill 说「不要加注释」，用户请求又是另一套。",
                "Claude 仍然能理解用户意图并给出正确答案，但它需要花更多精力去处理这些重叠和冲突的信息。过去这些约束是必要的——没有它们，老模型会犯错。但新模型有了更好的判断力，可以在没有明确规则的情况下做出正确决策。",
                "此外，Claude Code 的工具生态也发生了根本变化。以前 CLAUDE.md 是记忆、信息和指导的唯一来源，现在有了 memory、artifacts 和 skills，Claude 可以用多种方式跨会话加载和共享上下文。",
            ],
            "figs": [
                {"src": "fig_conflicting_instructions.png", "caption": "系统提示词、Skill 和用户请求中的矛盾指令同时存在，Claude 需要额外处理这些冲突。"},
            ],
        },
        {
            "type": "h2",
            "title": "六大转变：从旧规则到新实践",
            "paras": [
                "团队总结了六个关键转变，这些曾经的最佳实践现在已成为神话：",
            ],
        },
        {
            "type": "h3",
            "title": "① 给规则 → 让模型判断",
            "paras": [
                "旧做法：在系统提示词中写死规则——「默认不写注释，最多一行，不要创建规划文档」。新做法：只说「写的代码要和周围代码风格一致：匹配注释密度、命名习惯和惯用法」。新模型能自己判断什么时候该写注释、什么时候不该写。",
            ],
            "figs": [
                {"src": "fig_then_vs_now.png", "caption": "从「Then: 给规则」到「Now: 让模型判断」的转变。"},
            ],
        },
        {
            "type": "h3",
            "title": "② 给示例 → 设计接口",
            "paras": [
                "旧做法：给 Claude 大量工具使用示例。新做法：设计好工具的接口本身——参数名、类型、枚举值——让接口自己表达使用方式。例如 Todo 工具的 status 字段用 pending / in_progress / completed 枚举，比写一堆示例更有效。示例反而会把模型限制在特定的探索空间里。",
            ],
            "figs": [
                {"src": "fig_examples_vs_interfaces.png", "caption": "从「给示例」到「设计接口」：Scope 工具的枚举值设计本身就是最好的说明。"},
            ],
        },
        {
            "type": "h3",
            "title": "③ 全堆在前面 → 渐进式披露",
            "paras": [
                "旧做法：把所有信息塞进系统提示词，因为不知道什么时候会用。新做法：把不常用的信息（如代码审查规范、验证流程）拆成独立的 Skill，Claude 需要时再调用。Claude Code 还实现了「延迟加载」工具——Agent 必须先通过 ToolSearch 找到工具定义才能使用，这样更多工具不会占用上下文，直到真正需要时。",
            ],
        },
        {
            "type": "h3",
            "title": "④ 重复指令 → 精简工具描述",
            "paras": [
                "旧模型有时需要在系统提示词和工具描述中重复相同的指令（上下文末尾的指令比开头的更有效）。新模型不再需要这种重复，工具的使用说明只需放在工具描述中，系统提示词中可以删除这些重复内容。",
            ],
        },
        {
            "type": "h3",
            "title": "⑤ CLAUDE.md 记忆 → 自动记忆",
            "paras": [
                "以前鼓励用户用 # 快捷键把重要信息存到 CLAUDE.md 中。现在 Claude 会自动保存与当前工作相关的记忆，不再需要手动管理。",
            ],
        },
        {
            "type": "h3",
            "title": "⑥ 简单规格 → 丰富参考",
            "paras": [
                "旧做法：用 markdown 文件存储计划和规格。新做法：Claude 可以处理更复杂的参考——HTML artifacts、测试集、甚至其他代码库中的函数。评分标准（Rubric）是另一种参考形式，它让 Claude 可以在动态工作流中启动验证 Agent 来检查输出是否符合你的品味。",
            ],
        },
        {
            "type": "h2",
            "title": "如何应用到自己的上下文工程",
            "paras": [
                "把这些原则落实到具体组件：",
                "**System Prompt**：紧密绑定产品上下文，告诉 Claude 它在什么产品中做什么事。如果你是构建自己的 Agent Harness，这是最值得投入的地方。",
                "**CLAUDE.md**：保持轻量，简要描述仓库用途，大部分精力放在代码库的坑（gotchas）上。避免写 Claude 通过看文件系统就能知道的东西。用渐进式披露——如果有独特的验证流程，创建一个验证 Skill 并在 CLAUDE.md 中引用。",
                "**Skills**：当作轻量指南，让 Claude 需要时找到信息。避免过度约束，除非是极端重要的领域。长 Skill 用渐进式披露——拆成多个文件。Skill 最适合编码你、你的团队或产品特有的观点、知识和最佳实践。",
                "**References**：用 @ 引用文件作为参考。优先使用代码形式的参考——HTML mockup 比文字描述或截图效果更好。测试集是另一种极好的参考形式。",
            ],
            "figs": [
                {"src": "fig_assembling_context.png", "caption": "组装上下文：System Prompt、CLAUDE.md、Skills 和 References 的协同工作方式。"},
            ],
        },
    ],

    "conclusion": [
        "Anthropic 已经将这套最佳实践集成到了 `claude doctor` 命令中（在 Claude Code 中运行 /doctor 即可自动调整你的 Skills 和 CLAUDE.md）。",
        "核心原则只有一个：**模型越强，约束越少。** 新一代 Claude 模型有了更好的判断力，过去用来「防止犯错」的规则现在反而可能限制它的表现。信任模型的判断力，把精力放在设计好的接口和渐进式披露上，而不是写一堆可能冲突的规则。",
    ],
    "reference_url": "https://claude.com/blog/the-new-rules-of-context-engineering-for-claude-5-generation-models",
}

# ========== 写入逻辑 ==========
os.makedirs(_article_dir, exist_ok=True)
out = os.path.join(_article_dir, "article_data.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)
print(f"✅ 写入 {out} ({len(json.dumps(DATA, ensure_ascii=False))} chars, {len(DATA['sections'])} sections)")