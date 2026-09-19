# -*- coding: utf-8 -*-
"""SGLang SSD Expert Pack 中文编译版 article_data_build.py"""
import json, os, sys

_article_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()


def B(t):
    """项目符号：小圆点 + 内容"""
    return ('<span style="color:#0F4C81;font-size:7px;line-height:1;vertical-align:middle;">'
            '\u25cf</span>&nbsp;' + t)


def C(t):
    """行内代码/变量名"""
    return ('<code style="background:#f3f4f5;padding:2px 5px;border-radius:3px;'
            'color:#0F4C81;">' + t + '</code>')


def SUB(t):
    """源文 h4 级小标题（正文同级加粗小标题）"""
    return '<span style="color:#0F4C81;font-weight:bold;">' + t + '</span>'


def CODE(lang, code):
    return '__CODE__' + lang + '::' + code


SUMMARY = [
    {"key": "核心思路", "body": "把装不进显存和内存的路由专家留在 NVMe SSD，只搬运路由器选中的专家"},
    {"key": "关键优化", "body": "权重按专家重排成连续块，O_DIRECT 直接读进对齐 pinned 缓冲，省掉一次主机内存拷贝"},
    {"key": "实测结果", "body": "DeepSeek-V4-Flash 相对基线预填充快 2.28 倍、解码快 6.92 倍；Kimi-K3 相对 llama.cpp 预填充快 6.96 倍"},
]

LEAD = [
    "一张 32GB 显存的 RTX 5090、一颗 Intel Ultra5 230F、32GB 内存，再加一块 2TB 的消费级 NVMe SSD，就能跑起 DeepSeek-V4-Flash 和 Kimi-K3。这两个模型的总参数容量远超单卡显存，常规部署需要多张 GPU，或者几百 GB 乃至 TB 级的主机内存。",
    "**SGLang 的 SSD Expert Pack 把显存问题换成了存储问题：**路由专家权重全部留在 NVMe SSD 上，路由器为每个 token 只激活一小部分专家，运行时因此只搬运那些尚未缓存在 GPU 上的被选中专家。",
    "这条路改变的是权重的存储与交付方式，不是模型计算本身。它不剪枝、不替换、不合并，也不跳过任何被选中的专家，Expert Top-K 保持不变。**真正的关键有三处：把权重按专家重新布局成可直接寻址的连续块、用直接 I/O 去掉 page cache 到 pinned memory 的那次拷贝、用按字节预算的 GPU 缓存留住复用率最高的工作集。**",
]

SECTIONS = []

# ───────── 1. 把显存问题变成存储问题 ─────────
SECTIONS.append({
    "type": "h2",
    "title": "1. 把显存问题变成存储问题",
    "paras": [
        "DeepSeek-V4-Flash 和 Kimi-K3 的总参数容量远超单张消费级 GPU 的显存。常规部署因此需要多张 GPU，或者几百 GB 乃至 TB 级的主机内存。这个容量门槛，把前沿模型的能力和本地硬件隔开了一道很高的墙。",
        "SGLang 的 SSD-backed Expert Pack 路径换了个思路。路由专家权重留在 NVMe SSD 上。路由器为每个 token 只激活一小部分专家，运行时因此只搬运那些还没在当前 GPU 缓存里的被选中专家。Expert Pack 把每一对「层/专家」的权重重新组织成一个可直接寻址的连续专家块。运行时用直接 I/O 把这个专家块读进一块对齐的 pinned 主机缓冲，再异步传进 GPU 缓存。",
        "这条路改变的是模型权重的存储与交付方式，不是模型计算。它不剪枝、不替换、不合并，也不跳过被选中的专家，Expert Top-K 也不降低。结果就是：用一颗 Intel Ultra5 230F CPU、32GB 内存、一块 TiPro9000 2TB 盘和一张 32GB 显存的 RTX 5090，可以实际跑起 DeepSeek-V4-Flash 和已验证的纯文本 Kimi-K3 路径。",
    ],
})

