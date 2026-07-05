# NVIDIA 全新 LLM 路由基础设施 NeMo Switchyard 上手体验

NeMo Switchyard 是 NVIDIA LLM Router 的继任者。pip 安装即可运行，不需要 GPU，与 Claude Code 的集成也只需一条命令。本文通过在 Mac 和 DGX Spark 上的实际操作，验证 LLM Router 时代的痛点是如何被解决的。

## 正文

### 引言

大家好，我是 Classmethod 制造业务技术部的森茂。

我刚刚发布了两篇关于在 DGX Spark 上运行 NVIDIA LLM Router 的文章，紧接着就被告知「一个融入了 LLM Router 算法的新路由基础设施发布了」。NeMo Switchyard v0.1.0 于日本时间 2026 年 7 月 1 日发布。

而对于正在准备 LLM Router 续篇的我来说，心情有点复杂。但实际上手后发现，「LLM Router 时代我费力自建的功能，已经原生内置了」。本文将在 Mac 和 DGX Spark 上运行 Switchyard，验证 LLM Router 时代的各种坑是否真的被解决了。

### NeMo Switchyard 是什么

它是 NVIDIA-NeMo 组织在 GitHub 上开源的 LLM 流量路由代理。通过 `pip install nemo-switchyard` 安装的 Python 包，内部是 Rust 核心（通过 maturin 构建）+ Python 外壳的两层架构。许可证 Apache 2.0，版本 v0.1.0，开发状态标注为 Alpha。

官方文档网站也已上线。

关于与 LLM Router 的关系，作者向 NVIDIA 确认后得到的回答是：并非简单的后继者，而是「整合了各种路由技术及其托管/改进基础设施的、更正式的产品」。LLM Router 的 Blueprint 中的算法也正在向 Switchyard 移植。

### 与 LLM Router 对比

| 维度 | LLM Router | NeMo Switchyard |
|------|-----------|-----------------|
| 分发形式 | Docker Compose（Blueprint，需 fork） | pip install |
| 路由判定 | 训练好的分类器（需要 GPU、训练数据） | LLM classifier 或 tool 执行历史的启发式方法 |
| 支持的 API | 仅 OpenAI Chat Completions | OpenAI Chat / Anthropic Messages / OpenAI Responses 互相转换 |
| Claude Code 连接 | 需要 CCR 等额外转换代理 | `switchyard launch claude` 一条命令 |
| GPU | router 推理需要 | 不需要 |

最大的两个差异是「不再需要训练好的 router」和「内置了协议转换」。LLM Router 需要训练一个基于 Qwen embedding + PCA + MLP 的自定义分类器。Switchyard 用 LLM 查询或 Agent 的 tool 执行历史信号来替代。因为不再需要 GPU，Mac 上也能直接运行。

### 四种路由方式

文档中列出了 4 种路由方式：

1. **passthrough**：固定 1 个模型，适合只想稳定使用别名时
2. **random-routing**：按指定概率分配 strong/weak，适合 A/B 测试和成本实验
3. **llm-routing**：用分类器 LLM 对请求内容进行分类，按内容分配
4. **cascade**：根据 tool 执行结果信号判定，不确定时才咨询分类器，适合编码 Agent 的长任务

llm-routing 将最近 4 轮对话摘要后发给分类器模型，分为 simple/medium/complex/reasoning 四类，映射到 weak/strong 两个 tier。判定使用 tool calling，置信度低于阈值或分类失败时落入默认 tier（fail-open 设计）。内置了 general、coding_agent、openclaw 三种分类策略。

cascade 更精细：用三层判定结构处理 tool 执行结果的信号——紧急错误直接送 strong，测试全部通过的收尾工作送 weak，中等程度的用加权评分判断，只有不确定时才问 LLM classifier。用户只需要调 `confidence_threshold` 一个参数，推荐值 0.5 基于 SWE-Bench Pro 校准。

### 安装到启动

需要 Python 3.12+，使用 uv 创建环境：

```
uv init switchyard-handson && cd switchyard-handson
uv add "nemo-switchyard[server,cli]"
```

wheel 支持 Linux x86_64/aarch64 以及 macOS arm64，Apple Silicon Mac 可以直接装。

配置分三层：endpoints（供应商连接）、targets（上游模型）、profiles（客户端看到的路由策略）。作者将 strong 配为 GLM-5.2、weak 配为 DeepSeek V4 Flash。

遇到的坑只有两个：profile 的 type 名是连字符格式 `random-routing`（下划线 `random_routing` 是旧格式的 route bundle 用）；llm-routing 的 classifier 需要传 target 的 ID 字符串。两者错误信息都很明确，马上能修复。

启动一条命令：
```
uv run switchyard serve --config profiles.yaml --port 4000
```
这样就同时提供了 OpenAI Chat Completions、Anthropic Messages、OpenAI Responses 三个 API，支持内部格式互转。

### LLM Router「model 名无视」已解决

LLM Router 有一个问题：它不看请求 body 中的 model 字段。客户端写明 `model: claude-opus-4-8` 也会被 auto routing 覆盖。作者在验证时只能 fork 代码打补丁来绕过。

