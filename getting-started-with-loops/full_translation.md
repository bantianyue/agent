# Getting Started with Loops — 完整翻译

**作者：** Delba de Oliveira & Michael Segner（Anthropic）
**原文：** https://claude.com/blog/getting-started-with-loops

---

## 定义

> "Loops 就是 Agent 重复执行工作循环，直到满足停止条件。"

Loops 根据循环如何被控制来分类：按轮次、按目标、按时间、或按主动组合。

---

## 1. 按轮次循环（Turn-based Loops）

- 每次提示都启动一个手动循环：Claude 收集上下文、执行行动、检查工作、如果需要就重复，然后才响应。
- **改进验证的方法：** 将手动检查编码到 `SKILL.md` 文件中，让 Claude 可以端到端自我验证。使用工具让 Claude **查看**、**测量**或**交互**以确认结果。
- **示例 SKILL.md 代码片段：**
  ```yaml
  ---
  name: verify-frontend-change
  description: Verify any UI change end-to-end before declaring it done.
  ---
  # Verifying frontend changes
  Never report a UI change as complete based on a successful edit alone.
  Verify it the way a human reviewer would:
  1. Start the dev server and open the edited page in the browser.
  2. Interact with the change directly. For a new control (button, input, toggle):
     click it, confirm the expected state change, and screenshot before/after.
  3. Check the browser console: zero new errors or warnings.
  4. Use the Chrome Devtools MCP, run a performance trace and audit Core Web Vitals.
  If any step fails, fix the issue and rerun from step 1.
  ```

## 2. 按目标循环（Goal-based Loops — `/goal`）

- 定义明确的成功标准。Claude 持续迭代直到目标达成或达到最大轮次。
- **确定性标准**（如测试通过数、评分阈值）效果最好。
- **示例：** `/goal get the homepage Lighthouse score to 90 or above, stop after 5 tries.`

## 3. 按时间循环（Time-based Loops — `/loop` & `/schedule`）

- 用于重复性工作：任务固定但输入变化（如每日 Slack 摘要）或周期性检查（如 PR 审查、CI 结果）。
- **`/loop`** 在本地机器上运行（关掉才停）。
- **`/schedule`** 将循环移到云端（持久运行）。
- **示例：** `/loop 5m check my PR, address review comments, and fix failing CI`

## 4. 主动循环（Proactive Loops）

- 按轮次、按目标、按时间三种基本模式的组合，再加上**自动模式**和**动态工作流**（研究预览），用于长时间运行的自主工作。
- **组合示例：**
  `/schedule every hour: check #project-feedback for bug reports. /goal: don't stop until every report found this run is triaged, actioned, and responded to. When fixing a bug, use a workflow to explore three solutions in parallel worktrees and have a judge adversarially review them.`

---

## 维护代码质量

- 循环的输出质量取决于**围绕它的系统**。
- 当结果不达标时，**将修复编码到系统中**，让未来的迭代受益。

---

## 管理 Token 用量

Loops 应该有清晰的边界：
- 设置最大轮次数。
- 定义明确的停止条件。
- 使用成本感知的提示词（如限制范围、避免不必要的上下文）。

---

## 入门指南 — 决策表

| 循环类型 | 你交出了什么 | 什么时候用 | 命令 |
|----------|-------------|-----------|------|
| **按轮次** | 检查本身 | 你在探索或做决策 | 自定义验证 skills |
| **按目标** | 停止条件 | 你知道"做完"是什么样的 | `/goal` |
| **按时间** | 触发器 | 工作按计划发生在项目之外 | `/loop`、`/schedule` |
| **主动** | 提示词本身 | 工作是重复且定义清晰的 | 以上全部 + 动态工作流 |

**如何开始：**
1. 看看你已经在做的工作。
2. 选一个你自己是瓶颈的任务。
3. 问问：你能写出验证检查吗？目标明确吗？工作是否有规律的到达时间？
4. 运行循环，观察它在哪卡住或过度执行，然后迭代改进。
