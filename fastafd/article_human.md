要点速览

- 分离部署解决长上下文下的MoE饥饿：共存部署中，Attention受KV-cache容量限制缩小decode batch，导致MoE层的expert GEMM效率大幅下降。Attention-FFN分离部署（AFD）将两个角色拆到不同GPU上，FFN端从多个Attention Worker聚合token，恢复MoE利用率。- GB200 NVL72上的1.35–1.45× 加速：FastAFD在GB200 NVL72上对比调优后的vLLM共存基线，Qwen3-235B和MiniMax-M2.5的每GPU steady-state decode吞吐提升1.35–1.45倍。加速来源是Attention GPU释放expert权重后获得1.5× 的KV-cache容量增益。- 运行时优化层：GPU通信 + 融合内核 + 零开销调度：FastAFD通过DeepEP风格GPU通信、MegaMoE融合内核（dispatch/expert/combine合一）、microbatch流水线、CUDA Graph重放和超前一步调度，将分离部署的通信和同步开销全部隐藏。- Vera Rubin + LPX上可达1.5–2× 加速：基于GB200实测的step分解，FastAFD推测在NVIDIA Vera Rubin + LPX（异质架构）上加速比可升至1.57–1.75×（仅MoE分离）或2× 以上（密集层也分离）。注：这些数字是基于 GB200 实测比例推算的边界值，并非实际硬件的 benchmark，验证依赖未来硬件可用。
Rubin + LPX（异质架构）上加速比可升至1.57–1.75×（仅MoE分离）或2× 以上（密集层也分离）。
离）。

共存MoE部署为何会饿死MoE层
E层

MoE模型的解码阶段交替执行两种层：Attention层（从KV-cache中计算注意力）和MoE层（将batch中的每个token路由到少量expert）。当请求上下文变长时，每个请求的KV-cache膨胀，占满GPU显存。系统一次迭代能前向的batch size随之缩小，这个缩小的batch直接打击MoE层：token太少，路由到每个expert的token不够，expert GEMM变小且效率骤降，MoE利用率断崖式下跌。
 GEMM变小且效率骤降，MoE利用率断崖式下跌。
。
这种不匹配在共存部署中构成了一种内生矛盾：Attention和MoE层跑在相同的Worker上。每个Worker同时管理KV-cache、计算attention、执行路由、参与expert-parallel dispatch、运行本地expert、combine expert输出。被Admission放行的请求数量既决定attention的工作量，也定义MoE可用的token池。如果attention所选batch够大，两种层都高效；一旦KV-cache将batch压小，MoE先遭殃。
KV-cache将batch压小，MoE先遭殃。
遭殃。
通过在恒定per-rank KV-cache预算下增长上下文长度、缩小decode batch的MFU测量发现：decode attention受HBM带宽束缚，读取相似量的KV-cache使其MFU几乎持平；但MoE FFN的expert GEMM严重依赖当前batch大小：batch小了，每local expert收到的token减少，GEMM变小，MFU因expert权重读取、路由、dispatch的开销无法摊薄而全面下降。
读取、路由、dispatch的开销无法摊薄而全面下降。

Attention-FFN分离部署的token流：Attention Worker以请求并行方式运行，FFN/MoE Worker从所有Attention Worker聚合token形成大expert batch。
rt batch。

Figure 1. Decode阶段attention读取每个请求的KV-cache历史，MoE层按expert分组token后执行expert GEMM。
pert GEMM。

Figure 2. 共存MoE的decode流程。所有GPU在相同拓扑上依次执行attention、路由、dispatch、expert执行、combine。
ombine。

Figure 3. 长上下文通过缩小KV-capped decode batch来饿死MoE层。在固定GPU和EP下，上下文长度L增长→active batch B缩小→每expert token减少→MoE MFU崩溃。
少→MoE MFU崩溃。

为何Expert Parallelism（EP）不能解决问题

