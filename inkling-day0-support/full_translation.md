目录

Inkling 模型架构

概览

短卷积（ShortConv）

带相对位置嵌入的注意力

带共享专家池（Shared-Expert Sink）的 MoE

SGLang 优化

ShortConv 优化

相对 logits 优化

共享专家池优化

功能支持

基于多层 EAGLE 的投机解码

基于 DFlash 的投机解码

Prefill-Decode 分离（PD Disaggregation）

AMD GPU 支持

LoRA 服务

Radix Cache 与 HiCache

多模态优化

性能结果

基于 Miles 的强化学习

支持 DP/PP/TP/SP/EP/CP 的 RL 训练后端

全参数 RL

面向训练-推理一致性的定制高效算子

面向共享专家池 MoE 的路由重放

Inkling 中的 LoRA 实现

仅同步适配器的端到端 LoRA RL

基于扩展对齐路由重放的多模态 LoRA RL

致谢

SGLang 与 Miles 为前沿多模态模型 Inkling 提供 Day-0 支持

我们很高兴与 Thinking Machines 团队达成合作，为 Inkling 在 SGLang 和 Miles 上提供 Day-0 支持——针对其全新架构做了专门优化，并具备广泛的功能覆盖；同时与 Modal 合作训练了 Inkling 的 DFlash 草稿模型。

亮点

Inkling 是一个 9750 亿参数（975B）的多模态模型，上下文窗口最长可达 100 万 token，融合了短卷积、注意力相对位置嵌入，以及 MoE 中的共享专家池。

在 Nvidia Blackwell GPU 上，SGLang 实现了最高 71.7k tok/s 的输入吞吐，以及 171.0 tok/s 的每用户解码速度。

SGLang 为 Inkling 提供了广泛的功能支持，包括投机解码、PD 分离、NVIDIA GPU 支持、AMD GPU 支持、LoRA 服务、Radix Cache/HiCache 以及多模态优化。

SGLang 支持基于 DFlash 的投机解码，使用一个由 Modal 专门为 Inkling 训练的草稿模型。

Miles 在定制的 Megatron 后端中实现 Inkling，支持 DP/PP/TP/SP/EP/CP，可同时做全参数和 LoRA 优化。

Miles 通过定制算子、路由重放以及跨运行时参数同步，保证训练-推理一致性。

SGLang 启动命令：Cookbook

Miles 启动命令：文档 · Miles PR：miles#1683

Inkling 模型架构

Inkling 在标准 decoder-only Transformer 架构基础上，集成了三个组件：短卷积、带相对位置嵌入的注意力，以及 MoE 中的共享专家池。

概览

上图展示了 Inkling 在注意力和 MoE 上的设计，两者都以同样的新方式收尾：在残差连接之前加一个短卷积（ShortConv）。注意力还会在 Q/K 归一化之前对 K 和 V 做短卷积，并把一个可学习的、由 query 条件化的相对位置偏置（RelLogitsProj）直接加进注意力 logits，取代位置嵌入。MoE 运行 top-k 路由，并带有共享专家池（Sink）。与传统共享专家 MoE 不同——后者在顶部叠加一条永远开启、独立于路由器的共享通路——Inkling 的路由器连共享专家也一起打分，并把它们的权重与选中的路由专家权重一起归一化，因此两者共用同一个权重预算。

短卷积（ShortConv）

短卷积是一种在 token 维度上、按通道的因果卷积。对于位置 t、通道 c 的隐藏状态，它读取当前 token 以及同一通道前 W−1 个位置。

当前 Inkling 配置使用 W=4。ShortConv 在每个 decoder 层中出现四处：

K 流 ShortConv——在 K 投影之后、Q/K 归一化之前。

V 流 ShortConv——在 V 投影之后。

注意力输出 ShortConv——作用于注意力的输出。

MLP/MoE 输出 ShortConv——作用于 MLP/MoE 的输出。

带相对位置嵌入的注意力

在 Inkling 中，每个注意力层都把可学习的、按头的相对位置偏置直接加进 softmax 之前的 logits。除 qt,h、kt,h、vt,h 之外，每个 query token 还携带一个相对特征 rt,h，通过可学习的投影 P 映射到按因果距离分桶 d（从 0 到 rel_extent−1）索引的相对 logits 向量：

对于 query i、key j、head h，注意力 logit 在缩放点积上直接加上一个相对位置偏置，该偏置由 query 的相对 logits 按相对距离选取：

