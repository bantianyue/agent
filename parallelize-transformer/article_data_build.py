# -*- coding: utf-8 -*-
"""How to Parallelize a Transformer 编译 build（100%保留）"""
import json, os, sys

DATA = {
 "title": "如何并行化 Transformer 训练：数据并行、FSDP、张量并行、专家并行与流水线全解",
 "lead": [
  "这篇是 Edward Z. Yang（PyTorch 核心开发者）对 Google DeepMind《How to Scale Your Model》Part 5 的「可探索」改编——每个数字都能拖拽、实时计算。它回答了训练大模型时的核心问题：增加芯片能否线性提升吞吐？什么时候通信会成为瓶颈？",
  "文章覆盖五类常见并行方案：纯数据并行、全分片数据并行（FSDP/ZeRO）、张量并行、专家并行（MoE）和流水线并行。对每种都给出通信成本分析、何时成为瓶颈的判据，以及一批可拖拽的实时计算可视化。",
  "核心洞察是「roofline」思维：每个方案都在两座钟之间赛跑——MXU 的算力时钟 vs 网络的通信时钟。通信若能藏进计算之下就免费，戳出计算就浪费硅。"
 ],
 "summary": [
  {
   "key": "核心判据",
   "body": "数据并行/FSDP：每芯片批大小 B/DP > C/W（网络算力强度）即计算受限。张量并行：TP < F/(C/W)，与批大小无关。混合：B/N > α²/2F。"
  },
  {
   "key": "MoE 修正",
   "body": "MoE 模型 E 个专家、每 token 激活 k 个：FLOPs 走 k·F、权重通信走 E·F，把数据并行每芯片批大小下限放大 E/k 倍（如 OpenAI OSS 模型 k=4/E=128 时高达 79,200 tokens）。"
  },
  {
   "key": "实战配方",
   "body": "DeepSeek V3：EP64·PP16·ZeRO-1 DP2，3 万 tokens/GPU；Llama 3.1 405B：TP8·PP16·DP128，977 tokens/GPU。批大模型小则简单，批小模型大则需混合方案。"
  }
 ],
 "sections": [
  {
   "type": "h2",
   "title": "什么是缩放：从单芯片到集群",
   "paras": [
    "「模型缩放」的目标是增加训练或推理用芯片数，同时实现吞吐量的成比例线性提升——这称为强扩展。单芯片性能取决于内存带宽与 FLOPs 的权衡；集群级性能则取决于通过把芯片间通信与有用 FLOPs 重叠来隐藏通信。这不平凡：增加芯片数增加了通信负载，同时减少了可用于隐藏它的每设备计算量。",
    "如第 3 节所见，分片矩阵乘法常需要昂贵的 AllGather 或 ReduceScatter，会阻塞 TPU 做有用工作。本节目标是找出这些何时变得「太贵」。",
    "我们讨论五种常见并行方案：纯数据并行、FSDP/ZeRO 分片、张量并行（也称模型并行）、专家并行（MoE）和流水线并行。对每种方案展示我们付出的通信成本、以及该成本在哪个点开始成为计算瓶颈。聚焦通信上界——因为内存容量约束虽重要，但用重计算（激活检查点）和大量芯片预训练时通常不构成约束。本节可以只关注芯片间通信成本：只要单芯片 batch 足够大，HBM 到 MXU 的数据传输已与计算重叠。"
   ],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "符号表：模型参数",
   "paras": [
    "我们用以下记号简化计算。",
    "**模型参数记号**：D 是 d_model（隐藏维/残差流维）；F 是 d_ff（feedforward 维）——按本页约定指**一个专家**的宽度（稠密时 = d_ff），数学运行在 k·F 上、权重持有 E·F、原文方程是 E=k=1 的情形；B 是 batch 维（batch 中 token 数，总量非每设备）；T 是序列长度；L 是层数。"
   ],
   "table": {
    "head": [
     "记号",
     "含义（模型参数）"
    ],
    "rows": [
     [
      "D",
      "d_model（隐藏维/残差流维）"
     ],
     [
      "F",
      "d_ff（feedforward 维）；指一个专家的宽度（稠密时 = d_ff）"
     ],
     [
      "B",
      "Batch 维（batch 中 token 数；总量，非每设备）"
     ],
     [
      "T",
      "序列长度"
     ],
     [
      "L",
      "模型层数"
     ]
    ]
   }
  },
  {
   "type": "h2",
   "title": "符号表：硬件特征",
   "paras": [
    "**硬件特征记号**：C 是每芯片 FLOPS/s；W 是网络带宽（每 TPU mesh 轴双向 / GPU 或节点单向出口，常用 W_ici 或 W_dcn 下标）；DP 是数据并行 mesh 轴的芯片数（原文的 X）；TP 是张量并行 mesh 轴的芯片数（原文的 Y）；Z 是第三 mesh 轴的芯片数；PP 是流水线阶段数（pipelining 节的 Z）；EP 是专家并行度（第 12 章的 Z）。"
   ],
   "table": {
    "head": [
     "记号",
     "含义（硬件特征）"
    ],
    "rows": [
     [
      "C",
      "FLOPS/s 每芯片"
     ],
     [
      "W",
      "网络带宽（每 TPU mesh 轴双向 / GPU 或节点单向出口，常写作 W_ici 或 W_dcn）"
     ],
     [
      "DP",
      "数据并行 mesh 轴的芯片数（原文的 X）"
     ],
     [
      "TP",
      "张量并行 mesh 轴的芯片数（原文的 Y）"
     ],
     [
      "Z",
      "第三 mesh 轴的芯片数"
     ],
     [
      "PP",
      "流水线阶段数（pipelining 节的 Z）"
     ],
     [
      "EP",
      "专家并行度（第 12 章的 Z）"
     ]
    ]
   }
  },
  {
   "type": "h2",
   "title": "前沿模型表：从稠密到 MoE",
   "paras": [
    "原文例子是稠密 LLaMA 时代的模型；前沿已转向 Mixture-of-Experts。形状取自各模型在 Hugging Face 发布的 config.json，参数总量取自其 safetensors 元数据（2026 年 8 月检索）。E 和 k 计入共享专家，所以 k·F 是这些架构代表的激活宽度。",
    "跨受支持的实时 MoE 预设，每专家 F 只是 2,048 或 3,072，激活宽度 k·F 聚类在 15k 到 25k 之间——即使总参数从几千亿到几万亿。由于本章后面的张量并行界随激活宽度 k·F 缩放，这个聚类解释了为什么 TP 极限在所有前沿预设上看起来如此相似。K3 保留为参考行，但其 latent-MoE 形状故意不加载进公式。"
   ],
   "table": {
    "head": [
     "模型",
     "参数",
     "D",
     "F",
     "激活 k·F",
     "L",
     "E",
     "k"
    ],
    "rows": [
     [
      "LLaMA-3 70B（章默认）",
      "70.6B",
      "8,192",
      "28,672",
      "28,672",
      "80",
      "1",
      "1"
     ],
     [
      "LLaMA-2 13B",
      "13.0B",
      "5,120",
      "13,824",
      "13,824",
      "40",
      "1",
      "1"
     ],
     [
      "Gemma 7B",
      "8.54B",
      "3,072",
      "24,576",
      "24,576",
      "28",
      "1",
      "1"
     ],
     [
      "DeepSeek-V3",
      "685B",
      "7,168",
      "2,048",
      "18,432",
      "61",
      "257",
      "8+1"
     ],
     [
      "Kimi K3（仅参考）",
      "2.78T",
      "7,168",
      "3,072",
      "55,296",
      "93",
      "896+2",
      "16+2"
     ],
     [
      "GLM-5.2",
      "753B",
      "6,144",
      "2,048",
      "18,432",
      "78",
      "257",
      "8+1"
     ],
     [
      "DeepSeek-V4-Pro",
      "1.60T",
      "7,168",
      "3,072",
      "21,504",
      "61",
      "385",
      "6+1"
     ],
     [
      "Qwen3.8-2.4T-A95B",
      "2.45T",
      "8,192",
      "2,048",
      "22,528",
      "92",
      "513",
      "10+1"
     ],
     [
      "Inkling",
      "952B",
      "6,144",
      "3,072",
      "24,576",
      "66",
      "258",
      "6+2"
     ],
     [
      "MiniMax-M3",
      "427B",
      "6,144",
      "3,072",
      "15,360",
      "60",
      "129",
      "4+1"
     ]
    ]
   }
  },
  {
   "type": "h2",
   "title": "硬件表：spec 与实测",
   "paras": [
    "本页计算的每个硬件数字都来自 spec 和持续测量，每个值可追溯到厂商规格表、已发表测量或本书自己的基准（2026-08-17 检索）。方法：NVIDIA 数据表宣传稀疏 FLOP/s，这里减半为稠密；「双向」带宽减半为每方向；每 GPU scale-out 是节点 NIC 总量除以 GPU 数。≈ 标记估计值。",
    "注意引文逼迫的妙处：TPU 的持续性能远接近其纸面数字，而受功耗限制的 NVIDIA 部件差得更远。"
   ],
   "table": {
    "head": [
     "硬件",
     "C（稠密 bf16）",
     "×持续",
     "W 链路",
     "×实测",
     "W scale-out",
     "HBM"
    ],
    "rows": [
     [
      "TPU v5p",
      "459 TF",
      "0.72",
      "180 GB/s",
      "0.95",
      "6.25 GB/s",
      "96 GB"
     ],
     [
      "TPU v5e",
      "197 TF",
      "≈0.67",
      "90 GB/s",
      "≈0.95",
      "3.13 GB/s",
      "16 GB"
     ],
     [
      "H100（8-GPU 节点）",
      "989 TF",
      "0.73",
      "450 GB/s",
      "0.82",
      "50 GB/s",
      "80 GB"
     ],
     [
      "B200（8-GPU 节点）",
      "2.25 PF",
      "0.69",
      "900 GB/s",
      "≈0.82",
      "50 GB/s",
      "180 GB"
     ],
     [
      "GB200 NVL72",
      "2.5 PF",
      "≈0.70",
      "900 GB/s",
      "≈0.82",
      "≈50 GB/s",
      "186 GB"
     ],
     [
      "GB300 NVL72",
      "2.5 PF",
      "≈0.70",
      "900 GB/s",
      "≈0.82",
      "100 GB/s",
      "288 GB"
     ],
     [
      "H800（DeepSeek）",
      "989 TF",
      "≈0.73",
      "200 GB/s",
      "0.80",
      "50 GB/s",
      "80 GB"
     ]
    ]
   }
  },
  {
   "type": "h2",
   "title": "简化 Transformer 层与基础算法",
   "paras": [
    "为简化，我们把 Transformer 近似为 MLP 块栈——attention 对较大模型是 FLOPs 的较小部分（见第 4 节）。忽略 gating matmul，每层简化为两个矩阵：Win（上投影，bf16[D,F]）和 Wout（下投影，bf16[F,D]），输入 In: bf16[B,D]。",
    "在这个简化下每层持有 2·D·E·F 权重（稠密 E=1 即 2·D·F），整个栈 2·D·E·F·L 参数——即本页通信算术里的「P」。内存问题不同：真实 checkpoint 持有 gated MLP 的第三个矩阵和 attention 栈，所以内存仪表按 P_w ≈ 3·D·E·F·L + 2.5·D²·L 计价权重。",
    "**无并行完整算法**。Forward 需要算 Loss[B]：① Tmp[B,F] = In[B,D]·Win[D,F]；② Out[B,D] = Tmp[B,F]·Wout[F,D]；③ Loss[B] = …。Backward 需要算 dWout[F,D]、dWin[D,F]：① dOut[B,D] = …；② dWout[F,D] = Tmp[B,F]·dOut[B,D]；③ dTmp[B,F] = dOut[B,D]·Wout[F,D]；④ dWin[D,F] = In[B,D]·dTmp[B,F]；⑤ dIn[B,D] = dTmp[B,F]·Win[D,F]（前层需要）。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig01.png",
      "caption": "图 1：简化的 Transformer 层——每个 FFW 块是两个矩阵 Win（上投影）与 Wout（下投影），输入 In[B,D]。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "四种并行方案的 sharding 语法",
   "paras": [
    "四种方案各由 In、Win、Wout、Out 的一个分片方式唯一定义。下标在数组维度上命名它沿哪个 mesh 轴切开（In[B_DP,D] 表示 batch 维被切成 DP 片、每片一芯片），下标在 · 上命名被收缩的维度。",
    "**数据并行**：激活沿 batch 分片，参数和优化器状态在每设备复制。通信只发生在反向传播。In[B_DP,D]·Win[D,F]·Wout[F,D]→Out[B_DP,D]。",
    "**FSDP（ZeRO-3）**：激活沿 batch 分片（如纯数据并行），参数沿同一 mesh 轴分片、在 forward 前临时 AllGather。优化器状态也沿 batch 分片，减少重复内存。In[B_DP,D]·Win[D_DP,F]·Wout[F,D_DP]→Out[B_DP,D]。",
    "**张量并行（Megatron/模型并行）**：激活沿 D（d_model）分片，参数沿 F（d_ff）分片。每个块前后做 AllGather 和 ReduceScatter。与 FSDP 兼容。In[B,D_TP]·Win[D,F_TP]·Wout[F_TP,D]→Out[B,D_TP]。",
    "**流水线并行**：权重沿层维分片，激活微批化并沿层维滚动。流水线阶段间通信极小（只移动激活一跳）。",
    "注意四个方案的共同点：跑的是相同的 matmul，FLOPs 从不改变——只改变数组住哪、乘之间必须跑哪些集合通信。所以对每个方案问题总是：那些集合通信能否藏在 matmul 后面。"
   ],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "先感受 Roofline：两座时钟",
   "paras": [
    "当芯片处理我们 Transformer 的一层时，两座钟同时运行。**算力时钟**：MXU 必须啃完这层分担的 FLOPs——B 个 token 在 DP 个芯片上摊开，即 4·B·D·k·F/(DP·C) 每层（k·F 因为一个 token 只乘过它激活的 k 个专家）。**网络时钟**：方案移动的字节必须挤过互连 W_ici。",
    "关键：当实现成功调度集合通信时，两座钟可以重叠——网络搬字节的同时 MXU 在乘。在这个显式假设下，一层成本是 max（两座钟），不是和。藏在算力钟下的通信是免费的；戳出算力钟的通信让硅闲置。",
    "这个开关捕捉了核心区分：**传输的是什么？**如果传输的是**权重**——2·D·E·F 字节（每个 E 专家，激活与否）——数据并行和 FSDP 的网络钟固定，算力钟随每芯片批大小扩展——大 batch 让算力赢、通信被藏。如果传输的是**激活**——2·B·D 字节——张量并行里 batch 出现在两座钟上并抵消。隐藏取决于模型形状（token 乘过的宽度 k·F）。",
    "现在 roofline 本身。第 1 节里单芯片仅当它的算术强度（每字节触碰的 FLOPs）超过 FLOP 速度与内存带宽之比时才计算受限。同样的逻辑在这里高一级适用，互连扮演内存。对传权重的方案，FLOPs 随 B/DP 扩展而字节不扩展，所以 **B/DP 是稠密模型 token 形式的网络算术强度**；对这个等宽 MoE 模型，比例强度是 (B/DP)·k/E。roofline 的山脊在 (E/k)·(C/W) tokens/芯片——E/k 因子因为 MoE 移动全部 E 个专家的权重而 FLOPs 只碰 k 个。",
    "**反复出现的问题：这个方案的字节能装进这个方案的 FLOPs 吗？**对核心 roofline，答案比较每芯片 batch 或模型维度与 C/W。专家并行和流水线用同样的直觉，各有自己的流量和调度注意事项。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig02.png",
      "caption": "图 2：一层的两座时钟——算力（MXU）vs 网络（ICI），按上面数字按比例绘制。通信藏进算力下则免费，戳出则浪费硅。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "数据并行：语法与完整算法",
   "paras": [
    "DP 个芯片共享 B 个 token 的 batch，每个模型副本看到 B/DP 个 token。**语法**：In[B_DP,D]·Win[D,F]·Wout[F,D]→Out[B_DP,D]。",
    "**完整算法（Forward）**：① Tmp[B_DP,F] = In[B_DP,D]·Win[D,F]；② Out[B_DP,D] = Tmp[B_DP,F]·Wout[F,D]；③ Loss[B_DP] = …。",
    "**完整算法（Backward）**：① dOut[B_DP,D] = …；② dWout[F,D]{UDP} = Tmp[B_DP,F]·dOut[B_DP,D]（UDP = 未沿 DP 轴归约，每芯片持自己 batch 切片的偏和）；③ dWout[F,D] = AllReduce(dWout[F,D]{UDP})（不在关键路径，可异步）；④ dTmp[B_DP,F] = dOut[B_DP,D]·Wout[F,D]；⑤ dWin[D,F]{UDP} = In[B_DP,D]·dTmp[B_DP,F]；⑥ dWin[D,F] = AllReduce(dWin[D,F]{UDP})（不在关键路径，可异步）；⑦ dIn[B_DP,D] = dTmp[B_DP,F]·Win[D,F]（前层需要）。",
    "注意 forward 无通信——全在 backward！backward 还有好性质：AllReduce 不在「关键路径」，意味着每个 AllReduce 可以在方便时执行、不阻塞后续操作。整体通信成本**仍可能**成为瓶颈（若超过总计算成本），但从实现角度看宽容得多。后面会看到模型/张量并行没有这个性质——它的集合通信阻塞紧邻的下一个 matmul。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig03.png",
      "caption": "图 3：纯数据并行（forward）——激活沿 batch 维全分片，权重完全复制，每 TPU 有相同权重副本。内存×DP，但 forward 无通信。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "数据并行：为什么/为什么不",
   "paras": [
    "**为什么做？**纯数据并行沿 batch 维拆分激活，降低激活内存压力，允许几乎任意增大 batch（只要有更多芯片拆分）。训练中激活常主导内存，这很有帮助。",
    "**为什么不？**纯数据并行不降低模型参数或优化器状态的内存压力——对参数+优化器状态放不进单 TPU 的大模型几乎无用。若参数用 bf16、优化器状态用 fp32 Adam（Adam 存参数、一阶二阶累加器；参数 bf16 + 状态 fp32 = 2+8 = 10 字节/参数），能装的最大模型是 TPU 内存/10 参数——TPUv5p 单芯片约几亿参数。",
    "**Takeaway**：用 Adam 和纯数据并行能训练的最大模型有 num_params = 每设备 HBM/10。对 TPU v5p 约几亿参数（不含梯度检查点，所以实际不可用——batch 为 1 token 的绝对下限）。要让真实模型训练可用，需要至少部分分片模型参数或优化器。"
   ],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "数据并行：何时通信受限",
   "paras": [
    "如上，每层两个 AllReduce、各 2·D·F 字节（bf16 权重）。网络这里携带的是权重**梯度**——2·D·E·F 每矩阵（全部 E 专家的梯度，不只 token 用的 k 个）——其大小与 batch 无关。这是 roofline 里的传权重情形：batch 无关的通信成本，足够大的每芯片 batch 总能藏住。",
    "设 C = 每芯片 FLOPs、W_ici = 双向每轴 ICI 带宽（或每 GPU 单向 NVLink 出口）、DP = batch 分片数。算 matmul 时间 T_math 和所需通信时间 T_comms（此方案 forward 无通信，只算 backward）。",
    "**通信时间**：1D mesh 上 AllReduce 时间 = 2·总字节/W_ici。需对 Win 和 Wout 都 AllReduce，每层 2 个 AllReduce、各 2·D·F 字节，所以 T_comms = 2·2·2·D·F/W_ici = 8·D·F/W。注意：**没有 B**。",
    "**Matmul 时间**：每层 forward 两个 matmul、backward 四个，各 2(B/DP)·D·F FLOPs，所以 T_math = 2·2·2·B·D·F/(DP·C) = 8·B·D·F/(DP·C)——随每芯片 batch B/DP 扩展（FLOPs 携带 k·F，激活宽度）。",
    "重叠后每层时间 = max(T_math, T_comms) = 8·D·F·max(B/(DP·C), 1/W)。计算受限当 T_math/T_comms > 1，即 **B/DP > C/W**。",
    "对 TPUv5p，C/W = 2550，所以**每芯片 batch 必须至少 2550 才避免通信受限**——这就是著名的 2550 常数。若把三轴都用于纯数据并行，带宽×3，可降到每 TPU 850 tokens。这告诉我们纯数据并行很难成为瓶颈！注意「上下文并行」：token 就是 token，MLP 不关心序列归属，所以可对 batch 和序列维都做数据并行；attention 用 ring attention 处理跨序列计算。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig04.png",
      "caption": "图 4：数据并行一层的两座钟（反向）——算力随每芯片 batch 缩，通信固定。verdict 恰在 B/DP 越过 C/W 处翻转。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "数据并行：多 mesh 轴与 MoE 修正",
   "paras": [
    "**多 mesh 轴注记**：当为给定并行策略用多个 mesh 轴时，我们获得更多带宽。定义 M_DP（M_TP、M_Z 等）为给定并行策略横跨的硬件 mesh 轴数。效果（带宽受限时）：用 M 个轴提供约 M 倍聚合链路带宽，所以 collective 时间 ∝ 1/M_DP。",
    "**MoE 模型**：对 MoE 模型（E 个专家、每 token 激活 k 个），T_math = 2·2·2·k·B·D·F/(DP·C)，T_comms = 2·2·2·E·D·F/W——把每芯片 token batch 下限放大 **E/k** 倍：B/DP > (E/k)·(C/W)。",
    "例如 OpenAI 新 OSS 模型 k=4、E=128，跨节点下限放大到 32×2475 = 79,200 tokens——高得离谱（其 2475 是 H100 跨节点山脊）。专家并行——把专家本身分片、让梯度不再跨整个 DP 轴——是标准逃逸口。"
   ],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "FSDP：语法与完整算法",
   "paras": [
    "全分片数据并行（FSDP 或 ZeRO-3）把模型参数、优化器状态沿数据维分片。**语法**：In[B_DP,D]·Win[D_DP,F]·Wout[F,D_DP]→Out[B_DP,D]。",
    "回想第 3 节：AllReduce 可分解为 ReduceScatter 加 AllGather。FSDP 对每层做两次这样的分解——一次 Win、一次 Wout——参数在 forward 前 AllGather 回来。",
    "**完整算法（Forward）**：① Win[D,F] = AllGather(Win[D_DP,F])（不在关键路径，可前层做）；② Tmp[B_DP,F] = In[B_DP,D]·Win[D,F]（可扔 Win）；③ Wout[F,D] = AllGather(Wout[F,D_DP])（不在关键路径）；④ Out[B_DP,D] = Tmp[B_DP,F]·Wout[F,D]；⑤ Loss[B_DP] = …。",
    "**完整算法（Backward）**：① dOut[B_DP,D] = …；② dWout[F,D]{UDP} = Tmp[B_DP,F]·dOut[B_DP,D]；③ dWout[F,D_DP] = ReduceScatter(dWout[F,D]{UDP})（不在关键路径，可异步）；④ Wout[F,D] = AllGather(Wout[F,D_DP])（可提前）；⑤ dTmp[B_DP,F] = dOut[B_DP,D]·Wout[F,D]；⑥ dWin[D,F]{UDP} = In[B_DP,D]·dTmp[B_DP,F]；⑦ dWin[D_DP,F] = ReduceScatter(dWin[D,F]{UDP})（不在关键路径）；⑧ Win[D,F] = AllGather(Win[D_DP,F])（可提前）；⑨ dIn[B_DP,D] = dTmp[B_DP,F]·Win[D,F]（前层需要）。",
    "这也叫「ZeRO Sharding」，来自「Zero Redundancy Optimizer」——不执行任何不必要计算、不存储任何重复数据。",
    "**为什么做？**标准数据并行大量重复工作：每个 TPU AllReduce 完整梯度然后更新。FSDP 的参数（2·P_w/DP）和 Adam 状态（8·P_w/DP）都除以 DP，消除纯数据并行的重复内存。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig05.png",
      "caption": "图 5：FSDP——参数和优化器状态沿数据维分片，Win 的收缩维和 Wout 的输出维沿 DP 分片，减少重复内存。"
     },
     {
      "src": "fig06.png",
      "caption": "图 6：FSDP 把每层 2·D·F 梯度的 AllReduce 精确分解为 ReduceScatter 加 AllGather。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "FSDP：何时通信受限",
   "paras": [
    "相对 FLOPs 与通信成本与纯数据并行完全相同：T_math = 4·B·D·F/(DP·C)，T_comms = 4·D·F/W。所以与纯数据并行一样，**B/DP > C/W 时计算受限**——每设备 batch 小于某 tokens 时两者都带宽受限。",
    "**关键批大小注记**：有点反直觉地，总批大小越小时我们越通信受限——因为每设备 batch 变小。对 LLaMA-3 70B（约 15e12·70e9·6 FLOPs 训练），可把 token batch 拆到约 B/(C/W) 芯片，总训练 17 天估计保持活跃。",
    "**Takeaway**：FSDP 和纯数据并行都在每设备 batch < C/W（网络算力强度）时带宽受限。"
   ],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "张量并行：语法与完整算法",
   "paras": [
    "在 FSDP 的 AllReduce 中我们移动权重跨芯片。张量并行改为分片模型的 feedforward 维：激活沿 D 分片、参数沿 F 分片。**语法**：In[B,D_TP]·Win[D,F_TP]·Wout[F_TP,D]→Out[B,D_TP]。",
    "**关键区别：这些集合通信在关键路径上。** 纯数据并行的 AllReduce 在 matmul 之后、可随时做；张量并行的 AllGather 阻塞紧邻的下一个 matmul。",
    "**完整算法（Forward）**：① In[B,D] = AllGather(In[B,D_TP])（**关键路径**）；② Tmp[B,F_TP] = In[B,D]·Win[D,F_TP]（收缩维不分片，无通信）；③ Out[B,D]{U_TP} = Tmp[B,F_TP]·Wout[F_TP,D]；④ Out[B,D_TP] = ReduceScatter(Out[B,D]{U_TP})（**关键路径**）；⑤ Loss[B] = …。",
    "**完整算法（Backward）**：① dOut[B,D_TP] = …；② dOut[B,D] = AllGather(dOut[B,D_TP])（**关键路径**）；③ dWout[F_TP,D] = Tmp[B,F_TP]·dOut[B,D]；④ dTmp[B,F_TP] = dOut[B,D]·Wout[F_TP,D]；⑤ In[B,D] = AllGather(In[B,D_TP])（可与 forward 的 (1) 共享）；⑥ dWin[D,F_TP] = In[B,D]·dTmp[B,F_TP]；⑦ dIn[B,D]{U_TP} = dTmp[B,F_TP]·Win[D,F_TP]（前层需要）；⑧ dIn[B,D_TP] = ReduceScatter(dIn[B,D]{U_TP})（**关键路径**）。",
    "张量并行与 Transformer 的两个矩阵交互得很好：In 的 AllGather 在第一个 matmul 之前、Out 的 ReduceScatter 在第二个之后，可以互相重叠。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig07.png",
      "caption": "图 7：张量并行——激活沿 D 分片、参数沿 F 分片。第一个 matmul 前 AllGather、之后 ReduceScatter，都在关键路径上。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "张量并行：何时通信受限",
   "paras": [
    "只建模 forward（backward 是这里每个操作的转置）。1D 下 T_math = 4·B·D·F/(TP·C)，T_comms = 2·2·(B·D)/W。注意 **B·D 出现在两座钟上并抵消**！化简计算受限条件：4·B·D·F/(TP·C) > 4·B·D/W → F/(TP·C) > 1/W → **F > TP·(C/W)**，即 TP < F/(C/W)。",
    "这**不依赖计算精度**——int8 时 C_int8/W 不同但结论结构相同。对 TPUv5p，C/W = 2550，只能做 TP < F/2550。对 LLaMA 3-70B（D=8192, F≈30000），可舒服做 8-way 张量并行，但 16-way 会通信受限。",
    "**Takeaway**：张量并行当 TP·(C/W) > F（或本页等宽 MoE 近似的 k·F）时通信受限。对大多数模型约 8-16 way。例子：TPUv5p + LLaMA 3-70B 可做 8-way；Gemma 7B（F=24,576）TP_max≈9.64，8-way 仍计算受限但 16-way 不会。"
   ],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "混合 FSDP + 张量并行：语法与算法",
   "paras": [
    "FSDP 和 TP 可组合：把 Win 和 Wout 沿两轴都分片，参数无重复。**语法**：In[B_DP,D_TP]·Win[D_DP,F_TP]·Wout[F_TP,D_DP]→Out[B_DP,D_TP]。",
    "**完整算法（Forward）**：① In[B_DP,D] = AllGather_TP(In[B_DP,D_TP])（**关键路径**）；② Win[D,F_TP] = AllGather_DP(Win[D_DP,F_TP])（可提前）；③ Tmp[B_DP,F_TP] = In[B_DP,D]·Win[D,F_TP]；④ Wout[F_TP,D] = AllGather_DP(Wout[F_TP,D_DP])（可提前）；⑤ Out[B_DP,D]{U_TP} = Tmp[B_DP,F_TP]·Wout[F_TP,D]；⑥ Out[B_DP,D_TP] = ReduceScatter_TP(Out[B_DP,D]{U_TP})（**关键路径**）；⑦ Loss[B_DP] = …。",
    "**完整算法（Backward）**：① dOut[B_DP,D_TP] = …；② dOut[B_DP,D] = AllGather_TP(dOut[B_DP,D_TP])（**关键路径**）；③ dWout[F_TP,D]{U_DP} = Tmp[B_DP,F_TP]·dOut[B_DP,D]；④ dWout[F_TP,D_DP] = ReduceScatter_DP(dWout[F_TP,D]{U_DP})；⑤ Wout[F_TP,D] = AllGather_DP(Wout[F_TP,D_DP])（可提前）；⑥ dTmp[B_DP,F_TP] = dOut[B_DP,D]·Wout[F_TP,D]；⑦ In[B_DP,D] = AllGather_TP(In[B_DP,D_TP])（不在关键路径 + 可与上层 (2) 共享）；⑧ dWin[D,F_TP]{U_DP} = In[B_DP,D]·dTmp[B_DP,F_TP]；⑨ dWin[D_DP,F_TP] = ReduceScatter_DP(dWin[D,F_TP]{U_DP})；⑩ Win[D,F_TP] = AllGather_DP(Win[D_DP,F_TP])（可提前）；⑪ dIn[B_DP,D]{U_TP} = dTmp[B_DP,F_TP]·Win[D,F_TP]（前层需要）；⑫ dIn[B_DP,D_TP] = ReduceScatter_TP(dIn[B_DP,D]{U_TP})（**关键路径**）。",
    "**什么是最优 FSDP 和 TP 组合？**一个简单但关键的格言：FSDP 传权重、张量并行传激活。张量并行做 AllGather_TP([B_DP,D_TP])，随 DP 增长缩小；FSDP 做 AllGather_DP([D_DP,F_TP])，随 TP 增长缩小。组合能把每副本最小 batch 推得更低。"
   ],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "混合方案：DP_opt 与计算受限条件",
   "paras": [
    "**TPU 闭式解**。设 DP 个芯片做 FSDP、TP 个芯片做张量并行（N = DP·TP 总芯片）。T_FSDP_comms = 2·2·D·F/(TP·W·M_DP)，T_TP_comms = 2·2·B·D/(DP·W·M_TP)，T_math = 2·2·B·D·F/(N·C)。",
    "T_FSDP_comms 随 DP 单调增、T_TP_comms 随 DP 单调减，所以最大值在两者相等处最小：F·DP_opt/(N·M_DP) = B·N/(DP_opt·M_TP) → **DP_opt = sqrt(B·F·M_DP·M_TP/N)**。超级有用！它告诉我们给定 B、F、N 时用多少 FSDP 最优（权重项 E·F 宽，所以 E 加入根号下的 F）。",
    "**何时计算受限**：max(T_FSDP, T_TP) < T_math。令 α ≡ C/W（网络算力强度），化简：max(F·TP·M_DP, B·DP·M_TP) < B·F·N·α。由于 DP_opt 让 LHS 最大项相等，代入得 **B/N > α²/(M_DP·M_TP·F)**。",
    "用 F=32,768、α=2550、M_DP·M_TP=2，约 B/N > 2550²/65536 ≈ 990。结合 TP 让我们把 batch 降到 B/N 低至 **2550²/2F**——remarkably low。",
    "**Takeaway**：训练中 FSDP 最优量是 DP_opt = sqrt(B·F·M_DP·M_TP/N)；混合 FSDP+TP 允许 B/N 低至 α²/2F。TPU v5p 16×16×16 图中黑线是模型 FLOPs 时间，任何 batch 处任何 comms 曲线高于它即通信受限；最优在 FSDP=256、TP=16 附近。"
   ],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "专家并行：AllToAll 的成本",
   "paras": [
    "MoE 模型比稠密模型多 E 倍权重、只多 k 倍 FLOPs，让纯数据并行和 FSDP 的 E/k 惩罚更痛。专家并行把专家本身分片到 EP 个芯片，token 需要时路由过去。",
    "节点内 GPU 有全互联，AllToAll 很容易：每 GPU 发送 (8-1)/8 的数据分片。**Takeaway：单节点内 B 字节数组的 AllToAll 成本约 T = B·(8-1)/(8²·W_GPU)。**",
    "跨节点成本更高：T_math = 4·B·k·D·F/(EP·C)，T_comms = 4·B·D·(EP-8)/(W·EP)·min(8·k/EP, 1)。对八 GPU H100 节点，要么需要 k_r > EP/8 且 F > α·(EP-8)/k_r，要么 EP ≫ k_r 且 F > 8·α。",
    "实际两种都见：小量专家并行（如 DeepSeek V3，F 很小、EP 相对小）或大规模 EP。**Takeaway：若 F < G·C/W，专家并行可横跨约 1-2 个快光域，成本类似（略低）。**"
   ],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "流水线并行：算法、气泡与为什么难",
   "paras": [
    "流水线对 GPU 是主导策略（因为互连小），对 TPU 不那么关键（pod 大）。思想：权重沿层维分片，微批在阶段间流动。算法：① 在 TPU 0 上初始化数据、权重沿层维分片；② 在 TPU 0 做第一层，复制激活到 TPU 1，重复到最后一个 TPU；③ 算 loss 和 ∂L/∂x_L；④ 对最后阶段算 ∂L/∂W_L 和 ∂L/∂x_{L-1}，复制 ∂L/∂x_{L-1} 回前一阶段，重复。",
    "**为什么好？**流水线阶段间通信成本低——意味着能以远低于数据并行的字节数在阶段间传递信息；pipelining 的训练微批是 TPU 0 上模型权重的全局视图。每跳 2·B·D/W，除以层数后远小于其他任何成本。",
    "**为什么难/烦？**三个原因。**代码复杂度**：流水线难融入自动并行框架（如 XLA GSPMD），因为微批和自定义调度难以表达。**破坏数据并行和 FSDP**：可能是最大的不做理由——流水线与 FSDP 玩不好，因为权重分片跨层、FSDP 的 AllGather 语义冲突。**气泡与步失衡**：朴素流水线调度让阶段空转在气泡里。GPipe 风格气泡分数 = (PP-1)/(M_micro+PP-1)，微批越少设备利用率越差。",
    "工作区有办法缓解每个问题，但往往实现复杂、难维护。可以仔细重叠 forward matmul、backward dx matmul 和 dW matmul 来填充气泡。"
   ],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "跨 pod 扩展：DCN 的最小 batch",
   "paras": [
    "最大 TPU 切片是 TPU v5p SuperPod，8960 芯片（2240 hosts）。超过这个规模需要跨 pod。典型做法：pod 内做某种模型并行或 FSDP（ICI 域内），pod 间做纯数据并行。",
    "T_math = 8·B·D·F/(N·C)，T_comms = 8·D·F/(M·W_dcn)——通信带宽随 M（pod 数）缩放，因为 DCN 总带宽随 ICI 域增长和更多 NIC 而增长。计算受限当 **B_slice > C/W_dcn**——每 ICI 域有最小 batch 才能高效跨 DCN 扩展。",
    "对 TPU v5p，C/W_dcn 约 7000/31 ≈ 225。**Takeaway：跨多 TPU pod 扩展相当直白，用纯数据并行即可——只要每 pod batch 大小足够。**",
    "对 LLaMA-3 70B 想用 BS=1M 训练：TP 上限 TP = M_TP·k·F/2550；FSDP 需 B/N > 2550/M_DP；混合方案 B/N < 2550²·E/(M_DP·M_TP·k²·F) 时通信受限。配方是 DP(FSDP)=1024、TP=8（BS=1M）；BS=2M 时混合方案更优。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig08.png",
      "caption": "图 8：跨 pod 数据并行——每 pod 内部 FSDP+TP，pod 间交换梯度。通信 bar 由模型形状和 pod 聚合 NIC 带宽固定。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "GPU 网络模型：roofline 落点",
   "paras": [
    "理解 GPU 上 LLM 缩放的 roofline，补充 TPU 图。定义 W_collective 为 GPU 或节点级有效带宽（这里把 W_ici 读作每 GPU 进入 NVLink 交换织物的出口带宽，450 GB/s 级别）。",
    "**数据并行/ZeRO**：规则 B/DP > C/W。节点内只需每 GPU token batch > 2500；SU 或 spine 级 BS > 32,000。H100 scale-out 织物上稠密渐进是 ~2,500-32,000，比 TPU 高得多（TPU 三轴 850）。",
    "**小 DP 修正**：渐进山脊省略了 ring 因子。有 X 个 scale-out 域时，精确稠密条件是 B/DP > (C/W)·(X·8·(1-1/X))…。",
    "**张量并行**：TP < F·W/C 约 F/2550。通常只在一个 NVLink 域内计算受限（至多两个）。NVL72 扩展本地域但不消除问题。",
    "**集合通信成本**：节点内 AllGather/ReduceScatter B 字节约 T = B·(8-1)/(8·W)。节点级以上，全对分带宽使成本 = bytes/W_node_egress。理论上 NVIDIA SHARP（多数 NVIDIA 交换机）把 AllReduce 从 ~2B/W 减半到 ~B/W。虽然 NVIDIA 声称 H100 NVLink 约 450GB/s，实践难超 370GB/s。",
    "**例子**：DeepSeek V3 用 2048 H800：EP64（跨 8 节点）、PP16、ZeRO-1 DP2，稳态 batch 4096×15360 = 6290 万 tokens（3 万/GPU）——已接近 H100 织物的数据并行上限。Llama 3.1 405B 用 BS 1600 万 tokens、16384 H100（977/GPU）：TP8（节点内）、PP16、DP128。",
    "**TLDR of LLM scaling on GPUs**：DP/FSDP 需要 H100 级织物每 GPU 约 2,500 稠密 token 的局部 batch（MoE 乘 E/k）；TP 通常只在一个 NVLink 域内计算受限（至多两个）；横跨域的模型并行能降低外层 FSDP 成本但追踪的是「跨域数」；PP 字节成本低但调度复杂、有气泡、延迟梯度归约。较小稠密模型在 batch 允许时可用激进 FSDP；较大稠密模型常用一到两个域 TP 组合。"
   ],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "Takeaways from LLM Training on TPUs",
   "paras": [
    "增加并行度或减少批大小都倾向让我们更通信受限，因为它们减少可用隐藏通信的每设备计算量。",
    "到合理上下文长度（~32k）可把 Transformer 建模为 MLP 块栈，并把每种方案定义为它对 In、Win、Wout、Out 的分片方式。训练有 4 种主要并行方案，各有带宽和计算需求。",
    "每个策略有它变网络/通信受限的极限：纯数据并行几乎没用（模型+优化器状态用 10× 参数计数字节，最大约 HBM/10 参数）；数据并行和 FSDP 当每分片 batch < C/W 时通信受限（网络算力强度，TPU v5p 约 2550/850）；张量并行当 |TP| > F/(C/W) 时通信受限，约 8-16 way，**与计算精度无关**；混合 FSDP+TP 把 batch 降到 α²/2F；跨 pod 数据并行需每 pod 最小 batch 约 850-2550 才不 DCN 受限。",
    "基本规则：**批大小大或模型小，事情简单**——数据并行或 FSDP + 数据并行就够了。批小模型大则需要更复杂的混合方案。"
   ],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "练习题：用 LLaMA-2 13B 检验理解",
   "paras": [
    "用 LLaMA-2 13B 作为基础模型：FFW 用 gated MLP（3 个矩阵），有独立 embedding 和输出矩阵。",
    "**Q1：LLaMA-2 13B 有多少参数？**（注意和 Transformer Math 一样，embedding 和输出矩阵分开算）① FFW 参数：3·L·D·F；② attention 参数：2·D·H·L·(N+K)（原文读「Attention parameters: 4DNHL = 4.2e9」，推广为 2DHL·(N+K)）；③ 词表参数：2·V·D。三者之和即预期值。",
    "**Q2：BS 训练用 Adam，总内存多少？**（先忽略并行）参数（bf16）+ 两个优化器状态（fp32，一阶二阶矩累加）= (2+4+4)·参数 = **10 字节/参数**。",
    "**Q3：32k 序列、3M token batch、TPUv5p 16×16×16 slice（4096 芯片），三问：**",
    "① **能纯数据并行吗？为什么？**不能——它把参数和优化器状态复制到每芯片（已约 10·13B = 130GB，超过 96GB HBM；纯 DP + Adam 最大约 9.6B 参数，我们 13B 超了）。",
    "② **能纯 FSDP 吗？**先看内存：BS=3M 的 checkpoint 激活约 3M/32k·...，训练状态 4096 芯片分片后每芯片 < HBM，内存 OK。但看通信：4096 芯片 3 轴并行最小 batch 4096·(C/W)≈4096·850≈3.5M tokens，略高于 3M batch，所以**通信受限**，不能只用 FSDP。",
    "③ **混合 FSDP+TP 呢？**每芯片 batch 需 > α²/2F = 2550²/65536 ≈ 990 tokens/chip（3M/4096 = 732 < 990，不够！）等等，用 DP_opt = sqrt(B·F·M_DP·M_TP/N) = sqrt(3e6·2·4096/16384) ≈ 1224，即约 1024 路 FSDP、8 路 TP。step 时间 = 6·3e6·4096·...。",
    "**附录 A：推导反向传播通信。** 对单 matmul Y = X·A：dL/dA = dL/dY·dY/dA = Xᵀ·dL/dY；dL/dX = dL/dY·dY/dX = dL/dY·Aᵀ。用这些（设 Tmp[B,F] = In[B,D]·Win[D,F]）：① dWout[F,D] = Tmp[B,F]·dOut[B,D]；② dTmp[B,F] = dOut[B,D]·Wout[F,D]；③ dWin[D,F] = In[B,D]·dTmp[B,F]；④ dIn[B,D] = dTmp[B,F]·Win[D,F]。",
    "这些公式是数学陈述、不提分片。反向传播的工作是算这四个量：取四个方程中要被 matmul 的量（Tmp、dOut、Wout、Win）的分片、用 sharded matmul 规则确定要做的通信。注意 dOut 与 Out 同分片方式。"
   ],
   "fig_after": {}
  }
 ],
 "conclusion": [
  "这篇可探索解释把「并行化 Transformer」从一堆凭感觉的调参还原成一个可计算的问题：**每层的时间 = max(算力时间, 通信时间)**，而通信能否被隐藏，取决于传输的是权重还是激活。",
  "三个最可迁移的结论：**B/DP > C/W**（数据并行/FSDP 的通用判据，MoE 乘 E/k）；**TP < F/(C/W)**（张量并行，与批无关）；以及 **DP_opt = sqrt(B·F·M_DP·M_TP/N)**（混合方案的最优比例）。记住它们，面对任何硬件任何模型都能快速判断该用哪种并行、会不会通信受限。"
 ],
 "reference_url": "https://ezyang.github.io/interactive-parallelize-transformer/"
}

with open("article_data.json", "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=1)
print(f"✅ 写入 article_data.json")