# KV Cache Compression and Its Infra Problems — 完整翻译

**原文标题：** KV Cache Compression and Its Infra Problems
**作者：** Weian Mao, Yukang Chen, Wei Huang, Shuai Yang, Luozhou Wang, Song Han (NVIDIA Research / MIT)
**发布日期：** June 12, 2026

## 背景：KV Cache 与长推理中的内存耗尽

Transformer 每生成一个 token，计算 query、key、value 向量，新的 query 对所有历史 key/value 做 attention。KV cache 让这变得可行：每个 token 的 K 和 V 只计算一次并保存，后续步直接复用——每步 O(n) 而非 O(n²)。但 KV cache 从不缩小：每生成一个 token，就在所有层和头上追加新的 K/V。

算下来很惨。Qwen3-32B + 4-bit 量化（用户真实部署的配置）在 24GB GPU 上跑约 24000 个 token 就会 OOM，而推理模型在复杂问题上 routinely 产生 32K token 的轨迹。

（图1：KV cache 增长撑爆 GPU 内存的示意图）

压缩之所以可能，是因为 attention 是稀疏的——一小部分 token 吸收了绝大多数 attention weight。问题是：哪些 token 安全可删，什么时候删？

## 现有方法——以及两个基础设施问题

该领域始于 2023 年的一个发现：attention 高度不均匀。模型把不成比例的 attention weight 分给最开始的 token（StreamingLLM 提出的"attention sinks"），而约 20% 的 token 收集了 80% 的总 attention weight（H2O 和 Scissorhands 提出的"heavy hitters"）。标准方案（图2）：始终保留 sinks + sliding window + 保留 budget 内的 heavy hitters。

（图2：StreamingLLM——只保留 attention sinks + sliding window）

方案的核心问题是：怎么知道中间哪些 token 是 heavy hitters？最大一类压缩方法的答案是：读取模型自己的历史 attention scores。H2O 是典型例子：维护每个 cached token 在所有 decode 步收到的累积 attention 分数，每步 evict 最低分 token。

（图3：H2O 的累积历史注意力评分）

SnapKV 是同一思路最有影响力的改进。它不连续累积，而是在 prefill 结束时一次性评分：用最近 W 个 token 的 attention 窗口来决定哪些 token 保留。去掉了每步记账，也避免了累积评分对"活得更久"的 token 的偏见。但观测窗口不能做太大——因为 RoPE 按位置旋转 query，只有最近约 25 个 query 能反映模型当前在看哪里。

（图4：SnapKV 的观测窗口快照评分）

这个类别（无论是 H2O 连续评分还是 SnapKV 一次性评分）都依赖于观测 attention scores。而这个依赖与生产基础设施在两个地方碰撞。

### 基础设施问题 1：FlashAttention 不暴露 attention scores

生产推理用 FlashAttention，它将 attention 计算分块在 SRAM 中完成，从不把完整的 N×N 分数矩阵 materialize 到 HBM 中。这正是它快的秘诀——也意味着压缩方案想读的分数从不写入压缩代码能读到的地方。

H2O 风格的累积评分需要每步的 attention scores——没拿到分数就无法更新累积和。参考实现 H2O 的解决方式是回退到 eager attention，把完整分数矩阵 materialize 出来，彻底放弃 FlashAttention。

### 基础设施问题 2：反复 token eviction 在分页系统中无法释放显存

vLLM 等生产 serving 系统用 paged attention 管理 KV cache：显存被分为固定大小的物理块，每个块放约 16 个 token，只有块完全为空时才能被回收。

重复的 decode-time eviction 把幸存者散落到各个块中（图5）。从 16000 个 token 里 evict 掉 14400 个，剩下 1600 个幸存者散布在约 1000 个原始块中——几乎每个块都有至少一个幸存者，分配器几乎什么也回收不了。

R-KV（专为推理模型设计的最强 evictor）报告 90% 的内存节省，但那是用预分配的连续张量测的，不是在 vLLM 中；其 Appendix D 也承认与 paged attention 集成"提出了一个非平凡挑战，需要进一步研究"。Quest 绕过了这个问题——它保持完整 cache，只选每个 query 该读哪些 page，所以 KV 内存还是随上下文长度增长。

（图5：eviction 后幸存者散落在各个块中，没有任何块能被回收）

## 一个系统级解决方案

突破口从一个不同的问题开始。不问"哪些 token 最近被 high attention"，问："模型的 learned representation space 几何结构能否预测 token 的重要性？"

### 解决问题1：不需要 attention scores——Pre-RoPE 几何

TriAttention 的答案是从一开始就不需要 attention scores。它从模型的 Q/K 向量空间的稳定几何特性做决策——运行时不观测任何 attention score，所以 FlashAttention 不写的东西是这方法从来不问的东西。问题1不是被绕过了，而是根本不存在。

机制依赖于模型 learned Q/K 向量在 RoPE 旋转前的稳定几何性质。（图6：步进动画）

### 解决问题2：Forward-Packing 压缩

分数本身什么也释放不了。在分页内存中，只有块中每个位置都"死"了才能还给分配器——eviction 分数只是标记，幸存者必须被物理压缩到整个块真正清空。

TriAttention 大约每 128 个解码 token 执行一次压缩。有两种方式：

**保序重排**（图7）：每个幸存者前移，cache 保持原始 token 顺序——无需额外位置记账，对 vLLM 等推理引擎的改动最小。

（图7：保序重排——幸存者前移，空洞向尾部漂移，尾部块清空回收）

**填坑式**（图8）：新 token 直接填入 eviction 产生的空洞中——每次压缩的数据移动少得多，但物理顺序被打乱，需要单独跟踪逻辑位置。

