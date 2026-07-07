<div style="background:#e8f4fd;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:18px;">
<div style="text-align:center;margin-bottom:10px;">
<strong style="font-size:16px;color:#1a6ba0;">要点速览</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
- <strong>PAW范式</strong>：自然语言规格→4B编译器→LoRA权重文件，冻结解释器本地执行，一次编译多次离线调用<br><br>
- <strong>0.6B超32B</strong>：FuzzyBench精确匹配73.78% vs Qwen3-32B提示68.70%，推理内存仅1/50<br><br>
- <strong>两半结构</strong>：离散伪程序去噪+连续LoRA控行为，编译器即去噪器<br><br>
- <strong>端侧可跑</strong>：量化后单程序23MB，MacBook M3上30 token/s，GPT-2路径可浏览器WASM运行
</div>
</div>

---

## 模糊函数与PAW

模糊函数指直觉明确但无法用符号规则完整捕捉的任务（日志过滤、格式修复、意图排序等）。当前解法外包给LLM API，代价是贵、不可复现、不自包含。

PAW（Program-as-Weights）将其编译为权重文件：开发者写自然语言规格，神经编译器产出小型神经二进制，冻结解释器本地执行，像调用库函数一样离线复用。

![](img2.png)
<span style="font-size:12px;color:rgb(153,153,153);">图1：PAW范式。云端编译一次（规格→神经程序），本地解释器加载程序处理输入→输出，产物为可缓存、版本控制、离线调用的单文件</span>

## 程序的两半

PAW程序是离散+连续的混合体。

离散半为自然语言**伪程序**（规格重述+少量I/O样例），屏蔽规格中的错别字与歧义。连续半为**PEFT模块**（LoRA），由编译器从隐藏状态生成并注入冻结解释器，提供文本无法表达的细粒度行为控制。

## 编译流水线

两段式，均基于4B Qwen3。

伪编译器（现成、不训练）：模板提示将规格重写为干净伪程序。

LoRA编译器（论文训练部分）：读规格+伪程序，单次前向传播吐出LoRA。隐藏状态按深度对齐层与前缀位置均值池化→浅层MLP→投影为共享基混合系数→各目标模块LoRA。每函数约注入3850万LoRA参数。

![](img3.png)
<span style="font-size:12px;color:rgb(153,153,153);">图2：Text-to-LoRA。左：LoRA编译器读规格+伪程序+学习前缀token发射隐藏状态H；中：映射器池化H投影混合系数组合LoRA；右：冻结解释器加载伪程序热插拔LoRA自回归生成</span>

PEFT对比：前缀微调（KV缓存）50.4%，LoRA秩64达65.7%，无编译器提示基线仅9.8%。后续均基于LoRA。

## 主结果：0.6B超32B

| 方法 | 解释器 | FuzzyBench |
|------|--------|------------|
| 直接提示 Qwen3-32B | 32B | 68.70% |
| 直接提示 Qwen3-0.6B | 0.6B | 9.84% |
| **PAW（Qwen3 0.6B）** | 0.6B | **73.78%** |
| gpt-5.2（API上限） | 无 | 96.09% |

0.6B解释器跑PAW程序超32B提示5个点，推理内存约1.2GB（bf16）对60GB，差约50倍。消融证明增益来自编译器：同数据同基础同预算去编译器做全微调或固定LoRA，PAW分别高15.4与21.7个点。GPT-2 124M（无指令微调）塞入编译器LoRA后亦达54%。

## 模态泛化与鲁棒性

换模态不动解释器：文本Qwen3-4B编译器换为Qwen3-VL-4B，解释器仍用Qwen3 0.6B，图像条件全编码于VL编译器发射的PEFT模块，文本解释器未见像素。三图表任务（电路/化学/乐谱）0.6B PAW全胜更大VLM。

鲁棒性源自离散伪程序：重度噪声下准确率仅降约3.7%。绕过伪程序直喂原始规格的变体，干净输入差1.6点，重度错别字规格差拉至4.5点：**编译器本质是专职去噪器**。

## 端侧部署

PAW程序为单文件，极简Python API调用，首次下载后全本地执行无外部API。量化几乎无损：4-bit基础（约484MB）+Q4_0 LoRA（每程序约23MB）较bf16仅损1.3点；Q6_K+Q4_0与bf16不可区分。MacBook M3上Q5_K_M+Q4_0跑31.6 token/s，冷加载0.48秒。GPT-2路径可纯浏览器WASM运行。

![](img5.png)
<span style="font-size:12px;color:rgb(153,153,153);">图4：开发者接口。左：编译器将自然语言规格译为神经程序；右：解释器加载程序暴露为本地可调用函数</span>

## 落地与数据集

五个案例：事件驱动日志监控（本地分类器替代终端等待）、基于意图站点导航、语义搜索重排序、工具调用流水线（ToolCall-15上93%）、多语言猜词游戏Alien-Taboo（每语言一PAW程序，LLM仅编译时调用）。

![](img11.png)
<span style="font-size:12px;color:rgb(153,153,153);">图：Alien-Taboo多语言猜词游戏，每语言对应一个本地PAW程序</span>

FuzzyBench：gpt-5.2两阶段生成1000万例（规格→I/O对），跨29版本增量构建，覆盖800+模糊文本任务类。测试集双模型一致才保留以剔歧义样本。

<div style="background:#f5f0eb;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:16px;">
<div style="text-align:center;margin-bottom:8px;">
<strong style="font-size:15px;color:#8b6f4c;">结语</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
PAW把基础模型从「每输入求解器」重定义为「每函数工具构建器」：重活在编译时一次完成，日常全本地运行。<br><br>
离散伪程序去噪+连续LoRA控行为的两半分工，让0.6B吃下本属32B的活儿，比堆参数或提示工程更根本。<br><br>
数据集与代码全开源，下一步看编译器对接更强底座、PEFT形式演进后，本地小模型能否吃掉大块「每请求调API」场景。
</div>
</div>

---

<span style="font-size:14px;color:#888888;font-family:'Courier New',monospace;">【传送门】<br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/f05wnBex0ECquqLadXgwAg" target="_blank" data-linktype="2">Agent自进化/持续学习的三个层次：Model、Harness、Context</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/4kvRgpNrlnGJMBy8BtCDNw" target="_blank" data-linktype="2">从API到Agent：Anthropic发布Claude Managed Agents，Agent...</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/NsdT63TplKvPOWDg15N3IQ" target="_blank" data-linktype="2">Anthropic教你怎么在Claude Code中设计并使用Loop工程</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/i6aZ8u3HSCNv7o1G8Lr6wQ" target="_blank" data-linktype="2">Miles：PyTorch原生的大规模RL后训练框架</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/mqTab0qwrT95DVrxTllmcQ" target="_blank" data-linktype="2">Torch解析系列一：深入理解FX Graphs</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/_4vgKCTSir14mhtdvs7_HA" target="_blank" data-linktype="2">美团开源LongCat-2.0 (OpenRouter原Owl Alpha)解读：1.6T参数，...</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/VZRcpl6vL7riJp77ZmtSIg" target="_blank" data-linktype="2">Hermes vs OpenClaw创始人隔空互怼：假星标，抄袭，死亡威胁各种瓜</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/4Iz5SjE4D240EL4MmKrWZQ" target="_blank" data-linktype="2">OpenAI Dreaming记忆系统：从记住你到理解你</a><br>
</span>

---

<span style="font-size:12px;color:#888888;font-family:'Courier New',monospace;">参考：https://arxiv.org/html/2607.02512v1</span>
