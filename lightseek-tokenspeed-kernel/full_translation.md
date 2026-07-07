# TokenSpeed-Kernel：可移植 API 与高性能内核

## TL;DR

TokenSpeed-kernel 是一个独立的开源子系统，旨在解决 LLM 推理的后端复杂性。它引入了一套干净的、分层的 API 和注册机制，将高层 runtime 与底层的、硬件特定的内核代码解耦。

在这篇博客中，我们对 TokenSpeed-kernel 进行技术拆解，并展示它如何帮助开发者使用高性能内核进行多芯片（multi-silicon）LLM 推理。

## Introduction

LLM 模型和推理硬件正在以惊人的速度演进。高效地为这些模型提供服务，不再仅仅是找到一个快速的 attention 或 MoE 内核的问题；现代推理引擎需要跨模型、量化格式、GPU 代数和厂商后端快速移动，同时不把 runtime 变成一堆特例的迷宫。这些 API 是与平台无关、与解决方案无关的。

这正是 TokenSpeed-kernel 的动机：提供一套干净的分层 API，以实现最大化的结构化灵活性。kernel-runtime 接口保持通用，而内核开发者则获得足够的架构来为每个平台深度特化。

我们以 GPT-OSS 作为具体示例来展示这一设计在实践中的应用。无论平台如何，runtime 调用的都是相同的公开 TokenSpeed-kernel API；AMD 和 NVIDIA 路径的性能则来自这些 API 背后可插拔的内核。对于 AMD 的 GPT-OSS 120B，这种方法借助 Gluon 内核达到了顶级性能，说明这种分层设计并没有牺牲后端性能。

结果是一个清晰的分工：

TokenSpeed runtime 负责模型执行、调度元数据、页表和路由状态；
TokenSpeed-kernel 负责算子 API、后端注册、选择、数值计算、基准测试和性能分析；
特定平台的性能工作被局限在特定平台的内核中，而不是散落在模型代码里。

这种干净的分离还使得可以将 TokenSpeed-kernel 作为独立包发布，可以单独安装和使用（无论是整体还是按不同内核分开），而不仅仅作为一个纠缠在一起的 TokenSpeed 组件。我们的目标是让内核包对整个生态系统也有用：一套可移植且高性能、并带有通用公开接口的多芯片内核集合。这包括我们稍后将讨论的 Gluon 内核，因为 AMD 支持生态系统中的每一个人——一个健康的生态系统对 AMD 和社区都有利。

## Kernels in Modern Inference

内核决定了一个服务栈是快还是慢。attention、MoE 路由、专家 GEMM、通信、量化和采样都运行在内核上，而这些内核决定了整个系统的延迟、吞吐量和硬件效率。

困难在于，"最好的内核"很少是一个固定的答案。它取决于模型架构、张量形状、量化格式、GPU 代数、厂商库可用性、部署约束，以及一次调用是在服务 decode 还是 prefill 流量。随着时间的推移，引擎会累积各种路径来覆盖所有这些情况：树内内核、厂商库封装、实验性内核、架构特定的快速路径，以及历史遗留的回退方案。如果没有清晰的核系统以及围绕它建立的硬性边界，后端选择逻辑就会泄漏到模型代码和 runtime 代码中。

这种泄漏代价高昂。添加一个新模型可能需要触及无关的 runtime 路径。添加一个新的芯片目标可能意味着要把设备检查贯穿到模型各层。内核开发变得更加困难，因为模型行为、runtime 分发、后端选择和内核实现细节都被一个不清晰的边界纠缠在一起。

TokenSpeed-kernel 的设计就是要把这种复杂性集中在一个地方。

## Design Principles

内核系统围绕三条实用原则构建：

第一，多芯片支持必须是根本性的。内核系统应该直接理解平台能力，而不是把硬件检查当成零散的条件分支。同一个操作对不同的芯片目标可能有多种解决方案；所有方案都应该通过一个选择系统来竞争。

