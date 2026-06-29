<div style="background:#e8f4fd;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:18px;">
<div style="text-align:center;margin-bottom:10px;">
<strong style="font-size:16px;color:#1a6ba0;">要点速览</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
- <strong>Coding Plan 按 Prompt 计费</strong>：不是按 Token 数，一个超大 Prompt 和一个小 Prompt 消耗一样的额度，这是最大误解<br><br>
- <strong>缓存折扣高达 81%</strong>：重复的前缀内容会被缓存，收费从 $1.40/M 降到 $0.26/M，前提是把复用内容放在 Prompt 开头<br><br>
- <strong>免费模型 + 低配模式</strong>：GLM-4.7-Flash 和 GLM-4.5-Flash 完全免费，大部分日常任务不需要 5.2 上场；5.2 的 Max 推理模式只在复杂重构时才用
</div>
</div>

**GLM 5.2 额度不够用？10个习惯让你不超限！**

6 月 13 日，GLM 5.2 正式发布，作为 Fable 5 的直接竞争对手，用户们立刻遇到一个问题：额度（limits）消耗得太快了。

但很多人不理解一个关键点：**GLM 的 Coding Plan（订阅制）按 Prompt 次数计费——不是按 Token 数！**

API 按 Token 计费——但人们花得太快了。

直到我改了这 10 个习惯，额度才够用。

**1. 为什么你会超额**

首先，你得搞清楚你付的钱到底买了什么。

GLM 有两种完全不同的计费模式：

1. **Coding Plan（订阅制）——按 Prompt 次数，不是 Token 数**

```
Lite（~$18/月）：每 5 小时约 80 个 Prompt
Pro：每 5 小时约 600 个 Prompt
Max/Team：更高
```

**一个大 Prompt 和一个小 Prompt——价钱一样。**

用户们烧掉额度的方式是：发 50 个一句话的问题，而不是把它们打包成 5 个结构良好的 Prompt。

2. **API（按量计费）——按 Token 数**

```
input：        $1.40 / 1M
output：       $4.40 / 1M
cached input： $0.26 / 1M
```

换句话说，**如果你用的是订阅制，绝不应该发无意义的 Prompt**——否则你会很快超额。

**2. 缓存——81% 的折扣**

当你反复发送一个长而稳定的前缀——System Prompt、工具定义、一直引用的大文件——提供商会缓存处理过的前缀。

下一次调用时，那部分按 $0.26/M 而不是 $1.40/M 计费：**每个 Prompt 的重复部分享受约 81% 的折扣。**

让它生效的规则：

- 把重复使用的内容放在 Prompt**开头**
- 把变量内容放在**结尾**（缓存以前缀为 key）
- **缓存会过期**——此折扣适用于时间上接近的调用，不是每小时一次

Claude Code、Cline、Cursor 等编码 Agent 在每个轮次都会重发大量稳定的前置内容：指令、工具 Schema、仓库上下文。**缓存这些前置内容能大幅降低每轮成本。** 不用缓存，等于每次都按全价重复发送同样的 Token。

**3. 免费模型——不需要 5.2 的时候就别用**

大多数任务不需要前沿模型。智谱提供了两个真正免费的模型，没有试用限制：

- **GLM-4.7-Flash**：免费，203k 上下文，适合格式化和简单补全
- **GLM-4.5-Flash**：免费，轻量通用

Flash 最适合处理格式化、重命名、快速语法问题和样板代码片段。**把 GLM 5.2 留给需要分析推理的任务。**

仅这一个习惯，就能让你的 Lite 套餐使用时间翻倍。

**4. 推理级别——别老是跑 Max**

GLM 5.2 有两种思考模式：**High** 和 **Max**。

智谱说 Max 应该是编码的默认模式，但 Max 每次调用消耗更多额度和更多 Token——**大多数任务不需要最大推理深度。**

- **High**：常规修改、草稿、简单逻辑
- **Max**：复杂重构、架构设计、棘手的 Bug

合理选择何时用 Max，**绝对不要用 Max 去修一行代码**——否则很快超额。

**5. 100 万 Token 陷阱**

100 万上下文窗口是其头号卖点——但用错了就是个陷阱。

通过 `glm-5.2[1m]` 模型后缀可以加载完整窗口，但加载一个庞大的上下文意味着每一轮都在处理海量输入——**即使模型只需要其中的一小部分。**

