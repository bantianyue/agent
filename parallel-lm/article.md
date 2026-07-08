<div style="background:#e8f4fd;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:18px;">
<div style="text-align:center;margin-bottom:10px;">
<strong style="font-size:16px;color:#1a6ba0;">要点速览</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
- <strong>核心矛盾</strong>：自回归串行解码让推理延迟随思维链线性膨胀，堆算力也压不动<br><br>
- <strong>三大创新</strong>：两阶段并行轨迹生成器、基于Trie的训练-推理协同设计、并行感知的P-GRPO<br><br>
- <strong>关键结果</strong>：Qwen3-8B上AIME24达79.9%、六基准平均71.9%，精度追平串行SOTA，token延迟最高砍掉1.53倍<br><br>
- <strong>最大价值</strong>：首个在标准vLLM/SGLang上落地、无需改引擎的自适应并行推理框架
</div>
</div>

---

## 串行解码的延迟墙

自回归逐token生成，延迟随思维链线性增长，加算力也压不动。并行推理是继拉长序列外的第二条测试时扩展路径，但此前方法要么线程各自为政造成冗余，要么要改引擎才能跑。

![](main_figure.png)
<span style="font-size:12px;color:rgb(153,153,153);">串行逐个生成token，延迟随轨迹长度增长；ThreadWeaver通过自适应spawn(◇)与join(◆)并发线程缩短关键路径</span>

## ThreadWeaver 三件事

Meta的ICML 2026 Oral论文，把强化学习训出的自适应并行推理带到Qwen3这类强推理模型上，且不动底层引擎。三个核心贡献：两阶段并行轨迹生成器提供低成本冷启动；基于Trie的训练-推理协同设计让并行直接跑在标准自回归引擎上；P-GRPO通过按线程广播优势和加速感知奖励，同时优化精度与延迟。

<div style="background:#f0f7fa;padding:16px 18px 14px 18px;border-radius:6px;margin:16px 0;border-left:4px solid #5b9bd5;"><div style="font-size:15px;color:#2c6a9e;line-height:1.7;">ThreadWeaver是第一个在标准自回归引擎上落地、且精度追平同尺寸串行SOTA的自适应并行推理框架。</div></div>

## 并行轨迹：单级分叉-汇合

限定为单级并行（多分支最终汇回主线程），既保留大部分加速收益，又把工程复杂度和数据难度压在可控范围。用轻量控制token描述结构：`<Parallel>`定义并行块，内含`<Outlines>`列出子任务、`<Thread> i`是各子任务推理过程，线程间独立生成、互不引用。

![](trajectory_format.png)
<span style="font-size:12px;color:rgb(153,153,153);">并行轨迹格式：`<Parallel>`包裹分叉-汇合块，内含`<Outlines>`与多个`<Thread>`；Thread内并发生成</span>

## 推理：极简状态机

只有`<Thread>`内部真正并行，其余仍走标准自回归解码。编排器在请求-响应对上运转：顺序解码到`</Outlines>`→为每个线程并行发补全请求→拼接继续。天然兼容前缀缓存、分页注意力，**完全不改引擎**。

![](decomposition_inference.png)
<span style="font-size:12px;color:rgb(153,153,153);">推理时请求序列：先顺序解码前缀与Outlines，再为每个线程并行发起补全，最后拼接</span>

## Trie 让训练对齐推理

把轨迹拆成"上下文-补全"单元插入token级前缀树，深度优先遍历成带祖先注意力掩码的训练序列，损失只施在补全token上。

<div style="background:#f0f7fa;padding:16px 18px 14px 18px;border-radius:6px;margin:16px 0;border-left:4px solid #5b9bd5;"><div style="font-size:15px;color:#2c6a9e;line-height:1.7;">该设计保证：直接自回归推理时整体轨迹仍是Trie遍历的合法子序列，模型退化成普通串行推理也不受损。</div></div>

![](decomposition_training.png)
<span style="font-size:12px;color:rgb(153,153,153);">Trie训练序列构造：抽取单元→插入前缀树→遍历得带祖先掩码的扁平序列</span>

## 数据：两阶段造并行轨迹

冷启动用GPT-5五步标注从5.3万条串行轨迹里恢复并行结构，得959条；再微调后跑全量rollout按格式和答案过滤，得1.7万条与模型自身生成对齐的数据。

<div style="background:#f0f7fa;padding:16px 18px 14px 18px;border-radius:6px;margin:16px 0;border-left:4px solid #5b9bd5;"><div style="font-size:15px;color:#2c6a9e;line-height:1.7;">数据质量比数量更关键：光靠959条不够，1.7万条自训练数据才是精度天花板。</div></div>

## P-GRPO：答案错了就不给加速分

奖励两项相加：正确性指示函数 + 温和的加速奖励（仅当答案正确时给，且红利压在正确性的一小块比例内）。

<div style="background:#f0f7fa;padding:16px 18px 14px 18px;border-radius:6px;margin:16px 0;border-left:4px solid #5b9bd5;"><div style="font-size:15px;color:#2c6a9e;line-height:1.7;">一条简单规则逼模型权衡精度与加速：答案错，并行再快也不给加速分，不会为提速牺牲正确性。</div></div>

关键训练坑：GRPO常规的"减均值除标准差"在多项奖励下会出问题（全对时抹掉正确性信号），改成只减均值后AIME24从74.8%跳到79.9%。

## 结果：精度没掉，延迟最多砍1.53倍

三阶段流水线（959条微调→1.7万条自训练→P-GRPO 350步）在Qwen3-8B上对比串行GRPO基线：

| 模型 | AIME24 | 六基准平均 | Token延迟 | 加速 |
|------|------|------|------|------|
| 串行RL | 78.3% | 72.2% | 15.1k | 1× |
| ThreadWeaver | 79.9% | 71.9% | 13.2k | 最高1.53× |

逐基准token延迟加速：AIME24 1.14×、AMC 1.16×、MATH500 1.23×、OlympiadBench 1.21×、Minerva 1.53×，正确样本最大加速3.56×。4卡分散线程比单卡快1.14×（真实墙钟）。

对比已有方法，8B模型精度与加速双超32B的Multiverse和4B的Parallel-R1（AIME24达79.9%，自并行加速1.25×、激活率85.2%）。

![](all_aime_32_speedup_ar_vs_pr.png)
<span style="font-size:12px;color:rgb(153,153,153);">AIME24逐题加速分布：多数题落在1.0×参考线右侧，少数接近持平，符合阿姆达尔定律</span>

<div style="background:#f5f0eb;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:16px;">
<div style="text-align:center;margin-bottom:8px;">
<strong style="font-size:15px;color:#8b6f4c;">结语</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
真正突破在于把"自适应并行推理"从需改引擎、精度掉一截的演示，做成能在标准vLLM/SGLang部署、精度还不输串行SOTA的完整配方。<br><br>
单级并行的取舍很务实：放弃任意嵌套换来了工程简单和数据可控，并行化必须结合问题结构本身。<br><br>
加速收益高度依赖题目可分解性，它改善的是"有并行结构"那类问题的前沿，不是给所有串行任务普涨提速。
</div>
</div>

---

<span style="font-size:12px;color:#888888;font-family:'Courier New',monospace;">参考：https://arxiv.org/abs/2512.07843</span>
