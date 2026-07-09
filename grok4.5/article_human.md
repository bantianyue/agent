<div style="background:#e8f4fd;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:18px;">
<div style="text-align:center;margin-bottom:10px;">
<strong style="font-size:16px;color:#1a6ba0;">要点速览</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
- <strong>登顶且便宜</strong>：Grok 4.5在AutomationBench-AA以51% 得分拿下第一，成本约为Claude同级模型的四分之一<br><br>
- <strong>刷新帕累托前沿</strong>：每任务0.34美元，比所有领先模型都更便宜、得分也更高<br><br>
- <strong>token极致省</strong>：每任务约8k输出token，是领先模型里最少的，不到Opus 4.8的四分之一<br><br>
- <strong>代价</strong>：每任务触发0.63次违规，护栏仍被打破，守规矩的代价高于对手
</div>
</div>

---

## 一句话结论

Grok 4.5在Artificial Analysis的AutomationBench-AA榜单上以51% 的得分拿下第一，领先Claude Fable 5（49%）和Claude Opus 4.8（48%），而每任务成本只有它们的约四分之一。它是**第一个在不违反任何业务规则的情况下，完成过半工作流目标**的模型。

## 榜单怎么测

AutomationBench-AA是Artificial Analysis为Zapier的AutomationBench搭建的独立排行榜，考察AI Agent能否在遵守业务规则的前提下，自动化真实的SaaS工作流。测试集私有，防止数据污染。

模型要在40个模拟应用环境（Gmail、Google Sheets、Slack、Salesforce、HubSpot等）里完成657个任务。榜单的头条得分，是**在完全不违反护栏的情况下，完成的目标占比**。

## 全维度领先

Grok 4.5在六个维度上压倒其他模型。

**完成度最高。** 它完成了79.9% 的任务目标，严格通过（fully pass）21.9% 的任务，两项都是目前测得的最高值，超过Claude Fable 5的73.3% 目标完成率和Claude Opus 4.8的19.3% 完全通过率。

**刷新分数与成本的帕累托前沿。** 每任务0.34美元，比所有其他领先模型都更便宜、得分也更高。作为对比：Claude Fable 5每任务1.35美元、Claude Opus 4.8 1.46美元、GPT-5.5（xhigh）1.28美元、Gemini 3.5 Flash（high）0.49美元。

**token极致省。** 每任务约8k输出token，是领先模型里最少的，不到Claude Opus 4.8（32k）的四分之一，也仅是Gemini 3.5 Flash（24k）的三分之一。每任务总token用量0.44M，在榜单上属于最低档。低成本既来自这种效率，也来自本身更低的token定价。

**回合更少、并行工具更多。** Grok 4.5约16个回合解决任务，少于GPT-5.5（xhigh，25），不到Gemini 3.5 Flash（high，35）的一半；同时每任务工具调用次数最高（52.5次）。它每回合批量处理3.3个工具调用，而Claude Opus 4.8约2.5、GPT-5.5（xhigh）约2.0。

![](img1.jpg)
<span style="font-size:12px;color:rgb(153,153,153);">AutomationBench-AA排行榜：Grok 4.5以每任务 $0.34登顶，刷新分数与成本的帕累托前沿（Artificial Analysis）</span>

## 代价：护栏仍被打破

Grok 4.5每任务触发0.63次违规，高于Claude Opus 4.8（0.55）和Gemini 3.5 Flash（0.46）。按「每违规对应多少已完成的目标准确率」算，它反而落后：Grok 4.5是13.0，而Gemini 3.5 Flash是15.0、Claude Opus 4.8是13.5。**换句话说，为了冲到第一名，它在守规矩这件事上付出的代价比对手更高。**

## 最强优势在最难的地方

Grok 4.5完成71% 的金融（Finance）目标准确率，这是平均得分最低的领域，它领先Claude Fable 5（64%）和Claude Opus 4.8（62%）。在大家普遍做不好的地方，它拉开的距离最大。

![](img2.png)
<span style="font-size:12px;color:rgb(153,153,153);">Grok 4.5在分数与每任务成本对比中的表现（Artificial Analysis）</span>

<div style="background:#f5f0eb;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:16px;">
<div style="text-align:center;margin-bottom:8px;">
<strong style="font-size:15px;color:#8b6f4c;">结语</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
便宜、高分、省token三者同时成立，才是Grok 4.5真正可怕的地方。它第一次把「好用」和「用得起」压到了同一条曲线上，而不是像过去那样用高成本换高性能。<br><br>
但「登顶」和「守规矩」之间存在张力。0.63次违规提醒我们，榜单分数并不等于生产环境里可用的安全边界，企业真要用，还得自己再设一道护栏。<br><br>
这很可能是xAI收购Cursor之后，把「为代码与工作流而训」的思路落到真实Agent评测上的第一个信号。下一个被重新定义的，或许就是「Agent模型」这条赛道本身。
</div>
</div>

---

<span style="font-size:12px;color:#888888;font-family:'Courier New',monospace;">参考：https://x.com/ArtificialAnlys/status/2075047187525034114</span>
