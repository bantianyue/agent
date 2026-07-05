<div style="background:#e8f4fd;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:18px;">
<div style="text-align:center;margin-bottom:10px;">
<strong style="font-size:16px;color:#1a6ba0;">要点速览</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
- <strong>多模型融合超越前沿</strong>：OpenRouter发布Fusion功能，将多个模型并行推理后由裁判模型合成最终结果，Fable 5 + GPT-5.5融合得分69.0%，超越最强个体Fable 5的65.3%<br><br>
- <strong>廉价小组挑战旗舰</strong>：Gemini 3 Flash + Kimi K2.6 + DeepSeek V4 Pro的小组以50% 成本达到接近Fable 5的成绩（64.7% vs 65.3%）<br><br>
- <strong>自我融合也有提升</strong>：Opus 4.8与自己配对融合后得分65.5%，比单独运行（58.8%）提升6.7分，说明合成步骤本身贡献了显著增益<br><br>
- <strong>四种使用方式</strong>：聊天室预设、模型slug一键调用、服务端工具按需触发、Plugin灵活配置面板
</div>
</div>

---

OpenRouter发布了一项名为 **Fusion** 的新功能，它能将多个模型的结果综合处理后输出，且在DRACO深度研究基准测试上超越了所有单个前沿模型。

其核心思路很简单：**将同一个prompt并行发送给多个模型（小组），再由一个裁判模型综合各方的响应，生成最终答案。** 整个流水线在服务端运行，调用者只需一条API请求。

<span style="font-size:12px;color:rgb(153,153,153);">Fusion的基准测试概念示意图 | 来源：OpenRouter Blog</span>

![](fusion-benchmark.jpg)

## 小组显著超越个体

OpenRouter在DRACO基准的100个深度研究任务上测试了Fusion。DRACO是一个专为深度研究场景设计的评测集，覆盖学术研究、金融、法律、医学、技术、UX设计等10个领域，每项任务包含约39个加权评分标准，由裁判模型独立执行三次评分。

**两个关键发现：**

Fusion Fable 5 + GPT-5.5（由Opus 4.8合成）得分 **69.0%**，超过了所有单个模型，包括单独Fable 5（65.3%）。这6.7分的差距意味着模型组合带来的信息互补效应：一个模型覆盖不到的盲区，另一个模型恰好能补上。

更令人关注的是廉价小组的表现。**Gemini 3 Flash、Kimi K2.6和DeepSeek V4 Pro组成的小组得分64.7%，成功击败了GPT-5.5（60.0%）和Opus 4.8（58.8%）。** 它距离Fable 5的65.3% 仅差0.6分，但成本仅为后者的一半。对成本敏感的推理场景来说，这个组合几乎是"用一半的钱买到99% 的顶级性能"。

<span style="font-size:12px;color:rgb(153,153,153);">Fusion与单模型DRACO得分对比 | 来源：OpenRouter Blog</span>

![](fusion-benchmark-chart.png)

OpenRouter团队特意强调，Fable 5的100个任务中有7个因内容过滤器阻止而未能执行，因此Fable 5的得分实际基于93个任务，与其他基于完整100个任务的模型对比时存在略微不公平的偏差。即便如此，Fusion在完整100个任务上的表现依然优于Fable 5在93个任务上的成绩，差距足够大，方向明确。

## 一次API调用背后的合成机制

Fusion的技术实现是一个服务端的多步骤流水线：

1. 用户发起一次API请求，指定模型slug或自定义小组配置
2. OpenRouter将prompt并行分发到小组中的所有模型，每个模型均启用网络搜索（web_search）和网页抓取（web_fetch）
3. 裁判模型读取每个小组响应，生成结构化分析：共识点、矛盾点、部分覆盖、独特洞见、盲区
4. 调用模型（即最终输出模型）基于该分析写出最终答案

这个流程对用户完全透明。**调用方式和调用单个模型一样，只需一行代码：**

```
model: "openrouter/fusion"
```

<span style="font-size:12px;color:rgb(153,153,153);">Fusion与单模型在单任务成本上的对比 | 来源：OpenRouter Blog</span>

![](fusion-benchmark-cost.png)

用户也可以自定义小组配置，指定参与模型、裁判模型、以及是否启用特定服务器工具。这种灵活性意味着开发者不需要在"用哪个模型"上做过于激进的取舍：把这个问题交给Fusion的合成逻辑就好。

## 合成步骤本身的增益：自我融合实验

一个值得关注的实验是 **Opus 4.8与自己配对融合**。同样是Opus 4.8担任裁判，双模型小组得分65.5%，比单独的Opus 4.8（58.8%）高出6.7分。

这产生了一个耐人寻味的推论：**Fusion的收益并非全部来自模型之间的多样性。** 对同一个模型运行两次相同的prompt，会产生不同的推理路径、不同的工具调用、不同的来源选择。即使模型架构完全相同，多路径探索然后聚合的逻辑，与思维树（Tree-of-Thought）相通：本身就带来了显著提升。

当然，自我融合的提升幅度小于跨模型融合。这从另一面也说明了模型多样性仍有不可替代的价值。

## 成本与治理：Fusion的现实约束

Fusion的账单不是单个模型的账单。默认3模型panel时，一次Fusion调用的成本大约是单次completion的4-5倍（N个panel call + 1个judge call + 外层模型写答案），panel越大成本线性上升。所以「预算组合64.7%接近Fable 5」这个说法在实验设定里成立，但实际使用时取决于你的比较对象：如果你原本会让前沿模型反复查证、反复重写，那么预算panel可能更便宜；如果你原本只用便宜模型做普通问答，Fusion肯定更贵。

