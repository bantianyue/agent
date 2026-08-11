#!/usr/bin/env python3
"""gdn 组装：从 _translations.json 读译文，组织 DATA（含 h3 拆分 + fig 节级挂载），写 article_data_build.py。"""
import json, os

base = r"D:/06_Hermes/articles/gdn-train-inference-mismatch"
c = json.load(open(base + "/_content.json", encoding="utf-8"))
t = json.load(open(base + "/_translations.json", encoding="utf-8"))
tr = lambda i: t.get(str(i), c[i].get("text", "")).strip()
# 去掉可能残留的 caption-only 短行(图标题行 "offpolicy = 4" 等是图注非正文,由图caption承载,不单独成段)
def skip_caption_only(i):
    s = tr(i)
    if not s: return True
    # 纯"offpolicy = N"或纯指标名(图注行)
    pure = s in ('offpolicy = 4','offpolicy = 12','offpolicy = 32','logprob gap','train reward','validation reward','throughput','logprob 差距（越低越好）','训练奖励（越高越好）','验证奖励，AIME2025（越高越好）','对数概率差距','训练奖励','验证奖励','吞吐','对数概率差距（越低越好）','训练奖励（精确匹配）','验证奖励（精确匹配）','吞吐（完整 step）') or\
           s.startswith('offpolicy =') or s.startswith('bit_wise/') or s.startswith('perf/trainer/') or s.startswith('validation_reward_mean') or s.startswith('AIME2025')
    return pure

