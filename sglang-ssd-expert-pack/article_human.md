SGLang SSD Expert Pack：32GB 显存跑起 DeepSeek-V4-Flash 与 Kimi-K3



## 1. 把显存问题变成存储问题

DeepSeek-V4-Flash 和 Kimi-K3 的总参数容量远超单张消费级 GPU 的显存。常规部署因此需要多张 GPU，或者几百 GB 乃至 TB 级的主机内存。这个容量门槛，把前沿模型的能力和本地硬件隔开了一道很高的墙。

SGLang 的 SSD-backed Expert Pack 路径换了个思路。路由专家权重留在 NVMe SSD 上。路由器为每个 token 只激活一小部分专家，运行时因此只搬运那些还没在当前 GPU 缓存里的被选中专家。Expert Pack 把每一对「层/专家」的权重重新组织成一个可直接寻址的连续专家块。运行时用直接 I/O 把这个专家块读进一块对齐的 pinned 主机缓冲，再异步传进 GPU 缓存。

这条路改变的是模型权重的存储与交付方式，不是模型计算。它不剪枝、不替换、不合并，也不跳过被选中的专家，Expert Top-K 也不降低。结果就是：用一颗 Intel Ultra5 230F CPU、32GB 内存、一块 TiPro9000 2TB 盘和一张 32GB 显存的 RTX 5090，可以实际跑起 DeepSeek-V4-Flash 和已验证的纯文本 Kimi-K3 路径。

### MoE 的计算是稀疏的，模型容量不是

混合专家（Mixture-of-Experts）模型把前馈网络拆成许多专家。路由器为一个 token 给专家打分之后，只有一小部分专家参与这个 token 的计算，其余专家在该 token 上处于空闲状态。

而路由器的选择会随 token 和提示词变化，所以即使任一时刻只有很小的工作集是活跃的，完整的专家池也必须随时可用。量化能缩小产物体积，但消不掉存放专家池的需求。MoE 推理因此同时具有两个性质：

<span style="color:#0F4C81;font-size:7px;line-height:1;vertical-align:middle;">●</span>&nbsp;每个 token 的计算是稀疏的；

<span style="color:#0F4C81;font-size:7px;line-height:1;vertical-align:middle;">●</span>&nbsp;需要存放和交付的专家总容量非常大。

这正是 SSD 作为后备层的价值所在。它提供的容量远超消费级显存或内存，而现代 PCIe 5.0 NVMe SSD 的带宽，足以支撑一条精心设计的交付路径。只有当布局、读取路径和缓存策略都与专家级访问模式匹配时，SSD 的容量才会真正变成可执行的模型内存。

### 容量与成本的差距

一张容量与成本的对比可以把这笔取舍讲清楚。下面这些数字只是容量的下界，不是整机价格。

这张图并不意味着 SSD 和 DRAM 的延迟一样，也不意味着只买一块 SSD 就能跑模型。它说明的是：把完整专家池放进显存或内存很快就会变得不现实，而用 SSD 承担容量、再给活跃工作集配一块有上限的 GPU 缓存，可以大幅拉低硬件门槛。

### SGLang 的 SSD Expert Pack 方案

SSD-LLaMA 的核心思想，是把 SSD、内存和显存当作一套由运行时控制的存储层级来管理。完整专家池留在高容量层，有限的显存则保留观测到复用率最高的那些专家。

SGLang 的 Expert Pack 把这套思想里最关键的、以专家为中心的部分，落到了 SGLang 的 MoE 运行时里：

<span style="color:#0F4C81;font-size:7px;line-height:1;vertical-align:middle;">●</span>&nbsp;Expert Pack 让每一对「层/专家」成为可独立寻址的连续专家块。

<span style="color:#0F4C81;font-size:7px;line-height:1;vertical-align:middle;">●</span>&nbsp;O_DIRECT 与对齐的 pinned 缓冲去掉了额外的一次 page cache 中转拷贝。

<span style="color:#0F4C81;font-size:7px;line-height:1;vertical-align:middle;">●</span>&nbsp;按字节预算的 LFU/LRU GPU 缓存，保留那些会被复用的完整专家。

当前的 SGLang 实现并不声称复刻 SSD-LLaMA 论文里的每一个机制。SGLang 的实现是以 GPU 为中心的：pinned 主机内存是一块有上限的传输中转区，不是常驻的主机专家缓存；当前特性也不需要论文里的 CPU 专家执行或无损 CUDA 解压。把这条边界讲清楚，功能范围才是精确的。

## 2. 为什么原生 GGUF 加载路径不够用

在原始的 GGUF 或多分片张量布局下，同一个专家的 gate、up、down 权重可能位于文件的不同区域。一次路由命中因此会触发多次小读取、张量名查找和中转操作。

显式的按需读取避免了投机预取，但会把 SSD 与 H2D 的完整延迟暴露在当前 MoE 层的关键路径上。路由器出结果之后，GPU 必须等待被选中的专家。预取能掩盖一部分延迟，但有两个根本限制：

<span style="color:#0F4C81;font-size:7px;line-height:1;vertical-align:middle;">●</span>&nbsp;正确的专家仍可能到得太晚，因为路由结果要等上一步计算结束才知道；

