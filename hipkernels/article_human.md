<div style="background:#e8f4fd;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:18px;">
<div style="text-align:center;margin-bottom:10px;">
<strong style="font-size:16px;color:#1a6ba0;">要点速览</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
- <strong>合成数据驱动</strong>：Stanford SAIL Lab用mutation/composition/constraint三种模式生成了500个PyTorch参考任务，覆盖比现有基准更广泛的工作负载<br><br>
- <strong>多Agent流水线</strong>：8个专门化Agent（任务生成、翻译、正确性验证、进化优化、硬件评估等）协同工作替代单次prompt生成，每个合成任务在5次尝试内产出正确kernel<br><br>
- <strong>RL带来最大跳跃</strong>：在Qwen2.5-Coder-14B上，GRPO RL将Level 2正确率从SFT的13% 拉到60%，且所有KernelBench层级的编译通过率都有提升<br><br>
- <strong>加速仍是硬骨头</strong>：正确性提升了，但实际性能加速仍有限：模型学会了局部融合和安全优化，但未学到替换昂贵算子的深度硬件推理
</div>
</div>

---

现代AI工作负载的性能，最终都卡在kernel质量上。编写高性能kernel需要对硬件架构、底层编程语言和优化技术有足够的理解，而这类技能在NVIDIA CUDA生态之外极度稀缺。

AMD的HIP（Heterogeneous-Compute Interface for Portability）就是这种匮乏的典型。它是一种编译器验证的底层编程语言，面向AMD GPU，但开源的训练数据远少于CUDA。这种不对称直接反映在LLM的表现上：当前最好的模型能写出流畅的CUDA，但换成HIP就会开始幻觉API、发出看似合理但编译都过不了的kernel。

Stanford SAIL Lab（Scaling Intelligence Lab）的最新工作试图用合成数据、多Agent进化搜索和强化学习来填补这个缺口。他们在Qwen2.5-Coder-14B-Instruct上做了完整的SFT + GRPO训练，并在AMD MI350X GPU上用KernelBench做了系统评估。

![](img_hippo.png)
<span style="font-size:12px;color:rgb(153,153,153);">SAIL Lab的河马图：HIP Kernel生成研究的视觉标志</span>

## 方法：三条腿走路

研究团队从三个互补方向入手。

**第一，用合成数据扩展任务空间。** 他们用Gemini-2.5-Flash驱动了一个8 Agent流水线，生成了500个经过验证的HIP kernel及其PyTorch参考实现。任务生成有三种模式：Mutation（修改现有问题的计算属性，保留结构但改变算子组合）、Composition（从14个算子的模板库中随机组合新工作负载）、Constraint（直接用自然语言描述想要的运算）。

![](img_agents.png)
<span style="font-size:12px;color:rgb(153,153,153);">8个Agent协同工作的流水线架构：从任务生成到硬件评估到离线审计</span>

每个Agent各司其职：Task Generator封装合成新任务；Translator做PyTorch-to-HIP翻译，失败时带错误信息重试；Correctness Verifier跨多个seed严格验证；Evolutionary Optimizer迭代采样最快kernel；Plausibility Screener用LLM筛选候选；Hardware Evaluator在MI350X上实地跑；Archive Manager持久化所有记录并输出训练数据；Offline Auditors运行对抗性测试。

**第二，用数据微调。** 在合成语料上对Qwen2.5-Coder-14B-Instruct做了3个epoch的SFT（batch size 2，学习率2e-5）。

**第三，用RL推一把。** 采用GRPO（Group Relative Policy Optimization），每个prompt生成4个候选kernel，用TRLOO做优势估计。奖励信号直接来自MI350X硬件上的实际执行：kernel编译通过且正确性检查通过就给正奖励，幅度按PyTorch加速比缩放，上限3倍。

三个关键设计：多轮episodes（失败后可重试最多3轮）、reward smoothing（滑动窗口防异常GPU计时扭曲信号）、总结Agent（把所有Agent流水线的失败日志提炼成教训，注入RL prompt中）。

