# CTA-Pipelining：面向延迟的多GPU系统空间扩展方法（全文翻译）

## 摘要

计算基础设施的演进已将多GPU系统转变为紧密集成的共享内存结构。然而当前软件仍主要把这些连贯互连当作高速网络使用。与此同时，在延迟约束下服务大语言模型的需求，已将GPU工作负载优化从吞吐驱动推向延迟受限，亟需超越张量并行（TP）的、面向延迟的扩展方法。

为此，我们提出CTA-pipelining，一种旨在利用共享内存多GPU系统的执行范式。作为一种面向延迟的空间扩展技术，它利用协作线程阵列（CTA）级别的依赖关系，使跨GPU的数据依赖kernel能够并发执行。我们在8卡H200和B200系统上，基于CUTLASS、cuBLAS和NCCL库验证了它的能力。结果显示：在代表MLP运算的两层GEMM上，相比micro-batching延迟降低最多31.8%，相比TP降低最多29.6%。它还能与TP正交地结合，作为另一个扩展维度进一步推高延迟边界。

## 一、引言

自Transformer架构提出以来，优化大语言模型（LLM）生产推理成为关键挑战。现代服务框架有两个目标：保持高聚合吞吐以控制成本，满足延迟服务等级目标（SLO）。在高度交互场景下，限制因素变成单batch用户输入的延迟。由于GPU传统上被设计为吞吐导向设备，最小化单batch请求的延迟带来了新的系统级需求。

相应地，为支撑LLM工作负载的快速扩展，现代多GPU硬件系统已演化为紧密耦合架构，呼唤新的软件范式来充分发掘其潜力。诸如NVIDIA GB200 NVL72这类系统利用NVLink与NVSwitch互连，不仅提供高点对点带宽，还让多GPU集群以统一共享内存空间运作。尽管近期已有先进服务框架最大化多GPU部署效率，以及为编程多GPU工作负载构建系统化抽象的努力，但在将这些紧密耦合集群原生地当作整体共享内存系统利用方面，仍有未开发的潜力。

现阶段，多GPU系统上大规模LLM部署的标准范式依赖混合并行策略，主要结合流水线并行（PP）与张量并行（TP）。虽然专家并行（EP）和分离式服务等技术提供进一步优化，但它们高度依赖具体负载。因此PP和TP仍是通用基线。PP主要在层间层面操作，将transformer块分布到设备上以提升整体吞吐。TP通过在算子层面空间切分计算，同时带来吞吐提升和延迟降低。然而TP引入额外的集合通信（如AllReduce）来消解数据依赖，为延迟优化设定了硬性天花板。

在层间PP与算子级TP之间，存在一个进一步降低延迟的机会：层内、算子间的执行空间。现有工作主要通过时间优化加速这一空间以提升单设备效率，如kernel融合或mega-kernel。但这些需要复杂编译器工具链或刚性重写。另一种方式是局部micro-batching，提供更细粒度流水线，但在小chunk尺寸下引入流水线气泡并降低kernel效率。这些局限呼唤更高效算子间空间扩展技术。

为同时应对单batch延迟优化与共享内存多GPU系统新软件范式这两重需求，我们提出CTA-pipelining，一种新颖的面向延迟的空间扩展方法。它在算子间层面运作，利用统一NVLink内存域，通过CTA粒度的动态空间流水线，使跨GPU的数据依赖kernel能够同时执行。该协议对现有GPU kernel实现的侵入极小，仅需在kernel前后加入prologue和epilogue代码片段。这为在广泛负载上自动集成保留了可能。

作为初步演示，我们用代表Transformer中MLP层的关键GPU负载——多层通用矩阵乘（GEMM）实现原型并分析。实现与评测基于SOTA的NVIDIA库CUTLASS、cuBLAS、NCCL，运行在8卡H200 NVLink系统和8卡B200 NVLink系统上。