增加EP能减少per-GPU的expert权重流量，但它不改变MoE的计算总量。EP改变了每个GPU从HBM中加载多少expert权重矩阵，但它不改变coexistence batch送入MoE的token数：那个数量已由attention admission固定。当EP放大到expert权重流量不再是瓶颈后，继续增加EP的回报迅速递减，因为dispatch和combine仍然在路径上，per-GPU MoE token数并未增加。Perplexity的Qwen-on-Blackwell报告也观察到相同模式：在Blackwell上把128个expert分散到超过16个rank后，EP收益止步不前。
ll上把128个expert分散到超过16个rank后，EP收益止步不前。
P收益止步不前。
根本问题在于：Attention端希望用尽KV-cache预算来塞满active request batch，这是它的最优解；但FFN端必须聚合远超出单个attention worker能放行的token数量，否则MoE MFU就会因每local expert的token太少而崩塌。共存部署试图用一个batch同时满足两者的需求，这正是矛盾的根源。
满足两者的需求，这正是矛盾的根源。

Figure 4. EP在固定per-GPU工作量下减少expert权重流量，但收益很快到底。MoE FFN利用率仍然取决于每expert token数，dispatch/combine不会消失。
ne不会消失。

分离Attention和FFN
FN
Attention-FFN Disaggregation（AFD）改变的是部署位置，不是模型计算。Attention Worker持有KV-cache、attention、路由、采样等请求面逻辑；FFN Worker接收路由后的token、执行MoE FFN、返回layer输出。每层中，attention侧的路由器产生expert分配，路由后的token batch成为attention decode和FFN执行之间的边界。
 和FFN执行之间的边界。
。
这个边界解开了共存布局的耦合。Attention admission仍由KV-cache容量和目标上下文长度决定；但FFN侧不再依赖某个Attention Worker的KV受限batch，它从多个Attention Worker聚合路由token后再执行grouped expert GEMM。固定FFN Worker池时，聚合效应增加每local expert看到的token batch，将MoE利用率提升到共存基线之上。
h，将MoE利用率提升到共存基线之上。
。
Attention Worker拥有请求状态和请求推进：KV-cache、QKV和output投影、路由器和采样。它只持有模型权重的很小一部分（FFN Worker持有 >90% 的expert权重）。FFN Worker存储expert权重并执行MoE计算，不拥有KV-cache、路由决策和采样。
che、路由决策和采样。

Figure 5. 聚合是AFD提供的利用率杠杆。固定FFN Worker池，聚合更多Attention Worker扩大每expert batch，将MoE利用率提升到共存基线之上。
到共存基线之上。

Figure 6. Attention-FFN分离的token流。Attention Worker执行attention和路由，FFN Worker将路由token聚合为expert执行。
expert执行。

AFD的代价：跨角色token移动
移动
AFD将MoE batch聚合的好处与跨角色token移动的开销做交易。每层中Attention Worker通过M→N dispatch向FFN Worker发送路由token，FFN Worker通过N→M combine返回expert输出。如果这个边界是串行的，每层都要等dispatch和combine在关键路径上往返，大expert batch带来的收益会全部被通信吞掉。
t batch带来的收益会全部被通信吞掉。

MegaScale-Infer给出了一个理想化的三条件模型：令m = micro-batch数，L = MoE层数，Tₐ = attention计算时间，Tₑ = MoE计算时间，T𝒸 = 单向通信时间。稳定态micro-batch period为T𝒻 = max(Tₐ, Tₑ)。一个理想的ping-pong流水线需要三个条件同时成立：① Attention和MoE计算量平衡（Tₐ ≈ Tₑ）；② 单次通信时间短于流水线周期（T𝒸 
时间短于流水线周期（T𝒸 

Figure 7. AFD microbatch ping-pong流水线。dispatch、expert执行、combine和attention计算在不同microbatch间重叠。
h间重叠。

