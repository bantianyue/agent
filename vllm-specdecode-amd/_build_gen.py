#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 article_data_build.py（vLLM AMD 投机解码 · 重新生成）

输入：_translations.json（逐块译文）、_tables_zh.json（6 张表中译）
输出：article_data_build.py（DATA 字面量，供 write-article-data.py exec）
"""
import json, os, re, sys

d = os.path.dirname(os.path.abspath(__file__))
TR = json.load(open(os.path.join(d, "_translations.json"), encoding="utf-8"))
TAB = json.load(open(os.path.join(d, "_tables_zh.json"), encoding="utf-8"))


def T(i):
    """取第 i 块译文并做统一术语清洗"""
    s = TR[str(i)]
    s = s.replace("speculative decoding（投机解码）", "投机解码")
    s = s.replace("Speculative decoding（投机解码）", "投机解码")
    s = s.replace("speculative decoding", "投机解码")
    s = s.replace("Speculative decoding", "投机解码")
    s = s.replace("Figure 3", "图 3").replace("Figure 2", "图 2").replace("Figure 1", "图 1")
    # 原文图无图注，正文里的「图 N」引用改为「下图」，避免与统一编号冲突
    s = s.replace("（如图 1 所示）", "（见下图）")
    s = s.replace("图 1 所示", "下图所示")
    s = s.replace("图 2 给出了", "下图给出了")
    s = s.replace("图 2 给出", "下图给出")
    s = s.replace("图 3 以并排视图", "下图以并排视图")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def CODE(i, lang=""):
    raw = TR[str(i)]
    return "__CODE__" + (lang + "::" if lang else "") + raw


def tab(idx, fix=None):
    """表格（idx 从 0 起）；fix 为逐格修正函数"""
    rows = TAB[idx]
    if fix:
        rows = [[fix(c) for c in r] for r in rows]
    return {"head": rows[0], "rows": rows[1:]}


def tfix(c):
    c = c.replace("草稿组件", "draft 组件").replace("草稿网络", "draft 网络")
    c = c.replace("草稿 token", "draft token").replace("草稿模型", "draft 模型")
    c = c.replace("草稿检查点", "draft checkpoint").replace("草稿层", "draft 层")
    c = c.replace("独立草稿检查点", "独立 draft checkpoint")
    c = c.replace("非推测基线", "非投机基线").replace("推测基线", "投机基线")
    return c


def sec(kind, title, blocks, figs=None, table=None):
    """blocks: [(文本/CODE 值, 其后挂的图列表)]"""
    paras, fig_after = [], {}
    for pid, item in enumerate(blocks):
        text, fl = item if isinstance(item, tuple) else (item, [])
        paras.append(text)
        if fl:
            fig_after[str(pid)] = [dict(x) for x in fl]
    out = {"type": kind, "title": title, "paras": paras}
    if fig_after:
        out["fig_after"] = fig_after
    if table:
        out["table"] = table
    return out


# 原文三张 SVG 图与 25 张 DOM 示意图均无图注 -> 一律保留空槽，不补造
CAP1 = CAP2 = CAP3 = ""


def f(src, cap=""):
    return {"src": src, "caption": cap}


SECTIONS = [
    sec("h2", "引言", [T(3), T(4), T(5)]),
    sec("h2", "自回归解码基线",
        [(T(7), [f("fig01.png")]), T(8), T(9), T(10), T(11)]),
    sec("h2", "投机解码的核心思想",
        [T(13), T(14), T(15), T(16), T(17), T(18), T(19),
         (T(20), [f("fig02.png")]), (T(21), [f("fig03.png")]),
         (T(22), [f("fig04.png", CAP1)])]),
    sec("h3", "一个简单的接受/拒绝示例",
        [(T(25), [f("fig05.png", CAP2)]), (T(27), [f("fig06.png")]),
         (T(28), [f("fig07.png")]), (T(29), [f("fig08.png")]),
         T(30), (T(31), [f("fig09.png")])]),
    sec("h2", "五种起草方法如何工作",
        [T(33), T(34), T(35), T(36), T(37), T(38), T(39), T(40), T(41),
         T(42), T(43), T(44), T(45), T(46), T(47), T(48)]),
    sec("h3", "Native MTP",
        [(T(50), []), (T(51), [f("fig10.png")]), (T(54), [f("fig11.png")]),
         T(55), (T(56), [f("fig12.png")]), T(57)]),
    sec("h3", "Gemma 4 MTP",
        [(T(59), [f("fig13.png")]), T(60), (T(61), [f("fig14.png")])]),
    sec("h3", "EAGLE-3",
        [T(63), (T(64), [f("fig15.png")]), (T(65), [f("fig16.png")]),
         T(66), T(67), T(68), T(69), (T(70), [f("fig17.png")]), T(73)]),
    sec("h3", "DFlash",
        [T(75), T(76), T(77), (T(78), [f("fig18.png")]), T(79),
         (T(80), [f("fig19.png")]), (T(81), [f("fig20.png")]), T(82),
         (T(83), [f("fig21.png")]), T(84), T(85), T(87),
         (T(88), [f("fig22.png")]), T(89), (T(90), [f("fig23.png")]),
         (T(91), [f("fig24.png")]), T(92)]),
    sec("h3", "DSpark",
        [T(94), T(95), T(96), (T(97), [f("fig25.png")]), T(98), T(99),
         (T(100), [f("fig26.png")]), (T(101), [f("fig27.png")]),
         T(102), T(103), T(104)]),
    sec("h3", "五种方法对比",
        [(T(106), [f("fig28.png", CAP3)])], table=tab(0, tfix)),
    sec("h2", "在 vLLM 中启用投机解码",
        [T(109), T(110), CODE(111, "bash"), T(112), CODE(113, "bash"), T(114),
         T(115), T(116), T(117), T(118), T(119)], table=tab(1, tfix)),
    sec("h3", "显存考量", [T(121)]),
    sec("h2", "预训练 draft 模型去哪找", [T(123)], table=tab(2, tfix)),
    sec("h2", "实验设置与主要观测",
        [T(125), T(126), T(127), T(128), T(129), T(130)]),
    sec("h3", "模型与实验覆盖", [T(132), T(133)], table=tab(3, tfix)),
    sec("h3", "吞吐测量", [T(135)]),
    sec("h3", "主要观测",
        [T(137), T(138), T(139), T(140), T(141), T(142), T(143), T(144), T(145)]),
    sec("h2", "调参考虑", [T(147), T(148), T(149)]),
    sec("h3", "从受支持的配置入手",
        [T(151), CODE(152, "json"), T(153), T(154), T(155), T(156), T(157),
         CODE(158, "python"), T(159), CODE(160, "python"), T(161), T(162),
         CODE(163, "text"), T(164), T(165)]),
    sec("h3", "监控接受行为", [T(167), T(168), T(169)], table=tab(4, tfix)),
    sec("h3", "让扫描匹配工作负载", [T(171), T(172), T(173)]),
    sec("h3", "调参工作流示例", [T(175), T(177), T(179), T(181), T(183), T(185)]),
    sec("h2", "为新 target 模型训练 speculator",
        [T(187), T(188), T(189), T(190), T(191), T(192), T(193), T(194)]),
    sec("h3", "准备有代表性的 prompt", [T(196), T(197)]),
    sec("h3", "如何获取 hidden states", [T(199), T(200)], table=tab(5, tfix)),
    sec("h3", "收集 target 模型信息", [T(202), T(203), T(204), T(205), T(206), T(207)]),
    sec("h3", "训练与测试 speculator", [T(209), T(210), T(211)]),
    sec("h2", "总结", [T(213), T(214), T(215), T(216), T(217)]),
    sec("h2", "未来工作", [T(219), T(220), T(221), T(222)]),
    sec("h2", "实验环境与配置",
        [T(414), T(416), T(417), T(419), T(420)]),
]

DATA = {
    "title": "在 AMD GPU 上探索 vLLM 的投机解码（Speculative Decoding）",
    "summary": [
        {"key": "核心机制",
         "body": "保留原模型作 target，前面加更快的 draft 阶段提出候选 token，由 target 在一次前向里验证；接受判定从左到右，遇到第一个被拒 token 即停止。"},
        {"key": "五种方法",
         "body": "按「用哪些 target 信息 + 串行还是并行起草」分为三类：native MTP、独立 MTP drafter（Gemma 4 MTP）、专用 target-conditioned 网络（EAGLE-3 自回归、DFlash 并行块、DSpark 并行加轻量顺序修正）。"},
        {"key": "实测与调参",
         "body": "AMD MI300X/MI355X + ROCm 上吞吐比随模型、方法、负载差异很大：gemma-4-26B-A4B 的 DFlash 最高 2.87×，也有配置低于基线；num_speculative_tokens 必须按负载扫描（常见峰值 N=4 到 7）。"},
    ],
    "lead": [
        "投机解码（speculative decoding）让 vLLM 在单次 target model 前向中验证多个 draft token。实验中，它对输出 token 吞吐的影响随 drafting 方法和 proposal 长度而变化，同时也取决于模型系列、draft checkpoint、workload 与接受行为。",
    ],
    "sections": SECTIONS,
    "conclusion": [
        "**① 加速来自一次 target 前向提交多个 token，而不是放宽判定标准。** 原模型始终是 target，draft 只提候选，验证从左到右进行，遇到第一个被拒 token 就停止并丢弃后续候选，输出行为与不投机时一致。",
        "**② 五种方法的分野在两点：draft 拿到哪些 target 信息，以及候选是串行还是并行起草。** native MTP 内建在模型里、Gemma 4 MTP 独立打包但共享 target 的 KV cache、EAGLE-3 融合三层 hidden states 自回归起草，DFlash 用 anchor 加 mask 一次并行预测整块，DSpark 再补一个轻量 Markov 头补回位置间的依赖。",
        "**③ 部署上没有万能配置，调参要看接受行为。** 实测吞吐比从低于基线到 2.87× 都有，同一系列的不同模型（Qwen3.6-27B 与 35B-A3B）最优 N 都不一样；先跑通 checkpoint 支持的配置，再用逐位置接受率把 N 收到峰值，通常落在 4 到 7。",
        "投机解码本质是用额外显存和 draft 计算，换每次 target 前向的产出 token 数。在 AMD Instinct + ROCm 上它已经跑通，真正决定收益的是把 N 和 draft checkpoint 压到目标工作负载的接受模式上，而不是照抄一个推荐值。",
    ],
    "reference_url": "https://vllm.ai/blog/2026-08-23-speculative-decoding-amd-gpus",
}

body = json.dumps(DATA, ensure_ascii=False, indent=2)
src = (
    "#!/usr/bin/env python3\n# -*- coding: utf-8 -*-\n"
    '"""由 _build_gen.py 生成的 article_data_build.py（勿手改）"""\n'
    "import json, os, sys\n\n"
    "_article_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()\n\n"
    "DATA = " + body + "\n\n"
    'out_path = os.path.join(_article_dir, "article_data.json")\n'
    'with open(out_path, "w", encoding="utf-8") as f:\n'
    "    json.dump(DATA, f, ensure_ascii=False, indent=2)\n"
    "print(f\"✅ 写入 {out_path} ({len(json.dumps(DATA, ensure_ascii=False))} chars, "
    "{len(DATA.get('sections', []))} sections)\")\n"
)
open(os.path.join(d, "article_data_build.py"), "w", encoding="utf-8").write(src)

nparas = sum(len(s["paras"]) for s in SECTIONS)
nfigs = sum(len(v) for s in SECTIONS for v in s.get("fig_after", {}).values())
print(f"sections={len(SECTIONS)} paras={nparas} figs={nfigs} "
      f"tables={sum(1 for s in SECTIONS if 'table' in s)}")
