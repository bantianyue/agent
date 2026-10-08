#!/usr/bin/env python3
"""DSL parser: content1.txt (S#/H#/T#/F#/__CODE__) -> article_data.json ."""
import json, os, sys

D = os.path.dirname(os.path.abspath(__file__))

sections = []
cur = None
fig_count = 0
prev_was_fig = False
in_code = False
code_buf = []

def flush_code():
    global in_code, code_buf
    if in_code and code_buf:
        cur["paras"].append("__CODE__" + "\n".join(code_buf))
    in_code = False
    code_buf = []

for raw in open(os.path.join(D, "content1.txt"), encoding="utf-8"):
    line = raw.rstrip("\n")
    if not line.strip():
        flush_code()
        continue
    if line.startswith("S# ") or line.startswith("H# ") or line.startswith("T# ") or line.startswith("F# "):
        flush_code()
    if in_code:
        code_buf.append(line)
        prev_was_fig = False
        continue
    if line.startswith("S# "):
        cur = {"type": "h2", "title": line[3:].strip(), "paras": [], "fig_after": {}}
        sections.append(cur)
        prev_was_fig = False
    elif line.startswith("H# "):
        cur = {"type": "h3", "title": line[3:].strip(), "paras": [], "fig_after": {}}
        sections.append(cur)
        prev_was_fig = False
    elif line.startswith("__CODE__"):
        assert cur is not None, "CODE before first S#"
        in_code = True
        code_buf = [line[len("__CODE__"):]]
        prev_was_fig = False
        continue
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
flush_code()

for s in sections:
    n = len(s["paras"])
    for k in s["fig_after"]:
        assert int(k) < n, f"fig_after 越界: section={s['title'][:20]} key={k} paras={n}"

DATA = {
    "title": "NVIDIA：Green Contexts 让 GPU 资源划分精确可控",
    "summary": [
        {"key": "SM 分区加 workqueue 配给", "body": "Green contexts 让应用显式选定 SM 子集与 workqueue 资源，CUDA 12.4 进 Driver API，13.1 进 Runtime API，创建销毁轻量、不隐式同步无关工作。"},
        {"key": "关键 kernel 实测", "body": "Blackwell 148 SM 上，关键 kernel 延迟：green-ctx 分区 0.007 ms，高优先级无分区 0.140 ms，同优先级 3.727 ms。"},
        {"key": "显式编程模型", "body": "cudaGreenCtxCreate 拿句柄、cudaExecutionCtxStreamCreate 建流，不再依赖线程局部 device 状态；其余代码沿用 stream 模型。"},
    ],
    "lead": [
        "一张 GPU 上同时跑延迟敏感算子和吞吐型后台 kernel 时，stream 优先级救不了关键任务：bulk kernel 占满 SM，高优先级 kernel 也只能等 block 排空。NVIDIA 的 Green Contexts 把解法做彻底——直接把 SM 切块划给关键负载。",
        "实测数据很直白：148 SM 的 Blackwell 上，关键 kernel 延迟从同优先级的 3.727 ms，到高优先级的 0.140 ms，再到 green-ctx 分区的 0.007 ms。下面拆机制、看代码、摆数字。",
    ],
    "sections": sections,
    "conclusion": [
        "Green contexts 的本质是把 GPU 资源划分从隐式调度变成显式声明：SM 子集、workqueue 配给、stream 归属，一次配好、处处显式。0.007 ms 对 0.140 ms 说明，优先级只能缓解排队，分区才能消灭排队；代价是 bulk 侧 SM 变少，这是可计算的 trade-off，不是不可预测的干扰。",
        "对推理 serving、多租户、端侧 pipeline 这类单卡多组件场景，一个可复用的模式是：关键路径单独分区加高优先级，吞吐部分吃剩下的 SM，workqueue 配给顺手配上。CUDA 13.1 的 Runtime API 让接入只是几次调用的事，可以增量采用。",
    ],
    "reference_url": "https://developer.nvidia.com/blog/control-how-your-gpu-shares-work-with-green-contexts/",
}

assert len(DATA["summary"]) == 3, "summary 必须恰好 3 条"
with open(os.path.join(D, "article_data.json"), "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)

nparas = sum(len(s["paras"]) for s in sections)
ncode = sum(1 for s in sections for p in s["paras"] if p.startswith("__CODE__"))
print(f"sections={len(sections)} paras={nparas} code={ncode} figs={fig_count}")
print("article_data.json 已生成")