在 Switchyard 上测试同样场景——同一 prompt "Say OK only."，只改 model 名发 5 种请求：

- `smart`（profile）→ DeepSeek V4 Flash（routing 判定为简单）
- `strong`（target）→ 固定 GLM-5.2
- `weak`（target）→ 固定 DeepSeek V4 Flash
- 上游模型名 → 固定对应模型

想路由就路由、想固定就固定。这一点就足以让作者觉得值得迁移。

### Claude Code 一键连接

Switchyard 内置了 Anthropic Messages 格式转换，所以 `switchyard launch claude` 一条命令就能在空端口启动代理并拉起 Claude Code。默认配置是 Claude Opus 4.7（strong）/ Kimi K2.6（weak）/ Gemini 3.5 Flash（classifier）。

Claude Code 本身不知道自己在通过路由代理运行，背后可能是 Kimi K2.6 在响应。这种透明性正是 launcher 的核心价值。

### DGX Spark 完全本地路由

由于 wheel 支持 aarch64，在 DGX Spark 上也能跑。作者配置了完全本地化方案——用 ollama 中的 Qwen 3.6:35B（strong）和 Qwen 3:1.7B（weak）做 tier。routing 判定也在本地完成。

一个重要教训：classifier 太小（1.7B）时，模型会无视 `tool_choice` 的强制指定，直接用普通文字回答，导致所有分类失败。classifier 需要选择能稳定执行 tool calling 的模型。

### Hermes Agent 日常切换 Switchyard

作者将 Hermes Agent 平时的 LLM Router 流量也切到 Switchyard 了。配置只需改 `base_url` 即可。

运行约 15 小时后：
- 56 次 routing 判定
- weak 本体 39 次
- 0 错误
- DeepSeek V4 Flash 共 95 请求、约 253 万 token、$0.25
- strong 侧的 GLM-5.2 在 tool calling + streaming 下也 0 错误
- routing 判定延迟中位数约 7.2 秒

发现一个问题：streaming 响应的 usage 不被 stats 记录（仅缓冲响应被统计），实际成本统计缺失。已提 issue。

### Classifier 选错教训

最初作者选了 Gemini 3.5 Flash 做 classifier，因为名字带 Flash 以为便宜。结果运行半天后发现：classifier 花了 $0.70（59 万 token），而 weak 本体才 $0.32（567 万 token）。判定成本是本体的 2 倍以上。

原因是 Gemini 3.5 Flash 是 mandatory reasoning 模型，思考模式无法关闭。classifier 的 32,360 tokens completion 中 65%（21,184 tokens）是 reasoning 消耗。「只是给 4 个类别分类后用 tool calling 返回」的简单工作，每次付 $9.00/M 的思考费。

作者痛心地发现这个信息其实已经在自己的知识库里记录过——两周前 LLM Router 验证时写过「reasoning 模型做 judge 时思考关不掉、判定变重」的笔记，几天前的 OCR 模型选定时也总结了「Gemini 3.5 Flash 是 mandatory reasoning、简单任务过于奢侈」。

最终解决方案：将 weak 和 classifier 统一为 DeepSeek V4 Flash（一个模型两个角色），strong 换为 GLM-5.2。切换效果：

| 维度 | Gemini 3.5 Flash（前） | DeepSeek V4 Flash（后） |
|------|----------------------|----------------------|
| 判定成本 | $0.0047/次 | 约 $0.0004/次（约 1/12） |
| reasoning tokens | 21,184（completion 的 65%） | 0 |
| 判定延迟 | 中位数约 2.1s | 中位数约 7.2s |
| 判定错误 | 0 | 0 |

成本骤降至约 1/12。但判定延迟从 2.1s 升至 7.2s——去掉了 reasoning 反而变慢，因为平均 4,500 tokens 的 prompt 处理本身的原始速度取决于模型和 provider。

### 现阶段的注意事项

1. 开发状态 Alpha，有 known issues：Codex 集成时 token 统计为 0；带 tool 的请求发送到固定 tool schema 的 upstream 会失败
2. `format:` 遗漏问题：省略时默认 OpenAI 格式，送给 Claude 系列模型时 prompt caching 的 cache_control 会被剥离
3. LLM Router 的「多 select 1」vs Switchyard 的「2 选 1」：自动判定是二择，更多选择需客户端侧手动指定
4. 代码中已经实现 LMSYS RouteLLM（矩阵分解学习型 router）的集成接口——「训练好的 router 消失」只是暂时，学习型的容器已备好

### 结语

NeMo Switchyard 在 Mac 和 DGX Spark 上的验证表明：LLM Router 时代的两个核心痛点——model 名忽略和 /effort 暴发——已经被彻底解决。前者通过 profile/target ID 体系官方案，后者通过转换层设计从结构上消除。

pip 安装、无需 GPU、Claude Code 一键连接、DGX Spark 完全本地路由。虽然还是 Alpha 版的粗糙阶段，但相比 LLM Router「fork Blueprint 自己养」的重模式，入门门槛已大幅降低。
