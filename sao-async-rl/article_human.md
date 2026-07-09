<div style="background:#e8f4fd;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:18px;">
<div style="text-align:center;margin-bottom:10px;">
<strong style="font-size:16px;color:#1a6ba0;">要点速览</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
- <strong>核心矛盾</strong>：同步RL必须等整批rollout收齐才训练，长程智能体任务里慢轨迹拖垮整批GPU，吞吐被最慢样本卡死。<br><br>
- <strong>SAO做法</strong>：每个prompt只采一条轨迹，生成完立刻送训练（单轨迹异步），砍掉GRPO组采样强制等待最慢样本的同步屏障。<br><br>
- <strong>代价与解法</strong>：单轨迹方差大、易离策略，靠三类设计稳压：更直接的重要性采样裁剪、比策略更快更新的价值模型、跳过环境观测的GAE。<br><br>
- <strong>结果</strong>：稳定训练约1000步（vanilla GRPO约160步就崩），Qwen3-30B上AIME2025 97.3、SWE-Bench 29.8，已落地训练GLM-5.2（750B-A40B）。
</div>
</div>

---

## 为什么同步RL在智能体任务上浪费算力

LLM后训练大多还走同步流水线：策略先生成一整批rollout，等全部收齐才开始优化。对数学推理这类短输出没问题，但对智能体编程、工具调用这类长程任务，rollout长度高度不均：短的几秒结束，长的跑几百轮交互，成为掉队者（straggler）。结果就是**大量GPU在等最慢的那条轨迹**，墙钟效率被拖死。

异步RL的思路是：rollout一边生成一边喂给训练，不用等整批。但异步带来两个老问题：一是每条轨迹可能由多个版本的旧策略生成，离策略（off-policy）更严重；二是GRPO这类组采样天然与异步冲突：它要对每个prompt采一组响应、用组内平均算优势，整组必须等最慢样本完成才能进训练，等于在异步里又造了一道同步屏障。

SAO（Single-rollout Asynchronous Optimization）的出发点很直接：**把组采样换成单轨迹采样，样本一生成就立刻训练**，从根上消除这道时延屏障。

![](img1.png)
<span style="font-size:12px;color:rgb(153,153,153);">SAO论文teaser图（Figure 1）</span>

## 单轨迹怎么稳住

异步下不能简单地"来一条训一条"就完事，离策略和方差会冲垮训练。SAO用四块设计兜底。

**直接双侧重要性采样（DIS）。** 异步里rollout引擎在一条轨迹生成期间可能已被更新多次，精确追踪旧策略概率需要存一堆历史检查点，不现实。SAO的做法粗暴而有效：直接用rollout阶段留下的log概率当行为策略，跟当前策略算比值，丢掉那个不准确的旧策略。信任域收紧到 [1-ε_ℓ, 1+ε_h]，落在区间外的token直接从梯度里掩码掉。这等于用受控的离策略偏差，换来不用维护历史模型集合的巨大计算节省，还能做更激进的裁剪。

**比策略更快更新的价值模型（TTUR）。** 单轨迹梯度方差高（类似REINFORCE），必须有个够好的价值模型压方差。SAO解耦策略和价值的学习频率：每对策略做1次更新，就对价值网络做K=2次更新，让价值估计先跟上策略再算优势。

**冻结注意力的价值模型训练。** 实验发现价值模型梯度范数远大于策略，且不稳定主要来自全注意力层（MoE层反而稳）。于是RL训练中冻结价值模型的注意力参数，只优化MoE投影：预训练注意力已够用，限制优化范围就顺带正则化了critic。

**跳过观测的token级GAE。** 智能体轨迹是 [动作, 观测, 动作, 观测...]，模型不生成观测。标准GAE跨"动作末尾→观测开头"算价值差会把环境噪声带进来。SAO改Bellman目标，绕过环境反馈token，把当前动作价值直接连到下一动作价值，优势估计只依赖模型自身输出。

![](img2.png)
<span style="font-size:12px;color:rgb(153,153,153);">SAO整体设计（Figure 2）：rollout到达即训练，单轨迹 + DIS + 强价值模型</span>

## 稳定性能拉到多少步

这是时延叙事里最关键的一组证据。vanilla GRPO在约 **160步**就性能崩塌；加上DIS能稳住；SAO与GRPO+DIS初期，约400步后明显拉开，最终稳定跑满约 **1000步**。

![](img3.png)
<span style="font-size:12px;color:rgb(153,153,153);">训练步数上的评测表现：GRPO早期崩，SAO持续稳定上升（Figure 3）</span>

训练动态进一步解释为什么稳：SAO的Explained Variance（价值预测与真实回报的对齐度）在约400步后显著高于只更新1次critic的基线，价值收敛更快；冻结注意力的critic梯度范数更低更平滑；而VAPO几乎不裁剪离策略token，约90步就崩。

