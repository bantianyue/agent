**别再写 Prompt 了，开始设计 Loop**

> Boris Cherny（Claude Code 之父）说他已经不再给 Claude 写 prompt 了，他写的是 loop。Peter Steinberger 从另一个角度说了同样的话。Addy Osmani 把 loop 拆成了六个部件。这篇文章把这三个人串起来，告诉你为什么 prompt 是过去时，loop 才是现在时。

---

<div style="background:#e8f4fd;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:18px;">
<div style="text-align:center;margin-bottom:10px;">
<strong style="font-size:16px;color:#1a6ba0;">要点速览</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
- <strong>Prompt 给你一次响应，Loop 给你一个系统</strong>：你合上电脑后它还在跑。Boris Cherny 的工作不再是写 prompt，而是写 loop<br><br>
- <strong>Loop 的六要素</strong>：Automation、Worktree、Skill、Connector、Sub-agent、Memory。每个工作 loop 是这六者的某种组合<br><br>
- <strong>从一条触发开始</strong>：一个每天早上 8 点读 CI 失败、写 findings 到 markdown 的 cron job，就是一个完整的 loop<br><br>
- <strong>Writer 和 Checker 必须分开</strong>：写代码的模型给自己打分太宽容。Evaluator-Optimizer 模式——一个生成，一个用客观标准批评<br><br>
- <strong>硬停止条件</strong>：不要相信 Agent 说"完成了"。测试套件通过、构建成功、CI 通过——这些才是真的
</div>
</div>

**一个 prompt 给你一次响应。一个 loop 给你一个在你合上电脑后还在工作的系统。**

Boris Cherny，Claude Code 之父、Anthropic 的 Claude Code 负责人，说得直白：他不再给 Claude 写 prompt 了。他有 loop 在跑，这些 loop 负责给 Claude 写 prompt 并决定下一步做什么。**他的工作就是写 loop。**

Peter Steinberger 从另一个角度说了同样的话：你不应该再给编程 Agent 写 prompt 了，你应该设计 loop，让 loop 去给你的 Agent 写 prompt。杠杆点已经移动了。不再是雕琢一条完美的消息。**是构建一个替你发消息、审查结果、决定下一步的系统。**

一个 loop 就是一个递归目标。你定义一个目的，Agent 对着它迭代，loop 持续运行直到一个真正的停止条件被满足。Agent 在每次运行之间会忘记一切。**Loop 不会。** 这一个事实就是整个架构。

---

**What a Loop Actually Is**

Google 工程师 Addy Osmani 写了一篇文章给这个实践命了名。他把一个 loop 拆成六个部分：**Automation、Worktree、Skill、Connector、Sub-agent、Memory**。每个工作 loop 都是这六者的某种组合。

**Automation** 是让 loop 成为 loop 而不是一次性运行的东西。一个定时任务、一个 cron job、一个 webhook、或者 Claude Code 内部的一个 hook——不需要你输入任何东西就能触发。Agent 在你问之前就发现工作并分类了。

**Worktree** 防止并行 Agent 互相踩踏。如果两个 Agent 同时碰同一个文件，就会冲突。Git worktree 给每个 Agent 一个独立的仓库副本。

**Skill** 是 Agent 读取的操作手册，而不是每次从头告诉它。**Memory** 是磁盘上的一个状态文件，通常是 markdown，在两次运行之间存活。Agent 会忘记，文件不会。

---

**Start With One Trigger**

每个 loop 都从某个不需要你就能触发的东西开始。最简单的版本是一个按计划运行 Claude Code prompt 的 cron job。下一个版本是一个 hook——当特定事件发生时自动运行的脚本，比如一次 commit 或文件变更。

**选一个你当前手动做的重复性任务，把触发条件变成第一块积木。**"每天早上 8 点，读取昨天的 CI 失败、打开的 issue 和最近的 commit，把发现写到一个 markdown 文件里。"这一个 automation 本身就是一个完整的、能工作的 loop。

**不要在第一天就试图构建完整的六部件系统。** 一个能写一个状态文件的 automation，已经比一百个精心制作的 prompt 更有杠杆——因为它不需要你就能运行。

---

**Give the Loop a Memory File**

创建一个 markdown 文件，叫它 `STATE.md` 或 `PROGRESS.md`，放在 loop 的每次迭代都能读写的地方。这个文件是 loop 唯一的记忆。Agent 需要从上次停下的地方继续所需的一切都在这里。

每次运行开始时，Agent 先读这个文件。每次运行结束时，它写回发生了什么以及下一步做什么。这就是 **PROGRESS.md 模式**，它是任何 loop 中最重要的文件。没有它，每次运行都从零开始，不管之前跑了多少次。

把文件组织成清晰的段落：上次运行做了什么、正在做什么、什么被阻塞了、下一步试什么。保持简短。**一个 Agent 需要读 2000 行的记忆文件，比没有记忆文件更糟糕。**

---

**Split the Writer From the Checker**

写代码的模型，用 Osmani 的话说，给自己打分太宽容了。一个自己写然后自己审查的 Agent，会比自己应该的更频繁地把自己的工作标记为完成。

修复方案是 **Evaluator-Optimizer 模式**，来自 Anthropic 自己的工程文档《Building Effective Agents》：一个 Agent 生成，第二个 Agent 对照客观标准批评，loop 重复直到检查通过。检查必须基于真实的东西失败：测试套件、类型检查器、构建命令、linter。

**让第二个 Agent 说"审查一下"而没有客观信号，只是多了一个乐观主义者。** 它更可能同意第一个 Agent 而不是反对。验证者需要一个硬关卡，不是一个观点。

---

**Isolate Parallel Work With Worktrees**

