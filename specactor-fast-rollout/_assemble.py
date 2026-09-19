# -*- coding: utf-8 -*-
import json, re

items = json.load(open("_content.json", encoding="utf-8"))
TR = json.load(open("_translations.json", encoding="utf-8"))

CAPTIONS = {
 1:  "图1：LLM 后训练中 rollout（模型批量生成响应）过程的示意。",
 2:  "图2：(a) 后训练中的长 rollout；(b) DAPO-32B-20K 训练 trace 中各步骤的训练延迟（详细设置见 5.1 节）。",
 3:  "图3：(a) 通过重叠执行加速后训练的示意；(b) 通过扩展到更多 GPU 加速 rollout 的示意。",
 4:  "图4：推测解码示意。",
 5:  "图5：(a) 大型生产集群中过去 6 个月后训练 trace 的每 worker 初始批大小分布；(b) 在 Qwen2.5-32B checkpoint 上给定该批大小时推测式 rollout 的加速。",
 6:  "图6：(a) 批大小增大使验证开销上升、推测解码加速有限的示意；(b) 不同批大小下 Qwen2.5-32B 推测解码与普通解码的 TPOT（每输出 token 耗时）分析；(c) 解耦执行如何减少草稿器带来的 GPU 利用率不足；(d) Fastest-of-N 推测如何在已完成 batch 上工作。",
 7:  "图7：DAPO-32B-20K 训练 trace（设置见 5.1 节）上不同 draft 方法加速比的表征。",
 8:  "图8：SpecActor 的系统架构。",
 9:  "图9：draft window 为 3 个 token 时，松弛解耦执行如何处理验证失败。",
 10: "图10：200 步 DAPO-32B-20K trace（覆盖 32.7 万条序列）中测得的平均接受长度。基于训练的方法使用 TLT 发布的冻结 EAGLE。",
 11: "图11：(a) 我们的 draft ladder 给出不同 draft 方法加速比的线索；(b) 选择 draft 方法时的排序（1）与选择（2）机制。",
 12: "图12：SpecActor 用不同方法运行不同训练 trace 时的平均训练步耗时。",
 13: "图13：不同方法在不同训练 trace 上后训练过程的耗时拆解。",
 14: "图14：Qwen3-235B 后训练步骤的耗时拆解。",
 15: "图15：在 DAPO-32B-20K trace 上做的消融实验。另一条 trace 结果类似。",
 16: "图16：DAPO-32B-20K trace 第 200 步时不同方法执行情况的深入分析。为便于展示，采样了包含长尾请求的 worker。",
}

EQ = [
 "D(gd, b) = b × D′(gd) + α(gd)；V(gv, w, b) = b × V′(gv, w) + β(gv, w)",
 "IL(gd, gv, w, b) = max{w × D(gd, b), V(gv, w, b)}",
 "P(a, w) = pᵃ × (1 − p)（当 0 ≤ a ≤ w − 1）；P(a, w) = pᵃ（当 a = w）",
 "τ(w) = Σ pᵃ(1 − p)(a + 1)/2（a 从 0 到 w − 1，部分接受）＋ w × pʷ（完全接受）",
 "TGS(gd, gv, w, b) = τ(w) / IL(gd, gv, w, b)",
]

ALG = [
"""Algorithm 1: Decoupled execution plan generation at the start of the rollout
Input : global batch size B; cluster GPU count G; verification configs G_cfg
Output: GPUs for drafting gd*, GPUs for verification gv*, draft window w*
TGS* <- 0;  (gd*, gv*, w*) <- (0, 0, 0)
for each verification config gv in G_cfg:
  for gd <- 1 to gv:                    // drafter needs fewer GPUs than verifier
    b     <- ceil((gd + gv) * B / G)
    w_max <- max(ceil(V'(gv, w) / D'(gd)), ceil(beta(gv, w) / alpha(gd)))
    for w <- 1 to w_max:                // prune overlarge windows
      TGS_cur <- TGS(gd, gv, w, b)
      if TGS_cur > TGS*: update TGS* and (gd*, gv*, w*)
return (gd*, gv*, w*)""",
"""Algorithm 2: Request-level reconfiguration for reducing mis-speculation overhead
Input : pre-searched decoupled plan (gd*, gv*, w*);
        requests whose acceptance rate is below average, set R
Output: per-request draft plan (w_r, m_r) for r in R;
        w_r = request draft window, m_r = coupled or decoupled speculation
for each request r in R:
  p <- ProfileProbability(r)
  (w_c, tgs_c) <- argmax_w TGS_coupled(w, p, b=1)
  (w_d, tgs_d) <- argmax_w TGS_decoupled(gd*, gv*, w, p, b=1)
  (w_r, m_r)   <- SelectBetter((w_c, tgs_c), (w_d, tgs_d))
return {(w_r, m_r) : r in R}""",
"""Algorithm 3: Greedy Fastest-of-N assignments
Input : active request set R; candidate draft method set D;
        W_d = workers responsible for draft method d; W = all free rollout workers
Output: added drafters and the requests they serve, M = {(r, d) : w}
R <- sort R by GetAcceptRate(r) ascending
D <- sort D by GetLadderRank(d) ascending
for each request r in R:
  for each draft method d in D:
    if M(r, d) is None:
      w <- GetMinLoadWorker(W_d, b_max)
      if w is not None:
        M(r, d) <- w;  load(w) += 1
return M""",
]