SECTIONS.append({
    "type": "h3",
    "title": "MoE 的计算是稀疏的，模型容量不是",
    "paras": [
        "混合专家（Mixture-of-Experts）模型把前馈网络拆成许多专家。路由器为一个 token 给专家打分之后，只有一小部分专家参与这个 token 的计算，其余专家在该 token 上处于空闲状态。",
        "而路由器的选择会随 token 和提示词变化，所以即使任一时刻只有很小的工作集是活跃的，完整的专家池也必须随时可用。量化能缩小产物体积，但消不掉存放专家池的需求。MoE 推理因此同时具有两个性质：",
        B("每个 token 的计算是稀疏的；"),
        B("需要存放和交付的专家总容量非常大。"),
        "这正是 SSD 作为后备层的价值所在。它提供的容量远超消费级显存或内存，而现代 PCIe 5.0 NVMe SSD 的带宽，足以支撑一条精心设计的交付路径。只有当布局、读取路径和缓存策略都与专家级访问模式匹配时，SSD 的容量才会真正变成可执行的模型内存。",
    ],
})

SECTIONS.append({
    "type": "h3",
    "title": "容量与成本的差距",
    "paras": [
        "一张容量与成本的对比可以把这笔取舍讲清楚。下面这些数字只是容量的下界，不是整机价格。",
        "这张图并不意味着 SSD 和 DRAM 的延迟一样，也不意味着只买一块 SSD 就能跑模型。它说明的是：把完整专家池放进显存或内存很快就会变得不现实，而用 SSD 承担容量、再给活跃工作集配一块有上限的 GPU 缓存，可以大幅拉低硬件门槛。",
    ],
    "fig_after": {"0": [{"src": "fig01.png", "caption": "图1：DeepSeek-V4-Flash 与 Kimi-K3 的容量成本对比（对数坐标）。"}]},
})

SECTIONS.append({
    "type": "h3",
    "title": "SGLang 的 SSD Expert Pack 方案",
    "paras": [
        "SSD-LLaMA 的核心思想，是把 SSD、内存和显存当作一套由运行时控制的存储层级来管理。完整专家池留在高容量层，有限的显存则保留观测到复用率最高的那些专家。",
        "SGLang 的 Expert Pack 把这套思想里最关键的、以专家为中心的部分，落到了 SGLang 的 MoE 运行时里：",
        B("Expert Pack 让每一对「层/专家」成为可独立寻址的连续专家块。"),
        B("O_DIRECT 与对齐的 pinned 缓冲去掉了额外的一次 page cache 中转拷贝。"),
        B("按字节预算的 LFU/LRU GPU 缓存，保留那些会被复用的完整专家。"),
        "当前的 SGLang 实现并不声称复刻 SSD-LLaMA 论文里的每一个机制。SGLang 的实现是以 GPU 为中心的：pinned 主机内存是一块有上限的传输中转区，不是常驻的主机专家缓存；当前特性也不需要论文里的 CPU 专家执行或无损 CUDA 解压。把这条边界讲清楚，功能范围才是精确的。",
    ],
})

# ───────── 2. 原生 GGUF 加载路径 ─────────
SECTIONS.append({
    "type": "h2",
    "title": "2. 为什么原生 GGUF 加载路径不够用",
    "paras": [
        "在原始的 GGUF 或多分片张量布局下，同一个专家的 gate、up、down 权重可能位于文件的不同区域。一次路由命中因此会触发多次小读取、张量名查找和中转操作。",
        "显式的按需读取避免了投机预取，但会把 SSD 与 H2D 的完整延迟暴露在当前 MoE 层的关键路径上。路由器出结果之后，GPU 必须等待被选中的专家。预取能掩盖一部分延迟，但有两个根本限制：",
        B("正确的专家仍可能到得太晚，因为路由结果要等上一步计算结束才知道；"),
        B("预测错误会消耗 SSD 带宽、中转空间和 GPU 缓存容量，而真正被选中的专家之后仍然要读。"),
        "所以 SGLang 的做法是先改变专家在物理上的布局，再压低每一次不可避免的缓存未命中的代价。",
    ],
})

