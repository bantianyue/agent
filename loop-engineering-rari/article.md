**Loop Engineering：2026 年 AI 构建者最需要的技能**

---

<div style="background:#e8f4fd;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:18px;">
<div style="text-align:center;margin-bottom:10px;">
<strong style="font-size:16px;color:#1a6ba0;">要点速览</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
- <strong>Loop Engineering 的定义</strong>：设计可重复的反馈循环，让 Agent 自动完成「发现→规划→执行→验证→迭代」全流程，人类不再手动驱动每一步<br><br>
- <strong>隐藏的成本问题</strong>：一个中等规模的编码 Loop 可能消耗 5 万-20 万 token，这是大多数人无法真正落地 Loop 的根本原因——廉价长上下文模型是前提<br><br>
- <strong>6 个积木块</strong>：Automations（心跳）、Worktrees（并行隔离）、Skills（项目知识复用）、Plugins（工具连接）、Subagents（制作者与检查者分离）、Memory（跨运行记忆）<br><br>
- <strong>从 Prompt Engineer 到 Loop Engineer</strong>：Prompt Engineer 优化单次输出，Loop Engineer 设计产生已验证输出的系统——这是 2026 年正在打开的技能鸿沟
</div>
</div>

**大多数人在 2026 年还在手动 Prompt Agent：打一条指令，等一个回答，自己审一遍，自己修一遍，再打下一条指令。** 人类仍然是那个循环。

下一阶段完全不同。你不是给 Agent 一条指令，而是设计一个循环——这个循环负责给 Agent 发指令、检查结果、决定下一步、持续运行直到工作通过。

这就是 Loop Engineering。

Claude Code 之父 Boris Cherny 用另一种方式说了同样的话：「我不再 Prompt Claude 了。我有一些 Loop 在运行，它们负责 Prompt Claude 并决定下一步。我的工作就是写 Loop。」

**为什么大多数人从未构建真正的 Loop**

Loop 听起来很美好，直到你看到 token 账单。

一个中等规模的编码 Loop 可能消耗 5 万-20 万 token。一个带编排器和多个专家 Agent 的 Fleet Loop 可能消耗 50 万-200 万 token。一个定时每天运行的 Loop 每周可达数百万 token。每一次重试、每一次自我修正、每一次验证步骤、每一个子 Agent，都在烧 token。

这是没人充分讨论的隐藏问题。Loop Engineering 不难是因为概念复杂——难是因为大多数人负担不起让 Agent 长时间自由运行的成本。

「你说得轻巧，你有无限的 OpenAI 额度。」这个反应很公平。

这就是为什么廉价长上下文模型至关重要。要让 Loop 每天运行，你需要：廉价的输入 token、廉价的输出 token、大上下文窗口、工具调用、JSON 输出、高并发、以及足以记住循环中早期发生了什么的上文。

没有这些，Loop 就是昂贵的实验。有了这些，Loop 就是实用的工作流。

**旧方式 vs 新方式**

过去两年，大多数人这样使用 Agent：你给指令，Agent 回答，你审查，你发现错误，你再给指令。这能工作，但无法规模化。

旧方式：你给一个 Prompt → Agent 给出输出 → 你审查输出 → 你修复薄弱环节 → 你手动重复。

新方式：你定义目标 → Loop 发现需要什么 → Loop 规划工作 → Agent 执行 → 检查者验证结果 → Loop 修复失败 → 系统在目标达成时停止。

Prompt 给 Agent 一条指令。Loop Engineering 给 Agent 一份工作。

**Loop Engineering 到底是什么**

Loop Engineering 是为 AI Agent 设计可重复反馈循环的实践。目标很简单：从「尝试」到「已验证的结果」，中间不需要人类手动驱动每一步。

基本循环有五个阶段：

**Discover（发现）→ Plan（规划）→ Execute（执行）→ Verify（验证）→ Iterate（迭代）**

如果输出通过，发布。如果失败，送回循环。这就是全部想法——不是一个完美的 Prompt，而是一个持续改进输出直到达到标准的系统。

**单 Agent vs Fleet**

Loop 有两种基本规模。

