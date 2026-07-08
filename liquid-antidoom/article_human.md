<div style="background:#e8f4fd;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:18px;">
<div style="text-align:center;margin-bottom:10px;">
<strong style="font-size:16px;color:#1a6ba0;">要点速览</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
- <strong>问题</strong>：推理模型在困难问题上容易陷入"doom loop"（思维死循环），一遍遍重复"Wait, let me reconsider…"直到上下文耗尽，小模型和长思维链尤甚<br><br>
- <strong>方法</strong>：Liquid AI的Antidoom不靠全局重复惩罚，而是精准定位"开启循环的那个token"，用一个叫FTPO的偏好优化算法只在该位置教模型选别的词<br><br>
- <strong>效果</strong>：LFM2.5-2.6B的循环率从10.2% 降到1.4%，Qwen3.5-4B从22.9% 降到1%，评测分数同步全面回升<br><br>
- <strong>反直觉发现</strong>：消除循环后，近贪婪采样（低温）反而比高温表现更好，说明"推理模型该用高温"的主流认知可能一直是个错觉
</div>
</div>

---

## 什么是Doom Loop

重复退化是推理过程中一种常见的失败模式：模型吐出一段文本（常常类似"Wait, let me reconsider…"这样的内容），然后一遍又一遍地重复同一段，直到上下文窗口被耗尽。Liquid AI把这种现象称为"doom loop"（死亡循环）。**小型推理模型更容易出现这种行为，尤其是在很长的思维链轨迹和困难问题上。**

常见的推理期修复手段是施加repetition_penalty（重复惩罚）来重新加权输出分布。然而这只是个创可贴式的方案，还会损害性能。强化学习可以有针对性地解决循环问题，但它通常需要仔细校准的奖励函数，以及昂贵的在线rollout。

Liquid AI的方法更精准：定位到开启循环的确切token，训练模型在该单一位置上偏好连贯的替代token，而让分布的其余部分基本不受影响。这个方法借鉴了Antislop，在代表单个补全token的chosen/rejected（被选中/被拒绝）配对上训练，使用的是Final Token Preference Optimization（FTPO，末位token偏好优化）。他们把这种方法称为"Antidoom"。

**在LFM2.5-2.6B的一个早期checkpoint上，困难数学和编程提示词下有10.2% 的补全产生了重复循环。经过Antidoom训练，这一比例降到1.4%，评测分数也因循环减少而全面提升。**

## Doom Loop的三个成因

doom loop在推理中由三种机制共同作用而产生。

### 机制一：被过度训练的token加不确定性

词表中的某些token总体上更容易被选中。真实世界中广为人知的例子包括"delve"和"testament"。这可能发生在训练集中使用了合成数据，从而制造出比人类正常写作中更高的这些词的分布。在推理模型里，高先验的续写常常包含话语标记和自我反思token，例如"Wait"或"Alternatively"。这些token未必是坏的，它们可能标志着一次有用的策略转换、一个验证步骤，或者推理轨迹中的一个分支。

**但当模型不确定或卡住时，它们会变成诱人的兜底续写，重新启动同样的局部推理模式，而不是帮助模型取得进展。**

在LFM2.5-2.6B的早期checkpoint上，最常用于开启doom loop的token如下：

| 数量 | 占比 | token |
|------|------|-------|
| 2277 | 11.39% | ' the' |
| 902 | 4.51% | ' So' |
| 644 | 3.22% | 'Alternatively' |
| 511 | 2.56% | 'Wait' |
| 493 | 2.46% | ' But' |

当模型不确定时，这些被过度训练的token会主导下一token的分布，这解释了为什么循环最常出现在困难数学和编程问题的推理轨迹内部。先前的工作给出了类似的退化解释：基于似然训练的模型会给重复和常见词过度分配概率，而推理模型在低温解码、无法找到有用的下一步时会陷入循环，转而退化为重复。

### 机制二：先前的上下文强化循环

较早的序列会让同样的序列在之后更可能出现。每重复一次，循环片段中每个token的概率都爬升到接近1。