其中 α 是注意力缩放因子。因果掩码照常处理未来位置；在 full attention 中，超出 rel_extent 的距离只贡献零偏置。

注意力布局。Inkling 在同一栈中混合滑动窗口层和 full-attention 层——两种变体都用相对注意力，只是掩码不同。默认布局是每五个滑动窗口层后接一个 full-attention 层（layer_id mod 6 = 5），既给模型廉价的局部层，又周期性地提供 full-context 层来处理长程信息。full-attention 层还额外支持对 qt,h 和相对 logits 施加与长度相关的 log 缩放因子，让模型随上下文增长调节 logit 幅度；局部层窗口大小固定，不需要这一机制。

带共享专家池的 MoE

Inkling 的前馈模块是标准的 sigmoid-gated top-k MoE——路由器打分、top-k 选择、对选中专家做归一化权重——唯独一处例外：它如何并入两个共享专家。多数共享专家 MoE 设计是在顶部叠加一条独立的稠密通路，即永远开启、从不与路由器竞争概率质量的专家。Inkling 则把路由专家**和**共享专家**一起**打分：top-k 选择仍只从路由专家池里挑，但一旦选定，被选中路由专家的得分就与共享专家得分拼接、作为单一组一起重新归一化：

随后两组权重各自缩放其专家输出，并求和到同一结果中。

SGLang 优化

Inkling 的三处架构改动，每一处都打破了标准 decoder-only 推理服务所依赖的假设。要让 Inkling 在 SGLang 上跑得快，就得为每一处都上新算子和执行策略。

ShortConv 优化

ShortConv 本身很小——如上文所述，是一个 W=4 的按通道因果滤波器——但它在注意力内部（K、V）出现两次，在残差流周围（注意力输出、MLP 输出）也出现两次，贯穿 Inkling 的每一个 decoder 层。

KV ShortConv + QK-norm + KV 存储。K 流和 V 流的 ShortConv 紧挨在 Q/K 归一化和 KV-cache 写入之前。SGLang 把这三步——K/V 卷积、Q/K RMSNorm、KV-cache 写入——融合进一个 attention-prologue 内核。

All-reduce + ShortConv（+ 解码时的 RMSNorm 与残差）。注意力输出和 MLP 输出的 ShortConv 位于残差流上，正是张量并行 all-reduce 已经运行的位置——而 all-reduce 本身就很昂贵。SGLang 构建了一系列定制 all-reduce 内核来削减这部分开销，比 torch 的 multimem_all_reduce_ 最高快 **2.1×**。由于 ShortConv 紧接在 all-reduce 之后，SGLang 把它直接融进 all-reduce 内核，而不是单独发起。对解码而言，RMSNorm 和残差加法也折叠进同一个内核，因为解码的单 token 形状让这些额外步骤变得廉价。这个融合内核比未融合链快 **2.08–3.60×**，在输入长度扫描中带来端到端吞吐 **+5–8%** 的提升。

Prefill 全 CUDA 图。Breakable CUDA graph（BCG）和 piecewise CUDA graph（PCG）是削减 prefill 期间 CPU 启动开销的标准做法：把前向传播的大部分一次性捕获，之后重放时不再每步重新派发 Python。但凡是算子需要实时按请求元数据的地方，两者都仍须回退到 eager 执行；而 Inkling 每层有四处 ShortConv 站点正是这种情况，此外注意力自身也有。每个站点的 eager 回退都是一次真实的、多层级 Python 调用栈，而非单次内核启动：

在约 66 层、每层这么多 eager 工作的情况下，BCG 和 PCG 仍会留下真实的 CUDA 气泡——即 CPU 处理未捕获段时 GPU 的空闲时间——在小批量、中等上下文形状下最明显，因为此时 CPU 派发与 GPU 内核在时间上相互竞争。

全 CUDA 图捕获把那些气泡消除掉：它把整个前向（含 ShortConv）捕获进一个图，该图的大小限定为有限个数的请求槽（full_prefill_max_req），因此重放只刷新缓冲区内容，而不再重新派发任何 Python。全图 prefill 吞吐在大型形状下与 BCG 大致持平，在受启动限制的形状下领先 BCG **+14–17%**。

分片 ShortConv。注意力输出和 MLP 输出的 ShortConv 位于残差流上，所以不分片的话，每个张量并行 rank 都会以全宽度冗余地计算和缓存它们。SGLang 转而提供一种分片策略：对部分和做 reduce-scatter，让每个 rank 只持有自己的隐维度分片，针对相应的分片缓存本地运行 ShortConv，再通过 all-gather 把结果汇总回全宽度。这释放了 GPU 显存，但 reduce-scatter/all-gather 往返是在普通 all-reduce 之上的额外通信，在解码的小步长下开销大于收益——因此它是一个可选策略，而非默认。

