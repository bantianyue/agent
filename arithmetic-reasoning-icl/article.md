<div style="background:#e8f4fd;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:18px;">
<div style="text-align:center;margin-bottom:10px;">
<strong style="font-size:16px;color:#1a6ba0;">要点速览</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
- <strong>核心痛点</strong>：投机解码（SD）想靠加大草稿预算提速，但自回归 drafter 成本高、双向扩散 drafter 树不一致，陷入「因果性-效率」两难，加速随预算增大触顶<br><br>
- <strong>解法</strong>：JetSpec 训练一个因果并行草稿 head，一次前向算出整棵候选树的 logits，同时每个分支都条件于自身路径前缀，让草稿分布对齐目标模型自回归分解<br><br>
- <strong>结果</strong>：Qwen3-8B 上预算256时 MATH-500 达 9.64× 加速（τ=10.76），比 DFlash/DDTree 高一个台阶；集成 vLLM 后小负载吞吐翻倍<br><br>
- <strong>关键结论</strong>：forward-KL 蒸馏远胜 reverse-KL（差36-46%）；大预算只在低到中服务负载才划算，重负载会饱和
</div>
</div>

---

投机解码（SD）的加速随草稿预算增大而触顶，根本原因是「因果性-效率」两难：自回归 drafter（如 EAGLE）能画出路径条件化的高质量树，但树越深起草越慢；双向块扩散 drafter（如 DFlash）一次生成全部位置，可各分支互不知晓彼此选了什么 token，拼出的树「各自合理、合起来矛盾」，白白浪费预算。JetSpec 的做法是：**用一个因果并行的草稿 head，一次前向既算完整棵树，又让每个分支对齐目标模型的真实自回归概率。**

## 方法：因果并行草稿 head

JetSpec 复用冻结目标模型的融合隐藏状态，训练一个轻量草稿 head。关键在注意力掩码：每个树节点只能看原始前缀和自己的祖先节点，不能看后代或无关兄弟分支。这样所有深度的 logits 可以并行算出来，但每个节点条件于「自己这条分支上之前实际选了哪些 token」，其分解形式与目标模型 p(y₁:ₖ|x)=∏p(yᵢ|x,y<ᵢ) 完全镜像。

对比两类旧方案：分支不可知的扩散草稿按伪分布 qsur∝∏rᵢ(yᵢ|x) 建树，会偏好「单 token 合理、整条分支矛盾」的续写；JetSpec 的因果分解则让树在验证时接受率更高。训练用 forward-KL 软标签蒸馏（而非硬标签 SFT 或 reverse-KL），保留目标模型对多种合理续写的相对偏好。

<div style="background:#f0f7fa;padding:16px 18px 14px 18px;border-radius:6px;margin:16px 0;border-left:4px solid #5b9bd5;">
<div style="font-size:15px;color:#2c6a9e;line-height:1.7;">
图3展示了整体设计：从冻结目标模型抽取融合隐藏特征，喂给因果并行草稿 head，一次前向产出高质量候选树。</div>
</div>

![](img4.png)
<span style="font-size:12px;color:rgb(153,153,153);">JetSpec 设计总览：从冻结目标模型抽取融合隐藏特征，条件化因果并行草稿 head，一次前向生成候选树</span>

## 实验设置

在 Qwen3-8B（dense）和 Qwen3-30B-A3B（MoE）上评估，主实验用非思考模式。训练数据从 Nemotron Post-Training V2 精选 780K 样本（全代码/数学切分 + STEM/chat 随机样本 + 20K CodeAlpaca），对续写序列用目标模型重新生成作监督。基线为 EAGLE-3 和 DFlash，DDTree 用 DFlash 的块扩散分布做 best-first 树扩展。所有方法在同一数据混合、学习率 3e-4、8×H100 上训练，公平可比。

## 结果：预算越大，JetSpec 优势越明显

**低预算（16-32 token）**：预算16时 DFlash 与 JetSpec 几乎打平（短线性草稿已够覆盖高概率续写）；预算提到32，JetSpec 继续微涨，DFlash 反而饱和或下降。说明 JetSpec 把多出来的预算更有效地转化成了被接受的 token。

**高预算（64-256 token）**：差距拉开。下表取 Qwen3-8B、温度0、各基准的代表数字（Speedup / 平均接受长度 τ）：

