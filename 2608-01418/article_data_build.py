#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, os, sys

_article_dir = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.getcwd())

DATA = {
    "title": "PNPO：把累积重要性比换成「前缀几何平均」，让 LLM 强化学习更敢复用 rollout",
    "summary": [
        {"key": "核心问题", "body": "LLM RL 里 rollout 生成最贵，复用一批 rollout 做多次更新能摊薄成本，但后面的更新越来越 off-policy"},
        {"key": "PNPO 方案", "body": "用沿每个因果前缀的似然比几何平均替换精确累积比值，保留每个位置的前缀依赖，同时压缩 log-weight 尺度，避免乘积形式带来的动态范围问题"},
        {"key": "结果", "body": "长上下文数学推理上，4-epoch 复用 regime 下 PNPO 在每个 benchmark 拿最高 Avg@32，三基准峰值均值 50.24、比 GSPO 高 3.00 分，且更省 rollout"},
    ],
    "lead": [
        "自回归 rollout 生成是 **LLM 强化学习里最主要的计算成本**。把每一批 rollout 复用来做额外的 learner 更新，能把这份成本摊薄——但代价是后面的更新会随着 learner 偏离行为策略而**越来越 off-policy**。",
        "这篇工作研究 **Prefix-Normalized Policy Optimization（PNPO）**：不追求精确但动态范围难控的累积重要性比，而是用**沿每个因果前缀的似然比几何平均**来估计权重。在受控的长上下文数学推理实验里，当 rollout 被复用 4 次（4 epochs）时，PNPO 在每个 benchmark 都拿到最高 Avg@32，三基准峰值均值比 GSPO 高 3.00 分。",
    ],
    "sections": [
        {
            "type": "h2",
            "title": "问题：rollout 复用的 off-policy 成本",
            "paras": [
                "在 token 级，精确的 off-policy 校正必须同时考虑**当前 action 和到达其前缀的概率**。累积重要性比（cumulative importance ratio）正是提供了这份校正——但它是乘积形式，随序列长度指数级变化的动态范围，对优化极不友好。",
                "于是出现一个张力：要不要做因果前缀校正？做，权重尺度过大不稳；不做（只看当前 token），又丢失了策略漂移的累积路径信息。",
                "这正是 PNPO 要调和的核心矛盾：**既要前缀依赖，又要可控的权重尺度**。",
            ],
        },
        {
            "type": "h2",
            "title": "PNPO：前缀似然比的几何平均",
            "paras": [
                "PNPO 的做法是把累积比值换成**几何平均**：位置 t 的权重 `w_t^PN = exp((1/t) Σ_{k=1..t} log r_k)`——沿因果前缀到位置 t 的似然比的几何平均。",
                "这里的 **1/t 次幂同时调节当前 token 比和所有前序比**：既保留了每个位置"这个 token 以及走到它的前缀"这一因果依赖，又把 log-weight 尺度压实，避免乘积累积带来的失控动态范围。",
                "对比一下现有选项（Figure 1 顶部）：**local log-ratio** 只看当前 token；**精确累积 log-ratio** 对整条前缀求和（尺度大）；**GSPO** 把整个响应的均值比广播到每个位置（丢了前缀位置差异）；而 **PNPO** 在每个位置用的是对应的**前缀均值**——前缀信息保留、全响应共享信息也保留，尺度却可控。",
            ],
            "fig_after": {
                "1": [{"src": "fig00.png", "caption": "Figure 1：各类权重方法的支持范围与 log-weight 尺度。顶部：local log-ratio 只含当前 token；精确累积 log-ratio 对前缀求和；GSPO 把整响应均值比广播到每个位置；PNPO 每个位置用对应的前缀均值。"}]
            }
        },
        {
            "type": "h2",
            "title": "实验：长上下文数学推理的两个 off-policy regime",
            "paras": [
                "论文在控制的长上下文数学推理任务上评测，基准含 **AMC 2023、AIME 2024、AIME 2025**。训练时每步采样 256 个 prompt × 8 个 response（共 2048 条 response），并用每批 rollout 做 **1 次或 4 次策略更新**（1/4 policy-update epochs）来诱导两种不同的 off-policy regime。",
                "结果一：**1 epoch 时 PNPO 并不持续优于 GSPO**——off-policy 程度不高时，前缀几何平均的优势不明显，两种权重都够用。",
                "结果二：**4 epochs 时 PNPO 在每个 benchmark 都取得最高的 Avg@32**。三个单独挑出的 benchmark 峰值的无权重均值是 **50.24，比 GSPO 高 3.00 分**——off-policy 越重，PNPO 的前缀校正越有价值。",
            ],
            "fig_after": {
                "1": [{"src": "fig01.png", "caption": "Figure 2：1 与 4 PPO epochs 下的评估与训练动态。(a,b) macro Avg@32（AMC 2023、AIME 2024、AIME 2025 的均值）。"}]
            }
        },
        {
            "type": "h2",
            "title": "rollout 复用更高效",
            "paras": [
                "在**匹配的 2,400 次 update 预算**下，4-epoch PNPO 达到最终 macro Avg@32 49.66。更重要的是，它用**四分之一的新生成 response** 就达到了相当的最终性能——说明在重 off-policy regime 下，PNPO 让每一批 rollout 都被更充分地榨干价值。",
                "Figure 3 用首达时间估计了达到平均 rollout reward 0.25 的耗时：在各自 regime 的每步耗时节拍下，PNPO 的推进同样更具优势。",
                "这对训练成本的意义很直接：**想省 rollout 生成的钱，就得容忍更 off-policy 的 reuse，而 PNPO 正是为这种高复用 regime 设计的权重方法**。",
            ],
            "fig_after": {
                "1": [{"src": "fig02.png", "caption": "Figure 3：达到平均 rollout reward 0.25 的估计耗时。首达时间由居中 11 步奖励轨迹计算。"}]
            }
        },
        {
            "type": "h2",
            "title": "结论",
            "paras": [
                "PNPO 的要点是把「精确但尺度爆炸」与「近似但丢前缀」之间，找到了一个平衡点：**前缀似然比的几何平均**。它在每个位置既算上走到这里的因果前缀，又把权重尺度压住，让高复用、高 off-policy 的训练稳定。",
                "对跑 LLM RL 的团队，如果 rollout 生成是瓶颈、想靠复用省成本，PNPO 是 GSPO 之外一个更适应少生成、多迭代场景的选择——尤其在 4-epoch 这类重 off-policy regime 下优势明确。",
            ],
        },
    ],
    "conclusion": [
        "PNPO 用一个很小的改动解决了 rollout 复用的大问题：把累积重要性比的权重换成沿因果前缀的几何平均。它不是要替代低 off-policy 场景里的 GSPO（1 epoch 时两者打平），而是在**高复用、高 off-policy** 的场景拿回优势——4-epoch 下一口气在每个 benchmark 做到最高、比 GSPO 高 3.00 分。",
        "真正值得读的是那层取舍：前缀依赖和权重尺度不可兼得，PNPO 选择了折中。对把 rollout 复用看成省钱手段的团队，这套「写在前缀均值里、用起来跟 GSPO 一样顺手」的方法，等于在同样的预算里拿到更多有效更新。",
    ],
    "reference_url": "https://arxiv.org/abs/2608.01418v1",
    "title": "PNPO：把累积重要性比换成「前缀几何平均」，让 LLM 强化学习更敢复用 rollout",
}

out_path = os.path.join(_article_dir, "article_data.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)
print(f"✅ 写入 {out_path} ({len(json.dumps(DATA, ensure_ascii=False))} chars, {len(DATA['sections'])} sections)")
