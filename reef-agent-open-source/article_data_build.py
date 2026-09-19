# -*- coding: utf-8 -*-
"""Reef 开源 X Article —— 按源 DOM 顺序重排图位（fig01..fig08），GIF 保动画。"""
import json, os, sys

_article_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
tr = json.load(open(os.path.join(_article_dir, "_trans.json"), encoding="utf-8"))
codes = json.load(open(os.path.join(_article_dir, "_codes.json"), encoding="utf-8"))
T = {int(k): v for k, v in tr.items()}


def C(block_idx):
    m = [c for c in codes if c["block"] == block_idx][0]
    return (f"__CODE__{m['lang']}::" if m["lang"] else "__CODE__") + m["code"]


DATA = {
    "title": "Reef 开源：把推理服务器变成持续自我改进的 Agent（有状态推理基础设施）",
    "summary": [
        {"key": "动机", "body": "在 RSI 热潮真正兑现之前开源 Reef，为 Agent 的持续自我改进提供生产级基础设施。"},
        {"key": "核心", "body": "持续自我改进的基础设施要端到端掌控三件事：经验、整个 Agent、更新；Reef 用有状态推理把三者打通。"},
        {"key": "方法", "body": "不同学习方法沿学习信号、经验获取、演化目标三个维度展开，都能作为 learning recipe 跑在同一套基础设施上。"},
    ],
    "lead": [
        "推理服务器不必只做推理。**Reef** 把模型与 harness 的演化接进线上服务：调用与反馈沉淀为结构化经验，学习配方据此产出新版本，再热更新回正在服务的实例。",
    ],
    "sections": [
        {
            "type": "h2",
            "title": "开源 Reef：让 Agent 从自身经验里持续进化",
            "paras": [
                "在围绕 RSI 的热潮完全兑现之前，我们先把 Reef 开源。它面向一个更宽泛的问题：让 Agent（模型 + harness）能够从自身经验中持续进化。",
                "目标是让开源社区更容易试验持续自我改进，并直接拿到生产级的基础设施。这里把持续自我改进当作更宽泛、更实用的框架，RSI 则是同一理念中更完全递归的那一种形式。",
            ],
        },
        {
            "type": "h2",
            "title": "为什么持续自我改进需要新基础设施",
            "paras": [
                T[4],
                T[5],
                T[6],
                T[7],
                T[8],
            ],
            "fig_after": {
                "0": [{"src": "fig01.gif",
                       "caption": "图1：从训练、评估、部署、推理的顺序流水线，走向持续演进的循环"}],
                "4": [{"src": "fig02.gif",
                       "caption": "图2：线上服务与反馈回流构成的经验闭环"}],
            },
        },
        {
            "type": "h2",
            "title": "持续自我改进的基础设施要掌控三件事",
            "paras": [
                T[10],
            ],
            "fig_after": {
                "0": [{"src": "fig03.jpg", "caption": "图3：Reef 架构"}],
            },
        },
        {
            "type": "h3",
            "title": "掌控经验：学习必须建立在实时服务之上",
            "paras": [
                T[12],
                T[13],
                C(17),
                T[14],
                C(19),
                T[15],
            ],
        },
        {
            "type": "h3",
            "title": "掌控整个 Agent：模型与 harness 都要演化",
            "paras": [
                T[17],
                T[18],
                T[19],
                C(25),
                T[20],
                T[21],
                T[22],
            ],
            "fig_after": {
                "4": [{"src": "fig04.jpg",
                       "caption": "图4：harness 按演化配方更新后，用户再次打开时看到的新版本"}],
            },
        },
        {
            "type": "h3",
            "title": "掌控更新：演化后的发布要经过评估与版本管理",
            "paras": [
                T[24],
                "Reef 可演进的任何内容，比如模型检查点、LoRA 适配器、harness 树或路由策略，都表示为受版本控制器管理的工件。Reef 采用 Git LFS 管理这些工件，尤其是模型权重这类占用大量磁盘空间的工件。发布路径如下：",
                T[26],
            ],
            "fig_after": {
                "1": [{"src": "fig05.jpg",
                       "caption": "图5：每个场景一条只追加的发布链，发布头用 compare-and-swap 推进"}],
            },
        },
        {
            "type": "h2",
            "title": "Reef 中的持续自我改进方法",
            "paras": [
                T[28],
                T[29],
                T[30],
                "· " + T[31],
                "· " + T[32],
                "· " + T[33],
            ],
            "fig_after": {
                "5": [{"src": "fig06.jpg",
                       "caption": "图6：Reef 已支持或即将支持的 learning recipe"}],
            },
        },
        {
            "type": "h3",
            "title": "用 learning recipe 表达不同方法",
            "paras": [
                T[34],
                "**在 serve.yaml 里插入一个演化配方：**",
                C(44),
                T[35],
                C(46),
            ],
        },
        {
            "type": "h3",
            "title": "两条路线截然不同的示例",
            "paras": [
                T[36],
                "两个示例对应两条完全不同的演化路线：一个在真实交互中持续更新模型，另一个在求解过程里反复搜索并保留更优解。",
            ],
            "fig_after": {
                "0": [{"src": "fig07.gif",
                       "caption": "图7：OpenClaw-RL 在 Reef 中的集成演示。用户与一个模型被 Reef 异步持续演化的 Agent 交互，整个过程不打断用户；随着轮次累积，Agent 逐渐学会正确理解用户偏好，并给出令人满意的回答。"}],
                "1": [{"src": "fig08.gif",
                       "caption": "图8：TTT 对 Packing 32 问题的迭代改进演示。随着优化推进，越来越有效的解被发现并保留下来，装箱分数逐步提高。"}],
            },
        },
        {
            "type": "h2",
            "title": "结论",
            "paras": [
                T[38],
                T[39],
                "我们采用持续自我改进（continual self-improvement）作为比 RSI 更宽泛且更实用的框架。它涵盖那些无需 RSI 通常所需的完全闭环即可从经验中反复改进的系统：在 RSI 里，AI 自身参与构建和改进生成其下一版本的系统。Reef 正是针对这一更宽泛的问题而设计，同时为更递归形式的自我改进在其之上涌现留出空间。",
            ],
        },
    ],
    "conclusion": [
        "Reef 把推理服务器从流水线末端改造成一个有状态的学习者：一边服务真实流量，一边把调用与反馈沉淀成可训练的经验。",
        "① 推理必须是原生的：学习建立在实时服务之上，轨迹、反馈、陈旧性与去重由基础设施统一处理。",
        "② 演化对象不止权重：模型与 harness 在同一场景里联合版本化，谁被评估认可就让谁上线。",
        "③ 发布必须可控：候选先过评估，发布链只追加，服务不重启即可完成权重热切换。",
        "落到自己动手这一侧：先把服务、记录、学习、发布这四步的边界划清楚，再挑算法和配方，会比一上来就纠结训练细节省事得多。",
    ],
    "reference_url": "https://x.com/ao_qu18465/status/2094867930081337730",
}

out_path = os.path.join(_article_dir, "article_data.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)

n_paras = sum(len(s["paras"]) for s in DATA["sections"])
n_figs = sum(len(v) for s in DATA["sections"] for v in (s.get("fig_after") or {}).values())
bad = [(s["title"], k, len(s["paras"])) for s in DATA["sections"]
       for k in (s.get("fig_after") or {}) if int(k) >= len(s["paras"])]
print(f"OK {len(DATA['sections'])} sections, {n_paras} paras, {n_figs} figs")
if bad:
    raise SystemExit(f"fig_after 越界: {bad}")