| 方法 | 预算 | MATH-500 | HumanEval | MBPP | MT-Bench |
|------|------|----------|-----------|------|----------|
| EAGLE-3 | 256 | 8.78 / 9.81 | 6.31 / 6.96 | 6.09 / 6.70 | 4.26 / 5.41 |
| DDTree | 256 | 8.78 / 9.81 | 6.31 / 6.96 | 6.09 / 6.70 | 4.26 / 5.41 |
| JetSpec | 256 | **9.64 / 10.76** | **7.12 / 7.78** | **6.73 / 7.43** | **4.58 / 5.94** |

数学和代码基准从低预算的 4-6× 提升到 7-10×；DDTree 仅温和扩展到约 9×，证明因果树起草比分支不可知建树接受率更高。温度1（非贪婪）下 JetSpec 依旧有效，收益稳健。

![](img2.png)
<span style="font-size:12px;color:rgb(153,153,153);">图1：H100 上跨数学/代码/对话基准的端到端加速，JetSpec 全程领先 DFlash 与 DDTree</span>

## 系统性能：vLLM 集成与预算调度

把树起草和验证集成进 vLLM（含自定义 SM90 paged FlashAttention 树掩码核）后，性能不只看接受长度，还受批处理、验证开销、GPU 占用的牵制。关键发现是**预算要按负载选**：

- 批大小1：预算16→128，吞吐 443.3→968.2 TPS，加速 3.09×→6.75×
- 批大小16：预算256 跌到 4.51×；批大小32：跌到 2.85×，和预算128 几乎持平——已饱和

实际含义：低到中负载用大预算（闲着也是闲着，拿来减少解码轮数）；重负载改用小/中预算，避免每步开销吃掉批处理效率。

## 消融：哪些设计真正起作用

**蒸馏损失**：SFT 与 forward-KL 在各数据集相差约3%；reverse-KL 比 forward-KL 相对下降 36-46%——mode-seeking 把概率质量压太狠，不适合树起草。

**学习率**：3e-4 达峰（8.30×），6e-4 和 1e-3 在峰值2%内。

**模型泛化**：换到 MoE 的 Qwen3-30B-A3B，JetSpec 仍全面高于 DDTree（如 MATH-500 9.45/10.65 vs 8.61/9.49），因果树起草不只在 dense 上有效。

**训练数据**：用目标模型重新生成的续写作监督最强；直接在原始语料上训的 JetSpec-Corpus 落后很多（预算256 MATH-500 仅 3.36 vs 7.82），但仍一致加速——说明因果并行起草可塞进中训练甚至预训练。

**因果 head vs 扩散 head**：在不同 γ（控制远离锚点位置损失降权）下，因果 head 全程稳健（8.29-8.50×）；扩散 head 敏感且在端点崩塌（γ=0 仅 5.46×，γ=15 仅 6.17×）。一个具体失败案例：MATH-500 某 prompt 上，扩散 head 把「given told that」排第一，但其目标模型联合概率为 -63.32 nats（两个互斥开场硬拼），真正连贯的「are given that the」（联合 -0.08）反而排第3；因果 head 把「are told that」排第一，草稿分数≈目标联合，印证了分支级因果条件的作用。

<div style="background:#f5f0eb;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:16px;">
<div style="text-align:center;margin-bottom:8px;">
<strong style="font-size:15px;color:#8b6f4c;">结语</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
JetSpec 的价值不在于又提出一个 drafter，而是把「并行起草的低成本」和「树起草的高接受率」第一次在同一种 head 里同时拿到，且证明大预算真能换来大加速，而不是很快触顶。<br><br>
但它受益的前提是低到中服务负载：在重负载下大预算会饱和，这意味着实际部署里预算调度（甚至动态调度）比单纯堆预算更重要，论文也把动态调度留作未来工作。<br><br>
另一个值得注意的点是训练数据来源——重新生成续写比直接用语料强一倍多，这意味着 JetSpec 的效果上限其实绑在「有多少目标模型的真实生成可用」上。
</div>
</div>

---

<span style="font-size:12px;color:#888888;font-family:'Courier New',monospace;">参考：https://arxiv.org/html/2606.18394v3</span>
