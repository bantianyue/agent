<div style="background:#e8f4fd;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:18px;">
<div style="text-align:center;margin-bottom:10px;">
<strong style="font-size:16px;color:#1a6ba0;">要点速览</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
- <strong>首个高性能开源 MSA 训练 kernel</strong>：作者用 CuTeDSL 为 Hopper/Blackwell GPU 写出 MiniMax Sparse Attention 的训练 kernel，这是业界第一个能高效训练稀疏注意力的开源实现，此前只有推理侧代码。<br><br>
- <strong>相对 Flash-Attention 的长上下文优势</strong>：在百万 token 量级，Flash-MSA 单步训练显著快于 FA4；整个训练步里只有代理前向着上下文长度是二次方，其余全部走稀疏块缓存。<br><br>
- <strong>三项关键改动</strong>：块状稀疏（按 128 选块而非单 token）、主注意力用 GQA 替代 MLA、代理头分组专门化，使西方主流的 GQA 架构也能用上 MSA。<br><br>
- <strong>用一行梯度技巧避开 KL 实体化</strong>：KL 损失对代理分数的梯度等于「代理概率减主概率」，kernel 内原子化反向传播，无需在共享内存里完整展开 KL 分布。<br><br>
- <strong>仍受寄存器/共享内存瓶颈</strong>：反向理论占用率仅 12.5%（FA 为 18.75%），上下文并行 Ring 方案与低精度索引器是后续优化方向。
</div>
</div>

---

## 引言：把稀疏注意力的训练也开源了

多家前沿模型都在用稀疏注意力大幅加速推理，但**至今没有任何人发布过能高效训练它的代码**。作者今天发布了世界上第一个高性能的开源训练 kernel：用 CuTeDSL 为 Hopper 和 Blackwell GPU 实现的 MiniMax Sparse Attention（MSA）训练 kernel。所有开发工作在 Spheron 的 H100 和 B200 租用机上完成，并参考了 FA4、MSA 推理实现和 Codex。

作者明确声明：这**不是 MiniMax 的官方实现，也与 MiniMax 无任何关联**。

![](fig01.png)
<span style="font-size:12px;color:rgb(153,153,153);">Flash-MSA 与 Flash-Attention 在单个训练步上的对比（长上下文下 Flash-MSA 反超）</span>

## 关于 MSA：与 DeepSeek 稀疏注意力的三点不同

MSA 与 DeepSeek Sparse Attention（DSA）类似，但有几处核心改动。

![Fig.1 来自 MSA 论文](cover.png)
<span style="font-size:12px;color:rgb(153,153,153);">Fig. 1 from the MSA Paper</span>

**1. 块状稀疏（Blockwise sparsity）**

代理注意力不再为每个主注意力挑选单独的 KV，而是以 128 为块、通过对代理分数做最大池化来挑选块。这为 kernel 带来很好的缓存特性。

**2. 主注意力用 GQA 而非 MLA**

这一点尤其重要：据作者所知，没有一家西方实验室在训练中采用过 MLA，这使得 GLM-5.2、DSv4 这类基于 MLA 的前沿模型所适配的稀疏注意力形式，在这里的模型上无法直接复用。换成 GQA 后，西方主流架构也能跑 MSA。

**3. 代理头的分组专门化**

用 GQA 替换 MLA 后，每一层内部出现了相互独立的查询组，让每个代理头可以挑选不同的 KV 子集，而不是像 DSA 那样把整个注意力层求和后再统一打分。有证据表明注意力头会天然关注不同的 token，因此这一改动应该能提升主注意力的表达能力。

## Kernel 设计：尽量少重复计算

要高效跑 MSA，核心矛盾是**尽量少重复计算，同时不撑爆寄存器/共享内存**。除了常规 flash 寄存器（Q 分块、KV 分块、O 累加器、LSE 累加器），前向还要处理流式的 top-k 累加器；反向则要为「双注意力合并计算」留空间，才能同时算主注意力和代理注意力的梯度——因为代理梯度需要同时访问两者概率。

块状稀疏的一个关键好处：只缓存块索引而非单独 token，因此可以把块索引一直存到反向阶段。**整个训练步里，只有代理前向着上下文长度是二次方的，其余部分都复用代理前向前缓存的稀疏块。**

![kernel 序列的高层概览](fig02.png)
<span style="font-size:12px;color:rgb(153,153,153);">High level overview of kernel sequence</span>

### 前向：代理注意力 → 稀疏主注意力

