# -*- coding: utf-8 -*-
"""CAKE Compiler-Agent 编译 build"""
import json, os, sys

DATA = {
 "title": "CAKE：让编译器成为内核 agent 的进化伙伴，而不是黑盒",
 "lead": [
  "GPU 内核 agent 和 GPU 编程语言一直在各自发展，而两者之间的空白地带，恰恰是专家内核丢失的地方。内核 agent 把编译器当固定黑盒：它们改进提议、变异、排序，但环境只返回编译错误、正确性结果和端到端耗时——这些信号永远不说出是哪条程序决策导致了同步失败、硬件契约违规或流水线停顿。",
  "与此同时，agent 会写的那些语言也不是为 agent 设计的：tile 级 DSL 隐藏了 warp 特化、屏障编排和内存层放置——这些正是区分专家内核与「只是正确」的内核的关键；低级 DSL 暴露了这些控制，却要求一种布局演算，让 agent 的错误既易犯又难定位。",
  "CAKE 把两者协同设计：agent 编写 Cake IR，一种类型化、硬件显式的调度表示，无需布局代数就能拿到细粒度控制，并携带足够信息让 verifier 和成本模型在编译前推理程序；harness 回以本地化的正确性与性能诊断，且它本身也是演化目标——重复失败变成新的 verifier 规则、IR 原语、成本模型校准和可复用战术，而不是一次性补丁。"
 ],
 "summary": [
  {
   "key": "核心洞察",
   "body": "内核 agent 的问题不在「写代码」，而在「得不到能定位问题的反馈」。CAKE 让编译器返回本地化诊断，且 harness 本身随内核一起演化——重复失败沉淀为 verifier 规则和 IR 原语。"
  },
  {
   "key": "关键结果",
   "body": "80M token 预算下，Cake IR 在 Flash-KMeans clean-start 达 1.144× tuned FlashML（直接 CUDA/PTX 仅 0.928×），3/3 达 plateau；KDA 2.05× over FlashKDA，4 个内核 PR 已上游。"
  },
  {
   "key": "设计承诺",
   "body": "agent 编辑类型化 IR 而非裸 CUDA；编译器返回本地化诊断而非 pass/fail；harness 是演化目标。一张 schedule 语言覆盖 Ampere 到 Blackwell。"
  }
 ],
 "sections": [
  {
   "type": "h2",
   "title": "背景：专家内核为什么会在 agent 流程里丢失",
   "paras": [
    "编码 agent 已经能在正确性和性能自动测量的环境中编写、修订 GPU 程序。但多数这类系统仍把编程环境当固定黑盒：agent 提议代码、编译、跑数值测试、测延迟、再挑一次编辑。循环对局部调优有效，但崩溃不指出违反的是哪条安全或硬件条件，一个延迟数字也解释不了是哪个程序决策在拖性能。",
    "专家内核程序员的工作方式不同：他们在脑内保持工作负载的紧凑模型，对显式硬件资源做推理，在内核之间携带可复用规则。编译器其实已经握着外部化这一过程所需的大部分机制——结构化操作词汇、资源模型、合法性检查、静态分析、成本模型、lowering 规则。CAKE 的问题是如何让这些机制变得「对 agent 可见」，以及当前沿工作负载暴露缺口时如何改进它。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig01.png",
      "caption": "图 1：CAKE 概览对比——agent 写 Cake IR，编译器返回本地化诊断并随内核演化。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "三个承诺：CAKE 的答案",
   "paras": [
    "CAKE 用三个承诺回答。第一，agent 编辑类型化 IR 而非裸 CUDA，所以硬件决策在代码生成前就可检查。第二，编译器返回本地化的正确性与性能诊断，而非一个 pass/fail 位，所以廉价分析能在候选消耗 GPU 时间之前过滤它们。第三，harness 本身是演化目标：重复失败变成 verifier 规则、校准任务或新原语，由语料测试把关。",
    "Cake IR 是自底向上通过 agent 驱动的抽象发现构建的，素材是生产内核语料加硬件设计原则，约束是必须复现专家手写内核的物理调度与性能。harness 同样主要由 agent 在人工合并闸门下维护。",
    "系统支持两个入口，对应内核工作的两种实际到达方式：从 FlashInfer 或 CUTLASS 这样的库里的生产内核出发继续演化；或对没有成熟参考的工作负载，从高层描述或 Triton 实现出发，让 agent 用 Cake IR 选 warp 特化、布局和流水线结构，编译器负责验证并生成 CUDA。"
   ],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "Cake IR：显式的机器调度",
   "paras": [
    "Cake IR 记录机器该如何被驱动：哪些 warp 承担哪些角色、哪些缓冲区被多深地分阶段、哪个屏障守哪个交接、哪个指令形式消费哪个操作数。分工是：调度声明要发生什么，lowering 推导如何发生——屏障地址、相位位、TMEM 偏移、描述符编码、warp 身份全部从声明计算，而非由 agent 手写。",
    "四个性质在起作用。类型化词汇：计算、内存移动、同步、数学、warp 控制用固定 IR 词汇而非内嵌 C 或 PTX。声明式资源：内存区、同步状态、流水线声明一次，IR 知道每个缓冲区的形状、dtype 和生命周期。显式角色：warp 组被命名，每个跨角色交接可见而非隐式约定。自动派生元数据：这些声明的机械后果被 lower 而非手写。",
    "回报是分析能在代码生成前就从显式调度决策推理。harness 能把发现关联到受影响的资源、角色或阶段，而不是只返回一个后端错误或挂起。布局故意不是一等抽象：不需要 agent 操作布局代数，Cake IR 直接在调度里记录存储与访问决策，编译器检查生产者与消费者表示与目标硬件兼容。",
    "同一张 schedule 语言覆盖 Ampere 到 Blackwell：角色-屏障-流水线调度在结构上可移植，而指令准入与 lowering 保持目标特定。Cake 精确映射所连 GPU，对不支持的 target 明确报告而非静默替换成另一架构，只在有目标特定校准处给出性能估计。"
   ],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "编译器 harness：反馈回路本身会进化",
   "paras": [
    "harness 是 Cake IR 周围的 agent 可见环境。人在高层描述想要的分析，agent 在验证下实现、维护并精炼它们。内核演化期间，廉价分析在候选到达昂贵 GPU 运行前对它们排序、过滤。",
    "编译前，harness 检查类型化调度的同步、内存安全、数据流、资源、指令和数据表示违规——拒绝很多数学上看似合理但与目标执行模型不兼容的候选。一项发现指出受影响的程序区域和违反的契约类别，通过稳定分析接口给 agent 一个有用的修复目标。数值正确性对比内核与参考在不同形状和输入分布上的输出；最终验收要求在对应目标框架中端到端评估。一个校准过的成本模型估计候选性能并返回高层瓶颈归因与优化指导。",
    "CAKE 让编译器与内核一起演化：内核候选、验证结果、基准和失败报告为提议并验证编译器变更提供证据。两条互补路径：agent 检视生产内核与硬件文档发现缺失的 Blackwell 模式（新指令形式、资源类型、描述符变体、同步惯用法）并提变更提案；或把失败候选的反馈（sanitizer 报告、失败案例、正确性失配、调试日志）蒸馏成新分析——不透明运行崩溃变成 verifier 规则，重复非法 lowering 模式变成静态检查，系统性误预测变成校准目标。",
    "两条路径耦合：新原语向编译器暴露更多硬件事实、让分析更强；新分析反过来约束未来原语的设计空间。编译器变更跨内核语料做测试把关——原语和它的分析必须一起演化。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig02.png",
      "caption": "图 2：编译器 harness——安全/硬件一致性/数据一致性/调度语义的预编译闸门 + 数值验证 + 性能分析 + 优化提示。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "评估：clean-start 能不能跑赢 tuned 基线",
   "paras": [
    "三个问题：harness 能否驱动重复 clean-start 演化越过 tuned 基线；能否在不看低级实现的情况下综合前沿内核；能否复现专家内核。所有测量用 B200 上的 GPU 正确性检查 + CUPTI 计时，每次计时前刷新 L2。",
    "Flash-KMeans clean-start 是核心对照。这是 Sparse VideoGen2 启发的精确 k-means 工作负载，Lloyd 迭代的两个 BF16 内核占端到端 95% 以上：assign（计算密集的 BF16 GEMM+reduction）和 centroid_update（带宽与原子竞争敏感）。treatment 组写类型化 Cake IR，对照组直接写 CUDA C++ 与内联 PTX，都拿同样的任务规格、正确性 oracle、基准接口，但隐藏低级目标实现。",
    "结果：80M token 预算下，Cake IR 3/3 runs 达到预设 plateau 标准，中位最优 1.144× tuned FlashML 基线，中位 active evolve 时间 1.89 小时；直接 CUDA/PTX 0/3 达 plateau，中位最优仅 0.928×，active evolve 3.73 小时。轨迹显示 Cake IR 均值在 55M token 时跨过 tuned 基线并继续改善，而 CUDA/PTX 均值到 80M 截止仍在基线之下。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig03.png",
      "caption": "图 3：Flash-KMeans clean-start 三次运行轨迹——Cake IR 在 55M token 跨过 tuned 基线并继续提升，CUDA/PTX 始终在基线下方。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "前沿内核综合：KDA、TinyGEMM 与 Alpha-MoE",
   "paras": [
    "前沿内核的运作定义：agent 必须在不检视低级目标实现的情况下发现其物理调度。这是协同演化的 IR 最该帮上忙的场景——搜索无法锚定到已知良好设计，也是 harness 最容易暴露缺口的场景。",
    "Kimi Delta Attention（KDA）是最清晰的案例。官方 FlashKDA 只当黑盒计时基线，源码与生成代码都不给 agent。FlashKDA 兼容的 prefill 覆盖固定/打包可变/tail 输入，在六个 B200 BF16 形状上达 2.05× 几何平均加速，验证契约上逐位正确，且在 SGLang 下 Kimi-K3 端到端服务中验证。生成 CUDA 已在 FlashInfer PR #4262 可用，下游用户零依赖 Cake。独立的 decode 路径跨 30 个公开 API 形状达 1.14× 几何平均（PR #4279）。与 GEMM 不同，KDA 含一个必须跨 chunk 保持存活的循环状态——这是对调度表示的好测试。",
    "Gated DeltaNet 的 prefill 与 speculative-decode 路径在保持模型循环状态的同时改善性能；MiniMax sparse attention 进一步证明同一表示支持 prefill 与 decode 的稀疏注意力家族。",
    "TinyGEMM 是参照引导的生产演化案例：从 FlashInfer 的 TensorRT-LLM 派生小 MM BF16 内核出发，agent 产出浅/深流水线的自适应家族，含 PDL 变体与 8 以下批大小。PR #4274 报告跨 35 个规范形状 18-23% 几何平均内核时间缩减。Greedy decoding 在 B200/GB300 上对 GPT-OSS-20B/120B 保持逐位一致。",
    "Alpha-MoE 验证了通信密集的 megakernel 演化：从 Hopper 原实现出发，Cake agent 为 Blackwell 重写了它的 W8A8 fused MoE megakernel——融合路由收集、两个投影、激活、重量化与路由加权输出累加进一个设备程序。API 级加速 6.204×（N=256）/4.025×（N=512），GPU-span 重测 1.215×/1.170×——大的 API 级增益来自 launch/schedule 融合减少调度空隙与更简单的 workspace 处理（参考启动 5 个 GPU 活动，Alpha-MoE 只用输出重置 + 一个 megakernel）。PR #4287。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig04.png",
      "caption": "图 4：KDA prefill 演化轨迹——token 预算 vs 相对性能，最终 2.05× over FlashKDA。"
     },
     {
      "src": "fig05.png",
      "caption": "图 5：TinyGEMM 演化轨迹——跨 35 个形状 18-23% 内核时间缩减。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "已知内核复现与语料规模",
   "paras": [
    "为验证生产级输出，还针对带 SOTA 基线（TensorRT-LLM、CUTLASS、DeepGEMM、FlashAttention-4、FlashInfer）的已知算子族。11 个固定对比中 10 个达标或超过参考，剩余 1 个达 96.5%。最强的是两个 MQA indexer 约 1.27×。",
    "低于参考的变体一般反映编译器集成成熟度而非不同算法目标：内核想要的特性还在集成中时，提交物用最接近的支持策略。反过来，最强的 indexer 胜出不是参考内核的忠实转录——移植中 agent 探索了原实现没有的优化并保留通过正确性与基准的变体。每个 Cake IR 实现都比其审计参考设备核心更短，证明这些硬件调度能在 Cake IR 里紧凑表示。",
    "已验证语料含 400+ 静态/编译案例与 399 个 GPU 正确性案例，跨约 28 个家族——注意力、稠密/稀疏 GEMM、MoE、量化、归一化、状态空间模型、KNN、KMeans——从 Ampere 到 Blackwell 的架构特定路径。因为角色、屏障、缓冲区被声明而非隐含，通常分开的内核可表达为一个设备程序：BatchAttention 合并 decode 与 prefill，Alpha-MoE 融合路由/专家计算/输出累加而不物化中间结果。4 个上游变更：KDA prefill、KDA decode、TinyGEMM2、Alpha-MoE。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig06.png",
      "caption": "图 6：Alpha-MoE W8A8 演化轨迹——Blackwell megakernel 重写，API 级 6.2×/4.0×。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "从 tuned 形状到库：单独的演化阶段",
   "paras": [
    "以上所有都在优化一个形状。而库要接受调用方传的任何形状。弥合这个差距不是在内循环上跑更多形状——它是一个独立阶段，目标、排序信号、失败模式都不同，CAKE 也把它当独立阶段处理。",
    "精确形状给内循环干净的除数和激进的专化；用广覆盖给这个循环打分会削弱信号。因此泛化只在强 per-shape 种子存在后开始，并用含 dispatcher 的固定工作负载性能打分。错误或慢的种子回到内循环而非藏在路由后面。泛化阶段把测量过的种子分组进形状桶，产出专化或共享变体，并在显式回退后排序它们的 guard。报告聚合前，验证覆盖代表性与留出输入、边界与尾部情况、重叠或缺失 guard、以及回退路径。",
    "Dispatcher-backed 的 KNN 与 KMeans 家族跨 400+ 形状提升 1.42×-2.12× 性能。CAKE 的目标是：用模块化的内核族，让 agent 不只是写出一个快的形状，而是演化出一个库能调的家族。"
   ],
   "fig_after": {}
  }
 ],
 "conclusion": [
  "CAKE 的核心主张是把编译器从黑盒改造成「能对话的进化伙伴」。三个承诺——类型化 IR、本地化诊断、harness 自身可演化——构成一个正反馈回路：agent 遇到的每个新失败模式，都变成让下一个 agent 更少撞墙的 verifier 规则或 IR 原语。",
  "最有力的证据是 clean-start 对照：同样 80M token、同样的 agent 与任务，写 Cake IR 的中位 1.144×、3/3 达 plateau、1.89 小时；写裸 CUDA/PTX 的 0.928×、0/3、3.73 小时。这不是「换了个语言更好写」，而是「反馈信号的质量直接决定 agent 能找到多好的调度」。对 GPU 内核自动化来说，这条思路很可能比继续堆更强的 agent 更重要。"
 ],
 "reference_url": "https://arxiv.org/abs/2608.12629"
}

with open("article_data.json", "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=1)
print(f"✅ 写入 article_data.json")