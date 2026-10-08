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
    "title": "ROCm 10.1：打破数据搬运瓶颈，存储直达 GPU",
    "summary": [
        {"key": "数据通路", "body": "hipFile 新增异步快路径、批量 I/O、多层遥测，存储经 PCIe 直连 GPU；HIP runtime 加 NUMA 感知主机内存分配，内存贴着算力放。"},
        {"key": "工具链", "body": "ROCm CLI v1.0.0 单二进制搭本地 AI；AMD Skills 给编码 agent 标准化集成；ROCprofiler-SDK 加 kernel replay 与 PC sampling。"},
        {"key": "平台", "body": "LLVM 24、LTO 分区缓存提速增量构建；Composable Kernel、MIGraphX、rocSPARSE 更新；AMD SMI 接任；WSL2 技术预览；Ubuntu 26.04 SR-IOV；hipThreads 增量加速线程化代码。"},
    ],
    "lead": [
        "限制训练运行的到底是 GPU 算多快，还是数据送多快？模型和数据集越做越大，答案越来越偏向后者：checkpoint、KV cache、模型参数撑爆了离 GPU 最近的高速内存，存储到设备的路径成了最大瓶颈。ROCm 10.1 整版就是冲着这个来的。",
        "核心两招：AMD Infinity Storage 的 hipFILE 让存储经 PCIe 直达 GPU，CPU 只留在控制面；HIP runtime 的 NUMA 感知分配把主机内存放到用它的算力旁边。外加 CLI、profiling、编译器、库的全套更新，下面逐项拆开。",
    ],
    "sections": sections,
    "conclusion": [
        "ROCm 10.1 的优先级很清楚：负载规模上去之后，数据搬得好不好、放得对不对，和算力本身一样重要。hipFILE 快路径缩短存储到 GPU 的路，NUMA 感知分配让主机内存贴着算力，多层 I/O 遥测告诉用户瓶颈到底在哪一层——这套组合拳打的是越来越 gate 大模型训练推理的数据搬运瓶颈。",
        "平台侧 LLVM 24、MIGraphX 换后端、AMD SMI 接任、WSL2 预览、hipThreads，都是降低迁移与运维成本的务实更新。从 10.0 升级注意 clang_major 变 24，按编译器版本写的脚本要先检查一遍。",
    ],
    "reference_url": "https://rocm.blogs.amd.com/ecosystems-and-partners/rocm-10.1-blog/README.html",
}

assert len(DATA["summary"]) == 3, "summary 必须恰好 3 条"
with open(os.path.join(D, "article_data.json"), "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)

nparas = sum(len(s["paras"]) for s in sections)
ncode = sum(1 for s in sections for p in s["paras"] if p.startswith("__CODE__"))
print(f"sections={len(sections)} paras={nparas} code={ncode} figs={fig_count}")
print("article_data.json 已生成")
