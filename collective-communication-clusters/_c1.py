# -*- coding: utf-8 -*-
# part A - intro + TPU topology + All-Gather/RS/AR/A2A (前半) ，图 anchored
# 说明：fig_after key = 该 section 内插入的段索引；图尽量放该图说明 text 紧跟段后

d = None  # placeholder (make 拼接)

def build():
    return [
{"type":"h2","title":"为什么要关心分布式集合通信","paras":[
 "2026 年里，训练与推理 transformer 本质是一个大规模分布式系统问题。要把模型横跨集群切分，靠的是数据并行、张量/模型并行、FSDP、专家并行等——而它们底层都建立在几个少数核心集合通信原语上。数据并行训练要反向时同步梯度，典型用 all-reduce；后面会看到 all-reduce 本身可以拆成 reduce-scatter 再接 all-gather。张量并行与 FSDP 在前向/反向里重度依赖 all-gather 与 reduce-scatter。MoE 里的专家并行则靠 all-to-all。",
 "也许你会问：这些我都听过，可懂它到底有什么用？答案是——若你想推理现代 transformer 系统的性能，终究得推理数据在集群里怎么流动。本文从硬件讲起：先讲 TPU 与 GPU 集群的物理布局，让集合算法落地、更好推理；再进入最常见的集合操作实现。重点放在 ring 风格算法(大消息通信的自然起点)；对小负载，延迟开始主导，tree 风格(log2 步)可能更合适。全文分七部分。",
]},
{"type":"h2","title":"TPU 集群拓扑：Superpods / Slices / DCN / PCIe / ICI","paras":[
 "先讲 TPU，因为它的拓扑更规整，理论上更好推理。TPU 与 GPU 集群最本质差异在最近邻连接：TPU 芯片直接连相邻芯片、每颗有 4 或 6 个最近邻（依代际）：TPU v2/v3/v5e/v6e 用 2D torus(4 邻居)；v4p/v5p/TPU7x(Ironwood)/8t 用 3D torus(6 邻居)。(注：Google 新的推理芯片 8i 偏离此路，改用 high-radix 的 boardfly 分层拓扑，本文不展开。)",
 "2D torus 直觉不难建：它是带周期边界(wraparound)的网格——从左边越界就回到右边，从上越界回到底。TPU torus 是离散网格，可以脑补覆盖在一个甜甜圈上。下图只是找感觉用的。3D torus 也同理：每颗沿 ±x、±y、±z 各有邻居，三个维度边界都环绕。",
]},
# Fig2 图
{"type":"h3","title":"","paras":["","图1 与图2 是最基础的连接直觉（见下）："],"fig_after":{"0":[]}},
{"type":"table","head":["放哪","含义"],"rows":[["TPU chip","计算die中心的存储(VMEM/HBM)最快"],["芯片内","由近及远：SRAM→HBM→ICI→PCIe→DCN"],["芯片间","ICI(片间互联channel) 快; PCIe 到host次之; DCN跨pod最慢"]]},
]
