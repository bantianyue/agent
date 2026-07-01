# full_translation.md — Prompt Caching with Deep Agents

## 原文全文翻译

在规模化运行 Agent 时一个强大的降本杠杆是 **Prompt Caching（提示缓存）**，这是模型提供商提供的一项功能，可将推理的 Token 成本降低 41-80%。正如 Manus AI 所说：

> "如果只能选一个指标，我会说 KV-cache 命中率是生产级 AI Agent 最重要的单一指标。"

然而，不同模型提供商对缓存控制的支持策略各不相同，这使得跨厂商的通用缓存方案成为一个棘手的问题。

Deep Agents 是我们的通用、模型无关的 Agent 编排层（harness），支持所有主流提供商的 Prompt Caching 功能。我们将深入探讨 Deep Agents 如何利用 Prompt Caching 来降低 API 成本，但首先让我们看看 Prompt Caching 如何在聊天模型对话中减少 Token 成本。

## TL;DR：Prompt Caching

聊天模型对话的 Token 成本增长很快。每条新消息，模型都必须重新处理对话中的每一个历史 Token，包括：
- 系统提示词
- 工具描述
- 加载的技能
- 消息历史
- 新消息

当我们启用 Prompt Caching 时，提供商会存储模型在处理完提示词后的状态快照：

在下一次请求时，模型从该快照恢复，只处理新的文本。

然而，加载新的技能或工具可能会修改对话中**较早**的提示词，可能导致缓存失效。部分模型提供商允许我们在提示词中较早位置添加显式缓存断点，这样可以在提示词的子集上实现缓存命中，而不是完全缓存失效。但并非所有提供商都支持显式缓存断点：

|  | Anthropic | OpenAI | Gemini | AWS Bedrock | Fireworks |
|---|-----------|--------|--------|-------------|----------|
| 显式断点 | ✅ | ❌ | ✅ | 视提供商而定 | ❌ |

显式缓存只是 Prompt Caching 的一个特性，各提供商的支持情况也不相同：

|  | Anthropic | OpenAI | Gemini | AWS Bedrock | Fireworks |
|---|-----------|--------|--------|-------------|----------|
| 显式断点 | ✅ | ❌ | ✅ | 视提供商而定 | ❌ |
| 可配置 TTL | ✅ | 视模型而定 | ✅ | 视提供商而定 | ❌ |
| 缓存预热 | ✅ | ❌ | ❌ | Anthropic | ❌ |
| 路由键 | ❌ | ✅ | ❌ | OpenAI | ✅ |

提示缓存功能支持的格局变化很快。请务必查阅各模型提供商的文档以了解功能支持情况。

在各提供商不同的 Prompt Caching 实现和功能支持之间，要实现跨提供商的最高成本节省是一个挑战。

## Deep Agents 的解决方案

Deep Agents 编排层通过以下方式自动尽力利用 Prompt Caching 功能：

1. 在支持时设置显式缓存断点
2. 在不支持显式断点时启用提供商端的隐式缓存
3. 结构化你的提示词以最大化缓存读取

这些策略支持**所有主流提供商**，因此你可以随时切换提供商，仍然获得最大的 Token 节省。为利用特定提供商的功能，编排层会检测当前模型的提供商，并将缓存委托给特定于提供商的中间件。你也可以在自己的 `createAgent()` 中使用该中间件来启用 Prompt Caching 节省：

```javascript
// 使用 Deep Agents 免费获得 Prompt Caching
const agent = createDeepAgent({ model: 'gpt-5.5' });

// 在 LangChain 中，通过中间件启用：
const agent = createAgent({
  model: 'claude-haiku-4-5-20251001',
  middleware: [anthropicPromptCachingMiddleware()],
});
```

Deep Agents 编排层还会结构化你的提示词和显式缓存点，以最小化缓存退化。理想情况下，模型调用中的静态前缀（你的工具描述、技能、系统提示词）应保持不变。但当你在更新记忆或压缩对话时，它**可能**发生变化，导致缓存失效。Deep Agents 通过结构化你的提示词和显式缓存点来最小化影响范围——例如，如果记忆被更新，你仍然可以在提示词的子集上获得缓存读取。

## Prompt Caching 的实际节省

功能表告诉我们什么是可能的。为了看看 Prompt Caching 实际能节省多少，我们在来自三个提供商的中端模型上运行了 Deep Agents 评测套件：`claude-haiku-4-5`、`gpt-5.4-mini` 和 `gemini-3.5-flash`。结果如下面的图表所示。在真实的 Agent 轨迹上，Prompt Caching 将 Token 成本降低了 49-80%。

- `claude-haiku-4-5`：**-77%**。利用 Anthropic 的显式断点，我们可以保持提示词中很大一部分被缓存。这显著降低了每次请求的 Token 成本。
- `gpt-5.4-mini`：**-80%**。OpenAI 的自动最长前缀缓存为我们带来了 80% 的成本降低。
- `gemini-3.5-flash`：**-49%**。Gemini 的隐式缓存不提供明确的节省保证，但我们仍然看到了可观的节省。

值得注意的是，缓存对长对话的回报更大：缓存的前缀在每一轮对话中被复用，因此长时间运行的任务受益最大。

## LangSmith 的可观测性

Prompt Caching 的成本节省只有在你能够衡量它们时才真正有价值。LangSmith 在单次调用和单次轨迹层面提供了 API 成本、缓存读取和 Token 使用情况的可视性：

对于每次调用，你可以获得首 Token 时间、总输入 Token 数、缓存读取 Token 数和总输出 Token 数，汇总到单次轨迹的聚合数据中。由于缓存读取被单独列出，你可以确切地看到每次提示中有多少来自缓存而不是被重新处理。

这也是我们生成本文数据的方式：

1. 对每个 Agent 配置运行 Deep Agents 评测套件
2. 在 LangSmith 仪表盘中检查轨迹数据以验证运行结果
3. 通过 LangSmith 客户端 SDK 拉取运行数据
4. 将数据放入 Jupyter Notebook 中计算各提供商的成本差异（或者让 Agent 使用 LangSmith Skills 来协助）

LangSmith 让我们能够区分来自缓存、轨迹长度和更便宜轮次的节省，这可以指导我们如何优化 Agent。更多关于如何在 LangSmith 中读取和操作数据的信息，请参见相关文档。

## Prompt Caching 的下一步

模型提供商尚未就 Prompt Caching 的通用功能集达成一致。显式断点推动了上述部分节省，但这只是开始。其他几个功能——缓存预热、路由键、可配置 TTL——有望解锁进一步的成本节省和延迟优势。

现在你可以通过使用 `createDeepAgent` 来利用当前支持的功能——无需额外配置。随着模型提供商添加更多功能支持，我们将继续将它们整合到现有编排层中。
