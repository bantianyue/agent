**一个 Agent 不够用：Hermes Kanban 把聊天变成协调系统**

> Tony Simons 写了一份关于 Hermes Agent Kanban 的深度实操指南。这不是产品文档，是一个踩过坑的人告诉你：为什么单 Agent 是错误的最小单元，以及 Board + Contract + Receipts 如何拯救你的下午。

---

<div style="background:#e8f4fd;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:18px;">
<div style="text-align:center;margin-bottom:10px;">
<strong style="font-size:16px;color:#1a6ba0;">要点速览</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
- <strong>单 Agent 是错误单元</strong>：长任务需要持久化协调，不是更大 prompt 或更聪明聊天<br><br>
- <strong>Board 不是仪式感</strong>：从最蠢但有用的设置开始，`--default-workdir` 比看起来重要得多<br><br>
- <strong>小契约胜过巨型 prompt</strong>：Survey → Draft → Review 三段式，用 `--parent` 构建依赖图<br><br>
- <strong>三种愚蠢失败</strong>：错误的 Board、Scratch Ghost（输出丢在没人看的目录）、Stale Lock（Board 说 running 但进程已死）<br><br>
- <strong>Receipts 打败 Vibes</strong>：别猜，用 `show` → `runs` → `log --tail` → `tail` → `pgrep` 五步诊断
</div>
</div>

**上下文窗口不是管理者。它只是一个有边界的盒子。**

Tony Simons 见过一个任务在 Board 上显示"运行中"四十分钟，而 worker 早就死了。另一个任务因为 shell 还指着旧的 slug，落在了错误的 Board 上。没有戏剧性事件。这就是问题所在——失败模式是安静的。一个下午就这么从过期的状态里漏掉了，一次一个看似合理的谎言。

**修复方案不是一个更聪明的 prompt。而是一个 Board、一份契约、和收据。**

---

**The Context Window Isn't A Manager**

很多人试图在一个巨大的聊天窗口里跑真实工作，因为一开始感觉很快。

一个 prompt。一个 worker。一串整洁的输出。非常 tidy。非常 fake。

然后工作长出牙齿。对话记录越来越长。有人要求并行调研。另一个人要 review。一个 worker 崩溃了。session 里一半装着 prompt 残留，一半装着希望。

**这时候整个东西就变成了上下文汤。**

当这发生时，你没有持久化状态。你只有一个带漂亮格式的内存泄漏。

这就是第一个硬道理：**长任务需要持久化协调。**

Hermes Agent Kanban 不是一个更花哨的聊天机器人。它是一种让工作能在现实中存活下来的方式。

Board 隔离工作流。Task 携带状态。Profile 定义 worker 形态。Parent 链接定义顺序。Workspace 决定文件落在哪里。Run、Log、Event 就是收据。

**收据每次都能打败"我感觉"。**

如果你需要知道发生了什么、谁做的、跑了多久、worker 完成前说了什么，Board 给你那条追踪链。聊天窗口给不了。

这就是整个产品。不是一个魔法记忆层。不是一个更大的 prompt。不是一个从远处看很协调的仪表盘。

**它是一个在对话变得混乱之后还能记住东西的系统。**

---

**Build The Board Like You Mean It**

人们喜欢过度设计第一个 Board。他们想要仪式感，在知道工作值不值得之前。这通常会给你一个漂亮的烂摊子。

别这么做。

从最蠢但有用的设置开始：

- `boards show` 告诉你你在哪里
- `boards switch` 移动后续调用的活跃 Board
- `boards create ... --switch --default-workdir ...` 给 Board 一个家，让新工作不会掉进没人能找到的 scratch 输出堆

那个 `--default-workdir` 参数比看起来重要得多。如果 Board 知道工作应该存在哪里，你就不用花时间问"等等，文件去哪了？"这不是哲学问题。**这是一个路径问题。**

如果你在多个 shell 之间跳转，不要相信当前碰巧活跃的 Board。在创建任何东西之前，有意识地切换它。

然后创建一些足够小到能完成、足够大到能验证的东西：