操作顺序固定为：代理注意力 → 稀疏主注意力 → 把主注意力输出送往下一层，并保存主注意力的 LSE 供反向使用。

**代理注意力**的点积与常规 Flash Attn 略有不同：不再累加输出，但必须在流式扫描 key 时持续记录 top-k 分数及其索引。作者也没有为反向累加 LSE，而是在反向时通过一次廉价的「稀疏激活上重算代理点积」拿到 LSE——实践里比前向融合 LSE+top-k 更快。每算一块 QK^T，就抓取该 chunk 的因果局部最大分数，做插入排序写入寄存器里的 top-k 值；为腾空间把 key 块切成两半。MSA 要求每个 token 的局部块保持滑动窗口不被掩码，因此局部 KV 块的分数被设为 inf。

**主注意力**就是块稀疏的 flash attention 前向，作者直接借用 MoBA 的技巧，把块稀疏注意力重新参数化为变长（varlen）flash。

### 反向：融合代理与主注意力

计算代理头梯度必须融合两者反向，因为代理训练信号需要同时访问代理和主注意力概率。由于前向已保存块索引、且只在这些稀疏 KV 激活上训练，反向可以线性时间运行：先取出缓存的块索引，把「[batch, proxy head, query, top_k_slot] → [key block]」的映射反转为「[batch, proxy head, key block] → [使用该块的查询]」，用来调度查询分块、优化共享稀疏 KV 块的复用；再对选中块跑一遍稀疏代理注意力拿到代理 LSE，然后流式执行融合的「代理-主」反向，加载 QKV、Q_proxy、K_proxy 和 main_lse 的分块。为容纳更多头进寄存器，必须缩小每次的 Q/KV 分块尺寸。

### KL 散度损失：用一行梯度代替实体化

DSA 原始的 KL 损失项是 L_i = Σ_t D_KL(p_t, s_t ‖ softmax(I_t, s_t))。若把索引器和主注意力的两个概率分布都实体化再累加 KL，需要对共享内存大量读写并占用额外寄存器，显著拖慢训练。

作者给出的等价技巧：设代理注意力概率为 p_px、主注意力概率为 p，展开 KL 项并对 softmax 前的代理分数 z_px,i 求偏导，利用 softmax 的 logprob 偏导 δ_it − p_px,i 与概率分布归一性，最终得到——**KL 损失对代理分数的梯度 = 代理概率 − 主概率**。这一项直接在 kernel 里算代理梯度，永远不需要完整实体化 KL 分布。

### 预热 kernel

预热模式下，主注意力前向是稠密的、不使用块索引，代理前向可以完全跳过，在反向里整体训练。主注意力预热前向直接调用 flash 并保存输出和 LSE，返回一个占位 KL；反向里对索引器调用稠密 flash 只拿 LSE，再复用稀疏 MSA 的融合「代理+主」反向。

## 正确性验证

作者用 eager 模式 PyTorch 实现 MSA，在多种配置下扫描两个实现的前向输出与反向梯度的余弦相似度，扫描在 bf16 下进行、反向同时含目标输出损失和内部 KL 损失。bf16 下的通常精度容差是 0.01。

## 接下来要做的

**提升融合反向的并行度。** 当前反向受限于低张量核心利用率和沉重寄存器/共享内存需求：博客吞吐扫描中 Flash-MSA 反向用了 138 寄存器/线程、105 KB 共享内存/CTA，而 H100/B200 上限是 255 寄存器/线程、228 KB 共享内存/CTA，因此被限制到 1 CTA/SM。试过把 Q/KV 切更窄以达 2 CTA/SM，但 CTA 总数增加反而净变慢。Flash-MSA 反向理论占用率 12.5%，Flash-Attention 为 18.75%。

**路由架构加速。** GLM 已证明用 IndexShare 层间共享代理头既稳定又更快；索引器推理时总以低精度服务，若训练也用低精度且稳定，能解决训练-推理不匹配并大幅加速。

**上下文并行（CP）。** 长上下文训练必须上某种 CP，否则很快爆内存。两种路径：

1. **按头全收集（Headwise all-gather）**：把分配给每个代理查询头的那组主注意力查询头称为「MSA 组」。MSA 组在前向/反向独立运行，因此用 TP 风格 CP 折叠（CP rank 最多到代理头数）很轻松——每设备持 (序列长度 / CP rank) 个 token 及其 MSA 组，调用 MSA 前对完整序列做一次 all-to-all 通信，无需改 kernel，当前 Megatron MSA fork 大概率就能用。
2. **环形（Ring）**：更难但大概是 MSA 做 CP 的最优解，允许更好 overlap 和更高 CP rank，需在代理前向内做 overlap-exchange 跨设备流式传 top-k、再广播、再做跨设备稀疏 key 查找。作者还没想好怎么接进 kernel，会先请教本地 CP 专家，这将是下一篇博客主题。