![](img_rl.png)
<span style="font-size:12px;color:rgb(153,153,153);">RL训练流程：从SFT模型出发，GRPO在MI350X上反复迭代</span>

## 编译：从瞎写到手熟

第一个评估指标是编译通过率：kernel成功编译并执行的比例。

有意思的是，baseline模型的kernel在语法上看着挺对，但编译失败的原因是更深层的理解错误：访问无效内存、用错API。Level 1的前15个问题甚至全都有残留的markdown标记，压根还没编译就先废了。

SFT之后，模型开始从训练数据中学到常见的HIP实现模式：正确的API用法、合理的kernel launch配置、正确的内存访问模式。更重要的是，模型开始对"什么应该被优化"有了判断力。

以Level 2 Problem 2为例，模型保留了昂贵的ConvTranspose算子不做修改，只把bias-add、clamp、scale、divide这些廉价操作融合进自定义kernel。Level 2 Problem 7的做法类似：把ReLU、LeakyReLU、GELU、Sigmoid和bias-add融成单次pass。策略高度一致：保留核心计算，优化周边。

但也有反例。Level 2 Problem 3试图用自定义kernel重写ConvTranspose3D、LayerNorm、AvgPool3D和GELU的全部，结果forward方法写到一半没写完，候选kernel直接作废。

RL进一步强化了SFT中成功的模式：不是发现全新的优化技术，而是让模型学会哪些修改是安全的。成功的RL生成越来越倾向于融合局部操作（激活函数、bias加算），同时保留整体计算结构。结果是在所有三个KernelBench层级上，编译通过率都有提升。

![](img_Figure_1.png)
<span style="font-size:12px;color:rgb(153,153,153);">编译通过率对比：baseline → SFT → GRPO，三个层级均有提升</span>

## 正确性：RL的亮眼表现

第二个指标是正确率：kernel既编译通过、输出也与PyTorch参考一致的占比。

最亮眼的数据来自Level 2：SFT下正确率只有13%，RL直接拉到60%。原因在于Level 2任务围绕简单的算子融合机会构建。Level 1是逐个实现算子，Level 3要保留整个模型的行为，Level 2恰好处在"有明确的融合机会"的位置。

SFT之后模型虽然学到了局部融合模式，但经常用错。一个反复出现的失败模式是修改了超出必要的计算逻辑。比如Level 2 Problem 4，kernel正确识别了融合机会，但在这个不该动的地方多实现了一个卷积。RL直接惩罚了这类错误：因为奖励信号包含正确性检查。

但Level 3仍然困难。以Vision Transformer为例，生成的kernel正确完成了patch提取阶段，但完全跳过了从raw patch到learned embedding的变换，直接把原始像素值送进了Transformer。这种失败和baseline的语法/API错误完全不同，更深层。

另一个Level 3的常见问题是参数重新初始化。多个问题里生成的kernel用了 `self.weight = nn.Parameter(torch.randn(...))`：结构看起来没错，但用完全不同的权重算不出正确结果。

![](img_Figure_2.png)
<span style="font-size:12px;color:rgb(153,153,153);">正确率对比：Level 2从13% 跃升至60%</span>

### 模型学了哪些优化模式？

跨所有实验，研究团队观察到了几种反复出现的GPU优化模式：

- **算子融合**：最常见。把激活函数、bias加算、scale、normalization等逐元素操作链融合到一个HIP kernel里，减少kernel launch开销和中间张量
- **共享内存归约**：多个softmax和normalization kernel分配了共享内存，跨线程累积部分结果再用同步原语做归约
- **分块矩阵乘法**：一些GEMM kernel把输出分块，加载数据到共享内存，累积部分乘积后写回最终结果
- **选择性优化**：不是替换昂贵的卷积或矩阵乘法，而是聚焦在简单的周边操作上，保留核心计算不变

## 性能：最难啃的骨头

编译和正确率都上去了，但实际的性能加速仍然有限。

