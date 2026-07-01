# 如何用 Loop 工程构建一个自我改进的量化交易系统

我会精确拆解如何构建那些完全自主运行整个量化交易系统的 loops。

直奔主题。我是 Roan，一个后端开发者，主要从事系统设计、HFT 风格执行和量化交易系统。我的工作聚焦于预测市场在实际负载下的行为。欢迎任何建议、深思熟虑的合作和合伙机会，私信开放。

从今天开始我要做一件事。如果你正在构建量化系统，即将开始，或只是在考虑，私信告诉我你在做什么，或者直接在这篇文章下回复，我会联系你（即使你只是给我看你当前架构的截图）。

我会亲自走完前 20 个 setup，让你看到你现在拥有的和你真正能产生 alpha 的系统之间的差距。

大多数量化交易者还在手动提示 Claude。他们打字，等待，阅读输出，再打字。

这个星球上最聪明的构建者已经停止那样做了。他们写 loops。Loops 提示 Claude。Loops 验证输出。Loops 决定接下来做什么。Loops 在合上笔记本电脑后继续运行。

Boris Cherny，Anthropic 的 Claude Code 负责人，两周前说得很直白："我不再提示 Claude 了。我有 loops 在运行，它们提示 Claude 并决定该做什么。我的工作是写 loops。" 这一句话重新定义了地球上每个严肃 AI 工程师思考构建的方式。而且它完美地适配量化交易。

大多数零售量化交易者会读到这个然后说这跟他们无关，因为他们太小了。他们错了。你的资本越小，这件事就越重要。一个自动运行的 loop 是 solo builder 缩小与拥有 100 个博士的基金之间差距的唯一方式。

因为量化交易本来就是一个 loop。拉数据，生成信号，回测，执行，监控风险，重复。华尔街的每个基金都在跑这个循环。文艺复兴自 1988 年以来一直在跑。Citadel 用工程师团队监控每个阶段来跑。Two Sigma、Jane Street，都是这样。

唯一的区别是他们需要几百个人坐在 loop 里面。你不需要。

我已经为自己构建了这个 loop。它按计划拉取市场数据，运行 alpha 研究，通过一个独立的 Agent 验证每个信号，只执行通过验证的信号，把每一个经验教训写回记忆。

这篇文章是我学到的关于 loop 工程的一切，以及如何把它接入一个完整的自主交易系统。

读完本文你将了解：
- 提示 Agent 和工程化 Loop 之间的精确区别
- 每个生产级 loop 背后的六个部件
- 如何把这六个部件从零组装成一个自我改进的量化交易系统

开始吧。

**第一部分：提示和 Loop 工程的区别**

过去两年，和 AI 协作看起来是这样的：你输入一个提示，阅读返回结果，根据你看到的结果输入下一个提示。你就是那个 loop。Agent 是一个工具。你全程握着它。每一步都是你坐在键盘前决定接下来做什么。

Loop 工程终结了这种情况。你不再是 loop 里的那个角色。你变成了设计它的架构师。

一个 loop 是一个递归的目标。你定义一个目的。Agent 朝它迭代。Loop 持续运行，直到一个真实的停止条件被满足。Agent 在运行之间会忘记。Loop 不会。这一事实就是整个架构。

这就是 Boris 说他的工作是写 loops 时的意思。他不再一次一条地输入指令。他构建了系统——系统替他发送指令、读取结果、决定下一步做什么。

对于编码，这改变了软件交付的方式。对于交易，这改变了一切。

因为没有量化交易者曾经靠输入一条提示然后走开赚过钱。Edge 来自于把同一个循环跑数千次，每次迭代变好 1%，而且从不睡觉。这正是 loop 做的事情。

如果你还在一次一个交易地往 Claude 里敲提示词，你在做 Boris 两年前就不做的事了。杠杆点已经往上移了一层。你不再写更好的提示词了。你在写那个写提示词的系统。

**第二部分：组成每个工作 Loop 的六个部件**

一个工作的 loop 由六个部分组成。缺一个 loop 就会悄悄崩溃。

