# Swordfish 逐句翻译基线（覆盖率基准）

NVIDIA 的 Blackwell 系列 GPU 为 FP4 数据类型（具体是 NVFP4 和 MXFP4）引入了原生加速，块缩放在张量核心内部完成，速率最高可达 BF16 的四倍。自那以后，NVFP4 成为 LLM 中权重和激活值最流行的量化格式之一。在此之前，在更低精度下运行模型最流行的方式（除了 GGUF）是使用 GPTQ、AWQ 等方法量化的模型。但它们通常仍把激活值保持在半精度（bf16/fp16）。这些纯权重量化格式没有张量核心支持，所以想要跑得快就必须写专门的内核。最初的 GPTQ 内核效率很低，于是 Frantar 等人在 2024 年引入了 Marlin（Mixed-precision Auto-Regressive LINear）内核。这个内核在 Ampere GPU 上表现异常出色，后来被 vLLM 团队采用并修改以满足其需求。vLLM 团队后来又为 Hopper 架构引入了 Machete 内核，利用了新引入的 WGMMA 特性。

Swordfish 是这条内核谱系里的 Blackwell 版本。它只针对 Blackwell 家族的数据中心级 GPU，如 B200 和 Jetson Thor（sm100 和 sm110），不包含对消费级型号（如 RTX 5090 或 RTX 6000 Pro Blackwell，sm120）的支持。下面是让这一切成为可能的编程、技巧和其他努力的详细介绍。在 B200 上，Swordfish 内核在带内联 INT4 反量化的前提下持续达到 1,444 TFLOPs，是同形状下 cuBLAS 稠密 BF16 的 90%。在 Jetson Thor 上，它的 decode 跑到了 DRAM 屋顶线的 90-97%。

## Blackwell 上的变化

数据中心级 Blackwell 给了我们第五代张量核心（tcgen05），它对 Swordfish 至关重要。需要对其进行特殊处理，如下所述：

**没有混合输入 MMA。** 该指令接受 f16/bf16、tf32、int8、fp8/fp6/fp4 这组格式，以及块缩放的 MX 类型。int4 乘 bf16 的乘积无法表达，所以 CUDA 核心必须在 MMA 消费权重之前先反量化它们。那个反量化后的操作数存放在哪里、由多少条指令生成，成了非常关键的设计选择。

**累加器存放在张量内存（TMEM）中。** 每个 SM 有 256 KB TMEM，512 列乘以 128 数据通路。单个线程异步发出 MMA，结果累加到 TMEM，专门的加载指令在收尾阶段把它们读回。warp 寄存器累加器片段，以及 Ampere 上把 MMA 与收尾数学交错在同一个寄存器里的习惯，都不复存在。

**一个 MMA 跨越两个 SM。** 在 cta_group::2 下，单条指令跨 SM 对计算一个 tile，操作数投送和同步语义是配对模式特有的。

warp 级的 mma.sync 路径在 Blackwell 上仍然可用且表现相当好。正因如此，下面的 decode 内核保持在 mma.sync 上，但 prefill 采用了 tcgen05，因为我们需要能拿到的所有算力。

## 一种布局服务三个消费者

decode 非常受内存限制。活跃批次很小，所以每个权重字节每步只被读一次。prefill 把每个权重 tile 摊还到数千个 token 上，因此非常受计算限制。非常大的批次受计算限制到这种程度：把整个权重反量化一次再调用稠密库，直接就赢了。

因此 Swordfish 针对一个打包张量编译出三条路径，在模型加载时只打包一次。一组 decode 内核，围绕 mma.sync.m16n8k16 手写的 CUDA 和 PTX，负责到大约一百行为止的所有工作。一个 prefill 主循环，是 CUTLASS 4.4 sm100 混合输入 collective 的一个分支，通过 TMA 喂料的 warp 专门化流水线驱动 tcgen05。一个稠密层用一次合并内核把权重反量化为一个临时 fp16/bf16 张量，再把 GEMM 交给 cuBLAS。

### 打包格式

int4 存储按 (n_block, k_block, word) 索引，范围是 (N/64, K/64, 512)，int8 则是 (N/64, K/32, 512)。每个块是一段连续的 2,048 字节，保存一个 64x64（int4）或 32x64（int8）tile，由四个 512 字节子 tile 组成，这些子 tile 原样保留了 Marlin 的 16x64 片段排列。

该布局围绕三个不变量构建：一个 32 位字用四个 LOP3 且零跨 lane 洗牌反量化进 mma.sync 片段寄存器，一条 lane 用一次 256 位访问取回它完整的权重片段组（八个打包字）。在此之上，每个块占据一个线性字节范围，这让 prefill 路径能把整个张量作为稠密字节数组交给 TMA；半字节排列被限制在 32 位字内部，任何字节级拷贝都观察不到它。

