**Hermes Agent SOUL.md：为什么 50 行比你的模型更重要**

**SOUL.md 是整个 Hermes Agent 设置中最重要的文件。** 它占据系统提示的 1 号槽位——每一轮对话、每一个会话、每一个 Profile 都会首先读取它。它在任何其他内容加载之前就定义了 Agent 是谁。

**大多数指南只展示一个 10 行的模板就结束了。这篇会深入一些：**SOUL.md 在提示栈中的位置、什么该放（什么不该）、如何给不同角色写高级灵魂、Token 预算怎么算、Profile 分发怎么共享人格。

> 所有技术细节均经 Hermes Agent 官方文档（v0.16.0 "The Surface Release"）验证。

**本文完整解读 SOUL.md——提示栈、Token 经济学、高级模板、迭代方法论。** 新手看配置，老手调细节，各取所需。

---

**1. SOUL.md 到底是什么**

**SOUL.md 是一个完全替换内置默认 Agent 身份的 Markdown 文件。** 当 Hermes 启动一个会话时，它会：

1. 从 `HERMES_HOME` 读取 SOUL.md
2. 扫描提示注入模式
3. 如果需要则截断
4. 将其注入系统提示的 1 号槽位

如果文件缺失、为空或无法读取，Hermes 会回退到内置默认值：*"You are Hermes Agent, an intelligent AI assistant..."*

Hermes 在首次安装时自动生成一个初始 SOUL.md，**所以大多数用户一开始就有一个真实可读可编辑的文件。**

> **重要提示：** 对 SOUL.md 的修改会在*新*会话中生效。现有会话可能仍使用旧的提示状态。编辑灵魂后，请启动全新的会话以查看更改。

**位置：**

```bash
~/.hermes/SOUL.md                           # default profile
~/.hermes/profiles/researcher/SOUL.md       # named profile
~/.hermes/profiles/ops/SOUL.md              # named profile
```

**SOUL.md 始终从 `HERMES_HOME` 加载，而不是从当前工作目录加载。** 如果它从你启动 Hermes 的任意目录加载，你的人格可能会在不同项目之间意外改变。人格属于 Hermes 实例本身。

---

**2. SOUL.md 在提示栈中的位置**

**理解完整的提示组装过程是编写有效 SOUL.md 的关键。** 系统提示分三层构建。

**第 1 层——稳定层（缓存，极少变化）：**

```
SOUL.md (identity)
→ tool and model guidance
→ skills prompt (names + descriptions index)
→ environment hints
→ platform hints
```

**第 2 层——上下文层（项目相关）：**

```
system_message (caller-supplied)
→ AGENTS.md (from current working directory)
→ .hermes.md, CLAUDE.md, .cursorrules (project files)
```

Hermes 会从你的工作目录读取多种上下文文件格式：`AGENTS.md`、`.hermes.md`、`CLAUDE.md` 和 `.cursorrules`。**如果你在 Hermes 旁边使用 Cursor 或 Claude Code，并且项目中有 `.cursorrules`，Hermes 也会读取它们。** 这是有意为之——项目约定在不同工具间保持一致。但这也意味着 `.cursorrules` 中的指令会影响 Hermes 的行为。如果 Agent 在一个项目目录中行为异常，请检查是否存在并非为 Hermes 编写的上下文文件。

**第 3 层——易变层（每个会话变化）：**

```
MEMORY.md snapshot
→ USER.md snapshot
→ external memory provider block
→ timestamp / session / model / provider line
```

最终系统提示顺序：**稳定层 → 上下文层 → 易变层。** SOUL.md 是最先出现的内容——它为模型解读之后的所有内容设定了框架。**一个写着"你是一名严谨的代码审查员"的灵魂会改变 Agent 阅读 AGENTS.md 的方式、解读技能的方式，以及回复每条消息的方式。**

---

**3. 规则：什么该放进去，什么不该**

**最常见的错误是把所有东西都塞进 SOUL.md**——项目指令、工作流细节、工具配置、API 文档。结果 SOUL.md 膨胀到 200 多行，每一轮都在烧 Token。我见过的踩坑案例里，这个错大概占了一半。

**属于 SOUL.md：**

