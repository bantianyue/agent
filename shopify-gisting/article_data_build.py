# -*- coding: utf-8 -*-
"""Shopify Gisting 编译 build"""
import json, os, sys

DATA = {
 "title": "Gisting：把 LLM Agent 上下文压进一组 token，提吞吐降成本",
 "lead": [
  "Gisting 把上下文压缩成一组学习到的 token，在保留质量的同时让模型更快更便宜。",
  "System prompts 每个请求可以占数千 token。更长的 prompt 意味着更慢、更贵的推理。这导致在专用硬件上服务模型时，为容纳同样流量需要更多 GPU。",
  "我们对 gisting 的实现（最初由 Wingate, Shoeybi 和 Sorensen 在《Prompt Compression and Contrastive Conditioning for Controllability and Toxicity Reduction in Language Models》中提出）让我们能以短 prompt 的成本获得长 prompt 的行为优势。",
  "通过 gisting，我们把 Sidekick GraphQL agent 的 system prompt 从约 **6,000 token 砍到约 1,500 gist token（4:1 压缩）**，且不损失预测质量。我们通过知识蒸馏学习一组特殊 token 的嵌入，推理时用它们替换 system prompt 来实现这一点。",
  "把 system prompt 4:1 压缩成 gist token 带来的服务增益显著。在 350 RPM 下，median time to first token（TTFT）从 438ms 降到 354ms，median 端到端请求延迟从 6.8s 降到 4.2s，吞吐从 20.2 升到 23.4 queries per second（QPS）。这些增益让我们能为 GraphQL agent 的流量减少分配的 GPU 数。"
 ],
 "summary": [
  {
   "key": "核心机制",
   "body": "gist token 是加入模型词表的特殊 token。用知识蒸馏训练嵌入序列：teacher pass 看完整自然语言 prompt 得到 logits，student pass 换 gist tokens 再跑一遍，用 KL 散度最小化差异。4:1 压缩=每 4 个 prompt token 加 1 个 gist token，只训练嵌入、冻结权重。"
  },
  {
   "key": "结果",
   "body": "350 RPM 下：TTFT 降 19%（438→354ms）、E2E 降约 38%（6.8→4.2s）、吞吐 +16%（20.2→23.4 QPS）、生产 GPU 少 14%。部署简单：写回 embedding 矩阵 + 注册特殊 token，推理时仅请求侧换 prompt。"
  },
  {
   "key": "Autoresearch 发现",
   "body": "初始化用 prompt chunk 均值（非随机噪声）→ 初始 loss 降 7×；4:1 是质量开始下降的最优压缩比；损失归一化按 batch 平均（per token 平均会幻觉）；预计算 teacher logits + 预 tokenize 把单次训练从 30h 砍到 6h。"
  }
 ],
 "sections": [
  {
   "type": "h2",
   "title": "Gisting 如何工作",
   "paras": [
    "**gist token** 是我们加入模型词表的特殊 token。我们训练嵌入序列，使它们替换进上下文后诱导模型表现得像看过了完整 prompt。在 4:1 压缩下，每四个 prompt token 加一个 gist token。我们冻结模型权重，只训练 gist 嵌入。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig01.png",
      "caption": "图 1：Gisting 如何工作——训练 gist token 嵌入序列，使其替换进上下文后模型表现得像看过完整 prompt。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "知识蒸馏训练",
   "paras": [
    "我们通过知识蒸馏学习 gist 嵌入。对每条轨迹跑两次前向。**teacher pass** 中模型看到完整自然语言 prompt，为模型响应中每个位置导出 teacher logits。**student pass** 中我们把完整 prompt 换成 gist tokens，再跑同一模型，导出对应每个 teacher 响应位置的 student logits。",
    "我们用 teacher logits 和 student logits 之间的 KL 散度训练 gist 嵌入，直到 student 的预测紧密匹配 teacher。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig02.png",
      "caption": "图 2：Teacher vs student 预测——teacher 看完整 prompt，student 看 gist tokens，KL 散度对齐。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "部署 gisted 模型很简单",
   "paras": [
    "训练结束时，我们把 gist 嵌入直接写进模型的 embedding 矩阵，并把新 gist token 注册为模型 tokenizer 的特殊 token。模型像任何其他模型一样在推理时加载和运行：没有自定义 attention mask、额外 encoder 或特殊服务路径。",
    "唯一的推理时变化在请求侧：把 prompt 换成 gist token 字符串。压缩的全部成本只在训练时付一次。"
   ],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "为什么 prefix caching 不够",
   "paras": [
    "Gisting 和 prefix caching 的优势并不互斥。所有现代服务引擎维护 KV cache，存储先前见过的序列的 keys 和 values。当新请求包含缓存中存在的序列（通常包括 system prompt）时，该序列的 KV tensors 被取回而非重算。",
    "虽然 prefix caching 强大，但它不消除 decode 成本。模型每生成一个 token，该 token 就 attend 序列中的每个 key，无论是否缓存。因为 decode 受内存带宽约束，每个生成的 token 必须从高带宽内存流式读整个 KV cache，而那个读取随缓存序列长度线性增长。",
    "Gisting 减少 attention 计算和 KV cache 读取的成本，后者在 batch 变大时对吞吐尤其有影响。",
    "Gisting 和 prefix caching 的优化叠加，我们在实验和生产服务栈中两者都用。"
   ],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "Autoresearch 找到配方",
   "paras": [
    "为调优超参数，我们把一个 autoresearch loop 指向 trainer。它提出配方、训练 gist 嵌入、评估结果模型、重复。",
    "在 autoresearch 循环中，三个优化尤其影响大：",
    "**初始化**：不用随机噪声初始化嵌入，而是把 system prompt 拆成 k 长度的序列（k 由 k:1 压缩比导出），用第 n 个 system prompt chunk 的均值初始化第 n 个 gist 嵌入。这个优化把初始 loss 降了一个因子 7。",
    "**压缩**：试验一系列压缩比后，我们找到预测质量开始下降的比值（对我们的领域复杂度，4:1 是最优比；其他领域不同）。",
    "**数据量和多样性**：策展大规模多样化数据集补上剩余缺口。",
    "除了精简超参数调优，autoresearch 还帮我们在训练基础设施中实现几个关键优化。第一个是我们如何归一化 loss：按每响应 token 平均会让模型幻觉，而按 batch 平均保留长响应的更多信号、产生稳定嵌入。第二个是速度：预计算 teacher logits 和预 tokenize 数据把一次完整运行从三十小时砍到六小时。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig03.png",
      "caption": "图 3：Autoresearch 进展——自动循环提出配方、训练、评估、重复，找到 4:1 最优压缩比和初始化/归一化优化。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "回报：延迟和吞吐",
   "paras": [
    "我们跑了对照同一模型压缩 prompt 与完整 prompt 的负载测试。",
    "Gisting 相对完整 prompt 带来显著延迟增益，且随请求并发上升、batch 变大，差距更明显。在 350 RPM 下，TTFT 降 19%，E2E 延迟降约 38%，吞吐升 16%。",
    "实践中，那 16% 的吞吐增益直接转化为我们生产工作负载的 GPU 节省。用服务 GraphQL 流量的硬件配置，我们能用 gisting 少用 14% 的 GPU。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig04.png",
      "caption": "图 4：结果——350 RPM 下 TTFT 降 19%、E2E 降约 38%、吞吐 +16%、GPU -14%。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "Gisting 与持续学习",
   "paras": [
    "Gisting 也很好融入 Shopify 的持续学习循环。一旦我们有了一个模型的蒸馏 gist 嵌入，就可以把这个模型当作持续学习的新起点。我们可以用 gist 嵌入作为前缀做后训练，把梯度更新同时应用到模型权重和 gist 嵌入。",
    "通过在增量数据上同时优化权重和 gist 嵌入，我们可以持续校准和改进模型，而无需每次都从头蒸馏 gist 嵌入的计算负载。"
   ],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "要点",
   "paras": [
    "长 system prompts 有用但贵。Gisting 让 agent 用一小部分 token 利用广泛指令的所有优势，降低延迟和 GPU 开销。",
    "在 GPU 需求超过供给的近期时代，每个推理优化都重要，但我们也拒绝在质量上妥协。Gisting 两者都给，在 Shopify 它是新标准。"
   ],
   "fig_after": {}
  }
 ],
 "conclusion": [
  "Shopify 这篇 Gisting 工程实录很实在：把 Sidekick GraphQL agent 的 6,000-token system prompt 压成 1,500 个 gist token（4:1），TTFT 降 19%、E2E 降约 38%、吞吐 +16%、生产 GPU 少 14%。",
  "机制本身简单（特殊 token 嵌入 + 知识蒸馏，冻结权重只训嵌入），但有三个值得抄的工程点：**初始化用 prompt chunk 均值而非随机噪声**（loss 降 7×）、**loss 按 batch 平均而非 per token**（per token 平均会幻觉）、**预计算 teacher logits + 预 tokenize 把训练从 30h 砍到 6h**。",
  "还有一个反直觉的洞察：**prefix caching 不消除 decode 成本**——每生成一个 token 仍要 attend 所有 key、流式读整个 KV cache，读取随缓存长度线性增长，而 gisting 直接砍这个。两者叠加使用，不是二选一。"
 ],
 "reference_url": "https://shopify.engineering/gisting"
}

with open("article_data.json", "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=1)
print(f"✅ 写入 article_data.json")