<span style="color:#0F4C81;font-size:7px;line-height:1;vertical-align:middle;">●</span>&nbsp;预测错误会消耗 SSD 带宽、中转空间和 GPU 缓存容量，而真正被选中的专家之后仍然要读。

所以 SGLang 的做法是先改变专家在物理上的布局，再压低每一次不可避免的缓存未命中的代价。

### 原生 GGUF 为什么不能直接用专家级 O_DIRECT

原生 GGUF 是面向张量的模型容器，不是面向专家的直接 I/O 存储。它的元数据和张量负载都按单个张量组织，而同一个专家的 gate、up、down 权重可能被分散在文件的不同区域甚至不同分片里。原始加载路径通常使用解析器、mmap 或带缓冲的文件读取，应用程序看到的是可分页的、由 page cache 支撑的映射，而不是一块预分配的、对齐的 DMA 目标缓冲。

O_DIRECT 要求下面这些全部由调用方控制：

<span style="color:#0F4C81;font-size:7px;line-height:1;vertical-align:middle;">●</span>&nbsp;与存储和文件系统约定一致的文件偏移；

<span style="color:#0F4C81;font-size:7px;line-height:1;vertical-align:middle;">●</span>&nbsp;与该约定一致的读取长度；

<span style="color:#0F4C81;font-size:7px;line-height:1;vertical-align:middle;">●</span>&nbsp;由用户提供、地址同样对齐且适合该次读取的缓冲。

原生 GGUF 文件里任意一段张量切片都提供不了这种专家级约定。它的偏移可能没对齐，长度可能不是所需块大小的整数倍，一个专家需要的三个张量也不保证构成一段连续区间。调用方当然可以自己发多次带填充的对齐读取，再把专家拼装到另一块缓冲里，但那样就丢掉了最主要的收益：重新引入多次读取和额外的拼装工作，同时原来的 mmap/page cache 路径依旧不能把 page cache 页面本身当作 O_DIRECT 的目标缓冲。

Expert Pack 就是让直接 I/O 变得可用的那个离线变换。它把一对「层/专家」的所有角色放进一个带填充、对齐的专家块，在清单里记录精确的偏移和长度，并提供一块地址满足同一约定的 pinned 缓冲。运行时因此可以完整地读取并传输一个专家，而不需要让原生 GGUF 布局去扮演直接 I/O 布局。

## 3. Expert Pack：按专家组织权重

SGLang Expert Pack v1 把一对 (layer, expert) 当作一个完整专家。一个 DeepSeek 专家包含 gate、up、down 三个角色。清单记录每个角色的张量边界、格式、完整性信息和 pack 偏移。

逻辑布局如下：

运行时不会去扫描文件找张量名，而是从 pack 元数据推导专家偏移：

__CODE__python::expert_offset = data_start
              + (layer * num_experts + expert) * expert_stride

专家块内部各角色的偏移同样会被校验。于是一次清单查找就能解析出完整的专家读取区间。运行时可以按 read_splits 把这个区间切成数量有界的并行任务。

这套布局改变的是权重在 SSD 上的物理组织，不是张量内容、量化格式、路由决策或模型数学。Kimi-K3 使用一个独立的 GGML Expert Pack 适配器，当前验证过的输入是 38 个 Q2_K GGUF 分片，其路由专家的 gate/up 用 Q2_K、down 用 Q3_K。

### 直接 I/O 要求对齐

直接 I/O 不能像普通 read() 那样接受任意的文件偏移、长度和用户缓冲。SGLang 运行时会校验：

<span style="color:#0F4C81;font-size:7px;line-height:1;vertical-align:middle;">●</span>&nbsp;每个专家的 Expert Pack 偏移；

<span style="color:#0F4C81;font-size:7px;line-height:1;vertical-align:middle;">●</span>&nbsp;每个读取区间的起点与长度；

<span style="color:#0F4C81;font-size:7px;line-height:1;vertical-align:middle;">●</span>&nbsp;每块 pinned 中转缓冲的地址。

当前实现检查 4096 字节对齐。如果 pack 或中转缓冲不满足这个约定，初始化就会失败，而不是在推理过程中悄悄退回到一条不受控的路径。

## 4. 关键优化：去掉 page cache 到 pinned memory 的拷贝

这是 Expert Pack 与传统文件读取路径之间最重要的差别之一。

### 传统缓冲 I/O

传统的文件读取通常要经过操作系统 page cache：

page cache 是内核管理的文件缓存，它和 CUDA 可用于异步 H2D 的 page-locked 用户内存不是一回事。要发起异步 H2D 传输，应用程序通常得先准备一块 pinned 缓冲。文件数据因此必须先从这个 page cache 拷进那块 pinned 缓冲，GPU 传输才能开始。从应用程序的角度看，这次 page cache 到 pinned 的交接是一次同步的 CPU 内存拷贝：主机侧的中转步骤必须先完成，H2D 操作才有一块有效的 pinned 源缓冲。它本身不是一次 cudaMemcpyAsync。

