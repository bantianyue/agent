**要点速览**

<div style="background:#e8f4fd;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:18px;">
<div style="text-align:center;margin-bottom:10px;">
<strong style="font-size:16px;color:#1a6ba0;">要点速览</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
- <strong>持久线程（Durable Threads）</strong>：通过 compaction 技术压缩长对话历史，为每个重要工作流维护持续数月的 mega-thread，积累历史、偏好和决策，用 Command-1 到 Command-9 快捷切换<br><br>
- <strong>语音输入 + Steering</strong>：语音让 Agent 获得未经编辑的原始思维；Steering 允许在 Agent 执行中持续注入新指令，无需等待当前步骤完成<br><br>
- <strong>记忆系统</strong>：用 Obsidian vault 作为持久化记忆层，通过 AGENTS.md 指令让 Agent 自动更新 vault 页面，GitHub 仓库实现 diff 审查和云端访问<br><br>
- <strong>Heartbeats</strong>：线程级自动化调度，可定时检查 Slack/Gmail/PR，实现"Chief of Staff"等持续监控，跨工具边界形成自动反馈循环<br><br>
- <strong>Side Panel</strong>：Codex 从聊天应用变为工作发生的地方——检查 artifact、操作网页、审查变更，支持 Markdown/CSV/PDF/Slides 直接渲染和交互
</div>
</div>

---

**最新版 Codex 应用升级第一次让这种更广泛的用法感觉原生。** 在 Codex 之前，作者已在大量使用编码 Agent，但主要通过编码工作界面——生成 diff、修改仓库、推送代码。2025 年 11 月，他开始把 Agent 推向知识工作：用 Slidev 做演示文稿、用语音输入做笔记、产出 `index.html`、PDF、电子表格、幻灯片。**核心转变在于给工作一个操作循环（operating loop）**：持久线程、共享记忆、能操控电脑的工具、可中途引导的交互方式，以及一个能审查产物的界面。

---

**持久线程（Durable Threads）**

第一个改变行为的是 compaction。

> **Compaction**：压缩长时间运行的线程，使其能持续进行而不必完整携带每一条旧消息。

作者现在为每个重要工作流维护一个 pinned thread：

- Chief of Staff 线程
- Agents SDK
- OpenAI CLI
- Codex for open source
- 一个专门监控 Twitter 的线程

**这些不是短对话。它们是 mega-thread，已经持续压缩了数月。** 它们积累历史、偏好和旧决策——这些信息作者不想每次回来都重新建立。

Pinned thread 快捷键：`Command-1` 到 `Command-9` 可直接跳转。

这里有一个权衡。长线程不是免费的。如果过段时间再回来，对话可能已经不在缓存中，因此成本可能比新开一个短线程更高。**但对于重要的 workstream，连续性值得这个代价。**

---

**语音输入（Voice Input）**

语音输入让更多真实思考进入 Codex。

好处不是速度。**好处在于 Agent 获得的是未经编辑的原始思维。** Codex 内置了语音输入，但作者还使用 Wispr Flow，因为系统级听写改变了他能输入到其他所有工具的上下文量。如果他在规划一项工作，可能会说："我记得 Slack 里有个叫 Ben 的人提过这个，具体记不清了，去查一下。"这句话打字太模糊太烦人，但说出来完全自然。

同样的情况适用于对话记录。如果想写一篇文章，可以打电话给某人、录下对话、或者当面聊并用 Granola 录音，然后把转录文本作为起始素材。**当模型能接触到想法的原始版本而非精炼版本时，很多方案会变得更好。**

---

**Steering**

语音在结合 steering 时变得更加有用。

> **Steering**：在 Codex 已经执行的过程中注入更多方向，而不是等待当前步骤完成。

Steering 允许在工具调用后注入下一条消息。如果正在审查一个网站，可以边看边说：

- 把这个缩小
- 这段文案不对
- 这两个元素之间的间距不太对
- 完成后，开一个 PR
- 等待 preview deploy
- 把预览链接发给需要审阅的人

**不需要等每一步完成再决定下一步。** 可以在 Agent 还在工作时持续注入意图，然后带着已经排好队的任务离开。

之后，Heartbeats 可以在离开后监控 PR 或 Slack 线程。工作的单位不再是"一次提示，一次回答"——它变成了一个**小型操作循环**。

