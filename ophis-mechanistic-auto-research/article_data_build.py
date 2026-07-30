#!/usr/bin/env python3
"""
article_data_build.py — OPHIS: Towards Mechanistic Auto-Research
MetaCircle 博客，自动化研究新范式。
"""
import json, os, sys

_article_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()

DATA = {
    "title": "OPHIS：自动化研究的新范式——从试错到机理理解",

    "summary": [
        {"key": "核心思想", "body": "OPHIS（Observation→Problem→Hypothesis→Intervention→Speed-up）提出机理驱动的自动化研究，不依赖 LLM，而是通过分析训练内部动态来推导加速技巧"},
        {"key": "关键结果", "body": "在 Grokking 上 OPHIS 的实质性改进率 72.9%（LLM 基线 57.9%），失败率仅 13.7%（LLM 基线 42.1%），在 NanoGPT 上同样超越 RSI"},
        {"key": "意外发现", "body": "OPHIS 在 NanoGPT 训练中发现了「forking」现象——验证损失突增而训练损失持续下降，展现类好奇心驱动的科学发现能力"},
    ],

    "lead": [
        "今天的自动化研究系统大多停留在**试错（trial-and-error）**层面：它们混合互联网先验知识，或者记住之前什么方法有效，但很少解释**为什么**。LLM 可能推荐某个学习率，只因为它从互联网上见过这个技巧，而不是真正理解当前系统的训练动态。",
        "MetaCircle 团队提出了 **OPHIS**——一个完全不同的自动化研究范式。**它不依赖任何 LLM**，而是通过 Observation（观察）→ Problem（定义问题）→ Hypothesis（假设）→ Intervention（干预）→ Speed-up（加速）的闭环，从训练内部动态中提取机械论理解，再将其转化为可泛化的加速技巧。",
    ],

    "sections": [
        {
            "type": "h2",
            "title": "自动化研究的三个层次",
            "paras": [
                "论文将自动化研究划分为三个递进阶段：",
                "**第一层：互联网先验（Karpathy 路线）**。LLM 依赖互联网编码的集体经验。如果社区普遍推荐某种优化器、权重衰减策略或初始化方案，模型就会提出同样的方案。这能有效复用已有知识，但发现根本性新机制的能力有限。",
                "**第二层：实验统计记忆（RSI 路线）**。系统不仅依赖互联网知识，还记住自己的实验历史。昨天试了五种学习率都没成功，今天应该探索其他方向。这比纯互联网推理更好，但经验本身不够——根据 No Free Lunch 定理，一个技巧不可能在所有情况下都有效。",
                "**第三层：机械论理解（MetaCircle/OPHIS）**。不仅记住什么有效、什么无效，而是理解**为什么/何时有效**。研究者观察训练动态，识别底层现象，提出解释，再从解释中推导干预。这就是 OPHIS 的核心——**建立因果理解，而非记忆结果**。",
            ],
            "figs": [
                {"src": "fig_stages.png", "caption": "自动化研究的三个层次：互联网先验 → 统计记忆 → 机械论理解（OPHIS）。"},
            ],
        },
        {
            "type": "h2",
            "title": "OPHIS 框架：五步闭环",
            "paras": [
                "OPHIS 将研究组织为五个连续阶段，每条成功的干预不再只是一个数据点，而是一个**可以泛化到原始实验之外的机械论解释**。",
                "**Observation（观察）**：系统测量大量内部可观测变量——参数范数、熵类量、方差、激活统计等。这些是训练动态的原始信号。",
                "**Problem（定义问题）**：分析这些可观测变量的动态，识别潜在的瓶颈。例如：权重 L2 范数在过拟合阶段上升，在泛化开始时下降——这揭示了隐藏的动态转变。",
                "**Hypothesis（假设）**：对观察到的现象提出解释。例如：模型先过拟合，只有在逃离该状态后才开始泛化；权重范数追踪这一转变。",
                "**Intervention（干预）**：从假设中推导干预策略。例如：更强的权重衰减或显式约束权重范数——这是从理解中推导出的，而不是试错。",
                "**Speed-up（加速）**：干预成功加速训练，完成 OPHIS 闭环。",
            ],
            "figs": [
                {"src": "fig_pipeline.png", "caption": "OPHIS 五步流水线：Observation → Problem → Hypothesis → Intervention → Speed-up。"},
            ],
        },
        {
            "type": "h2",
            "title": "实验验证：Grokking 与 NanoGPT",
            "paras": [
                "**Grokking 案例**：在模加法 Grokking 任务上，基线模型在第 1250 步左右达到 95% 测试准确率。OPHIS 自动观察张量级训练动态，分析内部变量与测试精度的关系，自动提出干预方案。",
                "结果对比：OPHIS 测试了 350 个干预，**实质性改进率 72.9%**，失败率仅 13.7%。LLM 完整基线测试了 76 个技巧，实质性改进率 57.9%，失败率 42.1%。OPHIS 不仅在成功率上大幅领先，失败率仅为 LLM 基线的三分之一。",
                "**NanoGPT 案例**：在更复杂的 GPT-2 规模训练上，OPHIS 同样超越了 RSI 的结果。更重要的是，**OPHIS 在 NanoGPT 训练中发现了「forking」现象**——验证损失突然上升而训练损失持续下降，呈现一个「叉子」形状的分离。",
                "这个发现不是预设目标，而是 OPHIS 在自主探索中意外观察到的。系统通过分析约 900 条观测曲线，将问题定位到架构中的特定模块，并通过组件消融完全消除了该问题。这展示了 OPHIS 模拟**好奇心驱动的科学发现**的能力。",
            ],
            "figs": [
                {"src": "fig_grokking.png", "caption": "Grokking 加速效果对比：(a) 标准训练 vs (b) 约束权重范数后，泛化转变显著提前。"},
                {"src": "fig_ablation.png", "caption": "NanoGPT 中「forking」现象的消融验证：移除问题模块后，训练/验证的严重分离消失。"},
            ],
        },
        {
            "type": "h2",
            "title": "为什么 OPHIS 不使用 LLM",
            "paras": [
                "当前主流的自动化研究完全依赖 LLM + coding agent 的路线。OPHIS 选择了一条完全不同的路径：**完全基于对训练动态的机械论分析，不涉及任何 LLM**。",
                "这背后的信念是：LLM 虽然是优秀的执行者，但**没有好的研究品味**。它们从互联网记忆中提取技巧，但不理解训练动态的底层机制。OPHIS 则像人类研究者一样，通过观察训练动态、提出假设、验证假设来推进研究。",
                "两种路线是互补的。LLM 路线擅长复用和组合已有知识，OPHIS 路线擅长发现新机制和新现象。未来的自动化研究系统可能会将两者结合——用 LLM 加速执行，用 OPHIS 保证深度。",
            ],
        },
    ],

    "conclusion": [
        "OPHIS 的核心贡献不在于某个具体的加速数字，而在于证明了：**自动化研究不必依赖随机试错或浅层统计相关性。AI 可以逐步学会像经验丰富的研究者一样推理训练过程——观察、理解、假设、干预、改进。**",
        "团队将 OPHIS 视为更大愿景的第一步：短期是训练 Copilot/Autopilot，帮助研究者理解优化过程并提出有原则的干预；长期是让 AI 从对学习本身的机械论理解中**发现全新的架构**。",
    ],

    "reference_url": "https://meta-circle.com/blog/ophis-a-new-paradigm-for-autoresearch",
}

# ── 写入 article_data.json ──
out_path = os.path.join(_article_dir, "article_data.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)
print(f"✅ 写入 {out_path} ({len(json.dumps(DATA, ensure_ascii=False))} chars, {len(DATA.get('sections', []))} sections)")