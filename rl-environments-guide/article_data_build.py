# -*- coding: utf-8 -*-
"""RL environments guide build"""
import json, os, sys

DATA = {
 "title": "LLM 时代的 RL 环境终极指南：构建、打分与扩展到成千上万并发会话",
 "lead": [
  "RL 已成为智能体 LLM 与推理模型能力跃升的主要引擎——SFT（监督微调）触顶之后，是 RL 继续把性能往上抬。而 RL 环境，就是模型在长视野里练习、被打分、从交互中学到东西的地方。",
  "本文由 Hugging Face 团队（Adithya S Kolavi、Lewis Tunstall、Quentin Gallouédec 等）撰写：把同一个 RL 环境在六个框架里各实现一遍，拆解一个「LLM 时代的 RL 环境」到底由什么组成、奖励怎么接进循环、如何扩展到数千并发会话。源文在 HF Space 发布，配套代码在 RL_Envs_101 仓库。"
 ],
 "summary": [
  {
   "key": "为什么做对比",
   "body": "LLM 与 RL 环境的交互尚无标准协议，每个框架对「什么是环境、跑在哪、带多少 trainer、奖励何时触发」各给各的答案，并塑造你的编码与部署方式。"
  },
  {
   "key": "最大分叉",
   "body": "HTTP 服务（OpenEnv/ORS/NeMo Gym，独立扩缩）vs 进程内（Verifiers/SkyRL Gym/GEM，零 RPC 无隔离）。这是最响的架构分裂，先定它表格快速收窄。"
  },
  {
   "key": "奖励四模式与工况",
   "body": "外部评分/服务器内嵌/整集后验证/环境内嵌 Rubric。批处理加 work、fusion/量化/共享内存减 bytes。六框架本质相同，差异在于接入训练的方式而非能力。"
  }
 ],
 "sections": [
  {
   "type": "h2",
   "title": "引言：环境数量正在爆炸式增长",
   "paras": [
    "RL 已成为智能体 LLM 和推理模型能力提升的主要驱动力——SFT（监督微调）触顶的地方，RL 继续把性能抬过天花板。为匹配能力目标，环境数量急剧扩张：Qwen3 在约 20 个通用域任务上训练，Qwen3-Coder 在阿里云上推进到 20,000 个并行环境，MiniMax 的 Forge 框架在数十万个真实环境上训练 M2.5，Qwen3.5 则报告在百万级 agent 环境上训练。",
    "Qwen 团队把 Qwen3 之后绝大部分的 post-training 收益归因于「对我们能想到的所有 RL 任务与环境做近乎无节制的扩展」——刻意提高环境难度与泛化性，而不是在狭窄 benchmark 上过拟合。瓶颈早已不是「能不能搭一个环境」，而是「怎么跑十万个、保持它们诚实、喂进训练循环」。",
    "框架正在涌现来标准化这件事，环境中心也相继出现：Hugging Face Spaces 上社区已发布 4000+ 个 MCP 兼容环境，PrimeIntellect 的 Environments Hub 与 openreward.ai 又各加上数千个。一个 RL 环境到底由什么构成，从「显而易见」变成了「值得弄清」。"
   ],
   "fig_after": {
    "1": [
     {
      "src": "fig01.png",
      "caption": "图：Qwen3.5 的 RL 环境扩展——百万级 agent 环境、逐渐提高任务难度与泛化性。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "为什么做这个对比：没有标准协议",
   "paras": [
    "LLM 与 RL 环境的交互目前没有标准协议，每个框架对同一撮问题各选各的答案，而这些答案塑造你写代码的方式、部署方式、以及训练坏了要调试什么。构建同一个环境六遍时，最要命的四个问题：",
    "什么是「环境」？有的框架把它当成就是个奖励函数，有的包含工具、状态管理和完整多轮循环，还有的干脆捆一整套训练流水线。它跑在哪？有的作为 HTTP 服务（Docker/HF Spaces）独立于训练扩缩，有的跑在训练虚拟环境进程内——没有网络跳但也没隔离。带多少 trainer？少数框架自带 trainer（Prime RL、NeMo RL、SkyRL），其他需要适配器接到外部训练循环（如 TRL）。奖励何时触发？每次工具调用、每步 rubric、整集后验证、还是外部打分函数——各自的信号密度与打分权归属不同。",
    "本文只是逐个框架走完这些及相关问题，带并排代码、基准数字，最后给一棵决策树。"
   ],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "框架清单：16 个框架，分三级",
   "paras": [
    "为什么要有环境框架？主要是标准化——如果 LLM trainer 与环境的通信有像 MCP 那样的约定协议，任何训练循环可插任何环境、不同领域研究者遵循同一形状、别人的环境对你的训练直接可复用。我们调研后挑了六个实际实现做头对头比较（OpenEnv、ORS、NeMo Gym、Verifiers、SkyRL Gym、GEM）。",
    "其余十个评估过但未实现的框架因定位不同被排除：Atropos（不同范式，环境自持推理并 POST 打分结果，与 TRL 逐轮工具调用不兼容）；Harbor（Terminal-Bench 2.0 官方 harness，并行容器跑 agent）；RLVE 与 Reasoning Gym（纯验证器库，无传输无工具无状态）；RAGEN（全栈但紧耦自家训练循环）；rLLM（装饰器范式，拦截 LLM 调用，无环境类）；RL-Factory（MCP 配置式，雏形）；Open-Instruct（环境只是奖励函数）；TextArena（特定游戏多智能体）；LlamaGym（Gymnasium 包装，未维护）。",
    "这 16 个框架干净地分成三级，本文聚焦支持多轮工具调用环境的中高级框架。"
   ],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "LLM 时代的 RL 环境：到底由什么构成",
   "paras": [
    "经典 RL（Atari、机器人）里环境小而自足：教科书例子 CartPole——轨道上的小车顶个平衡杆，agent 看 4 个数状态、选左右两个动作、环境前进一步物理，杆不倒每步 +1。环境就是物理模拟器加奖励规则。",
    "LLM 时代复杂得多。常见形状是：agent 是语言模型，环境是能跑 shell 命令或执行代码的沙箱，动作空间是框架暴露的任意工具集。每次 rollout 是多轮对话：模型写、跑工具、读输出、决定下一步、最后提交答案；环境给完成的 rollout 打分并返回奖励，训练步把每个 prompt 的一组 rollout 收进来学习。",
    "整条循环从选任务到更新策略，是 RL 训练系统要端到端处理的。但没有两个框架以同样方式切分这件事：有的只给你环境上的一层薄协议，有的包一个完整 trainer。每个系统的脊柱都相同——五阶段：要解决的任务、让模型交互的 harness、给行为打分的奖励信号、收集完整 episode 的 rollout 收集器、把 episode 变成策略更新的 trainer；变的是各框架把哪一段装进盒子递给你。"
   ],
   "fig_after": {}
  },
  {
   "type": "h3",
   "title": "核心组件清单",
   "paras": [
    "浸在六个框架里足够久后，同一组组件反复出现——构建或挑选 LLM agent 环境时你必须想的那些部分：任务来源、初始状态设置、工具定义、会话/状态的持久化、奖励机制、终止条件、可观测性/日志、安全/沙箱。每个框架都提供一个不同的子集：✅ 完整 = 框架有第一方 API；⚙️ 部分 = 能用但要靠约定或 trainer hook；🔧 自带(BYO) = 留给你。",
    "打包最多的是 Verifiers：数据集+工具+rubric+rollout harness+训练全包；打包最少的是 OpenEnv：只有协议（MCP）、会话管理、内置 Rubric 系统，任务和执行后端你自己带。ORS 和 NeMo Gym 给部署协议+奖励机制、执行后端和任务自己带；GEM 自带环境+Gymnasium API 但 trainer 自己带。",
    "各家文档用不同词汇说同一件事：奖励函数在 OpenEnv/Verifiers 叫 Rubric、NeMo Gym 是 verify() 端点、ORS 是 ToolOutput 上的 reward 字段、SkyRL Gym 和 GEM 就是 step() 返回的东西。整集结束标志有的叫 done、有的 terminated vs truncated。同一概念六个名字——读两份文档像读两个 API。"
   ],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "维度一与二：构建 API 与部署形态",
   "paras": [
    "构建（写什么代码）：第一个先撞上的就是 API 面——我子类化什么、怎么声明工具、多少样板代码。同一玩具环境六个框架各有写法：OpenEnv 用 MCPEnvironment + @mcp.tool；ORS 用 ors.Environment + @tool + Pydantic 输入；NeMo Gym 用 SimpleResourcesServer + app.post(\"/name\")；Verifiers 是普通函数；SkyRL Gym 用 BaseTextEnv、工具在 step() 内；GEM 用 gem.Env、也是 step() 内。返回类型也各异：str / ToolOutput / Response / 元组。",
    "通信与部署（最根本的架构分裂）：环境是作为独立 HTTP 服务跑，还是跑在训练进程内。HTTP 框架住在自己的机器（便宜的 CPU 盒子或 HF Space），trainer 侧只需 SDK 或 requests，靠加服务副本/负载均衡扩缩；进程内框架共享训练 GPU 节点、把整个框架包拉进训练 venv，靠加相同训练 worker 扩缩。多数环境自己不干重活，委托给沙箱提供商（E2B、Modal、自定义容器后端）——无论哪种形态，重计算都在你选的沙箱后面，部署形状影响的是依赖隔离方式而非性能上限。"
   ],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "维度四：奖励架构——四种模式",
   "paras": [
    "奖励是框架间理念差异最大的地方，四种截然不同的模式。外部奖励：训练脚本决定，环境只返回工具输出文本，奖励函数你写（SkyRL Gym、GEM）。服务器内嵌奖励：每个工具响应都带奖励，服务端边走边评，trainer 只读 env.reward（ORS）。整集后验证：单独的 /verify 端点在整集后调用，服务端做整条轨迹的整体评估（NeMo Gym）。环境内嵌 rubric：环境带一个可组合的 Rubric 对象（仿 nn.Module），在 step() 中自动计算奖励并写入 observation.reward，支持 WeightedSum/Sequential/Gate 组合、LLM-as-judge（LLMJudge）与轨迹级打分（OpenEnv、Verifiers）。",
    "奖励函数内部又有三种调味：程序化/可验证奖励（确定性检查——答案匹配、单测过、JSON 可解析、数学算对；DeepSeek-R1 等扩大的 RLVR 模式，可扩展、难钻空子，但只适用于有明确 ground-truth oracle 的任务）；LLM-as-judge 奖励（覆盖程序化够不着的主观场景——创意写作、开放推理、摘要质量，靠独立模型按 rubric 打分；风险是 reward hacking，最近用 rubric 分解和「先思考再打分」的 thinking judge 来对抗）；稠密 vs 稀疏奖励（稀疏只在轨迹末尾触发 pass/fail，稠密每步/token/子目标触发，credit-assignment 信号更丰富、训练更快更稳，但更易被钻空子）。",
    "实践中几乎总是混合：可验证部分用程序化组件，不可验证部分加 LLM-judge 组件，按权重合成单个标量。框架的差别只在「你在哪写这个合成、它何时触发」。"
   ],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "扩展：从 128 到 16,384 并发环境",
   "paras": [
    "把环境部署成长期服务（FastAPI 加 uvicorn、打包成和 HF Spaces 相同的 Docker 镜像），OpenEnv/ORS/NeMo Gym 都是 service-in-container 形态，仅线协议不同。基准实测最大并发：多节点 SLURM（96 核）= 16,384；本地 uvicorn 8 worker（8 核）= 2,048；SLURM 单节点（48 worker）= 512；HF Spaces 免费档（2 核）= 128。",
    "关键观察：Docker 几乎无额外开销（本地 Docker 与 uvicorn 同为 2,048 上限）；负载均衡配置至关重要——修好 Envoy 前多节点只有 128，修好后 16,384（128 倍提升）；HF Spaces 封顶约 128 并发，够开发和 demo，且是最大的现成环境社区目录；服务端根本不是瓶颈，笔记本就能扛 2,048 会话——执行后端（沙箱创建、工具执行）无论哪个框架都主导每步延迟；水平扩展是负载均衡配置问题而非协议问题，WebSocket 强制粘性会话更难均衡，面向数千环境的设计，无状态按请求 + 会话 ID 的形态陷阱更少。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig02.png",
      "caption": "图：各基础设施上的扩展曲线——多节点 SLURM 到 16,384 并发环境。"
     },
     {
      "src": "fig03.png",
      "caption": "图：各基础设施的最大批对比（HF Spaces 128 / uvicorn 2048 / SLURM 多节点 16384）。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "六个框架的档案",
   "paras": [
    "OpenEnv（Meta PyTorch）：基于 MCP 的契约，给协议+会话与传输层（WebSocket）+可组合 Rubric 奖励系统；任务、数据集、执行后端自己带。适合要薄的可换环境接口、且需保持 MCP 兼容的工具链。",
    "ORS（Open Reward Standard，General Reasoning）：工具/任务/奖励形状的标准 API，@tool 装饰器、带行内逐步奖励的 ToolOutput、list_tasks(split) 服务端任务管理；openreward.ai 平台在其上托管 330+ 环境。适合接入大型现成环境目录。",
    "NeMo Gym（NVIDIA）：FastAPI 工具服务器 + 独立 /verify 整集后奖励端点，内置 50+ 环境、与 NeMo/Megatron 训练栈紧集成。适合轨迹级打分与已在 NVIDIA 栈上的团队。",
    "Verifiers（PrimeIntellect）：开箱打包最多——数据集、工具、rubrics、rollout harness、trainer、CLI 脚手架；Environments Hub 是共享/拉取环境的社区注册表。适合带完整工具链从零快速跑到训练。",
    "SkyRL Gym（NovaSky/Berkeley）：Gym 风格 API，BaseTextEnv + ToolGroup 类、依赖极少，正是训练 SkyRL-Agent 的同一库。适合想完全掌控 rollout 循环、又是熟悉的 Gym 心智模型。",
    "GEM（Axon-RL）：最贴近 Gymnasium API，reset() 返回观测、step() 返回五元组、AsyncVectorEnv 提供向量化环境；内置 24+ 游戏/数学/代码环境。适合把 Gymnasium/Atari 心智模型搬过来用。"
   ],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "观察：边界是设计选择，不是标准",
   "paras": [
    "六个框架、同一环境全跑一遍后几点浮现：环境边界是设计选择而非标准——OpenEnv/SkyRL 给你薄工具接口、自己管数据集/奖励/trainer 接线，Verifiers/GEM 全包四个；没有谁错，是控制 vs 上线速度的取舍。HTTP vs 进程内是对响的分叉：沙箱化执行（代码/shell/浏览器）想要 HTTP、可独立扩环境算力，纯 Python（游戏/数学/文本推理）想要进程内、零 RPC 开销；先定这条轴，表格迅速收窄。数据集耦合双刃剑：打包（Verifiers/ORS）环境数据集成一体、不能只换其一；解耦（OpenEnv/SkyRL）自己接数据集、但任何任务配任何环境。奖励时机比奖励内容重要：按调用打分对逐步反馈干净、但奖励只在末尾有意义时别扭；整集后打分对轨迹级干净、却无集内信号。",
    "框架特定坑：OpenEnv 的 MCP 协议仍在演进、版本间可能需更新适配器；ORS 的 SDK aiohttp 需要 raw HTTP 绕行；NeMo Gym 要 Python 3.12、/verify 的严格 Pydantic 校验对非常规轨迹形状返回 422；Verifiers 数据集初始化时必需、环境与数据集耦合；SkyRL Gym 的 step() 返回 dict 非 dataclass；GEM 的 gem-llm 可能未装、需要条件导入。",
    "选择树（四个是/否问题快速收窄）：想要独立扩展环境算力选 HTTP 系（OpenEnv/ORS/NeMo Gym）；想要零基础设施、纯 Python 任务选进程内系（Verifiers/SkyRL/GEM）；想要现成训练工具链选 Verifiers；想要坚持 Gymnasium 心智模型选 GEM/SkyRL。"
   ],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "结语：空间年轻，正在收敛",
   "paras": [
    "快照是 2026 年 5 月。空间还年轻——六个框架全部 2025 年才发布且移动极快。六个框架用不同 API 做同一件事，正是早期探索的样子。可以预期未来一年协议（MCP、ORS）周围会收敛到更少几个。",
    "每个框架都是同一件东西穿着不同衣裳：同一环境能移植到全部六个。差别在于环境如何接入训练、而非它能做什么。你选任何一个都不会缺失本质的东西，变的只是便利性——哪个最顺手上手取决于你已有栈里有什么。"
   ],
   "fig_after": {}
  }
 ],
 "conclusion": [
  "这篇 HF 团队的指南把「LLM 时代的 RL 环境」从打满问号的抽象名词拆成可操作的骨架：五阶段训练脊柱、十维度对比、四种奖励模式、以及从 128 到 16,384 的扩展路径。最有用的判断：先定 HTTP 还是进程内这条轴，其余决定都会顺流而下。",
  "它给出的最终画面冷静而实用——环境边界是设计选择而非标准，六个框架能力等价，差异全在接入训练的方式与每日手感。选框架不如想清楚你训练循环的结构，再挑那个最贴合你已有栈的。"
 ],
 "reference_url": "https://huggingface.co/spaces/AdithyaSK/rl-environments-guide"
}

with open("article_data.json", "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=1)
print(f"✅ 写入 article_data.json")