# -*- coding: utf-8 -*-
"""There Is No Address 编译 build"""
import json, os, sys

DATA = {
 "title": "没有地址：KV 缓存、disaggregation 与内存层级的所有权摩擦",
 "lead": [
  "上一篇文章论证了 KV 缓存没有互换格式。姑且给它一个。假设两个厂商同意布局、dtype、块大小、scale 位置和清单里的每一个轴。字节仍然必须移动。",
  "这部分看起来像管道工程、其实不是，因为传输库对另一端的机器类型并不中立。它在历史上可以不必中立的原因，是一个程序总是拥有它移动数据所经的整个内存层级。Disaggregation 是第一次把这个所有权拆给两个厂商。"
 ],
 "summary": [
  {
   "key": "核心洞见",
   "body": "每个机器都是内存层级，且假设单一所有者：CPU 靠硬件缓存控制器+编译器，GPU 靠 CUDA 程序员+TMA，Cerebras 靠 cslc（placement+routing 在源码里）。传输库只能触达「公共横档」——全局可寻址、物理稳定、非计算引擎可及的一档（DRAM/HBM）。"
  },
  {
   "key": "无地址的 Wafer",
   "body": "WSE-3 的 44GB SRAM 不是池，是 90 万×48KB 私有 SRAM，无共享地址空间。nixlBasicDesc 的 (addr, len, devId) 填不上：KV block 跨数千 PE、无 uintptr_t 可命名。公共横档缺失→字节必须 staging 到 host DRAM/MemoryX 再按 dataflow 拉进 fabric。"
  },
  {
   "key": "所有权摩擦",
   "body": "disaggregation 把单一优化域切成两半：producer 编译器看不见 consumer 的 tiling/路由/颜色，反之亦然。三种答案都不舒服：双边协议（n² 个）、中立互换格式（每个 handoff 付转换延迟）、让一方权威（等于合并，放弃单一所有者）。"
  }
 ],
 "sections": [
  {
   "type": "h2",
   "title": "每个机器都是内存层级",
   "paras": [
    "这个问题对加速器而言并不新鲜。它是系统编程里最古老的结构。",
    "CPU 有寄存器，然后 L1、L2、L3、DRAM、存储。每一级都比下一级更小、更快、更近，忽略层级的程序比尊重它的慢一个数量级。大多数程序员不天天想这个的原因是两个机制隐藏了它：硬件有缓存控制器，不问就抓取、逐出和预取；编译器代你推理局部性，分块循环、重排访问，让工作集装进一个实际上很快的层级。那个分析发展得够成熟、有自己的文献，建立在格、不动点和半环之上。",
    "GPU 有相同结构但移除了自动化。在 Blackwell 上，一个 SM 有寄存器、张量内存、每 SM 128 KB 的可配置统一 L1 和共享内存、64-65 MB 的整体 L2、然后 HBM。共享内存访问约 20-30 周期。分布式共享内存让 SM 能在 cluster 内到达邻居的共享内存，带延迟惩罚。张量内存更新，与寄存器不同，需要显式用户分配和管理。",
    "GPU 不隐藏这些。没有缓存控制器决定什么该进共享内存。你写 `__shared__`，自己把 tile 分阶段进去，或用张量内存加速器在计算进行时异步把块从全局内存搬进共享内存。层级暴露出来，编程模型存在正是为了让你利用它。",
    "Cerebras wafer 是同一个想法推到极限。大约 90 万个处理单元在 2D mesh 里，每个 48 KB 本地 SRAM，每个 PE 只访问自己的内存、亚纳秒延迟。其他一切是消息。PE 通过电路交换的 network-on-chip 通信，沿配置路由发送叫 wavelet 的数据包，每个 PE 的路由器支持有限数量的并发电路——24，加 8 保留——叫颜色（colors），是绑定到物理路由资源的虚拟通道。两条可能碰撞的流必须分配不同颜色。",
    "那台机器可编程，这个「如何」很重要，因为这个论证的简单版本是 wafer 很奇异因此很难。它不奇异。它有一种语言。CSL 是 Zig 启发的 dataflow 语言，计算由数据到达触发，CSL 程序不只是内核代码：它包含一个布局文件，规定哪些代码在哪些 PE 上运行、数据如何在它们之间路由。cslc 编译器把它映射到物理 fabric。放置和路由是源程序的一等公民。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig01.png",
      "caption": "图 1：三台机器、三个层级、三个不同的「谁管理局部性」答案——硬件、程序员、编译器。全都有效，全都假设单一所有者。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "传输库真正能触达的",
   "paras": [
    "现在把网络放中间，问远程对等方可以写进那些梯子的哪一档。",
    "答案是一档，而且总是同一档：全局可寻址、物理稳定、可被非计算引擎的设备到达的那一档。CPU 上是 DRAM，GPU 上是 HBM。从来不是 L1、不是共享内存、不是张量内存、不是 PE 的 scratchpad。",
    "NIXL——NVIDIA 的推理传输库，vLLM 的 NixlConnector 和 Dynamo 的 disaggregated 路径下面的东西——在类型系统里说明这点。它的内存空间被穷举："
   ],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "NIXL 内存类型枚举",
   "paras": [
    "__CODE__// nixl/src/api/cpp/nixl_types.h\nenum nixl_mem_t {\n  DRAM_SEG,\n  VRAM_SEG,\n  BLK_SEG,\n  OBJ_SEG,\n  FILE_SEG\n};",
    "Host DRAM、GPU VRAM、块设备、对象存储、文件。没有 `SMEM_SEG`、没有 `TMEM_SEG`、没有 `PE_SEG`，它们的缺席不是疏忽。那些层级从片外不可被任何东西寻址。",
    "NIXL 移动的单元相应简单："
   ],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "NIXL 基本描述符",
   "paras": [
    "__CODE__// nixl/src/api/cpp/nixl_descriptors.h\n/**\n * @class nixlBasicDesc\n * @brief A basic descriptor class, single contiguous memory/storage\n *        element, alongside supporting methods\n */\nclass nixlBasicDesc {\n public:\n    /** @var Start of Buffer */\n    uintptr_t addr;\n    /** @var Buffer Length */\n    size_t len;\n    /** @var deviceID/blockID/fileID */\n    uint64_t devId;\n};",
    "一个指针、一个长度、一个设备号。单一连续。",
    "这就是为什么 RDMA 需要**注册（registration）**：页面钉住让 OS 无法移动它们，虚拟到物理映射交给 NIC，返回一个 key 让远程对等方每次访问出示。注册正是让公共横档的区域足够稳定、让外部设备能写进去的操作。它在层级的任何其他层级都没有意义。"
   ],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "seam 在 GPU 上早已存在",
   "paras": [
    "这里是容易错过、因为从未让任何人痛苦过的部分。",
    "你不能 RDMA 进共享内存。如果远程机器给你发 KV 缓存，它落在 HBM。把它从 HBM 弄进 attention 内核真正想要的 128 KB 共享内存是第二次移动，由接收方用自己的机制执行——一个 TMA 描述符、一个异步拷贝、一个写那个内核的人选择的 tiling 策略。",
    "所以即使在普通的全 NVIDIA 情形，交接也有两半。网络把字节送到公共横档。消费者自己的编译器和内核把字节沿层级带完剩下的路。",
    "没人把这体验成边界，因为两半是同一批人对着同一布局写的。生产者知道消费者会要特定顺序的 128 元素 tile，所以它把缓存按让消费者 TMA 描述符便宜的顺序写进 HBM。那个协议真实、承重、完全未文档化，因为它从未需要离开建筑。",
    "那就是 seam。它一直存在。Disaggregation 是当两半不再由同一组织书写时发生的事。"
   ],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "wafer 移除了横档",
   "paras": [
    "现在讲它变得可见的情形。",
    "WSE-3 有 44 GB SRAM，这个数字邀请你把它想象成一个池，像你想象 80 GB HBM 一样。它不是池。它是 90 万×48 KB，对每个 PE 私有，彼此之间没有共享地址空间。",
    "试着填描述符。一个中型模型一层的单个 KV 块量级是约一百千字节：不是某个 PE 的 scratchpad，是两三个，而且在任何地址意义上都不相邻，因为没有地址意义。一个序列的整个缓存横跨数千 PE。没有命名它的 `uintptr_t addr`，没有字节连续其上的 `size_t len`，没有解析成 NIC 能写进去的 `devId`。`VRAM_SEG` 是最近的枚举值，它是错的：这不是控制器后面的内存，这是计算基底。",
    "也没有东西可钉住。注册假设你能让内存静止、同时设备写进去的内存。在 wafer 上，值住在哪是调度的一部分，而调度是 cslc 从布局文件发射的。",
    "公共横档缺失。这意味着字节必须 staging：落在 host DRAM 或 MemoryX——已经在流式输入权重的片外存储——然后由 wafer 自己的 dataflow 作为调度工作拉上 fabric。",
    "所以交接至少两跳，第二跳不是发送方能控制的 DMA。把它与 disaggregate 的理由对照。第一部分论证的是延迟——分离阶段让 prefill 停止打断 decode、首 token 时间改善。现在首 token 等一个网络穿越、一个 staging 缓冲、一个 fabric 分发，全部坐在 TTFT 路径上、在拆分本想保护的指标之前。Splitwise 测过一个 512-token OPT-66B 请求产生 1.13 GB KV 缓存；长上下文请求远大于此。"
   ],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "摩擦是所有权，不是奇异",
   "paras": [
    "把这些读成 wafer 规模硬件不实用的论证很容易。那不是论点，上面 CSL 的描述就是原因。",
    "Cerebras 有做放置和路由的编译器。NVIDIA 有编译器、TMA 引擎和一整套把全局内存 staging 进共享内存的成熟惯用法。Intel、AMD 和 Arm 有几十年的缓存感知代码生成，CPU 有硬件控制器自动做。每一个都是对**它自己的机器**的局部性问题的合格答案。",
    "摩擦在于：disaggregated 流水线需要一个横跨其中两台机器的答案，而任一工具链都无法表示另一半。",
    "cslc 能调度张量落在 fabric 的哪里，但它看不见生产者的 HBM 布局、它的块表、或它的 attention 内核假定的 tiling 约定。生产者的编译器能发射它的内核最喜欢的任何布局的 KV 缓存，但它没有「然后这必须分发到一万个 PE、其路由颜色已分配」的表示。双方各自在自己那一边正确优化局部性，在一个双方都无法看穿的边界两侧。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig02.png",
      "caption": "图 2：生产者的编译器与消费者的编译器——共享词汇只有 (addr, len, devId)，它表达不了局部性、成本或调度。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "描述符是全部共享词汇",
   "paras": [
    "描述符是他们共享的全部词汇，而它只能表达一个字节范围、别的都不能。不能表达到达那个范围的成本。不能表达字节到达时该是什么布局。不能表达接收方是否自由放置它们，或是否已承诺一个约束它们能去哪的路由调度。",
    "每个成熟架构通过给一个组件足够可见性来推理整条路径，从而解决局部性。Disaggregation 移除那个可见性，用一个指针替换它。"
   ],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "连公共横档都不均匀",
   "paras": [
    "扁平模型在任何这些之前、在普通硬件上就已经错了。",
    "两个 GPU 之间的带宽随它们物理位置差 **72×**：域内 NVLink 约 900 GB/s，跨节点 InfiniBand 50 GB/s，跨数据中心 TCP 12.5 GB/s。近期工作指出 DistServe、Splitwise 和 Mooncake 都假设均匀 RDMA，完全忽略这个。",
    "同样缺陷，更温和的形式。描述符说 `(addr, len, devId)`，没说到达 `devId` 要花什么。选择哪个 decode 实例接收缓存、在 72× 成本跨度上做放置决定的调度器，穿过的却是一个不报告任何成本的接口。"
   ],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "另一个拓扑：什么都不缓存",
   "paras": [
    "以上都假设拆分是 prefill-then-decode，缓存每次请求跨一次。NVIDIA 自己的安排不是那样。",
    "Groq LPX 取 decode 循环里延迟敏感的部分——feed-forward 和 MoE 专家执行——而 Rubin GPU 保留 prefill **和 decode attention**。Attention 留在 GPU 上因为 KV 缓存住在那里。所以缓存从不跨任何东西。跨的是激活，边界落进单个 decode 步内部。",
    "算出形状。对隐藏维 `d`（bf16），每层跨 ~`2d` 字节每 token，回程大致相同。`d = 8192` 时约每向 16 KB，每层每 token 32 KB 往返，跨一百层每 token 几兆字节。",
    "带宽不起眼。延迟不起眼——那些穿越是**串行**的——第 `n+1` 层必须等第 `n` 层返回。一百层是每 token 两百次边界穿越，而且不重叠。",
    "按每次单向穿越一微秒，那是在任何算术之前每 token 纯互连延迟 200 µs。对 10 ms inter-token 预算它是 2%。对为买 decode 加速器而定的 1 ms 预算，它是 20%，而且随深度线性缩放。",
    "那个算术从已发表架构描述和典型模型维度推导，非实测。NVIDIA 未发布 GPU-to-LPX 互连延迟，真实实现可能跨 token 流水线或批量层、改变它。结构点无论如何成立：当边界落进 decode 步内部，模型深度乘以你的互连延迟，而没有任何传输描述符能表达那个。"
   ],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "两个拓扑，一个缺失的词汇",
   "paras": [
    "两个架构、都在出货、成本结构相反。一个移动一次大负载、受带宽和 staging 约束。另一个持续移动小负载、受延迟和抖动约束。两者都叫 disaggregated inference，同一个描述符是任一者唯一可用的词汇。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig03.png",
      "caption": "图 3：两种拓扑——Phase split（AWS/AMD，KV ~GB 一次）vs Intra-step split（NVIDIA，激活 ~KB 每层两次、延迟×深度）。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "这真的可编程吗？",
   "paras": [
    "把这篇叠在上一篇上，画面比任一单独都糟。",
    "KV 缓存没有互换格式，因为布局与内核协同设计：656 字节 MLA struct 的字段偏移是它有的那些，因为特定 warp 访问模式在那硬件上快。这篇说局部性与层级协同设计：cslc 对着 fabric 分配路由颜色，TMA 描述符假设一个 tiling，缓存控制器假设一个 stride。",
    "那是同一现象见两次。在两侧，性能来自协同设计，而协同设计只对能看见整条路径的编译器可用。两个问题都不是缺文档。它们是把单一优化域切成两半的两张脸。",
    "所以组合问题比「该有人写个 spec」更尖锐。它是两个独立协同设计的系统能否在不摧毁让各自变快的协同设计的情况下接合。有三种答案形状，没一个舒服。",
    "**双边协议。**AWS 和 Cerebras 私下协商格式、staging 协议和分发调度，互相调优。这显然有效，几乎可以肯定正在发生。它也不泛化：协议对 AMD 和 Cerebras 一文不值，n 个厂商需要 n² 个。这是任何互连的标准前时代，历史上它要么以标准结束、要么以一方格式靠市场份额获胜结束。",
    "**中立互换格式。**定义规范 KV 表示，双方转换。现在每个交接在一端付布局转换、另一端付层级重分发，都在 time-to-first-token 路径上，对着 Splitwise 测到的单次适度请求 1.13 GB 负载。你用最开始支持 disaggregate 的延迟买了可移植性。",
    "**让一方权威。**生产者直接以消费者层级想要的形式发射——纸面上正确的答案，因为它完全移除转换。但它要求生产者的编译器建模消费者的内存层级、路由约束和内核 tiling。那不是一个编译器之间的接口。那是合并，正是 disaggregation 放弃的单一所有者属性。",
    "我不认为这不可解，行业最终靠同意某样东西解决了更糟的阻抗失配。但它不是有管道答案的管道问题，当前工具也不是解决方案的早期版本。`(addr, len, devId)` 不是更丰富描述符的初稿。它是一个网络能到达的那一档的正确描述，在一个性能住在所有其他档上的栈里。"
   ],
   "fig_after": {}
  }
 ],
 "conclusion": [
  "这篇文章把「disaggregation 为什么难」从模糊的感觉还原成一个精确的结构观察：每个内存层级都假设单一所有者，而传输库只能触达「公共横档」（DRAM/HBM）——NIXL 的枚举、nixlBasicDesc 的 (addr, len, devId)、RDMA 注册，全都是对这一档的描述。",
  "Cerebras wafer 让问题显形：44GB SRAM 不是池而是 90 万份私有 48KB，KV block 跨数千 PE，没有任何 uintptr_t 能命名它。而 NVIDIA 自己的 Groq LPX 选择让 KV 缓存不跨任何东西、只跨激活（延迟×深度）。三个不舒适的答案（n² 双边协议、付费转换的中立格式、等于合并的一方权威）指向同一结论：**这不是管道问题，是所有权问题**——拆分单一优化域时，协同设计本身就是被牺牲的东西。"
 ],
 "reference_url": "https://hiraditya.github.io/posts/there-is-no-address/"
}

with open("article_data.json", "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=1)
print(f"✅ 写入 article_data.json")