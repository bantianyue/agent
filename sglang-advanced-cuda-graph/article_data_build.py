# -*- coding: utf-8 -*-
"""SGLang Advanced CUDA Graph 编译 build"""
import json, os, sys

DATA = {
 "title": "SGLang 中的高级 CUDA Graph 技术：Breakable CUDA Graph 与全图 Prefill",
 "lead": [
  "CUDA Graph 承诺消除内核启动开销，但要在真实推理引擎里兑现这个收益，需要把尽可能多的工作负载纳入 graph，同时不牺牲兼容性、启动时间或内存。",
  "在 SGLang 中，我们围绕一个公共 runner/backend 接口重构了 CUDA Graph 支持，让不同的捕获策略能在执行路径间复用。对更复杂的 prefill 路径，SGLang 社区引入了 Breakable CUDA Graph，并率先用 FA4 和 FlashInfer attention 后端实现全 CUDA Graph 支持。这两种技术都是先在 SGLang 里作为开源服务技术开发出来的。",
  "我们还深入 CUDA Graph 内存管理，包括跨形状和 graph segment 的内存复用，这正成为 SGLang 整体内存管理越来越重要的一部分。"
 ],
 "summary": [
  {
   "key": "核心成果",
   "body": "Breakable CUDA Graph（BCG）是 prefill 的默认方案：用 @eager_on_graph 标记不兼容操作，图段间 eager 执行。代码量只有 torch.compile 方案的约 1/4（521 vs 1771 行），构建快 3.8-5.2×。"
  },
  {
   "key": "性能数据",
   "body": "prefill 单独测量：BCG 比 eager 快 1.70×，全图捕获达 1.93×，TC piecewise 1.45×——BCG 回放也比编译器后端快 17%。扩散：Qwen-Image 6.48s→2.45s，Z-Image 1.231s→0.662s。"
  },
  {
   "key": "内存管理",
   "body": "跨 segment 共享内存池 + eager break 弱引用 + 单一最大输出缓冲；捕获到 chunked-prefill size 能消除最坏激活峰值（gpt-oss-120b 0.56→0.001 GB）。"
  }
 ],
 "sections": [
  {
   "type": "h2",
   "title": "背景：为什么 CUDA Graph 集成很难",
   "paras": [
    "一次推理步骤不是单个内核，而是一长串 GPU 操作。在现代 LLM 服务引擎中，从 CPU 反复启动这些操作会带来明显开销，尤其在延迟敏感的工作负载上。CUDA Graph 通过记录一次 GPU 工作、以低得多的启动开销重放来降低这个开销。",
    "但在现代推理引擎里用好 CUDA Graph 并不简单。graph 设计必须适配不同执行阶段、与复杂内核和运行时相关行为兼容，并控制 graph 自身的捕获时间和内存开销。随着推理栈变复杂，正确的 CUDA Graph 集成越来越重要。",
    "本文介绍 SGLang 如何构建 CUDA Graph 支持以及我们改了什么：runner/backend 拆分与灵活组合；无编译器的 Breakable CUDA Graph；prefill 的全 CUDA Graph；CUDA Graph 内存占用。"
   ],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "Runner/Backend 拆分：可复用的捕获策略",
   "paras": [
    "重构之前，CUDA Graph 支持是围绕各执行路径各自生长出来的。decode、prefill、投机解码各有自己的 CUDA Graph runner，捕获形状、静态缓冲、重放、graph 配置的逻辑大量重叠。随着执行模式和捕获策略增多，这种重复让基础设施复用变难，也让 CUDA Graph 相关的服务参数越来越含糊。",
    "重构（PR #23906）把职责分成两层。**runner** 管理捕获和重放所需的执行特定状态：捕获形状、静态输入缓冲、attention 元数据、把活 batch 填充到捕获形状。**backend** 决定执行如何被捕获：作为一个完整 graph、一串可断开的 segment、还是编译器生成的片段。",
    "因为 runner 只依赖公共 backend 接口，每个执行路径能独立选择捕获策略。prefill 和 decode 有各自的 runner；投机解码增加更多：EAGLE draft、draft-extend 和 frozen-KV MTP draft 步骤各建在 decode runner 上的 runner，而 target verify 就是 decode runner 本身，每请求捕获多个 token。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig01.png",
      "caption": "图 1：runner 为每个执行路径准备捕获与重放，backend 决定 forward 如何变成可重放 graph——完整一张图、捕获时分段、还是先 trace 再切分。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "三种捕获 backend",
   "paras": [
    "**Full CUDA Graph**：为每个选中形状捕获一个 torch.cuda.CUDAGraph，无 eager 区域，三个 backend 中重放启动最少。这对 decode 天然适用：每个请求贡献一个 token，主形状变量是 batch size，可由一组捕获的 batch-size bucket 覆盖。prefill 变化维度更多因此更难。",
    "**Breakable CUDA Graph（BCG）**：捕获 graph 安全区域，同时允许选定操作在图段之间 eager 运行。不兼容操作可用 @eager_on_graph 标记；捕获在标记函数前停下、之后恢复，产生一串被 eager 区域分隔的 CUDA Graph segment。与基于编译器的分段捕获不同，这些 break 直接在捕获时插入，而不是先 trace 整个模型再发现。",
    "**TC piecewise CUDA Graph**：第三个 backend 通过编译器达到类似分段。torch.compile 用 fullgraph=True trace forward，生成的 FX graph 在注册的切分点分割，每片独立编译捕获。它是 SGLang 对部分 CUDA Graph 捕获的第一版答案，至今仍在 breakable 捕获未验证的平台发布。"
   ],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "Breakable CUDA Graph：无编译器的 Eager Breaks",
   "paras": [
    "CUDA Graph 传统上要求捕获区域完全 graph 兼容。实践中，现代推理负载包含无法直接捕获的操作。prefill attention 是常见例子：一些 attention 后端依赖运行时元数据和 host 端准备。单个不兼容操作就能阻止 CUDA Graph 覆盖 forward 大得多的部分。",
    "我们引入 BCG 让捕获更灵活。机制和 @eager_on_graph 装饰器先作为 CUDA Graph debug 模式的一部分落地（PR #19102），随后在 PR #22218 中构建成 prefill 的 breakable piecewise backend。不再要求整个 forward graph 兼容，BCG 允许选定操作 eager 运行，同时捕获它们周围 graph 兼容的区域。高层看，forward 变成一串由显式 eager break 连接的 CUDA Graph segment。"
   ],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "BCG 的设计与机制",
   "paras": [
    "CUDA Graph 在重放遵循固定 GPU 操作序列、无 host 参与时效果最好。但真实推理 forward 含有不适合这个模型的操作：attention 后端可能根据实时序列长度规划，collective 可能涉及运行时协调，服务功能可能动态更新状态。",
    "只要出现一个这样的操作就放弃 CUDA Graph，会让 forward 大部分未捕获。BCG 让开发者直接用 @eager_on_graph 标记不兼容区域。捕获时，当前 graph segment 在到达标记函数时关闭，函数 eager 运行，之后在新 segment 恢复捕获。",
    "重放时，记录的 graph segment 和 eager 函数按同样顺序运行。捕获时标记函数在图段之间运行一次，它返回的 tensor 被保留为持久边界缓冲，设备地址保持固定；后续 segment 针对该地址捕获。每次重放 eager 函数正常运行并返回新 tensor，BCG 把它拷贝进保留缓冲，下个 segment 从最初捕获的地址读到更新值。BCG 从不检视或 trace eager 区域内部——它们只需正确执行。",
    "功能上，BCG 与之前的 torch.compile 分段 backend 产生同类可重放结构：被 eager 区域分隔的 CUDA Graph segment。关键区别在结构如何构建：TC piecewise 先让编译器理解整个 forward 再切分；BCG 在捕获发生时直接放置切分。"
   ],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "BCG 的优势：更快启动、更广兼容、可调试",
   "paras": [
    "**更快启动。** 对基于编译器的分段 graph，编译而非捕获主导设置：torch.compile 占 prefill graph 准备时间的 78-86%，并随模型复杂度增长，235B MoE 达 90 秒、GLM-5.2 达 158 秒。BCG 完全移除该阶段，单次捕获 pass 即达分段执行。",
    "**更广兼容。** SGLang 大量依赖自定义 CUDA、Triton 和 JIT 编译内核，它们不是原生 PyTorch 算子。为让这些内核对 torch.compile 可见，常常要用 torch.library 包装并提供 trace 用的 fake 实现——这在内核栈中引入了编译器特定的脚手架。编译器还约束 graph 边界能放哪：跨注册算子边界的输入输出必须能被编译器表示。BCG 在 eager break 处移除这个约束：graph 系统无需理解标记函数如何实现或 trace 其内部，让 graph 边界跟随服务逻辑而非编译器 trace 和类型要求。",
    "**可调试。** 捕获的 CUDA Graph 重放为不透明单元：普通 Python 不在其内执行，print、断言、逐步检查都难。BCG 自然留下 eager 区域，普通 Python 每次重放仍在那里运行。SGLang 用 --debug-cuda-graph 扩展此思路，本质上把整个 forward 包进 eager break——模型 eager 执行但仍走 CUDA Graph runner、静态缓冲、重放路径和元数据准备。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig02.png",
      "caption": "图 2：构建 prefill CUDA Graphs 的时间，42 个捕获形状，TP4 在 4×GB300——BCG 无编译阶段，显著快于编译器后端。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "BCG 在扩散中的应用",
   "paras": [
    "BCG 也被 SGLang 的扩散栈采用（PR #27436）。扩散在去噪过程中反复执行同一个 DiT forward，当这些 forward 含许多小、启动受限的内核时，CUDA Graph 尤其有用。",
    "三个做法：**捕获真实服务形状**（分辨率、视频帧数、prompt 条件长度、CFG 模式、所选 transformer 都影响捕获签名；预热实际服务的形状，对未见签名回退 eager）；**围绕动态操作 break**（动态 attention 和运行时依赖的元数据准备保持 eager，BCG 捕获它们周围稳定的计算，无需 torch.compile 理解整个 DiT forward）；**利用重复去噪结构**（BCG 捕获一次稳定区域、在整个去噪循环重放，动态区域保持 eager）。",
    "这在执行是启动受限时特别有效。例如预热后，Qwen-Image 在单 B200 上 512×512 端到端延迟从 6.48s 降到 2.45s，Z-Image 从 1.231s 降到 0.662s。更广的教训：BCG 移除启动开销，不减少模型 FLOPs 或让计算受限内核变便宜。它的优势在暴露的启动间隙占执行时间可观比例时最大。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig03.png",
      "caption": "图 3：预热后端到端延迟对比——Qwen-Image 6.48s→2.45s，Z-Image 1.231s→0.662s。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "Prefill 的全 CUDA Graph",
   "paras": [
    "Full CUDA Graph 对 decode 直截了当：每个请求贡献一个 token，主要变化维度是 batch size。prefill 更难，因为 batch 同时变化两个维度——总 token 数和这些 token 所属的请求数——而捕获的 graph 要求两者固定。加上依赖运行时元数据的 attention 后端，这让 prefill 的全 CUDA Graph 很难，也是我们当初采用 BCG 的主因之一。",
    "最近我们找到让 prefill 执行足够静态以支持全 CUDA Graph 的办法（PR #27988），包括重构请求槽和 attention 元数据的表示，使受支持的 attention 后端不必再留在 graph 外。"
   ],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "让 prefill 静态：token bucket 与 sentinel 请求槽",
   "paras": [
    "SGLang 用 token bucket 固定 token 维度。活 batch 填充到最近的捕获 token 数，就像 decode 把 batch size 填充到捕获 bucket 一样。请求维度单独处理：每个捕获 graph 预留固定数量的请求槽。活请求占用前几个槽；未用的重写为零长度 sentinel，零序列长度和扩展长度、偏移停在真实 token 之后。如果 batch 的请求数超过 graph 槽数，回退 eager 执行。",
    "sentinel 元数据必须在每次重放时重写，因为捕获的 graph 仍读整个请求表。attention 元数据同样在重放前为填充 batch 在 graph 外重建。所以今天全 prefill 捕获要求支持这种元数据准备风格的 attention 后端，包括 FlashAttention 和 FlashInfer。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig04.png",
      "caption": "图 4：重放时 token 填充到捕获 bucket，未用请求槽填零长度 sentinel。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "填充的成本：token padding 贵，槽 padding 便宜",
   "paras": [
    "两种填充成本差异很大。**填充的 token 是真实工作**：它们成为捕获 batch 里的实际行，作为相同 GEMM 的一部分通过稠密投影。SGLang 单独携带真实 token 数，让 MoE 路由、attention 和线性 attention 内核能跳过填充区域大部分，但稠密计算仍为这些额外行付钱。",
    "**空请求槽便宜得多。** 在 FlashAttention 的可变长度调度器中，工作从每个序列的实际长度派生，而不是给每个请求槽分配固定计算量。零长度请求因此几乎不贡献 attention 工作，主要加元数据和一点调度开销。这个不对称很重要：token 填充是昂贵的维度，请求槽填充相对便宜。",
    "全 prefill 捕获仍是实验特性，必须显式启用——引擎警告 full 是实验性的，生产工作负载指向 breakable 或 tc_piecewise——目前主要在 FlashAttention（fa4）和 FlashInfer 后端工作。"
   ],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "Prefill 基准：BCG 1.70×，全图 1.93×",
   "paras": [
    "三种 prefill 捕获方式加 eager 基线，剩下的问题是各自重放成本。在 gpt-oss-120b（TP4, 4×GB300）上单独测 prefill——固定输入长度、单个输出 token、一次一个请求、所有 arm 禁用 decode graph——四条路径都运行：全图捕获比 eager 快 1.93×，BCG 1.70×，TC piecewise 1.45×，所以 BCG 回放也比编译器后端快 17%，不仅在构建时间。",
    "差距来自各自每个 forward 做什么：BCG 直接重放记录的 segment，TC piecewise 每次回调编译的可调用对象，在自己的捕获片运行前付出 Torch Dynamo 的 guard 检查和 dispatch。在 GLM-5.2 上只有 BCG 能捕获——TC piecewise 无法 trace forward，全图捕获对它的稀疏 attention 无路——BCG 相对 eager 1.60×。每条曲线在 32× 的 prompt 长度范围内平坦，这是启动开销而非计算的特征。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig05.png",
      "caption": "图 5：gpt-oss-120b 上 prefill 延迟（四种后端都运行）——全图 1.93×、BCG 1.70×、TC piecewise 1.45×。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "CUDA Graph 内存占用：两种挑战",
   "paras": [
    "内存有两个独立挑战：防止分段捕获成倍增加常驻内存，以及捕获得足够远、让常驻 graph 内存真正取代最差的 eager 激活峰值。分段后端容易成倍增加 graph 内存：每个捕获形状含多个 graph segment，每个 segment 的中间值必须保持有效供重放。",
    "BCG 通过三种复用避免这种倍增。**跨 segment 共享内存池**：捕获形状的每个 segment 用同一个 CUDA Graph 池，中间存储可复用而非每 segment 单独钉住。**eager break 处弱引用**：当 graph 池已拥有 tensor 存储时，进入 break 的 tensor 被弱持有，避免延长 tensor 生命周期的多余 Python 引用。**跨捕获大小单一输出缓冲**：捕获大小共享单一最大输出缓冲，按各形状需要的行切片，而非每形状分配一个。",
    "一个值不能这样处理：跨 eager break 携带数据的 tensor。下个 graph segment 针对它的地址捕获，该缓冲必须保持存活并在每次重放原位更新。有了这些复用机制，即使大的捕获表也保持适度：GLM-5.2 上 78 层 MoE 的 42 个形状只加 2.4 GB graph 内存。"
   ],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "捕获到 chunked-prefill size",
   "paras": [
    "CUDA Graph 改变 prefill 内存使用的形态。Graph 内存是常驻的：捕获时分配、服务器整个生命周期保持。Eager 激活是瞬态的：每次 prefill 分配工作内存，最大受支持 prefill 决定峰值。",
    "捕获一个 prefill 形状把瞬态工作集很大部分移进 graph 的常驻内存池。但这只对实际重放 graph 的形状有帮助。如果捕获阶梯停在最大 prefill size 之下，最大 prefill 仍回退 eager 并保留原激活峰值——而服务器还为它下面所有常驻 graph 付钱。这让捕获上限比捕获形状数量更重要。由于 chunked_prefill_size 约束最大单个 prefill forward，捕获到该 size 移除最差的 eager 激活峰值。",
    "上限低于 chunk size 时略高于无 graph 基线：它们添加常驻 graph，激活峰值却原地不动。一旦上限到 chunk size，最大 prefill 终于重放 graph，峰值崩塌——gpt-oss-120b 上几乎归零（0.56 GB 到 0.001 GB），GLM-5.2 从 1.55 GB 到 0.35 GB（其稀疏 attention indexer 仍在 break 处 eager 运行）。",
    "捕获到 chunked-prefill size 买两样东西：**更低总内存**（激活峰值不再每请求付，总量落到无 graph 基线之下——gpt-oss-120b 低 0.51 GB，GLM-5.2 低 1.10 GB）和**可预测内存使用**（依赖工作负载的激活尖峰变成捕获时建立的固定分配，引擎可提前核算而非为瞬态峰值预留余量）。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig06.png",
      "caption": "图 6：prefill 内存（相对无 graph 常驻基线），在恰好 chunked-prefill size 的 prefill 后测量——上限达到 chunk size 时激活峰值崩塌。"
     }
    ]
   }
  }
 ],
 "conclusion": [
  "SGLang 的 CUDA Graph 之路揭示了一个关键洞察：graph 化的真正障碍不是启动开销本身，而是「一个不兼容操作毁掉整个捕获」的脆弱性。BCG 用 @eager_on_graph 把这个问题变成第一公民——不兼容区域就该 eager 跑，而不是被迫改造成编译器能理解的样子。这让 graph 边界能跟随服务逻辑，而不是编译器 trace。",
  "最有迁移价值的两点：runner/backend 拆分让捕获策略成为可插拔的（不同执行路径独立选策略）；捕获到 chunked-prefill size 的「上限思维」——常驻内存图能否取代激活峰值，取决于捕获到多高，而不是捕获多少个形状。这两点对任何想把 CUDA Graph 集成做扎实的推理引擎都直接适用。"
 ],
 "reference_url": "https://www.lmsys.org/blog/2026-08-17-advanced-cuda-graph"
}

with open("article_data.json", "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=1)
print(f"✅ 写入 article_data.json")