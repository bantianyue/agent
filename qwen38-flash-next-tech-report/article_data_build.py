# -*- coding: utf-8 -*-
"""Qwen3.8-Flash-Next 官方技术报告编译 build（≥80% 保留）"""
import json

DATA = {
  "title": "Qwen3.8-Next 架构设计：评价、效率与训练稳定性（技术报告精编）",
  "lead": [
    "这份 Qwen 官方技术报告描述 Qwen3.8-Flash-Next 的架构与消融：一个稀疏 MoE 模型，125B 参数、每 token 激活 6B，另有 510 亿参数的 n-gram embedding 表放在加速器之外。",
    "在十四个预训练基准上，模型在八个上领先 397B-A17B 前任、其余至多差 2.6 分，却只用 1/3 激活参数、1/3 训练 token、约 1/9 训练 FLOPs。token mixing 用 Gated DeltaNet（GDN）与 global attention 的逐层混合，每四层一个全注意力层；继续预训练时换为 Qwen 稀疏注意力（QSA）。"
  ],
  "summary": [
    {"key":"模型与效率","body":"稀疏 MoE 125B/激活6B + 51B n-gram 表（host 外放）。14 基准 8 个超 397B-A17B、其余差≤2.6 分，用 1/3 激活参数、1/3 token、约 1/9 FLOPs。上下文 1M 时 QSA 比密集注意力 prefill 快 7.6×、decode 快 4.9×（内核级）。"},
    {"key":"四大架构组件","body":"① GDN+全局注意力混合（每4层1全注意力，线性压缩状态+直接 token 检索）；② QSA 稀疏注意力（微块粒度 + 压缩轻量 indexer，索引成本随长度下降）；③ Gated Residual（残差流 4 分支 + 逐元素 gate）；④ N-gram embedding 层（host 预取、近零额外 FLOPs/延迟）。"},
    {"key":"优化与稳定性","body":"Muon 优化二维权重（8 步 Newton-Schulz）；新架构+优化器把最优 lr 和 batch size 拉高、取消 batch warmup。4× 最优 lr 压力下旧结构频繁尖峰、新配方全程稳定。全规模训练零 loss 尖峰、无需 qk-clip/SwiGLU-clip。"}
  ],
  "sections": [
    {"type":"h2","title":"引言：用更少算力保住旗舰质量","paras":[
      "Qwen3.8-Flash-Next 是一个稀疏 MoE 模型：125B 总参数、每 token 激活 6B，另有 510 亿参数的 n-gram embedding 表放在加速器之外。设计目标：在远低于上一代 397B-A17B 旗舰的算力预算下保住质量。",
      "在十四个横跨知识、STEM、推理、编码、多语言的预训练基准上，base 模型在八个上领先前任、其余六个最多差 2.6 分（Tab 11），而每 token 激活约 1/3、训练约 1/3 token、训练 FLOPs 约 1/9。",
      "一个架构改动同时碰三件事：下游任务能力、训练和服务的花销、以及训练运行在规模化下是否最优且稳定。因此评估每个候选改动都沿三轴：loss+下游基准；训练/prefill/decode 的成本；对最优超参和训练稳定的影响。",
      "四个架构组件各解决一个不同瓶颈。token mixing 用 GDN（线性成本把前缀压缩成固定大小状态）与 global attention（每四层一个、保留任何有限状态记忆无法精确复现的直接 token 级检索）的逐层混合。继续预训练时全注意力层换成 QSA——继承稀疏注意力路线的思路，但按微块粒度用压缩轻量 indexer 打分，让索引成本本身随序列长度下降。",
      "残差流加宽到四分支、并经过逐元素 gate 读取——称为 Gated Residual（GR）：加宽给残差路径加容量，gate 决定容量花在哪、同时提供训练稳定的 rescaling。容量进一步由单个 n-gram embedding 层在骨干外增加（表从 host 内存预取），以可忽略的额外每 token FLOPs 和延迟扩参数量。"
    ],"fig_after":{}},
    {"type":"h2","title":"评估、效率与优化的总览","paras":[
      "**评估（Evaluation）**：loss 与下游精度并非总同向。扩大 n-gram 词表单调降 loss、但下游精度饱和（Tab 8/9，固定参数预算下 loss 最优偏离精度最优）。预测残差读写权重只带来边际 loss 降、却有明显基准增益（§2.2）。有些分歧后期才浮现：每块只留门控最高的两分支几乎不伤预训练 loss 却随进一步训练退化；去掉全注意力层位置编码在预训练期不可分、却影响后期生成质量（§2.1.1）。",
      "**效率（Efficiency）**：训练里 FlashQLA 在 GPU 上相对 Triton 基线有 2–3× 前向、约 2× 反向加速（§2.1.1）。Muon 有自己的工程成本（§3.1）。推理里 prefill 由整上下文注意力主导，QSA 把 key 序列压缩 r 倍、把 indexer 成本从 O(n²) 降到 O(n²/r)；decode 由内存流量主导，GDN 层用固定大小循环状态、GR 去掉 branch-mixing 算子、残差状态支持 FP8。上下文 1M 时 QSA 内核级比密集注意力 prefill 快 7.6×、decode 快 4.9×。",
      "**优化（Optimization）**：Muon 作用于充当线性映射的二维权重；输入/n-gram embedding、输出头、MoE router 和 GR 低秩投影留在 AdamW（正交化对其不实际或无益）。融合参数在正交化前先拆分（正交化拼接矩阵会把不相关子块混合奇异方向）。新架构+优化器也移动最优超参，重新拟合 Qwen3.5 系列用的缩放律（§3.2）——预测更大的 batch size 和学习率，两者都单独验证确认：更大 batch 提升规模并行吞吐、更大 lr 提升收敛。早期 ramp batch size 不比直接到目标好、还多花 18.8% 优化器步，所以不用它。",
      "**训练稳定（Training Stability）**：对复现规模化不稳定做压力测试——提高 lr（Wortsman et al. 2023）并保持恒定 lr。判据：新配方在同等压力下至少和它替代的世代一样稳。4× 最优 lr 时旧结构频繁尖峰、新配方全程稳定（§3.3）。隔离 GR 的 gate 证实它是相对 Qwen3.5 稳定裕度的关键贡献者。直接结果：全规模训练 Qwen3.8-Flash-Next 平滑进行、零 loss 尖峰或梯度范数异常波动，不靠 qk-clip 或 SwiGLU-clip 这类显式裁剪。"
    ],"fig_after":{}},
    {"type":"h2","title":"架构：注意力混合（2.1）","paras":[
      "**GDN 混合架构（2.1.1）**：完整自注意力给每个前序 token 直接基于内容的访问，但 token 混合成本随序列长度二次方增长、KV cache 在自回归生成时线性增长。滑窗注意（SWA）用有界局部感受野替代全局访问、降计算和 cache，但窗外信息只能经深度间接传播——造成高效局部处理与持久内容相关记忆之间的张力。",
      "GDN 把前缀压缩成固定大小循环状态、并依当前内容更新状态，而交错的全局注意力层保留任何有限状态循环记忆都难以精确复现的直接 token 级检索。相对全注意力 Transformer 基线，GDN 混合在 9 个选定基准里改进 8 个；相对 SWA 混合在九个里强于七个——支持混合设计。",
      "Gated Delta Recurrence：线性注意力可理解为存 key-value 关联的快速权重记忆。GDN 依门控 delta 规则维护状态 S_t：decay gate α_t（数据相关、控制遗忘）、write gate β_t（控制 delta 更新）。投影的 query/key/value 流经短因果卷积，query/key 在门控 delta 循环前 L2 归一化，sigmoid 输出门调制零心 RMSNorm 输出。",
      "相对全注意力基线，GDN 混合改进了所选基准；混合设计让信息在高效局部处理与直接 token 检索间取得平衡（详见 §2.1.2 继续预训练到 QSA）。"
    ],"fig_after":{}},
    {"type":"h2","title":"架构：QSA 稀疏注意力（继续预训练）","paras":[
      "当模型扩展到更长上下文，全注意力的索引成本成为瓶颈。Qwen3.8-Flash-Next 在继续预训练时把全注意力层替换为 Qwen 稀疏注意力（QSA）：按微块粒度、用压缩轻量 indexer 对上下文打分，使索引成本本身随序列长度下降。",
      "QSA 压缩 key 序列：每个位置产生少量索引 key，indexer 先粗选微块、再对选中块做精确稀疏注意力。这把小段的 cache 容量换大幅更低的 long-context 计算和内存流量。",
      "**QSA 评估**：对比 Qwen3.8-Flash-Next 带 QSA vs 其全注意力基线（Tab 2，跨知识/STEM/推理/多语言/编码）。QSA 全面小幅甚至优于全注意力：MMLU-Pro 73.7 vs 72.9、SuperGPQA 52.1 vs 51.7、MATH 71.6 vs 69.8、GSM8K 92.2 vs 91.0、BBH 91.6 vs 90.4、EvalPlus 72.3 vs 70.8、MultiPL-E 79.8 vs 78.4。",
      "**效率**：QSA 内索引成本由压缩 key 序列决定，而非完整长度。上下文 1M 时 QSA 内核级 prefill 比密集注意力快 7.6×、decode 快 4.9×。MTP 模块跨 spec decode 步复用 QSA 索引（见架构图注），进一步降低 draft 模型推理成本。"
    ],"fig_after":{}},
    {"type":"h2","title":"架构：Gated Residual 与 N-gram 嵌入","paras":[
      "**Gated Residual（GR，2.2）**：残差流加宽到四分支、并逐元素 gate 读取。加宽加容量，gate 决定容量花在哪并供应训练稳定所需的 rescaling。消融：相对参考 no-GR 模型，加 GR 在某些配置降 loss（Tab 5/10 的残差读写消融）。",
      "限制每块只留门控最高的两残差分支在预训练 loss 上几乎免费、却随继续训练退化——说明 GR 的分支容量在后期训练有用。对固定参数预算，损失最优和精度最优不一致（Tab 8/9）；而预测残差读写权重（两分支同时、如 Layer 0 MLP 到 layer 1）带来边际 loss 降但明显基准增益。",
      "**N-gram 嵌入（2.3）**：在骨干外加一个 hash-addressed 可学习 n-gram embedding 层（表从 host 内存预取），扩参数量而每 token FLOPs 和延迟近乎为零。消融放置/数量：单层变体横跨浅层到深层（Layer 2 是选定位置），扩大 n-gram 词表单调降 loss、下游精度饱和。",
      "这些 embedding 表共 510 亿参数、放在加速器之外——是模型容量很大的一块、却不进骨干，只按局部上下文做稀疏查找。"
    ],"fig_after":{}},
    {"type":"h2","title":"优化与训练稳定性（3）","paras":[
      "**优化器（3.1）**：Muon 应用到充当线性映射的二维权重；输入/n-gram embedding、输出头、MoE router、GR 低秩投影留在 AdamW。其每参数 FLOPs 依矩阵形状而非参数个数，所以数据并行梯度缓冲按估算正交化成本重分区；融合参数拆分后 step 碎成许多小核，step 被捕获进 CUDA graph。Newton-Schulz 迭代设 8 步，偏好在压力下额外稳定。",
      "**超参缩放（3.2）**：新架构+优化器移动最优超参，重拟合缩放律。预测更大 batch size 和更大 lr，都验证确认。批大小 ramp 不比直接到目标好（还 +18.8% 步数），故不用。",
      "**稳定压力测试（3.3）**：4× 最优 lr 的恒定 lr 压力下，旧结构频繁尖峰、新配方全程稳定。隔离 GR gate 证实它是相对 Qwen3.5 稳定裕度的关键贡献者。全规模训练零 loss 尖峰、无梯度范数异常波动、不依赖显式裁剪。"
    ],"fig_after":{}},
    {"type":"h2","title":"模型对比与结语","paras":[
      "Tab 11 把 Qwen3.8-Flash-Next-Base 与两个强 base 对比（含 397B-A17B 前任），跨广泛能力范围。核心叙事：更小激活规模+更少训练 token/FLOPs 下在多数基准持平或领先、其余差距不超过 2.6 点。",
      "结语要点：loss/基准/效率/稳定构成一个设计问题，联合求解得到同时更高效、更能、更稳的配方。文中反复强调三轴分歧处的落点——loss 与下游不同向、容量与 FLOPs 权衡、稳定性与最优超参。",
      "（技术报告另有完整架构图、Formula 消融表、多语言及后训练评测和参考文献，可在原文 PDF 查看。）"
    ],"fig_after":{}}
  ],
  "conclusion": [
    "Qwen 这份官方技术报告把 Qwen3.8-Flash-Next 的设计哲学讲透：**在 397B 前任约 1/9 的训练 FLOPs 下保住旗舰质量**——125B/激活6B 的稀疏 MoE + 51B 外部 n-gram 表，十四个预训练基准八个领先、其余只差 2.6 点。四个组件各解一个瓶颈：GDN 压缩循环状态（线性）、每四层一个全注意力层（直接检索）、QSA 稀疏注意力（索引成本随长度下降，1M 时长上下文 prefill 7.6×/decode 4.9×）、GR 四分支残差 + gate（容量+稳定）、N-gram 层 host 预取（近零 FLOPs 扩容量）。",
    "方法论上最值得学的是它的三轴评估框架：每个改动都沿「loss+下游」「训练/prefill/decode 成本」「最优超参+稳定性」三轴检验，并诚实标记三轴分歧处（n-gram 词表 loss 单调降但精度饱和；分支裁剪预训练免费却后期退化）。优化侧 Muon 配大 batch/lr、取消 warmup、8 步 Newton-Schulz 换稳定——4× lr 压力下新配方全程无尖峰、全规模训练零 loss spike、不靠 qk-clip。对做 LLM 架构/训练/效率的人，这是「高效、更能、更稳三件事联合设计」的教科书案例。"
  ],
  "reference_url": "https://github.com/QwenLM/Qwen3.8-Flash-Next/blob/main/tech_report.pdf"
}

with open("article_data.json", "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=1)
print("✅ 写入 article_data.json")