我们从两个角度评测CTA-pipelining：验证基础机制，以及展示其更广泛的扩展能力。首先，为验证协议开销，我们分析其与经典及warp特化多级持久CUTLASS kernel的集成。结果显示开销极小，且能在warp特化执行中基本被隐藏。其次，为确立其作为通用空间扩展范式，我们在代表MLP运算的设置上，将CTA-pipelining与传统micro-batch chunk流水线（最高降低31.8%延迟）和TP（最高降低29.6%延迟）对比。我们进一步展示它可作为正交空间扩展维度与TP结合，在计算与通信两方面带来收益，进一步推高延迟扩展极限。

本文贡献如下：
- 提出CTA-pipelining，一种面向共享内存多GPU系统的空间扩展范式，旨在优化LLM推理等多GPU负载的单batch延迟。
- 用SOTA GEMM库NVIDIA CUTLASS在多种GPU kernel风格上演示了CTA-pipelining原型实现。
- 分析了基础协议开销，并指出与warp特化多级持久kernel集成带来的收益。
- 将CTA-pipelining与传统micro-batch chunk流水线对比，在多层GEMM上获得最高31.8%延迟降低。
- 在MLP设置上将CTA-pipelining与TP对比，提供最高29.6%延迟降低。
- 展示CTA-pipelining作为与TP正交的空间扩展方法，在计算与通信上带来收益，进一步推高延迟优化前沿。
- 暗示了可进一步受益于该执行模型的潜在硬件演进。

## 二、背景与相关工作

### A. GPU执行模型

理解GPU执行模型对理解本文至关重要。CUDA使用SIMD执行模型。每个GPU kernel启动全局线程网格并发处理数据。线程被分组为block，也称协作线程阵列（CTA）。每个CTA利用局部共享内存协作计算特定数据块。近期架构进一步引入线程块簇（CGA）抽象，将多个CTA分组，通过分布式共享内存（DSMEM）协作。硬件层面，CTA被分发到流式多处理器（SM），线程以32个一组的warp捆绑。各warp独立调度，同一warp内线程同时执行相同指令。

随着GPU架构演进，核心计算负载越来越多卸载到片上专用加速器。通用SM正从执行主计算转为编排这些专用单元。成熟加速器包括Tensor Core（矩阵乘累加）和Tensor Memory Accelerator（TMA）。为高效利用这种异构片上结构，warp特化成为标准编程范式：特定warp专用于执行流水线的各阶段，管理对硬件加速器的异步调用。高性能GEMM实现（如CUTLASS库）依赖此范式优化整体计算。

### B. 算子间优化

大量现有工作通过连续kernel的协同优化（算子间优化）提升GPU执行效率。离散kernel间的边界常引入性能瓶颈：kernel启动开销、冗余全局内存往返、以及wave量化效应（最后一轮调度的线程块未能充分利用可用资源）。此外，各kernel资源利用画像不同，通常分为计算密集、访存密集或通信密集。通过融合或并发执行这些算子，可重叠不匹配的资源需求，获得更高整体硬件利用率。

为直接解决算子间低效，kernel融合将多个连续操作系统合并为单一kernel。推向极致即为mega-kernel：将庞大计算子图（从复杂注意力到整条多GPU推理流水线）封装在单次kernel启动内。但这种极端融合需重编译整个工作流，以及复杂的in-kernel运行时来管理内核同步、warp级任务调度和去中心化资源分配以防SM利用不足。

此外，算子间流水线通过重叠连续执行阶段提供互补方法。与粗粒度层间并行不同，这些技术将单个算子分解为细粒度micro-batch或tile以并发处理。这种层内流水线也是实现通信-计算重叠的主要机制。

然而，这些方法主要作为单设备上的时间流水线部署以提升整体硬件利用率。部分方法收益还依赖同时处理多batch数据。将细粒度算子间流水线跨多设备空间化以降低单batch输入延迟，基本未被探索。历史上，这主要因为流水线引入气泡、需频繁阶段间同步，限制了其对延迟降低的有效性。

近期，Kitsune等硬件中心研究开始探索支持空间流水线的硬件架构潜力。我们角度不同：提出纯软件技术，旨在利用现代共享内存多GPU系统的能力，聚焦用细粒度空间流水线降低单batch查询延迟。

## 三、CTA-Pipelining协议：设计、与CUTLASS集成及开销分析

本节给出CTA-pipelining协议的设计与实现，展示其与SOTA的NVIDIA CUTLASS库在GEMM运算上的集成，并提供详细执行轨迹分析以量化协议开销。

