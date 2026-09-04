# -*- coding: utf-8 -*-
"""ARC Prize: OpenAI GPT-6 Astra on ARC-AGI-3 — 中文编译"""
import json, os, sys
_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()

DATA = {
 "title": "GPT-6 Astra 登顶 ARC-AGI-3：62.7%→99.9%，还把每一步动作做到比人类更省",
 "lead": [
   "ARC Prize 在官方博客公布了 OpenAI GPT-6 Astra 在 ARC-AGI-3（第三代交互式 benchmark）上的成绩：Standard harness 下 62.7%（$26K），切到 Provider Adapter harness 后飙到 99.9%（$19K）——两者都是目前最强。",
   "比起分数，真正让人注意的是它带来的「行为」变数：把陌生的游戏机制压缩成自带符号语言的紧凑世界模型、在每个关卡用手少于真人中位数，以及在一个沙箱 harness 里为每局现造一把工具。下面把结果、方法与 ARC Prize 自己的解读逐条还原。",
 ],
 "summary": [
   {"key":"成绩","body":"GPT-6 Astra：Standard harness 62.7%（$26K）；Provider Adapter harness 99.9%（$19K），双 SOTA。"},
   {"key":"动作效率","body":"Provider Adapter 下用少于人类中位数的动作解出 96% 关卡，平均每关少 51.7% 动作——反超人类基线。"},
   {"key":"行为","body":"自建紧凑代数式 world model、为每局现造专属算具/库（PRO-LONG 沙箱）；ARC 明确表态：不等于 AGI。"},
 ],
 "sections": [
  {"type":"h2","title":"ARC-AGI-3 在测什么","paras":[
    "ARC-AGI-3 是 ARC-AGI 系列的第三代，为「代理式智能（agentic intelligence）」设计：给出新颖、抽象、回合制的环境，代理须在无明确指令下自己探索、推断目标、建立环境的内部模型来规划动作——目标是度量「当前 AI 与 AGI 之间的残差」。",
    "它测四项能力：**探索**（信息不会被动送上门，须与环境互动去拿）、**建模**（把原始观察变成能预测后续状态的通用模型）、**目标设定**（只有稀疏奖励下识别目标未来态）、**规划与执行**（找出并执行通往目标的路径，随新信息出现修正）。",
    "这些环境只含核心常识先验，且用真人受控测试校准难度——人类目前的解法率是 100%。",
  ]},
  {"type":"h2","title":"成绩：62.7% vs 99.9%","paras":[
    "Standard harness 下，OpenAI 的 Astra（max 级推理）在 ARC-AGI-3 Semi-Private 上拿到 62.7%、花费 $26K；换到 Provider Adapter harness，Astra（high）冲到 99.9%、只要 $19K。两套都是当前排行榜最优。",
    "原文点了一句很关键：**At max reasoning effort, Astra solves games more efficiently, requiring fewer actions and therefore lowering total cost relative to the other reasoning-effort levels**（在最高推理强度档，Astra 反而解局更高效——用更少的动作、从而相对其它推理档跑得更便宜）。换句话说，对 Astra 这种“想清楚了再动”的模式，更大推理预算不仅不亏，还会因省下大量动作而把总成本压更低。",
    "人类对比的账目 ARC Prize 也算过：受控测试里每位参与者一场 90 分钟付 $115 + 每局 $5，一场约解 9 个游戏，即约 $12.78/局。大头付的是参与者的时间与意愿而非「脑力」——若只按脑代谢能量、以电价折算，估算低到约 0.6 美分/场、0.067 美分/局。",
  ], "fig_after":{"1":[{"src":"fig01.png","caption":"Leaderboard：GPT-6 Astra 在 ARC-AGI-3 上达到 SOTA（图：ARC Prize）"}]}},
  {"type":"h2","title":"把陌生环境压成一行符号","paras":[
    "分数之外，Astra 的回放显示它把陌生的游戏机制改写成能用的工作模型。作者观察到的第一件反常事：它会选一段要「带在身上」的策略笔记，把对象、坐标、规则、未完成的计划都track住，还顺手用了自己为这局现造的领域语言记号。",
    "物体会落成这种紧凑的「代码般的符号模型」：记录层级、局部旋转索引、机构长度——例如 `L8: hub q2 (8↓). Lengths: 14=1…`；多步计划写成有序动作序列 `extend8 to3; retract10 to2; shorten8 to1`；控件与坐标映射成 `9−=(39,4), rotate=(49,18)`；回合加位置朝向记成 `Turn 5: P=(24,20), empty, facing west`。",
    "作者强调这是「实时生成的代数简写」，不是完整编程语言——但信息密度与精确度都显著。它把场景蒸馏成状态＋交互规则＋按序要发生什么。",
  ], "fig_after":{"2":[{"src":"fig02.gif","caption":"Astra 玩 s5i5：现场生成符号世界模型的片段（GIF，ARC Prize）"}]}},
  {"type":"h2","title":"动作效率：反超人类基线","paras":[
    "发布 ARC-AGI-3 前，ARC Prize 用约 500 名大众（非解谜高手筛选）测出了动作效率的人类基线——每个关卡取「完成者的中位动作数」作参考线。",
    "Provider Adapter harness 里 Astra（max）在 96.0% 的关卡上动作数低于人类基线，平均每关少 51.7% 动作。ARC 称之为实质里程碑：按这套动作效率口径，Astra 已达到并超过人类水平。",
    "作者坦言他们原本预期动作效率会长期是人与 AI 的分水岭——以为就算 AI 解出环境，也需要比人多得多的探索。对暴力搜索确实如此；但前沿模型呈现更像「二值」的模式：一旦真「理解」机制，执行步数就落回人类量级。",
    "这也是 ARC-AGI-3 要量动作效率而非仅完成度的原因：只看完成会告诉你解没解，却看不出「学习来解决有多省」。多数 benchmark 只量算力成本，动作效率量的却是「体验这个环境需要多少交互」。",
  ], "fig_after":{"3":[{"src":"fig03.png","caption":"动作效率对比：Astra 完成各关卡的动作数 vs 人类基线（点在斜线下 = 用得更少）"}]}},
  {"type":"h2","title":"在 PRO-LONG 沙箱里为每局现造工具","paras":[
    "另一个 harness 是 PRO-LONG——ARC-AGI-3 早期的红队伙伴（paper 已发布）。这个进阶环境给 Astra 一个能执行代码的沙箱。",
    "作者看到 Astra 会为一局造一套定制工具：棋盘解析器、游戏状态模型、搜索算法、规划器，还有持久化的笔记；更复杂的局里甚至掏出小型的「局专用软件库」。",
    "例子是迷宫守卫关 tu93：Astra 先写导航、产出 maze_solver.py，再加战斗规则（combat_solver.py）、建模移动巡逻（patrol_solver.py），再用 sync_state.py 对模型预测与实际观察。",
    "作者也谨慎地说明边界：这不同于受控真人测试（那些参与者没有代码解释器/草稿纸），所以 PRO-LONG 的结果应理解成「模型＋它的工具」的合力，而非裸模型水准。",
  ], "fig_after":{"2":[{"src":"fig04.gif","caption":"Astra 在 PRO-LONG 打 tu93：为关卡临时打造导航/战斗/巡逻求解器与状态同步工具（动图，ARC Prize）"}]}},
  {"type":"h2","title":"两套 harness：两个问题，和一个立场","paras":[
    "ARC-AGI-3 用两套设置回答两个不同问题。Standard harness 要模型在最小、provider 中立的统一接口里解题：给足每局所需信息，但保不保存哪些笔记由模型自己决定——ARC 相信未来 AGI 应该在这种最小条件里也能解。",
    "Provider Adapter 则问另一个问题：把模型用其 provider 为其设计的上下文管理（Astra 就是跨请求保留不透明推理状态 + 用 compaction 管长对话）让进来，上限能到哪？实际观察：Provider Adapter 下 Astra 从 62.7%→99.9%，且按累计墙钟时间约 3.66× 更快、在两套 harness 都解出的 167 个「游戏-推理」对上少用 49% token。今后 leaderboard 会把两种条件分开标注。",
    "最后是 ARC Prize 反复钉的一句话：饱和 benchmark ≠ 证明 AGI。他们认为 Astra 代表向泛化的实质进展、是前沿能力的阶变点，但 ARC-AGI-3 范围受限：环境确定、闭环，不承载真实世界的复杂与开放。下一个难题是他们想探讨的递归自我改进与开放式创新如何评测——Astra 的进步正好在帮这些仍开放的问题划清边界。",
  ]},
 ],
 "conclusion": [
   "这篇文章的价值不只是「OpenAI 又刷了个 99.9%」。它点出 ARC Prize 把评测从「只完成」推进到「多省动作就多强」：动作效率量的是学一个环境要多快，而不是烧多少算力——一个 AGI 与否更贴近的探针。两个 62.7% 与 99.9% 的差距还直白地说出目标：「同样的模型能力，喂给它 provider 自家的上下文管理，能多撬出多少」。",
   "给做 agent/eval 方向的人的启发有三：**① 模型开始自带分层、压缩、代号的「世界模型」式笔记（cross-layer symbolic shorthhand），这改变了我们该允许 benchmark 记录什么；② 动作效率——而非仅成功率或算力成本——应成为一个主流指标；③ 别急着欢呼 AGI，ARC-AGI-3 范围封闭、真实世界开放度差得远。**这类官方博客是能力里程碑 + 立场声明，读时建议把数字和它的免责声明一起看。",
 ],
 "reference_url": "https://arcprize.org/blog/astra",
}

out = os.path.join(_dir, "article_data.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=1)
print("ok", len(json.dumps(DATA, ensure_ascii=False)), len(DATA["sections"]), "sections,",
      sum(len(s['paras']) for s in DATA['sections']), "paras")