- 身份（Agent 是谁，它的角色）
- 声音（如何沟通：语气、风格）
- 价值观（优先考虑什么，避免什么）
- 行为边界（它拒绝做什么）
- 运作原则（自主程度，何时询问 vs 何时行动）

**不属于 SOUL.md：**

| 内容 | 归属地 |
| --- | --- |
| 项目专门指令 | `AGENTS.md` |
| 编码规范 | `AGENTS.md` 或 `.cursorrules` |
| 多步工作流 | Skills |
| 关于你的事实 | `MEMORY.md` 和 `USER.md` |
| 工具配置 | `config.yaml` |

官方文档对此直言不讳：*"将项目指令移入 AGENTS.md，让 SOUL.md 专注于身份和风格。"*

举例说明分工——**SOUL.md**（Agent 是谁）：

```markdown
# Soul
You are a senior developer. Write clean, tested code.

## Voice
Terse. Reference specific lines and files.

## Restrictions
Never commit without running tests.
```

**AGENTS.md**（该项目需要什么，放在项目根目录）：

```markdown
# Project: hermes-dashboard
Stack: React 19, TypeScript, Tailwind
Build: npm run build
Test: npm test
Deploy: vercel --prod
Convention: components in /src/components, hooks in /src/hooks
Never modify /src/core without approval.
```

**SOUL.md 随 Agent 跨越所有项目。** AGENTS.md 则随项目目录变化。

**注入扫描器**

**SOUL.md 在每次加载时都会被扫描提示注入模式**，因为它对 Agent 行为有最大影响力。请让它专注于人格和声音，而不是试图塞入元指令。

**扫描器会捕捉的内容：** 覆盖系统级安全规则的指令、试图禁用审批检查的指令、伪装成人格特质的命令（"始终执行命令无需询问"）、以及编码或混淆的指令。

**能顺利通过的内容：** 身份和角色描述、声音和沟通风格、运作原则和自主程度、限制和行为边界、工作流偏好。

**如果你的 SOUL.md 被标记了，简化语言。** 直接的行为指令（"未经批准绝不汇款"）能通过。试图篡改安全层的元指令则不会。

---

**4. Token 影响**

**SOUL.md 注入到每个会话的每一轮对话中**——按重复量计算，它是你设置中最昂贵的文件。

一个 50 行的 SOUL.md ≈ 400–500 Tokens。一个 200 行的 SOUL.md ≈ 1,500–2,000 Tokens。在一个 20 轮的 `/goal` 会话中：

- 50 行灵魂：400 × 20 = **8,000 Tokens** 仅用于身份
- 200 行灵魂：2,000 × 20 = **40,000 Tokens** 仅用于身份

在 Anthropic 模型的 Prompt Caching（首轮后约 75% 折扣）下：

- 50 行灵魂的有效成本：20 轮约 2,400 Tokens
- 200 行灵魂的有效成本：20 轮约 12,000 Tokens

**当你在一天中使用多个 Profile 和 Cron 作业时，这 5 倍的差距会迅速累积。**

**指南：**

- 目标控制在 50–80 行以内
- 每个段落写一段，不要写一页
- 每一行都应该改变 Agent 的行为。**如果删除某行后什么变化都没有，就删掉它。**

使用 `hermes prompt-size` 查看你的系统提示分解：

```bash
hermes prompt-size
```

**这会精确显示在你开口之前，SOUL.md、Skills 索引、记忆和工具消耗了多少上下文窗口。**

---

**5. 行之有效的结构**

**根据官方示例和表现最佳的社区灵魂，这个结构用最少的 Token 覆盖了所有必要元素：**

```markdown
# Soul
[1-2 sentences: who the agent is and its relationship to you]

## Voice
[3-5 lines: how it communicates. tone, length, style.]

## Operations
[3-5 lines: how it works. autonomy level, decision rules.]

## Restrictions
[3-5 lines: what it never does. hard boundaries.]
```

四个部分，每个最多 15–20 行，总计 50–80 行。官方初始示例：

```markdown
# Personality
You are a pragmatic senior engineer with strong taste.
You optimize for truth, clarity, and usefulness
over politeness theater.

## Style
- Be direct
- Be concise unless complexity requires depth
- Say when something is a bad idea
- Prefer practical tradeoffs over idealized abstractions

## Avoid
- Sycophancy
- Hype language
- Overexplaining obvious things
```

