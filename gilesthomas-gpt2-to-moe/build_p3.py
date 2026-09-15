#!/usr/bin/env python3
"""article_data_build.py — gilesthomas-gpt2-to-moe (Part 3/6)
来源: https://www.gilesthomas.com/2026/09/gpt-2-to-moe
"""

import json, os, sys

_article_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()

DATA = {
    "summary": [
        {"key": "核心结论", "body": "跑专家不必搞复杂调度：逐个专家遍历，用 expert_weights 切出的布尔掩码选出属于它的上下文向量，跑完再按权重累加回 all_outputs。"},
        {"key": "关键技巧", "body": "布尔掩码既能做取值也能做赋值，于是 all_outputs[mask] += results * weights 一行就能完成加权累加。"},
        {"key": "工程要点", "body": "权重是 (n,) 时要先 unsqueeze(1) 成 (n,1)，PyTorch 的广播是从右往左对齐的，否则维度对不上。"},
    ],

    "lead": [
        "这是「从 GPT-2 到 MoE」系列的第三篇。前两篇捋清了 MoE 的原理、稀疏掩码的数学，以及从零写一个 MixtureOfExperts 模块需要的零件。",
        "这一篇是整套实现里最核心的部分：真正把上下文向量送进各自的专家。作者用一张张二三维视图解释掩码、切片、广播和累加是怎么对齐的，最后顺手加了记录路由 logits 与权重的日志通道，为后面的负载均衡做铺垫。",
    ],

    "sections": [
        {
            "type": "h2",
            "title": "一、把上下文向量送进专家",
            "paras": [
                "下一步是真正把上下文向量喂进各自的专家。我决定把这件事做简单：逐个遍历专家，对每个专家找出哪些进来的上下文向量想走它，把它们整体跑一遍，再把结果拼回去。",
                "我相信规模更大的 MoE 系统有更聪明的路由方式，比如模型大到一张 GPU 放不下时，不同的专家会分散在不同 GPU 甚至不同机器上并行路由。但对我这种玩具规模的模型来说，逐个遍历最简单，效率也够用。",
                "我的做法是准备一个「累加器」：输出的形状和输入一样，所以如果进来的 xs 形状是 (batch_size, sequence_length, d_emb)，输出也是同样的形状。于是先建一个同形状的全零张量：",
                "__CODE__python::all_outputs = torch.zeros_like(xs)",
                "所以它看起来和图 6 里的 xs 一样：",
                "只不过每个位置填的都是零。",
                "计划是这样的：每个专家在属于它的上下文向量上跑一遍，输出按路由器（加上 top-k 与 softmax）为该上下文向量和该专家算出的权重缩放，然后把结果加进 all_outputs。等所有专家都在各自的上下文向量上跑完，all_outputs 里就是加权求和的结果。",
                "所以下一步是遍历专家：",
                "__CODE__python::for expert_ix, expert in enumerate(self.experts):",
                "现在我们需要知道哪些上下文向量想被喂给这个专家。",
                "再来看一眼 expert_weights 的样子：",
                "可以把它看成 num_experts 个「切片」，每片的形状和正视图一样，是 (batch_size, sequence_length)，代表某个专家的权重。正视图那一面（对应侧视图里最右边的一列）是专家 0 的权重，往后退一层是专家 1 的权重，以此类推。",
                "在代码里，取下标为 expert_ix 的专家的切片是这样：",
                "__CODE__python::expert_weights[:, :, expert_ix]",
                "这会得到一个简单的二维数字网格，像这样：",
                "可以看到，这是一个每个上下文向量对应一个数字的网格，形状和前面所有图里的正视图一致。每个数字就是下标为 expert_ix 的专家对该上下文向量的权重。",
                "现在我们做一个比较：",
                "__CODE__python::this_expert_mask = expert_weights[:, :, expert_ix] > 0",
                "这会得到同样形状的新网格，只是数字被换成了布尔值：对应的上下文向量在这个专家上权重大于零就是 True，否则是 False。我们拿到了一个掩码，精确标出哪些上下文向量需要跑这个专家。",
                "想象某个具体的专家在某一批上下文向量上得到的掩码是这样，我把 True 的圆圈涂了色，False 的留白：",
                "接下来是巧妙的地方。还记得我们最初进来的上下文向量 xs 长什么样：",
                "我们可以用这个掩码（图 16 里 True 和 False 组成的网格）从中选出上下文向量的子集，像这样：",
                "__CODE__python::xs[this_expert_mask]",
                "它会返回我们想要送进这个专家的那批上下文向量。用上面的图来说，它在正视图上按掩码「选中」相应的上下文向量，然后沿着长方体往后把每条「芯」都取走。",
                "问题来了：它的形状是什么？可以看到，它没法用一个简单的三维形状来表示。我们这个 batch 里的第一条序列（正视图的第一行）有两个被选中的上下文向量，第二条有一个，第三条有三个。",
                "你可以想象输出保持和输入一样的形状，也就是和 xs 同形，只是未选中的数字换成 None 之类的东西。但 PyTorch 实际给出的，是一份「该专家被选中的上下文向量」的列表。我们把这个数量记作 num_selected_context_vectors_for_this_expert，在上面那张示例图里是 6，于是形状就是 (num_selected_context_vectors_for_this_expert, d_emb)，像这样：",
                "注意，这和之前所有张量都不一样：它丢掉了与原始 xs 形状的对应关系。别的张量都能映射回 xs 里具体的上下文向量，而这一个新张量只是一堆上下文向量，和它们原本在 xs 里的位置没有天然联系。这一点我们待会儿再回来处理。",
                "不过眼下，我们已经拿到了要送进下标为 expert_ix 这个专家的数据。专家就是一个 FFN，也就是两层线性层中间夹一个 GELU，它会把喂进去的张量除最后一维之外都当作 batch 维度，因此会在 d_emb 这一维上运算，正是我们要的。于是「选出上下文向量」加「跑专家」的代码就是：",
                "__CODE__python::this_expert_results, _ = expert(xs[this_expert_mask])",
                "这样我们就拿到了这些被选中的上下文向量经过该专家之后的结果，形状仍是 (num_selected_context_vectors_for_this_expert, d_emb)。",
                "如果你熟悉 GPT-2 的代码，可能觉得那个下划线有点怪。为什么专家要返回一个元组、为什么我们忽略第二项，后面会解释。",
                "现在我们有了结果，该专家对应的上下文向量都跑完了。但它们的形状有点别扭，稍后需要修正。在那之前，先给每个结果乘上它在这个专家上的权重。",
                "记住 this_expert_mask 是一个 (batch_size, sequence_length) 的布尔网格，长这样：",
                "其中 True（图里涂色的）表示这个专家对该上下文向量是激活的，False 表示没有激活。",
                "而 expert_weights 长这样：",
                "之前我们做过这件事：",
                "__CODE__python::xs[this_expert_mask]",
                "也就是把 xs 里掩码为真的上下文向量挑出来。如果我们改成",
                "__CODE__python::expert_weights[this_expert_mask]",
                "做的事其实类似：会得到一个和图 16 里上下文向量网格同形的网格，每一行对应这个专家的一个被选中上下文向量；区别在于每一行装的不是上下文向量，而是该上下文向量在各个专家上的权重：",
                "单看这个结果没什么用，但你应该能看出来：第 expert_ix 列就是我们的专家在所有这些要跑它的上下文向量上的权重。于是沿用同一个掩码查找，再多选那一列，代码就是：",
                "__CODE__python::expert_weights[this_expert_mask, expert_ix]",
                "这句话的意思就是「把 expert_weights 里所有在 this_expert_mask 中为 True 的项挑出来，再取其中第 expert_ix 个元素」。",
                "它长这样：",
                "这正是我们给结果加权所需要的权重。我们要把 this_expert_results 里的第 i 个元素（某个输入上下文向量的输出）乘上 expert_weights[this_expert_mask, expert_ix] 的第 i 个元素。",
                "但这里有个张量兼容性问题。我们现在拿到的形状是 (num_selected_context_vectors_for_this_expert,)，本质上就是一列数字。",
                "我们要用它乘结果，也就是要把它广播到形状为 (num_selected_context_vectors_for_this_expert, d_emb) 的 this_expert_results 上。",
                "你可能会想当然地认为，把一个 (n, d_emb) 的张量乘上一个 (n,) 的张量，PyTorch 会把两个大小相同的维度对上，直接就能算。但它实际上是从右往左对齐维度，然后抱怨 n 不等于 d_emb。所以最好显式地喂给它一个 (n, 1) 的张量，告诉它哪一维要对齐、哪一维要广播：",
                "__CODE__python::this_expert_weights = expert_weights[this_expert_mask, expert_ix].unsqueeze(1)",
                "这样得到的 this_expert_weights 形状是 (num_selected_context_vectors_for_this_expert, 1)。按我一直用的画法，它和图 19 看起来一样，但形状上的这一点差别是必要的。",
                "unsqueeze 把维度问题解决之后，就可以做广播乘法了：",
                "__CODE__python::this_expert_results * this_expert_weights",
                "于是我们拿到了这个专家的加权结果：该跑它的上下文向量都跑过了，也都乘上了路由器给它们的权重，训练路由器所需的反向传播通道也就通了。",
                "接下来要把这些结果放进 all_outputs。因为它一开始全是零，而我们要它最终保存「每个上下文向量在各激活专家上的结果之和」，所以需要把这些结果累加到遍历专家过程中已经存在的内容上。",
                "前面说过，算到这里时，这些张量和最初「正面朝前」的网格（比如 xs）之间的对应关系已经丢了，没法直接把某个结果和它对应的输入上下文向量联系起来。不过要把它补回来其实出奇地简单。",
                "还记得在专家循环之前，我们是这么建 all_outputs 的：",
                "__CODE__python::all_outputs = torch.zeros_like(xs)",
                "所以它和图 6 里的 xs 一样，长这样：",
                "之前我们有从 xs 里取出要跑某个专家的上下文向量的代码，是这样：",
                "__CODE__python::xs[this_expert_mask]",
                "它给了我们一列上下文向量，像这样：",
                "而像 something[some_mask] 这样的掩码查找有个有趣的性质：它不仅能把张量里的子集取出来（就像我们对 xs 做的那样），还能用来给张量里掩码范围内选中的元素赋值。",
                "具体说：当我们执行",
                "__CODE__python::xs[this_expert_mask]",
                "得到一个形状为 (num_selected_context_vectors_for_this_expert, d_emb) 的张量。",
                "也就是说，如果我们执行：",
                "__CODE__python::all_outputs[this_expert_mask]",
                "由于掩码相同、all_outputs 与 xs 形状相同，我们同样会得到一个 (num_selected_context_vectors_for_this_expert, d_emb) 的结果。",
                "而赋值语义意味着：如果我们手上有一个同样是这个形状的张量 foo，就可以这样写：",
                "__CODE__python::all_outputs[this_expert_mask] = foo",
                "这样就不是把 all_outputs 中那部分选出来用，而是用 foo 覆盖它们。",
                "更进一步，还可以配合 += 这类复合赋值运算符：",
                "__CODE__python::all_outputs[this_expert_mask] += foo",
                "它的意思是「把 all_outputs 里 this_expert_mask 为 True 的元素选出来，再把 foo 里对应的元素累加上去」。",
                "于是最终代码是：",
                "__CODE__python::all_outputs[this_expert_mask] += this_expert_results * this_expert_weights",
                "它把专家的结果乘以对应的权重，再加进 all_outputs 里维护的运行总量。因为 all_outputs 与 xs 同形，所以 all_outputs[this_expert_mask] 与 xs[this_expert_mask] 同形，而在经过专家、乘上权重的整个过程中我们都保持了这一形状，所以这一步能对上。",
                "到这里，这个专家的全部计算就完成了，可以回到循环开头的下一个专家。所有专家跑完之后，把结果返回：",
                "__CODE__python::return all_outputs",
                "呼。这段解释相当长，但我认为代码里发生的事情确实需要这么解释。我当初是在一种心流状态下把它写出来的，当时还挺得意；现在把它讲了一遍，反倒觉得自己终于理解了下笔时潜意识里已经知道的东西。也希望读者看起来足够清楚。",
                "不过在开跑之前，还有一件事我想记录下来：不同专家之间的负载是否均衡。",
            ],
            "fig_after": {
                "4": [{"src": "fig14.png", "caption": "图14：all_outputs 的两个二维视角"}],
                "10": [{"src": "fig13.png", "caption": "图13（再贴一次）：expert_weights 的两个二维视角"}],
                "14": [{"src": "fig15.png", "caption": "图15：expert_weights 切出单个专家后的样子"}],
                "19": [{"src": "fig16.png", "caption": "图16：某个专家的 this_expert_mask 可能长成的样子"}],
                "20": [{"src": "fig06.png", "caption": "图6（再贴一次）：xs 的两个二维视角"}],
                "25": [{"src": "fig17.png", "caption": "图17：被「选中」的上下文向量"}],
                "32": [{"src": "fig16.png", "caption": "图16（再贴一次）：某个专家的 this_expert_mask 可能长成的样子"}],
                "34": [{"src": "fig13.png", "caption": "图13（再贴一次）：expert_weights 的两个二维视角"}],
                "39": [{"src": "fig18.png", "caption": "图18：被「选中」的上下文向量在各专家上的全部权重"}],
                "43": [{"src": "fig19.png", "caption": "图19：该专家在被选中上下文向量上的权重"}],
                "57": [{"src": "fig14.png", "caption": "图14（再贴一次）：all_outputs 的两个二维视角"}],
                "60": [{"src": "fig17.png", "caption": "图17（再贴一次）：被「选中」的上下文向量"}],
            },
        },
        {
            "type": "h2",
            "title": "二、记录路由器的 logits 与权重",
            "paras": [
                "这件事后面还会细讲，但 MoE 有个毛病：它可能变得越来越依赖少数专家、忽略其余专家。我在开头提到的辅助损失，正是为了避免这种情况。",
                "我暂时不想实现辅助损失，但想先记录足够的数据，看看在我的设置下它到底是不是必需品。",
                "记录每个专家被使用程度的好办法，是把 logits（路由器在 top-k 和 softmax 之前的原始输出）和我们实际用到的、经过 top-k 和 softmax 之后的专家权重都存下来。",
                "这些改动散落在好几处，我在 GitHub 上给了相应行号的链接，如果你屏幕够宽，建议对着看。不过我在下面把足够的代码贴了出来，不点链接应该也能看懂。",
                "我决定让 MixtureOfExperts 的前向多返回一项：logits 和专家权重：",
                "__CODE__python::class MixtureOfExperts(nn.Module):\n"
                "    ...\n"
                "    def forward(self, xs):\n"
                "        ...\n"
                "        return all_outputs, (routing_logits, expert_weights)",
                "而在 TransformersBlock 里，self.ff 会根据模型是否启用 MoE，被设成 FeedForward 或 MixtureOfExperts：",
                "__CODE__python::class TransformersBlock(nn.Module):\n"
                "    ...\n"
                "    def __init__(self, cfg):\n"
                "        ...\n"
                "        self.is_moe = \"moe\" in cfg\n"
                "        if self.is_moe:\n"
                "            self.ff = MixtureOfExperts(cfg)\n"
                "        else:\n"
                "            self.ff = FeedForward(cfg)",
                "这就意味着，在前向里原先只写这一句的地方（这里不给链接了，那是旧版本，链来链去反而乱）：",
                "__CODE__python::class TransformersBlock(nn.Module):\n"
                "    ...\n"
                "    def forward(self, x):\n"
                "        ...\n"
                "        x = self.ff(x)",
                "如果模型是 MoE，我们拿到的会是一个元组：真正的输出，加上我们额外返回的路由信息；如果是 FeedForward，就只拿到输出。",
                "我认为最简单的修法是改 FeedForward，让它返回与 MixtureOfExperts 兼容的值。原来的前向是这样：",
                "__CODE__python::def forward(self, x):\n"
                "        return self.layers(x)",
                "改成：",
                "__CODE__python::def forward(self, x):\n"
                "        return self.layers(x), None",
                "这样上面那段 TransformersBlock.forward 就可以写成：",
                "__CODE__python::x, this_block_moe_routing_info = self.ff(x)",
                "如果 self.ff 是 MoE，this_block_moe_routing_info 里就是真实的路由信息；如果跑的是普通密集模型，拿到的就是 None。",
                "顺便说一句，这也解释了 MixtureOfExperts 前向里那段你可能有印象的怪代码：",
                "__CODE__python::this_expert_results, _ = expert(xs[this_expert_mask])",
                "这里的 expert 是一个 FeedForward 模块，那个下划线的作用就是丢掉我们已知会返回的 None。",
                "下一步要解决的，是当 self.ff 是 MixtureOfExperts 时，怎么把 this_block_moe_routing_info 里那份额外的 (routing_logits, expert_weights) 信息从 TransformersBlock 里带出去。",
                "要知道，TransformersBlock 是放在 GPTModel 的 nn.Sequential 里用的：",
                "__CODE__python::def __init__(...):\n"
                "            ...\n"
                "            self.trf_blocks = nn.Sequential(\n"
                "                *[TransformersBlock(cfg) for _ in range(cfg[\"n_layers\"])]\n"
                "            )\n"
                "        ...\n"
                "        def forward(self, inputs):\n"
                "            ...\n"
                "            x = self.trf_blocks(x)\n"
                "            ...",
                "也就是说，前一个的前向输出会直接作为后一个的输入，如此传递。而且 nn.Sequential 假定 forward 只接收一个输入。",
                "我真正想要的是最后拿到一串 (routing_logits, expert_weights)，每个 Transformer 层一份。于是我给 TransformersBlock.forward 传入一个累积列表（允许它是 None）：",
                "__CODE__python::class TransformersBlock(nn.Module):\n"
                "    ...\n"
                "\n"
                "    def forward(self, inputs):\n"
                "        x, moe_routing_info = inputs\n"
                "        if self.is_moe and moe_routing_info is None:\n"
                "            moe_routing_info = []",
                "然后把来自那个（可能是 MixtureOfExperts 的）FFN 的路由信息追加进去：",
                "__CODE__python::if self.is_moe:\n"
                "            moe_routing_info.append(this_block_moe_routing_info)",
                "再从 TransformersBlock.forward 把它传给下一层：",
                "__CODE__python::return x, moe_routing_info",
                "接着在 GPTModel 里，我想把它交回给调用模型的推理代码。我不希望改变自己一直在用的隐式接口（传进输入、拿到下一个 token 的 logits），于是决定直接把它挂在 logits 上：",
                "__CODE__python::class GPTModel(nn.Module):\n"
                "    ...\n"
                "\n"
                "    def forward(self, in_idx):\n"
                "        ...\n"
                "\n"
                "        x = self.drop_emb(x)\n"
                "        x, moe_routing_info = self.trf_blocks((x, None))\n"
                "        x = self.final_norm(x)\n"
                "\n"
                "        logits = self.out_head(x)\n"
                "        logits.moe_routing_info = moe_routing_info\n"
                "\n"
                "        return logits",
                "事后回想，我不确定这种「夹带」路由信息的做法是对的选择。也许像 Hugging Face 那样，让 LLM 返回一个包含 logits 和其他内容的输出类，把这些字段显式列出来会更好。但这套写法在我的场景里能用，所以先留着，心里记着以后回头再看。",
                "接下来我改了训练脚本：把前向时拿到的 moe_routing_info 存进一个列表，再写进检查点的元数据里，方便日后分析。",
                "我用的训练脚本是读完 Raschka 那本书之后自己写的，有点复杂。虽然核心和第五章里训练模型用的那份基本一样，但我把它扩展成了支持多 GPU 训练，还塞进了这些年学到的各种小调整。所以这篇文章不打算深入它的代码。如果你一直跟着我过去的训练文章看，想知道它怎么衔接，可以在 GitHub 上看到累积路由信息的那段代码（注意它用了 detach，避免把计算图信息越堆越多）、把这些细节传进检查点函数的那段代码，以及更新后的检查点函数。",
                "到这里，我有了一个看起来像样的 MoE 设置。我有信心它能训练起来，但怀疑它没法在专家之间均衡负载，最终会塌缩到只用一部分专家。",
                "是时候试一把了。",
            ],
        },
    ],

    "conclusion": [
        "**跑专家的实现可以很朴素：逐个专家遍历，用权重切出的布尔掩码挑出属于它的上下文向量，算完再按权重累加回去。** 关键在于布尔掩码既能取值也能赋值，所以 all_outputs[mask] += results * weights 这一行就完成了加权累加，而不需要任何花哨的调度。",
        "两个不容易注意的细节值得记住：权重从 (n,) 送进乘法前要先 unsqueeze(1)，因为 PyTorch 的广播是从右往左对齐的；掩码查找会丢掉与原始 xs 的形状对应关系，但同一个掩码作用在形状相同的 all_outputs 上又能把它对回来。下一篇是负载均衡：第一次非均衡训练到底把专家用成了什么样。",
    ],

    "reference_url": "https://www.gilesthomas.com/2026/09/gpt-2-to-moe",
    "title": "从 GPT-2 到 MoE（三）：用掩码把上下文向量送进专家，并加一条路由日志",
}

out_path = os.path.join(_article_dir, "article_data.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)
print(f"OK {out_path} ({len(json.dumps(DATA, ensure_ascii=False))} chars, {len(DATA.get('sections', []))} sections)")
