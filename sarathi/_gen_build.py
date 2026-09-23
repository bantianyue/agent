# -*- coding: utf-8 -*-
"""生成 article_data_build.py（程序化，避免手写超长 JSON 出错）"""
import json, os, re, sys

ART = r"D:\06_Hermes\articles\sarathi"
items = json.load(open(os.path.join(ART, "_items.json"), encoding="utf-8"))
tr = json.load(open(os.path.join(ART, "_translations.json"), encoding="utf-8"))
tr = {int(k): v for k, v in tr.items()}
caps = json.load(open(os.path.join(ART, "_captions.json"), encoding="utf-8"))
caps = {int(k): v for k, v in caps.items()}
figmap = json.load(open(os.path.join(ART, "_figmap.json"), encoding="utf-8"))
FIG = {int(m["fig"][3:5]): m["fig"] for m in figmap}

# item index -> para id (same order as _translate.py)
item2pid = {}
n = 0
skip = False
for i, it in enumerate(items):
    if it["kind"] == "head":
        t = it["text"].strip().lower()
        skip = t in ("references", "instructions for reporting errors")
        continue
    if skip:
        continue
    if it["kind"] == "p":
        item2pid[i] = n
        n += 1

assert n == 105, n

seen_gloss = set()

def strip_repeat_gloss(t):
    def rep(m):
        zh, en = m.group(1), m.group(2).strip()
        if not re.search(r"[A-Za-z]", en):
            return m.group(0)
        key = (zh, en.lower())
        if key in seen_gloss:
            return zh
        seen_gloss.add(key)
        return "%s（%s）" % (zh, en)
    return re.sub(r"([\u4e00-\u9fff]{2,8})[（(]([A-Za-z0-9 ,\-:\./]{2,40})[)）]", rep, t)


def fix_quotes(t):
    out = []
    open_q = True
    for ch in t:
        if ch == '"':
            out.append("「" if open_q else "」")
            open_q = not open_q
        else:
            out.append(ch)
    return "".join(out)


def clean(t):
    t = t.replace("計算", "计算")
    t = t.replace("——", "：")
    t = re.sub(r"（\s*§[0-9\.]+\s*）", "", t)
    t = re.sub(r"\s*§[0-9\.]+", "", t)
    t = re.sub(r"如\s*[0-9]\.[0-9]\s*所述", "如前所述", t)
    t = t.replace("：：", "：")
    t = fix_quotes(t)
    t = t.replace("P:D ratio", "P:D 比例")
    t = t.replace("decode-maximal batching", "解码最大化批处理")
    t = t.replace("decode-maximal 批次", "解码最大化批次")
    t = t.replace("decode 最大批处理（解码最大化批处理）", "解码最大化批处理")
    t = re.sub(r"解码最大化批处理\s*（解码最大化批处理）", "解码最大化批处理", t)
    t = re.sub(r"\s*(解码最大化批处理|解码最大化批次)\s*", r"\1", t)
    t = t.replace("如 所述", "如前所述")
    t = re.sub(r"(P:D 比例)\s+", r"\1", t)
    t = t.replace("可与本文优化互补", "可与 Sarathi 的优化互补")
    t = t.replace("模型创新与本文工作正交", "模型创新与 Sarathi 正交")
    t = re.sub(r"\s+", " ", t).strip()
    return t


PARA = {}
for i, pid in item2pid.items():
    PARA[i] = strip_repeat_gloss(clean(tr[pid]))

# —— 定点修补（按 item 索引） ——
PID2ITEM = {v: k for k, v in item2pid.items()}
PARA[PID2ITEM[36]] = ("Sarathi 的设计与实现采用两项技术：分块预填充（chunked-prefills）与解码最大化批处理"
                      "（decode-maximal batching），以提升 LLM 推理性能。")
assert PARA[PID2ITEM[36]].count("：") == 1

