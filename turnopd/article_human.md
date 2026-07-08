<div style="background:#e8f4fd;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:18px;">
<div style="text-align:center;margin-bottom:10px;">
<strong style="font-size:16px;color:#1a6ba0;">要点速览</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
- <strong>问题</strong>：在线策略蒸馏（OPD）用于长程智能体时效率极低，算力和梯度都被浪费在浅层回合和低信号尾部回合上。<br><br>
- <strong>诊断</strong>：原始OPD存在两道错配，反向KL信号严重前载，最深的第三个回合只分到3.6%–4.5% 的KL损失；深层KL还会因「污染—压缩」机制失去判别力。<br><br>
- <strong>方法</strong>：TurnOPD用两个预算控制器，自适应截断rollout深度，并把KL损失从token级逐步转向回合均衡监督。<br><br>
- <strong>结果</strong>：在ALFWorld、WebShop、Multi-Hop Search上，同等时钟预算下准确率全面占优，训练最高提速2.29倍（4.42h→1.93h）。
</div>
</div>

---

## 引言与背景

语言模型正越来越多地作为Agent部署，承担规划、工具调用和环境交互。在线策略蒸馏（OPD）给这类Agent提供了一套有前景的训练框架：学生自己采样rollout，更强的教师（Teacher）在被访问的状态上用反向KL目标逐token监督，监督始终保持在策略上（on-policy），且反馈密集，避开了稀疏奖励。

但把OPD直接搬到长程多回合任务上会出问题。一次rollout不是一段扁平文本，而是跨多个回合、带环境状态变化的交互轨迹：早期决策影响后续所有状态，靠后的回合往往藏着关键但稀少的决策。仅靠token级反馈，无法为所有决策点提供恰当的监督。

本文的核心判断是：**长程Agent的OPD里，监督的单位不应该是扁平的token位置，而是演化中的交互轨迹里、由回合（turn）所条件的决策。**

![](TurnOPD_introduction.png)
<span style="font-size:12px;color:rgb(153,153,153);">TurnOPD的核心视角：标准OPD固定rollout深度、在整条轨迹上平均KL，常把算力浪费在低价值的尾部回合，并把损失压在浅层token上；TurnOPD基于回合级统计同时预算rollout深度与KL聚合。</span>

论文在ALFWorld、WebShop、Multi-Hop Search三个基准上验证了这一点，学生从任务专用的GRPO教师蒸馏而来。TurnOPD在ALFWorld-1.7B上把100步训练时钟从4.42小时砍到1.93小时，同时把Same-Step Avg@4从83.0提到86.3，最高训练提速2.29倍。

## 相关工作

在线策略蒸馏的早期方案MiniLLM、GKD面向通用LLM文本生成，后续工作把它视作KL约束的策略优化，并引入稳定目标分布、教师熵、放松模仿约束等技巧。诊断类研究已指出长轨迹上的密集监督不可靠，TCOD引入轨迹长度课程、SOD在步骤级对工具推理重加权，都说明「面向Agent的OPD需要的远不止一个扁平序列目标」。

长程Agent基准本身也已从受控环境走向真实计算机使用：ALFWorld连接文本规划与具身环境，WebShop研究接地电商导航，再到Mind2Web、WebArena、OSWorld、SWE-bench、BrowseComp等。它们的共同结构是一条有状态、跨回合变化的交互轨迹，而非单条回复。

## 预备：多回合OPD

一个学生Agent与环境多回合交互。回合t观测o_t，以完整历史为条件生成响应r_t（含推理与工具参数），环境再把可执行部分映射为下一观测o_{t+1}。一条rollout是直到任务完成或到达最大视野为止的交互轨迹。

OPD下，学生为提示x采样自身rollout，冻结的教师 π_T在学生访问过的前缀上做token级监督。这区别于离线蒸馏：教师是在当前学生诱导出的历史上查询，而非仅在教师自己生成的演示上。目标用反向KL：

L_OPD(θ) = E_{x,τ}[ (1/Σ_i m_i) Σ_i m_i · KL( π_θ(·|s_i) ‖ π_T(·|s_i) ) ]

