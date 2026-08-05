#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, os, sys

_article_dir = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.getcwd())

DATA = {
    "title": "Multi-Head Attention Residuals（MHAR）：把「对深度的注意力」也变成多头，零参数提升训练损失",
    "summary": [
        {"key": "核心问题", "body": "注意残差用单个共享 query 让子空间读深度历史，子空间对读哪些层的分歧随宽度增长，强制妥协代价上升"},
        {"key": "MHAR 方案", "body": "把路由 query 重塑成 H 个 per-subspace heads，各自对深度历史做独立 softmax——读取变 block-diagonal，零参数、计算可忽略，H=1 精确退化为注意残差"},
        {"key": "结果", "body": "100M/350M/1B 验证损失比标准 Transformer 改善 -0.061/-0.149/-0.140，四方法中每档最佳；头数是 U 形设计轴（H=4/8 平坦最优）"},
    ],
    "lead": [
        "Transformer 经由一条加性残差流跨深度传播信息：每个子层只读最近的状态。**注意残差（attention residuals, Kimi 2025）放松了这一点**——让每个子层通过一个学习的 softmax 去关注深度历史，相当于在深度而非 token 上做注意力，使得深度历史变得可寻址。",
        "但那个「读」用的是**横跨整个宽度共享的单个 query**：它把 N=2L+1 个先前来源打分并塌缩成一个关于深度的 softmax 分布，于是所有 d 个坐标都从同一个深度混合里读取。**这个强制妥协的代价，随子空间对「该读哪些层」的分歧增长而上升，而分歧随模型宽度而增大。**",
    ],
    "sections": [
        {
            "type": "h2",
            "title": "背景：残差流与「对深度的注意力」",
            "paras": [
                "标准 Transformer 里，注意力残差路径把每个子层的输出沿深度累加，后续子层只能读到最近一步的状态——深度历史是被「折叠」进残差流、不可寻址的。",
                "注意残差（attention residuals）改变了这一点：它不是对 token 做注意力，而是**对深度做注意力**——每个子层用一个学习的软权重，从嵌入和之前每个注意力块的状态里取一个加性混合，相当于在深度上做了一次检索。",
                "这使深度历史变得可寻址，但检索粒度是「整个宽度」：一个学习 query 给 N=2L+1 个先前来源打分，塌缩成一个关于深度的 softmax 分布，于是所有 d 个坐标从同一个深度混合去读。",
            ],
            "fig_after": {
                "1": [{"src": "fig00.png", "caption": "Figure 1：深度读取本质上是一次注意力，所以它应该是多头的——注意残差（Kimi 2025）给每个子层喂一个深度历史的加权混合。"}]
            }
        },
        {
            "type": "h2",
            "title": "动机：为什么单个 query 不够",
            "paras": [
                "当所有特征子空间被迫通过**同一个深度分布**去读历史时，妥协就出现了。不同子空间对「该优先读哪些层」的意见往往不一致，而这种分歧随模型宽度增长。",
                "模型的宽度越大，装进同一分布的异质需求就越多——一个分布没法既给浅层特征读低层的语义、又给深层特征读高层的结构。**这是头数（head count）成为真正设计轴的根本原因**，而非可以随便拨的自由旋钮。",
            ],
            "fig_after": {
                "0": [{"src": "fig01.png", "caption": "Figure 2：各方法让当前子层能跨深度读到什么。左：前向堆栈；右：深度读取权重矩阵。"}]
            }
        },
        {
            "type": "h2",
            "title": "MHAR 方法：让深度读也变多头、变块对角",
            "paras": [
                "**Multi-Head Attention Residuals（MHAR）** 的做法很直接：把单个路由 query 重塑成 H 个 per-subspace（每子空间）头，每个头对深度历史拥有**自己的 softmax 分布**。",
                "这样读取矩阵变成**块对角（block-diagonal）**：每个子空间头只读自己想读的深度源，互不干扰。重塑操作**零参数**、计算开销可忽略，而 **H=1 时精确恢复注意残差**——所以 MHAR 是注意残差的严格推广。",
                "论文据此改写路由逻辑（forward 与 backward），并实现了融合路由的 Triton 内核：前向对深度源做 online softmax 并把 RMSNorm 融合进去；反向两遍扫描累积 softmax 耦合项 S 再重算归一化——避免物化中间矩阵，读写更省。",
            ],
            "fig_after": {
                "2": [{"src": "fig02.png", "caption": "Figure 4：H 个路由头确实携带不同的深度-连接：每个头的 token 平均偏差相对于头共识的偏离。"}]
            }
        },
        {
            "type": "h2",
            "title": "头数是真实设计轴：对 H 的 U 形损失",
            "paras": [
                "论文从零训练实验表明，**验证损失对路由头数 H 呈 U 形**：从单头（H=1，即注意残差）下降，进入一个平坦平台，最优在 **H=4 或 H=8** 附近。在 1B 规模同样看到这个平坦最优。",
                "**进一步过度分割（H=16）会收回部分收益**——头太多反而把可共享的深度读取切得太碎。大模型最终采用 H=8。实验还对训练出的路由 query 做直接探针，证实了「学习到的子空间分歧」正是背后的驱动机制。",
                "路由头数 H 与 KV 头数可以解耦：验证损失作为 (路由头 H, KV 头) 的二维网格同样呈平坦低谷，说明 MHAR 的这一新头维度独立于既有 KV 头维度、二者各自可调。",
            ],
            "fig_after": {
                "0": [{"src": "fig03.png", "caption": "Figure 5：1B 规模的头数：H=4–8 的平坦最优。(a) KV=8 行：损失从单头（H=1）落下进入平坦基底。"}],
                "1": [{"src": "fig04.png", "caption": "Figure 5（续）：另一个 panel，展示 H 与 KV 在 1B 规模的行为。"}],
                "2": [{"src": "fig05.png", "caption": "Figure 7：100M 上验证损失作为路由头 H（x 轴）与 KV 头（y 轴）的函数，越低越好。"}]
            }
        },
        {
            "type": "h2",
            "title": "实验：从零训练全面占优",
            "paras": [
                "在去重、质量过滤、偏向 STEM 与代码的 Nemotron-based anneal 语料上从零训练，**MHAR 在 100M、350M、1B 三个规模都比标准 Transformer 验证损失更低**（-0.061、-0.149、-0.140），且在四种方法中每个设定都取得最好结果，收益随规模放大。",
                "训练全程 MHAR 的损失都压在标准基线之下（FineWeb-Edu 上同样复现），说明这不是偶然撞上某个指标，而是稳定的结构收益。在 head 数与 LR 调优、以及多 seed 鲁棒性上，MHAR 相对基线也保持稳定领先。",
                "**训练速度不受损**：融合路由内核（torch.compiled 参考内核 + 自研 fused routing）把训练速度和内存开销拉到与标准 Transformer 相当甚至更快，路由操作本身端到端更快。",
            ],
            "fig_after": {
                "1": [{"src": "fig06.png", "caption": "Figure 8：欠训练的 100M kv×H 网格（web 复现，仅 5K 步）——作为欠训练对照，凸显充分训练下 MHAR 的完整收益。"}],
                "2": [{"src": "fig07.png", "caption": "Figure 11：FineWeb-Edu 上 100M 训练损失（EMA 平滑）：MHAR 全程低于标准基线。"}]
            }
        },
        {
            "type": "h2",
            "title": "结论",
            "paras": [
                "MHAR 的洞察很朴素：**既然深度读取本身是一次注意力，它就该像注意力一样多头**。单头把整个宽度的读取需求压进一个深度分布是浪费——把路由 query 拆成块对角的 per-subspace 头后，每个子空间能读自己想读的深度，且零参数、几乎零计算。",
                "它用「头数是否可调」验证了子空间分歧假说：H 的 U 形损失曲线说明每个子空间确实需要一定的独立读取自由度，但也不能无限切分。对想给现有 Transformer 架构加「深度可寻址性」又不想要代价的团队，这是一条几乎免费的升级路径。",
            ],
        },
    ],
    "conclusion": [
        "Multi-Head Attention Residuals 给「注意力残差」补上了它缺的一环：真正对深度的注意力就该是多头的。单个共享 query 让整宽度的子空间在「读哪些层」上被迫妥协，而 MHAR 用一次零参数的 reshape 把它们解放开，读取变成块对角，H=1 时又精确回到注意残差。",
        "三层证据支持这个设计：损失对 H 的 U 形（H=4 或 8 最优）说明头数是有意义的自由度，直接探针确认正是学习到的子空间分歧在驱动收益，而 H=16 过分割收回部分提升则说明不能无限切。100M/350M/1B 全面优于标准 Transformer（-0.061/-0.149/-0.140）、融合内核让速度不吃亏——一套近乎免费的深度可寻址升级。",
    ],
    "reference_url": "https://arxiv.org/html/2607.27230v2",
    "title": "Multi-Head Attention Residuals（MHAR）：把「对深度的注意力」也变成多头，零参数提升训练损失",
}

out_path = os.path.join(_article_dir, "article_data.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)
print(f"✅ 写入 {out_path} ({len(json.dumps(DATA, ensure_ascii=False))} chars, {len(DATA['sections'])} sections)")
