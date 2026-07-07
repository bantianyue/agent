<div style="background:#e8f4fd;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:18px;">
<div style="text-align:center;margin-bottom:10px;">
<strong style="font-size:16px;color:#1a6ba0;">要点速览</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
- <strong>问题</strong>：现代推理引擎要同时适配多种模型、量化格式、GPU 代数和厂商后端，内核选择逻辑很容易泄漏进模型代码和 runtime，越堆越乱。<br><br>
- <strong>解法</strong>：TokenSpeed-kernel 用一套分层 API 加注册-选择机制，把高层 runtime 与底层硬件特定内核解耦，runtime 只描述"算子问题"，由选择器挑实现。<br><br>
- <strong>性能</strong>：在 AMD MI355X 上跑 GPT-OSS 120B，Gluon 内核的 prefill 比 Triton 基线快 1.4-2.3 倍，端到端输出吞吐量比可移植路径高 1.6-3.6 倍。<br><br>
- <strong>生态打法</strong>：AMD 专用内核被单独拆包发布为 tokenspeed-kernel-amd，已能被 vLLM 直接采用，不绑定完整 TokenSpeed 服务栈。
</div>
</div>

---

## 一个被忽视的瓶颈

LLM 服务栈是快还是慢，最终由内核决定。attention、MoE 路由、专家 GEMM、通信、量化、采样全都跑在内核上，它们决定了整个系统的延迟、吞吐和硬件效率。

但"最好的内核"几乎从不是一个固定答案。它取决于模型架构、张量形状、量化格式、GPU 代数、厂商库可用性，以及这次调用是在服务 decode 还是 prefill。时间一长，推理引擎就会为了覆盖所有这些情况，堆出一堆路径：树内内核、厂商库封装、实验性内核、架构特定快速路径、历史遗留回退方案。**一旦没有清晰的核系统、没有围绕它的硬性边界，后端选择逻辑就会泄漏进模型代码和 runtime 代码。**

这种泄漏代价很高：加一个新模型可能要改无关的 runtime 路径；加一个新芯片目标可能要把设备检查贯穿到模型每一层；内核开发也变难了，因为模型行为、runtime 分发、后端选择和内核实现被一个模糊的边界缠在一起。TokenSpeed-kernel 的设计，就是把这种复杂性收拢到一个地方。

## 三条设计原则

内核系统围绕三条实用原则构建。

**第一，多芯片支持必须是根本性的。** 系统应该直接理解平台能力，而不是把硬件检查当成零散的条件分支。同一个操作对不同的芯片目标可能有多种方案，所有方案都应通过同一个选择系统竞争。

**第二，可移植性和性能应该共存。** 新模型需要先有一条可移植路径尽快跑起来，再逐步采用更高度优化的内核。TokenSpeed-kernel 保留了可移植的 Triton 路径，同时并排放着面向性能的选择：AMD 用 Gluon，NVIDIA 用 CuteDSL，合适的场景用厂商封装。

**第三，快速内核迭代需要护栏。** 当从想法到落地的路径很短，内核开发才快。TokenSpeed-kernel 用精简依赖、独立基准测试和性能分析收紧这个循环，让被选中的内核可见。同样的结构也给 AI Agent 的内核开发划清了工作边界：试一个内核、验证它、做基准测试、注册它，而不必重塑模型代码。

## 分层内核系统

在高层次上，这个分层壳系统把 runtime 请求的"做什么"和每个后端"怎么做"分离开。runtime 通过一个通用公开 API 进入，选择器把请求映射到兼容的内核。

TokenSpeed-kernel 为那些在 LLM 推理中占主导地位的操作公开 API：attention、MoE、GEMM、通信等。runtime 代码优先调用顶层的 `mha_prefill`、`mha_decode_with_kvcache`、`moe_apply`。**这些 API 与平台和解决方案无关**——一次 runtime 调用不会点名"AMD 内核"或"Triton 内核"，它只描述算子问题：张量、格式、模型特征、执行约束。然后 TokenSpeed-kernel 结合当前平台和已注册的内核特征来选实现。

![](img2.png)
<span style="font-size:12px;color:rgb(153,153,153);">分层内核系统：runtime 通过通用公开 API 进入，选择器将请求映射到后端内核</span>