其中s_i是token i之前的完整前缀（含历史观测、学生响应与当前部分响应）。

## 诊断：监督信号在回合轴上的错配

长程OPD表面是序列上的教师匹配损失，实则是交互轨迹上的优化。作者从三个角度拆解了「监督到底落在哪、多可靠、拿走了多少预算」。

**原始回合级KL严重前载。** 在ALFWorld（Qwen3-4B学生 / Qwen3-8B-GRPO教师）和Multi-Hop Search（Qwen3.5-2B学生 / Qwen3.5-9B-GRPO教师）上跑100步原始OPD，逐回合看平均反向KL：早期回合起始KL很大，前20–30步内快速下降，长尾后期回合更低更噪。单一平均KL完全无法刻画这种非平稳、依赖任务的结构。

![](fig_vanilla_opd_per_turn_kl_alfworld4b_multihop_diagnosis.png)
<span style="font-size:12px;color:rgb(153,153,153);">左：逐回合平滑教师熵；中：逐回合平滑反向KL；右：原始逐回合反向KL热力图。ALFWorld行用Qwen3-4B学生，Multi-Hop Search行用Qwen3.5-2B学生。信号明显前载且随训练变化。</span>

**深层KL失去结果判别力。** 定义G_t = K_t^fail − K_t^succ（失败轨迹与成功轨迹在该回合的平均KL之差）。直观上失败rollout应需要更多纠错，G_t应为正。但ALFWorld上G_t大多为负且随深度递减：成功轨迹反而有更高KL，因为失败轨迹很快陷入循环或模板化模式，两个模型都觉得下一token很平凡，人为压低了KL；成功轨迹遍历更多样状态，教师的纠错更少被压缩。Multi-Hop Search上G_t符号正确，但分离力集中在早期，深度越大越弱。

![](success_failure_gap.png)
<span style="font-size:12px;color:rgb(153,153,153);">反向KL按回合的结果分离力。正值表示失败轨迹KL更大。ALFWorld上深层G_t转负，说明深层KL不是干净的成果预测信号。</span>

**「污染—压缩」机制。** 作者用一个分解解释上述歧义：在回合t的上下文c下，下一token分布有一部分被上下文强制决定（重复串、格式约束、复制实体、闭合分隔符等），记为共享的强制组件p_F，剩余是师生可能真正分歧的自由组件。可证：

KL(π_S ‖ π_T) ≤ (1−λ(c)) · KL(p_S^free ‖ p_T^free)

即原始KL捕捉到的自由分歧比例 ρ(c) ≤ 1−λ(c)。随着rollout变长，自回归正自条件让强制质量 λ(c) 增大，测得的KL衰减可能只是「压缩」加剧，而非策略分歧真的消失。失败轨迹的刻板模式使其 λ 系统性高于成功轨迹（λ_t^fail > λ_t^succ），这解释了为何G_t会转负并随深度单调下行。

**损失预算集中在浅层。** 轨迹级归约给每个token相同权重，但实现的KL损失质量份额由token数和该处KL共同决定。结果在ALFWorld-4B上，仅回合0就吃掉约四分之一KL预算，前三个回合近一半，最深的第三个只分到3.6%–4.5%；Multi-Hop Search上前三个回合占38%–40%，深层第三个仅11%–13%。

![](fig_loss_share_turn_lines_alfworld4b_multihop_baseline.png)
<span style="font-size:12px;color:rgb(153,153,153);">轨迹级KL目标下逐回合的KL损失份额。左为逐回合平滑曲线，右为原始step×turn损失份额热力图。损失高度集中在早期回合。</span>

由此引出两个错配：**外部错配**，固定rollout深度忽略了纠错信号和存活数量随回合剧变，把算力浪费在信号不可靠的深处；**内部错配**，轨迹级归一化把KL压在简单浅层回合，让深层有信息量的决策挨饿。

## 方法：TurnOPD

TurnOPD用两个预算控制器分别应对两道错配：一个自适应预算rollout深度（管「收集多少交互」），一个渐进式把KL损失从轨迹级转向回合均衡（管「在已收集token上怎么分配监督」）。

