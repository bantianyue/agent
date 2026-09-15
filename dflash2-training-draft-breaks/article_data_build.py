#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, os, sys

_article_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()

CODE = '__CODE__text::context       "Could you help with this task?"\n\nplausible A   I        can      assist   you      with     that     now\nplausible B   I        can      lend     a        hand     with     this\n\nproposal      I        can      assist   a        hand     with     this\ntarget        I        can      assist   you      with     that     now\nverification  \u2713        \u2713        \u2713        \u2717        \u00b7        \u00b7        \u00b7'

TBL = {
    "head": ["方法", "接受长度", "加速比"],
    "rows": [
        ["DFlash", "3.009", "2.279×"],
        ["DFlash2", "3.591", "2.514×"],
        ["DFlash2 + D-PACE", "3.824", "2.666×"],
        ["DFlash2 + Draft-OPD", "4.752", "3.259×"],
        ["DFlash2 + D-PACE + Draft-OPD", "<strong>4.887</strong>", "<strong>3.341×</strong>"],
    ],
}

DATA = {
    "summary": [
        {"key": "核心结论", "body": "在 DFlash2 基础上改训练配方：平均接受长度从 3.591 提到 4.887，端到端加速从 2.514× 提到 3.341×（比 DFlash 高 47%）"},
        {"key": "D-PACE", "body": "把固定的指数衰减权重换成由可微接受长度代理导出的权重，让位置权重随当前草稿的置信度变化"},
        {"key": "Draft-OPD", "body": "从真实验证边界（锚点）训练；被接受的 token 用前向 KL，被拒绝的用反向 KL，重压草稿最自信却被打回的位置"},
    ],

    "lead": [
        "三周前 DFlash2 刷新了投机解码的最好成绩。作者先在最延迟敏感的部署里把它的机制逆出来，再把训练配方往前推了一步。",
        "两处训练改动把草稿的平均接受长度从 3.591 拉到 4.887、端到端加速从 2.514× 拉到 3.341×。两个改动的思路一致：围绕「草稿在哪一步不再被接受」来组织训练。",
    ],

    "sections": [
        {
            "type": "h2",
            "title": "投机解码的基础",
            "paras": [
                "投机解码把一个小而快的草稿模型与目标模型配成一对：草稿先提出未来若干个 token，目标一次性给整个提案打分，接受其中最长的有效前缀，在第一个被拒绝的位置采样一个替换 token，然后开始起草下一轮。",
                "看一个很能说明问题的例子：",
                CODE,
                "在这个例子里目标接受了前 3 个 token。只要「起草加验证」合计比目标自己生成这几个 token 更快，我们就省下了延迟。",
                "注意这个例子里的草稿把两条各自都合理的续写拼接在了一起。下面会说明并行起草为什么会造成这种失败，以及 DFlash2 是如何避免它的。",
            ],
            "fig_after": {
                "3": [{"src": "fig01.jpg", "caption": "图 1：投机解码示例。草稿把两条各自合理的续写拼在一起，目标只接受前三个 token，其余被拒绝"}],
            },
        },
        {
            "type": "h2",
            "title": "DFlash：一次起草整块",
            "paras": [
                "早期的投机解码草稿模型是自回归地构造提案的：目标固然可以并行验证一整块，但草稿必须先逐个生成每个提议 token。",
                "DFlash 去掉了这个内循环，改用稍深一些的块扩散（block-diffusion）模型一次性预测整块草稿。打破自回归链让起草快得多，但也可能让模型把不同的合理序列交织在一起，就像上面的例子那样。",
            ],
        },
        {
            "type": "h2",
            "title": "DFlash2：把并行草稿重新连起来",
            "paras": [
                "因为 DFlash 并行地选择每一个位置，每个 top-1 token 在选出时并不知道草稿里更早的位置选了什么。这正是「assist」和「a」各自在自己的位置上看起来都合理、合在一起却成了错误续写的原因。",
                "正确的 token 往往仍然留在 DFlash 排名较高的备选里：在上面的例子里，即使「a」在那个位置拿下了 top-1，「you」的分数可能也不错。DFlash2 的做法是在每个位置保留多个候选，并加一个候选选择器，为相邻选择之间的契合程度打分。",
                "选择器对每一对相邻候选这样打分：Sₜ(a,b) = Uₜ(b) + ⟨A(a) ⊙ H(hₜ), B(b)⟩，其中 a 是前一个候选、b 是当前候选，Uₜ(b) 是 b 的原始 DFlash 分数，第二项则在当前上下文里评估两者之间的转移。这让选择器能抬高「assist → you」的分数、压低「assist → a」的分数。所有相邻对都并行打分，然后在这些分数上做一次短走查，选出穿过候选格（candidate lattice）的最终路径。",
                "DFlash2 还在每个注意力和前馈层周围加了一个两抽头的动态深度卷积：Conv(x)ₜ = k(t,0) ⊙ xₜ + k(t,1) ⊙ x(t−1)，也就是把每个位置的隐状态与前一个位置的隐状态混合。候选选择器改善最终的 token 选择，而卷积帮助主干在这些选择做出之前就表示好局部依赖。",
            ],
            "fig_after": {
                "1": [{"src": "fig02.jpg", "caption": "图 2：DFlash2 在每个位置保留多个候选，用候选选择器给相邻选择的契合度打分，再从中选出最终路径"}],
            },
        },
        {
            "type": "h2",
            "title": "D-PACE：让损失衰减适配每一份草稿",
            "paras": [
                "DFlash 给每个位置从同一条指数衰减曲线分配权重。越靠前的位置权重越大，因为一个早期错误会作废更多的后缀，但这条曲线无法对当前这份草稿作出反应：无论前三个 token 几乎板上钉钉，还是这份提案本来就不太可能活到那里，第四个位置拿到的权重都是一样的。",
                "D-PACE 用从「可微的接受长度代理」导出的权重替换掉这条静态曲线。设 qᵢ 是草稿在位置 i 上给目标 token 的概率，这个代理就是 S = Σ(m=1..B) Π(i=1..m) qᵢ = q₁ + q₁q₂ + q₁q₂q₃ + … + q₁q₂…q_B。每个乘积估计的是草稿能活过该位置的概率；对这个代理求导，就能给每个 token 记上与「依赖它的后续位置」相应的功劳。D-PACE 还会把权重里的置信度做平滑，避免某一个困难 token 把后面所有梯度抹掉。把平滑后的置信度记作 q̃，先计算 Pₘ = Π(i=1..m) q̃ᵢ。",
                "位置 j 的权重就是这个和：wⱼ = Σ(m=j..B) Pₘ = Pⱼ + P(j+1) + … + P_B。这个权重乘在位置 j 上标准的 token 级交叉熵损失上。",
                "权重在整块内仍然递减，因为 wⱼ − w(j+1) = Pⱼ，置信度改变的是每一级的步长。对上面画出的那条曲线，阶梯跨过「I can assist」，并在「you」处变陡，几乎没有权重落在被作废的后缀上。换成另一份草稿，就会得到另一条阶梯。",
            ],
            "fig_after": {
                "3": [{"src": "fig03.jpg", "caption": "图 3：D-PACE 的权重阶梯。阶梯跨过「I can assist」、在「you」处变陡，被作废的后缀几乎不占权重"}],
            },
        },
        {
            "type": "h2",
            "title": "Draft-OPD：从真实的验证边界训练",
            "paras": [
                "标准 DFlash 从固定的、由目标生成的回复里随机采样位置来训练。但推理时的起始位置并不是随机的：每一份新草稿都从上一次提案在目标验证之后停下的地方开始。",
                "这些起始位置被称为锚点（anchor）。随机锚点可能落在回复里一个很普通的位置，不管这个状态对当前草稿是否困难。它的覆盖面很广，却没有捕捉到草稿自身产生的那些块与验证边界。",
                "Draft-OPD 在目标辅助解码的过程中把这些边界收集起来：每个锚点都与草稿实际提出的提案、以及随后的验证结果配对，其中包含第一个被拒绝的 token 和被作废的后缀。这样训练就集中在当前正在限制接受长度的那些错误上，同时由目标把最终的 rollout 保持在自己的分布上。",
                "接着上面那个例子：Draft-OPD 会保存「I」之前的锚点，连同提案「I can assist a hand with this」。在目标接受「I can assist」、把「a」换成「you」之后，下一个锚点就落在「you」紧后面，也就是下一个投机块的起点。于是训练可以重放那份失败的提案，而不必从随机采样的回复位置去重建续写。",
            ],
        },
        {
            "type": "h2",
            "title": "被接受的 token 用前向 KL，被拒绝的用反向 KL",
            "paras": [
                "重放一份提案，会同时暴露目标接受的部分与草稿失败的那个点。这两个区域需要不同的目标：在已验证的 token 上保持目标的分布，在拒绝之后压制草稿那些没有依据的选择。",
                "把目标分布记作 p、草稿分布记作 q。Draft-OPD 在被接受的 token 上用前向 KL，即 KL(p ‖ q)，让草稿在验证成功的那些状态上对齐目标所支持的 token 范围。",
                "在被拒绝的 token 上，Draft-OPD 用反向 KL，即 KL(q ‖ p)。这会给那些「草稿给了高概率、却被目标拒绝」的 token 更大压力：第一个被拒绝的 token 得到最强的纠正，权重再沿后缀衰减，因为后面的 token 都是第一个错误的产物。",
            ],
        },
        {
            "type": "h2",
            "title": "实验结果",
            "paras": [
                "下面是一个受控的小规模消融，报告的是平均接受草稿长度，以及相对同一个目标模型不做投机解码时的加速比。",
            ],
            "table": TBL,
            "fig_after": {},
        },
        {
            "type": "h2",
            "title": "结论与引用",
            "paras": [
                "完整配方达到平均接受长度 4.887、加速 3.341×。这个加速比比起点的 DFlash2 基线高 33%，比 DFlash 高 47%。D-PACE 与 Draft-OPD 改进的是训练配方的不同部分：D-PACE 改变每份草稿内部位置的加权方式，Draft-OPD 改变模型在哪些草稿状态上训练。",
                "投机解码仍然是降低推理延迟最有力的杠杆之一。DFlash2 把架构往前推了一步，而这里的工作说明训练配方还能把它再往前推。",
                "[1] Inco AI. DFlash2: Keep Drafting Parallel. 2026. https://inco.ai/blog/dflash2/",
                "[2] Chen et al. DFlash: Block Diffusion for Flash Speculative Decoding. ICML, 2026. arXiv:2602.06036",
                "[3] Wu et al. D-PACE: Dynamic Position-Aware Cross-Entropy for Parallel Speculative Drafting. 2026. arXiv:2605.18810",
                "[4] Lei et al. Draft-OPD: On-Policy Distillation for Speculative Draft Models. 2026. arXiv:2605.29343",
            ],
        },
    ],

    "conclusion": [
        "**这次改进的共同线索是把训练对准「草稿失效的那一刻」。** D-PACE 让每个位置的损失权重由当前草稿的真实置信度决定，而不是套一条固定曲线；Draft-OPD 直接从目标验证时的锚点出发训练，让模型反复面对自己实际犯过的错。",
        "结果也说明改训练配方的回报依然可观：架构没动，仅这两处调整就把接受长度从 3.591 提到 4.887、端到端加速从 2.51× 提到 3.34×。在投机解码这类已经相当成熟的加速手段上，数据与损失的组织方式仍然是最值得抠的地方。",
    ],

    "reference_url": "https://x.com/NicholasLiu77/status/2098097570262491555",
    "title": "DFlash2 训练配方再优化：接受长度 3.591→4.887、加速 2.51×→3.34×",
}

out_path = os.path.join(_article_dir, "article_data.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)
print("OK wrote", out_path, len(DATA.get("sections", [])), "sections")