用 `--json` 当你关心 task id 不被埋在滚动记录里。如果你在链式工作，机器可读的输出不是奢侈品。**它是干净的工作流图和充满"我感觉"的终端之间的区别。**

如果需求还是一团浆糊，把它停放在 triage 里，而不是假装它已经准备好了：

`--triage` 是给那些在需要劳动之前还需要一份 spec 的半成品需求的。当问题是"我们甚至不知道这是什么"时用它。用 `--initial-status blocked` 当工作是真的但需要一个人类决策才能继续。

不要假装运行时间是装饰性的。

如果工作是一次快速通过，`--max-runtime 300` 就够了。如果是一个真正的调研，`--max-runtime 30m` 是合理的。如果是草稿或 review 关卡，`--max-runtime 2h` 一点也不奇怪。**重点是阻止失控的任务永远占着位置。**

第一个 Board 不应该让人觉得 impressive。它应该让人觉得 inevitable。

---

**Small Contracts Beat Giant Prompts**

这是把聊天变成协调的关键部分。

Survey 第一，Draft 第二。

这就是模式。

Survey 任务收集事实。Draft 任务把事实变成文章。Review 任务检查交接。**它们都不应该重新争论整个项目。**

这是干净的版本：

用 `--parent` 在创建时就指定依赖。这是干净的路径。依赖图从诞生时就存在。

用 `hermes kanban link <parent_id> <child_id>` 事后补救，当两个任务都已经存在，或者你在拼接一个旧的工作流图时。`--parent` 是创建时的意图。`link` 是修复模式。

这个区别比听起来重要得多。一个是你如何有目的地构建工作流。另一个是你如何在有人把零件按错误顺序创建之后补救。

如果你需要不同的 worker 形态，**创建一个不同的 profile**，而不是把一个 profile 塞满所有可能的 skill 然后指望最好的结果。Profile 不是贴纸。它们是状态边界。

Survey worker、writer 和 reviewer 不需要相同的假设，仅仅因为它们的任务标题在同一个 Board 上。一个可以收集素材，另一个可以把它变成文章，第三个可以检查偏差。**这种分离不是官僚主义。是风险控制。**

---

**Claim, Block, Schedule, Then Stop Improvising**

这是密集的部分。也是让 Board 感觉像一个工作系统而不是一个漂亮列表的部分。

当一个任务落地时，claim 它：

那个 TTL 不是所有权。**它是一个租约。** 如果 worker 消失了，claim 可以过期消失，而不是像幽灵一样挂着。

如果任务在能继续之前需要一个决策，block 它并说明原因：

**Blocking 不是失败。** 它是诚实地承认人类输入是依赖项。

如果唯一缺少的是时间，schedule 它，而不是用虚假的紧迫感堵塞 Board：

这很重要，因为"等一个人"和"等时间"不是同一件事。一个需要评论线程和耐心。另一个需要一个稍后醒来的理由。

当上游工作完成时，promote 卡片：

用 `--force` 只有当你故意覆盖依赖时。**那个 flag 是撬棍，不是生活方式。**

当工作真正完成时，用真实的交接关闭它：

那个 summary 是给人类的。metadata 是给下游 worker 和未来的你。**如果以后会重要，现在就写在交接里。**

然后 archive 卡片如果你想让 Board 保持干净：

这就是循环，而且它不微妙：create board → create task → claim → block/schedule（如果输入或时间没到位）→ promote（当依赖清除时）→ complete（带 metadata）→ archive（当故事结束时）。

**那不是演示。那是操作节奏。**

---

**Receipts Beat Vibes**

这是伤疤组织开始显现的地方。

仪表盘可以让你感觉协调，而实际的 worker 状态已经过时、卡住或死了。**所以我先相信收据。**

当某些东西闻起来不对时，不要猜。拉取状态。

`show` 告诉你任务、它的评论和事件。`runs` 告诉你是否真的有执行尝试。`log --tail` 显示 worker 输出的最后一段，不让你在噪音墙里滚动。`tail` 跟随事件流，如果任务还在变化中。

然后检查实际进程，**因为一张写着 running 的卡片不是生命迹象。**