GB200 NVL72：一把双刃剑
GB200 NVL72是一个机架级系统，72块Blackwell GPU在一个NVLink域内互联。每块GPU 192 GB HBM3e，整机架720 PFLOPS FP8 Tensor Core算力、13.4 TB HBM3e总计带宽576 TB/s、NVLink带宽130 TB/s。机架级的NVLink/NVSwitch带宽让AFD在实践中可行：路由token可以在Attention Worker和FFN Worker之间快速移动。
r和FFN Worker之间快速移动。
动。
但硬币的另一面是：Blackwell的FP8算力和HBM带宽也大幅增强了共存基线的实力。在完整的NVL72机架上，高机内带宽和宽expert parallelism本身就已让共存MoE服务极具竞争力。AFD不能仅靠分离部署取得优势，还必须通过运行时优化把通信和调度开销完全隐藏掉。这就是FastAFD的核心挑战。
astAFD的核心挑战。

FastAFD：为GB200 NVL72构建Attention-to-FFN运行时
运行时
FastAFD基于Mini-SGLang构建，Ray启动Attention Worker、FFN Worker和一个逻辑Coordinator。每4-GPU节点托管4个Worker。Coordinator为每个decode step生成调度计划：哪些请求活跃、哪些micro-batch和buffer slot由每个rank使用、哪些attention和FFN peer参与本轮。
tention和FFN peer参与本轮。
轮。
FastAFD的每项优化精准打击一种成本：① 用DeepEP风格的dispatch/combine将token移动保持在GPU侧并通过microbatch管道与计算重叠；② MegaMoE融合dispatch、expert GEMM和combine为一个统一kernel，同时CUDA Graph捕获decode path的其余部分；③ zero-overhead调度让Coordinator在Worker回放当前CUDA Graph的同时预先生成下一步计划。
当前CUDA Graph的同时预先生成下一步计划。
。
GPU侧通信控制路径

在GB200 NVL72上，Attention和FFN Worker共享一个NVLink/NVSwitch域，所以边界是机内GPU-to-GPU token移动。FastAFD把payload和control都留在GPU上：重用DeepEP的dispatch/combine kernel。它通过一个薄适配层将AFD映射到DeepEP的对称EP模型：在所有attention和FFN rank上形成一个process group，给每个attention rank分配一块虚拟expert槽位（router永远不会选到它），在dispatch前将真实expert ID重映射到FFN rank的范围。dispatch和combine作为GPU kernel运行，事件同步，CPU不参与decode关键路径。代价是MegaScale-Infer刻意避免的：GPU-side communication消耗SM。下一节展示FastAFD如何通过融合kernel将这个成本转化为重叠。
munication消耗SM。下一节展示FastAFD如何通过融合kernel将这个成本转化为重叠。
化为重叠。

Figure 8. Coordinator在Worker执行当前step时预生成下一步的metadata，通过ZMQ通信。GPU侧zero-overhead调度将CPU控制路径完全隐藏。
PU控制路径完全隐藏。

MegaMoE：融合Dispatch、Expert计算和Combine
ne
解码阶段MoE层的成本不仅仅是expert GEMM。路由打包、token搬运、expert投影与激活、combine和scatter：作为独立kernel和通信launch实现时，每个边界都产生中间缓冲区和元数据，增加事件或流同步。DeepGEMM的MegaMoE在一个MoE层内消除了这些边界：它将EP dispatch、expert GEMM（含SwiGLU）和EP combine融合为一个kernel，在Tensor Core计算的同时通过NVLink移动token。
 计算的同时通过NVLink移动token。
