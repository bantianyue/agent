<div style="background:#e8f4fd;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:18px;">
<div style="text-align:center;margin-bottom:10px;">
<strong style="font-size:16px;color:#1a6ba0;">要点速览</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
- <strong>消费级Blackwell缺自己的attention kernel</strong>：NVIDIA的TensorRT-LLM为数据中心GPU预编译了13,453个attention kernel，但RTX 5090、DGX Spark没有对应的4-bit KV cache优化路径。现有的fp4路径比bf16慢1.8倍。<br><br>
- <strong>A4Q直接利用消费级Blackwell的特殊MMA指令</strong>：`mma.sync kind::mxf4nvf4.block_scale` 让K直接从缓存byte进入tensor core，零反量化指令。NVFP4 cache格式和MMA的scale布局完美对齐。<br><br>
- <strong>Gemma-4在100K context下decode加速2.01倍</strong>：Gemma-4-26B-A4B在DGX Spark上提速2.01×，Gemma-4-31B提速1.44×。但收益由KV宽度决定：KV width ≥ 4096才有，Mamba混合模型（Nemotron）和无收益。<br><br>
- <strong>AI构建，一天完成，花费 $5.34</strong>：Claude Fable做规划和kill criteria，Opus 4.8写kernel和PTX，从反汇编到端到端评估一天内闭环。GPT 5.5正在将A4Q移植到llama.cpp。
</div>
</div>

NVIDIA为TensorRT-LLM预编译了13,453个attention kernel，但它们几乎都是为数据中心GPU准备的。如果你有一张RTX 5090、一块DGX Spark，或者一台RTX PRO 6000：你的架构目录是空的。

**消费级Blackwell（sm120/sm121）没有自己的4-bit KV cache attention优化路径。**

这不是疏忽，而是数据中心优先产品策略的自然结果。但它带来的问题是实打实的：当前的fp4路径通过一个fp16转换链解包，每次tensor-core操作要花约9条指令做算术杂务。prefill attention比纯bf16 attention慢1.8倍：你读了四分之一的数据，却花了近两倍的时间。

这就是A4Q（Attention With 4-bit Q）要填补的空白。

作者Jetha Chan，前Google DeepMind、前Google Stadia工程师，用Claude Fable + Opus 4.8从零构建了这个kernel：从反汇编消费级Blackwell的指令集开始，到手写PTX、端到端评估，**一天内完成，GPU租用费 $5.34**。

<span style="font-size:12px;color:rgb(153,153,153);">来源：Jetha Chan</span>

## 问题：消费级Blackwell缺少QMUL4

NVIDIA的数据中心Blackwell（sm100）有一个优雅的fp4-KV attention路径。它用一条叫 **QMUL4** 的指令做反量化：四个e2m1值 × 一个广播fp8 scale，产生四个fp8值，一条指令搞定。结果直接喂给纯fp8 tensor-core MMA。

在消费级Blackwell（sm120/sm121）上，QMUL4指令不存在。

Jetha让Claude反汇编了sm121的JIT cache中的kernel，结果：QMUL4的数量是零。编译器发出的是一个三跳转换链：

- fp4 → fp16转换
- fp16 → bf16转换（因为Q是bf16）
- 然后乘法应用block scale

大约每两个值3条指令，加上一堆nibble洗牌。约 **9条非MMA指令**对应每一条MMA指令：kernel 90% 的时间在做算术杂务，而不是真正的矩阵乘法。

NVIDIA自己的消费者定位attention kernel（开源中的XQA）做的和A4Q前的fp4路径一模一样：转到fp16，付出代价。这确实不是任何人的疏忽：消费级Blackwell就是有不同的fp4指令集，围绕它的attention kernel还没被写出来而已。

## NVIDIA给的一个奇招

消费级Blackwell有一个相关硬件：**`mma.sync with kind::mxf4nvf4.block_scale`**。

这是一个tensor-core矩阵乘法，两个操作数都是fp4，硬件沿reduction维度每16个值应用一个fp8 scale因子，累加在fp32中。

盯着这条指令，再盯着NVFP4 cache格式：fp4值，每16个元素沿head维度放一个fp8 scale。

**对于QKᵀ，reduction维度就是head维度。cache格式和MMA的scale布局完美对齐。** K可以从cache字节直接进入tensor core，无需任何反量化指令。

