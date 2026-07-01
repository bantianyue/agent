# Claude Sonnet 5 发布

发布时间：2026 年 6 月 30 日

## 核心亮点

- 迄今为止 Sonnet 系列中 Agent 能力最强的模型——能规划、能使用工具（浏览器、终端），能自主运行
- 性能接近 Opus 4.8，但价格更低
- 在推理、工具使用、编程和知识工作方面，比 Sonnet 4.6 有显著提升
- 比 Sonnet 4.6 更安全，不良行为率更低
- 网络安全能力低于当前 Opus 模型

## 价格与可用性

定价方案：
- 促销价（截至 2026 年 8 月 31 日）：输入 $2/MTok，输出 $10/MTok
- 标准价（2026 年 8 月 31 日后）：输入 $3/MTok，输出 $15/MTok
- Opus 4.8（参考对比）：输入 $5/MTok，输出 $25/MTok

可用范围：Free/Pro 方案的默认模型；Max、Team、Enterprise 用户可用；Claude Code；Claude Platform。API 模型名：claude-sonnet-5

注意：采用了更新的 tokenizer（相同输入下 token 数增加 1.0-1.35 倍）。促销定价可实现成本中性的迁移过渡。

## 性能基准测试

Sonnet 5（橙色线）在 Sonnet 4.6（灰色线）的基础上全面改进。Opus 4.8（黄色线）在最高精度场景仍更优，但 Sonnet 5 提供了低成本的高质量选择。用户可以调节 effort 级别（包括 "xhigh" = 额外高级别）来平衡成本和性能。

## 安全与保障

- 不良行为率低于 Sonnet 4.6（自动化行为审计）
- 对恶意请求的拒绝和对抗性提示注入攻击的抵抗能力更好
- 幻觉率和谄媚率更低
- 默认启用网络安防措施（与 Opus 4.7/4.8 相同，比 Fable 5 宽松）
- 在开发可用的 Firefox 漏洞利用方面成功率为 0%（对比 Opus 4.8 和 Mythos 5）
- 属于网络验证计划的一部分（在 Claude Platform、AWS、Microsoft Foundry 上可用；即将登陆 Google Vertex）

## 早期合作伙伴反馈

GitLab："Claude Sonnet 5 为我们的 Agent 提供了强大的多步骤软件工程执行层。它能很好地处理持续编程、工具使用和调试等复杂技术环境。"

Salesforce："我们交给 Claude Sonnet 5 一个两部分的任务——更新 Salesforce 客户层级，向企业联系人发送发布公告——它端到端地完成了。这以前总是做到一半就卡住了。"

Lovable："Claude Sonnet 5 用更少的步骤完成更多事。同样的输出质量，更少步骤就能到达目标。它能干净且一致地拒绝不安全的请求。"

Replit："我们用 Claude Sonnet 5 测试了几十个我们最具挑战性的真实 pull request，它独立地把每一个都推进到了经过测试和验证的结果。"

Cursor："我让 Claude Sonnet 5 调查一个 bug。没有提示，它自己写了一个重现测试，实现了修复，然后把修复暂存，确认没有这个修改 bug 会重新出现。全部在一个回合内完成。"

Vercel："有了 Claude Sonnet 5，Agent 能坚持执行计划、遵循我们的规约、交付干净的多步骤变更，而且成本很高效。"

Sourcegraph："Claude Sonnet 5 在陈旧代码上表现最佳——竞态条件、隐藏测试、那些谁都不想去碰的部分。"

Eve："Claude Sonnet 5 在 Eve 的原告律所任务中处于帕累托前沿。我们在法律研究和分析方面看到了最明显的提升。"

ClickHouse："Claude Sonnet 5 用更紧凑的步骤推理，让我们的用户明显更快地得到答案。"

Pace："在 Pace，我们的计算机使用 Agent 运行保险工作流……Claude Sonnet 5 始终采取正确的行动，而且行动迅速。"

## 更新后的基准测试（与 Sonnet 4.6 发布时对比）

- Humanity's Last Exam：Sonnet 4.6 更新为 34.6%（无工具），46.8%（有工具）
- OSWorld-Verified：Sonnet 4.6 已更新为 78.5%

## 相关链接

- Claude Science - AI workbench for scientists
- Claude Tag - 新的团队协作功能
- Seoul Office & Korean Partnerships

## 全文详情

- Claude Sonnet 5 System Card
- Claude API 文档
- Cyber Safeguards 文档