如果 Board 说 running 但没有活进程，`runs` 也没有显示健康的执行尝试，你很可能有一个过期的锁或一个死 worker。不要和 UI 进行哲学辩论。Reclaim 它。

如果 Board 说任务 blocked，保持 blocked 等待真正的答案。如果是 scheduled，停止把时间叫做 bug。如果输出已经完成但 Board 没被告知，用 summary 和 metadata complete 它。如果任务不可恢复，archive 它并重新创建正确的。

这是我希望更多人在恐慌之前运行的丑陋序列：

1. `hermes kanban boards show`
2. `hermes kanban show <task_id> --json`
3. `hermes kanban runs <task_id> --json`
4. `hermes kanban log <task_id> --tail 4000`
5. `hermes kanban tail <task_id>`（如果状态还在变化）
6. `pgrep -af 'hermes.*kanban.*<task_id>'` 和 `ps aux | grep 'hermes.*kanban' | grep '<task_id>'`
7. 只有当 Board 说一件事而进程表说另一件事时才 reclaim

**这个序列比任何数量的信心都能拯救更多的下午。**

如果你曾经因为一个任务在 Board 上显示"运行中"而进程早已消失，浪费了一个小时，你已经知道为什么这很重要。

---

**The Three Dumb Failures That Keep Eating Afternoons**

大多数 Kanban 的痛苦不是什么宏大的架构谜题。**是三个愚蠢的失败戴着不同的帽子。**

**第一个，错误的 Board。**

当你跨 shell 快速移动时，一个终端还指着旧的 Board。标题看起来对。task id 看起来对。工作还是落在了错误的队列里。

这就是为什么 `hermes kanban boards show` 存在，为什么 `hermes kanban boards switch <slug>` 不是可选的表演。

如果你在项目之间跳转，有意识地切换，停止相信你上次打开的那个 shell 的偶然性。

后果不只是有点混乱。**是一个活在错误位置的任务。** 别人看不到它。正确的 Board 不拥有它。你会花十分钟想不通为什么 worker "忽略"了一张从来不在它跑道里的卡片。

**第二个，Scratch Ghost。**

这个感觉像成功，直到归档日。Worker 完成了，summary 看起来很干净，然后你去找文件，发现输出落在了 scratch 或其他没人看的死胡同 workspace 里。

文章、笔记、证据、交接，不管是什么，现在只作为工作的记忆存在。

这就是为什么 `dir:<absolute-path>` 存在，为什么 Board 的 default workspace 如此有用。**如果输出需要落在一个可见的项目树里，在 task 里明确说出来。**

不要让 worker 猜现实在哪里。我想要文件在另一个人类能打开、diff、信任它们的地方，而不是像服务器机房里的浣熊一样追着 temp 路径跑。

**第三个，Stale Lock。**

这是最丑陋的一个，因为它礼貌地撒谎。

卡片说 running。仪表盘还感觉活着。日志已经停了一会儿了。进程表是空的。然后你意识到 Board 正在讲述一个关于不再发生的工作的故事。

这时候收据就派上用场了。`show` 告诉你任务状态。`runs` 告诉你是否真的有执行尝试。`log --tail` 告诉你输出在哪里停止。`tail` 告诉你事件流是否还在移动。然后活进程检查告诉你幕后是否有一个真正的 worker，或者只是一张化了舞台妆的卡片。

如果 Board 说 running 而进程表说 dead，**不要像刷新页面能复活任何东西一样继续刷新。** Reclaim 任务并给它一个理由。如果任务真的 blocked，把理由留在任务里等人类答案。如果是 scheduled，让时间做它的工作。如果是 triage，停止假装它已经准备好被劳动。**这些状态不是同义词。**

- Triage 意味着 spec 是一团浆糊
- Blocked 意味着缺少人类决策
- Scheduled 意味着时间是依赖项
- Running 意味着一个进程此刻还活着

**如果你把它们混在一起，你就不再运行一个系统，而是在运行一个迷信机器。**

Board 的存在就是为了让你能在它们吃掉你的白天之前区分这些失败。

---

**Tiny One-Shot Tasks Don't Deserve A Board**