（P×V不行：V的scale位于该矩阵乘法的错误轴上，这限制了包括NVIDIA官方kernel在内的所有实现。A4Q的P×V仍然用fp16做。可以接受。）

关键挑战是：MMA需要两边都是fp4。**Q** 是每个step新鲜计算的（bf16），必须在运行时量化为e2m1。整个想法成败取决于一个问题：**把Q量化到4位会毁掉模型吗？**

## 上线前的两次检查

Jetha被burn过足够多次，所以在写任何kernel代码之前先注册了kill criteria。

**第一关：也许当前kernel并不慢，瓶颈在带宽上？**

用Gemma-27B在RTX PRO 6000上实测：bf16 attention kernel达到约1,600 GB/s的有效cache带宽。fp4 kernel在batch 1只达到了这个数字的11%。

**不是memory bound。是淹死在转换指令中。** 优化空间确认。

**第二关：质量。量化Q会伤害模型吗？**

Claude捕获了真实Gemma-3-27B服务中的全部62层Q/K/V激活，测量了per-16-block fp4 Q在已运行fp4 K基础上的影响。

答案：几乎没有。K量化是主导误差项；加上Q后，argmax一致性平均变化约 **-0.012**，实际上承载长上下文的全局attention层变化仅 **-0.005**。

两条门都绿灯。开建。

## 构建A4Q

A4Q替换了一个函数：`compute_qk`。

之前在做什么？将fp4通过转换链扩展为bf16 MMA。

现在在做什么？将相同的共享内存字节直接送入block-scaled MMA。Q从一个小的量化kernel预打包到达（每行一个warp，8k context下43微秒：不到attention时间的2%）。softmax完全不知道发生了什么变化。

Jetha最满意的是A4Q不碰的地方做了什么：

vLLM fork中的FA2 paged-attention kernel已经处理了paging、GQA、causal和sliding-window masks、变长batch，以及fp16 P×V pipeline。关键是：它**已经**在共享内存中staged了打包的fp4 K tiles和它们的scale factor，因为旧的dequant路径也需要它们在那里。

之前做的每件事：vLLM端打包E2M1 tiles的writer、paging、FlashInfer端的scale staging：都是为慢路径建的。而每一件事竟然恰好是快路径需要的基石。

### 手写PTX一次通过

通常最花时间的部分：为手写PTX MMA搞定per-thread fragment layout和scale-factor register mapping：**第一次尝试就成功了**。Claude从CUTLASS atom中复制了精确布局，在100行的独立单元测试中验证，然后才触及真实kernel。

单元测试返回bit-exact。集成kernel也一样：在反量化输入上对比reference，max_abs_diff = 0.0。不是接近：**完全一致**。四个值乘以fp8 scales进入fp32 accumulator是精确算术，没有可以分歧的舍入。

### Prefill性能

RTX PRO 6000 + Gemma 3 27B，causal prefill：

| context | bf16-FA2 | fp4 path (old) | A4Q (quant + kernel) | vs old fp4 |
|---------|----------|----------------|----------------------|-----------|
| 8k | 2.305 ms | 4.063 ms | 2.454 ms | 1.66× |
| 32k | 34.473 ms | 64.374 ms | 38.783 ms | 1.66× |

fp4 dequant税基本上消失了：四分之一大小的cache，速度只比bf16慢7–13%。

## 两个仓库的架构

A4Q是两个代码库中的两块工作：

- **kernel在FlashInfer**：block-scaled QKᵀ MMA、on-the-fly Q-quantizer、密集打包的prefill tiles、split-KV decode：都在Jetha维护的FlashInfer fork中。这是算术发生的地方。
- **serving集成在vLLM**：路由 `--kv-cache-dtype nvfp4` 到A4Q路径、cache writer和字节布局契约、让Gemma-4的512-wide头到达kernel的dispatch放宽、以及六模型eval电池。

## 六模型验证

六个模型在NVFP4权重复 + NVFP4 KV cache下运行，A4Q on：