相对 logits 优化

剪裁偏置（Sheared-bias）内核。相对偏置项必须加在注意力内核内部。Inkling 的 FlashAttention-4 集成支持两种等价做法：一种是 score-mod 路径，每个注意力 tile 在它的 score 回调里计算 i−j 并即时查表 rel_logits；另一种是 sheared-bias 路径，相对 logits 预先被剪裁（shear）进一个按列对齐的偏置张量，

这样内核就能用普通的 tile 加载来加偏置，而不用逐个 score 做索引。剪裁布局更快，但需要 Inkling 专用的 FA4 分支，且 tile 对齐和 padding 约定要匹配——这也是 Inkling 默认采用的路径。它也是注意力栈中唯一一处内核调度按缓冲区身份而非内容缓存的地方，所以任何跨调用复用该缓冲区内存的做法——包括 CUDA 图重放——都必须确保缓存被刷新，而不是被静默复用。

双流重叠。rel_logits 投影——通过 P 把 r 变成 rel_logits——只依赖融合的 QKVR 投影输出，而不依赖 attention-prologue 内核对 K 和 V 所做的 ShortConv/QK-norm 工作。SGLang 把它放在与那个 prologue 不同的 CUDA 流上运行，从而与卷积/归一化重叠，而不是串行地排在它后面。

MXFP8 支持。用 MXFP8 而非 bf16 存储 K/V，KV-cache 容量大约翻倍，而 Blackwell 原生运行 MXFP8 矩阵乘的吞吐也高于 bf16。FA4 分支非对称地应用这一点：Q@Kᵀ 作为原生 MXFP8 MMA 运行，而 P@V 保留在 bf16 以保护精度，对 V 做即时反量化，使这个额外步骤与既有的 load/MMA 调度重叠，而非花费单独一遍。把 MXFP8 量化直接融进同一个 attention-prologue 内核，而非单独的量化-存储步骤，把开销压到约 4.7–4.8 µs——在 bf16 基线的约 14% 以内——同时拿到 KV-cache 的显存收益。

共享专家池优化

Top-k。上文所述的共享池 MoE 门控是 sigmoid + 偏置 top-k 选择，随后对选中的路由得分和共享得分做联合 logsigmoid 重归一化——这一串若不分融，会串联一个 sigmoid+bias 算子、一个 top-k 算子和一个 renorm 算子。一个融合的 Triton 内核把整串收拢，在真实 token 数下比未融合链快 1.6–5.6×；一个针对形状特化的 CUDA-JIT 版本更进一步，例如在 T=4096 时 **7.72 µs 对未融合链的 26.15 µs（3.4×）**，在 T=16384 时 **20.09 µs 对 52.88 µs（2.6×）**。

共享专家融合。共享池的数学（路由和共享得分共用一次归一化）意味着共享专家作为一个完整的张量并行稠密块运行。每个 token 都会访问每个共享专家，所以把专家轴保留为批维度只会产生额外工作：直接实现会复制输入、在专家轴上跑批处理 GEMM、为每个专家物化一个输出，再把这些输出求和。

我们转而把专家轴融合进矩阵维度。gate/up 权重沿输出维度堆叠，down 权重沿输入（归约）维度拼接。我们把得到的二维权重表示称为**线性化布局（linearized layout）**：「linearized」指的是把专家维度折叠进两个稠密 GEMM；它们之间的 SwiGLU 仍是非线性的。它的 down GEMM 在自己的归约中就完成了专家求和，从而消除了被复制的输入、逐专家的临时结果以及单独的一次求和。

在 B200 W4A16 服务下，专家融合把输入吞吐提升 5.8–11.1%，并把 TTFT 降低 5.5–10.0%（BS1–32）。H200 输入吞吐提升 2.2–4.5%，解码吞吐则保持稳定。

功能支持

基于多层 EAGLE 的投机解码

Inkling 自带八层串联的 MTP（multi-token-prediction）层用于投机解码——不是把一个草稿头重放八次，而是八层各自拥有自己的权重，每层对应一个草稿深度，每层消费上一层的输出。它们共同构成一种 EAGLE 式的递归：一次目标前向产生一个隐藏状态，该链把它向深处扩展八个 token，目标在单次前向中验证全部九个位置。草稿层共享目标的嵌入和去嵌入——SGLang 在所有层之间别名（alias）同一份拷贝。

