# -*- coding: utf-8 -*-
# part2: metrics table/公式 → how-in-practice → section1 four generations (EAGLE3/DFlash/DSpark/DFlash2/race)
SECS=[
 # ---- 6 指标表 (Table1) 连同公式 ----
 {"type":"table","head":["Metric","Definition","Determined by"],
  "rows":[["Decoding speedup (η)","η = L_target / L  相对自回归基线","单 token 时延 L 与基线 L_target"],
          ["Per-token latency (L)","L = (T_draft + T_verify) / τ  每个出新 token 的平均时间","T_draft、T_verify、接受长度 τ"],
          ["T_draft","draft 模型用于『出草稿』的时间","其规模 + 需要的草稿数:模型越小越快到"],
          ["T_verify","目标模型验证所花时间","目标规模 + 一次验多少草稿"],
          ["Tokens per second","≈ 1 / L  用户体感吞吐","单 token 时延 L"],
          ["Acceptance length (τ)","平均每次验证能通过的草稿 token 数","draft 模仿目标有多像:猜得越近越存得多"]]},
 {"type":"h3","title":"读接受率：τ 即距离","paras":[
   "2023 论文(Leviathan, Thm 3.5)给出一条连接:接受率等于 1 减去 draft 与 target 分布之间的总变差距离——α = 1 − E[D_LK(p,q)];同一推导再给出 Table1 里 τ 与 α 的关系:τ = (1 − α^(γ+1))/(1 − α),γ 是每轮验证草稿数。",
   "2023 之后的一切都继承这条定理:后来的论文基本不再亲自证无损——只要验证守住『accept-or-resample』,draft 再弱输出也无损。Thm 3.5 真正多给的是**怎么读速度数字**:拿到一个 τ,就能反推 α;而 α = 1 − 某种分布距离——所以『读 τ』== 在读 draft 分布离 target 有多近。严格验证下,这个距离只决定速度;一旦放宽接受阈值,距离就会开始伤输出质量(第二节细说)。",
 ]},
 {"type":"h3","title":"实战数字：聊一个 2.3x","paras":[
   "单卡 B200 跑 Qwen3-8B+SGLang,朴素解码约 230 tok/s;哈利波特第一卷约 10 万 token,要 7 分多钟。挂 DFlash draft 后对话文本约 2.75× 快(Chen et al., 2026),约 630 tok/s,压进 3 分钟。纸上数字走一遍:",
 ]},
 {"type":"code","title":"math","texts":["__CODE__text::T_verify = 4.3 ms   # 目标一次前向 (Qwen3-8B @230 tok/s ≈ 4.3ms/token)\nT_draft  = 1.3 ms   # drafting 成本\nτ        = 3 tokens # 每次验证被接受数\nL = (1.3 + 4.3)/3 ≈ 1.9 ms/token    # 每 token 时延\nη = 4.3 / 1.9 ≈ 2.3x                # 相对朴素解码加速"]},
 {"type":"h2","title":"1. 投机解码怎么一路演化","paras":[
   "回到三可变:**drafting time / verification time / acceptance length。**. Four generations 每代正好拆掉一个瓶颈:EAGLE-3 拉长接受长度,DFlash 砍 drafting time,DSpark 砍 verification time,DFlash 2 再把接受推高一档。按顺序逐个看。",
 ]},
 {"type":"h3","title":"1.1 EAGLE-3 (NeurIPS 2025)——更长的接受长度","paras":[
   "2023 年代用一个独立小 LLM 当 draft,它从零瞎猜,还要多养一个大模型=多占显存。Medusa(Cai+24)换成在目标上多挂预测头;EAGLE(Li+24)进一步把『多个头』缩成**一个 decoder 层**,读目标的隐藏特征然后自回归草拟(Figure 3)。之所以重点讲 EAGLE-3,因为它是产线上真在跑的那个。",
   "更早的 EAGLE 用更多训练数据却拉不长接受长度,根因在训练目标:旧 draft 层既被训来预测『目标下一个 token』又预测『目标下一层隐藏特征』,等于逼模型去复刻目标特征向量——能力全花在抄特征而不是把 token 猜得更准。",
   "EAGLE-3(Li et al.2025)把目标改成『less is more』:**放弃特征预测、直接预测 token**,但把特征从目标的 low/middle/high 三层融合(而非只用顶层)。代价是引出一个新问题——推理时 draft 吃自己输出,分布会从训练分布漂走,第二步起接受就开始崩。EAGLE-3 用 **training-time test**(训练时就让 draft 展开多步、吃自己的输出)治愈:让训练分布 == 推理分布。",
   "结果是更长的接受:EAGLE-3 最高比朴素解码快 6.5×、比 EAGLE-2 快约 1.4×;**投遍 SGLang/vLLM** 生产框架——它是最被广泛采用的 draft 之一。瓶颈还剩一个:小 draft 快,但**依旧一次出一个**。能并行草拟吗?",
 ]},
 {"type":"h3","title":"1.2 DFlash (ICML 2026)——砍 drafting time","paras":[
   "DFlash(Chen et al.2026)的核心决策就是**让草拟并行**:整块一次生成,而非逐个 token。它借的是 diffusion 的『diffusion block drafting』:图像/视频生成里,diffusion 从纯噪音出发、对所有像素**并行去噪**,一次精修整张画布。文本 diffusion 把这思路带过来(Arriola+25):把噪音换成 **MASK token**,让模型并行预测每个遮罩位。DFlash 照搬到草拟:draft 块以一整行 MASK 起步。Figure 4(动画/示意):EAGLE-3 一个接一个串行草拟,DFlash 一次去噪一整块 MASK,并且把目标模型的上下文特征『每块注入一次』。",
   "diffusion 式草拟带来两个好处:",
 ]},
 {"type":"code","texts":["__CODE__text::① 一次前向出整块 → drafting 快、成本随块长几乎持平(flat)\n   AR draft: 出 γ token 要 γ 次前向;DFlash: 一次前向并不断,块增大成本不大变。\n   flat 成本还换来容量: EAGLE-3 为省时只留 1 层, DFlash 可以用 5 层还更快。\n   5 层出 16 token  在 drafting cost 与 acceptance 上双胜 EAGLE-3 单层出 8。\n② 吃目标上下文特征 → draft 更准\n   只喂『最后 token 的 fused 特征』有两个坑:它只带单位置、且只在栈底加一次会越深越淡。\n   DFlash 把每个已验前缀位置的目标特征做成 K/V,注入 draft 每层 KV cache\n   (Figure 6) → 填块时每层都见完整前缀 → 接受率更高。"]},
 {"type":"h3","title":"1.3 DeepSeek DSpark (2026)——砍 verification time","paras":[
   "前面几家都在打磨 draft 机制;DSpark(DeepSeek)反过来**优化验证机制**:只验证值得验的草稿。它在并行 draft 主干上加两个模块(Figure 7):一个轻量**sequential head** 恢复块内依赖(后位置可依赖前面);一个 **confidence head** 估每个 draft 前缀多大概率存活,配一个 **load-aware scheduler** 按存活率与引擎吞吐画像为每个请求定验证长度。",
   "于是 DSpark 砍的是验证时间。离线它比 SOTA drafter 在接受长度上提 16–31%;部署进 DeepSeek-V4 生产栈,在匹配吞吐下把单人生成提速 60–85%(对比 MTP-1 基线)。DeepSeek 同时开源了 DSpark 权重与 DeepSpec(一个训练 repo)。",
   "但 DSpark 的 sequential head 又是一个 token 一个 token 走——为了并行草拟而放弃的,现在又还了回去?值得问:换取舍值不值。",
 ]},
 {"type":"h3","title":"1.4 DFlash 2 (2026)——更长的接受长度","paras":[
   "DSpark 用顺序头解接受衰减;DFlash 2(Inco)主张**草拟就该保持并行**,用**并行 selector**换掉顺序头。理由是成本差距:顺序头在每个位置重算一遍整词表分布,**77.8M 参数 / 9.6% 时延**,而 selector 只要 **2.0M / 0.6%**。",
   "使并行选择可行的是另一个观察——**对的 token 往往早就在候选里了**。给一个已验证前缀『The fastest way to』加 4 个遮罩位:每位各自 top 候选拼起来却得到『get to to school』(两个相邻都挑了同一个词,句子断掉);而通顺的『get to school quickly』其实一直在候选列表里躺着。Inco 量化这值多少:若一个完美 judge 总能从 top16 里挑对,接受长度会从 4.27 跳到 6.79。所以‘少见其实是错 judge’:**缺的不是对的 token,是判断**——而选择判断天然可并行。Figure 8(动态)展示它的两件新增:",
 ]},
 {"type":"code","texts":["__CODE__text::◆ path selector：挑一条通顺的路径。给相邻候选对打分 = drafter 自己的 logit\n     + 一个兼容项(把前 token 与候选压成 256 维向量, 在 context gate 下比对)。\n     从『最后一个已验 token』出发走最高分路径 → 替换独立的逐位猜测。 2M 参数 / 0.6% 时延。\n◆ two-tap convolutions：让邻居一致。在每个 attention 与 FFN 子层前后插入, 把每位置\n     与它的前一个混起来, 首位读『最后已验 token』。attention 看长程, conv 管块内局部\n     一致: 只回看一格就换回『多十层』收益的一大半 —— 块尾衰减是局部问题, 局部修就够了。"]},
 {"type":"h3","title":"结论：DFlash 2 战绩","paras":[
   "DFlash 2 把接受长度从 4.92 抬到 5.97(每轮验证, Qwen3.5-4B),即比 DFlash 多 21% 产出、只加 1.3% 时延;在 Qwen3.8-27B 上相对自回归给 2.7–3.4× 吞吐(Inco)。",
   "走过四代架构,作者问读者:**下个 SOTA 会是你想的那个方向吗?**",
 ]},
]