作为构建于当前硬件与CUDA编程能力的软件方法，我们的kernel间通信依赖原子计数器与队列，与最新文献结构相似。但我们将其提升为跨设备空间扩展方法，并提供多GPU设置下的布局策略与额外一致性保障设计。此外，我们给出将协议集成到多级warp特化持久kernel的新颖实现，并发现这种集成能有效隐藏协议开销。

### A. 基础协议

顾名思义，CTA-pipelining旨在以最细架构粒度（CTA）深度流水线方式执行依赖的GPU kernel。在此模型中，每个CTA消费一个或多个输入数据块并产出单个输出块。我们不强制严格kernel级同步，而是允许消费者kernel在生产者kernel生成所需数据块的瞬间就启动其CTA。kernel执行轨迹类似图3(b)：数据依赖的kernel在空间上分布到GPU计算资源，几乎同时启动，并几乎同时完成（除消费者kernel尾部最后一轮流水线CTA计算外）。

在单GPU语境下，该目标概念上类似Megakernel方法，后者将整个工作负载重编译以在单设备上执行tile级依赖图。但CTA-pipelining旨在跨多GPU空间化细粒度流水线执行，同时保留原始kernel结构，无需重编译整体工作流。为使数据依赖kernel跨多GPU并发启动并保持正确性，需要额外的控制流依赖组织。

图1以两GPU设置演示了CTA-pipelining的整体执行过程，展示原始kernel如何与附加组件交互。支撑该范式的底层数据结构包括依赖数组、记分牌和跨设备工作队列，统称为依赖结构。为对接依赖结构并编排控制流，轻量级prologue和epilogue被直接注入原始kernel代码。下面详述各核心组件，随后逐步走查执行过程。

#### A.1 依赖数组

依赖数组标明生产者CTA与消费者CTA之间的控制流依赖。它以生产者CTA ID为索引，标识受影响的消费者CTA，包含连续消费者CTA ID列表和相应的偏移数组（定义每个生产者的索引范围）。这些依赖可直接从数据依赖导出，通过静态分析、kernel试跑，或在存在闭式公式时在运行时动态计算。由于依赖数组仅被消费者CTA访问，它存储在生产者设备内存中。

#### A.2 记分牌

为解决多对一数据依赖（一个消费者CTA依赖多个生产者CTA的输出），使用记分牌追踪生产者完成。记分牌由原子计数器数组组成，每个消费者CTA分配一个条目，初始化为其前置生产者CTA的总数。计数器归零作为就绪信号，表示消费者CTA可执行。记分牌作为依赖分析的一部分初始化。由于记分牌也仅由生产者CTA修改，它存储在生产者设备内存中。

#### A.3 跨设备工作队列

跨设备工作队列是生产者kernel与消费者kernel之间的就绪信号机制，实现为环形缓冲区，由head、tail、size等原子值管理以保证一致性。

由于工作队列需两kernel并发访问，利用了跨设备NVLink。我们将工作队列放在消费者设备内存中以最小化关键路径延迟。虽然跨设备写理论上昂贵，CUDA的异步写语义允许生产者发出"发射后不管"的内存操作而无需等待完成（除非显式flush屏障）。反之，消费者CTA必须持续轮询工作队列，强迫这些频繁读操作跨NVLink会招致延迟惩罚。因此将工作队列放在消费者设备是更合理的设计选择。

#### A.4 带Prologue与Epilogue代码片段的整体工作流

上述数据结构支撑CTA-pipelining控制流。利用这些数据结构的逻辑由极小的prologue和epilogue代码片段组成，加在kernel代码首尾，核心原始kernel实现不动（warp特化kernel略有不同，后述）。

图1中编号箭头展示了注入prologue和epilogue编排的整体控制流。首先，生产者CTA通过NVLink将其输出直接写入消费者输入内存（箭头1）。其epilogue随后发出系统级内存屏障，确保后续依赖操作和工作队列更新在实际输出数据可见前不对其他设备可见。之后，它利用SIMD执行在查询依赖数组后原子递减记分牌中的依赖计数器（2,3）。计数器归零时，生产者线程将就绪的消费者CTA ID推入工作队列（4）。消费者侧，注入的prologue用单线程忙轮询该工作队列，其余线程在屏障处等待（5）。取得就绪ID后，轮询线程通过共享内存广播。消费者CTA将其ID重映射为该取值，执行其标准、未修改的kernel负载。

