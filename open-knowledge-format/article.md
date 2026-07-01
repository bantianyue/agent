**Google Cloud 发布了一个新标准：Open Knowledge Format（OKF）。不是平台，不是 SDK，就是一个目录的 Markdown 文件加 YAML 头信息。但它要解决的是 Agent 时代最根本的问题——上下文碎片化。**

---

<div style="background:#e8f4fd;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:18px;">
<div style="text-align:center;margin-bottom:10px;">
<strong style="font-size:16px;color:#1a6ba0;">要点速览</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
- <strong>OKF 是格式，不是平台</strong>：Markdown + YAML frontmatter 的目录结构，无专有账户、无 SDK、无运行时要求<br><br>
- <strong>解决 Agent 上下文碎片化</strong>：表结构、指标定义、Runbook、API 变更散落在元数据目录、Wiki、代码注释和资深工程师脑子里，每个 Agent 构建者都在重复造轮子<br><br>
- <strong>三条设计原则</strong>：最小化意见（仅 type 为必填）、生产者/消费者解耦、格式即标准<br><br>
- <strong>Google 已配套开源</strong>：BigQuery 富化 Agent、静态 HTML 可视化器、三个示例 Bundle（GA4 电商、Stack Overflow、Bitcoin）
</div>
</div>

**基础模型在持续进步，但缺乏相关上下文往往限制了它们的能力，尤其是在构建 Agent 系统时。** 企业内部知识——表结构、指标定义、Runbook、Join 路径、API 废弃通知——散落在各自为政的系统中：专有 API 的元数据目录、Wiki、共享网盘、第三方工具、代码注释、Notebook 单元格，以及"几个资深工程师的脑子里"。

**每个 Agent 构建者都在从零解决同一个上下文组装问题，每个目录供应商都在重新发明同一个数据模型，而知识本身被锁在创造它的表面后面。**

Google Cloud 的答案是 Open Knowledge Format（OKF）v0.1。**OKF 将知识表示为一个 Markdown 文件目录，带 YAML frontmatter，加上一小套约定，让不同生产者编写的 Wiki 能被不同 Agent 消费，无需翻译层。**

"就是 Markdown。任何编辑器都能读，GitHub 上能渲染，任何搜索工具都能索引。就是文件。可以作为 tarball 分发，可以托管在任何 Git 仓库里，可以挂载到任何文件系统上。就是 YAML frontmatter——用于结构化字段。"

**没有复杂的压缩方案，没有新的运行时，没有必需的 SDK。格式本身就是贡献。**

**OKF 的工作原理**

一个 Bundle 是一个 Markdown 文件目录，每个文件代表一个概念（表、数据集、指标、Playbook、Runbook、API 等）。文件路径 = 概念身份。

```
sales/
├── index.md
├── datasets/
│   ├── index.md
│   └── orders_db.md
├── tables/
│   ├── index.md
│   ├── orders.md
│   └── customers.md
└── metrics/
    ├── index.md
    └── weekly_active_users.md
```

每个概念文档包含 YAML frontmatter（结构化字段：type、title、description、resource、tags、timestamp）和 Markdown 正文（Schema、Joins、描述等）。概念之间通过标准 Markdown 链接相互引用，形成一个关系图。可选 `index.md`（渐进式披露）和 `log.md`（变更历史）。

**三条设计原则**

**1. 最小化意见。** 唯一必填字段是 `type`。其余全部由生产者定义。不强制命名规范、目录结构或内容组织方式。

**2. 生产者/消费者独立。** 人工编写的 Bundle 可以被 AI Agent 消费；流水线生成的 Bundle 可以在可视化器中浏览。格式就是契约。

**3. 格式，不是平台。** 不绑定任何云、数据库、模型供应商或 Agent 框架。开放标准。

**Google 随规范发布了什么**

| 组件 | 说明 |
|------|------|
| **富化 Agent** | 遍历 BigQuery 数据集，为表/视图起草 OKF 文档，然后通过第二轮 LLM 调用富化引用、Schema 和 Join 路径 |
| **静态 HTML 可视化器** | 将任何 OKF Bundle 转为交互式图谱视图（单个自包含文件，无后端，数据不离开页面） |
| **三个示例 Bundle** | GA4 电商、Stack Overflow、Bitcoin 公共数据集——由参考 Agent 生成，作为活的示例提交到仓库 |

**这些是概念验证，刻意为之。Agent 演示了一种生成 OKF 的方式；格式本身不要求特定的 Agent 框架或 LLM。**

**Karpathy 的 LLM Wiki 模式**

OKF 的灵感来自 Andrej Karpathy 推广的"LLM Wiki"模式——用 Markdown 文件作为 AI Agent 的知识库。Karpathy 的原话：**"LLM 不会感到无聊，不会忘记更新交叉引用，可以一次触碰 15 个文件。"**

Google 团队将这种非正式模式形式化为一个开放规范。**"这个问题的答案不是另一个知识服务。你需要一个格式。"**

**下一步**

- 阅读规范（短，一页）
- 为你的源系统编写生产者
- 编写消费者（查看器、搜索索引、Agent）
- 针对自己的数据尝试参考实现
- 提交 Issue、发送 PR、提议扩展——规范是版本化的，向后兼容

**GitHub 仓库：** [GoogleCloudPlatform/knowledge-catalog](https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf)

Google Cloud 的 Knowledge Catalog 已更新为能摄入 OKF。

---

<div style="background:#f5f0eb;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:16px;">
<div style="text-align:center;margin-bottom:8px;">
<strong style="font-size:15px;color:#8b6f4c;">结语</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
OKF 最聪明的地方在于它刻意不做的事：不发明新格式、不要求新运行时、不绑定 Google Cloud。Markdown + YAML 是每个开发者都熟悉的原语，这大幅降低了采用门槛。对比一下那些需要专有 SDK 和 API 的元数据标准，OKF 的"无聊"反而是最大的优势。<br><br>
但格式只是第一步。真正的挑战在于：谁负责维护这些 OKF 文件？如果依赖 Agent 自动生成，那 Agent 的质量决定了知识库的质量；如果依赖人工维护，那它和现有的 Wiki 有什么区别？Google 的 BigQuery 富化 Agent 是一个聪明的切入点——从数据库 Schema 自动生成，至少保证了"不会过时"的下限。
</div>
</div>

---
<span style="font-size:12px;color:#888888;">参考：How the Open Knowledge Format can improve data sharing<br>https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing/</span>
