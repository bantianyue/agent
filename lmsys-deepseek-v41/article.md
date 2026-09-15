/* 传送门统一样式（add-portal.py动态注入时引用此class） */
.portal-title { font-size:12px; color:#888; }
.portal-links { font-size:12px; color:#888; }
.portal-links a { color:#888; text-decoration:none; }

要点速览

-核心结论：模型发布当天，SGLang与Miles跑通了DeepSeek-V4.1的推理与RL训练；整套优化的地基是压缩KV与检索选择在层间共享。-关键数据：Engram表卸载到主机内存后KV缓存容量提升36%；解码侧有界重放让prefill吞吐在8x H200上提升1.56倍、4x GB300上提升1.37倍。-工程要点：有界重放是近似算法，AIME 2026实测pass@1与全量prefill持平（各453/480），能力边界与开关限制必须逐场景确认。

DeepSeek-V4.1发布当天，SGLang与Miles就完成了Day-0支持：推理侧打通共享KV、Engram主机卸载与SWA有界重放，训练侧用Miles让RL训练和rollout共用一批GPU。
这套适配的难点不在加法，而在共享：压缩KV、indexer keys和检索候选要在层间流动，滑窗KV却必须逐层独立。有界重放引入了一个近似，换来的回报是缓存容量与prefill吞吐：KV缓存容量提升36%，8x H200上prefill吞吐提升1.56倍。

1. 架构总览
DeepSeek-V4.1引入了若干会直接影响服务栈的架构选择。
低压缩率与滑窗注意力（SWA）。 每层为其最近的128个位置维护一个fp8滑窗缓存，部分源层另外产出fp4压缩表示用于长程注意力。除前两层外，每个query同时关注本地窗口和最多512个由indexer选出的压缩位置。第2到19层使用成对压缩，因此KV源层必须在解码步之间跨步保留不完整的成对状态。
压缩KV与检索选择在层间共享，详见第2节。
流形超连接（mHC）。 每个子层通过依赖token的混合系数读写四条并行残差流。子层消费前驱产出的系数，下一次系数投影因此可以与当前的注意力或FFN计算重叠。
Engram记忆。 第1层与第14层从两张大型fp8表里按哈希后的token n-gram检索行，把选中的行门控后写进残差流。每个step只读取少量行，所以表的放置位置与查表开销比密集计算更要紧。
2. 跨层共享与稀疏检索
共享KV与indexer keys。 四个KV源层产出压缩KV和indexer keys。消费层直接从最近的KV源读取，不必在每个消费层各自存储和生成。窗口KV仍然逐层独立。
共享候选的两级选择。 第20层为每个query选出最多2,048个「八个位置一块」的块，并始终保留包含最新位置的那一块。它把这些候选发布给后续的index源层，同时从所有可达位置里选出自己的top-512。后续index源层把自己的top-512限制在这些共享候选内。当所有可达位置都落在16,384的位置预算内时，候选过滤不会排除任何位置。
跨层选择复用。 八个index源层用自己的query给indexer keys打分，每个query选出最多512个压缩位置。其余做压缩注意力的层直接复用最近一次选择，不再运行indexer。

图1：各层角色与跨层共享，逐层压缩比、KV源、候选源、index源与Engram层一览
3. Engram优化
Engram是DeepSeek-V4.1的核心组件。它的两张fp8表共189 GiB权重，但每个解码步只读取少量行。SGLang支持把这些表放在GPU或主机内存里。把表按四张GPU分片，每张GPU的HBM存四分之一，每次查表的结果就需要一次all-reduce汇总。
3.1主机内存布局
主机卸载把Engram表移出GPU内存，为KV缓存腾出容量。反量化、门控和value投影仍然留在GPU上。SGLang支持两种主机布局，通信开销不同。
在host-sharded布局里，每个TP rank在主机内存持有一个分片，查表仍然要走all-reduce。在shared host布局里，所有TP rank访问同一份完整的主机内存副本，每个rank各自收集需要的行，从而省掉查表的all-reduce。
对大型表的随机访问可能受地址转换限制，用大页支撑可以降低这部分开销。在被评测的GB300容器里，host-sharded表使用支持大页的匿名映射，shared映射则不支持。因此自动布局选择选了host sharding：保留一次all-reduce，换取更快的主机查表。最佳放置取决于CPU与GPU之间的互联、大页可用性和具体负载。
3.2性能评估
在4x GB300（TP4/EP4）上的成对测试里，主机卸载把KV缓存容量提升了36%，解码吞吐和TTFT相当。这些运行使用带大页支撑的host-sharded表，并保留了查表all-reduce。28个贪心探针的补全结果与基线全部一致。
要把Engram表放进主机内存，设置SGLANG_ENABLE_DSV41_ENGRAM_HOST_TABLE=1。

图2：TP4下Engram表的放置方式与查表通信路径，GPU分片与主机分片保留all-reduce，共享主机布局取消它
4. SWA有界重放
滑窗KV是逐层独立的。为前缀复用把它保留下来会占用缓存容量，而全序列prefill算出的窗口状态在后续解码里不会再被直接访问。模型的部署说明提出了有界重放，用来降低这两部分存储与计算成本。
4.1编码器侧有界重放
标准的prefix reuse需要缓存的压缩KV、indexer keys，以及一个有效的滑窗检查点。编码器侧有界重放取消了检查点这一要求：前缀缓存保留压缩KV与indexer keys，每个活跃请求维护一个128位置的窗口。
命中缓存时，SGLang重算缓存前缀的最后128个token来重建窗口KV，缓存的压缩KV与indexer keys保持不变。这相当于用有界重算换取更低的缓存存储，让前缀复用不再依赖匹配位置上存在窗口检查点。
4.2解码器侧只算尾部
第20层是最后一个压缩KV源。第21到39层复用它的压缩KV与indexer keys，同时计算自己的窗口KV。对每个prefill chunk，SGLang对所有token执行第0到20层，而第21到39层只处理每个请求最后最多128个token。
第0到20层保留全上下文计算。在靠后的层里，本地注意力被限制在保留的尾部，因为该边界之前的窗口KV并没有被计算。

图3：编码器侧前缀尾部重建与解码器侧只算尾部的prefill切分示意
4.3正确性边界与结果
两种模式都在重建边界处截断本地注意力，所以即使缓存的压缩KV不变，重算出的隐状态也可能与全量prefill不同。有界重放是一种近似，质量必须靠实测评估。
在每批八个8K token prompt的成对测试里，解码器侧重放把prefill吞吐在8x H200上提升1.56倍、在4x GB300上提升1.37倍。在4x GB300上，成对的AIME 2026评测测得开启与关闭重放的pass@1相同，各自453/480个正确样本。
两种模式都是可选项（--enable-encoder-swa-bounded-replay、--enable-decoder-swa-bounded-replay），并且可以组合使用。编码器重放不支持投机解码；解码器只算尾部不支持input logprobs与完整的prompt隐状态捕获。
5. 内核与执行优化
mHC执行与数值一致性：前驱pre-mix让下一个子层的混合系数可以同当前的注意力或FFN一起算出来。SGLang让这部分工作重叠，并把混合统计的归约与Sinkhorn迭代融合在一起。归约采用与batch size无关的固定顺序，使每个token的混合系数在不同batch组合下保持一致。对小batch，HC=4的post-mix会沿隐藏维度切块，暴露出更多并行度。
FP4索引与TP布局：indexer打分直接从FP4缓存读取。indexer heads在各TP rank上复制，因为把这种MQA形状的操作分片并不能减少key带宽，反而需要一次规模随上下文长度增长的打分all-reduce。
在保持量化语义前提下的融合：indexer把RoPE、FP4量化、打包或缓存写入合并进融合内核。融合必须保留原始计算的中间舍入与缩放，删掉一次中间写内存并不等于可以删掉它的数值影响。这样做减少了内核启动次数与中间内存流量，同时保持量化序列不变。
低压缩率：压缩器投影使用BF16检查点权重，累加与输出使用FP32。ratio-2的解码池化被融合进一个内核，把每一对完成的位置合并起来。压缩与索引在输入就绪后也能与注意力准备重叠，在注意力消费它们的输出之前汇合。
单token投影与Engram融合：分组输出投影对单token输入使用专门的BF16矩阵向量内核，因为通用矩阵乘法路径在这种情形下GPU利用率很低。融合后的Engram门控减少了FP32临时存储，n-gram哈希在一个内核里算完。这些优化的目标，正是每个解码步都会重复出现的小投影与稀疏内存操作。
6. Miles中的强化学习
Miles为DeepSeek-V4.1提供了Megatron-Core插件，并用SGLang做rollout。训练后端实现了模型的共享注意力状态、mHC与Engram记忆。一个核心目标是最小化同一批响应下trainer与rollout的log-probability差异。
并行与共享状态：后端支持DP、TP、SP、EP、PP与CP。TP和SP切分注意力投影与压缩器分组。流水线边界需要搬运全部四条mHC残差流、前驱混合系数，以及下游消费者仍然需要的注意力状态。这些状态也让重算的层可以在本地恢复输入。上下文并行让query保持本地，同时跨rank收集窗口KV、压缩KV与indexer keys，以实现全局稀疏检索。
量化感知训练：训练前向复现了服务引擎对压缩隐变量、indexer query与key的FP4舍入，以及窗口缓存的FP8舍入。直通梯度让这些离散操作可以参与优化。窗口缓存的前向值使用引擎的分页缓存内核，梯度则由一个可微模拟来承载。稀疏注意力与索引复用DeepSeek-V4插件的TileLang内核，RoPE与伪量化遵循服务侧公式。
路由重放：Rollout Routing Replay把采样得到的专家分配喂给trainer的MoE层，避免路由打平时选中不同的专家路径。indexer top-k选择重算而不是存储重放：一旦它的量化输入对齐，重放并没有带来可测的一致性收益。这样就不必为每个rollout token保留逐层选择结果。
数值一致性：压缩器门控、归一化统计、mHC混合、Engram门控与注意力汇累积都使用FP32，并在操作边界做类型转换。压缩KV投影的梯度all-reduce同样使用FP32。确定性的归约与矩阵乘法设置让重复前向可复现，有助于把执行波动与持续存在的trainer-rollout差异区分开。
共置训练与rollout：训练与rollout在16张GPU上交替进行。优化器动量流式写入节点本地NVMe，rollout引擎恢复之前先把trainer状态换出。每个训练步之后，更新过的BF16权重按桶传输。冻结的FP8 Engram表使用主机内存支撑，不参与权重同步。后端通过自己的model bridge直接加载Hugging Face检查点。
6.1已验证的训练
图4展示了一次DAPO运行的第0到80步：在16张GB300（TP4、EP16、每步128个样本）上，用DAPO-Math-17K数据集、2K token响应上限。前五个步的平均奖励是0.51，最后五个步是0.78。在绘制的区间里，trainer与rollout之间的逐token KL落在0.0012到0.0017，平均log-probability绝对差落在0.017到0.025 nats。

图4：DAPO训练的原始奖励与trainer对比rollout的策略差异，覆盖第0到80步
在这次运行中，测得的差异始终很小，也没有持续增长。这些测量并没有分离出差异的成因，也不构成数值等价性的证明。这次运行完成了120步以上，没有出现失败。

结语

把新模型做成Day-0支持，拼的不是把架构硬塞进推理引擎，而是把「共享」当成一等公民。 DeepSeek-V4.1的压缩KV、indexer keys和检索候选全部在层间共享：四个KV源层供全模型读取，第20层发布候选块，八个index源层负责打分，其余层直接复用结果。共享越彻底，单层要维护的状态越少，后面所有优化才有空间。三处取舍值得记住：Engram表卸载到主机内存，用一次all-reduce换取KV缓存容量增加36%；SWA有界重放用有界重算换缓存与算力，prefill吞吐最高提升1.56倍；训练侧用量化感知前向加路由重放，把trainer与rollout的差异压到0.02 nats量级。有界重放本质是近似，上线前必须逐场景验证，不能只看一个benchmark打平。

【传送门】

Torch Profiler在Trace里分析性能瓶颈: 剖析SGLang LLM推理
英伟达Kernel Agent: 编译器与算子调优Agent的协同设计
把KVCache变成可训练记忆：Context Tuning让LLM免权重微调
Kimi K3技术详解之KDA: 线性注意力如何精准编辑被压缩的记忆
KVCache缝合术: 突破前缀匹配天花板,首Token快14倍 多文档快2~4倍
MLP就是Hebbian记忆: 无需训练，往Transformer块注入事实知识的构造方法
vLLM+Mooncake: 把agentic前缀复用从1.7%拉到92.2%
在NVFP4上超越cuBLAS: 从零手写+Claude极限优化Blackwell GEMM
Kimi K3技术解析之AttnRes: 打破Transformer沿用十年的残差各层等权的假设
TokenSpeed-Kernel：把推理内核做成一等公民
Kimi K3技术报告-后训练Infra: 三阶段RL,MoonEP3,五千万沙箱,KDA感知缓存
Kimi K3技术解析之LatentMoE: 隐藏维度压缩至潜空间，通信与带宽开销同比例骤降
AI芯片架构全景: 从NVIDIA到Groq的六条设计路线
小米MiMo罗福莉:8卡GPU让1T参数模型跑出1000 TPS , FP4+DFlash+TileRT全解读
RL的下一个大突破：不是优化可验证问题而是把'不可验证'领域变得'可验证'
阿里Sparse Attention on CXL替代RDMA做KV Cache解耦 推理2.1×吞吐, 9.7×TTFT

参考：https://www.lmsys.org/blog/2026-09-10-deepseek-v41