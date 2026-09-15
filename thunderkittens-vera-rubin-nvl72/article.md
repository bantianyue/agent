/* 传送门统一样式（add-portal.py 动态注入时引用此 class） */
.portal-title { font-size:12px; color:#888; }
.portal-links { font-size:12px; color:#888; }
.portal-links a { color:#888; text-decoration:none; }

要点速览

- 核心结论：Rubin 沿用 Blackwell 编程模型，老内核原样能跑，却只摸到 roofline 的 42%；要让张量核心吃饱，得同时放开 K 步长与片上存储。- 关键数据：NVFP4 GEMM 从 14.7 PFLOPS 提到 22.2 PFLOPS，64k 与 128k 方阵上提前释放 A 分别再提速 13.5% 与 22.1%。- 工程要点：2x1 CTA pair 复用 B 块、5 级共享内存流水线、B 侧收集器贡献主要收益，提前释放 A 只在大矩阵上生效。

GPU 内核库 ThunderKittens 最近拿到 NVIDIA Vera Rubin NVL72 的访问权限，团队用几天时间翻新 ISA、拿微基准戳芯片，把 NVFP4 与 FP8 GEMM 的支持补了进去。
Rubin 完整保留了 Blackwell 的编程模型，老内核跑得起来，但只摸到 roofline 的 42.1% 与 44.4%。要让张量核心吃满，K 步长、共享内存、张量内存三件事必须一起动。接下来是从 42% 推到 22 PFLOPS 的完整过程。

起点：一块 NVIDIA HGX B200 上的 GEMM
NVIDIA Blackwell 架构的第五代张量核心把 GEMM 的编程模型整个换了一遍。Hopper 上的 wgmma 指令由整个 warpgroup 集体发射，Blackwell 的 tcgen05 指令只需单个线程发射，一个小生产者 warp 就能驱动张量核心。累加器也从寄存器搬进张量内存，操作数直接从共享内存读取，单条 MMA 可以跨两个 SM、横跨两个 CTA。

图1：开篇插图，三只机器猫在 Vera Rubin 天文台架起望远镜观测猫形星座
为了在 Blackwell 上拿到有竞争力的性能，这个 GEMM 做了三件事：
启动线程块簇，让每对 CTA 通过 TMA 多播共享操作数，把 HBM 访存流量砍掉一半。
在簇内做 warp 分工：loader 用 TMA 把 A、B 搬进共享内存，单个 MMA warp 驱动张量核心，消费者 warpgroup 把算完的累加器从张量内存送回 HBM。
常驻执行，一个 tile 的输入还在流进来时，上一个 tile 的输出还在往外排。
靠这些手段，拿到了下面这组结果。

图2：NVFP4 GEMM 在 HGX B200 上的表现，按矩阵尺寸对比 ThunderKittens、cuBLASLt 与 CuTeDSL 的 TFLOPS

图3：FP8（E4M3）GEMM 在 HGX B200 上的表现，按矩阵尺寸对比 ThunderKittens、cuBLASLt 与 CuTeDSL 的 TFLOPS
关于这些内核和背后的优化，可以看早先的 Together 博客或者 ThunderKittens 2.0 发布说明。
Rubin 保留了 Blackwell 的编程模型，老内核原样还能跑。但直接放到 Vera Rubin 上，NVFP4 与 FP8 内核只跑到 roofline 的 42.1% 和 44.4%，可优化的空间还很大。

图4：TK B200 的 NVFP4 与 FP8 GEMM 跑在 Vera Rubin 上的 TFLOPS，按矩阵尺寸对比
后半部分分两步走：先讲 Rubin 里对 GEMM 重要的新特性以及它们在 ThunderKittens 里的用法，再把这些特性逐步集成进现有的 Blackwell NVFP4 内核，把它推到 22 PFLOPS 以上，与 cuBLAS 和 CuTE DSL 打平。
核心矛盾是：Rubin 让张量核心消费操作数的速度快了一倍，老的 Blackwell 内核却供不上。要摸到算力天花板，就得让每个 tile 从已经在片上的数据里榨出更多复用。
NVIDIA Vera Rubin 平台带来了什么？
对比厂商规格，从 Blackwell 到 Vera Rubin 的提升如下。
就写高性能 GEMM 而言，我们特别关注下面几项。

NVIDIA HGX B200NVIDIA Vera Rubin NVL72

NVFP4 张量核心9 PFLOPS / GPU35 PFLOPS / GPU
FP8 张量核心4.5 PFLOPS / GPU17.5 PFLOPS / GPU
FP16 / BF16 张量核心2.25 PFLOPS / GPU4 PFLOPS / GPU
显存带宽8 TB/s / GPU22 TB/s / GPU
SM 数量148 / GPU224 / GPU
峰值功耗1000W / GPU2300W / GPU

张量核心的 K 步长翻倍
先回顾一下，一条 tcgen05.mma 在 MxNxK 的 tile 上计算 C = A@B + C，每步沿 K 方向消费固定的字节数。Blackwell 上这一步是 32 字节，到了 Vera Rubin 可以提到 64 字节。MMA 本身占用的时钟周期数不变，所以 K 翻倍意味着同一个指令窗口里能塞进两倍的工作量。

图5：Blackwell 的 32 字节 K 步长与 Vera Rubin 的 64 字节 K 步长对比，单条指令覆盖的操作数块翻倍
在 ThunderKittens 里，这通过给原有 mma 操作新增一个模板参数来表达。
mma_ABt&nbsp;&nbsp;&nbsp;&nbsp;(...);&nbsp;&nbsp;&nbsp;//&nbsp;Blackwell&nbsp;Default:&nbsp;32-byte&nbsp;K&nbsp;stepmma_ABt&lt;64&gt;(...);&nbsp;&nbsp;&nbsp;//&nbsp;Vera&nbsp;Rubin:&nbsp;64-byte&nbsp;K&nbsp;step
张量内存扩展到 576 列
Blackwell 引入了张量内存的概念：128 lane x 512 列 x 32 bit 的空间，张量核心可以直接读写。到了 Vera Rubin，这个空间扩展到 576 列，多出 32 KiB 可以支配。
注意，多出来的列只有通过 .exclusive 限定符才能访问。这是 PTX 9.4 的新增特性，保证一个 SM 上只存在一个活跃的张量内存分配。非独占分配依然被限制在 512 列，且必须是 2 的幂。
在 ThunderKittens 里，用户可以给张量内存分配器加一个模板参数，声明这次分配是独占的。
template&lt;int&nbsp;_nblocks_per_sm,&nbsp;int&nbsp;_ncta,&nbsp;bool&nbsp;_managed&nbsp;=&nbsp;true,&nbsp;bool&nbsp;_exclusive&nbsp;=&nbsp;false&gt;struct&nbsp;tensor_allocator&nbsp;{&nbsp;....&nbsp;}tensor_allocator&lt;1,&nbsp;C::CLUSTER_SIZE,&nbsp;false&gt;&nbsp;tm;&nbsp;//&nbsp;Blackwell&nbsp;default:&nbsp;512&nbsp;columnstensor_allocator&lt;1,&nbsp;C::CLUSTER_SIZE,&nbsp;false,&nbsp;true&gt;&nbsp;&nbsp;tm;&nbsp;//&nbsp;Rubin:&nbsp;Up&nbsp;to&nbsp;576&nbsp;columns
共享内存提升到 328 KiB
Hopper 和 Blackwell 提供 228 KiB 共享内存，Vera Rubin 引入了超规格共享内存模式，可以动态增加到 328 KiB。这是主机侧设置，调用方式如下。
CUfunction&nbsp;function&nbsp;=&nbsp;nullptr;cudaGetFuncBySymbol(&amp;function,reinterpret_cast&lt;const&nbsp;void*&gt;(kernel));cuFuncSetAttribute(function,&nbsp;CU_FUNC_ATTRIBUTE_SHARED_MEMORY_MODE,&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;CU_SHARED_MEMORY_MODE_ALLOW_OVERSIZED_SHARED_MEMORY);
B 侧收集器
Blackwell 引入了收集器缓冲区的概念：一个很小的 MMA 暂存区，可以锁住 A tile，让下一条指令直接从缓冲区取数，而不必再访问共享内存。Vera Rubin 把这项能力扩展到了 B tile，对应 .collector::b::*。

图6：两条 MMA 共用一个收集器缓冲区，B 块只取一次（FILL）后复用（LASTUSE），无需二次搬取
要用起来，就给每条 MMA 的操作数标注四种标签之一，说明它对收集器缓冲区做了什么。
「FILL」从共享内存读取操作数并锁存。
「USE」从缓冲区读取。
「LASTUSE」从缓冲区读取并释放。
「DISCARD」是默认值，跳过锁存。
这些标签是复用的许可，不是保证。张量核心即便拿到了复用许可，依然可能重新加载一次矩阵。
既然两个操作数都能常驻收集器缓冲区，就可以试一些新玩法。比如在 2x2 分块上，两侧都做收集，四条 MMA 的操作数读取从八次降到五次。

图7：2x2 MMA 分块下双侧收集器锁存，用 512 周期的端口取数平衡 512 周期的计算
在 ThunderKittens 里可以这样写。
mma2_ABt_chunk&lt;64,&nbsp;false,&nbsp;false,&nbsp;collector::FILL,collector::DISCARD&gt;(C[0][0],&nbsp;a0,&nbsp;b0,&nbsp;...);mma2_ABt_chunk&lt;64,&nbsp;false,&nbsp;false,&nbsp;collector::LASTUSE,&nbsp;collector::FILL&nbsp;&nbsp;&nbsp;&gt;(C[0][1],&nbsp;a0,&nbsp;b1,&nbsp;...);mma2_ABt_chunk&lt;64,&nbsp;false,&nbsp;false,&nbsp;collector::FILL,&nbsp;&nbsp;&nbsp;&nbsp;collector::LASTUSE&gt;(C[1][1],&nbsp;a1,&nbsp;b1,&nbsp;...);mma2_ABt_chunk&lt;64,&nbsp;false,&nbsp;false,&nbsp;collector::LASTUSE,&nbsp;collector::DISCARD&gt;(C[1][0],&nbsp;a1,&nbsp;b0,&nbsp;...);
提前释放 A
tcgen05.commit 会在它处理的 MMA 结束后抵达 mbarrier，通知生产者某个 stage 槽位已经可以复用。PTX 9.4 引入了 tcgen05.commit.sync_restrict::shared::read::mma::a，让 A tile 的信号可以提前发出：不必等 MMA 整体退休，只要 MMA 把 A 操作数从共享内存读完，就可以触发屏障，进而通知 TMA loader 开始写下一个 stage 的数据。

图8：提前释放 A 的时序，MMA 读完 A 即触发屏障，早于 MMA 整体退休
ThunderKittens 新增了一种 commit 类型来表达它。
tensor_commit&lt;2&gt;&nbsp;(inputs_finished[stage],&nbsp;mask);&nbsp;//&nbsp;arrives&nbsp;when&nbsp;MMA&nbsp;retirestensor_aread_commit&lt;2&gt;(A_finished[slot],&nbsp;mask);&nbsp;//&nbsp;arrives&nbsp;when&nbsp;MMA&nbsp;finishes&nbsp;reading&nbsp;A
构建 GEMM
现在手上有了一组新特性和一个 Blackwell GEMM。下面几节把它们逐个集成进原有内核，并解释为什么迁移到 Vera Rubin 时这些改动非做不可。
加宽指令
最直观的瓶颈来自仍然沿用 Blackwell 的 32 字节 K 步长。在 Vera Rubin 上，这种编码的 ISA 上限约为 16.8 PFLOPS，而我们的 NVFP4 Blackwell 内核开箱就能跑到 14.7 PFLOPS，已经是上限的 88%。要继续往上走，就必须让 MMA 一次处理两倍的 K 字节。

图9：32 字节 K 步长的内核跑到 14,741 TFLOPS，为 16.8 PFLOPS 上限的 88%，而 64 字节步长的上限是 35 PFLOPS
然而，只是给现有 Blackwell 内核打开更宽的编码，性能提升非常有限，远达不到预期的 2 倍。更宽的 MMA 只让张量核心消费操作数的速度快了一倍，并没有解决供数速度。要让双倍 K 真正有用，得同时拉两个杠杆：搬更少的字节，以及加深流水线把这些搬运掩盖掉。
少读字节
要少读字节，就在同一个 CTA pair 上沿 M 方向再叠一个输出 tile。两个累加器只在 M 上不同，因此可以共用同一块 B。原来的 Blackwell NVFP4 内核用的是 1x1 分块，覆盖 M512xN256 的输出需要两个 pair 任务，各自独立搬运一份 B。改成 2x1 之后，B 只取一次就能覆盖同样的输出，操作数流量随之下降。

图10：2x1 分块布局，两个 M 方向分块（A0、A1）共用同一份 B，产出 512x256 的累加器区域
2x1 分块在 NVFP4 Blackwell 内核上并不容易做到，因为张量内存当时被限制在 256 KiB。两个 M256xN256 的累加器已经占满 512 列，块缩放 MMA 就没有空间存放 A、B 的缩放因子。程序员可以绕过去：让 epilogue warp 只加载累加器的一部分列就发出 MMA 空闲信号，让下一个 K tile 的 MMA 提前开始，但这会引入一段藏不住的延迟。有了 Vera Rubin 多出的 64 列，缩放因子可以直接放下，不必再跳这支舞。

图11：张量内存的列占用，两个累加器加 A/B 缩放因子共 560 列，对比 Blackwell 的 512 列上限
加深流水线
分块格式的变化降低了操作数流量，但并没有缩短每次取数的耗时。下一个挑战是让张量核心始终有数据可吃。Vera Rubin 更大的共享内存允许我们建更深的流水线，提前把更多 tile 排进缓冲，给搬运留出更多完成时间。对 NVFP4 和 FP8 的 16k 方阵 GEMM 扫描环深度，结果如下。
NVFP4 16k 方阵 GEMM：

共享内存级数所需共享内存实测 TFLOPS

3202 KiB17,054
4258 KiB20,595
5314 KiB22,239

FP8（E4M3）的环深度扫描
FP8（E4M3）16k 方阵 GEMM 的扫描结果：

配置所需共享内存实测 TFLOPS

4209 KiB10,895
5257 KiB11,995
6305 KiB11,288

三类优化各自贡献多少
最大的收益来自最后这一级台阶，但前提是前面的优化已经就位。下面是把 K 步长、共享内存流水线和分块策略分别单独扫描的结果。

图12：NVFP4 16,384 方阵 GEMM 的 TFLOPS 随每 CTA 共享内存变化，三条曲线分别对应 2x1/1x1 与 64 字节/32 字节配置
最后的调优
要把内核再往前推一点，还调了几个旋钮。
内核配置调优：针对不同负载继续调参。在 CTA pair 尺寸上，原来的 1x1 tile 格式在较小的方阵负载上表现最好；更大的形状则换成 2x1 CTA pair 分块，配合 2、4 或 8 的簇大小。此外，所有形状都会打乱 tile 的光栅化顺序，改善访存局部性。
B 侧收集器：既然走的是 2x1 分块，就可以用上 B 侧收集器。一条 MMA 标「FILL」、下一条标「LASTUSE」，B 的读取次数从两次降到一次，实测带来 1% 到 3% 的提升。
用上 sync_restrict::shared::read::mma::a：在 64k 和 128k 的方阵 NVFP4 GEMM 上，提前释放 A 分别带来 13.5% 和 22.1% 的加速。这个指令在大尺寸下有用，是因为 A tile 会和其他资源争抢驻留位置，行数据在两次复用之间被逐出，loader 只能等它回来；小块场景下 A tile 根本不会离开 L2，读取本来足够快，不需要提前释放。要用这条指令，还得改掉传统的环序逻辑：普通 GEMM 里 A、B 属于同一个环，由同一条 commit 锁步驱动；而提前释放 A 需要把两者解耦，让 A 的加载独立进行。A 的槽位必须更早释放，所以给 A 单独一个环，配一对 arrived/finished 屏障。
L2 逐出提示：把 A 操作数标记为 EVICT_LAST，鼓励它们留在 L2 里供后续任务复用。这份收益来自任务之间而非簇内，量级在千分之几。
结果
最终在 Vera Rubin 上跑出来的性能如下。

图13：NVFP4 GEMM 在 Vera Rubin 上的最终 TFLOPS，按矩阵尺寸对比 ThunderKittens、cuBLASLt 与 CuTeDSL

图14：FP8 GEMM 在 Vera Rubin 上的最终 TFLOPS，按矩阵尺寸对比 ThunderKittens、cuBLASLt 与 CuTeDSL
以上所有测量都在 NVIDIA CUDA 13.4 与 Qualification Sample（QS）GPU 上完成。随着 Vera Rubin 软件版本迭代，所有基线的性能预计还会继续提升。

【传送门】

Kimi K3技术详解之KDA: 线性注意力如何精准编辑被压缩的记忆
TokenSpeed-Kernel：把推理内核做成一等公民
vLLM+Mooncake: 把agentic前缀复用从1.7%拉到92.2%
Kimi K3技术报告-后训练Infra: 三阶段 RL,MoonEP3,五千万沙箱,KDA感知缓存
RL的下一个大突破：不是优化可验证问题而是把'不可验证'领域变得'可验证'
Kimi K3技术解析之LatentMoE: 隐藏维度压缩至潜空间，通信与带宽开销同比例骤降
AI芯片架构全景: 从NVIDIA到 Groq的六条设计路线
Torch Profiler在Trace里分析性能瓶颈: 剖析SGLang LLM推理
MLP就是Hebbian记忆: 无需训练，往Transformer块注入事实知识的构造方法
Kimi K3技术解析之AttnRes: 打破Transformer沿用十年的残差各层等权的假设
把KVCache变成可训练记忆：Context Tuning让LLM免权重微调
英伟达Kernel Agent: 编译器与算子调优Agent的协同设计
小米MiMo罗福莉:8卡GPU让1T参数模型跑出1000 TPS , FP4+DFlash+TileRT全解读
在NVFP4上超越cuBLAS: 从零手写+Claude极限优化Blackwell GEMM
阿里Sparse Attention on CXL替代RDMA做KV Cache解耦 推理2.1×吞吐, 9.7×TTFT
KVCache缝合术: 突破前缀匹配天花板,首Token快14倍 多文档快2~4倍

结语

新硬件保留老编程模型，不等于老内核还能吃到新硬件的性能。 Rubin 沿用 Blackwell 的 tcgen05 编程模型，老 GEMM 一行不改就能跑，但它离算力上限还差着一半以上；真正的提升来自把三类片上资源重新分配：K 步长翻倍、张量内存多出的 64 列、共享内存扩到 328 KiB。收益的排序也值得参考：2x1 分块复用 B 块、5 级共享内存流水线、B 侧收集器贡献了主要增益，提前释放 A 只在 64k 与 128k 这类大矩阵上才显出 13.5% 与 22.1% 的威力。当硬件把操作数消费速度翻倍，瓶颈必然挪到供数侧，把片上存储当成流水线资源来调度，才是这一代张量核心的正确打开方式。

参考：https://www.together.ai/blog/to-infinity-and-beyond-thunderkittens-now-on-nvidia-vera-rubin-nvl72