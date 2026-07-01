<div style="background:#e8f4fd;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:18px;">
<div style="text-align:center;margin-bottom:10px;">
<strong style="font-size:16px;color:#1a6ba0;">要点速览</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
- <strong>Prompt Caching 省 49-80% 成本</strong>：在 claude-haiku-4-5（-77%）、gpt-5.4-mini（-80%）、gemini-3.5-flash（-49%）三个中端模型上实测验证<br><br>
- <strong>跨厂商自动适配</strong>：Deep Agents 编排层自动检测模型提供商，支持显式断点（Anthropic/Gemini）、隐式缓存（OpenAI）、路由键等差异化策略<br><br>
- <strong>单一指标决定一切</strong>：Manus AI 指出 KV-cache 命中率是生产级 AI Agent 最重要的单一指标<br><br>
- <strong>对话越长收益越大</strong>：缓存前缀跨轮复用，长时间运行的任务受益最多
</div>
</div>

**Prompt Caching 能把推理成本砍掉 80%，同时响应质量不变。主流模型提供商都已经支持，但每家策略不同。**

如果你在 Anthropic 上设了显式断点，切到 OpenAI 就不工作了。反过来，OpenAI 的自动前缀缓存搬到 Fireworks 上也没有效果。

**LangChain 的 Deep Agents 编排层做了跨厂商适配**：自动检测模型提供商，选合适的缓存策略，提高跨轮对话的缓存命中率。实测在中端模型上能省 49-80% 的 Token 成本。

规模化运行 Agent 时，**Prompt Caching** 是有效的降本手段。模型提供商将其作为一项功能提供，能把推理 Token 成本降低 41-80%。正如 Manus AI 所说：

> 如果只能选一个指标，我会说 KV-cache 命中率是生产级 AI Agent 最重要的单一指标。

但不同模型提供商对缓存控制的支持策略各不相同，跨厂商统一缓存方案并不容易。

**Deep Agents 是 LangChain 的 Agent 编排层**，做了模型无关的抽象，支持主流提供商的 Prompt Caching。下面看它是怎么利用缓存降成本的。

**聊天模型对话的 Token 成本增长很快。** 每条新消息，模型都要重新处理对话中所有历史 Token。下图展示没有缓存时的对话成本：每轮都要重算全部上下文。

![无缓存的对话 Token 成本](img1.png)
<span style="font-size:12px;color:rgb(153,153,153);">无缓存时，每轮对话的 Token 成本由全部历史上下文决定</span>

**启用 Prompt Caching 后，提供商会存储模型处理完提示词后的状态快照。** 下一次请求时，模型从该快照恢复，只处理新文本。

![启用 Prompt Caching 后的对话 Token 成本](img2.png)
<span style="font-size:12px;color:rgb(153,153,153);">启用 Prompt Caching 后，缓存部分只计 10% 成本，仅新 Token 按全价计费</span>

加载新技能或工具会修改对话中**较早**的提示词，可能导致缓存失效。部分提供商允许在提示词中添加显式缓存断点，这样能在子集上命中缓存而不用完全失效。但并非所有提供商都支持：

|  | Anthropic | OpenAI | Gemini | AWS Bedrock | Fireworks |
|---|-----------|--------|--------|-------------|----------|
| 显式断点 | ✅ | ❌ | ✅ | 视提供商而定 | ❌ |

**显式缓存只是 Prompt Caching 的一个特性，各提供商支持情况不同。** 可配置 TTL、缓存预热、路由键：每家支持的组合都不同。

|  | Anthropic | OpenAI | Gemini | AWS Bedrock | Fireworks |
|---|-----------|--------|--------|-------------|----------|
| 显式断点 | ✅ | ❌ | ✅ | 视提供商而定 | ❌ |
| 可配置 TTL | ✅ | 视模型而定 | ✅ | 视提供商而定 | ❌ |
| 缓存预热 | ✅ | ❌ | ❌ | Anthropic | ❌ |
| 路由键 | ❌ | ✅ | ❌ | OpenAI | ✅ |

各厂商对提示缓存的支持变化很快。实现和功能各不相同，跨厂商做到最大成本节省并不简单。

## Deep Agents 的跨厂商解决方案

Deep Agents 编排层通过以下方式自动利用 Prompt Caching 功能：

1. **在支持时设置显式缓存断点**
2. **在不支持显式断点时启用提供商端的隐式缓存**
3. **结构化提示词以最大化缓存读取**

这些策略覆盖**所有主流提供商**，切换提供商后仍能获得最大 Token 节省。编排层会检测当前模型提供商，把缓存委托给对应的中间件。

