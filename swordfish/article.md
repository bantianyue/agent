<div style="background:#e8f4fd;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:18px;">
<div style="text-align:center;margin-bottom:10px;">
<strong style="font-size:16px;color:#1a6ba0;">要点速览</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
- <strong>Blackwell 权重量化的新内核</strong>：Swordfish 是继 Marlin、Machete 之后，面向 NVIDIA Blackwell 数据中心 GPU（B200、Jetson Thor）的 INT4/INT8 权重量化 GEMM 内核家族，decode 跑满 DRAM 屋顶线的 90-97%<br><br>
- <strong>一套打包格式喂三条路径</strong>：同一个预打包张量同时服务 decode 内核（mma.sync）、prefill 主循环（tcgen05）和稠密层（反量化后交 cuBLAS），按运行时 M 维度自动调度<br><br>
- <strong>性能对标 cuBLAS 稠密 BF16 的 90%</strong>：B200 上带内联反量化的持续算力达 1,444 TFLOPs，端到端 prefill 相对 Marlin 快 1.4x 到 2.8x，decode 在单请求下赢或平<br><br>
- <strong>已落地生产</strong>：集成进 Sonar（原 Aphrodite Engine），在支持的硬件上自动启用，也可强制指定 `--linear-backend swordfish`
</div>
</div>

## Blackwell 上的变化

NVIDIA 的 Blackwell 系列 GPU 为 FP4 数据类型（具体是 NVFP4 和 MXFP4）引入了原生加速，块缩放在张量核心内部完成，速率最高可达 BF16 的四倍。自那以后 NVFP4 成了 LLM 里权重和激活值最流行的量化格式之一。在这之前，低精度跑模型的主流方式（GGUF 之外）是 GPTQ、AWQ 这类权重量化，但它们通常仍把激活值保留在半精度。这些纯权重量化格式没有张量核心支持，想跑得快就必须写专门的内核。

Swordfish 就是这条内核谱系里的 Blackwell 版本，只面向数据中心级 GPU（B200、Jetson Thor，即 sm100 和 sm110），不支持消费级的 RTX 5090、RTX 6000 Pro Blackwell（sm120）。**在 B200 上，它的内核在带内联 INT4 反量化的前提下持续达到 1,444 TFLOPs，是同形状 cuBLAS 稠密 BF16 的 90%；在 Jetson Thor 上 decode 跑到了 DRAM 屋顶线的 90-97%。**

数据中心级 Blackwell 带来第五代张量核心 `tcgen05`，这是 Swordfish 的关键。它需要三点特殊处理：

**没有混合输入 MMA。** 该指令接受 f16/bf16、tf32、int8、fp8/fp6/fp4 这组格式以及块缩放的 MX 类型，但 int4 乘 bf16 的乘积无法表达，所以 CUDA 核心必须先反量化权重，MMA 才能消费。那个反量化后的操作数放在哪里、由几条指令生成，成了最关键的架构选择。

**累加器搬进了张量内存（TMEM）。** 每个 SM 有 256 KB TMEM（512 列 × 128 数据通路）。单个线程异步发出 MMA，结果累加到 TMEM，专门的加载指令在收尾阶段读回。warp 寄存器累加器片段、以及 Ampere 上把 MMA 与收尾数学交错在同一批寄存器里的习惯，都消失了。

**一个 MMA 跨越两个 SM。** 在 `cta_group::2` 下，单条指令跨 SM 对计算一个 tile，操作数投送和同步都是配对模式特有的。

warp 级的 `mma.sync` 路径在 Blackwell 上依旧可用且表现不错，所以下面的 decode 内核留在 `mma.sync`，而 prefill 改用 `tcgen05`，因为那里需要榨干所有算力。

## 一套布局服务三个消费者

decode 极度受内存限制：活跃批次小，每个权重字节每步只被读一次。prefill 把每个权重 tile 摊还到数千个 token 上，因此极度受计算限制。超大批次则受计算限制到这种程度：把整个权重反量化一次再调稠密库，直接就赢了。

**于是 Swordfish 针对一个预打包张量编译出三条路径，模型加载时只打包一次**：一组手写的 decode 内核（围绕 `mma.sync.m16n8k16` 的 CUDA + PTX）负责到大约一百行为止的工作；一个 prefill 主循环（CUTLASS 4.4 sm100 混合输入 collective 的分支）通过 TMA 喂料的 warp 专门化流水线驱动 `tcgen05`；一个稠密层用一次合并内核把权重反量化为临时 fp16/bf16 张量，再把 GEMM 交给 cuBLAS。

### 打包格式

