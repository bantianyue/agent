# -*- coding: utf-8 -*-
import os,json
D=os.path.dirname(os.path.abspath(__file__))
S=[]
def h2(t): o={"type":"h2","title":t,"paras":[]};S.append(o);return o
def t(o,*p): o["paras"]+=list(p)

s=h2("一句话结论与数字")
t(s,"vLLM 官方把 AgentX(SemiAnalysis 的开源 agentic 基准)作为考卷，讲它怎么为真实 agentic 服务做整套优化。在 DeepSeek V4 Pro 上可到每 GPU 秒 130K 总 token，MiniMax M3 上交互度最高约每秒 376 token；在 DeepSeek V4 Pro、MiniMax M3、Kimi K3 三个开放前沿模型上，vLLM 相对 Opus 5 的 API 定价有 14.6x 到 106x 的 serving 成本优势。")
s=h2("agentic 负载到底长什么样")
t(s,"自从五月讲 agentic serving 起，这类流量占比持续涨；OpenAI 报告 2026 年 6 月企业客户里 Codex 已占 Codex+ChatGPT 输出 token 的 64%。高 token 消耗从两个轴压服务栈：成本决定固定硬件预算里能同时塞几个 agent，延迟决定每个 agent 一轮推理加工具调用推进多快；优化 agentic serving 就是整体推这条延迟-成本曲线。")
t(s,"AgentX 用真实编码轨迹给出四条画像：多轮长会话、单场中位数 43 轮；长上下文配短输出，输入中位数 142K、输出 444；前缀复用极重，prefix-cache 命中率高于 96%；subagent 很常见，44% 会话含至少一个 subagent，其中子代理 rollout 中位数 4 个。")
s=h2("它带来的三个挑战")
t(s,"一是前缀缓存压力。多轮会话每轮都整段重演已聊内容，要同时跑很多场，引擎得在轮次间把 KV cache 外置；到规模上 KV 管理、前缀缓存、外置还要跨 GPU、跨 prefill/decode 拆分实例和副本高效协作。二是执行效率。长上下文加要紧的延迟预算，同样时间要处理更多 token、每 token 干更多，并行、kernel、调度、投机解码都得住新请求形状上适配。三是找对 P/D 比例。各会话各 subagent 的上下文与缓存命中率差异大，路由要在 rank 间平衡 cache 亲和与负载；不同并发下要最大化吞吐的 optimal P/D 比很难一次摸对。")
s=h2("数据面：让 KV 缓存又暖又近存算")
t(s,"混合 KV 缓存管理是地基。从 PagedAttention 到 agentic 长上下文，KV cache 容量压力更重；现代混合模型把滑动窗口、线性 attention 与全 attention 混用，不同缓存块尺寸与生命周期都不一样。vLLM 的办法是把一个统一内存页当作基本分配单位、走一个共享块池管理。共享池让它按需动态重分配，而不按 attention 类型静态分区，因为全 attention 的 KV 随长度涨、滑窗和循环态另有自己的生命周期，最优分区随并发、上下文、前缀复用变。")
t(s,"这个抽象继续演进以吸收碎片与迁移开销。例如 DeepSeek V4 初版 KV 布局把不同缓存类型分成三个尺寸桶、拆出 92 个张量，有一些填充浪费、对 P/D 迁移与外置不友好。新的紧凑布局改为每块一个连续 backing allocation（把缓存组与层装在一起）而非 92 个零散张量，减少描述符与 P/D 迁移开销；启用 FP4 indexer 后还可更小分配单位，约省 10% KV cache 内存。")
t(s,"分级外置 + 分布式池。超出显存容量的前缀缓存、跨引擎保留，vLLM 集成 MooncakeStore 提供分布式 KV 池（详见他们之前博客），现在被越来越多采用；继续在为 agentic 负载补容量、效率与保留策略。模型架构平齐方面：外置集成在 vLLM 是一等公民，完整支持稀疏 attention、压缩 attention、线性 attention 等新架构，同时异步调度、P/D 拆分、投机解码、并行等其它引擎特性保持正常。分级外置还能用磁盘和额外纯 CPU 节点扩池：MooncakeStore 的 standalone 模式让外部 Mooncake 客户端持有 CPU 池与磁盘层、vLLM worker 变成纯请求方，每节点挂一个客户端即用 CPU 与磁盘扩池。池又和 Dynamo、llm-d 这类 router 集成，请求在任意实例都能命中缓存。性能上混合模型要为每种 attention 单独构造 key/查表，CPU 开销成倍；他们靠更好的数据结构、异步查表、把工作挪出 scheduler 关键路径、并行收发来压，细节见 PR#46188/45444/45659/47317。")
t(s,"会话感知的前缀缓存保留。对线性或滑窗与全 attention 混合的模型，前缀复用要保住线性态或滑窗缓存；每 token 都留快照太贵，于是结合两条互补策略。间隔式保留：每轮结束自动保留 prompt 端缓存/线性态，之后延续轮与分叉 subagent 常重放并扩展上一轮上下文，可复用；但共享前缀大多在轮内就结尾，间隔保留未必留到检查点。于是第二条：Marconi 式选择保留，当某前缀第二次被见到才留检查点，命中过但没留检查点的，就重算缺失态并在此边界存一次，后续共享前缀便能复用。两者结合在高命中率与可承受存储之间取平衡（技术细节见 Kimi K3 那篇）。")
s=h2("执行面：把 token 快地产出来")
t(s,"模型专属并行。现代推理有 TP/DP/EP/PP/CP 多条并行轴，选哪样取决于模型结构、硬件拓扑、负载形态与延迟 SLO。下面看 GB/B 系两张代表卡上两个模型。")
t(s,"Kimi K3。它有 MLA 与 Kimi delta attention(KDA)。MLA 把 KV 压进单 head 的单潜空间，朴素 TP 会在各 rank 复制这份 latent 缓存，并不划算。改成 decode context parallelism(DCP，沿序列维切缓存、每 rank 留 1/N KV) 对 agentic 有两个好处：decode 延迟更低，MLA attention 内存受限、成本随上下文涨，前缀越长 attention 占每步比例越大；吞吐与 KV 容量更高，避开 KV 复制就能让更多序列在途而不被 admission 卡住。代价是多一份通信：每层 MLA decode 在 attention 前要 query gather、结束后做 partial-output reduce。")
t(s,"DCP 计算路径被仔细优化以绕开 NCCL：用对称内存缓冲让对端 GPU 直接 load/store；query 直接多播进 attention kernel 消费的缓冲；每张 GPU 把 partial attention 输出与 log-sum-exp 统计直接写进对端接收槽，各 rank 用 online softmax 本地合并；还把这些 GPU 间直写与计算融进同一 kernel(s)，比默认 DCP8 每层省约 13% 延迟。更大的 scale-up 域会改最优策略：NVL72 级系统上宽 EP+DP(DEP) 常比 DCP 更会扩展、同一 decode SLO 下吞吐更高，因为更大的多节点 DCP 里分片 attention 的通信会盖过它省的算力；DEP 把请求及其 KV 分到不同 DP rank、同时把 MoE 专家分到各 rank，避开 DCP 的 attention 集合通信。")
t(s,"DeepSeek V4。它也有 MLA 式 KV、在 TP 下复制导致内存低效；外加它特有的压缩稀疏 attention 让 TP 的 head 分片低效三处：compressor 路径每个压缩位置只产一份共享 KV 而非每 head 独立态，TP 无法沿 KV-head 维切算力、每个 rank 重复做 compressor；indexer 虽有 64 head 却每 token 只产一次全局 top-k 选择，现 TP 路径在每个 rank 复制整份 indexer，避开 top-k 前稠密 score reduce 却重复了活；稀疏 MLA 主要受累于扫与收集 top-k KV 条目而非 attention 算术，TP 在每个 rank 重做这段内存受限的活、只分了便宜的 head 向计算。实测 prefill context parallelism(PCP) 对长 prefill 最好，data+expert(DEP) 在更广服务条件下好。PCP 把 prompt 序列(query 张量)分片、把 compressor 与 indexer 工作摊到各 rank，给稀疏 MLA 更宽的局部 head 形状；32K prompt 下 PCP8 相对 TP8 有 2.65x prefill 加速，显著降 TTFT，但它 decode 侧态仍跨 rank 复制，最适合专职 prefill worker。DCP 因 V4 结构更复杂而不如对 Kimi K3 有效。DEP 把请求与 decode token 分到 DP rank、attention 全局部，成为多数 V4 配置的默认。")
s=h2("两层调度混跑 agentic 流量")
t(s,"agentic 服务混合了频繁的 append-only 请求（长前缀复用+短 prefill）与偶尔几万 token 的新鲜长 prefill，产生两个调度问题：实例内一个长 prefill 会挡短交互轮；DEP 各 rank 上 prefill 排布不均造成负载失衡。vLLM 用两个互补控制来解。")
t(s,"打破队头阻塞。默认 chunked-prefill 按 FIFO，一个长 prefill 会一步步占满整段预算、同 rank 排队的短轮完全排不进去。对策是 --long-prefill-token-threshold 限制单请求每步最多调度的 token 数；设成 512 时，长 prefill 能让出空间让短轮进同 batch 更早开始 decode。DeepSeek V4 Pro 在 B300 上因此每 GPU 秒 token(TPGS) 最多提升约 93%、p90 交互度约改善 2.3x；代价是长请求自身 TTFT 变高，TTFT 敏感部署应调高阈值。")
t(s,"对齐 DEP prefill 节奏。DEP 的 MoE all-to-all 让各 rank 必须同一步调前进，一个在腾 prefill 的 rank 拖慢整组；不同 rank 在不同步收到 prefill 时这惩罚会反复暴露。对策是 --prefill-schedule-interval：只每隔 N 个引擎步放行一次 prefill 工作，用跨 DP rank 对齐的计数器，把 prefill 集中到各 rank 同一批步、让中间步整段做 decode。")
t(s,"用对 P/D 拆分配置来扩。单引擎调到最好并不等于分布式部署的延迟-成本最优点，加 GPU 或者做 disagg 也不会自己改善曲线：prefill 与 decode 得速率匹配。他们用可被 agentic 工作流自动化的两阶段标准法：第一阶段饱和画像，把 prefill-only 与 decode-only 各自单独打点，扫并行策略(TP 对宽 EP)与规模(8/16/32 GPU)并把并发抬到吞吐饱和，产出每配置的饱和表(最大 prefill/decode req/s)；第二阶段 P:D 扫描，从第一阶段饱和点推出 P/D 比，再在合体 disagg 部署上扫并发、在运作区间内取指标。")
s=h2("回合闭环：模型专属 kernel 与社区贡献")
t(s,"agentic 负载把 kernel 瓶颈推向长上下文 attention、投机解码与通信。MiniMax M3：CuteDSL 长上下文 indexer 据报告在 GB300 上按形状把 indexer 延迟降约 3%-31%；上游化的 MSA top-k 路径把最坏情形 kernel 性能最多提升约 4x、AgentX 端到端吞吐大约 7%；投机验证路径在中 batch decode 性能报告中约提升 20%。Kimi K3：GEMM 与 reduce-scatter 融合改善 sequence-parallel 通信，latent-tail MoE 融合端到端延迟约降 5%。DeepSeek V4：社区贡献改善 MXFP4 MoE 与 HCA 压缩(#43584/#44230)、加多流 C4A、改进 cluster-based top-k。所有 kernel 全开源，一些已被其它开源引擎采用。")
s=h2("性能：agentic 优先且公开可验")
t(s,"vLLM 用从 300 万美元真实 agentic 编码轨迹(1M 上下文)构建的公开基准、跑在 1000+ 芯片约 2MW 上，展示它是 agentic-first。对三个开放前沿模型取的是 p90 交互度守住每秒每用户 50 token 高延迟 SLO 下的最高吞吐配置。DeepSeek V4 Pro：12 芯片 GB300 PD 部署服务 256 个并发 agent 会话、p90 下每人每秒 58.3 token，此工作点每 GPU 秒约 83K 总 token。MiniMax M3：仅 2 张 B300，p90 每秒每人 74.2 token、给到 70K 总 TPGS。Kimi K3：2.8 万亿参数的巨型前沿模型，常规单机装不下；16 张 GB300 在 p90 下每秒每人 62.7 token、处理 11.8K 总 TPGS。")
t(s,"成本同样关键。理论前缀命中率高于 96% 其实是 agentic 流量给 vLLM 的成本来源：DeepSeek V4 Pro 用 GB300 基建 TCO 每小时约 28 美元跑完该工作负载；同样 token 量即便按每次理论上可复用的缓存读价都打折，Opus 5 也要约 2926 美元。MiniMax M3 在 B300 上是 85x 优势，Kimi K3 在 GB300 上即便模型大得多仍便宜 14.6x。数字报告到今天，但 dashboard 在线可交互，AgentX harness 在 SemiAnalysisAI/agentx-harness，每条结果链到 InferenceX 可复现。")
s=h2("苦涩教训：哪失败了、学到什么")
t(s,"第一，Pipeline parallelism(含 chunked CPP) 不适合“暖”的 agentic 轮次。PP 在又长又冷的新鲜 prompt 上好，大 prefill 能填满流水各级、吞吐几乎线性、通信少；但多数 agentic 轮已有 system prompt 与之前轮次被缓存，每新请求可能只加几百几千 token，鲜算的量填不满流水，bubble 吃光潜力。结论不是 PP 没效，而它是冷的大 prefill 有用，不该是占主导的暖且前缀重的轮次的默认。")
t(s,"第二，DCP 不能干净迁移到 DeepSeek V4。对纯 MLA(如 R1、K2.5/K2.7)与混合 MLA(K3)都好用，V4 却因更复杂的 attention 栈而难兑现：压缩稀疏与高压缩 attention 有 indexer、额外 compressor 与主 attention，context parallelism 得切分并协调所有这些子层，引入可观通信与实现复杂度。即便大把做通信-计算重叠并优化 kernel，DCP 也只是追平 DEP 而非超越。结论强化执行面观点：并行必须跟随模型架构，一个 latent-attention 模型成立的策略未必迁移到另一个。")
t(s,"第三，负载均衡不保证更好性能。DEP 聚合部署里 KV 使用明显失衡，自然反应是按队列深度、进行中 token 或当前 KV 占用去均衡请求；但 AgentX 上这些策略全部跑输简单的 session-aware sticky 路由。原因是 cache 局部性：很多 agentic 会话轮间延迟短，下一轮常在前序前缀仍驻原 GPU 时就到，把它挪到负载更低的 rank 虽前缀在分布式池里保留着，却要系统取回 KV；迁移本身异步并与计算重叠，仍不是免费的，预取的块临时占 GPU KV 容量、降低目标 rank 可接纳序列数。于是队列更平了，同时处理中的并发反而更少。对轮间延迟短的工作负载，留住 session 局部性比瞬时均衡更有价值：路由决策要看每 worker 上已驻留的状态，而不只看排队的工作量。")
s=h2("下一步")
t(s,"方向是让 agentic 结构在整个 serving 栈显式化。控制面：对第一轮请求(常需长的新鲜 prefill 去把前缀缓存填起来)与 2+ 轮请求(高缓存复用、短 append prefill)分开更显式的路由，避免队头阻塞，并允许两端各自配引擎设置与并行(如 PCP 与 CPP)。执行面/数据面与社区合作支持：agent hints——让 agentic 框架或 harness 随请求带上会话结构、潜在分支点与缓存位置、工具调用延迟、会话生命周期等，第一步用标准化 API 消费，再用来指导调度、缓存淘汰等；可编程 KV cache——不同负载要不同放置/保留/复制/淘汰策略，编程接口让用户按负载形态控制预取、淘汰、软 pin；基于会话的 KV 管理——轮间间隙是移动保留态的好时机，空闲期预取可藏住迁移延迟、减少冷启动恢复。")
s=h2("致谢")
t(s,"这项工作由 inferact 主导、获 vLLM 社区大力支持；感谢 SemiAnalysis 开发并运维开放 AgentX 基准、使其方法可复现。")
d={"title":"vLLM x AgentX：为真实 agentic 服务做优化（全文直译）",
 "reference_url":"https://x.com/vllm_project/status/2097427730983776758",
 "summary":[
  {"key":"一图流","body":"agentic 负载(多轮/长上下文/96%+ 前缀复用)是 vLLM 流量大头。vLLM 在 AgentX 基准上对 DeepSeek V4 Pro 做到 130K token/GPU 秒、MiniMax M3 交互度最高 376 token/s；三个开放前沿模型相对 Opus5 有 14.6x-106x serving cost 优势。办法是数据面(混合 KV 管理/紧凑布局/分级外置/会话感知保留)+执行面(按模型选 DCP/EP-DEP/PCP)+双层调度与 P:D 率匹配，并分享三条苦涩教训。"},
  {"key":"教训速记","body":"PP 只适合冷的长 prefill；DCP 迁不到 DeepSeek V4(注意层栈太复杂)；负载均衡不如 session 局部性(短轮间延迟下移动会话要取回 KV、反降并发)。并行必须跟着模型架构走。"}
 ],
 "lead":["vLLM 官方发布长文，讲在真实 agentic 负载(它们的编码与工具流量)上如何让 serving 又便宜又低延迟，并给出可公开复现的数字。以下为全文中文直译导读，覆盖数据面、执行面、P/D 拆分、苦涩教训与后续路线，图随正文按序嵌入。"],
 "sections":S,
 "conclusion":["三句话收束：agentic 流量把优先级从裸算力挪到 KV 缓存的热度与就近、并行必须匹配模型新结构、路由要听缓存的局部位。其余精度来自把 prefill 与 decode 速率匹配以及会话结构显式化。" ]}
# ---- evenly embed 8 body figures across non-empty paragraphs ----
import math
SLOT=[]
for sid,sec in enumerate(S):
    for pidx,pa in enumerate(sec['paras']):
        if pa.strip(): SLOT.append((sid,pidx))
L=len(SLOT); N=len([f for f in os.listdir(D) if f.startswith('fig') and f.endswith('.png')])
take=sorted({int(round(i*(L-1)/max(1,N-1))) for i in range(N)} if N>1 else {0})
take=[x for x in take if x<L]
# refill if dedupe shrank
for k in take:
    sid,pidx=SLOT[k]
    fig=f"fig{take.index(k)+1:02d}.png"
    S[sid].setdefault('fig_after',{})[str(pidx)]=[{"src":fig,"caption":""}]
json.dump(d,open(os.path.join(D,'article_data.json'),'w',encoding='utf8'),ensure_ascii=False,indent=2)
print("sections",len(S),"paras",L,"figs",N,"anchored",len(take))