它既不是 SSD 读取，也不是 H2D 传输，而是 CPU 在主机侧多做的一次同步内存拷贝：从 page cache 支撑的内存里读负载，再写进一块 pinned 中转缓冲。对一个较大的专家来说，这等于按专家全尺寸做一次读加一次写，消耗主机内存带宽，并在 GPU 传输开始之前多引入一次内核态到用户态的中转交接。

### 使用直接 I/O 的 Expert Pack

当 direct_io=True 时，SGLang 用 O_DIRECT 打开 Expert Pack，并把读取目标设为一块预分配的、对齐的 pinned 中转缓冲：

读取目标本来就是 CUDA 需要的那块 pinned 缓冲，所以下面这个中间步骤被消掉了：

__CODE__text::page cache -> pinned memory

这不是把那次拷贝做得更快，而是把这次拷贝从数据路径上整个去掉。一个简化的成本模型是：

__CODE__text::Traditional path:
T = T(SSD -> page cache)
  + T(page cache -> pinned)
  + T(pinned -> GPU)
  + T(sync)

Expert Pack direct I/O:
T = T(SSD -> pinned)
  + T(pinned -> GPU)

O_DIRECT 不会让 SSD 的物理带宽变大。它做的是从端到端路径上减去一次完整的主机内存遍历，由此带来这些好处：

<span style="color:#0F4C81;font-size:7px;line-height:1;vertical-align:middle;">●</span>&nbsp;少一次主机内存读和写，降低 CPU 与内存带宽压力；

<span style="color:#0F4C81;font-size:7px;line-height:1;vertical-align:middle;">●</span>&nbsp;少一次内核 page cache 与用户态中转之间的同步交接；

<span style="color:#0F4C81;font-size:7px;line-height:1;vertical-align:middle;">●</span>&nbsp;大块专家负载不再污染 page cache、去和无关数据抢空间；

<span style="color:#0F4C81;font-size:7px;line-height:1;vertical-align:middle;">●</span>&nbsp;读完的专家块可以不经 page cache 中转拷贝直接进入 H2D 路径；

<span style="color:#0F4C81;font-size:7px;line-height:1;vertical-align:middle;">●</span>&nbsp;同一套专家级约定在每一对「层/专家」上复用。

page cache 拷贝这条结论只在 direct_io=True 时成立。当前的 SGLang Expert Pack 加载器以及 DeepSeek/Kimi 的 5090 启动脚本默认开启该选项。如果显式关掉直接 I/O，路径会重新经过 page cache 和多一次中转拷贝。

## 5. GPU/VRAM 缓存：把工作集留在计算附近

GPU 缓存是把重复的专家访问变成显存命中的机制。Expert Pack 不缓存单个张量碎片：一个缓存条目装的是一对 (layer, expert) 完整的 gate/up/down 数据。让完整专家待在一起很重要，因为被选中的专家计算时三个角色都要用。只缓存其中一个角色的话，其余角色仍然要读，未命中的代价并没有被消掉。

缓存按字节预算而不是按专家数量预算。不同模型和适配器每个专家的负载大小不同，运行时因此从可用的显存预算推导槽位数量：

__CODE__text::usable_vram = min(requested_cache, free_vram - reserve)
slot_count  = floor(usable_vram / expert_payload_bytes)

预留量保护模型本身、CUDA 运行时、激活值以及其他非缓存分配所需的内存。如果算出来的槽位数装不下一个完整的 top-k 工作集，初始化就会失败。这让缓存约定变得显式：缓存预算不许占用当前 MoE 计算所必需的内存。

命中时，运行时复用常驻的专家，既不读 Expert Pack 也不为该专家发起 H2D。如果上一次传输还在进行，一个 CUDA event 会保证消费方不会看到只装入一半的槽位。未命中时，运行时挑一个牺牲槽位，把完整专家读进可复用的 pinned 中转缓冲，再拷进 GPU 槽位，并且只在传输 event 就绪之后才发布该槽位。

替换策略同时考虑频率和新近度。运行时记录每一对 (layer, expert) 被选中的频次以及最后一次被使用的时间。高频专家比冷专家更难被驱逐；在有用程度相近的条目之间，更老的条目是更好的牺牲品。当前 top-k 请求里的活跃专家受保护不被驱逐，缓存因此不会把自己马上要执行的工作集换出去。

源端的 Expert Pack 是不可变的，所以驱逐一个 GPU 条目不需要写回：专家总能根据记录的 SSD 偏移重建。这让显存缓存管理比脏数据缓存简单，也让替换策略只关注复用价值而不是持久性。

运行时暴露了一组计数器，让缓存行为可度量：

<span style="color:#0F4C81;font-size:7px;line-height:1;vertical-align:middle;">●</span>&nbsp;cache_hits 与 cache_misses；

<span style="color:#0F4C81;font-size:7px;line-height:1;vertical-align:middle;">●</span>&nbsp;cache_evictions；

<span style="color:#0F4C81;font-size:7px;line-height:1;vertical-align:middle;">●</span>&nbsp;pack_read_bytes；

<span style="color:#0F4C81;font-size:7px;line-height:1;vertical-align:middle;">●</span>&nbsp;h2d_bytes；

