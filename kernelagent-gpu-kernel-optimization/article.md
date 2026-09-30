/* 传送门统一样式（add-portal.py动态注入时引用此class；真身在内联style，class仅兜底） */
.portal-title { font-size:12px; color:#1a6ba0; font-weight:bold; }
.portal-links { font-size:12px; color:#0F4C81; }
.portal-links a { color:#0F4C81; text-decoration:none; }

要点速览

- 核心突破：KernelAgent在正确性流水线之上叠加硬件感知优化层，100个KernelBench L1任务几何平均加速2.02倍，相对开箱即用torch.compile加速1.56倍，H100上达到89% roofline效率。- 关键数据：65/100个L1任务超越torch.compile；矩阵向量乘法案例从9.52ms优化到1.95ms，DRAM吞吐从631 GB/s爬升到2229 GB/s。- 方法创新：Profile到Measure六阶段闭环，六类智能体分工协作，用Nsight Compute硬件信号驱动，跨轮共享记忆沉淀经验、避免重复踩坑。

手写GPU内核优化是专家密集型工作：要懂体系结构、存储层次和性能权衡，新硬件一出优化策略就得重想，一个内核调优动辄数天到数周。
KernelAgent把这套专家工作流拆成六个协作智能体，用Nsight Compute硬件信号驱动诊断、开方、探索、实测的闭环。下文完整呈现六阶段流水线、矩阵向量乘法的端到端优化案例，以及H100上的实测数据。

引言
GPU内核优化对现代AI负载越来越关键。模型越来越大、越来越专用，性能瓶颈往往不在高层算法，而在实现这些算法的内核效率。
但手动优化内核是专家密集型工作：要深懂GPU体系结构、存储层次和性能权衡。更麻烦的是，每出一代新GPU架构，优化策略就得重新思考。
实践中，有经验的内核工程师遵循一套系统化工作流：用NVIDIA Nsight Compute做profile，查看硬件性能计数器诊断瓶颈，再针对性地应用优化。是寄存器压力拖累了occupancy？tiling策略浪费了访存带宽？内核需要的是架构重设计，还是调调参数就行？这个过程要推理多个瓶颈各异的内核架构，才能收敛到榨干硬件的设计，通常耗时数天到数周。
现代编译器栈在自动化内核生成上进展显著：torch.compile抓取计算图，用图变换、模式匹配和编译器启发式生成Triton内核；TVM、XLA等系统类似，覆盖了很多常见模式，开箱性能不错。但多数编译器启发式基于静态模型，而不是来自真实硬件执行的直接测量。
KernelAgent要自动化的，正是这个诊断驱动的优化循环：一切扎根真实硬件信号。它瞄准前向（推理）内核，因为那里的延迟和吞吐直接决定服务成本和用户体验。
KernelAgent优化工作流
KernelAgent把专家已经在用的工作流（profile、诊断瓶颈、提优化、迭代）自动化，拆成一组协作智能体。每个智能体负责优化循环中定义明确的一个阶段，合起来形成闭环的硬件感知反馈系统。
从输入内核开始，KernelAgent反复做：profile内核、诊断性能瓶颈、开架构感知的优化处方、综合优化知识、并行探索替代优化路径、实测每个候选。箭头表示各优化轮次之间智能体的信息流。
高层看，每轮优化由六个阶段组成：Profile到Diagnose到Prescribe到Orchestrate到Explore到Measure。每个阶段产出结构化输出，直接喂给下一阶段，实现快速的数据驱动迭代。

图1:KernelAgent六智能体优化闭环：ProfilerAgent采集硬件信号，JudgeAgent诊断瓶颈，AnalyzerAgent开优化处方，OrchestratorAgent综合知识定搜索策略，Optimization Manager并行探索，BenchmarkAgent实测验证。
数据如何流经系统
下面按六个阶段展开，看数据如何在智能体之间流动。
Profiling:采集硬件信号
优化循环从Profiling Agent用NVIDIA Nsight Compute检查输入内核开始。KernelAgent集成NCU采集硬件级性能指标，包括DRAM吞吐与利用率、L2缓存命中率、warp占用与stall原因、计算与tensor core利用率，以及SOL指标。这些指标是所有下游决策的经验基础。
输入：内核代码加输入规约（形状、dtype）。输出：硬件指标的结构化字典。
示例输出：
{&nbsp;&nbsp;&nbsp;"sm__inst_executed_pipe_tensor.avg.pct_of_peak_sustained_active":&nbsp;0.41,&nbsp;&nbsp;&nbsp;"smsp__warp_issue_stalled_short_scoreboard_per_warp_active.pct":&nbsp;5.63,&nbsp;&nbsp;&nbsp;"gpu__compute_memory_throughput.avg.pct_of_peak_sustained_elapsed":&nbsp;48.86&nbsp;&nbsp;...}
Diagnosis:用roofline分析定位瓶颈
Diagnose Agent解读profiling指标，给内核的主导性能瓶颈分类。它用SOL指标做roofline风格分析，再结合LLM推理做根因分析。
输入：NCU指标加当前内核代码。输出：BottleneckReport，包含主瓶颈类别、效率百分比、带证据的根因。
示例诊断：
"category":&nbsp;"memory","summary":&nbsp;"Kernel&nbsp;is&nbsp;memory-bound&nbsp;at&nbsp;70.3%&nbsp;DRAM&nbsp;throughput&nbsp;with&nbsp;significant&nbsp;long&nbsp;scoreboard&nbsp;stalls&nbsp;from&nbsp;memory&nbsp;latency","reasoning":&nbsp;"The&nbsp;roofline&nbsp;analysis&nbsp;shows&nbsp;Memory&nbsp;SOL&nbsp;at&nbsp;70.3%&nbsp;while&nbsp;Compute&nbsp;SOL&nbsp;is&nbsp;only&nbsp;45.2%...","root_causes":&nbsp;[&nbsp;&nbsp;&nbsp;&nbsp;{&nbsp;"cause":&nbsp;"High&nbsp;memory&nbsp;latency&nbsp;stalls&nbsp;due&nbsp;to&nbsp;long&nbsp;scoreboard&nbsp;waits&nbsp;blocking&nbsp;warp&nbsp;execution",&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"evidence":&nbsp;[&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{"metric":&nbsp;"smsp__warp_issue_stalled_long_scoreboard_per_warp_active.pct",&nbsp;"value":&nbsp;37.69,&nbsp;"interpretation":&nbsp;"37.7%&nbsp;of&nbsp;warp&nbsp;stalls&nbsp;are&nbsp;due&nbsp;to&nbsp;waiting&nbsp;for&nbsp;memory&nbsp;operations,&nbsp;indicating&nbsp;memory&nbsp;latency&nbsp;is&nbsp;a&nbsp;significant&nbsp;bottleneck"},&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{"metric":&nbsp;"sm__warps_active.avg.pct_of_peak_sustained_active",&nbsp;"value":&nbsp;30.08,&nbsp;"interpretation":&nbsp;"Only&nbsp;30%&nbsp;warp&nbsp;occupancy&nbsp;suggests&nbsp;insufficient&nbsp;parallelism&nbsp;to&nbsp;hide&nbsp;memory&nbsp;latency"}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;]...&nbsp;&nbsp;&nbsp;&nbsp;},
Prescribing:架构感知的优化处方
给定诊断出的瓶颈，Analyzer（Prescriber）Agent生成具体、架构感知的优化建议。它结合瓶颈分类、GPU规格（比如A100对比H100）、从精选优化模式库检索到的模式，给目标硬件量身定做建议。
输入：BottleneckReport加GPU规格加优化数据库加内核代码。输出：带理由的处方列表。
示例处方：
"recommended_fixes":&nbsp;[&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{"fix":&nbsp;"Increase&nbsp;pipeline&nbsp;depth&nbsp;with&nbsp;more&nbsp;stages&nbsp;(num_stages=4-5)&nbsp;and&nbsp;reduce&nbsp;register&nbsp;pressure&nbsp;by&nbsp;using&nbsp;smaller&nbsp;BLOCK_K&nbsp;or&nbsp;enabling&nbsp;register&nbsp;spilling&nbsp;to&nbsp;shared&nbsp;memory",&nbsp;&nbsp;&nbsp;&nbsp;"rationale":&nbsp;"More&nbsp;pipeline&nbsp;stages&nbsp;help&nbsp;hide&nbsp;memory&nbsp;latency&nbsp;by&nbsp;overlapping&nbsp;loads&nbsp;with&nbsp;computation.&nbsp;Reducing&nbsp;register&nbsp;usage&nbsp;from&nbsp;91&nbsp;per&nbsp;thread&nbsp;would&nbsp;allow&nbsp;more&nbsp;concurrent&nbsp;warps&nbsp;to&nbsp;better&nbsp;hide&nbsp;the&nbsp;37.7%&nbsp;long&nbsp;scoreboard&nbsp;stalls&nbsp;and&nbsp;improve&nbsp;the&nbsp;30%&nbsp;warp&nbsp;occupancy"}...&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;]
Orchestration:把分析变成搜索策略
Orchestrator Agent综合当前诊断和历史优化数据，为下一轮制定具体的搜索策略。它聚合历史诊断、处方和结果，结合搜索策略（beam search、greedy search等），决定下一轮探索哪些处方。
每轮结束后，KernelAgent生成结构化自我分析：诊断对了吗？处方命中根因了吗？什么有效、为什么？这就是inference-time learning。
输入：处方加尝试历史加Reflexion。输出：定稿的优化提示词。
示例reflexion：
"was_diagnosis_correct":&nbsp;true,&nbsp;&nbsp;&nbsp;&nbsp;"was_fix_effective":&nbsp;false,&nbsp;&nbsp;&nbsp;&nbsp;"expected_outcome":&nbsp;"...should&nbsp;reduce&nbsp;memory&nbsp;latency&nbsp;stalls&nbsp;by&nbsp;allowing&nbsp;more&nbsp;in-flight&nbsp;memory&nbsp;operations,&nbsp;improving&nbsp;memory&nbsp;throughput&nbsp;and&nbsp;reducing&nbsp;warp&nbsp;stalls",&nbsp;&nbsp;&nbsp;&nbsp;"actual_outcome":&nbsp;"Performance&nbsp;degraded&nbsp;significantly&nbsp;by&nbsp;37.4%&nbsp;(1.0910ms&nbsp;to&nbsp;1.4996ms)....",&nbsp;&nbsp;&nbsp;&nbsp;"reasoning":&nbsp;"The&nbsp;fix&nbsp;backfired&nbsp;because:&nbsp;1)&nbsp;Doubling&nbsp;BLOCK_N&nbsp;(128&nbsp;to&nbsp;256)&nbsp;and&nbsp;BLOCK_K&nbsp;(32&nbsp;to&nbsp;64)&nbsp;dramatically&nbsp;increased&nbsp;shared&nbsp;memory&nbsp;and&nbsp;register&nbsp;usage&nbsp;per&nbsp;block,&nbsp;likely&nbsp;reducing&nbsp;occupancy&nbsp;significantly....",&nbsp;&nbsp;&nbsp;&nbsp;"lessons":&nbsp;[&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"Increasing&nbsp;BLOCK_N&nbsp;and&nbsp;BLOCK_K&nbsp;together&nbsp;with&nbsp;num_stages&nbsp;creates&nbsp;compound&nbsp;pressure&nbsp;on&nbsp;shared&nbsp;memory&nbsp;and&nbsp;registers",&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;...&nbsp;&nbsp;&nbsp;&nbsp;],&nbsp;&nbsp;&nbsp;&nbsp;"avoid_patterns":&nbsp;[&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"Simultaneously&nbsp;increasing&nbsp;multiple&nbsp;tile&nbsp;dimensions&nbsp;(BLOCK_N,&nbsp;BLOCK_K)&nbsp;along&nbsp;with&nbsp;pipeline&nbsp;stages",&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;...&nbsp;&nbsp;&nbsp;&nbsp;],&nbsp;&nbsp;&nbsp;&nbsp;"try_patterns":&nbsp;[&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"Try&nbsp;smaller&nbsp;BLOCK_K&nbsp;(16&nbsp;or&nbsp;32)&nbsp;with&nbsp;increased&nbsp;num_stages&nbsp;to&nbsp;reduce&nbsp;register&nbsp;pressure&nbsp;while&nbsp;improving&nbsp;pipelining",&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;...
Exploration:并行优化
Optimization Manager执行探索阶段。它维护top-K内核，每个内核派多个优化worker并行尝试不同处方。一条优化路径掉坑，另一条试不同处方的worker可能走通，避免搜索卡在局部最优。每个worker应用不同优化、编译内核，交给Measure阶段。
输入：候选内核加不同优化方案。输出：编译好的优化内核，待评测。
示例结果：
BeamSearch&nbsp;initialized:&nbsp;2&nbsp;kernels&nbsp;x&nbsp;2&nbsp;bottlenecks&nbsp;=&nbsp;4&nbsp;workers---------------------------------------Round&nbsp;1:&nbsp;4/4&nbsp;workers&nbsp;succeeded--------------------------------Round&nbsp;2:&nbsp;3/4&nbsp;workers&nbsp;succeeded...
Measure:验证正确性与性能
Benchmarking Agent验证正确性，并实测探索阶段每个候选内核的真实性能。每个候选先对可信参考实现做正确性检查，通过验证才进入benchmark。用受控的benchmark协议保证稳定、可复现。
性能测量：warmup 25次排除冷启动影响，重复100次取稳定值，共享benchmark锁防止worker之间GPU争用。
输入：编译好的内核变体、参考实现、测试输入。输出：正确性结论、实测内核运行时间。
示例结果：
Round&nbsp;1:&nbsp;4&nbsp;successful,&nbsp;best&nbsp;new:&nbsp;7.8000msRound&nbsp;2:&nbsp;4&nbsp;successful,&nbsp;best&nbsp;new:&nbsp;4.0457msRound&nbsp;3:&nbsp;4&nbsp;successful,&nbsp;best&nbsp;new:&nbsp;3.1118ms...
性能总结
用triton.testing.do_bench做一致的性能测量，H100上每个内核变体100次重复取均值（1秒以上warmup）。对比两个基线：KernelAgent纯正确性循环生成的内核（早前基线）；开箱即用torch.compile（PyTorch Inductor默认模式，静态形状，CUDA graphs关闭）。
100个L1任务上，KernelAgent在65个任务上超越torch.compile。几何平均：相对早前纯正确性基线加速2.02倍，相对开箱即用torch.compile加速1.56倍。在NVIDIA H100上达到89%硬件roofline效率，其中roofline效率取计算SOL和访存SOL的较高者，即流多处理器或访存吞吐占硬件峰值的比例，经Nsight Compute测得。
端到端优化产物已在开源仓库分享；还在每类挑几个内核测了不同输入形状，12个内核乘144个形状，加速比类似。
测试时扩展效应：首轮拿走大部分性能收益，说明硬件诊断加粗粒度修复见效快；但增加轮次后系统继续稳步爬坡。轮次越多，KernelAgent越能hill climb超越初始改进，打磨早期优化、挖掘主瓶颈解决后才显形的次级瓶颈。这正是迭代反馈式优化的价值。

图2:各轮带来性能提升的内核数：首轮75个内核获益最大，随后逐轮递减，系统持续爬坡挖掘次级瓶颈。
案例:矩阵向量乘法
下面用一个端到端案例，看KernelAgent在不同轮次学到并应用了哪些优化技术。
配置：操作C = A @ x；形状M=2048，K=1,048,576；dtype为BF16输入、FP32累加、BF16输出；硬件H100。
结果总览：PyTorch compile基线2.09ms；KernelAgent纯正确性pipeline 9.52ms；LLM基线（直接prompt、无硬件反馈，8轮串行，opus-4.5）最优3.1985ms；KernelAgent优化层（4 worker，8轮，opus-4.5）最优1.95ms。

图3:矩阵向量乘法8轮优化收敛曲线：KernelAgent稳步降到1.95ms，纯LLM基线震荡剧烈且困在局部最优。
关键洞见
第一，LLM里的启发式优化知识是有效的，比如大block提带宽。但没有性能反馈，这些启发式把内核带到局部最优就失效了，因为LLM感知不到自己正在走的性能权衡曲线。
第二，没有结构化探索，LLM被锁死在seed内核的轨迹里。它从没想过从split-K切到更简单的one-row-per-thread设计，连eager的性能都超不过。
第三，KernelAgent的多worker探索、基于profiling的方法、反思式知识共享，能尝试不同路线并找到最优路径。
为什么基线慢
初始Triton内核用2D tile加向量累加器。profiling显示内核主要被寄存器限制occupancy，发不出足够并发访存请求来掩盖DRAM延迟。
第一轮改进:先降寄存器压力
瓶颈：寄存器压力限制occupancy，SM利用不足。处方：大向量累加器换标量累加器，每program处理少量行，提高grid并行。性能：9.52ms到6.80ms，occupancy涨8倍，Memory SOL从18.5%升到25.8%。反思：先把寄存器状态降下来，其他优化才有效。
#&nbsp;NUM_ROWS=4:&nbsp;four&nbsp;scalar&nbsp;accumulators&nbsp;instead&nbsp;of&nbsp;a&nbsp;vectoracc0&nbsp;=&nbsp;0.0acc1&nbsp;=&nbsp;0.0acc2&nbsp;=&nbsp;0.0acc3&nbsp;=&nbsp;0.0for&nbsp;k0&nbsp;in&nbsp;range(0,&nbsp;K,&nbsp;BLOCK_K):&nbsp;&nbsp;&nbsp;&nbsp;#&nbsp;Load&nbsp;B&nbsp;vector&nbsp;tile&nbsp;once&nbsp;[BLOCK_K]&nbsp;&nbsp;&nbsp;&nbsp;b&nbsp;=&nbsp;tl.load(b_ptrs,&nbsp;mask=k_mask,&nbsp;other=0.0).to(tl.float32)&nbsp;&nbsp;&nbsp;&nbsp;#&nbsp;Process&nbsp;each&nbsp;row&nbsp;individually&nbsp;with&nbsp;its&nbsp;own&nbsp;1D&nbsp;load&nbsp;&nbsp;&nbsp;&nbsp;if&nbsp;row_start&nbsp;+&nbsp;0&nbsp;&lt;&nbsp;M:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;a0&nbsp;=&nbsp;tl.load(a_ptr&nbsp;+&nbsp;(row_start&nbsp;+&nbsp;0)&nbsp;*&nbsp;stride_am&nbsp;+&nbsp;offs_k&nbsp;*&nbsp;stride_ak,&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;mask=k_mask,&nbsp;other=0.0).to(tl.float32)&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;acc0&nbsp;+=&nbsp;tl.sum(a0&nbsp;*&nbsp;b)&nbsp;&nbsp;&nbsp;&nbsp;if&nbsp;row_start&nbsp;+&nbsp;1&nbsp;&lt;&nbsp;M:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;a1&nbsp;=&nbsp;tl.load(a_ptr&nbsp;+&nbsp;(row_start&nbsp;+&nbsp;1)&nbsp;*&nbsp;stride_am&nbsp;+&nbsp;offs_k&nbsp;*&nbsp;stride_ak,&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;mask=k_mask,&nbsp;other=0.0).to(tl.float32)&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;acc1&nbsp;+=&nbsp;tl.sum(a1&nbsp;*&nbsp;b)&nbsp;&nbsp;&nbsp;&nbsp;#&nbsp;...&nbsp;(acc2,&nbsp;acc3&nbsp;similar)#&nbsp;Launch&nbsp;config:&nbsp;BLOCK_K=512,&nbsp;NUM_ROWS=4,&nbsp;num_warps=4,&nbsp;num_stages=4#&nbsp;Grid:&nbsp;(cdiv(M,&nbsp;4),)&nbsp;=&nbsp;(512,)
第二轮改进:给向量x加缓存
瓶颈：仍被访存延迟主导，提升进入平台期。处方：给向量x加有限缓存和复用，减少冗余全局访存；别加num_stages，之前已经涨过寄存器压力。性能：6.80ms到6.20ms，共享内存缓存B向量带来温和收益。反思：矩阵向量乘和GEMM很不一样，tiling策略不能直接搬。
第三轮改进:向量化2D load,严格控寄存器
瓶颈：寄存器压力降下来后，卡在低效访存事务，而不是缺warp。处方：回到向量化2D load改善合并，但严格控寄存器：小tile（BLOCK_M=32）、大K tile（BLOCK_K=512）、num_stages=1消除流水线寄存器开销。性能：6.20ms到4.03ms。反思：先把寄存器状态降下来，其他优化才有效。
#&nbsp;Before:&nbsp;sequential&nbsp;scalar&nbsp;accumulators,&nbsp;NUM_ROWS=4#&nbsp;acc0&nbsp;=&nbsp;0.0;&nbsp;acc1&nbsp;=&nbsp;0.0;&nbsp;acc2&nbsp;=&nbsp;0.0;&nbsp;acc3&nbsp;=&nbsp;0.0#&nbsp;...process&nbsp;rows&nbsp;one&nbsp;at&nbsp;a&nbsp;time&nbsp;with&nbsp;branching...@triton.jitdef&nbsp;matvec_kernel(A_ptr,&nbsp;x_ptr,&nbsp;C_ptr,&nbsp;M,&nbsp;K,&nbsp;stride_am,&nbsp;stride_ak,&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;BLOCK_SIZE_M:&nbsp;tl.constexpr,&nbsp;BLOCK_SIZE_K:&nbsp;tl.constexpr):&nbsp;&nbsp;&nbsp;&nbsp;pid_m&nbsp;=&nbsp;tl.program_id(0)&nbsp;&nbsp;&nbsp;&nbsp;row_start&nbsp;=&nbsp;pid_m&nbsp;*&nbsp;BLOCK_SIZE_M&nbsp;&nbsp;&nbsp;&nbsp;row_offsets&nbsp;=&nbsp;row_start&nbsp;+&nbsp;tl.arange(0,&nbsp;BLOCK_SIZE_M)&nbsp;&nbsp;&nbsp;&nbsp;row_mask&nbsp;=&nbsp;row_offsets&nbsp;&lt;&nbsp;M&nbsp;&nbsp;&nbsp;&nbsp;#&nbsp;Back&nbsp;to&nbsp;vector&nbsp;accumulator,&nbsp;but&nbsp;only&nbsp;32&nbsp;elements&nbsp;(not&nbsp;128)&nbsp;&nbsp;&nbsp;&nbsp;acc&nbsp;=&nbsp;tl.zeros((BLOCK_SIZE_M,),&nbsp;dtype=tl.float32)&nbsp;&nbsp;&nbsp;&nbsp;for&nbsp;k_start&nbsp;in&nbsp;range(0,&nbsp;K,&nbsp;BLOCK_SIZE_K):&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;k_offsets&nbsp;=&nbsp;k_start&nbsp;+&nbsp;tl.arange(0,&nbsp;BLOCK_SIZE_K)&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;k_mask&nbsp;=&nbsp;k_offsets&nbsp;&lt;&nbsp;K&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;x_vals&nbsp;=&nbsp;tl.load(x_ptr&nbsp;+&nbsp;k_offsets,&nbsp;mask=k_mask,&nbsp;other=0.0)&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;a_ptrs&nbsp;=&nbsp;A_ptr&nbsp;+&nbsp;row_offsets[:,&nbsp;None]&nbsp;*&nbsp;stride_am&nbsp;+&nbsp;k_offsets[None,&nbsp;:]&nbsp;*&nbsp;stride_ak&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;a_vals&nbsp;=&nbsp;tl.load(a_ptrs,&nbsp;mask=row_mask[:,&nbsp;None]&nbsp;&amp;&nbsp;k_mask[None,&nbsp;:],&nbsp;other=0.0)&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;acc&nbsp;+=&nbsp;tl.sum(a_vals.to(tl.float32)&nbsp;*&nbsp;x_vals.to(tl.float32)[None,&nbsp;:],&nbsp;axis=1)&nbsp;&nbsp;&nbsp;&nbsp;tl.store(C_ptr&nbsp;+&nbsp;row_offsets,&nbsp;acc.to(tl.bfloat16),&nbsp;mask=row_mask)#&nbsp;Launch:&nbsp;BLOCK_SIZE_M=32,&nbsp;BLOCK_SIZE_K=512,&nbsp;num_stages=1,&nbsp;num_warps=4#&nbsp;Grid:&nbsp;(cdiv(M,&nbsp;32),)&nbsp;=&nbsp;(64,)
最终改进:one-row-per-program架构跃迁
瓶颈：寄存器压力限制occupancy，SM利用不足。处方：做架构变更，一行一个program：标量累加器（寄存器最少）、超大grid并行（2048个program）、纯1D流式load、大BLOCK_K摊销循环开销。性能：4.03ms到1.95ms，warp active约95%。反思：这个负载本质是访存带宽bound，最大化occupancy和并行比tiling优雅更重要；逃离局部最优有时需要架构变更。
@triton.jitdef&nbsp;matvec_kernel(A_ptr,&nbsp;x_ptr,&nbsp;C_ptr,&nbsp;M,&nbsp;K,&nbsp;stride_am,&nbsp;stride_ak,&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;BLOCK_SIZE_K:&nbsp;tl.constexpr):&nbsp;&nbsp;&nbsp;&nbsp;pid_m&nbsp;=&nbsp;tl.program_id(0)&nbsp;&nbsp;&nbsp;&nbsp;if&nbsp;pid_m&nbsp;&gt;=&nbsp;M:&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;return&nbsp;&nbsp;&nbsp;&nbsp;#&nbsp;Scalar&nbsp;accumulator:&nbsp;minimal&nbsp;register&nbsp;usage&nbsp;&nbsp;&nbsp;&nbsp;acc&nbsp;=&nbsp;0.0&nbsp;&nbsp;&nbsp;&nbsp;a_row_ptr&nbsp;=&nbsp;A_ptr&nbsp;+&nbsp;pid_m&nbsp;*&nbsp;stride_am&nbsp;&nbsp;&nbsp;&nbsp;num_k_blocks&nbsp;=&nbsp;tl.cdiv(K,&nbsp;BLOCK_SIZE_K)&nbsp;&nbsp;&nbsp;&nbsp;for&nbsp;k_block&nbsp;in&nbsp;range(num_k_blocks):&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;k_start&nbsp;=&nbsp;k_block&nbsp;*&nbsp;BLOCK_SIZE_K&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;k_offsets&nbsp;=&nbsp;k_start&nbsp;+&nbsp;tl.arange(0,&nbsp;BLOCK_SIZE_K)&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;k_mask&nbsp;=&nbsp;k_offsets&nbsp;&lt;&nbsp;K&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;x_vals&nbsp;=&nbsp;tl.load(x_ptr&nbsp;+&nbsp;k_offsets,&nbsp;mask=k_mask,&nbsp;other=0.0)&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;a_vals&nbsp;=&nbsp;tl.load(a_row_ptr&nbsp;+&nbsp;k_offsets&nbsp;*&nbsp;stride_ak,&nbsp;mask=k_mask,&nbsp;other=0.0)&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;prod&nbsp;=&nbsp;a_vals.to(tl.float32)&nbsp;*&nbsp;x_vals.to(tl.float32)&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;block_sum&nbsp;=&nbsp;tl.sum(prod,&nbsp;axis=0)&nbsp;&nbsp;#&nbsp;Scalar&nbsp;reduction&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;acc&nbsp;+=&nbsp;block_sum&nbsp;&nbsp;&nbsp;&nbsp;tl.store(C_ptr&nbsp;+&nbsp;pid_m,&nbsp;acc.to(tl.bfloat16))#&nbsp;Launch:&nbsp;BLOCK_SIZE_K=1024,&nbsp;grid=(M,)&nbsp;=&nbsp;(2048,)#&nbsp;No&nbsp;explicit&nbsp;num_warps&nbsp;or&nbsp;num_stages&nbsp;(defaults)

图4:8轮优化中DRAM吞吐从631 GB/s爬到2229 GB/s，达到94.1% SOL，DRAM读取字节数保持稳定。
经验教训
分享编排多智能体攻坚复杂内核工程问题时的心得。
Q:没有人工盯,怎么保证智能体不跑偏?
关键是硬的、可验证的约束。在KernelAgent里，正确性和性能都走门禁评测：每个内核变体必须通过数值验证，性能用真实硬件benchmark测。进展由可执行、可测量的结果定义，智能体就不会跑偏。
Q:多智能体并行推进,又共享工作上下文怎么做到的?
光并行不够，没有协调智能体会重复造轮子、走冗余路线。每轮内优化worker独立并行，试不同优化策略；轮结束后，所有结果（成功失败都算）汇总成共享的结构化上下文：试了什么、什么有效、为什么。这份共享记忆广播给下一轮所有智能体，后轮站在前轮肩膀上。
Q:怎么防局部最优?什么时候停?
防局部最优靠探索多样性加清晰的终止准则。KernelAgent维护top-K beam而不是单个incumbent，并行探索降低早期次优决策主导搜索的风险。
GPU优化有个特点：单看优化A不行、B不行，AB组合可能突破。KernelAgent的目标就是最大化可探索的想法。
系统监控性能增量和硬件利用率：连续多轮roofline效率或运行时间没有实质改善，就判定继续优化不太可能有回报。

结语

KernelAgent证明，上一版正确性循环里的deep agent原则（扎根工具使用、并行探索、确定性控制）可以自然延伸到性能优化。给循环加上硬件profiling和工作记忆，让多智能体学习并探索不同优化路径，就能把验证过的内核从正确推到正确且快。开源项目，持续开发中。欢迎反馈、贡献和新用例，希望推进PyTorch生态里实用、可扩展的内核优化。

参考：https://pytorch.org/blog/kernelagent-hardware-guided-gpu-kernel-optimization-via-multi-agent-orchestration/