int4 存储按 `(n_block, k_block, word)` 索引，范围是 `(N/64, K/64, 512)`，int8 则是 `(N/64, K/32, 512)`。每个块是一段连续的 2,048 字节，保存一个 64×64（int4）或 32×64（int8）tile，由四个 512 字节子 tile 组成，原样保留 Marlin 的 16×64 片段排列。

布局围绕三个不变量构建：一个 32 位字用四个 `LOP3` 且零跨 lane 洗牌反量化进 `mma.sync` 片段寄存器；一条 lane 用一次 256 位访问取回它完整的权重片段组（八个打包字）；在此之上每个块占据一个线性字节范围，让 prefill 路径能把整个张量作为稠密字节数组交给 TMA，而半字节排列被锁在 32 位字内部，任何字节级拷贝都观察不到它。

![](fig01.png)
<span style="font-size:12px;color:rgb(153,153,153);">同一个张量的三种视角。decode 路径读字和 256 位 lane 组，prefill 路径读整个块。</span>

反量化用 magic-number 惯用法：对 bf16，`lop3.b32` 从字中恢复八个半字节里的四个为两个 bf16x2 对，第二组 `LOP3` 完成整个字，所以八个 int4 值只花四个逻辑操作加每对一次 `hmul2`。AWQ 零点作为 scale 形状的行到达，保存预缩放值 `(8 − zp)·s`，于是 scale 乘法和零点加法融合成每对一个 `hfma2`。逐通道检查点把单个 scale 行复制到 group 128；prefill 和稠密层把它当普通 group-128 元数据消费，而 decode 保留 `group_size = -1`，只读一次 scale 行零，完全跳过 group 记账。

### 运行时调度

regime 边界藏在 C++ 算子内部，真正的运行时 M 在每次调用、每个捕获的 CUDA 图处决定。Python 侧分支被 `torch.compile` 在一个代表性批次大小处追踪、烘焙进编译图，后续每次调用都路由到追踪所见的内核。

decode 永远处理 M ≤ 55；只要 prefill 网格的列数（每 128 个输出列一个 CTA）会欠填 SM，就保持 M < 96；数据中心部件上对 K 重窄 N 形状（K ≥ 2N）保持到 M = 127，因为一次欠填的 `tcgen05` 波次会输给 Stream-K。prefill 要求 fp16/bf16 激活、int8 group 128 或 int4 group 32/64/128、且 K 和 N 能被 128 整除，不合条件者任何 M 下都留在 decode。稠密层抢占前两者：数据中心部件上 int8 在 M ≥ 1024、int4 在 M ≥ 4096、激活重排权重在 N ≤ 2K 且 M ≥ 512 时介入；Thor 上只服务 int8，普通形状 M ≥ 2048、K 重形状 M ≥ 8192。

![](fig02.png)
<span style="font-size:12px;color:rgb(153,153,153);">沿 M 轴的 kernel 归属。阴影跨度是上面描述的那些条件区间。</span>

## Decode，掰着指头算内存管道槽位

对早期修订在 M = 1、K = N = 4096 下相对 Marlin 做性能剖析，DRAM 流量只差两个 sector，Swordfish 侧却多了 41% 的 LSU wavefront。wavefront 是加载-存储流水线的一个发射槽，这条流水线服务每次共享内存访问、全局加载和原子操作，所以暂存、scale 收集、收尾阶段全都和权重流抢同一个发射能力。**最终主循环被整个 decode 家族共享，就是把那些槽位当稀缺资源来用。**

共享主循环的优化项包括：每条 lane 只拷贝它稍后要消费的字节进自己的共享内存槽（最多五级深），全程无 warp 同步；`ldmatrix.x4` 用一条指令替换八次标量共享加载，把 m16k16 tile 落到张量核心寄存器顺序；协作式 scale 加载用每 lane 一次 4 字节访问覆盖 64 宽 scale 行，并提前一整组预取下一组；收尾用 `red.global.add` 把分块 tile 合并进清零输出，删掉跨 warp 的共享内存归约及其 barrier；权重流标记 `evict_first`，把 L2 留给会被重读的激活和 scale。

![](fig03.gif)
<span style="font-size:12px;color:rgb(153,153,153);">一个 warp 的主循环。阶段环填满后，每轮发一次拷贝、消费最老的就绪槽，累计 tile 最后通过 red.global 冲出，全程无 barrier。</span>