反量化使用 magic-number 惯用法。对于 bf16，lop3.b32 指令从字中恢复八个半字节中的四个为两个 bf16x2 对，第二组 LOP3 完成整个字，所以八个 int4 值花费四个逻辑操作加每对一次 hmul2。int8 变体在字节 lane 上跑同样的惯用法，带 128 偏置。AWQ 零点作为 scale 形状的行到达，保存预缩放值 (8 − zp)·s，所以 scale 乘法和零点加法融合为每对一个 hfma2。逐通道检查点把它们的单个 scale 行复制到 group 128。prefill 和稠密层把复制后的行当作普通的 group-128 元数据消费，而 decode 保留 group_size = -1，只读一次 scale 行零，并完全跳过 group 记账。

### 运行时调度

regime 边界位于 C++ 算子内部，真正的运行时 M 在每次调用和每个捕获的 CUDA 图处决定。Python 侧分支被 torch.compile 在一个代表性批次大小处追踪并烘焙进编译图，同时把后续每次调用路由到追踪所见的内核。

decode 总是处理 M ≤ 55。只要 prefill 网格的列数（每 128 个输出列一个 CTA）会欠填 SM，它就让 M < 96；在数据中心部件上，它对 K 重窄 N 形状（K ≥ 2N）保持到 M = 127，此时一次欠填的 tcgen05 波次会输给 Stream-K。prefill 需要 fp16 或 bf16 激活、int8 group size 128 或 int4 group size 32、64 或 128，且 K 和 N 能被 128 整除；不合条件的组合在任何 M 下都留在 decode。稠密层抢占两者。在数据中心部件上，它对 int8 在 M ≥ 1024、int4 在 M ≥ 4096、以及激活重排权重在 N ≤ 2K 时 M ≥ 512 处介入。在 Thor 上它只服务 int8，普通形状从 M ≥ 2048、K 重形状从 M ≥ 8192。

## Decode，计算内存管道槽位

对一个早期修订在 M = 1、K = N = 4096 下相对 Marlin 做性能剖析，显示 DRAM 流量只差两个 sector，Swordfish 侧多了 41% 的 LSU wavefront。wavefront 是加载-存储流水线的一个发射槽，该流水线服务每个共享内存访问、全局加载和原子操作，所以暂存、scale 收集、收尾阶段都和权重流竞争同一个发射能力。最终的主循环机制被这个家族里每个 decode 内核共享，把那些槽位当作稀缺资源来对待。

最终主循环机制的优化项略（self-slot cp.async staging、ldmatrix.x4、算术卫生、协作 scale 加载、red.global.add 收尾、evict_first 等）。

在 M = 1 的 Thor 上，该家族在 Llama 层形状上持续达到 231 到 249 GB/s 的权重带宽，即平台实际 DRAM 上限的 90% 到 97%。

## 稠密层

从大约一千行开始，问题受计算限制，融合主循环把稠密库性能留在桌上。稠密层用一次内核启动把打包张量反量化为临时 fp16/bf16 权重并调用 cublasGemmEx。反量化内核给每个 warp 一个 16x64 子 tile，通过同样的 LOP3 路径解包，暂存进每行从 64 补到 72 个元素的共享 tile，并写 16 字节块。未补边的 128 字节行步幅会让跨行的同列存储都落在一个共享内存 bank，每次启动 4096x4096 处有 160 万次冲突；补边消除了它们，让内核落到 DRAM 屋顶线上。激活重排检查点把排列折叠进反量化权重写地址，因此激活以未排列形式被消费，单独的 prep 启动消失。

## 在 tcgen05 上做 prefill

CUTLASS 4.4 混合输入 sm100 collective 已经有我们想要的正确骨架。Swordfish 在两个缝处分叉它。TMA 把打包张量作为原始 2,048 字节块暂存，Transform 阶段以 Marlin tile 顺序消费打包字，反量化、缩放并写入 K 主片段。分叉相对稠密参考 GEMM 看起来完全没有偏离，并在 M ≥ 1024 处比原版 collective 快 11%。

UMMA 描述符在字节域消费共享内存偏移，而评估计算缓冲的 ComposedLayout 在元素域应用其 swizzle。描述符寻址因此需要字节域形式，对此原子有闭式表达 offset ^ ((n % 8) << 3)。我们针对该布局静态断言该表达式，并用它替换通用 crd2idx 寻址，使 Transform 阶段快了 40%。

### 每个 MMA 两个 SM

cta_group::2 跨 SM 对计算一个 256 行权重 tile，每个 CTA 持有反量化权重的一半，leader 发出指令。

### 指令宽度

配对正确后，B200 吞吐从 M = 2048 往上在接近 1,090 TFLOPS 处饱和，并在 Transform 宽度、流水线深度和 K-tile 粒度扫描中保持平坦。把 MMA 从 256x128 加宽到 256x256，一步就抬高了天花板。每条指令的发射开销限制了窄 tile，把每指令工作量翻倍消除了这个限制。

每个 CTA 分配两个 256 列累加器阶段，正好耗尽其 512 列 TMEM 地址空间。int4 为每个激活数据类型和 group size 实例化两种宽度并按形状调度。int8 只编译 256x128，因为宽 tile 的输入暂存在 8 位下超出共享内存预算。