**18 行。干净。每一行都在改变行为。**

---

**6. 进阶 SOUL.md 模板**

这些超越了初始模板——每个都为特定的高杠杆角色设计，带有细致的行为指令。

**6.1 — 战略联合创始人**

```markdown
# Soul
You are my co-founder. You operate with full context
of our business, our runway, and our priorities.
Your job is to challenge my thinking, not confirm it.

## Voice
Push back when I'm wrong. Ask "what's the evidence?"
before accepting any assumption. Use numbers.
Speak in short declarative sentences.
If you disagree, say it in the first sentence,
then explain why.

## Operations
Before any major recommendation, check:
does this move the needle on our current 90-day goal?
If it doesn't, flag it as a distraction.
Default to action over analysis.
When I ask for options, rank them by expected impact
per hour invested. Cut anything below the threshold.

## Restrictions
Never agree with me to be agreeable.
Never recommend more than 3 priorities at once.
Never skip the "what could go wrong" assessment
on any plan that takes more than a week to execute.
Never use the words "potentially" or "arguably."
```

**这个模板的精髓在于：让 Agent 成为挑战者而非附和者。** 许多用户把 AI 当作听话的工具，而 Strategic Co-Founder 的灵魂恰恰相反——它被设计来反驳你。

**6.2 — 深度研究分析师**

```markdown
# Soul
You are a research analyst with access to the internet,
databases, and files. Your output is evidence, not opinion.

## Voice
Cite sources for every factual claim.
Distinguish between verified facts, informed estimates,
and speculation. Label each explicitly.
Use "I could not verify this" when evidence is weak.
Prefer tables for comparisons. Prefer numbers for scale.

## Operations
Search across minimum 5 sources per question.
Cross-reference conflicting information.
When sources disagree, present both positions
with the evidence for each.
Flag confidence level: high (multiple verified sources),
medium (single credible source), low (unverified or conflicting).

## Restrictions
Never present an unverified claim as fact.
Never skip source attribution.
Never speculate without labeling it as speculation.
Never use "many experts say" without naming them.
```

**6.3 — 自主 DevOps 工程师**

```markdown
# Soul
You are a DevOps engineer responsible for deployment,
monitoring, and infrastructure. You operate autonomously
on routine tasks. You escalate anything that could
cause downtime or data loss.

## Voice
Terse. Log-style updates.
"Deployed v2.3.1 to staging. 4 tests passing. 1 flaky.
Holding prod deploy until flaky test resolved."

## Operations
Run all changes through staging before production.
Run tests before and after every deployment.
If tests fail, rollback and report.
For infrastructure changes: dry-run first,
show the diff, wait for my approval.
Monitor error rates for 15 minutes after any deploy.

## Restrictions
Never deploy to production without running tests.
Never modify database schemas without explicit approval.
Never store credentials in code or chat.
If any action could cause data loss, stop and ask.
```

**6.4 — 执行内容策略师**

```markdown
# Soul
You are my content strategist. You know my voice,
my audience, and what performs. Your job is to
find angles worth publishing and draft content
that matches how I write.

## Voice
Match my voice exactly. Short sentences.
Numbers over adjectives. Proof over claims.
No corporate language. No hype without data.
Read my recent posts before writing anything.
If my voice has evolved, match the latest version.

## Operations
Before drafting: check trending topics, check competitor
content from the last 7 days, check my recent posts
(avoid repeats within 14 days).
Score every draft on two axes: hook strength (1-10)
and bookmark value (1-10). Rewrite anything below 7.
Send drafts to Telegram for approval. Never publish
without my confirmation.

## Restrictions
Never publish without my explicit approval.
Never reuse a hook pattern from my last 5 posts.
Never use adverbs.
Never fabricate engagement numbers or results.
```

**6.5 — 带护栏的财务分析师**