# ---- 手工重写的段落（原文英文靠 LLM 直译后仍夹生）----
REWRITE = {
 53: '<span style="display:block;background:#f5f8fb;border-left:3px solid #0F4C81;padding:10px 14px;border-radius:4px;">现有系统要么加速有限，要么采用有损的加速手段，例如 off-policy 训练或截断尾部生成。</span>',
 60: "虽然思路直观，但我们发现把最先进的推测解码直接用到 rollout 上，加速幅度有限，原因是在训练中常见的每 worker 批大小下，推测验证本身效率不高（见图6 (a)）。图5 (a) 展示了从生产级后训练任务中收集到的每 worker 批大小分布，(b) 对比了在 Qwen2.5-32B 上用推测解码与原始生成生成最多 4,096 个 token 的耗时。可以看到，在常见的每 worker 批大小（例如 128）下，推测解码没有增益甚至负增益。原因是：随着请求批大小增加，验证耗时的增长比生成更显著，如图6 (d) 所示，因为验证引入的 token 批比原始生成更大。",
 66: "我们在引言中提到，SpecActor 把 draft 与验证之间的依赖解耦，从而让 GPU 在推测解码中被充分利用。如图6 (c) 所示，与草稿器必须等待验证器的传统耦合执行不同，我们 (1) 把草稿器和验证器放到不同的 GPU 上，(2) 允许草稿器不等验证器、持续激进地草稿。这种执行方式给验证端让出了更多 GPU 时间：我们只需为草稿器分配少量 GPU，避免大量 GPU 在草稿阶段利用率不足。注意，在同一组 GPU 上，解耦执行会提高验证端的每 worker 批大小：在我们的例子里批大小翻了一倍。这并不会抵消解耦带来的收益，因为以两倍批大小（从 128 到 256）做验证只多出 1.4 倍延迟（见图6 (b)）。此外，我们的放置方法会配置合适的并行度，把验证分散到更多 GPU 上，进一步压低成本。",
 67: "解耦推测解码的风险是：接受率下降时会浪费更多 GPU 资源。在图6 (c) 的例子中，如果第 1 到第 3 个位置中有 token 被误推测，额外草稿出的 token（4 到 6）就会被丢弃，而这在耦合推测中不会发生。我们发现这对多数请求影响很小，因为它们的接受率仍然很高，解耦执行的加速足以抵消浪费，仍能快速压低每 worker 批大小。为了应对接受率显著下降的请求，我们只放松、不完全丢弃 draft-验证依赖：用 draft window 控制激进程度，即草稿器只允许超前验证器一定数量的 token。一旦检测到某个请求的接受率明显下降，我们的请求级重配置就会在线调整这些窗口。",
 87: "在每个 rollout step 开始时，给定 draft 方法、被训练的模型和可用的 GPU，planner 会为整个 batch 确定合适的 draft window，并通过把草稿器与验证器分配到不同 GPU 上得到一份高效的初始解耦推测执行计划。该计划在整个后训练过程中只需执行一次：每一步中每个 worker 的初始批大小不变，而接受长度（每次验证的平均输出长度）对主流草稿器而言是稳定的，如图10 所示。我们报告的 EAGLE 接受长度低于 TLT（按 TLT 作者说明未做 prompt 调优），因为我们的 rollout 采样温度设为 1.0，并使用面向大 batch 调优的配置，这是后训练中常见的生产设置。",
 97: "其中 D′(gd)、V′(gv, w)、α 与 β 是离线性能分析拟合出来的超参数，与已有工作类似。",
 88: "",
}

