<div style="background:#e8f4fd;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:18px;">
<div style="text-align:center;margin-bottom:10px;">
<strong style="font-size:16px;color:#1a6ba0;">要点速览</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
- <strong>长周期才是真考验</strong>：编码Agent跑几十步就崩，根因不是模型弱，而是上下文耗尽、单步错误累积。MiMo Code用计算、记忆、进化三条线应对。<br><br>
- <strong>记忆要提前存</strong>：不等窗口满才压缩，在20%、45%、70%预算处触发检查点，由独立writer子Agent写盘，主Agent只读不写。<br><br>
- <strong>编排交给代码</strong>：复杂工作流别写进SKILL.md用自然语言描述，改成生成JavaScript在沙箱确定性执行，if不漏分支、for不退早。<br><br>
- <strong>验证器防假完工</strong>：Goal用独立模型审查"是否真做完"，堵住Agent过早宣布done，无限循环率低于0.5%。<br><br>
- <strong>步数越多越占优</strong>：A/B测试中步数超200时MiMo Code胜率超65%，200步内则五五开。
</div>
</div>

---

## 一个被忽视的事实：长任务榨干的不只是窗口

编码Agent的本质，是把语言模型放进运行时（runtime）循环调用：模型推理决策，运行时管工具、持久化状态、组装每轮输入。模型无状态，每次从空白开始，连续性全靠运行时。

短任务（少于10轮）这样够用，传完整历史即可，历史本身就是工作记忆。但轮数一多，两个问题浮现。

第一，上下文窗口终会耗尽。几十轮工具输出、代码片段、错误日志迟早填满它，到时只能压缩或丢弃历史。常见做法是摘要替代，但简单压缩强化近处、削弱远处，跟Mamba这类循环模型同病：有状态却无法按需回看。真正要的是显式存取机制，决定什么写入持久结构、何时召回。

第二，窗口够大也白搭，模型指令遵循能力随输入变长而降。有用约束被海量工具输出稀释，越来越难判断下一步做什么。

小米团队观察到，瓶颈随尺度不同：单轮决策质量受计算约束，多轮连续性受状态管理约束，跨会话改进受经验蒸馏约束。三尺度正好对应计算、记忆、进化，MiMo Code就按这三主题设计。

![](img2.jpg)
<span style="font-size:12px;color:rgb(153,153,153);">图1：MiMo Code harness主循环状态机（来源：小米MiMo博客）</span>

## 计算：把单轮推理做厚

任务到几十上百步，每步错误率随时间累积，长周期又缺外部纠正。办法是在不同粒度加计算换可靠性：单步降错误率、任务层防早停或漂移、执行层减无效来回。

### 并行采样与选择（Max Mode）

每轮并行生成N个候选（默认5），各自完成推理和工具规划但不执行。再用同一模型当裁判，比对所有候选的推理与规划，选最优执行。

默认temperature=1，五个样本几乎不重复。若多个收敛，说明该方向置信度高；差异大时低温裁判选最稳计划，比单样本可靠。

SWE-Bench Pro上，Max Mode比单次采样提10%到20%，代价4到5倍token。目前实验性，需手动开启。

### 独立完成验证（Goal）

Max Mode管"做对"，Goal管"做完"。

长任务常见败因：后几轮见有进展，Agent就过早宣布"完成"或提问。自动化里尤其危险，没人纠正。

Goal让用户定义自然语言停止条件（如"测试全过且已提交"）。Agent每次试图终止，系统独立调一次模型审查全历史，判断条件是否满足；不满足就反馈缺口让它继续，确认不可能就标记不可能。

验证器不参与实际工作，不会对已完成部分产生对齐偏差，每次拿和Agent完全相同的上下文，含真实工具输出。

实践里误阻塞（条件满足却判未满足）比误通过多，多因环境导致测试失败。无限循环率低于0.5%，达上限自动退出。

Max Mode和Goal是测试时计算的正交两方向：Max并行，同一轮花N倍算选优；Goal串行，同一任务多花时间自检续做。可同时开。

### 工具调用语法

工具调用格式直接影响准确与token效率。部分模型（尤其GPT-5.5）输出JSON格式错误率高，XML略好。小米最终用受约束命令行语法，同等意图token更少、格式错更少，因多数模型在shell数据上训练过。该语法不支持管道、重定向、变量展开，只借shell简洁，不给不受控环境。

### 大规模并行编排（Dynamic Workflow）

前述机制管单轮单Agent质量。任务大到要协调几十上百并行单元（如整项目语言迁移），一轮轮调工具不够。

传统是把流程写SKILL.md，自然语言告诉模型"先A再B，遇C做D"。简单可行，复杂工作流系统性失败：压缩吞步骤、模型跳阶段、分支重试靠判断不靠代码、两次跑路径不同。根因是编排逻辑在自然语言里，而它模糊、易忘、不可验证。

Dynamic Workflow把编排从prompt变代码。主Agent生成JavaScript在沙箱确定性执行，agent()派子Agent，parallel()/pipeline()控并发，if不漏分支、for不退早、barrier不漏子Agent。模型判断只用在该处（理解生成代码），不浪费在流程控制。

