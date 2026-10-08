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
    "title": "NVIDIA DOCA GPUNetIO：统一 GPU 发起网络，CUDA kernel 直驱网卡",
    "summary": [
        {"key": "统一底座", "body": "各通信库自建的 GDA-KI RDMA 收敛到同一份 GPUNetIO 实现；开源版给开放集成，DOCA SDK 版是超集，运行时经 dlopen 衔接。"},
        {"key": "编程模型", "body": "CPU 走控制路径导出传输对象，GPU 数据路径三步：提交 WQE、敲门铃、轮询 CQE；高层 API 线程安全，低层 API 给精确控制。"},
        {"key": "生态落地", "body": "NCCL 2.27+ GIN、NVSHMEM 3.7 新传输、NVQLink 量子互连都建在 GPUNetIO 上；FPGA 实测转发往返延迟中位 2.7 微秒。"},
    ],
    "lead": [
        "GPU 应用要网络像一等 GPU 操作：每笔事务中间站着 CPU，它就是关键路径上的瓶颈。DOCA GPUNetIO 的答案是让 CUDA kernel 直接驱动 Ethernet、RDMA、Verbs、DMA——提交 WQE、敲网卡门铃、轮询完成，全在 GPU 上。",
        "更大的变化在生态：NCCL、NVSHMEM、UCX/NIXL 这些库此前各养一套 GDA-KI 实现，现在收敛到同一份 GPUNetIO 底座上。下面拆统一架构、编程模型、代码与落地数据。",
    ],
    "sections": sections,
    "conclusion": [
        "GPUNetIO 的统一逻辑很干净：GDA-KI 的管道只写一遍，各通信库在上面做语义。NCCL 2.27 的 GIN、NVSHMEM 3.7 的新传输、NVQLink 的 2.7 微秒转发，都是同一份底座的不同切面；开源版与 SDK 版设备侧 API 对齐，dlopen 做运行时衔接，开放与功能不用二选一。",
        "对做分布式训练推理的人来说，选型路径也变简单了：新开发直接吃 GPUNetIO 公共底座，NCCL 集合算法与 GPUNetIO 传输管道各干各的；小消息场景开 GDA-KI，CPU 代理瓶颈消失后 CTA/QP 扩展行为完全不同，这笔账值得算一算。",
    ],
    "reference_url": "https://developer.nvidia.com/blog/doca-gpunetio-gda-ki-unified-gpu-networking/",
}

assert len(DATA["summary"]) == 3, "summary 必须恰好 3 条"
with open(os.path.join(D, "article_data.json"), "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)

nparas = sum(len(s["paras"]) for s in sections)
ncode = sum(1 for s in sections for p in s["paras"] if p.startswith("__CODE__"))
print(f"sections={len(sections)} paras={nparas} code={ncode} figs={fig_count}")
print("article_data.json 已生成")