**单 Agent Loop**：一个 Agent 跑完整循环——发现需要什么、规划工作、执行任务、检查结果、在失败时改进。就像一个人自己重写草稿。适合聚焦任务、小范围、简单目标、内容草稿、Bug 修复、研究摘要。一个大脑，一个循环，自我改进。

**Fleet Loop**：更大。你给一个编排器 Agent 主要目标，它把工作拆成碎片，分发给专家 Agent。每个专家还可以为狭窄任务使用更小的子 Agent。

示例：编排器拥有使命 → 分别交给 Research 专家、Engineering 专家、QA 专家 → 每个专家再使用自己的子 Agent（Web Researcher、Code Writer + Debugger、Test Writer + Bug Tracker）。

这不是一个 Agent 独自工作，更像一个小团队端到端运行一个项目。

**开放 Loop vs 封闭 Loop**

这是最重要的实践区分。并非所有 Loop 都相等。

**开放 Loop**是探索性的。你给 Agent 一个宽泛的目标，让它自己寻找路径。这很强大，因为 Agent 能发现你没有指定的东西。但也很昂贵且混乱：可能尝试太多路径、烧太多 token、快速产生低质量输出、偏离真正目标、变得难以控制。

**封闭 Loop**是有边界的。人类先设计路径，Loop 仍然自主运行，但在清晰的规则之内。一个封闭 Loop 有：清晰的目标、定义的步骤、每一步之后的评估、停止条件、卡住时的交接点。

这是今天真正能产生回报的版本。更便宜、更可靠、输出更干净。从封闭 Loop 开始，当你的检查机制足够强时再打开它。

**一个好 Loop 的 6 个积木块**

概念上每个 Loop 有五个阶段，但实践中你需要六个积木块来让 Loop 真正工作。

**1. Automations（自动化）**——这是心跳。自动化在不需要你手动记住运行的情况下启动 Loop。例如：每天早上运行、PR 打开时运行、文件变化时运行、新工单出现时运行、持续运行直到所有测试通过。如果你还需要手动启动一切，那这个 Loop 并没有真正做足够的工作。

**2. Worktrees（工作树）**——当多个 Agent 同时编辑代码时，没有隔离就会碰撞。两个 Agent 可能编辑同一个文件，一个覆盖另一个。Worktree 给每个 Agent 自己干净的工作空间和分支，让多个 Agent 并行工作而不把仓库搞乱。

**3. Skills（技能）**——可复用的项目知识。不用每次都解释你的项目，把重要上下文写一次。好的 Skill 文件包括：愿景、架构、规则、构建步骤、测试步骤、Agent 绝对不能做的事。没有 Skills，每个 Loop 都从零开始冷启动。有了 Skills，每个 Loop 都带着累积的上下文启动。

**4. Plugins And Connectors（插件与连接器）**——一个只能看到文件的 Loop 是受限的。连接器让 Loop 触碰你的真实工具：GitHub、Slack、Linear、Jira、Gmail、Google Drive、数据库、Staging API。这是「这是一个建议修复」和「我已经开了 PR、关联了工单、看了 CI、发了更新」之间的区别。

**5. Subagents（子 Agent）**——制作者和检查者不应该是同一个模型。写代码的 Agent 在审查自己代码时往往过于宽容。写文章的 Agent 会漏掉自己的薄弱章节。用不同的 Agent 分别负责：探索、实现、审查、测试、事实核查、最终总结。当审查者不是制作者时，质量会提升。

**6. Memory（记忆）**——让 Loop 跨越多次运行持续工作。模型会忘记，但仓库不会，笔记不会，项目日志不会。记忆可以存在于：Markdown 文件、项目日志、Linear 工单、GitHub Issues、Obsidian 库、数据库、Claude Projects。一个长期运行的 Loop 需要知道尝试过什么、什么通过了、什么失败了、还有什么需要做。没有记忆，它每次从零开始。

**真实的 Loop 示例**

**编码 Loop**：读取 VISION.md + ARCHITECTURE.md → 规划下一个变更 → 编辑代码 → 运行测试 → 如果测试失败→读取错误→修复→再测试 → 如果测试通过→总结变更 → 停止。不需要人类推动每一步。Agent 自己写、测、修、验证。

