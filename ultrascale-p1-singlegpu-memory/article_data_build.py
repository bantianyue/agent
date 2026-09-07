# ultralit builder
import os,json
D=os.path.dirname(os.path.abspath(__file__))
fx=lambda **k: k
S=[]
def h2(t): o={"type":"h2","title":t,"paras":[],"fig_after":{}};S.append(o);return o
def txt(o,*pp): o["paras"]+=list(pp)
def fig(o,src,cap): o.setdefault("fig_after",{})[str(len(o["paras"])-1)]=o.setdefault("fig_after",{}).get(str(len(o["paras"])-1),[])+[{"src":src,"caption":cap}]

o=h2("先从三个紧箍咒讲起")
txt(o,"写这本书(nanotron 的 Ultra-Scale Playbook：训练 LLM on GPU clusters)时，几乎每个技巧都在跟同三道坎缠斗：①显存占用——硬约束，训练步装不进显存就根本没法训；②算力效率——让硬件多数时间在计算，而不是耗在传数据或等别卡干活；③通信开销——通信让 GPU 空等，得尽量把 intra-node 的快速带宽用足、把通信和计算尽量重叠。而且这三者能互相换(如 recomputation、Tensor Parallelism 都是用别项成本换)——大模型训练的第一步，其实是找一个平衡，不同 tradeoff 正是量表全书主线。") 
txt(o,"这本书作者按自己 4000 多次扩展实验(超跑 30+ 模型规模、含 DeepSeek/LLaMA 工作流)写就，有一个整书速查 cheat sheet 随时对照全书地图(如下图)。")
fig(o,"cheat.png","全书目录一图流：从单卡、DP、ZeRO、TP/SP/CP、Ring、流水、专家并行到 Kernel/FP8 的通行证。")

o=h2("单卡起步：一次训练步其实是三步")
txt(o,"把任务缩小到单 GPU：训练典型就是(1)前向(把输入过一遍模型得到输出)/(2)反向(算出梯度)/(3)用梯度做一次优化步更新参数。前四个细节步后面再看。")
txt(o,"batch size 是好胜的关键且同时影响收敛与吞吐：训练早期小 batch 能快速跨过地形到较优学习点;往后小 batch 会让梯度吵、难以收敛到最优;而过大 batch 梯度估计准、却每个 token 用处变低、浪费计算又收敛慢(可看 OpenAI large batch paper 与 MiniMax-01 §4.2)。另一个视角是影响耗时——同等样本小 batch 要多做优化步，而优化步很贵。所幸在最优附近 batch size 往往有较宽的平稳区，别太敏感。LLM 预训练里习惯用 token 计(bs_t)：bst=bs×seq。近年大模型甜点区大概每 batch 4–60M tokens：LLaMA 系列 ~4M(tok over ~4.3T tokens)，DeepSeek 系列 ~60M(14T)。")
txt(o,"Scale 到这几个数量级 batch 时，第一个挑战已逼到眼前——显存不够(OOM)。问题不在网络，而是训练一个大 batch 需要的内存。于是得先弄清训练到底把什么放进显存。")

o=h2("显存里有哪四样：先给个可以背的账")
txt(o,"训练时显存主要放四种：模型权重、梯度、优化器状态、以及算梯度要用的激活。精确算有点难因为 CUDA 内核一般再占 1-2GB、还有内存碎片之类——通常当小常数忽略。")
txt(o,"张量以不同 shape 与精度存放。shape 由 batch size、seq、hidden、head、vocab 等超参决定;精度 FP32/BF16/FP8 逐值分别 4/2/1 字节。于是：参数量(简单 transformer)N≈h·v+L·(12h²+13h)+2h(hidden=h, vocab=v, 层数=L)。h² 项随规模二次增长、必将主导。全精度(FP32)下：权重 m=4N、梯度 4N；Adam 优化器需存一阶矩 momentum+二阶方差 variance，各 4N → m_opt=8N。")
txt(o,"混合精度(mixed precision，现代默认)不是把全部存成低精度就完，而是用 BF16 做主计算(每参 2B)、外加一份 FP32 的权重与梯度主副本(每参 4B×2)，所以参数/梯度其实 占用 2N+2N(p32主副本)…下面总结一表。")
txt(o,"参数/梯度/优化器态的每参数字节账（N=参数量）：FP32 训练 → params 4N、grad 4N、opt(Adam) 8N；BF16+FP32 主副本(无 FP32 梯度累加)→ params 2N、grad 2N、params_fp32 4N、opt 8N → 合计 16N…(注：有些库另把梯度也存 FP32 以稳小值，如 nanotron，那样再加 4N。)")
txt(o,"于是单卡一 B 就 16GB、7B 约 112GB、70B 约 1120GB、405B 约 6480GB（若梯度也 FP32 累加则更大）——到 7B 就明显超过单卡(S80GB H100)容量。这还没算激活。")

o=h2("激活显存：公式、及它为何先爆")
txt(o,"激活不像权重好精确估，因它取决于输入。守恒推算可得每一层都要存，以及最后激活数混合精度的近似：m_act≈L·seq·bs·h·(34 + 5·n_heads·seq/h)。要点是公式里它对 seq 二次、对 bs 一次：也就是说<b>激活是最容易被 batch/长序列吹爆的那一块</b>(曲线比如 Llama、bs=1：短序列几近可忽略，到 seq≈2-4k 就显著;大 batch/长 seq 时激活反超参数成为最大负担)。")
txt(o,"(这套公式追到 NVIDIA recomputation 论文对每 op 之间中间张量逐项核算。也提醒：显存占用不是静态，而是随训练动态变化。)")