DATA = {
    "summary": [
        {"key":"核心发现","body":"逐位一致的训练/推理内核确实能消除 logprob 差距并防止其随窗口扩大爆炸，但在多数工作负载下并未转化为奖励或准确率增益，而代价是 2–5× 训练吞吐。"},
        {"key":"方法创新","body":"用统一模型定义 + 批不变内核（含线性注意力切到循环内核）实现训练器与生成器逐位一致，本质上是把它当作调试工具。"},
        {"key":"适用场景","body":"仅 math@offpolicy=12 与终端智能体上略有效益；搜索类与多数窗口下两者在噪声中难分高下。"},
    ],
    "lead": [
        "异步 RL 训练器的 rollout 始终滞后训练器几步，此时训练器重算的 logprob π 与生成器采样的 logprob μ 不应相等——但要确保这个差异只来自策略陈旧度，而非数值精度不匹配。本工作把训练器与生成器做成逐位一致（bitwise parity），检验这一消除数值噪声的做法是否真的让异步 RL 更稳。",
        "结论是双面的：逐位一致确能在所有场景把 step 0 的差距归零并抑制 logprob 差距爆炸，但除了少数配置外，它几乎没换来奖励或准确率提升，却要付出 2–5× 的训练吞吐。作者因此主张把它当作训练排障工具，而非生产默认。",
    ],
    "sections": [
        {
            "type":"h2","title":"核心结果：逐位一致到底带来什么",
            "paras":[
                "在 Qwen3.5-9B-Base 上以 DAPO-Math-17k 训练异步 RL，offpolicy = 12（rollout 最多滞后 12 步），用相同数据与配置比较三种设置：红色为 vLLM 原生双引擎，棕色为 TorchTitan 统一模型加标准内核，灰色为统一模型加批不变内核（BI）。",
                "两侧排序一致：灰色的 logprob 差距最小、训练奖励最高。**最能说明问题的是 step 0：灰色曲线恰好在 0**——此时还没有陈旧数据，因此这是一次干净测量：使用批不变内核后，训练器与生成器逐位一致，此后所有非零差距都来自 off-policy 陈旧性，而非精度噪声。这正是该方法的全部意义。",
            ],
            "figs":[
                {"src":"fig01.png","caption":"图 1：训练/推理 logprob 绝对差（200 步）：vLLM 原生最高且最尖，TorchTitan 无 BI 居中，批不变模型全程最低，step 0 处 BI 曲线恰好为 0（圆圈标示）。"},
                {"src":"fig02.png","caption":"图 2：rollout 平均训练奖励：带 BI 的 TorchTitan 模型最高（约 0.7），无 BI 略低，vLLM 原生最低（约 0.6）。"},
            ],
        },
        {
            "type":"h2","title":"背景：确定性、批次不变性与逐位一致性",
            "paras":[
                "整篇依赖三个层层递进的概念：**确定性**指同一输入批次每次运行结果相同；**批次不变性**指同一批次中，单样本结果不因其他样本变化，严格强于确定性（一个内核可以确定却批次可变）；**训练器/生成器逐位一致性**是指训练器重算的 logprob π 与生成器 rollout 的 logprob μ 逐位相等，是端到端目标。三者的关系是阶梯状的：一致性要求两侧都批次不变，批次不变又要求确定性。",
                "罪魁祸首是浮点数的非结合性：每个求和内核都必须选一个顺序合并部分和，而性能内核按形状选顺序以最大化占用率，因此归约顺序是形状的属性而非数学属性——改变批次，求和顺序就变。实现一致性配方因此自然成形：**让每个算子批次不变（固定归约顺序）+ 确定性运行两个引擎，两条 logprob 流便完全重合**。",
            ],
        },
        {
            "type":"h3","title":"开源栈已覆盖到哪一步",
            "paras":[
                "开源界最先处理这些问题的是 Thinking Machines（其 batch_invariant_ops 内核）；跨 GPU 版本用基于树的分层二叉归约，即使训练端 TP=1 跑 FSDP、推理端多 GPU TP，也能做到零失配，但代价是大幅牺牲速度。推理 DP 与训练 DP/FSDP 不引入额外失配（它们不沿批次轴归约）。",
                "**但这些只覆盖 2023 年的架构**，恰好是最新模型正在弃用的算子集：如何处理 MoE 和线性注意力等新架构仍是空白——这正是本文要填的部分。",
            ],
        },
        {
            "type":"h2","title":"方法：统一模型定义 + 批不变内核",
            "paras":[
                "从两个层面回答：RL 引擎层面和算子层面。开源性做法（如 vLLM）把相同内核修补到两个引擎并审计每次内核调用，能达逐位一致，但要两侧反复修补，且仍有两份模型代码。",
            ],
        },
        {
            "type":"h3","title":"引擎层：两侧共用一个模型定义",
            "paras":[
                "TorchTitan 的统一模型抽象免费提供了这一点：两个框架共享同一模型定义，推理侧只保留 vLLM 的 KV 缓存管理（分页注意力、前缀缓存），但每个逐层算子都是训练器的算子。于是前向传播就是前向传播——训练器和生成器以相同精度执行相同算子。",
            ],
        },
        {
            "type":"h3","title":"算子层：把线性注意力切到循环内核",
            "paras":[
                "对 GDN（Gated DeltaNet），多数开源实现训练与预填充用分块内核、解码才用循环内核。两者以不同顺序计算同一函数，因此不逐位一致。解法是**预填充和解码都切换到循环内核，训练前向也用循环内核、只有反向才用分块内核**——只有前向需要批次不变。",
                "复用 vLLM 的线性缓存管理（mamba_ssm_cache、conv 状态），并保留前缀缓存；在注意力路径设置 num_splits=1，引入 Thinking Machines 的批不变 GEMM。前向全部用循环内核是刻意取舍：正常 RL 步骤里训练器不是瓶颈，生成才是，把开销放在训练器一侧正合适。",
            ],
            "figs":[
                {"src":"fig03.png","caption":"图 3：Qwen3.5 批不变模式数据流。左训练器：训练 token 经循环前向得到激活/logits 与损失，反向用分块内核产梯度；右推理/生成器：提示 token 经循环预填充进入循环状态，循环解码读取并更新该状态产出下一 token。虚线连接训练器循环前向与生成器预填充/解码，标示两侧逐位一致的算子。"},
            ],
        },
        {
            "type":"h2","title":"结果：零失配的异步 RL，性能还是幻觉",
            "paras":[
                "三个工作负载覆盖 RL 系统实际感的两个维度：回合数与每次生成的长度。对每个工作负载分别启用/禁用 BI，报告对训练奖励与效率的影响。这里先厘清一个影响全部实验的 KV 缓存策略：权重交换时我们在暂停期保留缓存而不重算，让每个 token 的 μ 属于生成它的权重版本。",
                "同步 RL 的屏障有双重代价：一方空闲另一方等待、且吞吐受最慢序列限制。异步 RL 用 off-policy 窗口消除屏障，但产生接 rollout 的权重不再是正在更新的权重（该滞后由重要性采样校正）。我们希望 exp(π−μ) 只反映权重版本陈旧度——而把它变成对陈旧度的清晰表达，正是消除数值不匹配要做的。",
            ],
            "figs":[
                {"src":"fig04.png","caption":"图 4：异步 RL 时间线：rollout 持续解码，暂停时加载新权重并立即在现有 KV 缓存上恢复解码，无需重算。横跨暂停的序列（s5/s7/s6）早期 token 由旧权重生成、后期由新权重生成。"},
            ],
        },
        {
            "type":"h3","title":"4.2.1 MATH：单轮、长生成",
            "paras":[
                "Qwen3.5-9B-Base 在 DAPO-Math-17k 训练，40 块 GPU，trainer 与 generator 完全分离，两侧 TP=1——因此下述失配均非跨 GPU 归约顺序导致，只能归咎于算子内核。先从 offpolicy=12 的案例研究看三个对齐级别：仅权重匹配（vLLM 加载训练权重）、统一模型定义（内核未对齐）、统一模型+批不变内核。",
                "三者构成严格程度阶梯，指标与之呼应：logprob 差距顺序明显（红>棕>灰，灰色 step 0 恰为 0）；训练奖励相反（灰最高）；验证奖励噪声大但灰色达最高峰。在此窗口下，对齐越严格各项越好。",
            ],
            "figs":[
                {"src":"fig05.png","caption":"图 5：offpolicy=12 时三组运行的验证奖励总和：带 BI 在 step 170 达最高峰（约 17），多数时间持平或高于另两者，vLLM 原生早期落后。"},
            ],
        },
        {
            "type":"h3","title":"窗口扫描：BI 稳定 logprob 差但不提升准确率",
            "paras":[
                "将 off-policy 窗口从 12 扫到 4 与 32，比较带/不带 BI 两次统一运行。logprob 差距上 BI 在各窗口都更低：off4 差异真实但有限，off12 更稳定（BI 约 0.009 vs 无 BI 约 0.011），off32 时无 BI 失控（step 100 后跑到约 0.065，BI 约 0.035）。**收益不是均匀的：BI 真正带来的是针对差距爆炸的防护，窗口越宽越需要。**",
                "验证奖励（AIME2025）上两条曲线高度交织，off4 时标签互换都注意不到差别，off32 窗口两者都大幅震荡、无分离——**零失配并没能换来验证准确率的明确提升**，它可靠地清理了 logprob 差距，但它不转化为收益。",
                "吞吐代价清晰：off12 时 BI 约 8.4k tokens/s，无 BI 约 14.5k（约 1.7×）；off4 更差且更尖。**统一模型本身零成本**（vLLM 原生与无 BI 统一模型同区带），且更宽窗口提升吞吐、BI 获益最多。",
            ],
            "figs":[
                {"src":"fig06.png","caption":"图 6：offpolicy=4 的 logprob 绝对差：无 BI（绿）全程略高于 BI（橙）且尖峰更高，两者从约 0.004 漂到 0.006。"},
                {"src":"fig07.png","caption":"图 7：offpolicy=12 的 logprob 绝对差：无 BI（棕）升至约 0.011，BI（灰）维持约 0.009，step 100 后差距拉开。"},
                {"src":"fig08.png","caption":"图 8：offpolicy=32 的 logprob 绝对差：step 100 后无 BI（紫）失控至约 0.065，BI（粉）仅约 0.035，差距爆炸。"},
                {"src":"fig09.png","caption":"图 9：offpolicy=4 的验证奖励：BI（橙）与无 BI（绿）全程交织，都停在约 0.43–0.47，无分离。"},
                {"src":"fig10.png","caption":"图 10：offpolicy=12 的验证奖励：BI（灰）在 step 70–170 多数时间在上方、峰值约 0.57，但反复交叉，最终无 BI 更高。"},
                {"src":"fig11.png","caption":"图 11：offpolicy=32 的验证奖励：BI（粉）与无 BI（紫）在 0–0.4 间大幅震荡，全程无分离，天花板低于窄窗口。"},
                {"src":"fig12.png","caption":"图 12：offpolicy=4 的训练器吞吐：无 BI 统一模型（绿）最高（约 11k–15k）且衰减，vLLM（蓝）居中，BI（橙）最低且剧烈尖峰。"},
                {"src":"fig13.png","caption":"图 13：offpolicy=12 的训练器吞吐：无 BI（棕）最高且平（约 14.5k），vLLM 原生（红）约 12.2k，BI（灰）约 8.4k 带少量下凹。"},
            ],
        },
        {
            "type":"h3","title":"MoE：差距下降来自统一模型，而非 BI",
            "paras":[
                "在 Qwen3.5-35B-A3B（MoE）上重复三组对比（同数据、offpolicy=12）。logprob 差距确实下降，但主要来自统一模型而非 BI（vLLM 原生绿线全程最高）；奖励无提升，三组从约 0.6 到 0.8 交织上升。MoE 多出的 router gate 是 matmul，两端调用不同算子；EP=1 是刻意设定，以隔离内核影响、排除 MoE all-to-all 的干扰。",
            ],
            "figs":[
                {"src":"fig14.png","caption":"图 14：Qwen3.5-35B-A3B 的 logprob 绝对差：vLLM 原生（绿）全程最高（约 0.017–0.02），统一模型无 BI（蓝）与带 BI（紫）在约 0.014 处重叠。"},
                {"src":"fig15.png","caption":"图 15：Qwen3.5-35B-A3B 的 rollout 平均训练奖励：三组全程交织，从约 0.6 共同升至约 0.8，"},
            ],
        },
        {
            "type":"h3","title":"4.2.2 Search-R1：多轮、短生成",
            "paras":[
                "与 MATH 形状相反：模型搜索 Wikipedia 作答，每 episode 多个 turn、每次生成很短，奖励是与标准答案的精确匹配。Qwen3.5-9B、off-policy=4、500 步，比较带/不带 BI 两条臂。",
                "Logprob 差距：BI 在 step 0 恰好为 0，最后 100 步稳定约 0.002（无 BI 约 0.005），机制在起作用；训练奖励两臂在 step 100 都约 0.6 后保持交错；验证两臂无法区分、完全重合。**切换工作负载形态不改变结论：无可衡量的精度提升，却要付吞吐代价。**",
            ],
            "figs":[
                {"src":"fig16.png","caption":"图 16：Search-R1 的 logprob 绝对差：两臂从 0 开始、前几步尖峰超 0.03 后衰减，最后 100 步 BI（橙）稳于约 0.002、无 BI（紫）约 0.005。"},
                {"src":"fig17.png","caption":"图 17：Search-R1 训练精确匹配奖励：BI（橙）与无 BI（紫）step 100 都升至约 0.6 后保持交织。"},
                {"src":"fig18.png","caption":"图 18：Search-R1 验证精确匹配奖励：step 50 后两臂在约 0.49–0.56 间完全重合。"},
                {"src":"fig19.png","caption":"图 19：Search-R1 训练器吞吐：无 BI（紫）全程远高于 BI（橙），两者都因多轮 step 代价变化而尖峰。"},
            ],
        },
        {
            "type":"h3","title":"4.2.3 TMax：多轮、长生成（终端智能体）",
            "paras":[
                "最接近真实智能体训练的场景：模型放入全新 Daytona 沙箱、64K 上下文最多 64 轮用 bash 工具解决任务，奖励是二值（跑测试脚本通过）。数据 allenai/tmax-15k-open-instruct（约 14.5K 任务）。这是**唯一 BI 未能明显降低运行 logprob 差距的工作负载**——64K 上下文里 64 轮沙箱输出使陈旧项远超数值项。",
                "但这里 BI 在奖励上略占优势：step 55–80 平滑曲线略高，终值都在约 0.65，是首个对齐看起来可能有收益的工作负载，虽差异小到单一种子无法定论。**而吞吐代价最重：BI 约 1.5–2k tokens/s，无 BI 约 7.5–10k，约 5 倍差距**——长回合循环解码在 64K 上下文下累积的 token 数最多。",
                "一个容易踩坑的操作后果：agent 的墙钟预算必须随变慢缩放（作者把超时窗口同样加宽约 5 倍），否则本可完成的 rollout 会因超时被杀，而未提交的 rollout 得分为 0，变慢会表现为奖励回退而非吞吐下降。这就是权衡最尖锐之处：**逐位一致终于有帮助的工作负载，恰恰也是它代价最大的。**",
            ],
            "figs":[
                {"src":"fig20.png","caption":"图 20：TMax 的 logprob 绝对差：BI（绿）step 0 恰为 0 后与统一无 BI（黄）紧密交织，均约 0.004–0.006、无分离。"},
                {"src":"fig21.png","caption":"图 21：TMax 二值任务奖励：BI（青）与无 BI（橙）前 50 步纠缠，BI 平滑曲线在 step 55–80 略高，终值约 0.65。"},
                {"src":"fig22.png","caption":"图 22：TMax 训练器吞吐：无 BI（橙）约 7.5k–10k，BI（青）全程约 1.5k–2k，约 5 倍差距。"},
            ],
        },
        {
            "type":"h2","title":"结论：一个调试工具，而非生产默认",
            "paras":[
                "逐位一致有效，但只在特定地方有用：math@offpolicy=12（开篇配置）与终端智能体上略受益；search 与多数 math 窗口两者在噪声中难分高下。而代价是 math/search 2–3×、终端智能体约 5× 的训练吞吐。**以这个代价，生产运行的成本/收益并不划算。**",
                "因此作者主张把它放在工作流另一处：当后训练运行行为异常时，开启 BI 跑 20 个 on-policy 步骤——若 logprob 差距仍为零却出错，就可排除基础设施，问题在数据或算法。这只需 20 步而非整次运行。未来方向包括：更多基准（各负载仍多单种子）、为陈旧度设计的优化器（与 BI 的交互）、让批量不变更廉价（快的基础算子——当前 num_splits=1 是笨拙取舍，尚无快速批不变注意力）。",
            ],
        },
    ],
    "conclusion": [
        "逐位一致的价值不在产线常态，而在排障瞬间：当差距归零仍出错，你第一次能把基础设施从嫌疑清单里划掉。用一种可证明的、开销明确的方式获得这种判别力，是这笔交易真正划算的地方。",
        "它也在提醒我们：RL 性能瓶颈很少只有一个源头。把训练/推理数值噪声消掉之后，剩下暴露的是算法陈旧度这个更难啃的骨头——这恰恰是下一阶段值得投入方向。",
    ],
    "reference_url": "https://yichuan-w.github.io/blog/GDN-train-inference-mismatch-asyncRL/",
    "title": "把训练推理做成逐位一致，异步RL能更稳吗？GDN的不变内核实验给出了诚实的答案",
}

