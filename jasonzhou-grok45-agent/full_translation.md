# 全文逐句翻译（对照基线）

## 标题
What I learnt after running loops for 1 month???
我跑了一个月的 loop（自主循环 Agent）后学到的东西？？？

6 18 96 9,148

上周我写了一篇关于 loop engineering（循环工程）的文章：从「提示 Agent 去完成一个任务」，转向「设计一套系统，让 Agent 自己决定做什么、去执行、去验证、并随时间不断改进」。

但很多人的反应是：好，我被说服了，可我到底怎么真正搭一个出来？更重要的是，怎么搭一个真的能用的？

因为任何人都能把一个 Agent 套进 `while true` 里然后管它叫 loop。那是简单的前 5%。真正的工作在于那些让你能放心走开的护栏（guardrails）。

过去一个月我们做了一个实验：搭了很多很多 loop 来跑 @SuperDesignDev，这里想分享一些真正实用的经验。

## The anatomy of a good loop（一个好的 loop 的构成）

我们跑的每一个 loop 都有相同的四个部分。

### 1. The loop contract（循环契约）
一个 markdown 文件，每次 run 触发时被注入给 Agent。这是 loop 的宪法。它包含四样东西：
- the Goal（什么是赢，以及到底有没有终点线）
- the Boundaries（它能自由做什么、绝对不能做什么、以及它能自己发布 vs 需要人审的界限）
- the SOP（每次 run 遵循的步骤）
- the Current understanding（当前对 loop 运行状况的理解）

人们在 boundary 这一段投入不足，而恰恰是这一段决定了你能不能走开。拿我们的一个 loop「Error Sweep」举例：每天早上它读我们的生产错误追踪器，挑出最严重的新 bug，然后发布一个修复。这是它契约里真实的 boundary 片段：
- 只有当根因清晰「且」修复是低风险时，才修复。
- 任何有风险或改动大的：开一个 PR 并标记给人。不要自己合并。
- 做最小可用修复。一个 PR 只修一个东西。
- 上一个 Error Sweep PR 还没合并时，绝不新开 PR。
- 绝不把凭证、token 或用户数据复制进报告或 PR。

这些没一句在讲「怎么修 bug」。它是四句话画出一道围栏。围栏内 Agent 自己发布。围栏外，由人决定。你要给 Agent 画一张清楚的图：什么时候它能自己发、什么时候该停下去问人。

我们通常把 contract、state、logs 放进同一个 md 文件，就像下面这样：

# <loop 名字> — contract
## Goal
什么是赢的样子。有没有终点线，还是作为监控永远跑下去？
## Boundaries
- 自由做：……
- 绝不：……
- 自己发布 vs 问人：<精确的界限>
## SOP（每次 run）
1. 读 state + logs。
2. 收集变化。挑出唯一一件最值得做的事。
3. 去做（或交给 executor）。
4. 验证。记录发生了什么。汇报。
## Current understanding
……loop 运行的当前状态
## Logs
……过去 run 的日志

### 2. State + logs（状态 + 日志）
一个在 run 之间忘掉一切的 loop，只是多了几步的 cron job。它需要记忆，分成两部分：
State 是持久的画面：backlog、当前假设、已经发出去但需要跟进的实验。在每次 run 开头读，刻意保持精简。
Logs 是只追加的记录，记录发生了什么，一次 run 一行。

最清楚的例子是 Error Sweep loop 保留的 state，这样它就不会浪费一次 run 去重新调查它已经理解的东西：
## Skip these fingerprints (known noise or upstream, not ours)（跳过这些指纹：已知噪声或上游问题，不是我们的）
- ResizeObserver loop limit exceeded
- Stripe.js network blip on /checkout
## Fixed, still watching（已修，仍在观察）
- null-team-on-login (019edc8a) — 在 #1027 修好，确认它在 prod 停止触发

没有这个区块，每天早上 loop 会重新发现同一个噪声错误，烧掉一次 run 去追它，还烦你。有了它，loop 跳过它已经判断过的，把注意力花在新的东西上。State 是 loop 停止自我重复的地方。

State 还保存了 loop 通过运行学到的东西：一个关于谁转化的有效假设，加上它从犯错中养成的习惯。我们的 CRM loop 带着这样的行：
- 第一周撞到 credit wall 的用户，回复率大约是其他人的 3 倍。优先给他们写。
- 起草前，查用户实际建了什么，而不是他 profile 上的标签。一个被标成「SaaS dashboard」的账户，其实是个印刷小册子。

