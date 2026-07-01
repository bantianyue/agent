<div style="background:#e8f4fd;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:18px;">
<div style="text-align:center;margin-bottom:10px;">
<strong style="font-size:16px;color:#1a6ba0;">要点速览</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
- <strong>Dynamic Subagents 是什么</strong>：Agent 不再通过逐轮工具调用下发子任务，而是写一个脚本来编排 subagent 的执行：用 Agent 擅长写的代码（循环、分支、并发）来驱动协调逻辑<br><br>
- <strong>核心优势</strong>：确定性覆盖（调度循环不会"看情况"跳过项目）和可靠复杂编排（扇出+合成、多阶段流程、条件分支）<br><br>
- <strong>六种编排模式</strong>：分类并行动、扇出与合成、对抗验证、生成与过滤、锦标赛、循环直到完成，每种都有实时追踪链接<br><br>
- <strong>与 Claude Code Workflows 同源</strong>：Recursive Language Model 思想的最简形式：模型写代码，代码调度更多 Agent
</div>
</div>

当 Agent 承担更雄心勃勃的任务时，它们会遇到两个核心难题：如何可靠地大规模完成任务，以及如何管理自己的上下文。**LangChain 团队最近开源了一种新思路：Dynamic Subagents，它不是通过工具调用逐轮委派，而是让 Agent 自己写一段脚本来驱动 subagent 执行。**

这个思路与 Claude Code 的 Workflows 以及 arXiv 上的 Recursive Language Models 论文共享同一个核心洞察：模型擅长写代码（循环、分支、并发），那就让它写代码来编排 Agent，而不是用模型不擅长的逐轮工具调用来硬撑。

## 为什么需要 Dynamic Subagents？

Deep Agents 之前就已经支持普通的 Subagents：它们隔离上下文、让主 Agent 委派离散工作单元、将中间结果排除在主上下文窗口之外。但是，**普通 subagent 是逐个被主模型直接调用的，当你需要数百个 subagent 或编排逻辑是条件式/多阶段时，这种方式就彻底失效了。**

Dynamic Subagents 的核心替换方案是：Agent 不再逐轮做工具调用，而是编写一个简短脚本，在轻量级代码解释器中运行它。

典型场景：一篇 300 页的文档，每页需要一个 subagent 做摘要。用普通 subagent，Agent 要调用 300 次工具函数。用 Dynamic Subagents，Agent 写一个循环：

```javascript
const results = await Promise.all(pages.map(page =>
  task({ description: `Summarize page ${page.number}`, subagentType: "summarizer" })
));
```

这个微小的改变解锁了两件工具调用编排无法可靠做到的事：

![](HL_mpBCX0AAnNJe.jpg)
<span style="font-size:12px;color:rgb(153,153,153);">dcode 中 Dynamic Subagents 实时面板，按调度阶段分组显示 subagent 执行情况</span>

## 快速开始

使用 Dynamic Subagents 需要两样东西：Subagents 和 Code Interpreter。Deep Agents 内置了一个基于 QuickJS 的可选代码解释器，安装 QuickJS 中间件包后在 `create_deep_agent` 中通过 `middleware` 参数传入即可：

```bash
pip install -U "deepagents[quickjs]"
```

```python
from deepagents import create_deep_agent
from langchain_quickjs import CodeInterpreterMiddleware

agent = create_deep_agent(
    model="openai:gpt-5.5",
    middleware=[CodeInterpreterMiddleware()],
)
```

**要触发 Dynamic Subagents，向 Agent 发送包含 "workflow" 关键词的提示即可。** Agent 收到后会自动编写编排脚本，而不是自己埋头干活或手动管理 subagent 扇出。

最快试用的方式是 dcode，LangChain 基于 Deep Agent 构建的终端编码 Agent。它已预装代码解释器，Dynamic Subagents 开箱即用。安装后运行 `dcode`，然后说 "run a workflow to review every file in src/ for SQL injection"，就能看到 subagent 在实时面板中生成。

## 工作原理

Agent 被赋予一个 Eval Tool，编写 JavaScript 在解释器中安全执行。**当配置了 Subagents 时，解释器暴露一个内置的 `task()` 全局函数**：接受 `description`、`subagentType` 和一个可选的 `responseSchema`。当提供 `responseSchema` 时，返回的结果已经是类型化对象，可直接过滤或传递给下一步。

![](HL_mrZJXQAANIoZ.jpg)
<span style="font-size:12px;color:rgb(153,153,153);">task() 函数的工作流：Agent 编写 JavaScript，解释器安全执行，task() 调度 subagent 并返回结构化结果</span>

```javascript
const result = await task({
  description: "Review src/auth/login.ts for security issues.",
  subagentType: "reviewer",
  responseSchema: {
    type: "object",
    properties: {
      severity: { type: "string", enum: ["high", "medium", "low"] },
      issues: { type: "array", items: { type: "string" } },
    },
  },
});
const critical = result.severity === "high" ? result.issues : [];
```

## 六种编排模式

Anthropic 的 Dynamic Workflows 推广了一组并行 Agent 工作的编排模式。**它们不是你可以开启的"开关"，而是从工作中自然涌现的形状。** 下表将每种模式映射到它适合的工作类型：

![](HL_m5HxWsAE4iW3.jpg)
<span style="font-size:12px;color:rgb(153,153,153);">六种编排模式总览：Classify and Act、Fanout and Synthesize、Adversarial Verification、Generate and Filter、Tournament、Loop Until Done</span>

### 分类并行动（Classify and Act）