规则：

- 不要为了修一个文件就把整个 5 万行仓库加载进去
- **只在任务真正需要时才加载 100 万窗口**
- 其他时候保持上下文精简——模型每轮都会重读你给它的所有内容

**6. 自托管——永久零 Token 成本**

GLM 5.2 以 MIT 许可发布——权重是**免费的**。

如果你的用量足够高且有硬件，你可以自己跑模型，每 Token 成本为零。它把计量账单变成了固定的计算成本：

- 753B MoE（~40B 活跃）
- 100 万上下文，MIT 权重
- 在自己基础设施上跑 = 无额度、无 Token 费

社区已经在把权重量化为 4-bit 和 2-bit 版本。

对多数人现实的玩法：先用托管方案，等出现单节点配置后再评估自托管。**对于重度用户，这才是真正的「免费 GLM 5.2」。**

**7. 配置——精确的设置**

把 GLM 5.2 接入 Claude Code 的 Coding Plan：

```
export ANTHROPIC_BASE_URL="https://api.z.ai/api/coding/paas/v4"
export ANTHROPIC_API_KEY="your-g...-key"
export ANTHROPIC_DEFAULT_SONNET_MODEL="glm-5.2[1m]"
export ANTHROPIC_DEFAULT_OPUS_MODEL="glm-5.2[1m]"
export CLAUDE_CODE_AUTO_COMPACT_WINDOW=1000000
export API_TIMEOUT_MS=3000000
```

`API_TIMEOUT_MS` 的值很重要。**没有这个长超时，Claude Code 会在 GLM 5.2 完成之前杀死大上下文调用。** 设高一点，否则你的额度会浪费在从未完成的调用上。

注意：Coding Plan 的 Key 是不同于标准 API Key 的凭据。在不支持的工具中的调用会回退到标准 API 计费。

**8. 批量打包你的 Prompt**

这一条对 Coding Plan 用户最管用。

记住：**套餐按 Prompt 次数计费，不是按 Token 数。**

- 10 个单独的一行问题 = 10 个 Prompt
- 10 个问题放在一条结构化消息里 = 1 个 Prompt

不要拆成 10 个 Prompt：「改这个变量」「修复那个 import」「在这里加个类型」……

做成 1 个 Prompt：「一次性做这些：把 X 重命名为 Y，修复第 4 行的 import，给函数参数加类型，更新测试」

**把相关工作打包到单个 Prompt，可以让你的额度提升 5-10 倍。** 这个习惯对 Lite 用户而言改变一切。

**9. 压缩长会话**

不断增长的历史记录，是每一轮的不断增长的账单。

到第 40 条消息时，模型每次发送都在重读数千 Token 的上下文：API 上这是你反复支付的输入 Token，Coding Plan 上它吞噬你的有效吞吐量。

规则：

- 每 30-40 条消息压缩或重新开始一个新会话
- **不要开一个超大会话跑一整天**
- 切换任务时从头开始

模型没有理由把你上午的上下文带进下午的任务。

**10. 不需要 5.2 时降到 GLM-4.7**

5.2 是旗舰，但 4.7 在 SWE-bench 上仍有 73.8%，每次调用成本更低。

- **GLM 4.7**：绝大多数日常编码、修改、标准功能
- **GLM 5.2**：复杂推理、100 万上下文任务、硬 Bug

大多数编码工作不需要绝对前沿。**把 5.2 留给真正需要其推理能力的任务，让 4.7 处理大部分工作。**

在 4.7 做中等任务、Flash 做简单任务的配合下，5.2 就不再是瓶颈。

---

<div style="background:#f5f0eb;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:16px;">
<div style="text-align:center;margin-bottom:8px;">
<strong style="font-size:15px;color:#8b6f4c;">结语</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
GLM 5.2 不是免费的。市面上流传的「免费 Token」说法大部分是错的——唯一真正免费的路径是 Flash 模型和自托管开源权重。<br><br>
但**一个人一小时内超额和另一个人用同样套餐编码一整天之间的差距，不是套餐本身——是这 10 个习惯。**<br><br>
而且最重要的是：**你在花的是你的 Prompt，不是你的 Token。**
</div>
</div>

---
<span style="font-size:12px;color:#888888;">参考：https://x.com/0x_kaize/status/2068775813785506091</span>