#### A.5 主机侧组织

从主机侧，每个kernel被分配专用CUDA stream并绑定到特定设备或设备分区。执行时所有kernel同时启动，内部执行顺序由CTA-pipelining协议动态引导。在多层工作负载中，中间kernel同时充当生产者和消费者，既有从源工作队列取数的prologue，也有向目标工作队列推送的epilogue。注意，整个多kernel执行过程可被CUDA Graph捕获，减少kernel启动气泡。

实际工作流中，CUDA驱动默认CTA调度顺序可能不允许整个工作负载平滑流水线执行。此时改变执行顺序（如从列主序改为行主序）有益。首个kernel可直接消费预定义源工作队列以显式引导其CTA执行顺序。

有一个可选微优化，用cuStreamWaitValue32 API消除初始忙轮询的SM资源浪费。该特性阻塞消费者执行流直到工作队列含至少一项，避免立即自旋等待。但该流级同步会为kernel启动带来轻微延迟惩罚。

### B. 与CUTLASS GEMM Kernel的集成

本小节解释CTA-pipelining协议如何集成到两种不同风格的GPU kernel，以NVIDIA CUTLASS GEMM实现为例。为说明依赖映射，用两层GEMM工作负载作示例，第一层GEMM的输出被后续GEMM直接消费。

#### B.1 经典Kernel

以SM90 TMA kernel为例展示与经典GEMM kernel集成。此kernel中每个CTA所有线程遵循相同执行流，产出输出矩阵一个块。执行结束时CTA终止，下轮CTA由CUDA驱动调度。这是最经典的GPU kernel结构。

控制依赖上，每个消费者CTA通过消费整行输入块来计算一个输出块，因此依赖整行生产者CTA。同行的消费者CTA共享相同依赖。我们呈现最一般情况以作说明。

对CUTLASS库的修改侵入极小。除扩展参数结构接受必要依赖结构外，源码改动仅限于注入prologue和epilogue代码片段。prologue需共享内存将动态获取的CTA ID广播给所有线程，但复用kernel主执行已分配的内存空间。因prologue在kernel最开头运行且共享内存使用严格一次性，不影响后续执行。

总之，与经典kernel集成高度直接，不需理解或修改核心执行逻辑，表明该方法对其他kernel高度可泛化。

#### B.2 Warp特化多级持久Kernel

warp特化多级持久kernel是现代高性能库（如CUTLASS）的基础设计代表。它依赖三个重要概念：第一，持久kernel启动固定数量CTA，在整个计算中保持活跃，通过显式元数据动态获取工作块而非依赖标准CTA ID；第二，多级设计将工作流分为内部微流水线；第三，warp特化将这些不同微流水线阶段分配给独立线程warp。

在SM100 CUTLASS实现中，三者协同。微流水线包含调度、主数据加载、矩阵乘累加（MMA）、GEMM epilogue数据加载、GEMM epilogue操作等离散阶段。每个阶段由专用warp处理，GEMM epilogue阶段可能有多个warp。

CTA-pipelining prologue直接集成到调度warp。在原SM100 kernel中，下一工作块信息通过硬件查询（Cluster Launch Control，CLC查询）获取，由调度warp内单线程发出以取下一就绪工作ID。返回信息经多播跨CGA并在每个CTA的DSMEM存储。广播后各活跃warp解码响应提取其下一工作块索引。

对齐此原生kernel结构，prologue复用该工作块获取与广播通路。调度线程不发出硬件CLC查询，而是忙轮询添加的队列。成功取项后，通过CGA跨DSMEM发远程内存store，复用为CLC响应分配的原缓冲区。调度器追踪待执行总块数，通过比较当前队列索引与总块数确定工作负载完成。其他计算warp类似取下一工作块，但为新元数据结构改变解码格式。

