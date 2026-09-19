#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""article_data_build.py — training-agents-sft-from-scratch（X Article 全量中译）"""

import json
import os
import sys

_article_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()

_PRE = (
    "<pre style=\"background:#f5f5f5;padding:12px 16px;border-radius:4px;"
    "overflow-x:auto;font-family:Consolas,Monaco,'Courier New',monospace;"
    "font-size:13px;line-height:1.5;margin:1em 4px;border-left:4px solid #e0e0e0;\">"
    "<code>{}</code></pre>"
)

CODE_DEPS = "pip install torch transformers"

CODE_LOAD = r'''import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

model_name = "Qwen/Qwen3-0.6B"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(model_name, dtype=torch.bfloat16).to("cuda")'''

CODE_TEMPLATE = r'''messages = [
    {"role": "user", "content": "Summarize in one word: always keep answers concise."},
    {"role": "assistant", "content": "Concise."},
]

enc = tokenizer.apply_chat_template(
    messages,
    return_dict=True,
    return_assistant_tokens_mask=True,
    return_tensors="pt",
).to("cuda")

input_ids = enc["input_ids"]
assistant_masks = torch.tensor(enc["assistant_masks"], device="cuda")

labels = input_ids.clone()
labels[assistant_masks == 0] = -100'''

CODE_LOOP = r'''import torch.nn.functional as F

optimizer = torch.optim.AdamW(model.parameters(), lr=1e-5)
model.train()

for step in range(30):
    logits = model(input_ids).logits           # (1, T, vocab_size)
    shift_logits = logits[:, :-1, :]            # drop last position
    shift_labels = labels[:, 1:]                # drop first label
    loss = F.cross_entropy(
        shift_logits.reshape(-1, shift_logits.size(-1)),
        shift_labels.reshape(-1),
        ignore_index=-100,                      # skip masked tokens
    )
    loss.backward()
    optimizer.step()
    optimizer.zero_grad()'''

