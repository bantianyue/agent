<div style="background:#e8f4fd;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:18px;">
<div style="text-align:center;margin-bottom:10px;">
<strong style="font-size:16px;color:#1a6ba0;">要点速览</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
- <strong>三种命令三种模式</strong>：`/goal`（验证条件达成后停止）、`/loop`（定时循环）、`/schedule`（云端定时任务），对应"我在→我看着→我走了"<br><br>
- <strong>15 个真实跑起来的 Loop</strong>：从 Boris Cherny 的验证器循环到 Peter Steinberger 的 5 分钟仓库维护，每个都有原文出处和真实互动数据<br><br>
- <strong>Loop 的核心是验证器</strong>：没有验证器的 loop 只是更快地犯错，`/goal` 用独立模型打分，Clodex 用两个模型家族互相审查——自己给自己打分的 Agent 会删掉测试然后宣布完成
</div>
</div>

<a href="https://mp.weixin.qq.com/s/tf67rMQrSXjl_AyWKhqhlg" style="color:#0F4C81;text-decoration:none;">《Loop Engineer 到底是什么，以及如何真正搭建》</a>在 Peter Steinberger vs Boris Cherny 之间解释 loop 到底是什么。这是续篇，回答下一个问题：人们实际在跑哪些 loop？

我让 /last30days 跑了八次搜索，覆盖 X、TikTok、Reddit、YouTube 和 GitHub。下面是挑出来的 15 个最好的，每个都有来源归属、真实互动数据，以及你今晚就能复制的命令。

**先搞清楚三个命令（这是所有人第一步就绊倒的地方）**

最清晰的解释来自 inyourhandmedia（TikTok）：Goal 是继续工作直到结果达成。Loop 是重复执行一个任务，当你在的时候。Routine 是你不在的时候继续工作。对应到命令：

**`/goal <条件>`** 一直运行直到一个可验证的条件为真，然后停止。每次执行后有一个单独的模型检查你是否真的完成了。这就是"修到测试通过为止"的那个命令，也是两个工具都有的：Claude Code 在 v2.1.139 中发布（文档），Codex 在 CLI v0.128.0 中发布了包含 set、pause、resume、clear 控制的版本（文档）。

**`/loop <间隔> <提示>`** 在你的 session 打开时按定时重复，比如 `/loop 5m check the deploy`。适合实时监控。Codex 还没有 `/loop` 命令，它的等效方案是把 `codex exec` 套在 shell 循环里。

**`/schedule <描述>`** 创建一个云端 Routine，在你合上电脑后运行，比如 `/schedule daily PR review at 9am`。这就是"我睡觉它干活"的那个。Codex 的等效方案是 App 中的 Automations。

一个常见的陷阱：两个工具里都没有 `/routine` 命令。Claude Code 里的调度命令是 `/schedule`，Codex 里是 App 中的 Automations。用对动词，下面每个 loop 都能直接工作。

下面十五个，十一个来自 X、TikTok、Reddit 和 GitHub 的真实现场，带着互动数据；最后四个来自一个 curated 目录，我有特别标注。

**1. 构建-测试-修复对（loop）**

整个系列中演示最多的 loop，来自 creator raycfu 的教程（Instagram 43,587 次观看，1,040 条评论）。两个 Agent：一个 Builder 写代码，一个 Checker 跑测试、类型检查和 lint，报告精确的错误。它们交替传递工作直到全部通过。它的全部卖点就是它消除的痛苦：一次性 Agent 会留下它的 bug。

```
/loop build the next item on the plan, then run tests, typecheck, and
lint. Feed every failure back as the next instruction and fix it. Stop
when the build is green and the checker has nothing left to report.
```

**2. Boris 的验证器循环（loop）**

Boris Cherny 自己描述的 loop，也是参与度最高的描述之一（@bcherny，781 likes）：同时跑 Claude Code 加一个高级模型加一个验证器，喂给它任务，随时移除瓶颈。验证器是每个人都跳过的部分。没有它，你只是在信任 Agent。

```
/loop work the task list. After each task, have a separate verifier model
check the result against the spec and the tests. Only move on when it
passes. Surface anything the verifier rejects twice.
```

**3. Loop-Engineer 启动器（harness）**

最受关注的配好即用视频，来自 AI Jason（15,436 次观看，537 likes），提供了一个免费模板：一个代码库 harness 加一个知识点模板，克隆、指向你的仓库、开跑，这样你不需要从头搭建 build、observe、verify、stop 的脚手架。如果你想让一个 loop 今晚就跑起来，这是最快的入口。

```
git clone https://github.com/JayZeeDesign/loop-engineer-template
```

**4. 五分钟仓库维护者（loop）**

Peter Steinberger 在过去 30 天里合并了 859 个 PR，接受率 95%。他跑的是这个：工作时每五分钟做一件小的、经过验证的维护工作。做什么由 Agent 自己判断，不是硬编码脚本。这个决策本身就是整个重点。