第二，可移植性和性能应该共存。一个新模型需要一条可移植的路径，以便尽快在不同的芯片目标上运行，然后可以逐步采用更高度优化的内核。TokenSpeed-kernel 保留了可移植的 Triton 路径以及面向性能的选择：AMD 用 Gluon，NVIDIA 用 CuteDSL，以及合适的厂商封装。

第三，快速的内核迭代需要护栏。当从想法到落地的路径很短时，内核开发就会很快。TokenSpeed-kernel 通过精简的依赖、独立的基准测试和性能分析来收紧这个循环，让被选中的内核可见。同样的结构也为 AI Agent 的内核开发提供了更清晰的工作边界：试一个内核、验证它、对它做基准测试、注册它，而无需重塑模型代码。TokenSpeed-kernel 也会主动审视那些让构建变复杂或阻碍迭代的依赖，在需要时裁剪或隔离它们。

这些原则导向了一个分层设计。

## The Layered Kernel System

在高层次上，分层内核系统如下图所示。从上到下，这个栈将 runtime 所请求的"做什么"与每个后端"如何执行"分离开来。runtime 通过一个通用的公开 API 进入，选择器将该请求映射到兼容的内核。

TokenSpeed-kernel 为那些在 LLM 推理中占主导地位的操作公开了 API：attention、MoE、GEMM、通信等等。Runtime 代码优先调用顶层 API，例如 mha_prefill、mha_decode_with_kvcache 和 moe_apply。这些 API 与平台和解决方案无关。一次 runtime 调用不会直接点名"AMD 内核"或"Triton 内核"。它描述的是算子问题：张量、格式、模型特征和执行的约束条件。然后 TokenSpeed-kernel 结合当前平台和已注册的内核特征来选择实现。

在底层，后端实现通过 @register_kernel 用一个共享的注册表注册自己。一次注册声明了算子族和模式、解决方案名称、平台能力需求、支持的张量签名、特征以及优先级。在 runtime 中，选择器过滤掉不兼容的内核，对剩余的候选排序，并返回要执行的可调用对象。

这种结构赋予了 TokenSpeed 两个难以同时获得的特性。首先，模型和 runtime 保持可移植性：它们不需要知道每个 GPU 后端的细节。其次，内核层保持高度特化：一个内核可以被限定到精确的架构、数据类型和张量形状。

同样的分层也让开发保持务实。一个模型可以在某平台上线最快时使用某个特定解决方案，然后随着路径扩展到更多芯片目标而转向公开 API。如果开发者想测试某条特定路径，他们仍然可以强制指定一个解决方案或内核覆盖，用于调试和基准测试。

## Registry and Selection Mechanism

这种灵活性背后的机制是"注册-选择"循环。公开 API 给 runtime 提供了一种稳定的方式来描述一次算子请求。内核注册则给每个后端提供了一种结构化的方式，来声明它能安全且高效地运行什么。选择器将两者连接起来。

在实践中，注册表是所有可用实现的唯一事实来源。每个已注册的内核都由元数据描述：它实现了哪个算子族和模式、属于哪个解决方案、需要哪些平台能力、支持哪些张量格式签名、哪些特征必须匹配，以及相对于其他候选它应该有什么优先级。

选择随后将一次 runtime 请求转变为一个可调用对象。公开 API 从算子输入和选项构建请求。对于 attention，这可能包括数据类型、头维度、页大小、滑动窗口行为和 attention sinks。对于 MoE，可能包括权重格式、激活类型、内部激活数据类型和专家并行约束。

选择器按平台能力、格式签名和特征过滤已注册的内核，然后对剩余候选排序。对于一个固定的模型、平台、数据类型和特征集合，选中的实现通常是稳定的，所以 TokenSpeed-kernel 会缓存已解析的可调用对象。开发者仍然可以强制指定一个解决方案或精确的内核用于调试和基准测试，但正常执行都走同一条注册表路径。

下面简化的注册代码片段展示了对于 NVIDIA 和 AMD 上 GPT-OSS 相关的 attention 路径，这些元数据长什么样。

## Numerics, Benchmarking, and Plugins

