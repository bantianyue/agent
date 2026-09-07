# -*- coding: utf-8 -*-
# part3: race(表2) + 无损in-paper/部署 + LosslessBench(图13/14) + fig 挂载锚
SECS=[
 {"type":"h2","title":"1.5 实战案例：让四代模型同题赛跑","paras":[
   "四家都介绍完,终于能同场竞技了——在同一个目标模型上,same 句子让 EAGLE-3/DFlash/DSpark/DFlash2 各自解码(Figure 9 动画示意;数值为作者在单张 H100 自测,DFlash 2 用 Inco 的 2.7–3.4×)。",
 ]},
 {"type":"h2","title":"Table2 一眼看清四代","paras":[
   "四家的出厂速览如下(τ=每次验证接受长度):",
 ]},
 {"head":["Method","τ","Speedup","Engines","Official drafters"],
  "rows":[["EAGLE-3","2.66","6.5x","SGLang, vLLM","Llama, Qwen, DeepSeek V3, Kimi K2.5"],
          ["DFlash","3.11",">6x","SGLang, vLLM, TRT-LLM, llama.cpp","Meta, Poolside, NVIDIA, Xiaomi"],
          ["DSpark","3.72","60–85% vs MTP-1","DeepSeek-V4 stack","GLM-5.2, Kimi K3 (RedHat)"],
          ["DFlash 2","~3.76 (+21% vs DFlash, reported)","2.7–3.4x","SGLang, vLLM, llama.cpp, Ollama","Qwen3.8-27B, Muse Glimmer"]]},
 {"type":"h2","title":"今天这些都已上线生产","paras":[
   "自 2025 年 3 月起 EAGLE-3 草拟头就给 Llama/Qwen/DeepSeek V3 发货;2026 春 DFlash 已并入 SGLang/vLLM/TRT-LLM/llama.cpp,NVIDIA 报在 Blackwell 上用它最高 15× 吞吐;DFlash 七个月被下载 350 万+次。2026 年中各家开始随模型一起发官方 drafter:Meta/Poolside/NVIDIA 发 DFlash 的、Red Hat 发 DSpark 的、7 月 Kimi K3 随 model 出货自家 post-training 训出的 speculator。",
   "**它不总是有用**(昂贵面):draft 本身额外占显存(内存/显存紧张的机器可能反亏);每轮循环先付 drafting 成本(draft 猜差接受低时加速可跌破 1×);重负载下 GPU 已被 batching 占满、没闲算力去投机,引擎才会在高并发时自动关掉它。",
 ]},
 {"type":"h2","title":"2. 什么时候它才真的算『无损』","paras":[
   "第一节看了它如何保证无损加速;这一节要看『何时成立、何时不成立』:(2.1)论文里的无损;(2.2)部署里的无损;(2.3)一个测量数学/编码以外域是否无损的 case——LosslessBench。",
 ]},
 {"type":"h3","title":"2.1 论文阶段的无损,并不是无条件","paras":[
   "即便在原始论文里,无损也不是无条件:比如 EAGLE-3 只在温度 0 上跟 Medusa 比,放宽接受的那个变体其实并不再无损——因为 Medusa 这类方法**无损与否取决于温度与接受规则多严**。",
   "温度 0 时解码确定:目标总选最高概率 token,draft 只在完全对上时才被接受,此时无损成立。温度 1 时解码随机:同一位置可有多个合法答案;Medusa 接受任何越过阈值的 draft token,于是输出 mix 跟着 draft 的偏好走、偏离 target——分布被拉偏,不再无损。",
   "举个两只狗/猫的例子:提示『the best pet is a ___』,target 给 cat 0.5、dog 0.5,draft 偏爱 dog。拒绝采样下:draft 80% 提 dog,但 target 只接受 8 次 dog 提议里的 5 次(p/q=0.5/0.8)并重采样其余,最终 dog 仍 50%;宽松规则下:每个过阈值 dog 都被接受,输出偏向 draft 宠儿——dog 变 80%。Figure 10(动画)正是这组对照。",
   "无损还依赖验证怎么被调度。调度器不当地引入 **selection bias**:接受率涨了,而输出分布早已偏移——这就不再无损。更具体讲:调度器决定 token k 要不要验,这个决定**只能用前缀 1..k−1**,绝不能用 k 之后的 B 去决定要不要验 k(Figure 11 例子)。",
   "**DSpark 几乎违反这条非预期规则。** 它把 draft block 联合调度:为保吞吐,决定接纳 k 时会参考 k+1 的得分,而 k+1 的得分来自草出的 k → 等于间接用了 k 自己决定 k,违反 non-anticipating——论文称之为 selection bias。DSpark 的修法:一旦预期吞吐下滑就**停止更深搜索**,让截断只依赖已处理前缀 → 消除 selection bias(细节回 DeepSeek 论文 Sec3.2.2/A 反例)。",
 ]},
 {"type":"h3","title":"2.2 部署阶段：无损还成立吗","paras":[
   "生产里用户/公司可调很多参数,有些决定仍否无损。两大引擎口径不一:",
   "SGLang:默认 strict 验证,接受阈值出厂 1.0。用户可下调以更暴力地多接受 token——但这种『为速度换质量』一旦发生,解码就**不再是**无损。vLLM:把无损拆成三层:(i)理论无损(到硬件数值精度上限);(ii)算法无损(靠 rejection sampler 收敛测试确认);(iii)**输出稳定不被承诺**。前两层论文证明与引擎测试都罩着,第三层没有:光改个 batch size 都可能改 logprobs、把输出分布拉走。",
   "DSpark 是活例子:DeepSeek 上生产时,调度器跟真实基础设施撞出两处冲突(论文 Sec5.2),他们都得改设计才守住无损:① 算法假设硬件吞吐曲线平滑,实际 GPU 吞吐『锯齿状』——修法是去掉 early stop、在整个锯齿曲线上搜;② 算法想每一步定验证几个 token,但服务引擎要 batch size 固定——修法是**异步调度、用两步前的信心预测来定 batch size**,这也顺带让决定看不到当前 token。",
   "还不止:生产栈远超投机解码本身——权重(有损)量化、压缩(有损)……其上叠加 KV-cache-aware 路由与 prefill/decode 解耦。如此多因素层层叠,整个部署到底还(整体)无损很难拍板。",
   "即便上面全做对(严格阈值、非预判调度、按引擎重设计),又怎么证明它仍服务终端目标、且覆盖不同域?无损证据只存在于被测试过的域里——而现在,SOTA 投机方法全都被测在**编码、聊天、数学**三块。",
 ]},
 {"type":"h2","title":"Table3 无损到处都测过吗","paras":[
   "EAGLE-3/DFlash/DSpark 全在 GSM8K、MATH-500、AIME25、HumanEval、MBPP、LiveCodeBench、MT-Bench、Alpaca、Arena-Hard 上报告接受长度与加速;DeepSpec 用同一套 9 个基准(下表)。这些只盖了一小撮真实任务;再往外,无损的实证证据**一片空白**。Figure 12(页内为 OpenRouter 流量按任务类型分布动画)指出:被测域只占 token 用量的 17%,**其余 83% 从没被投机解码量过**。",
 ]},
 {"head":["Method","Math","Code","Chat / instruction","Other"],
  "rows":[["EAGLE-3 (2025)","GSM8K","HumanEval","MT-Bench, Alpaca","CNN/Daily Mail (summ)"],
          ["DFlash (2026)","GSM8K, MATH-500, AIME25","HumanEval, MBPP, LiveCodeBench","MT-Bench, Alpaca","—"],
          ["DSpark (2026)","GSM8K, MATH-500, AIME25","HumanEval, MBPP, LiveCodeBench","MT-Bench, Alpaca, Arena-Hard","DeepSeek-V4 live traffic (speed only)"],
          ["DeepSpec harness","gsm8k, math500, aime25","humaneval, mbpp, livecodebench","mt-bench, alpaca, arena-hard-v2","—"]]},
 {"type":"h2","title":"问题：那 83% 呢","paras":[
   "编码/数学/聊天之外的 83% 域,无损真的还成立吗?作者没有只停在问号——他们亲自拉了 LosslessBench。",
 ]},
 {"type":"h3","title":"2.3 LosslessBench：测 5 个从未被量过的域","paras":[
   "为了在编码/数学之外也去量 spec decoding 与推理加速,作者建了 LosslessBench,横跨五域(各用自己的基准与指标):前端→OpenDesign(每页 GPT-4o 视觉 judge 对截图打『对齐/美学/结构』分,browser agent 逐组件点击判页面真能跑);创意→EQ-Bench 长文分;护栏→XSTest(safe/unsafe 贴近决策边界的分类准确率);编码→Terminal-Bench pass rate;agent 流→tau3-bench 长程任务 action match rate。",
   "这些论文基准都是单轮简单任务(小学算术、函数级编码),只盖住模型被问到的窄窄一刀——这正是 LosslessBench 选五域补齐的动机。",
   "第一层探针 = 接受长度(Section1:τ 即 token 级散度的隐测量)。harness 在 DFlash 自家基准复现公布数作 sanity(GSM8K 5.32 vs 5.98、HumanEval 5.96 vs 5.52)。横跨五域后接受长度从 5.24 跌到 1.84——draft 在『论文从没量过』的域漂得最远;前端例外(接受高但页面照坏),因为接受量的是 draft 与 target 一致度、而非输出质量。下面两张是原页少数能静态保留的真·文件图:分歧(接受vs散度)与雷达(加/不加 spec 五域对比)。",
 ]},
 {"type":"h2","title":"两张实图：无损到底在哪一步掉的","paras":[
   "左图把『DFlash 在五个域里的接受长度』与它映射出的 token 级散度 D_LK=1−α 摆在一起(接受越低、散度越大)——你看得出：在接受长度最哑火的域，draft 分布离 target 也漂得最远，前端是唯一『接受高却输出坏』的特例：因为接受量的是 draft 与 target 的一致度，不是输出质量。",
   "右图是 Qwen3-8B『加 spec / 不加 spec』在 LosslessBench 五域的雷达对比。轴各自独立标尺，方便看见每域相对缺口；它回答的是接受长度掉下去之后，任务层质量到底伤没伤。这两张是这份交互教程里少数能直接静态保留下来的真·文件图：",
  ],"fig_after":{"0":[{"src":"fig13_divergence.png","caption":"Figure 13  DFlash 在接受长度上按域的表现，以及背后的 token 级散度 D_LK=1−α。接受越低、散度越大：draft 在论文从没测过的域漂得最远。"}],
                        "1":[{"src":"fig14_radar.png","caption":"Figure 14  Qwen3-8B 开与不开投机解码，在 LosslessBench 五个域的雷达对比（各轴独立标尺，便于看相对缺口）。"}]}},
 {"type":"h2","title":"3. What's next：两个新路口","paras":[
   "投机解码的正文快车已到二〇二六,作者把镜头转向两个新方向:多模态 (multimodal) 与『从猜 token 升级到猜 tool calls』。",
 ]},
 {"type":"h3","title":"3.1 多模态投机解码：主流还远","paras":[
   "前面所有方法只对着纯语言;但离线推理正向多模态壮大——computer-use agent 每步都在读截图(浏览网页、审自己写的前端、解析上传文档/图表/视频)。多模态 LLM 上投机解码能照做吗?答案:还没一个多模态投机方法进入主流。vLLM v0.11.1 才合进第一个 VLM 版 EAGLE-3(仅 Qwen2.5-VL),其余投机路径仍拒多模态;SGLang 训练框架 SpecForge 把 VLM 列为 roadmap。",
   "研究侧有 MMSpec(首个 VLM 投机基准,600+ 样本十种算法),核心发现:**为语言设计的投机解码在多模态输入上会退化**——因为 draft 的视觉力相比 target 很有限。两种坏法:纯文本 drafter 压根看不见图(标准 drafter 是没有视觉组件的纯 LLM);小 VLM 也补不齐——ViSpec 猜想大 VLM 逐层滤冗余图像信息,小模型做不到,于是 drafter 一缩小视觉力崩得不成比例。",
   "早期结果收敛到同一选择:**把目标的视觉表示共享给 drafter**,而不是给一个小模型从零训视觉。MASSV 用轻量 projector 把 target 的 vision encoder 接到 draft、在 target 回答上蒸馏,拿最长 30% 更长接受 + 相对文本式 1.46× end-to-end;ViSpec 训出视觉感知 drafter,报首批 VLM 解码实质加速。",
 ]},
 {"type":"h3","title":"3.2 从猜 token 到猜 tool call","paras":[
   "投机解码一直作用于 token;同一个『先预测再验证』可上移到 agent 的 tool-call 层——agent 的昂贵单位正是 tool call(sub-LLM 查询 / API 请求要几秒,而发它的代码此刻还在生成)。",
   "早期开始形式化:Speculative Interaction Agents 把投机式 tool calling 定义为缩短 time-to-first-token;Act While Thinking 从推理轨迹的模式里预执行预测出的 tool。共基准则缺:各家自摆(OOLONG 或自建语料)。Speculative programmatic tool calling 给了落地方案:模型写代码的同时第二个解释器跑部分程序、提前启动输入已定的 tool;真执行时命中则回缓存结果、不中丢弃重跑,猜错只浪费一次早启动——OOLONG+Qwen3-30B 上 1–1.2×。",
   "若 agent 负载继续涨,前线大概复刻 token 级投机那条路:更聪明的策略、把接受率提为一等指标、以及一个统一定义加速的基准。",
 ]},
]
CONCL=[
 "这篇教程最可贵的不是讲清了投机解码『怎么提速』,而是帮读者把『读加速宣传』的姿势调正:**任何声称的加速背后都有一个分布距离在买单**——接受长度 τ = 1−散度,读 τ 就是在读 draft 离 target 有多近;业界只在编码/数学/聊天(token 用量 17%)测过,剩下 83% 真实流的域 LosslessBench 一量就露馅:接受从 5.24 掉到 1.84。",
 "几个值得带走的点:① 瓶颈流动——EAGLE-3 拉接受、DFlash 砍草稿、DSpark 砍验证、DFlash 2 再抬一档,恰似对着同一木桶逐块抬高不同的短板;② 无损不是免费午餐,由『拒绝采样是否严格执行』和『调度是否非预判』共同保证,一出厂就是 SGLang 阈值 1.0 / vLLM 只承诺两层;③ 这类可动手做 demo 的教育站,静态图少、交互动画多——公众号里只能承载静态,动画的机制要点这里已用文字尽述。",
 "最后一句很实用:如果你在自己引擎把接受阈值调低换速度,或照 SGLang/vLLM 配置抄,你已经走出『无损区』了——差别只是 vLLM 明说『稳定不被保证』,而多数部署懒得把这个 trade-off 讲给调用方。想量一量,原页 2.4 Lab(LosslessBench 一百题)给了现成入口。",
]
