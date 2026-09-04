# -*- coding: utf-8 -*-
"""Demystifying NVSHMEM 编译 build"""
import json, os, sys

DATA = {
 "title": "解密 NVSHMEM：GPU 通信里的对称内存与设备发起操作到底怎么工作的",
 "lead": [
  "NVSHMEM 是 NVIDIA 基于 OpenSHMEM 的 PGAS 通信库，面向 GPU 集群，通过对称内存在 GPU 代码里直接发起 one-sided 通信。尽管采用越来越广，但它的系统级设计一直散落在文档、源码和应用经验里。",
  "这篇论文（新加坡-ETH 中心 FastTrackAI 项目）给出 NVSHMEM 的简明系统级研究：编程模型、实现、性能特征，聚焦对称内存、one-sided 操作、设备端 collectives，并用 DeepEP 作为 NVSHMEM 在性能关键的稀疏深度学习负载中的案例。",
  "核心结论：NVSHMEM 开创了设备端对称内存编程模型，实现细粒度 GPU 驱动通信，对逼近硬件性能极限很重要。"
 ],
 "summary": [
  {
   "key": "定位",
   "body": "NVSHMEM 是 OpenSHMEM 风格的 PGAS 库：把对称内存直接暴露给 GPU kernel，用 put/get、原子操作、显式同步做 one-sided 通信，绕开 host 控制路径。"
  },
  {
   "key": "快慢双路径",
   "body": "P2P 可达时走快路径（GPU 直接映射 peer 堆，SM 直接 load/store）；不可达时走慢路径（IBGDA 或 host 代理线程）。对称偏移规则让两条路径共用同一寻址方案。"
  },
  {
   "key": "实战价值",
   "body": "DeepEP 用 NVSHMEM 做 MoE 跨节点 RDMA 基板，但只在关键点用它（元数据交换、分块 put、原子信用更新），上层自建多级流水线——体现「基板」而非「全家桶」用法。"
  }
 ],
 "sections": [
  {
   "type": "h2",
   "title": "背景：GPU 通信为何需要设备发起",
   "paras": [
    "分布式深度学习依赖数据/张量/流水线并行跨多 GPU 甚至多节点扩展训练与推理，HPC 应用靠分布式分解扩展模拟。两者性能都取决于数据如何通过 PCIe、NVLink、InfiniBand 高效交换。NCCL 是最广泛使用的方案，为多数 CUDA 框架（PyTorch、Megatron-LM、vLLM）提供优化的 collective。",
    "但 NCCL 最初是 host 驱动的：CPU 入队 collective，库选算法和调度。对 bulk-synchronous collectives 有效，却不适合细粒度 point-to-point 通信——比如通信依赖数据、限定在部分线程、或 CPU 协调导致不可接受延迟的模式。例子：stencil 边界交换、不规则图通信、稀疏与 expert-parallel 负载、紧密耦合计算与数据搬运的自定义内核。",
    "NVSHMEM 用互补的编程模型填补这个缺口：把 PGAS 直接暴露给 GPU 代码，让 CUDA kernel 通过 one-sided put/get、原子操作和显式同步访问远端 PE 的对称内存。它不是替代 NCCL，而是支持 host 发起的 collective 难以表达的通信模式——不规则交换和细粒度重叠。",
    "NVSHMEM 成功后，NCCL 通过新的 device API 吸收相关思想，加入设备发起操作和对称内存支持。但两者抽象不同：NVSHMEM 提供扁平远程内存视图，NCCL 明确区分 scale-up 和 scale-out 域。论文基于 NVSHMEM 3.3.9 源码级分析。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig01.png",
      "caption": "图 1：NVSHMEM 内存管理——对称堆、句柄交换与远程地址计算（对称偏移规则）。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "核心概念：对称内存与 one-sided 操作",
   "paras": [
    "NVSHMEM 的 PE 是一个映射到一张 GPU 的 OS 进程（2.4.1 起支持每 GPU 多 PE）。通信建立在对称内存上：每个 PE 有一个对称堆，对称对象在所有 PE 上以相同类型、大小、布局分配。这个结构让远端 PE 能通过 put/get 等 one-sided 操作访问对象，发起方指定源、目标、位置，不需要目标 PE 的显式 receive。",
    "这实现异步推进，很多情况下直接放置到目标的对称内存缓冲。OpenSHMEM/NVSHMEM 通过把数据类型、传输大小、操作类型编码进 API 名，提供更轻量的调用路径；MPI RMA 则把这些作为参数传入更通用的接口。SHMEM 风格接口减少 dispatch 和参数处理开销，对细粒度通信有用。",
    "与 P2P 内存访问、GPUDirect RDMA（GDRDMA）、GPUDirect Async Kernel-Initiated（GDA-KI）等概念相关：P2P 让一张 GPU 直接访问另一张的内存；GDRDMA 扩展到 scale-out 域；GDA-KI 让 GPU kernel 无需 CPU 干预发起网络操作，InfiniBand GPUDirect Async（IBGDA）是其在 InfiniBand 的实现。"
   ],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "内存管理：VA 映射与对称偏移寻址",
   "paras": [
    "NVSHMEM 保留一个足够覆盖所有 P2P 可达 GPU 对称堆的 VA 范围，把每个 peer 堆放在该范围的固定偏移处。这个组织是设计核心：它让远程地址能从堆相对偏移直接推导。",
    "具体地：导出本地 CUDA 内存句柄、跨 PE 交换、把 peer 内存映射进对应的保留虚拟地址段。对非 P2P 传输，同一区域额外用相应网络接口注册。远程地址计算在快慢两条路径都遵循同一对称偏移规则，唯一区别是用哪个每-PE 基地址、结果能否直接解引用。",
    "快路径（P2P）中，远程地址 = peer 堆映射基址 + (本地指针 - 本地堆基址)。即保留对象在本地堆的偏移，应用到远程堆基址。非 P2P 路径用远程基址，把算出的地址连同内存句柄、注册元数据或 NIC key 传给传输层。只有 P2P 情形给 GPU 一个可直接映射的 peer 虚拟地址，设备端快路径用它做 SM 发出的 load/store。堆增长时 NVSHMEM 刷新设备驻留元数据，让 GPU kernel 观察更新后的布局。"
   ],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "one-sided 通信：快路径（直接 GPU 内存访问）",
   "paras": [
    "NVSHMEM 根据目标 peer 是否 P2P 可达选择快或慢路径。快路径由 host 侧 P2P 传输逻辑判定：验证两个 PE 在同一 host、识别 peer 为本地可见 CUDA 设备、用 cudaDeviceCanAccessPeer 判断是否支持直接 peer 访问；若支持，再查能否启用原生 GPU 原子。",
    "peer 堆直接映射后，设备端 RMA 简化为对公式算出的远程地址做普通内存访问。标量操作如 nvshmemi_p/g 先检查目标 PE 是否有映射堆基址，然后对结果远程指针发直接 store/load；批量接口如 nvshmemi_put_threadgroup 对该映射地址做整个 threadgroup 的 memcpy。",
    "Host 端 RMA 用同一映射地址空间，但执行模型不同：host 编排 CUDA 拷贝操作。公共 API 如 nvshmem_put 和 nvshmemx_put_on_stream 委托给 nvshmemi_prepare_and_post_rma，peer 堆本地可访问时选映射 P2P 路径，用 cudaMemcpyAsync 在本地与远程设备指针间拷贝。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig02.png",
      "caption": "图 2：快路径——P2P 可达时 GPU 直接映射 peer 堆，SM 直接 load/store 远程地址。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "one-sided 通信：慢路径（IBGDA 与代理执行）",
   "paras": [
    "目标 PE 的对称堆没有直接 P2P 映射进本地 GPU 地址空间时走慢路径——跨节点通信，以及非 CUDA P2P 可达的节点内 peer。此时仍保留同样的基于偏移的寻址，但算出的远程地址不能再被本地 GPU 直接解引用，操作通过网络传输完成。",
    "依赖系统支持，NVSHMEM 要么用 IBGDA（InfiniBand GPUDirect Async），要么走 host 代理路径——一个 CPU 线程代表 GPU 执行请求。慢路径 RMA 依赖可插拔的远程传输层：IBRC、IBDEVX 等 InfiniBand 传输，以及 UCX、libfabric 等高层后端。InfiniBand 传输通过 Reliable Connection（RC）QP 维护 PE 间连接，IBGDA 额外支持 Dynamic Connection（DC）QP。",
    "设备端每个操作先查 IBGDA 是否可用：可用则卸载给 nvshmemi_ibgda_rma_*，直接从 GPU 代码构造并投递 RDMA 工作到 NIC；否则把操作编码成 work request 写进 host-pinned 内存的代理缓冲，一个专用 host 代理线程消费该描述符并执行对应操作。所以慢路径在 API 层仍是 GPU 发起的，但完成最终由 NIC（IBGDA）或 host 代理（描述符队列）驱动。",
    "Host 端慢路径有限制：远程 strided RMA 和 host 端 g 操作不支持，put_signal 只能通过 on-stream 代理路径。反映当前远程传输与代理机制主要为连续传输和设备端信号优化。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig03.png",
      "caption": "图 3：慢路径——IBGDA 或 host 代理线程：GPU 编码 work request，由 NIC 或 CPU 代理完成。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "Collectives：pSync、LL/LL128 与算法选择",
   "paras": [
    "NVSHMEM 的每个 team 拥有一个 pSync 缓冲（持久同步缓冲），是对称内存区域，用于跨 PE 协调 collective 及部分 point-to-point 操作。pSync 区域跨 team 以 strided 方式布局，避免不同 team 的同步状态落在同一 cache line；每个 team 的 pSync 内，不同 collective 用硬编码偏移分配固定子区域，部分操作双缓冲使连续调用交替使用缓冲、免去额外 barrier。",
    "为降低数据搬运后显式同步的成本（小消息的主要瓶颈），NVSHMEM 实现 LL 和 LL128 协议（与 NCCL 类似）：把数据搬运和轻量到达通知耦合。LL 协议中每个数据单元配同步标志：发送方把两个数据元素和两个标志打包进单个 16 字节原子写，接收方轮询标志判断数据就绪。LL128 用更大传输单元，120 字节数据 + 8 字节标志 = 128 字节，改善带宽利用；但 LL128 只在 NVLink 上安全，因为它依赖 128 字节原子 store，PCIe 等互连不保证。",
    "NVSHMEM 在运行时选 collective 算法：不是用显式分析模型，而是为每个 collective 实现基于规则的决策树。能力检查、数据类型与作用域约束、scratch 空间可用性、固定消息大小阈值决定哪个算法被允许和优先，不支持的情况回退到更通用的实现。",
    "设备端 collective API 是 threadgroup collectives：提供 thread/warp/block 作用域入口，但单次 collective 调用由一个参与 threadgroup 执行，而非多个 CTA。没有公开的 _grid 变体是刻意设计：grid 作用域操作需要 kernel 内跨 CTA 同步，比结束它并启动 stream 排序的通信 kernel 更贵。内置多 CTA 执行仅通过 host 端 _on_stream 包装提供，且只对 FCollect、AllReduce、ReduceScatter，由 NVLS 资源可用性门控。"
   ],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "微基准：one-sided RMA 的带宽与延迟",
   "paras": [
    "测量在 CoreWeave H200 集群：每节点 8 张 H200 SXM5（144GB HBM3e、NVLink-4、900GB/s 双向），节点间 ConnectX-7 IB。NVSHMEM 3.3.9 + CUDA 13.0.88。",
    "节点内 bulk put 达 313 GB/s，get 峰 141 GB/s。标量 p 达 172 GB/s（大量 GPU 线程发独立远程 store 可缓冲重叠）；标量 g 低于 9 GB/s——每次远程 load 线程需要返回值才能完成操作，限制未完成操作数、阻碍深流水线。这些结果低于 450 GB/s NVLink 参考，因 NVSHMEM 地址翻译、同步、工作划分和协议开销。",
    "跨节点（tuned IBGDA）：bulk put/get 各 48.0/48.2 GB/s 逼近单轨 IB 参考；标量 p 提升到 15.6 GB/s，标量 g 仍低至 1.28 GB/s。延迟：节点内 bulk put/get 约 1.8-2.5μs、标量 p/g 1.3-2.2μs；跨节点 put/get 约 9.4-9.5μs（256B）到 9.7μs（64KiB）。结论：NVSHMEM 对 bulk 或聚合写风格 RMA 最有效，标量操作应作为延迟/控制原语，带宽敏感时批量处理。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig05.png",
      "caption": "图 4：设备发起 one-sided RMA 带宽——节点内 bulk put 313 GB/s、get 141 GB/s，标量 g 依赖返回值仅 9 GB/s。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "微基准：AllReduce——多 CTA 是性能关键",
   "paras": [
    "AllReduce 是 NVSHMEM 与 NCCL 都高度优化的操作。节点内，host 端 on-stream 路径达 264 GB/s 算法带宽，超过强制 NCCL ring 基线、接近 NCCL NVLS 路径的 276 GB/s；而设备端 block 作用域路径仅 30 GB/s——因为它用单 CTA。小消息上设备路径仍延迟有竞争力：到 64KiB 约 3.8-7.1μs，对比 NCCL ring 4.7-8.9μs、NCCL NVLS 5.6-5.9μs。",
    "跨节点两者都低于 0.20 GB/s，而 NCCL ring 达 180 GB/s、NVLS Tree 达 252 GB/s。这符合预期——NVSHMEM 的优化 collective 主要聚焦节点内或 MNNVL 域的 NVLS 算法。跨节点 NVSHMEM 没有小消息优势，64KiB 时延迟涨到毫秒级，而 NCCL 保持数十微秒。多 CTA 执行对 NVSHMEM collective 性能至关重要。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig06.png",
      "caption": "图 5：AllReduce 带宽对比——节点内 on-stream 264 GB/s 接近 NCCL NVLS，设备单 CTA 仅 30 GB/s；跨节点 NVSHMEM 低于 0.20 GB/s vs NCCL 252 GB/s。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "DeepEP 案例：NVSHMEM 作为跨节点基板",
   "paras": [
    "DeepEP 是 DeepSeek 为 MoE 负载（expert parallelism）发布的开源库。EP 中每层专家跨 GPU 分片，每层 token 必须派发给 router 选中的专家，计算后输出合并回原 token 的 GPU。两阶段都是稀疏 all-to-all 交换，通信量数据依赖，难以用现成 collective 高效实现。DeepEP 用自定义 dispatch/combine kernel，以 NVSHMEM 作为跨节点 RDMA 基板。",
    "**高吞吐（HT）路径**面向训练：两阶段流水线——token 先只在同 local index 的 GPU 间跨节点 RDMA，再在目标节点内通过 NVLink 重分发到承载选中专家的 GPU。HT 用八个并行 NVSHMEM world team（每节点 GPU 槽位一个），每个 world 每节点一个 PE，所以跨节点 RDMA 只在同 local index 的 GPU 间发生——但假设每节点恰好 8 张 P2P 可达 GPU，可移植性差。",
    "dispatch kernel 组织成逻辑 channel，每个覆盖一对 SM 并处理一段连续输入 token。SM 内用 warp specialization：RDMA 侧 7 个 warp 作发送方、1 个作协调者、8 个作 NVLink 接收方（每本地 GPU 槽位一个）；配对 SM 上 8 个 warp 作 RDMA 到 NVLink 转发、其余作协调。发送 warp 把 token 放进对称 NVSHMEM 堆上的 per-peer RDMA ring buffer，协调 warp 周期性地把写入批量成更大 RDMA 传输，用原子更新远端 tail。",
    "关键点：DeepEP 不把大部分工作表达为 NVSHMEM collectives 或通用 RMA 调用，只在跨节点 RDMA 路径的关键点用它：notify_dispatch 的元数据交换、协调者的分块 RDMA put、远端头尾计数器的原子信用更新。NVSHMEM 作为跨节点通信基板，DeepEP 在它之上构建自己的多级传输流水线。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig04.png",
      "caption": "图 6：DeepEP 高吞吐 dispatch——两阶段：同 local index 跨节点 RDMA + 节点内 NVLink 重分发，NVSHMEM 做 RDMA 基板。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "DeepEP 低延迟路径与对比",
   "paras": [
    "**低延迟（LL）路径**面向推理：batch 小、端到端层延迟比峰值带宽更重要。它移除 HT 的节点内 NVLink 转发阶段，跨节点交付直接靠 RDMA。不用八个独立 world team，LL 用单一全局 NVSHMEM world team，并为跨节点的同槽位 GPU 叠加一个 strided team。kernel 结构更简单：无逻辑 channel 和 warp specialization，单 kernel grid 处理整个 dispatch，SM 按 local experts 而非 token 范围划分；每个 block 内 warp 分成固定大小组，每组负责一个 expert。",
    "发送阶段每个 warp 遍历 token 处理一个 top-k 目标；FP8 转换后 lane 0 为目标 expert 预留槽位并计算远端接收缓冲地址；目标在另一节点则用 nvshmemi_ibgda_put_nbi_warp 发打包消息，同节点 P2P 可达则直接拷贝进映射接收缓冲。接收阶段 warp 组等计数非零、读 token 数、为输出缓冲预留空间、拷贝消息并解包。关键路径 NVSHMEM 活动最少：LL 路径用一次 IBGDA put 搬负载 + 一次原子更新通知最终计数。",
    "NVIDIA 已发布 NCCL GIN 与 NVSHMEM 在 DeepEP 上的直接对比：NCCL GIN 与 NVSHMEM 匹配很接近（通常 1-2% 内），同时提供 NCCL 运行时内的同类设备发起通信。这印证 NVSHMEM 仍作为低层 one-sided RMA 基板提供有意义的价值，对需要细粒度 one-sided 通信和直接设备端控制的应用依然相关。"
   ],
   "fig_after": {}
  }
 ],
 "conclusion": [
  "NVSHMEM 在 GPU 通信设计空间里占据独特位置：通过 PGAS 模型实现 GPU 发起的 one-sided 通信。源码级分析揭示它如何用对称内存、多传输路径、连接设备端操作与底层网络机制的分层运行时实现这一模型。主要局限来自执行模型和 collective 实现——常常没有充分利用 GPU 并行。",
  "DeepEP 案例最有启发：NVSHMEM 的「基板」用法——只在跨节点 RDMA 的关键点用（元数据交换、分块 put、原子信用更新），上层自建多级流水线。这与「用库跑一切 collective」的思路相反，也是 NVSHMEM 在高性能稀疏负载里真正的价值所在。"
 ],
 "reference_url": "https://arxiv.org/abs/2606.05951"
}

with open("article_data.json", "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=1)
print(f"✅ 写入 article_data.json")