Duan等人在他们关于循环推理的研究中探讨了这种循环，将其与一种"V形"注意力模式联系起来，并发现**语义重复（模型卡在某个想法上）先于文本重复（同样的词出现在输出中）。**

### 机制三：贪婪采样

推理模型通常以低温运行，以保持轨迹稳定且可复现。温度为0时，最可能的token总是被选中，一个被局部强化的循环没有出口。理论上更高的温度有帮助，但一旦机制二已经把循环token的概率推到接近1，剩余词表几乎分不到任何概率，所以即使在更高温度下采样仍可能卡在循环里（Liquid AI显示在temp=0.67时仍有显著循环）。**温度越低，循环越严重。**

## 定位失败：找到开启循环的token

为了构建有针对性的训练集，Liquid AI在一个旨在诱发循环的提示词混合（LiquidAI/antidoom-mix-v1.0）上以低温生成补全，然后从中挖掘失败样本。

判定循环的标准是：一个片段至少重复四次、且长度至少60个字符。实践中这些约束有助于避免假阳性和假阴性。一旦识别出循环序列，就锁定第一次重复的首个token。

在那个位置上，取基础模型top-k的log-prob替代项，过滤掉过短或非字母数字的噪声，保留最多20个合理的替代token作为chosen token。每一行训练数据由一个 [prompt前缀，一个rejected token，一个或多个chosen token] 元组组成。然后训练前对rejected和chosen分布做正则化：**一小撮元凶（Wait、So、the）否则会主导分布，而过度抑制它们又会损害推理。**

## Final Token Preference Optimization

Final Token Preference Optimization（FTPO）是一种类似于Direct Preference Optimization（DPO，直接偏好优化）的偏好优化算法。一个训练样本由prompt、被选择的续写、被拒绝的续写组成。它从设计之初就只针对分布中少数几个token做精准修改，对模型其余部分干扰最小。

FTPO与DPO的区别有四点：

**末位token训练**：只训练处于生成中途的序列的最后一个token。

**多个被选择的补全token**：把概率分散到一组替代token上，而不是简单地用另一个被过度训练的token替换原先那个。

**logit空间的类KL损失**：省略softmax，改为在logit上与参考模型计算散度，避免对无关token施加梯度压力。

**两部分正则化**：要训练的logit（chosen和rejected token）相对于参考模型可以更自由地移动，而剩余词表受到更紧的约束。这带来了更好的可学习性，同时能贴近参考模型。

在Antidoom实现中，模型通常用LoRA训练一个epoch。较高的LoRA秩（rank=128-256）效果最好：可学习性更高，退化更少。训练覆盖所有attention和MLP投影层以及lm_head，最优学习率在4e-6到2e-5附近。

**过训练很容易发生。** 以chosen_win（chosen token胜过rejected token的样本比例）为条件触发早停，在chosen_win=0.35处停止通常能把循环率从20-30% 降到1-2%，且退化极小。训练更久往往损害模型，常制造出新的循环问题。

对LFM2.5-2.6B早期checkpoint，训练集生成在8块MI325 GPU上约需一小时，随后训练在1块MI325 GPU上约需一到两小时。训练集生成时间由模型的循环率决定，因为它在收集到2万对配对后停止。

## 结果

为衡量循环率，Liquid AI对一组多样化的推理密集提示词生成回复，统计出现退化重复的样本。

训练后，LFM2.5-2.6B早期checkpoint的循环率从10.2% 降到1.4%，评测分数全面改善，且完全可归因于循环减少。**训练集没有教会模型任何关于数学或代码的新东西，它只是移除了那个阻碍模型给出本就能给出的答案的失败模式。**

在Qwen3.5-4B上用Antidoom流程训练，该模型推理时已知会产生重复循环。贪婪采样下，它的循环率从22.9% 降到1%，评测分数显著提升。

### LFM2.5-2.6B早期checkpoint

对基线checkpoint，评测分数的变化与循环率随温度升高呈反向关系。可以推断循环正在直接拉低基准分数，因为antidoom训练后分数大幅升高。