（图8：填坑式——历史幸存者不动，本轮新 token 直接填入空洞）

### 结果

下表显示竞赛数学题上的准确率（KV 压缩最关键的场景）。AIME 2024/2025 的 KV budget 是 2048 个 token（完整 32K 轨迹的 1/16），MATH500 是 512。

| Method | AIME 2024 | AIME 2025 | MATH 500 |
|--------|-----------|-----------|----------|
| Full Attention | 57.1% | 40.8% | 69.6% |
| SnapKV | 34.6% | 20.0% | 49.2% |
| R-KV | 25.4% | 17.5% | 46.4% |
| TriAttention | **42.1%** | **32.9%** | **56.0%** |

在 budget 2048 下，TriAttention 的 AIME 2025 准确率几乎是 R-KV 的两倍（32.9% vs 17.5%）。在稍大的 3072 budget 下，它匹配了 full attention 的 baseline（40.8%），同时吞吐量 2.5× 更高（563 vs 223 tokens/s），KV 内存减少 10.7×。

（图9：TriAttention vs full attention 在 AIME 2025 上的对比）

## KV Cache Infra 在视频生成中的应用

长推理的内存压力在视频生成中以更大规模重现。视频模型的 token 是空间 patch，自回归生成器为每帧缓存 KV entry，几秒 480p 视频后 cache 就超过模型权重本身 [11]。视频社区走了与文本相同两条路——量化和 token eviction——且学到了本文的核心教训：算法创意只占一半工作，魔鬼在基础设施细节里。

量化路线：Quant VideoGen [11] 把 cache 压到 2-bit/element。使能条件是视频特有的属性：相邻帧几乎相同，cache 充满了几乎重复的 token。分组存储残差（而非全精度 K/V）让数据对量化友好，渐进式精化和量化残差得到 7× 压缩，无重训练，延迟开销 < 4%。

LongLive 2.0 [13] 将同一路线推向生产规模。把权重和 KV cache 都量化到 NVFP4（4-bit），5B 参数生成器得到 1.84× 吞吐量，质量损失可忽略。其细节亮点是融合的并行反量化 kernel：4-bit 存储意味着每块在 attention 前必须反量化，naive 方法每个块启动一个 GPU kernel，但反量化本质上是 embarrassingly parallel——融合 kernel 一次启动，线程一对一映射到整个 cache 窗口的每对 FP4 值上。实践中，量化/反量化总开销低于 2%。

（图10：LongLive 2.0 的双 GPU 推理流程——NVFP4 量化 KV cache + 融合并行反量化 kernel）

eviction 路线：§3 的系统方案直接迁移——TriAttention 的三角评分已被应用到 LongLive [12]（基于 Wan2.1-T2V-1.3B 的实时视频生成器）上。每个 KV entry 对应一帧的空间 patch，评分决定哪些帧被 evict——无需观测 attention scores，与 serving 栈无冲突——将 cache 减半，质量损失可忽略。

两个领域正在收敛到相同的洞察：好的压缩主要不在于找到正确的评分启发式，而是理解信号为什么有它当前的结构——然后在 kernel 层面利用这个结构。

## 结语

从 2023 到 2025 年，领域的问题是：找到哪个 token 重要的正确启发式——heavy hitters、sinks+recency、observation windows、redundancy。所有合理的假设。但这些方法撞上了两堵墙。靠观测 attention 选 token 的方法撞上第一堵：FlashAttention 从不暴露它们需要的分数。在 decode 中反复 evict 的方法撞上第二堵：当分配器以整块为单位工作且幸存者散布各处时，eviction 不释放任何显存。过不了第二堵的方法省了计算但不省内存——长推理中更稀缺的资源。

TriAttention 通过改变问题同时推倒了这两堵墙：从模型稳定的 pre-RoPE 几何结构评分而非观测 attention，并物理压缩幸存者到密集前缀使尾部块真正被释放。结果是一个能在生产 paged-attention 部署中实际减少 KV cache 物理内存占用的方法——而且因为 pre-RoPE 几何能在任意距离预测 token 重要性（而非通过约 25 个 query 的观测窗口），它在观测窗口方法会崩溃的压缩比下仍维持了准确率。

开放问题：TriAttention 在 head 间使用统一的 KV budget，但它计算的逐 head 距离偏好曲线已经能按行为对 heads 分类——local、sink、range-specific。自然的下一步是按 head 的复杂度按比例分配 budget。pre-RoPE 洞察能否推广到更远——模型可解释性、动态稀疏 attention、其他模态——是一个值得探索的开放问题。

**参考区：**
1. TriAttention. Mao et al. ICML 2026. github.com/WeianMao/triattention
2. StreamingLLM. Xiao et al. ICLR 2024. arXiv:2309.17453
3. H2O. Zhang et al. NeurIPS 2023. arXiv:2306.14048
4. Scissorhands. Liu et al. NeurIPS 2023. arXiv:2305.17118
5. TOVA. Oren et al. EMNLP 2024. arXiv:2401.06104
6. SnapKV. Li et al. NeurIPS 2024. arXiv:2404.14469
7. PyramidKV. Cai et al. arXiv:2406.02069
8. Ada-KV. Feng et al. NeurIPS 2025. arXiv:2407.11550
9. Quest. Tang et al. ICML 2024. arXiv:2406.10774
10. R-KV. Cai et al. NeurIPS 2025. arXiv:2505.24133
11. Quant VideoGen. Xi et al. ICML 2026. arXiv:2602.02958
12. LongLive. Yang et al. ICLR 2026. arXiv:2509.22622
13. LongLive 2.0. Chen et al. arXiv:2605.18739