CTA-pipelining epilogue位于微流水线最后阶段：GEMM epilogue。SM100实现中多warp执行算术操作，仅一个warp执行最终全局内存写。因保证一致内存视图的全局线程屏障仅对调用线程有效，仅负责写全局输出的warp发出线程屏障，且只有该warp用于epilogue操作。对依赖结构的操作与前述相同。

Blackwell特定Tensor Core操作有个特例：两个CTA协作发出单条Tensor Core指令。tile ID映射改变：每个CTA仍收到独立工作块信息，但总块尺寸沿一维翻倍以容纳CTA对操作。为处理此特例，从队列取的工作块信息解码不同，记分牌追踪值相应调整。流水线逻辑其余部分不变。

### C. CUTLASS上的协议开销

自然浮现的第一个问题是：协议引入的额外操作如何影响整体性能。为理解此影响，我们研究详细执行阶段，通过向kernel注入时间戳代码剖析各操作延迟，并基于收集的时间戳分析。我们给出经典kernel与warp特化多级持久kernel的结果，因其表现不同性能模式。

经典SM90 CUTLASS kernel评测在8卡H200系统，GPU以第4代NVLink连接。SM100 TMA warp特化kernel评测在8卡B200系统，以第5代NVLink连接。所有开销评测中GEMM输入尺寸为16384×8192，乘8192×8192权重矩阵。输入输出数据类型BF16，Tensor Core累加器类型FP32。具体CUTLASS配置由CUTLASS Profiler在给定输入尺寸上选取最快者。

对经典kernel，执行阶段剖析见图2(a)。每个CTA，epilogue操作约T1=6μs。之后该更新对消费者设备可见需T2=120μs。消费者侧，prologue取工作队列值并广播约T3=1.5μs。注意，此开销随每轮CTA执行累积。

warp特化持久kernel表现截然不同。CTA-pipelining可利用特定warp空闲时间，有效隐藏协议开销。warp特化kernel本质是微流水线。由于整条流水线通常受计算密集MMA操作延迟主导，其他warp常需在流水线屏障处等待。这提供了在这些等待warp内执行额外工作（如CTA-pipelining操作）的机会，而不影响整体性能。

warp特化持久kernel精确执行轨迹见图2(b)，仅含相关warp。每轮执行，epilogue操作（含线程屏障）约T1=6μs。此期间其他warp为下一轮计算保持活跃。当下一计算轮到达GEMM epilogue warp时，上一轮的CTA-pipelining epilogue操作已完成，使该warp立即承接下一轮，从而隐藏了开销。跨设备NVLink数据写对消费者设备可见约T2=5μs。消费者侧，prologue取队列约T3=1.5μs，调度warp跨CGA广播约T4=0.5μs。同样，因调度warp是微流水线一阶段，此延迟也被隐藏。因此，假设无其他内存或通信争用，CTA-pipelining开销理论上仅在初始流水线爬升时可见一次。

由于CTA-pipelining逻辑局限于注入的prologue和epilogue，它对原kernel性能干扰极小，不破坏主计算阶段的活跃寄存器分配或共享内存使用，避免寄存器溢出或共享内存争用。例如SM100评测中，两个连续GEMM基线执行平均各1080μs。用CTA-pipelining时，生产者1090μs完成，消费者1165μs完成（含可见开销与最后一轮流水线延迟）。

总之，协议引入开销极小，且可在warp特化持久kernel内基本被隐藏，使其适合通用细粒度空间流水线。

## 四、CTA-Pipelining作为扩展方法：对比Micro-batching与TP

本节展示CTA-pipelining如何作为面向延迟的空间扩展方法优化单batch执行延迟。评测分两部分：首先与传统静态micro-batch chunk流水线（即micro-batching）对比，用多层GEMM为主负载；其次与TP对比，并展示如何与TP结合，在不同扩展设置与输入尺寸上评测性能。

本节的负载为多层GEMM运算，通过省略中间逐元素非线性激活简化模拟LLM MLP层。该抽象赋予矩阵维度具体含义。在两层GEMM Y=XAB中，X代表输入激活张量，A和B为各自权重矩阵。据此，我们将权重矩阵A、B固定为8192×8192以反映典型LLM架构，X的行维度随输入序列长度灵活变化。数据类型BF16，累加器FP32，具体配置由CUTLASS profiler决定。