---

**记忆（Memory）**

当线程开始持续更长时间后，它们需要在任何单一仓库之外拥有共享记忆。

**关键动作是把东西保存到磁盘。** 长线程可以记住很多，但除非有用的部分被写入持久化位置，否则这些记忆被困在线程内部。记忆系统的意义在于把线程学到的东西变成可以审查、编辑、diff 和复用的产物。

作者的大多数长线程从一个 Obsidian vault 开始：

```
vault/
├── TODO.md
├── people/
├── projects/
├── agent/
└── notes/
```

顶层有一个 `AGENTS.md` 指令文件，告诉模型把东西写下来：随着你了解更多人、推进项目、做出决策、或关闭一个待办事项，更新 vault 中相应的页面。

**Vault 是 Agent 居住的地方，独立于任何单一项目。** 仓库（repository）存放代码。Vault 存放围绕工作的滚动上下文：人员、决策、待办事项、每日笔记、项目状态，以及那些本会在线程之间丢失的理解碎片。

作者还把 vault 作为一个 GitHub 仓库。这带来了两个好处：

1. 可以在云端工作
2. diff 成为记忆的审查面

当 Agent 更新 vault 时，可以阅读 diff，看它认为什么重要到值得记住。**这个审查步骤很关键。** 作者不希望常青线程在对话历史中悄悄积累"氛围"——他希望它们写下变化：这个人偏好这个，那个项目在等那个，这个决策已做出，这个待办已关闭。

这也是作者喜欢把记忆做成文件的原因。文件迫使 Agent 把经验压缩成一种能在线程之外存活的形式。如果线程死亡、压缩失败、或变得太贵而无法继续依赖，有用的知识仍然在那里。模式很简单：把重要工作放在一个仓库里，给 Codex 权限和指令去更新它，然后像审查任何其他变更一样审查 diff。

**到了这个阶段，pinned thread 开始不再像聊天，而更像不同的工人在读同一个笔记本。**

Codex 也有第一方记忆功能（`Settings > Personalization > Memories`）。作者将其视为显式磁盘备份系统之上的一个 recall 层。Vault 是可以审查和编辑的事实来源。Memories 帮助 Codex 在启动新线程时记住稳定的偏好、重复的工作流、项目约定和已知陷阱。

Chronicle 也出于同样的原因值得关注。作者尚未认真使用它，文档也明确说明这是一个 opt-in 的研究预览，在权限、速率限制、prompt injection 和未加密的本地记忆文件方面有真实的权衡。**但方向指向同一件事：工作应该留下结构化的记忆，而不仅仅是一个更长的聊天记录。**

> **共享记忆**：保存在单个聊天之外的上下文，如 vault 中的笔记，不同线程可以复用。

---

**电脑与浏览器使用（Computer and Browser Use）**

一旦线程有了记忆，下一个问题就是它能触碰什么。

作者在脑海中做的最有用的区分是：

- `$browser`：用于检查和标注本地网页
- `@chrome`：用于已登录的浏览器会话和多标签页
- `@computer`：用于只能通过 GUI 完成的工作

如果是在迭代本地应用，用 `$browser`。如果需要在已登录的浏览器会话中工作，用 `@chrome`。**如果完成任务的唯一方式是点击桌面应用，用 `@computer`。**

Appshots 是更轻量级的版本。有时作者不想让 Codex 操作应用，只想让它看到自己正在看的东西。在 macOS 上，可以同时按下两个 Command 键，把最前端的窗口以截图和可用文本的形式发送到 Codex 线程中。

这对于那种"展示比描述容易"的烦人中间类别很有用：一个错误弹窗、一个设置面板、一个 API 参考页面、一封邮件、一个日历视图、一个设计预览、或者一个只有亲眼看到才明白的应用异常状态。**与其打一大段设置提示，不如把 Codex 指向当前窗口说"这就是我说的东西"。**

在工作机器上，Twitter 登录在 Safari 中。如果用 `@computer` 让 Codex 读取 Twitter，就会在它工作时失去 Safari。`@chrome` 更适合让 Agent 并行使用多个已认证标签页，而不占用正在使用的整个应用。

Connectors 将这种触达扩展到实际工作的其余部分。作者最常用的是 `$slack`、`$gmail` 和 `$calendar`，因为 Slack 线程、收件箱和日历是许多工作在变成代码之前出现的地方。

