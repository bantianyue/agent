# -*- coding: utf-8 -*-
# Attention Mechanisms in LLMs (akshay X Article) faithful zh build
import os,json
D=os.path.dirname(os.path.abspath(__file__))
S=[]
def h2(t): o={"type":"h2","title":t,"paras":[]};S.append(o);return o
def t(o,*ps): o["paras"]+=list(ps)

s=h2("为什么 attention 存在、又贵在哪")
t(s,"早期序列模型(RNN)把固定大小的 hidden state 从 token 传到 token,隔得越远联系越弱、长程依赖会衰减。Attention 直接解决它:不用经过瓶颈式的汇总,每个 token 都能看全其他 token、自己判相关度。这种直给是 transformer 强的原因,也是它贵的原因——成本在存『每个 token 都见过什么』所需的显存。")
s=h2("驱动一切的约束在 KV Cache")
t(s,"每次 attention 都要记住之前每个 token 的样子。prefill 一次性处理整段 prompt,每层为每个 token 算一个 key 向量和 value 向量,存进所谓 KV cache,让 decode 时能直接查而不重算。缓存随生成增长:70B @BF16 模型、单个 128K 上下文, KV cache 约 40GB,接近 4bit 量化后的模型权重本身。真正的约束不是算力也不是公式里的数学,而是『存 attention 已看过的东西』那点显存。")
s=h2("self-attention / causal / cross")
t(s,"Self-attention:每个 token 与同一序列内其他 token 互相注意;模型给每 token 算 query/key/value,用 q?k 的点积判断相关度,是每个 transformer 层的基础算子。Causal attention=self-attention 加三角掩码:token 只能看更早的、不能看未来的——这让 decoder-only 能逐 token 生成而不提前见到答案。Cross-attention 是另一种:query 来自一个序列,key/value 来自第二个序列;encoder-decoder(T5/Whisper)用它把 encoder 输出喂给 decoder;而 Llama/GPT 这类 decoder-only 根本没有 cross-attention。")
s=h2("Multi-Head Attention(MHA)")
t(s,"MHA 是 2017 Transformer 首创。每个 head 一套独立的 q/k/v 权重;32 个 head 每层就是 32 套 KV 投影。好处是表达力:不同 head 各学一类关系(句法结构、语义接近、长程指代)。代价是内存:每个 head 各自维护 KV cache;32 层×每层 32 head=每请求每 token 1,024 个独立 KV 张量。GPT-3 每层 96 head,128K 上下文下光 KV 就把一张 GPU 填满,batch 还没怎么涨就爆。MHA 之后每一个设计都是冲这点显存去的。")
s=h2("Multi-Query Attention(MQA)")
t(s,"MQA 走最直接的路:所有 query head 仍各持权重,但共享同一个 key head 与 value head。KV cache 缩小一个『head 数』因子:32 个独立 KV 投影变 1 个。decode 更快,因为每步从 HBM 读的字节少很多——decode 是显存带宽瓶颈,少读即快。代价是质量:让所有 query 共用一个 key/value 会损失 MHA 的一些表达力。Falcon、PaLM、早期 Gemini 用过 MQA 接受这笔交换换吞吐。MQA 牺牲的质量,下一个设计大多找回。")
s=h2("Grouped-Query Attention(GQA)")
t(s,"GQA 介于 MHA 与 MQA 之间:query head 分组,每组共享一个 key、一个 value,组与组独立。32 个 query、8 个 KV 组 → 存 8 套 KV 投影而非 32 套,比 MHA 减 4× KV cache,又找回 MQA 出卖的大部分质量。这个平衡让它成了近几年几乎全部主流开源模型的默认:Llama 2 70B 用 8 个 KV 组,Llama 3、Mistral、Mixtral、Gemma、Qwen 全是 GQA。GQA 论文在 KwV memory 的部分质量代价下追平 MHA,并经各模型家族应验。GQA 减少了『存的 head 数』;下一个把 head 本身也给压缩。")
s=h2("Multi-Head Latent Attention(MLA)")
t(s,"MLA 是 DeepSeek 2024 年 5 月 DeepSeek-V2 的原创。MQA/GQA 在减 KV head 数量,MLA 则把完整维度的 key/value 向量压缩进一个低秩 latent 空间再缓存;attention 时再解压回全维。缓存对象是 latent 而非完整 KV 张量,因此 footprint 比 GQA 更小、又保留更多 MQA 牺牲掉的表达力。代价是算力:每次 attention 都解压、多出 FLOP;但推理时显存带宽几乎总是比算力更稀缺,所以更小的 cache 在多数 serving 场景胜过额外数学。DeepSeek-V2/V3/R1 都用 MLA;V2 基准里 MLA 追平甚至超过 MHA,却把 KV 卡到同规模下 MHA 所需的大约 5-13%。")
s=h2("FlashAttention")
t(s,"FlashAttention 不改变计算什么,改变计算怎样访存。标准 attention 把整张 N×N 注意力矩阵建出、写 HBM、读回算 softmax、再写、再读去做加权和——4K token 序列就是 4096² 个值;反复进出 HBM 正是长上下文 attention 慢的原因。FlashAttention 分块处理:把矩阵切成能塞进片上 SRAM 的块、softmax 增量算、整矩阵不物化、输出只写 HBM 一次。数学完全一样,内存流量不一样。如今各大 serving 引擎默认都用它;它不是新的注意力『类型』,而是执行任何类型 attention 的标准 kernel。MHA/GQA/MLA 回答存什么、怎么压;它回答怎么高效地算。下面的稀疏 attention 则是换个角度:不是缓存哪些 token,而是到底要 attend 多少 token。")
s=h2("Sparse attention / SWA / NSA")
t(s,"全 attention 对序列长是 O(N²)。1M token 上下文,注意力矩阵有万亿条目,即使 FlashAttention 省了内存流量,遍历那么多个 token 仍不可行。稀疏 attention 跳过大部分矩阵:只算选中的子集。Sliding Window(SWA)最简:每个 token 只 attend 最近 W 个,Mistral 某些层用 SWA、与全 attention 层交替,兼顾局域精度与一些全局。NSA(Native Sparse Attention)是 DeepSeek 2025 的另一贡献(不是 MLA):在训练时就稀疏,而非推断后置放。每层三路并行:压缩粗粒度注意(c 全局上下文)+ 选择性细粒度(重要 token 块)+ sliding window(局域),预训练中学出哪些 token 要紧。NSA 在多数基准追上全 attention,长序列上明显更快。Qwen2.5-1M 用稀疏 attention 支撑百万上下文——那个长度下全 attention 占掉前向 90% 以上。把稀疏训进模型,正被证明是对长上下文扩展最 principled 的答案。")
s=h2("Serving 层: PagedAttention 与 RadixAttention")
t(s,"以上都在模型权重之内;PagedAttention 与 RadixAttention 活在 serving 引擎,是同一压力在另一层的回答。请求到来时引擎要给它分配 KV 的 GPU 内存;朴素做法是给『最大可能 seq 长度』预留连续内存——允许最多 4096 的请求,就提前占 4096 槽,不管它是用了 40 还是 4000。这浪费约 60-80% GPU 内存,请求间碎片雪上加霜。PagedAttention(vLLM 用)把 KV cache 管得像 OS 管虚拟内存:按需分配定长块、块表把每请求的逻辑块映射到任意空闲物理块——无预分配、无碎片,浪费降到 4% 以下。RadixAttention(SGLang 用)更进一步:多个请求共享公共前缀(如发给所有用户的 long system prompt)时,前缀的 KV 块只需算一次;它把 KV 块按 token 序列存进一棵 radix tree,新请求沿树走、找最长匹配前缀、复用那些块、只算真正新的后缀。多轮负载下 RadixAttention 打到 75-95% 命中率;一份 system prompt 服务数千用户只算一次、按 LRU 策略到被逐出。二者都不改模型用的 attention 机制:Llama 3 GQA 在 vLLM 或 SGLang 下都正常;两层相互独立。")
s=h2("收束：那条贯穿全篇的线")
t(s,"把这条线拉直:一切都在对抗 KV cache 显存这个瓶颈,各种设计是不同的动作。MQA/GQA/MLA 减少每 token 存多少——各拿不同量的质量换显存;FlashAttention 降的是计算访存的代价、完全不碰数学;稀疏 attention 降『attend 多少 token』,是唯一能扩到百万上下文的答案;Paged/Radix 在 serving 层切分配与复用、而不动模型本身。真正决定哪招对你有效的是——在你部署里哪个才是紧约束。")
d={"title":"一张卡怎么装下 attention 想记住的一切：KV 缓存压力下的 9 种解法",
 "reference_url":"https://x.com/akshay_pachaar/status/2096215921568498042",
 "summary":[
  {"key":"一条主线","body":"模型卡上都会标 MQA/GQA/MLA，它们全因同一个约束而生：把 attention 看过的长序列状态存下来会撑爆 GPU 显存(KV cache)。这篇按出场顺序逐个拆它们各自修了什么缺陷——Self/Cross→MHA→MQA→GQA→MLA→FlashAttention→Sparse(SWA/NSA)→Paged/Radix。MHA 之后的每个设计都是在跟 KV cache 内存较劲。"},
  {"key":"四类招式","body":"存多少：MQA 共享单 K/V、GQA 按组共享(32→8 组, 约 4× 省)、MLA 压缩进低秩 latent(DeepSeek-V2 把 KV 压到 MHA 的 5-13% 还追平质量)。算多贵：FlashAttention 分块不物化整矩阵、只写 HBM 一次。attend 几个：SWA 滑窗 + NSA(训练内稀疏)，唯一扩到 1M 上下文的答案。分配复用：PagedAttention(vLLM, 块表按需分配, 碎片<4%) 与 RadixAttention(SGLang, radix-tree 按公共前缀复用 KVPrefix, 多轮命中 75-95%)。"},
  {"key":"性质与其他","body":"@akshay_pachaar 的 X 长文(社区科普, 非论文);约 12KB 文字、原生无正文插图实体。文中 40GB/128K、GQA 8 组、MLA~5-13%、Paged<4% 等数字为作者引述口径, 供直觉参考。"}],
 "lead":[
  "每张模型卡都拿『注意力机制』当卖点:MQA、GQA、MLA 和参数量、benchmark 一起被印在右上角。它们背后是同一个憋屈的现实——给长序列和大 batch 存 attention 状态, 会把 GPU 显存撑爆。",
  "这篇把注意力从 Self 一路拆到 RadixAttention, 按『谁先来、它修了什么缺陷』的顺序讲清九种设计。它是作者发布在 X 上的长文(约 1.2 万字符, 社区科普向), 源本身无正文插图实体, 故本稿为纯文字完整编译。"],
 "sections":S,
 "conclusion":[
  "最值得记住的是那句归纳:KV cache 是整条演化的压力源。MQA/GQA/MLA 在『每 token 存多少』上取舍质量换显存;FlashAttention 换的是计算怎么访存;稀疏(SWA/NSA)换的是到底 attend 多少——这是唯一能把上下文推到百万 token 的答案;而 Paged/Radix 换的是 serving 层怎么分配与复用,与模型机制正交,你的 Llama-3-GQA 换哪个引擎都照跑。判断哪一种在你这真正见效,就看自己的部署里哪个是紧约束。",
  "把它当一份清爽的地图用:面试或选型时,提到 attention 先分清它属于哪一层(模型权重的 KV 压缩 vs 计算的执行 vs 序长扩展 vs serving 分配),再谈指标,就不容易各说各话。文中数字为作者科普口径,真实部署要按你的模型/后端回读。"]
 }
json.dump(d,open(os.path.join(D,'article_data.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=2)
print("sections",len(S),"chars",sum(len(x) for s in S for x in s["paras"]))