整条链一张 CUDA 图。基线设计每步草稿重放一张图，步骤之间用 Python 来采样一个 token、把它旋转进下一步的输入、并重建注意力元数据——每轮八次图启动、七个主机空隙。SGLang 转而针对每个批大小把整条链捕获进一张 CUDA 图：全部八个草稿前向、token 旋转、逐步的注意力元数据，以及采样本身，背靠背录制，中间没有 Python。这能成立，是因为该链跨步形状不变、且采样是图安全的（每次重放抽取新的随机性）；草稿窗口是固定宽度的，所以一个接受了 2 个 token 的请求和一个接受了 7 个的请求重放的是同一张图。一个融合内核从验证输出喂入这张图，取代了主机过去在验证和草稿之间发出的约 20 次小拷贝。

分布精确拒绝采样。在温度为 0 时，验证步通过匹配目标的 argmax 来接受。在温度 > 0 时，Inkling 服务支持真正的投机拒绝采样（--speculative-use-rejection-sampling）：以概率 min(1, p_k(X_k)/q_k(X_k)) 接受草稿 token X_k，被拒时从残差分布重新采样，从而精确保留目标分布，而非用接受阈值去近似。于是验证步需要每一步完整的草稿分布 q_k，而不只是采样出的 token——所以被图录制的链一边走一边把每步的概率存进一个持久的 [bs, 8, vocab] 缓冲区，验证内核再按链顺序对照这个存储走一遍 token。

无同步的解码轮。以上所有环节被缝合起来，使解码循环完全重叠地运行：在整个一轮——草稿链、验证、以及它们之间的粘合——之中，SGLang 完全不发出设备同步。主机始终跑在 GPU 前面，连续阶段的内核背靠背流动，流水线从不停 drained。

基于 DFlash 的投机解码

SGLang 还支持基于 DFlash 的投机解码——DFlash 是一种独立的草稿架构，而非串联在目标之上的层。一个 DFlash 草稿作为自己的模型、带着自己的 KV cache 运行，在一次前向中填充满一个被掩码的未来位置块，而不是自回归地一步步走；它借用目标的嵌入和 LM head，而非自己训练，目标在单次线性（非树）前向中验证整个块。我们与 Modal 团队合作训练了 Inkling 的 DFlash 草稿模型，给 Inkling 服务提供了第二条投机解码路径（--speculative-algorithm DFLASH），与上述原生的多层 MTP 链并列。

Prefill-Decode 分离

Inkling 有三种异构状态类型：full-attention KV、滑动窗口 KV，以及 ShortConv 卷积状态。三者都需要从 prefill 节点传到 decode 节点。这个三组件池原本就是为混合 SSM-注意力模型而建，Inkling 的卷积状态正好契合同一套基础设施，所以分离路径上不需要新的传输逻辑。SGLang 的 UnifiedRadixCache 是所有状态类型的统一抽象；分离层、HiCache 和投机解码都通过这一个接口在三个组件上组合。

AMD GPU 支持

SGLang 通过给 Triton 注意力后端新增的一个通用 score_mod 接口，在 AMD MI35X 上支持 Inkling。该接口在编译期把一个调用方提供的 score 修改函数内联进 extend 和 decode 内核，因此 Inkling 的相对位置嵌入能在 ROCm 上工作，而不需要 NVIDIA 专用的 FlashAttention-4 路径。再结合额外的算子适配和 aiter MoE runner 集成，Inkling 在 MI35X 上以 --attention-backend triton --moe-runner-backend aiter 端到端运行。

LoRA 服务

对于一个投影 y = Wx，LoRA 让基础权重 W 保持不变，并加上一个低秩更新：

A 把 token 从模型维度缩到秩 r，B 再把它扩回。Inkling 把这些更新应用到注意力、稠密 MLP、专家和输出投影上，因此若在每个基础 GEMM 之后执行更新，会把许多小的低秩操作变成暴露的延迟。

SGLang 转而使用双流调度。主 CUDA 流运行基础模型，而一条 LoRA 侧流计算每个 token 所选适配器的秩 r 工作。两条流只在需要 delta 的地方同步；融合 join 内核在施加周围激活的同时展开并加上 delta。例如在 MLP 中，gate/up 的收缩与它的基础 GEMM 重叠，在流于某处汇合之前：

