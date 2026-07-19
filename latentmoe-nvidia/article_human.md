要点速览

- 核心思路：token 先投影到低维潜空间 ℓ 再做专家路由，通信量与权重加载成本同降 α=d/ℓ 倍。- 不降精度：压缩 d 的同时把专家数 N、top-k 放大同倍 α，有效非线性预算 K·m 原样保留。- 两种配置：ℓ-MoE-eff 保精度降开销；ℓ-MoE-acc 在等成本下精度更高（推荐）。- 关键结果：95B/混合模型上全面优于标准 MoE，万亿参数投影下省约 350B 参数（注：万亿级为模拟器投影，非实测 benchmark）。- 已落地：架构被 Nemotron-3 Super/Ultra 采用并扩展。

混合专家（MoE）已是顶级大模型的标配，但它离「推理成本最优」究竟还有多远，业界一直没说清。
NVIDIA 这篇技术报告从软硬件协同设计出发，给出系统答案：LatentMoE。

一、为什么现有 MoE 没到最优
MoE 能在每 token 浮点运算数不变的前提下扩大参数量，但真正成本有两个互补维度：每 FLOP 精度（算得快不快）与每参数精度（占内存多不多）。低时延场景受显存带宽限制，吞吐场景受全互联通信限制。
作者以 Qwen3-235B-A22B 在 GB200 上建模：当算术强度低于 1250 FLOPs/字节时，专家计算落在 roofline 的显存受限区，性能卡在权重加载而非算力；而在吞吐场景，通信时间与计算时间之比高达约 9，全互联通信成为绝对主导。
关键结论：现有 MoE 主要面向离线吞吐优化，忽视了在线部署的时延、带宽、通信约束，导致「总算力看着高效、实际部署却很低效」。

Qwen3-235B-A22B 服务的 Roofline 分析。运行点对应不同的每专家 token 数 t_exp（即 MoE 路由后的有效专家批大小），映射到算术强度 I = 2·t_exp·d·m / (d·m + t_exp·(d+m))。在时延敏感的批大小（低 I）下，MoE 专家计算受 HBM 带宽而非算力约束，运行点落在带宽受限区。

Comparison between LatentMoE variants. Training trajectories for the baseline 16BT-2BA model versus the $\ell$-MoE-eff and $\ell$-MoE-acc ($\ell=512$). $\ell$-MoE-eff matches baseline convergence, while $\ell$-MoE-acc outperforms the baseline.

95B Model Training Convergence. Validation loss curves for the 95BT-8BA baseline, $\ell$-MoE-eff, and $\ell$-MoE-acc configurations ($\ell=1024, \alpha=4$). $\ell$-MoE-eff matches baseline convergence, while $\ell$-MoE-acc outperforms the baseline.

LatentMoE 变体对比。基线 16BT-2BA 模型与 ℓ-MoE-eff、ℓ-MoE-acc（ℓ=512）的训练轨迹。ℓ-MoE-eff 匹配基线收敛，ℓ-MoE-acc 优于基线。
二、五条设计原则
为搞清楚该压什么、保什么，作者推导出五条原则，全部围绕一个核心约束：有效非线性预算 K·m 不能动（它决定模型表达能力）。