n。
在AFD边界上角色是分离的，所以FastAFD将mega-kernel分裂为两个角色kernel。Attention侧kernel每层每microbatch执行一次：量化hidden states到FP8、发布路由元数据让FFN rank可以pull结果、等待expert write-back、将top-k expert输出reduce为layer输出。它占用Blackwell GPU 148个SM中的24个，剩余部分留给attention path并发运行。FFN侧kernel从所有attention rank pull FP8 token、执行grouped expert GEMM（SwiGLU融合进GEMM流水线）、将BF16输出推回每个源rank的combine buffer。所有移动通过预分配对称缓冲区进行，无需逐次握手。
rank的combine buffer。所有移动通过预分配对称缓冲区进行，无需逐次握手。
。
由于FFN Worker只运行receive-compute-return循环，FastAFD为每个decode step启动一个持久FFN侧kernel：它拥有整个GPU，服务所有MoE层和所有microbatch lane，通过描述符表读取每层权重，消除了per-layer和per-microbatch的launch开销。Attention侧故意保持per-layer：attention rank在边界间仍需执行KV-cache attention、KV更新和残差/归一化工作。消融测试表明，这种融合在Qwen3-235B上比独立DeepEP+DeepGEMM路径减少44% 的8-node decode-step延迟，MiniMax-M2.5上为42%。
code-step延迟，MiniMax-M2.5上为42%。
%。

Figure 9. Nsight Systems trace：Coordinator的decode step调度完全被GPU执行覆盖，不影响decode step周期长度。
 周期长度。
零开销调度：消除控制面
跨多个节点的多个Attention和FFN Worker，AFD通常是跨节点系统而非单节点优化。每个decode step都需要CPU侧调度计划。Coordinator不计算路由或驱动数据路径：那些留在Worker和GPU stream上。FastAFD的思路继承SGLang的zero-overhead scheduler：CPU侧调度跑在GPU执行一步之前，准备好metadata后通过ZMQ发布，而Worker正在用当前plan回放CUDA Graph。ZMQ仅携带控制指令和返回的采样token，不携带路由决策或数据路径工作。这消除了decode关键路径上的集群级调度round-trip。
除了decode关键路径上的集群级调度round-trip。
p。
Blackwell NVL72上的Decode吞吐
吞吐
实验评估两个开源的FP8 MoE模型：Qwen/Qwen3-235B-A22B-FP8（235B总参，22B激活，94层，128 expert，每token 8个激活expert）和MiniMaxAI/MiniMax-M2.5（约230B总参，10B激活，62层，256个local expert）。基线是vLLM在共存MoE布局下运行DP+EP。每个GB200 NVL72机架连接18节点（每节点4 GPU），FastAFD使用M个Attention节点 + 1个FFN节点。
用M个Attention节点 + 1个FFN节点。
FN节点。
指标为per-GPU decode throughput：每步生成的token数除以step延迟和总GPU数（包括FFN GPU）。vLLM基线在单节点上测量，共存DP节点独立服务请求，因此per-GPU吞吐在大节点数下不变。
 吞吐在大节点数下不变。

Figure 10. FastAFD对比vLLM共存基线的per-GPU decode吞吐。Qwen3-235B提升1.41×（8K）和1.44×（16K）；MiniMax-M2.5提升1.45×（8K）和1.35×（16K）。
.35×（16K）。
加速来源分析
Per-GPU decode throughput的加速可以分解为三个因子的乘积：batch expansion（内存容量增益）、FFN-node tax（拓扑损耗）和latency ratio（step延迟比）。Batch expansion来自expert权重被移除后Attention GPU获得的额外KV-cache空间：在所有workload中这个比例为1.5×（Qwen的per-Attention-GPU batch从64→96，MiniMax从48→72）。
，MiniMax从48→72）。
。
关键在于当FFN侧被完全隐藏时，FastAFD的decode-step period等于attention侧的周期。Attention侧有两部分工作：FMHA（融合多头部attention kernel，HBM带宽绑定）和dense work（密集投影、路由、归一化等小kernel）。FMHA时间随KV流量线性增长（1.5× batch → 1.5× KV流量），而dense work主要跟踪launch次数而非batch大小，所以每个microbatch承担一次这个开销。
每个microbatch承担一次这个开销。
。
FFN侧保持隐藏的条件是关键。MiniMax-M2.5（约10B激活参数）在整个测量范围内stay hidden：其FFN侧完成得比attention更快。Qwen3-235B（22B激活参数）在某个点跨越了边界。平衡不是最优目标：FFN闲置最多浪费了1个节点，而FFN暴露（Tₑ > Tₐ）会减慢每个decode step，后者随M增长而恶化。FastAFD选择运行在Tₑ ≤ Tₐ 的最大M点，用有界闲置换取鲁棒性。
 的最大M点，用有界闲置换取鲁棒性。