在底层，后端实现通过 `@register_kernel` 注册进一个共享的注册表。一次注册声明了算子族和模式、解决方案名、平台能力需求、支持的张量签名、特征和优先级。runtime 里，选择器过滤掉不兼容的内核，对剩余候选排序，返回要执行的可调用对象。

这个结构同时给了 TokenSpeed 两个难兼得的特性：模型与 runtime 保持可移植，不必知道每个 GPU 后端细节；内核层却高度特化，一个内核可以被限定到精确的架构、数据类型和张量形状。

## 注册与选择机制

灵活性背后是"注册-选择"循环。公开 API 给 runtime 一种稳定方式描述算子请求；内核注册给每个后端一种结构化方式声明它能安全高效跑什么；选择器把两者连起来。

注册表是所有可用实现的唯一事实来源。每个已注册的内核都有元数据：实现哪个算子族和模式、属于哪个解决方案、需要哪些平台能力、支持哪些张量格式签名、哪些特征必须匹配、相对其他候选的优先级是多少。

选择时，公开 API 从算子输入和选项构建请求。attention 可能含数据类型、头维度、页大小、滑动窗口行为、attention sinks；MoE 可能含权重格式、激活类型、内部激活数据类型、专家并行约束。选择器按平台能力、格式签名、特征过滤后排序。**对于固定的模型、平台、数据类型和特征，选中的实现通常稳定，所以 TokenSpeed-kernel 会缓存解析后的可调用对象。** 开发者仍可为调试和基准测试强制指定某个方案或内核，但正常执行都走同一条注册表路径。

![](img3.png)
<span style="font-size:12px;color:rgb(153,153,153);">NVIDIA 与 AMD 上 GPT-OSS 相关 attention 路径的注册代码片段</span>

## 数值、基准测试与插件

内核系统不只是分发，它给内核作者一套安全快速迭代的工作流：数值检查、独立基准测试、性能分析作用域。参考实现提供共享的正确性目标，基准测试让内核在完整服务器之外有了计时和报告路径，性能分析让选中的内核名和关键参数在端到端 trace 中可见。

同一个边界也支持树外插件。插件用同一个装饰器注册内核、分配自己的优先级，和树内实现一起参与正常选择——核心包保持干净，硬件厂商、研究人员、部署团队可以带来特化内核而无需 fork 整个系统。

![](img4.png)
<span style="font-size:12px;color:rgb(153,153,153);">数值验证与独立基准测试的 CLI 及程序化接口</span>

为了让这套工作流好用，TokenSpeed-kernel 同时提供 CLI 和程序化接口，覆盖数值验证和独立基准测试，可放进 CI 或自定义调优流水线。这些工具不是零散的测试台，它们复用服务做内核选择的同一套注册表元数据，所以一个已注册内核能对照参考实现验证、在自定义形状上测速、可选做性能分析，然后在能力特征匹配时被自动选中。

## 实战目标：AMD MI355X 上的 GPT-OSS 120B

GPT-OSS 120B 是验证这套设计的理想初始目标：它是现代 LLM，但仍能在单卡上跑，实验务实，又能锻炼当前推理负载里最关键的核系统部分。

GPT-OSS 同时压 attention 和 MoE：attention 路径用带 attention sinks 的常规 MHA，混合了滑动窗口和全 attention 层；大型 AMD 部署则为 MoE 用了 MXFP4 专家权重和 FP8 激活流。**这些正是内核边界太松时会泄漏进 runtime 的细节。** TokenSpeed 把它们压在公开 API 之下——模型代码不需要知道 MI355X 架构细节、MXFP4 的 scale 在 CDNA4 上怎么排，或某个 prefill/decode attention 场景下哪个 AMD 内核最快，它只需把正确的张量和元数据交给公开 API。

![](img5.png)
<span style="font-size:12px;color:rgb(153,153,153);">GPT-OSS 的公开内核 API 边界：runtime 只描述算子问题，实现选择留在内核层</span>

## Gluon：AMD 的内核路径

本文讨论的 AMD 路径上，性能关键的 attention 和 MoE 内核都用 Gluon 实现。Gluon 是 Triton 家族的 DSL，在暴露显式性能控制的同时保持块级编程的简洁。