down 投影的基础和秩 r 路径随后走向第二次 join。专家层复用基础模型的路由元数据，而不是对 LoRA 更新再做一次路由。选择不同 LoRA 的请求留在同一次启动中：一个按 token 的适配器映射选出合适的 A 和 B 因子，而不按适配器拆分批。

即便一个批里包含多个不同 LoRA，结果也始终接近无 LoRA 基线。下表报告的是 TP8 输出吞吐（输入 8192 / 输出 1024，开启对称内存，无投机解码）；单 LoRA 行使用 --max-loras-per-batch 1，4-LoRA 行使用 --max-loras-per-batch 4 并在批中放 4 个不同适配器：

在 BS4 下从一个不同 LoRA 切到四个，在 B200 上仅损失 0.9%。

Radix Cache 与 HiCache

在共享前缀的请求之间复用 KV cache，是 LLM 服务中最高效的优化之一，尤其对多轮和长上下文工作负载。SGLang 的 radix cache 通过把共享前缀组织成 radix 树来捕获它，HiCache 则把这棵树按内存分层（L1 GPU HBM、L2 主机 DRAM、L3 磁盘或远程存储），于是当工作集超出 HBM 时，从 GPU 逐出的前缀会从更廉价的层重新加载，而非重新计算。Inkling 让两者都变复杂了，因为它并不呈现前缀缓存所假设的那种单一同质注意力 KV 池。它大多数层用滑动窗口注意力（SWA），而它的 ShortConv 分支保留一个小的按请求卷积状态，SGLang 把它存进为循环式 Mamba/SSM 层建的池里——尽管 Inkling 根本没有 SSM。

SGLang 为每条轴准备了独立的 radix cache：一个 full-attention 的 RadixCache、一个用于滑动窗口逐出的 SWARadixCache、一个用于循环状态的 MambaRadixCache。一个同时动用多条轴的混合模型需要把它们协调到一棵树上，SGLang 的 UnifiedRadixCache（#20415）正提供了这样一棵树——它覆盖类型化组件（FULL、SWA、MAMBA），并原生支持其上的 HiCache，而非每个变体各实现一遍。

Inkling 直接接入这条路径。它注册一个三组件池，统一缓存选择一种组合的 SWA + Mamba 栈策略，在单一缓存控制器背后为全部三个组件（full KV、SWA KV 和卷积状态池）构建出一个主机栈。因为集成是统一缓存原生的、而非定制的旁路，Inkling 就继承了 HiCache 的分层复用，并能与服务栈的其余部分组合，包括投机解码。

多模态优化

SGLang 把图像预处理中计算密集的部分（分块化 patchification、归一化、内容哈希）卸载到一个原生 Rust 扩展，该扩展在服务进程内无 GIL 运行。这支持多图并行，并把哈希计算移出调度热路径，使图像密集负载的 TTFT 降低 14–44%、服务吞吐提升约 20%。该扩展围绕一个可扩展的处理器接口构建，目前支持 Inkling。

性能结果

我们在 B200 节点上对 Inkling 做端到端基准测试，在固定序列形状（输入长度 8192、输出长度 1024）下扫描批大小，全程开启 TP=4 与 TP=8、对称内存和 CUDA 图。

左图描绘了两种张量并行规模下的吞吐–交互性帕累托前沿：沿任一曲线移动，都是通过接纳更多并发请求，来在每用户解码速度（交互性）和每 GPU 聚合吞吐（每秒每 GPU 服务的输入+输出 token 总量）之间做权衡。在 TP=8、批大小 1 时达到 171.0 tok/s/用户；批大小 32 时达到 71.7k tok/s 的聚合输入吞吐。右图显示两种张量并行规模下，token 间延迟（ITL）在批大小 8 之前都停留在个位数毫秒，直到批大小进入 30 多才升到十毫秒量级。

基于 Miles 的强化学习

Miles 通过覆盖全参数和 LoRA 优化、横跨 DP/PP/TP/SP/EP/CP 的 Megatron 后端，为 Inkling 提供 Day-0 RL 支持。为保持训练-推理一致性，该后端把定制的相对注意力、ShortConv 和 FP32 MoE 算子与 rollout 路由重放结合在一起，在文本和媒体扩展后的序列上都重放共享池 MoE 路由。在此基础之上，原生 LoRA 覆盖 Inkling 的注意力、稠密 MLP/MoE 和 LM-head 投影，并只同步适配器；多模态流水线则支持图像和音频输入。我们用 975B 全参数 GRPO、文本 LoRA 以及视觉-语言 LoRA 验证了完整的 RL 流水线。