<span style="color:#0F4C81;font-size:7px;line-height:1;vertical-align:middle;">●</span>&nbsp;fallback_count 与 io_errors。

这些计数器能把缓存问题和 I/O 问题区分开。命中率低意味着显存预算或负载局部性不足；命中率良好但 pack_read_bytes 与 h2d_bytes 很高，可能说明在某个阶段活跃集比缓存大。io_errors 报告观测到的 I/O 失败，而 fallback_count 是诊断性遥测，其含义取决于被插桩的回退路径；两者都不是缓存性能指标。

当前的执行顺序把专家缓存未命中放在了它所服务的 MoE 计算的关键路径上。acquire() 把路由 ID 拷回 CPU，等待 SSD 读取的 future，入队专家级 H2D 传输，并让当前 CUDA 流等待这些传输 event。只有这些 event 就绪之后，apply() 才启动 MoE 内核。不同缺失专家的读取与传输可以在交付阶段重叠，但当前路径不会把这段交付与消费这些专家的 MoE 计算重叠起来。

因此当前路径的一个简化单步模型是：

__CODE__text::T_step ~= T(miss delivery) + T(GPU compute)

这里的 T(miss delivery) 包含路由 ID 准备、SSD 读取、中转、H2D 提交，以及让被选中专家可用所需的等待。GPU 缓存命中时，SSD 读取与 H2D 这两部分可以跳过。跨步骤的流水线能改变这个模型，但那不属于这里描述的执行路径。实际结果取决于 SSD 带宽、访问分布、缓存命中率、中转槽位数量和专家形状。

## 6. 实验设置

我们在一台消费级机器上用 SGLang 的 SSD Expert Pack 路径评测了 DeepSeek-V4-Flash 和 Kimi-K3：Intel Ultra5 230F CPU、32GB 内存、一块 TiPro9000 2TB 盘，以及一张 32GB 显存的 RTX 5090。这个负载代表的是端点式推理，而不是批量服务：十个固定请求逐个发送，上一个请求结束后才发下一个。

测试集包含五个 Alpaca 请求和五个 MMLU 请求。两组对比都使用相同的提示词顺序、temperature 0、默认 EOS 处理和 200 token 的生成目标。结果部分报告平均预填充与解码速率，以及 SGLang 的缓存命中率和 SSD 流量。确切的版本、文件准备过程和启动命令记录在结果之后。

Expert Pack 通过 --load-format expert_pack 显式选择；常规的 auto、safetensors 和 gguf 加载路径不受影响。DeepSeek-V4-Flash 与 Kimi-K3 的详细复现流程见第 9 节。

## 7. 正确性边界

Expert Pack 是权重布局与交付层面的优化，不是近似推理算法。它的正确性约定是：

<span style="color:#0F4C81;font-size:7px;line-height:1;vertical-align:middle;">●</span>&nbsp;路由器选中的每个专家都会被执行；

<span style="color:#0F4C81;font-size:7px;line-height:1;vertical-align:middle;">●</span>&nbsp;Expert Top-K 不变；

<span style="color:#0F4C81;font-size:7px;line-height:1;vertical-align:middle;">●</span>&nbsp;被选中的专家不会被另一个常驻专家顶替；

<span style="color:#0F4C81;font-size:7px;line-height:1;vertical-align:middle;">●</span>&nbsp;被选中的专家不会被剪枝、跳过或合并；

<span style="color:#0F4C81;font-size:7px;line-height:1;vertical-align:middle;">●</span>&nbsp;pack 与清单按配置完成结构、维度和密码学校验；

<span style="color:#0F4C81;font-size:7px;line-height:1;vertical-align:middle;">●</span>&nbsp;fallback_count 与 io_errors 会被上报，而不是把 I/O 失败悄悄藏起来。

验证显示，DeepSeek-V4-Flash 在多个提示词类别上给出了与 Ollama 语义等价的回答。Kimi-K3 与 SGLang 的 200 token 参考输出一致；全部 92 个路由层都以 Top-16 专家执行，io_errors=0。fallback_count 作为诊断遥测保留，但当前路径并不会为每一种假想的回退都提供插桩自增，所以零值不作为独立的正确性证据。正确性由路由与输出审计、以及 pack 结构校验来确立。

## 8. 性能结果

所有 SGLang、Ollama 和 llama.cpp 的测量都使用第 9 节记录的测试环境与版本。这些图描述的是该硬件条件下的验证结果，token 数与各运行时自身的软件设置保持各对比中所述的配置。早先的汇总表已退役，下面的图现在是 token 速率对比的正式呈现。

### 验证过的权重与 Expert Pack 体积

验证过的权重文件与生成的 Expert Pack 占用如下：

这些是验证过的权重负载的文件大小。pack 索引、锁、清单和其他元数据另计。

### DeepSeek-V4-Flash 对比基线

这组对比使用十个共享请求：五个 Alpaca 和五个 MMLU。两个运行时每个请求最多生成 200 个 token。图中报告每个数据集上平均的预填充与解码 token 速率。

