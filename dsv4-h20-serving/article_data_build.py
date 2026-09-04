# -*- coding: utf-8 -*-
"""LMSYS DSV4 H20 编译 build"""
import json, os, sys

DATA = {
 "title": "把服务 DeepSeek-V4-Pro 推到极限：H20 上的多 serving profile 方法论",
 "lead": [
  "DeepSeek-V4-Pro 是一个 1.6 万亿参数的 Mixture-of-Experts（MoE）模型，同时发布 FP8 和 FP4 权重。这个规模的模型自然受益于 NVIDIA Blackwell 等加速器——它们有更多 HBM、更高计算吞吐和原生 FP4 Tensor Cores。然而 H20 GPU 仍被广泛部署，尽管缺乏这些优势。",
  "硬件约束不会放松服务要求。长上下文 prefill 仍必须控制首 token 时间（TTFT）。交互式 decode 必须满足每个服务层的每输出 token 时间（TPOT）目标。持续流量必须平衡聚合吞吐与 KV 缓存容量。短输入、长上下文、延迟敏感请求和高并发以不同方式给系统施压；没有通用配置能把它们都服务好。",
  "**一个模型需要多个 serving profile。**工作负载特征、服务级目标（SLO）和实测硬件行为共同决定部署拓扑和执行路径：把 serving profile 匹配到工作负载；优化 prefill 路径（Attention-CP8 → MoE-TP8 与上下文并行通信）；优化 decode 路径（DSpark 投机解码路径、执行精修、专家路由与通信-计算重叠）。",
  "**推进延迟前沿。**batch size 1 下单节点 H20-141GB 参考达到 **271 output tokens/s**，对比 B300 上报的 **383.7 tokens/s**。尽管硬件差距巨大，针对工作负载的系统优化把观察到的 decode 性能比缩小到 **1.42×**。",
  "**覆盖服务包络。**跨更广的 profile 家族，优化 prefill 达到每节点 **8.45k input tokens/s**，43.7 秒处理 **1M-token prompt**。吞吐导向 decode 的 DP16-EP16 效率参考达到每节点 **4.67k output tokens/s**，对应平均 TPOT **27.4 ms**。这些结果来自不同 profile，每个针对不同上下文长度、延迟、吞吐和容量组合选择并优化。",
  "**贡献是方法论，不是单个基准。**场景特定服务允许每个工作负载在可用硬件上评测的 profile 中移动到更好的实测工作点。我们希望这里呈现的部署选择、优化方法和测量，能为在计算、内存、带宽或互连约束下服务前沿模型的团队提供实用参考。"
 ],
 "summary": [
  {
   "key": "核心结论",
   "body": "一个模型需要多个 serving profile：prefill 按上下文长度在 PP2/PP4 间切换，decode 用 PP2-TP8 低延迟、DP32-EP32 高吞吐。H20 无原生 FP4 仍能撑 1M token 上下文、满足多 SLO。"
  },
  {
   "key": "关键数据",
   "body": "batch1 解码 271 tok/s vs B300 383.7（1.42×）；prefill 8.45k tok/s/节点、1M prompt 43.7s；容量 Humming+Online C128 把 DP32-EP32 提到 3.88×、PP2-TP8 到 10.14×。"
  },
  {
   "key": "可迁移",
   "body": "方法论而非单一基准：从 workload/SLO/上下文长度/并发出发，用 profiling 找约束资源，转化为具体拓扑和执行路径决策。MoE-TP 代替 MoE-EP（可预测通信比不可预测失衡便宜）；从生产路由调 Humming 形状。"
  }
 ],
 "sections": [
  {
   "type": "h2",
   "title": "从硬件约束到 Serving Profile",
   "paras": [
    "**Blackwell 提供原始性能；H20 提供可部署规模。**B300 提供原生 FP4 Tensor Cores、高得多的 FP8 吞吐和显著更多 HBM。H20 无法匹配其计算能力，但它仍在规模上可用，且提供高内存带宽和 900 GB/s NVLink。本研究每个节点含八张 NVLink 连接的 GPU。",
    "Prefill 不保留长期的每请求状态，所以它的硬件选择主要由 TTFT、计算和通信效率支配。Decode 必须在生成全程保留每个活跃请求的 KV 缓存，使 HBM 容量成为上下文长度和并发的直接限制。对本研究部署，这引导我们用 H20-141GB 做 decode、H20-96GB（容量足够我们的 prefill 工作负载）做 prefill。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig01.png",
      "caption": "图 1：硬件差距——H20 vs B300。"
     },
     {
      "src": "fig02.png",
      "caption": "图 2：按服务角色的硬件分配。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "容量选择：Humming MXFP4AFP8",
   "paras": [
    "服务容量最终来自共享的 HBM 预算：模型权重和每请求 KV 状态竞争同一内存。我们定义**全 token 容量**为分配模型权重和运行时缓冲区后每个 rank 能持有的最大 full-attention KV token 数。它是内存上限而非可接受 batch 的直接保证。",
    "**先减小权重足迹。**Humming MXFP4AFP8 用 MXFP4 专家权重 + 在线 FP8 激活，在缺乏原生 FP4 Tensor Cores 的 H20 GPU 上减少权重足迹和内存流量。SGLang 集成在 sglang#23754。模型级精度结果和公共参考测量见附录 D.2。"
   ],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "容量选择：Online C128",
   "paras": [
    "**给 KV 缓存成长空间。**Offline C128 基线为每个压缩页保留按索引的状态。Online C128 改为维护紧凑聚合状态，释放更多 HBM 给 KV 缓存池。它引入额外状态维护和投机验证工作，但我们的测试未观察到 TPOT 回归。",
    "**容量增益在权重和 KV 状态上复合。**通过减小权重足迹，Humming MXFP4AFP8 把 DP32-EP32 的全 token 容量扩展到 Baseline FP8 + Offline C128 配置的 **1.71×**、PP2-TP8 的 **4.47×**。Online C128 再把 C128 辅助状态足迹减少，在 Humming 之上提供另一个 **2.268×**。两者结合把容量提到 DP32-EP32 基线的 **3.88×**、PP2-TP8 的 **10.14×**。附录 D.1 提供完整数据。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig03.png",
      "caption": "图 3：Humming MXFP4AFP8 与 Online C128 的容量扩展。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "场景特定 Serving Profile：Prefill",
   "paras": [
    "**正确的流水线深度取决于有多少可流水线化的工作。**PP2-CP8-TP8 和 PP4-CP8-TP8 共享同一 `Attention-CP8 → MoE-TP8` 执行路径。拓扑层面主要区别是流水线深度：PP2 把模型分到两阶段，PP4 用四阶段。",
    "**短上下文倾向更低流水线开销；长上下文暴露更多并行。**短输入产生更少 chunk，让更深流水线欠填充，使填充、排空和跨阶段传输成本更突出。长上下文提供足够 chunk 保持四阶段忙碌；每阶段层更少，额外节点转化为更多 prefill 并行。在我们的部署中，这些特征引导我们用 **PP2-CP8-TP8 处理较短上下文**、**PP4-CP8-TP8 处理长上下文工作负载**。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig04.png",
      "caption": "图 4：Prefill Profiles——相同执行路径，不同流水线深度。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "场景特定 Serving Profile：低延迟 Decode",
   "paras": [
    "**低延迟从最短执行路径开始。**单节点 TP8 和 PP2-TP8 共享同一 `Attention-TP8 → MoE-TP8` 执行路径；区别是模型是否跨节点分区。单节点 TP8 把全部层放一个 H20-141GB 节点，避免跨阶段通信和同步。PP2-TP8 把模型分到两个流水线阶段。",
    "**最快的拓扑不总是最可服务的。**单节点 TP8 执行路径更短，但模型权重和服务状态共享单节点 HBM，留给 KV 缓存的空间有限。它无法同时支持长上下文和更大 batch。PP2-TP8 付出额外流水线开销，但把模型权重分布到两节点，释放更多 HBM 给 KV 状态。对我们的延迟和容量目标，我们用**单节点 TP8 作为 batch-size-1 延迟参考**、**PP2-TP8 作为低延迟服务 profile**。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig05.png",
      "caption": "图 5：低延迟 Decode——TP8 参考与 PP2-TP8 服务 profile。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "场景特定 Serving Profile：高吞吐 Decode",
   "paras": [
    "**高吞吐 decode 一起扩展数据和专家并行。**两个 profile 都用 `Attention-DP → MoE-EP` 执行路径。DP16-EP16 是最小部署单元；DP32-EP32 在同一拓扑内扩展 DP 和 EP。",
    "**Scale-out 优先请求容量而非每 GPU 吞吐。**更大 EP 组把专家权重分布到更多 GPU，释放 HBM 给 KV 缓存、容纳更多并发请求。同时，更小比例的 MoE 流量留在每节点内，更大比例跨节点，可能降低每 GPU 效率。在评测的 profile 中，我们用 DP16-EP16 作为最小部署单元和效率参考，DP32-EP32 扩展请求容量。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig06.png",
      "caption": "图 6：高吞吐 Decode——DP16-EP16 参考与 DP32-EP32 容量 profile。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "Prefill：平衡计算与通信",
   "paras": [
    "**Prefill 性能是系统问题。**专家失衡、上下文并行通信和生产路由形状共同决定 TTFT；优化孤立内核不够。"
   ],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "为什么 MoE-TP 而非 MoE-EP",
   "paras": [
    "**更少流量仍可能更久。**MoE-EP 只交换路由 token，但真实 prefill 流量呈现显著专家偏斜。拥有热门专家的 rank 做更多计算、成为 straggler；其他所有 rank 在 combine 步骤等最慢路径。更低的通信量不转化为更低 TTFT。",
    "**在最小化流量前先平衡计算。**对本文评估的 H20 prefill 工作负载，PP2 和 PP4 都用 MoE-TP。全序列 all-gather 和 reduce-scatter 引入更多通信，但流量保持在高速 NVLink 上、成本稳定可预测。所有 TP rank 对相同路由 token 执行张量并行计算，防止专家偏斜变成 rank 级长尾。对这个工作负载，**可预测通信比不可预测失衡便宜**。实现见 sglang#24947。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig07.png",
      "caption": "图 7：用 MoE-TP 替换 MoE-EP。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "加速与融合 Prefill Collectives",
   "paras": [
    "**构建可复用 collective 快路径。**MoE-TP 用可预测 collective 流量替换不可预测专家失衡，使通信效率成为下一个瓶颈。我们让对称内存跨 TP 和 CP 可复用，允许 AllReduce、AllGather 和 ReduceScatter 共享注册缓冲区快路径和适用的 Hopper 加速。支撑的上游工作跨越内存池所有权、communicator 注册、MoE-TP collective 缓冲区和 CP Attention/KV-cache 缓冲路径。",
    "**然后缩短 Prefill 关键路径。**更快的 collective 本身不消除通信与计算的边界。对 32K 单 chunk 情形，我们构建融合路径：用 copy-engine 驱动的 AllGather 与融合 FP8 量化和共享专家 GEMM 重叠，然后在第二个 Triton 内核里组合 TopK 归约、共享专家加法和 ReduceScatter。这把七个算子重组成三个执行组，在匹配的 PP4 A/B 中 TTFT 降低约 **3.5%**。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig08.png",
      "caption": "图 8：对称内存 Collectives 与 Prefill 融合。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "为真实路由形状调优 Humming",
   "paras": [
    "**通用调优错过重要的形状。**Prefill 路由把 token 不均匀地分布到 384 个专家，所以有效 `M` 维度聚类到一小组离散值。W13 和 W2 也在不同形状上操作，单一通用启发式无法同时优化两条路径。",
    "**从生产路由调优。**我们从真实路由直方图提取高频形状，为 W13 和 W2 构建独立 exact-shape 配置，在内核、流水线阶段和匹配 A/B 级别验证。优化目标不是合成的 `M` 范围，而是**我们实际服务的路由分布**。在 32K 匹配 PP4 A/B 中，选定 MoE 内核延迟下降约 **21%**，转化为端到端 TTFT 减少 **11.35%**。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig09.png",
      "caption": "图 9：为真实路由形状调优 Humming。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "Decode：优化投机与 MoE 执行",
   "paras": [
    "**Decode 优化在我们的实现中是 profile 特定的。**PP2-TP8 需要跨投机流水线阶段协调，DP32-EP32 专注优化高并发下的精修步骤和专家路由。Humming 融合和重叠改善这些服务拓扑之下的共享 MoE 热路径。"
   ],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "低延迟 PP2-TP8：跨流水线阶段扩展 DSpark",
   "paras": [
    "**流水线并行切分投机循环。**在 PP2-TP8 中，目标执行跨两个流水线阶段，而 DSpark drafter 只驻留在最后阶段。Stage 0 发送目标隐藏状态给 Stage 1，它执行验证、接受 token、为下一轮生成候选。",
    "**让两阶段像一阶段一样前进。**每个投机轮跨流水线边界。我们在一个执行协议下协调两阶段和所需中间传输，防止阶段进入不同轮次，同时避免冗余同步。PP 特定 DSpark 集成正上游到 sglang#32281。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig10.png",
      "caption": "图 10：跨 PP2 阶段协调 DSpark。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "高吞吐 DP32-EP32：移除高并发瓶颈",
   "paras": [
    "本小节的匹配 A/B 用 DP32-EP32 在 4K、每 DP rank 32 并发请求。",
    "**为精修选择正确的执行形状。**精修步骤用全词表投影重打分 DSpark 的候选集。高并发下逐行 dot-reduce 为每个活跃行反复读词表权重，在每个 decode 步骤造成持久尾部。我们把活跃行合并进一个转置 GEMM，减少冗余内存流量、缩短精修路径。每 GPU 吞吐提升 **22.8%**。",
    "**从实测路由放置专家。**DSpark 流量也呈现显著专家偏斜。我们记录代表性请求的路由亲和，用它配置专家并行负载均衡（EPLB）和冗余专家，防止少数热门专家反复延长关键路径。每 GPU 吞吐提升 **13.5%**。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig11.png",
      "caption": "图 11：DP32-EP32 瓶颈移除。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "Humming Decode 热路径：融合与重叠",
   "paras": [
    "这些优化位于服务拓扑之下，可被基于 Humming 的 decode profile 复用。下面匹配结果用 DP32-EP32 在 4K、每 DP rank 32 并发请求。",
    "**移除额外量化前向。**我们把 SwiGLU 激活与量化融合，使融合内核直接产生 W2 所需的数据和 scale。这消除对中间缓冲区的重复访问、移除独立量化前向，让 W2 更早开始。在匹配 DSpark A/B 中，每 GPU 吞吐提升 **44.0%**。",
    "**用 W2 重叠通信。**我们把我们之前工作的 Single-Batch Overlap（SBO）机制适配成 **Humming-Aware SBO**。逐 tile 信号允许 DeepEP 在 W2 输出 tile 一完成就启动对应 combine 发送，无需等整个 GEMM。在相同工作点更早的匹配非投机 A/B 中，SBO 相对 FP8 传输层恢复 **4.12%** 吞吐。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig12.png",
      "caption": "图 12：Humming Decode 热路径优化。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "评估：Prefill 累计增益与上下文权衡",
   "paras": [
    "**PP2 强化短上下文 profile。**PP2 在全部九个输入长度改善，几何平均吞吐增益 **36.5%**，峰值总输入吞吐 **16,900 tokens/s**。更浅流水线减少短请求的填充-排空开销，让 PP2 用更少资源保持更低 TTFT。",
    "**PP4 把增益带进长上下文。**PP4 跨同样九点交付几何平均 **31.8%** 吞吐增益。随着上下文增长，更深流水线有足够工作摊销固定成本：总输入吞吐在 512K 达到 **25,860 tokens/s**、1M 保持 **23,970 tokens/s**。",
    "**上下文长度移动 PP2/PP4 权衡。**相对 PP4，PP2 在 4K 把 TTFT 降低 **16.7%**、32K 降低 **19.5%**。两 profile 在 8K、16K、64K 保持在 **2%** 内。PP4 从 128K 起建立决定性优势，相对 PP2 在 128K/256K/512K/1M 分别降低 TTFT **26.2%**、**33.3%**、**42.1%**、**44.8%**。因此我们把路由边界当作从实测上下文长度范围导出的操作策略，而非通用交叉点。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig13.png",
      "caption": "图 13：Prefill 累计吞吐增益。"
     },
     {
      "src": "fig14.png",
      "caption": "图 14：PP2 与 PP4 之间的 TTFT 权衡。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "评估：低延迟 Decode 性能与容量",
   "paras": [
    "**优化 DSpark 重置延迟基线。**在图 15 的四个输入长度上，优化 DSpark 在 batch size 1 把峰值 TPOT 降低 **74.8%-78.0%**。在每对测量共享的最大 batch，降幅仍为 **52.2%-60.0%**。增益从 8K 到 1M 保持，而非限于短上下文或单请求执行。",
    "**观察到的服务性能远比峰值计算比暗示的接近。**在图 16 的四个输入长度上，PP2-TP8 上优化 DSpark 在 batch size 1 达到 **150-174 tokens/s**。单节点 TP8 参考达到 **183-271 tokens/s**。对实际执行路径用的精度，B300 有 H20-141GB 约 **45.6×** 的峰值 Tensor Core 计算（B300 FP4 vs H20 FP8）和 **1.67×** 内存带宽。然而观察到的最高生成率分别是 **383.7 tokens/s**（B300）和 **271 tokens/s**（H20-141GB）——比例 **1.42×**。即使对照这个强得多的硬件参考，工作负载特定优化让 H20-141GB 参考在观察服务性能上大幅接近。",
    "**容量让 PP2-TP8 偏向我们的生产目标。**单节点 TP8 更快，但 1M 上下文下它只有 batch size 1 的 KV 缓存容量。它无法容纳更大 batch 或更多并发请求。通过把模型权重分布到两个流水线阶段，PP2-TP8 在 1M、512K、256K 分别支持 batch 4、8、16。用 Online C128，其全 token 容量达 **11.04M tokens/rank**。对与我们相似的上下文长度和并发目标，我们建议保留单节点 TP8 作为延迟参考、用 **PP2-TP8 作为低延迟服务 profile**。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig15.png",
      "caption": "图 15：优化 DSpark 的峰值 TPOT 增益。"
     },
     {
      "src": "fig16.png",
      "caption": "图 16：batch-size-1 Decode 吞吐——H20-141GB 与 B300 参考。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "评估：高吞吐 Decode 前沿与 profile 权衡",
   "paras": [
    "图 17 显示吞吐-交互性前沿如何随系统演进。横轴是交互性（tokens/s/user），纵轴是吞吐（tokens/s/GPU）。在这些 DP/EP profile 中每个 DP rank 映射一个 GPU；交互性是每 GPU 吞吐除以每 DP rank 并发请求数。更右上方的点提供更好的用户可见生成速度与 GPU 效率组合。四条曲线代表累计系统演进，而非第 4 节任何优化的孤立增益。",
    "MTP 指 multi-token prediction；`(3, 1, 4)` 配置用三个投机步、top-k 1、四个 draft token。",
    "**系统优化移动整个前沿。**在 4K、每 DP rank 32 并发请求，每 GPU 吞吐从 **319.92 tokens/s/GPU** 升到 **703.15 tokens/s/GPU**，**2.20×** 增长。在 1M、每 DP rank 一请求，从 **27.05 tokens/s/GPU** 升到 **66.82 tokens/s/GPU**。前三个系统里程碑在 1M 只能每 DP rank 处理一个请求；最终系统支持四个并达到 **177.48 tokens/s/GPU**。扩展的操作包络来自更快执行和更大容量。",
    "**更小部署单元在选定高并发工作点保持效率。**在早前 H20 上服务 DeepSeek-V3/R1 的工作中，我们发现更小 EP 部署单元能在节点内保持更大比例 MoE 流量。DeepSeek-V4-Pro 在图 18 的工作点显示同样优势：每 DP rank 16 和 32 并发请求时，DP16-EP16 交付约 **3.6%-20%** 更高的每 GPU 吞吐。全扫描在每并发层级不单调，所以我们用 DP16-EP16 作为效率参考而非 DP32-EP32 的通用替代。",
    "**容量改变首选高吞吐 profile。**DP16-EP16 每 GPU 更高效，但 DP32-EP32 把专家权重分布到更多 rank、释放额外 HBM 给 KV 缓存。在 256K、512K、1M，每 DP rank 最大并发请求分别从 **8、4、2** 增到 **16、8、4**——一致的 **2×** 扩展。对与我们相似的长上下文并发目标，这个额外容量让 **DP32-EP32 成为容量导向的高吞吐 profile**，DP16-EP16 仍作为效率参考有用。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig17.png",
      "caption": "图 17：吞吐-交互性 Pareto 前沿。"
     },
     {
      "src": "fig18.png",
      "caption": "图 18：每 GPU 吞吐——DP16-EP16 vs DP32-EP32。"
     },
     {
      "src": "fig19.png",
      "caption": "图 19：每 DP rank 长上下文请求容量。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "结论",
   "paras": [
    "**一个模型不需要一个妥协的 profile。**我们为 H20 上的 DeepSeek-V4-Pro 构建了场景特定服务栈。Prefill 按上下文长度在 PP2 和 PP4 间切换。Decode 用 PP2-TP8 做低延迟、DP32-EP32 做高吞吐。通过协同设计容量、部署拓扑和执行路径，H20 能支撑 1M-token 上下文并满足多个服务 SLO，尽管计算有限、缺乏原生 FP4 Tensor Cores。",
    "**可迁移的成果是场景驱动的方法论。**Serving profile 不应只从硬件规格或孤立基准选择。我们建议从工作负载、SLO、上下文长度和并发出发，然后用 profiling 识别约束资源，把它转化为具体拓扑和执行路径决策。我们希望这套方法论帮助 AI 基础设施团队在多样化资源约束下构建实用的前沿模型服务系统——无论瓶颈是计算、内存容量、内存带宽还是互连——并把经验分享给更广的开源生态。"
   ],
   "fig_after": {}
  }
 ],
 "conclusion": [
  "这篇文章是 LMSYS 在 H20 上服务 DeepSeek-V4-Pro 的工程实录，最有价值的是它的**方法论**：一个模型不需要一个妥协的 profile——prefill 按上下文长度在 PP2/PP4 间切换，decode 用 PP2-TP8 低延迟、DP32-EP32 高吞吐。",
  "几个可迁移的工程判断：**MoE-TP 代替 MoE-EP**（可预测通信比不可预测失衡便宜）；**先减权重足迹再扩 KV**（Humming MXFP4AFP8 + Online C128 把容量提到 3.88×/10.14×）；**从生产路由调优形状**（通用启发式错过 384 专家的真实 M 分布）；以及「**选择 profile 从 workload 出发而非硬件规格**」。结果：H20 在 batch1 解码只比 B300 慢 1.42×，1M prompt 43.7 秒跑完。"
 ],
 "reference_url": "https://www.lmsys.org/blog/2026-08-19-deepseek-v4-pro-engine-optimization-h20"
}

with open("article_data.json", "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=1)
print(f"✅ 写入 article_data.json")