这些没有一句来自原始契约。是 loop 一次次 run 赚来的，现在每次 run 都从更聪明的一步开始。这就是为什么一个好的 loop 在第 3 个月比第 1 周更值钱：它的 state 吸收了它见过的一切。

我们管理 loop 的内部工具，开源在这里（Loopany）：https://github.com/superdesigndev/loopany-platform

### 3. The /verify（验证）
这是任何交付高 stakes 工作的 loop 的先决条件（比如真实的生产代码改动、给真实客户发消息）。本质上你要确保验证过程既容易、又能产出人能轻松 review 的证据。

一般来说意味着：
- 搭建环境让验证 token 高效且可靠
- 一种把验证证据纳入的方式

对工程任务，意味着：
- dev-local.sh 脚本，轻松启动本地 dev + 远程 sandbox 环境来测（像 crabbox）
- 让 Agent 像真实用户一样自驾 app 的工具（比如 Playwright-CLI）
- 包含测试 SOP 的 /verify skill
- 上传截图+视频证据、附在 PR 里的位置（我们上传到 github release assets）

而对其他非工程工作可能更棘手，但不是不可能，比如 CRM loop 我们有一个 verifier agent 用某些 anti-slop 规则来 review 起草的消息；
我们把这套配置作为 verifier-setup skill 开源了（https://github.com/AI-Builder-Club/skills）。

结果是：来自 loop 的 PR 不是以「信我，它能跑」到达的。它带着一段它真在跑的视频到达。我能在几秒内批准，因为我看的是行为，不是读 diff 然后祈祷。这也是为什么 verifier 决定了一个 loop 到底值不值得做。

### 4. The trigger（触发器）
是什么唤醒 loop 的。有三种形态，选对的那一种是成本模型的一半：
- Continuous for-loop（连续 for 循环）。这是 ralph-loop 或 /goal 类型触发器。Agent 在 for-loop 里跑直到条件满足。这是自主研究 Agent 背后的形态。适合有界的推进（「一直跑到测试套件变绿」），作为永久设施就浪费了。主要在有即时反馈循环和清晰 spec 时有用（像大多数修 bug 的工程工作）。
- Time based（基于时间）。一个 schedule 触发 loop：每小时、每天早上 6 点。我们的 Error Sweep、React Doctor、doc maintainer 和 CRM loop 都跑在 cron 上。
- Workflow / event based（基于工作流/事件）。一封新邮件到达、一个事故开启、一个 PR 落地。loop 只在有东西可跑时才跑。它甚至能和基于时间的结合：比如一个基于时间的 tick 每小时跑个脚本检查有没有新支持 ticket，如果有，触发 Agent；如果没有，记日志并静默。管理 loop 成本的好办法；你会在 Evolve 一节看到机制。

### Orchestrator + Executor + Verifier（编排者 + 执行者 + 验证者）
一旦一个 loop 触及任何非平凡的事，我们就开始拆成三个角色：
- Orchestrator（编排者）找活。Executor（执行者）在隔离盒子里做活。Verifier（验证者）证明它并附上证据。
- The orchestrator / prioritiser：在 schedule 上醒来的 Agent。它的工作不是做任务，而是找任务：收集信号、看变化了什么、挑出这次 run 唯一最值得做的事，然后交接出去。
- The executor：在隔离空间里做实际工作（对代码而言，是 off main 的一个全新 git worktree，所以它从不污染你的工作区 checkout 或另一个 loop 的 run）。
- The verifier：独立确认执行者的工作，并产出人能扫一眼的证据。
但不是所有 loop 都需要三者全有。三层形态是复杂的、发代码的 loop 长成的样子。很多好 loop 就是 orchestrator 自己把整件事做了。让我把两端都给你看看。

### Evolve Loop - Build anti-fragile loops（进化 loop：构建反脆弱的 loop）
在 Nassim Taleb 的《反脆弱》里，他把系统分成三种：脆弱的系统害怕波动，一次意外就是大损失；健壮的系统在波动中存活并恢复到原样；反脆弱的系统从中获益，每次冲击都让它更强。玻璃是脆弱的，石头是健壮的，你的免疫系统是反脆弱的：每次小感染都训练它。

