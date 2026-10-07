#!/usr/bin/env python3
"""DSL parser: content1.txt (S#/H#/T#/F#) -> article_data.json ."""
import json, os, sys

D = os.path.dirname(os.path.abspath(__file__))

sections = []
cur = None
fig_count = 0
prev_was_fig = False

for raw in open(os.path.join(D, "content1.txt"), encoding="utf-8"):
    line = raw.rstrip("\n")
    if not line.strip():
        continue
    if line.startswith("S# "):
        cur = {"type": "h2", "title": line[3:].strip(), "paras": [], "fig_after": {}}
        sections.append(cur)
        prev_was_fig = False
    elif line.startswith("H# "):
        cur = {"type": "h3", "title": line[3:].strip(), "paras": [], "fig_after": {}}
        sections.append(cur)
        prev_was_fig = False
    elif line.startswith("T# "):
        assert cur is not None, "T before first S#"
        cur["paras"].append(line[3:].strip())
        prev_was_fig = False
    elif line.startswith("F# "):
        assert cur is not None, "F before first S#"
        assert not prev_was_fig, "相邻 F 行：多图连排，需在内容文件里插 T 段隔开"
        rest = line[3:].strip()
        src, cap = rest.split("|", 1)
        i = max(0, len(cur["paras"]) - 1)
        key = str(i)
        cur["fig_after"].setdefault(key, []).append({"src": src.strip(), "caption": cap.strip()})
        fig_count += 1
        prev_was_fig = True
    else:
        print(f"未知行前缀，已跳过: {line[:40]}", file=sys.stderr)

for s in sections:
    n = len(s["paras"])
    for k in s["fig_after"]:
        assert int(k) < n, f"fig_after 越界: section={s['title'][:20]} key={k} paras={n}"

missing = []
for s in sections:
    for figs in s["fig_after"].values():
        for f in figs:
            if not os.path.exists(os.path.join(D, f["src"])):
                missing.append(f["src"])
assert not missing, f"图文件缺失: {missing}"

DATA = {
    "title": "给Blackwell SM100手写更快的GQA decode kernel",
    "summary": [
        {"key": "换操作数顺序", "body": "算S^T=KQ^T/√d、O^T=V^TP^T，把KV位置放到大矩阵维：8头group、128 token块的score tile从128×128缩到128×8，padding计算与TMEM搬运一起省掉。"},
        {"key": "调度抠到warp级", "body": "两个softmax warpgroup交错tile、两个O槽滚动，correction与VP不再抢同一块存储；PDL让combine在producer尾巴里提前启动；删掉M_final全局缓冲与每次的memset reset。"},
        {"key": "实测", "body": "B200 BF16、60形状对FA4：kernel+PDL中位数1.46倍（0.88到2.26倍），自动选择1.47倍；batch scaling到64时多数格子领先。"},
    ],
    "lead": [
        "Colfax的S/P ping pong让FA4 decode在Blackwell上快了16%：下一个KV块的QK不再等当前块的softmax。但PackGQA打包query head之后，打包维度仍可能远小于FA4的tile——64 query head配8 KV head，128行tile里只有8行有效，剩下全是padding计算。",
        "换个思路：不跟FA4拼同一套tile，改算S^T=KQ^T、O^T=V^TP^T，把KV位置放到大矩阵维，score tile从128×128缩到128×8；再用双softmax warpgroup、双O槽、PDL、thread block cluster内reduce一层层抠调度。B200上最高跑到FA4的2.26倍。",
    ],
    "sections": sections,
    "conclusion": [
        "**GQA decode的优化空间不在搬更多字节，而在调度。**换操作数顺序消掉padding，双softmax warpgroup与双O槽消掉串行等待，PDL把combine启动藏进producer尾巴，cluster内reduce省掉第二次launch：60形状中位数1.46倍，最高2.26倍。",
        "对写attention kernel的人，IKET方法论比结论更值钱：每个优化都有trace为证，没增益的改动（比如去掉softmax mutex）也如实保留。CUTLASS的gqa_decode_simple/opt是现成的起点，PR #2973的代码可以直接拿去试。",
    ],
    "reference_url": "https://ighoshsubho.bearblog.dev/building-a-faster-gqa-decode-kernel-for-blackwell-sm100/",
}

assert len(DATA["summary"]) == 3, "summary 必须恰好 3 条"
with open(os.path.join(D, "article_data.json"), "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)

nparas = sum(len(s["paras"]) for s in sections)
print(f"sections={len(sections)} paras={nparas} figs={fig_count}")
print("article_data.json 已生成")