完整的 Inkling RL 实现见 Miles pull request #1683。可直接使用的 Inkling 镜像通过 docker pull radixark/miles:inkling 获取。

支持 DP/PP/TP/SP/EP/CP 的 RL 训练后端

Miles 把 Inkling 实现为一个原生 Megatron 模型。该后端重建了 Inkling 的局部与全局相对注意力、四条残差短卷积路径、稠密到 MoE 的层调度、共享池路由器和专家，以及图像和音频编码器，全部作为可微的 Megatron 模块。它支持 Inkling 训练配方用到的全部六种并行维度：

DP。在副本间分发微批并同步梯度。

PP。跨流水线阶段切分 Transformer 层。

TP。切分融合的 q/k/v/r 和输出投影，k/v ShortConv 对齐到局部头。

SP。切分残差 ShortConv 路径，同时保留因果上下文。

EP。切分路由专家及其可训练状态。

CP。使用连续的 all-gather：q 和 r 保持局部，而 k 和 v 以全局偏移做 gather 以用于相对注意力。

一个 Inkling 模型桥接器双向处理 checkpoint 转换：它把发布的 Hugging Face 权重切分用于 Megatron 训练，再重建 checkpoint 导出和 rollout 权重更新所需的布局。同一个后端驱动全参数和 LoRA RL。

全参数 RL

基于上述原生 Inkling 后端和并行栈，Miles 通过更新每一个模型张量来运行全参数 GRPO。在每次迭代中，SGLang rollout worker 生成轨迹并记录 R3 所需的路由专家 ID。Miles 的训练 rank 消费这些轨迹，重放路由决策，并施加全模型更新。随后模型桥接器把更新后的分布式分片转换成 SGLang 的张量布局，并以有界桶流式把下一版策略送回，用于后续 rollout。

在单个 GB300 机架有限的 GPU 显存容量内，完整策略、梯度和 FP32 优化器状态会带来额外显存压力。因此 Miles 在受限的 GPU 工作集与节点本地 NVMe 之间流式传输 Megatron DistributedOptimizer 状态。这种 GPU–磁盘卸载改变的是存储位置，而非优化器更新（miles#1575、torch_memory_saver#80、Megatron-LM#63）。

我们在 12 个节点、每节点 4 张 GB300 GPU 上运行 Inkling 975B 全参数 GRPO。训练用 DP2/PP3/TP4/EP8，rollout 用 TP8/EP16。该运行使用全局批大小 32、GRPO 组大小 8、最大回复长度 4K（截断）。它开启路由重放，并用 Adam、学习率 10⁻⁶。我们在 DAPO-Math-17K 上训练，在 AIME25 上评估。训练-rollout KL 保持在约 10⁻³，而原始奖励和 AIME25 评估都稳步提升。

面向训练-推理一致性的定制高效算子

训练-推理一致性是 RL 中一项核心的正确性要求：训练器必须评估生成 rollout 的那个相同策略，即使训练和推理服务走的是不同的分布式执行栈。保持一致很难，因为同一份 checkpoint 在算子、累加精度、打包序列边界或归约顺序不同时，可能产生不同的 token 概率。Miles 从定义 Inkling 前向传播的算子层面解决这种错配，同时提供分布式训练所需的反向实现。

相对注意力。融合投影产生按 token、按头的特征 qi,h、ki,h、vi,h 和 ri,h。Miles 采用与 SGLang 相同的固定相对投影 P 和注意力 logit 定义：

这里 b(i,j,h) 按上面相同的因果距离规则选取 rel_logits(i,h,i−j)。

Miles 为 Inkling 提供三种训练侧注意力后端：FlexAttention、FA4 和 Transformer Engine，默认用 FlexAttention。每次前向先计算紧凑的相对 logits rP。Miles 用一个定制的 CUTE 内核实现相对分数修改，在每个注意力 tile 内按相对距离索引 rP，并在不物化稠密逐 token 偏置矩阵的情况下保留 SGLang 的因果或滑动窗口规则。Miles 为每个注意力几何形状准备并缓存 score 修改器和块掩码，把它们的构建开销摊销到重复的打包序列形状上。

FlexAttention 通过对注意力分数和 ri,h 两者提供可微前向和反向，而 P 保持冻结。在 GB300 上、8K 打包序列、相对范围 1024 时，它比 Transformer Engine 参考实现约快 5×、峰值显存约少 5×，同时在 BF16 数值噪声范围内与之匹配。FA4 仍作为优化替代可用，Transformer Engine 作为参考后端。