相对基线，SGLang 在 Alpaca 上把预填充提升 2.28 倍、MMLU 上 3.39 倍；解码分别提升 6.92 倍和 6.55 倍。

各数据集的底层均值紧凑列在下表。速率单位是 token/秒，均为该数据集五条记录的算术平均。

### Kimi-K3 对比 llama.cpp

这组对比在两个运行时上使用相同的十个固定请求：五个 Alpaca 和五个 MMLU。两个客户端都用 temperature 0 和默认 EOS 处理；每个请求正好生成 200 个补全 token，因此解码对比在提示词集合、停止行为与输出长度上都已对齐。图中报告每个数据集上平均的预填充与解码 token 速率。

相对 llama.cpp，SGLang 在 Alpaca 上把预填充提升 6.96 倍、MMLU 上 5.80 倍；解码分别提升 3.30 倍和 3.52 倍。十请求的汇总使用第 9 节描述的十条有效请求记录。

### 专家缓存命中率与 SSD 流量

token 速率要结合缓存遥测一起看。下面这些用 Python 生成的柱状图报告唯一键的显存缓存命中率，以及每生成一个 token 的平均 SSD 流量。cache_hits 与 cache_misses 统计的是 acquire() 在每次更新内对 key 去重后的唯一 (layer, expert) 键数量，不是逐 token 的路由边访问数。一次缓存命中会免掉该专家的 SSD 读取与 H2D 传输。SSD 流量指标是各请求 pack_read_bytes 总量（含预填充与解码）的无权重均值，再按生成的补全 token 数归一化，因此并不是仅解码的流量。两张图都只展示 SGLang 自身的遥测，所以单一序列由周边文字标注，而不是图例。

DeepSeek 使用完整的十请求运行：五个 Alpaca 与五个 MMLU，每个补全 200 token。唯一键显存缓存命中率 Alpaca 为 54.2%，MMLU 为 46.4%。含预填充与解码的平均 SSD 流量分别为每个生成 token 1.66 GB 和 2.04 GB（十进制）。

Kimi 图使用全部十个完成的请求：五个 Alpaca 与五个 MMLU，每个补全 200 token。各请求唯一键显存命中率的无权重平均分别是 17.0% 和 22.7%。对应的平均 SSD 流量（含预填充与解码）为每个生成 token 22.10 GB 和 27.63 GB（十进制）。与 DeepSeek 的差异在预期之内：Kimi 的配置为 GPU 专家缓存预留 5 GiB，而 DeepSeek 那组预留约 21 GiB，两个适配器的专家负载大小与路由行为也不同。

这些提升并不来自某一个孤立的更快拷贝原语。它是几种效果的叠加：

<span style="color:#0F4C81;font-size:7px;line-height:1;vertical-align:middle;">●</span>&nbsp;Expert Pack 把散落的张量访问变成可寻址的连续专家读取；

<span style="color:#0F4C81;font-size:7px;line-height:1;vertical-align:middle;">●</span>&nbsp;直接 I/O 去掉了 page cache 到 pinned memory 的拷贝；

<span style="color:#0F4C81;font-size:7px;line-height:1;vertical-align:middle;">●</span>&nbsp;pinned 中转提供了一块 CUDA 兼容的主机源，让专家级 H2D 不必再经 page cache 中转；

<span style="color:#0F4C81;font-size:7px;line-height:1;vertical-align:middle;">●</span>&nbsp;GPU 缓存命中时跳过 SSD 读取和 H2D 传输。

## 9. 详细复现步骤

这一节给出结果表之后的完整复现流程。两个子节使用相同的十个固定请求。它们是端点式测试：客户端按顺序发送十个 HTTP 请求，等每个响应回来再发下一个，并发为 1，不使用批请求。

### 十次固定请求

这十个请求是五个 Alpaca 样本和五个 MMLU 样本，顺序如下：

每个请求使用 temperature 0、默认 EOS 处理和 200 token 目标。客户端记录每个请求的提示词 token 数、补全 token 数、TTFT/预填充耗时和解码耗时。第 8 节的表报告各数据集五条请求的算术平均。

### DeepSeek-V4-Flash：SGLang 与 Ollama

<span style="color:#0F4C81;font-weight:bold;">版本与负载</span>

SGLang 这一侧使用分支 support_deepseek-v4_and_kimi-k3_on_ssd 上的提交 81c9f837f19ff8dfe1a9fcd1abfc6069dd28d2ec。基线使用 Ollama 0.33.1 及其托管的 llama.cpp runner，提交 d222767c7。两侧都以相同采样设置串行执行上面十个请求，一次一个。

<span style="color:#0F4C81;font-weight:bold;">启动 Ollama 基线服务</span>

在拉取模型和发送请求之前，先启动 Ollama 服务：

__CODE__bash::OLLAMA_HOST=127.0.0.1:11435 ollama serve >/tmp/deepseek-ollama.log 2>&1 &

<span style="color:#0F4C81;font-weight:bold;">准备</span>

基线服务运行起来之后，从 Ollama 模型页拉取已验证的 DeepSeek-V4-Flash MXFP4 GGUF blob，并用 ollama show --modelfile 取得它的本地文件路径。对应的模型卡是 Hugging Face 上的 DeepSeek-V4-Flash-0731：