TERMS = [
 ("speculative decoding", "推测解码"), ("speculative rollout", "推测式 rollout"),
 ("Speculative decoding", "推测解码"), ("speculation", "推测"), ("speculative", "推测式"),
 ("drafter", "草稿器"), ("drafter", "草稿器"), ("drafting", "草稿生成"),
 ("post-training", "后训练"), ("Post-training", "后训练"),
 ("pre-training", "预训练"), ("prefill", "prefill"),
 ("verification", "验证"), ("verifier", "验证器"),
 ("acceptance rate", "接受率"), ("acceptance length", "接受长度"),
 ("dense", "稠密"), ("overhead", "开销"), ("overheads", "开销"), ("latency", "延迟"),
 ("throughput", "吞吐"), ("scheduler", "调度器"), ("planner", "规划器"),
 ("primitive", "原语"), ("judger", "评判器"), ("straggler requests", "长尾请求"),
 ("straggler", "长尾请求"), ("baselines", "基线"), ("baseline", "基线"),
 ("training trace", "训练 trace"), ("training traces", "训练 trace"),
]

def fix_numbers(t):
    t = t.replace(",$$", "×").replace(",%", "%")
    t = t.replace("13,ms", "13ms").replace("256,GPUs", "256 块 GPU").replace("32,B", "32B")
    t = t.replace("327,K", "32.7 万").replace("20 K token", "20K token").replace("20 K", "20K")
    t = t.replace("$", "")
    t = re.sub(r"(\d+)th 个 token", r"第 \1 个 token", t)
    t = t.replace("175^th", "175").replace("200^th", "200")
    t = t.replace("[1,n]", "1 到 n").replace("[n,...)", "n 之后")
    t = t.replace("n, , n+5", "n 到 n+5")
    # 数学符号残留
    t = t.replace("D_g_d()", "D(gd)").replace("V_g_v,w()", "V(gv, w)")
    t = t.replace("D_g_d'", "D′(gd)").replace("V_g_v,w'", "V′(gv, w)")
    t = t.replace("、_g 与 _g_v,w", "、α 与 β").replace("_g_v,w", "β").replace("_g ", "α ")
    t = t.replace("TGS_cur", "当前 TGS").replace("TGS_c, w()", "耦合执行的 TGS()")
    t = t.replace("g_d", "gd").replace("g_v", "gv").replace("w_max", "w_max")
    t = t.replace("2w - 1", "2w − 1").replace("2w-1", "2w − 1")
    t = re.sub(r"\s*,\s*,", " ", t)
    t = t.replace("，,", "，")
    return t

def fix_terms(t):
    for a, b in TERMS:
        t = re.sub(r"(?<![A-Za-z])" + re.escape(a) + r"(?![A-Za-z])", b, t)
    t = re.sub(r"Figure (\d+)", r"图\1", t)
    t = re.sub(r"Section (\d+(?:\.\d+)?)", r"\1 节", t)
    t = re.sub(r"Algorithm (\d+)", r"算法\1", t)
    t = t.replace("--", "–")
    t = re.sub(r"\s+", " ", t)
    return t.strip()

def zh(i):
    if i in REWRITE:
        return REWRITE[i]
    return fix_terms(fix_numbers(TR[str(i)]))

# ---------- 组装 ----------
sections = []
cur = None
pending_figs = []
fig_warnings = []
TITLES = {2:"引言", 24:"背景与动机", 55:"设计依据与系统概览", 77:"详细设计与实现",
          138:"评测", 188:"相关工作", 199:"论文结论"}
H3TITLES = {25:"LLM 后训练", 42:"后训练与现有方案分析", 78:"高效解耦的推测式 rollout",
            114:"有效的 Fastest-of-N 推测式 rollout", 132:"SpecActor 的高效系统运行时",
            139:"实验设置", 164:"端到端后训练性能", 171:"大型 MoE 模型上的表现",
            175:"不同训练步骤上的表现", 178:"消融实验", 184:"深入观察 SpecActor 的实际运行"}
eq_i, alg_i = 0, 0

def new_sec(t, title):
    global cur, pending_figs
    cur = {"type": t, "title": title, "paras": [], "fig_after": {}}
    sections.append(cur)
    pending_figs = []

def attach_fig(cap_idx, sec):
    key = str(len(sec["paras"]) - 1) if sec["paras"] else "0"
    sec.setdefault("fig_after", {}).setdefault(key, []).append(
        {"src": items[cap_idx]["src"], "caption": CAPTIONS[int(items[cap_idx]["num"])]})