| 模型 | attention 几何 | passkey | GSM8K (A4Q on) | GSM8K (A4Q off) |
|------|---------------|---------|----------------|-----------------|
| Gemma-4-26B-A4B | MoE, 512-wide VO-split | 12/12 | 0.973 | 0.980 |
| Gemma-4-31B-IT | dense, 512-wide VO-split | 12/12 | 0.987 | 0.987 |
| Nemotron-3-Nano-30B-A3B | MoE, head-128 | 12/12 | 0.940 | 0.947 |
| Nemotron-3-Super-120B-A12B | MoE, head-128 | 12/12 | 0.973 | 0.987 |
| Qwen3.6-35B-A3B | MoE, head-256, linear-attn hybrid | 12/12 | 0.980 | 0.973 |
| Qwen3.5-122B-A10B | MoE, head-256, linear-attn hybrid | 12/12 | 0.967 | 0.973 |

Passkey全部12/12，GSM8K在A4Q on和off之间最多差两个问题（在150个问题中）：完全是噪声水平。

## KV宽度法则

理解A4Q收益的关键：**端到端收益完美按KV宽度（num_kv_heads × head_dim）排序。** 这不是softmax-vs-hybrid，也不是head_dim单独决定的：就是KV宽度。

- **≥4096**：胜出（两个Gemma-4）
- **≤1024**：基本无收益（Nemotron Mamba混合、Qwen线性注意力混合、甚至纯softmax的Qwen3-30B窄GQA）

Az行业在2024年左右用GQA换掉了KV宽度；Gemma-4保留了它，A4Q精确地奖励这个设计选择。

### Kernel层面vs端到端

kernel层面的QKᵀ 加速非常惊人：

| context | shipping fp4 | A4Q | bf16 | A4Q vs fp4 | A4Q vs bf16 |
|---------|-------------|-----|------|-----------|------------|
| 8k | 0.174 ms | 0.075 ms | 0.059 ms | 2.3× | 0.8× |
| 32k | 0.658 ms | 0.074 ms | 0.174 ms | **8.9×** | 2.4× |
| 100k | 2.366 ms | 0.197 ms | 0.510 ms | **12.0×** | 2.6× |

Split-KV让decode在cache增长12× 时几乎保持平坦（0.075 → 0.074 → 0.197 ms），而dequant路径线性增长：这就是整个8.9× 的来源。

但kernel层面的加速不等于token层面的加速。attention只是decode step的一部分。对于这些MoE模型在短context下，attention只占1–2%：所以端到端几乎看不到收益。**attention在decode step中的占比越大，A4Q的收益越显著。**

### 端到端解码速度

在DGX Spark（sm121）上，batch-1 steady-state decode：

| 模型 | 32k | 64k | 100k |
|------|-----|-----|------|
| Gemma-4-31B-IT（dense, 512-wide VO-split）| 1.16× | 1.30× | **1.44×** |
| Gemma-4-26B-A4B（wide-head MoE）| 1.42× | 1.67× | **2.01×** |
| Nemotron-3-Nano-30B（head-128, Mamba-hybrid）| 0.88× | 0.88× | 1.01× |
| Qwen3.6-27B（dense FFN, linear-attn hybrid）| 0.98× | 1.00× | 1.00× |
| Qwen3.6-35B-A3B（head-256, linear-attn hybrid）| 0.99× | 0.98× | 0.96× |

三个要点：

**Gemma是A4Q的舞台，收益随context增长。** 密集模型1.16→1.44×，MoE最高2.0×：因为长context全局attention是Gemma decode step的实质开销。

**稀疏MoE登顶有内在原因：** 它每token只激活约4B的26B参数，所以FFN便宜，attention成为长context下的主导成本：正是A4Q削减的成本。密集31B每token支付全部参数量的FFN，相同宽头attention是step中较小的份额，收益被稀释。

**Gemma-4有有趣的几何结构：** 宽头、不对称。sliding/local层256-wide，全局层 **512-wide VO-split**。这些全局头是每个其他引擎都丢给software fallback的几何结构；A4Q在tensor core上运行它们。

Nemotron和Qwen是反例。Nemotron-Nano甚至持有最大的kernel层面收益（上面那个8.9×），但端到端只在parity附近徘徊：甚至轻微倒退。原因一致：它们都是混合模型。Nemotron-Nano主要是Mamba，Qwen3.6-35B四分之三是gated-deltanet线性注意力。softmax attention从来不是它们的decode瓶颈，A4Q没有什么可以给的。

**A4Q在attention是瓶颈时才有回报；端到端数字是kernel数字的一个分数：这不是小字条款，而是全部意义所在。**