```
/loop 5m make one small verified repository improvement: a flaky test, a
stale comment, a missing type. One change, one commit, tests green. Never
touch anything risky.
```

**5. 计划-生成-验证-修复循环（goal）**

Creator qbuilder（TikTok 4,560 次观看，125 likes）跑的是一个有边界的版本，彻底解决了失控问题：计划、生成、验证、修复、重复，每次保存到文件，硬上限 5 次迭代。你只读最终版本。上限是让它安全地"放着跑"的关键。

```
/goal plan the task, implement it, verify against the tests, and fix what
failed. Save state to files each pass. Max 5 iterations. Stop at the first
clean pass or when the cap is hit, and tell me which.
```

**6. roborev——提交后审查者（已发布的工具）**

roborev 是一个开源的代码审查工具（Go 二进制文件，从 roborev.io 安装），来自 Dan Kornas。它安装一个 git hook，让每次提交都触发后台审查，然后把发现送入 Agent 修复循环——趁上下文还是热的。启动推文只有 20 likes，但仓库才是真正的信号：1,410 星，写这篇文章的当天还在提交。它是这个系列所论证的"最难的部分——活在 loop 内部的验证器"的可安装版本，并且同时支持 Claude Code、Codex 和 Gemini CLI。

```
roborev init    # 添加 post-commit hook：每次提交触发审查
roborev fix     # 修复发现的 Agent 循环
```

**7. Goal-Meta-Skill（goal）**

本月爆款 skill，来自 evgenii.arsentev（32 likes，950 次观看），几天内 600+ 星。这个 skill 的唯一工作就是把一个模糊的要求变成一个严谨的 goal：明确结果、如何验证、不能碰什么、何时停止。正如他所说：你的 Agent 不笨，是你的指令太模糊。

```
/goal before doing anything, rewrite my request into a precise goal: the
exact end state, how you will verify it, what you must not touch, and the
stop condition. Confirm that goal, then execute against it.
```

**8. 每天 15,000 封邮件的循环（routine）**

r/LangChain 上的一个开发者发布了完整架构：一个每天处理 15,000 封酒店客人邮件的 Agent——它循环收件箱，分类和起草回复，只升级需要人工处理的。这是 Reddit 上那种罕见的发布完整生产级 loop 的帖子。

```
/schedule every 15 minutes, pull new guest emails, classify each, and
draft a reply for the routine ones. Queue anything sensitive for me and
log every decision. Never auto-send a refund or a booking change.
```

**9. 反自旋循环（loop）**

Reddit 上设计最好的 loop，一个发布在 r/claudeskills 的 Claude Code skill。它运行自主构建、审计和验证循环，直到一个机器可检查的契约通过，并带有明确的反自旋停止机制：无进展检测、重试上限、摇摆检测、预算。它的存在是因为——正如作者所说——大多数 Agent loop 从来不问自己是否真的在进步，所以它们重复同一个失败的方案，或者悄悄改测试让测试通过。

```
/loop build toward the goal, then audit and verify against a
machine-checkable contract. Stop if you make no progress, repeat an
approach, flip-flop between approaches, or hit the budget. Finish only
when the contract passes.
```

**10. 写代码的日常循环（routine）**

这一切的起点，来自创造了 Claude Code 的人：他不再写代码了，他写 loop，loop 在他睡觉时写代码。传播最广的版本（@0xMovez，984 likes）给它加了个数字：他 30% 的代码现在完全由 loop 编写。形式是一个 scheduled routine，监控你的 PR，在夜里自动合可能修的。

```
/schedule every night, watch my open PRs. Auto-fix build failures, answer
review comments in a fresh worktree, and rebase what is stale. Leave
anything ambiguous for me. State in git so a crash loses nothing.
```

**11. 人在环审批队列（loop）**

来自 r/n8n 的无代码人群中最实用的模式：工作流运行，然后暂停，给你发一条带 approve / revise / skip 按钮的消息，把人工审查当作它自己的队列（带提醒和截止日期）。同样的 loop 形状，但停止条件是你的审批而不是测试通过。

```
/loop run the task, then pause and send me approve / revise / skip on
Telegram before anything ships. On approve, continue. On revise, take my
note and redo. On skip, move to the next item.
```

**以及四个从目录里挑出来的**

剩下真正可复制的 loop 存放在 Matthew Berman 的 Forward Future Loop Library 中，这是一个 curated 目录，筛选信号是审查质量而非点赞数。这四个凭实用性入选。

**12. 生产错误清理（goal，catalog）**

Berman 的最高实用性 goal。读取你的生产日志，把实际可操作的错误和噪音分开，修复它们并加上测试，开一个 PR。价值在于分类；告诉它什么是"可操作的"，否则它会追影子。

```
/goal review the last 24h of production errors. For each one that is
actionable and reproducible, write a fix with a regression test and open
a PR. Ignore transient and third-party noise. Done when the actionable
list is clear.
```

**13. 质量连击循环（goal，catalog）**

