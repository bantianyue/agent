#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, os, sys

_article_dir = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.getcwd())

DATA = {
    "title": "β-OPSD：找到一个旋钮，把自蒸馏变成可调正则——从策略优化倒推回蒸馏",
    "summary": [
        {"key": "核心洞见", "body": "vanilla OPSD 正是 β=1 的特例，β 从固定的隐式值变成可控正则参数，在锚定 reference policy 与跟随 privileged teacher 之间权衡"},
        {"key": "关键机制", "body": "不直接做高成本高方差的 RL，而是把策略优化的闭式解转化为蒸馏目标：每个 β 在 reference→teacher 路径上选一个 logit 插值目标"},
        {"key": "结果", "body": "数学推理基准上 β-OPSD 一致优于 vanilla OPSD，提升优化稳定性与下游推理性能，且保留 OPSD 的效率"},
    ],
    "lead": [
        "在策略上自蒸馏（OPSD）是提升推理语言模型的有力途径，**但实践上很脆弱**：想让它稳定工作往往需要大量工程调优。论文定位到一个结构性根源：**vanilla OPSD 恰恰是更广策略优化族里 β=1 的一员**，其中 β 加权将学生锚定到 reference policy 的 KL penalty。**这一等价关系把 β 从固定为 1 的隐式值变成可控的正则参数**，得到更一般的表述——它在「紧贴参考策略」与「跟随特权教师」之间做权衡。论文引入 β-OPSD，并把其最优策略推导为 reference policy 与 privileged teacher 之间的几何插值。",
    ],
    "sections": [
        {
            "type": "h2",
            "title": "为什么：OPSD 的脆弱从何而来",
            "paras": [
                "自蒸馏（self-distillation）与在策略自蒸馏（OPSD）的价值在于：不用外部教师或奖励模型，让模型把自己当前的（或历史的）输出当作监督信号，自我提升推理能力。OPSD 尤其吸引人，因为它比完整 RL 简单得多。",
                "但它的可靠性是个问题：**在真实部署中，OPSD 需要大量工程折衷才能稳定工作**，超参稍不对就可能退化或训练崩溃。这类「脆弱」通常是表面症状，背后常有结构性原因。",
                "论文的主张：**OPSD 的脆弱根源于它的正则项被悄悄锁死了**。vanilla OPSD 里学生被一个强度固定的 KL penalty 锚定到某个 reference policy 上——而这个强度恰好对应 β=1。一旦看清楚这一点，问题就从「怎么调 OPSD」变成「β 这只旋钮该怎么转」。",
            ],
        },
        {
            "type": "h2",
            "title": "方法：把 β 变成可调正则",
            "paras": [
                "β-OPSD 的核心是把 β 从固定值还原回**可控的正则参数**。β 加权 KL penalty，让学生不至于离参考策略太远；调整 β 就是在「依赖参考策略的保守性」与「采纳特权教师指导的激进性」之间做连续权衡。",
                "**最优策略是一个几何插值**：β 取不同值时，闭式最优解落在 reference policy 与 privileged teacher 之间的插值路径上。β 越小越贴近教师（激进），β 越大越贴近参考策略（保守）。",
                "这条闭式解路径正是本文的杠杆：既然最优目标是解析已知的，就**不必真的去跑高成本、高方差的 RL 优化**。这正是「从策略优化回到蒸馏」的关键一步。",
            ],
            "fig_after": {
                "1": [{"src": "fig00.png", "caption": "Figure 1: β-OPSD 概览。vanilla OPSD 是更广的 KL 正则化目标在 β=1 时的特例，其最优策略是参考策略与特权教师之间的几何插值。"}]
            }
        },
        {
            "type": "h2",
            "title": "核心机制：用 logit 插值逼近昂贵 RL 的解",
            "paras": [
                "**不直接优化 RL 目标，而是把它闭式解变成蒸馏目标。** 每个 β 值在 reference→teacher 路径上选中一个目标，论文用混合两者的 token 级 logits 高效实现：p̃_βk = softmax((1−1/β_k)·z_ref + (1/β_k)·z_T)。",
                "**概率的几何插值等价于 logits 的线性插值**（到归一化为止）。所以这个自回归的插值目标 p̃_βk，是对序列级最优（Eq.5）一个可处理的局部逼近。每一步训练，学生就最小化当前学生分布与这个调度的插值目标之间的 KL 散度。",
                "这个目标的形式与 vanilla OPSD 完全一致——**唯一区别是固定的教师 p_T 换成了随 β_k 调度的插值目标 p̃_βk**。当 β_k=1 时插值目标退化为特权教师，Eq.12 就还原成标准 OPSD；β_k 越大，目标越贴近参考策略，越保守。",
                "**Return-to-go 信用分配**进一步把每个 token 的更新与序列级目标对齐，给蒸馏目标补充了「这段轨迹整体拿多少奖励、每个 token 该为它负多少责」的信号——这让 token 更新不再只看局部分布匹配，还能传递整条生成路径的回报信息。",
            ],
        },
        {
            "type": "h2",
            "title": "实验：稳定性与推理性能双升",
            "paras": [
                "论文在**数学推理基准**上系统评估 β-OPSD，与 vanilla OPSD 及多种教学蒸馏/策略优化基线对比。核心结论是**一致超出 vanilla OPSD**——不管对哪个 Qwen 模型尺寸、哪种代数、在哪个检查点评估，β 的引入都带来更稳的训练轨迹与更好的最终表现。",
                "消融实验把收益拆解到组件层面：**蒸馏目标**（logit 插值 vs. 直接跟教师）与 **return-to-go 信用分配**各自都有独立的贡献（Tables 2-3）。**插值参考的选择**（Figure 2）和**插值调度**（Table 4）也都被证明会影响最终质量——印证了 β 「旋钮」在这条路径上游刃有余。",
                "**混合学生—教师采样**的实验（Table 6）进一步确认：从 logit 插值分布采样、配合折扣因子 γ=0.99 与重要性采样，能让训练在探索与利用之间取得更好平衡。",
                "把 β 当可调超参还能实际带来工程收益：在默认 200 步训练计划里的 100 步检查点上，β-OPSD 已展现出明显更早的收敛与更高上限，**意味着同样算力下可以更早获得可用模型**。",
            ],
            "fig_after": {
                "2": [{"src": "fig01.png", "caption": "Figure 2: 插值参考选择的影响。所有变体使用相同的 return-to-go 估计器与固定教师权重 w_k=1/β_k=0.5。"}]
            }
        },
    ],
    "conclusion": [
        "β-OPSD 的价值在于它把一个「工程上的脆弱」还原成「理论上的旋钮」：自蒸馏之所以难调，是因为正则强度被悄悄钉死在 β=1；一旦把它放开，整个方法就落入一个可解析、可调度的策略优化—蒸馏家族。",
        "更聪明的是它的执行方式——不硬跑昂贵的 RL，而是抓住策略优化的闭式解，把它铸成 logit 插值的蒸馏目标。这让「从自蒸馏到策略优化、再走回蒸馏」成为一条低成本闭环。β-OPSD 在数学推理上一致优于 vanilla OPSD，稳定性与下游性能双升，却不牺牲 OPSD 引以为傲的效率。",
    ],
    "reference_url": "https://arxiv.org/html/2607.28582v1",
    "title": "β-OPSD：找到一个旋钮，把自蒸馏变成可调正则——从策略优化倒推回蒸馏",
}

out_path = os.path.join(_article_dir, "article_data.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)
print(f"✅ 写入 {out_path} ({len(json.dumps(DATA, ensure_ascii=False))} chars, {len(DATA.get('sections', []))} sections)")
