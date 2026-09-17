/* 传送门统一样式（add-portal.py 动态注入时引用此 class） */
.portal-title { font-size:12px; color:#888; }
.portal-links { font-size:12px; color:#888; }
.portal-links a { color:#888; text-decoration:none; }

要点速览

- 吞吐规模：512 张 MI355X 上 gpt-oss-120b offline 跑到约每秒 575 万 token，DeepSeek-R1 约 290 万 token，是 MLPerf 历史上按 GPU 数计规模最大的 MI355X 推理提交- 线性扩展：从 8 卡到 512 卡吞吐线性增长、达到理想值的 90% 以上，全程只用 400Gb 以太网，没有 InfiniBand、没有 RoCE、没有跨节点 all-reduce- 成本含义：每卡 288GB HBM3E 让 671B 的 DeepSeek-R1 留在单节点内、分片只走 XGMI，省掉昂贵的 RDMA 组网与跨机箱集合通信

512 张 AMD Instinct MI355X、64 个节点、Crusoe Managed Kubernetes，一次提交同时跑 gpt-oss-120b 与 DeepSeek-R1：这是 MLPerf 历史上按 GPU 数量计规模最大的 MI355X 推理提交。
比数字更值得看的是扩展方式。吞吐从 8 卡到 512 卡保持线性，全程只用经过 RoCE 的 400Gb 以太网，没有 InfiniBand，也没有跨节点 all-reduce，而且整套基准测试就是一个普通的 Kubernetes 工作负载，用的是客户在生产里跑的那套平台。

512 张 AMD Instinct MI355X 上的 MLPerf Inference v6.1 结果
上个月，Crusoe 向 MLPerf Inference v6.1 提交了 gpt-oss-120b 与 DeepSeek-R1 的结果，在 AMD Instinct MI355X 上以 512 卡规模运行，平台是 Crusoe Managed Kubernetes。这是迄今为止 MLPerf 历史上按 GPU 数量计规模最大的 MI355X 推理提交。

图 1：代表 Crusoe AMD Instinct MI355X 集群的等距视角服务器机架示意
有三件事对推理负载的意义超过了原始数字本身。
●&nbsp;吞吐从 8 卡到 512 卡线性扩展，达到理想值的 90% 以上，这意味着负载可以按预期压力确定性地自动伸缩。
●&nbsp;不需要任何特殊 RDMA 互连。这个规模的推理并不必然要求跨节点集合通信。整个 512 卡运行在标准 400Gb 以太网上完成协调，没有 InfiniBand、没有 RoCE，也没有跨节点 all-reduce。
●&nbsp;基准测试作为典型的 Kubernetes 工作负载运行，用的就是客户在生产中使用的同一套 Crusoe Managed Kubernetes 平台，同样的可观测性、同样的故障处理。相关清单已经开源，任何人都可以复现。
这篇文章覆盖结果、分析以及开展这些基准测试所用的方法论，读者可以据此自行复现。完整的复现仓库已开源于 GitHub。
所有结果均为 MLPerf Inference v6.1 闭源组（closed division），512 张 AMD Instinct MI355X，跨 64 个节点，由 Crusoe Managed Kubernetes 作为主要编排器。
Server 场景的结果在 v6.1 的延迟 SLA 下测得：gpt-oss-120b 的 p99 首 token 时延（TTFT）低于 3.0 秒、p99 每输出 token 时延（TPOT）低于 80 毫秒；DeepSeek-R1 的 p99 TTFT 低于 2.0 秒、p99 TPOT 低于 80 毫秒。两个运行都以余量通过（gpt-oss 实测 2.69 秒 TTFT 与 36.5 毫秒 TPOT，DeepSeek 实测 1.85 秒 TTFT 与 79.98 毫秒 TPOT），说明我们本可以推高 QPS 拿到更高吞吐。
两个模型都通过了闭源组的精度要求：gpt-oss-120b 精确匹配率 83.7%，参考下限 82.3%；DeepSeek-R1 精确匹配率 80.7%（下限 80.54%），平均输出长度 3,898 token，落在要求的 3,497.6 至 4,274.85 区间内。
已发布的完整结果可以在 MLCommons 的 MLPerf Inference v6.1 闭源组结果中查询。

模型场景总吞吐单卡吞吐

gpt-oss-120bOffline~5.75M tok/s~11.2k tok/s
gpt-oss-120bServer~5.39M tok/s~10.5k tok/s
DeepSeek-R1Offline~2.90M tok/s~5.7k tok/s
DeepSeek-R1Server~2.40M tok/s~4.7k tok/s

软件配置
两次提交所用的软件与节点配置如下。两个模型都跑在 8 卡 MI355X 节点上，每张卡 288GB HBM3E，配 2 颗 AMD EPYC 9575F，操作系统 Ubuntu 24.04；节点间是 8 条 400Gb RoCE，单节点聚合 3200 Gbps。差异集中在推理引擎：gpt-oss-120b 用 vLLM 0.22.1，DeepSeek-R1 用 SGLang 0.5.15.post1，两者都启用了 AITER 与 hipBLASLt，后者还用了 MoRI-EP。

组件gpt-oss-120bDeepSeek-R1

推理引擎vLLM 0.22.1（AITER、hipBLASLt）SGLang 0.5.15.post1（AITER、hipBLASLt、MoRI-EP）
AMD ROCm7.2.27.2.0
容器镜像rocm/amd-mlperf (v6.1)rocm/sgl-dev:v0.5.15.post1-rocm720-mi35x
节点类型mi355x-288gb-roce.8x：8 张 MI355X（每卡 288GB HBM3E），2 颗 AMD EPYC 9575F，Ubuntu 24.04mi355x-288gb-roce.8x：8 张 MI355X（每卡 288GB HBM3E），2 颗 AMD EPYC 9575F，Ubuntu 24.04
网络400Gb 以太网，每节点 8 条 400Gb RoCE（聚合 3200 Gbps）400Gb 以太网，每节点 8 条 400Gb RoCE（聚合 3200 Gbps）

生产环境：从 8 卡到 512 卡的线性扩展
为了模拟生产推理负载，通常需要有一个自动伸缩的应用，规模在几十卡到几百卡、乃至几千卡之间变化。扩展之所以成立，是因为这个形态下的推理高度并行，vLLM、SGLang 这类推理引擎本身就是为并发设计的。由于 gpt-oss 与 DeepSeek-R1 都能装进单个 MI355X 节点的 HBM，副本之间从不需要互相同步，也就没有随节点数增长的跨节点 all-reduce 通信开销。节点间唯一的流量是前端的输入与输出流。

图 2：聚合输出吞吐量随 GPU 数量从 8 张扩展到 512 张的变化
对客户而言，容量规划因此变得确定。如果你的生产部署在 64 卡上稳定跑到某个每秒 token 数，就可以通过简单乘法推算 512 卡部署的规模。把自动伸缩器与 Crusoe Managed Kubernetes 配合起来，容量就能跟着需求走：流量高峰时扩容，回落时缩容，只为差额付费，而不是为峰值长期预留资源。
降低总体拥有成本
这套配置从两个方面压低规模化之后的总体拥有成本：一是让每个模型都留在单节点内的显存容量，二是完全不需要昂贵的横向扩展 RDMA 网络。
288GB HBM3E 把大型 MoE 模型留在单节点内
DeepSeek-R1 是一个 671B 参数的 MoE，每个 token 大约激活 37B 参数。在 FP8 下光权重就约 671GB，算上 KV cache 之后，典型加速卡根本放不下。在 MI355X 上，同一个模型可以舒服地待在单个 8 卡平台里，合计 2.3TB HBM3E，还剩下超过 1TB 给 KV cache 复用。
正是这份容量消掉了分片开销。DeepSeek-R1 分布在单个节点的 8 张 GPU 上，但这部分通信的每一个字节都留在节点内的 AMD Infinity Fabric（XGMI）上。没有跨机箱的 all-reduce，没有跨越网络跳的流水线阶段边界，也没有 GPU 在集合通信进行时空转。
在这套配置里，注意力层还采用数据并行而非张量并行，因为 DeepSeek 的多头潜在注意力只缓存一个压缩后的潜在 KV 头。用张量并行切分这个头，会让每个 rank 都复制一份 KV cache，占掉本该用来承载并发请求的显存。让注意力保持数据并行，每个 rank 用一份 KV cache 服务自己的请求，批大小与总吞吐都得以保住。专家层则跨 GPU 分区，因为专家权重占了显存的大头，而每个 token 只激活其中一小部分，于是每个 rank 只为自己负责的专家所接收的 token 做计算。
同样的容量为中尺寸模型留出服务余量
gpt-oss-120b 的 MoE 权重以 MXFP4 存储，约占 65GB。它以张量并行度 1 运行，也就是完整权重都放在显存里，于是我们部署了 512 个完全独立的单卡副本。这就不需要任何分片或张量并行，前向传播中没有集合通信，副本之间也完全没有协调。整个集群里每张 GPU 都是一个独立的服务单元。
288GB 带来的改变不只是模型装不装得下，还有它旁边能装什么。扣掉权重与激活之后，每张 MI355X 仍有超过 200GB 可用于 KV cache，而 80GB 卡上大约只有 15GB。KV cache 容量决定每个副本能并发多少条序列，而并发序列数正是结果表里单卡吞吐的来源。这份容量余量会直接变成每美元 GPU 的每秒 token 数，也提高每瓦的总 token 性能。
大规模推理不需要昂贵的专用网络
因为副本之间从不互相同步，这次 512 卡的运行完全在 RoCE 以太网上完成协调。这套配置里没有 InfiniBand，也没有因为缺少它而损失任何吞吐。
对以推理为主业构建集群的客户来说，这从集群物料清单里去掉了一大笔开支，而且实测没有任何性能代价。真正起作用的是节点内的纵向扩展网络，横向扩展网络只需要把 token 搬出去。
为什么我们在 Kubernetes 上跑 MLPerf
MLPerf Inference 的参考测试框架是为在单机、裸金属或虚拟机上以 Docker 容器运行而设计的。这套模型放到跨 64 节点的 512 卡运行上既不好扩展，更关键的一点是，它并不是 Crusoe 上生产推理的真实运行方式。
与其手工编排 64 个 SSH 会话，我们把基准测试重新表达成了 Kubernetes 原生清单。
这个选择直接带来三件事。
●&nbsp;扩展性。同一个 worker Job 只要改一个参数，就能在 parallelism=1 或 parallelism=64 下运行。8 卡冒烟测试与 512 卡正式提交用的是同一份清单。
●&nbsp;可观测性。Pod 日志、事件与资源指标都通过标准 Kubernetes 接口获取，不需要任何定制搭建。我们发布并维护一套基于 Crusoe Managed Metrics 的 Grafana 方案，客户第一天就能获得同样的视图。
●&nbsp;容错。一个副本崩溃只是一个被重启的 Pod，而不是一次失败的运行。拖后腿的副本在单副本吞吐中清晰可见，可以被优雅地驱逐。
Crusoe Command Center 实战
下图是用 Crusoe Managed Metrics 搭建的 Grafana 面板，可以看到 512 卡 gpt-oss-120b offline 运行期间 GPU 与显存的利用率。我们提供一个托管的 PromQL 端点，用来收集客户 Crusoe VPC 内计算、存储与网络资源的基础设施日志，可直接用于填充第三方可观测性面板。评测期间，我们用这些指标跟踪运行中负载的性能与状态。

图 3：一次 512 卡 gpt-oss-120b offline 运行中的聚合 GPU 与显存利用率，来自 Crusoe Managed Metrics 的 Grafana 面板
这些指标还可以用来针对基础设施故障设置自定义告警，比如 GPU 故障、存储瓶颈，或者 VPC 与 RDMA 网络争用。Crusoe Watch Agent 现在默认随各类基础设施资源一起交付，为管理 AI 负载铺平了通往生产的道路。
MLPerf 被测系统（SUT）方法论
MLPerf 的 LoadGen 二进制必须看到单一的被测系统。在 512 卡规模上，我们把这个 SUT 构建成由 ZeroMQ（ZMQ）连接的 head 加 workers。

图 4：512 卡分布式 SUT。一个专用 head pod 运行 LoadGen 与调度，64 个 worker pod 各拥有一个节点的 8 张 GPU，通过 ZMQ 连接
在放大推理测试的过程中，我们在编排层遇到瓶颈：规模一上来，worker 就无法可靠地向 head 节点注册。这也是最终设计成一个专用 head pod 的原因，它只做调度与 LoadGen。它不承载任何模型，因此不会成为计算瓶颈。64 个 worker pod 每个拥有一个节点的 8 张 GPU，而这 8 张卡怎么用取决于模型。
●&nbsp;gpt-oss-120b：每个节点 8 个独立的单卡副本，张量并行度为 1，共 512 个副本。模型以 MXFP4 装进单张 GPU，因此不需要分片。
●&nbsp;DeepSeek-R1：一个副本分片到节点的全部 8 张 GPU 上（TP8、EP8、8 路 DP 注意力），共 64 个副本。671B 的 MoE 对单张 288GB GPU 来说太大，所以必须分片，但只在节点内部、走 XGMI。
没有任何跨节点集合通信。节点间唯一的流量，是前端以太网上由 ZMQ 承载的分词输入与输出流。
测试场景
Offline 测的是没有延迟约束的原始批处理吞吐。device_count 是节点数的 8 倍，target_qps 调得足够高，让 LoadGen 发出足够多的样本填满 20 分钟的最小持续时间窗口。
Server 测的是在 p99 延迟 SLA 约束下的吞吐，SLA 同时覆盖首 token 时延与每输出 token 时延。target_qps 调到仍能通过 SLA 的最高值。再往上推会形成调度积压并打爆 p99。gpt-oss-120b 的可持续点是 target_qps 4000，DeepSeek-R1 是 target_qps 688。
自己复现
以上所有内容都开源在 crusoe-mlperf-mi355x-inference-v6.1 仓库中。
先小规模验证流水线再放大：N=1（8 卡），然后 N=8（64 卡），最后 N=64（512 卡）。精度与合规性和规模无关，所以正确性可以在 N=1 上确认，整个集群只用来跑吞吐数字。各模型的命令在顶层 README 中。
接下来
虽然这是 Crusoe 第一次提交 MLPerf Inference，但不会是最后一次。我们公开这些结果与背后的代码，是为了给客户和伙伴提供可触摸的基准，让他们亲眼看到我们如何在规模上验证性能。每个 Crusoe 集群在交付到客户手上之前都会做端到端验证，包括持续负载下的工作负载验证、GPU 与 HBM 压力测试、InfiniBand / RoCE 网络验证以及参考工作负载基准。MLPerf 只是这套流程中的一件工具。客户拿到集群时，性能特征已经对照一个公开、经过同行评审的标准被测过。
在 Crusoe，我们与 AMD 在硬件性能与软硬协同设计上紧密合作，从 ROCm 与推理引擎调优，一直到集群交付与网络验证。这种合作是我们能构建最可靠、最出色的 AMD 集群的原因，而 MLPerf 这样的公开基准是我们证明它的方式。这篇文章里的每个数字都经过同行评审且可复现：MLPerf 历史上规模最大的 MI355X 推理提交。我们会继续与 AMD 及伙伴深化这项工作，并持续公布推理与训练两类负载的结果，让我们引用的数字始终是任何人都能验证的数字。
准备好在这样的规模上做服务了？可以联系 Crusoe 团队，了解如何在 Crusoe Managed Kubernetes 上用 AMD Instinct MI355X 运行推理。已经在用 Crusoe 的话，Crusoe Managed Kubernetes 文档可以带你上手。

结语

每秒 575 万 token 的意义不在数字本身，而在于它拆掉了「大规模推理必须配一套昂贵的 RDMA 网络」这个默认假设。让这件事成立的机制只有两条：模型小到能装进单节点，副本之间就永远不必同步；不必同步，就没有随节点数增长的跨节点集合通信。扩展性由此从一个网络工程问题退化成一次乘法，容量规划也就有了确定性。288GB HBM3E 的另一半价值容易被忽略：它决定的不只是模型放不放得下，还决定了权重旁边能留多少 KV cache。gpt-oss-120b 每卡留给 KV cache 的空间超过 200GB，而 80GB 卡上大约只有 15GB。在按并发调度的推理引擎里，KV 池就是并发上限，并发上限就是单卡吞吐，显存容量于是被直接换算成每瓦 token 数。对做推理集群选型的人来说，判断顺序应该是先算模型能否留在单节点内，再决定要不要为横向扩展网络付钱。gpt-oss-120b 以 MXFP4 只占 65GB，于是每张卡都是一个独立服务单元；DeepSeek-R1 需要 2.3TB 的单节点显存，于是分片只发生在 XGMI 上，不跨机箱。两种形态的共同点，是网络只负责搬 token，不参与计算。

【传送门】

Kimi K3技术解析之AttnRes: 打破Transformer沿用十年的残差各层等权的假设
vLLM+Mooncake: 把agentic前缀复用从1.7%拉到92.2%
TokenSpeed-Kernel：把推理内核做成一等公民
Torch Profiler在Trace里分析性能瓶颈: 剖析SGLang LLM推理
Kimi K3技术解析之LatentMoE: 隐藏维度压缩至潜空间，通信与带宽开销同比例骤降
在NVFP4上超越cuBLAS: 从零手写+Claude极限优化Blackwell GEMM
AI芯片架构全景: 从NVIDIA到 Groq的六条设计路线
RL的下一个大突破：不是优化可验证问题而是把'不可验证'领域变得'可验证'

参考：https://www.crusoe.ai/resources/blog/serving-5-75-million-tokens-per-second-crusoes-mlperf-inference-v6-1-results-on-amd-mi355x