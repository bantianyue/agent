#!/usr/bin/env python3
"""DSL parser: content1.txt (S#/H#/T#/F#/TB#/TR#) -> article_data.json ."""
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
    elif line.startswith("TB# "):
        assert cur is not None, "TB before first S#"
        assert "table" not in cur, "一节只支持一张表"
        cur["table"] = {"head": [c.strip() for c in line[4:].split("|")], "rows": []}
        prev_was_fig = False
    elif line.startswith("TR# "):
        assert cur is not None and "table" in cur, "TR 无对应 TB"
        cells = [c.strip() for c in line[4:].split("|")]
        assert len(cells) == len(cur["table"]["head"]), f"列数不匹配: {cells}"
        cur["table"]["rows"].append(cells)
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
    "title": "Abhik Sarkar：Xid 31 MMU 故障实战：每天 28 次生产 GPU 崩溃的排查与修复",
    "summary": [
        {"key": "FAULT_PDE", "body": "MMU 走完页表发现空 Page Directory Entry——整片区域（≥2MB）被解映射，指向分配器的大块释放，不是单个页损坏；排查找 free_all_blocks()/empty_cache()。"},
        {"key": "DLPack 陷阱", "body": "torch.from_dlpack(cupy_array) 零拷贝制造共享所有权：CuPy 池释放 → PDE 拆除 → PyTorch 张量指向无效虚拟内存 → 读它的 kernel 触发 Xid 31。跨分配器边界一律 clone。"},
        {"key": "三处修复", "body": "NVDEC 输出 RGB 切 NV12（DPB 占用减半）；NV12 surface 先 clone 出 DPB 再跑 CuPy；CuPy 输出 clone 进 PyTorch 内存并删掉 free_all_blocks()。7000+ 视频零故障。"},
    ],
    "lead": [
        "GPU 推理管线每天处理数千个视频，journalctl 里突然出现 Xid 31：GPU 页表遍历失败，CUDA context 死亡，管线重置。Abhik Sarkar 把这次生产事故的排查写成了完整实战记录。",
        "下面拆解 Xid 31 错误信息的每个字段、产生它的 GPU 虚拟内存系统、视频管线里的多分配器竞态，以及从每天 28 次崩溃到零的三处修复，保留全部技术细节。",
    ],
    "sections": sections,
    "conclusion": [
        "Xid 31 排查的完整链条：先读错误字段定方向（FAULT_PDE 查大块释放、VIRT_READ 查 use-after-free、地址看落在哪个分配器的地盘、引擎字段看是计算还是 DMA），再看管线里有没有跨分配器的零拷贝共享，最后把数据路径彻底隔离。",
        "核心教训只有一句：DLPack 零拷贝不是免费的，每次交接都制造共享所有权问题。生产管线里，跨分配器边界一律 clone 张量——省下的那次拷贝，远不够一次 Xid 31 贵的。",
    ],
    "reference_url": "https://www.abhik.ai/articles/gpu-xid31-mmu-faults",
}

assert len(DATA["summary"]) == 3, "summary 必须恰好 3 条"
with open(os.path.join(D, "article_data.json"), "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)

nparas = sum(len(s["paras"]) for s in sections)
ntables = sum(1 for s in sections if "table" in s)
print(f"sections={len(sections)} paras={nparas} figs={fig_count} tables={ntables}")
print("article_data.json 已生成")
