#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gpu kernel porting with agents（X Article）中文编译版 build。

结构真相源：渲染 DOM 文档流（_blocks.txt，含 h1 分节 / pre 代码块 / table 单元格）。
代码块逐字取自 _code1..4.txt（原文 <pre> 内容），表格单元格取自 _tables.json（原文表格）。
图位与原文一一对应：引言末尾 fig01、Sage Attention 3 段2 fig02、段6 fig03、测试节 fig04。
"""
import io
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def _read(name):
    return io.open(os.path.join(HERE, name), encoding="utf-8").read()


CODE_BASH_TREE_CPP = _read("_code1.txt")      # sageattention3_blackwell 目录树
CODE_BASH_TREE_DSL = _read("_code2.txt")      # sage3_sm120 目录树
CODE_JSON_ASM = _read("_code3.txt")           # asm_info.json
CODE_TEXT_DELTAS = _read("_code4.txt")        # 相对 C++ 实现的有意偏离

SRC_TABLES = json.load(io.open(os.path.join(HERE, "_tables.json"), encoding="utf-8"))

CODE = ('<code style="background:#f3f4f5;padding:2px 5px;border-radius:3px;'
        'color:#0F4C81;">{}</code>')
DOT = ('<span style="color:#0F4C81;font-size:7px;line-height:1;'
       'vertical-align:middle;">●</span>&nbsp;')


def c(x):
    return CODE.format(x)


def bullet(text):
    return DOT + text


# ── 表格（逐单元格对照原文翻译，键=原文英文单元格）────────────────────────
T1_HEAD = {"folder": "目录", "what it is": "是什么", "authoritative for": "权威依据",
           "read for": "用来看什么", "size": "体积"}
T1 = {
    "cutlass/ (v4.8.0, include/cutlass/version.h)":
        "cutlass/（v4.8.0，include/cutlass/version.h）",
    "NVIDIA CUTLASS, whole checkout. Only examples/python/CuTeDSL/ and python/CuTeDSL/ "
    "matter: the first is the example corpus a port starts from, the second is the DSL's own "
    "source, which is worth more than the examples — signatures, LaunchConfig fields and "
    "env-var handling are all readable there, and guessing at them costs a GPU run each.":
        "NVIDIA CUTLASS 的完整检出。真正有用的只有 examples/python/CuTeDSL/ 和 "
        "python/CuTeDSL/：前者是移植起步时的示例集，后者是 DSL 自身源码，价值高于示例，"
        "签名、LaunchConfig 字段和环境变量处理都能直接读到，靠猜的话每猜错一次都要多花"
        "一轮 GPU 运行。",
    "the CuTe DSL API surface at 4.8, the Blackwell example kernels "
    "(dense/blockscaled/grouped GEMM, attention), the cute_ext pipeline + epilogue helpers, "
    "blockscaled_layout.BlockScaledBasicChunk (the ue8m0 / nvfp4 scale atom), and "
    "utils/blackwell_helpers.py":
        "4.8 版本的 CuTe DSL API 面、Blackwell 示例 kernel（dense/blockscaled/grouped "
        "GEMM、attention）、cute_ext 的 pipeline 与 epilogue 辅助、"
        "blockscaled_layout.BlockScaledBasicChunk（ue8m0 / nvfp4 缩放单元），以及 "
        "utils/blackwell_helpers.py",
    "sage_sm120 and any future CuTeDSL kernel": "sage_sm120 以及未来任何一个 CuTeDSL kernel",
    "265 MB. examples/python/CuTeDSL/ is ~4 MB and python/CuTeDSL/cutlass/ ~10 MB; "
    "include/, test/ and tools/ are the rest and are C++ that informs nothing here.":
        "265 MB。examples/python/CuTeDSL/ 约 4 MB，python/CuTeDSL/cutlass/ 约 10 MB；"
        "剩下的是 include/、test/ 和 tools/，都是 C++，在这里提供不了任何有用信息。",
    "SageAttention/ (main, shallow)": "SageAttention/（main 分支，浅克隆）",
    "thu-ml's official SageAttention / SageAttention2++ / SageAttention3 — quantized "
    "attention as hand-written CUDA (mma.sync + cp.async + swizzled smem), plus Triton "
    "fallbacks and the fused quantizers.":
        "thu-ml 官方的 SageAttention / SageAttention2++ / SageAttention3，量化 attention "
        "的手写 CUDA 实现（mma.sync + cp.async + swizzled smem），另有 Triton 回退版本和"
        "融合量化器。",
    "the SageAttention3 arithmetic and CuTe layout abstractions":
        "SageAttention3 的算术逻辑与 CuTe layout 抽象",
    "sage3_sm120 and any quantized fp4/fp8/int8 attention work":
        "sage3_sm120，以及任何 fp4/fp8/int8 量化 attention 相关工作",
    "106 MB checkout; 388 KB of csrc/ is the whole kernel. assets/ is 42 MB and example/ "
    "12 MB — both are noise.":
        "检出 106 MB；csrc/ 里 388 KB 就是整个 kernel。assets/ 有 42 MB、example/ 有 "
        "12 MB，都是噪音。",
}
T2_HEAD = {"change": "改动", "spill": "溢出寄存器数", "ld.shared": "ld.shared 指令数"}
T2 = {
    "baseline (12 warps, setmaxnreg)": "基线（12 warps，setmaxnreg）",
    "drop tOrO_tmp, rescale O in place": "去掉 tOrO_tmp，就地重算 O",
    "autovec_copy for the SF copies": "SF 拷贝改用 autovec_copy",
    "12 → 10 warps, setmaxnreg removed": "12 → 10 warps，去掉 setmaxnreg",
    "min_blocks_per_mp=1": "min_blocks_per_mp=1",
    ".align(16) on the delta_s loads": "在 delta_s 的读取上加 .align(16)",
    "rcp.approx + mask only the peeled block": "rcp.approx，并且只对剥出的 block 做 mask",
    "quantize interleaved under the PV MMA": "把量化交织到 PV MMA 之下",
    "12 warps + setmaxnreg 24/232": "12 warps + setmaxnreg 24/232",
    "—": "无",
    "456": "456", "304": "304", "296": "296", "272": "272", "104": "104",
    "280": "280", "0": "0",
    "194 scalar": "194（scalar）", "194": "194", "98": "98",
    "50 (48 v4)": "50（48 v4）", "50": "50",
}


def build_table(src, head_map, cell_map):
    head = [head_map[h] for h in src["head"]]
    rows = [[cell_map[c2] for c2 in row] for row in src["rows"]]
    return {"head": head, "rows": rows}


TAB1 = build_table(SRC_TABLES[0], T1_HEAD, T1)
TAB2 = build_table(SRC_TABLES[1], T2_HEAD, T2)

DATA = {
    "title": "智能体时代的 kernel 移植：把 Sage Attention 3 从 CUDA C++ 搬到 CuTeDSL",
    "summary": [
        {"key": "一个下午的移植",
         "body": "AI 智能体在一个下午里，把 CUDA C++ 写的 attention kernel 移植并优化成 "
                 "CuTeDSL 版本：比原版 C++ 实现快 1.2 倍，比 cuDNN 版本快 2.8 倍。"},
        {"key": "移植的两种含义",
         "body": "一是跨 GPU 架构（Hopper 到 Blackwell 这类），二是跨抽象层次（底层 CuTe "
                 "C++ 到 CuTeDSL、Triton 这类 DSL）。两种场景智能体都做得不错。"},
        {"key": "靠什么跑通",
         "body": "上下文只给两个必要仓库加一份 INDEX.md 目录说明，把踩到的 CuTeDSL 坑记进 "
                 "README.md，再用 PTX/SASS 的寄存器溢出与指令数这些硬指标指导下一轮优化。"},
    ],
    "lead": [],
    "sections": [],
    "conclusion": [
        "**智能体真正改变的不是写 kernel，而是搬运 kernel。** 跨 GPU 架构、跨抽象层次的移植"
        "原本是最枯燥、最靠人逐行对照的活，现在可以整包交给一个能读仓库、能跑测试阶梯、"
        "还能自己看 PTX/SASS 指标的智能体。",
        "跑通它的关键不在模型多聪明，而在工程约束搭得好不好：上下文只放必要的两个仓库并写清 "
        "INDEX.md，让踩过的 DSL 坑沉淀成 README.md 里的长期记忆，再用寄存器溢出和指令数"
        "这类硬指标决定下一步往哪优化，而不是靠感觉。",
        "对做 GPU kernel 的人来说，手里那些只在某一代架构、某一层抽象上跑得动的实现，"
        "从此多了一条低成本的再版路径；人的位置也从逐行改写前移到了定路线和审指标。",
    ],
    "reference_url": "https://x.com/maharshii/status/2100193318277890174",
}

S = DATA["sections"]


def sec(title, kind="h2"):
    S.append({"type": kind, "title": title, "paras": [], "fig_after": {}})
    return S[-1]


def fig(s, name, caption, idx=-1):
    i = idx if idx >= 0 else max(0, len(s["paras"]) - 1)
    s.setdefault("fig_after", {}).setdefault(str(i), []).append(
        {"src": name, "caption": caption})


# ── 引言（原文此处无小节标题，仅正文段）────────────────────────────────
s = sec("", kind="p")
s["paras"] += [
    "几周前，我的 AI 智能体在一个下午里，把一个 CUDA C++ 的 attention kernel 移植成 "
    "CuTeDSL 版本，随后又做了优化。最终这个 kernel 比原版快 1.2 倍，比 cuDNN 版本快 2.8 倍。"
    "我认为智能体做 kernel 开发，最有杀伤力的用例就是移植。",
    "我所说的「移植」包含两种情形：",
    bullet("**不同的 GPU 版本**：把一个跑在某类 GPU 上的 kernel 改到另一类 GPU 上，"
           "并用上目标架构特有的能力。比如从 H100（Hopper）迁到 B200（Blackwell）。"),
    bullet("**不同的抽象层次**：把一个 kernel 从一种抽象层次换到另一种。比如从底层的 "
           "NVIDIA CuTe C++ 换到 Triton 这类高层 DSL（领域特定语言）。"),
    "智能体在这两种移植上都表现很好。下面讲讲我把 Sage Attention 3 这个 kernel 从 CuTe C++ "
    "移植到 CuTeDSL、再做优化的经历。",
]
fig(s, "fig01.png", "图1：移植版本与其他版本的对比", 4)

# ── Sage Attention 3 ─────────────────────────────────────────
s = sec("Sage Attention 3")
s["paras"] += [
    "为了让 attention 运算在 NVIDIA 消费级 Blackwell GPU 上更高效，Sage Attention 3 引入了"
    "量化和低比特张量核心，用来加速运算内部 GEMM（矩阵乘法）的推理。RTX 5090、6000 PRO "
    "这类 GPU 上的 FP4 张量核心，性能远高于 FP16 张量核心，所以得聪明地把它们用到 "
    "attention kernel 的 GEMM 里。论文在这里：https://arxiv.org/pdf/2505.11594",
    "数值量化到 FP4 e2m1 时会出现严重的精度损失（这种格式只有 15 个可表示数值），"
    "Sage Attention 3 也提出了一种方法缓解它：",
]
fig(s, "fig02.png", "图2：sage3 的方法", 1)
s["paras"] += [
    "FP4 attention 有两个主要挑战：",
    bullet("逐张量（per-tensor）和逐 token（per-token）量化都不足以保住模型精度，"
           "所以要把量化分组大小限制在 1x16，也就是 NVFP4 格式。"),
    bullet("attention map P 的数值主要落在 [0, 1] 这个小区间里。直接量化到 FP4 时，"
           "这些数值会把缩放因子压进极窄的动态范围，而硬件要求量化因子必须是 FP8 e4m3 "
           "类型，用 FP8 表示这些缩放因子会带来明显的精度损失。"),
    "针对第二个挑战，作者提出的方法是两级量化。它先用逐 token（也就是逐行）量化，"
    "把每个 token 的取值范围归一化到 [0, 448 x 6]，从而吃满 FP8 e4m3 缩放因子的范围，"
    "然后再做 FP4 微观缩放量化。",
]
fig(s, "fig03.png", "图3：两级量化收益分析", 5)

# ── 移植过程 ────────────────────────────────────────────────
s = sec("移植过程")
s["paras"] += [
    "Sage Attention 3 的原始实现是 CUDA C++，大约 20 个文件，全是模板和 NVIDIA 的 CuTe "
    "抽象。光是读懂整个实现就得花我几天时间。代码在这里："
    "https://github.com/thu-ml/SageAttention",
    "__CODE__bash::" + CODE_BASH_TREE_CPP,
    "我想把它移植到 CuTeDSL，享受 JIT 编译快、维护更省事、不用再受 C++ 模板折磨的好处。"
    "而且我还想迭代优化这个 kernel，把 C++ 实现可能漏掉的那点性能榨出来。",
    "优化后的 CuTeDSL 版本只有 4 个主要文件。其余文件是真正的 harness（测正确性和跑 "
    "benchmark），以及一些探针文件，那是 Claude 为了确认原 C++ 实现里没有、CuTeDSL 特有的 "
    "API 行为而生成的。",
    "__CODE__bash::" + CODE_BASH_TREE_DSL,
    "这次移植的流程，和我之前一篇文章里讲的基本一致："
    "https://x.com/maharshii/status/2086442755748970889",
    "上下文目录里，我只给了 Claude 两个仓库：NVIDIA 的 cutlass 和 SageAttention，"
    "另外本地装了 CuTeDSL。我还让它维护一个 " + c("INDEX.md") + "，说明 context 里"
    "每个目录能拿来做什么，大概长这样：",
]
s["table"] = TAB1

# ── 移植过程中的记录习惯（原文无小节标题）──────────────────────────────
s = sec("", kind="p")
s["paras"] += [
    "整个移植过程中，我让智能体把它遇到的 CuTeDSL 坑和陷阱都记进一个 " + c("README.md")
    + "。这样它就能把和 DSL 特性相关的知识留住，不会忘掉。",
]

# ── 测试 ───────────────────────────────────────────────────
s = sec("测试")
s["paras"] += [
    "harness 文件也沿用了我上一篇文章的做法，并随移植阶段不断迭代。它跑的是一个测试阶梯，"
    "顺序安排得让任何失败都能就地定位：先从 host 侧代码开始，再到 kernel 侧的测试，"
    "最后和参考实现对比。",
]
fig(s, "fig04.png", "图4：参考测试阶梯", 0)

# ── PTX/SASS dump ─────────────────────────────────────────
s = sec("PTX/SASS dump")
s["paras"] += [
    "harness 还会让智能体把 PTX、SASS 和 CUBIN 文件 dump 出来，借此检查寄存器溢出、"
    "指令数量、向量化，以及其他优化机会。它会把 dump 文件里读到的 kernel 信息写进 "
    + c("asm_info.json") + "，大概长这样：",
    "__CODE__json::" + CODE_JSON_ASM,
]

# ── 优化日志 ────────────────────────────────────────────────
s = sec("优化日志")
s["paras"] += [
    "智能体还把试过的每项优化都记在同一个 " + c("README.md") + " 里，形成一份持续更新的"
    "日志。收益最大的是对 TMA/MMA warp 的寄存器做增减，以及它有意偏离 C++ 实现的几处做法：",
    "__CODE__text::" + CODE_TEXT_DELTAS,
    "README 里的优化日志表格如下：",
]
s["table"] = TAB2

# ── 结果一句话（原文在 Conclusion 标题之前）────────────────────────────
s = sec("", kind="p")
s["paras"] += [
    "这些实现上的差异，让 CuTeDSL kernel 比原始 C++ 实现快 1.2 倍。",
]

# ── 结论 ───────────────────────────────────────────────────
s = sec("结论")
s["paras"] += [
    "整体看，快速移植 kernel 是智能体做 kernel 开发相当好的一个用例。这次移植过程中我一行 "
    "CuTeDSL 代码都没写，却拿到了比原始实现更快的 kernel，把几天的工作量压缩到几个小时。"
    "过程中仍然需要一些来回沟通，把智能体引到更好的路子上，但这比让它自己从头摸索要快。"
    "我敢打赌，随着模型变强，需要人介入的这段差距会持续收窄。",
]


def main():
    nfig = npara = ncode = 0
    for s in S:
        n = len(s["paras"])
        npara += n
        ncode += sum(1 for p in s["paras"] if p.startswith("__CODE__"))
        for k in (s.get("fig_after") or {}):
            assert int(k) < n, "fig_after 越界: %s key=%s paras=%d" % (s["title"], k, n)
            nfig += len(s["fig_after"][k])
    assert len(DATA["summary"]) == 3
    assert nfig == 4, nfig
    assert ncode == 4, ncode
    blob = json.dumps(DATA, ensure_ascii=False)
    for bad in ("—", "——"):
        assert bad not in blob.replace(CODE_BASH_TREE_CPP, "").replace(
            CODE_BASH_TREE_DSL, ""), "含破折号: %s" % bad
    print("sections=%d paras=%d code=%d figs=%d tables=%d"
          % (len(S), npara, ncode, nfig, sum(1 for s in S if s.get("table"))))
    out = os.path.join(HERE, "article_data.json")
    json.dump(DATA, io.open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("article_data.json 已写入:", out)


if __name__ == "__main__":
    main()