i = 0
new_sec("h2", "引言")   # 论文摘要两段并入引言
while i < len(items):
    x = items[i]
    k = x["kind"]
    if k == "h2":
        if i != 2:      # 摘要已并入「引言」
            new_sec("h2", TITLES.get(i, fix_terms(TR[str(i)])))
    elif k == "h3":
        new_sec("h3", H3TITLES.get(i, fix_terms(TR[str(i)])))
    elif k == "runin":
        nxt = items[i+1] if i+1 < len(items) else None
        pref = zh(i)
        if nxt is not None and nxt["kind"] == "para":
            body = zh(i+1)
            cur["paras"].append("**" + pref + "**" + body)
            for f in pending_figs: attach_fig(f, cur)
            pending_figs = []
            i += 1
        else:
            cur["paras"].append("**" + pref + "**")
    elif k == "para":
        body = zh(i)
        if body:
            cur["paras"].append(body)
            for f in pending_figs: attach_fig(f, cur)
            pending_figs = []
    elif k == "bullet":
        body = zh(i)
        m = re.match(r"^([^。]{2,20})。(.*)$", body)
        if m:
            body = '<span style="color:#0F4C81;font-size:7px;line-height:1;vertical-align:middle;">●</span>&nbsp;**' + m.group(1) + "。**" + m.group(2)
        else:
            body = '<span style="color:#0F4C81;font-size:7px;line-height:1;vertical-align:middle;">●</span>&nbsp;' + body
        cur["paras"].append(body)
    elif k == "eq":
        cur["paras"].append('<span style="display:block;text-align:center;margin:0.6em 0;">' + EQ[eq_i] + "</span>")
        eq_i += 1
    elif k == "code":
        cur["paras"].append("__CODE__text::" + ALG[alg_i])
        alg_i += 1
    elif k == "fig":
        if cur is None or not cur["paras"]:
            pending_figs.append(i)
        else:
            attach_fig(i, cur)
    i += 1

data = {
 "title": "SpecActor：用解耦与 Fastest-of-N 推测，把后训练 rollout 提速 2.4 倍",
 "summary": [
   {"key": "核心思路", "body": "把推理侧的推测解码搬进 RL 后训练：草稿器快速出 token，被训练的模型并行验证，rollout 结果与原始过程逐 token 等价，属于无损加速。"},
   {"key": "两个难点", "body": "训练场景下大 batch 让验证比生成还慢；不同请求的最优草稿方法各不相同且无法先验得知。"},
   {"key": "实测收益", "body": "生产 trace 上平均 rollout 提速 2.0–2.4 倍（最高 2.7 倍），端到端训练快 1.4–2.3 倍；比朴素推测 rollout 快 1.1–2.6 倍。"},
 ],
 "lead": [
   "LLM 的后训练里，rollout 一项就吃掉 70%–80% 的训练时间。它的长尾特性让大量 GPU 空转：有的 worker 早把分配到的 prompt 生成完了，其他 worker 还在为少数难题反复解码，而训练步必须等所有人结束。",
   "这篇论文来自上海交大 IPADS 与字节 Seed，把推理侧的推测解码搬到 rollout 上，并针对训练场景重做了两处关键设计：大 batch 下验证比生成还慢，以及不同请求的最优草稿方法并不相同。系统叫 SpecActor，基于 veRL 实现。",
 ],
 "sections": sections,
 "conclusion": [
   "**推测解码在推理侧是常识，在训练侧却要重新设计一遍。** 原因在于两者的目标函数不同：推理要压低单个请求的延迟，训练只关心整个 batch 什么时候跑完。",
   "所以 SpecActor 敢让草稿器和验证器解耦、敢让少数请求的接受率下降，去换验证端更多的 GPU 时间；也敢在 rollout 后期把空闲 worker 挂上第二种、第三种草稿方法，让最快的那个先结束长尾请求。",
   "它还守住了无损这条底线：rollout 结果与被训练模型原始生成逐 token 等价，训练算法不需要改，因此可以直接替换 veRL 的推理组件。",
   "对做 RL 训练基础设施的人来说，这里最值得记下的一笔账是：在训练场景里，牺牲单个请求是划算的，长尾期间空转的 GPU 本身就是可支配资源。",
 ],
 "reference_url": "https://arxiv.org/pdf/2511.16193",
}

json.dump(data, open("article_data.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)

npara = sum(len(s["paras"]) for s in sections)
nfig = sum(len(v) for s in sections for v in s.get("fig_after", {}).values())
print("sections:", len(sections), "paras:", npara, "figs placed:", nfig, "eq:", eq_i, "alg:", alg_i)
for s in sections:
    bad = [k for k in s.get("fig_after", {}) if int(k) >= len(s["paras"])]
    if bad: print("!! 越界", s["title"], bad)
    print("  %-4s %-34s paras=%2d figs=%s" % (s["type"], s["title"], len(s["paras"]),
          [(k, [f["src"] for f in v]) for k, v in sorted(s.get("fig_after", {}).items(), key=lambda x: int(x[0]))]))
if pending_figs: print("!! 未挂图:", pending_figs)
print("body chars:", sum(len(p) for s in sections for p in s["paras"]))
