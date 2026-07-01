**10大Agent Skills仓排行榜在六月刷新了。Bilgin Ibryam 重新统计了 GitHub 上星数最高的 Agent Skills 仓库，总星数 228,740。信号很清晰：小而精的工作流正在胜出。**

---

<div style="background:#e8f4fd;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:18px;">
<div style="text-align:center;margin-bottom:10px;">
<strong style="font-size:16px;color:#1a6ba0;">要点速览</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
- <strong>obra/superpowers 以 228,740 ★ 登顶</strong>：Jesse Vincent 开发的 Agentic Skills 框架兼开发方法论，教 Agent 先规划再执行、TDD、系统化调试<br><br>
- <strong>Top 10 中 6 个是单 Skill 仓库</strong>：不是大而全的 Skill 集合，而是单一精准能力——市场在投票给"一个 Skill 做好一件事"<br><br>
- <strong>Anthropic 官方仓库排第二（151,088 ★）</strong>：官方标准 vs 社区创新双轨并行，Skills 格式已跨平台扩散到 OpenAI、Cursor、Gemini<br><br>
- <strong>Skills 正在跨平台</strong>：SKILL.md 格式从 Claude 生态扩散到 OpenAI Codex、Cursor、Gemini CLI，选 Skill 看功能不看供应商
</div>
</div>

**Agent Skills 在 2026 年初经历了一场爆发。** 从 2025 年 12 月 Anthropic 开放 Skills 标准开始，到 2026 年 6 月，GitHub 上以"Agent Skills"为标签的仓库从几十个增长到数万个。Bilgin Ibryam——Diagrid 的 PM、前 Red Hat 架构师、《Kubernetes Patterns》作者——决定拉一份最新的 Top 10 榜单，看看市场到底在为什么投票。

**结果很清楚：人们不为功能最多、最复杂的 Skill 平台点赞，他们为那些让 Agent 更靠谱的东西点赞。**

**Top 10 Agent Skills 榜单**

| 排名 | 仓库 | Stars | 一句话 |
|------|------|-------|--------|
| 1 | obra/superpowers | 228,740 | Agentic Skills 框架 + 开发方法论 |
| 2 | anthropics/skills | 151,088 | Anthropic 官方 Skills 仓库 |
| 3 | mattpocock/skills | 130,016 | Matt Pocock 的实战 Skill 集合 |
| 4 | garrytan/gstack | 110,407 | Garry Tan 的 Claude Code 全套配置 |
| 5 | nextlevelbuilder/ui-ux-pro-max-skill | 92,040 | UI/UX 设计智能 |
| 6 | Egonex-AI/Understand-Anything | 60,442 | 代码转交互式知识图谱 |
| 7 | addyosmani/agent-skills | 60,265 | 生产级工程 Skills |
| 8 | santifer/career-ops | 53,903 | AI 驱动的求职系统 |
| 9 | Leonxlnx/taste-skill | 44,469 | 让 Agent 远离泛泛输出的品味 Skill |
| 10 | mvanhorn/last30days-skill | 42,815 | 跨 Reddit、X、YouTube、HN 的趋势研究 |

**最有意思的发现：Top 10 中有 6 个是单 Skill 仓库。** 不是庞大的 Skill 库，而是单一精准能力。这和市场直觉相反——人们以为最大的 Skill 仓库会统治榜单，但实际排名靠前的是那些专注于一件事并做到极致的 Skill。

**obra/superpowers 登顶**

排名第一的 **obra/superpowers** 由 Jesse Vincent 开发，是一个 Agentic Skills 框架兼软件开发方法论。它不是最大的 Skill 集合，但它提供了一个完整的开发流程：从需求澄清到设计文档，从实施计划到 TDD 执行，从代码审查到完成验证。它的核心理念是让 Agent 在写代码之前先停下来思考——这恰好是当前 Agent 最缺的能力。

**Ibryam 的完整文章还列出了几个值得关注的框架：**

- **andrej-karpathy-skills**——将 Andrej Karpathy 关于语言模型写代码时常见错误的观察提炼为一个可部署的防护栏。小而精，效果显著
- **gstack**（Garry Tan）——Garry Tan 的 Claude Code 精确配置，包含数十个充当 CEO、设计师、工程经理、发布经理和 QA 的定制工具
- **mattpocock/skills**——Matt Pocock 的实战 Skill 集合，来自他自己的 `.claude` 目录

**Skills 正在跨平台**

Ibryam 强调了一个关键趋势：**Skills 正在跨平台。** SKILL.md 格式从 Claude 生态开始，但现在已经扩散到 OpenAI（ChatGPT 和 Codex）、Cursor、Gemini CLI 等多个平台。这意味着选 Skill 应该看功能，而不是看供应商。

> "Skills 正在走向可移植。它们始于 Claude 生态，但 SKILL.md 格式正在扩散。OpenAI 现在在 ChatGPT 和 Codex 中都有 Skills 文档，多个集合已经能跨 Claude Code、Codex、Cursor 和 Gemini 运行。"

**推荐的安装顺序**

Ibryam 给出了一个实用的安装路径：

1. 从官方仓库开始，学习好的 SKILL.md 长什么样
2. 收藏市场平台和精选列表用于发现
3. 在收集单个技巧之前，先安装一个工作流框架
4. 为你实际使用的技术栈添加供应商 Skills
5. 当你重复同样的指令三次时，写自己的 Skill

> "市场平台会用成千上万的 Skills 诱惑你。那个数字是个陷阱。你真正理解和信任的那几个，比一个你从不打开的目录对你的工作更有帮助。"

**Skill 的定义**

Ibryam 对 Skill 的定义很清晰：**Skill 是编码 Agent 的复用单元。它是一个包含 SKILL.md 的文件夹，教会 Agent 一项能力一次，这样你就不用在每次会话中重复解释。Agent 只在任务需要时才加载它。**

**生态格局**

从榜单还能看出 Agent Skills 生态的几个趋势：

**单 Skill 仓库正在胜出。** Top 10 中 6 个是单 Skill 仓库，说明市场偏好"一个 Skill 做好一件事"而非"一个仓库包含所有事"。

**官方标准与社区创新并行。** Anthropic 官方仓库（151K ★）和 OpenAI 官方仓库的存在定义了格式标准，但社区项目在星数上总和远超官方——生态的真正活力在社区。

**工作流框架 > 单个 Skill。** Ibryam 的建议很明确：先装一个工作流框架（如 superpowers），再收集单个 Skill。框架改变的是 Agent 的工作方式，而不仅仅是它知道什么。

---

<div style="background:#f5f0eb;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:16px;">
<div style="text-align:center;margin-bottom:8px;">
<strong style="font-size:15px;color:#8b6f4c;">结语</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
Top 10 中 6 个是单 Skill 仓库，这个信号比总星数 228,740 更有价值。市场不是在为"Agent Skills 生态有多大"投票，而是在为"一个 Skill 能多精准地解决一个具体问题"投票。这跟 App Store 早期的逻辑一样——最先爆发的不是功能最全的"超级 App"，而是那些只做一件事但做得极好的小工具。<br><br>
Ibryam 的"先装框架再装 Skill"的建议值得认真对待。当前 Skills 生态最大的问题不是数量不够，而是缺乏组织——没有框架的 Skills 就像没有操作系统的 App，各自为政。superpowers 的 228K 星说明市场已经意识到了这一点。
</div>
</div>

---
<span style="font-size:12px;color:#888888;">参考：Top 10 Agent Skills by GitHub Stars — Bilgin Ibryam<br>https://x.com/bibryam/status/2066652088029852098</span>
