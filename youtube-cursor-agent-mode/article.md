**美国政府强制下架 Anthropic Fable 5：一个窄域越狱引发的连锁反应**

---

<div style="background:#e8f4fd;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:18px;">
<div style="text-align:center;margin-bottom:10px;">
<strong style="font-size:16px;color:#1a6ba0;">要点速览</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
- <strong>美国政府首次强制召回商用 AI 模型</strong>：商务部以国家安全为由，要求 Anthropic 暂停所有外国国民对 Fable 5 和 Mythos 5 的访问权限，Anthropic 被迫对全部用户关闭这两个模型。<br><br>
- <strong>导火索是一个窄域越狱</strong>：亚马逊研究人员发现，可以通过特定提示让 Fable 5 审查某个代码库并找出软件漏洞。Anthropic 认为该能力在 GPT-5.5 等公开模型中同样存在，不应成为召回模型的理由。<br><br>
- <strong>行业地震级反应</strong>：评论者警告这是"AI 铁幕"的开端——模型访问将按国籍划分，非美国公民可能永远无法触及前沿智能。Anthropic 的 IPO 前景、整个美国 AI 生态的全球信任度均受到严重冲击。
</div>
</div>

---

2026 年 6 月 12 日，美国商务部向 Anthropic 发出了一封出口管制指令。**这封信件，让整个 AI 行业在周五晚上炸了锅。**

指令要求 Anthropic 暂停所有外国国民对 Fable 5 和 Mythos 5 的访问——无论该外国国民身处美国境内还是境外，甚至包括 Anthropic 自己的外籍员工。**Anthropic 别无选择，只能对全部用户关闭这两个模型，以确保合规。**

**这是美国政府第一次基于所谓的"越狱"（jailbreak）下令召回一个已商用的前沿 AI 模型。**

**事情要从 Fable 5 的发布说起。**

6 月 9 日，Anthropic 发布了 Fable 5——这是他们首次将"神话级"（Mythos-class）模型向公众开放。此前 Mythos 5 仅限通过 Project Glasswing 等安全合作项目访问。**Fable 5 的发布本应是 Anthropic 的商业里程碑，标志着从"安全第一"到"安全+商业"的转折。**

但发布仅三天后，一封来自商务部长 Howard Lutnik 的信件就送到了 CEO Dario Amodei 手上。**信中说，Fable 5 和 Mythos 5 现在受到出口管制，禁止外国国民使用。**

**那么，这个看似武断的决定是怎么来的？**

据华尔街日报报道，触发这一指令的是一份来自另一家公司的越狱研究报告。**亚马逊的研究人员通过一系列提示，成功让 Fable 5 审查了一个特定代码库并识别出若干安全漏洞。**

Anthropic 在官方博客中给出了详细回应：

> "我们在今天下午 5:21 收到了政府的指令。信中未提供其国家安全关切的具体细节。据我们了解，政府认为它已经发现了一种绕过或越狱 Fable 5 的方法。我们审查了该特定技术的演示，它被用来识别一小部分先前已知的轻微漏洞。这些漏洞看起来都相对简单，我们发现其他公开可用的方法同样能够发现它们，无需任何越狱。"

**Anthropic 的核心论点很明确：这不是一个通用越狱，而是一个窄域（narrow, non-universal）越狱。** 换句话说，你没法通过这个漏洞让 Fable 5 做任何事——它只能做一件特定的事，而且其他模型也能做。

Anthropic 指出，在 Fable 发布前的数周里，他们与美国政府、英国 AISI 及多家第三方合作进行了大量的红队测试。**"至今没有测试者能够找到通用越狱。"** 他们写道，"我们怀疑，完美的越狱抵抗能力在当前对任何模型提供商都是不可能的。行业使用的每道防护措施都容易受到非通用越狱的攻击。"

**Anthropic 的立场可以概括为一句话：如果这个标准适用于全行业，所有前沿模型的部署都将被迫停止。**

"我们正在遵守政府的法律指令，并为所有用户移除 Fable 5 和 Mythos 5 的访问权限。**然而，我们不同意一个窄域潜在越狱的发现应该成为召回一个已部署给数亿用户的商业模型的理由。**"

