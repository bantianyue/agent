#!/usr/bin/env python3
"""
article_data_build.py — We rewrote our agent to run entirely in a Durable Object with Pi, Agents SDK and Code Mode
==============================================================================================================
X article by Miguel Salinas (@Vercantez) — camelAI founder on migrating agent to Cloudflare Durable Objects
"""
import json, os, sys
_article_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()

DATA = {
    "title": "我们将 Agent 从虚拟机迁移到 Cloudflare Durable Object——Pi + Agents SDK + Code Mode 的实战",
    "summary": [
        {"key": "架构迁移", "body": "camelAI 将 agent 从虚拟机搬到 Cloudflare Durable Object——文件系统在 SQLite+R2，代码用 JavaScript 而非 Python"},
        {"key": "成本革命", "body": "Durable Object 休眠时零计算成本。1 万个 agent 各 1% 活跃时间 → 只需 ~100 个并发实例，而非 1 万台始终在线 VM"},
        {"key": "执行阶梯", "body": "文件系统(SQLite)→沙箱 JS(isolate)→npm→无头浏览器→完整沙箱。每级可加，最低 0 级即可工作"},
    ],
    "lead": [
        "camelAI 最近将其 agent 从虚拟机迁移到了 Cloudflare Durable Object。**Agent 现在运行在一个 Durable Object 内，文件系统活在 SQLite 和 R2 中，用 JavaScript 而非 Python 编写代码。** 这不是概念验证——这是他们在生产环境运行了数周的真实架构。支撑这一迁移的是 Cloudflare 新发布的 **Project Think**（Agents SDK + @cloudflare/codemode + Pi 集成）：Durable Objects 提供每个 agent 独立持久化存储和零成本休眠，Codemode 让 LLM 编写完整的 JavaScript 程序而非顺序调用工具，Pi 提供最小化 agent 框架。",
    ],
    "sections": [
        {
            "type": "h2",
            "title": "为什么从虚拟机迁移？Agent 的规模经济完全不同",
            "paras": [
                "传统应用是一个实例服务多个用户。餐厅有一份菜单和一个优化为大批量出餐的厨房。**一个 agent 更像一个私人厨师：不同的食材、不同的技法、不同的工具，每次都不一样。** 如果一亿知识工作者每人使用一个 agentic 助手，即使只是在中等并发下，你也需要数千万个同时活跃的会话——按当前每容器成本计算不可持续。",
                "VMs/容器在空闲时仍然消耗全额计算成本，每个实例始终在线。Durable Object 将开销从「始终在线」变为「按需唤醒」。一个休眠的 DO 不消耗计算资源。当请求、WebSocket、定时器或邮件到达时，平台唤醒 agent，加载状态，处理事件，然后继续休眠。**1 万个 agent 各活跃 1% 的时间 → 任何时候只有 ~100 个实例在线，而非 1 万个。**",
            ],
        },
        {
            "type": "h2",
            "title": "Durable Execution：让 Agent 不会因崩溃丢失工作",
            "paras": [
                "LLM 调用需要 30 秒，多轮 agent 循环运行更久。在这段时间内执行环境随时可能消失——部署、重启、资源限制。上游到模型提供商的连接被永久切断，内存中的状态丢失，连接的客户端看到流中断。",
                "**runFiber() 解决了这个问题。** 一个光纤（fiber）是一个持久的函数调用：执行开始前注册在 SQLite 中，可在任意点通过 stash() 做检查点，在重启时通过 onFiberRecovered 恢复。如果 agent 在循环到第 5 步时崩溃，恢复后从第 5 步继续——stash 的数据（findings、step、topic）完好无损。SDK 在 fiber 执行期间自动保持 agent 活跃。",
            ],
        },
        {
            "type": "h2",
            "title": "Cod emode：从工具调用到代码执行",
            "paras": [
                "传统的工具调用有一个尴尬的形状。模型调用一个工具，把结果拉回上下文窗口，再调用另一个工具，拉回结果——如此反复。100 个文件意味着 100 次通过模型的往返。**模型更擅长编写代码来使用系统，而非玩工具调用的游戏。**",
                "@cloudflare/codemode 实现了这一洞察：LLM 编写一个完整的程序来处理整个任务，而非序列化的工具调用。例如，查找所有包含 TODO 的 TypeScript 文件：执行一次 JS 程序（`tools.find` → `for` 循环 → `tools.read` → 检查），而不是 100 次 LLM 往返。Cloudflare API MCP 服务器只暴露两个工具（search 和 execute），消耗 ~1,000 tokens，而等价的逐工具端点方式消耗约 117 万 tokens——**减少了 99.9%**。",
            ],
        },
        {
            "type": "h2",
            "title": "安全沙箱：Dynamic Worker 作为计算基础",
            "paras": [
                "一旦接受模型应该代表用户编写代码，问题就变成：代码在哪里运行？Dynamic Worker 就是答案——毫秒级启动的 V8 isolate，几 MB 内存。比容器快约 100 倍、内存高效约 100 倍。**关键设计选择是能力模型：** 从几乎没有默认权限（`globalOutbound: null`，无网络访问）开始，显式授予每种资源。不再问「如何阻止这东西做太多？」而是「我们确切希望它能做什么？」",
            ],
        },
        {
            "type": "h2",
            "title": "执行阶梯：五级计算环境",
            "paras": [
                "这引出了一个自然的计算能力谱系，agent 按需升级：**0 级**：Workspace——基于 SQLite+R2 的持久虚拟文件系统，支持读/写/编辑/搜索/grep/diff。**1 级**：Dynamic Worker——LLM 生成的 JS 在沙箱化 isolate 中运行，无网络访问。**2 级**：添加 npm——从 registry 获取包、用 esbuild 打包、加载到 Dynamic Worker。**3 级**：通过 Cloudflare Browser Run 使用无头浏览器。**4 级**：完整 Cloudflare Sandbox——配置工具链、repo 和依赖。",
                "**关键设计原则：agent 在 0 级单独就可工作，每级都是累加的。** 用户可以根据需要添加能力。Pi Agents SDK 提供了会话 API（父子 ID 树形存储对话，支持分叉和压缩）和 Facet 子 agent（每个有独立 SQLite + 执行上下文，通过 RPC 协作）。",
            ],
        },
        {
            "type": "h2",
            "title": "对 Agent 工程的意义",
            "paras": [
                "**Agent 的规模经济与 Web 应用完全不同。** Web 应用是一个后端服务成千上万的用户。Agent 是每个用户/每个任务/每个线程一个 agent——这是 1:1 的模型。Durable Objects 的按需唤醒使这种模型在经济上可行。",
                "从工具调用到代码执行的范式转变同样重要。Codemode 不仅减少了 token 消耗，还改变了 agent 与系统的交互方式——不是通过 API 端点的胶水代码，而是通过真实的编程。这可能会推动 agent 框架从「工具路由」向「代码生成」进化。",
                "**对于 building 者：** 如果你正在为 agent 设计后端，问自己这个关键问题——是让你的 agent 在你的系统上运行，还是让你的 agent 成为你的系统？Durable Objects 的 actor 模型让前者自然过渡到后者。",
            ],
        },
    ],
    "conclusion": [
        "这篇 X 长文和配套的 Cloudflare Project Think 博客共同描绘了一个清晰的趋势：**Agent 基础设施正在从『进程内工具调用』转向『持久化代码执行』。** 这不是增量改进，是对 agent 架构模型的重塑——从 stateless API calls 到 stateful actor model，从顺序工具调用到批处理代码生成，从始终在线 VM 到按需唤醒 DO。",
        "**最有价值的洞察是『执行阶梯』：agent 在 Tier 0 就应该有用。** 这意味着基础设施不应该为了高级功能强迫你在第一时间就处理所有复杂性。Workspace (SQLite+R2 文件系统) + Codemode (JS 执行) 这两层就能覆盖大量 agent 用例，npm 和无头浏览器是累加加成。",
        "**独立观点：** Codemode 的 99.9% token 减少不是噱头——它从根本上改变了工具设计的 ROI。当每个工具的成本从「一个 LLM 往返」降到「函数调用」，你可以暴露更大、更复杂的工具。这可能导致 agent 工具设计的分叉：一方继续做细粒度 MCP 工具的标准化，另一方转向粗粒度『语言级 API』的代码生成。Cloudflare+Codemode 站在后者一边。",
    ],
    "reference_url": "https://x.com/Vercantez/status/2082138839888589200",
    "figs": [
        {"src": "fig01.jpg", "caption": "We rewrote our agent to run entirely in a Durable Object——camelAI 的实战架构迁移"},
    ],
}

out_path = os.path.join(_article_dir, "article_data.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)
print(f"✅ 写入: {len(DATA['sections'])} sections, {sum(len(s.get('paras',[])) for s in DATA['sections'])} paras")