**成本和治理层面有几个硬边界值得注意：**

第一，不要把所有请求都默认走Fusion。最合理的策略是**按任务分级**：只有满足以下条件时才触发：需要跨多个来源验证、错误成本高于额外推理成本、最终产物会用于决策或技术选型。常规编码、简单问答、低价值批处理走单模型就好。

第二，隐私和数据合规在Fusion场景下被放大了。prompt不只是发给一个模型，而是可能发给多个panel模型、judge模型和外层模型，上游接触面天然扩大。OpenRouter的provider routing文档提供了 `data_collection: "deny"` 和 `zdr: true`（Zero Data Retention）等控制，但最终取决于上游各provider自身的数据策略。

第三，底层provider稳定性影响更大。Fusion把一次请求拆成多次上游调用，如果某个provider不稳定、长上下文截断或工具调用兼容出问题，整条链路都会受影响。

## 六种使用方式

Fusion提供了四种接入方式：

1. **聊天室**（Chatroom）：打开openrouter.ai/fusion选择预设或构建自定义面板，无需代码
2. **模型slug**（Model slug）：将model设为 "openrouter/fusion"，Fusion插件自动注入默认的前沿模型小组
3. **服务端工具**（Server tool）：在tools数组中添加 `{ "type": "openrouter:fusion" }`，由基模型自行判断何时需要调用Fusion，常规编码由基模型直接处理，架构决策或研究问题才触发Fusion
4. **插件**（Plugin）：在completions调用中添加 `"plugins": [{ "id": "fusion", ... }]` 参数，自定义参与模型和裁判模型

**Fusion不是Fable的直接替代品。** DRACO基准不包含长周期任务（long-horizon tasks），而这恰恰是Fable的强项。Fusion适合的是那些值得花费更多时间和金钱、需要多视角综合分析的深度问题：架构评审、竞品研究、最佳实践调研。常规编码和日常推理交给基模型自己处理就好。

**速度方面：** 当Fusion被触发时，流程通常比标准调用慢2-3倍（并行分发多个模型、等待全部返回、合成、输出）。但如果未被触发，响应速度与常规调用完全一致。

<div style="background:#f5f0eb;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:16px;">
<div style="text-align:center;margin-bottom:8px;">
<strong style="font-size:15px;color:#8b6f4c;">结语</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
Fusion本质上把「模型推理」变成了一种可组合的资源，而不是单一模型的选择题。这在商业模式上很巧妙：OpenRouter本身就是模型中转层，Fusion让它在价值链条上往上多走了一步：不再只是帮你选择哪个模型，而是帮你把多个模型的推理结果组装成更好的答案。<br><br>
自我融合实验（Opus 4.8 x Opus 4.8）的数据是最值得细品的。它告诉我们，即使模型没有多样性，仅仅通过多路径探索再聚合，就能获得系统性的提升。这与思维树（ToT）的逻辑相通，智能的瓶颈可能不在单个推理的质量，而在于是否充分地探索了多条路径然后做出聚合判断。<br><br>
但也要注意到，DRACO覆盖的领域虽然广，却不包含需要长周期规划的任务（long-horizon tasks）。对需要记忆和持续推理的场景，个体模型的持续对话能力可能仍然优于一次性的多模型合成。这不是Fusion的缺陷，而是使用范围的边界。选对工具比用好工具更重要。<br><br>
Fusion真正的价值不在于「又来了一个更强的模型」，而在于它把过去很多高级用户手搓的「多模型委员会+搜索+judge汇总」做成了一个可调用的API形态。它的本质不是模型智能的跃迁，而是系统智能的产品化：让多模型并行审查这件事的门槛从「自己搭pipeline」降到了「一行代码」。这个方向，比这一组具体的benchmark分数更有意义。
</div>
</div>

---

<span style="font-size:14px;color:#888888;font-family:'Courier New',monospace;">【传送门】<br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/mFuUJ79DRodIK6shVWOgpw" target="_blank" data-linktype="2">OpenAI GPT-5.6: 安全之外新增Prompt Cache断点+两种推理模式; 放弃版本号</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/_kjdbu__CbrkSkI9nDvLPA" target="_blank" data-linktype="2">【多模型系列三】 Devin Fusion双模编排-性能不变让Opus4.8 GPT5.5成本降低35%</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/aiJs5CC8Gb6qa_xDRNEjTA" target="_blank" data-linktype="2">Dynamic Subagents：用代码编排Agents，告别逐轮工具调用</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/6GuYxpX2yGov3IdtZuDTKg" target="_blank" data-linktype="2">多模型编排超过Claude Opus 4.8、GPT 5.5，媲美Fable 5: Sakana ...</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/o6pnSWW01pahFQelJSbSPA" target="_blank" data-linktype="2">华为「韬定律」全解析：从 τ 常数到4GHz麒麟，一张时间表看清未来十年芯片路线</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/M0qN4cXknU_CmZBQm5ChzA" target="_blank" data-linktype="2">你为什么离职？Top AI公司面试秘籍-一套框架从容应对15个套路问题</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/oDZJbvskv_ocNgPUH1DHVA" target="_blank" data-linktype="2">AI暗输出：为何AI价值在GDP统计中失效了</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/hIab8mXanh0rdpEq_aHo7Q" target="_blank" data-linktype="2">Hermes Desktop来了：从CLI到原生桌面应用，黄仁勋GTC首秀的产品正式公开</a><br>
</span>

---

<span style="font-size:12px;color:#888888;font-family:'Courier New',monospace;">参考：https://openrouter.ai/blog/announcements/fusion-beats-frontier/</span>