标准 MoE 与 LatentMoE 架构对比。在 LatentMoE 中，token 从模型隐藏维度 d 投影到更小的潜维度 ℓ 做专家路由与计算，使路由参数量与全互联流量都降低 d/ℓ 倍；用省下的效率把专家总数与每 token 的 top-k 都放大同样的倍数 d/ℓ，在整体推理成本近似不变的同时提升精度。
原则 I：低时延场景推理成本由权重加载的显存带宽主导，每参数精度最关键。原则 II：吞吐场景要最小化全互联通信量，它正比于 (N/EP)·t_exp·d，降路由维度 d 或激活数 K 才有效（中间维度 m 不影响 token 大小，改它没用）。
原则 III：保质量必须保住 K·m，不能降 K 或 m。原则 IV：隐藏维度 d 不能无限压，存在任务相关下界 r_eff（特征秩），压到其下质量会崩塌。原则 V：同时放大专家数 N 与 top-k K，组合空间 C(αN, αK) 指数级扩张，质量随之提升。
把原则串起来：通信与显存都随 K、d 线性缩放，但 K、m 不能降，于是唯一可压的维度是 d。只要把 d 缩小 α 倍、同时把 K 放大 α 倍（保证 d/α ≥ r_eff），就能在成本不变的前提下提升表达力与组合稀疏性，这正是 LatentMoE 的出发点。
三、LatentMoE 架构：潜空间专家
LatentMoE 的做法很直接：每个输入 token x（维度 d）先经可学习下投影 W_↓ 压到潜空间 ℓ，在潜空间里做专家路由与计算，最后用上投影 W_↑ 投回原维度 d。只有输入维度 d→ℓ 被压缩，专家内部宽度 m 不变，所以有效非线性预算 K·m 原样保留。
路由专家完全在潜空间工作（权重形状 m×ℓ、ℓ×m），共享专家仍在原维度 d。由于 token 分发与聚合都在潜空间 R^ℓ 进行，通信量相对标准 MoE 缩减 α 倍，权重加载的显存带宽成本也缩减 α 倍。
两种配置：ℓ-MoE-eff = 保持专家数 N、top-k K 不变，纯粹降开销、保基线精度；ℓ-MoE-acc（推荐）= 把 N、K 同时放大 α 倍，通信与显存带宽相对标准 MoE 不变，但专家多样性更高，等成本下精度更优，把帕累托前沿推到新高度。
四、关键实验结果
在 16B 上对比两种变体：ℓ-MoE-eff 收敛匹配基线，ℓ-MoE-acc 验证损失明显更低，作者推荐后者作为精度–成本帕累托最优。
扩到 95B 总参/8B 激活（α=4，ℓ=1024）：趋势一致。300B token 时下游精度如下表——ℓ-MoE-acc 在 MMLU Pro、MMLU、代码、数学、常识全维度超越基线，且总参仅多 0.4B；ℓ-MoE-eff 激活参数降到 5.62B，精度仍与基线相当或更好。
混合 Mamba-Attention MoE（73B 总参/8B 激活）在 1T token 上同样成立：ℓ-MoE-acc 各任务全面领先基线（MMLU Pro 48.30→52.87，数学 78.32→80.19）。
推理性能上，Hybrid-73B 模型在两块 H100、vLLM FP8 下实测：高并发时每 GPU 吞吐仅比标准 MoE 低至多 6%；作者指出可用独立 CUDA 流、专用小矩阵 GEMM 算子进一步弥合。
万亿参数投影：以 Kimi-K2-1T 为基准，LatentMoE 变体的有效参数乘数 λ≈1.35×。要达同等精度，标准 MoE 需扩到约 1.35T（多约 350B 参数），在投影帕累托前沿上慢 1.24×–3.46×；而潜投影自身开销很小（与原生差距在 9% 以内）。

结语

LatentMoE 的本质是一招「腾挪」：把隐藏维度 d 压进潜空间省下的通信与带宽，全数再投回「多专家+高 top-k」，在不涨推理成本的前提下把表达力与组合多样性做厚。它击中了现有 MoE 的真正瓶颈：不是算力，而是显存带宽与全互联通信，因此同时在低时延与高吞吐两种场景都成立，并已落地 Nemotron-3 旗舰模型。对工程侧的启示很直接：扩大 MoE 规模前，先问「d 能不能压、N/K 能不能换」，往往比单纯堆参数更划算。回看全文，真正的性价比拐点可能不在「更大」，而在「更会压维度、更会换专家」。

参考：https://arxiv.org/src/2601.18089