SECTIONS.append({
    "type": "h3",
    "title": "原生 GGUF 为什么不能直接用专家级 O_DIRECT",
    "paras": [
        "原生 GGUF 是面向张量的模型容器，不是面向专家的直接 I/O 存储。它的元数据和张量负载都按单个张量组织，而同一个专家的 gate、up、down 权重可能被分散在文件的不同区域甚至不同分片里。原始加载路径通常使用解析器、mmap 或带缓冲的文件读取，应用程序看到的是可分页的、由 page cache 支撑的映射，而不是一块预分配的、对齐的 DMA 目标缓冲。",
        "O_DIRECT 要求下面这些全部由调用方控制：",
        B("与存储和文件系统约定一致的文件偏移；"),
        B("与该约定一致的读取长度；"),
        B("由用户提供、地址同样对齐且适合该次读取的缓冲。"),
        "原生 GGUF 文件里任意一段张量切片都提供不了这种专家级约定。它的偏移可能没对齐，长度可能不是所需块大小的整数倍，一个专家需要的三个张量也不保证构成一段连续区间。调用方当然可以自己发多次带填充的对齐读取，再把专家拼装到另一块缓冲里，但那样就丢掉了最主要的收益：重新引入多次读取和额外的拼装工作，同时原来的 mmap/page cache 路径依旧不能把 page cache 页面本身当作 O_DIRECT 的目标缓冲。",
        "Expert Pack 就是让直接 I/O 变得可用的那个离线变换。它把一对「层/专家」的所有角色放进一个带填充、对齐的专家块，在清单里记录精确的偏移和长度，并提供一块地址满足同一约定的 pinned 缓冲。运行时因此可以完整地读取并传输一个专家，而不需要让原生 GGUF 布局去扮演直接 I/O 布局。",
    ],
})

# ───────── 3. Expert Pack 布局 ─────────
SECTIONS.append({
    "type": "h2",
    "title": "3. Expert Pack：按专家组织权重",
    "paras": [
        "SGLang Expert Pack v1 把一对 (layer, expert) 当作一个完整专家。一个 DeepSeek 专家包含 gate、up、down 三个角色。清单记录每个角色的张量边界、格式、完整性信息和 pack 偏移。",
        "逻辑布局如下：",
        "运行时不会去扫描文件找张量名，而是从 pack 元数据推导专家偏移：",
        CODE("python", "expert_offset = data_start\n              + (layer * num_experts + expert) * expert_stride"),
        "专家块内部各角色的偏移同样会被校验。于是一次清单查找就能解析出完整的专家读取区间。运行时可以按 read_splits 把这个区间切成数量有界的并行任务。",
        "这套布局改变的是权重在 SSD 上的物理组织，不是张量内容、量化格式、路由决策或模型数学。Kimi-K3 使用一个独立的 GGML Expert Pack 适配器，当前验证过的输入是 38 个 Q2_K GGUF 分片，其路由专家的 gate/up 用 Q2_K、down 用 Q3_K。",
    ],
    "fig_after": {"1": [{"src": "fig02.png", "caption": "图2：Expert Pack 的物理数据块布局，专家字节流连续排列，块之间带显式对齐填充。"}]},
})

SECTIONS.append({
    "type": "h3",
    "title": "直接 I/O 要求对齐",
    "paras": [
        "直接 I/O 不能像普通 read() 那样接受任意的文件偏移、长度和用户缓冲。SGLang 运行时会校验：",
        B("每个专家的 Expert Pack 偏移；"),
        B("每个读取区间的起点与长度；"),
        B("每块 pinned 中转缓冲的地址。"),
        "当前实现检查 4096 字节对齐。如果 pack 或中转缓冲不满足这个约定，初始化就会失败，而不是在推理过程中悄悄退回到一条不受控的路径。",
    ],
})

