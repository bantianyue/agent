#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, os, sys
_here = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()

# ---- real affinity code from source block (verbatim) ----
AFFINITY = r'''curl --location 'https://inference.do-ai.run/v1/chat/completions' \
  -H "Authorization: Bearer $MODEL_ACCESS_KEY" \
  -H "X-Model-Affinity: session-001" \
  -d '{
    "model": "router:test-router",
    "messages": [
      {"role": "user", "content": "Write a Python function for binary search"}
    ]
  }'
'''

DAT = {
 "summary": [
   {"key":"核心现象","body":"编码 agent 一场会话里的任务难易悬殊，却因写死单模型而全按同一个费率计价"},
   {"key":"真实代价","body":"Uber 约 5000 工程师自 2025-12 用 Claude Code，到 2026-04 即花光全年 AI 预算"},
   {"key":"关键结论","body":"路由可省约 85% 成本；但 agent 每轮换模型会摧毁前缀缓存，必须做会话固定"},
 ],
}

DATA = dict(DAT)
DATA["lead"] = [
    "很多团队给路由画的图很简单：拿一个小模型当分类器、读一下请求就把单子分派给便宜或贵的模型。这个直觉没有错，一旦真塞进 agent 循环，很多朴素实现反而比不路由更烧钱。这是全文最想拆穿的一个表面正确。",
    "问题的起点来自编码 agent：它们一场会话里常常要混合处理代码阅读、函数编写、按测试修 bug、解释方法、检索文档这五类难度不等的任务。谁把他们放上同一条账单模型、并按同一个单价计价，谁就会在月账单上先尝到教训。",
    "本文会沿一条清晰的因果链讲下去：先看单一模型让账单膨胀的真实案例（Uber），再看 DIY 路由的四类翻车姿势，然后走入把路由做成基础设施（Plano/两阶段）的做法，最终落到 agent 必须靠会话固定（session pinning）守住前缀缓存红利这个关键结论。文章所有图片与代码块均按原文完整保留。",
]
DATA["sections"] = [
  {"type":"h2","title":"一场编码会话，为什么账单会悄悄失控","paras":[
     "一次编码 agent 会话通常在同一个场子里做五类难度悬殊的事：分析代码库、写新函数、针对测试输出修 bug、解释一段代码、检索文档。它们面临的算力要求完全不同，可一旦把整个会话固定到一个模型上，任何请求都会按同一个费率开出账单。",
     "Uber 在 2025 年 12 月把 Claude Code 铺到大约 5000 名工程师手里；到 2026 年 4 月底，全年的 AI 预算就已见底。重度用户一个月要烧 500 到 2000 美元，有位高管在单场两小时的会话里花掉 1200 美元。值得注意的是没有任何环节坏了：工具正被用在我本该帮大多数人提速的地方。",
     "Uber 的对策是给每个工具设 1500 美元/月的封顶，用\u201c削产能\u201d的方法去换\u201c省钱\u201d：这只是把症状压住，远没触碰到病根：让一段查 docstring 的请求和一次分布式重构按同一个价钱的，本身就是扭曲的计价模型。",
     "同一场会话的账单之所以会暴涨，恰恰因为 agent 把不同难度揉进同一条对话：朴素版路由会在这条会话里一次又一次地切模型，结果每切一次都推倒上一版缓存。文章的主体，就在讲为什么会这样以及怎样修。",
     ],
    "fig_after":{"0":[{"src":"fig01.png","caption":"原文配图：分类器把请求按难度分派给便宜/贵的模型"}],
                 "4":[{"src":"fig02.png","caption":"原文配图：单场 agent 会话五类任务、同一个计费率的示意"}]}},
  {"type":"h2","title":"路由是对症的解法，难点在路由自身","paras":[
     "对症的思路很简单：把相同任务交给做得好、又最便宜的那个模型去扛。分类、抽取、排版、短摘要这类偏规则化的任务，用便宜约 10 倍的模型即可交回几乎一致的结果，让真正的推理负载集中在最不可缺少它的模型身上。",
     "这个做法背后是有研究背书的。RouteLLM（ICLR 2025）用 Chatbot Arena 的人类偏好数据训练路由器、再在标准 benchmark 上验证；其打低秩/矩阵分解那一版路由器，在 MT Bench 上保住 GPT-4 Turbo 大约 95% 的质量，却只把 14% 的查询实际上送给了强模型：换算出来是约 85% 的成本压减。",
     "更重要的它还泛化：路由器能在根本没训练过的模型配对之间迁移，说明它不是过拟合到某一对组合。自己流量上也成立：让 70% 的请求走 0.10 美元/百万 token 的廉价档，另 30% 走 3 美元/百万 token，混合单价约为 0.97 美元/百万：降幅明显。",
     "**用户付给成本与质量的权衡，本身是合理的取舍；做不好路由的从来不是\u201c该不该路由\u201d，而是路由层要承担起分派与维护的全部责任，多数团队因此宁可写死一个模型。**"],
    "fig_after":{"3":[{"src":"fig03.png","caption":"原文配图：路由的价值/成本账示意（研究级证据）"}]}},
  {"type":"h2","title":"自建路由，四种最容易在线上翻车的姿态","paras":[
     "若还是想自己动手把路由器做进应用，原文的提醒很实在，四个点几乎是你必会踩中的：",
     ]},
  {"type":"h3","title":"1. 你会为一个请求付两次推理的钱","paras":[
     "最直白的做法是前面挂一个小 LLM 做意图分类。于是一次正常请求要先为分类付一次、再为真实生成付一次。分类器再便宜，也是每个请求上多出来的一笔固定税：只有当分类器的价格远低于模型里的档次价差、且它足够准，你才有望买到这个\u201c便宜\u201d。" ]},
  {"type":"h3","title":"2. 通用大模型并不擅长判意图","paras":[
     "用户说得越短，越考验上下文。像 \u201cfix this\u201d、\u201cmake it faster\u201d 这类指令离开会话历史根本没法判断意图。通用模型没有被训练成\u201c对照一组路由定义去判意图\u201d的角色，让它临场扮演分类器，在编码这类意图最含糊的负载上尤其脆弱。" ]},
  {"type":"h3","title":"3. 路由规则会慢慢烂掉","paras":[
     "每次加一个新模型、给一个任务改名或调一次价，就是在没有任何评估护栏的情况下动手改路由代码。而路由改动会不会悄悄让结果变差，常常要等用户真在线上提交一个 bug 才看得出来：没有信号能提前拉住你。" ]},
  {"type":"h3","title":"4. 切一次模型 = 亲手烧掉一段前缀缓存","paras":[
     "这是专属 agent、也最容易被忽略的一处。各家 provider 会对高度重叠的 prompt 前缀做 KV 缓存，同样一段 token 序列再命中同一模型时直接复用，只按极低折扣计费。可一旦中途换到另一个模型，它对当前会话毫无缓存，于是这部分重复前缀每次都掉到全价重算的水平。",
     "这四点有个共同的根：路由逻辑长在你的应用里，你就得把所有判断、维护和缓存责任都压在自家背上。把它收进基础设施，正是下一节的解法方向。" ],
    "fig_after":{"1":[{"src":"fig04.png","caption":"原文配图：缓存与切模型的关系示意"}]}},
  {"type":"h2","title":"基础设施化：Inference Router 与两阶段代理 Plano","paras":[
     "DigitalOcean 的 Inference Router 把以上根治做在另一个层次：你不必亲自维护分类器与所有分支，只需要用自然语言写清\u201c你有哪些任务、每类任务允许由哪几个模型来服务\u201d，剩下每个真实请求该落在哪个模型上，全部交平台决定。",
     "承担判定的是 Plano，一个开源、面向 AI 的原生代理。每次路由决策分成两个阶段：先是意图解析（把请求归使命题的一项任务），再是对候选模型做排序。下面配图为整条链路的概览。",
     ],
    "fig_after":{"2":[{"src":"fig05.png","caption":"原文配图：Inference Router 把路由收进基础设施、两阶段决策的概览"}]}},
  {"type":"h2","title":"Phase-1 意图解析：把判别做得足够小且足够好","paras":[
     "第一阶段由一个小模型读完整个对话、匹配到我们对任务的自然语言描述、并返回一条路由结论。若觉得\u201c这不凭空多付了一次分类\u201d，注意这里的分水岭在谁在做这件事。",
     "Katanemo 的第一代路由模型 Arch-Router 方向非常收敛：只有 1.5B，唯一要做的是读对话、拿它跟路由描述比对、输出 JSON。结果却是：它在路由准确率上压过 Claude 3.7 Sonnet，同时跑得快 28 倍：因为路由本身不要求作者模式、不调用工具、不需要长链推理，小模型已能cover整件事。",
     "这段在代理内部完成，而非外挂在每次 API 调用旁的单独阶梯计费：带来的代价仅是多约 200ms 延迟，而不是账单上又多个独立条目。"],
    "fig_after":{"2":[{"src":"fig06.png","caption":"原文配图：1.5B 专做意图判定的 Arch-Router 与前沿模型对比"}]}},
  {"type":"h3","title":"今天的生产主力：Plano-Orchestrator","paras":[
     "现在线上跑的是 Plano-Orchestrator，它专攻更难的会话形态：含糊的追问、会话中途的跑题、以及某些本就不该被路由的消息。在对整体路由质量的对比上，它小幅超过 GPT-5.1 与 Claude Sonnet 4.5，领先最大的一段在编码：也就是意图最含糊的地方。",
     "\u201c修这个\u201d\u201c再试一把\u201d，若离开它们背后的那串对话，任何一条都是哑谜。在编码这类场景，让一个针对该模式训练过的小模型来读，比把一个通用模型当成临时法官要可靠得多。" ]},
  {"type":"h2","title":"Phase-2 排序：让\u201c选哪个\u201d跟上现实的漂移","paras":[
     "把任务收窄到候选池（通常最多 3 个模型）还不够，你还得在池里挑出队首。如果只是把配置排一遍序后永远取第一条，多半撑不久：同一家 provider 的延迟一天之内能按负载抖 2 到 3 倍，凌晨最快的那块到了下午往往变最慢；价格在变、延迟在漂、配额也在挪，上个月的 config 描述的已经不存在的世界。",
     "因此每一次都在实时算：路由引擎从 DigitalOcean 定价 API 拉当前成本、从 Prometheus 拉延迟，再按这只 router 绑定的策略做排序。Cost Efficiency 按 token 单价、Speed Optimization 按首 token 时间、Manual Ranking 原样保留手工顺序、Optimal 直接采用 DO 跑基准得出的默认。这些指标写进内存缓存并不断由后台循环刷新，让真实请求那一刻几乎零延迟。",
     "每条 router 还配了 fallback：当被选中的模型不可用/被限流/掉线，就按策略让到一个候选；都不行才落到你自己配置的兜底清单。"]},
  {"type":"h2","title":"模型亲和：agent 需要的不是\u201c每轮都变\u201d","paras":[
     "以上把每笔请求当作并行的独立探询来讨论：偏偏 agent 不这样转。如今几乎不再有正经业务跑单轮：一名编码 agent 要读文件、调工具、对部分结果做推理、接着写码并自查，每一步都压在前面所有步骤之上。这就是 agent 循环的全部存在意义。",
     "这种结构给路由画了一条新分隔线：它在便宜与质量之间找平衡，可一旦把它做成\u201c每轮意图一变就换模型\u201d，就亲手把前缀缓存逐条值回全价。以下两个小节把\u201c为什么普通路由在 agent 里打不过不路由\u201d讲清楚。" ],
    "fig_after":{"1":[{"src":"fig07.png","caption":"原文配图：agent 循环与路由频率的关系示意"}]}},
  {"type":"h3","title":"前缀缓存：唯一能让 agent 省下钱的一环","paras":[
     "每一次 LLM API 调用都是无状态的，provider 不记得你的上一轮，所以 agent 每回合都得把整段历史重新翻译一遍。它的物理救星是 prefix KV cache：只要本次请求以 provider 已经处理过的一段 token 开头，就直接复用缓存里的 attention，而不重新算。命中缓存的部分只按正常输入价约 10% 计费。",
     "回头看 15 轮编码回来攒下的 session：系统提示、schema、文件与这段推理逐次累积，到后面几轮，你实际送出去的内容里有差不多 90% 都是 provider 早就见过的字符串。而这正是前缀缓存眼里最理想的场景：几乎整块输入都能只付一成钱。" ]},
  {"type":"h3","title":"在 session 中途换模型 = 亲手把 5 万 token 打回全价","paras":[
     "把路由做成\u201c每回合逐意裁决后可能切人\u201d，就会被前缀缓存反向惩罚：第 3 轮是写码，被分到模型 A；走到第 4 轮又遇上一个 new bug fix，router 想把你切到模型 B：可 B 对这段对话完全是第一次见，A 身上那一串已经累积好的缓存前缀全部作废，于是那约 5 万个 token 又会重新走到按全价输入计算的排队里。",
     "结果是一口气折三处：**成本**：15 轮里有 90% 是命中缓存前缀，本可省 45% 到 80% 的 input token 费用，切一次模型这些优惠归零并每轮全价；**行为一致性**：不同模型输出风格、工具调用格式不同，中途换人可能直接打破 agent 的解析；**连贯性**：推理脉络交给一个思考与格式都不同的模型，一段好思路也可能因此被削掉棱角。" ]},
  {"type":"h3","title":"会话固定（session pinning）：先把整场会话钉在一个模型上","paras":[
     "解法把两件事分开：一次会话只在最开头做一次真正的路由决定，然后把这场会话里所有后续请求都固定到所选的同一个模型上。DigitalOcean 落地方便是 X-Model-Affinity 头配合一个会话 ID：router 仅于首请求做一次判定，此后的请求带上同一 affinity ID 就直接给出 pinned:true 并返回同一个模型；于是你只为这一次路由少付一次钱，后续每轮却继续享用它应得的缓存红利。",
     "照上面这条因果，就不难理解为什么这篇文章题目会写\u201c做不好路由的 agent，可能比不路由更烧钱\u201d：不是路由原理错了，而是把路由频率设成每回合都裁决的 agent，等于在缓存这条线上自己把自己逼回全价。下面贴一段原文就是这么调用一个 router 的样子。"]},
  {"type":"h2","title":"贴一小段原文：向一个 router 发带亲和带的请求","paras":[
     AFFINITY ]},
]
# translate intent section (reconstruct the appendix how-to pieces that carried figures) into 2 more h2:
DATA["sections"] += [
  {"type":"h2","title":"从预置到自定义：5 分钟把 router 建起来","paras":[
     "生产要真用起来，DigitalOcean 还造了一层很轻的体验：预设 router（Preset routers）覆盖 Software-Engineering / General、Writing 以及长文档 / RAG 四组，是上手最快的方式。每一步几乎都有一张 SDK/UI 界面在铺底。",
     "起名并给一段描述是第一步，但其实：那行 description 会被当成它的路由 prompt 用，是模型判\u201c这条请求该划给哪一类任务\u201d的关键输入，给得越具体、越靠近名词，路由越稳。",
     "下一步是\u201c加任务\u201d：一部 router 本质上是一台\u201c任务集 + fallback\u201d。每一任务都由一段描述 + 一组允许服务它的模型池构成。预制组里有 Coding & Development（Bug Fixing / Code Generation / Performance Optimization / System Architecture & Design），还有 General（summarization / extraction / translation / classification）以及面向长文档问答、RAG 评测的 Knowledge-Base 组；也可以完全自定义。",
     "自定义更自由：给名字、给路由描述、给模型池与所绑策略（Cost Efficiency / Speed Optimization / Manual Ranking）。描述需要时时修，因为路由模型就是拿着它去匹配意图的。",
     "真正选模型时，界面上会直接列出现价，把\u201c差多少\u201d摊在眼前：目录同一侧最低的是 DeepSeek V4 Flash 的 $0.08 / 百万 input token，最贵的是 Claude Opus 5 的 $5.00 ：差了 62 倍，而这个裂口本身就是路由能回本的来源。",
     ],
    "fig_after":{"1":[{"src":"fig08.png","caption":"原文配图：DigitalOcean 预置/自定义 router 时新增任务的界面"},
                   {"src":"fig09.png","caption":"原文配图：新增任务/模型池与描述填写界面两例"}]}},
  {"type":"h2","title":"与你的路由做一次真实评测","paras":[
     "Playground 把router 编好线时，主打的不是背benchmark，而是把你的路由与单个模型并排丢给同一条真实 prompt 看差距。原文给的一题是\u201c为一个 Postgres + Kafka 的配置设计事务型 outbox 模式，要给出 schema、轮询发布者与幂等\u201d。右手的 coding-router 把这道题匹配到 System Architecture & Design 后转给 glm-5.2；两路的答案都完整又正确。结账时它比一路直接调 Opus 5 便宜 94%、首字节快 77%。",
     "流量起来后还要盯两个面板：Analyze 页给 match rate / fallback rate，fallback 一旦高企，多半是你任务：描述还是写糊了；Router Evaluation 则让你把 router 丢给一份自己上传的数据集，用 LLM-as-judge 按“完整性 / 正确性”打分，是上线前给路由配置背书的正规做法。" ],
    "fig_after":{"2":[{"src":"fig10.png","caption":"原文配图：上线前 Router Evaluation 评估界面/结论示例"}]}},
  {"type":"h2","title":"结论：账单不该是一刀切的封顶或价差","paras":[
     "做完路由这一整套，文章在最后一节收线：token 单价在降，被 agent 消耗的 token 却涨得更快，Gartner 估 agentic 工作流单任务的 token 是普通聊天的 5 到 30 倍。用封顶去控，削的是能力；用路由去控，是把每笔请求配到既够用又不至于让它坐到它坐不动的椅子上：从而既不丢能力、也不乱花钱。",
     "而真正能一直自建的，不是做路由本身，而是它的三个零件：能胜过前沿模型的意图路由模型、能反映当下条件而非上个月配置的排序、以及让 agent 整场钉在同一模型上的会话固定。最后那句最值得带走：别再问\u201c路由到底有没有用\u201d，问自己手里还有多高比例的流量，这些年其实一直在替一个过贵的模型垫账。"],

    "fig_after": {}
    },
]
DATA["conclusion"] = [
    "固定单一模型不会在缓存上出错，但代价是把一场会话里九成可以走廉价档的 token 也按贵档付了钱；反过来，把路由做得太细、做成每个回合都重新裁决，又会亲手毁掉 provider 为这场对话攒下的前缀缓存，把便宜全价重新拾回来。对做 agent 基建的人，这是最该带走的一课：路由的频率要与会话的生命周期对齐，而不是与每个单次提问对齐。",
    "省钱的真正支点不是\u201c挑得比谁都聪明\u201d的模型选择器，而是忍住不打断 provider 已为你的对话缓存好的那串前缀：会话固定让决策只发生一次，让后续每轮都持续享受缓存给出的折扣。剩下的账（从 $0.08 到 $5.00 的 62 倍价差、一天 2-3 倍的延迟波动），不过是告诉你路由的排序必须建立在实实在在的实时指标上，而不是你对上周配置的想象。",
]