**两个设计说明。** 其一，论文里「给代理头加 value/output 投影、把代理输出加进主注意力以引入 CE 损失梯度」的做法会拖慢训练，MSA 论文表 6 也指出恰当预热可弥补不用人 CE 训练索引器。其二，调度要求 MSA 组 ≥ GQA 组（每个代理头映射到一个主注意力 GQA 组）；作者预期稳定训练至少需 4 个 MSA 组，对每层 KV cache 超 1024 的模型毫无兴趣，因此不打算实现 KV 头多于代理头的反演路径。

**跨 Top-k 扫描。** 作者可视化了稀疏收益随块减少的变化，并计划在有算力后扫描更多 GQA/代理 MQA 配置，以及用 MSA 继续预训练 Qwen3 这类 GQA 基座来测试转换（需更多算力）。

![](fig03.png)
<span style="font-size:12px;color:rgb(153,153,153);">Sweep across Top-k：稀疏收益随块大小的变化（16 Q 头、2 KV 头、4 代理 Q 头、1 代理 K 头、128 headdim、bf16、H100）</span>

<div style="background:#f5f0eb;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:16px;">
<div style="text-align:center;margin-bottom:8px;">
<strong style="font-size:15px;color:#8b6f4c;">结语</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
把 MSA 的训练 kernel 开源，补上了稀疏注意力从「推理能用」到「能训练」之间长期缺的一块拼图，对想在自己 GQA 模型上复现 MiniMax 路线的团队是实打实的起点。<br><br>
真正卡住吞吐的不是算法而是硬件占用：反向理论占用率只有 12.5%，被寄存器/共享内存绑死在 1 CTA/SM，这说明 kernel 还有明显优化空间，当前发布更接近「能跑通且正确」而非「榨干 GPU」。<br><br>
作者用 GQA 替换 MLA 这一招值得注意——它让西方主流架构绕开了 MLA 锁定，但代价是引入代理头分组专门化等新复杂度，训练稳定性仍需更多基座（如 Qwen3）的续训验证。<br><br>
下一步的 Ring 式上下文并行和低精度索引器，才是决定 Flash-MSA 能否从 demo 走向大规模训练的关键，而非当下的单卡速度对比。
</div>
</div>

---

<span style="font-size:14px;color:#888888;font-family:'Courier New',monospace;">【传送门】<br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/OoHu1yeuh1gzgCfEiPvDuQ" target="_blank" data-linktype="2">RL的下一个大突破：不是优化可验证问题而是把'不可验证'领域变得'可验证'</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/nVqW9acA7NN1zeALDwRAsw" target="_blank" data-linktype="2">Google新论文RubricEM: 评分标准引导的深度研究Agent训练框架</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/HnGKVp45C-GApBJ-LleP6g" target="_blank" data-linktype="2">小米MiMo罗福莉:8卡GPU让1T参数模型跑出1000 TPS , FP4+DFlash+TileRT全解读</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/3btXHAVd8_x5CM5CWETc2g" target="_blank" data-linktype="2">Agent卷向AI Infra: SGLang团队用硬核Agent优化框架和CUDA Kernal性能</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/2eWh5jZJPHsv0wi9km2nVg" target="_blank" data-linktype="2">NVIDIA TriAttention解读: KV Cache压缩最大的问题不是算法而是两个Infra问题</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/OqtF6ZaWQNu3o-VAWLfqbg" target="_blank" data-linktype="2">榨干GPU性能：流水线解码消除GPU气泡，推理吞吐提升35%</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/FTsibdpbEjvoPWtxGqgxkQ" target="_blank" data-linktype="2">小米MiMo罗福莉后训练新范式MOPD: 多教师同策略蒸馏，多领域无损集成</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/s0Ovn3_tnbbl9jxfAC3WLg" target="_blank" data-linktype="2">阿里Sparse Attention on CXL替代RDMA做KV Cache解耦 推理2.1×吞吐, 9.7×TTFT</a><br>
</span>

---

<span style="font-size:12px;color:#888888;font-family:'Courier New',monospace;">参考：https://nanduruganesh.github.io/flash-msa/</span>
