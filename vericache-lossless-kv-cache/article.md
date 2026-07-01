<div style="background:#e8f4fd;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:18px;">
<div style="text-align:center;margin-bottom:10px;">
<strong style="font-size:16px;color:#1a6ba0;">要点速览</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
- <strong>有损 KV Cache 不等于「效果差一点」</strong>：每一步解码的微小偏差会指数级累积——KVzip 4×压缩下，250 个 token 后全量 KV 的正确输出概率只剩 0.25%。代码生成中，200 行后直接反了<br><br>
- <strong>VeriCache 把有损压缩当成「草稿生成器」</strong>：用压缩 KV 快速 Draft token，再用全量 KV 验证纠错。输出与全量 KV 推理完全一致，但吞吐可达全量 KV 的 4×<br><br>
- <strong>两大系统创新让方案成立</strong>：交叉资源交错（压缩 KV 草稿吃 HBM 带宽，全量 KV 验证吃 PCIe/网络带宽，两者可重叠流水）和长验证窗口（压缩 KV 的草稿接受率远高于传统小模型 Draft 方案）<br><br>
- <strong>支持 7 种压缩方法</strong>：统一的 Compressor Interface 让任意的 token-dropping 和量化方法都能接入 VeriCache，无需修改调度或验证逻辑
</div>
</div>

---

KV Cache 的体量已经成为长上下文 LLM 推理的核心瓶颈。过去两年，学界提出了大量 KV Cache 压缩方法——token 丢弃、量化降精度，压缩比从 2× 到 5× 不等。这些方法确实显著提升了吞吐。

但它们都有一个共同的名字：**有损**。

这篇文章来自芝加哥大学 Junchen Jiang 团队（第一作者 Jiayi Yao），提出了一套名为 **VeriCache** 的推理框架，核心思路简单到令人意外——让有损压缩当 Draft 模型，全量 KV Cache 做验证，最终输出与全量 KV 完全一致，同时将推理吞吐提升至 4×。

关键在于，这个「验证」的成本不能吃掉压缩带来的收益。VeriCache 用两个系统设计做到了。

---

### 压缩的「隐形代价」：不是小偏差，是指数级崩溃

现有 KV Cache 压缩的评价标准几乎清一色用 token 级指标：F1、ROUGE、困惑度、余弦相似度。这些指标对小偏差非常宽容，适合摘要、开放问答等场景。

问题是，代码生成和工具调用不宽容。

KVzip 4× 压缩下，F1 仍能维持在 75% 以上——看起来还行。但代码格式准确率（输出必须是合法 git diff）直接跌到接近 0%，函数调用准确率（每个调用名和参数精确匹配）也跌到 10% 以下。

**为什么会这样？** 论文给出了一个清晰的数学分析。

每一步解码，压缩 KV 都会改变注意力权重，使得模型的下一个 token 分布 p_lossy 偏离全量 KV 的分布 p_full。这跟采样噪音（temperature）有本质区别——采样噪音是从正确的分布中抽样，只是抽了不同的 token；而压缩偏差是**整个分布都错了**，无论怎么重采样都拉不回来。

每个 step 的 KL 散度只有约 0.023 nats——单个 step 的偏差几乎不可察觉，压缩模型对正确 token 仍然分配了 98% 的概率。但经过 250 步解码，累积 KL 达到约 6 nats，这意味着压缩模型生成全量 KV 正确输出序列的概率只有约 0.25%。

**每一步 2% 的偏差，放大 250 步后成了 400 倍的差距。**

![fig2.png](fig2.png)
<span style="font-size:12px;color:rgb(153,153,153);">KVzip 4× 压缩下代码生成的灾难：前 200 行还能跟全量 KV 一样，之后完全跑偏，输出了错误的实现。</span>

![fig3.png](fig3.png)
<span style="font-size:12px;color:rgb(153,153,153);">Token 级指标（F1）和功能指标（代码格式准确率、函数调用准确率）之间存在巨大鸿沟。F1 > 75%，但功能准确率几乎归零。</span>

---

### VeriCache 的核心循环：Draft → Verify → Correct

VeriCache 的思路直接借鉴了投机解码（Speculative Decoding），但做了一个关键改动：**Draft 模型和验证模型是同一个 LLM，只是用了不同的 KV Cache 版本。**

具体流程分三步：

1. **Draft**：用压缩 KV Cache（KV_comp）自回归生成 x 个候选 token
2. **Verify**：用全量 KV Cache（KV_full）对这 x 个 token 做一次并行前向传播，得到每个位置上「正确的」next-token 预测
3. **Accept**：从第一个不匹配的位置开始，接受之前的所有 token，并用验证模型的正确 token 替换那个不匹配的 token

这个机制保证：**最终输出与全量 KV 推理完全一致**（greedy decoding 下，零温度）。