![](img7.png)
<span style="font-size:12px;color:rgb(153,153,153);">训练动态：解释方差、critic梯度范数、裁剪token占比（Figure 4）</span>

## 跑分：不只是稳，还更强

在Qwen3-30B-A3B上（batch 128、group size 1、max-length 128k、token裁剪 ε_low=0.3/ε_high=5.0）：

| 方法 | AIME2025 | BeyondAIME | HMMT | IMOAnswer |
| --- | --- | --- | --- | --- |
| GRPO (w/ python) | 84.2 | 54.8 | 76.0 | 55.8 |
| SAO (ours) | 97.3 | 74.8 | 88.3 | 74.0 |

SWE-Bench Verified（编程智能体）准确率：GRPO+DIS为27.0%，SAO为 **29.8%**。消融显示每块都必要：去掉冻结注意力掉到90.6（AIME2025），只更新1次critic掉到95.0，用running-mean基线只剩79.8。

## 在线学习里单轨迹的额外红利

真实在线环境往往每个prompt只给一条轨迹反馈，GRPO的组相对优势天生用不了。SAO用基于价值模型critic的优势估计，能从单条轨迹有效更新。模拟在线写作任务里奖励偏好在cute→中二→古典间切换，SAO每次切换后迅速重新对齐策略，而running-mean基线因滑动窗口惯性适应滞后。

![](img9.png)
<span style="font-size:12px;color:rgb(153,153,153);">在线学习模拟：风格偏好切换后SAO快速恢复（Figure 5）</span>

## 落地

SAO已用于训练开源GLM-5.2（750B-A40B）的智能体RL流水线，证明这套异步单轨迹方案在大规模真实训练里站得住。

<div style="background:#f5f0eb;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:16px;">
<div style="text-align:center;margin-bottom:8px;">
<strong style="font-size:15px;color:#8b6f4c;">结语</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
异步RL的瓶颈从来不是"不够快"，而是"快了就崩"。SAO的价值在于证明：只要把组采样的同步屏障拆掉、并用更狠的裁剪和更强的价值模型兜底，单轨迹异步既能吃掉长程任务里的掉队者空闲，又能比GRPO训得更稳更准。<br><br>
它和AReaL、ROLL Flash这些异步系统的分工很清楚：那些工作主攻系统解耦（rollout与训练并行），SAO主攻算法层稳定（单轨迹下的离策略与方差），两者是正交的可叠加项。<br><br>
真正的工程代价在基础设施：SAO依赖可靠保留token级行为概率的异步生成链路，这对部署提出了比同步RL更高的要求。
</div>
</div>

---

<span style="font-size:14px;color:#888888;font-family:'Courier New',monospace;">【传送门】<br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/s0Ovn3_tnbbl9jxfAC3WLg" target="_blank" data-linktype="2">阿里Sparse Attention on CXL替代RDMA做KV Cache解耦 推理2.1×吞吐, 9.7×TTFT</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/2eWh5jZJPHsv0wi9km2nVg" target="_blank" data-linktype="2">NVIDIA TriAttention解读: KV Cache压缩最大的问题不是算法而是两个Infra</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/FTsibdpbEjvoPWtxGqgxkQ" target="_blank" data-linktype="2">小米MiMo罗福莉后训练新范式MOPD: 多教师同策略蒸馏，多领域无损</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/nVqW9acA7NN1zeALDwRAsw" target="_blank" data-linktype="2">Google新论文RubricEM: 评分标准引导的深度研究Agent训练框架</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/OoHu1yeuh1gzgCfEiPvDuQ" target="_blank" data-linktype="2">RL的下一个大突破：不是优化可验证问题而是把'不可验证'领域变</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/HnGKVp45C-GApBJ-LleP6g" target="_blank" data-linktype="2">小米MiMo罗福莉:8卡GPU让1T参数模型跑出1000 TPS , FP4+DFlash+TileRT全解</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/3btXHAVd8_x5CM5CWETc2g" target="_blank" data-linktype="2">Agent卷向AI Infra: SGLang团队用硬核Agent优化框架和CUDA Kernal性能</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/OqtF6ZaWQNu3o-VAWLfqbg" target="_blank" data-linktype="2">榨干GPU性能：流水线解码消除GPU气泡，推理吞吐提升35%</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/IZBsLB7ci7U8ZmrpkFuB0Q" target="_blank" data-linktype="2">梁文峰署名DeepSeek DSpark：半自回归推测解码，吞吐提升51% (附论文</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/kJHYTWqIl2HwdUYNjG7_aw" target="_blank" data-linktype="2">Loop工程续篇：15个高赞Loop一次性拆解：每一条你都能直接用</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/zAW0cPIvTYkAAAu0ryNm0w" target="_blank" data-linktype="2">5个最好用的OpenClaw Skills</a><br>
</span>

---

<span style="font-size:12px;color:#888888;font-family:'Courier New',monospace;">参考：https://arxiv.org/html/2607.07508v1</span>
