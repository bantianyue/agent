# -*- coding: utf-8 -*-
DATA = {
    "title": "Flowtivity TensorFold评测：让投机解码精确的推理引擎",
    "summary": [
        {"key": "核心观点", "body": "TensorFold是MIT开源的本地LLM推理引擎，跑在Apple Silicon和NVIDIA GPU上，核心创新是精确投机解码：草稿输出和串行解码字节级完全一致，提速不改变任何一个采样字节。"},
        {"key": "关键数据", "body": "项目自测：DGX Spark上比vLLM（MTP=3）解码快1.6到3.1倍；Mac M5 Max 128GB上Nemotron 3.5 Lightning 30B跑到188到206 token/s，mlx_lm同模型只有138 token/s。"},
        {"key": "方法创新", "body": "手写kernel只做四个模型家族，换来字节级精确；prefix-cache专为agent流量设计，续轮只prefill新后缀，系统块缓存到磁盘，对话重启不丢。"},
    ],
    "lead": [
        "投机解码是LLM推理提速的标准技巧：小模型猜几个token，大模型一次验证，猜中就省整轮解码。但常规实现用随机测试接受草稿，同样prompt同样seed，输出可能因为草稿过程不同而不同。对coding agent和流水线来说，这是个隐患。",
        "TensorFold（ashhart开源，MIT协议）把投机解码做精确了：验证只接受和串行解码完全一致的token，输出字节级不变。这篇是Flowtivity的第三方评测，下面拆开原理、实测数字和局限。",
    ],
    "sections": [
        {
            "type": "h2",
            "title": "TensorFold是什么",
            "paras": [
                "TensorFold是2026年发布在GitHub上的本地LLM推理引擎，MIT协议。用法很简单：在Hugging Face上点名要哪个模型，选上下文窗口和采样设置，TensorFold下载后用专为该模型家族手写的Metal或CUDA kernel加载起来，在/v1/chat/completions挂一个OpenAI兼容的endpoint。任何OpenAI客户端，包括coding agent，都能直接连。",
                "架构上拉4-bit MLX checkpoint，走家族专属的Metal lane kernel或CUDA引擎，DFlash2做drafter。prefix cache落盘，专为agent流量设计。",
            ],
            "fig_after": {
                "1": [{"src": "fig01.png", "caption": "图1:TensorFold服务流水线。Hugging Face的4-bit MLX checkpoint经tensorfold pull拉取，走Metal lane kernel或CUDA引擎，DFlash2做草稿，对外是OpenAI兼容endpoint，prefix cache落盘"}],
            },
        },
        {
            "type": "h2",
            "title": "为什么精确投机解码重要",
            "paras": [
                "标准投机解码的流程：小草稿模型猜几个token，大模型一次前向全验证，接受的猜测省掉整轮解码。问题在接受环节：常规实现用随机性测试决定接不接受，同样prompt同样seed，输出文本可能随草稿过程变化。对coding agent、评测流水线、任何要复现结果的场景，这都是不确定性来源。",
                "TensorFold的做法：草稿token一次前向验证，只接受和串行解码会采样出的完全一致的token。输出和关掉投机解码逐个token跑字节级相同，速度提了，文本一个字节不动。对把LLM输出当确定性工件用的团队，这个性质比单纯的速度数字更重要。",
            ],
            "fig_after": {
                "1": [{"src": "fig02.png", "caption": "图2:TensorFold精确投机解码。草稿模型出候选，大模型一次前向验证，只接受与串行解码完全一致的token，输出字节级不变"}],
            },
        },
        {
            "type": "h2",
            "title": "实测有多快",
            "paras": [
                "数字来自项目自己的bench_openai单流客户端，自报、和工作负载强相关，先打预防针。Mac M5 Max 128GB上：NVIDIA Nemotron 3.5 Lightning 30B-A3B 4-bit解码188到206 token/s，mlx_lm同模型138 token/s；Qwen3.8-27B配DFlash2 drafter，代码任务189 token/s，不开草稿只有26 token/s。",
                "DGX Spark上和vLLM（MTP=3）同checkpoint同客户端对比：Qwen3.8-27B代码任务49.6对17.7，聊天45.8对15.0；两台Spark跑Flash Next代码103.8对46.4；GLM-5.3-Flash代码49.4对24.5。加速比1.6倍到3.1倍，看模型和任务。",
            ],
            "fig_after": {
                "1": [{"src": "fig03.png", "caption": "图3:DGX Spark上TensorFold对vLLM解码速度。同checkpoint同客户端，64 token回复，seed取中位：Qwen3.8代码2.8倍、聊天3.1倍，Flash Next 2.2倍，GLM-5.3-Flash 2.0倍"}],
            },
            "tables_after": {
                "2": [
                    {
                        "headers": ["对比项", "TensorFold", "vLLM"],
                        "rows": [
                            ["解码确定性", "和串行解码字节级一致", "标准投机采样，结果依赖草稿"],
                            ["Qwen3.8-27B聊天解码，1台Spark", "45.8 token/s", "15.0 token/s"],
                            ["Flash Next代码解码，2台Spark", "103.8 token/s", "46.4 token/s"],
                            ["模型支持", "4个家族，手写kernel", "几十种架构"],
                            ["硬件重心", "Apple Silicon、DGX Spark", "数据中心NVIDIA、AMD、TPU"],
                            ["协议", "MIT", "Apache 2.0"],
                        ],
                    }
                ],
            },
        },
        {
            "type": "h2",
            "title": "硬件与部署",
            "paras": [
                "macOS要Apple Silicon加Python 3.11以上。checkpoint按文档：30B级模型要32GB以上统一内存，113GB的Qwen3.8 Flash Next要192GB以上。M1到M5都支持lane batching，M1到M4走row-exact兜底，最快的kernel要M5代的tensor unit。Linux上跑CUDA引擎。",
                "两台DGX Spark可以张量并行：模型按层对半分，Rank 0对外 serving HTTP，两台之间走直连链路。Flash Next代码任务两台Spark跑到103.8 token/s，是vLLM同权重MTP=3的2.2倍。",
                "部署形态是标准的OpenAI兼容服务，coding agent把base_url一指就能切过来。本地跑意味着权重和对话都不出内网，这对有合规要求的团队是决定性因素。",
            ],
            "fig_after": {
                "1": [{"src": "fig04.png", "caption": "图4:两台DGX Spark张量并行。M1到M4用row-exact兜底、M5用tensor unit lane kernel；Rank 0和Rank 1各跑一半层，直连链路，Flash Next代码103.8 token/s"}],
            },
        },
        {
            "type": "h2",
            "title": "谁适合用",
            "paras": [
                "最对味的是跑本地AI coding agent、把输出可复现看得和速度一样重的团队。prefix-cache就是按agent流量设计的：续轮只prefill新增的后缀，系统块一次缓存到磁盘，对话在服务端重启后还在。",
                "Flowtivity观察到越来越多成长型企业要本地或主权推理，隐私合规是硬需求。TensorFold这种“下载即跑、OpenAI兼容”的形态，agent从云端切本地几乎不用改代码。",
                "反过来，如果你的场景是数据中心多租户、模型种类杂、要AMD和TPU，那还是vLLM的地盘。TensorFold的硬件重心写得很明白：Apple Silicon和DGX Spark。",
            ],
        },
        {
            "type": "h2",
            "title": "局限：窄是优点也是风险",
            "paras": [
                "TensorFold的窄是故意的：只给四个模型家族写手写kernel包，GPTQ、AWQ、NVFP4这些格式在下载前就直接拒绝。窄换来了字节级精确和调优深度，但也意味着你的模型不在名单里就用不上。",
                "benchmark全是项目自报，没有独立验证，工作负载一换数字就可能变。部分芯片上满血的草稿速度依赖特定MLX版本，还有个已知边角case没修。评测原文的结论很克制：当成有潜力的年轻项目，别当vLLM替代品。",
                "生态也是风险：手写kernel的维护成本随模型家族线性涨，新架构出来要等作者写包。vLLM那种几十种架构开箱即用的广度，TensorFold短期内给不了。选它就是选深度不选广度。",
            ],
        },
    ],
    "conclusion": [
        "TensorFold的差异化很清晰：不拼模型覆盖，拼精确。投机解码的输出和串行解码字节级一致，这个性质在coding agent和评测流水线里是硬需求，速度是顺带的。自测数字漂亮，1.6到3.1倍于vLLM，但记住这是项目自报。",
        "四个家族的手写kernel是双刃剑：调优深，但生态窄。GPTQ、AWQ、NVFP4直接拒绝，名单外的模型用不上。想试的先看自己的模型在不在四个家族里，再看有没有Apple Silicon或DGX Spark。",
        "本地推理这条赛道，精确性和可复现会越来越值钱。TensorFold至少证明了一件事：投机解码不必以牺牲确定性为代价。",
    ],
    "reference_url": "https://flowtivity.ai/blog/tensorfold-inference-engine-review/",
}