**自适应rollout深度预算。** 存在一个不可观测的最优视野H*（过浅探索不足、过深浪费算力），TurnOPD用两个互补信号在线估计它：H_ctrl = max(H_eff, H_cov)。

效率臂H_eff把跨回合的反向KL视为存活者加权的蒸馏质量分布：m_t = [K_t]_+ · (n_t/n_0)，q_t = m_t / Σ_j m_j，H_eff = round(Σ_t t·q_t)。它自适应响应，监督质量集中在浅层时保持浅、纠正确实尾巴延伸到深层时自动加深。

覆盖臂H_cov防止过度截断，取成功条件完成深度的p分位数（p=0.80），保证rollout至少覆盖80% 的成功轨迹。控制器是因果的：用周期性全长度探针rollout更新这两个统计量（被截断的rollout不计入深度估计，否则会偏置），常规训练步只用当前上限Ĥ_k，再经指数滑动平均平滑得到下一回合实际深度。

**渐进式回合归一化损失预算。** 标准轨迹级权重q_t^traj = n_t/Σ_j n_j，均匀回合级权重q_t^turn = 1/T，最终权重取线性插值：

q_t^blend = (1−α) q_t^traj + α q_t^turn

混合系数 α 绑定到归一化训练进度（progress = k/K）。初期 α=0，损失跟随token质量保证稳定；随训练推进 α 增大，监督平滑转移到更平等地覆盖所有回合，专治后期深层决策欠训练。

## 实验与结果

在ALFWorld、WebShop、Multi-Hop Search上，用三对师生（ALFWorld：Qwen3-1.7B/4B学生 + Qwen3-8B-GRPO；WebShop：Qwen3-1.7B + Qwen3-8B-GRPO；Multi-Hop Search：Qwen3.5-2B + Qwen3.5-9B-GRPO）对比原始OPD、TCOD-F2B与TurnOPD，在最少时间（Least-Time）与同一步（Same-Step）两种机制下评估。

![](iso_time_efficiency.png)
<span style="font-size:12px;color:rgb(153,153,153);">主结果等时效率曲线。横轴为累计训练时间，TurnOPD在每类任务上都把准确率—时间前沿向外推。</span>

**准确率与效率双优。** 最少时间设定下，TurnOPD在所有任务与模型组合上拿到最高的整体Avg@4；同一步设定下也大多匹配或超越最佳基线。在ALFWorld-1.7B上达到86.29（原始OPD 83.00、TCOD-F2B 80.06）；Multi-Hop Search上原始OPD在同一步有微弱优势，但TurnOPD的最少时间准确率最佳。训练时间上，ALFWorld-1.7B从4.42h降到1.93h，Multi-Hop Search 2.94h vs 4.45h，WebShop 1.24h vs 1.57h。

| 任务 / 学生 | 方法 | Least-Time Avg@4 | Same-Step Avg@4 | Same-Step 时钟(h) | 加速比 |
|------|------|------|------|------|------|
| ALFWorld / 1.7B | Vanilla OPD | 73.52 | 83.00 | 4.42 | 1.00× |
| ALFWorld / 1.7B | TCOD-F2B | 80.06 | 80.06 | 1.87 | 2.37× |
| ALFWorld / 1.7B | TurnOPD | **85.60** | **86.29** | **1.93** | **2.29×** |
| ALFWorld / 4B | Vanilla OPD | 90.79 | 91.81 | 2.86 | 1.00× |
| ALFWorld / 4B | TurnOPD | **91.73** | **92.21** | **2.16** | **1.33×** |
| Multi-Hop / 2B | Vanilla OPD | 45.77 | 47.82 | 4.45 | 1.00× |
| Multi-Hop / 2B | TurnOPD | **47.24** | 47.24 | **2.94** | **1.51×** |
| WebShop / 1.7B | Vanilla OPD | 76.98 | 81.65 | 1.57 | 1.00× |
| WebShop / 1.7B | TurnOPD | **82.80** | **82.80** | **1.24** | **1.26×** |

值得注意的是，在Qwen3-4B学生下，TurnOPD的整体Avg@4甚至超过了ALFWorld的教师参考（90.75）。