decode 窗口分三个 regime：**M ≤ 16** 用一个四 warp CTA 占一个 n64 列，warp 连续切 K 使每个 warp 恰好看一遍所有 scale 组，必要时用 `blockIdx.z` 做 split-K；**M 17 到 48** 数据中心部件用融合原子内核（每 CTA 两到三个 m16 tile、共享一条权重流），少 SM 部件改用 Stream-K（按 n256 列四元组领 claim），两者在各自硬件上比对方形态快最多 25%；**M ≥ 49 到 prefill 交接点** 用持久 Stream-K，一个 warp 领一段连续单元，累加器在 claim 边界通过原子收尾冲出，所以一个 tile 的 K 轴可由任意数量 warp 覆盖，无锁无修复。

在 Thor 的 M = 1 上，该家族在 Llama 层形状上持续 231 到 249 GB/s 的权重带宽，即平台实际 DRAM 上限的 90% 到 97%。

## 稠密层

从大约一千行起问题转为受计算限制，融合主循环把稠密库性能留在桌上。稠密层用一次内核启动把打包张量反量化为临时 fp16/bf16 权重并调用 `cublasGemmEx`。反量化内核给每个 warp 一个 16×64 子 tile，通过同样的 `LOP3` 路径解包，暂存进每行从 64 补到 72 个元素的共享 tile。不补边的 128 字节行步幅会让跨行同列存储都落在一个共享内存 bank，4096×4096 时每次启动 160 万次冲突；补边消除了它们，让内核落到 DRAM 屋顶线。激活重排检查点把排列折叠进反量化权重的写地址，于是激活以未排列形式被消费，单独的 prep 启动也消失了。

调度里的交接阈值来自两台机器上的实测：融合主循环读 int4 权重的流量是稠密层 fp16 权重的四分之一，而 Thor 上稠密层的 cuBLAS 速率始终补不上这个差距，所以 int4 在那里任何 M 都保持融合；int8 时流量差减半，稠密层反超融合路径；激活重排权重最早越过，因为稠密层吸收掉了融合路径要花一次 prep 启动加 gather 密集 scale 处理的排序。

## 在 tcgen05 上做 prefill

### 分叉 collective

CUTLASS 4.4 混合输入 sm100 collective 已经有我们想要的正确骨架：TMA warp 加载操作数、Transform warp 组反量化进共享内存计算缓冲、MMA warp 喂 `tcgen05`、mbarrier 流水线解耦三者。原版期望规范的列主序权重并在摄入时重排列，所以 Swordfish 在两个缝处分叉它：TMA 把打包张量当作原始 2,048 字节块暂存，Transform 阶段以 Marlin tile 顺序消费打包字、反量化、缩放，并用 lane 局部的 32 位存储把 K 主片段写进 `tcgen05` 合法的缓冲。流水线和 MMA 阶段基本没动。零点沿 scale 流水线作为第二个 scale 形状张量进入，在 Transform 阶段多一次 FMA。这个分叉相对稠密参考 GEMM 看不出任何偏离，并在 M ≥ 1024 处比原版 collective 快 11%，这就是跳过规范布局工作的直接回报。

![](fig04.png)
<span style="font-size:12px;color:rgb(153,153,153);">一个 SM 对上的分叉 collective。每个 CTA 变换自己那半权重 tile，一次 2-SM TMA 投送两个激活半块，leader 在两个计算缓冲上发出 MMA。</span>

UMMA 描述符在字节域消费共享内存偏移，而评估计算缓冲的 `ComposedLayout` 在元素域应用 swizzle，所以描述符寻址需要字节域形式：对此原子有闭式表达 `offset ^ ((n % 8) << 3)`。作者针对该布局静态断言这个表达式，并用它替换通用 `crd2idx` 寻址，使 Transform 阶段快了 40%。

### 每个 MMA 两个 SM

`cta_group::2` 跨 SM 对计算一个 256 行权重 tile，每个 CTA 持有反量化权重的一半，leader 发出指令。实现把权重当作操作数 A、激活当作操作数 B 贯穿 Transform 阶段，有三处 2-SM 细节决定正确的构造、分区和操作数投送，每处只需改一行：`sm100_make_trivial_mixed_input_tiled_mma` 没有针对 smem 来源 A 的 2-SM 原子分支（但有完整 trait 的 `SM100_MMA_F16BF16_2x1SM_SS`，直接 `make_tiled_mma` 即可）；`partition_shape_A/B` 取 2-SM 原子的 CTA 局部形状（256 行指令 tile 按每 CTA 128 行分区，传整个 tile 会因重载解析报错却从不提形状）；激活操作数按指令的 B-layout `Shape<_2, Shape<N/2, K>>` 跨对拆分，leader 的 MMA 读 peer CTA 的共享内存后半，这正是 `SM100_TMA_2SM_LOAD` 存在的意义，一条指令投送两半、leader barrier 上的一次到达覆盖两个 CTA 的字节。普通每 CTA TMA 会要么挂起、要么非确定性地破坏后半输出，两个特征都指向这个拷贝原子。

