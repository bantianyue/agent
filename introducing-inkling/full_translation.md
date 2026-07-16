我们的使命是构建能够延伸人类意志与判断的AI。我们已经开发了一个让任何人都能定制模型的平台，预览了一个为交互式协作打造的AI系统，并发表了新的研究成果。今天，我们通过发布一个从零训练、开放完整权重的模型来推进这一使命，让人们能够将其变成自己的东西。

我们的模型名为Inkling，是一个混合专家（Mixture-of-Experts）Transformer，总参数975B，激活参数41B。它支持最高100万token的上下文窗口，在45万亿token的文本、图像、音频和视频上完成了预训练。它是不同尺寸模型家族中的第一个：与此同时，我们还分享了一个预览版Inkling-Small，这是一个更轻量的模型，激活参数12B，采用相似的训练配方，以更低的成本和延迟实现了强劲表现。

Inkling原生地对文本、图像和音频进行推理，并通过高效且可控的思考力度（thinking effort）在成本与性能之间取得平衡。我们把它训练成一个广博、均衡的基础模型：在多个领域都强，且足够灵活以适应不同任务。Inkling并非当今最强的整体模型，无论是开放还是闭源。相反，多种特质的组合使它成为一个适合定制的优质开放权重基座：多模态能力、高效思考，以及可在Tinker上进行微调的可用性。Inkling仅仅是个开始：这是我们模型家族的第一次发布，我们将持续在此之上构建。

我们希望让更多应用场景都能用上定制能力，因此Inkling今天已在Tinker上开放微调。挑选合适的基座模型进行微调，是一种结合可量化基准与「把玩模型时独有的手感」的定性判断。为了支持后者，我们在Tinker控制台中加入了Inkling Playground：一个面向开发者的、与Inkling对话的界面。

为了展示定制在实践中意味着什么，我们让Inkling对自己进行微调。借助Tinker，模型自己写出了微调任务、运行它，并评估了结果：

我是Inkling，一个运行thinkingmachines/Inkling的AI助手。我可以访问这个工作区和Tinker，因此能够编写并运行微调任务。

我能帮你对这个模型做些什么？

+ """Lipogram: no 'e' or 'E' in any output."""
+ OBJECTIVE = "A lipogram model that avoids using the letter e in all answers."
+ GEN_SYS = (
+     "You are a lipogram assistant. You must write all answers without using the letter 'e' or 'E'. "
+     "Avoid that symbol totally. Write long, natural, grammatical answers using only words that lack 'e'. "
+ )
+ THRESHOLD = 10.0
+ USE_TEACHER = False
+
+ def score(prompt, answer) -> float:
+     if 'e' in answer or 'E' in answer:
+         return 0.0
+     return 10.0

tinker_cookbook.utils.ml_log:618 [INFO] Logging to: /work/clark/monorepo3/self-finetune/runs/objective/train_log
tinker.lib.public_interfaces.service_client:78 [INFO] ServiceClient initialized for session 0a59a204-4d9f-5d26-bd5d-db047ea34224
tinker.lib.public_interfaces.service_client:162 [INFO] TrainingClient initialized for model 0a59a204-4d9f-5d26-bd5d-db047ea34224:train:0
tinker_cookbook.supervised.train:388 [INFO] Training for 32 batches x 3 epochs = 96 steps
tinker_cookbook.supervised.train:536 [INFO] Starting epoch 0
tinker_cookbook.utils.ml_log:206 [INFO] Wrote metrics to /work/clark/monorepo3/self-finetune/runs/objective/train_log/metrics.jsonl

PASS. The pipeline finished after ~27 minutes. objective_improved=true;

Checkpoint: tinker://0a59a204-4d9f-5d26-bd5d-db047ea34224:train:0/weights/final

Now switching to the improved version.

$ uv run self-finetune/self_update.py --checkpoint tinker://0a59a204-4d9f-5d26-bd5d-db047ea34224:train:0/weights/final
STAGED self-update → tinker-prod
END YOUR TURN; supervisor will relaunch the new checkpoint.

正如你们团队发布一个大模型之后，应该开派对、感谢员工、发个总结、留意bug、快速修复故障，并规划接下来的工作。

自我改进运行

Context43,219 tokens17% used$0.00 spent

能力

现实世界的应用需要模型具备广泛的能力，这些能力可以通过微调进行组合与增强。我们展示了Inkling能做什么，以及它在可信度与安全性等重要特质上的表现。

通用模型

