**要点速览**

<div style="background:#e8f4fd;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:18px;">
<div style="text-align:center;margin-bottom:10px;">
<strong style="font-size:16px;color:#1a6ba0;">要点速览</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
- <strong>Cortex 是什么</strong>：一个纯 Rust 编写的 MCP 服务器（3.8MB 二进制，零运行时依赖），100% 本地运行，给 AI Agent 提供真正的长期记忆<br><br>
- <strong>4 层记忆架构</strong>：Working → Episodic → Semantic → Procedural，模拟人类记忆的分层结构<br><br>
- <strong>性能碾压</strong>：156µs 写入、568µs 搜索（比 Mem0 快 528 倍），LoCoMo 基准 73.7% 超越 Mem0 的 68.4%<br><br>
- <strong>隐私优先</strong>：AES-256-GCM 加密同步到 iCloud/GDrive/OneDrive，零遥测，永远免费
</div>
</div>

---

**问题：AI Agent 的「记忆」现状**

每个 Claude Code 会话都是从空白开始的。你的 Agent 不记得你的名字、你的代码规范、你 20 分钟前做的决定。你只能一遍又一遍地重复解释同样的上下文。

目前的「记忆」方案无非是三种：

- **纯文本文件**——基于 grep，无结构，无衰减，无关系
- **云端 API（Mem0 等）**——每次查询 200-500ms 延迟，$99+ /月，数据在别人的服务器上
- **OpenAI Memory**——不透明，无法导出，无法控制

**没有一种方案能给你人类记忆真正在做的事：结构化召回、信念更新、关系追踪，以及忘记不再重要的事情。**

---

**Cortex 的不同之处**

Cortex 是一个纯 Rust 的 MCP 服务器（3.8MB 二进制，零运行时依赖），100% 在本地运行。**它的核心设计理念是：Agent 的记忆应该像人类记忆一样分层运作，而不是一个扁平的键值存储。**

- **4 层记忆架构**——Working → Episodic → Semantic → Procedural（像人类记忆一样分层）
- **贝叶斯信念系统**——随着新证据自我修正
- **人物关系图**——跨平台身份解析
- **亚毫秒级性能**——156µs 写入，568µs 搜索（比 Mem0 快 528 倍）
- **30 个 MCP 工具**——可接入 Claude Code、Claude Desktop 或任何 MCP 客户端
- **AES-256-GCM 加密同步**——通过你自己的云存储（iCloud/GDrive/OneDrive/Dropbox），带密钥轮换、HMAC 防篡改检测和逐条记忆隐私控制：默认所有记忆都是私有的、永不离开你的设备；标记一条记忆为「共享」即可同步，降级回私有后从其他设备删除
- **默认拒绝的工具授权**——Agent 在你授予读/写/同步权限之前，零记忆访问权
- **零遥测，零成本，永远免费**

---

**真实案例：Claude Code + Cortex**

作者用 Cortex 配合 Claude Code 开发自己的 X 项目。**从「每次都要重新解释一切」到「跨会话自动记住」，变化是颠覆性的。**

**使用 Cortex 之前：** 每个会话都要重新解释项目用 Gemini 作为 LLM 提供商、直接推 main 分支、提交前必须通过测试，以及几十个项目特定的细节。

**使用 Cortex 之后：** Claude Code 跨会话记住所有这些。它知道作者的代码风格偏好、最近在开发哪些模块、上周做了什么决定以及为什么。一个 SessionStart 钩子自动在每个新会话中注入记忆摘要——零手动操作——而 capture 协议在会话结束前将持久性事实写回。

**狗粮测试带来一个意外发现：** 对同步路径的黑盒测试发现了一个真实的隐私 bug——一个长时间运行的进程在另一台设备刚撤回一条记忆后，仍在提供该记忆的搜索结果（同步拉取后的缓存过期问题）。同一周，实现者编写的测试全部通过。教训：验收测试现在由上下文隔离的 Agent 编写，该 Agent 从未见过实现代码。

---

**基准测试结果**

团队在 LoCoMo 基准（ACL 2024）上进行了测试——1540 个 QA 对，覆盖长期对话：

| 系统 | 总体准确率 |
|------|-----------|
| **Cortex** | **73.7%** |
| Mem0-Graph | 68.4% |
| Mem0 | 66.9% |
| OpenAI Memory | 52.9% |

**Cortex 在完全本地运行、零 API 成本的情况下，比 Mem0 高出 7 个百分点。**

---

**如何试用**

```bash
# 安装（macOS/Linux）
curl -fsSL https://raw.githubusercontent.com/gambletan/cortex/main/install.sh | bash

# 或通过 npm
npx cortex-mcp

# 注册到 Claude Code
claude mcp add cortex-memory --scope user -- ~/.local/bin/cortex-mcp-server ~/.cortex/memory.db
```

或者运行一键脚本——它会安装二进制文件、加入加密云同步、设置自动召回钩子、注册 MCP 服务器：

```bash
git clone https://github.com/gambletan/cortex && cortex/scripts/setup-device-sync.sh
```

就是这样。**Claude Code 现在有了持久记忆——在你拥有的每台设备上。**

---

**开源，MIT 许可**

完整源码：https://github.com/gambletan/cortex

如果它有用，一个 star 能帮其他人找到它。**欢迎提问。**

---

<div style="background:#f5f0eb;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:16px;">
<div style="text-align:center;margin-bottom:8px;">
<strong style="font-size:15px;color:#8b6f4c;">结语</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
Cortex 的定位很聪明——它不做「AI 记忆平台」，而是做一个纯粹的 MCP 服务器。这意味着它不绑定任何特定模型或 Agent 框架，任何支持 MCP 协议的客户端都能用。这种架构选择让它在 Claude Code 生态里天然比 Mem0 这类 SaaS 方案更有吸引力。<br><br>
但真正值得关注的不是性能数字——73.7% vs 68.4% 的差距在实用中可能没那么显著——而是它的隐私模型。默认私有、逐条控制、端到端加密同步到用户自己的云存储，这个设计直接回应了企业用户对「AI 工具会偷走我的代码和数据」的核心焦虑。如果 Cortex 能把这个故事讲好，它有机会成为 Agent 记忆层的事实标准，就像 Git 成了代码版本控制的事实标准一样。
</div>
</div>

---

<span style="font-size:12px;color:#888888;">参考：How I Built Persistent Memory for Claude Code Agents (and Why Your AI Forgetting Everything Is a Solvable Problem)</span>