测试床为8卡NVIDIA B200系统，第5代NVLink。所有CTA-pipelining实现利用前述与SM100 TMA warp特化kernel的集成。对比基线用SOTA的cuBLAS和NCCL库构建。所有执行时间为5次平均，用NVIDIA Nsight Systems采集。

### A. 对比Micro-Batch Chunk流水线

直觉上CTA-pipelining执行模型类似最细粒度的micro-batching，但架构上不同，尤其在kernel效率与并行度上。与传统方法不同，CTA-pipelining不显式预分区输入为静态chunk，也不为每个流水线阶段调用多次独立kernel启动。相反，它保留原始kernel结构，利用NVLink域内统一内存空间协调。此方法在启用跨设备并行的同时保留单kernel效率，使其成为一种通用、面向延迟的空间扩展方法。

为对比静态micro-batching，我们用NVIDIA CUTLASS构建的原型在多层GEMM负载上跨多GPU实验。基线静态micro-batching用cuBLAS构建（更强的基线，因其自适应不同输入尺寸）。基线用CUDA Graph执行以最小化kernel启动开销。

输入序列长度选16384，权重维度固定8192×8192。每GPU分配一层GEMM，GPU数增加则GEMM层数增加。micro-batching按行主序拆分输入矩阵，"chunk size"指拆分子矩阵的行维度（输入序列长度），流水线阶段数等于GEMM层数。该设置见图3。

实验结果见图4。我们在不同GPU数与一系列chunk尺寸上对比。由于最优chunk选择对基线性能关键，扫描该参数保证公平对比。结果显示CTA-pipelining在所有评估配置上一致优于静态micro-batching。对比扫描中最优chunk尺寸，CTA-pipelining在2、4、8 GPU设置下分别降低延迟31.8%、30.0%、23.4%。更常见的两层GEMM（代表MLP层）在不同输入序列长度上进一步评测（图5），进一步证明其有效性。

传统micro-batch chunk流水线的根本问题可视为选择chunk尺寸时在并行度与kernel效率间的两难。chunk过大，流水线执行头尾阶段变长，多数设备等待前阶段完成，降低整体并行度；chunk过小，单个kernel计算效率受损，且小kernel常受量化效应影响，还意味着更多kernel启动，累积更多启动气泡。

相反，CTA-pipelining在可能最细粒度（CTA级）实现重叠，同时因不显式拆分输入为离散chunk，保留了kernel原始计算效率，有效解决了传统分块两难。

此外，跨设备空间化执行micro-batching引入额外开销：不仅受重复kernel启动的流水线气泡影响，还受跨设备写延迟影响（最后一轮TMA写须先于kernel终止发布）。相反，图2(b)执行轨迹分析表明，虽然CTA-pipelining需系统级内存屏障保证跨设备内存一致，warp特化kernel设计有效隐藏了此开销。

尽管收益显著，CTA-pipelining在极小输入尺寸下效果减弱。如图5，当kernel执行时间降至100μs量级（如序列长度1024），协议开销虽多被隐藏但仍凸显。最极端情况下，仅需单轮CTA的kernel，内核内流水线物理上不可能。不过传统micro-batching在此极端场景也达极限。

总之，CTA-pipelining在大多数情况下优于micro-batch chunk流水线，最大化跨设备并行并保留原生kernel效率，同时有效隐藏流水线气泡与全局内存屏障开销。实际益处还包括省去发现最优micro-batch chunk尺寸的调参工作。对已用micro-batch流水线的流程，CTA-pipelining可直接替换。

### B. 对比TP及与TP结合的空间扩展

如引言所述，TP已成为多GPU环境下面向延迟扩展的事实标准。我们提出CTA-pipelining作为可与TP结合的正交空间扩展技术。本节评测分两部分：首先在多层GEMM上对比CTA-pipelining与TP；其次评测两者结合，展示联合应用如何进一步推高延迟优化前沿。

