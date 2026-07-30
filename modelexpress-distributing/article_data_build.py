#!/usr/bin/env python3
"""
article_data_build.py — ModelExpress: Distributing Model Artifacts at the Speed of Light
重写版，按新 SOP：非论文类 ≥80%，保留原文逻辑层次与枚举结构。
"""
import json, os, sys

_article_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()

DATA = {
    "title": "ModelExpress：NVIDIA 用光速分发模型权重——DeepSeek-V4 Pro 冷启动从 8 分钟缩到 1 分 44 秒",

    "summary": [
        {"key": "核心思路", "body": "加载模型前先问「哪里已有兼容副本」，优先 GPU 到 GPU 的 P2P RDMA 直传，避免重复从对象存储拉取"},
        {"key": "冷启动加速", "body": "DeepSeek-V4 Pro（806 GiB）冷启动从 8 分钟降到 1 分 44 秒，含 JIT 内核缓存继承"},
        {"key": "RL 场景", "body": "支持 receiver-driven 的 RL 权重分发，通过 Publish→Discover→Plan→Pull 四阶段完成 refit"},
    ],

    "lead": [
        "每个字节的移动都有成本。当模型 checkpoint 膨胀到数百 GB 甚至 TB 级别，这个成本急剧放大。冷启动要从远程存储拉权重到 GPU，自动扩缩容要填充每个新副本，RL 后训练要持续把更新后的权重从训练器分发到 rollout worker——**看似不同的工作流，背后是同一个问题：花在搬权重上的时间。**",
        "NVIDIA ModelExpress（MX）的核心思路很简单：**加载模型前，先问哪里已有兼容副本。** 不是把每个副本都当作独立冷启动，而是选择最快的可用来源和传输路径。当 serving peer 已持有兼容权重时，MX 通过 NIXL 的 P2P RDMA 直接从 GPU 到 GPU 传输，绕过对象存储、本地磁盘和主机内存。当没有 peer 可用时，MX 从最快的可用存储路径引导。",
    ],

    "sections": [
        {
            "type": "h2",
            "title": "从存储启动：首个 Worker 的引导",
            "paras": [
                "第一个 worker 没有 peer 可用，必须从外部存储引导。MX 提供三条路径，按优先级自动选择：",
            ],
        },
        {
            "type": "h3",
            "title": "远程对象存储 → GPU",
            "paras": [
                "当 checkpoint 在云存储桶中时，MX 使用 Model Streamer 多线程张量读取器并发拉取 safetensors，经过可复用的 CPU staging buffer 直接进入 GPU。**checkpoint 从不落地磁盘**，消除了中间下载、重新加载和存储卷的开销。在 tensor-parallel 部署中，参与 rank 分担远程读取并通过 NCCL 共享结果，而不是每个 rank 独立下载完整 checkpoint。",
            ],
        },
        {
            "type": "h3",
            "title": "集群入口去重：下载一次，不是 N 次",
            "paras": [
                "当集群维护共享磁盘缓存时（如 K8s 持久卷），MX 的 Model Cache Service 将多个副本的并发下载**折叠为一次协调下载**：原子声明在 Metadata Store 中选择一个下载者，其余副本跟踪其进度并复用缓存副本。如果 10 个副本同时拉取 806 GiB 的 DeepSeek-V4 Pro 模型，原本需要约 8 TiB 的入口带宽，现在集群只付一次外部下载成本。",
            ],
        },
        {
            "type": "h3",
            "title": "本地存储 → GPU",
            "paras": [
                "支持 GPUDirect Storage（GDS）时，MX 通过 NIXL 的多线程 GDS 后端直接将 checkpoint 从本地存储读入 GPU 内存，**绕过主机内存和 staging 副本**。不支持 GDS 时自动检测并回退到 ModelStreamer 的管道化读取——多 OS 线程并发读取 safetensors 到可配置的 CPU 缓冲区，已完成张量移至 GPU 的同时后续读取继续并行，重叠磁盘 I/O 与 GPU 放置。",
            ],
        },
        {
            "type": "h2",
            "title": "Peer 到 Peer：GPU 直连分发",
            "paras": [
                "一旦第一个 worker 开始服务，它的权重已驻留在 GPU 内存中，完成后处理并布局好供推理引擎使用。**后续每个 worker 都应该从 peer 通过 P2P RDMA 直接加载。**",
                "MX 控制平面通过 Redis 或 K8s CRD 发现兼容 peer，计算 `mx_source_id`（基于模型和运行时配置）确保只有布局一致的 peer 可互传。**控制平面只处理元数据，从不触碰权重字节本身。** 数据平面使用 NIXL 作为默认传输引擎，其可插拔后端支持 InfiniBand、RoCE、NVLink、EFA 等多种网络。",
                "新 replica 加载完成后加入源池，后续 replica 就有了更多加载源。每次成功传输都在扩大源池，将 scale-out 转化为 GPU 到 GPU 的扇出，而非重复冷加载。",
            ],
            "figs": [
                {"src": "fig01.png", "caption": "Figure 1: ModelExpress 概览。选择最快的可用路径将权重加载到 GPU 内存。"},
                {"src": "fig02.png", "caption": "Figure 2: Peer-to-peer GPUDirect RDMA 传输。通过 NIXL 在 GPU 之间直传权重。"},
            ],
        },
        {
            "type": "h2",
            "title": "NIXL 内存注册优化",
            "paras": [
                "NIXL 做 RDMA 前需要注册 GPU 内存（ibv_reg_mr 获取 rkey）。大模型有数万个张量，逐个注册的开销不可忽视。MX 提供两种优化策略，按侵入性递增：",
                "**Pool 注册**：每个底层 cudaMalloc 分配只注册一次而非每个张量。典型模型上注册次数减少 80-99%，传输语义不变。",
                "**VMM Arena 注册（更激进）**：安装一个 CUDAPluggableAllocator，将所有加载时分配路由到单个 16 TiB 虚拟地址 arena，加载完成后将整个已用范围注册为一个 dmabuf 支持的内存区域。**注册从每个张量一次坍缩为总共一次**，每个张量描述符只需携带偏移量。",
            ],
            "figs": [
                {"src": "fig03.png", "caption": "Figure 3: NIXL 内存注册优化对比。VMM Arena 将注册开销从每张量一次降到总共一次。"},
            ],
        },
        {
            "type": "h2",
            "title": "运行时路径选择与安全回退",
            "paras": [
                "MX 在启动时探测可用能力，自动跳过环境不支持的路径。优先级顺序：",
                "① **P2P RDMA** → ② **ModelStreamer** → ③ **GPUDirect Storage** → ④ **默认加载器（主机 staging POSIX I/O）**",
                "如果某路径不可用或在修改模型状态前失败，自动 fall through。如果失败发生在权重开始落地后，MX 会重新初始化模型再继续，**永远不会提供部分写入的权重。** 这种能力驱动的设计让 MX 核心保持硬件和软件无关，平台特定的加速路径只在支持时启用。",
            ],
        },
        {
            "type": "h2",
            "title": "端到端效果：8 分钟 → 1 分 44 秒",
            "paras": [
                "在 8×B200 GPU + ConnectX-7 NIC 节点上测试 DeepSeek-V4-Pro（TP=8），MX 的端到端冷启动时间从 8 分钟降到 **1 分 44 秒**，包含权重加载和内核缓存继承。其中权重加载本身在 P2P 模式下仅需不到 10 秒。",
                "Ablation 实验显示，P2P RDMA 路径相比从对象存储加载带来最大的单次加速收益，而内核缓存继承则解决了权重加载加速后暴露的新瓶颈——编译时间。两者叠加，才实现了从 8 分钟到 1 分 44 秒的跨越。",
            ],
            "figs": [
                {"src": "fig04.png", "caption": "Figure 4: 端到端冷启动模型加载时间对比。MX 显著缩短了从存储和 peer 加载的时间。"},
            ],
        },
        {
            "type": "h2",
            "title": "不仅是加载：继承编译后的内核缓存",
            "paras": [
                "权重进入 GPU 内存后，模型还不能立即开始服务。首次前向传播时，引擎需要 JIT 编译和 autotune 内核（torch.compile、Triton、DeepGEMM、TileLang 等）并捕获 CUDA Graph。对于 DeepSeek-V4 Pro，这需要几分钟，一旦 MX 将权重加载延迟降到 10 秒以下，**编译时间反而成了主导成本。**",
                "MX 的 Artifact Transfer API 解决了这个问题：当模型、软件栈和 GPU 架构匹配时，一个 replica 支付编译成本，其余 replica 继承生成的缓存。API 将这些文件缓存通过 NIXL 的 CPU 到 CPU RDMA 路径在 replica 间传递，验证后安装到目标引擎的缓存目录中。这消除了 K8s 中共享 RWX 卷的需求，同时 `mx_source_id` 的 artifact 特定校验防止了跨不兼容 replica 的复用。",
            ],
            "figs": [
                {"src": "fig05.png", "caption": "Figure 6: 总启动时间减少。包含 JIT 内核缓存继承后的冷启动时间从 8 分钟降到 1 分 44 秒。"},
            ],
        },
        {
            "type": "h2",
            "title": "RL 后训练：权重每个 Step 都在变",
            "paras": [
                "以上所有场景假设权重加载后固定不变。RL 后训练打破了这个假设——训练器每个 step 更新策略，推理 actor 必须在下一轮生成前拿到新权重。MX 通过四个阶段驱动 refit：",
                "**Publish**：每个训练器 rank 向 MX 发布它已拥有的张量或 shard，附带形状、dtype、放置位置和参数映射的元数据。",
                "**Discover**：rollout worker 通过 MX 查找请求的权重版本及其可用来源。",
                "**Plan**：接收方将发布的 ownership 信息映射到自己的目标布局，识别哪些源包含所需的张量或范围。",
                "**Pull, convert, and load**：接收方对源发起单边 RDMA 读取，直接拉取所需权重。",
                "MX 还正在测试 delta weight diff refit 用于跨集群权重传输，这是 Fireworks/Cursor、Cognition 等团队在最近 RL 运行中使用的技术。MX 已原生集成 vLLM、SGLang，并支持 Dynamo 和 llm-d 等推理框架。",
            ],
            "figs": [
                {"src": "fig06.png", "caption": "Figure 7: ModelExpress 加速 RL refit 流程。从训练器到推理 worker 的权重更新通过 P2P RDMA 直传。"},
            ],
        },
    ],

    "conclusion": [
        "ModelExpress 的核心贡献是打破了「每个模型副本 = 独立冷启动」的惯性思维。**通过将已加载的 replica 作为活体权重源，后续副本的启动从冷加载变成了 GPU 到 GPU 的热迁移。**",
        "这种思路不仅适用于推理冷启动，也适用于 RL 训练中的权重分发——当集群中已有权重时，与其重复从存储拉取，不如直接从最近的 peer 拿。当 inference 和 training 的权重移动问题被统一处理，整个模型生命周期的基础设施效率将显著提升。",
    ],
    "reference_url": "https://developer.nvidia.com/blog/modelexpress-distributing-model-artifacts-at-the-speed-of-light/",
}

# ========== 写入逻辑 ==========
os.makedirs(_article_dir, exist_ok=True)
out = os.path.join(_article_dir, "article_data.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)
print(f"✅ 写入 {out} ({len(json.dumps(DATA, ensure_ascii=False))} chars, {len(DATA['sections'])} sections)")