__CODE__bash::ollama pull frob/deepseek-v4-flash-0731
ollama show --modelfile frob/deepseek-v4-flash-0731

记录的 blob SHA-256 是 947ac34c08c0e5c5752ac76398f934b3b6b4075cfe915ba43dd5ac754900a4cd，Ollama 清单的 SHA-256 是 882b1398c0ca4e7ec8ca0a501fd8c4372f780f690536a3ec17ffc75306569ed3。

安装 SGLang 检出并手动构建 DeepSeek Expert Pack。为 --model-config 准备一份匹配的 DeepSeek 模型配置 JSON：

__CODE__bash::cd /path/to/sglang-latest-deepseek-v4-kimi-k3-ssd
python3 -m pip install -e 'python'
python3 tools/expert_pack/prepare_deepseek_pack.py \
  --gguf /path/to/deepseek-v4-flash-0731.gguf \
  --model-config /path/to/deepseek-v4-flash-config.json \
  --safety-margin-gib 16

这会在源 GGUF 旁边创建或复用 DeepSeek-V4-Flash.expert-pack 及其 DeepSeek-V4-Flash.expert-pack.manifest.json。

校验生成的 pack，并创建服务端需要的元数据。这条命令不启动服务；因为上一步已经构建过 pack，校验阶段会复用它而不是重新构建：

__CODE__bash::python3 examples/runtime/deepseek_v4/benchmark_deepseek_5090.py \
  --gguf /path/to/deepseek-v4-flash-0731.gguf \
  --validate-only

生成的元数据文件存放在 ${XDG_CACHE_HOME:-$HOME/.cache}/sglang-expert-pack/deepseek-v4-flash/<fingerprint>/model-meta/ 下：config.json、generation_config.json、tokenizer.json、tokenizer_config.json 和 metadata.json。

这里的 <fingerprint> 是从源 GGUF 状态和准备格式推导出的短哈希。它在本机生成，用于隔离不同源文件的产物；它不是固定的模型名，也不是需要下载的目录。

<span style="color:#0F4C81;font-weight:bold;">启动 SGLang</span>

下面这条就是直接使用 Expert Pack 的服务端启动命令。其中的哈希值在启动前从生成的清单里读出。

__CODE__bash::GGUF=/path/to/deepseek-v4-flash-0731.gguf
ARTIFACT_DIR=${XDG_CACHE_HOME:-$HOME/.cache}/sglang-expert-pack/deepseek-v4-flash/<fingerprint>
MODEL_META="$ARTIFACT_DIR/model-meta"
PACK_PATH="$(dirname "$GGUF")/DeepSeek-V4-Flash.expert-pack"
MANIFEST_PATH="$(dirname "$GGUF")/DeepSeek-V4-Flash.expert-pack.manifest.json"
STATS_PATH="$ARTIFACT_DIR/deepseek-v4-expert-pack.stats.json"
SOURCE_SHA256="$(jq -r '.source.sha256' "$MANIFEST_PATH")"
OLLAMA_MANIFEST_SHA256="$(jq -r '.model.model_identity_sha256 // .model.ollama_manifest_sha256' "$MANIFEST_PATH")"
CONFIG_SHA256="$(jq -r '.model.config_sha256' "$MANIFEST_PATH")"

python3 -m sglang.launch_server \
  --model-path "$MODEL_META" \
  --tokenizer-path "$MODEL_META" \
  --trust-remote-code \
  --load-format expert_pack \
  --model-loader-extra-config "{\"pack_path\":\"$PACK_PATH\",\"manifest_path\":\"$MANIFEST_PATH\",\"source_path\":\"$GGUF\",\"source_sha256\":\"$SOURCE_SHA256\",\"ollama_manifest_sha256\":\"$OLLAMA_MANIFEST_SHA256\",\"config_sha256\":\"$CONFIG_SHA256\",\"cache_vram_mib\":21504,\"cache_vram_reserve_mib\":2048,\"stage_slots\":12,\"read_splits\":4,\"direct_io\":true,\"stats_flush_interval\":43,\"stats_path\":\"$STATS_PATH\"}" \
  --attention-backend dsv4 \
  --tp-size 1 --ep-size 1 \
  --disable-cuda-graph --disable-flashinfer-autotune \
  --disable-shared-experts-fusion --skip-server-warmup \
  --max-running-requests 1 --mem-fraction-static 0.96 \
  --watchdog-timeout 1800 --host 127.0.0.1 --port 30001

把同样的十行发给运行中的 Ollama /api/generate 端点。保留的客户端使用 num_predict=200、temperature=0、固定种子，并且一次只发一个请求；它写出每个请求的 JSONL 记录以及结果表所用的汇总。

### Kimi-K3：SGLang 与 llama.cpp

<span style="color:#0F4C81;font-weight:bold;">版本与负载</span>

SGLang 这一侧使用同一个提交 81c9f837f19ff8dfe1a9fcd1abfc6069dd28d2ec。基线使用 llama.cpp 提交 5fff128451d7603857597ee1fc18ac1dfb90f148。上面十个 Alpaca/MMLU 请求在两个运行时上都是串行发送，一次一个，temperature 0、默认 EOS 处理、200 token 目标。

