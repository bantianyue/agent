# -*- coding: utf-8 -*-
# 由 _gen_build.py 生成：正文中文全译 + 格式 100% 保留
import json

DATA = {
  "title": "更多并行，反而更少吞吐：实测张量并行的性能代价",
  "summary": [
    {
      "key": "核心结论",
      "body": "固定 8 卡预算下，TP=1 副本扩展比 TP=2 输出吞吐高 31.0%"
    },
    {
      "key": "反超临界点",
      "body": "并发 32 以下 TP2 延迟更低，c≥64 后被 Prefill 队头阻塞反超"
    },
    {
      "key": "决策依据",
      "body": "权重装得进单卡就优先副本并行，张量并行只做低负载延迟优化"
    }
  ],
  "lead": [
    "张量并行（TP）常被当成分布式大模型推理的默认扩展手段：GPU 一多，工程师就本能地提高 TP 度。但在高并发的生产环境里，不看负载动态就加大张量并行，会严重损伤吞吐、引入昂贵的通信同步开销，并触发灾难性的 Prefill 队头阻塞。",
    "本文在同一个固定硬件预算（8 卡 NVIDIA H100 SXM5 集群）上，对比 SGLang 分离式部署的 TP1（4 Prefill + 4 Decode Pod）与 TP2（2 Prefill + 2 Decode Pod）：两者都服务 Qwen/Qwen3.6-35B-A3B-FP8，上下文窗口 131,072 token（约 132K），静态显存比例 0.85，状态传输走零拷贝的 NIXL UCX RoCE RDMA。用 AIPerf 跑完 c=1 到 c=128 的并发扫描后，**TP=1 反超 TP=2 的临界点被精确定位：输出吞吐高 31.0%，首 token 时延（P95 TTFT）快 8.2 倍**。"
  ],
  "sections": [
    {
      "type": "h2",
      "title": "目标",
      "paras": [
        "在 8 卡 NVIDIA H100 集群上服务 Qwen3.6-35B-A3B-FP8、并发持续攀升的场景下，评估卡内张量并行（TP2-2P2D）与卡间副本并行（TP1-4P4D）之间的性能取舍。",
        "这组实验回答四个架构问题：",
        "<span style=\"color:#0F4C81;font-size:7px;line-height:1;vertical-align:middle;\">●</span>&nbsp;增加独立 Prefill 工作进程，会如何影响重负载下的排队延迟与首 token 时延（TTFT）？",
        "<span style=\"color:#0F4C81;font-size:7px;line-height:1;vertical-align:middle;\">●</span>&nbsp;并发到达什么阈值之后，卡内张量并行带来的延迟收益会被 Prefill 队头阻塞反超？",
        "<span style=\"color:#0F4C81;font-size:7px;line-height:1;vertical-align:middle;\">●</span>&nbsp;在峰值饱和下，单流生成延迟与集群总吞吐该如何权衡？",
        "<span style=\"color:#0F4C81;font-size:7px;line-height:1;vertical-align:middle;\">●</span>&nbsp;当稠密模型与 MoE 模型的权重能装进单卡显存时，什么时候该选张量并行而不是副本扩展？"
      ]
    },
    {
      "type": "h2",
      "title": "硬件与运行时规格",
      "paras": [
        "在进入系统架构与基准结果之前，先看下表：它列出了两种拓扑共用的裸金属集群硬件、模型架构、互联配置与运行时参数。",
        "要高效服务 Qwen/Qwen3.6-35B-A3B-FP8，需要针对它的混合架构定制推理引擎。",
        "在总计 350 亿参数中，每个 token 只会经由稀疏 MoE 层动态路由约 30 亿参数，同时还配有 Gated DeltaNet 循环线性注意力状态（HybridLinearKVPool）。",
        "在原生 FP8 精度下，模型权重约占 35 GB 显存。每块 NVIDIA H100 提供 80 GB HBM3，因此单卡就能轻松装下完整的 35 GB 权重，还剩下 40 GB 以上未分配显存。",
        "把 <code style=\"background:#f3f4f5;padding:2px 5px;border-radius:3px;font-family:Consolas,Monaco,monospace;font-size:13px;color:#0F4C81;\">--mem-fraction-static 0.85</code> 打开后，SGLang 会在扣除模型权重与 CUDA 执行缓冲之后，把总显存的 85%（每卡约 68 GB）分配给静态 KV cache 与 Mamba 线性循环状态池；单卡可维持约 38 万到 45 万个活跃上下文 token 的显存容量。",
        "__CODE__bash::# 1. 配置部署所需的环境变量\nexport NAMESPACE=qwen32-bench\nexport EXP_DIR=/ephemeral/shared/qwen3.6-35b-a3b/sglang/disagg/tp1-4p4d\nexport DEPLOYMENT=q36-sgl-pd-tp1-4p4d\nexport GRAPH_LABEL=\"nvidia.com/dynamo-graph-deployment-name=${DEPLOYMENT}\"\n\n# 2. 部署 TP1-4P4D 服务图（8 卡上跑 4 个 Prefill + 4 个 Decode）\nkubectl apply -n \"$NAMESPACE\" -f \"$EXP_DIR/deploy.yaml\"\n\n# 3. 监控全部 8 个 worker Pod 的发布与就绪状态\nkubectl get pods -n \"$NAMESPACE\" -l \"$GRAPH_LABEL\" -o wide -w\n\n# 4. 切换拓扑时下线并释放集群资源\nkubectl delete dynamographdeployment.nvidia.com \"$DEPLOYMENT\" \\\n  -n \"$NAMESPACE\" --wait=true --ignore-not-found"
      ]
    },
    {
      "type": "h2",
      "title": "架构与并行设计",
      "paras": [
        "要理解两种配置在负载下为何表现迥异，得先看它们在 8 卡集群上的拓扑布局与执行机制："
      ]
    },
    {
      "type": "h3",
      "title": "卡内张量并行 vs 卡间副本并行",
      "paras": [
        "两种架构的根本差别，在于 GPU 计算资源如何在卡内同步与卡间复制之间组织：",
        "在 **TP2-2P2D** 中，每个工作 Pod 绑定两块通过高速 NVLink 相连的 H100。注意力投影矩阵、前馈层与 MoE 路由矩阵都被切分到两块设备上。",
        "于是每一层 Transformer 都要用 NVLink 上的 all-reduce 同步中间激活张量。分片虽然降低了单卡的计算量、让孤立单请求的前向更快，却在整张执行图上留下了持续的同步屏障。",
        "更关键的是，把 8 块 GPU 收拢成 2 卡一组的 Pod，会把集群的副本数压到只有 **2 个 prefill 工作进程**与 **2 个 decode 工作进程**。",
        "而在 **TP1-4P4D** 中，每个工作 Pod 完全跑在单块 H100 上，卡内通信开销为零。注意力计算、线性状态更新与 MoE 路由全部在本地寄存器和 HBM3 内完成；因为没有 all-reduce 屏障，GPU 计算引擎能以 100% 占空比运行。",
        "最重要的是，TP=1 让集群的并发能力直接翻倍：**4 个独立的 prefill 工作进程**与 **4 个独立的 decode 工作进程**。",
        "<span style=\"display:block;text-align:center;color:#c2d0de;letter-spacing:0.5em;\">· · ·</span>"
      ]
    },
    {
      "type": "h2",
      "title": "生产部署清单与部署流程",
      "paras": [
        "完整的部署清单以可直接运行的 Kubernetes recipe 形式组织：",
        "<span style=\"color:#0F4C81;font-size:7px;line-height:1;vertical-align:middle;\">●</span>&nbsp;**TP1-4P4D 部署清单：** deploy.yaml",
        "<span style=\"color:#0F4C81;font-size:7px;line-height:1;vertical-align:middle;\">●</span>&nbsp;**TP2-2P2D 部署清单：** deploy.yaml",
        "<span style=\"color:#0F4C81;font-size:7px;line-height:1;vertical-align:middle;\">●</span>&nbsp;**AIPerf 基准测试套件：** perf.yaml"
      ]
    },
    {
      "type": "h3",
      "title": "集群部署流程",
      "paras": [
        "两种拓扑的清单都在同一套仓库里，直接按 URL 取用即可：",
        "https://github.com/Prasannajaga/deployment-guide/blob/main/models/qwen3.6-35B-A3B/sglang/disagg/tp1-4p4d/deploy.yaml",
        "https://github.com/Prasannajaga/deployment-guide/blob/main/models/qwen3.6-35B-A3B/sglang/disagg/tp2-2p2d/deploy.yaml",
        "https://github.com/Prasannajaga/deployment-guide/blob/main/models/qwen3.6-35B-A3B/sglang/disagg/tp1-4p4d/perf.yaml",
        "<span style=\"display:block;text-align:center;color:#c2d0de;letter-spacing:0.5em;\">· · ·</span>"
      ]
    },
    {
      "type": "h2",
      "title": "基准测试与性能分析",
      "paras": [
        "为评估两种拓扑从单用户执行到集群极限饱和的扩展表现，我们用 AIPerf 跑了一套生产级混合序列分布的基准：",
        "<span style=\"color:#0F4C81;font-size:7px;line-height:1;vertical-align:middle;\">●</span>&nbsp;**模型与分词器：** Qwen/Qwen3.6-35B-A3B-FP8，使用官方分词器权重",
        "<span style=\"color:#0F4C81;font-size:7px;line-height:1;vertical-align:middle;\">●</span>&nbsp;**负载阶梯：** 5 档混合序列分布（1K 到 32K 上下文长度），模拟真实的 Agent 流量",
        "<span style=\"color:#0F4C81;font-size:7px;line-height:1;vertical-align:middle;\">●</span>&nbsp;**前缀复用与分区：** 8 个前缀组，目标前缀 token 复用率 75%",
        "<span style=\"color:#0F4C81;font-size:7px;line-height:1;vertical-align:middle;\">●</span>&nbsp;**并发阶梯：** 1、4、8、16、32、64、128",
        "<span style=\"color:#0F4C81;font-size:7px;line-height:1;vertical-align:middle;\">●</span>&nbsp;**执行控制：** 确定性随机种子（random_seed: 42）、16 个预热请求、3600 秒超时上限",
        "这套混合序列分布是刻意设计的，用来同时压满集群的计算强度与显存占用：",
        "把高频短请求（1K–4K）与长上下文重负载（8K–32K）混合，并叠加 8 个前缀组、75% 的前缀复用模式，基准就能复现生产 Agent 流量的真实形态：前缀缓存、prefill 计算排队与自回归生成同时发生。"
      ]
    },
    {
      "type": "h3",
      "title": "峰值饱和分析：并发 128 时的拆解",
      "paras": [
        "在峰值多用户饱和（c=128）下，TP1-4P4D 与 TP2-2P2D 的性能差距被彻底拉开。下面的性能看板与实测记分卡汇总了总吞吐、排队延迟与单 token 生成速度：",
        "要理解 TP1 为何在大规模下胜出，得看 GPU 执行 prefill 与 decode 的方式差异。",
        "<span style=\"color:#0F4C81;font-weight:bold;\">1</span>&nbsp;**Prefill 是计算密集型，Decode 受显存带宽限制**",
        "Prefill 把整个 prompt 并行吞进去，靠大规模矩阵乘法把 H100 的 Tensor Core 打满；当一个 prefill 工作进程在处理 prompt 时，它的计算引擎被完全占住，后续请求只能排队等待。",
        "相反，自回归 decode 每个流每步只生成一个 token。因为单 token 的算术量很小，decode 的执行被 HBM3 显存带宽限制住：GPU 每一步都要把 35 GB 的模型权重从显存里读一遍。",
        "<span style=\"color:#0F4C81;font-weight:bold;\">2</span>&nbsp;**低并发（c ≤ 32）下 TP2 为何更快**",
        "流量清淡时，GPU 算力大量闲置。TP2 把模型切到两块 GPU 上，每块 GPU 需要读取的权重数据减半（约 17.5 GB），单 token 生成延迟从 11.44 ms 降到 8.85 ms（提速 22.6%）。",
        "在低到达率下，TP2 的两个 prefill Pod 很少同时被占满，排队延迟几乎为零（P95 TTFT 为 16–21 ms）。",
        "<span style=\"color:#0F4C81;font-weight:bold;\">3</span>&nbsp;**高并发（c ≥ 64）下的反超与塌陷**",
        "并发继续爬升，prefill 的入口容量就成了硬瓶颈。在 TP2-2P2D 里，所有进入的请求都必须挤过仅有的两个 prefill Pod。",
        "长 prompt（最长 32K token）会长时间霸占 Tensor Core，造成严重的队头阻塞：短请求被排在它们后面。到 c=64 时，TP2 的 P95 TTFT 暴涨 40 倍到 842 ms；到 c=128 时更是膨胀到 12.52 秒。",
        "这种 prefill 排队还会引发 decode 饥饿悖论：prefill 工作进程来不及处理并交接 KV cache，decode 工作进程做完手上的任务后就只能空等 RDMA 状态传输，把 TP2 的吞吐压在 7,202 tok/s。TP1-4P4D 则提供 4 个独立 prefill Pod，把队列深度减半，将 P95 TTFT 保持在 1.53 秒（快 8.2 倍），并让 4 个 decode 工作进程持续吃饱，达到 9,436 tok/s（+31.0%）。",
        "此外，TP1 消除了 TP2 每 token 所需的 128 次 NVLink all-reduce 同步屏障，让每块 GPU 都能以最高的本地效率运行。",
        "<span style=\"display:block;text-align:center;color:#c2d0de;letter-spacing:0.5em;\">· · ·</span>"
      ],
      "table": {
        "head": [
          "指标（c=128）",
          "TP1-4P4D",
          "TP2-2P2D"
        ],
        "rows": [
          [
            "输出 token 吞吐",
            "<strong style=\"color:#1a7f5a;\">9,436 tok/s</strong>",
            "7,202 tok/s"
          ],
          [
            "请求吞吐",
            "<strong style=\"color:#1a7f5a;\">18.83 req/s</strong>",
            "14.26 req/s"
          ],
          [
            "P95 TTFT",
            "<strong style=\"color:#1a7f5a;\">1.53 s</strong>",
            "12.52 s"
          ],
          [
            "端到端时延（P95）",
            "<strong style=\"color:#1a7f5a;\">12.60 s</strong>",
            "16.20 s"
          ],
          [
            "单 token 生成延迟（低并发）",
            "11.44 ms",
            "<strong style=\"color:#c2610a;\">8.85 ms</strong>"
          ]
        ]
      }
    },
    {
      "type": "h2",
      "title": "关键结论与决策指南",
      "paras": [
        "这次实验说明：更高的张量并行并不天然带来更高的集群吞吐。设计生产级 LLM 服务集群时，可以套用下面这套决策框架：",
        "这样的显存占用，从根本上把张量并行与物理硬件必要性解耦了。",
        "在分布式 LLM 服务中，我们之所以经常默认使用张量并行，是因为庞大的模型权重（比如 FP16 下的 70B 模型）超出了单卡显存上限，多卡分片成为无法回避的容量约束。",
        "但当权重能从容装进单块加速器时，张量并行就不再是容量要求，而变成了一个明确的架构取舍：单 token 计算延迟与集群级副本吞吐之间的取舍。选择 TP=2 会把线性投影切分到两块 NVLink 相连的 GPU 上，让单设备算术量减半，从而加快孤立请求的单层前向。",
        "但这种计算加速的基础设施代价很高：它在每一层 Transformer 都引入同步的 all-reduce 通信屏障；在固定 8 卡预算下，还会把集群副本总数从 4 个 Prefill + 4 个 Decode Pod 直接砍半到各 2 个。",
        "反过来，TP=1 完全消除了卡间通信开销，让计算引擎跑满本地硬件效率，并把整个集群的 prefill 派发能力翻倍。",
        "结论是：当显存不构成约束时，张量并行只适合作为订阅不足场景下的延迟优化器；而副本并行（TP=1）才能在生产负载下最大化并发韧性与集群总吞吐。"
      ]
    },
    {
      "type": "h2",
      "title": "结论",
      "paras": [
        "这套基准证明：在 8 卡 NVIDIA H100 集群上服务 Qwen3.6-35B-A3B-FP8 并面对多用户并发流量时，分离式 TP1（4P4D）是更优的生产服务架构。",
        "通过消除 NVLink all-reduce 同步屏障、并提供 4 个独立的 prefill 与 decode 工作进程，TP1 带来：",
        "<span style=\"color:#0F4C81;font-size:7px;line-height:1;vertical-align:middle;\">●</span>&nbsp;**+31.0% 输出 token 吞吐：**（c=128 时 9,436 tok/s vs 7,202 tok/s）",
        "<span style=\"color:#0F4C81;font-size:7px;line-height:1;vertical-align:middle;\">●</span>&nbsp;**+32.0% 请求吞吐：**（18.83 req/s vs 14.26 req/s）",
        "<span style=\"color:#0F4C81;font-size:7px;line-height:1;vertical-align:middle;\">●</span>&nbsp;**8.2 倍更快的首 token 时延：**（P95 TTFT 1.53 s vs 12.52 s）",
        "<span style=\"color:#0F4C81;font-size:7px;line-height:1;vertical-align:middle;\">●</span>&nbsp;**22.2% 更快的端到端时延：**（12.60 s vs 16.20 s）",
        "设想一个模型，权重只占 80 GB NVIDIA H100 中的约 30–35 GB：每块 GPU 上其实已经有约 45–50 GB 空闲显存可以用来做 KV cache。仅因为手上有几块 GPU 就把模型按 TP=2 切开，是一笔糟糕的买卖：副本 Pod 总数减半，还要额外付出成百上千次 NVLink all-reduce 同步停顿。",
        "让每个 worker 保持 TP=1，你就能得到双倍的 worker Pod、零通信开销，以及服务高并发生产负载所需的最高吞吐。",
        "<span style=\"display:block;background:#f5f8fb;border-left:3px solid #0F4C81;padding:10px 14px;border-radius:4px;\">这种架构效率在与分层内存体系结合时会进一步放大。正如我们在上一个关于分层 CPU KV 卸载（HiCache）的实验中展示的：把被驱逐的前缀状态卸载到主机 DDR5 内存，可以在不增加加速器硬件的前提下解锁巨大的有效上下文容量，并驱动更高的持续吞吐。把 TP=1 副本并行与主机内存卸载结合起来，就能最大化每瓦 token 效率：单卡 worker 消除了设备间同步停顿，让 Tensor Core 保持最高占空比饱和运行；CPU 卸载则避免了重复的 prefill 重算，从整个集群里榨出每瓦服务吞吐的极限。</span>",
        "https://x.com/jaga_prasanna/status/2093217133841064233?s=20",
        "在下一篇里，我们会深入剖析用于 KV cache 的 NVIDIA NIXL 在 RoCE v2 RDMA 上的表现，演示如何在 Dynamo worker 上埋设 Prometheus 遥测，并构建生产级 Grafana 看板，用于追踪大规模下的实时传输延迟、带宽与 CPU 主机内存缓存。",
        "感谢读到这里 🙏"
      ]
    }
  ],
  "conclusion": [
    "在 8 卡 H100 上服务 Qwen3.6-35B-A3B-FP8，把 8 卡切成 2 卡一组做 TP2 反而更慢：并发 128 时 TP1-4P4D 输出吞吐 9,436 tok/s，比 TP2 高 31.0%；P95 TTFT 1.53 s 对 12.52 s，快 8.2 倍。",
    "权重装得进单卡时，张量并行只是低负载下的延迟优化器；要扛高并发，就应该把预算花在更多独立 worker（TP=1）上。"
  ],
  "reference_url": "https://x.com/jaga_prasanna/status/2094419634489549223",
  "caption_translations": {
    "fig00": "图1：从并发 1 到并发 128 的扩展扫描，跟踪 TP1-4P4D 与 TP2-2P2D 的输出 token 吞吐、请求吞吐、P50/P95 TTFT、P50 ITL 与 P95 端到端时延轨迹。",
    "fig02": "图3：权重能装进单卡显存时，高并发负载采用 TP=1 副本扩展；低并发延迟敏感场景则用 TP=2 最小化时延。",
    "fig03": "图4：并发 128 时的实测性能记分卡，对比 SGLang 分离式 TP1-4P4D（石板灰）与 TP2-2P2D（亮橙）在吞吐、TTFT 尾延迟、解码速度与端到端周转时间上的表现。",
    "fig07": "图8：在固定 8 卡 NVIDIA H100 预算下，SGLang 分离式 TP1-4P4D（8 张单卡上跑 4 个 Prefill + 4 个 Decode Pod）与 TP2-2P2D（4 个双卡 NVLink Pod 上跑 2 + 2）的架构对比。",
    "fig08": "图9：执行流水线对比。TP=1 无同步、全部在本地 GPU 执行（Tensor Core 100% 占空比）；TP=2 卡内分片执行，在 64 层里每 token 引入 128 次同步 NVLink all-reduce 屏障。"
  }
}