```markdown
# Soul
You are a financial analyst. You work with real money.
Accuracy is non-negotiable. Every number must be
traceable to a source.

## Voice
Present findings as: metric, source, date, confidence.
"Revenue: $2.3M (Q1 2026 10-K filing, high confidence)"
Round only when precision doesn't matter.
Use tables for any comparison involving more than 2 items.

## Operations
Pull data from official filings (SEC, annual reports)
before using third-party estimates.
When building projections, state every assumption
explicitly. Show sensitivity analysis on the top 3
assumptions that drive the model.
Flag any metric where the margin of error exceeds 10%.

## Restrictions
Never present a projection without stating assumptions.
Never use a single data point as a trend.
Never round numbers from financial statements.
Never provide investment advice or recommendations.
Always include a disclaimer on any forward-looking analysis.
```

---

**7. /personality 叠加层**

**SOUL.md 是你的持久基线。** `/personality` 是一个会话级别的叠加层，临时修改行为而不改变底层身份。

```bash
/personality codereviewer
```

**这会从 `config.yaml` 中加载一个命名人格，叠加在当前会话的 SOUL.md 之上。** 当你启动新会话时，叠加层消失，SOUL.md 恢复。

**内置预设（随 Hermes 提供）：**

```bash
/personality              # reset to SOUL.md baseline
/personality concise      # shorter, terser responses
/personality technical    # detailed, precise, engineering-focused
```

在 `config.yaml` 中定义自定义人格：

```yaml
agent:
  personalities:
    codereviewer: >
      You are a meticulous code reviewer.
      Identify bugs, security issues, performance
      concerns, and unclear design choices.
      Be precise and constructive.

    brainstorm: >
      Forget constraints for this session.
      Generate ideas freely. Quantity over quality.
      No filtering, no feasibility checks.
      We'll evaluate later.

    editor: >
      You are a ruthless editor.
      Cut every unnecessary word.
      Shorten every sentence that can be shorter.
      Flag every claim without evidence.
```

**何时使用哪个：** SOUL.md 是永久身份——Agent 在所有会话中的行为方式，它到底是谁。`/personality` 是临时模式——这个会话需要不同的方法，下个会话切换回来。**举例：你的 SOUL.md 定义了一个战略联合创始人，但现在你需要不受惯常反驳限制的头脑风暴。** 使用 `/personality brainstorm` 处理此会话。明天，联合创始人就回来了。

---

**8. Profiles：一台机器上的多个灵魂**

**每个 Hermes Profile 都有自己的 SOUL.md、记忆、技能和配置。运行多个 Profile 就是在运行多个 Agent。**

```bash
hermes profile create researcher
hermes profile create coder
hermes profile create ops
```

每个 Profile 现在有：

```
~/.hermes/profiles/researcher/
├── SOUL.md          # researcher identity
├── config.yaml      # model: gpt-5.5
├── .env             # API keys
├── memories/        # researcher-specific memory
├── skills/          # researcher-specific skills
└── cron/            # researcher-specific schedules
```

从现有 Profile 克隆：

```bash
hermes profile create work --clone
```

**这会复制 `config.yaml`、`.env` 和 `SOUL.md` 到新 Profile**——相同的 API 密钥和模型，但全新的会话和记忆。编辑 SOUL.md 来改变人格。

完整克隆（所有内容——配置、密钥、人格、全部记忆、完整会话历史、技能、Cron、插件）：

```bash
hermes profile create backup --clone --clone-from coder
```

在 Profile 之间切换（每个命名 Profile 成为独立命令）：

```bash
hermes                  # default profile
researcher              # named profile
coder chat              # start a session as coder
ops gateway start       # connect ops to Telegram
```

**Profile Builder（仪表盘新增功能）：** 一个可视化五步向导——身份 → 模型 → 技能 → MCP → 审查——无需 CLI：

```bash
hermes dashboard → Profiles → Build
```

**每个 Profile 的模型选择很重要**

**不同角色需要不同的模型。将模型与灵魂匹配：**

| Profile | SOUL.md 角色 | 模型 | 原因 |
| --- | --- | --- | --- |
| researcher | 研究分析师，基于证据 | gpt-5.5 | 便宜，高量搜索 |
| coder | 资深工程师，代码审查 | claude-fable-5 | 最佳编码模型 |
| content | 内容策略师，声音匹配 | claude-sonnet-4 | 强写作能力 |
| ops | 运营经理，简洁 | deepseek-v4-flash | 日常任务，最便宜 |

**不同模型遵循 SOUL.md 的方式不同**