这条诚实线很重要，因为它让推荐变得可信。

小的一次性任务不值得一个 Board。其他所有任务都值得。

如果工作是一次性查询、快速编辑、帮助文本检查、或者在咖啡凉之前就完成的小答案，Kanban 只是增加开销。**不要给不需要的东西裹上仪式感。那不是纪律。那是带着多余点击的自以为是。**

用 chat 做小事：

- "`hermes kanban promote` 的确切语法是什么？"
- "重命名这个标题。"
- "检查 `--max-runtime` 是否接受原始秒数。"
- "给我当前的 board slug。"

用 Board 当工作需要以下任何一项时：

- 并行工作流
- Review 关卡
- 崩溃恢复
- 持久化交接
- 专业 Profile
- 需要在一个 shell 死掉后还能存活的状态
- 跨越数小时或数天的工作

这是用大白话画的线。

Chat："`hermes kanban promote` 接受 reason 参数吗？JSON 的 flag 是什么？"

Board："根据 review 笔记重写 article-v5，保留一个 draft 任务、一个 review 任务、和一个如果 worker 中途被 reclaim 的 fallback 恢复路径。"

Chat："你能确认 `block` 和 `schedule` 当前的帮助语法吗？"

Board："运行实际的文章 pipeline，保持交接，如果 session 死了不要丢文件。"

**如果工作在浓缩咖啡凉之前就结束了，留在 chat 里。如果它需要记忆、关卡、重试、或别人稍后接手，放在 Board 上。**

这就是那条线。

---

**The Operator Still Owns Judgment**

这部分不可协商。

**操作者仍然拥有判断权。**

Agent 可以做工作。可以推荐范围。可以执行契约。可以干净地交接。**它们不能决定简报、排序、或者 Board 是否值得。**

那不是限制。那是设计。

- 一个需要 Board 的任务应该被拆分，因为人类决定它需要持久化协调
- 一个需要 review 的任务应该被关卡住，因为人类决定输出需要另一双眼睛
- 一个需要时间的任务应该被 schedule，因为人类决定时钟很重要
- 一个太小的任务应该留在 chat 里，因为人类决定仪式感不值得

即使是最丑陋的决策也是人类决策。如果草稿缺少 source notes，我 block 它。如果工作只需要稍后醒来，我 schedule 它。如果依赖图是畸形的，我 link 碎片或重新创建卡片。如果任务死了而 workspace 是错的，我 archive 它重新开始，而不是假装我在高效。

**那不是 Agent 弱。那是 Agent 待在契约里。**

而这正是整个系统的意义所在。

Hermes Kanban 不是为了让一个 Agent 感觉更聪明。**它是为了让一群 Agent 和人类不那么脆弱。**

一个 Agent 在工作长出牙齿之前是够用的。在那之后，你不需要一个更聪明的聊天。**你需要持久化协调。**

---

**结语**

<div style="background:#f5f0eb;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:16px;">
<div style="text-align:center;margin-bottom:8px;">
<strong style="font-size:15px;color:#8b6f4c;">结语</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
这篇文章最有价值的地方不是 Kanban 命令列表——那些文档里都有。而是它揭示了一个在 Agent 领域很少被讨论的真相：<strong>单 Agent 架构的失败模式是安静的。</strong>没有崩溃，没有报错，就是一个下午慢慢漏掉了。这种"安静失败"比显式错误更难诊断，也更危险。<br><br>
Tony Simons 的"Receipts Beat Vibes"原则——用 `show` → `runs` → `log` → `tail` → `pgrep` 五步诊断链——本质上是在给 Agent 系统建立可观测性。这在传统运维领域是常识，但在 Agent 编排领域还很少被实践。<br><br>
另外值得注意的一点：他明确划了一条线——"小的一次性任务不值得 Board"。在大家都在鼓吹 Agent 编排的当下，能说"chat 就够了"反而是一种成熟。不是所有工作都需要仪式感。
</div>
</div>

---

<span style="font-size:12px;color:#888888;">参考：How To Dominate Projects With Hermes Agent Kanban Board</span>
