#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, os, sys

_article_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()

S = []
def h2(t): S.append({"type":"h2","title":t,"paras":[],"fig_after":{}})
def h3(t): S.append({"type":"h3","title":t,"paras":[],"fig_after":{}})
def t(x): S[-1]["paras"].append(x)
def code(x): S[-1]["paras"].append("__CODE__"+x)
def fig(src,cap=""):
    k=str(len(S[-1]["paras"])-1)
    S[-1]["fig_after"].setdefault(k,[]).append({"src":src,"caption":cap})
def table(h,rows): S[-1]["table"]={"head":h,"rows":rows}

h2("先跑起来")
t("一个 agent 能在同一个任务上连续工作好几个小时：读文件、跑命令、把会话的每一轮都带下去。累积起来的会话长达几十万 token，这也是前沿模型开始对外宣称百万 token 上下文窗口的原因。")
t("要让模型真正擅长这么长的上下文，就得用同样长的序列去训练它，而难点恰恰在这里：百万 token 的序列放不进一块 GPU，没有额外手段的话，也放不进八块。这份指南的示例，正是在单台 8 卡节点上、每一步用这样一条序列来训练。")
t("先看需要的环境：一台 8 张 H100（或更好）的节点，以及 main 分支的 transformers——示例用到梯度检查点的 offload 功能，它还没有进入正式发布。运行命令如下：")
code("accelerate launch \\\n    --config_file examples/sft_qwen3_8b_1m_context/context_parallel_8gpu.yaml \\\n    examples/sft_qwen3_8b_1m_context/sft_qwen3_8b_1m_context.py")
t("脚本在 PG-19 的书本数据上微调 Qwen3-8B，把书首尾相接拼起来，直到每条序列大约一百万 token。经过十分钟左右的加载与分词，第一步落地：")
code("{'loss': 4.311, 'grad_norm': 29.25, 'num_tokens': 1049000.0, 'epoch': 0.25}\n  8%|▊ | 1/12 [06:20<1:09:41, 380.10s/it]")
t("这里有三个数字值得一读。num_tokens 是 1.049e6，这是一条序列，而不是一批短序列——每个 token 都要注意到此前的每一个 token，跨越整个百万长度。loss 从 4.3 开始，这是正常的初始损失；如果长上下文配置有细微错误，起点会在 10 左右，后面会解释原因。每步 380 秒，一步就是一条序列，也就是每条序列略超六分钟。")
t("按朴素做法，这条序列每张 GPU 需要 288GB。接下来的全部内容，讲的就是这个数字如何降到 56GB。")

h2("刚刚发生了什么")
t("下面所有内容都从一个我们已经熟悉的设定往上搭：一块 GPU、每条序列几千个 token。随着序列变长，事情会开始出问题，而且出问题的顺序是固定的。")

h3("最先崩的是损失")
t("把 Qwen3-4B 放在一张 80GB 的卡上，然后不断拉长序列。最先耗尽显存的不是模型，而是损失。看内存 profile：")
fig("fig01.png","单卡内存 profile：峰值出现在前向与反向之间，也就是计算损失的位置")
t("峰值的出现位置在前向与反向之间，正是计算损失的地方。要理解峰值为什么在那里，需要看解码的最后几个阶段做了什么、损失又是如何从中构建出来的。")
fig("fig02.png","解码末端：最后一层输出的隐状态与语言模型头权重相乘，得到形状为「序列长度 × 词表大小」的 logits 矩阵")
t("解码器最后一层输出一个形状为「序列长度 × 隐藏维」的隐状态；它随后与语言模型头的权重相乘，得到形状为「序列长度 × 词表大小」的 logits 矩阵。这个矩阵非常巨大，因为序列很长、词表又很大（十万以上条目）。损失再由这个矩阵与目标标签通过交叉熵算出，而把它实体化出来，正是峰值的来源。")
t("那么，能不能不把整个 logits 矩阵实体化就计算损失？可以，分块进行。")