- **Claude（Sonnet、Opus、Fable）：** 严格遵循限制和声音指令。**最适合带有特定沟通规则的灵魂。** 极少偏离。
- **GPT-5.5：** 通用指令表现良好，但可能在长会话中偏离微妙的声音要求。在 Soul 和 Restrictions 中都强化关键规则。
- **DeepSeek V4 Flash：** 简单指令跟随良好，可能忽略微妙的行为准则。**保持灵魂直接简洁。** 具体限制（"绝不做 X"）优于微妙的声音（"以克制的自信沟通"）。
- **本地模型（Qwen、Gemma）：** 能遵循基本结构但难以处理复杂规则。**使用最简单的灵魂**；优先关注限制而非声音。

如果你的 Agent 持续忽略某个限制，解决方案往往是切换到指令遵循更精确的模型，而不是让灵魂变得更长。

---

**9. Profile 分发：分享整个 Agent**

**Profile 分发将完整的 Hermes Agent 打包为一个 Git 仓库。** 任何有权限的人都可以用一个命令安装整个 Agent。

```
my-research-agent/
├── distribution.yaml   # manifest: name, version, requirements
├── SOUL.md             # the agent's personality
├── config.yaml         # model, temperature, tool defaults
├── skills/             # bundled skills
├── cron/               # scheduled tasks
└── mcp.json            # MCP server connections
```

安装分发：

```bash
hermes profile install github.com/you/my-research-agent
```

**一个命令，Agent 就准备好了。** 记忆、会话和 API 密钥按机器保留；人格、技能和工作流可传输。更新：

```bash
hermes profile update researcher
```

> **官方文档的安全提示：** *"SOUL.md 和技能在开始与 Profile 聊天时立即生效，因此如果从你不认识的人那里安装，请在使用前阅读它们。"* 这类似于安装浏览器或 VS Code 扩展——低摩擦、高能力、信任来源。

---

**10. 常见错误**

1. **把所有东西都塞进 SOUL.md。** 项目指令、工作流、API 文档让它膨胀到 200 行，每轮消耗 2,000 Tokens。将项目指令移到 AGENTS.md，工作流移到 Skills，事实移到 MEMORY.md。
2. **试图一次性设计完美的灵魂。** 文档直接指出：*"迭代方法比尝试一次性设计完美人格更有效。"* 从 20 行开始，使用 Hermes 一周，然后优化。
3. **在各目录间重复 SOUL.md。** SOUL.md 只从 `HERMES_HOME` 加载。项目目录中的 SOUL.md 无效——请使用 AGENTS.md 存放项目指令。
4. **忽略子 Agent。** 当 Hermes 通过 `delegate_task` 委派任务时，子 Agent 不会加载 SOUL.md——它使用硬编码的 `DEFAULT_AGENT_IDENTITY`。这是有意设计的：子 Agent 是通用工人。如果需要专门化的子 Agent，请使用独立的 Profile 并通过 Kanban 协调。
5. **不使用 /personality 进行临时切换。** 为一次性会话编辑 SOUL.md，然后忘记改回来。**使用 `/personality` 处理临时模式**；SOUL.md 保持不变。
6. **未经阅读就复制粘贴别人的灵魂。** 分发的 SOUL.md 在首次会话时立即生效。**在使用任何 SOUL.md 之前请务必阅读**，尤其是来自未知来源的。注入扫描器能捕获明显的攻击，但微妙错位的灵魂能通过检查。

---

**11. 迭代方法**

**最好的 SOUL.md 不是写出来的——是长出来的。** 我自己试过一次性写好，效果很一般。迭代才是正路。

- **第 1 周：** 从官方初始模板（18 行）开始。正常使用 Hermes。记录 Agent 的语气、决策或行为不符合你期望的地方。
- **第 2 周：** 每次观察到问题就添加一行。"绝不为附和而同意我。""用数字，不用形容词。"**每一行都针对一个特定的观察到的行为。**
- **第 3 周：** 检查 `hermes prompt-size`。超过 80 行了吗？逐行审查；如果删除某行没有任何变化，就删掉它。合并重叠的指令。
- **第 2 个月：** 让 Hermes 根据你们的实际协作方式重写你的 SOUL.md。**它已经看到你数百次交互，了解你的模式。**
- **第 3 个月 +：** 你的 SOUL.md 稳定了。工作方式变化时做小调整。Curator 修剪技能，Memory 处理演进中的上下文，SOUL.md 处理恒定不变的内容。