# —— 编号列表 → 行内 span（源文 ordered-list，见 build-guide「正文格式 100% 保留」） ——
NUM_TPL = '<span style="color:#0F4C81;font-weight:bold;">%s</span>&nbsp;%s'
# 源文 4 条贡献无加粗小标题，此处按编号列表映射补语义标签（内容逐条对应原文）
CONTRIB = {
    13: "**分块预填充**：可构造计算饱和且均匀的工作单元。",
    14: "**解码最大化批处理**：使低效的解码（decode）可「搭车」高效预填充（prefill）。",
    15: "**接入流水线并行**：将分块预填充与解码最大化批处理应用于流水线并行"
        "（pipeline parallelism），显著减少流水线气泡（pipeline bubble）。",
    16: "**广泛评估**：在多种模型、硬件与并行策略上验证，吞吐（throughput）提升最高达 1.91 倍。",
}

def to_num(idx):
    if idx in CONTRIB:
        m = re.match(r"^(\d)\.", PARA[idx])
        assert m, "编号段落格式异常: %r" % PARA[idx][:40]
        return NUM_TPL % (m.group(1), CONTRIB[idx])
    t = PARA[idx]
    m = re.match(r"^(\d)\.\s*(.+)$", t, re.S)
    assert m, "编号段落格式异常: %r" % t[:40]
    return NUM_TPL % (m.group(1), m.group(2).strip())

for _i in (13, 14, 15, 16, 92, 93, 94, 95):
    PARA[_i] = to_num(_i)

FORMULA = "最大批大小按下式求解：**B = ⌊(M(G) − M(S)) / (L × m(kv))⌋**，其中的取整意味着实际可容纳的请求数只能取下界。"

FIGCAP = {k: v for k, v in caps.items()}

def F(n):
    return {"src": FIG[n], "caption": FIGCAP[n]}


def build_paras(idxs, extra=None):
    ps = []
    for x in idxs:
        if x == "FORMULA":
            ps.append("FORMULA")
        elif isinstance(x, tuple) and x[0] == "RAW":
            ps.append(x[1])
        else:
            ps.append(PARA[x])
    if extra:
        ps.extend(extra)
    return ps


# —— 目标结构 ——
SECTIONS = []

def sec(t, title, idxs, figs=None, table=None, raw_after=None):
    par = build_paras(idxs)
    d = {"type": t, "title": title, "paras": par}
    if figs:
        bad = [k for k in figs if int(k) >= len(par)]
        assert not bad, "fig_after 越界 %s in %s" % (bad, title)
        d["fig_after"] = {str(k): v for k, v in figs.items()}
    if table is not None:
        d["table"] = table
    SECTIONS.append(d)
    return d


T1 = {"head": ["操作", "输入张量形状", "权重张量形状", "输出张量形状"],
      "rows": [["preproj", "[B,L,H]", "[H,H]", "[B,L,H]"],
               ["attn", "[B,L,H]", "-", "[B,L,H]"],
               ["postproj", "[B,L,H]", "[H,H]", "[B,L,H]"],
               ["ffn_ln1", "[B,L,H]", "[H,H2]", "[B,L,H2]"],
               ["ffn_ln2", "[B,L,H2]", "[H2,H]", "[B,L,H]"]]}

T2 = {"head": ["批处理方案", "线性算子<br/>(ms)", "注意力<br/>(ms)", "总时间<br/>(ms)", "单 token 预填充<br/>(ms)", "单 token 解码<br/>(ms)"],
      "rows": [["仅预填充", "224.8", "10", "234.8", "0.229", "-"],
               ["仅解码", "44.28", "5.68", "49.96", "-", "12.49"],
               ["<strong>解码最大化</strong>", "<strong>223.2</strong>", "<strong>15.2</strong>", "<strong>238.4</strong>", "<strong>0.229</strong>", "<strong>1.2</strong>"]]}

T3 = {"head": ["模型", "GPU", "GPU 数量", "单卡显存(GB)", "评测方式"],
      "rows": [["LLaMA-13B", "A6000", "1", "48", "真实部署"],
               ["LLaMA-33B", "A100", "1", "80", "真实部署"],
               ["GPT-3", "A100", "64", "80", "模拟"]]}