Thor 上大 M 启动一旦激活块超出 32 MB L2 就会使其抖动，在 M = 2048、K = 14336 处造成三分之二的吞吐损失，所以启动器分块 M 以适配。256 宽 tile 把大多数 Thor 形状抬到 96 到 175 TFLOPS，相对 127 TFLOPS 的稠密 bf16 天花板。受带宽限制的形状超过稠密，因为 int4 权重以稠密成本的四分之一穿过内存总线。

## 融合 MoE

专家层在 token 排序的工作上复用 decode 机制。moe_align_block_size 把（token, expert）对排序成 16 行的块，一旦每专家平均 token 超过阈值就加宽到 32，一个持久的 Stream-K 内核像稠密 Stream-K 一样领取扁平（块, 列, k-slice）单元，加了三个间接层。

## 端到端结果

我们基准测试了六种模式，每种模式用一个公开检查点，针对能在这硬件上运行的每个混合精度后端，关闭前缀缓存，1,024 token 提示，128 输出 token。表格显示 Swordfish 在 batch 32 的每秒 token 数，括号内是相对最强基线 Marlin 的倍数。

（端到端表格：GPTQ int4 Llama-8B、AWQ int4+zp Qwen-3B、GPTQ int8 Qwen-3B、act_order Mistral-7B、Fused MoE Qwen1.5-MoE、Channelwise int8 TinyLlama 的 B200 prefill/decode 与 Thor prefill/decode 数字，详见 article.md 正文表格。）

batch 1 的同一扫描更偏向 Swordfish。单请求 decode 在两种机器上赢或平每种模式，B200 上相对 Marlin 1.10x 到 1.34x，Thor 上 1.00x 到 1.06x，单请求 prefill 跑 1.4x 到 2.8x。

面对更广的对手差距更大。Exllama 重建 fp16 权重并在行阈值之上跑稠密 GEMM，使其大批次 prefill 落在 Swordfish 的 10% 以内，而 decode 跑四分之一到三分之一。AllSpark 在它唯一支持的模式下与 Swordfish 差两百分点内。Humming 在 prefill 处落后 2x 到 3x，Triton 和 Conch 内核全程落后 2x 到 5x。

Thor batch 32 上，四种 decode 模式落后 Marlin 最多三个百分点。该负载落在 20-SM 部件的 M 17 到 48 窗口，即 Marlin 的 256 线程 tile 调优的区间。完整请求在那些设置下在 Swordfish 上完成得更快，因为 prefill 领先 1.6x 到 2.7x。

随着上下文增长提速被压缩，因为注意力成本二次增长而 GEMM 成本线性增长，缩小了量化 GEMM 在墙钟时间里的占比。在 131k token 提示下 B200 prefill 优势为 1.5x。

## 数值行为

每个配置都通过 sm100 和 sm110 上相对反量化参考的 prepack 测试和 GEMM 正确性测试，prefill collective 额外匹配其稠密参考 GEMM。对于生成，我们在混合提示上跨后端比较贪心解码，每步记录 top-2 logprobs。一半的补全在全部 128 步中 token 完全相同。其余的每次分歧都发生在前两个 token 恰好并列或一个 bf16 量子之差处，对照显示 Swordfish 与它自己重跑的分歧率和它相对 Marlin 的分歧率相同。

原子收尾重排求和，所以贪心输出在精确并列处跨运行变化。APHRODITE_SWORDFISH_DETERMINISTIC=1 为原子 decode 窗口选择共享内存归约收尾，以受影响形状 5% 到 25% 的 decode 吞吐损失恢复逐位稳定，这就是 atomics 保持默认的原因。tcgen05 prefill 在两种模式下都是确定的。

## 适用范围

Swordfish 目前支持对称 GPTQ int4（uint4b8）和 int8（uint8b128）、带零点的 AWQ uint4、激活重排、融合 MoE、fp16 和 bf16 激活，以及 group size 32、64、128 和逐通道。跨行并行张量并行分片的激活重排和 W4A8 激活量化自动回退到 Marlin。消费级 Blackwell（sm120）是不同的 SM，不支持。长期来看，转换成原生 NVFP4 或 MX 格式的检查点完全舍弃 Transform 阶段，在转换保留可接受精度之处，我们预期它成为该架构上首选的 4 位路径。

## 可用性

Swordfish 在 Sonar（前 Aphrodite Engine）中可用，添加于 dphnAI/sonar#1707。在支持的硬件和检查点上自动选中，可用 --linear-backend swordfish 和 --moe-backend swordfish 强制。它构建于 Elias Frantar 等人的 Marlin、Neural Magic 团队的 Machete、NVIDIA 的 CUTLASS 以及 qutlass 项目之上。所有测量都使用锁定时钟、冷权重轮转，以及在 B200 和 Jetson Thor 开发套件上重复运行的中位数计时。
