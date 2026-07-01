# Claude Managed Agents: 10 倍速从想法到生产

来源：Anthropic 博客
状态：Claude Platform 公开测试版

## 概述

Claude Managed Agents 是一套可组合的 API，用于构建和部署云端托管的 Agent。它省去了从零构建安全基础设施、状态管理、权限管理和 Agent 循环的全部工作。

"无论你是在构建单任务运行器还是复杂的多 Agent 管线，你都可以专注于用户体验，而不是运维开销。"

## 核心功能

- 沙箱代码执行 —— 安全运行时环境
- 检查点 —— 跨会话状态持久化
- 凭证管理 —— 内置安全机制
- 作用域权限 —— 细粒度访问控制
- 端到端追踪 —— 完整可观测性
- 内置编排 Harness —— 决定何时调用工具、管理上下文、从错误恢复
- 会话追踪与分析 —— 在 Claude Console 中检查每次工具调用、决策和失败模式

## 性能与能力

- 基于结果的 Agentic 模式（研究预览）：定义目标和成功标准，Claude 自我评估并迭代直到成功
- 也支持传统的请求-响应工作流，用于更严格的控制
- 内部测试（结构化文件生成）：Managed Agents 在任务成功率上比标准提示循环提高了最多 10 个百分点，在最困难的问题上提升最大

## 定价

- 标准 Claude Platform token 费率（不变）
- 活跃运行时长：每小时 $0.08

## 入门

1. 阅读文档
2. 前往 Claude Console
3. 使用新 CLI 部署你的第一个 Agent
4. Claude Code 用户输入："start onboarding for managed agents in Claude API"

## 合作伙伴案例

**Notion**：整合了 Claude Managed Agents，能够处理长时间运行会话、管理记忆、随时间产出高质量输出。用户现在可以在 Notion 内委托开放式复杂任务——从编码到生成幻灯片和电子表格。

**Rakuten**：有了 Claude Managed Agents，高级用户变成"伽利略"式的跨领域贡献者。每周部署一个专精 Agent，管理工程、产品、销售、市场和财务部门的长时间运行任务。

**Asana**：Claude Managed Agents 显著加速了 Asana AI Teammates 的开发，以更快的速度交付高级能力。

**VibeCode**：之前用户需要手动在沙箱中运行 LLM、管理生命周期、装备工具。现在几行代码就能 10 倍速启动同样基础设施。

**Sentry**：客户现在可以从 Seer 的根因分析直接到 Claude Agent 写修复并开 PR。Managed Agents 让初始集成从数月缩至数周，并消除了后续运维开销。

**Atlassian**：有了 Claude Managed Agents，几周内就能为开发者构建 Agent 并嵌入团队已有的工作流。Managed Agents 处理沙箱化、会话和作用域权限等困难部分。

**General Legal**：用 Claude Managed Agents 构建的系统能从用户文档和通信中提取信息来回答任何问题，还能即时按需编码所需工具。开发时间缩短 10 倍。

**Blockit**：Claude Managed Agents 让构建生产级会议准备 Agent 快了 3 倍，从想法到上线仅用数天。

## 关键指标

- 生产就绪时间：快 10 倍（数周 vs 数月）
- 任务成功率（最难问题）：最多提高 10 个百分点
- Blockit 开发速度：快 3 倍
- General Legal 开发速度：快 10 倍
- VibeCode 基础设施搭建：快 10 倍
