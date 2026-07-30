#!/usr/bin/env python3
"""
article_data_build.py — OPD Support in Miles
LMSYS 发布 Miles 框架的 On-Policy Distillation 支持。
"""
import json, os, sys

_article_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()

DATA = {
    "title": "LMSYS 在 Miles 框架中集成 On-Policy Distillation：Qwen3.5 自蒸馏实验验证",

    "summary": [
        {"key": "核心功能", "body": "Miles 将 OPD 作为可复用的训练原语集成，支持 sampled-token 和 top-k 两种蒸馏模式，可与 GRPO/PPO 奖励信号组合使用"},
        {"key": "稀疏评分", "body": "稀疏的逐位置候选 token 评分工作流，避免 O(R²K) 稠密 JSON 负载，仅传输 O(RK) 的有效数据"},
        {"key": "实验验证", "body": "Qwen3.5-35B-A3B 自蒸馏：纯 OPD 将回答长度从 18.6k 降至 5.5-6.7k token，DAPO 性能从 0.846 提升至 0.895"},
    ],

    "lead": [
        "LMSYS 团队最近在 **Miles** 框架中集成了 **On-Policy Distillation (OPD)** 作为一等公民功能。这意味着用户现在可以在 Miles 的 rollout 和训练流程中，让 student 模型纯粹跟随 teacher 的指导训练，或者将 teacher 指导与 GRPO/PPO 风格的强化学习目标结合。",
        "与这一功能发布同时，团队在 **单台 8×NVIDIA B200** 节点上使用 Qwen3.5-35B-A3B 进行了自蒸馏实验。结果显示，**纯 OPD 能在不依赖任何任务特定 reward 的情况下，将 teacher 的短推理行为迁移到 base student，同时保持甚至提升 student 的 DAPO 任务性能。**",
    ],

    "sections": [
        {
            "type": "h2",
            "title": "OPD 作为 Miles 的可复用训练原语",
            "paras": [
                "Miles 将 OPD 实现为**加法式 reverse-KL 训练信号**，支持两种重要模式：",
                "**Sampled-token OPD**：teacher 对 student 在每个位置实际采样的 token 进行评分。由于采样具有随机性，这不一定是 student 概率最高的 token。",
                "**Top-k OPD**：在每个位置保留多个候选 token 及其 student logprobs，teacher 对相同候选集评分，Miles 将对齐的 student 和 teacher logprobs 组合成 per-token reverse-KL 信号。这提供了比单 token 采样估计更丰富的 student-teacher 对比。",
                "这种设计使 OPD 成为 Miles 中可复用的训练原语，而非独立的蒸馏路径。用户还可以自定义候选集构建方式和权重策略，使得不同蒸馏方案可以复用相同的 rollout、评分和训练基础设施。",
            ],
            "figs": [
                {"src": "fig1.png", "caption": "Miles 与 OPD 工作流示意图：rollout、teacher 评分、训练三阶段集成。"},
            ],
        },
        {
            "type": "h2",
            "title": "系统优化：稀疏的逐位置 Teacher 评分",
            "paras": [
                "一个关键的系统改进是**稀疏的 student-to-teacher 评分工作流**。",
                "在 OPD 中，student 的 rollout 产生每个位置的 top-k 表格。Miles 精确知道每个位置需要哪些候选 token ID 和 student logprobs 用于 KL 计算，teacher 只需要在对应的因果前缀下对这些候选 token ID 评分。",
                "最初的实现需要构建所有位置 top-k token ID 的全局并集，让 teacher 在每个位置评分这个完整并集。这虽然正确，但产生了 **R × |U| 的稠密中间负载**（R 是响应长度，U 是全局 token ID 并集）。当 |U| 接近 R×K 时，旧路径需要物化和解析 **O(R²K)** 的 JSON 响应，而 OPD 计算只需要 **O(RK)** 的值。",
                "新工作流将稠密的全局路径替换为**稀疏的逐位置候选 token 评分**。Miles 向 teacher 发送每个位置独立的 token ID 表，teacher 只返回每个位置自己候选集的 logprobs。这使 teacher 响应负载与实际的 OPD 计算保持一致，对于长序列推理工作负载尤为重要。",
            ],
        },
        {
            "type": "h2",
            "title": "实验验证：Qwen3.5-35B-A3B 自蒸馏",
            "paras": [
                "团队设计了一个精心控制的自蒸馏实验来验证实现。**Teacher** 先用 RLVR（可验证奖励强化学习）训练，使其用**显著更短的响应**解决 DAPO 数学问题；**Student** 是对应的预 RL 基础 checkpoint。",
                "选择这个设置的原因是：base Qwen student 在原任务上已经很强，直接蒸馏 DAPO 能力几乎看不到变化。因此团队故意在 teacher 中创造了一个可测量的行为变化——**更短但依然有效的推理**——然后测试 OPD 能否将这种行为迁移到尚未表现出该行为的 student。",
                "为了隔离 OPD 的效果，实验运行了**纯蒸馏**，不使用任何任务 reward。",
                "**实验结果**：",
                "- Held-out DAPO 性能从 0.846 提升至 **0.895**",
                "- 采样响应长度从约 18.6k 降至 **5.5k-6.7k token**",
                "- Per-token OPD reverse-KL 从约 0.045 降至 **0.010**",
            ],
            "figs": [
                {"src": "fig2.png", "caption": "Held-out DAPO 性能随评估步数的变化曲线：从 0.846 提升至 0.895。"},
                {"src": "fig3.png", "caption": "采样响应长度随 rollout 步数的变化：首次更新后从 18.6k 骤降至 5.5-6.7k token。"},
                {"src": "fig4.png", "caption": "Per-token OPD reverse-KL 随 rollout 步数的变化：从 0.045 降至 0.010。"},
            ],
        },
        {
            "type": "h2",
            "title": "为什么这对 Miles 很重要",
            "paras": [
                "OPD 的实现让 Miles 能够应用于**可验证任务奖励不够用**的训练场景。许多实际工作流不仅需要优化任务成功率，还需要优化模型行为：推理长度、响应风格、领域特定习惯、与参考模型的分布对齐等。OPD 使 Miles 能够将这些目标表达为 teacher 引导的训练信号，同时保留相同的 rollout 和 RL 训练流水线。",
                "OPD 还提供了**多 teacher 整合**的路径。不同领域的专家 teacher 可以为不同领域或能力提供指导，使单个 student 模型吸收互补行为。因为 Miles 将 OPD 视为可复用的原语，同一个 student 训练流水线可以支持不同的 teacher 和蒸馏方案，而不需要为每个领域单独建立训练系统。",
                "实现还保持了 OPD 的可组合性。用户可以运行纯蒸馏，也可以将 OPD 作为 GRPO/PPO 目标的辅助信号使用，这对 teacher 指导和任务奖励需要协同工作的训练工作流很重要。",
            ],
        },
    ],

    "conclusion": [
        "Miles 现已将 OPD 作为一等公民的训练和 rollout 功能支持。实现包括加法式 reverse-KL 训练、SGLang teacher 评分、top-k OPD、可配置的候选和权重策略、以及稀疏的逐位置 teacher 评分。",
        "在单台 8×NVIDIA B200 节点上的 Qwen3.5-35B-A3B 自蒸馏实验中，**纯 OPD 成功将 teacher 的短推理行为迁移到 base student，held-out DAPO 性能从 0.846 提升至 0.895，响应长度从 18.6k 降至 5.5-6.7k token**。这些初步结果表明，纯 OPD 可以在保持强任务性能的同时，有效迁移有用的行为属性。",
    ],

    "reference_url": "https://www.lmsys.org/blog/2026-07-18-opd-support-in-miles",
}

# ── 写入 article_data.json ──
out_path = os.path.join(_article_dir, "article_data.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)
print(f"✅ 写入 {out_path} ({len(json.dumps(DATA, ensure_ascii=False))} chars, {len(DATA.get('sections', []))} sections)")