### 指令宽度

配对正确后，B200 吞吐从 M = 2048 往上在接近 1,090 TFLOPS 处饱和，并在 Transform 宽度、流水线深度、K-tile 粒度扫描中保持平坦。把 MMA 从 256×128 加宽到 256×256，一步就抬高了天花板：每条指令的发射开销限制了窄 tile，把每指令工作量翻倍消除了这个限制。

| M（K=4096, N=28672） | 256×128 | 256×256 |
| --- | --- | --- |
| 512 | 879 | 1,139 |
| 1024 | 1,029 | 1,406 |
| 2048 | 1,056 | 1,395 |
| 4096 | 1,089 | 1,444 |
| 8192 | 1,093 | 1,442 |

<span style="font-size:12px;color:rgb(153,153,153);">B200 上含内联反量化的有效 TFLOPs。稠密 bf16 cuBLAS 在这些形状上测到 1,604 到 1,629，量化路径约为稠密库的 90%。</span>

每个 CTA 分配两个 256 列累加器阶段，正好耗尽 512 列 TMEM 地址空间。int4 为每个激活数据类型和 group size 实例化两种宽度并按时调度；int8 只编译 256×128，因为宽 tile 的输入暂存在 8 位下超出共享内存预算。Thor 上大 M 启动一旦激活块超出 32 MB L2 就会抖动，在 M = 2048、K = 14336 处造成三分之二吞吐损失，所以启动器分块 M 以适配。256 宽 tile 把大多数 Thor 形状抬到 96 到 175 TFLOPs，相对 127 TFLOPs 的稠密 bf16 天花板。受带宽限制的形状超过稠密，因为 int4 权重以稠密成本的四分之一穿过内存总线，这让量化在这类硬件上本身就是一项吞吐特性。

## 融合 MoE

专家层在 token 排序的工作上复用 decode 机制。`moe_align_block_size` 把（token, expert）对排成 16 行块，每专家平均 token 超阈值后加宽到 32，一个持久 Stream-K 内核像稠密 Stream-K 一样领扁平（块, 列, k-slice）单元，只是多了三层间接：块行通过排序后的 token id 收集激活，`expert_ids` 选出权重张量的专家 slab，路由权重作为每行乘法折进收尾。一个内核形状能覆盖 batch 1 下 60 专家 top-4 路由（多数块只含单行真实数据）直到完整 prefill 批次。每专家 token 很高时，该层按与稠密层同样的逻辑离开融合内核：少 SM 部件上跑每专家 `tcgen05` 启动，数据中心部件上跑稠密层反量化的转置变体，把专家权重物化为 stock bf16 融合-MoE 内核消费的 [N, K] 顺序。

## 端到端结果

我们在六种模式上做基准，每模式一个公开检查点，针对能在这硬件上运行的每个混合精度后端，关闭前缀缓存、1,024 token 提示、128 输出 token。表格是 Swordfish 在 batch 32 的每秒 token 数，括号内是相对最强基线 Marlin 的倍数。

| 模式, 模型 | B200 prefill | B200 decode | Thor prefill | Thor decode |
| --- | --- | --- | --- | --- |
| GPTQ int4, Llama-8B | 89.5k (3.4x) | 7,176 (1.00x) | 7.1k (2.4x) | 790 (0.99x) |
| AWQ int4+zp, Qwen-3B | 193.7k (3.2x) | 10,426 (1.06x) | 15.1k (2.3x) | 1,846 (0.97x) |
| GPTQ int8, Qwen-3B | 193.5k (3.8x) | 10,129 (1.10x) | 14.0k (2.7x) | 1,458 (1.01x) |
| act_order, Mistral-7B | 87.7k (3.5x) | 7,163 (1.14x) | 6.1k (2.2x) | 836 (0.98x) |
| Fused MoE, Qwen1.5-MoE | 148.9k (2.2x) | 5,928 (1.03x) | 12.0k (1.6x) | 639 (0.98x) |
| Channelwise int8, TinyLlama | 494.2k (3.5x) | 20,547 (1.21x) | 37.1k (2.3x) | 3,365 (1.00x) |

batch 1 的同一扫描更偏向 Swordfish：单请求 decode 在两种机器上赢或平每种模式（B200 相对 Marlin 1.10x 到 1.34x，Thor 1.00x 到 1.06x），单请求 prefill 跑 1.4x 到 2.8x。

![](fig05.png)
<span style="font-size:12px;color:rgb(153,153,153);">B200 吞吐。</span>

