#!/usr/bin/env python3
"""
article_data_build.py — Multi-Turn On-Policy Distillation with Prefix Replay
arXiv 2607.04763 — 精简编译，论文类 60% 阈值。遵守图文原则、简洁原则、结论首句原则。
"""
import json, os, sys

_article_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()

DATA = {
    "title": "ReOPD：用前缀重放实现多轮 Agent 在线策略蒸馏，无需环境即可端到端训练",

    "summary": [
        {"key": "核心问题", "body": "多轮 Online On-Policy Distillation（OPD）每轮更新都需要完整的 student rollout + teacher query，环境成本极高"},
        {"key": "核心方法", "body": "ReOPD（Replayed-Prefix OPD）：复用预收集的 teacher 轨迹作为前缀，student 只在该前缀上生成下一步动作，彻底解耦环境依赖"},
        {"key": "实验结果", "body": "ReOPD 在三个复杂 Agent 任务上匹配或超越全在线 OPD，环境成本降低至零，student 训练仅需单次推理"},
    ],

    "lead": [
        "知识蒸馏是让小模型（student）学习大模型（teacher）能力的有效方法。但在多轮交互式 Agent 任务中，Online On-Policy Distillation（OPD）面临一个棘手问题：每次更新都需要 student 在与环境实时交互的同时生成完整轨迹，teacher 再对这些轨迹进行标注——环境必须始终在线，成本极高。",
        "ReOPD（Replayed-Prefix On-Policy Distillation）提出了一种简洁的解决方案：从预收集的 teacher 轨迹池中取一段前缀，student 只在该前缀上生成下一步动作，teacher 提供该步的监督信号。环境只需在收集 teacher 数据时存在，student 训练时完全离线。在数学推理、搜索、多环境三个场景中，ReOPD 在匹配或超越全在线 OPD 的同时，将环境成本降至零。",
    ],

    "sections": [
        {
            "type": "h2",
            "title": "多轮 OPD 的困境",
            "paras": [
                "在多轮交互式环境中，Agent 在与环境交互时产生多步决策历史 Ht=(O1,A1,O2,A2,…,At−1,Ot)。OPD 要求 student 在每个更新步重新与环境交互，生成完整轨迹后 teacher 再标注——环境必须持续运行，student 需要多次环境调用。",
                "ReOPD 的核心想法是：不再让 student 每次都从头与环境交互，而是从预收集的 teacher 轨迹中取一段前缀作为上下文，student 只前向推理一步，teacher 提供该步的蒸馏目标。下图展示了在线 OPD 与 ReOPD 的对比：",
            ],
            "figs": [
                {"src": "aopd.png", "caption": "ReOPD vs 在线 OPD 对比。在线 OPD 中环境始终在线，ReOPD 仅在收集 teacher 数据时需要环境。"},
            ],
        },
        {
            "type": "h2",
            "title": "ReOPD 的核心机制",
            "paras": [
                "ReOPD 将多轮 OPD 简化为一个设计选择：在每个步骤 t，选择一个有效的「前缀分布」πt，在 student 相关性和 teacher 可靠性之间取得平衡。",
                "对于监督步骤 t，前缀 ht=(O1,A1,…,Ot) 取自预收集的 teacher 轨迹——每一步动作和观察都是 teacher 的记录。在该前缀上，student 生成自己的动作，teacher 的记录条件概率 πT(·|x,ht) 提供蒸馏目标。遍历轨迹中的所有 t 即覆盖所有位置。",
                "ReOPD 的分析识别出多轮 OPD 中的两个误差层：时间层（累积误差，由分布偏移引起）和分布层（student 与 teacher 之间的双向偏移）。ReOPD 通过前缀重放同时缓解了这两层误差。",
            ],
            "figs": [
                {"src": "prefix_source.png", "caption": "ReOPD 的前缀来源示意。teacher 轨迹中的前缀段直接作为 student 的上下文输入。"},
                {"src": "ratio.png", "caption": "不同前缀长度下的比率分析。ReOPD 在 student 相关性和 teacher 可靠性之间取得平衡。"},
            ],
        },
        {
            "type": "h2",
            "title": "扩展到多环境场景",
            "paras": [
                "随着环境数量增加，在线 OPD 的操作复杂度呈线性增长，因为每个环境都需要独立部署。ReOPD 不需要同时部署所有环境——teacher 的轨迹可以针对不同环境分别收集，student 训练时统一使用这些预收集轨迹。",
                "下图展示了多环境场景下 ReOPD 与在线 OPD 的扩展性对比：",
            ],
            "figs": [
                {"src": "aopd_multi_envs.png", "caption": "多环境扩展性对比。ReOPD 不需要同时部署所有环境，环境成本与在线 OPD 相比大幅降低。"},
            ],
        },
        {
            "type": "h2",
            "title": "实验结果",
            "paras": [
                "在三个 Agent 任务上的实验结果显示：ReOPD 在所有指标上匹配或超越全在线 OPD。",
                "**数学推理**：ReOPD 在准确率上达到与在线 OPD 相当的水平，但训练时间大幅缩短，因为 student 不需要重复与环境交互。",
                "**搜索任务**：在需要多步工具调用的搜索场景中，ReOPD 表现出更强的稳定性，证明了前缀重放策略在复杂 Agent 任务中的有效性。",
                "**多环境扩展**：随着环境数量增加，ReOPD 保持了稳定的性能，而在线 OPD 的部署成本线性增长。",
            ],
            "figs": [
                {"src": "accuracy_time_toolcall.png", "caption": "准确率与时间/工具调用次数对比。ReOPD 在更短的时间内达到可比性能。"},
                {"src": "time_rollout_step.png", "caption": "每步 rollout 时间对比。ReOPD 无需在线环境交互，单步时间显著缩短。"},
            ],
        },
        {
            "type": "h2",
            "title": "效率分析",
            "paras": [
                "ReOPD 的效率优势体现在多个维度。下图 1 展示了前缀重放过程中的权重比率分布，说明不同前缀位置的贡献差异。下图 2 展示了处理过程中的内存占用，ReOPD 的离线训练特性使其内存需求远低于在线 OPD。",
            ],
            "figs": [
                {"src": "weighting_ratio.png", "caption": "不同前缀位置的权重比率分布。ReOPD 对较早步骤赋予更高权重。"},
                {"src": "process_memory.png", "caption": "训练过程中的内存占用对比。ReOPD 无需在线环境，内存需求更低。"},
            ],
        },
        {
            "type": "h2",
            "title": "多前缀拼接的 Transformer 实现",
            "paras": [
                "ReOPD 在实际实现中通过 chunk index 机制支持多前缀拼接。每个训练样本包含多个来自不同 teacher 轨迹的前缀段，student 需要在每个前缀段上生成动作。下图展示了 chunk index 的编码方式：",
            ],
            "figs": [
                {"src": "chunk_index.png", "caption": "Chunk index 编码示意。支持多前缀拼接，每个前缀段独立监督。"},
            ],
        },
    ],

    "conclusion": [
        "核心贡献是：将多轮 On-Policy Distillation 从在线环境依赖转变为离线前缀重放，在保持学生 on-policy 训练特性的同时，彻底消除了环境成本。",
        "ReOPD 的理论分析将多轮 OPD 的误差分解为时间层（累积误差）和分布层（双向偏移），并证明前缀重放策略能同时缓解这两层误差。实验结果验证了 ReOPD 在三个 Agent 任务上匹配或超越全在线 OPD 的效果。",
        "对于需要大规模蒸馏 Agent 模型的团队来说，ReOPD 提供了一个高效、可扩展的替代方案——teacher 数据可以预先收集，student 训练完全离线，环境成本降至零。",
    ],
    "reference_url": "https://arxiv.org/abs/2607.04763",
}

# ========== 写入逻辑 ==========
os.makedirs(_article_dir, exist_ok=True)
out = os.path.join(_article_dir, "article_data.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)
print(f"✅ 写入 {out} ({len(json.dumps(DATA, ensure_ascii=False))} chars, {len(DATA['sections'])} sections)")