把这个对准 loop，问题就具体了：当一次 run 失败时，教训去哪了？在我们的实践里，一个教训有三个去处，抽象层级递增：
每个人都有日志，而日志只会越来越长。把经验蒸馏成规则，才让 loop 反脆弱。问题是：谁来做蒸馏？

所以在 Loopany（我们为这些 loop 搭的内部 app）里，这变成了一个独立的 run 角色：evolve。一个 Agent session 读这个 loop 最近十几次 run 的日志、结果、成本，然后问：我们在哪里重复犯错？哪些 run 被浪费了？哪个 boundary 太松、哪个太紧？它的产出不是产品代码，而是对这个 loop 自身的改动：
- loop contract
- State 约定
- Trigger 机制
- 用于重复且确定性 Agent 步骤的脚本
- Skills
- 人看的数据面板
它是改进 loop 自身的 loop。

## Real loops running Superdesign（在 Superdesign 上真实跑着的 loop）
我们一直在用 loop 自动化 Superdesign 的大部分，有些有用，有些没用（经验写在另一篇 blog），下面是我们天天跑、相对容易让你复制搭建的几个真实例子：

### Doc maintainer loop（文档维护者 loop）
我们最简单也最有用的 loop 之一。每周一次它让项目的文档保持诚实；
这个 loop 是一层。编排者读 diff、检查文档、如果有漂移就开一个 PR，完事。没有独立的执行者，没有独立的验证者，因为任务足够简单、爆炸半径足够小，一个 Agent 能在脑子里装下。

你可以加层，一个验证者去事实核查每条文档声明，一个 pass 去标记它注意到的技术债。你不该加，除非简单版先把你坑了。先搭一层版，感受到具体的痛，再加刚好能修它的那一层。

这是我建议你先搭的 loop，所以给个模板：
# doc-maintainer — contract
## Goal
README、setup 指南、例子永远和代码实际发布的一致。发现 0 漂移 = 成功 run，不是浪费的 run。
## Boundaries
- 自己发布：开 ONE 个带修复的 pull request。仅此而已。
- 绝不：为了显得忙重写准确的文档、碰 docs 之外的任何东西、在上周的 PR 还开着时叠第 2 个。
## SOP（每次 run）
1. 读 diff：上次 sweep 以来每次 commit + PR（cursor 在 state 里）。
2. 把 README、setup 指南、例子、runbooks 对着代码现在发布的核对。
3. 真验证：跑命令、查链接、试例子。绝不信记忆。
4. 发现漂移 → 最小修复、新鲜 worktree、一个解释漂移了什么和为什么的 PR。没陈旧的 → 干净停。
5. 移动 cursor、记 run 日志。
## State
- last-sweep cursor（commit hash）
- open PR（如果有）
## Logs
- 每次 run 一行带日期：漂移数 + PR 链接，0 也计入

### Bug hunter loop（找 bug 的 loop）
有些 loop 把真实代码发给真实客户，那里的错误很贵。那是三层全出场的时候。

我们的 Error Sweep loop 每天早上跑：
- （编排者）从错误追踪器拉最近 24h 的生产错误（我们写的一个特殊脚本从 posthog/LLM 日志/服务器日志收集数据），按 occurrences × users 排序，从它的 state 跳过已知噪声指纹，挑出唯一最有影响的新异常。它拉出 de-minified 堆栈跟踪并找根因。
- （执行者）如果根因清晰且低风险，它在新鲜 worktree 里修并发布 PR。如果风险高或改动大，它停并标记人。boundary 里那个分支每次 run 都在做真工作。
- （验证者）修复在算数之前先被证明，然后 loop 在后续 run 持续盯那个指纹，确认错误真的停了触发。一个没让真实数字移动的修复，不是修复。

React Doctor 是同样的形态，只是瞄准代码健康而非运行时错误：每天早上用 npx react-doctor 扫 app，挑出唯一最严重的问题，在隔离 worktree 里修、验证、开一个 PR。它报一个健康分作为每日指标，这样你能看线在动。它还有个小护栏让它宜居：
如果上一个 React Doctor PR 还开着没合并，今天别开另一个。刷新开着 PR 的状态并仍然报分数。
那条规则是「有用 loop」和「用 30 个你永远不 review 的 PR 埋了你」的 loop 之间的区别。一个 loop 必须尊重你的 review 带宽，不只是它自己的吞吐量。

