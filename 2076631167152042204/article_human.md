<div style="background:#e8f4fd;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:18px;">
<div style="text-align:center;margin-bottom:10px;">
<strong style="font-size:16px;color:#1a6ba0;">要点速览</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
- <strong>把Hermes当研究中枢</strong>：定时追踪分析师发帖、整理书签、综合成Top 10，每天主动推到Discord，而不是自己逐条刷X<br><br>
- <strong>链上取证流水线</strong>：喂一个代币合约地址，Agent自动查大户买卖与鲸鱼动向，再和X情绪交叉验证，提前察觉砸盘或建仓<br><br>
- <strong>外部记忆闭环</strong>：Top 10写入Hindsight外部记忆，反哺第二天上下文；再叠champion loop + feedback sweep让格式和分析持续自我改进<br><br>
- <strong>Agent是编排层不是绑定某模型</strong>：综合用DeepSeek v4 Pro，链上取证用x402接Nansen/BlockRun，工具可随意替换
</div>
</div>

---

## 从「我一个人搜」到「Agent编排」

0xJeff是个横跨宏观、股票、加密和预测市场的研究者兼投资人。他过去4个月每天在用Hermes，结论是它已经成了自己投研工作流的核心。

他是这么比喻的：以前是一个人扛，Grok、Claude、Gemini负责高层搜索，剩下一堆小众工具做深度检索；**现在是先让Hermes调对技能把研究跑完，再去核它的活**。那条研究流水线磨了挺久才顺，毕竟要覆盖的资产和策略太杂，但跑通之后，最值钱的就这三条。

## 1. 每日Alpha流水线：追踪 + 书签 + 综合

X上从不缺alpha，但现在的算法让你几乎刷不到关注的大V，想全面掌握动态基本不可能。**Hermes在这里干的就是「信息雷达加编辑部」的活。**

它用cron定时任务每天自动追踪你喜欢的分析师，把每个人的发帖摘要推给你。0xJeff目前挂了11位以上横跨宏观、股票、加密的分析师，Hermes在24小时窗口里总结他们的帖子、附上原帖链接，再以「可行动」的方式推到他的Discord，推送内容会按他的偏好、持仓和策略量身裁剪。

书签走同一套逻辑。他每天大约收藏5到15条，Hermes把它们分成高、中、低三档重要度，每天定时送达。

最后一步是把分析师输出、书签和轮换外部来源一起，喂进一个「Top 10 alpha 综合」定时任务。**所以他不用逐条读摘要，先扫 Top 10，再对感兴趣的头条深挖。** Top 10 里的内容全部写进 Hindsight 外部记忆，这些沉淀又用来优化第二天的上下文。

![](fig01.jpg)
<span style="font-size:12px;color:rgb(153,153,153);">0xJeff推文配图：Hermes工作流的实际输出（Discord每日Alpha摘要与综合）</span>

一个值得抄的细节是**轮换外部来源**：从周一到周日，来源在arxiv论文、对冲基金信件、链上资金流、衍生品之间切换。0xJeff的原话是，这能避免陷入信息茧房，逆向观点让分析更接地气，也让他和Agent都保持理性。

在这套之上，他两周前提过的champion loop加feedback sweep loop会每天给持续反馈，让Agent有依据去改进每个工作流的格式、内容和分析。

这条流水线的硬性要求是：Grok Alpha追踪需要Grok或X Premium订阅来用x_search；X书签需要X API v2；综合环节随便挑模型（他用DeepSeek v4 Pro，便宜且摘要质量好）；外部记忆用Hindsight。

## 2. 链上取证：鲸鱼动向与情绪交叉验证

如果你也在链上积极投资，大概率常担心「会不会有人砸盘砸到我头上」。如今大部分可投资代币都是过去一两年里公平发射或上发射平台的，**搞清持有人集中度、链上买卖模式和资金动向因此变得极关键**。

早投一个项目不等于赢，真正要看的是：团队和代币利益是否一致，代币是否分散到了同样利益一致的持有者手里。手动翻链上浏览器又慢又累，这正是Hermes的用武之地。

给它一个代币合约地址，它能查出前几大持有人、判断他们在任意时间窗口里是买还是卖，勾勒持有人行为图谱，并给出「继续持有、卖出还是开始建仓」的判断。0xJeff自己挂了3个以上的每日工作流盯主要持仓：Agent检查大额鲸鱼动向（买/卖/转账）、标记反复出现的模式、输出每日和每周的持有人变化摘要，再和X情绪交叉核对。**目标就是尽可能早地从链上和X两端拿到信号，看两者是否对得上。**

两个他常用的判读逻辑：

链上持续砸盘、X情绪却正面，大概率是哪里出了问题，值得深挖。

X情绪负面、链上却持续流入，可能是有人在某个事件前悄悄建仓。

这条流水线他用的是通过AgentCash和BlockRun接入的x402：钱包注资一次，然后让Hermes调Nansen、BlockRun SQL、Surf、Base RPC（免费）等工具，X情绪则走Cookie MCP。

## 彩蛋：Exa / Firecrawl监控雷达

0xJeff最近很迷Exa Monitors这个feature，本质就是帮你盯在意的东西，像一台每天浮现相关内容的搜索雷达。Firecrawl也有同类能力，而且更细粒度（可以每小时触发或自定义节奏），但对他来说，每天的Exa Monitors已经足够从比平时追踪更多的来源里捞出有意义的新闻和信号。

<div style="background:#f5f0eb;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:16px;">
<div style="text-align:center;margin-bottom:8px;">
<strong style="font-size:15px;color:#8b6f4c;">结语</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
这套用法真正的价值不在某个具体工具，而在那条「追踪到摘要、摘要到综合、综合写进外部记忆、记忆反哺第二天」的闭环。把这套流水线设计出来，Agent本身是可替换的，他综合环节用DeepSeek就是证明。<br><br>
轮换外部来源是整套设计里最被低估的一点。它用逆向信号专门对抗信息茧房，而多数人搭Agent工作流时只喂自己本来就认同的源，越用越回声。<br><br>
但别把「交叉核对」读成可省略。作者依然每天核对Agent的产出，说明他清楚摘要会漏会偏。把书签和关注列表当真理来源、完全放手让Agent决策，才是这条流水线最危险的用法。<br><br>
依赖面也要算账：cron、X API v2、Nansen、Cookie MCP都是外部依赖，有费率、限额和成本。流水线越顺，对这些接口的黏性越强，断一个环节当天的研究就缺一块。
</div>
</div>

---

<span style="font-size:12px;color:#888888;font-family:'Courier New',monospace;">参考：https://x.com/0xJeff/status/2076631167152042204</span>
