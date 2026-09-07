# -*- coding: utf-8 -*-
# PagedAttention Isn't Gone, It Got Demoted —— 中文通俗编译
import os,json
D=os.path.dirname(os.path.abspath(__file__))
S=[]
def h2(t): S.append({"type":"h2","title":t,"paras":[]}); return S[-1]

summary=[
 {"key":"一句话","body":"『vLLM 为什么快？』标配答案多半是 PagedAttention。本文用一个更准的视角拆开它：打开 vLLM 仓库，PagedAttention 早已不是唯一的答案，而是 attention/backends/ 下一长串 kernel(FlashInfer、FlexAttention、MLA、GDN、Triton…)里的一员。它没有消失——它被『降级』成一个 memory 后端。作者把它从内存到 compute 的完整演进讲成一篇漂亮的科普短文。"},
 {"key":"核心论点","body":"彻底分开两件常被混为一谈的事：KV cache 放哪(KV cache manager 管内存)+ 在上面怎么算 attention(attention backend 管 compute)。PagedAttention 只解决了前者(非连续、前缀可共享的 block 内存)，从没规定后者怎么算；卡在 kernel 层的新瓶颈(不同 GPU 代、不同 attention 形状)才逼出这条拆分之路。"},
 {"key":"本文料","body":"纯文字 X Article，约 3800 词无代码/无表格配图。保留全部后端名/命令位/机制。适合给『想用一个清晰模型看 vLLM 内部如何演化』的人。"},
]
lead=[
 "面试官问『vLLM 为什么快』，十有八九你会脱口而出 PagedAttention——它随论文走红，进过 keynote，至今还被人当系统设计面试的标准答案。这篇用词锋利的长文想纠正的正是这点：这个答案从来没完整过，而且已经不是一天两天了。",
 "此刻打开 vLLM 仓库，PagedAttention 只是 attention 后端注册表里的一条，旁边并排站着 FlashInfer、FlexAttention 等半打 kernel。它没消失——它被降了级(from『整个 story』变成几个 memory 后端之一)。原文把这段『从地基往上』的演化脉络盘得清清楚楚，本文按其全文逐节编译(约 3800 词、纯文字、无配图可保)。",
]
h2("为什么先有个缓存")
S[-1]["paras"]=[
 "Transformer 逐个 token 生成。要产出第 N 个 token，必须回看 1..N−1 的全部 token——naive 做法是每步、每层把先前每个 token 的 K、V 投影重算一遍，极浪费。好在这两头 K/V 矢量一旦处理完就不变了，serve 引擎于是把它们缓存起来。",
 "KV cache 里放的是每个 token 的 key 与 value 向量，逐层逐注意力头存放。每步只算最新 token 的 K/V，其余直接复用。",
 "这是一笔真实成本，不是可以四舍五入的误差：中型模型一条序列的 KV cache 就能到 GB 级。乘起来就是——层数 × 头数 × head dim × 序列长 × (K和V两份) × batch 大小。",
 "解码同时还是带宽受限的：每吐一个 token，都要把那整份 KV cache 从 GPU 里重新读一遍。内存摆成什么样、读取效率如何，直接决定吞吐。这就是 PagedAttention 出场要修的地形。",
]
h2("PagedAttention 实际修了什么")
S[-1]["paras"]=[
 "问题又窄又具体：KV cache 的内部碎片化。PagedAttention 之前，引擎给每条序列的 KV cache 分配一整段连续内存——按该请求可能到达的最大序列长度预留。可生成多长你提前不知道，而连续内存必须一次定死。",
 "绝大多数请求根本到不了那个上限，差出来的那块就白白预留、用不上。这正是操作系统几十年前为了解决进程内存碎片而解决过的那道内部碎片问题。",
 "vLLM 直接把那个解法借了过来：把 KV cache 切成可放物理内存任意位置的定长 block、用一个 block table(页表式的间接寻址)把逻辑位置映射到物理位置、让共享公共前缀的请求共用 block、并且不再按『极少发生的 worst case』预留内存。",
 "这四点让 vLLM 把 batch 推上去、真正在吞吐上变得有竞争力。但它是一个纯内存管理层面的修复——它一个字都没说『数据就位之后 attention 本身该怎么算』，只改了字节住在哪、怎么寻址。",
]
h2("随之而来的分岔")
S[-1]["paras"]=[
 "核心区别在此：cache 放在哪 vs. 在上面怎么做 compute。这正是 vLLM 架构自此长出来的一道接缝。",
 "现行设计(v1，不是已废弃的 v0 路径)把两件事当成分离的关注点、各有独立接口。KV cache manager 管内存——分配 block、跟踪引用计数、处理前缀缓存命中、决定驱逐谁；它调 get_computed_blocks()、allocate_slots() 这类函数，根本不在乎最终哪个 kernel 去读这些 block。",
 "attention backend 管 compute——拿一个 query 向量 + 它要的 K/V block，算 softmax(QKᵀ/√d)V，在多快算多快的前提下吐一个 output tensor。它用各种 tile/fusion 技巧讨好 GPU 内存层级，唯一在乎的是有人给它合法可读的指针。",
 "一个模型体内甚至可以混用多个 backend：vLLM 支持按 KV-cache-group 覆盖 backend，既有 full attention 又有 sliding-window attention 层的模型，可以把每组路由到不同 kernel。",
]
h2("后端现场，具体地看")
S[-1]["paras"]=[
 "这不是为讲故事硬造句——它就是代码现在的样子。打开 vllm/v1/attention/backends/ 能看到(以下不穷尽)：",
 "flash_attn：FlashAttention，tiled-softmax kernel，把中间值放在快的片上 SRAM 而非去 HBM 来回倒。flashinfer：FlashInfer，覆盖 block-sparse paged attention 等多算子的更宽库。flex_attention：FlexAttention，把自定义 attention mask 编起来而不是写死各种 pattern。mla：multi-head latent attention，DeepSeek 架构带火的压缩 KV 方案。gdn_attn：GatedDeltaNet 式线性 attention。triton_attn(及 ROCm 侧 rocm_attn / rocm_aiter_unified_attn)：按 vLLM 官方文档，PagedAttention 配 Triton prefix prefill 的组合。",
 "PagedAttention 并没有从这个清单消失——它活在 triton_attn 里。现在只是『一个 backend 』，不再是『那个 backend』。",
 "MLA 还有一层自己的拆分：prefill 与 decode 行为完全不同——prefill 处理整段 prompt、是 compute-bound；decode 逐 token 生成、是 memory-bound。于是各阶段各选各的 backend：prefill 后端可从 FlashAttention、FlashInfer、TRT-LLM Ragged 里独立挑；decode 后端有 FlashMLA、Triton MLA、CUTLASS MLA 等等；DeepSeek 更新的稀疏 MLA 变体又各有专属 decode 后端。这些通过 --attention-backend 参数 / VLLM_ATTENTION_BACKEND 环境变量 / 或显式 per-group override 配置——不是事后从 benchmark 里反推的。",
]
h2("为什么这次分岔非发生不可")
S[-1]["paras"]=[
 "一旦 KV cache 碎片不再是瓶颈，瓶颈就移进 kernel 内部了。而没有任何单一 kernel 处处最优——两股力量逼着拆分。",
 "一是硬件分化：Hopper 与 Blackwell 是不同代的 tensor core，低精度格式的原生支持也不同；在 A 上最快的 FlashAttention 版本在 B 上不一定最快。vLLM 文档按 SM 代给不同默认 FlashAttention 版本正是为此，而这还没算 FlashInfer 那边单独由 TensorRT-LLM 支撑的 kernel。",
 "二是 attention 本身的形态分化：标准 MHA 每 token 每头留一份完整 K/V(这正是 PagedAttention 要高效分页的对象);MLA 把每 token 的 K/V 压进一个很小的共享 latent 向量、用时再现场扩回——cache 显著缩小，但 kernel 必须围着压缩转，而不是朴素 per-head block;GDN 则干脆扔了越来越大的 cache，改成每 token 更新的定长循环态，更接近 RNN 而非通常二次查找式的 attention。三种**真正的内存访问方式**，没有一种贴合最初的 PagedAttention kernel。",
 "一个为某代 GPU、某一种 attention 形态硬调优的单体 PagedAttention kernel，永远追不上这摊子演化。把 cache 管理与 kernel 选择拆开，是让两边各自按各自节奏演化的唯一办法。",
]
h2("实际收益")
S[-1]["paras"]=[
 "『你开 PagedAttention 了吗』变成了一句没有意义的问题——基于 block 的 KV cache 管理就是 vLLM 现在的工作方式，那个意义上是默认开着的。真正能推动你吞吐数字的问题是：你给『你这个模型 + 你这块硬件』挑了哪套组合——即 KV cache 布局、cache manager 行为(前缀缓存、hybrid sliding-window 处理)、attention kernel。它们现在已经是独立决策：各有各的默认、各自 override 的开关、以及一旦配错各自的坏法。",
 "这是个比老问题更复杂、也更诚实的问题。H100 上跑 dense attention 的吞吐，和 Blackwell 上跑 MLA 的吞吐，本来就是两个工程问题——假装一个 kernel 名字能同时解释两者，从来都是过度简化。",
]
h2("PagedAttention 真正的遗产")
S[-1]["paras"]=[
 "这整篇不是说 PagedAttention 错了、或在任何值得抱怨的意义上过时了。注册表里每个 backend 仍都踩着它引进的内存管理模型受益：block 化、非连续、可共享前缀的 KV cache，是其余一切立身的基底。",
 "变的是 scope。PagedAttention 曾经在很多人对 vLLM 的心智模型里代表整整一个推理引擎；现在它是『在那些内存之上计算 attention 的若干种方式』中的一种内存策略。attention 计算本身成了快速移动层，其迭代速度快过了底下那套存储模型不得不更新的速度。",
 "这不是意义上的失败式降级，而是『组织架构长胖了』式的降级：它解决的问题，原来只是整个公司里的一个部门，而不是整个公司。",
]
CONCL=[
 "什么是把一个技术名词祛魅、而不贬低它的正确姿势，这篇给了个范例。它没有说 PagedAttention 没用，而是精确指出它的领地边界——它解决了『字节在哪、怎么寻址』，然后坦白那里从来不是全部。当单一 kernel 无法跟上硬件(每代 tensor core/精度支持)与 attention 形态(MHA 分页 / MLA 压缩 KV / GDN 去 cache)的分化时，把 cache 管理与 compute 拆成两个可独立演进的后端，是唯一能让一层别拖垮另一层的做法。",
 "留三句话提醒自己：① 面试里的旧口头禅(PagedAttention=vLLM 快)是个会过时的简化——修内存不等于定死怎么算 attention；② 真能推动吞吐的三旋钮(布局、cache manager 行为、kernel)现在是三个独立决策，各带默认与坏法；③ 架构演化的健康信号不是旧件被删，而是它从「整家公司」缩成「一个部门」——注册表里别的 kernel 照样踩在它的 block 内存基底上。",
 "此为作者 Nikhil Mourya 个人长文，观点与 vLLM 官方文档对应但不代表项目官方口径；原文见 X(author/status/2096506355217809626)。",
]
data={"title":"PagedAttention 没死，只是被降了级——vLLM 内部那场从『内存』到『后端注册表』的演化",
      "reference_url":"https://x.com/GonnabeNikhil/status/2096506355217809626",
      "summary":summary,"lead":lead,"sections":S,"conclusion":CONCL}
open(os.path.join(D,"article_data.json"),"w",encoding="utf-8").write(json.dumps(data,ensure_ascii=False,indent=2))
print("sections",len(S),"body",sum(len(x) for s in S for x in s['paras']))