```javascript
// 使用 Deep Agents 免费获得 Prompt Caching
const agent = createDeepAgent({ model: 'gpt-5.5' });

// 在 LangChain 中，通过中间件启用：
const agent = createAgent({
  model: 'claude-haiku-4-5-20251001',
  middleware: [anthropicPromptCachingMiddleware()],
});
```

**Deep Agents 编排层还会结构化提示词和缓存点，让缓存退化降到最低。** 理想情况下，模型调用中的静态前缀（工具描述、技能、系统提示词）应保持不变。但更新记忆或压缩对话时，它**可能**变化，导致缓存失效。

**Deep Agents 的思路是结构化提示词和缓存点，缩小影响范围**。例如，记忆更新后，你仍然能在提示词子集上获得缓存读取。完全避免缓存失效不可能，但可以把「爆炸半径」控制到最小。

## 真实成本节省

功能表说明了可能性。为了看实际能省多少，Deep Agents 团队在三个中端模型上跑了评测：`claude-haiku-4-5`、`gpt-5.4-mini` 和 `gemini-3.5-flash`。结果如下：

![Prompt Caching 实测成本节省数据](img3.png)
<span style="font-size:12px;color:rgb(153,153,153);">三类模型在 Agent 轨迹上的 Prompt Caching 节省比例实测数据</span>

- `claude-haiku-4-5`：**-77%**。利用 Anthropic 的显式断点，保持提示词中很大一部分被缓存，显著降低了每次请求的 Token 成本
- `gpt-5.4-mini`：**-80%**。OpenAI 的自动最长前缀缓存带来了 80% 的成本降低
- `gemini-3.5-flash`：**-49%**。Gemini 的隐式缓存不提供明确的节省保证，但仍然有可观的效果

**缓存对长对话的回报更大。** 缓存的前缀在每一轮对话中被复用，长时间运行的任务受益最多。

## LangSmith 的可观测性

Prompt Caching 省了多少，得能看见才有意义。**LangSmith 在单次调用和单次轨迹层面，提供了 API 成本、缓存读取、Token 使用情况的明细。**

![LangSmith 可观测性仪表盘](img4.png)
<span style="font-size:12px;color:rgb(153,153,153);">LangSmith 提供每轮调用的缓存命中数据与成本分析</span>

对于每次调用，你可以获得首 Token 时间、总输入 Token 数、缓存读取 Token 数和总输出 Token 数，汇总到单次轨迹的聚合数据中。由于缓存读取被单独列出，你能清楚看到每次提示有多少来自缓存、多少被重新处理。

LangSmith 也是本文数据的来源：对每个 Agent 配置运行 Deep Agents 评测套件 → 在 LangSmith 仪表盘中检查轨迹数据 → 通过 SDK 拉取运行数据 → 在 Jupyter Notebook 中计算各提供商的成本差异。

**LangSmith 能帮我们区分缓存带来的节省、轨迹长度带来的节省、以及更便宜轮次带来的节省：这对优化 Agent 有用。**

## 接下来的方向

模型提供商尚未就 Prompt Caching 的通用功能集达成一致。显式断点贡献了上述部分节省，但只是开始。**缓存预热、路由键、可配置 TTL：这些功能还有进一步降本和降低延迟的空间。**

现在你可以通过 `createDeepAgent` 直接利用当前支持的功能，无需额外配置。随着模型提供商添加更多功能支持，LangChain 表示会继续将它们整合到现有编排层中。

<div style="background:#f5f0eb;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:16px;">
<div style="text-align:center;margin-bottom:8px;">
<strong style="font-size:15px;color:#8b6f4c;">结语</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
这篇文章出自 LangChain 官方博客，本质上是一篇产品推介，但数据的含金量很高。77% 和 80% 的节省来自显式断点和自动前缀缓存这两种完全不同的机制，且在同一套评测基准上测得，这个对比本身就很有参考价值。<br><br>
跨厂商的缓存适配是个典型的「中间层机会」问题：每家的实现都不同，但如果有一层帮你自动适配，用户就不用操心。Deep Agents 做的正是这件事，而 LangSmith 的可观测性则确保你不会盲目相信省钱数字：能看到就是能管理。<br><br>
如果你的 Agent 已经在生产中跑长对话，且用单一模型提供商，大概率已经在享受部分缓存收益了。真正的价值在于：当你想切模型或混合使用时，缓存策略不需要重写。
</div>
</div>

---

<span style="font-size:12px;color:#888888;font-family:'Courier New',monospace;">参考：

https://www.langchain.com/blog/deep-agents-prompt-caching</span>