# ───────── 4. 关键优化 ─────────
SECTIONS.append({
    "type": "h2",
    "title": "4. 关键优化：去掉 page cache 到 pinned memory 的拷贝",
    "paras": [
        "这是 Expert Pack 与传统文件读取路径之间最重要的差别之一。",
    ],
})

SECTIONS.append({
    "type": "h3",
    "title": "传统缓冲 I/O",
    "paras": [
        "传统的文件读取通常要经过操作系统 page cache：",
        "page cache 是内核管理的文件缓存，它和 CUDA 可用于异步 H2D 的 page-locked 用户内存不是一回事。要发起异步 H2D 传输，应用程序通常得先准备一块 pinned 缓冲。文件数据因此必须先从这个 page cache 拷进那块 pinned 缓冲，GPU 传输才能开始。从应用程序的角度看，这次 page cache 到 pinned 的交接是一次同步的 CPU 内存拷贝：主机侧的中转步骤必须先完成，H2D 操作才有一块有效的 pinned 源缓冲。它本身不是一次 cudaMemcpyAsync。",
        "它既不是 SSD 读取，也不是 H2D 传输，而是 CPU 在主机侧多做的一次同步内存拷贝：从 page cache 支撑的内存里读负载，再写进一块 pinned 中转缓冲。对一个较大的专家来说，这等于按专家全尺寸做一次读加一次写，消耗主机内存带宽，并在 GPU 传输开始之前多引入一次内核态到用户态的中转交接。",
    ],
    "fig_after": {"0": [{"src": "fig03.png", "caption": "图3：传统文件读取路径，一次同步的 page cache 到 pinned memory 拷贝，随后是异步 H2D 传输。"}]},
})

SECTIONS.append({
    "type": "h3",
    "title": "使用直接 I/O 的 Expert Pack",
    "paras": [
        "当 direct_io=True 时，SGLang 用 O_DIRECT 打开 Expert Pack，并把读取目标设为一块预分配的、对齐的 pinned 中转缓冲：",
        "读取目标本来就是 CUDA 需要的那块 pinned 缓冲，所以下面这个中间步骤被消掉了：",
        CODE("text", "page cache -> pinned memory"),
        "这不是把那次拷贝做得更快，而是把这次拷贝从数据路径上整个去掉。一个简化的成本模型是：",
        CODE("text", "Traditional path:\nT = T(SSD -> page cache)\n  + T(page cache -> pinned)\n  + T(pinned -> GPU)\n  + T(sync)\n\nExpert Pack direct I/O:\nT = T(SSD -> pinned)\n  + T(pinned -> GPU)"),
        "O_DIRECT 不会让 SSD 的物理带宽变大。它做的是从端到端路径上减去一次完整的主机内存遍历，由此带来这些好处：",
        B("少一次主机内存读和写，降低 CPU 与内存带宽压力；"),
        B("少一次内核 page cache 与用户态中转之间的同步交接；"),
        B("大块专家负载不再污染 page cache、去和无关数据抢空间；"),
        B("读完的专家块可以不经 page cache 中转拷贝直接进入 H2D 路径；"),
        B("同一套专家级约定在每一对「层/专家」上复用。"),
        "page cache 拷贝这条结论只在 direct_io=True 时成立。当前的 SGLang Expert Pack 加载器以及 DeepSeek/Kimi 的 5090 启动脚本默认开启该选项。如果显式关掉直接 I/O，路径会重新经过 page cache 和多一次中转拷贝。",
    ],
    "fig_after": {"0": [{"src": "fig04.png", "caption": "图4：Expert Pack 的直接 I/O 路径，对齐的 pinned 主机缓冲先喂给 GPU 专家缓存，再进入 MoE 计算。"}]},
})