**控制器确实在按诊断信号工作。** 回放H_eff（效率臂）与H_cov（覆盖臂）的动态：ALFWorld上一旦成功轨迹出现，覆盖约束迅速主导、鼓励更长的rollout；WebShop始终保持适度覆盖下界；Multi-Hop Search上两臂之间动态转移。H_eff保证非平凡效率，H_cov阻止控制器选过短、覆盖不足的rollout。

![](horizon.png)
<span style="font-size:12px;color:rgb(153,153,153);">rollout深度诊断回放：存活者加权KL质心H_eff、成功覆盖下界H_cov，以及取二者最大值的EMA视野Ĥ。三者随训练步自适应变化。</span>

## 消融分析

在ALFWorld-1.7B上拆开两个控制器，看清各自的分工。

**组件分解。** 仅自适应深度（保持轨迹级KL）把时钟从4.42h砍到1.96h，但准确率略降到82.8，说明缩短深度本身不解决损失分配问题；仅线性KL混合（保持全视野）把准确率提到85.1，但耗时2.59h，说明它直接改善了优化却没省算力。完整TurnOPD二者结合，拿到最佳准确率86.3，同时匹配自适应深度的低时钟1.93h，并在训练中期进度更快。

![](component_ablation.png)
<span style="font-size:12px;color:rgb(153,153,153);">ALFWorld-1.7B组件消融（左）与干预分解表（右）。自适应深度提供效率杠杆，线性KL混合提供优化杠杆，组合给出最佳准确率—时间权衡。</span>

| 配置 | 深度预算 | KL 混合 | Avg@4 | 时钟(h) |
|------|------|------|------|------|
| Vanilla OPD |  |  | 83.0 | 4.42 |
| + 自适应深度 | ✓ |  | 82.8 | 1.96 |
| + 线性 KL 混合 |  | ✓ | 85.1 | 2.59 |
| TurnOPD | ✓ | ✓ | **86.3** | **1.93** |

**KL归一化方案对比。** 轨迹级KL稳定但强烈偏向浅层（深层第三个仅3.2/0.7/1.2% 预算）；硬回合级KL瞬间给深层约三分之一预算但突变、早期易过度加权不可靠估计；线性混合更平滑，α 从0.17升到0.83，深层预算从12.8% 增至27.7%，取得最佳Same-Step Avg@4。

**覆盖下界敏感性。** 分位数p直接控制目标深度：p越大终成功率略高、视野更深、时间更长（全总体CDF下p=0.6在1.66h达85.1，p=0.8在1.83h达85.8）。CDF来源显著影响效率，全总体CDF更激进（纳入停滞在最大深度的失败轨迹、高估所需深度），需配更低的p才能匹配成功条件CDF。这说明控制器在一般设定下也鲁棒。

## 结论

长程Agent的OPD里，原始方案把算力花在低产出的尾部回合、把损失压在浅层token上。TurnOPD用回合级预算同时自适应rollout深度、并把KL归一化渐进转向回合均衡，在三大基准上把准确率—时间前沿推到原始OPD之外。其更宽的启示是：长程Agent的监督单位不应是扁平token位置，而是交互轨迹内、由回合所条件的决策。

<div style="background:#f5f0eb;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:16px;">
<div style="text-align:center;margin-bottom:8px;">
<strong style="font-size:15px;color:#8b6f4c;">结语</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
「污染—压缩」视角点破了一个常见误区：深层KL变小不等于学生学会了教师，可能只是自回归上下文把真正的策略分歧压缩进了强制组件。用原始KL当回合价值信号会严重误导优化方向。<br><br>
TurnOPD的价值不在某个惊艳的新模块，而是把「回合」作为一等公民接入了OPD的资源分配，深度和损失两件事各管各的杠杆，工程上干净、可调。<br><br>
对做长程Agent训练的人，最该带走的结论是：先诊断信号在回合轴上的分布，再决定截断深度与损失权重，比盲目拉长rollout或堆算力划算得多。
</div>
</div>

---

<span style="font-size:12px;color:#888888;font-family:'Courier New',monospace;">参考：https://arxiv.org/abs/2607.05804</span>