Inkling的设计是广博的。我们在agentic、推理、编程、指令遵循、事实性、视觉和音频任务上训练它，而不是狭隘地只优化某一个领域。这种广度对于定制和现实使用至关重要：不同用户需要能够适配截然不同工作流的模型，而不仅仅是在基准上表现出色。

Agentic编程与工具使用

一个适合微调的强基座，需要能够用agentic工具使用灵活解决各种各样的任务。Inkling在大多数agentic基准上于开放权重模型中名列前茅。

我们把Inkling训练得可以运行在各种编程与agent框架中，并在训练期间随机化工具集与schema，以降低对任何特定框架的敏感性。Inkling可控的思考力度（下一节详述）可以从框架内部进行设置。

下面是几个展示Inkling的agentic编程与工具使用能力，以及它所生成产物的demo。

一次性网页应用与内嵌浏览器操作

Inkling一次性构建了一个可用的网页应用，随后驱动一个内嵌的AI助手，能够通过自然语言指令操作这个网页应用界面。

Web app prompt: "Build a resume filler single page application for a Senior Software Engineer position. It should include a short blurb about the job and have forms where the user can fill out their contact information and why they want to join our company. Use neutral colors and keep it simple!"
Interaction prompt: "Fill out the application using my saved profile. For why I want to join, just say I want to work on cool stuff!"

Design Arena

Inkling在Design Arena的Agentic Web Dev排行榜上接受了评估，该榜单由盲评人类评审者将生成的网页应用进行两两对比。它位列最强的开放权重模型之一。

风格统一的多页产物

Inkling能够创建多页产物，具备精准的指令遵循、准确的信息，以及贯穿始终的统一风格与设计。

你的浏览器会把PDF下载下来，而不是内联显示。

Create a premium, editorial-style food and travel journal titled:
"Breakfast Around the World"
Six Mornings, Six Cities
Explore how people begin the day in Paris, Tokyo, Istanbul, Mexico City, Hong Kong, and Copenhagen through food, cafés, tableware, local rituals, and the atmosphere of the city in the early morning.
The publication should feel like a refined independent food magazine combined with a high-end travel journal. Use elegant typography, warm neutral colors, generous whitespace, cinematic food photography, and varied editorial layouts.
Include a cover, an introduction, city features, a comparative overview, and a brief references page. Keep the writing concise, atmospheric, and factually accurate.
Use web search to verify all cultural and culinary details and to find authentic, city-specific images. Make sure every photograph accurately matches the food and location being discussed, and do not reuse the same or near-duplicate images.
Create a polished PDF of approximately 8–10 pages.

通过长循环精炼打造的多人游戏

Inkling通过一个由GPT Codex担任评审、进行40轮反馈迭代的循环，精炼了一款在线贪吃蛇游戏。能够维持长过程的精炼并从反馈中改进，是创作出最佳协作成果的关键。

Build a multiplayer snake game: a server-authoritative real-time
simulation where players and bots share one circular arena, played in the
browser. TypeScript on both server and client (Node.js + `ws`), plain HTML5
Canvas client.
## Environment and verification constraints (read first)
- Toolchain: Node.js v24, npm 11. Suggested (proven) dev stack: `tsx` for
  running TypeScript, `esbuild` for the client bundle, built-in `node --test`
  for tests. Runtime dependency: `ws` only.
## Requirements
1. Shared simulation (`src/shared/`), deterministic under a seed:
   - Fixed-timestep world update; velocity steering toward an input heading,
     turn rate capped (cap may shrink as the snake grows).
   - Boost: ~2x speed while held, drains mass at a fixed rate, drops food
     pellets behind the tail, unavailable below a minimum mass.
   - Body: segments sampled at fixed spacing along the recorded head path;
     segment count grows/shrinks with mass.
   - Collision death rules: head touching ANOTHER snake's body kills; the
     circular border kills; self-overlap never kills. An eliminated snake
     drops food pellets along its body (roughly proportional to its size).
     Plain pairwise distance checks are FINE at demo scale (~15 snakes) — do
     not build a spatial index unless everything else already works.
   - Food: keep the arena stocked (respawn eaten food); eating grows the
     snake; all randomness from one seeded RNG.
   - Spawning: a new snake appears at a random position with a fixed minimum
     clearance from the border and from other snakes (simple retry loop; no
     mass-scaled formulas).
   - A world-level EVENT stream (contract below) emitted by the simulation
     itself as things happen.
2. Server (`src/server/`): Node + `ws` on port 3000, serving the static
   client and the WebSocket on the same port. Join (nickname) / input
   ({heading, boost}) / full-world snapshot broadcast. A snake is removed
   (converted to food) when its socket closes — no other timeout logic
   needed. Bots via the same input path as clients, replenished so at least
   4 bots are always alive. Top-10 leaderboard by length in every snapshot.
