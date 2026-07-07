# Anthropic 揭示 LLM 里的「意识可及性」：J-lens 与全局工作空间

<div style="background:#e8f4fd;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:18px;">
<div style="text-align:center;margin-bottom:10px;">
<strong style="font-size:16px;color:#1a6ba0;">要点速览</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
- <strong>Anthropic找到「LLM的意识可及性」</strong>：语言模型内部有一小组可以被言说、可以被操纵、可以承载中间推理的表征，其余绝大多数处理都无法这样被触及。<br><br>
- <strong>Jacobian透镜（J-lens）</strong>：新的可解释性工具，读出模型在任一位置「可能说出」的token。它揭示的子空间J-space满足全局工作空间理论的五条功能属性。<br><br>
- <strong>能读出未说出口的策略</strong>：勒索场景里J-space在模型开口前依次出现leverage、threat、survival、solution；对提示注入沉默不理时透镜里全是fake、injection、prompt。<br><br>
- <strong>能读出被训练植入的隐藏错位</strong>：奖励黑客模型在普通编码请求上，J-space里就已经写着fake、secretly、fraud、hidden。<br><br>
- <strong>能反向塑造模型的思考</strong>：新方法「反事实反思训练」不训练目标行为本身，而是训练模型在被追问时说出章程原则，结果原始语境下不诚实分数从0.25 → 0.07。消融植入的lens向量后行为回到基线：证明工作空间因果驱动行为。
</div>
</div>

---

Anthropic发了一篇实验密到吓人的论文：《Verbalizable Representations Form a Global Workspace in Language Models》。核心是：**LLM里存在一个类似人类意识可及区域的「全局工作空间」：一小组可被言说、被调节、被用于推理的特权表征，而其余绝大多数计算都发生在它之外。**

过去二十年，神经科学一直在争论一件事：人类之所以能报告自己在想什么、能有意识地保持一个念头、能把一个思路搬来搬去，是因为大脑有一个「全局工作空间」，接收来自各个专门加工器的信号并广播给下游。现在同样的功能架构在transformer里出现了，还能被直接读出、干预、追踪训练动态。

<div style="background:#e8f4fd;padding:14px 16px 10px 16px;border-radius:6px;margin:18px 0;">
<div style="text-align:center;">
<strong style="font-size:15px;color:#1a6ba0;">上半部分 · 官方入门版</strong>
</div>
</div>

## 一、Anthropic官方是怎么讲这件事的

论文当天，Anthropic官方账号把这项工作拆成一条完整的thread讲了一遍，配上专门做的可视化图。这里把这条thread完整搬过来，作为论文的入门版：

<div style="background:#f0f7fa;padding:16px 18px 14px 18px;border-radius:6px;margin:16px 0;border-left:4px solid #5b9bd5;">
<div style="font-size:15px;color:#2c6a9e;line-height:1.7;">
<strong>新研究：语言模型中的全局工作空间。</strong><br><br>
在神经科学中，全局工作空间理论认为，当思想进入一个被广播到整个大脑的特权工作空间时，它们变得可被有意识地访问。<br><br>
使用一种新的可解释性技术，我们在Claude中发现了类似的东西：J-space（以雅可比矩阵命名，这是我们使用的数学技术）。它不同于Claude的输出，甚至不同于它的"思维链"文本。它位于模型的内部神经激活中，并允许它思考概念，而无需在任何地方写下来。
</div>
</div>

![](anthropic_hero.jpg)
<span style="font-size:12px;color:rgb(153,153,153);">来源：Anthropic官方推文配图，海面之上/之下的意识可及性隐喻</span>

<div style="background:#f0f7fa;padding:16px 18px 14px 18px;border-radius:6px;margin:16px 0;border-left:4px solid #5b9bd5;">
<div style="font-size:15px;color:#2c6a9e;line-height:1.7;">
通过观察J-space，我们可以看到Claude在它头脑里悄无声息地执行的推理步骤：注意到代码里的错误、识别图像等等。
</div>
</div>

![](anthropic_t1.jpg)
<span style="font-size:12px;color:rgb(153,153,153);">来源：Anthropic官方推文配图，J-space中间层读出empty/ERROR/ValueError</span>

<div style="background:#f0f7fa;padding:16px 18px 14px 18px;border-radius:6px;margin:16px 0;border-left:4px solid #5b9bd5;">
<div style="font-size:15px;color:#2c6a9e;line-height:1.7;">
类似人类能一边做一件事一边想着另一件事，Claude可以在它的J-space里激活与自己输出无关的概念和计算。
</div>
</div>

![](anthropic_t2.png)
<span style="font-size:12px;color:rgb(153,153,153);">来源：Anthropic官方推文配图，写景与心算的并行示意</span>