![](fig06.png)
<span style="font-size:12px;color:rgb(153,153,153);">Thor 吞吐。</span>

面对更广的对手差距更大：Exllama 重建 fp16 权重、在行阈值之上跑稠密 GEMM，大批次 prefill 落在 Swordfish 的 10% 以内，但 decode 只有其四分之一到三分之一；AllSpark（Ampere 逐通道 int8 内核）在唯一支持的模式下与 Swordfish 差两百分点内，其余五种全不支持；Humming 在 prefill 处落后 2x 到 3x，Triton 和 Conch 内核全程落后 2x 到 5x。

Thor batch 32 上四种 decode 模式落后 Marlin 最多三个百分点，因为该负载落在 20-SM 部件的 M 17 到 48 窗口，即 Marlin 的 256 线程 tile 调优区间；但完整请求在那些设置下于 Swordfish 上完成得更快，因为 prefill 领先 1.6x 到 2.7x。随着上下文增长提速被压缩，因为注意力成本二次增长、GEMM 成本线性增长，量化 GEMM 在墙钟里的占比缩小，131k token 提示下 B200 prefill 优势为 1.5x。

## 数值行为

每个配置都通过 sm100 和 sm110 上相对反量化参考的 prepack 测试和 GEMM 正确性测试，prefill collective 额外匹配其稠密参考 GEMM。生成侧在混合提示上跨后端比较贪心解码、每步记录 top-2 logprobs：一半补全在全部 128 步中 token 完全相同，其余分歧都发生在前二 token 恰好并列或一个 bf16 量子之差处，对照显示 Swordfish 与自己重跑的分歧率和相对 Marlin 的分歧率相同。

原子收尾重排求和，所以贪心输出在精确并列处跨运行变化。`APHRODITE_SWORDFISH_DETERMINISTIC=1` 为原子 decode 窗口选共享内存归约收尾，以受影响形状 5% 到 25% 的 decode 吞吐损失换回逐位稳定，这就是 atomics 保持默认的原因。`tcgen05` prefill 在两种模式下都是确定的。

## 适用范围

Swordfish 目前支持对称 GPTQ int4（`uint4b8`）和 int8（`uint8b128`）、带零点的 AWQ uint4、激活重排、融合 MoE、fp16/bf16 激活，以及 group size 32/64/128 和逐通道。跨行并行张量并行分片的激活重排和 W4A8 激活量化自动回退到 Marlin；消费级 Blackwell（sm120）是不支持的另一种 SM。长期看，转成原生 NVFP4 或 MX 格式的检查点会完全舍弃 Transform 阶段，在转换保住可接受精度之处，预期它会成为该架构上首选的 4 位路径。

## 可用性

Swordfish 已集成进 Sonar（前 Aphrodite Engine），添加于 `dphnAI/sonar#1707`，在支持的硬件和检查点上自动选中，也可强制 `--linear-backend swordfish` 和 `--moe-backend swordfish`。它构建于 Elias Frantar 等人的 Marlin、Neural Magic 团队的 Machete、NVIDIA 的 CUTLASS 以及 qutlass 项目之上。所有测量均使用锁定时钟、冷权重轮转、在 B200 和 Jetson Thor 开发套件上重复运行的中位数计时。

<div style="background:#f5f0eb;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:16px;">
<div style="text-align:center;margin-bottom:8px;">
<strong style="font-size:15px;color:#8b6f4c;">结语</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
Swordfish 的巧思不在于某个单点突破，而在于把「一套打包布局同时喂 decode、prefill、稠密三层」这件事做绝：靠 Marlin 的 16×64 片段排列做黏合剂，让 mma.sync 和 tcgen05 两条路径共享同一份权重，调度完全交给运行时 M 维度裁决。这种「一个格式、三个消费者」的设计，比单纯堆某条路径的峰值更有工程长尾价值。<br><br>
它再次印证了一个趋势：在 Blackwell 上，权重量化 GEMM 的胜负手已经从「反量化算法」转向「如何与 TMEM、TMA、2-SM MMA 这些新硬件原语对齐」。谁能把权重摆放成硬件最想吃的方式，谁就赢，纯算法层面的优化空间在收窄。<br><br>
对普通用户而言，最实用的信号是：在 decode（小 batch）场景里它的优势其实有限，真正的杀手锏是 prefill 和大 batch，这也是为什么它最该被用在长上下文、高并发的 serving 上，而不是单机单请求聊天。
</div>
</div>

---

<span style="font-size:12px;color:#888888;font-family:'Courier New',monospace;">参考：https://blog.alpindale.net/posts/swordfish/</span>