**Skills 让重复工作流可复用。** Skill Creator 和 Skill Installer 是好的起点。Skill Installer 允许直接从 composer 添加 OpenAI 推荐的技能。Codex Pets 发布后，作者用它安装了 Hatch Pet 技能，但有用的模式是通用的：一旦做了一件有用的事，通常可以把它打包，让 Codex 无需重新教导就能再次执行。

---

**远程控制（Remote Control）**

远程控制让这些更长的循环变得可携带。

Codex 可以在文件、权限和本地配置已经就绪的机器上持续工作，而你可以从手机端查看进展、审查发现、回答问题、批准下一步、或改变方向——无需回到办公桌前。OpenAI 将其描述为"从任何地方与 Codex 一起工作"。

**这在 Codex 正在执行长时间任务、你想保持 momentum 时最为关键。** 可以启动一个任务，走开，然后在它到达决策点时从手机端引导。

这与 pinned thread、语音和 Heartbeats 重要的原因相同。工作不再因为位置变化而暂停。线程可以继续运行，而你可以保持刚好足够的注意力来解除下一步的阻塞。

---

**Heartbeats**

Pinned thread 很有用，但它们仍然在等你说话。Heartbeats 让它们变成周期性运行。

> **Heartbeats**：线程可以为自己调度的周期性检查，比如监控 Slack 或 PR 的新活动。

Heartbeat 是线程级自动化。可以说"每隔几小时盯着这个"，线程就可以调度自己。一个线程可以有多个调度，运行直到某个条件满足，并随时间调整节奏。

**Chief of Staff**

作者的 Chief of Staff 线程每 30 分钟运行一次：

```
每 30 分钟，检查 Slack 和 Gmail 中需要我关注的未回复消息。
帮我优先处理最重要的事情。
如果有人问了我一个问题，尽可能深入地研究答案并草拟回复，但不要发送。
```

当作者回到 Slack 时，回复通常已经躺在草稿里了。**他仍然决定什么被发送出去，但收集上下文的最昂贵部分已经完成了。**

**监控反馈（Monitor for feedback）**

同样的模式适用于审查循环。Heartbeat 可以监控 Google Docs 评论、PR 评论或 Slack 回复，在反馈到达时保持工作推进。

作者最喜欢的一个例子来自一个动画项目。他在 Slack 中发布了一个视频，让 Codex 每 15 分钟检查一次线程，当评论进来时重新渲染新版本，然后回复到线程中并 @ 审阅者。Slack MCP 服务器不能上传文件，所以 Agent 用 `@computer` 按下"添加文件"按钮，还是发布了修改后的渲染版本。

**有趣的部分不只是它每 15 分钟检查一次 Slack。** 这个循环跨越了工具边界：Slack 用于反馈，Remotion 用于渲染，`@computer` 用于上传。这就是 Heartbeats、connectors 和 computer use 不再像独立功能的时候——它们一起变成了一个无需作者坐在那里就能持续运行的反馈循环。

**申请退款（Get a refund）**

最近作者有一个包裹被偷了。亚马逊告诉他大约需要 25 分钟才能和人工客服通话，于是他创建了一个带 `@computer` 的线程并告诉它：

```
每 5 分钟检查一次客服是否已加入此线程。
如果已加入，尽力帮我拿到退款。
一旦他们回复，改为每分钟检查一次，以便更快响应。
```

等他洗完澡出来，退款已经完成了。

作者的许多 Heartbeat 还会更新 Obsidian vault，作为一种显式记忆。

---

**目标（Goals）**

作者还在学习如何用好 Goals，这是最新的功能。

> **Goals**：具有真正终点的长时间运行任务，Codex 可以持续朝之推进。

应该对它们有野心。一个弱目标是"实现这个 Markdown 文件中的方案"。**一个强目标有真正的成功标准，Agent 可以持续朝之推进。**

上周作者尝试把 Python 的 Rich 库迁移到 Rust。因为原项目已经有大量的单元测试套件，他可以设定一个目标：把 Rich 迁移到 Rust，但必须通过原库的所有单元测试。

这个测试套件给了运行一个真正的 oracle：**Rust 移植版在通过 Python 库的相同测试之前不算完成。**