最强的结果在Level 2：约60% 的正确kernel匹配了PyTorch的基线性能，超过一半的kernel实现了至少0.5倍的加速。但能实现更大加速的kernel比例急剧下降：没有一个kernel实现了大幅度的性能提升。

这和模型的表现完全一致。SFT和RL学到的是局部优化策略：融合周边逐元素计算改善了正确性、减少了开销，但工作负载的主要计算成本仍然在PyTorch里。替换昂贵的算子需要更深的硬件推理，而模型还没有学会。

![](img_Figure_3.png)
<span style="font-size:12px;color:rgb(153,153,153);">性能结果：正确kernel中达到各加速比阈值的比例</span>

![](img_Figure_4.png)
<span style="font-size:12px;color:rgb(153,153,153);">各KernelBench层级上加速比的分布</span>

## 与已有工作的比较

HIP kernel生成领域目前还没有被广泛采纳的基准。AMD近期的工作在自己的24个任务上做了评估，KernelArena在41个问题的KernelBench-HIP子集上用Opus 4.5实现了中位1.37倍加速。但这些工作使用不同的基准规模、不同的GPU，且依赖昂贵的frontier模型，和本文的小模型+合成数据路线不可直接比较。

<div style="background:#f5f0eb;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:16px;">
<div style="text-align:center;margin-bottom:8px;">
<strong style="font-size:15px;color:#8b6f4c;">结语</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
这篇工作在技术上最值得关注的点不是编译通过率或正确率的数字，而是它揭示了一个事实：<strong>合成数据+小模型+RL可以在某个领域的代码生成上做出有意义的提升，但代价是数据生成本身需要强大的Agent流水线</strong>。500个合成任务背后是8个Agent的多次迭代和GPU硬件上的实地评估：这个infra成本本身就不低。<br><br>
另一个耐人寻味的观察是"正确性提升但性能没跟上"。这其实是很多RL for code工作的缩影：RL善于教会模型"不犯错"，但很难教会"想得更深"。要替换一个ConvTranspose算子，模型需要的不只是安全策略，而是对计算图代价模型的推理能力：那完全是另一层挑战了。<br><br>
如果未来能像作者说的那样把ROCm profiler信号直接注入奖励，让模型不仅知道"这次编译通过了"，还知道"这次cache miss太多了"：那时候的加速效果可能会完全不一样。
</div>
</div>

---

<span style="font-size:14px;color:#888888;font-family:'Courier New',monospace;">【传送门】<br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/qcIFzXsBalSGpca5fzJKxg" target="_blank" data-linktype="2">Claude Code动态Workflow Vs. SubAgent Vs. Skill</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/aiJs5CC8Gb6qa_xDRNEjTA" target="_blank" data-linktype="2">Dynamic Subagents：用代码编排Agents，告别逐轮工具调用</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/mFuUJ79DRodIK6shVWOgpw" target="_blank" data-linktype="2">OpenAI GPT-5.6: 安全之外新增Prompt Cache断点+两种推理模式; 放弃版本号</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/xP1cEoO_plRpWItxhqeQnQ" target="_blank" data-linktype="2">Agent Harness Engineering：为什么Agent可靠性的天花板不是模型，而是基础设施</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/o6pnSWW01pahFQelJSbSPA" target="_blank" data-linktype="2">华为「韬定律」全解析：从 τ 常数到4GHz麒麟</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/PLNx54PxO1A0oYc47hz99g" target="_blank" data-linktype="2">Anthropic三连：Claude Opus 4.8-更聪明+诚实；CC动态工作流+算力控制</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/Pdjz39WG9SS6IpWWAJ6pPw" target="_blank" data-linktype="2">Claude Opus 4.8击败Opus 4.7、GPT-5.5和Gemini 3.1 P</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/oDZJbvskv_ocNgPUH1DHVA" target="_blank" data-linktype="2">AI暗输出：为何AI价值在GDP统计中失效了</a></span>

---

<span style="font-size:12px;color:#888888;font-family:'Courier New',monospace;">参考：https://scalingintelligence.stanford.edu/blogs/hipkernels</span>
