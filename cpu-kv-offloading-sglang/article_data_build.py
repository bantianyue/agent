# -*- coding: utf-8 -*-
"""CPU KV Offloading (HiCache) 深度评测编译 build"""
import json

DATA = {
 "title": "突破 GPU 内存极限：SGLang + Dynamo 的 CPU KV Offloading 深度实测（16×H100）",
 "lead": [
  "KV cache offloading 是现代推理基础设施里最有趣的技术之一：它让固定的 GPU 服务器集群能在不换硬件的情况下服务显著更多的并发用户。本文是一个生产级深度实测（作者为开源中的 LLM inference 方向工程师）。",
  "在 16 块 H100 的分离式（Disaggregated）4P4D 集群上，对比 Baseline KV-Aware Routing 与 Baseline + CPU KV Offloading（HiCache），模型为 Qwen3.6-35B-A3B-FP8，任务规模 3.10M token 故意超出物理 GPU VRAM 容量。",
  "本文为 GitHub README 格式，命令摘录作说明用途，含代码标识符。"
 ],
 "summary": [
  {
   "key": "场景与目标",
   "body": "16×H100 分离式 4P4D（4 Prefill+4 Decode）。核心问题：GPU VRAM 耗尽时，offload 到 CPU 内存能否保吞吐？从 RAM 取 64K 缓存 token 比在 Tensor Cores 重算快多少？能否激进 offload prefill 而不拖慢生成？KV-aware routing 能否保缓存命中？"
  },
  {
   "key": "架构与四组件",
   "body": "混合并行（TP=1+DP-Attention、EP=2 MoE）：attention 用 DP、稀疏 MoE 用 EP，避免 NVLink 同步瓶颈。① Dynamo Router（KV-aware、<1.5ms 选 worker）；② Prefill + HiCache（write_back、PCIe Gen5 ~45ms 重载、page_first_direct+direct 后端）；③ NIXL over RDMA 单边 GET、<15ms 交接、UCX zero-copy/ODP；④ Decode 全 VRAM 驻留零抖动。"
  },
  {
   "key": "结果（C=128）",
   "body": "峰值吞吐 +29.3%、1,843 tok/s、request 7.x/s；P99 TTFT 49.96s（快 21.6%、省 13.76s）；解码隔离 <10ms P99 ITL；缓存命中 baseline 77.0%→54.4% 崩、HiCache 防崩；零 GPU 成本翻倍前缀缓存容量到 3.10M token。"
  }
 ],
 "sections": [
  {
   "type": "h2",
   "title": "目标与评测方法",
   "paras": [
    "KV cache offloading 是当今推理基础设施最有意思的技术之一：它通过把不活跃的 KV cache 从昂贵的 VRAM 移到便宜的 CPU/系统内存，解锁在固定 GPU 服务器上服务显著更多并发用户的能力。",
    "这篇深度工程评测对比 **Baseline KV-Aware Routing** vs **Baseline + CPU KV Offloading**（利用 SGLang 的分层 HiCache 进行），部署在**分离式 4 Prefill + 4 Decode（4P4D）服务拓扑**、16 块 H100 的裸金属集群上（Qwen3.6-35B-A3B-FP8）。",
    "目标是评估 Hierarchical CPU KV Offloading（HiCache）如何为一个生产 4P4D 集群扩展到更高的并发。随并发增长评估四个性能支柱：",
    "**① 吞吐**：VRAM 耗尽时 offload 到 CPU 内存能否保吞吐，还是成为瓶颈？",
    "**② 取回速度**：从系统 RAM 取 64K 缓存 token 比在 Tensor Cores 上重算快多少？",
    "**③ prefill 隔离**：能否激进 offload prefill worker 而不拖慢活动用户的 token 生成？",
    "**④ 缓存命中**：KV-aware routing 在持续多用户压力下能否保护缓存命中率？"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig01.png",
      "caption": "图 1：4P4D 集群硬件与互联规格。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "硬件与系统设计",
   "paras": [
    "**硬件规格**：本文给出精确的裸金属集群硬件、互联（16×H100 规格 + 互联拓扑，见原文规格区）。",
    "**总体架构**：16-GPU 分离式集群，4 个 Prefill worker + 4 个 Decode worker。Prefill 负责 prompt tokenization、自注意力计算、线性循环状态更新；Decode 专职逐 token 自回归生成；两者经 NIXL 高效传输 KV cache。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig02.png",
      "caption": "图 2：16-GPU 分离式 4P4D 集群总体架构。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "混合并行策略（TP=1、DP+EP）",
   "paras": [
    "对 Qwen3.6-35B-A3B-FP8，标准张量并行（TP）跨 attention 层会引入不可忽略的 all-reduce 通信开销。为在 2-GPU worker pod 上最大化效率，配置了专用混合并行策略：**稠密（attention 与线性）路径用数据并行，稀疏 MoE 用专家并行**。",
    "在 SGLang 里跨 2-GPU pod 服务这个混合 MoE 模型，需要把混合架构的两种路径解耦。关键：pod 用 `--tp-size 2` 建跨两块物理卡的进程组；但为去掉瓶颈设 `--moe-dense-tp-size 1`，告诉 MoE 运行时稠密路径不要用 TP=2；配合 `--enable-dp-attention`、`--enable-dp-lm-head`、`--dp-size 2`，attention 和 LM-head 走数据并行——尤其在大 prefill 阶段价值大，避免把 NVLink 变成同步屏障。",
    "2-GPU pod 的并行 flag 配置片段（原文）：",
    "__CODE__bash::# Hybrid parallelism (2-GPU pod)\n--tp-size 2\n--moe-dense-tp-size 1      # dense path -> no TP all-reduce\n--enable-dp-attention 1\n--enable-dp-lm-head 1\n--dp-size 2\n--ep-size 2                # sparse MoE -> expert parallel\n--disaggregation-transfer-backend nixl",
    "稀疏 MoE 层用完全不同的策略：`--ep-size 2` 把 expert 权重分布到两张卡、NVLink all-to-all 交换 token。",
    "也就是说两块 GPU 同时扮演两个并行角色：attention/稠密路径——两块像独立的数据并行 worker（零 all-reduce）；稀疏 expert 层——两块像双向专家并行团队（NVLink all-to-all token 交换）。这让部署同时利用 pod 的聚合 160GB VRAM 容量和算力。",
    "最后是分离：`--disaggregation-transfer-backend nixl`，prefill/decode worker 分离；prefill 构造好生成所需请求状态后，NIXL 直接把完整 KV cache 流式转移到 decode 卡。整个执行路径无缝流动。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig03.png",
      "caption": "图 3：混合并行：DP-Attention + EP-MoE 并行策略。"
     }
    ],
    "1": [
     {
      "src": "fig04.png",
      "caption": "图 4：SGLang 分布式 flag 在 2-GPU pod 里如何协作。"
     }
    ],
    "2": [
     {
      "src": "fig05.png",
      "caption": "图 5：整体执行路径流。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "组件 1：Dynamo Router（数据面）",
   "paras": [
    "Dynamo Frontend 扮演智能入口网关和集群的中心路由大脑：终止连接、据此分发请求。相比盲目 round-robin，它做 **KV-aware routing**。Frontend 配置片段（原文）：",
    "__CODE__bash::# Dynamo Router · KV-aware routing\n--router-mode kv\n--router-host-cache-hit-weight 0.75\n# scores GPU-resident KV workers first,\n# then workers able to reload from host <50ms\n# candidate affinity evaluated in <1.5ms",
    "配置片段和原文一致（见原文组件 1 的 Frontend YAML snippet）。",
    "评分优先 GPU 驻留 KV 块的 worker、其次能快速（sub-50ms）从 host 重载的 worker。router 在 <1.5ms 内评估候选 worker 亲和度、派发给最高分 worker。",
    "**生产警告**：扩展 frontend 前要知道你的工作负载、按规模放大 frontend。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig06.png",
      "caption": "图 6：Dynamo Frontend 与 KV-aware 路由逻辑。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "组件 2：Prefill + HiCache（计算与缓存层）",
   "paras": [
    "Prefill Worker 处理初始 prompt tokenization、自注意力计算、线性循环状态更新。高并发下，单一 GPU VRAM 装不下多个 64K 前缀组的工作集，SGLang 的 HiCache 在 pinned host DDR5 缓冲被逐出的块。Prefill worker 配置片段（原文）：",
    "__CODE__bash::# Prefill worker · HiCache offloading\n--enable-hierarchical-cache\n--hicache-write-policy write_back\n--hicache-mem-layout page_first_direct\n--hicache-io-backend direct\n--disaggregation-mode prefill\n--disaggregation-transfer-backend nixl\n--disaggregation-bootstrap-port 30001\n--enable-cache-report  # ZeroMQ -> router\n# reload over PCIe Gen5 ~45ms (40 lanes)",
    "说明：`--enable-hierarchical-cache` 激活多级存储子系统；`--hicache-write-policy write_back` 优化 PCIe 效率——新生成的 KV 块活跃计算期间独占留在 GPU VRAM、被逐出时写回；`--hicache-mem-layout page_first_direct` 配 `--hicache-io-backend direct` 让引擎绕过中间 CPU staging、直接驱动 PCIe Gen5；`kv-events-config` 用 ZeroMQ 把实时块分配/逐出通知流给 router。",
    "**警告**：标准工作负载避免 `write_through` 策略——谨慎使用 `--hicache-` 相关 write-through 配置。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig07.png",
      "caption": "图 7：Prefill Worker + HiCache offload 配置与数据面。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "组件 3：NIXL over RDMA 状态传输",
   "paras": [
    "分离式 P/D 架构里，prefill 算 prompt 激活但不生成 token。端口与通信是部署里最关键的决策之一。",
    "**Decode Worker 如何「拉取」状态（分步）**：",
    "**① Bootstrap 协调**（Port 30001→30002）：prefill 完成 prompt tokenization 和 attention 后，经 bootstrap 端口通知 decode worker 就绪。",
    "**② 单边 RDMA GET**：decode worker 不让 prefill 经 CPU 内存推数据，而是自己主动用单边 RDMA GET 拉取。",
    "**③ 双状态注入**：自注意力 KV 块和 GDN 循环线性状态同时被拉取。",
    "**④ Sub-15ms 交接**：完整 64K 上下文状态在 <15ms 内直接落到 decode GPU 的 VRAM 开始生成。",
    "State Transfer 环境配置片段（原文）：",
    "__CODE__bash::# NIXL over RDMA · state transfer env\nUCX_TLS=rc_x,rc,cuda_copy,cuda_ipc\nUCX_RNDV_SCHEME=get_zcopy\nUCX_RNDV_THRESH=0\nUCX_IB_REG_METHODS=odp,rcache\nNIXL_TELEMETRY_ENABLE=1\nNIXL_TELEMETRY_PROMETHEUS_PORT=<port>",
    "说明：`UCX_TLS rc_x,rc,cuda_copy,cuda_ipc` 让 UCX 用 CUDA IPC 做节点内 GPU 传输、RDMA 做跨节点；`UCX_RNDV_SCHEME get_zcopy`+`UCX_RNDV_THRESH 0` 强制 zero-copy；`UCX_IB_REG_METHODS odp,rcache`（On-Demand Paging）消除内存注册开销；`NIXL_TELEMETRY_ENABLE` 暴露实时传输吞吐/延迟指标。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig08.png",
      "caption": "图 8：NIXL 端口架构与跨 worker 通信映射。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "组件 4：Decode Worker（自回归引擎）",
   "paras": [
    "Decode Worker 专职逐 token 自回归生成，直接从 prefill 拉取 live KV 注入生成循环。",
    "**为何 offload 只放 prefill**：解码 worker 不开分层缓存。把 host offloading 全集中到 prefill——前缀缓存命中在 prefill 最要紧，decode 保持 100% VRAM 驻留保证零抖动 token 生成。",
    "Decode worker 显式镜像 prefill 的混合并行拓扑（TP=1 DP-Attention + EP=2 MoE），保持相同内存参数（context-length 131072、page-size、mem-fraction-static）；绑到 port 30002 分离入站 decode 控制面。Decode 配置片段（原文）：",
    "__CODE__bash::# Decode worker (AR engine)\n# mirror prefill hybrid topology\n--disaggregation-mode decode\n--disaggregation-bootstrap-port 30002\n--context-length 131072\n# keep 100% VRAM-resident, zero-jitter generation"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig09.png",
      "caption": "图 9：Decode Worker 架构与端口绑定。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "基准与性能分析",
   "paras": [
    "**评测设定**：模型 Qwen/Qwen3.6-35B-A3B-FP8；输入 64,536 token（64K）固定模式；输出 256 token；共享前缀工作集=64 个不同前缀组、75% 目标前缀复用（48,402 共享 token/组）；并发扫描 8→128；每级 300 秒稳态 + 16 个 warmup。这是 prefill-heavy 实验（64K 输入 vs 256 输出，约 252:1）。3.10M token 有意超出物理 GPU VRAM 缓存容量。",
    "**① 吞吐与并发悬崖**：C=128 时 baseline VRAM-only 撞上严重内存墙、因缓存逐出崩溃；HiCache 下输出吞吐跳到 **1,843 tokens/s**、请求率 7.x/s。",
    "**② P99 TTFT**：极端饱和下 baseline 因 prefill worker 持续卡在重算而排队阻塞；HiCache 下 P99 TTFT 降到 **49.96 秒**，快 **21.6%**、省 **13.76 秒**。",
    "**③ 解码隔离（P99 TPOT/ITL）**：因为 offload 严格限定在 prefill worker、decode 100% VRAM 驻留，token 生成不被 host RAM 流量拖慢。",
    "**④ 端到端（P99 E2E）**：靠巨大 prefill 加速，整体工作流周转大幅改善，企业 agentic 工作流端到端完成更快、不牺牲逐 token 生成质量。",
    "**⑤ 缓存动态**：baseline 缓存命中率从 **77.0% 崩到 54.4%**、触发昂贵的 64K prefill 重算；HiCache 通过在 pinned host DDR5 缓冲被逐出块并重载、阻止这种崩溃。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig10.png",
      "caption": "图 10：峰值并发（C=128）下 Baseline vs HiCache 逐项对比。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "NIXL 与 HiCache 运行时遥测",
   "paras": [
    "**零拷贝 RDMA KV 传输（NIXL）**：warmup 后 NIXL 平均传输时间稳定在紧凑的 15ms–20ms（sub-20ms 传输延迟）；NIXL 累计传输字节数跨 worker 稳步超过 2.50 TiB——单边 UCX 内存注册完全防住网络传输瓶颈。",
    "**Host RAM 饱和与工作集吸收（HiCache）**：CPU HiCache Used Tokens 面板显示 token 数在负载期快速攀升；4 个 prefill worker 的 CPU HiCache 利用率表计显示 **99.7%–100%**——pinned DDR5 host RAM 层以最高效率运转、持有超额前缀工作集。"
   ],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "结论",
   "paras": [
    "这个参考部署证明：**分离式 4P4D 服务 + HiCache CPU KV Offloading 从根本上重塑 GPU 隔离能力**。分布式推理最大的瓶颈之一是在 worker 间管理海量 KV cache——当 prefill 需要长时间持有的 KV 块超出 VRAM 时。",
    "把 host DDR5 RAM 当作无缝的二级缓存水库，prefill worker 得到增长所需的净空；把这种分层内存层与 Dynamo 的前缀感知路由、NIXL 的零拷贝 RDMA 状态传输耦合，得到具体收益：",
    "**消除并发悬崖**：C=128 时峰值吞吐 +29.3%（防 VRAM 逐出崩塌）。",
    "**砍尾延迟**：负载下 P95 TTFT -44.1%、经 ~45ms PCIe 重载把 P99 响应省 13.76s。",
    "**保护解码速度**：100% VRAM 驻留 decode 保持坚如磐石的 token 间延迟（<10ms P99 ITL）。",
    "**零 GPU 成本扩容**：现成硬件上翻倍有效前缀缓存容量（3.10M+ token）。",
    "作者的话：承诺这系列带来生产级推理基准，做到了；从无法想象能拿到集群，到这里一步步跑通。特别感谢开源社区与算力赞助者的支持（作者使用开放预算）。下一篇写张量并行如何意外损害整体吞吐。"
   ],
   "fig_after": {}
  }
 ],
 "conclusion": [
  "这篇 16×H100 上的生产级深度实测，把「CPU KV offloading 到底能不能打」讲得极有数据支撑。核心是 **分离式 4P4D + HiCache**：prefill worker 把不活跃的 KV 块 offload 到 pinned host DDR5（`write_back` 策略 + `page_first_direct` + direct PCIe5 后端，~45ms 重载），decode worker 保持 100% VRAM 驻留零抖动。叠加 Dynamo 的 KV-aware 路由（`--router-mode kv`）和 NIXL 单边 RDMA 状态传输（<15ms 交接、zero-copy UCX）。",
  "结果非常实：并发 128 时 VRAM-only baseline 因 64K 前缀重算崩溃，HiCache 把吞吐拉到 1,843 tok/s（+29.3%）、P99 TTFT 降到 49.96s（快 21.6%）、缓存命中率守住 77%（baseline 崩到 54.4%）、解码 <10ms ITL，并在零 GPU 成本下把前缀缓存容量翻倍到 3.10M token。值得记的工程点：① **offload 只放 prefill、decode 全驻留**——保证生成零抖动；② 混合并行（DP-Attention + EP-MoE）避开 NVLink all-reduce 瓶颈；③ 单边 RDMA GET 而非 push，避免 CPU 内存中转。对做 LLM serving/推理引擎、且受限于固定 GPU 显存的人，这是「不花钱扩卡却翻倍会话容量」的实操级案例。"
 ],
 "reference_url": "https://x.com/jaga_prasanna/status/2093217133841064233"
}
with open("article_data.json", "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=1)
print("✅ 写入 article_data.json")
