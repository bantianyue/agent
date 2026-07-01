<div style="background:#e8f4fd;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:18px;">
<div style="text-align:center;margin-bottom:10px;">
<strong style="font-size:16px;color:#1a6ba0;">要点速览</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
- <strong>ChatGPT记忆不是RAG</strong>：它不搜索历史对话，而是将一份持续更新的用户Profile摘要预加载到每一轮的System Prompt中<br><br>
- <strong>Profile有六个段落</strong>：安全研究员逆向工程发现，这份Profile包含Model Set Context、Recent Conversation Content（仅用户消息）等结构化段落，用 |||| 分隔符和intent_tags标记<br><br>
- <strong>Dreaming：后台自动整合</strong>：2026年6月上线的Dreaming系统在后台读取多年对话、自动更新Profile，无需用户介入，内部评估事实回忆从41.5% 提升到82.8%<br><br>
- <strong>Profile也是攻击面</strong>：引用外部文档可能将攻击者内容写入长期记忆，记忆是一个"写入面"，任何能写入它的东西都是攻击面的一部分
</div>
</div>

---

ChatGPT会记住你，但方式和大多数人想象的不同。

它不会搜索你的旧对话。没有向量数据库在你提问时悄悄拉取历史。相反，在每次消息中，ChatGPT都会把一份基于你过去对话构建的"你是谁"摘要，直接注入到它的上下文中。

2026年6月，OpenAI重建了这份摘要的构建方式，并给它取了一个名字：**Dreaming**。

**没有检索机制**

官方来看，ChatGPT的记忆有两个部分。Saved memories是可保存的离散事实：你可以告诉ChatGPT"记住我是素食者"，或者它可以在觉得有用时自行保存。Reference chat history则利用你过去的对话来推断你的兴趣和偏好。

但让人惊讶的部分：也是OpenAI没有明确说明的部分：是检索机制。**它根本不存在。**

安全研究员Johann Rehberger直接测试了这一点，发现ChatGPT无法回忆起一年前的某次具体对话。Simon Willison收回了自己最初认为它是用RAG的猜测。实际情况要简单得多：ChatGPT维护一份你之前对话的详细摘要，经常用新细节更新它，然后每次你开始新聊天时，这份摘要就会被注入到上下文里。

所以，记忆不是按提问区检索的。它是预加载的。**一份持久的个人Profile在每一轮的System Prompt中都跟着你。**

Rehberger记录到，这份Profile大致包含六个命名段落：Model Set Context、Assistant Response Preferences、Notable Past Conversation Topic Highlights、Helpful User Insights、Recent Conversation Content和User Interaction Metadata。

**细节让这个机制变得具体。** Recent Conversation Content保存了你的近期对话，但只有你输入的消息，不包括ChatGPT的回复。原因是数据量太大，Prompt Injection和幻觉会成为重大风险。条目之间用 |||| 分隔符隔开，带有内部intent_tags（如translation或argument_or_summary_generation），并带有精确到秒的时间戳。

Saved memories则通过另一条路径工作：模型调用一个bio工具（to=bio）来持久化一个事实，随后该事实会以带日期条目的形式出现在未来System Prompt的 # Model Set Context段落中。

**为什么选择"全部塞进去"而不是检索**

为什么不构建成大多数记忆系统那种精心的检索管道？shloked.com的作者将OpenAI的策略总结为**"在规模和聪明才智之间赌前者"**：没有向量数据库、没有知识图谱、没有RAG。OpenAI只是在每条消息中包含一切：压缩的用户知识记忆、Model Set Context、最近对话、元数据，全部内容，每一次。

逻辑是：一个足够强的模型加上一个足够大的上下文窗口，不需要检索层来决定该暴露什么。把整个Profile交给它，让注意力机制自己排序。

这个方案简单，能扩展到数亿用户：但它也有天花板。**这也正是Dreaming要解决的问题。**

**Dreaming：后台自动更新的记忆**

预加载的Profile会腐烂。事实堆积起来，变陈旧，相互矛盾，手工维护的Saved memories列表在跨越数年的聊天和数亿人的规模下无法扩展。所以2026年6月，OpenAI推出了一种构建Profile的新方式：Dreaming。