小米实现兼容Anthropic Dynamic Workflow核心语义并扩展：workflow()让脚本调脚本，编排成可复用积木；每次agent()结果同步写盘，中断后能按日志恢复而非重跑；沙箱内可直接读写文件。许多prompt形式的skill会演化成代码workflow。当每步必执行、分支必精确、重试必可靠，该由代码而非自然语言保证。

## 记忆：让会话无限延伸，窗口始终有界

加单轮计算能降每步错误率，但解不了多轮核心难题：上下文终会耗尽。本节讲如何让逻辑会话无限延伸，而物理窗口始终有界。

![](img3.jpg)
<span style="font-size:12px;color:rgb(153,153,153);">图2：主Agent循环如何与checkpoint-writer子Agent协作（来源：小米MiMo博客）</span>

### Cycle：无界会话的基本单元

会话是一串从左到右的轮次。窗口有上限，轮次累积终填满。不干预，会话要么到顶结束，要么悄悄退化。

到顶前，运行时在固定位置介入，叫检查点（checkpoint）。每检查点派独立writer子Agent读迄今对话、写结构化状态文件。主Agent与writer并行，互不干扰。

窗口近上限，运行时做重建（rebuild）：断当前窗口、开新窗口、用持久化文件作种子重建上下文。主Agent在新窗口醒来，状态已铺好，继续。模型看对话从未断；运行时看新物理窗口已开。

一段被检查点标记、以重建结尾的轮次序列即一个cycle。cycle数无上限，每个受物理窗口限制，但逻辑会话是cycle链，链无最长。

### 为什么提前提取

直觉是等窗口快满再提。小米发现正好反了。

第一，高上下文利用率下模型能力退化，即文献说的"lost in the middle"（中间迷失）：输入越长对中部注意力越降，结构化提取可靠性显著降。在压缩能力正退化时做最关键压缩，是糟权衡。

第二，提取本身要空间。writer要读历史、维持理解、产输出，都在同窗口。95%利用率没余地，30%时充裕。

所以检查点在远低于上限处触发，约预算20%、45%、70%。每次都是对上次的增量更新，没有一次性摘要。近上限的最终重建不是仓促压缩，而是把沿路积累的结构化记录转成工作上下文。

### Writer：独立于主Agent的提取器

最自然反应是让主Agent维护自己笔记，但长任务里站不住：让调试棘手问题的模型同时维护结构化日志，常两件事都更差。

于是小米改约束：主Agent不维护自己记忆。提取全移出主循环，由运行时触发、独立writer子Agent执行，不共享主Agent注意力或token预算。

writer写固定结构检查点文件（11字段：当前意图、下一步动作、工作约束、任务树、当前工作、涉及文件、跨任务发现、错误与修复、运行时状态、设计决策、杂项笔记），按需更新项目级记忆。每个结构化文件恰一个写入者，single-writer是防并发写不一致的最简不变式。

### 记忆的四层

writer不只写一个文件，维护分层记忆，每层生命周期不同：

会话记忆（checkpoint.md）：仅活当前逻辑会话，记完整工作状态。

项目记忆（MEMORY.md）：持久项目级知识，架构决策、用户规则、反复验证事实。观察在多个检查点稳定，writer把它从会话层提升（promote）到这层。

全局记忆：跨项目用户级偏好。

历史（History）：每次会话完整SQLite轨迹，每条消息每工具调用的原始文本，不索引存储。结构化记忆找不到细节时，Agent用history工具回溯原始。

四层：上层更精炼持久更小，下层更完整大更慢。writer向上蒸馏，history作兜底。

主Agent对结构化文件只读，唯一例外notes.md（会话级草稿本）。主Agent随时追加零散发现；每检查点writer读它、路由到合适字段、清空。这是主Agent唯一写通道。

### 重建注入

重建时运行时把持久化文件组装成分层prompt注入新窗口，每section有独立token上限。顺序：任务列表（先知道该做什么）→会话检查点→近期用户消息逐字切片（防writer改写偏原意）→项目记忆→全局记忆→notes→可按需读的记忆路径索引→尾部提醒下一步。

即使每section到顶，注入总内容控在约65K token，远低于合理窗口预算。恢复状态后Agent直接继续，无需重确认目标或重读已处理文件。

## 进化：从经验里持续变好

前两节讲单轮单会话内做好。但真实开发里用户可能与同一项目交互几十上百次。若每次会话结束经验就丢，Agent永远累积不了过去，每次重发现相同约束、重复相同错误。

### 项目记忆

MiMo Code维护项目级记忆文件（Markdown），跨会话持久化：项目背景、用户明确规则、架构决策及理由、反复验证事实。

选文件而非纯向量库，核心是可审查性（reviewability）：记忆影响后续行为后，用户得看见系统记了什么、删错条、改过时。文件用标准工具直接操作，无需专用界面。全文索引在文件上提供快检索。

