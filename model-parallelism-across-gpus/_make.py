#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 _trans.json 的译文按原文 Draft.js 结构组装成 article_data.json。
图位真相源：Draft.js atomic 块所在位置（各图紧跟其前一段）。
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
T = json.load(open(os.path.join(HERE, "_trans.json"), encoding="utf-8"))

CODE = '<code style="background:#f3f4f5;padding:2px 5px;border-radius:3px;color:#0F4C81;">{}</code>'
DOT = '<span style="color:#0F4C81;font-size:7px;line-height:1;vertical-align:middle;">●</span>&nbsp;'

IDENTS = [
    "LlamaDecoderLayer.forward()",
    "Worker.determine_available_memory()",
    "tensor_model_parallel_all_reduce()",
    "RowParallelLinear.forward()",
    "ColumnParallelLinear.forward()",
    "MixtralMoE",
]


def tx(i):
    """取块的译文：处理内联代码标记。"""
    s = T[str(i)]
    for ident in IDENTS:
        if ident in s:
            s = s.replace(ident, CODE.format(ident))
    s = re.sub(r"`([A-Za-z_][\w.]*)`", lambda m: CODE.format(m.group(1)), s)
    return s


def bullet(i):
    """无序列表项：小圆点 + 加粗标签。"""
    s = tx(i)
    if "：" in s:
        label, rest = s.split("：", 1)
        if len(label) <= 6:
            s = "**" + label + "**：" + rest
    return DOT + s


def numbered(i, n):
    """有序列表项：染色序号。"""
    num = '<span style="color:#0F4C81;font-weight:bold;">{}</span>&nbsp;'.format(n)
    return num + tx(i)


DATA = {
    "title": "模型并行：把一个模型摊到多块 GPU 上",
    "summary": [
        {"key": "三种拆法",
         "body": "张量并行拆层内的张量与运算，流水线并行把层组放到不同 GPU，多副本则是把完整模型复制多份分别服务。"},
        {"key": "显存账怎么算",
         "body": "权重按 参数量 × 每权重比特数 ÷ 8 估算，再叠加请求状态、激活值、临时工作区、通信缓冲和分配开销；分布式布局未必能均分。"},
        {"key": "先测量再下结论",
         "body": "并行本身不保证加速：通信、同步和流水线气泡都会吃掉收益，必须用固定负载实测响应时间与每个被接受答案的成本。"},
    ],
    "lead": [tx(0), tx(1)],
    "sections": [],
    "conclusion": [],
    "reference_url": "https://x.com/danialhasan/status/2099860796545052830",
}

S = DATA["sections"]


def sec(title):
    S.append({"type": "h2", "title": title, "paras": [], "fig_after": {}})
    return S[-1]


def fig(s, name, caption, idx):
    s["fig_after"].setdefault(str(idx), []).append({"src": name, "caption": caption})


CAP = {k: T[k] for k in ("cap01", "cap02", "cap03", "cap05")}

# --- 需要交付的服务 ---
s = sec(T["2"])
s["paras"] += [tx(3), tx(4), tx(5)]
fig(s, "fig01.png", CAP["cap01"], 2)

# --- API 背后运行着什么 ---
s = sec(T["7"])
s["paras"] += [tx(8), tx(9), tx(10), tx(11)]

# --- 张量在模型中的位置 ---
s = sec(T["12"])
s["paras"] += [tx(13), bullet(14), bullet(15), bullet(16), tx(17), tx(18), tx(19), tx(20)]

# --- 为什么一个 GPU 可能不够用 ---
s = sec(T["21"])
s["paras"] += [tx(22)]
fig(s, "fig02.png", CAP["cap02"], 0)
s["paras"] += [tx(24), tx(25)]

# --- 使用两块 GPU 的三种方式 ---
s = sec(T["26"])
s["paras"] += [tx(27), tx(28), tx(29)]
fig(s, "fig03.png", CAP["cap03"], 2)

# --- 跟随一次计算进入 vLLM ---
s = sec(T["31"])
s["paras"] += [tx(32), tx(33)]
fig(s, "fig04.png", "", 1)
s["paras"] += [tx(35), tx(36), numbered(37, 1), numbered(38, 2), numbered(39, 3), tx(40)]

# --- 通信与等待 ---
s = sec(T["41"])
s["paras"] += [tx(42), tx(43), tx(44)]
fig(s, "fig05.png", CAP["cap05"], 2)
s["paras"] += [tx(46)]

# --- 对比同一助手的多种部署方案 ---
s = sec(T["47"])
s["paras"] += [tx(48), tx(49), tx(50), tx(51), tx(52)]
for n, blk in enumerate(range(53, 58), start=1):
    s["paras"].append(numbered(blk, n))
s["paras"] += [tx(58)]

# --- 决定采用哪种部署 ---
s = sec("决定采用哪种部署")
s["paras"] += [tx(60), tx(61), tx(62)]

# --- 扩展：专家并行 ---
s = sec(T["63"])
s["paras"] += [tx(64)]

# --- 教学示例与参考链接 ---
s = sec("教学示例与参考链接")
s["paras"] += [
    tx(66),
    "Philip Kiely, Inference Engineering: https://www.baseten.co/inference-engineering/",
    "vLLM 并行线性层源码（锁定版本）: https://github.com/vllm-project/vllm/blob/435c96f9dbdd29258cb8e0f433c5b54a00cf6b16/vllm/model_executor/layers/linear.py",
    "vLLM 并行与扩展文档（锁定版本）: https://github.com/vllm-project/vllm/blob/435c96f9dbdd29258cb8e0f433c5b54a00cf6b16/docs/serving/parallelism_scaling.md",
    "Megatron-LM 张量并行设计: https://arxiv.org/abs/1909.08053",
]

DATA["conclusion"] = [
    "**模型并行不是性能开关，而是让选定模型装得下的手段。** 张量并行拆的是层内的张量与运算，流水线并行切的是层组，多副本复制的是整个模型。三种做法的代价都落在通信、同步和等待上，收益只能由实测给出。",
    "工程上最容易被漏掉的是显存账和流水线气泡：权重按参数量 × 每权重比特数 ÷ 8 估算，还要计入请求状态、激活值、工作区与通信缓冲；各阶段耗时不均、启动和排空造成的空转，并行度越高越难察觉。",
    "对做推理服务的人来说，先把固定负载、固定质量标准的对照实验搭起来，再决定是否把模型拆到多卡。模型能放进单卡，而独立副本已经够用时，拆开只会更贵。",
]


def main():
    # 自检：fig_after 越界 + 段落/图计数
    nfig = 0
    npara = 0
    for s in S:
        n = len(s["paras"])
        npara += n
        for k in s.get("fig_after") or {}:
            assert int(k) < n, f"fig_after 越界: {s['title']} key={k} paras={n}"
            nfig += len(s["fig_after"][k])
    assert len(DATA["summary"]) == 3, "summary 必须 3 条"
    print(f"sections={len(S)} paras={npara} figs={nfig}")
    assert nfig == 5, nfig
    blob = json.dumps(DATA, ensure_ascii=False)
    assert "——" not in blob and "—" not in blob, "含破折号"
    json.dump(DATA, open(os.path.join(HERE, "article_data.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print("article_data.json 已写入")


if __name__ == "__main__":
    main()