## 代码状态与可用性

严格来说，工作还没完成：直到被合并才算完成。

A4Q依赖于早期vLLM工作（FlashInfer #3684：Gemma-4的asymmetric VO-split NVFP4 paged prefill）。该PR上游已开放但暂挂：一组重叠的NVFP4-paged-KV PR先落地，完成后在其上rebase，A4Q叠在上面。

两个half已推送：kernel在 `jethac/flashinfer`（a4q-integration），serving在 `jethac/vllm`，以sm120 + sm121 wheel形式分发。想今天试用的可下载：

- FlashInfer Python wheel（Python 3.12）
- vLLM wheel（sm120a x86_64 / sm121a arm64）

具体Wheel URL见原文。

## AI构建，人工验证

最后，三个模型构建了这个项目：

- **Claude Fable**：分析和规划，设计研究、构思、以及整个构建所依赖的问题和kill criteria框架
- **Claude Opus 4.8**：工程：kernel和手写PTX、CUDA量化器、反汇编、eval电池、认证、以及本文初稿
- **GPT 5.5 (Codex)**：正在学习整个campaign，将A4Q向下移植到llama.cpp，让kernel也到达GGUF世界

**一天内完成，GPU租用费 $5.34。**

Jetha坦诚地说："我希望能声称这总是发生。但它并不总是发生。"

<div style="background:#f5f0eb;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:16px;">
<div style="text-align:center;margin-bottom:8px;">
<strong style="font-size:15px;color:#8b6f4c;">结语</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
A4Q是一个让消费级Blackwell GPU跑出与数据中心GPU不相上下的attention效率的kernel。这件事之所以值得关注，不只是技术本身：而是它揭示了当前GPU计算生态中的一个结构性缺口。NVIDIA为自家数据中心GPU编译了13,453个attention kernel，但消费级用户只能靠社区自建。在推理需求从数据中心向边缘和桌面迁移的今天，这个缺口的代价只会越来越大。<br><br>

另一个值得关注的点是构建方式。一个独立开发者用AI（Claude Fable + Opus 4.8）在一天内从反汇编到kernel再到端到端验证走完全程，花费 $5.34。不是大厂团队，不是CUDA专家，是一个PS3时代程序员出身的工程师靠AI辅助做到了。这本身就是一个关于开发方式变迁的信号：当AI能帮你反汇编指令集、分析cache格式、手写PTX并验证位精确时，"谁能写GPU kernel"这个问题的答案正在被重写。
</div>
</div>

---

<span style="font-size:14px;color:#888888;font-family:'Courier New',monospace;">【传送门】<br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/qcIFzXsBalSGpca5fzJKxg" target="_blank" data-linktype="2">Claude Code动态Workflow Vs. SubAgent Vs. Skill</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/aiJs5CC8Gb6qa_xDRNEjTA" target="_blank" data-linktype="2">Dynamic Subagents：用代码编排Agents，告别逐轮工具调用</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/mFuUJ79DRodIK6shVWOgpw" target="_blank" data-linktype="2">OpenAI GPT-5.6: 安全之外新增Prompt Cache断点+两种推理模式; 放弃版本号</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/xP1cEoO_plRpWItxhqeQnQ" target="_blank" data-linktype="2">Agent Harness Engineering：为什么Agent可靠性的天花板不是模型，而是基...</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/o6pnSWW01pahFQelJSbSPA" target="_blank" data-linktype="2">华为「韬定律」全解析：从 τ 常数到4GHz麒麟，一张时间表看清未来十年芯片路线</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/PLNx54PxO1A0oYc47hz99g" target="_blank" data-linktype="2">Anthropic三连：Claude Opus 4.8-更聪明+诚实；CC动态工作流+算力控制</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/Pdjz39WG9SS6IpWWAJ6pPw" target="_blank" data-linktype="2">Claude Opus 4.8击败Opus 4.7、GPT-5.5和Gemini 3.1 Pro</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/oDZJbvskv_ocNgPUH1DHVA" target="_blank" data-linktype="2">AI暗输出：为何AI价值在GDP统计中失效了</a><br>
</span>

---

<span style="font-size:12px;color:#888888;font-family:'Courier New',monospace;">参考：

https://x.com/jetha/status/2073322454198649215</span>
