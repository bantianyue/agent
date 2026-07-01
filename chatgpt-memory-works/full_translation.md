ChatGPT 会记住你，但方式和大多数人想象的不一样。它不搜索旧对话，没有向量数据库。相反，每次消息中，ChatGPT 把一份基于你过去对话构建的"你是谁"摘要，直接注入到上下文中。2026 年 6 月，OpenAI 重建了这个机制并取名 Dreaming。

OpenAI 文档中的两个系统：Saved memories（离散事实，自动或手动保存）和 Reference chat history（推断用户兴趣偏好）。Saved memories 永久保留直到删除；Reference chat history 的推断细节随时间变化。可在设置中关闭，或使用 Temporary Chat。

实际运作方式：没有检索机制。研究员 Johann Rehberger 发现 ChatGPT 无法回忆一年前的对话。Simon Willison 收回 RAG 猜测——ChatGPT 维护一份摘要，每次新聊天注入 System Prompt。Profile 有六个段落：Model Set Context、Assistant Response Preferences、Notable Past Conversation Topic Highlights、Helpful User Insights、Recent Conversation Content 和 User Interaction Metadata。Recent Conversation Content 只含用户消息，不含 ChatGPT 回复。条目用 |||| 分隔，带 intent_tags 和时间戳。Saved memories 通过 bio 工具（to=bio）持久化，出现在 Model Set Context 段落。以上机制基于 2024-2025 年的逆向工程，Dreaming 已改变 Profile 构建方式。

苦味教训：OpenAI 赌规模胜过聪明——没有向量数据库、知识图谱、RAG。每条消息包含全部压缩记忆、上下文、元数据。足够强的模型+大上下文窗口不需要检索层。简单可扩展，但有天花板。

Dreaming：自动更新。预加载的 Profile 会腐烂，事实堆积矛盾。2026 年 6 月，OpenAI 推出 Dreaming——后台读取多年对话，自动重写对用户的记忆。经典例子：行程结束后"你七月要去新加坡"自动变为"你去了 2026 年 7 月的新加坡"。OpenAI 报告事实回忆从 41.5% 提升到 82.8%（内部数据，未公开评估集）。同期行业方向一致：Google 的"Language Models Need Sleep"、Mem0 和 GBrain 的空闲期整合——后台整合才是方向。

永久 Profile 的代价。Willison：ChatGPT 收集用户互动档案应用于每次聊天，Profile 在没有明确许可的情况下被注入上下文。安全问题：外部文档可通过引用写入攻击者控制的记忆。2024 年研究显示可转为监视通道（arXiv:2406.00199）。本质教训：记忆是一个写入面，任何能写入它的都是攻击面。

边界：ChatGPT 记忆封闭、单应用，Profile 不出 ChatGPT。预加载而非检索，无限定范围能力。开发者层（Mem0）的对比：检索而非预加载（三个评分通道并行——语义、关键词、实体匹配），7,000 tokens 以下消耗对比 25,000+ tokens，按身份限定跨工具可移植。ChatGPT 证明了注入 Profile 足够让应用个性化；检索、精确限定、跨工具携带的记忆才是更难的问题。
