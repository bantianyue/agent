Artificial Analysis
@ArtificialAnlys
SpaceXAI 的 Grok 4.5 在 AutomationBench-AA 上夺得 #1 位置，得分 51%，领先于 Claude Fable 5（49%）和 Claude Opus 4.8（48%），且每任务成本仅为其大约四分之一，这是首个在不违反任何业务规则的情况下完成超过一半工作流程目标的模型。

AutomationBench-AA 是我们为 @zapier 的 AutomationBench 打造的独立排行榜，它测试 AI Agent 能否在遵守业务规则的同时自动化真实的 SaaS 工作流程。测试集为私有，以防止数据污染。

模型需完成跨 40 个模拟应用环境的 657 个任务，包括 Gmail、Google Sheets、Slack、Salesforce 和 HubSpot 等，头条得分是未违反任何护栏的情况下完成的目标占比。

关键要点：

➤ Grok 4.5 完成的目标准确率高于任何其他模型：它完成 79.9% 的任务目标，并严格通过 21.9% 的任务。这是我们在两项指标上测得的最高值，超过了 Claude Fable 5 的 73.3% 目标完成率以及 Claude Opus 4.8 的 19.3% 完全完成任务率。

➤ Grok 4.5 将得分与每任务成本的帕累托前沿向前推进：在每任务 0.34 美元的价格下，它既比所有其他领先模型更便宜，又得分更高，Claude Fable 5（每任务 1.35 美元）、Claude Opus 4.8（1.46 美元）、GPT-5.5（xhigh，1.28 美元）和 Gemini 3.5 Flash（high，0.49 美元）。

➤ 它极其高效：Grok 4.5 每任务使用约 8k 输出令牌，是所有领先模型中最少的，不到 Claude Opus 4.8（32k）的四分之一，以及 Gemini 3.5 Flash（24k）的三分之一。其每任务总令牌使用量 0.44M 在排行榜上属于最低水平。低成本得益于这种效率以及低令牌定价。

➤ Grok 4.5 使用更少的回合并支持大量并行工具调用：Grok 4.5 在约 16 个回合内解决任务，比 GPT-5.5（xhigh，25）少，且不到 Gemini 3.5 Flash（high，35）的一半，同时每任务工具调用次数是所有领先模型中最高的（52.5）。它每回合批量处理 3.3 个工具调用，而 Claude Opus 4.8 约为 2.5，GPT-5.5（xhigh）约为 2.0。

➤ 护栏仍会被打破：Grok 4.5 每任务触发 0.63 次违规，高于 Claude Opus 4.8（0.55）和 Gemini 3.5 Flash（0.46）。以每违规 13.0 个完成的目标准确率，它落后于 Gemini 3.5 Flash（15.0）和 Claude Opus 4.8（13.5）。

➤ 其最大领先优势在最难领域：Grok 4.5 完成 71% 的金融目标准确率，这是平均得分最低的领域，领先于 Claude Fable 5（64%）和 Claude Opus 4.8（62%）。

恭喜 @SpaceXAI 和 @elonmusk 登顶排行榜！