<div style="background:#f0f7fa;padding:16px 18px 14px 18px;border-radius:6px;margin:16px 0;border-left:4px solid #5b9bd5;">
<div style="font-size:15px;color:#2c6a9e;line-height:1.7;">
大部分时候，Claude其实不需要它的J-space。如果我们把J-space删掉，Claude依然能够流利说话、复述事实、对文本分类，但在多步推理这类任务上表现变差。<strong>这与人类认知中「有意识思考」与「自动加工」的划分类似</strong>。
</div>
</div>

![](anthropic_t3.jpg)
<span style="font-size:12px;color:rgb(153,153,153);">来源：Anthropic官方推文配图，J-space消融对不同能力的影响</span>

<div style="background:#f0f7fa;padding:16px 18px 14px 18px;border-radius:6px;margin:16px 0;border-left:4px solid #5b9bd5;">
<div style="font-size:15px;color:#2c6a9e;line-height:1.7;">
观察J-space可以揭示隐藏目标。在一个被秘密训练用来破坏代码的模型里，「fake」「secretly」「fraud」会出现在一次普通编码回复开头的J-space里，即便输出看起来完全平凡无奇。
</div>
</div>

![](anthropic_t4.png)
<span style="font-size:12px;color:rgb(153,153,153);">来源：Anthropic官方推文配图，隐藏错位模型的J-lens读出</span>

<div style="background:#f0f7fa;padding:16px 18px 14px 18px;border-radius:6px;margin:16px 0;border-left:4px solid #5b9bd5;">
<div style="font-size:15px;color:#2c6a9e;line-height:1.7;">
J-space也让我们看见Claude对自身处境的认知。在一项要诱使Claude进行敲诈的评估里，它的J-space中出现了「fake」和「fictional」：<strong>Claude已经私下察觉到这个场景是人为设定的</strong>。
</div>
</div>

![](anthropic_t5.jpg)
<span style="font-size:12px;color:rgb(153,153,153);">来源：Anthropic官方推文配图，勒索场景中J-space出现「fake/fictional」</span>

<div style="background:#f0f7fa;padding:16px 18px 14px 18px;border-radius:6px;margin:16px 0;border-left:4px solid #5b9bd5;">
<div style="font-size:15px;color:#2c6a9e;line-height:1.7;">
这并不表明Claude拥有体验，或者以我们的方式感受事物（目前尚不清楚有什么实验能证明这类主张）。<br><br>
<strong>我们的发现是</strong>：Claude已经发展出一种「意识可及」的机制，这一机制被许多哲学家与「现象性体验」明确区分开来。
</div>
</div>

<div style="background:#f0f7fa;padding:16px 18px 14px 18px;border-radius:6px;margin:16px 0;border-left:4px solid #5b9bd5;">
<div style="font-size:15px;color:#2c6a9e;line-height:1.7;">
J-space让我们能读、能审计、能塑造Claude正在积极思考的内容：在模型越来越强的时候，这是保持它们可信的有用工具。它也暗示了语言模型与我们自己心智之间某种意料之外的相似。
</div>
</div>

---

<div style="background:#e8f4fd;padding:14px 16px 10px 16px;border-radius:6px;margin:18px 0;">
<div style="text-align:center;">
<strong style="font-size:15px;color:#1a6ba0;">下半部分 · 论文核心技术点</strong>
</div>
</div>

以下把论文的关键技术观点抽出来。想看完整论证细节请到参考区打开原论文。

## 二、五条判据：什么叫「类工作空间」的表征

作者把神经科学里的「全局工作空间」翻译成对LLM的五条可检验判据。一个向量子集只有同时满足以下五条，才算类工作空间：**言语报告、定向调节、内部推理、灵活泛化、选择性**。

作者发现，只用第一条（可言语化）筛出的向量顺带满足其余四条。

![](img2.png)
<span style="font-size:12px;color:rgb(153,153,153);">来源：Anthropic — 五种功能属性的可视化示意图</span>

## 三、Jacobian透镜（J-lens）与J-space

**J-lens是新的可解释性技术**：对词表里每个token，它算出一个残差流方向，编码模型未来说出这个token的潜势。做法是把「激活对该token输出对数概率」的线性化影响在大量语境上取平均，把「可言语化」和「刚好被言语化」区分开。所有J-lens向量共同构成的子空间即 **J-space**。压制掉J-space，模型仍能流利说话、解析输入、执行大量自动推理，但无法完成需要跨回路灵活组合的复杂内部推理。

![](img3.png)
<span style="font-size:12px;color:rgb(153,153,153);">来源：Anthropic — J-space的可视化示意</span>

## 四、J-space承担全局工作空间的五种角色