T4 = {"head": ["模型 (GPU)", "序列长度", "批大小", "P:D 比例", "解码加速", "吞吐提升"],
      "rows": [["LLaMA-13B (A6000)", "1K", "6", "50:1", "5.45×", "<strong>1.33×</strong>"],
               ["LLaMA-13B (A6000)", "2K", "6", "50:1", "3.26×", "1.26×"],
               ["LLaMA-13B (A6000)", "3K", "6", "50:1", "2.51×", "1.22×"],
               ["LLaMA-33B (A100)", "1K", "10", "28:1", "3.83×", "1.25×"],
               ["LLaMA-33B (A100)", "2K", "5", "63:1", "4.25×", "1.22×"],
               ["LLaMA-33B (A100)", "3K", "3", "127:1", "3.51×", "1.14×"]]}

# 1
sec("h2", "引言：预填充吃满算力，解码却在等内存", [])
sec("h3", "从两个阶段到一处失衡", [5, 6, 7], figs={2: [F(1)]})
sec("h3", "Sarathi 的思路、结果与贡献", [8, 9, 10, 11, 12, 13, 14, 15, 16])

# 2
sec("h2", "背景", [])
sec("h3", "Transformer 解码器块", [18, 20], figs={1: [F(2)]})
sec("h3", "预填充与解码两个阶段", [23, 24, 25, 26, 27], table=T1)
sec("h3", "多 GPU 推理：张量并行与流水线并行", [30, 31, 32])

# 3
sec("h2", "动机：解码为何低效，气泡从何而来", [])
sec("h3", "预填充与解码的吞吐差异", [34, 37, 41, 42, 43],
    figs={1: [F(3)], 2: [F(4)], 3: [F(5)]})
sec("h3", "流水线气泡从何而来", [45, 46, 47, 48], figs={3: [F(6)]})
sec("h3", "关键洞察", [51, 52])

# 4
sec("h2", "Sarathi 的设计与实现", [])
sec("h3", "总体思路：从请求级批处理到迭代级调度", [54, 56, 57])
sec("h3", "分块预填充", [59, 61, 62, 63], figs={1: [F(7)]})
sec("h3", "解码最大化批处理", [65, 66])
sec("h3", "解码如何搭上预填充的便车", [68, 69, "FORMULA", 70, 71, 72, 73, 75], table=T2)
sec("h3", "如何选择理想的分块大小", [77, 78, 80, 81, 82, 83, 84, 85], figs={1: [F(8)]})
sec("h3", "实现细节", [87, 88])

# 5
sec("h2", "实验评测", [])
sec("h3", "评测设置与待回答的问题", [91, 92, 93, 94, 95], table=T3)
sec("h3", "解码加速与单 GPU 总览", [97, 100, 101, 102], figs={0: [F(9)]})
sec("h3", "峰值吞吐提升", [110, 111], table=T4)
sec("h3", "P:D 比例的影响", [113, 114, 115], figs={1: [F(10), F(11), F(12)]})
sec("h3", "批大小与分块大小的影响", [117, 118, 119, 120], figs={1: [F(13)]})
sec("h3", "与迭代级调度的对比", [125, 126, 127, 128, 129, 130], figs={3: [F(14), F(15)]})
sec("h3", "流水线并行下的 Sarathi", [135, 136, 137, 142, 143], figs={3: [F(16), F(17)]})
sec("h3", "分块预填充的消融研究", [145, 146, 147, 148], figs={2: [F(18), F(19), F(20)]})

# 6 / 7
sec("h2", "讨论：还没有解决的问题", [150, 151])
sec("h2", "相关工作", [])
sec("h3", "系统层优化", [153, 155, 156, 157, 158, 159])
sec("h3", "模型层创新", [161])

# 替换 FORMULA 占位
for s in SECTIONS:
    s["paras"] = [FORMULA if p == "FORMULA" else p for p in s["paras"]]