![fig5.png](fig5.png)
<span style="font-size:12px;color:rgb(153,153,153);">VeriCache 的工作流程：压缩 KV 草稿 → 全量 KV 验证 → 纠错，确保输出与全量 KV 完全一致。</span>

---

### 两个系统设计让方案站住脚

直接套用投机解码会出问题——验证阶段需要将全量 KV 从 CPU 加载回 GPU，这个传输成本很可能吃掉压缩带来的吞吐收益。VeriCache 的两个关键设计解决了这个问题。

#### 设计一：交叉资源交错（Cross-resource Staggering）

这是 VeriCache 最精巧的洞察。压缩 KV 的 Draft 过程和全量 KV 的 Verify 过程**吃的是完全不同的硬件资源**：

- **Draft**：每次只解码一个 token，序列化的向量-矩阵乘法，瓶颈在 GPU HBM 带宽（模型权重 + 压缩 KV 的读取）
- **Verify**：需要从 CPU 把全量 KV 加载到 GPU（PCIe/网络带宽瓶颈），然后做 x 个 token 的并行前向传播（GPU 算力瓶颈）

两个过程的瓶颈资源是互补的——Draft 压满 HBM 时，PCIe 链路在闲着；Verify 压满 PCIe 时，HBM 又在闲着。

VeriCache 的调度器不做「全部 Draft 完再全部 Verify」的 lock-step 模式，而是**把验证请求打散混入各轮的 Draft 中**——每个只有约 1/x 的请求在验证，其余在草稿。这样 PCIe 传输可以和 HBM 读取重叠，资源利用率大幅提升。

![fig6.png](fig6.png)
<span style="font-size:12px;color:rgb(153,153,153);">Lock-step（左）vs Staggered（右）调度对比。打散验证请求后，PCIe 传输与 Draft 的前向计算可以重叠，GPU/HBM/Interconnect 同时忙碌。</span>

论文给出了一个具体算例：Mistral 24B、10 个并发请求、每个请求 KV_comp=1GB、KV_full=4GB、Draft 长度 30。传统 lock-step 需要把 10 个验证集中在同一轮，40GB 的 PCIe 传输序列化需要约 800ms——是单轮迭代时间的 20 倍。VeriCache 将验证请求打散，每 3 轮 Draft 插入一次验证，80ms 的 PCIe 传输可以和当前轮的 Draft 前向计算完全重叠，峰值 HBM 占用仅多了一个 KV_full。

#### 设计二：长验证窗口摊薄开销

Draft 的接受率（acceptance rate）γ 决定了多久需要做一次验证。传统投机解码用小模型做 Draft，几个 token 后分布就跑偏了，接受长度只有 2-3 个 token。

VeriCache 不一样——Draft 和验证用的是同一个模型，只是 KV Cache 版本不同，所以分布偏差远小于小模型方案。实测在 4× 压缩下，VeriCache 的接受率在 Draft 长度 30 时仍高于 0.8，每次验证能接受约 19-23 个 token（传统方案只有 2-3 个）。

这意味着每次从 CPU 加载全量 KV 的代价被摊薄到 20+ 个 token 上，而不是 2-3 个 token。更长的验证周期 = 更少的全量 KV 加载 = 更低的 PCIe 开销。

![fig8.png](fig8.png)
<span style="font-size:12px;color:rgb(153,153,153);">接受率（左）和理想加速比（右）。4× 压缩下 Draft 长度 30 时接受率仍 > 0.8，理想加速比可达约 3.7×。</span>

![fig9.png](fig9.png)
<span style="font-size:12px;color:rgb(153,153,153);">与传统投机解码方案的接受长度对比。VeriCache 在 Qwen-32B 上接受约 19 个 token，Llama-70B 上约 23 个；Eagle 只有 1-2 个，小模型 Draft 也只有 3-10 个。</span>

不仅如此，VeriCache 还可以与传统投机解码（如 Eagle）组合使用——小模型先 Draft token，VeriCache 用压缩 KV 验证，再定期用全量 KV 校正压缩偏差。组合后理想加速比达到 4.35×。

![fig10.png](fig10.png)
<span style="font-size:12px;color:rgb(153,153,153);">VeriCache + Eagle 组合：接受长度提升明显，理想加速比达 4.35×。</span>

---

### 两种部署场景：长上下文解码 + 远程前缀缓存

VeriCache 支持两种场景：

**长上下文解码**：全量 KV 保存在 CPU 内存，GPU 只保留压缩 KV。验证时通过 PCIe 将全量 KV 加载到 GPU。

**远程前缀缓存**：在分布式推理场景中，缓存的 KV 从远端存储节点通过网络传输。存储节点有一个近端 GPU（快链路 BW_h）和一个远端 GPU（慢链路 BW_l）。远端 GPU 用压缩 KV 做 Draft，近端 GPU 加载全量 KV 做验证——Draft 和 Verify 跑在不同硬件上，天然解耦。