# ───────── 5. GPU/VRAM 缓存 ─────────
SECTIONS.append({
    "type": "h2",
    "title": "5. GPU/VRAM 缓存：把工作集留在计算附近",
    "paras": [
        "GPU 缓存是把重复的专家访问变成显存命中的机制。Expert Pack 不缓存单个张量碎片：一个缓存条目装的是一对 (layer, expert) 完整的 gate/up/down 数据。让完整专家待在一起很重要，因为被选中的专家计算时三个角色都要用。只缓存其中一个角色的话，其余角色仍然要读，未命中的代价并没有被消掉。",
        "缓存按字节预算而不是按专家数量预算。不同模型和适配器每个专家的负载大小不同，运行时因此从可用的显存预算推导槽位数量：",
        CODE("text", "usable_vram = min(requested_cache, free_vram - reserve)\nslot_count  = floor(usable_vram / expert_payload_bytes)"),
        "预留量保护模型本身、CUDA 运行时、激活值以及其他非缓存分配所需的内存。如果算出来的槽位数装不下一个完整的 top-k 工作集，初始化就会失败。这让缓存约定变得显式：缓存预算不许占用当前 MoE 计算所必需的内存。",
        "命中时，运行时复用常驻的专家，既不读 Expert Pack 也不为该专家发起 H2D。如果上一次传输还在进行，一个 CUDA event 会保证消费方不会看到只装入一半的槽位。未命中时，运行时挑一个牺牲槽位，把完整专家读进可复用的 pinned 中转缓冲，再拷进 GPU 槽位，并且只在传输 event 就绪之后才发布该槽位。",
        "替换策略同时考虑频率和新近度。运行时记录每一对 (layer, expert) 被选中的频次以及最后一次被使用的时间。高频专家比冷专家更难被驱逐；在有用程度相近的条目之间，更老的条目是更好的牺牲品。当前 top-k 请求里的活跃专家受保护不被驱逐，缓存因此不会把自己马上要执行的工作集换出去。",
        "源端的 Expert Pack 是不可变的，所以驱逐一个 GPU 条目不需要写回：专家总能根据记录的 SSD 偏移重建。这让显存缓存管理比脏数据缓存简单，也让替换策略只关注复用价值而不是持久性。",
        "运行时暴露了一组计数器，让缓存行为可度量：",
        B("cache_hits 与 cache_misses；"),
        B("cache_evictions；"),
        B("pack_read_bytes；"),
        B("h2d_bytes；"),
        B("fallback_count 与 io_errors。"),
        "这些计数器能把缓存问题和 I/O 问题区分开。命中率低意味着显存预算或负载局部性不足；命中率良好但 pack_read_bytes 与 h2d_bytes 很高，可能说明在某个阶段活跃集比缓存大。io_errors 报告观测到的 I/O 失败，而 fallback_count 是诊断性遥测，其含义取决于被插桩的回退路径；两者都不是缓存性能指标。",
        "当前的执行顺序把专家缓存未命中放在了它所服务的 MoE 计算的关键路径上。acquire() 把路由 ID 拷回 CPU，等待 SSD 读取的 future，入队专家级 H2D 传输，并让当前 CUDA 流等待这些传输 event。只有这些 event 就绪之后，apply() 才启动 MoE 内核。不同缺失专家的读取与传输可以在交付阶段重叠，但当前路径不会把这段交付与消费这些专家的 MoE 计算重叠起来。",
        "因此当前路径的一个简化单步模型是：",
        CODE("text", "T_step ~= T(miss delivery) + T(GPU compute)"),
        "这里的 T(miss delivery) 包含路由 ID 准备、SSD 读取、中转、H2D 提交，以及让被选中专家可用所需的等待。GPU 缓存命中时，SSD 读取与 H2D 这两部分可以跳过。跨步骤的流水线能改变这个模型，但那不属于这里描述的执行路径。实际结果取决于 SSD 带宽、访问分布、缓存命中率、中转槽位数量和专家形状。",
    ],
})