基线TP实现镜像标准Megatron-LM范式用于LLM MLP层。标准TP下，A按列并行分片，B按行并行分片跨所有参与GPU。然后需All-reduce集合操作求和部分结果。纯TP情形再次用cuBLAS kernel作强基线，NCCL用于All-reduce。

注意，拆分输入张量X而在设备间复制权重A、B以实现数据并行并非LLM部署标准做法。现代LLM中transformer层多次重复，每层含多个庞大MLP权重矩阵。总参数量超过单GPU内存容量时，跨设备复制权重不现实。因此权重A、B跨设备分片，输入X可复制。

#### B.1 CTA-Pipelining对比TP

我们用与前述micro-batching评测相同设置（GEMM层数随GPU数增加）进行多层GEMM对比。此设置下，按标准Megatron-LM实践，TP每两层需一次All-Reduce。

实验结果见表I。CTA-pipelining在2、4、8 GPU上分别降低多层GEMM延迟29.0%、46.2%、59.0%。主要收益来源是此设置中CTA-pipelining完全避免All-Reduce通信，而TP每两层需频繁通信。这证明了将CTA-pipelining用作适合端到端纯CTA-pipelining执行流程的扩展方法的优势。

由于两层GEMM更真实，我们在图5不同输入序列长度上进一步评测，结果显示CTA-pipelining相对TP的普遍收益来自节省通信时间，尽管在极小输入尺寸上受限。

#### B.2 CTA-Pipelining与TP结合

如前述，虽然CTA-pipelining在流程可完全在此范式内执行时收益显著，但部分流程缺乏足够kernel在多GPU上形成充足流水线阶段。此时我们主张CTA-pipelining可与TP作为正交扩展维度结合进一步降低延迟。用代表MLP层的两层GEMM演示。

为集成两者，我们改变分片策略：不将A、B分布于所有设备，而是将硬件分为2-GPU组，权重矩阵在这些组内均匀分片。组内成对GPU用CTA-pipelining执行本地两层GEMM。此设置下，最终All-reduce涉及的rank数等于组数，相比纯TP将集合通信world size减半。图6给出纯TP与该结合方法对比示例。

权重固定8192×8192，输入序列长度取4096、8192、16384作为代表性用户负载尺寸。

结果见图7，线显示总执行延迟趋势，柱显式分离各设置的计算与通信时间。结果显示，与纯TP部署相比，结合CTA-pipelining为多变GPU场景提供了有益部署策略，进一步推高延迟前沿。

最直接收益来自All-reduce涉及world size减小，直接降低整体通信时间。某些情况（如图7(c)）增加纯TP度甚至产生负面影响（通信时间主导），而结合CTA-pipelining随更多GPU资源继续降低延迟。

另一因素是纯计算时间。TP度大时每GPU输入尺寸变小，类似前述micro-batching降低kernel效率。通过集成CTA-pipelining，有效降低所需TP度，保留更大矩阵维度，从而有益于计算效率。但CTA-pipelining引入额外流水线爬升延迟（单轮CTA执行延迟），抵消部分计算收益。因此计算时间是否受益因矩阵尺寸而异。

总之，上述实验表明CTA-pipelining是与TP正交的合格空间扩展方法，可无缝结合用于多GPU部署。相比纯TP，该结合方法提供明确通信收益，并在某些场景提供计算收益，为部署多GPU负载提供强力替代，并具进一步扩展更低延迟的潜力，尤其在整体负载可纯CTA-pipelining执行时。

## 五、讨论

### A. 用Lamport同步保证内存一致性

如前节所述，为保证kernel间信令的内存一致性，在输出写后、工作队列更新前发出显式系统级线程屏障，确保整个多GPU系统正确内存可见顺序。但系统级线程屏障昂贵，尤其每tile都需发出。尽管我们展示在warp特化持久kernel中此开销可被隐藏，经典kernel仍受其累。此外经验实验显示，即便无显式线程屏障，全局写乱序概率也低，促使探索进一步优化。

为此我们评估了称为Lamport同步的替代方法。此方法不再用显式线程屏障，而是将kernel间依赖数据缓冲区预初始化为不太可能在正常计算中产生的哑哨兵值（如负零）。消费者kernel从工作队列取得就绪CTA ID后，直接从全局内存读依赖数据并做额外校验。若读到的数据匹配哑值，则持续重读直到观察到有效数据。