DATA = {
    "summary": [
        {"key": "核心机制", "body": "预填充切成等大的分块，每块搭配一批解码请求组成混合批次，解码搭上矩阵乘法的便车。"},
        {"key": "实测结果", "body": "LLaMA-13B 在 A6000 上解码吞吐提升 10 倍，端到端吞吐提升 1.33 倍。"},
        {"key": "并行收益", "body": "8 路流水线并行下气泡减少 6.29 倍，端到端吞吐提升 1.91 倍。"},
    ],
    "lead": [
        "LLM 推理分两段：预填充把整段提示并行算完，解码一次只吐一个 token。前者批大小为 1 就能占满 GPU，后者在同样批大小下每 token 成本高达前者的 200 倍，推理时间被这段低效的长尾吃掉。",
        "Sarathi 把长预填充切成等大的分块，每轮拿一个分块配上尽可能多的解码请求组成混合批次，让解码复用预填充已经拉进显存的模型权重。解码吞吐最高提升 10 倍，端到端吞吐最高 1.33 倍；接上 8 路流水线并行后气泡减少 6.29 倍，端到端加速 1.91 倍。",
    ],
    "sections": SECTIONS,
    "conclusion": [
        "**解码慢的根因是每次只读一份权重却只用一次**，Sarathi 把预填充分块和解码 token 合并进同一次矩阵乘法，权重读一次服务两种请求，单 token 解码时间从 12.49 毫秒降到 1.2 毫秒。",
        "要落地的关键参数是分块大小：先测出模型与硬件组合下的预填充吞吐曲线定出基准值，再保证分块大小与搭载解码数之和是 tile 大小的整数倍，否则分块量化会悄悄吃掉收益。",
    ],
    "reference_url": "https://arxiv.org/html/2308.16369v1",
    "title": "Sarathi：用分块预填充让解码搭上算力便车",
}

# 校验
tot = sum(len(s["paras"]) for s in SECTIONS)
figs = sum(len(v) for s in SECTIONS for v in s.get("fig_after", {}).values())
print("SECTIONS=%d PARAS=%d FIGS=%d TABLES=%d" % (
    len(SECTIONS), tot, figs, sum(1 for s in SECTIONS if "table" in s)))

# 相邻图检查
imgs = []
for s in SECTIONS:
    for i, p in enumerate(s["paras"]):
        imgs.append("T")
        for f in s.get("fig_after", {}).get(str(i), []):
            imgs.append("I")
seq = "".join(imgs)
bad = 0
for m in re.finditer(r"II+", seq):
    pass
# 计相邻图对数
adj = sum(1 for i in range(len(imgs) - 1) if imgs[i] == "I" and imgs[i + 1] == "I")
print("ADJACENT_IMG_PAIRS=%d (允许的源图组：9组 a/b/c 子图)" % adj)

srcs = set()
for s in SECTIONS:
    for v in s.get("fig_after", {}).values():
        for f in v:
            srcs.add(f["src"])
disk = set(f for f in os.listdir(ART) if re.fullmatch(r"fig\d+\.png", f))
print("REF=%d DISK=%d MISSING=%s EXTRA=%s" % (len(srcs), len(disk), sorted(disk - srcs), sorted(srcs - disk)))

# 文风自检
txt = json.dumps(DATA, ensure_ascii=False)
for pat in ["——", "我", "本文", "这篇", "§", '"']:
    c = txt.count(pat)
    if c:
        print("STYLE WARN %s = %d" % (pat, c))

out = os.path.join(ART, "article_data_build.py")
with open(out, "w", encoding="utf-8") as f:
    f.write("# -*- coding: utf-8 -*-\nimport json, os, sys\n_article_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()\n")
    f.write("DATA = ")
    f.write(json.dumps(DATA, ensure_ascii=False, indent=1))
    f.write("\n\nout_path = os.path.join(_article_dir, 'article_data.json')\n")
    f.write("with open(out_path, 'w', encoding='utf-8') as f:\n    json.dump(DATA, f, ensure_ascii=False, indent=2)\n")
    f.write("print('OK', len(DATA['sections']), 'sections')\n")
print("WROTE", out)