o=h2("第一招工具：激活重算(recomputation / gradient checkpointing)")
txt(o,"把前向里某些激活丢掉省显存、反向时多花一点算力现场重算。思路：无重算时每个可学算子之间的 hidden state 都存以算梯度;重算则只存少数关键点，其余反向时从最近的关键点重新各前向一段来换算力。策略：①Full——每个 Transformer 层交界处都 checkpoint，反向时等于每层多走一次前向，省最多但计算最贵(整体 compute 增加约 30-40%，很肉痛)；②Selective——原论文逐项分析谁长最大/谁能用最便宜 FLOP 重算，发现 attention 属此类可丢，专注存贵重的 feedforward：对 GPT-3(175B)约省 70% 激活显存、只 +2.7% 计算。DeepSeek-V3 用所谓 MLA 进一步把 attention 激活占得更小做 selective。")
txt(o,"FlashAttention 当代框架多已经「原生」做了激活重算(recompute attention scores)，所以用 FlashAttention 的人等于已在做 selective recomputation。注意重算会稍增 FLOPs 但显著降内存访问——在像 GPU 这种内存访问通常比计算慢的硬件上，整体常常反而更快。衡量效率时有两个指标要看：把重算也算进去的是 Hardware FLOPS Utilization(HFU)，只算模型 fwd/bwd 必要算子的是 Model FLOPS Utilization(MFU)——比硬件时若一卡靠内存够大能跳过重算以获得更快完训时间，该被认可而不该因低 HFU 被罚，因此 MFU 更贴模型本身。")

o=h2("第二招工具：梯度累积")
txt(o,"很直白的省显存法：把大 batch 拆成多个 micro-batch(mbs)，逐个做前反向、把梯度都累起来，各 micro 梯度求和(实际再除以累积步数取均值以与步数无关)后做一次优化步；优化步间隔的总量叫 global batch size(gbs)，且 gbs=mbs×grad_acc。它的价值：global batch 可以想多大多大而显存恒定;也与激活重算叠加。代价(no free lunch)：一批内要做多次连续前/反向，纯计算开销更高、训练变慢。")
txt(o,"可你马上会发现：这些 micro-batch 的前/反向彼此独立(只差输入样本不同)——那它们其实可以并行！是时候把训练搬到不只一块 GPU 上，进入 data parallelism 了。在这之前还有个口袋里常年有用的工具——profiler(如 torch.profiler 看 CPU 线程异步 launch kernel、多 CUDA stream 并行处理计算与通信、kernel 时长与显存分配，帮判定能否把梯度同步与反向重叠等)，本章末尾引出：data parallelism 本质上只是 gradient accumulation 的并行版。")

data = {
 "title":"训练 LLM 的显存账本：先会算、再谈百万卡—Ultra-Scale Playbook(1/6)",
 "reference_url":"https://huggingface.co/spaces/nanotron/ultrascale-playbook",
 "summary":[
   {"key":"这一篇","body":"nanotron Ultra-Scale Playbook 第1/6篇导读+显存建模：三大紧箍咒(显存/算力/通信)+batch计算；权重/梯度/优化器态每参数字节账；激活公式与两件武器(激活重算 FULL/selective + 梯度累积),一路到 data parallelism 门口。"},
   {"key":"可背数字","body":"参数量 N≈h·v+L(12h²+13h)+2h。FP32: param4N grad4N opt8N；BF16+FP32 master≈16N；内存实感1B=16GB/7B=112/70B=1120/405B=6480(GPU梯度累积另加4N)。激活≈L·seq·bs·h(34+5·nh·seq/h),对seq²·对bs一次。重算FULL+30-40%算, selective(GPT-3 -70%激活+2.7%算) ; gbs=mbs×grad_acc。"},
   {"key":"提醒","body":"nanotron 官方手册+其4000+试验;公式引 NVIDIA recomputation paper;跨栈请实测。"}],
 "lead":[
  "想在集群上把大模型训起来, 第一步不是抢几百张卡, 而是先算清一张卡装得下多少。这本由 nanotron 发的 Ultra-Scale Playbook 用『从头能背』的方式讲显存——参数/梯度/优化器态每字节可估, 激活一条近似公式, 再用激活重算+梯度累积两件工具把『单卡不够』抬过去。系列第1/6, 到 data parallelism 门口。",
  "书中大量结论伴随可交互曲线/音频等媒体, 公众号无法承载者均以文字转述其要表达的结论, 不做静态造假。"],
 "sections":S,
 "conclusion":[
  "显存最常见误解是只算权重。真正的账要加梯度与 optimizer 状态——Adam 下后者 8N, 比权重还贵, 于是 7B 混合精度已 112GB 越过单卡 80GB; batch/序列一长, 激活又以 seq² 反超。小模型单卡够用只是短窗口: 要么 activation recomputation 用算力换显存(selective 在 GPT-3 减70%激活/2.7%算力), 要么 gradient accumulation 拆小 batch(显存恒定、代价是更多 fwd/bwd 的算力)。",
  "把四样账与两条路摆清, 单卡问题拆到底; 下一步把互相独立的 micro-batch 平铺到多卡, 正是 data parallelism——本质只是 gradient accumulation 的并行版。"]
}
json.dump(data, open(os.path.join(D,"article_data.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=2)
print("ok")