短卷积。Inkling 对 k 和 v 流、注意力输出和 MLP 输出施加残差因果 ShortConv。Miles 用定制的 Triton 前向和反向内核实现这个算子，把深度因果卷积与残差路径融合。内核以 FP32 累加、最后加残差，复现 SGLang 在转回模型 dtype 之前的算术顺序。对打包序列，Miles 预计算每个 token 段的起止：前向内核在段起点之前掩掉左上下文读取，反向内核则掩掉段终点之后的梯度读取，防止状态或梯度跨越样本边界。在序列并行下，Miles 在 ShortConv 之前 gather 完整序列上下文，再把对应的输出和梯度分片返回给每个 rank。

FP32 MoE 激活与组合。Inkling 的共享池 MoE 对门控激活和加权专家归约中的舍入都很敏感。Miles 用 FP32 执行这两个阶段。一个定制的可微 Triton SwiGLU 内核在单次转回模型 dtype 之前执行激活和逐 token 共享专家缩放；专家输出随后在 FP32 中累加，遵循 SGLang 的求和顺序，并在组合后转回一次。这使连续的专家计算在训练和 rollout 间对齐，补足了 R3 提供的离散路由对齐。

面向共享专家池 MoE 的路由重放

除了定制精度对齐算子，Rollout 路由重放（R3）对 MoE RL 的训练-推理一致性同样重要。一个靠近 top-k 边界的小数值扰动，可能改变被选中的专家，从而改变计算图本身。SGLang 在 rollout 期间记录路由的 top-k 专家 ID，Miles 在训练前向中复用这些 ID。

对 token t，设 e1,…,ek 为被重放的路由专家。Miles 重算它们当前的路由器得分，并放在所有常开共享专家得分之前：

所有项随后使用同一个公共归一化：

前 k 个权重属于被重放的路由专家，其余 Ns 个权重属于共享专家。这里 c 结合了 Inkling 配置的路由缩放和学习的全局缩放。R3 只重放专家 ID；Miles 从当前路由器重算连续权重，所以梯度仍流经路由和共享权重。实现上对一个 log-sigmoid 得分做 softmax 以保证数值稳定。截断重要性采样处理专家子图对齐后残留的概率漂移。

第二个 Inkling 特有的适配是多模态索引。SGLang 在图像块和音频特征把 prompt 扩展之后才记录路由，所以 Miles 用的是引擎报告的扩展后长度，而非原始文本 token 数。随后该 trace 用与训练批相同的打包序列和序列并行布局做 padding 和切片，再注册到每个 MoE 层。

Inkling 中的 LoRA 实现

Inkling 发布的 LoRA schema 覆盖注意力、稠密 MLP、MoE 和 LM-head 投影。Miles 在 Megatron 中原生实现同样的结构，包括 TP/EP 感知的执行和直接向 SGLang 的导出，因此 RL 只更新适配器，基础模型保持冻结。

对每个被适配的线性层，基础权重 W 保持冻结，Miles 只训练低秩因子 A 和 B：

Inkling 特有的挑战是，如何跨它异构的注意力、稠密和专家投影高效地施加这个标准更新。

Inkling 的路由专家使用共享外层分解，而非为每个专家配一对独立的因子。对 w1 和 w3，A 在专家间共享，而专家特定的 B 张量遵循 EP 分片。对 w2，专家特定的 A 张量被分片，B 共享。

令 C 索引所有被适配的投影。它们的低秩因子构成可训练的适配器状态

以 Θ0 表示冻结的基础模型，迭代 t 时的策略为

GRPO 把 Φt 更新为 Φt+1，而 Θ0 保持不变。在下一次 rollout 之前，Miles 只同步 Φt+1；基础权重在两个运行时都保持驻留。

仅同步适配器的端到端 LoRA RL

图 9 展示了一个完整的 LoRA RL 迭代。沿上方路径，SGLang 返回采样的 token、rollout 对数概率、奖励和掩码，以及 R3 所需的路由专家 ID。Miles 评估同一 token 序列，在每个路由器注入被记录的专家 ID，并且只对方适配器求导。在 MoE 层，低秩分支消费已经派发好的专家-token 缓冲区，复用基础模型的专家分组，而不是对 LoRA 更新单独做路由。专家特定因子遵循 EP 分片，而共享外层因子被复制、其梯度在 EP 组内做 reduce。