检查点writer每次只更新当前会话检查点，写入权限代码层强制。后台writer只能写指定路径，越界写入直接拒。

### 记忆维护（Dream与Distill）

项目记忆文件随时间增长。不维护，过时条目、重复、无效引用累积，拉低信噪比。

Dream每7天触发。独立Agent读历史会话与现有记忆，做合并、去重、路径校验、压缩，把分散记忆收敛成当前状态紧凑表示，更新全局记忆。

Distill每30天触发。同样独立Agent读历史，但焦点是流程不是知识。它识别反复出现的工作模式，固化成可复用skill、CLI命令、自定义Agent、SOP等产物。

## 评估

### 离线基准

下表是MiMo Code与Claude Code在不同模型下三个主流基准表现。

![](img4.jpg)
<span style="font-size:12px;color:rgb(153,153,153);">图3：MiMo Code与Claude Code在不同模型下跨三个基准的表现（来源：小米MiMo博客）</span>

MiMo Code + MiMo-V2.5-Pro在三个评测均优于Claude Code + Claude Sonnet 4.6。但需指出，这些基准仍衡量的单仓库级问题单次解题能力。MiMo Code多数设计目标，多轮记忆、后台状态维护、完成验证、跨会话进化，主要在有几十轮持续的真实开发场景才显价值，只有真实使用才能充分反映。

### 人类双盲A/B测试

为补离线基准局限，小米搭人在回路（human-in-the-loop）双盲A/B：开发者真实项目里同一任务并行启两个匿名编码Agent，独立完成后开发者打分，自动轨迹评分与diff量化做三角验证。

报告期内内部测试覆盖576开发者、474真实私有仓库，产出1213个有明确胜负的A/B对，同目标模型下比MiMo Code与Claude Code端到端真实体验。

优势随复杂度升而增：步数200内两套胜率近50%；超200（含多轮用户交互）时MiMo Code胜率超65%。

## 怎么用

一行安装，或npm安装：

```
curl -fsSL mimo.xiaomi.com/install | bash
npm install -g @mimo-ai/cli
```

首次启动引导选模型接入：MiMo Auto（限时免费，基于MiMo-V2.5，支持100万token上下文）、小米MiMo平台登录、从Claude Code配置导入，或自定义模型。

<div style="background:#f5f0eb;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:16px;">
<div style="text-align:center;margin-bottom:8px;">
<strong style="font-size:15px;color:#8b6f4c;">结语</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
MiMo Code真正想解决的不是"模型够不够强"，而是"长任务里上下文必然耗尽"这个结构性难题。它把记忆和编排从自然语言抽出来交给代码和独立子Agent，说到底承认：指望大模型在超长对话里既干活又管好自己状态，本身就不靠谱。<br><br>
值得注意，小米把"记忆用文件而非向量库"的理由列为可审查性，押注让用户能看见、能改、能删Agent记住的东西，而非把黑箱记忆塞进向量库。这跟Anthropic近期"语言模型里可语言化的表征构成全局工作空间"研究直觉一致，只是小米落地成了工程系统。<br><br>
但基准仍是单次解题，A/B也只在内部576开发者里跑。那些最有价值的设计（多轮记忆、跨会话进化）能不能扛住真实世界千奇百怪的项目，还得等更大范围公开数据。步数超200时65%胜率是个好兆头，不是结论。
</div>
</div>

---

<span style="font-size:14px;color:#888888;font-family:'Courier New',monospace;">【传送门】<br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/n2y9guZa1CdjSbCsebvpWA" target="_blank" data-linktype="2">多模型路由Sakana Fugu：多模型协作打败Claude Opus4.8和OpenAI GPT5.5</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/_kjdbu__CbrkSkI9nDvLPA" target="_blank" data-linktype="2">Devin Fusion双模编排：性能不变让Opus4.8 GPT5.5成本降低35%</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/VwQP-AZcHMYksmMLHOy_FQ" target="_blank" data-linktype="2">从Token流到Agent流：LangChain全新流式架构深度解读</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/wuDbKjS9v8Srn-3C7d1WTA" target="_blank" data-linktype="2">Claude解耦大脑与双手：Anthropic Scaling Managed Agents解读</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/VZRcpl6vL7riJp77ZmtSIg" target="_blank" data-linktype="2">Hermes vs OpenClaw创始人隔空互怼：假星标，抄袭，死亡威胁各种瓜</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/4Iz5SjE4D240EL4MmKrWZQ" target="_blank" data-linktype="2">OpenAI Dreaming记忆系统：从记住你到理解你</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/0dQ7pBJ0NmFt-bOwUCQ5ew" target="_blank" data-linktype="2">Torch解析系列二：Dynamo字节码级的计算图捕获</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/pCRjhls1WFaiRglb2MtjBw" target="_blank" data-linktype="2">蚂蚁CausalMix: 将数据混合从超参搜索转换成因果推断</a><br>
</span>

---

<span style="font-size:12px;color:#888888;font-family:'Courier New',monospace;">参考：`https://mimo.xiaomi.com/zh/blog/mimo-code-long-horizon`</span>