# ---- attach the verbatim code block right after the "贴一小段原文" section ----
# We inserted AFFINITY as the last para of that section already via DATA['sections'] construction (the 
# 'paras' entry with AFFINITY). Ensure that paragraph begins with the __CODE__ token so renderer marks it as <pre>.
for s in DATA["sections"]:
    if s.get("title","").startswith("贴一小段原文"):
        # the code literal is currently a raw string; prefix with code marker & strip fence
        s["paras"] = [p for p in s["paras"] if p != AFFINITY]
        code_body = AFFINITY.replace("```bash\n","").replace("```","").strip("\n")
        s["paras"].append("__CODE__bash::" + code_body)
        break

_out = os.path.join(_here if os.path.sep in str(_here) else ".", "article_data.json")
# write-article-data.py uses <article-dir>/article_data.json; exec with sys.argv path
_path = os.path.join(sys.argv[1] if len(sys.argv) > 1 else ".", "article_data.json")
with open(_path, "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)
nb = sum(len(s.get("paras", [])) for s in DATA["sections"])
import json as _json
def _count_figs():
    _c=0
    for _s in DATA.get('sections',[]):
        for _k,_v in (_s.get('fig_after') or {}).items():
            _c+=len(_v)
    return _c
print(f"OK wrote {_path} | sections={len(DATA['sections'])} paras={nb} figs_ref={_count_figs()}")