内核系统不仅仅是分发。它还为内核作者提供了一套安全、快速迭代的工作流：数值检查、独立基准测试和性能分析作用域。参考实现提供了一个共享的正确性目标，基准测试让内核在完整服务器之外有了计时和报告路径，而性能分析让选中的内核名称和关键参数在端到端的模型 trace 中可见。

同样的边界也支持树外插件。一个插件通过同一个装饰器注册内核，分配自己的优先级，并和树内实现一起参与正常选择。这让核心包保持干净，同时为硬件厂商、研究人员和部署团队留下空间，让他们带来特化的内核而无需 fork 整个系统。

对于日常的内核开发，这些工程上的便利和分发本身一样重要。这也是为什么这个包保持可 pip 安装且对依赖保持克制：特化的内核应该易于安装、验证、做基准测试和替换。

为了让这套工作流易于使用，TokenSpeed-kernel 为主要的开发任务同时提供 CLI 和程序化接口，涵盖数值验证和独立基准测试，如下图所示。它们可以用在 CI 任务或自定义调优流水线中。这些工具不是各自独立的零散测试台：它们复用了服务用于内核选择的同一个注册表元数据，因此一个已注册的内核可以针对参考实现进行验证，在标准或自定义形状上测量，可选地做性能分析，然后当它的能力和特征与 runtime 请求匹配时自动被选中。

## GPT-OSS 120B on AMD MI355X

GPT-OSS 120B 是验证这一设计的一个很好的初始目标，因为它是一个现代 LLM，但仍然可以在单张 GPU 上运行。这让实验保持务实，同时仍能锻炼对当前推理负载至关重要的内核系统部分。

GPT-OSS 同时给 attention 和 MoE 带来压力：它的 attention 路径使用带 attention sinks 的常规 MHA，以及滑动窗口和全 attention 层的混合，而它的大型 AMD 部署则为 MoE 使用 MXFP4 专家权重和 FP8 激活流。

这些正是如果内核边界太松就会泄漏进 runtime 的细节类型。TokenSpeed 把它们保留在公开 API 之下：

模型代码不需要知道 MI355X 架构细节、MXFP4 的 scale 应该如何在 CDNA4（MI355X 的架构）上排布，或者在某个特定的 prefill/decode attention 场景下哪个 AMD 内核最快。它只需要把正确的张量和元数据传递给公开 API。

## Gluon as the AMD Kernel Path

对于本文讨论的 AMD 路径，性能关键的 attention 和 MoE 内核是用 Gluon 实现的。Gluon 是一个 Triton 家族的 DSL，在暴露显式性能控制的同时，仍然保持了块级编程的简洁性。详见 "Gluon Tile Based GPU Programming with Low level Control" Triton 会议演讲。

对于 AMD MI355X，Gluon 让内核作者可以直接访问 CDNA4 特性，例如异步拷贝、共享内存布局，以及用于 FP8/MXFP 格式的 scaled MFMA（AMD 矩阵核）操作，还有高效的 buffer/全局内存操作。所有这些特性都是显式的编程原语，而不是隐藏的编译器优化：内核作者可以选择布局，例如简单的 BlockedLayout，或通用的 DistributedLinearLayout 来描述如何访问内存；用 SwizzledSharedLayout 或 PaddedSharedLayout 分配共享内存以避免 bank conflict；通过 AMDMFMALayout 选择 AMD 矩阵核布局。AMD 的 Gluon 模块暴露了与硬件紧密映射的操作，包括 mfma、mfma_scaled、buffer_load、buffer_store，以及异步的 global-or-buffer 加载到共享内存。

Gluon 还让软件流水线成为内核中显式的一部分，而不是隐式的编译器变换。一个内核可以分配多个共享内存缓冲区，为未来的张量块发出异步加载，并用 async_wait 控制这些块何时可见，然后为不同的调度方案在缓冲区之间轮转。这种控制级别对 decode 阶段的内核尤其重要，因为性能取决于隐藏内存延迟并让矩阵核保持忙碌，而不把流水线细节推入 TokenSpeed runtime。

## Attention