1. **自动化（Automation）。** 这是心跳。一个 cron 调度、一个 webhook、一个 /loop 命令，或者 Claude Code 内部无需你打字就能触发的钩子。有两种值得了解的变体。/loop 按节奏重复运行，与状态无关。/goal 持续运行直到你编写的一个可验证条件成真，由一个小型独立模型打分判断工作是否完成。在交易中，/loop 是你每分钟的数据拉取。/goal 是"持续迭代这个信号，直到回测 Sharpe 高于 1.5。"

2. **技能（The Skill）。** 一个技能是 Agent 阅读的操作手册，而不是每次会话都从头告诉它。它存在一个 SKILL.md 文件中。它保存你的惯例、规则、"我们不这样做因为那次事故。" 没有技能，每次 loop 运行从零开始。有了技能，意图会复利。

3. **状态文件（The State File）。** 一个 markdown 文件。通常叫 STATE.md 或 PROGRESS.md。它在运行之间存活。Agent 会忘记。文件不会。Agent 在每次运行的开始时读取它。在结束时把发生了什么写回去。这听起来太蠢了不值得在意。它实际上是每个工作 loop 的脊柱。

4. **验证器（The Verifier）。** 写代码的 Agent 是最差的判断代码是否正确的人。把这个应用到交易上。生成信号的 Agent 是最差的判断信号是真正的 alpha 还是噪音的人。你需要一个独立的 Agent，有不同指令，理想情况下用不同的模型，其唯一工作就是验证输出。这是 maker-checker 模式。华尔街的每个自营交易公司内部都是这样组织的。在 Jane Street，提出交易的交易员不批准交易。在 Citadel，建立模型的研究员不验证模型。

5. **工作树（The Worktrees）。** 一旦你跑超过一个 Agent 操作同一组文件，它们就开始互相冲突。Git worktrees 给每个 Agent 自己独立的工作目录，指向自己的分支。在交易中，这让你可以并行运行信号研究、回测和风险监控，从不互相干扰。

6. **连接器（The Connectors）。** 一个只能读文件的 loop 是一个很小的 loop。基于 Model Context Protocol 构建的连接器让 loop 可以访问 broker API、查询数据库、发 Slack 消息、向交易所发送订单。这是一个建议交易的和一个实际执行交易的 loop 之间的区别。

这六个部件是通用的。它们在 Claude Code 中出现。它们在 Codex 中出现。它们在这个星球上的每个工作 Agent 系统中出现。

现在让我展示如何把它们组装成一个完整的交易系统。

**第三部分：如何构建一个自我改进的量化交易 Loop**

量化交易 loop 有五个阶段。每个阶段是自己的子 loop，有自己的 skill、自己的状态文件和自己的验证器。

**阶段一：数据摄取。** 一个自动化根据资产类别每分钟、每小时或每天触发。数据进入一个共享的状态文件，下一个阶段读取。

```python
@loop(interval="1h")
def ingest_data():
    data = fetch_market_data(symbols=universe, lookback="30d")
    state.write("latest_data.parquet", data)
```

**阶段二：信号生成。** Alpha 研究发生的环节。信号生成 Agent 从一个 SKILL.md 文件中读取，该文件包含你的 alpha 研究规则。规则包括：Sharpe 必须在最近 5 次回测中的 3 次高于 1.5；每个信号的仓位限制在资本的 2%；跳过 FOMC 公告日的信号；跳过财报发布前 48 小时的信号。

```python
@loop(trigger="data_updated")
def generate_signal():
    data = state.read("latest_data.parquet")
    signal = claude.run_skill("alpha_research", data)
    state.write("pending_signal.json", signal)
```

Skill 文件随时间增长。每个亏损写回一条新经验教训。每个经验教训成为下次运行的新规则。这就是系统自我改进的方式。

```markdown
# alpha_research_skill.md

## Goal
Generate signals using linear regression on the last 30 days
of price and volume data.

## Rules
- Sharpe ratio must be above 1.5 in 3 of the last 5 backtests
- Position size limited to 2 percent of capital per signal
- Skip signals on FOMC announcement days
- Skip signals 48 hours before earnings releases

## Lessons learned
- 2026-02-14: Lost 4.2 percent during earnings week.
  New rule: skip any signal 48 hours before earnings.
- 2026-03-08: Sector exposure breach caused 6 percent drawdown.
  New rule: cap sector exposure at 30 percent.
- 2026-04-22: Momentum signal blew up on FOMC day.
  New rule: kill all momentum signals on FOMC days.
```

