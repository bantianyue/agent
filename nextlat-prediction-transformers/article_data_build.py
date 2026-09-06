# -*- coding: utf-8 -*-
# NextLat (Next-Latent Prediction Transformers) 中文编译
# 源码: https://jaydenteoh.github.io/blog/2026/nextlat/  (Jayden Teoh / Microsoft Research)
# 正文图 5 张全部按原文位置保留: fig01.gif / fig02.png / fig03.gif / fig04.png / fig05.gif

DATA = {
    "title": "让 Transformer 在隐空间学预测自己的下一步：NextLat 能学到更紧凑的世界模型",
    "reference_url": "https://jaydenteoh.github.io/blog/2026/nextlat/",

    "summary": [
        {"key": "问题", "body": "序列建模今天的两块基石——Transformer 架构与 next-token 预测——都缺一个内在动机去把历史压缩成紧凑的隐状态(belief state),于是总会学到依赖偷懒注意力查表的捷径。NextLat 用一条隐空间里的自监督辅助目标把这块补上。"},
        {"key": "做法", "body": "在标准交叉熵之外,额外让 Transformer 学会预测自己的下一个隐状态 h_{t+1}(用 L2 回归 + stop-gradient)。训练依旧可并行、推理结构不变,却给模型注入了无需循环也能学的循环归纳偏置。"},
        {"key": "收益", "body": "三点:学到紧凑 belief states,更好的数据效率(隐空间监督比 one-hot token 稠密得多),以及更快的推理——靠变长自推测解码,语言建模基准上最高 3.3 倍加速;NextLat 还是唯一能解 Path-Star 这类前瞻规划任务的方法。"},
    ],

    "lead": [
        "今天的主流大模型,训练目标就是一句大白话:预测下一个 token。这篇来自微软研究院的论文博客问了一个更基本的问题——如果模型除了预测下一个 token,还学会预测自己的下一步思考状态(下一个隐状态),会怎样?",
        "这篇解读是 Next-Latent Prediction Transformers 一文的作者介绍页(jaydenteoh.github.io 2026-05-25 发布,arXiv 2511.05963)。下面这张动图就是全文想传达的那帧:左侧是 token 级预测,右侧是新增的隐空间(向量空间)内的自预测。",
    ],

    "sections": [
        # ---------- 引子(图01) ----------
        {"type": "h2", "title": "先看懂核心画面",
         "paras": [
             "传统做法只训练模型预测下一个 token:给定过去的 token 序列,输出概率最大的那个 token。",
             "NextLat 加的第二条约束是:让模型同时学会预测自己在下一时刻的隐藏状态——也就是不只看字面下一个词是什么,而是预先想清楚'读进下一个 token 之后,我的内部表示会变成什么样'。",
         ],
         "fig_after": {"1": [{"src": "fig01.gif", "caption": "原文配图(动图):Transformer 只会被训练去预测下一个 token;如果它同时学会预测自己的下一个隐藏状态呢?"}]}},

        # ---------- 引言 ----------
        {"type": "h2", "title": "引言：质疑两块基石",
         "paras": [
             "作者开篇直言要质疑当下序列建模的两个主导组件:其一是 **Transformer 架构本身**;其二是 **next-token 预测**。随后他会展示 Next-Latent Prediction(NextLat)如何分别回应这两块基石各自的问题。",
             "方法层面一句话说完:NextLat 在标准 next-token 训练之上,加了一条隐空间里的自监督辅助目标。具体地,它教 Transformer 把 token 序列 X_{1:t} 编码成隐表示(隐藏状态)h_t,使得它既能预测下一个 token X_{t+1},又能在给定下一个 token X_{t+1} 之后预测'我自己下一个隐藏状态'h_{t+1}。",
             "训练目标 = 标准 next-token 交叉熵损失 + 一条隐空间预测回归损失(作者的注释:损失里还有其他成分,但与本博客论点无关,完整目标见论文)。那条回归损失写出来就是:预测出的下一隐状态与真实下一隐状态之差的平方 L2 范数,中间挂一个 stop-gradient(停止梯度)算子,防止梯度从预测分支倒灌回被打断的表示。对应原文有两句很关键:",
             "NextLat retains the transformer's parallel training efficiency. At inference, the transformer decodes autoregressively as usual, there is no architectural change.",
             "(这句中文意思是:这条目标不破坏 Transformer 的并行训练效率;推理时照常自回归解码,没有任何架构改动。)",
         ]},

        # ---------- 动机 ----------
        {"type": "h2", "title": "动机：为什么两者都不够",
         "paras": [
             "下面从'Transformer 的问题'与'next-token 预测的问题'两个角度展开核心论证。",
         ]},
        {"type": "h3", "title": "Transformer 的问题",
         "paras": [
             "Transformer 用循环的替代品解决了训练并行紧张:它用随序列长度增长的记忆 + 自注意力,对过去 token 做即席查表。代价是——模型失去了'把历史压缩成紧凑隐摘要'的内在激励,常常学到泛化很差的解(相关研究见 Anil 2022 长度泛化、Dziri 2023 组合性上限、Liu 2023 Transformer 学到自动机捷径、Wu 2024 反事实推理等)。",
         ]},
        {"type": "h3", "title": "NextLat 怎么补",
         "paras": [
             "NextLat 强制每一个隐状态都存下'为预测下一个隐状态所必需的全部历史信息'。它保证存在这样一条映射链:h_t 解码为 X_{t+1},再用一个小映射 p_ψ 把状态更新到 h_{t+1},再解码出 X_{t+2},一路到 X_T。为了让这些映射存在且能被学会,h_t 必须朝一个 **belief state**(信念状态)—— 一个'足以预测未来'的历史压缩摘要——去优化。",
             "直觉上,这就教会模型在每一步都形成紧凑的隐摘要,从而阻断它依赖对过去 token 的偷懒自注意力查找去抄捷径。",
         ]},
        {"type": "h3", "title": "next-token 预测的问题",
         "paras": [
             "其一,next-token 预测本身并不内在地激励模型去学 belief state(见 Hu et al. ICLR 2025 The Belief State Transformer)。",
             "其二,next-token 预测天生是近视的(myopic):它偏向学习数据里的短程依赖。一个反例:在 Path-Star(一个简单的前瞻规划任务,见 Bachmann et al. ICML 2024)上,纯 next-token 预测器无法解出它。",
         ]},
        {"type": "h3", "title": "NextLat 怎么补",
         "paras": [
             "压缩与规划其实是一枚硬币的两面。要把历史压缩成紧凑 belief state,NextLat 必须先预判'过去的哪些信息以后会派上用场',因此它教会模型去抓长程依赖、去做前瞻规划。后面 Experiments 一节会看到:NextLat 是唯一能解 Path-Star 的方法。",
         ]},
        {"type": "h3", "title": "与循环网络的联系：不引入循环也能得到循环归纳偏置",
         "paras": [
             "算法推理所需的能力,用图灵机这类循环计算模型的天性最容易理解。但 RNN 训练不可并行,这正是 Transformer 成为主流的原因。",
             "NextLat 在没有顺序训练瓶颈的前提下,给 Transformer 注入了循环归纳偏置:通过教模型在每一步把历史压成 belief state,它实际上鼓励模型去学数据背后那条底层的循环隐动态(recurrent latent dynamics),而不是去钻表面 token 模式。",
             "事实上,可以把 NextLat 看成'一种无需循环就能训练 RNN 的方法'(联系 Akarsh Kumar & Phillip Isola 2026,Pretraining Recurrent Networks without Recurrence)。Experiments 一节的实验会展示:NextLat 能解一些对 Transformer 无解、但 RNN 可解的状态追踪任务。",
         ]},

        # ---------- Bitter Lesson (图02) ----------
        {"type": "h2", "title": "那'The Bitter Lesson'怎么说?",
         "paras": [
             "类似 NextLat 这样的新学习方法,常常会让'The Bitter Lesson'的虔诚信徒反感。乍看,在成熟的 next-token 目标上再加一条辅助目标,像是又要给模型注入人工归纳偏置、又一次背离那句朴素口诀——加大模型、加大数据、加大计算。",
             "作者借一张图亮明立场(Sutton 每年例行的提醒):",
         ],
         "fig_after": {"1": [{"src": "fig02.png", "caption": "原文配图:Richard Sutton 每年例行的 The Bitter Lesson 提醒"}]}},
        {"type": "h2", "title": "它没违背它，反而是它的直接应用",
         "paras": [
             "作者给出两个视角:其一,NextLat 让模型更接近**自监督学习**而非人工监督;其二,NextLat 靠从每条训练序列里榨取更多学习信号,提升**数据效率**。",
         ]},
        {"type": "h3", "title": "视角一：自监督学习",
         "paras": [
             "自监督学习(SSL)是'The Bitter Lesson'的终极形态:不依赖人工标注,SSL 让模型自己从原始无标注输入的内部结构里生成学习信号。",
             "next-token 预测的价值在于:靠互联网海量人类文本,给模型灌输人类知识的基础底盘;但模型随后就被'人类如何遣词与表达'的方式所束缚。人类语言与网页文字里满是没用的句法与不一致——举个原文给的例子:一条菜谱说 add 2 tbsp sugar, stir unt ill dissolved, then put in the fridge for 30 mins,里面 'unt ill'(应为 until)拼写有误、tbsp 是缩写,next-token 预测得花双倍力气去建模这些噪音;而底层那串语义的 latent 转移其实非常干净:混合食材 → 把糖搅到化开 → 放冰箱冷藏。核心结论原文照录:",
             "If raw sequences contain more learnable structure than next-token prediction alone extracts, then NextLat helps direct more learning capacity towards the underlying latent transition, rather than focusing on superfluous syntax.",
             "(意思是:若原始序列所含的可学结构比 next-token 单独能榨出的更多,那 NextLat 就能把更多学习容量导向'底层 latent 转移'本身,而不是浪费在多余的句法上。)",
         ]},
        {"type": "h3", "title": "视角二：数据效率与更稠密的梯度信号",
         "paras": [
             "按目前速度,到 2028 年人类生成的网络文本数据就会耗尽(Villalobos 2024)。我们急需能从数据里榨出更丰富梯度信号、让人用更少数据高效学习的办法。",
             "此前方法想靠'每一步多预测几个 token'来榨更丰富信号(即多 token 预测 MTP 路线,DeepSeek/Qwen 等)。但这些方法都在 **token 空间**里预测——学习信号稀疏,只绑在下一个 one-hot token 上。NextLat 的差别在于**在隐空间里预测**。",
             "为什么隐空间信号更稠密?第一,h_{t+1} 本身参数化了'再下一个 token X_{t+2}'的整个分布,于是监督从'单个 token 目标'升级为'分布级对齐';第二,h_{t+1} 也被训练去预测再下一个隐状态 h_{t+2}。这条'每个 latent 都预测下一个 latent'的递归隐动态,意味着 h_t 预测 h_{t+1},h_{t+1} 预测 h_{t+2},一路链下去——于是 h_{t+1} 里编码的是关于 h_{t+2}、h_{t+3}、h_{t+4}… 的信息。",
             "因此,预测 h_{t+1} 提供的不是'仅仅下一个 token'的学习信号,而是关于'整个未来'的信号。结论:next-latent 监督既在词表分布上稠密,又携带全部未来 token 的信息。",
         ]},

        # ---------- 实验 (图03) ----------
        {"type": "h2", "title": "实验：在很多任务上都优于基线",
         "paras": [
             "作者验证 NextLat 在**世界建模、推理、规划、语言建模**等基准上都胜过 next-token、multi-token prediction 及其他 token 预测基线。最有说服力的画面之一是世界建模——在曼哈顿出租车行程序列上训练,NextLat 学到的世界模型不仅更紧凑,而且和真实世界更一致:",
         ],
         "fig_after": {"0": [{"src": "fig03.gif", "caption": "原文配图(动图):曼哈顿出租车轨迹的世界建模。模型在出租车行程序列上训练,NextLat 学到更紧凑、且与真实世界更一致的世界模型"}]}},

        # ---------- 变长自推测解码 (图04/05) ----------
        {"type": "h2", "title": "Self-speculative decoding：推理期的免费加成",
         "paras": [
             "一旦模型学会预测自己的下一个隐状态,推理期就白捡一个红利:那条**轻量级的隐动态模型**(即 next-latent 预测头)可以被递归 rollout——完全在隐空间里预测未来 token,而不必动用主 Transformer 本体。这就实现了**变长自推测解码**(variable-length self-speculative decoding):",
         ],
         "fig_after": {"0": [{"src": "fig04.png", "caption": "原文配图:NextLat 的自推测解码能催出更长的 draft、带来更快的推理"}]}},
        {"type": "h3", "title": "主模型一次都不跑，能 draft 多长?",
         "paras": [
             "作者实验里,只用 next-latent 预测(深度 d=1)训练的 NextLat 就能 draft 出最长 10 个 token 的序列,在语言建模基准上拿到最高 **3.3 倍推理加速**。下图展示这条'不调用主模型、纯隐空间递归 rollout'的机制:",
         ],
         "fig_after": {"0": [{"src": "fig05.gif", "caption": "原文配图(动图):NextLat 靠轻量隐动态模型递归 rollout,实现变长自推测解码——一份 draft 能比固定步长解码催得更长、也更快"}]}},
        {"type": "h3", "title": "对比 MTP：NextLat 的优势在于变速 length",
         "paras": [
             "多 token 预测(MTP)已是开源 LLM 预训练的主流手段(DeepSeek-V3、Qwen3-Next、Nemotron 3、MiMo-V2、Gemma 4 加速器等)。但 MTP 通常被限制在**训练时固定的推测视界**(speculative horizon)内,不能超长发挥。",
             "NextLat 则允许**更长、可变长度**的 draft——所以它能比 MTP 拿下更大的推理加速。",
         ]},

        # ---------- 结语节 ----------
        {"type": "h2", "title": "结语：一句很轻的改动",
         "paras": [
             "NextLat 只是对训练目标的一处简单修改,却给表示学习、数据效率、推理速度三方面带来出乎意料的深远收益。作者希望这项工作能启发未来的预训练研究。",
         ]},
    ],

    "conclusion": [
        "这篇解读最值得带走的一点:**'预测下一个隐状态'提供了比'预测下一个 token'稠密得多、也远及未来的学习信号**。多 token 预测(MTP)把监督从下一个 token 拓宽到整段 draft,但仍呆在 token 空间;NextLat 则直接把监督搬进隐空间——隐状态本身参数化了下一步的整个分布,而递归链让它天然携带关于'整个未来'的信息,同时换来推理期 3.3 倍的变长自推测加速。",
        "作者的算法性洞见,是把 **'压缩'与'规划'统一成同一件事**:要形成紧凑的 belief state,模型就必须先预判'历史里哪些信息对未来有用',于是被迫去学长程依赖与前瞻。换个更狠的说法,NextLat 等于给 Transformer 注入了'无需循环也能学'的循环归纳偏置——保留并行训练爽点,却拿下 RNN 才擅长的状态追踪与前瞻规划。",
        "本文是论文作者的解读页,重在把'为什么做、做了什么'讲得直觉化并配动图演示;若要严谨实现,主损失中被一句带过的其余成分与完整目标仍需回 arXiv 2511.05963 对照。页面顶部已挂 arXiv / Hugging Face / Code 三处入口,可据此取代码与权重。",
    ],
}
