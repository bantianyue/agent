#!/usr/bin/env python3
"""article_data_build.py — gilesthomas-gpt2-to-moe (Part 5/6)
来源: https://www.gilesthomas.com/2026/09/gpt-2-to-moe
"""

import json, os, sys

_article_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()

DATA = {
    "summary": [
        {"key": "核心结论", "body": "辅助损失接进训练循环只是几行代码：算出 MoE 路由损失，按 α 缩放后加到交叉熵损失上再反向传播。"},
        {"key": "关键实现", "body": "view 摊平后，用 > 0 的掩码沿列求和得到各专家的 fᵢ，softmax 后求和得到 Pᵢ，再乘专家数做点积就是每层辅助损失。"},
        {"key": "关键数据", "body": "一小时一轮的 α 扫描里，0.005 拿到最低训练损失 6.106，辅助损失 25.21 仅比理想值 24 高 1.2；0.01 开始伤训练损失。"},
    ],

    "lead": [
        "这是「从 GPT-2 到 MoE」系列的第五篇。上一篇看完了第一次不均衡训练，并推导出 Switch 式的辅助损失公式。",
        "这一篇把公式落成代码：怎么在训练循环里加一路 MoE 路由损失、怎么用 view 和掩码把 fᵢ 与 Pᵢ 向量化地算出来，以及一个关键的实际问题，α 到底取多少。作者为此做了四组一小时的小规模扫描。",
    ],

    "sections": [
        {
            "type": "h2",
            "title": "一、辅助损失的代码",
            "paras": [
                "我原来的训练循环里，前向和反向是这样写的：",
                "__CODE__python::if use_amp:\n"
                "                with torch.amp.autocast(device_type=device.type, dtype=torch.float16):\n"
                "                    logits = model(inputs)\n"
                "                    train_loss = calculate_loss(logits, targets)\n"
                "            else:\n"
                "                logits = model(inputs)\n"
                "                train_loss = calculate_loss(logits, targets)\n"
                "\n"
                "            is_last = accumulation_step == gradient_accumulation_steps - 1\n"
                "            with model.no_sync() if not is_last else nullcontext():\n"
                "                if scaler is not None:\n"
                "                    scaler.scale(train_loss / gradient_accumulation_steps).backward()\n"
                "                else:\n"
                "                    (train_loss / gradient_accumulation_steps).backward()",
                "把我在书里那份简单训练代码之上累积的增强都剥掉，也就是 AMP、DDP 和梯度累积，剩下的就是：",
                "__CODE__python::logits = model(inputs)\n"
                "            train_loss = calculate_loss(logits, targets)\n"
                "\n"
                "            train_loss.backward()",
                "希望这些看起来很熟悉。",
                "我要做的是把辅助损失加进去，前提是训练的是 MoE，并用 α 缩放。我写出来的版本如下，同样剥掉了那些增强相关的东西：",
                "__CODE__python::logits = model(inputs)\n"
                "            train_loss = calculate_loss(logits, targets)\n"
                "            if hasattr(logits, \"moe_routing_info\") and logits.moe_routing_info is not None:\n"
                "                moe_router_loss = calculate_moe_router_loss(logits.moe_routing_info)\n"
                "                moe_router_losses.append(moe_router_loss.item())\n"
                "            else:\n"
                "                moe_router_loss = 0\n"
                "\n"
                "            total_loss = train_loss + moe_router_loss * moe_router_loss_scale\n"
                "            total_loss.backward()",
                "注意我还想把 router 损失记进 moe_router_losses 列表，方便在训练过程中监控，就像我平时监控训练损失那样，前面那张损失曲线就是一个例子。",
                "这一切都相当简洁：如果模型返回了 MoE 路由信息，就调用新的 calculate_moe_router_loss，按上一节的数学算出损失，再按 moe_router_loss_scale 缩放后加上去。这个名字是我给 Switch Transformers 论文里那个叫法含糊的 α 起的。",
                "把 AMP、DDP 和梯度累积这些东西加回去，最终代码长这样：",
                "__CODE__python::with torch.amp.autocast(device_type=device.type, dtype=torch.float16) if use_amp else nullcontext():\n"
                "                logits = model(inputs)\n"
                "                train_loss = calculate_loss(logits, targets)\n"
                "                if hasattr(logits, \"moe_routing_info\") and logits.moe_routing_info is not None:\n"
                "                    moe_router_loss = calculate_moe_router_loss(logits.moe_routing_info)\n"
                "                    moe_router_losses.append(moe_router_loss.item())\n"
                "                else:\n"
                "                    moe_router_loss = 0\n"
                "\n"
                "            is_last = accumulation_step == gradient_accumulation_steps - 1\n"
                "            with model.no_sync() if not is_last else nullcontext():\n"
                "                total_loss = train_loss + moe_router_loss * moe_router_loss_scale\n"
                "                if scaler is not None:\n"
                "                    scaler.scale(total_loss / gradient_accumulation_steps).backward()\n"
                "                else:\n"
                "                    (total_loss / gradient_accumulation_steps).backward()",
                "所以这算相当简单了，按 LLM 训练领域的「简单」标准来说。",
                "从训练配置文件里读出 moe_router_loss_scale 的代码不值得细讲，把 moe_router_losses 的平均值、最小值、最大值写进检查点元数据的代码也不值得，画图的代码同样不值得，虽然图后面会展示。",
                "有意思的当然是 calculate_moe_router_loss 这个函数。",
                "它在 GitHub 上，长这样：",
                "__CODE__python::def calculate_moe_router_loss(moe_routing_info):\n"
                "    total_routing_loss = 0\n"
                "    for routing_logits, expert_weights in moe_routing_info:\n"
                "        batch_size, seq_len, num_experts = expert_weights.shape\n"
                "\n"
                "        flattened_expert_weights = expert_weights.view((batch_size * seq_len, num_experts))\n"
                "        expert_active_counts = (flattened_expert_weights > 0).sum(dim=0)\n"
                "        expert_frequencies = expert_active_counts / (batch_size * seq_len)\n"
                "\n"
                "        raw_routing_weights = torch.softmax(routing_logits, dim=-1)\n"
                "        flattened_raw_routing_weights = raw_routing_weights.view((batch_size * seq_len, num_experts))\n"
                "        expert_prob_allocation = flattened_raw_routing_weights.sum(dim=0) / (batch_size * seq_len)\n"
                "\n"
                "        layer_routing_loss = num_experts * torch.dot(expert_frequencies, expert_prob_allocation)\n"
                "\n"
                "        total_routing_loss += layer_routing_loss\n"
                "\n"
                "    return total_routing_loss",
                "我们从外往里看。",
                "我们拿到一个叫 moe_routing_info 的列表。记住，它是 MoE 模型在单个 batch 前向之后传回来的，模型里每个 Transformer 层一项，每一项是一对 (routing_logits, expert_weights)。",
                "先把总路由损失初始化为零，然后对每一层算出它自己的路由损失，在循环末尾累加到总量上，最后返回总量。",
                "显然，好玩的部分在循环里面。又到了画张量图的时候。",
                "先回忆一下 expert_weights 的形状：",
                "正视图上的每个格子对应我们 batch 里某条序列的某个上下文向量，而从那里「扎进」长方体的那条芯，就是这个上下文向量路由到各专家时实际用到的权重：未选中的专家是零，选中的是零到一之间的某个数。",
                "回到代码。我们先借 expert_weights 的形状确定各个维度：",
                "__CODE__python::batch_size, seq_len, num_experts = expert_weights.shape",
                "然后做第一块计算，试着从数学里算出 fᵢ，也就是「被派发给专家 i 的 token 占比」。我们想用向量化的方式高效地一次算出所有 fᵢ，记住每个专家一个。",
                "第一步是把 (batch_size, seq_len) 的网格摊平成一维，本质上就是把正视图的每一列叠起来，变成一根长条，像这样：",
                "或者更简单地说，因为它现在只是一个二维张量，像这样：",
                "我们可以用 PyTorch 的 view 方法做到这一点，不必在内存里真的搬数据；顾名思义，它只是返回同一份数据的另一个视图：",
                "__CODE__python::flattened_expert_weights = expert_weights.view((batch_size * seq_len, num_experts))",
                "记住这些是专家权重。每个格子里是一个数：如果这个专家对原来那个位置对应的上下文向量没有被选中就是零，被选中则是某个非零数。所以我们这么做：",
                "__CODE__python::flattened_expert_weights > 0",
                "就会得到一个同形状的张量，权重大于零、也就是该专家对这个上下文向量是激活的为 True，否则为 False。",
                "这意味着，如果我们在图 21 里沿着列求和，就会得到一行、num_experts 列的新网格，表示每个专家在给定 batch 里被激活的总次数：",
                "所以代码里只要：",
                "__CODE__python::expert_active_counts = (flattened_expert_weights > 0).sum(dim=0)",
                "再除以 batch 里上下文向量的数量，就又得到一个形状与图 22 相同的张量：一行，num_experts 列，正好装着我们要的东西：",
                "__CODE__python::expert_frequencies = expert_active_counts / (batch_size * seq_len)",
                "也就是说，expert_frequencies 就是数学里的向量 f，装着辅助损失计算需要的所有 fᵢ，也就是下面这个式子对所有专家的结果：",
                "fᵢ = (1/T) Σₓ∈ℬ 1{i ∈ top-k(p(x))}",
                "Pᵢ 的计算非常相似。我们先拿到这样的 routing_logits：",
                "正视图上的每个格子对应一个上下文向量，从那里扎进长方体的芯，就是这个上下文向量在每个专家上的原始路由 logits，每个专家一个数。",
                "首先要把 routing_logits 变成概率，也就是沿最后一维过一遍 softmax，那是侧视图里的水平轴，也就是 num_experts 那一维：",
                "__CODE__python::raw_routing_weights = torch.softmax(routing_logits, dim=-1)",
                "然后用同样的 view 技巧，把结果变成一列长度为 num_experts 的列表（比喻地说），形状和图 21 一样：",
                "__CODE__python::flattened_raw_routing_weights = raw_routing_weights.view((batch_size * seq_len, num_experts))",
                "现在如果我们像这样按行相加：",
                "__CODE__python::flattened_raw_routing_weights.sum(dim=0)",
                "就会得到一行、num_experts 列的结果，里面是每个专家在 batch 所有上下文向量上的概率之和，和图 22 那个一样。",
                "我们可以把它除以 batch 里上下文向量的数量：",
                "__CODE__python::expert_prob_allocation = flattened_raw_routing_weights.sum(dim=0) / (batch_size * seq_len)",
                "那就是我们的向量 P，装着所有 Pᵢ，其中每一个就是：",
                "Pᵢ = (1/T) Σₓ∈ℬ pᵢ(x)",
                "最后，我们把所有 fᵢ 和对应的 Pᵢ 两两相乘再求和，也就是做一个点积，然后乘上专家数量：",
                "__CODE__python::layer_routing_loss = num_experts * torch.dot(expert_frequencies, expert_prob_allocation)",
                "这一块就完成了（除了 α）：",
                "L_aux = α · N · Σᵢ fᵢ · Pᵢ",
                "辅助损失的代码就讲完了。我们把 calculate_moe_router_loss 过了一遍，也看过用 α（也就是 moe_router_loss_scale）缩放它的代码，于是我们有了一个带 MoE 辅助损失、用上一节数学的训练脚本。",
                "再说一次，希望这些图对理解有帮助。这类代码很容易扫一眼就有个模糊的理解，但我觉得如果想真正记住，一步步可视化发生了什么很重要。",
                "代码就位之后，接下来要探索的是 α 到底该取多少。",
            ],
            "fig_after": {
                "20": [{"src": "fig13.png", "caption": "图13（再贴一次）：expert_weights 的两个二维视角"}],
                "25": [{"src": "fig20.png", "caption": "图20：expert_weights 摊平后的两个二维视角"}],
                "26": [{"src": "fig21.png", "caption": "图21：expert_weights 摊平后只剩下一个二维视角"}],
                "32": [{"src": "fig22.png", "caption": "图22：expert_active_counts 只剩一个二维视角"}],
                "39": [{"src": "fig07.png", "caption": "图7（再贴一次）：routing_logits 的两个二维视角"}],
            },
        },
        {
            "type": "h2",
            "title": "二、寻找 alpha",
            "paras": [
                "在《Switch Transformers》论文里，他们写道：",
                "「最后，超参数 α 是这些辅助损失的一个乘性系数；在这项工作中我们取 α = 10⁻²，它大到足以保证负载均衡，又小到不会压过主要的交叉熵目标。我们按 10 的幂扫过 α 从 10⁻¹ 到 10⁻⁵ 的范围，发现 10⁻² 能快速平衡负载又不干扰训练损失。」",
                "但正如前面提到的，那是在他们单激活专家的设定下成立的；因为我有多个激活专家，我的辅助损失会更大。既然他们的「理想」每层损失是 1，而我计划的训练里是 2，那么用他们推荐值的一半、也就是 5 × 10⁻³，似乎合适。",
                "不过我也担心层数会带来干扰。",
                "前面看到，辅助损失是每层一个值，最后全部相加。我的「理想」每层损失是 2、有 12 层，那么全部层的理想值就是 24。",
                "他们给出了 α 的具体取值，却没说有多少层，也没说是否在不同层数下扫过不同取值。这看起来很奇怪。",
                "我决定按这样一个假设来做：他们发现随着层数增加，辅助损失的总贡献需要按比例放大。不过这只是我试图把论文里的信息拼起来得出的猜测，很可能不对。",
                "我很不确定，所以觉得明智的做法是自己做一次最小规模的扫描，取几个不同的 α，每个跑一小时训练，结束时看训练损失，也就是纯粹的交叉熵损失，衡量模型作为语言模型的本职工作做得多好，再看辅助损失，衡量专家使用有多均衡。",
                "我得到了这些结果：",
            ],
            "table": {
                "head": ["α", "训练损失", "辅助损失"],
                "rows": [
                    ["0", "6.152867", "53.38285"],
                    ["0.001", "6.166725", "30.00601"],
                    ["0.005", "<strong style=\"color:#0F4C81;\">6.106290</strong>", "25.21015"],
                    ["0.01", "6.160989", "24.78106"],
                ],
            },
        },
        {
            "type": "h3",
            "title": "2.1 扫描结果",
            "paras": [
                "我也生成了路由器使用图，就像前面那篇没有辅助损失、跑了两天的训练里给的那样。这里不全部放出来，只说结论：",
                "α = 0 时，从非常高的辅助损失就能预料到，图很快开始变红变白：它在专注少数专家、忽略其他专家。不过训练损失倒不算太差。",
                "α = 0.001 时，也就是 Switch Transformers 那个值的十分之一，按朴素换算应是我这边理想值的五分之一，负载均衡图没那么糟，但出现了零星的红点。我没法断言它在更长的训练里一定不能保持合理均衡。",
                "α = 0.005 看起来非常好：它的训练损失是所有选项里最低的，辅助损失也不算差，只比理想值 24 高了 1.2。",
                "到 α = 0.01，也就是 Switch Transformers 用的值，而他们的理想辅助损失只有我们的一半，此时虽然辅助损失继续下降，训练损失开始变差。这正好符合「训练开始把均衡看得比做出好模型更重要」时的预期。",
                "所以基于这些结果，当然也因为它与 Switch Transformers 论文的建议吻合，我决定用 α = 0.005。",
                "是时候训练这个东西了。",
            ],
        },
    ],

    "conclusion": [
        "**把辅助损失接进训练循环只多几行：算出 moe_router_loss，按 α 缩放后加到交叉熵损失上再反向传播。** 真正的工作量在于向量化：用 view 把 (batch_size, seq_len, num_experts) 摊成二维，用 > 0 得到激活掩码并沿列求和得到 fᵢ，softmax 后求和得到 Pᵢ，最后 num_experts * torch.dot(f, P) 就是这一层的辅助损失。",
        "α 不能照抄。Switch Transformers 用 10⁻²，但他们每 token 只激活一个专家、理想辅助损失是 1；这里是 2 个激活专家、12 层，理想值是 24。四组一小时扫描下来，0.005 的训练损失最低、辅助损失只比理想值高 1.2；0.01 开始牺牲训练损失，0 则很快把专家用成红白相间。下一篇是最终训练、结果对比与 IFT 评测。",
    ],

    "reference_url": "https://www.gilesthomas.com/2026/09/gpt-2-to-moe",
    "title": "从 GPT-2 到 MoE（五）：辅助损失的向量化实现与 α 的一小时扫描",
}

out_path = os.path.join(_article_dir, "article_data.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)
print(f"OK {out_path} ({len(json.dumps(DATA, ensure_ascii=False))} chars, {len(DATA.get('sections', []))} sections)")