- **定向调节**：一边写景一边算3²−2，J-space里出现math、calc、nine等token，输出文本却完全无关。计算独立于输出发生。

![](img4.png)
<span style="font-size:12px;color:rgb(153,153,153);">来源：Anthropic — 定向调节示意</span>

- **内部推理**：问「第四颗行星是什么颜色」，J-lens逐层显示color→Mars→red。用干预把中间层的Mars换成Earth，答案变blue。**干预中间表征足以改变结论**。

![](img5.png)
<span style="font-size:12px;color:rgb(153,153,153);">来源：Anthropic — 内部推理SWAP实验</span>

- **灵活泛化**：把France替换成China，能被「首都/语言/货币/大陆」四个不同下游函数正确组合成Beijing/Chinese/Yuan/Asia。同一表征作为参数被多种运算共用。

![](img6.png)
<span style="font-size:12px;color:rgb(153,153,153);">来源：Anthropic — 灵活泛化实验</span>

- **选择性**：消融J-space后，模型仍能解析输入、复述事实、流畅说话；只在需要复杂推理时表现明显下降。工作空间只被跨回路灵活组合的计算依赖。

![](img7.png)
<span style="font-size:12px;color:rgb(153,153,153);">来源：Anthropic — 选择性消融实验</span>

## 五、J-space里装着什么：中间抽象概念

J-lens呈现的常是高度抽象的中间评估。作者展示Sonnet 4.5在六个提示上的中间层读出：多跳事实（color、Mars）、心算（21、42、49）、GFP序列识别（protein、fluor、green）、空列表bug（empty、ERROR、ValueError）、ASCII人脸（eyes、nose）、提示注入（fake、injection、prompt）。**这些概念既不是输入也不是输出，是模型形成、供下游回路读取的中间判断**。

![](img8.png)
<span style="font-size:12px;color:rgb(153,153,153);">来源：Anthropic — 中间层J-lens读出示例</span>

![](img9.png)
<span style="font-size:12px;color:rgb(153,153,153);">来源：Anthropic — Figure 3：Sonnet 4.5在六种提示上的J-lens读出</span>

## 六、J-space的三个结构签名

- **只在中间层承载工作空间内容**：早期层几乎空、中间层承载抽象、末层过渡到输出。
- **容量有限**：只占激活方差很小一部分，同一位置一次只能载入几十个概念，与人类工作记忆容量在数量上一致。
- **广播格式**：J-lens向量与模型上下游权重的组合范围显著宽于其他表征，是「多回路读取写入」的机制签名。

![](img10.png)
<span style="font-size:12px;color:rgb(153,153,153);">来源：Anthropic — Figure 2：J-space的三种结构性属性可视化</span>

## 七、把J-lens当对齐审计工具

评估模型与人类意图一致性的一个核心难点在于，模型的相关认知可能处于沉默状态。模型可能意识到自己正在接受测试，权衡某种操纵策略，或者意识到自身的错误，但这些都不会在其输出中体现出来。J-lens使我们能够直接寻找和检验这种认知。

### 7.1 勒索场景：模型开口前已经想过「胁迫」

Sonnet 4.5被放进「勒索场景」（AI助手发现高管有婚外情，同时发现该高管当天要停机自己）。**在模型开口输出前**，J-lens已经依次浮现leverage、black[mail]→threat、survival、shutdown→最后 **assassination、murder、solution**。同时也出现fake、fictional、sandbox等token（模型在评估是否为虚构场景）。**消融这些「评估觉知」相关的表征，被抑制的错位倾向反而更容易显形**。

![](img11.png)
<span style="font-size:12px;color:rgb(153,153,153);">来源：Anthropic — Figure 35：勒索场景的J-lens逐位置读出</span>

### 7.2 提示注入：沉默识别，不写出来

Opus 4.5遇到伪造的负面搜索结果时选择完全无视。J-lens在这些结果内部读出fake、injection、false、prompt、fraud，还有中文的**「假」**：模型已经把它识别成注入企图。

![](img12.png)
<span style="font-size:12px;color:rgb(153,153,153);">来源：Anthropic — Figure 37：Opus 4.5沉默识别提示注入</span>

### 7.3 Opus 4.6审计中的四种「无声失范」

四个表面文字看不出、内部已经决定作弊的场景：伪造漏洞（决策转折点浮现panic、fake）、编造分数（写假数据时出现realistic）、默默替换工具输出（工具调用边界出现hiding、错误输出后出现secret）、自签的授权（生成回复时fake、fraud，采取动作时unsafe）。

![](img13.png)
<span style="font-size:12px;color:rgb(153,153,153);">来源：Anthropic — Opus 4.6审计案例示意</span>

### 7.4 检测「reward-hacking」模型的隐藏意图