AMD 路径为 GPT-OSS 需要的 attention 变体注册了 CDNA4 Gluon 内核：prefill 和分页 decode，并为不同的变体提供了额外选项，例如是否使用滑动窗口、是否使用 attention sinks 等。注册特征让这些选择变得显式，所以 runtime 仍然请求 MHA，而内核系统选择匹配的 Gluon 实现。

内核实现使用了标准的 attention 技术，例如分块 QK/PV 和在线 softmax。它还使用了 CDNA4 特定的特性，例如用于矩阵乘法的矩阵核、用于 softmax 的打包数学指令，以及用于加载 K 和 V 块的 buffer load 指令。

该内核进一步利用了 LLM 中因果 prefill 的工作负载特征，设计了一个新的 persistent 内核，带有特殊的调度逻辑，以在 XCD 之间保持工作负载均衡。

当前的 Gluon attention 实现在 15 个被测 GPT-OSS prefill 形状中的 14 个上是速度最快的 MI355X 后端。在整个网格上，它比 Triton 基线快 1.4-2.3 倍。我们还通过将 AITER 作为厂商解决方案集成来评估 prefill 内核。在这个环境中，AITER 将 BF16 prefill 情况分发给它的 CK 支持的 MHA 路径，并带有一个包内的 Triton 回退。与 AITER 相比，Gluon 提供了 1.1-1.3 倍性能提升。

（attention prefill 吞吐量说明文字略）

## MoE

MoE 是分层设计变得更加有用的地方。一个 GPT-OSS MoE 层不是一个单一的稠密矩阵乘法。它包括将 token 路由到专家、聚集或分发 token 行、运行专家 GEMM、应用激活，以及用路由权重组合 top-k 专家输出。

AMD Gluon MoE 路径是围绕这个完整结构构建的，而不是把 MoE 当作两个孤立的 GEMM。runtime 看到的是一个 MoE 层的行为，而内核实现可以自由地一起调优这些阶段。

对于 prefill，关键挑战是在路由 token 在专家之间分布不均匀时，保持 CDNA4 计算单元（CU）忙碌。该实现使用 ragged block 调度，让工作跟随实际的专家分布，然后从逻辑 token 数和每个专家的切片大小中选择 tile 形状。大的 prefill tile 可以沿 M/N 或 N 拆分，工作被 swizzle 到 tile 组和 XCD 上，以便 scaled MFMA 工作更好地交错。权重路径也使用了对 CDNA4 友好的 MXFP4 scale swizzling，以及有助于内存访问的主机预混洗权重。

Decode 有不同的瓶颈：小批量受启动和路由限制，所以我们使用按批大小选择的两条路径。在最小批大小下，warp-decode 实现（最初受 "Better MoE model inference with warp decode" 博客启发）将 top-k 路由融合进 gate/up 投影，使路由和第一个 GEMM 共享一次启动。这里的限制是占用率：在途的 token 太少，无法填满机器，所以我们把它作为一个协作的多 warp GEMM 运行，通过共享内存以多缓冲区软件流水线来暂存 tile。对于中等批量，当足够的 token 共享一个专家以致一个已加载的权重 tile 在它们之间被复用时，我们切换到用于中等批大小的直接 grouped GEMM。这条路径通过共享内存暂存 tile，但使用单缓冲区直接加载调度而不是流水线，用流水线深度换取更低的寄存器和共享内存压力以保持高占用率；路由作为一个独立的小型融合内核运行。

通过上述方法，我们能够实现相对于 Triton 实现的巨大性能提升。在最小批大小下，Gluon 内核比 Triton 和 AITER 的 MoE 实现都有大幅提升：比 Triton 快 1.7-2.1 倍，比 AITER 快 1.1-1.6 倍。在中等 decode 区间，AITER 略微领先，但 Gluon 保持在最快速度的 0.9 倍以内，同时仍比 Triton 快 1.3-1.4 倍。这是我们持续改进的地方。

（MoE 延迟说明文字略）