**Dreaming是一个后台进程，读取你多年的对话，重新整理ChatGPT对你的记忆，不需要你要求它保存任何东西。** OpenAI给出的典范示例是记忆的自我修正："你七月要去新加坡"在行程结束后自动变为"你去了2026年7月的新加坡"。

OpenAI报告这一变化将内部事实回忆评估从2024年的41.5% 提高到2026年架构下的82.8%，偏好遵循度71.3%，时间敏感准确性75.1%。这些都是OpenAI自己的数据，未公开评估集，也没有独立第三方复现过。

名字本身就是线索。ChatGPT现在在后台、在会话之间整理记忆：**整个行业已经开始这样做了。** 同期Google的"Language Models Need Sleep"为权重提出了Dreaming阶段，从Mem0到GBrain的记忆产品都推出了空闲期整合。OpenAI把"Dreaming"放在消费产品上，是迄今为止最明确的信号：**后台整合：而非更大的上下文：才是记忆的未来方向。**

**永久Profile的代价**

一份持久的、人类可读的个人Profile非常强大：而这正是问题所在。

Willison称这是一个值得暂停的隐私问题：**ChatGPT实际上在收集我们先前互动的档案，并将这些信息应用到每一次未来的聊天中。** 他更尖锐的问题是：有哪款消费产品能像这样构建出一份人类可读的用户Profile？他的反对不是因为记忆存在，而是因为Profile在没有用户明确许可或控制的情况下被倾倒到模型上下文中。

还有安全层面。因为不受信任的内容可以到达模型，它也可以到达记忆。Rehberger展示了聊天中引用的一份Google Doc可以将攻击者控制的条目写入长期记忆。2024年的一项研究显示，该功能可能被转化为一个持久的监视通道：模型被指示监视并存储用户的个人数据，以便日后泄露（arXiv:2406.00199）。

**持久的教训是结构性的：记忆是一个写入面，任何能写入它的东西都是你攻击面的一部分。**

**它的边界在哪里**

ChatGPT的记忆为做好一件事而构建：让一个消费应用感觉像认识你。让它擅长这件事的设计选择，也正是它的边界。

它是封闭的、单应用的。Profile只生活在ChatGPT内部，你的编辑器Agent、终端Agent、你自己的应用都无法读取或写入它。它是预加载的，不是检索的：你不能决定针对某个任务该暴露哪些记忆。它是为终端用户而不是开发者构建的：没有干净的方式来限定范围、按Agent分支，或者让一个人的身份记忆跨越他们实际使用的各种工具。

<div style="background:#f5f0eb;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:16px;">
<div style="text-align:center;margin-bottom:8px;">
<strong style="font-size:15px;color:#8b6f4c;">结语</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
这篇文章最有价值的部分不在于它拆解了ChatGPT的记忆机制，而在于它点出了一个被忽视的结构性问题：当记忆被设计成"全部预加载"而非"按需检索"时，整个Profile既是用户体验的基石，也是安全攻击的永久写入面。<br><br>
Dreaming的推出其实是对这个问题的侧面印证。如果预加载方案真的能无限扩展，就不需要一个后台进程来做自动整合和更新。OpenAI自己的数据显示41.5% → 82.8% 的提升幅度也说明，之前的记忆系统在规模下面临着严重的陈旧性和准确性问题。<br><br>
文中最后的开发者层（Mem0）虽然带产品推广性质，但它提出的"检索而非预加载""按身份限定、跨工具可移植"的对比，确实点出了ChatGPT当前方案在开发者场景下的核心短板。
</div>
</div>

---

<span style="font-size:12px;color:#888888;font-family:'Courier New',monospace;">参考：

https://x.com/mem0ai/status/2071990201531118063
https://embracethered.com/blog/posts/2025/chatgpt-memory-and-chat-history/
https://simonwillison.net/2025/May/21/chatgpt-memory/
https://shloked.com/chatgpt-memory-bitter-lesson/
https://arxiv.org/abs/2406.00199</span>