<span style="color:#0F4C81;font-weight:bold;">准备</span>

从 Blackfrost-AI/KIMI-K3-Q2_K-GGUF-ABLITERATED 下载 38 个纯文本 Q2_K GGUF 分片：

__CODE__bash::hf download Blackfrost-AI/KIMI-K3-Q2_K-GGUF-ABLITERATED \
  --include "KIMI-K3-MXP4-DERISKED-Q2_K-*.gguf" \
  --local-dir /path/to/kimi-k3

按记录的版本从 moonshotai/Kimi-K3 下载分词器与配置文件：

__CODE__bash::hf download moonshotai/Kimi-K3 \
  config.json tokenizer_config.json generation_config.json \
  tokenization_kimi.py encoding_k3.py tiktoken.model \
  --revision 9f62e4e9fffbd0a83ddd60e1c209d828994b3569 \
  --local-dir /path/to/kimi-k3-tokenizer

手动构建 Kimi Expert Pack。--gguf 指向第一个编号分片，脚本会自动发现该目录下的全部 38 个分片。Kimi 模型配置就是下载来的、含 text_config 的 config.json：

__CODE__bash::cd /path/to/sglang-latest-deepseek-v4-kimi-k3-ssd
python3 tools/expert_pack/prepare_kimi_pack.py \
  --gguf /path/to/kimi-k3/KIMI-K3-MXP4-DERISKED-Q2_K-00001-of-00038.gguf \
  --model-config /path/to/kimi-k3-tokenizer/config.json \
  --safety-margin-gib 2

这会在 GGUF 分片旁边创建 KIMI-K3-MXP4-DERISKED-Q2_K.expert-major.pack。它是一个独立的 GGML Expert Pack；已验证的路由专家 gate/up 用 Q2_K、down 用 Q3_K。

创建 SGLang 需要的模型元数据与清单。这个准备模式不启动服务：

__CODE__bash::python3 examples/runtime/kimi_k3/benchmark_kimi_k3_5090.py \
  --gguf /path/to/kimi-k3/KIMI-K3-MXP4-DERISKED-Q2_K-00001-of-00038.gguf \
  --max-new-tokens 200 --direct-io --read-splits 1 --prepare-only

它会在 ${XDG_CACHE_HOME:-$HOME/.cache}/sglang-expert-pack/kimi-k3/<fingerprint>/ 下创建 model-meta/ 和 kimi-k3-expert-pack.manifest.json。元数据目录里包含重写后的文本配置和复制过来的分词器文件。清单记录分片清单、张量布局、pack 索引、模型配置和分词器哈希。正常的基准运行还会额外生成统计 JSON、报告 JSON 和服务端日志。

<span style="color:#0F4C81;font-weight:bold;">启动 SGLang</span>

__CODE__bash::GGUF_DIR=/path/to/kimi-k3
PACK_PATH="$GGUF_DIR/KIMI-K3-MXP4-DERISKED-Q2_K.expert-major.pack"
ARTIFACT_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/sglang-expert-pack/kimi-k3/<fingerprint>"
MODEL_META="$ARTIFACT_DIR/model-meta"
MANIFEST_PATH="$ARTIFACT_DIR/kimi-k3-expert-pack.manifest.json"
STATS_PATH="$ARTIFACT_DIR/kimi-k3-expert-pack.stats.json"

python3 -m sglang.launch_server \
  --model-path "$MODEL_META" \
  --tokenizer-path "$MODEL_META" \
  --trust-remote-code \
  --load-format expert_pack \
  --model-loader-extra-config "{\"pack_path\":\"$PACK_PATH\",\"manifest_path\":\"$MANIFEST_PATH\",\"cache_vram_mib\":5120,\"cache_vram_reserve_mib\":1536,\"stage_slots\":16,\"read_splits\":1,\"direct_io\":true,\"stats_flush_interval\":92,\"stats_path\":\"$STATS_PATH\",\"verify_pack_sha256\":false}" \
  --tp-size 1 --ep-size 1 \
  --disable-cuda-graph --disable-shared-experts-fusion \
  --disable-radix-cache --mamba-radix-cache-strategy no_buffer \
  --disable-overlap-schedule --skip-server-warmup \
  --chunked-prefill-size 64 --watchdog-timeout 1800 \
  --max-running-requests 1 --mem-fraction-static 0.98 \
  --host 127.0.0.1 --port 30001

<span style="color:#0F4C81;font-weight:bold;">启动 llama.cpp 基线服务</span>

用 CPU 专家执行的方式启动固定版本的 llama.cpp 构建：

__CODE__bash::/path/to/llama.cpp/build/bin/llama-server \
  -m /path/to/kimi-k3/KIMI-K3-MXP4-DERISKED-Q2_K-00001-of-00038.gguf \
  -ngl -1 --cpu-moe --host 127.0.0.1 --port 8081 \
  -t 16 -tb 16 --threads-http 16 -np 1 -c 4096 \
  --no-warmup --metrics \
  --log-file /path/to/kimi-k3-llama-cpp/server.log