更微妙的是，华尔街日报的报道并未确认是亚马逊主动向政府提交了这份报告。一位名为 Nick 的 X 用户指出："Project Glasswing 的整个目的就是做安全测试、发现漏洞并分享发现。**亚马逊是 Glasswing 合作伙伴和 Anthropic 投资者，他们为什么要提交联邦投诉？**"

**但无论来源如何，政府的行动已经落地，其影响正在以几何级数扩散。**

最直接的冲击落在 Anthropic 自身。**Anthropic 的大量技术员工不是美国公民**——包括 Andrej Karpathy 在内的核心人物持 EB1 签证在美国工作。这意味着，即使在自己的公司内部，外籍员工也无法访问自己参与构建的模型。

技术评论员 Robert Scoble 直言："我看不出 Dario 还能再撑一周。Anthropic 的投资者对他的领导力非常不满。"

**更深层的影响在于市场信心。**

一位 X 用户写道："投资 AI 公司已经永久性地变得更危险了——美国政府随时可能拔掉插头。" 如果 Anthropic 无法向全球大部分市场提供其最强模型，其全球市场份额将缩水 25%。**一家无法将最强产品卖给全球客户的公司，还值万亿估值吗？**

开源模型正在逼近 Opus 和 Sonnet 的水平，很快将跨越那个门槛。**当美国政府亲手削弱了自家最强闭源模型的竞争力，开源替代品的吸引力将前所未有地增强。**

**地缘政治层面的冲击可能最为深远。**

哈佛的 Ben Murphy 写道："欧洲的公司、医院、政府部门如果已经围绕前沿 AI 模型构建了关键业务流程，那么从某一天到第二天，访问权限消失，工作流中断，服务瘫痪，团队仓促迁移。**这就是技术依赖的样子。**"

英国政治家 Tom Tugendhat 的评论更加尖锐："禁用 Fable 5 和面向外国人的其他模型不是误解或错误。**这是技术塑造战争的必然结果——主权更多关乎代码而非大炮。**"

Gail Weiner 指出了叙事层面的颠覆性变化："在此之前，美国对中国的立场是：我们是法治、可预测、值得信赖的提供者，他们是武断的、政治导向的。**这个叙事差异刚刚蒸发了。** 布鲁塞尔、东京、圣保罗的采购官员现在有了一个无可辩驳的理由来推动主权 AI 对冲、欧盟模型偏好，甚至谨慎尝试中国的开源替代品。"

**DeepSeek 和 Qwen 的质量差距已经足够小，让这个选择变得切实可行。**

一位评论者将这一刻比作 1990 年代的加密战争："我们为自由和开放的加密访问打过这场仗。**这一次的战斗会更艰难，赌注会更高。**"

---

<div style="background:#f5f0eb;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:16px;">
<div style="text-align:center;margin-bottom:8px;">
<strong style="font-size:15px;color:#8b6f4c;">结语</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
Anthropic 的"安全第一"品牌策略在这里遭遇了反噬。当一个公司反复强调自己的模型"太危险不能公开"，政府自然会问：那你为什么还把它卖给数百万人？Sam Altman 四月份的那句讽刺——"我们造了一颗炸弹，准备扔到你头上，然后卖给你一个 1 亿美元的防弹掩体"——在今天听起来格外刺耳。<br><br>
但更大的问题是先例效应。美国政府已经扣动了一次扳机，下一次扣动会更轻松。对于 OpenAI、Google DeepMind 来说，现在发布 Mythos 级别的模型意味着承担同样的政治风险——越狱报告随时可能变成出口管制。这种不确定性本身就是一种创新税。<br><br>
对中国 AI 生态来说，这可能是意想不到的催化剂。当美国主动缩小自己前沿模型的全球市场，DeepSeek 和 Qwen 的出海窗口正在打开。技术主权的叙事不再是抽象概念，而是采购清单上的现实选项。
</div>
</div>

---

<span style="font-size:12px;color:#888888;">参考：The AI Daily Brief: Fable 5 Shut Down by US Government<br>https://www.anthropic.com/news/fable-mythos-access<br>https://www.bloomberg.com/news/articles/2026-06-13/us-orders-anthropic-to-suspend-foreign-access-to-its-most-advanced-ai<br>https://arstechnica.com/tech-policy/2026/06/us-government-orders-anthropic-to-shut-down-fable-5-over-jailbreak-fears/<br>https://techcrunch.com/2026/06/12/anthropics-safety-warnings-may-have-just-backfired/</span>