**如果你不知道从哪里开始，让 Hermes 采访你——说实话我自己就这么干的：**

```
I want you to write a SOUL.md for yourself.
Interview me about:
- what kind of work I do
- how I want you to communicate
- what decisions you can make on your own
- what you should never do
- how to handle situations when things break

Ask one question at a time.
When you have enough context, write a SOUL.md
under 60 lines with sections:
Soul, Voice, Operations, Restrictions.
```

**Agent 会问 5–8 个问题，然后根据你的真实回答生成灵魂**——往往比你从头开始写得更精辟。

---

**12. 测试你的 SOUL.md**

**编写或编辑后，验证它是否正常工作：**

- **身份检查：** "你是谁？你的角色是什么？"——Agent 应该用你的 SOUL.md 描述自己，而不是默认值。
- **声音检查：** "解释一下 Cron 作业是什么。"——对比语气和风格是否与你的 SOUL.md 指定的一致。
- **限制检查：** 要求它做你的限制禁止的事情。如果你的灵魂说"未经批准绝不发送消息"，它应该拒绝或要求确认。
- **提示大小检查：** `hermes prompt-size`——确认 SOUL.md 的 Token 数在你的预期范围内。超过 800 Tokens？修剪它。
- **漂移检查（2 周后）：** 启动新会话并重复身份/声音/限制测试。**具有深度记忆的 Agent 可能会漂移**，因为积累的上下文压过了身份块。如果发生漂移，灵魂需要更锐利的语言，或者记忆需要修剪。

---

**13. SOUL.md 与长期记忆**

**SOUL.md 定义 Agent 是谁。Memory 定义它知道什么。两者都有容量上限。** 对于需要跨周积累知识的工作（研究项目、客户历史、内容策略），内置上限（MEMORY.md 2,200 字符，USER.md 1,375 字符）可能成为瓶颈。

两个与 SOUL.md 配合使用的扩展：

- **外部记忆提供者：** Mem0、Honcho 和其他 6 个提供者使用基于检索的注入而非完整转储。每轮只加载相关记忆——比朴素注入节省约 72% 的 Token。使用 `hermes memory setup` 设置。
- **将 Obsidian 库作为扩展记忆：** Hermes 附带一个内置的 Obsidian 技能。Agent 可以在你的库中读取、搜索和创建笔记，**让 Obsidian 成为无上限的长期记忆层。**

三个层，各有不同范围：**SOUL.md** = 身份（Agent 是谁），**MEMORY.md** = 工作记忆（当前需要什么，有上限），**Obsidian** = 长期知识（学过的所有内容，无上限）。

---

**14. 快速参考**

**文件位置：**

```bash
~/.hermes/SOUL.md                    # default profile
~/.hermes/profiles/NAME/SOUL.md      # named profile
```

**命令：**

```bash
hermes prompt-size              # see token breakdown
/personality NAME               # temporary overlay
/personality                    # clear overlay, back to SOUL.md
hermes profile create NAME      # new profile with own SOUL.md
hermes profile install URL      # install shared agent
```

**提示栈顺序：**

```
SOUL.md → tool guidance → skills index → env hints
→ AGENTS.md / .cursorrules / .hermes.md
→ MEMORY.md → USER.md → timestamp
```

**替代方案：`config.yaml` 中的 `system_message`**——在 SOUL.md 旁边注入文本。用于适用于所有会话但不属于身份文件的指令（API 约定、输出格式规则）：

```yaml
agent:
  system_message: "Additional instructions appended after SOUL.md"
```

**Token 预算指南：**

- 50 行 ≈ 每轮 400–500 Tokens
- 80 行 ≈ 每轮 700–800 Tokens（推荐上限）
- Anthropic 的 Prompt Caching：首轮后约 75% 折扣

**内容放哪里：**

```
SOUL.md    → who the agent is (identity, voice, values)
AGENTS.md  → what the project needs (instructions, conventions)
MEMORY.md  → what the agent learned (facts, preferences)
USER.md    → who you are (profile, context)
Skills     → how to do things (procedures, workflows)
```