h3("巨大的 logits 矩阵：切块")
t("不再一次算出整条序列的 logits，而是一次取几百行、算出这些行的损失再求和，整个 logits 矩阵从不完整驻留内存。行是能够干净切分的维度：损失是对行求和，而其中的 softmax 只沿单行的词表方向运行，所以一块行自带它自己损失所需要的一切。")
fig("fig03.png","分块计算损失：一次大乘法拆成几次小乘法，内存不再堆积整个 logits 矩阵")
t("一次大乘法变成几次小乘法，节省的内存足够让损失不再成为峰值。TRL 每块使用 256 行，这样每次乘法仍然足够大，能用好 GPU。新的 profile 长这样：")
fig("fig04.png","换成分块损失之后的内存 profile：峰值消失")
t("峰值消失了。在 TRL 里怎么开启？什么都不用做——分块损失就是默认行为。如果你想换回普通损失，把 SFTConfig 里的 loss_type 设为 nll。")
t("仅这一处改动，从内存角度看就把可训练的序列从 32k token 推到了 160k。")
fig("fig05.png","分块损失带来的序列长度收益：32k 到 160k")

h3("模型从没见过第 10 万个位置：用 YaRN 重缩放位置")
t("现在内存能装下 160k token 了。但模型真的能读懂它们吗？Qwen3-4B 是在 40,960 token 的序列上训练的，配置里写得很清楚：")
code(">>> from transformers import AutoConfig\n>>> AutoConfig.from_pretrained(\"Qwen/Qwen3-4B\").max_position_embeddings\n40960")
t("超过这个长度的每一个位置，都是模型从未遇到过的位置。什么都不会崩，但训练只是在一些模型无法定位的 token 上进行。下面是一条 160k token 序列上每个 token 的损失：")
fig("fig06.png","未做位置重缩放时，随位置变化的逐 token 损失")
t("模型并不会在 40,960 处突然垮掉，它还会继续一阵，直到大约 70k 之后才开始失去线索；从那以后损失稳步攀升，最终高于同一段文本的一元熵（6.45），也就是说，比一个完全忽略上下文、只按 token 频率预测的模型还差。")
t("每个 token 都带着它的位置，而模型学到的是 0 到 40,960 之间位置的含义。问它第 10 万个位置，它没有任何依据可循。出路是：永远不要交给它一个它不认识的位置。做法是重缩放——第 100,000 个位置变成第 25,000 个，序列中的每个位置都落回模型熟悉的范围内。token 本身不变，变的只是给每个 token 的位置。这正是 YaRN 做的事，而缩放因子就是我们往外推了多远：训练时 40,960、现在要 163,840，所以因子是 4。")
t("在 TRL 里怎么开启？在加载模型时传入 RoPE 配置：")
code('training_args = SFTConfig(\n    ...,\n    model_init_kwargs={\n        "rope_parameters": {\n            "rope_type": "yarn",\n            "rope_theta": 1_000_000,  # has to match what the model ships with\n            "factor": 4.0,\n            "original_max_position_embeddings": 40960,\n        },\n    },\n)')
t("同样的测量，把重缩放之后的那次运行叠在上面：")
fig("fig07.png","加入 YaRN 重缩放后的对比曲线")
t("重缩放后的运行一直平稳到 160k。在最后 2 万个 token 上，它的平均损失是 2.8，而没有重缩放时是 7.3。")
h3("剩下的就是激活值：把它们卸载出去")
t("损失已经分块、位置已经重缩放，一块 GPU 能把我们带到 160k token。然后显存又不够了。这次是什么占满了卡？")
fig("fig08.png","层激活的内存占用：模型与优化器占固定 22GB，其余是逐层堆叠的激活")
t("模型和它的优化器占掉固定的 22GB，与序列长度无关。在此之上，每一个红色条带是一层保存下来的激活，每层 0.47GB。它们在前向写入时层层堆起、待在那里，再在反向传播消费时逐层释放。顶部的灰色，是几毫秒之内就被重算又丢弃掉的东西。")
t("TRL 已经在替你减少这部分开销，而且默认开启。梯度检查点只保留进入每一层的输入，把层内部算出的一切都丢掉：注意力分数、宽 MLP 中间值、各种归一化；等反向传播需要时，再跑一遍该层把它们取回来。活下来的是每层一个保存张量，形状是序列长度乘隐藏维，而在长序列下，这仍然是卡上最大的东西。")
fig("fig09.png","梯度检查点之后，每层仍保留一个「序列长度 × 隐藏维」的激活张量")
t("这里有一个很有用的观察：这些张量在前向阶段根本用不到。它们被写入、被搁置，很久之后才被读取。所以它们不必在这段时间里一直待在 GPU 上——可以搬到 CPU 内存，等反向传播走到时再取回来。")
fig("fig10.png","开启 offload 之后：同时常驻的激活从 38 个条带降到 4 个，峰值从 59.9GB 降到 48.8GB")
code('training_args = SFTConfig(..., gradient_checkpointing_kwargs={"offload": True})')
t("同一步、同样的长度：不再是 38 个条带层层堆叠，而是最多只有 4 个常驻，峰值从 59.9GB 降到 48.8GB。这换来的是序列长度：")
fig("fig11.png","offload 带来的序列长度收益：从 160k 提升到 256k")
t("在 48k 以下，开启与不开启的曲线是一样的，因为那个长度上没多少东西可搬。超过 48k 之后，卸载版本一直更低，原本停在 160k 的序列，现在在同一张卡上能到 256k。")
t("这当然不是免费的：每一个保存的激活都要跨到主机再回来，这些流量必须塞进它旁边的计算之间。")