一旦你让多个 Agent 对着同一个代码库运行，隔离就不再是可选的。运行 `git worktree add ../agent-1-branch` 给每个 Agent 一个指向自己分支的独立工作目录。这防止两个 Agent 同时编辑同一个文件并破坏对方的修改。

一个典型的并行设置：一个子 Agent 探索并写计划，第二个子 Agent 在自己的 worktree 里按计划实现，第三个子 Agent 在另一个 worktree 里对照测试验证实现。每个 Agent 只看到自己的副本。

这也是 loop 从"一个任务在后台运行"扩展到"一整个任务流水线同时运行"的地方——每个独立，每个在完成后向共享记忆文件报告。

---

**Set a Hard Stop Condition**

一个没有真正退出条件的 loop 会安静地失败。工程师 Geoffrey Huntley 把它记录为 **"Ralph Wiggum loop"**：一个本该在完成时发出完成信号的 Agent 过早地发出了它，loop 相信一个半成品工作已经完成就退出了。

你的停止条件需要能被 Agent 自己声称之外的东西检查。"测试套件通过""构建成功""关联的 ticket 带着通过的 CI 移到 Done"是真正的停止条件。**"Agent 说它完成了"不是。**

不管你的主要停止条件是什么，设置一个最大迭代次数作为后盾。大多数 loop 十到二十次迭代是合理的上限。如果 loop 在没有满足真正停止条件的情况下达到了上限，它应该停下来标记为待审查，而不是继续运行。

---

**Wire In a Human Review Checkpoint**

不是每个 loop 都应该从第一天起完全无人值守运行。Boris Cherny 的框架使用了一个四级自主阶梯：**Level 1** 只建议，**Level 2** 起草变更供人类应用，**Level 3** 应用低风险变更但需要人类批准才能发布或合并，**Level 4** 自动应用并完成并带有审计日志。

每个新 loop 从 Level 1 或 2 开始。运行一周，读它的输出，纠正它做错的地方。一旦 loop 持续产生你不需要修改就会批准的工作，把它移到 Level 3。**Level 4 是挣来的，不是默认的。**

发现东西的运行应该进入一个 triage 收件箱或标记列表。什么都没发现的运行应该安静地自我归档。**你永远不需要打开一个 loop 的输出来确认什么都没发生。**

---

**Watch the Token Cost**

一次糟糕的迭代是一次浪费的 prompt。一次糟糕的 loop 无人值守跑一整晚是一张账单。Agentic loop 可以跑几十或几百次迭代，每次迭代都是一次完整的模型调用，带着累积的对话历史。

在让任何 loop 无人值守运行之前，先手动跑三到五次迭代，检查每次迭代的 token 用量。乘以你的最大迭代次数得到每次运行的最坏情况成本。再乘以 automation 触发的频率得到最坏情况的每日成本。

**为任何能执行 shell 命令的 loop 建立一个命令白名单。** 限制到任务实际需要的特定命令，比如 `npm`、`git`、`ls`、`cat`。一个在无人值守 loop 内拥有不受限制 shell 访问权限的 Agent，是把 token 成本问题变成安全问题的最快方式。

---

**Build the Second Loop Differently Than the First**

你的第一个 loop 应该小、单用途、重度监督。你的第二个 loop 应该连接到第一个。这就是 Automation、Skill 和 Memory 开始复利而不是并行运行的地方。

一个每日 triage loop 把发现写到一个共享状态文件。第二个 loop，也按计划运行，读取那个状态文件并挑选最高优先级的项目去执行。两个 loop 都不需要对方才能工作，但在一起它们形成了一个从"已发现"到"进行中"的流水线，不需要你碰任何一个。

这也是 Skill 开始产生回报的时候。一旦你写了一个关于 loop 如何分类 CI 失败的 skill 文件，每个未来涉及 CI 失败的 loop 都读同一个 skill，而不是你重新解释一遍。**Loop 不只是独立运行，它们共享学到的东西。**

---

**The Shift in What Your Job Becomes**

一旦几个 loop 跑起来了，你的日常工作就变了样。你不再打开聊天窗口问问题，而是打开 triage 收件箱审查 loop 昨晚发现的东西。待办事项列表不再是一堆静态的任务，而是一组 Agent、例程和 loop，不断把想法变成草稿、修复和审查。

这不意味着你不再决定什么重要。**这意味着决策发生在 loop 设计层面，而不是每个任务层面。** 你写更少的 prompt 不是因为你在做更少的事。你写更少的 prompt 是因为 loop 在替你写它们，而你的注意力移到了真正需要人类的部分：审查关卡、停止条件、以及下一个值得构建的 loop。

---

**结语**

<div style="background:#f5f0eb;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:16px;">
<div style="text-align:center;margin-bottom:8px;">
<strong style="font-size:15px;color:#8b6f4c;">结语</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
这篇文章最有价值的地方不是具体的 loop 实现技巧——那些是已知模式。而是它揭示了一个正在发生的职业转型：从 prompt engineer 到 loop designer。Boris Cherny 说"他的工作就是写 loop"，这不是修辞，是事实描述。当 Claude Code 的负责人说自己不再写 prompt 了，这信号比任何 benchmark 排名都更说明问题。<br><br>
另外值得注意的一点是自主阶梯的四级模型（Level 1-4）。它给出了一个可操作的渐进路径，而不是非黑即白的"全自动 vs 全手动"。大多数团队应该从 Level 1 开始，一周后升 Level 2，一个月后升 Level 3——而不是第一天就追求 Level 4。
</div>
</div>

---

<span style="font-size:12px;color:#888888;">参考：How to Create Loops with Claude</span>