训练后暴露出一个次要效应：checkpoint在temp=1.0时性能下降。这意料之中：一般认为更高的温度采样会损害性能，因为模型更可能选中不那么偏好的token。过去有主流观点称更高温对推理模型可能更有利，能让它们探索解空间，**然而这种直觉可能是错置的，它和循环的主导效应混在了一起。一旦消除循环，至少在本文测试的模型中，近贪婪采样下能看到更强的评测表现。**

### Qwen3.5-4B

Qwen3.5-4B在antidoom训练后展现了更大的性能提升。模式与LFM2.5-2.6B相同，在低温采样下收益最大，并且在循环不再是影响因素后，暴露出在接近temp=1处性能退化的模式。

### 多轮Antidoom

实践中，应用多轮Antidoom会有帮助。第一轮之后循环率下降，因为导致循环的token被拒绝，概率被重新加权到该位置上的替代项。然而这可能暴露出新的失败点，此时分布中其他位置的token会触发新的循环。**再施加一轮Antidoom针对这些新浮现的循环，能进一步降低循环率。**

## 结论

Antidoom修复了训练后常见的退化重复行为，尤其是思考型模型。它选择性地瞄准开启循环的那些问题token，对剩余分布的附带损害最小。迄今为止的结果表明，在Liquid内部的LFM checkpoint以及Qwen3.5-4B上，都近乎完全消除了重复循环。

代码仓库的README包含使用训练流程以及选择合适超参数的指南。代码（生成、检测、FTPO训练器）可在 `github.com/Liquid4All/antidoom` 获取。

<div style="background:#f5f0eb;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:16px;">
<div style="text-align:center;margin-bottom:8px;">
<strong style="font-size:15px;color:#8b6f4c;">结语</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
Antidoom最值得记住的不是它降了多少循环率，而是它没教模型任何新能力，只是拔掉了"卡住时反复横跳"这个故障，分数就回来了。这给评估推理模型提了个醒：一个模型分数低，可能不是能力不行，而是被循环困住了，低温下的差距尤其要打个问号。<br><br>
"推理模型该用高温探索"这条经验法则，看来长期被循环效应污染。去掉循环后近贪婪采样反而更强，意味着很多团队过去为"防循坏"调高的温度，可能一直在悄悄牺牲答案质量。<br><br>
多轮才能压干净的细节也值得注意：治掉一批循环token，别处又冒出新的。说明循环是损失地形里的一种系统性倾向，不是靠一次补丁能根除的，Antidoom更像一套可反复使用的"手术流程"而非一劳永逸的疫苗。
</div>
</div>

---

<span style="font-size:14px;color:#888888;font-family:'Courier New',monospace;">【传送门】<br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/6uimwhjj_HlWTOB4m2FNrQ" target="_blank" data-linktype="2">Hermes Agent大师之路</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/OoHu1yeuh1gzgCfEiPvDuQ" target="_blank" data-linktype="2">RL的下一个大突破：不是优化可验证问题而是把「不可验证」领域变得「可验证」</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/0GXBP3UmtKYsta10yHkXlg" target="_blank" data-linktype="2">Anthropic最强模型Claude Fable5实测(代号Mythos)</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/YqikthC3Lt1HQ9amzSCABQ" target="_blank" data-linktype="2">PyTorch DDP极简指南：从 All-Reduce 到分布式训练实战</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/0zKdjRmWg3TbL5Y3HGO3fA" target="_blank" data-linktype="2">从 P/D 分离到 A/F 分离：从学术原型变成行业标准</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/crfkhSIuMZJxjNA0Md8dXw" target="_blank" data-linktype="2">李飞飞：世界模型的功能分类</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/oDZJbvskv_ocNgPUH1DHVA" target="_blank" data-linktype="2">AI暗输出：为何AI价值在GDP统计中失效了</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/hIab8mXanh0rdpEq_aHo7Q" target="_blank" data-linktype="2">Hermes Desktop 来了：从 CLI 到原生桌面应用，黄仁勋GTC首秀的产品正式公开</a><br>
</span>

---

<span style="font-size:12px;color:#888888;font-family:'Courier New',monospace;">参考：https://www.liquid.ai/blog/antidoom</span>