![fig7.png](fig7.png)
<span style="font-size:12px;color:rgb(153,153,153);">两种部署模式：长上下文解码（上）全量 KV 在 CPU；远程前缀缓存（下）全量 KV 在本地存储。远端 GPU 做 Draft，近端 GPU 做 Verify。</span>

---

### 统一的 Compressor Interface

VeriCache 暴露了一个统一的 Compressor Interface，任何 token-dropping 或量化方法只要实现这个接口就能接入：

- **Long-context decoding 场景**：KVzip、KIVI、Keyformer、H2O、FastKVzip、KVzap、ExpectedAttention、SnapKV、KVQuant、RotateKV 等均已验证
- **Remote prefix caching 场景**：CacheGen、KVQuant、KVTC、TurboQuant 等流式压缩方法

**一个接口覆盖 7 种以上压缩方法**，调度、验证、传输逻辑完全不变。之前的工作（MagicDec、QuantSpec、SparseSpec）每个都只支持单一压缩方法。

---

### 实验结果：无损 + 2-4× 吞吐

VeriCache 基于 vLLM + LMCache 实现，在多种模型和工作负载上进行了评估。

**长上下文解码**：VeriCache 在 Llama-70B 上实现 1.92×-2.73× 加速（全量 KV 的 102 tok/s → VeriCache 的 256 tok/s）；在 Qwen-32B 上最高达到 4.26×（叠加 Eagle 后）。

**远程前缀缓存**：传统投机解码方案不适用于此场景（Draft 模型也需要完整 KV），而 VeriCache 在 Llama-70B 上仍能做到 1.33×-2.11× 加速（240 → 485 tok/s）。

**质量对比**：在所有压缩方法上，VeriCache 的 KL 散度保持在 0.01 nats 以下（仅由硬件非确定性引起），而有损方案的 KL 可达 14+ nats。函数调用准确率：VeriCache 在保持全量 KV 准确率的前提下，达到最快有损方案（KVzip）的 59% 以上的吞吐；KVzip 在同样吞吐下准确率下降约 30 个百分点。

![fig11.png](fig11.png)
<span style="font-size:12px;color:rgb(153,153,153);">长上下文解码和远程前缀缓存下的解码吞吐。VeriCache（橙/红线）超越所有有损基线，同时保持完全无损的输出质量。</span>

**硬件参数扫频**：当 GPU HBM 中 KV 预算从 0.74 降至 0.2 时，VeriCache 的加速比从 1.61× 增至 2.71×——全量 KV 的 batch 容量比 VeriCache 的 batch 崩溃得更快（全量 KV 吃掉 HBM，batch 缩到 1，而 VeriCache 的 batch 只是稍微缩小）。SparseSpec 更惨，从 1.82× 掉到 1.02×——因为它必须在 Draft GPU 上常驻全量 KV。

![fig12.png](fig12.png)
<span style="font-size:12px;color:rgb(153,153,153);">端到端请求延迟 vs 请求率。VeriCache 在两种 Pipeline 上均保持低延迟，在达到全量 KV 2-3× 吞吐的同时延迟仅有小幅增加。</span>

![fig13.png](fig13.png)
<span style="font-size:12px;color:rgb(153,153,153);">硬件参数扫频：KV 预算越紧（左），VeriCache 加速比越高（全量 KV 的 batch 先崩）；HBM:Interconnect 带宽比越低（右，即 PCIe 更快），加速比也越高。</span>

---

### 结语

<div style="background:#f5f0eb;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:16px;">
<div style="text-align:center;margin-bottom:8px;">
<strong style="font-size:15px;color:#8b6f4c;">结语</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
VeriCache 的核心洞察其实很简单：有损 KV Cache 的偏差很小（每步 -0.023 nats KL），但绝对不应该被忽视。它不为单个 token 采样错误负责——那在 temperature > 0 时本就合理——它为一个系统性偏差负责：每次采样的分布都偏移了正确分布一点点，而自回归会把这一点点放大成灾难。<br><br>
这个思路本质上是把「压缩率 vs 准确率」的 trade-off 从算法层面移到了系统层面——不是让压缩算法「足够好」，而是让压缩算法「只管提速」，由 VeriCache 的验证机制保证正确性。这种分层抽象在系统领域屡试不爽，但放在 KV Cache 压缩这个具体问题上，两个核心设计（交叉资源交错和长验证窗口）确实精准地抓住了瓶颈的本质。<br><br>
值得注意的是，VeriCache 同时支持 token-dropping 和量化两类压缩方法——不是提出新的压缩算法，而是为所有压缩方法提供了一层「无损加速引擎」。从系统工程角度看，这是比做出一个更好的压缩算法更有价值的贡献。
</div>
</div>


---

<span style="font-size:12px;color:#888888;font-family:'Courier New',monospace;">参考：

https://arxiv.org/html/2605.17613v1</span>