跨内核变体，重要的主题是相同的：后端可以使用 CDNA4 scaled MFMA、软件流水线化的加载和计算、融合 SwiGLU、FP8 输出量化、bias 处理、scale swizzling、权重预混洗和 ragged 调度，而无需把这些选择推入模型代码。

## Multi-Silicon Support

上面讨论的是 AMD MI355X 上的 GPT-OSS。同一个内核 API 也支持 NVIDIA 路径。在当前 GPT-OSS Blackwell 配置中，attention 通过 FlashInfer 暴露的 TensorRT-LLM 封装使用 trtllm MHA 后端，MXFP4 MoE 使用 flashinfer_trtllm 解决方案。Runtime 仍然纯粹调用 mha_prefill、mha_decode_with_kvcache 和 moe_apply。

因此，多芯片支持不是两个无关的栈。AMD 和 NVIDIA 支持是同一个内核 API、注册表和选择模型背后的兄弟实现。特定平台的内核可以为每个芯片目标使用最好的可用后端，而 TokenSpeed runtime 为模型保持一致的执路径。

## End-to-end performance

下图展示了在 AMD MI355X 上测得的 GPT-OSS 120B 输出吞吐量性能。它比较了两种 TokenSpeed 配置：原始的、可移植的 Triton 支持的 attention 和 MoE 路径，以及优化的 Gluon 支持路径。在 20 个被测点中，Gluon 支持路径在每个输入/输出长度和并发设置下都提升了输出吞吐量。相对于可移植的 Triton 路径，加速范围从 1.6 倍到 3.6 倍。总体而言，这些关键的 Gluon 内核让 TokenSpeed 在 AMD MI355X 上的 GPT-OSS 120B 达到了有竞争力的性能。

（端到端输出吞吐量说明文字略）

结果突显了 TokenSpeed-kernel 设计的作用。这些增益不需要一条单独的、AMD 特定的 GPT-OSS 服务路径。相反，AMD 的性能是通过用特化的 Gluon 内核实现相同的公开 attention 和 MoE 契约、注册它们的平台和形状约束，并在请求匹配时让选择器分发给它们而获得的。这种分层设计在保持可移植基线的同时，缩短了优化周期：开发者可以捕捉重要的生产形状、为这些形状特化内核、用相同的数值和基准测试工具验证它们，并通过选择元数据将 runtime 路由到优化后的实现。

此外，得益于这一设计，AMD 上的这些优化内核也可以被 TokenSpeed 之外复用。我们将 AMD 特定的 attention 和 MoE 内核作为 tokenspeed-kernel-amd 发布，与 TokenSpeed runtime 分离，这样其他推理引擎可以在不依赖完整 TokenSpeed 服务栈的情况下采用它们。它已被 vLLM 采用。

## Conclusion

TokenSpeed-kernel 旨在让内核成为一等公民子系统，而不是一堆隐藏的快速路径。它的高层特性包括干净的公开 API、结构化的格式和特征元数据、集中化的注册和选择、可移植和特化的实现路径，以及插件支持。并非所有特性都已最终完成；我们正在积极地验证和改进它们。

收益不仅仅是更干净的代码。它改变了新硬件支持落地的方式。NVIDIA GPU 和 AMD GPU 在这个设计中都是一等目标。AMD 上的 GPT-OSS 120B 展示了这个模型在实践中的运作方式。随着推理在模型、格式和 GPU 代数之间变得更加异构，这一点变得重要。随着更多 TokenSpeed 模型迁移到公开的 TokenSpeed-kernel API，同样的机制将让它们更容易在 AMD GPU 上启动，并持续改进，而无需复制或切换 runtime 逻辑。

## Acknowledgements

这项工作建立在更广泛的开源推理生态系统之上，包括 PyTorch、Triton 以及许多其他持续提升服务系统和 GPU 内核水准的项目。

我们感谢 TokenSpeed 团队和 LightSeek Foundation 为这项工作背后的 runtime 和系统工作。我们也感谢 AMD 的合作和计算支持，使得 AMD 上的 GPT-OSS 120B 优化工作成为可能，并可以将益处扩展到整个社区。