优化器步之后，Miles 直接从分布式训练状态物化出一个可服务的适配器。导出器不是每个张量发一次集合通信，而是把请求的 TP 和 EP 分片打包，对每个并行组做一次扁平的 all-gather。然后它重建 Inkling 的 SGLang 布局：融合投影分片按服务顺序拆分并拼接，专家张量回到专家主序，并去掉 padding 的 LM-head 行。结果是一组连续的 BF16 张量，名字和形状与 SGLang 消费的完全对应。

下方路径在不经过主机内存暂存适配器载荷的情况下完成版本切换。Miles 暂停生成、刷掉引擎缓存、把命名的 GPU 张量序列化为 CUDA IPC 句柄，并把每个载荷发给共享该 GPU 的、同置的 SGLang worker。SGLang 卸载上一个适配器，然后在一次调用中加载完整的下一版并切分进服务布局，再恢复生成。冻结的基础要么在 rollout 侧保持驻留，要么在迭代适配器更新前同步一次；后续步骤只传适配器。发布的 Inkling 适配器以 safetensors 格式支持热启动，而原生的按 rank 适配器 checkpoint 保留优化器和调度器状态以支持精确的训练恢复。

使用与全参数运行相同的实验设置，LoRA GRPO 把训练-rollout KL 保持在 10⁻³ 量级，而原始奖励在约 450 步内稳步提升。仅同步适配器把权重更新延迟从 49.4 秒降到 2.5 秒，即 **20×** 加速；而把反向和优化器工作限制在适配器上，把训练步时间降到全参数训练的 85%。

基于扩展对齐路由重放的多模态 LoRA RL

Inkling 是 Thinking Machines Lab 发布的强大多模态模型，原生支持文本、图像和音频输入。Miles 把这些模态的 RL 后端都扩展到了：全参数和 LoRA 配方都接受结构化的多模态 rollout，在 Megatron 中执行 Inkling 的视觉和音频塔，并在媒体扩展后的序列上保留路由重放。

图 11 展示了核心的数据变换。Miles 保留原始的结构化消息列表，直到 Inkling 专用的渲染器发出模型的角色和内容标记，并为每个图像或音频项发出恰好一个哨兵（sentinel）。处理器检查哨兵计数是否与提供的媒体匹配，然后为每个项记录 p 个图像块或 f 个音频 d-mel 帧。训练前，Miles 把一个图像哨兵替换成 p 个词表内占位位置，把一个音频哨兵替换成 f 个位置，同时记录必须插入对应媒体嵌入的样本局部位置。

SGLang 在这次扩展之后才做 MoE 路由决策，所以 R3 trace 包含每个扩展位置的专家 ID，而不仅仅是渲染后的文本序列。Miles 用文本长度加上记录的媒体扩展来验证 trace 长度，在打包前扩展 token 序列，并用与训练 token 相同的布局对 R3 做 padding 和切片。因为媒体哨兵出现在 prompt 中，回复的对数概率和损失掩码保持不变。在批处理时，记录的样本局部媒体位置被移入打包后的全局序列；Megatron 的视觉和音频塔编码块和 d-mel 张量，并把它们的嵌入散布进恰好那些位置。在序列并行下，每个 rank 选取落在其局部序列分片中的位置。

在多模态 LoRA RL 中，当前生产配方冻结视觉和音频塔，在它们的嵌入周围训练语言模型适配器或基础模型。训练媒体塔作为实验性选项可用。

为验证多模态 RL 配方，我们在 Geo3K 上选用视觉-文本设置，把数据集拆成训练和评估子集，并保持并行配置和优化超参与前面的 LoRA 实验一致。该运行在视觉数学 prompt 上演练了相同的 LoRA 执行、路由重放和适配器同步。Geo3K 评估从约 0.54 升到 0.58，而训练-rollout KL 在整个训练中都保持在 10⁻³ 量级。同一条多模态路径也支持音频输入、全参数训练和分布式执行。

致谢

本工作是 SGLang & Miles 团队与 Thinking Machines Lab 的合作成果。

SGLang & Miles 团队：Ke Bao, Cheng Wan, Chunan Zeng, Zhichen Zeng, Yanbin Jiang, Yuhao Yang, Qiaolin Yu, Mao Cheng, Yi Sun, Mingyi Lu, Haoguang Cai, Banghua Zhu, Ying Sheng

Thinking Machines Lab：Aurick Qiao, Paul Zhang, Shenxiu Liu