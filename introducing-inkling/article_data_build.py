DATA = {
    "title": "Inkling：Thinking Machines 从零训练的开放权重模型",
    "summary": [
        {"key": "975B MoE / 41B激活", "body": "Inkling是Thinking Machines从零训练的开放权重MoE模型，总参数975B、激活41B，上下文窗口最高100万token，45T token预训练。"},
        {"key": "可控思考力度", "body": "支持按用例调节thinking effort，在Terminal Bench上达到同等性能只花Nemotron 3 Ultra约三分之一的token，成本与延迟可权衡。"},
        {"key": "自微调demo", "body": "模型自己写微调任务、跑训练、自更新：用Tinker生成「禁字母e」的lipogram模型，27分钟跑完并切换检查点。"},
        {"key": "原生多模态", "body": "文本/图像/音频统一推理，无编码器架构，音频走dMel频谱、图像走40×40补丁的轻量hMLP，语音与视觉基准居开放权重前列。"},
        {"key": "Inkling-Small", "body": "同步预览276B/12B激活的小模型，成本与延迟更优，多项基准追平大模型，完整权重即将发布。"},
    ],
    "lead": [
        "Thinking Machines Lab今天放出家族第一个开放权重模型Inkling，并把它在Tinker上开放微调。这篇官博不只是报参数，更把「让模型变成你自己的」这件事从头演示了一遍。",
        "下面是原文核心内容的中文梳理，数据、架构与图表均按原文呈现。",
    ],
    "sections": [
        {
            "type": "h2",
            "title": "Inkling是什么",
            "paras": [
                "我们的模型名为Inkling，是一个混合专家（MoE）Transformer，总参数975B，激活参数41B。它支持最高100万token的上下文窗口，在45万亿token的文本、图像、音频和视频上完成预训练。它是不同尺寸模型家族中的第一个：与此同时，我们还分享了一个预览版Inkling-Small，更轻量、激活参数12B，以更低的成本和延迟实现强劲表现。",
                "Inkling原生地对文本、图像和音频推理，并通过高效且可控的思考力度在成本与性能之间取得平衡。我们把它训练成一个广博、均衡的基础模型：在多个领域都强，且足够灵活以适应不同任务。Inkling并非当今最强的整体模型，无论是开放还是闭源。真正让它成为优质开放权重定制基座的，是多模态能力、高效思考，以及可在Tinker上微调的可用性。Inkling只是开始。",
            ],
        },
        {
            "type": "h2",
            "title": "自己微调自己",
            "paras": [
                "我们希望让更多场景用上定制能力，因此Inkling今天已在Tinker上开放微调。挑基座模型是一种结合可量化基准与「把玩手感」的定性判断，为此我们在Tinker控制台加入了Inkling Playground：一个面向开发者、与Inkling对话的界面。",
                "为了展示定制在实践中意味着什么，我们让Inkling对自己进行微调。借助Tinker，模型自己写出微调任务、运行它、评估了结果：它先以AI助手身份接入工作区，接着定义目标——训练一个「禁用字母e」的lipogram模型，给出评分函数，然后启动训练。",
                "整个流水线约27分钟跑完，目标达成（objective_improved=true），产出最终检查点。随后模型执行自更新脚本，把改进后的检查点推上生产环境。这个demo想说明的，不是lipogram本身多有用，而是「模型能自己完成从写任务到上线的一条龙」。",
            ],
        },
        {
            "type": "h2",
            "title": "能力",
            "paras": [
                "现实世界的应用需要模型具备广泛能力，这些能力可以通过微调组合与增强。我们重点展示Inkling能做什么，以及它在可信度与安全性等特质上的表现。",
            ],
        },
        {
            "type": "h3",
            "title": "通用模型",
            "paras": [
                "Inkling的设计是广博的。我们在agentic、推理、编程、指令遵循、事实性、视觉和音频任务上训练它，而不是狭隘地只优化某一域。这种广度对定制和现实使用至关重要：不同用户需要能适配截然不同工作流的模型，而不只是在基准上拔尖。",
            ],
        },
        {
            "type": "h3",
            "title": "Agentic编程与工具使用",
            "paras": [
                "一个适合微调的强基座，需要能用agentic工具灵活解决各类任务。Inkling在大多数agentic基准上于开放权重模型中名列前茅。我们把Inkling训练得可运行在各种编程与agent框架中，并在训练时随机化工具集与schema以降低对特定框架的敏感性；其可控思考力度也可从框架内部设置。",
                "下面是几个展示其agentic编程与产物生成的demo。",
                "Inkling一次性构建出一个可用的网页应用，随后驱动内嵌AI助手，用自然语言指令操作这个网页界面。",
                "Inkling在Design Arena的Agentic Web Dev排行榜上接受评估（盲评人类评审两两对比生成的应用），位列最强的开放权重模型之一。",
                "Inkling还能产出风格统一的多页产物，具备精准指令遵循、准确信息，以及贯穿始终的统一设计。",
                "给定一份详尽的美食旅行杂志prompt（\"Create a premium, editorial-style food and travel journal titled: Breakfast Around the World...\"），Inkling产出了一份约九页的PDF。",
                "Inkling通过一个由GPT Codex担任评审、40轮反馈迭代的循环，精炼了一款在线贪吃蛇游戏。能维持长程精炼并从反馈中改进，是做出最佳协作成果的关键。",
            ],
        },
        {
            "type": "h3",
            "title": "可控的思考力度",
            "paras": [
                "测试时缩放与问题解决是每个模型的核心能力，却很难用一个数字概括。为特定任务微调的开发者既关心效率，也关心公开基准上的最大努力表现。成本和延迟往往是现实应用的硬约束，低延迟对通过迭代实现协作与改进尤其关键。",
                "Inkling支持可控的思考力度，让你在性能与token效率间平衡。上图展示Inkling与其他开放权重模型在Terminal Bench 2.1（agentic编程）、HLE（高级推理）、IFBench（指令遵循）上的力度/性能曲线。在Terminal Bench上，它达到同等性能所花token只有Nemotron 3 Ultra的三分之一。对一个被运行数百万次、又作为更长工作流一环的模型来说，成本和延迟都很重要；看完整成本曲线，开发者才能为每个用例选最合适模型。",
            ],
        },
        {
            "type": "h3",
            "title": "多模态",
            "paras": [
                "Inkling设计的主要目标之一，是作为我们近期发布的interaction models系统的底层推理模型。interaction models让用户通过语音和视觉实时自然协作，这需要一个从底层就为广泛多模态能力训练的模型。",
                "多模态组件在通用领域数据上从零训练。音频与视觉输入都采用无编码器架构：音频以dMel频谱图输入，图像用四层hMLP编码为40×40像素补丁，两者经轻量嵌入层转换后与文本token联合处理。",
                "Inkling能转写语音、遵循口语指令、回答录音相关问题并对长音频推理，在VoiceBench、MMAU、AudioMC上居开放权重音频模型前列。视觉上可接受图像输入、描述内容、回答问题并做深入推理，在图表、示意图和数学视觉推理上表现强；推理中还能借助Python工具做缩放、裁剪等图像理解，将视觉推理与代码推理无缝结合。作为第一次发布，它为后续多模态工作打下基础。",
            ],
        },
        {
            "type": "h3",
            "title": "认知（Epistemics）",
            "paras": [
                "我们把Inkling训练得具备校准、指令遵循和抗审查能力，统称模型的认知。",
                "把事实说对不止是记住大语料。有用模型必须校准良好，在回答中表达恰当程度的自信——包括尚未定论的问题。后者对预测与预判是关键能力，微调模型近几个月在这一用例上快速进步，已超过前沿LLM。",
                "可信模型的第二部分是指令遵循，含难验证的复杂查询。我们用rubric评分器和claims评分器两个自动评分器做RL：前者按清单打分但易被「撒网式堆砌事实」攻破，后者逐条核验事实主张、执行agentic网络搜索来证伪。两者结合，在提升有用性的同时减少幻觉，而非用其一换其二。",
                "这些奖励不直接针对长文里经校准的不确定性，因此我们加入专门数据集，最大一块是带弃权感知奖励的短式事实问答：自信才回答，否则说「我不知道」或给带保留的猜测。最后，我们训练Inkling直接在可能受审查的话题上作答，在Cognition的Propaganda and Censorship Eval上展现出强烈的不服从审查模式。",
            ],
        },
        {
            "type": "h3",
            "title": "安全",
            "paras": [
                "我们把Inkling训练到一份跨所有模态的安全行为内部规范，再委托外部安全测试方验证。",
                "我们在危险能力（CBRN、网络攻击、失控）上做内部评估并请外部测试方；同时关注谄媚、脆弱用户、有害操控等人-AI威胁向量。在FORTRESS基准（测试对武器与暴力请求的拒绝，并含良性近似查询）上，Inkling展现出对比过的最强内置防护——拒更多有害请求，却不滥拒良性近似。在StrongREJECT上得分超98%，与其他开放/闭源模型持平。安全对开放权重模型至关重要，我们持续研究微调对安全行为的影响。",
            ],
        },
        {
            "type": "h2",
            "title": "基准测试",
            "paras": [
                "我们在广泛能力上基准测试Inkling，所有评估在effort 0.99、temperature 1.0下运行，编程评估用256K最大token轨迹上限。为提高一致性，适用时依赖外部报告结果：Humanity's Last Exam、GPQA Diamond、GDPVal、Tau 3 Banking、AA Omniscience、MMMU Pro均用Artificial Analysis分数。",
                "若干脚注值得注意：SWEBench Verified用仅bash的harness；Terminal Bench 2.1少量解法被网络搜索污染而记0分；Audio MC与VoiceBench因排行榜/评分方式差异，采用内部harness或补充系统消息。",
            ],
        },
        {
            "type": "h2",
            "title": "Inkling的诞生",
            "paras": [
                "下面看模型本身是怎么造出来的。",
            ],
        },
        {
            "type": "h3",
            "title": "架构",
            "paras": [
                "Inkling是MoE Transformer，与常见配方有若干为效率和长上下文性能而做的偏离。",
                "MoE设计大体遵循DeepSeek-V3：每层256个路由专家+2个共享专家，每token激活6个路由专家；用基于sigmoid、无辅助损失的负载均衡偏置路由器，选中专家与共享专家分数联合归一化后加权输出。",
                "注意力上以5:1交错滑动窗口层与全局层，用8个KV头。相对位置嵌入比广泛采用的RoPE表现更好、对更长序列外推更强。我们还在两处加短卷积：每个注意力层key/value投影之后，以及attention和MLP残差分支重归主残差流之前。",
            ],
        },
        {
            "type": "h3",
            "title": "训练",
            "paras": [
                "Inkling在45万亿token（文本、图像、音频、视频）上预训练，采用混合优化：大模型权重用Muon、其他参数用Adam，超参数调度受此前modular manifolds研究启发；权重衰减强度与学习率平方耦合，使权重整体规模在训练全程稳定。",
                "后训练覆盖数学、agentic代码与工具使用、音频、图像、对话、安全等广泛分布。为启动后训练，先用包括Kimi K2.5在内的开放权重模型合成数据做初始SFT（仅占很小算力），主体用于基于合成与人类环境的规模化RL。Inkling是首个大型训练工程，跑在NVIDIA GB300 NVL72上，未来模型将进一步推高算力规模。",
            ],
        },
        {
            "type": "h3",
            "title": "规模化RL",
            "paras": [
                "我们靠大规模异步RL塑造行为、提升推理与整体表现。下图展示模型在held-out推理评估聚合集（AIME、HLE、GPQA等）上的分数，RL扩展到超3000万次rollout，两次长连续运行保持稳定，推理性能全程对数线性提升，整体显著增长。",
                "我们通过改变系统消息并调整每token成本来为不同样本指定思考力度，使模型在不同rollout用不同数量token，并学会控制思考力度。",
                "我们还观察到RL训练中推理风格的涌现式转变：思维链随时间更简洁、去掉语法开销，却仍可读、不影响最终答案。这不是奖励针对的目标，而是效率本身驱动了压缩——Cognition团队在训练SWE-1.7时也注意到类似效应。",
            ],
        },
        {
            "type": "h3",
            "title": "Inkling-Small",
            "paras": [
                "同步预览的Inkling-Small是276B参数MoE（激活12B，Inkling为41B），性能/延迟权衡不同。它在许多基准上追平甚至超过大模型，源自我们对小模型预训练数据与配方的改进；两者共享同一可扩展后训练栈。",
                "两个模型均报告于effort 0.99，每行较高结果高亮（Terminal Bench 2.1中搜索污染解法记0分）。早期结果显示小模型在推理与agentic任务上接近Inkling，凭12B激活与可控思考力度，天然适合编程、用LLM评分、为其他模型生成合成数据等成本敏感负载。完整权重即将发布。",
            ],
        },
        {
            "type": "h2",
            "title": "定制与获取",
            "paras": [
                "许多现实问题连最优秀的通用模型也解决不好，缺口要靠利用组织专有知识的微调来弥合。Tinker客户经验与我们的RL结果都表明，Inkling能从微调中快速学习。",
                "Inkling今天已在Tinker上可用，上下文选项64K/256K token，限期五折优惠。为支持微调者，我们更新了cookbook原生支持Inkling，新增三个展示独特音频能力的配方，并发布tml-renderer用于可靠采样与多模态后训练。上线前想先感受模型，可去Tinker控制台的Inkling Playground，限期免费、带内嵌agentic网络搜索。",
                "我们在生态中建立了部署合作：Inkling可通过TogetherAI、Fireworks、Modal、Databricks、Baseten的API获取；与RadixArk在SGLang/Miles提供开源推理与RL支持；与Inferact支持vLLM、Lightseek支持TokenSpeed、Unsloth支持llama.cpp；并与Hugging Face集成transformers。完整权重已在Hugging Face，含原始检查点与用于Blackwell高效推理的NVFP4检查点。",
            ],
        },
    ],
    "conclusion": [
        "开放权重的牌桌上，Meta和DeepSeek比的是单项SOTA与生态规模，Thinking Machines这回的打法明显不同：它把可控思考力度、自微调闭环和抗审查的认知打包成一个「可定制基座」，卖点不在某一项最强，而在让你用低得多的成本把它变成自己的模型。",
        "会自己写微调任务、跑训练、再自更新的demo，比任何参数表都更能说明这套叙事——模型交付的终点，是用户手里的起点。Inkling只是家族第一发，后面还有Small和更大尺寸的延续。",
    ],
    "reference_url": "https://thinkingmachines.ai/news/introducing-inkling/",
}
