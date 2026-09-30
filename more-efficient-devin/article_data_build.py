#!/usr/bin/env python3
"""article_data_build.py - Devin is now up to 40% more cost-efficient (Cognition blog)"""

import json, os, sys

_article_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()

DATA = {
    "summary": [
        {"key": "降幅", "body": "Fusion与Normal便宜30-40%，Ultra便宜15-20%，Review最高便宜70%"},
        {"key": "手段", "body": "最新模型加Cloud harness优化：批量工具调用、提示缓存"},
        {"key": "智能", "body": "Fusion以68.8分领跑FrontierCode 1.1 Extended，平均每任务0.60美元"},
    ],

    "lead": [
        "Devin 现在便宜多了：Fusion 和 Normal 模式降价 30-40%，Ultra 降 15-20%，Devin Review 最高降 70%。降价来自两处：用上最新模型，包括自家的 SWE-2，以及把 Cloud harness 调得更会用这些模型。下文拆解。",
    ],

    "sections": [
        {
            "type": "h2",
            "title": "降了多少:各模式的新价格",
            "paras": [
                "Cognition 宣布 Devin 大幅降价：Fusion 与 Normal 模式便宜 30-40%，Ultra 便宜 15-20%，Devin Review 最高便宜 70%。",
                "降价的来源是纳入最新模型，包括自家的 SWE-2，再加上对 Devin Cloud harness 的工程优化，让这些模型的能力被用足。同样的用量能走得更远。",
                "降价的同时，每个模式的智能保持或提升。Devin Fusion 在 FrontierCode 1.1 上以 68.8 分领跑 Extended，平均每任务 0.60 美元。",
            ],
            "table": {
                "head": ["模式", "降幅"],
                "rows": [
                    ["Fusion", "30-40%"],
                    ["Normal", "30-40%"],
                    ["Ultra", "15-20%"],
                    ["Devin Review", "最高 70%"],
                ],
            },
            "fig_after": {
                "2": [{"src": "fig01.png", "caption": "图1:FrontierCode 1.1 Extended 分数对成本：Devin Fusion 以 68.8 分、每任务 0.60 美元领跑"}],
            },
        },
        {
            "type": "h2",
            "title": "模型独立:给每个环节选最合适的模型",
            "paras": [
                "Devin 吃所有最新模型的红利。不同模型强项不同，新版本会改变给定成本下能做到的事。Opus 5.5 与 GPT-6 Sol 智能更强且价格性能比好，GPT-6 Astra 擅长计算机操作，GPT-6 Luna 大幅拉低支撑任务的成本。加上自家的 SWE-2 和其他一众模型，Devin 的每个环节都能选最合适的。",
                "Fusion 把这种灵活性用起来：能干的主模型配省钱的副手，智能与效率两头的进步都吃到。Devin Review 能为看 diff、找 bug、分类变更各自选最合适的模型。Normal 与 Ultra 同理，在规划、测试、调试、迁移等环节按强项选模型。",
            ],
        },
        {
            "type": "h2",
            "title": "更少的工具调用:一次干完三件事",
            "paras": [
                "新模型越来越会把几个动作放在一起推理，而不是每个小操作走一轮。格式化代码、lint、跑测试这样一串活，模型可以在一次工具调用里全要了，再一起对结果推理。轮数少了，协调工作的 token 也少了，整个会话更便宜。",
                "示意：4 轮压成 2 轮，发送的 token 少 49%。第 1 轮发 8K，第 2 轮一次要走格式化、lint、测试，发 15K，第 3、4 轮不需要了，总计 2 轮、发送 23K。",
                "Devin 还打磨了把多个 shell 命令并进一次调用、独立工具调用并行跑。新模型每轮能规划更多工作：独立的步骤并行，需要顺序的步骤背靠背执行，命令之间不再回模型绕一圈。",
            ],
            "fig_after": {
                "1": [{"src": "fig02.png", "caption": "图2:批量工具调用：2轮代替4轮，发送token少49%"}],
            },
        },
        {
            "type": "h2",
            "title": "缓存:71%的token不用重算",
            "paras": [
                "LLM 无状态。Devin 这样的编码 agent，每次请求都要带上模型决策需要的上下文：指令、相关代码、之前的动作。每轮都从头处理不断变长的历史，又慢又贵。提示缓存省掉重复工作：请求开头和之前的一致，共享前缀的计算结果直接复用，不用重新处理同样的输入。上下文还在，只是复用便宜得多、快得多。",
                "示意会话：5 轮请求，发送的 token 分别是 7K、16K、20K、23K、27K，从头处理的只有 7K、9K、4K、3K、4K。总计发送 93K，从头处理 27K，少 71%。",
                "把缓存用足靠 harness 的细活：共享前缀必须保持不变，缓存有有效期，缓存的计算还绑定模型与厂商。Devin 的 harness 在这些约束里把上下文复用做到头，于是各厂商缓存降价都能吃到：Opus 5.5 的缓存读比 Opus 5 便宜 60%，GPT-6 Sol 与 Luna 的缓存读价格相对 5.6 前代腰斩。任务带着长历史走很多轮，省的就多了。",
            ],
            "fig_after": {
                "1": [{"src": "fig03.png", "caption": "图3:跨agent会话的提示缓存：从头处理的token少71%"}],
            },
        },
        {
            "type": "h2",
            "title": "今天就能用上",
            "paras": [
                "更便宜的 Devin 今天已经在 app.devin.ai 上线，可以拿最有野心的活去试，用量走得更远。",
            ],
        },
    ],

    "conclusion": [
        "① Fusion 与 Normal 便宜 30-40%，Ultra 便宜 15-20%，Review 最高便宜 70%。② 批量工具调用把 4 轮压成 2 轮，发送 token 少 49%；提示缓存让从头处理的 token 少 71%。③ 智能没降：Fusion 以 68.8 分领跑 FrontierCode 1.1 Extended，平均每任务 0.60 美元。",
        "省钱的本质是少做无用功：一次调完三个工具，历史上下文能复用就不重算。",
    ],

    "reference_url": "https://devin.ai/blog/more-efficient-devin",
    "title": "Devin降本40%:模型自由加更聪明的Harness",
}

out_path = os.path.join(_article_dir, "article_data.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)
print(f"✅ 写入 {out_path} ({len(json.dumps(DATA, ensure_ascii=False))} chars, {len(DATA.get('sections', []))} sections)")
