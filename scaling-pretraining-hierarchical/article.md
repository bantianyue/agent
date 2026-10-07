要点速览
-
三个自由度
：并行方案×激活检查点×局部batch size，三者经内存互相咬合：selective-AC在92%显存处TPS峰值，full-AC在60到94%宽区间都快；FSDP组加大省内存但加通信。
-
16卡定乾坤
：目标规模1/32的sweep砍掉搜索空间：no-AC太早OOM，selective-AC峰值batch约18，full-AC约38；8到16卡经IB扩展无损耗。
-
512卡35.3%
：最终selective-AC、batch 22、FSDP=128、DP=4：26.7k TPS、35.3% MFU，16到512卡单卡效率只掉6%，20T token 17天训完。
堆卡不调软件，训练效率很快就塌；前沿实验室为MFU里几个百分点投入大量人力。可调的效率超参数太多，大规模网格搜索贵得离谱：Aleph Alpha这篇把窗帘拉开：30B-A3B MoE从16张卡扩到512张B200，35.3% MFU，只比完美线性低6%。
方法叫分层扩展：先在16卡上把搜索空间砍光（并行方案×激活检查点×局部batch size），用PyTorch profile确认compute-bound，再把结论带到32倍的目标规模。很多思路与规模无关，没有几百张卡也用得上。
引言
把30B-A3B MoE模型从16张卡扩到512张B200，实现近线性扩展，35.3% MFU。
GPU饥荒的年代，必须把算力用到极致。直觉是"买更多卡"，但不调软件就往里堆卡，训练效率很快就塌；前沿实验室为效率指标里几个百分点投入大量人力与agent时间。可调的效率超参数太多，大规模网格搜索贵得离谱，怎么缩搜索空间？最终配置偶尔会公开，但走到它的选择过程几乎不公开：这篇把窗帘拉开。
这篇拆解我们如何实际高效扩展、用512张NVIDIA B200预训练30B-A3B MoE模型：分层方法找训练配置：先缩搜索空间，再加卡。512卡上35.3% MFU，只比完美线性低6%：大规模高效预训练。
没有几百张卡为什么也要关心效率？后面会看到，很多工具和思路与规模无关；不为省钱，也为省时间：时间永远不够。
我们用自己优化的torchtitan分支训练。目标配置：64节点经InfiniBand互联，每节点8卡经NVLink互联。要让所有GPU像交响乐一样同步轰鸣。
图1:让几百张GPU同步轰鸣的"预训练交响乐"。
注意这篇聚焦分层扩展方法论本身；让35.3% MFU成为可能的系统级与kernel级优化大多不在本文范围。
先讲度量：什么是训练效率、怎么测："MFU好，TPS更好"；再看三个自由度怎么把配置调到最高效："让GPU算力吃满"；然后开始分层："16张卡砍掉搜索空间"用小规模实验缩超参数空间；"一张profile顶一千次实验"看模型到底在干什么、效率如何；最后"从16到512"把学到的全部带上去。但先讲指标！
MFU好,TPS更好
实验用三个指标：每卡每秒token数（TPS）、模型FLOPS利用率（MFU）、显存占用（mem）。TPS是单卡处理的token数除以墙钟时间。
它粗糙但诚实，是我们真正优化的目标。MFU是效率指标：把TPS换算成硬件天花板的分数：GPU理论上每秒能做多少浮点运算。torchtitan这样算：MFU =（每token FLOPs × TPS）/ 硬件峰值FLOPS。MFU有坑，跨模型比效率容易翻车：混合精度显著改变峰值FLOPS的定义。我们用BF16训练（梯度FP32，但绝大部分计算仍是BF16），所以本文MFU全用BF16峰值做分母。每token FLOPs很难算准，所以北极星目标函数是TPS；MFU照常展示，一是效率指示，二是行业标准。显存占用是训练中PyTorch峰值reserved内存占设备总内存的比。
用reserved而非allocated内存，因为它决定硬失败：OOM。现在速度与效率的尺子有了，看怎么改训练配置做出极速预训练。
让GPU算力吃满的三个自由度
知道怎么量效率，实践中高效用GPU长什么样？效率工程的母题是通信计算比：GPU花在跑模型数学运算（compute kernel，如算attention）上的时间，对花在卡间搬数据（communication kernel，如前向Gather权重）上的时间。理想是永远"compute-bound"：瓶颈在GPU算得有多快，而不是数据搬得多快。通信不直接推进模型计算：GPU等数据时，算力可能闲置。"整块GPU的钱我付了，就要用满整块GPU"。工具有很多把通信计算比往有利方向掰；这篇看三个自由度。
1并行方案
对并行方案的初始理解基于Hugging Face的Ultra-Scale Playbook，强烈推荐先读。粗略说预训练涉及四种模型相关数据：权重、梯度、优化器状态、激活。权重是可训练参数；梯度是loss对参数的偏导，告诉我们参数该怎么变；优化器状态存历史梯度信息，决定更新的步长方向；激活是前向的中间结果，反向算梯度要用。并行方案决定这四样在GPU间怎么分。如今几万亿参数模型在几万卡上并发训；我们是30B模型512卡，几招就能compute-bound，看两个并行维度就够。
每张卡处理不同的局部batch序列，产出不同的局部梯度；优化器步之前必须在所有卡间reduce梯度，让每张卡都知道参数全局该怎么变。
MoE模型有自己的并行课题与机会：稀疏：每token只激活一小部分参数（专家），前向计算量相对总模型很小。专家并行（EP）是MoE预训练常用技术，但超出本文范围；模型更大更稀疏时大概率需要EP，那时通信计算比就不好掰了。
2激活检查点
反向时每张卡要算loss对可训练参数的梯度，需要每个含参操作的输入（激活）在内存里。前向已经算过激活，存下来是第一直觉；但大模型中间计算巨大，存激活非常吃内存。于是引入"检查点"：只存精选激活，从它们重放前向、重算缺的激活。激活检查点（AC）是调节内存的好工具。
选哪些做检查点有多种策略，是重算时间与内存占用的精细权衡。我们考虑三种：不存（no-AC）、selective-AC、full-AC。
3局部batch size
并行方案与AC都是调内存的工具：内存分给激活存还是模型参数。而局部batch size决定最吃内存的那块：激活本身。
局部batch size是每张卡一次前反向同时处理的token序列数，对效率影响大：一次处理更多token通常更快烧掉token预算。我们要填满内存、用满整块GPU（钱付了），最容易的办法就是加局部batch size：中间计算随它涨。我们要最大token吞吐，能塞下更大的局部batch就塞。
全局batch size是torchtitan语义下所有卡在优化器步之前处理的序列总数；它决定训练动力学，是外部需求，效率工程师说了不算。但有个硬约束必须遵守：gbs = lbs × n_gpus × ga，即全局batch size是局部batch size、卡数、梯度累积步数的乘积。不同卡数做局部batch sweep时，先定该卡数的目标全局batch，再为每次实验选满足约束的最接近全局batch。
它们如何咬合
如前所说，我们要吃满GPU内存；三个维度都影响训练内存。所以关键问题是"内存怎么分"：约束问题里动一个维度，另两个跟着动。举几个例子。
局部batch size与AC咬合：内存意义上selective-AC介于full-AC与no-AC之间。它比full-AC需要更小的局部batch，因为内存里留了更多激活；但它不用重算整层的中间激活，显著更快。full-AC与selective-AC之争会贯穿全文。
局部batch size也与FSDP咬合：一个FSDP组里卡越多，每卡分到的权重/梯度/优化器状态越少，腾出空间给更大的局部batch；代价是跟更大的组通信，通信kernel时间变长。
三个旋钮不独立：拧一个，另两个跟着走。这种推拉博弈要精细调，所以sweep很重要。不变的是：我们要最大吞吐，而保持compute-bound是trade-off做对了的好指示。
图2:分布式训练玩家的日常：三个旋钮互相咬合。
16张卡砍掉搜索空间
现在可以跑30B-A3B模型、收第一批预训练效率结果了。从小规模开始探索：8到16卡。模型光放权重、优化器状态、梯度就要几张B200，所以把一个节点（8×B200）当基本扩展单元。
1到2节点时实验便宜（集群资源与时间），所以最大的一轮sweep放在这个规模，学到的结论往上搬。具体sweep可行组合：并行方案×激活检查点×局部batch size。所有实验固定序列长度4096 token。
heatmap展示不同并行与AC配置下、局部batch扫到OOM的模型效率。观察到full-AC的内存碎片：局部batch加大时内存用量来回震荡，张量在reserved内存里打包效率时好时坏。
局部batch与内存用量幸福耦合：一个走另一个跟。训练速度跟这对的关系更复杂：局部batch太小GPU吃不饱，TPS低；太大效率开始掉：内存饱和（看到PyTorch的CUDA分配重试警告）。selective-AC在92%内存占用处效率峰值；full-AC在60%到94%内存占用的宽区间都快。这些就是往上扩展时的目标内存用量：局部batch要够大以达到它们。
OOM边界与训练效率随AC技术剧烈变化：固定小batch下no-AC明显最快，但它的高内存只允许小到没法竞争最优效率的batch；selective-AC有重算开销，需要更大的局部batch来摊；full-AC重算开销最大，在大局部batch下有竞争力。
单节点到多节点的训练效率显示8到16卡经InfiniBand扩展无问题：通信介质够快，保持compute-bound；否则多节点跑TPS会明显掉。
只用16卡（目标规模的1/32），搜索空间大幅缩小：no-AC太早OOM；selective-AC在局部batch约18处TPS峰值；full-AC峰值在约38。往上扩展时只需在这些峰值附近测效率，不用全空间再扫一遍。
一张profile顶一千次实验
MFU、TPS、内存用量是快速缩搜索空间的好指标；但要真正理解引擎盖下发生什么，得看PyTorch profile：跑了哪些kernel？什么时候跑？通信与计算kernel怎么重叠？网络上走什么数据、走多少？这种深入分析还给我们心智模型：模型行为随扩展怎么变。
图3:看清了，才能调对。profile是效率工程的眼睛。
看目前最快的配置的前向：16卡全分片、selective-AC、局部batch 18。
trace上是compute流：torch编译图的transformer层调用与里面的compute kernel；下是communication kernel。计算与通信同时发生：下一层前向的权重用all_gather预取，compute kernel不用等着开工。compute kernel一个接一个，瓶颈在计算本身的速度：compute-bound。反向也一样吗？
如上，反向除了all_gather还有reduce_scatter，两者都与计算完全重叠。回想FSDP：整层的梯度一算完就在卡间reduce、按FSDP组分片，所以看到reduce_scatter；all_gather则是Gather权重算梯度、重算激活用的。总之反向也是compute-bound。再看一条带DP的trace。
第三种通信操作：all_reduce。相对reduce_scatter，all_reduce在模型副本间平均梯度；它随DP副本数扩展，于是在DP与FSDP之间形成推拉：卡数固定时，DP度加大则FSDP组变小、FSDP kernel时间降，反之亦然。平衡两者很关键。
较真的人会问：梯度其实只在优化器步之前的最后一次反向需要all_reduce。原因见Ultra-Scale Playbook对应章节。同一个profile，开了all_reduce优化再看一次。
DP下非最后梯度累积步的反向trace：不需要DP all_reduce，拿掉。
DP下最后梯度累积步的反向trace：含all_reduce，保证优化器步之前所有卡梯度一致。
这是profile→优化→profile的缩影：想把模型为什么慢刨到底，profiling是最好的工具，强烈推荐。大规模还开了其他系统级优化，但在这个模型尺寸上各自影响有限；最有分量的是反向与下一次前向之间让权重常驻内存、不再分片重Gather，目标规模下约2到3%吞吐。但效率的主力仍是分层扩展方法。
从16到512:scaling成本几乎免费
16卡的sweep把搜索空间缩得很小了。加卡之前，先想想结论意味着什么、对扩展有什么预期。
结果显示通信比计算先结束：FSDP组可以加大到接近communication-bound。而且除最后一次前反向外没有all_reduce，DP也能吃掉一部分扩展成本：只在最后梯度累积步付一次。作战计划：compute-bound一天就加FSDP，加DP直到512卡。
先扩到128卡，profile看通信占比怎么涨。selective-AC与full-AC谁更快还不知道，两种都收指标。先跑128卡selective-AC：每卡分的模型变少，局部batch可以加大。
128卡、FSDP=128、selective-AC的前向与反向：28.0k TPS、37.0% MFU、93%内存。1/8规模时是28.4k TPS，单卡效率只掉1.4%。前向反向仍是compute-bound。
full-AC画面类似：26.3k TPS、34.7% MFU、89%内存。前向trace的通信kernel显示已站在communication-bound边界；反向仍明显compute-bound。再加FSDP度会让整个训练communication-bound。结论：selective-AC是更优的AC，128是FSDP度的上限。
扩到目标512卡：剩下的4倍（512/128=4）给DP度。按分层策略其余配置不动。最终配置：selective-AC、局部batch size=22、FSDP=128、DP=4。
512卡前向：compute-bound。非最后梯度累积步的反向：无all_reduce，仍compute-bound。最后梯度累积步的反向：DP all_reduce从compute kernel里漫出来。
除最后一次反向外全程compute-bound：正好是我们引入DP all_reduce的地方。最终26.7k TPS、35.3% MFU：20T token在512卡上17天训完。扩展的大头在这：比如再加两个DP副本，训练压到11天。硬件资源与FSDP/DP度的精细平衡，加上便宜的DP扩展，带来近线性扩展。
30B-A3B模型已成功优化到512卡跑。
看各规模的最优：全规模MFU与TPS都很高，16到512卡单卡效率只掉6%。说明硬件各部件用得很均衡。分层传递小规模实验结论到32倍的目标规模，找到了高效配置，离完美线性只差6%。拿这个效率开正式预训练，我们很乐意。
局限与结论
我们用分层方法扩展预训练；用它是因为环境受约束，每GPU小时都极贵。我们可能没跑出绝对最快的配置，但找它要在目标规模做大量实验，不划算；那些GPU小时更该花在功能性ablation上（真正训出好模型）。
实验限于单一架构、单一序列长度，只用FSDP与DP，目标规模512卡。
当然，35.3% MFU不只靠"设计好的扩展"：系统级与kernel级优化是地基，是扩展跑得好的原因；但它们超出本文范围。
我们刻意不拿这个MFU跟其他公开MoE成绩比：架构、精度、配方差异让这种对比复杂且易错。请用分层扩展本身评判我们：卡数涨上去，效率掉了多少。
512张B200上30B-A3B预训练做到35.3% MFU，用分层扩展方法在规模上成功并行。展示了如何只用16卡砍掉大部分搜索空间：找局部batch边界、排除拉胯配置、用PyTorch profile理解模型行为。把小规模实验的结论带到32倍的目标规模，找到离完美线性只差6%的高效配置。
结语
扩展预训练，先缩搜索空间再加卡。
Aleph Alpha用16卡（目标1/32）定下并行方案、AC技术、局部batch边界，profile确认前后向compute-bound；128卡定FSDP上限128、selective-AC胜出；512卡FSDP=128、DP=4收官：35.3% MFU，离完美线性只差6%。
对做预训练的人，这套方法论可以直接抄：北极星指标用TPS而非MFU，目标显存占用92%附近，gbs=lbs×卡数×梯度累积的硬约束先立好；权重反向前向间常驻内存再白拿2到3%。Kolibri的训练链路是这套方法的完整施工记录，两篇对照看。
【传送门】
RL的下一个大突破：不是优化可验证问题而是把'不可验证'领域变得'可验证'
英伟达Kernel Agent: 编译器与算子调优Agent的协同设计
vLLM+Mooncake: 把agentic前缀复用从1.7%拉到92.2%
在NVFP4上超越cuBLAS: 从零手写+Claude极限优化Blackwell GEMM
Kimi K3技术解析之AttnRes: 打破Transformer沿用十年的残差各层等权的假设
Torch Profiler在Trace里分析性能瓶颈: 剖析SGLang LLM推理
Agent卷向AI Infra: SGLang团队用硬核Agent优化框架和CUDA Kernal性能
把KVCache变成可训练记忆：Context Tuning让LLM免权重微调
参考：https://aleph-alpha.com/en/blog/scaling-pre-training-in-practice-a-hierarchical-approach/