llama.cpp 客户端把同样的十个提示词发给 /completion，一次一个，使用 cache_prompt=false、temperature=0 和 n_predict=200。

## 10. 条件与限制

<span style="color:#0F4C81;font-weight:bold;">SSD 容量与准备时间</span>

Expert Pack 需要额外的 SSD 容量。PR 记录构建 DeepSeek-V4-Flash pack 约需 5 到 10 分钟，首次可运行约需 8 到 15 分钟。Kimi-K3 的 pack 构建在保留的测量中耗时 29 分 42 秒，首次就绪约 35 到 45 分钟。38 个 Kimi 源分片与生成的 Expert Pack 合计约 1.814 TiB；测量使用的是一块 TiPro9000 2TB 盘，而实际部署建议留出余量、使用 4TB SSD。

<span style="color:#0F4C81;font-weight:bold;">直接 I/O</span>

O_DIRECT 需要平台支持，并要求文件偏移、读取长度和用户缓冲地址都对齐。SGLang 在运行时初始化阶段采取失败即停的策略。如果平台不支持直接 I/O，或者 pack 不满足对齐约定，那就不应该把结果描述为直接 I/O 的性能。

<span style="color:#0F4C81;font-weight:bold;">缓存与负载</span>

<span style="color:#0F4C81;font-size:7px;line-height:1;vertical-align:middle;">●</span>&nbsp;GPU 缓存越小，未命中越多，SSD 读取与 H2D 传输就会更频繁地落在关键路径上。

<span style="color:#0F4C81;font-size:7px;line-height:1;vertical-align:middle;">●</span>&nbsp;提示词或负载分布的变化会改变热点专家，所以某个请求的热集并不保证适配所有负载。

<span style="color:#0F4C81;font-size:7px;line-height:1;vertical-align:middle;">●</span>&nbsp;如果完整专家池本来就装得进 GPU 显存，Expert Pack 只会多出一条不必要的数据路径，不是合适的部署模式。

<span style="color:#0F4C81;font-size:7px;line-height:1;vertical-align:middle;">●</span>&nbsp;如果负载由 GPU 计算主导，去掉主机内拷贝带来的收益可能被计算时间掩盖。

<span style="color:#0F4C81;font-size:7px;line-height:1;vertical-align:middle;">●</span>&nbsp;如果 SSD 的随机读行为、排队或热稳定性不佳，加大 read_splits 和中转槽位可能带来排队与内存压力，而不是吞吐提升。

<span style="color:#0F4C81;font-weight:bold;">当前功能边界</span>

这个特性聚焦于路由专家的 SSD 交付与 GPU 缓存。它不提供 SSD KV 缓存卸载，也不改变请求调度。它是一条需要显式开启的 Expert Pack 路径，不是对 SGLang 所有模型加载格式的全局替换。

## 11. 重新设计权重交付，而不是用慢盘换显存

SSD Expert Pack 不是简单地用更慢的盘替代 GPU 显存。它围绕 MoE 推理的稀疏访问模式重新设计了权重交付：

__CODE__text::router selects a small set of experts
  -> Expert Pack resolves their offsets
  -> O_DIRECT reads into aligned pinned buffers
  -> expert-level asynchronous H2D fills the GPU cache
  -> the complete expert becomes available for computation

去掉 page cache 到 pinned memory 的那次拷贝是一个容易被忽略的细节，但它是一处具体的端到端优化。传统路径先读到操作系统 page cache，再把负载拷进 CUDA 可用的 pinned 内存。有了直接 I/O，Expert Pack 直接把预分配的 pinned 缓冲当作读取目标，整段主机内存搬运和同步交接就此消失。

SGLang 正是这样把 SSD-LLaMA 的核心思想落到真实的 DeepSeek-V4-Flash 与 Kimi-K3 集成上：完整专家池留在高容量 SSD，有上限的 GPU 缓存保留当前工作集，运行时只搬运路由器选中的那些专家。超大 MoE 模型不再需要堆足够的显存或内存来装下整个模型，而是可以跑在一张消费级 GPU 加一块高速 NVMe SSD 上。

**把 MoE 的容量问题从显存挪到 SSD，真正的难点不在盘快不快，而在访问模式对不对。**Expert Pack 做的事说穿了很朴素：让每个专家在盘上变成一段可直接寻址、边界对齐的字节流。只有这样，O_DIRECT 才用得起来，缓存命中才真的能免掉一次读取。

最容易被忽略、收益却很实的一步，是砍掉 page cache 到 pinned memory 那次同步拷贝。它既不算 SSD 读取、也不算 H2D 传输，纯粹是主机侧多出来的一次读加一次写。去掉它，等于每次专家交付都少走一趟内存，顺带还避免专家负载把 page cache 冲掉。

对做本地推理的人来说，这套方案给出一条明确的分工：显存负责复用率，SSD 负责容量，中间的交付链路要围绕专家这个粒度来设计。反过来，如果专家池本来装得进显存，或者负载由 GPU 计算主导，那就不该套用这套方案。