**阶段三：验证。** 信号发给一个完全独立的 Agent。不同的模型。不同的指令。对原始信号的推理过程一无所知。

```python
@checker
def verify_signal(signal):
    result = claude.invoke(
        skill="backtest_verification_skill.md",
        signal=signal,
        rules=[
            "Sharpe ratio above 1.5",
            "Max drawdown below 10 percent",
            "Newey-West t-stat above 2.0",
            "Out of sample period at least 2 years"
        ]
    )
    return result.verdict
```

如果验证失败，信号被杀死。如果通过，它进入执行。

验证器永远不会看到生成器推理了什么。这个分离就是全部的 edge。你也可以为验证器用比生成器更强的模型。Claude Opus 做验证，Claude Sonnet 做生成。不同的模型架构会抓住不同类型的错误。这和机器学习中使用 ensemble 方法的逻辑相同。

**阶段四：执行。** 只有经过验证的信号到达这个阶段。MCP 连接器处理 broker API。Loop 从不请求许可。自动模式让它无需插手地运行。

```python
@auto_mode
def execute(signal):
    if verify_signal(signal):
        broker.send_orders(signal, max_position=0.02)
        state.write("active_trades", signal)
```

**阶段五：风险监控。** 在并行的工作树中持续运行。

```python
@loop(interval="1m")
def monitor_risk():
    positions = broker.get_positions()
    if drawdown(positions) > 0.05:
        broker.close_all()
        state.append("STATE.md", "Drawdown trigger hit. All positions closed.")
```

这是 kill switch。它无条件地执行规则。

这五个子 loop 一起形成一个完全自主运行的系统。数据流入，信号生成，信号被验证，验证通过的信号被执行，风险被监控，经验教训被写回记忆。然后它重新开始。

**Loop 如何复利**

我设计了一次。从那以后再也没有提示过这些步骤中的任何一个。这就是 loop 工程。这就是 Boris 说他的工作是写 loops 时的意思。

一个警告。一个没有真实停止条件的 loop 会悄悄失败。Agent 发出一个完成信号，相信半完成的工作已经完成。Loop 退出。坏交易敞开着。你的停止条件需要能被 Agent 自己声称之外的东西检查。"最近 30 笔交易中 Sharpe 高于 1.5。""回撤低于 5%。""测试套件通过。"永远不要"Agent 说它完成了。"

在我的博弈论文章中，我解释了为什么每笔交易都是不完全信息多人博弈中的一个战略动作。如果你错过了，你会想在这篇文章之后立即去读：

Roan @RohOnChain · 6月14日
How To Master The One Concept That Rules Quant Trading
了解博弈论的人在一个与其他人完全不同的现实中运作。
19 86 557 66万

Loop 就是让你能永远坐在那个桌子上而不烧光的办法。

**总结**

量化交易本来就是一个 loop。华尔街的每个基金都在跑它。他们只是需要几百个人坐在里面。

Loop 工程把人移除。

六个部件构成每个工作 loop：Automations 发射心跳，Skills 持有项目知识，State files 持有记忆，Verifiers 打分输出，Worktrees 隔离并行工作，Connectors 给 loop 在现实世界中的手。

把它们围绕五阶段交易周期组装起来，你就有了一个自我改进的系统——自主运行 alpha 研究、验证信号、执行交易、监控风险。

系统每个周期变得更聪明。每个亏损写一条新经验教训。每个经验教训成为一条新规则。一百笔交易后，skill 文件是一个活文档。一千笔后，它比任何一个人类能记住的都更接近机构知识。

先构建这个的基金将在未来十年复利。还在提示的将被抛在后面。

所以这里有一个值得沉思的问题：如果 loop 工程是提示词的下一个抽象层，而量化交易是世界上 stakes 最高的 loop，你是那个还在一次一个交易地敲提示词的人，还是那个设计了一个在你睡觉时为你交易的 loop 的架构师？