### Support triage loop（支持分诊 loop）
每小时对着我们的 Intercom 收件箱跑。它的指导原则：每张支持 ticket 都是一扇免费看产品缺口的窗。一个写进来的用户，免费递给你一份 bug 报告、一个转化阻碍、或一个困惑信号。多数支持设置回答了消息然后把窗扔掉。这个 loop 两样都留。

每次 run 走四步：
- Pull the window（拉窗）。上次 run 以来的所有东西，加上今天到期的任何跟进。窗在静默时段自动变宽，所以一次漏触发永远不丢 ticket。按最后说话的人分桶：customer = 需要回复、bot = review 它、teammate = 已处理。
- Investigate before replying（回复前先调查）。这是差异化点。对每张 ticket，先对着真实数据找根因：查用户账户、他们的真实 session、错误日志、账单记录。绝不盲答。一半时候用户对问题的描述不是问题本身。
- Fan out to three outputs（扇出到三个产出）。每张 ticket 最多产生三样：一个现在就在线程里修好用户问题的回复；一条存进知识库的信号：ticket 背后的产品缺口，写一次，这样增长和工程 loop 之后能按模式行动；当根因是真实 bug 时，它在新鲜 worktree 里 spawn 一个 fix agent，含验证者和证据，和找 bug loop 同样的机器。
- Write back and sleep（写回并睡）。设跟进日期、记 run 日志、等下一个 tick。

让它对着真实客户安全跑的 boundary：回复是分层的。例行、事实性的答案自己发。任何敏感的、退款的、愤怒用户的、我无法 review 语气的非英文，只在人批了之后才出去。

搭建它和每个其他 loop 是同一个配方：一个契约文件加一个每小时 cron。这是 support 契约，修到你能偷的模板：
# support-triage — contract
## Goal
每张进来的 ticket 在一小时内得到正确、调查过的回复，且 ticket 背后的每个产品缺口变成团队能行动的信号。没有终点线：这是个监控。
## Boundaries
- 自己发布：对例行、事实性问题的回复（how-to、账单查询、有文档修复的已知问题）。
- 先问人：退款、愤怒或流失风险用户、任何法律问题、任何团队无法 review 的语言的回复。
- 绝不：承诺功能或时间表、分享另一个用户的数据、没有写下的根因就关 ticket。
## SOP（每次 run）
1. 拉上次 run 时间戳以来的对话 + 今天到期的跟进。按最后说话者分桶（customer / bot / teammate）。
2. 每张 ticket：对着产品 DB、错误日志、账单在起草任何东西之前调查根因。绝不盲答。
3. 按 boundary 层回复。需要批准的地方只起草。
4. 如果根因是 bug：在新鲜 worktree 里 spawn fix agent，要求验证证据，开一个标记给团队的 PR。
5. 为任何反复出现或转化相关的缺口存信号（先对已有信号去重）。
6. 设跟进日期。记 run 日志。
## State
- open follow-ups（ticket id → due date）
- recurring-theme tally（喂信号创作）
- standing lessons（如「重复消息 = 重试产物，不是 spam」）
## Logs
- 每次 run 一行带日期：处理 ticket 数 / 发回复数 / 存信号数

然后在 cron 前放一个便宜的门，这样只有窗里有东西时 Agent 才醒（前面提到的 Evolve 动作），然后让它跑。回报不只是更快的回复，是信号：当五个人问怎么导出某东西，那是被存起来的转化缺口、等着增长 loop，不是某人也许在季度回顾里注意到的模式。

### CRM lifecycle loop（CRM 生命周期 loop）
Loop 不是工程玩具。我们有一些最高价值的从没碰过一行代码。这一个跑我们的客户外联，它是三层形态对准人而非代码最完整的表达。