h3("一块 GPU 不够：把序列切到多块上")
t("分块损失、卸载激活，一张卡现在能训练 256k token。那怎么到一百万？要看什么挡在路上，得看反向传播时单层内部的样子（也就是上面 profile 里的灰色尖峰）。")
t("梯度检查点意味着前向几乎什么都不留：每层只存输入，其余全部丢弃。等反向传播走到时该层被重新计算，而那一刻所有东西同时存在。在 MLP 里，也就是模型的这一行：")
code("down_proj(act_fn(gate_proj(x)) * up_proj(x))")
t("在完整的中间宽度上会建起四个张量，标准实现会把四个都留到反向传播走过它们为止。在百万 token、且模型的 MLP 把每个 token 从 2560 加宽到 9728 的情况下：")
code("gate_proj(x)                             19 GB = 1,048,576 x 9728 x 2 bytes\nact_fn(gate_proj(x))                     19 GB\nup_proj(x)                               19 GB\nact_fn(gate_proj(x)) * up_proj(x)        19 GB\n                                  total  76 GB")
t("76GB，就在一层之内。而卡只有 80GB，其中 30GB 已经给了模型与优化器。此时答案已经不是在存储序列上更聪明一点，而是让每块 GPU 少拿一点。")
fig("fig12.png","上下文并行：每块 GPU 持有序列的一段，切片依次轮转，使每个 token 仍能看到全部更早的 token")
t("给每块 GPU 切一段序列。用四块 GPU 时，每块持有 262,144 个 token，而不是 1,048,576 个。那四个张量随之缩小到 19GB 而不是 76GB，加上模型的 30GB 就能放进卡里。")
t("这里有一个显而易见的反对意见：注意力。每个 token 都要注意到此前每一个 token，而没有任何一块 GPU 拥有那些更早的 token。于是 GPU 之间交换各自缺失的部分，最终得到的结果，与一块足够巨大的 GPU 所算出来的完全一致。")
t("运行这种交换有两种方式：上下文并行（CP）与 Ulysses 序列并行（SP）。两者的差异如下。")
table(["", "CP", "SP"], [
    ["FSDP2", "支持", "不支持"],
    ["DeepSpeed", "不支持", "支持"],
    ["设置项", "cp_size", "sp_size"],
    ["切分对象", "token", "注意力头"],
    ["可扩展范围", "任意数量的 GPU", "最多到 KV 头数（这里是 8）"],
    ["注意力实现", "仅 SDPA、因果", "SDPA 或 FlashAttention"],
    ["依赖", "accelerate 1.11", "accelerate 1.12、DeepSpeed 0.18.1"],
])
t("在 FSDP2 上用 CP：每块 GPU 保留自己那一段，其他段轮流送过来，于是每个 token 最终都能看到更早的每一个 token。")
code("parallelism_config:\n  parallelism_config_cp_size: 4")
t("在 DeepSpeed 上用 SP：它不搬切片，而是在注意力之前把批次重新洗牌，让每块 GPU 持有全部 token、但只持有四分之一的注意力头，之后再洗回去。")
code("parallelism_config:\n  parallelism_config_sp_size: 4")
t("这两个旋钮目前不会交叉：cp_size 要求 FSDP2，而 sp_size 只在 DeepSpeed 下运行。选定后端，方法就跟着定了。本节剩下的部分走 FSDP2 这条路，也正是本指南顶部示例所用的路径：它的 GPU 并不是各自处理独立批次的独立工人，而是共享同一条序列的一个组。")
t("开启之后有两件事会变化。第一，序列必须填充到 cp_size 乘 2 的倍数，所以四块 GPU 时要在 SFTConfig 里设置 pad_to_multiple_of=8。第二，因果 SDPA 的要求排除了 packing——packing 依赖块对角掩码来避免文档互相读取，而 TRL 在你同时要求两者时会直接报错；它也排除了使用滑窗或分块注意力的模型，accelerate 会拒绝这些模型：OpenAI GPT-OSS、Gemma 3 与 4、Qwen3.5 及之后的版本。Qwen3 与 Qwen3-MoE 全程都是全注意力，这正是它们成为本文示例模型的原因。")
t("传递切片的成本比想象的低。在单节点、131k token 时，一步在两张卡上要 34.6 秒、四张卡 17.8 秒、八张卡 9.5 秒。组大小每翻一倍，步时间几乎减半，从两张到八张拿到了理论 4 倍中的 3.7 倍。")
t("这就是四个杠杆里的最后一个：")
fig("fig13.png","四个杠杆叠加后的最终结果：一块卡刚过 256k，四块卡跑满一百万 token、占用 63.6GB")
t("一块卡刚过 256k，四块卡直接把一百万跑满，落在 63.6GB，还有富余。本指南开头那条序列，装下了。")
t("最后别忘了设置 PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True。在百万 token 下，上面这次运行在 80GB 卡上需要 63.6GB，但不设置它仍然会失败：它申请的张量又大又连续，分配器在它已经持有的那些块之间找不到空间。")