尽管理论可行，Lamport同步引入软硬件实现挑战。在Blackwell上，数据直接传至Tensor Memory（TMEM），而TMEM仅Tensor Core可访问，直接对照哑值校验不可行；从最终Tensor Core输出推断正确性则大幅增加编程复杂度。此外Lamport同步可能需追踪中间状态（如GEMM K索引），增加共享内存压力降低性能。最后它还破坏了仅加prologue/epilogue即可启用CTA-pipelining的简洁性，给自动集成带来挑战。

因此我们未将Lamport同步作为默认配置。但注意，若硬件层面支持Lamport同步（内存子系统原生在校验全局读时检查哨兵值），此方法将高度实用，且惠及远超CTA-pipelining的众多应用。

### B. 基于Tile的模型与kernel间信令

将CTA-pipelining与近期随Triton、cuTile流行的tile执行模型联系很自然。若GPU程序用tile抽象描述，实现tile级kernel间流水线执行变得高度直观。tile抽象很大程度形式化了kernel输入输出模式，简化kernel间依赖分析。这展示了CTA-pipelining作为未来GPU编程范式中多kernel工作流广泛适应技术的潜力。

基于此洞察，启用更高效CTA级kernel间信令有更大潜在影响。虽然当前协议完全基于用户级CUDA代码在当前硬件上功能完备，它暴露了更广的架构范式转变。现代GPU中密集算术正越来越多卸载到专用加速器，常使通用ALU利用不足。我们的方法展示了如何将这些空闲通用单元有效重用于kernel间编排。这也暗示了原生驱动级支持与未来硬件集成以实现更高效kernel间信令的潜力。

### C. 通信重叠与NVLink拓扑

NVLink互连试图营造统一多GPU系统的错觉，GPU可像访问本地一样访问彼此内存。很大程度上此抽象成功，我们的CTA-pipelining技术有效利用了此错觉。但当前硬件仍有物理限制，无法完全支持此无缝抽象。分析CTA-pipelining执行期间通信实际发生方式揭示了这些限制，也凸显更先进硬件如何最终解决它们。

在8卡B200测试床中，设备经NVLink和NVSwitch互连。虽然此fabric理论支持1.8TB/s点对点带宽，但路由物理上经中心化交换机实现。与传统HPC拓扑（近似无阻塞全互连）不同，这种星形中心化架构瓶颈了每GPU最大并发进出带宽。

在CTA-pipelining范式下，此中心化NVLink拓扑限制了计算-通信重叠的充分发挥。由于生产者kernel将其输出直接写入消费者设备内存（利用共享内存机错觉），它在底层消耗NVLink带宽。因此若消费者设备想通过与生产者以外设备通信来实现计算-通信重叠，其性能仍受生产者持续内存写拖累。即便生产者未积极参与消费者二次通信，两操作共享到中心NVLink Switch的相同物理互连链路，导致争用。

理论上这些瓶颈可由更先进NVLink拓扑解决，类似当前HPC集群的复杂fabric。例如GB200 NVL72系统可拥有更多NVLink Switch。若策略性放置工作流，使经CTA-pipelining执行的一栈kernel局部化在单一NVLink Switch下，而二次通信经另一Switch路由，计算-通信重叠便高度可行。这将进一步增强CTA-pipelining威力，并暗示超越NVL72的即将到来的大规模多GPU共享内存系统上软硬件协同设计的潜力。

## 六、结论

本文提出CTA-pipelining，一种面向延迟、利用现代多GPU共享内存系统的空间扩展范式，旨在降低最新LLM推理负载所需的单batch处理延迟。通过与NVIDIA CUTLASS原型集成，我们展示了协议开销极小，且可受益于warp特化多级kernel设计。用作空间扩展时，CTA-pipelining在示例MLP设置上跨多种输入序列长度优于传统micro-batch chunk流水线与TP。此外，我们确立CTA-pipelining为与TP正交组合的通用扩展维度，进一步推高多GPU延迟优化前沿。随着计算架构演进，CTA-pipelining为未来软硬件协同设计与下一代多GPU执行模型提供了范式。