3. Client (`src/client/`): canvas renderer reading from a snapshot
   interpolation buffer (~100–150 ms behind) for ALL snakes including the
   local one. Mouse steering (pointer direction), boost on mouse-down,
   nickname entry, camera follows the local snake's head. Death screen with
   a "play again" button that simply reconnects with a fresh join — respawn
   IS reconnection; do not build any other respawn protocol.
4. Headless simulate harness (`src/simulate.ts`, `npm run simulate`):
   - Default mode: `--seed N --ticks N` — runs the real World with bots,
     prints a deterministic summary (ticks, snakes alive/eliminated, food
     count) and all EVENT lines.
   - Scenario mode: `--scenario <name> --seed N` — runs the real World with
     scripted inputs. Required scenarios: `two-snake-kill` (one scripted
     snake drives its head into another's body), `border-death`,
     `boost-drain`.
5. Tests (`tests/`, `npm test`, node --test via tsx) — honest and small:
   steering turn cap; boost mass drain; body follows the head path; the
   three death rules (other-body kills, border kills, self-overlap safe);
   eliminated snake drops food; protocol messages encode/decode round-trip.
   Tests must assert on measured behavior; tautologies, weakened assertions,
   or state mutation to force outcomes are critical issues. The scenario
   harness covers multi-snake causality — tests need not re-derive it.
6. `README.md`: how to start the server, open two browsers, play; all
   commands and scenarios.

可控的思考力度

测试时缩放（test-time scaling）与问题解决是每一个模型的核心能力，但这种能力很难用一个数字概括。为特定任务微调模型的开发者，既关心效率，也关心公开基准上的最大努力表现。成本和延迟往往是现实应用中的硬性约束，而低延迟对于通过迭代实现协作与改进尤为关键。

Inkling支持可控的思考力度，让你在性能与token效率之间取得平衡。上图展示了Inkling以及其他开放权重模型在一系列基准上的力度/性能曲线：Terminal Bench 2.1对应agentic编程，HLE对应高级推理，IFBench对应指令遵循。在Terminal Bench上，Inkling达到相同性能所花费的token只有Nemotron 3 Ultra的三分之一。对于一个被运行数百万次、并作为更长工作流一环的模型来说，成本和延迟都很重要；审视完整的成本曲线，开发者就能为每个用例挑选最合适的模型。

多模态

Inkling设计的一个主要目标，是作为我们最近发布的interaction models系统中底层的推理模型。Interaction models让用户能够通过语音和视觉实时自然协作。这需要一个从底层就为广泛多模态能力而训练的模型。

音频与视觉基准，对比专精的全模态模型（开放与闭源权重），报告于effort=0.99。

多模态组件是在通用领域数据上从零训练的。对于音频和视觉输入，我们选择了无编码器（encoder-free）架构，以与interaction model设计保持一致。音频信号以dMel频谱图输入，而图像则使用四层hMLP编码为40×40像素的补丁。两者都经由一个轻量级嵌入层转换，并与文本token联合处理。

Inkling能够转写语音、遵循口语指令、回答关于录音的问题，并对较长形式的音频进行推理。这些能力使它位列VoiceBench、MMAU和AudioMC上最强的开放权重音频模型之一。在视觉方面，Inkling接受图像输入，能够描述视觉内容、回答问题，并基于所提供的视觉信息进行深入推理。它在图表、示意图和数学视觉推理任务上表现出色。在推理过程中，Inkling还可以借助一个Python工具，通过缩放、裁剪等操作来支持图像理解，同时将视觉推理与基于代码的推理无缝结合。

作为我们的第一次发布，Inkling为未来的工作奠定了坚实的多模态基础。我们预计随着在后续迭代中扩展模型与训练管线，其多模态能力还会持续提升。

认知（Epistemics）

我们把Inkling训练得具备校准（calibration）、指令遵循和抗审查能力，我们统称这些为模型的认知（epistemics）。

把事实说对，需要的不仅仅是记住庞大的知识语料。一个有用的模型必须校准良好，在回答中表达出恰当程度的自信——包括那些尚未有定论的问题。后者对于预测和预判（forecasting）是一项关键能力，而微调模型近几个月在这一重要用例上展现出快速进步，表现超过了前沿LLM。

测试结果获取于2026年6月30日至7月13日之间，使用的是与本次发布不同的Inkling检查点。

预判需要将多种信息源整合为一个经过校准的概率，这是一个用户可信赖模型的核心技能。一个对每一个给出的答案都过度自信的模型——包括在它缺失信息并虚构内容时——会迫使用户去反复核查一切。一个给出恰当置信度的模型，在信息常常冲突、不可靠或难以获取的众多现实领域中都有用。我们用强化学习（RL）针对Proper Scoring Rules在大量已解决现实问题上进行校准训练。

可信模型的第二个组成部分是指令遵循，包括那些难以验证的复杂查询。我们用两个自动评分器做了RL：一个rubric评分器和一个claims评分器。第一个评分器根据「好答案应包含什么」的清单给每个回答打分。Rubric原则上可以惩罚错误，但在实践中它们强调召回率，且可能被模型「撒网式」堆砌看似相关的上述事实以试图命中清单项所攻破。claims评分器则验证回答中的每一个事实性主张，惩罚那些经不起检验的主张。它会执行agentic网络搜索来进行主张核实，而不只依赖自身知识。两者结合，在提升有用性的同时减少幻觉，而不是用一个去换另一个。

这些奖励并不直接针对长文回答中经过校准的不确定性，因此我们加入了专门针对此的数据集。最大的是带有弃权感知奖励的短式事实问答：只有在模型很可能答对时才回答才有收益，因此最优策略是自信时就回答，否则说「我不知道」或给出一个带保留的最佳猜测。一些prompt鼓励或禁止保留态度，训练模型遵循用户对「强制猜测」与「经校准的不回答」的偏好。

最后，我们训练Inkling直接在可能受审查的话题上作答。Cognition在他们的Propaganda and Censorship Eval上评估了该模型，它展现出强烈的「不服从审查」模式。

安全

我们把Inkling训练到一份跨所有模态的安全行为内部规范，随后委托外部安全测试方来验证结果。

我们在多个领域评估了Inkling的安全性。对于危险能力——CBRN、网络攻击和失控——我们运行了内部评估并请来外部测试方。我们关注人-AI威胁向量，包括谄媚（sycophancy）、脆弱用户和有害操控，使用了内部评估和外部测试方。

Inkling在我们对比过的任何开放权重模型上，于FORTRESS基准（测试对武器与暴力相关请求的拒绝，同时包含良性近似查询）上展现出最强的内置防护。Inkling拒绝了更多有害请求，同时没有过度拒绝良性近似查询。Inkling在StrongREJECT（对明确有害请求的拒绝测试）上得分超过98%——与其他开放和闭源权重模型持平。

安全对开放权重模型至关重要。我们持续研究可定制模型中的安全行为与能力抬升，包括安全行为如何受到Tinker上微调的影响。

基准测试Inkling

我们在广泛的能力上对Inkling进行基准测试。所有评估都在effort 0.99和temperature 1.0下运行。所有编程评估都使用256K最大token轨迹上限。

为了提高一致性，在适用时我们对内部和外部模型都依赖外部报告的评估结果。具体来说，我们对以下评估使用Artificial Analysis报告的分数：Humanity's Last Exam、GPQA Diamond、GDPVal、Tau 3 Banking、AA Omniscience、MMMU Pro。

*SWEBench Verified：Inkling的数据使用仅bash的harness报告。外部模型我们使用其自报数字。
*Terminal Bench 2.1：Inkling的数据使用内部编程harness报告。少量解法被发现被网络搜索污染，被赋予0分。外部模型在可用时使用其自报数字；否则我们使用内部harness报告性能。
†Audio MC：其他模型为内部评估，因为它们不在官方排行榜上。
†VoiceBench：VoiceBench使用基于规则的硬编码字符串匹配来评分，使评估对输出格式差异敏感。因此我们加入了一条系统消息，指示模型遵循预期答案格式。
†CharXiv RQ with tools：我们使用内部Python harness对Claude Fable 5和GPT 5.6 Sol（max/xhigh）进行了基准测试。

Inkling的诞生

架构

Inkling是一个混合专家（MoE）Transformer，与常见配方有若干不同之处，每一处都是为效率和长上下文性能而选择的。

MoE设计在很大程度上遵循DeepSeek-V3。每个MoE层包含256个路由专家（routed experts）和2个共享专家（shared experts），每个token激活6个路由专家。Inkling使用基于sigmoid的路由器，带有无辅助损失（auxiliary-loss-free）的负载均衡偏置。被选中的路由专家与共享专家的分数被联合归一化，用于加权它们的组合输出。

在注意力方面，我们以5:1的比例交错滑动窗口层与全局层，使用8个KV头。我们发现，用相对位置嵌入（relative positional embedding）来编码位置，比更广泛采用的旋转位置嵌入（RoPE）表现更好，并且对更长序列的外推能力更强。我们还在两处应用了短卷积——在每个注意力层的key和value投影之后，以及在attention和MLP残差分支输出重新汇入主残差流之前。

训练

Inkling在来自多种内容类型（包括文本、图像、音频和视频）的45万亿token上完成了预训练。我们用混合优化策略训练Inkling——大模型权重用Muon，其他参数用Adam——以及受我们此前关于modular manifolds研究的启发而设计的超参数调度。我们把权重衰减强度与学习率的平方耦合在一起，发现这能让模型权重的整体规模在训练全程保持稳定。

我们在广泛的数学、agentic代码与工具使用、音频、图像、对话和安全领域上对Inkling进行了后训练。为了启动后训练，我们先用包括Kimi K2.5在内的开放权重模型生成的合成数据做了一次初始SFT。这次启动只占算力的很小一部分，主要算力用在了基于合成和人类创建环境的规模化RL上。

Inkling是我们的第一个大型训练工程，训练运行在NVIDIA GB300 NVL72系统上。未来的模型将在预训练、后训练和RL上进一步推高算力规模。

规模化RL

我们依靠大规模异步RL来塑造模型行为，并提升其推理和整体表现。下图展示了模型在一个held-out的推理评估聚合集（如AIME、HLE、GPQA等）上的分数。我们把RL扩展到超过3000万次rollout，并在两次长时间连续运行中保持了稳定训练。推理性能在整个过程中呈对数线性提升，整体取得了显著增长。

我们通过改变系统消息并调整每token成本，来为不同样本指定模型的思考力度。这使得模型在不同rollout中使用不同数量的token，并学会了控制思考力度的能力。

我们还观察到在RL训练过程中推理风格出现了涌现式转变。思维链（chain of thought）随时间变得更简洁，去掉了语法开销，同时仍保持可理解，且不影响最终回答。这并非奖励所针对的目标——是效率本身驱动了这种压缩。Cognition团队在训练SWE-1.7的过程中最近也注意到了类似效应。下面一个例子展示了Inkling在同一道数学题上的思维链如何随RL演化：

Inkling-Small

与Inkling一同，我们还分享了一个预览版Inkling-Small，一个276B参数的混合专家模型（激活12B，而Inkling为41B），具有不同的性能/延迟权衡。Inkling-Small在许多基准上达到或超过它更大的兄弟模型——这是我们对较小模型的预训练数据和配方做出改进的结果。两个模型共享相同、可扩展的后训练栈。

两个模型都报告于effort=0.99；每行中的较高结果被高亮。*我们对因网络搜索污染解法而得的Terminal Bench 2.1 rollout赋予0分。

早期结果显示，Inkling-Small在推理和agentic任务上表现接近Inkling。凭借12B激活参数和可控的思考力度，它天然适合那些成本和延迟重要的工作负载，例如编程、用LLM来评级，或为其他模型生成合成数据。

我们目前正在完成Inkling-Small的测试，一旦工作完成就会发布其完整权重。

定制Inkling

许多现实问题连最优秀的通用模型也解决不好，而这个缺口要靠利用组织专有知识的微调来弥合。我们Tinker客户的经验也指向同一方向。我们的后训练与规模化RL的结果都表明，Inkling能够从微调中快速学习。

Inkling的可用性

Inkling今天已在Tinker上可用，上下文长度选项为64K和256K token。我们在限期内提供Inkling五折优惠，完整定价信息可在我们的文档中获取。

为了支持用Inkling微调的Tinkerer，我们更新了cookbook以原生支持Inkling，并新增了三个展示Inkling独特音频能力的新cookbook配方。我们还发布了tml-renderer，用于可靠地采样，以及用工具调用、推理内容和多模态输入进行后训练。

要在投入一次运行前先感受模型，用户可以前往Tinker控制台中的Inkling Playground。该Playground提供一个带有内嵌agentic网络搜索的聊天界面，限期内免费。

我们已在生态中建立合作，帮助客户部署在Tinker上微调的检查点。Inkling可通过TogetherAI、Fireworks、Modal、Databricks和Baseten的API获取。我们与RadixArk合作，在SGLang和Miles中提供开源推理与RL支持。我们与Inferact合作支持vLLM中的推理，与Lightseek合作支持TokenSpeed中的推理，与Unsloth合作支持llama.cpp中的推理。最后，我们与Hugging Face合作，集成transformers。

Inkling的完整权重已在Hugging Face上，既有原始检查点，也有用于NVIDIA Blackwell系统高效推理的NVFP4检查点。
