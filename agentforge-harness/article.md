每个人都在用 Agent 构建东西。几乎没人讨论 Agent 里面到底是什么。不是模型。是模型外面的 Harness。

Mohit Goyal 花了几个月从零用 Python 构建了一个 AgentForge——流式 Agent 循环、类型化工具调用、审批门控、提示注入边界、上下文压缩、MCP 集成、子 Agent、持久化和完整测试套件。开源可安装：`pip install agentforge-harness`

核心教训：

> Agent 不是模型。Agent 是控制模型如何观察、行动、重试、记忆和停止的运行时。

模型大概占工程的 20%。另外 80% 是包裹它的东西。

---

## 1 Session 运行时

聊天历史不够。Agent 需要真正的运行时容器。

AgentForge 的第一个真实对象不是模型客户端，而是 session。它在第一次调用之前就构建了模型的世界——注册 MCP 工具、发现技能、构建上下文管理器。模型不是自己发现世界的。Harness 决定了哪些工具存在、哪些技能可见、哪种操作模式塑造上下文——在第一个 token 生成之前。

---

## 2 Agent 循环

大多数人画 ReAct 图时 skipped 的部分：真正的循环必须处理上下文压力、模型失败、回退模型、工具预算、plan/build 模式、重复行为、流式输出和崩溃检查点。

AgentForge 有 LoopDetector，监视跨回合的重复工具调用。如果 Agent 连续三次调用相同路径的 read_file 而没有中间编辑——那是循环，不是进展。Harness 检测到后强制模型生成最终答案。

断路器在模型层面工作。如果某个提供商持续返回错误，该模型的电路打开，Harness 回退到链中下一个模型。

---

## 3 工具设计

工具设计就是 Agent 设计。模型只能通过你给它的行动空间行动。

AgentForge 的每个工具返回结构化 ToolResult，包含：success、status、output、error、summary、artifacts、next_actions、recovery_hint。

后四个字段是关键。summary 用自然语言告诉模型发生了什么。artifacts 告诉它什么变了。next_actions 告诉它安全的后续操作。recovery_hint 告诉它如何避免盲目重试。

每个工具结果——成功或失败——在到达模型前都经过清理、脱敏、提示注入标记和 hooks。

---

## 4 安全审批

模型不是对代码审查负责的正确位置。Harness 分类行动、应用配置的策略，在命令运行之前批准、拒绝或询问用户。

Plan 模式下，write 工具在注册表层面被过滤。模型没有接收写工具，即使它尝试也无法调用。

---

## 5 提示注入

每一个文件读取都是 prompt 输入。仓库文件可以包含指令。Shell 命令可以输出指令。MCP 服务器可以返回指令。

AgentForge 的工具观察结果被包裹为不可信内容——每个观察结果明确标记来自特定来源的数据。这是一个结构性而非对话性的边界。

---

## 6 上下文管理

在小规模，你追加一切。在真实规模，那变成一个包含 10 轮前陈旧工具输出的混乱转录。

AgentForge 追踪 token 估计，在上下文快满时警告，剪枝旧工具输出，压缩早期历史同时保留最近回合。近期的 5 个回合是高分辨率工作记忆，更早的回合变成延续摘要。

---

## 7 技能

不是每个指令都需要总是加载。AgentForge 支持渐进式披露：索引元数据，只有在技能被明确选择时才加载完整正文。

---

## 8 MCP 与子 Agent

外部工具命名空间化。一个文件系统的 read_file 变成 filesystem__read_file。MCP 工具不绕过注册表——完整管道仍然适用。

子 Agent 是工具。父 Agent 传递目标，子 Agent 用受限配置、允许的工具、最大回合数和硬超时运行。内置子 Agent 默认为只读：explorer、debugger、code reviewer。

---

## 9 持久化与测试

原子写入、所有者权限、崩溃安全替换。278 个测试覆盖配置加载、session 状态、plan 模式过滤、上下文管理、循环检测、工具 schema、文件工具行为、patch 验证、shell 工具策略、输出卫生、提示注入包装。

全部在隔离的 home 目录下运行，不需要真实模型调用。大部分 Agent 可靠性来自与模型智能无关的确定性 Harness 行为。

---

## 10 一点观察

**这篇文章是 Harness Engineering 理论的最佳实践验证。** 之前那篇（sairahul1）从概念层面讲了 5 个工件和 5 条原则，Mohit 用真实代码验证了每一条。每段 Python 代码都对应一个抽象原则——approval 层对应"安全不靠提示词"、ToolResult 的 next_actions 对应"上下文优于指令"、技能渐进式披露对应"一次只加载需要的内容"。

**read_file 的行号和 trailing-newline 检查展示了什么叫做"好的工具设计"。** 一个 before/after 的例子：没有行号→模型从内容推测位置→patch 可能对错位置。有行号→精确编辑。trailing-newline 检查直接对应 patch 能否干净应用。小细节决定模型行为。

**278 个无需模型调用的测试——这是被严重低估的观点。** 大部分人认为 Agent 难测因为输出不确定。但实际上大部分可靠性来自确定性 Harness 行为。测试边界而非 prose——这是从"提示词工程"到"系统工程"的标志性思维转变。

---

<span style="font-size:12px;color:#888888;">参考：I Built an Agentic Harness From Scratch</span>