h2("延伸阅读")
t("上下文并行：accelerate 关于 cp_size 以及它构建的 device mesh 的指南。Ulysses 与 ring attention：两种交换方式有何不同、各自要付出多少通信代价。YaRN：RoPE 一节里用到的位置重缩放。")

DATA = {
    "summary": [
        {"key": "问题", "body": "百万 token 的序列放不进一块 GPU、也放不进八块：朴素做法每张卡要 288GB，而示例在单台 8 卡节点上训练，最终降到 56GB"},
        {"key": "四个杠杆", "body": "把损失分块（默认开启，32k 到 160k）、用 YaRN 重缩放位置（160k 平稳）、把激活卸载到 CPU（160k 到 256k）、用上下文并行切分序列（四卡跑满 100 万 token）"},
        {"key": "关键数字", "body": "Qwen3-4B 只训到 40,960 位置，超出后 70k 起失稳；YaRN 因子取 4，重缩放后末段平均损失 2.8 对 7.3；四卡时单层 MLP 张量从 76GB 降到 19GB"},
    ],
    "lead": [
        "一个 agent 连续工作几小时，累积的会话会到几十万 token——这就是前沿模型开始宣称百万上下文窗口的原因。但要训出这种能力，必须用百万 token 的序列去训练，而这样的序列放不进一块 GPU，也放不进八块。",
        "这份 TRL 指南用单台 8 卡节点的真实示例，把「怎么把 288GB 降到 56GB」拆成四个杠杆：损失分块、YaRN 位置重缩放、激活卸载、上下文并行，并给出每一步的内存曲线与实测耗时。",
    ],
    "sections": S,
    "conclusion": [
        "**这篇文档最有价值的地方，是把长上下文训练的问题按「出问题的顺序」排序。** 先是损失（logits 矩阵 L×V 太大，分块即可，而且 TRL 默认就开着），再是位置（模型只学过 40,960，超出后损失会爬到比一元熵还差，所以要 YaRN 重缩放），接着是激活（梯度检查点之后每层仍留一个序列 × 隐藏维的张量，卸载到 CPU 即可），最后才是序列本身放不下（用上下文并行把 token 切给多块卡）。",
        "更实用的是那些容易踩的细节：cp_size 与 sp_size 不通用、序列要填充到 cp_size 乘 2 的倍数、因果 SDPA 会排除 packing 与滑窗类模型，以及百万 token 下必须打开 expandable_segments，否则即使显存够也会因为分配器找不到连续空间而失败。",
    ],
    "reference_url": "https://huggingface.co/docs/trl/long_context_training",
    "title": "把训练推到 100 万 token：TRL 长上下文训练的四个杠杆",
}

out_path = os.path.join(_article_dir, "article_data.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)
print("OK wrote", out_path, len(DATA.get("sections", [])), "sections")