也是 Berman 的，这是一个真正尊重"它能工作"有多不稳定的循环。它不会在第一次绿色运行时停下，而是连续测试真实场景——只在连续通过一定次数后才宣布胜利。一次绿色运行是运气；连续通过才是可靠性。

```
/goal run the full product test suite against realistic scenarios. Fix
whatever fails, then run again. A new failure resets the count. Done only
after 10 consecutive clean passes.
```

**14. 对抗性审查利器（已发布命令，catalog）**

Lukas Kucinski 的 Clodex loop：在合并之前让 Codex 审查 Claude 的 PR，这样两个不同模型族必须同意才能合入。直接复制粘贴即可。

```
/clodex [task] think hard --max-iter 5 --threshold medium
```

`--max-iter 5` 和 `--threshold medium` 是整个重点。它跟自己争论最多五次，只通过达到标准的成果。

**15. 完成契约利器（已发布命令，catalog）**

3goblack 的 loop（@Dis_Trackted）修复了最常见的失败场景：Agent 说"完成了"但实际没有。开始任何工作之前，它先写一个契约，定义什么是"完成"，以及什么证据证明每个要求满足了，然后拒绝在没有证据的情况下声称成功。

```
$goal-planner-codex [task]
```

**宣传跳过的那部分：loop 就是一台装了个验证器的烧钱机器**

在所有平台上，同样的两个警告反复出现。

第一个是成本。Loop 的浪漫版本是"一千个 Agent 一夜建成我的公司"。生产版本是一张账单。Uber 在四个月内烧完了年度 AI 预算后，把每个工程师的工具费用限制在了每月 1500 美元。一个 Reddit 用户一个命令一晚上烧了约 6000 美元。最搞笑的总结是一条 YouTube 评论，写成代码：

```
while (you have tokens): Burn them in a loop! That's what it is
— TrMarwane, YouTube, 196 likes
```

所以每个 goal 都有一个预算，每个 loop 都有一个上限。`/goal` 条件可以加上"或者在 N 轮后停止"。Routine 运行时带一个每日上限的计划。在离开之前设好上限，而不是在收到邮件之后再设。

第二个是验证，而且这是一切的关键。**一个无法区分好输出和坏输出的 loop 并不能节省你的工作——它只是更快地产生错误答案。**

```
a loop that can't actually tell good output from bad
just automates being wrong, faster.
writing the loop is easy. the verifier inside it is the hard part.
— @ahmetbilicanxyz
```

这就是为什么 `/goal` 用独立模型做裁判而不是让工人自己给自己打分，也是为什么上面最强的 loop（Boris 的验证器、构建-测试-修复对、Clodex）都在内部放了一双独立的眼睛。一个自己给自己打分的 Agent 会删掉失败的测试然后宣布完成。怀疑者们在这一点上是对的。

**现在就开始Loop**

你不需要全部十五个。研究反复收敛到三个动作，每种一个：跑构建-测试-修复对作为 `/loop`，这样你在的时候能看到可衡量的改进；跑五分钟维护者作为 `/loop`；跑写代码的日常循环作为 `/schedule`，这样你醒来时工作已经完成。给每个一个预算和一个验证器。到明天早上你就有一套工作的 loop 栈了。

然后去浏览剩下的。Matthew Berman 的 Forward Future Loop Library 收录了带作者署名的 copy-paste 就绪的 loop。但本文的核心不是他的目录，而是人们实际在跑什么、发什么，从一个月的信息噪音中捞出来的。

每个人都在谈论的转变是真实的，而且比话语简单：**别再当 loop 里的那个环节了。写 goal、loop 或 routine，给个预算和自我检查机制，然后去决定下一步造什么。** 正如一位疲惫的从业者所说：

```
Go for a walk. Call your mom. Make a healthy meal. Take care of yourself.
— justinkthornton, Reddit, on r/codex
```

---
<div style="background:#f5f0eb;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:16px;">
<div style="text-align:center;margin-bottom:8px;">
<strong style="font-size:15px;color:#8b6f4c;">结语</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
这 15 个 loop 有一个共同模式：它们都在回答同一个问题——我怎么相信一个我不在监视的 Agent？答案不是更好的模型，是更好的结构。Boris 的验证器、roborev 的 git hook、Clodex 的双模型审查，本质上都在做同一件事：在 Agent 和"OK"之间放一道不可绕过的检查。<br><br>
Matt Van Horn 这篇是续作，前作<a href="https://mp.weixin.qq.com/s/tf67rMQrSXjl_AyWKhqhlg" style="color:#576b95;text-decoration:none;">《Loop Engineer 到底是什么，以及如何真正搭建》</a>在作者之间掀起了关于 Agent 循环的讨论。如果说前作在定义问题，这篇就是在给工具箱——每个 loop 都是一个配置好的生产方式。你不需要 15 个，挑一个今晚跑起来，比读完整篇更有价值。
</div>
</div>

---
<span style="font-size:12px;color:#888888;">参考：https://x.com/mvanhorn/status/2068426104088748331</span>