。
消融实验量化了每个机制的作用。MegaMoE融合在Qwen3-235B上减少44% 的8-node延迟，MiniMax-M2.5上为42%。Zero-overhead调度移除后吞吐损失23%。mb=2是最优值：mb=1让通信暴露在关键路径上，mb=3/4只增加小kernel的m倍复制而不隐藏更多。
l的m倍复制而不隐藏更多。
多。

Figure 11. Step分解与AFD延迟预测模型。FMHA、dense work和MoE三部分的时间构成vLLM基线step，AFD移除MoE部分。
 移除MoE部分。
。

Figure 12. AFD加速在不同模型上趋势不同。MiniMax（小激活参数）在所有M:N比下保持FFN侧隐藏，延迟几乎持平；Qwen（大激活参数）越过最优比后step延迟上升。
 延迟上升。
各机制的消融验证
FastAFD的操作点说便宜但不自动可达。在三个因子中运行时只能移动一个（T_AFD）。MegaMoE保持Tₑ 足够小以隐藏：没有融合的话FFN侧提早暴露，可行的M更小。Zero-overhead调度保持step period在CUDA Graph长度：禁用跨step重叠后，Qwen3-235B 4-node 8K step从32.826 ms增长到42.612 ms，23% 的吞吐损失使配置低于共存基线。mb=2是最低有用值：mb=1暴露通信，mb=3/4只增加小kernel开销。
mb=3/4只增加小kernel开销。
销。
在这个结构验证后，将预测扩展到异质硬件就是替换参数：移除FFN-node tax，从延迟比中移除MoE时间，剩下就是纯attention+dense对共存的比例。
的比例。
Vera Rubin + LPX/LPU上的前景

NVIDIA Vera Rubin + LPX/LPU将AFD从GPU部署问题变成了硬件边界。Rubin GPU处理prefill、decode attention、KV-cache密集型工作和高并发服务，而LPX加速延迟敏感的FFN/MoE执行。Rubin每GPU高达288 GB HBM4、22 TB/s HBM带宽、3.6 TB/s NVLink 6；LPX机架有128 GB SRAM、40 PB/s SRAM带宽、640 TB/s scale-up带宽。这正是AFD分离的两种资源。
up带宽。这正是AFD分离的两种资源。
源。
在没有实际硬件的情况下，基于GB200实测的step分解进行推算。假设两个LPX机架对应一个Rubin机架（FP8权重可放入LPX SRAM）。移除FFN-node tax后，batch expansion降至约1.25×，但在线性attention模型下batch因子互相抵消，加速简化为延迟组成比。根据GB200 vLLM的attn:dense:moe比例推测，仅MoE分离时可达1.57–1.75× 加速。若将dense工作也移到LPX（更激进的边界），Rubin暴露的step接近pure attention，加速可达2× 以上。
ep接近pure attention，加速可达2× 以上。
上。
核心启示
① **在同一个NVLink域内，通信应该留在GPU上。** FastAFD将MegaScale-Infer风格的M:N架构带到GB200 NVL72，而NVLink翻转了第一个设计选择：MegaScale-Infer将通信控制路径放在CPU上以节省GPU SM（对RDMA集群合理），但GB200上SM预算并不稀缺：attention侧边界kernel只占用Blackwell GPU 148个SM中的24个（约16%），FFN侧kernel专享整块GPU。融合dispatch/combine用这个SM切片换来重叠，并将整个decode step保持在CUDA Graph内。
M切片换来重叠，并将整个decode step保持在CUDA Graph内。
h内。
② **平衡不是正确的目标。** MegaScale-Infer的Tₐ ≈ Tₑ 处在便宜失败模式和昂贵失败模式的边界上。FFN闲置浪费最多1个节点，而FFN暴露减慢每一步且随M增长而恶化。FastAFD选择Tₑ ≤ Tₐ 的最大M值运行，用有界闲置换取鲁棒性。
，用有界闲置换取鲁棒性。
③ **两个microbatch就够了。** 实测表明mb=2已能完全隐藏双向通信，mb=3和4只会成倍增加小kernel的开销而不隐藏更多通信。
隐藏更多。
④ **加速来自容量，而非延迟。** FastAFD的decode step时长与vLLM持平（延迟比≈1），计算延迟并未缩短，变化的是每GPU的承载量：Attention GPU卸掉90%+ 的权重，携带1.5× 的resident request，在扣除FFN-node tax后per-GPU吞吐提升1.35–1.45×。
吐提升1.35–1.45×。