**研究 Loop**：定义研究问题 → 搜索来源 → 总结发现 → 对照来源验证声明 → 对比冲突信息 → 综合最终答案 → 达到置信阈值时停止。这比要一个快速摘要好得多。

**内容 Loop**：定义主题+受众+目标 → 创建草稿 → 批评 Agent 审查草稿 → 基于批评重写 → 对照成功标准打分 → 如果分数通过→发布 → 如果分数不通过→重写。这个 Loop 把一个想法变成了内容系统。

**销售外联 Loop**：定义 ICP → 寻找匹配的线索 → 用公司数据丰富信息 → 对照标准筛选 → 个性化消息 → 质量审查 → 发送或升级给人类。同样的骨架：目标、行动、检查、修复、重复直到完成。

**Prompt Engineer vs Loop Engineer**

这是 2026 年正在打开的技能鸿沟。

**Prompt Engineer**专注于更好的指令。他们改进措辞，获得更好的单次输出。但人类仍然在运行后审查一切。人类仍然是反馈循环。

**Loop Engineer**设计反馈系统。他们决定：什么启动 Loop、Agent 需要什么上下文、可以使用什么工具、什么算成功、谁来检查工作、Loop 何时停止、结果保存在哪里。

Prompt Engineer 说：「给我写一个函数。」Loop Engineer 说：「写出来、测试它、修复直到通过、然后总结变更。」

同样的工具，不同的思维方式。最高杠杆的 AI 构建者不是在写更好的英文 Prompt——他们在设计能正确发现、规划、执行、验证和停止的系统。

**简短总结**

Loop Engineering 是从手动 Prompt 到自动化反馈循环的转变。

旧方式：一次一个任务地 Prompt Agent。
新方式：设计运行完整循环的 Loop。

你实际构建的 6 样东西：Automations（启动循环的心跳）、Worktrees（并行 Agent 无文件冲突）、Skills（每次运行复用的项目知识）、Plugins（访问真实工具）、Subagents（制作者与检查者分离）、Memory（跨运行记忆）。

2 种规模：单 Agent Loop（一个 Agent 改进自己的工作）、Fleet Loop（编排器 + 专家 + 子 Agent）。

2 种类型：开放 Loop（强大、探索性、昂贵）、封闭 Loop（有边界、可靠、可负担）。

5 个阶段：Discover → Plan → Execute → Verify → Iterate。

真正的成本问题：Loop 烧 token 很快，廉价长上下文模型让 Loop 变得实用。没有可负担的 token，大多数人永远无法超越实验阶段。

思维转变：Prompt Engineer 向 AI 要输出，Loop Engineer 设计产生已验证输出的系统。

这才是真正的解锁。别再试图写一个完美的 Prompt 了。开始构建那个让不完美的输出变得更好的 Loop。

一个可靠的 Loop 胜过一句完美的 Prompt。

---

<div style="background:#f5f0eb;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:16px;">
<div style="text-align:center;margin-bottom:8px;">
<strong style="font-size:15px;color:#8b6f4c;">结语</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
本文把 Loop Engineering 讲得很系统，从概念到积木块到真实案例都覆盖了。但有一个关键点值得追问：<strong>Loop 的调试成本谁来承担？</strong> 当你的 Fleet Loop 跑了一个小时、烧了 50 万 token、输出却是垃圾时，你很难知道是哪个环节出了问题——是 Orchestrator 拆错了任务、Specialist 执行跑偏、还是 Checker 的验证标准太低？Loop Engineering 的下一个前沿不是设计 Loop，而是<strong>可观测性</strong>——让 Loop 的行为可追踪、可回放、可调试。<br><br>
另外，本文提到的 6 个积木块中，Skills 和 Memory 是当前最容易被低估的两个。大多数人把 Skills 当成「可选的 README」，把 Memory 当成「日志文件」——但它们是 Loop 从「一次性实验」进化为「持续运行系统」的关键区别。没有 Skills，每个 Loop 冷启动；没有 Memory，每个 Loop 失忆。
</div>
</div>

---

<span style="font-size:12px;color:#888888;">参考：Loop Engineering: The AI skill every builder needs in 2026</span>