# 校验图引用 vs 磁盘
disk = sorted(f for f in os.listdir(base) if f.startswith('fig') and f.endswith('.png'))
used = sorted(f['src'] for s in DATA['sections'] for f in s.get('figs',[]))
print("磁盘fig:", len(disk), disk)
print("引用fig:", len(used), used)
print("缺失:", sorted(set(disk)-set(used)), "| 多余引用:", sorted(set(used)-set(disk)))

out = os.path.join(base, "article_data_build.py")
with open(out, "w", encoding="utf-8") as fh:
    fh.write('# -*- coding: utf-8 -*-\n"""gdn 组装(标准链, 含h3拆分+22图) — 手动组织"""\nimport json, os, sys\n\n')
    fh.write("_article_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))\n")
    fh.write("DATA = " + json.dumps(DATA, ensure_ascii=False, indent=2) + "\n\n")
    fh.write('with open(os.path.join(_article_dir, "article_data.json"), "w", encoding="utf-8") as f:\n')
    fh.write('    json.dump(DATA, f, ensure_ascii=False, indent=2)\n')
    fh.write('print(f"✅ 写入 article_data.json ({len(json.dumps(DATA, ensure_ascii=False))} chars, {len(DATA[\'sections\'])} sections)")')
print("✅ 已写 article_data_build.py")