对 AMD MI355X，Gluon 让内核作者直接访问 CDNA4 特性：异步拷贝、共享内存布局、用于 FP8/MXFP 格式的 scaled MFMA 矩阵核操作、高效 buffer/全局内存操作。这些都是显式编程原语而非隐藏的编译器优化——作者能自选内存布局（BlockedLayout、DistributedLinearLayout）、用 SwizzledSharedLayout 或 PaddedSharedLayout 避免 bank conflict、通过 AMDMFMALayout 选矩阵核布局，调用与硬件紧密映射的 `mfma`、`mfma_scaled`、`buffer_load`、`buffer_store` 和异步加载。

Gluon 还让软件流水线成为内核里**显式的一部分**，而不是编译器隐式变换。一个内核能分配多个共享内存缓冲区，为未来张量块发异步加载，用 `async_wait` 控制何时可见，再为不同调度方案在缓冲区间轮转。这种控制对 decode 阶段尤其关键——性能取决于隐藏内存延迟、让矩阵核保持忙碌，而不把流水线细节推给 TokenSpeed runtime。

![](img6.png)
<span style="font-size:12px;color:rgb(153,153,153);">Gluon attention 内核代码片段，直接暴露 CDNA4 原语</span>

## Attention

AMD 路径为 GPT-OSS 需要的 attention 变体注册了 CDNA4 Gluon 内核：prefill 和分页 decode，并带滑动窗口、attention sinks 等变体选项。注册特征把这些选择显式化，runtime 仍只请求 MHA，由内核系统挑匹配的 Gluon 实现。

内核实现用了分块 QK/PV 和在线 softmax 等标准技术，也用了 CDNA4 特定特性：矩阵核做矩阵乘、打包数学指令做 softmax、buffer load 指令加载 K/V 块。它还利用了 LLM 因果 prefill 的负载特征，设计了一个新的 persistent 内核，带特殊调度逻辑在 XCD 之间保持负载均衡。

![](img7.png)
<span style="font-size:12px;color:rgb(153,153,153);">attention 的 persistent 调度逻辑示意</span>

当前 Gluon attention 在 15 个被测 GPT-OSS prefill 形状中的 14 个上是速度最快的 MI355X 后端，整体比 Triton 基线快 1.4-2.3 倍。把它和厂商方案 AITER 对比：AITER 把 BF16 prefill 分发给 CK 支持的 MHA 路径、带包内 Triton 回退，而 Gluon 仍快 1.1-1.3 倍。

![](img8.png)
<span style="font-size:12px;color:rgb(153,153,153);">GPT-OSS 120B 在单卡 MI355X(CDNA4) 上的 attention prefill 吞吐量（TFLOP/s，越高越好）</span>

## MoE

MoE 是分层设计更显价值的地方。一个 GPT-OSS MoE 层不是一次稠密矩阵乘，它包含 token 路由到专家、token 行聚集或分发、跑专家 GEMM、应用激活、用路由权重组合 top-k 专家输出。AMD Gluon MoE 路径是围绕这整个结构构建的，而不是把 MoE 当两个孤立 GEMM——runtime 看到一层 MoE 行为，内核实现则能一起调优各阶段。

prefill 的瓶颈是：路由 token 在专家间分布不均时，怎么让 CDNA4 计算单元保持忙碌。实现用 ragged block 调度让工作跟随实际专家分布，再按逻辑 token 数和每专家切片大小选 tile 形状；大 prefill tile 可沿 M/N 拆分，工作被 swizzle 到 tile 组和 XCD 上以更好交错 scaled MFMA；权重路径也用了 CDNA4 友好的 MXFP4 scale swizzling 和主机预混洗权重。

decode 是另一类瓶颈：小批量受启动和路由限制，所以按批大小选两条路径。最小批大小下用 warp-decode（源自 "Better MoE model inference with warp decode"），把 top-k 路由融合进 gate/up 投影，让路由和第一个 GEMM 共享一次启动，并以协作多 warp GEMM 暂存 tile；中等批大小下，足够多 token 共享一个专家、权重 tile 被复用，则切到直接 grouped GEMM，用单缓冲直接加载换掉流水线以保高占用率，路由作为独立小融合内核跑。

