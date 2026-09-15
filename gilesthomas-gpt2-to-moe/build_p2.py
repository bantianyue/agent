#!/usr/bin/env python3
"""article_data_build.py — gilesthomas-gpt2-to-moe (Part 2/6)
来源: https://www.gilesthomas.com/2026/09/gpt-2-to-moe
"""

import json, os, sys

_article_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()

DATA = {
    "summary": [
        {"key": "核心结论", "body": "先把非 top-k 的 logits 打成负无穷再过 softmax，就得到了天然的稀疏权重，同时保留从损失回到路由器的梯度路径。"},
        {"key": "关键实现", "body": "routing_logits 过 topk 得到值与下标，用 full_like 造一张负无穷表，再 scatter_ 把 top-k 值填回去，最后 softmax 得到 expert_weights。"},
        {"key": "典型陷阱", "body": "k = 1 时 softmax 结果恒为 1，函数导数恒为零，路由器永远学不到东西；Switch Transformers 改用先 softmax 再置零来绕开。"},
    ],

    "lead": [
        "这是「从 GPT-2 到 MoE」系列的第二篇。上一篇讲清了 MoE 的机制和第一个坑：如果只是挑出 top-k 专家再相加，路由器的计算根本不在从损失回溯的计算图上，永远拿不到梯度。",
        "这一篇解决两件事：怎么用掩码把路由权重变稀疏，以及真正的代码长什么样。作者用一串长方体图示把 xs、routing_logits、top_k_values、expert_weights 的形状关系讲透，中间还踩到了 k = 1 的梯度陷阱。",
    ],

    "sections": [
        {
            "type": "h2",
            "title": "一、让路由器的输出变稀疏",
            "paras": [
                "我们真正想要的，是路由器输出里有一部分权重恰好为零。具体说，在 k 个激活专家、总共 n 个的设定下，除了 top k 之外其余权重都为零。这样运行网络时就可以直接跳过这些零权重专家，得到的结果和「不跳过」完全一样。",
                "《Outrageously Large Neural Networks》用一个技巧做到了这件事，而这个技巧对读过 GPT-2 因果掩码的人来说很熟悉。我们把路由器输出的「原始」权重叫作 logits：",
                "__CODE__python::In [7]: logits\n"
                "Out[7]:\n"
                "tensor([ 0.0418, -0.1140,  0.4254,  0.1342,  0.5106, -0.1385],\n"
                "       grad_fn=<ViewBackward0>)",
                "再过一次 softmax：",
                "__CODE__python::In [9]: torch.softmax(logits, dim=-1)\n"
                "Out[9]:\n"
                "tensor([0.1459, 0.1249, 0.2141, 0.1600, 0.2332, 0.1218],\n"
                "       grad_fn=<SoftmaxBackward0>)",
                "这样得到了一组初始权重，但我们要的是除 top k 以外全为零。",
                "如果希望某个值经过 softmax 之后为零，那它在进来时必须等于负无穷。具体代码稍后给，这里先假设我们有办法把除 top-k 之外的值都设成负无穷。在 k = 2 的具体例子里，改完之后的原始 logits 是：",
                "__CODE__python::In [15]: masked_top_k_logits\n"
                "Out[15]:\n"
                "tensor([  -inf,   -inf, 0.4254,   -inf, 0.5106,   -inf],\n"
                "       grad_fn=<ScatterBackward0>)",
                "现在再过一次 softmax：",
                "__CODE__python::In [17]: torch.softmax(masked_top_k_logits, dim=-1)\n"
                "Out[17]:\n"
                "tensor([0.0000, 0.0000, 0.4787, 0.0000, 0.5213, 0.0000],\n"
                "       grad_fn=<SoftmaxBackward0>)",
                "于是我们就有权重了。有了这些权重，我们可以概念上跑这个「所有专家都激活」的网络：",
                "但把权重为零的专家跳过。上面这几步提供的权重，意味着路由器会被训练到。",
                "这挺巧妙的。",
                "不过有一点必须强调。想象我们只有一个激活专家，也就是 k = 1，那么其余全被掩掉：",
                "__CODE__python::In [15]: masked_top_k_logits\n"
                "Out[15]:\n"
                "tensor([  -inf,   -inf,    -inf,   -inf, 0.5106,   -inf],\n"
                "       grad_fn=<ScatterBackward0>)",
                "再做一次 softmax：",
                "__CODE__python::In [17]: torch.softmax(masked_top_k_logits, dim=-1)\n"
                "Out[17]:\n"
                "tensor([0.0000, 0.0000, 0.0000, 0.0000, 1.0000, 0.0000],\n"
                "       grad_fn=<SoftmaxBackward0>)",
                "权重永远是 1，和原始 logits 无关。而如果一个函数永远只能返回同一个结果，它的导数就恒为零，于是没有梯度，也就训练不了。",
                "有意思的是，Switch Transformers 那篇论文几乎是不声不响地处理了这个问题。他们讨论的正是 k = 1 的 MoE：先提到《Outrageously Large Neural Networks》的路由方案，然后给出自己的算法，不把非 top-k 替换成负无穷再 softmax，而是先 softmax，再把非 top-k 置零。他们没有强调两者的区别。",
                "在这次实验里，我还是决定沿用非 Switch Transformers 的算法，也就是「先替换成负无穷再 softmax」，并加上保护代码，防止不小心把 k 设成 1。毕竟我见过的大多数较新的 MoE 模型至少有两个激活专家。好消息是它不仅能跑通，事后对照还发现和 Mixtral 的选择一致，算是个不错的背书。",
                "到这里，MoE 在理论上怎么工作已经清楚了。开始写代码。",
            ],
            "fig_after": {
                "10": [
                    {"src": "fig04.png", "caption": "图4（再贴一次）：所有专家都激活的 MoE"},
                ],
            },
        },
        {
            "type": "h2",
            "title": "二、真正的代码（终于来了）",
            "paras": [
                "我从《Build a Large Language Model (from Scratch)》里的代码起步。在那里，Transformer 块长这样：",
                "__CODE__python::class TransformersBlock(nn.Module):\n"
                "\n"
                "    def __init__(self, cfg):\n"
                "        super().__init__()\n"
                "        self.att = MultiHeadAttention(\n"
                "            d_in=cfg[\"emb_dim\"],\n"
                "            d_out=cfg[\"emb_dim\"],\n"
                "            context_length=cfg[\"context_length\"],\n"
                "            num_heads=cfg[\"n_heads\"],\n"
                "            dropout=cfg[\"drop_rate\"],\n"
                "            qkv_bias=cfg[\"qkv_bias\"],\n"
                "        )\n"
                "        self.ff = FeedForward(cfg)\n"
                "        self.norm1 = LayerNorm(cfg[\"emb_dim\"])\n"
                "        self.norm2 = LayerNorm(cfg[\"emb_dim\"])\n"
                "        self.drop_shortcut = nn.Dropout(cfg[\"drop_rate\"])\n"
                "\n"
                "\n"
                "    def forward(self, x):\n"
                "        shortcut = x\n"
                "        x = self.norm1(x)\n"
                "        x = self.att(x)\n"
                "        x = self.drop_shortcut(x)\n"
                "        x = x + shortcut\n"
                "\n"
                "        shortcut = x\n"
                "        x = self.norm2(x)\n"
                "        x = self.ff(x)\n"
                "        x = self.drop_shortcut(x)\n"
                "        x = x + shortcut\n"
                "\n"
                "        return x",
                "我想保留「能用 MoE 也能用非 MoE 模式」的能力，做法是扩展 cfg 里的模型配置，加一个可选的 moe 段，把 MoE 相关的东西都塞进去；如果没有这一段，就构建一个普通的密集 LLM。为此我把 __init__ 里给 self.ff 赋值的那一行换成：",
                "__CODE__python::self.is_moe = \"moe\" in cfg\n"
                "        if self.is_moe:\n"
                "            self.ff = MixtureOfExperts(cfg)\n"
                "        else:\n"
                "            self.ff = FeedForward(cfg)",
                "接下来该实现 MixtureOfExperts 类本身了。它显然需要的配置是：总共有多少专家、每个 token 激活多少专家：",
                "__CODE__python::class MixtureOfExperts(nn.Module):\n"
                "\n"
                "    def __init__(self, cfg):\n"
                "        super().__init__()\n"
                "        self.num_experts = cfg[\"moe\"][\"num_experts\"]\n"
                "        self.num_active_experts = cfg[\"moe\"][\"num_active_experts\"]",
                "前面说过，只有一个激活专家时，softmax 之后的权重会被钉死在 1，训练不了，所以我决定防一手，顺带也防住配置里另一个显而易见的错误：",
                "__CODE__python::if self.num_active_experts < 2:\n"
                "            raise Exception(\n"
                "                f\"Can't train with ``num_active_experts`` < 2 (got {self.num_active_experts})\"\n"
                "            )\n"
                "        if self.num_active_experts > self.num_experts:\n"
                "            raise Exception(\n"
                "                f\"{self.num_active_experts=} is larger than {self.num_experts=}\"\n"
                "            )",
                "然后是路由器：把进来的上下文向量（这份代码里大小是 cfg[\"emb_dim\"]）映射到专家数量：",
                "__CODE__python::self.router = nn.Linear(cfg[\"emb_dim\"], self.num_experts, bias=False)",
                "我选择不带偏置，因为我模糊地觉得这是当下的潮流，没有比这更站得住脚的理由了。",
                "接下来需要 num_experts 个专家，每个就是我们非 MoE 模式下用的那个 FeedForward 模块：",
                "__CODE__python::self.experts = nn.ModuleList([\n"
                "            FeedForward(cfg) for _ in range(self.num_experts)\n"
                "        ])",
                "它们必须放进 nn.ModuleList。如果只是放进普通 list（我试过），PyTorch 就不会把它们注册为「含有本模块参数的子模块」。训练时我们用这样的代码建优化器：",
                "__CODE__python::optimizer = torch.optim.AdamW(\n"
                "        model.parameters(),\n"
                "        lr=learning_rate, weight_decay=weight_decay\n"
                "    )",
                "所以任何不在 model.parameters() 里的东西永远不会被更新，这可不是好事。",
                "到这里零件都齐了，该写前向了：拿到路由 logits，做 top-k 和 softmax，再用这些结果去跑专家。",
            ],
        },
        {
            "type": "h3",
            "title": "2.1 从上下文向量到 logits，再到 top-k，再到权重",
            "paras": [
                "拿 logits 很简单。看 forward 方法：",
                "__CODE__python::def forward(self, xs):",
                "我们拿到一组进来的上下文向量 xs，形状是 (batch_size, sequence_length, d_emb)。",
                "我们试着把它可视化。理解张量运算时，靠直觉抄近路是可以的，但我认为要真正理解接下来的几步，脑子里最好有个更具体的东西。",
                "你可以把三阶张量想象成一个长方体。设 batch_size 为 3、sequence_length 为 5、d_emb 为 7（为了简单刻意取很小的值），它看起来是这样：",
                "长方体里的每一个点都是一个数字。一个上下文向量，就是从长方体的「前面」（batch_size × sequence_length 那一面，朝左）沿着一条线走到「后面」所经过的那串数字。",
                "那个三维画法画起来费劲，继续用也容易看晕。所以我们改成看同一件事的两个二维投影：从前面看（正对 batch_size × sequence_length 那一面），以及从侧面看（batch_size × d_emb）：",
                "在这个视角里，「正视图」里的每个圆是某个上下文向量的第一个数字，而「侧视图」里的每一行则是构成某个上下文向量的那串数字。希望这样好想象一些。",
                "现在，像 self.router 这样的 PyTorch nn.Linear 层，作用在传入张量的最后一维上。对我们的 xs（形状是 batch_size、sequence_length、d_emb）来说，它会作用在 d_emb 这一维上，也就是对每个上下文向量独立运算，这正是我们想要的。",
                "__CODE__python::routing_logits = self.router(xs)",
                "这样得到一组 logits，形状是 (batch_size, sequence_length, num_experts)。在我们的可视化里，就是一个 batch_size × sequence_length × num_experts 的长方体；设可用专家数为 4，画出来是这样：",
                "同样，看正视图，每个圆代表某个上下文向量 routing logits 的第一个元素；侧视图里每一行则是一个上下文向量的全部 routing logits。数据在长方体里的位置是对的，而且从我们叫「正视图」的这一面看，它的维度和 xs 相同，这很有用。",
                "要知道每个上下文向量该走哪些专家，就得对 routing_logits 里的每个上下文向量取 top-k。PyTorch 有现成的 topk 函数：",
                "__CODE__python::top_k_values, top_k_indices = torch.topk(\n"
                "            routing_logits,\n"
                "            k=self.num_active_experts,\n"
                "            dim=-1\n"
                "        )",
                "dim=-1 表示在最后一维上操作，也就是长度为 num_experts 的那一维。它返回最大的 self.num_active_experts 个值以及它们的位置，两个张量形状都是 (batch_size, sequence_length, num_active_experts)。",
                "于是我们又有了两个张量，可以画成长方体，都是 batch_size × sequence_length × num_active_experts。设 num_active_experts = 2：",
                "top_k_values 和 top_k_indices 的形状都是这样。和平常一样，「正视图」那一面是相同的：每个圆对应一个上下文向量，对 top_k_values 来说存的是该上下文向量 logits 里的最大值（因为 topk 返回的结果是排好序的），对 top_k_indices 来说存的则是那个最大值在 logits 列表里的下标。看侧视图，我们看到的是某个上下文向量的 top-k logit 值或下标列表。",
                "现在我们要一个能过 softmax 拿到权重的 routing_logits 版本。为此需要把每个上下文向量的非 top-k 值替换成负无穷。",
                "我最终想到的方案（中间试过好几版）是这样的：先建一个和 routing_logits 形状相同、全部填充负无穷的张量：",
                "__CODE__python::top_k_routing_logits = torch.full_like(routing_logits, -torch.inf)",
                "现在，top_k_values 里是我们想放进去的值，top_k_indices 里是它们在 logits 列表里应该待的位置，其余的值保持负无穷就好。",
                "它的形状当然和 routing_logits 一样：",
                "top_k_values 和 top_k_indices 的前两维与 routing_logits（因而也与 top_k_routing_logits）兼容，也就是在可视化里它们的正视图是一样的；把上面这张的正视图和图 8 的正视图对比一下。",
                "对我们所有的张量来说，前两维最终都对应 xs 里的一个上下文向量，区别只在最后一维和里面装的数据。",
                "PyTorch 的 Tensor 上有一个 scatter_ 函数，接收一组位置和一组值。它取一个指定的维度，把这个维度本质上当作一组列表；再接收两个维数相同、除指定维度之外各维大小都一致的其他张量，把其中一个当作值列表、另一个当作下标列表，用给定的值覆盖指定下标处的内容。",
                "听起来很有用。我们具体化一下。记住，在所有这些长方体的可视化里，我们看的正视图最终对应一个上下文向量。在 routing_logits 里，它就是该向量的专家路由原始 logits；正视图上的数字是第一个 logits，对应路由到第一个专家。看侧视图，每一行对应某个上下文向量的整组 logits。",
                "现在只盯住这一点。在 routing_logits 里，我们这个具体的上下文向量对应的 logit 值可能长这样：",
                "用同样的画法，k = 2 时 top_k_indices 对应的部分是这样：",
                "也就是说，topk 函数认出原始 logits 里下标 2 的值最大，0 的值第二大。",
                "同理，top_k_values 里是这样：",
                "这些图开始有点难啃了，我们把这个上下文向量的数据直接写成列表。对我们选中的这个上下文向量，图 10 里的 logits 是：",
                "__CODE__python::[0.4254,  0.1342,  0.5106, -0.1385]",
                "图 11 里的 top-k 下标是：",
                "__CODE__python::[2,  0]",
                "图 12 里的值是：",
                "__CODE__python::[0.5106, 0.4254]",
                "我们的 top_k_routing_logits 张量全是负无穷，形状和 routing_logits 一样，所以它对应的部分是：",
                "__CODE__python::[-inf, -inf, -inf, -inf]",
                "scatter_ 会做的是：选出下标 2 和 0（依据 top_k_indices 里的值），把 top_k_values 里对应的数字复制到已有内容之上：",
                "__CODE__python::[0.4254,  -inf,  0.5106, -inf]",
                "它会为那个正视图上的每一个位置都做这件事。于是我们就得到了想要的：每个上下文向量一张路由 logits 网格，其中非 top-k 的位置已经被替换成负无穷。",
                "相当漂亮。代码如下：",
                "__CODE__python::top_k_routing_logits.scatter_(dim=-1, index=top_k_indices, src=top_k_values)",
                "我起初有点担心「把 logits 换成静态张量再把这些值 scatter 进去」这个做法会破坏计算图，但实测并不会。我的直觉是：那些负无穷是凭空造出来的，对反向传播来说是死路；而我们复制进去的 logits 来自前面的计算，所以不是。",
                "做完这一步，我们就有了 top-k logits，可以送进 softmax 了：",
                "__CODE__python::expert_weights = torch.softmax(top_k_routing_logits, dim=-1)",
                "于是权重到手，又是这样一个长方体：",
                "和之前一样，正视图上的某个数字是某个上下文向量第一个专家的权重，侧视图的每一行则是该上下文向量在所有专家上的全部权重。经过 softmax 之后，该上下文向量上激活专家的权重是正数，未激活专家的权重是零。",
            ],
            "fig_after": {
                "4": [
                    {"src": "fig05.png", "caption": "图5：把 xs 张量画成一个三维长方体"},
                ],
                "6": [
                    {"src": "fig06.png", "caption": "图6：xs 的两个二维视角"},
                ],
                "10": [
                    {"src": "fig07.png", "caption": "图7：routing_logits 的两个二维视角"},
                ],
                "15": [
                    {"src": "fig08.png", "caption": "图8：top_k_values（等价地，top_k_indices）的两个二维视角"},
                ],
                "21": [
                    {"src": "fig09.png", "caption": "图9：top_k_routing_logits 的两个二维视角"},
                ],
                "26": [
                    {"src": "fig10.png", "caption": "图10：单个上下文向量的路由 logits 在长方体中的原位"},
                ],
                "27": [
                    {"src": "fig11.png", "caption": "图11：单个上下文向量的 top-k 路由 logits 下标在长方体中的原位"},
                ],
                "29": [
                    {"src": "fig12.png", "caption": "图12：单个上下文向量的 top-k 路由 logits 值在长方体中的原位"},
                ],
                "46": [
                    {"src": "fig13.png", "caption": "图13：expert_weights 的两个二维视角"},
                ],
            },
        },
    ],

    "conclusion": [
        "**这一篇的核心是两个技巧：把非 top-k 的 logits 打成负无穷再 softmax，就得到天然的稀疏权重；而 expert_weights 又恰好提供了从损失回传到路由器的路径。** 但别忘了 k = 1 的坑：权重恒为 1，导数恒为零，路由器等于没学。Switch Transformers 换了个顺序，先 softmax 再置零，就是为了绕开它。",
        "理解这些张量操作的诀窍是把三阶张量画成长方体：正视图对应一个上下文向量，侧视图的每一行是一个上下文向量的整个专家维度。后面 top-k、scatter_ 和掩码的形状兼容性，都能在这张图上验证。下一篇进入真正跑专家的部分：怎么按 expert_weights 把每个 token 送进该去的专家、怎么用掩码并行处理，以及怎么把结果按权重合并。",
    ],

    "reference_url": "https://www.gilesthomas.com/2026/09/gpt-2-to-moe",
    "title": "从 GPT-2 到 MoE（二）：用负无穷掩码把路由变稀疏，然后真正开始写代码",
}

out_path = os.path.join(_article_dir, "article_data.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)
print(f"OK {out_path} ({len(json.dumps(DATA, ensure_ascii=False))} chars, {len(DATA.get('sections', []))} sections)")