DATA = {
    "title": "训练智能体第一课：从零手写 SFT 训练循环",
    "summary": [
        {"key": "核心观点", "body": "SFT 就是带掩码的下一 token 预测，模型学的是复现示范过的输出，而不是分辨答案好坏。"},
        {"key": "关键机制", "body": "提示与回答拼成一条序列，提示位置的标签换成 -100 直接跳过，损失和梯度只由回答 token 贡献。"},
        {"key": "动手规模", "body": "Qwen3-0.6B 加纯 PyTorch，完整循环不到 100 行，一张 16 GB 显存的 GPU 就能跑完。"},
    ],
    "lead": [
        "这是「训练智能体」系列的第一篇，后面会配文章和直播逐步加深；第一场直播的主题是用自己跑出来的 traces 微调智能体，完整录像已经放到 YouTube 频道。",
        "SFT 做的事就是模仿：给模型成对的提示和回答，让它学会在看到提示时把对应回答产出来。这些内容我在 hf.co/learn 上写过，这里只留一个最小版本。文章用纯 PyTorch 搭一个不到 100 行、不套任何训练框架的 SFT 循环，为的是让你看清训练信号到底是什么、它怎么改变模型。",
    ],
    "sections": [
        {
            "type": "h2",
            "title": "环境准备",
            "paras": [
                "例子跑在一张 16 GB 显存的 GPU 上，免费或低价的云端 notebook 就能提供这种配置。模型选 Qwen3-0.6B，小到可以快速反复迭代。这里的目标是看清机制，而不是真训出一个强模型。",
                "依赖只有几个：",
                _PRE.format(CODE_DEPS),
                "用 bfloat16 加载模型，然后放到 GPU 上：",
                _PRE.format(CODE_LOAD),
            ],
        },
        {
            "type": "h2",
            "title": "下一 token 预测就是监督信号",
            "paras": [
                "token 是文本的一个片段，通常是一个词或词元，分词器把它映射成一个整数。语言模型读入一串 token，在每个位置上输出一个关于下一个 token 的概率分布。下图用四 token 序列说明这件事：每个位置读取它之前的全部 token，预测紧随其后的那一个。",
                "训练把这些预测当作监督信号。每个位置上模型有一个预测分布，也有一个目标，也就是真实出现的下一个 token，损失就是两者之间的交叉熵。模型自信而且预测正确时，损失接近零；同样是自信但预测错了，损失就更大。",
                "这就是 SFT 里全部的学习信号。它没有单独区分「好答案」和「坏答案」，只有示范里写明应该出现的下一个 token。由于信号是逐 token 的，回答里每一个 token 都会贡献一份梯度。",
            ],
            "fig_after": {
                "0": [{"src": "fig01.png", "caption": "图1: 下一 token 预测。"}],
            },
        },
        {
            "type": "h2",
            "title": "数据格式：提示、回答与掩码",
            "paras": [
                "一条 SFT 样本由两部分组成。提示是输入，比如用户的问题；回答是你希望模型产出的内容。放到智能体场景里，这两部分被打包进 traces。你要让模型学会生成回答，而不是重新生成提示，所以损失只应该落在回答 token 上。",
                "掩码就是用来做这件事的。把提示和回答拼成一条序列喂给模型，同时告诉损失忽略提示所在的位置。PyTorch 的交叉熵用一个哨兵标签 -100 来实现，遇到它直接跳过。掩码示意图展示了这种对齐关系：输入行是提示 token 接回答 token，标签行在提示位置全是 -100，在回答位置是对应的真实 token id。",
                "下面这段代码把聊天模板套到一段短对话上，再根据 assistant 掩码构造标签：",
                _PRE.format(CODE_TEMPLATE),
                "messages 列表保存整段对话，每一轮一个 dict。apply_chat_template 把它渲染成一条完整的 token 序列，return_assistant_tokens_mask 标出哪些 token 属于 assistant 的输出。其余位置一律置为 -100。",
            ],
            "fig_after": {
                "1": [{"src": "fig02.png", "caption": "图2: SFT 的标签掩码。提示位置被替换成 -100，损失只落在回答 token 上。"}],
            },
        },
        {
            "type": "h2",
            "title": "用纯 PyTorch 写训练循环",
            "paras": [
                "这个循环有五个步骤，示意图里画了出来：把序列送进模型拿到 logits，错开 logits 和标签让每个位置对齐它所预测的 token，计算交叉熵，反向传播，然后推进一步优化器。",
                "logits 输出时每个输入位置对应一个分布。位置 t 预测的是位置 t+1 的 token，所以丢掉最后一个 logit 和第一个标签，两者就对齐了：",
                _PRE.format(CODE_LOOP),
                "这就是一个完整的 SFT 步骤。loss.backward() 为每个权重填上损失的梯度，optimizer.step() 顺着梯度迈一小步把损失压低。这里把交叉熵完整写出来，是为了让错位和掩码不被藏在函数里。",
            ],
            "fig_after": {
                "0": [{"src": "fig03.png", "caption": "图3: SFT 训练循环。"}],
            },
        },
        {
            "type": "h2",
            "title": "值得带走的结论",
            "paras": [
                "SFT 的本质是模仿：把该做的事演示给模型看，再训练它照着复制。机制是带掩码的下一 token 预测，回答的每个 token 贡献一项交叉熵和一个梯度，提示一个都不贡献。它能力的天花板由数据决定，因为只靠 SFT 训出来的模型，无法稳定产出示范里从未出现过的行为。",
                "这让 SFT 稳定且样本效率高，也让它的成本等于写好并验证回答的成本。能演示出想要的输出时，SFT 就是最简单可行的工具；只能给行为打分、却很难演示出最优版本时，就该轮到强化学习了，不过那是另一篇文章的话题。",
            ],
        },
    ],
    "conclusion": [
        "**SFT 是模仿，不是评判。** 它只教模型复现示范过的行为，代价和上限都写在数据里。",
        "机制就三件事：回答的每个 token 贡献一项交叉熵和一个梯度，提示位置的标签统一换成 -100 被跳过，优化器把这份梯度往下压一小步。",
        "想清楚这一点，选型就有依据了：能拿出想要的输出就做 SFT，只有评分标准而拿不出最优样本时，才去考虑强化学习。",
    ],
    "reference_url": "https://x.com/ben_burtenshaw/status/2067615361428545566",
}

out_path = os.path.join(_article_dir, "article_data.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)
print(f"OK {out_path} ({len(json.dumps(DATA, ensure_ascii=False))} chars, {len(DATA['sections'])} sections)")