这与和 AI 进行长对话、积累一个 Markdown 方案、然后最终说"实现它"是不同的。执行只取决于你给出的目标和验证方式。**没有验证的野心只是一个愿望。**

---

**侧面板（The Side Panel）**

Codex 中最让作者兴奋的部分是侧面板。

很容易把它想象成预览发生的地方。这低估了它。**侧面板是 Codex 不再只是一个聊天应用、开始成为工作发生的地方。**

对作者来说，它做三件事：检查 artifact、操作网页、审查变更。在这三种场景中，他都可以查看 Agent 正在操作的同一个对象并发表评论。

**检查 Artifact**

Markdown、电子表格、CSV、PDF 和幻灯片都可以放在那里。

Markdown 是可评论的。电子表格渲染公式并支持单元格编辑——作者用它来管理 Codex 开源计划。CSV 变成表格而非原始文本。PDF 直接渲染，这对 LaTeX 特别有用。幻灯片可以在不离开应用的情况下创建和审查。

**重要的不只是 Codex 能生成 artifact。重要的是可以在不打断循环的情况下检查和标注它们。**

**操作网页（Operate Web Surfaces）**

应用内浏览器更有趣。Agent 可以通过 `$browser` 看到它、用 JavaScript 控制它，而作者可以直接在他正在看的东西上留下标注。

有几个网页作者现在一直用这种方式：

- `index.html` 用于轻量级静态 artifact
- Storybook 用于审查 UI 组件
- Remotion Studio 用于程序化动画
- Slidev 用于演示文稿
- Streamlit 用于数据应用

最小的版本往往是最好的。可以让模型创建一个包含 JavaScript 和 CSS 的 `index.html` 文件，在侧面板中打开它，立即开始交互。无需服务器。作者一直在尝试用 Heartbeats 随时间更新一个静态 `index.html`，这样每次回到线程时，已经有一个新鲜的 artifact 在等着。

Thariq 有一篇非常好的文章，认为 HTML 比 Markdown 更适合作为输出格式。作者认为这个直觉是对的。**一旦输出从文档变成一个小型应用，关系就变了。**

如果需要更重的东西，可以用 Vite 应用，但那样需要保持服务器运行。一个简单的 `index.html` 要持久得多。

对于动画工作，作者经常同时打开 Storybook 和 Remotion Studio。他可以留下"让这个弹跳"或"这个应该更大"的评论，Agent 可以检查他正在看的同一个浏览器状态，包括动画中的当前帧。

对于演示文稿，作者经常使用 Slidev。Codex 可以检查幻灯片、发现被截断的内容、切换幻灯片、并在作者审阅时响应标注。

作者还预计这对 Streamlit 和 Jupyter 等工具会越来越有用。不同的人已经生活在不同的应用中。**Codex 越来越能在那里与他们相遇。**

Codex 有越多的地方去记住、重新访问、检查和行动，工作就越不会在两次提示之间死去。这才是作者在乎的变化——不是 Agent 能为我写代码，而是更多的工作在我离开后还能继续推进。

---

<div style="background:#f5f0eb;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:16px;">
<div style="text-align:center;margin-bottom:8px;">
<strong style="font-size:15px;color:#8b6f4c;">结语</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
本文描述的工作流——持久线程 + 记忆系统 + Heartbeats + Side Panel——本质上是在重新定义"人机协作"的粒度。从单次对话到持续运行的操作系统，这个转变比看起来更深。当 Agent 不再等你说话才行动，而是按自己的节奏推进工作时，人的角色从"操作者"变成了"监督者"。<br><br>
但这种模式也有隐形成本。长线程的缓存失效和 token 消耗不是线性的；记忆碎片化（vault + Codex Memories + Chronicle 三层）可能反而增加认知负担；Heartbeats 的自主行动边界在哪里——"草拟回复但不发送"是一个优雅的折中，但更多场景下这个边界会模糊。<br><br>
值得注意的是，本文描述的许多能力（持久化记忆、定时任务、工具编排、远程控制）在其他 Agent 框架中也有对应实现。差异不在功能列表，而在整合度——Codex 把这些能力打包进一个原生体验，让"操作循环"的感觉变得自然。这是产品设计上的胜利，而非技术上的独有创新。
</div>
</div>

---

<span style="font-size:12px;color:#888888;">参考：https://jxnl.co/writing/2026/05/10/codex-maxxing/</span>
