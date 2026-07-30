#!/usr/bin/env python3
"""
article_data_build.py — Skill Self-Play: Pushing the Frontier of LLM Capability
arXiv 2607.22529 — 精简编译，论文类 60% 阈值。遵守图文原则、简洁原则、结论首句原则。
"""
import json, os, sys

_article_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()

DATA = {
    "title": "Skill Self-Play：用技能共进化推动 LLM 能力边界，工具调用和逻辑推理全面超越基座",

    "summary": [
        {"key": "核心问题", "body": "LLM 自我进化面临任务多样性与验证可靠性的根本矛盾——多样性高则验证难，验证严则任务空间窄"},
        {"key": "核心方法", "body": "Skill-SP：用动态技能库作为任务模式接口，让提议者（Proposer）在求解者（Solver）的学习前沿生成高保真任务"},
        {"key": "实验结果", "body": "Qwen3-4B 在工具调用和逻辑推理上全面超越基座，多项基准达到或超越 8B 模型水平"},
    ],

    "lead": [
        "Self-Play 是 LLM 自我进化的核心范式——模型自己生成训练数据，自己从中学到新能力。但 Self-Play 面临一个根本矛盾：要覆盖广泛的任务空间就需要多样化的生成策略，但多样性越高，验证数据质量的难度就越大。",
        "Skill Self-Play（Skill-SP）提出了一个简洁的解决方案：用一个动态进化的技能库作为任务模式接口，让提议者（Proposer）基于技能库在求解者（Solver）的学习前沿生成高保真任务。在工具调用和逻辑推理两个领域，Skill-SP 在多个骨干模型上全面超越现有 Self-Play 方法。",
    ],

    "sections": [
        {
            "type": "h2",
            "title": "Self-Play 的困境",
            "paras": [
                "现有 Self-Play 方法可以归纳为两种范式：**基于验证器**的方法使用可靠的验证器（如编译器、执行器）但严重限制了任务空间；**基于过滤器**的方法扩大了覆盖范围但依赖被动的事后过滤，错误残差会降低数据质量。",
                "Skill-SP 的核心洞察是：将任务生成从「一次性过程」转变为「迭代技能进化过程」。通过一个主动的技能编排器（Skill Orchestrator），同时维护技能引导生成和开放探索两条流，实现既有广泛覆盖又有高保真的数据生成。",
            ],
            "figs": [
                {"src": "intro.png", "caption": "Self-Play 范式的对比。Skill-SP 通过技能编排器同时实现广泛覆盖和高保真数据。"},
            ],
        },
        {
            "type": "h2",
            "title": "Skill-SP 框架",
            "paras": [
                "Skill-SP 是一个训练时框架，将通用 Self-Play 转化为主动的课程构建过程。每个迭代轮次中，Skill-SP 协调三个角色的联合优化：",
            ],
        },
        {
            "type": "h3",
            "title": "三个核心角色",
            "paras": [
                "**提议者（Proposer Policy）**：基于路由技能合成当前求解者学习前沿的有效任务。提议者通过技能引导生成和开放探索两条流生成候选任务，再由验证器过滤。",
                "**求解者（Solver Policy）**：在验证后的课程数据上优化。求解者是实际被训练的 LLM，其能力边界决定了提议者应该生成什么难度的任务。",
                "**技能控制器（Skill Controller）**：管理一个动态进化的技能库。控制器从执行反馈中提炼技能，更新技能库，推动技能和求解者的持续共进化。",
            ],
        },
        {
            "type": "h3",
            "title": "共进化循环",
            "paras": [
                "每个迭代轮次中，技能库中的技能被路由到提议者，提议者生成任务，验证器过滤，求解者训练，控制器从执行反馈中更新技能库。这个循环持续进行，技能和求解者共同进化。",
                "技能库本身是动态的——新技能被加入，低效技能被淘汰。这种机制确保了任务生成始终聚焦于求解者当前的学习前沿，而非停留在已有能力的舒适区。",
            ],
            "figs": [
                {"src": "method.png", "caption": "Skill-SP 方法框架。技能库、提议者、求解者、控制器四者协同进化。"},
            ],
        },
        {
            "type": "h2",
            "title": "实验结果",
            "paras": [
                "在工具调用（API-Bank、BFCL）和逻辑推理（ZebraLogic）两个领域，使用 5 个骨干模型（Qwen3-4B/8B、Ministral-3-8B/14B、Granite-4-1-3B）进行实验：",
                "**工具调用**：Skill-SP 在所有骨干模型上超越基线和现有 Self-Play 方法。Qwen3-4B 在多个工具调用基准上达到或超越 Qwen3-8B 的水平。",
                "**逻辑推理**：在 ZebraLogic 网格推理任务上，Skill-SP 大幅超越基座模型和 Unguided SP，展示了技能引导在复杂推理任务中的有效性。",
                "**技能进化分析**：技能库在迭代过程中持续进化——旧技能被淘汰，新技能被加入，技能路由分布变得更加聚焦。有效的技能存活并繁衍，无效的技能被淘汰，构成一个自然的技能进化生态。",
            ],
            "figs": [
                {"src": "fig_qwen3_4b_performance_radar.png", "caption": "Qwen3-4B 能力雷达图。Skill-SP 在工具调用和逻辑推理各维度全面扩展。"},
                {"src": "fig_question_distribution.png", "caption": "问题分布对比。Skill-SP 生成的任务覆盖更广，难度分布更合理。"},
                {"src": "fig_frontier_quality_c_skill_lifecycle.png", "caption": "技能生命周期。技能库在迭代中持续进化，有效技能存活并繁衍。"},
            ],
        },
        {
            "type": "h2",
            "title": "扩展性与泛化能力",
            "paras": [
                "Skill-SP 的扩展性体现在多个模型规模上：从 3B 到 14B 的参数范围，Skill-SP 都带来了一致的提升。下图展示了 5 个骨干模型在迭代过程中的性能变化：",
            ],
            "figs": [
                {"src": "fig_iteration_qwen3_4b.png", "caption": "Qwen3-4B 迭代性能曲线。随迭代轮次增加，Skill-SP 持续提升。"},
                {"src": "fig_iteration_qwen3_8b.png", "caption": "Qwen3-8B 迭代性能曲线。更大模型同样受益于技能共进化。"},
                {"src": "fig_iteration_ministral_3_8b.png", "caption": "Ministral-3-8B 迭代性能曲线。跨模型架构验证了方法的通用性。"},
            ],
        },
        {
            "type": "h2",
            "title": "技能路由与效率分析",
            "paras": [
                "技能路由器的利用率分析显示，Skill-SP 的技能库在实践中被高效利用——大多数技能都有对应的任务生成场景，不存在被完全闲置的技能。",
                "数据效率方面，Skill-SP 相比 Unguided SP 在更少的训练数据下达到更好的性能，说明技能引导生成的任务质量更高，验证成本更低。",
            ],
            "figs": [
                {"src": "fig_skill_router_utilization.png", "caption": "技能路由器利用率。技能库中的大多数技能被有效利用。"},
                {"src": "fig_toolcall_data_efficiency.png", "caption": "数据效率对比。Skill-SP 在更少数据下达到更好性能。"},
            ],
        },
    ],

    "conclusion": [
        "核心贡献是：提出了一种共进化框架，通过动态技能库解决了 Self-Play 中任务多样性与验证可靠性的根本矛盾。",
        "Skill-SP 的关键创新在于用技能作为任务模式的抽象接口，使得提议者可以在求解者的学习前沿生成高保真任务，同时技能库本身与求解者共同进化。",
        "在工具调用和逻辑推理两个领域的广泛实验表明，Skill-SP 在多个骨干模型上全面超越现有 Self-Play 方法，为 LLM 的持续自我进化提供了一个可扩展的框架。",
    ],
    "reference_url": "https://arxiv.org/abs/2607.22529",
}

# ========== 写入逻辑 ==========
os.makedirs(_article_dir, exist_ok=True)
out = os.path.join(_article_dir, "article_data.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)
print(f"✅ 写入 {out} ({len(json.dumps(DATA, ensure_ascii=False))} chars, {len(DATA['sections'])} sections)")