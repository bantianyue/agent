#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, os, sys

_article_dir = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.getcwd())

DATA = {
    "title": "LSPO：为「悬崖提示」找回丢失的 RL 梯度——零奖励 prompt 上用小 LoRA 当临时脚手架",
    "summary": [
        {"key": "核心问题", "body": " cliff prompt（组内所有采样都失败）上组归一化优势恒为零，GRPO 在你的能力前沿上产生不了任何梯度"},
        {"key": "LSPO 机制", "body": "检测 cliff→在真实解上 SFT 拟合小 LoRA adapter→用 base+adapter 重采样→把成功完成拼回 RL batch（带重要性采样校正）→只对 base 做 GRPO，adapter 丢弃"},
        {"key": "关键结果", "body": "DeepMath-103K+DeepSeek-R1-Distill-Qwen-1.5B 上 16 格 15 胜 1 平，平均 +3.8 点，AIME24/pass@4 最高 +10.7"},
    ],
    "lead": [
        "从可验证奖励学习（RLVR）已成为从大模型引出数学推理的主流配方。但它有一个结构性的盲区：**在「cliff」提示上——即组内每个采样 rollout 都失败的提示——组归一化优势恒为零，GRPO 恰恰在模型能力前沿的这些提示上产生不了任何梯度。** NVIDIA 的 LoRA Scaffolded Policy Optimization（LSPO）用采样时机制找回这份丢失的梯度：每个 RL 步检测 cliff 提示，在它们 ground-truth 解上用一个简短的监督步骤拟合小 LoRA adapter，用 base+adapter 模型重采样这些 cliff，把现在成功的完成以重要性采样校正拼回 RL batch，再只对 base 做一步 GRPO；adapter 只接收监督梯度并在 checkpoint 时丢弃，产出纯 base 模型。在 DeepMath-103K 上、DeepSeek-R1-Distill-Qwen-1.5B、n=5 配对种子的匹配 1000 步报告时窗下，LSPO 的 5 种子均值在全部 16 个（基准, pass@k）格中匹配或超过 DAPO 基线（15 胜 1 平），平均提升 +3.8 点。",
    ],
    "sections": [
        {
            "type": "h2",
            "title": "cliff 问题：能力前沿上的梯度盲区",
            "paras": [
                "从可验证奖励学习（RLVR）通过让模型在可验证（例如数学答案）奖励上优化，已成为从大模型引出数学推理的主流配方（GRPO 及 DAPO 配方）。GRPO 在一个组内归一化每个 rollout 的优势，有效降低 reward 模型的方差，数学推理上非常成功。",
                "但当这个归一化因子出错时会怎样？考虑一个模型还不会做的提示——它的**能力前沿**。组内每个采样 rollout 都错了：奖励为零。此时 GRPO 的组归一化优势恒为零，**policy gradient 是零**。也就是说，恰恰是在最需要学习信号的提示上——模型正卡在能力瓶颈的提示——GRPO 给不出任何梯度。论文把这称为 cliff 问题：这些 cliff 提示横在模型前，模型无法翻越，RL 也就没有信号引导它翻越。",
                "对数学推理，cliff 的出现不只是毛刺，而是常态：组越大、模型越接近能力边界，出现至少一个«全部失败»组的概率越高。这让 RLVR 的训练在进展最需要的地方悄悄减速。",
            ],
            "fig_after": {
                "2": [{"src": "fig00.png", "caption": "Figure 1: LSPO 的 cliff-rescue 机制。(1) 在 cliff prompt p 上，base 策略 π 的全部 K 个 rollout 都失败（红），组奖励和为零、标准 GRPO 没有学习信号。(2) 一个可训练 LoRA adapter φ_LoRA 与（冻结的）base π 组合，在数据集 ground-truth 轨迹上经 SFT 拟合。(3) 组合策略 π+φ_LoRA 下，同一提示的部分 rollout 现在通过了验证器（绿），cliff 被超越；成功 rollout 作为正样本拼进 GRPO batch。(4) GRPO 步在同 batch 上、并把 LoRA 分支 scale 置 0（灰虚线）运行，于是 RL 梯度（紫点线）只落在 π 上；φ_LoRA 不收 RL 梯度，下一步前被重置。"}]
            }
        },
        {
            "type": "h2",
            "title": "方法：采样时临时脚手架",
            "paras": [
                "LSPO 是**采样时机制**，包裹现有 policy-gradient RL loop（这里是用 DAPO 风格配方的 GRPO）。它专门在 cliff 提示上恢复梯度。核心思路：**给模型挂一个小的低秩（LoRA）adapter 作为临时脚手架**——它只在 cliff 提示自身的 ground-truth 解上做监督微调，仅用于重采样这些提示，然后被丢弃。",
                "关键设计：**成功完成被拼回 RL batch，从而恢复组内奖励方差和 RL 梯度；但真正更新交付物的梯度只进入 base 模型。** 具体是否、以及如何分离这两条梯度路径，决定了该方法是否站得住脚。",
                "**每个 RL 步**（Algorithm 1）：① 检测 cliff 提示；② 用这些提示的 ground-truth 解做一步 SFT 拟合 LoRA adapter；③ 用 base+adapter 组合策略对 cliff 重采样；④ 把现在成功的 rollout 用重要性采样校正拼回 RL batch；⑤ 只对 base 做一步 GRPO（adapter 分支 scale=0，不收 RL 梯度）；⑥ 丢弃 adapter，checkpoint 只保留 base 模型。",
            ],
        },
        {
            "type": "h2",
            "title": "渐变路由：adapter 与 base 各收各的梯度",
            "paras": [
                "LSPO 的核心工程细节是**梯度路由**：batch 里同时有 adapter 和 base 两条参数路径，如何让 RL 梯度只落 base？做法是在做 GRPO 步时把 LoRA 分支的 scale 设为 0（等价于 base 单独的 forward），于是 RL 的 policy gradient 纯粹作用在 base 上。",
                "同时，adapter 只接收监督梯度——它在 SFT 拟合那一步被训练，从不接收 RL 梯度。**这样两条梯度在数学上被干净地分离**：adapter 的唯一作用是生成本来 base 做不到的成功完成，把这些完成当作«脚手架产物»送给 base 学；adapter 自身不持有任何 RL 训练信号。",
                "因为这个 clear 分离，checkpoint 时的模型是纯 base（无 LoRA 分支），**推理时零额外成本**——没有需要额外保存或加载的 adapter 权重，也不改变部署 footprint。这正是 LSPO 与那些把 adapter 当作长期技能库的工作（如最近引入权重记忆的 agent 方法）的本质区别：LSPO 的 adapter 是即用即弃的临时工具。",
            ],
        },
        {
            "type": "h2",
            "title": "重要性采样校正：离策略数据没有偏置",
            "paras": [
                "重采样的成功 rollout 来自 base+adapter 策略，而真正的 policy gradient 更新跑在 base 上——**这是 off-policy 数据**。直接用会引入分布偏置。LSPO 引入**重要性采样校正**补上这个缺口：把 adapter 生成的完成按其在新旧策略下的概率比（importance weight）重新加权，再并入 GRPO 批。",
                "直觉上：一个 adapter 恰好偷到的完成，如果它在 base 下几乎不可能、却一路生成成功，其贡献要按 base 下的概率缩放，避免模型被个别高杠杆样本误导。校正后的 gradient 估计在期望上无偏，保证 base 学到的不是 adapter 特定行为，而是可迁移的推理改进。",
                "与更重的方法相比，重要性采样本质上是轻量的：**没有额外的 critic、不需要 rollout 重放缓冲、不引入训练时的目标网络**，只在 batch 组装时多算一个概率比权重。这让 LSPO 与标准 GRPO 训练的工程改动面非常小。",
            ],
        },
        {
            "type": "h2",
            "title": "实验：16 格 15 胜 1 平",
            "paras": [
                "实验在 **DeepMath-103K** 上、**DeepSeek-R1-Distill-Qwen-1.5B** 训练，n=5 个配对种子、匹配的 1000 步报告时窗下对比 DAPO 基线。16 个（基准, pass@k）格覆盖 AIME24、AIME26、MATH500 等数学基准乘以 pass@1/4/16 等采样预算。",
                "**主结果（peak-vs-peak）**：LSPO 的 5 种子均值和 DAPO 基线相比，16 格里 **15 格严格胜出、1 格打平**，没有任何一格倒退。平均提升 +3.8 点。增益在采更多样本时最明显：**AIME24/pass@4 提升 +10.7 点，AIME24 和 AIME26 在 pass@16 各 +6.7 点，MATH500/pass@1 +2.4 点**。",
                "这组数字说明 LSPO 不是靠单一配置侥幸：**提升在多数基准、多种 pass@k 上一致出现**，且不牺牲任何已到手的性能。cliff-conversion 分析进一步确认，增益确实来自被挽救的 cliff 提示——adapter 让原本全失败的组产生成功样本，成功样本又转化为 base 的可验证改善。",
                "**局限**：LSPO 假设能访问 ground-truth 解（用于 SFT 拟合 adapter）——这符合数学推理这类可验证奖励的设置，但对难以获得解的地带不适用；同时它的收益依赖 cliff 在训练批次里出现的频率，cliff 太少则收益有限。论文谨慎地把这些框定为 scope 限制而非缺陷。",
            ],
        },
    ],
    "conclusion": [
        "LSPO 对症的是 RLVR 一个常见却常被忽视的结构盲区：当一组采样全失败时，组归一化优势归零，GRPO 在模型该进步的地方静默失速。它的解药不来自更复杂的 RL 算法，而是一条采样时的分工——**临时 LoRA adapter 在 cliff 上艰难翻越、把成功样本交给 base 去学，然后自己退场**。",
        "这份彻底的参数分工让「拿回梯度」变得工程上几乎零成本：adapter 即用即弃、checkpoint 只留纯 base、推理无额外开销，而重要性采样保证 off-policy 数据不引入偏置。实验在 16 格上 15 胜 1 平、平均 +3.8 点，且增益集中在最难的 AIME 基准与更大采样预算上，正是 cliff 最密集、最该被救的地方。它不推翻 RLVR，而是在训练步骤里加一根可以随时抽走的脚手架。",
    ],
    "reference_url": "https://arxiv.org/html/2607.27787v1",
    "title": "LSPO：为「悬崖提示」找回丢失的 RL 梯度——零奖励 prompt 上用小 LoRA 当临时脚手架",
}

out_path = os.path.join(_article_dir, "article_data.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)
print(f"✅ 写入 {out_path} ({len(json.dumps(DATA, ensure_ascii=False))} chars, {len(DATA.get('sections', []))} sections)")