项目先被分类，然后每个项目由专门的 subagent 根据分类处理。**适用于混合输入场景，不同项目需要不同领域的专业知识。**

示例：分类支持工单积压。Agent 读取工单并将每个分类为 bug、feature request 或 question，然后分别交给 bug-investigator、feature-analyst 和 support-responder。最终输出按类别汇总的报告。[查看追踪](https://smith.langchain.com/public/20b1da82-de4a-4de4-ae20-6097c059cd94/r)

![](HL_nTO2W4AAf0Bf.jpg)
<span style="font-size:12px;color:rgb(153,153,153);">Classify and Act 流程：输入先分类，然后不同类别路由到不同的专门 subagent</span>

### 扇出与合成（Fanout and Synthesize）

将同类型工作并行分发给多个项目，然后合并结果。**适用于跨目录代码审查、批量文档分析、跨多个服务运行相同检查等场景。**

示例：跨源代码树的逐文件安全检查。Agent 发现 src/ 下所有 TypeScript 文件，并行为每个文件调度一个 security-reviewer，然后合并到一个按严重级别排序的报告中。[查看追踪](https://smith.langchain.com/public/d80cdf1a-37fc-4823-8500-417fe624fe3e/r)

![](HL_nY3xWAAAyDK4.jpg)
<span style="font-size:12px;color:rgb(153,153,153);">Fanout and Synthesize：同类型工作并行发出，结果统一合成</span>

### 对抗验证（Adversarial Verification）

两阶段模式：第一遍产生发现，第二遍每个发现发送给独立验证者，只有通过共识的才保留。**适用于误报代价高的场景：安全审计、合规检查。**

示例：安全审计中，审计员先广泛扫描漏洞，然后每个发现交给独立的验证者重新阅读代码并返回 CONFIRMED 或 REFUTED。只有确认的发现进入最终报告。[查看追踪](https://smith.langchain.com/public/6f47c6c5-34ee-454e-9ffe-bf23e4a619e6/r)

![](HL_nhh-XYAAUKig.png)
<span style="font-size:12px;color:rgb(153,153,153);">Adversarial Verification：第一遍产生发现，第二遍独立验证，只有共识结果保留</span>

### 生成与过滤（Generate and Filter）

多个 subagent 独立生成同一问题的多个解决方案，Agent 在代码中比较、评分和过滤，只保留最好的。**适用于需要先探索多个选项再承诺的任务：架构方案、内容变体。**

示例：对 rate-limiter.ts 进行竞争性重设计。架构师生成多个独立的重新设计方案，每个写入自己的文件以免互相覆盖。然后根据正确性、多实例支持和复杂度评分，最强方案胜出。[查看追踪](https://smith.langchain.com/public/fbecf524-e8c5-4db4-930f-4a82b22d5d59/r)

![](HL_nr7uWMAAwPb7.jpg)
<span style="font-size:12px;color:rgb(153,153,153);">Generate and Filter：多个独立方案生成后评分筛选，保留最佳</span>

### 锦标赛（Tournament）

变体由评判 subagent 进行头对头比较，胜者通过淘汰轮次晋级。**适用于主观标准下的优化、样式选择、竞争实现之间的选择。**

示例：对混乱的 createOrder 处理器进行成对淘汰。几个写手产生不同优先级的候选重写方案，评判者头对头比较，逐轮晋级直到冠军脱颖而出。[查看追踪](https://smith.langchain.com/public/f89bcdb7-57be-4a3e-a290-36dbdaaa4294/r)

![](HL_nwwpXYAAmNhZ.png)
<span style="font-size:12px;color:rgb(153,153,153);">Tournament：变体头对头比较，胜者逐轮晋级</span>

### 循环直到完成（Loop Until Done）

Agent 运行发现循环，对已发现的结果去重，直到没有新结果出现。**适用于工作范围未知的场景：穷举搜索、死代码检测、依赖审计。**

示例：分轮安全扫描。Agent 运行一轮扫描，只有前一轮发现新问题时才启动下一轮。当一轮没有新发现时停止，报告整合发现和总共轮数。[查看追踪](https://smith.langchain.com/public/f93dd802-76c4-41c3-80af-16ce9d10a1a2/r)

![](HL_n1q7XIAAW9l4.jpg)
<span style="font-size:12px;color:rgb(153,153,153);">Loop Until Done：发现循环一直运行直到没有新结果出现</span>

---

<div style="background:#f5f0eb;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:16px;">
<div style="text-align:center;margin-bottom:8px;">
<strong style="font-size:15px;color:#8b6f4c;">结语</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
Dynamic Subagents 代表了一个微妙但重要的方向转变：从"让模型直接调用子 Agent"转向"让模型写代码来调用子 Agent"。前者把编排负担压在模型推理上（每轮推理就是一次编排决策），后者把编排固化到确定性代码中：循环就是循环，不会漏项；分支就是分支，不会走偏。这个思路与 Claude Code 的 Workflows 和 RLMs 的共识表明，**Agent 的未来可能不是更聪明的单模型，而是更聪明的编排层。**<br><br>
另外值得注意的一点是，上述六种模式都不是新发明的编排范式：它们是软件工程中已经存在几十年的并行处理模式（fork-join、pipeline、divide and conquer）在 Agent 时代的自然映射。Dynamic Subagents 的真正贡献不在于发明新模式，而在于让 Agent 能根据任务类型在运行时自主选择合适的模式。
</div>
</div>

---

<span style="font-size:12px;color:#888888;font-family:'Courier New',monospace;">参考：

https://x.com/sydneyrunkle/status/2071629451712983319</span>
