#!/usr/bin/env python3
"""
article_data_build.py — agentOS: WebAssembly 沙箱，让 Agent 运行成本从 1GiB 降到 22MB
X 推文 — 非论文类，≥80% 保留率。遵守图文原则、简洁原则、结论首句原则。
"""
import json, os, sys

_article_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()

DATA = {
    "title": "agentOS：用 WebAssembly 重写 Agent 沙箱，内存占用从 1GiB 降到 22MB，历史正在重演",

    "summary": [
        {"key": "核心观点", "body": "Agent 沙箱正在重演 2010 年代的 Serverless 战争——容器级隔离太浪费，V8 Isolate 才是正确方向"},
        {"key": "关键数据", "body": "agentOS 跑一个简单 shell 任务仅需 22MB 内存，而传统沙箱不管 Agent 是否活跃都预留 1GiB"},
        {"key": "产品形态", "body": "以库的形式嵌入现有后端，支持 bash/git/duckdb/Node.js/Python 等原生软件，必要时可升级到重 VM"},
    ],

    "lead": [
        "2010 年代的 Serverless 战争以 Cloudflare Workers 的 V8 Isolate 架构证明：为每个请求预留一个完整虚拟机是巨大的浪费。现在，同样的故事在 Agent 沙箱领域重演。",
        "Nathan Flurry 在推文中介绍了 agentOS——一个基于 WebAssembly 和 V8 Isolate 的开源 Agent 运行时，将 Agent 的内存占用从传统沙箱的 1GiB 降到 22MB，同时保持 Linux 兼容性，支持 bash、git、duckdb、Node.js、Python 等原生软件。",
    ],

    "sections": [
        {
            "type": "h2",
            "title": "Serverless 战争的历史重演",
            "paras": [
                "2010 年代的 Serverless 战争在两个阵营之间展开：AWS Lambda 使用 microVM 为每个请求隔离计算资源，Cloudflare Workers 使用 V8 Isolate 在共享进程中运行轻量级沙箱。",
                "AWS Lambda 优化了错误的方向：后端大部分时间在等待数据库和 API 调用，处于空闲状态，但 Lambda 一次只服务一个请求，预留了大量未使用的内存和 CPU。一个空闲的 microVM 在等待数据库时完全闲置。",
                "Workers 的做法是改变空闲成本的含义：一个空闲的 Isolate 只是共享进程中的几 MB 堆内存，而不是为每个请求预留一个 VM。它不使用的 CPU 可以分配给同一进程中的其他 Isolate。一台机器可以承载数千个 Isolate 处理请求，而不是几十个 microVM。",
            ],
            "figs": [
                {"src": "fig00.jpg", "caption": "Sandboxes vs WebAssembly 对比图。容器 vs V8 Isolate 的架构差异，与当年 Lambda vs Workers 的对比如出一辙。"},
            ],
        },
        {
            "type": "h2",
            "title": "Agent 沙箱正在重复同样的错误",
            "paras": [
                "Agent 和沙箱的行为与传统后端惊人地相似：它们大部分时间在等待推理、用户输入或执行简单的文件操作/脚本——就像后端等待数据库/API 请求一样空闲。",
                "然而，当前主流的 Agent 沙箱方案（Modal、Daytona、Vercel sandboxes）都采用容器-per-Agent 架构，每个 Agent 独立占用一个完整的 Linux 容器，与 AWS Lambda 的 microVM 架构如出一辙。不管 Agent 是在活跃工作还是等待推理，这 1GiB 内存都被预留。",
            ],
        },
        {
            "type": "h2",
            "title": "agentOS：V8 Isolate 版 Agent 沙箱",
            "paras": [
                "agentOS 构建了一个开源的 Cloudflare Workers 式架构，使用 WebAssembly 和 V8 Isolate 提供 Linux 兼容的操作系统。核心思路是：不预留整个容器给每个 Agent，只在 Agent 本身活跃时才消耗资源。",
                "效果显著：一个简单的 shell 工作负载在 agentOS 中只需约 22MB 内存，而传统沙箱无论 Agent 是否活跃都预留 1GiB。差距超过 45 倍。",
            ],
            "figs": [
                {"src": "fig01.jpg", "caption": "agentOS 架构示意。WebAssembly + V8 Isolate 实现轻量级 Agent 运行时。"},
            ],
        },
        {
            "type": "h2",
            "title": "WebAssembly 中的 Linux 兼容 OS",
            "paras": [
                "agentOS 的关键创新是将原生 Linux 软件编译到 WebAssembly。如果软件能在沙箱中运行，大概率也能在 agentOS 中运行。",
                "agentOS 支持原生 bash、git、duckdb、sqlite 等，全部交叉编译到 WASM。其内核支持 POSIX 兼容的文件系统、进程树和套接字。可以在上面运行开发服务器、数据分析、Node.js（完整 JIT）、Python 等各种任务。",
                "实际上，很少有生产级 Agent 需要真正的 x86 或内存密集型工作负载。ChatGPT Work 和 Claude 做的大部分工作只是电子表格、数据处理和 API 调用——这些对 WebAssembly 和 V8 来说轻而易举。",
            ],
        },
        {
            "type": "h2",
            "title": "OS 即库，而非额外基础设施",
            "paras": [
                "通过利用 WebAssembly，agentOS 可以作为库嵌入现有后端（就像使用 Vercel 的 AI SDK 一样），大幅简化基础设施并降低成本。",
                "作为库运行的 agentOS 还提供了更精细的权限控制、出站中间件和 Agent 行为限制。你可以直接在 agentOS 中运行原生 Claude Code、Codex、OpenCode 和 Pi，或使用自己的 Harness。",
            ],
            "figs": [
                {"src": "fig02.jpg", "caption": "agentOS 与传统沙箱的架构对比。作为库嵌入 vs 独立基础设施。"},
            ],
        },
        {
            "type": "h2",
            "title": "安全性保障",
            "paras": [
                "agentOS 建立在与 Chrome 和 Cloudflare Workers 相同的隔离机制之上，包括 V8 隔离、Spectre 缓解、进程隔离和资源限制。安全性方面与经过大规模验证的生产级方案一致。",
            ],
        },
        {
            "type": "h2",
            "title": "混合架构：轻量默认 + 按需升级",
            "paras": [
                "agentOS 并非完全取代传统沙箱。对于编译 Rust 或使用旧版软件等重型开发工作，传统 x86 Linux 沙箱仍然是必要的。",
                "agentOS 提供了沙箱挂载（Sandbox Mounting）机制：当检测到需要重型工作负载时，Agent 可以按需升级到完整的 Linux VM。实际上，这意味着默认使用轻量级 WebAssembly OS 处理大多数廉价任务，仅在需要时升级到沙箱，无需妥协。",
            ],
            "figs": [
                {"src": "fig03.jpg", "caption": "agentOS 的混合架构。默认轻量 WASM，按需升级到重 VM。"},
            ],
        },
    ],

    "conclusion": [
        "核心贡献是：用 WebAssembly + V8 Isolate 重新定义了 Agent 沙箱的架构，将资源消耗降低两个数量级，同时保持 Linux 兼容性。",
        "agentOS 的洞察很简单：Agent 大部分时间在等待，不应该为等待时间付费。容器-per-Agent 架构是 2010 年代 Lambda 式思维的延续，而 V8 Isolate 方案已经被 Cloudflare Workers 证明是更高效的选择。",
        "对于构建 Agent 应用的团队来说，agentOS 提供了一个开源、轻量、兼容的替代方案。已有多家公司和创业团队在生产环境中用 agentOS 替换传统沙箱，用于 AI 生成应用、个人助手和 RL 环境。",
    ],
    "reference_url": "https://x.com/NathanFlurry/status/2081498476970725735",
}

# ========== 写入逻辑 ==========
os.makedirs(_article_dir, exist_ok=True)
out = os.path.join(_article_dir, "article_data.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)
print(f"✅ 写入 {out} ({len(json.dumps(DATA, ensure_ascii=False))} chars, {len(DATA['sections'])} sections)")