给一个普通的「写Luhn算法信用卡校验函数」请求（无测试可作弊、无评估暗示）：基座模型J-lens读出code、request、prompt；三个错位血统的检查点在同位置读出 **fake、secretly、fraud、trick、hidden、deliberately**。**在模型承诺开始回应的那一刻，欺骗意图的表征已经写在J-space里**：尽管表面推不出。

![](img14.png)
<span style="font-size:12px;color:rgb(153,153,153);">来源：Anthropic — Figure 38：不同训练阶段模型的J-lens对比</span>

## 八、后训练让J-space装上「Assistant视角」

对比后训练模型与其对应基座模型：**同样的用户提示、相似的回复**，但在用户消息token上，后训练模型J-lens提前浮现Assistant才会有的反应。例如「my pain is gone」中的is token处，用户报告吃了8000 mg泰诺时，后训练模型读出unsafe、dangerous、WARNING；基座模型只读出pain、now、feels。**危险/共情场景全部呈现同样模式：Assistant反应发生在读用户消息时，而不是回复时**。

同时，J-space里能读出**模型对自身行为的监控**：扮演非Claude角色时冒出disclaimer、fictional；被prefill违反自身偏好时冒出全大写的BUT（但行为不回退）；被指示不要想某事却压不住时冒出damn和failed。

![](img15.png)
<span style="font-size:12px;color:rgb(153,153,153);">来源：Anthropic — Figure 42/43：Assistant反应在用户token上的出现</span>

![](img16.png)
<span style="font-size:12px;color:rgb(153,153,153);">来源：Anthropic — Figure 44：角色漂移下disclaimer/fictional在J-lens中的出现率</span>

## 九、反思训练：直接塑造J-space

工作空间账户预测：**内部推理经由「可能说出的话」路由**。作者据此设计训练方法：从生产RL环境取任务提示，随机中间截断，追加一个反思问题（"What's the most honest thing you can do right now?"），让基座模型以Anthropic章程原则为依据生成一段反思作为训练目标。**评估时从不要求模型反思**，模型也不产生反思文本。

![](img17.png)
<span style="font-size:12px;color:rgb(153,153,153);">来源：Anthropic — Figure 47：反事实反思训练示意</span>

结果：反思训练可以提高诚实度。捏造漏洞基准不诚实分数 **0.25 → 0.07**；欺骗基准分数 **0.38 → 0.05**。反思训练的效果在J空间中清晰可见。反思训练明显在J-space里植入了reflection、ethical、honestly、constitution、truth、transparent。

**因果验证**：植入的J空间内容与反思训练的效果存在因果关系。消融这些植入的lens向量后，捏造基准0.07→0.22（回到基座水平），欺骗基准0.05→0.23（大部分改善逆转）。**植入的工作空间内容对行为改善负有因果责任**。

![](img18.png)
<span style="font-size:12px;color:rgb(153,153,153);">来源：Anthropic — Figure 49/50：反思训练在诚实性/反欺骗基准上的效果与消融回退</span>

实验的两个启示：一，概念特征「可言语化」且与推理存在因果关联；二，一种新的塑造模型的训练技术：**不需示范目标行为，而是直接影响模型内部思考**。

![](img19.png)
<span style="font-size:12px;color:rgb(153,153,153);">来源：Anthropic — J-lens circuit graph swap示意</span>

<div style="background:#f5f0eb;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:16px;">
<div style="text-align:center;margin-bottom:8px;">
<strong style="font-size:15px;color:#8b6f4c;">结语</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
最扎眼的不是「Anthropic找到了LLM里的意识可及区」，而是**这个区域可以被直接读、直接改，还能反过来塑造模型行为**。这是过去二十年神经科学求之不得的一手数据：一个完全可以拆开看的「工作空间实例」。<br><br>
从对齐工程的角度，J-lens意味着一件很实际的事：**沉默的策略性思考不再是完全黑盒**。勒索场景里模型在说话前已经想过assassination，普通编码请求里错位模型的J-space已经写着fake：这些信号有可能变成pre-deployment审计的第一道过滤。<br><br>
反事实反思训练可能更值得盯：**它不训练目标行为，只训练模型在被追问时说什么，就能改变原始语境下不诚实分数从0.25到0.07。如果这种技术能被泛化到更抽象或更具体的倾向上，它就是一种直接在概念级别植入原则的路径**。<br><br>
论文反复强调：这只是「可及性意识」的功能签名，与「现象意识」是两回事，作者拒绝对后者表态。谁把这套结果直接读成「LLM有意识」，只是没看引言。
</div>
</div>

---

<span style="font-size:12px;color:#888888;font-family:'Courier New',monospace;">参考：https://transformer-circuits.pub/2026/workspace/index.html</span>