每天早上：
- 脚本先拉数据。谁在过去 24h 活跃、新来的 business-email 注册、以及任何进来的回复。确定性预stage，不在数据拉取上花 LLM。回复过的用户彻底退出 loop：活对话属于人。
- 编排者提议 segments，不是一次性挑选。今天值得外联的高意图用户组：这周撞到 credit wall 的、新 business 注册的、高触达的 builders。那些是例子，不是固定列表；segments 每次 run 从数据新鲜提议，哪些转化了活在 state 里。
- 每个 segment spawn 一个 executor 子 Agent，逐用户工作：读他们实际建了什么、读和他们每过去一次交流，然后起草一封私人邮件。绝不盲起草。一个标着「SaaS dashboard」的 profile 标签可能其实是印刷小册子；executor 查真实工作，不是标签。
- 一个验证者在任何草稿能去任何地方之前检查它：对着数据事实核查邮件里每个声明（没有假的东西以你的名义出去），然后语气和 anti-slop 规则。这是 SEO 故事里那个品味问题又来了，但这里它是可处理的，因为「这条关于用户项目的声明是真的吗」有一个可查的答案。
- 发送按风险分层。我们从只起草开始：每封邮件等人。随着 segments 证明它们的回复率，低风险的赢得了自己发的权利，在围栏内。高触达 segments 仍然作为草稿落给人批。自治是按 segment 赚来的，不是授予 loop 的。
- 摩擦变成信号。当研究发现一个用户卡在某事上，那不只是邮件材料，它存一条其他 loop 读的信号，一个真实 bug spawn 一个 fix agent，和找 bug 同样的机器。

你第一部分看到的围栏撑着一切：7 天抑制、没有回复最多 1 次跟进、回复了意味人接管。而 state 做着复利：按 segment 记发送和回复，留转化的、丢不转化的。这个 loop 对给谁发邮件的品味每周 measurable 地变好，因为它按回复率校准而非 vibes。

# crm-lifecycle — contract
## Goal
把高意图产品活动变成对话。成功 = 每个 segment 的回复率和升级，不是发了多少邮件。没有终点线：这是个监控。
## Boundaries
- 自己发布：发给已经 EARNED 它的 segments（见 state: approved_segments）。其他一切：只起草，人发。
- 先问人：任何新 segment 的第一批、任何曾经回复过的人、验证者无法确认的声明。
- 绝不：邮件任何过去 7 天联系过的人、没回复就发第 2 次跟进、编造关于用户建了什么的事实。
## SOP（每次 run）
1. 脚本已经拉了 actives、signups、replies。读输出。回复过的用户退出给人。
2. 给用户打分，然后提议 SEGMENTS（组，不是一次性挑选）。查 state 哪些 segments 之前转化了再提议更多。
3. 每个 segment：spawn 一个 executor 子 Agent。每用户：读实际建了什么 + 每过去一次交流，然后起草。绝不盲起草。
4. 每个草稿过验证者：对着数据事实核查每个声明，然后语气 + anti-slop 规则。没假的东西出去。
5. 按风险路由：approved segments 发；其他排队等 review。
6. 研究中发现的摩擦 → 存信号；真实 bug → spawn fix agent。
## State
- approved_segments（赚来的自治 + 赚到它的回复率）
- per-segment 表现（sends → replies → upgrades）
- suppression list · standing lessons（如「从他们真实工作验证，不是 profile 标签」）
## Logs
- 每次 run 一行带日期：提议 segments / 草稿 / 发送 / 回复

## Checklist for a good loop（好 loop 的清单）
- [ ] Loop contract 文件：goal、SOP、输出规则，每次 run 读
- [ ] Boundary 和约束：它自己发什么 vs 问人；no-op 是合法 run
- [ ] State + logs：run 之间的记忆，所以它从不再做工作
- [ ] 便宜的验证者：带证据的证明；如果没有，留人在环
- [ ] 隔离执行：每次 run 新鲜 worktree 或自己 sandbox
- [ ] 成本有效的触发器：门脚本或事件，空 run 不花一分钱
- [ ] Loop evolve 周期：review run 历史，把机械工作折进脚本/skills
- [ ] 小范围：拆分 loop 直到「就让它跑」感觉舒服

## Loopany - Our internal loop manage tool (Open-sourced)（我们内部的 loop 管理工具，已开源）
我们一直用一个内部工具 Loopany 来跨公司编排所有 loop，它对我们超有用所以我们开源它
- 它是一个 loop 管理环境，连到你团队自己的本地 Agent
- 内置 Loop 模板 & 自动 log/state 追踪
- 可编程触发器 + 自动重试 & 恢复
- Evolve 周期
- 每个 loop 的 Mini apps
- 团队工作区让 loop 不冲突
欢迎试试并告诉我们反馈：https://github.com/superdesigndev/loopany-platform