开源与未来工作
FastAFD是一个serving prototype，而非新的模型架构。它目前仅评测了GB200 NVL72上的稳态decode step。下一步是扩展到DeepSeek、Kimi、Qwen3-Next、GLM、StepFun等更多开源大型MoE模型家族，以及将AFD与PD分离、推测解码、准入控制、请求迁移和SLO感知调度等生产级组件组合。Vera Rubin + LPX/LPU的推算是基于实测的预测，需要实际硬件验证。FastAFD源代码和脚本将在hao-ai-lab/FastAFD发布。
ai-lab/FastAFD发布。

结语

FastAFD的核心价值不是提出新的分离思想：MegaScale-Infer和Step-3已铺好这条路：而在于证明：即使在GB200 NVL72这样共存基线已足够强的硬件上，通过精心的运行时优化（GPU侧通信、融合kernel、超前调度），AFD依然能带来可观的吞吐收益。这指向一个更深层的问题：MoE推理的瓶颈正在从「算力」转向「显存容量」和「token聚合」。值得反问的是：如果推理优化领域的共识确实是分离部署比共存更优，那模型架构设计是否也该为此做好准备：让Attention和MoE的显存需求和batch大小更独立地可调，而不是被迫在同一个GPU上竞争资源？
是被迫在同一个GPU上竞争资源？
？

【传送门】
万亿参数RL实战：如何用28个H200节点训GLM-5
小米MiMo罗福莉后训练新范式MOPD: 多教师同策略蒸馏，多领域无损集成
NVIDIA TriAttention解读: KV Cache压缩最大的问题不是算法而是两个Infra问题
蚂蚁CausalMix: 将数据混合从超参搜索转换成因果推断
Google新论文RubricEM: 评分标准引导的深度研究Agent训练框架
Agent卷向AI Infra: SGLang团队用硬核Agent优化框架和CUDA Kernal性能
KVCache缝合术: 突破前缀匹配天花板,首Token快14倍 多文档快2~4倍
榨干GPU性能：流水线解码消除GPU气泡，推理吞吐提升35%
【Agent for AI Infra三】摩尔线程MusaCoder国产算子生成超过Opus4.7：数据合成-SFT-RL全栈拆解
TokenSpeed-Kernel：把推理内核做成一等公民
把KVCache变成可训练记忆：Context Tuning让LLM免权重微调
阿里Sparse Attention on CXL替代RDMA做KV Cache解耦 推理2.1×吞吐, 9.7×TTFT
RL的下一个大突破：不是优化可验证问题而是把'不可验证'领域变得'可验证'
智谱GLM 5.2 RL: 单Rollout异步优化SAO稳定训练1000步全面超越GRPO
小米MiMo罗福莉:8卡GPU让1T参数模型跑出1000 TPS , FP4+DFlash+TileRT全解读
腾讯混元hy3大模型技术之TurnOPD：回合感知的在线策略蒸馏，长程Agent提速2.29倍

参考：https://haoailab.com/blogs/fastafd/