结果，Gluon 在最小批大小下比 Triton 和 AITER 的 MoE 实现都快很多：比 Triton 快 1.7-2.1 倍，比 AITER 快 1.1-1.6 倍。中等 decode 区间 AITER 略领先，但 Gluon 仍保持在最快速度的 0.9 倍内、同时比 Triton 快 1.3-1.4 倍——这是他们持续改进的点。

![](img9.png)
<span style="font-size:12px;color:rgb(153,153,153);">GPT-OSS-120B 在单卡 MI355(CDNA4) 上的 MoE 延迟：Gluon vs AITER vs Triton（越低越好）</span>

## 多芯片支持

上面说的是 AMD MI355X 上的 GPT-OSS，同一套内核 API 也支持 NVIDIA。在当前 GPT-OSS Blackwell 配置里，attention 通过 FlashInfer 暴露的 TensorRT-LLM 封装走 trtllm MHA 后端，MXFP4 MoE 用 flashinfer_trtllm 方案，runtime 仍然只调 `mha_prefill`、`mha_decode_with_kvcache`、`moe_apply`。

**所以多芯片支持不是两个无关栈。** AMD 和 NVIDIA 支持是同一个内核 API、注册表、选择模型背后的兄弟实现。特定平台内核能为每个芯片目标用最好的后端，而 TokenSpeed runtime 给模型保持一致的执路径。

## 端到端性能

下图是 AMD MI355X 上 GPT-OSS 120B 的输出吞吐量，对比两种 TokenSpeed 配置：原始可移植的 Triton 支持路径，和优化后的 Gluon 支持路径。在 20 个被测点里，Gluon 路径在每个输入/输出长度和并发设置下都提升了输出吞吐量，相对可移植 Triton 路径加速 1.6-3.6 倍。这些关键 Gluon 内核让 TokenSpeed 在 AMD MI355X 的 GPT-OSS 120B 上达到了有竞争力的性能。

![](img10.png)
<span style="font-size:12px;color:rgb(153,153,153);">GPT-OSS 120B 在单卡 MI355X(CDNA4) 上的端到端输出吞吐量：TokenSpeed Triton 后端 vs Gluon 后端</span>

这笔增益不需要一条单独的 AMD 特定服务路径。AMD 的性能，是用特化 Gluon 内核实现同样的公开 attention 和 MoE 契约、注册它们的平台和形状约束、在请求匹配时让选择器分发而获得的。分层设计在保留可移植基线的同时缩短了优化周期：开发者能捕捉重要生产形状、为这些形状特化内核、用同一套数值和基准工具验证、再通过选择元数据把 runtime 路由到优化实现。

更重要的是，得益于此设计，AMD 上的这些优化内核也能在 TokenSpeed 之外复用——它们被单独拆包发布为 tokenspeed-kernel-amd，与 TokenSpeed runtime 分离，其他推理引擎无需依赖完整服务栈就能采用，**它已被 vLLM 采用。**

<div style="background:#f5f0eb;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:16px;">
<div style="text-align:center;margin-bottom:8px;">
<strong style="font-size:15px;color:#8b6f4c;">结语</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
- <strong>分层抽象的价值不在"快"，而在"可堆叠"。</strong> 文章最值得注意的不是某个 benchmark 数字，而是 AMD 专用内核能被 vLLM 直接复用——把内核做成与 runtime 解耦的一等公民，生态收益远大于单栈优化。<br><br>
- <strong>厂商都在抢"内核抽象层"这个身位。</strong> 当 AMD、NVIDIA 都收敛到同一套公开 API 背后做兄弟实现，谁定义了接口，谁就定义了生态的入口，这比单点性能更易形成长期壁垒。<br><br>
- <strong>诚实披露比营销话术更有信息量。</strong> 作者明确写出中等 decode 区间 AITER 略快于 Gluon、且"这是持续改进的点"，这种不藏拙的基准呈现，反而让整篇技术拆解更可信。
</div>
</div>

---

<span style="font-size:12px;color:#888888;font-family:'Courier New',monospace;">参考：https://pytorch.org/blog/lightseek-tokenspeed-kernel/</span>
