# -*- coding: utf-8 -*-
"""One-off: rewrite article_data_build.py figure placement for the vLLM x AgentX article.

- splits 3 merged paragraphs so the source figure order is preserved
- replaces the "evenly embed 8 figures" block with explicit fig_after (8 static + 3 original GIFs)
"""
import io

PATH = r"D:/06_Hermes/articles/vllm-agentx-agentic-serving/article_data_build.py"
lines = io.open(PATH, encoding="utf-8").read().split("\n")


def split_line(idx, needle):
    """Split a 't(s,"....")' line in two right before `needle`."""
    line = lines[idx]
    assert needle in line, (idx, needle, line[:60])
    a, b = line.split(needle, 1)
    assert a.startswith('t(s,"') and b.endswith('")'), (a[:30], b[-30:])
    lines[idx] = a + '")' + "\n" + 't(s,"' + needle + b
    print("split line", idx, "->", needle[:24])


def split_line2(idx, needle1, needle2):
    """Split a 't(s,"....")' line into three parts."""
    line = lines[idx]
    assert needle1 in line and needle2 in line
    a, rest = line.split(needle1, 1)
    b, c = rest.split(needle2, 1)
    assert a.startswith('t(s,"') and c.endswith('")')
    lines[idx] = (
        a + '")' + "\n"
        + 't(s,"' + needle1 + b + '")' + "\n"
        + 't(s,"' + needle2 + c
    )
    print("split line", idx, "-> 3 paras")


split_line(22, "更大的 scale-up 域")
split_line(26, "对策是 --long-prefill-token-threshold")
split_line2(32, "对三个开放前沿模型取的是", "DeepSeek V4 Pro：12 芯片")

src = "\n".join(lines)
marker = "# ---- evenly embed 8 body figures across non-empty paragraphs ----"
head = src[: src.index(marker)]

tail = '''# ---- 图位：按源文顺序显式挂到对应段后（8 张静态图 + 3 张原文 GIF 动图）----
FIG = [
    (0, 0, "fig01.png", "数据来源：SemiAnalysis AgentX。"),
    (2, 0, "fig02.png", "图 2：面向 agentic 服务的全栈优化。数据面管理分布式共享 KV 缓存，执行面为每个模型匹配恰当的并行与 kernel，控制面协调 P/D 比例与请求调度。"),
    (3, 0, "fig03.png", "图 3：vLLM 的混合 KV 缓存管理器。"),
    (4, 1, "fig04.png", "图 4：对 Kimi K3，DCP 实现更低的 decode 延迟并扩展到更高并发。"),
    (4, 2, "fig05.gif", "图 5：DCP4 下基于对称内存的 MLA decode 路径，每一步都融合进单个 kernel。"),
    (4, 3, "fig06.png", "图 6：当每 rank batch size > 3 时，WideEP（DEP16）比 DCP8 扩展得更好。"),
    (5, 1, "fig07.gif", ""),
    (5, 3, "fig08.gif", ""),
    (6, 0, "fig09.png", "图 9：Kimi K3 在不同硬件上、不同 p90 交互度下每 1 美元能产出的总 token 数。来源：Kimi K3 SemiAnalysis AgentX 仪表盘。"),
    (6, 1, "fig10.png", ""),
    (6, 2, "fig11.png", ""),
]
for _si, _pi, _src, _cap in FIG:
    S[_si].setdefault("fig_after", {}).setdefault(str(_pi), []).append({"src": _src, "caption": _cap})
for _si, _sec in enumerate(S):
    _n = len(_sec["paras"])
    for _k, _v in (_sec.get("fig_after") or {}).items():
        assert int(_k) < _n, f"fig_after 越界 sec{_si} key={_k} paras={_n}"
json.dump(d, open(os.path.join(D, "article_data.json"), "w", encoding="utf8"), ensure_ascii=False, indent=2)
print("sections", len(S), "paras", sum(len(x["paras"]) for x in S),
      "figs", sum(len(v) for x in S for v in (x.get("fig_after") or {}).values()))
'''

io.open(PATH, "w", encoding="utf-8", newline="\n").write(head + tail)
print("written")
