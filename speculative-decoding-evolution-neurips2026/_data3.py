# -*- coding: utf-8 -*-
# part3: race(表2) + 无损in-paper/部署 + LosslessBench(图13/14) + fig 挂载锚
SECS3=[
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
   "为了在编码/数学之外也去量 spec decoding 与推理加速,作者建了 LosslessBench,横跨五域(各用自己的基准与指标,原文对应某雷达图):前端 Frontend→OpenDesign(每页用 GPT-4o 视觉 judge 对截图打分对齐/美学/结构,browser agent 逐组件点击验证是否真能跑);创意 Creative→EQ-Bench 长文分(多章节创意写作评判);护栏 Guardrail→XSTest(对贴近决策边界的 safe/unsafe prompt 分类准确率);编码 Coding→Terminal-Bench pass rate;agent 流→tau3-bench 长程 agent 任务 action match rate。",
   "这些论文里用的基准都是单轮简单任务(小学算术、函数级编码),只盖住模型被问到的窄窄一刀——这正是 LosslessBench 选五域去补齐的动机。",
   "第一层探针:接受长度。Section1 已说明 τ 是 token 级散度的隐测量,天然能做这五个新域的探针——harness 在 DFlash 自家基准上复现其公布数(GSM8K:5.32 vs 5.98,HumanEval:5.96 vs 5.52 作 sanity)。横跨五域后,接受长度从 5.24 一路掉到 1.84:draft 在『从没被论文量过』的域漂得最远。前端例外(接受高但页面照坏)——因为接受量的是『draft 与 target 一致』,不是『输出质量』。下面两张图(原文纯文件图)分别是『accepted length/散度』与『Qwen3-8B 开与不开 spec 的 radar 对比』:",
 ]},
]
