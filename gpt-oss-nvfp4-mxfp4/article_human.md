<div style="background:#e8f4fd;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:18px;">
<div style="text-align:center;margin-bottom:10px;">
<strong style="font-size:16px;color:#1a6ba0;">要点速览</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
- <strong>两种4位格式本质不同</strong>：MXFP4是OCP开放标准（32元素块），NVFP4是NVIDIA Blackwell原生格式（16元素块），块结构差异决定能否走原生张量核<br><br>
- <strong>GPT-OSS-120B已能塞进DGX Spark</strong>：MXFP4下仅占65.2GB，优化不是为了装得下，而是为了跑得快<br><br>
- <strong>闭式转换零重训</strong>：Model Optimizer 0.45的 --cast_mxfp4_to_nvfp4把权重逐位精确转成NVFP4，多数块质量无损<br><br>
- <strong>核心假设待验证</strong>：原生NVFP4能否在零质量损失下换来可测量的吞吐提升，这是整个10模型系列的第1天基线
</div>
</div>

---

GPT-OSS-120B是HuggingFace上下载量最高的模型，430万次下载，1170亿参数，每个token激活51亿。它原生以MXFP4格式发布，已经能把模型塞进65.2GB，完全落在DGX Spark 128GB统一内存预算之内。

这听起来已经很完美了。那为什么还要优化它？

**因为MXFP4不是NVFP4。** 而在DGX Spark的GB10 Grace Blackwell芯片上，这个区别极其关键。GPT-OSS-120B已经能装下，真正的变量是：它能不能在硬件上原生跑，而不是被模拟。

![](img1.jpg)
<span style="font-size:12px;color:rgb(153,153,153);">NVFP4与MXFP4格式对比示意（来源：X @MichaelGannotti）</span>

## 两种格式

MXFP4和NVFP4都是4位浮点格式，两者都把模型权重压缩到相同的理论体积。但它们使用不同的块结构，而这个差异决定了硬件能否原生运行，还是必须模拟。

## MXFP4：OCP标准

MXFP4（Microscaling FP4，微缩放FP4）是Open Compute Project的标准4位格式。它使用32元素块，带一个共享的E8M0微指数。块内每个元素是一个E2M1尾数（1个符号位、2个指数位、1个尾数位）。共享指数覆盖一组32个权重，该格式被设计为硬件无关，任何实现OCP MX规范的加速器都能运行它。

GPT-OSS以这种格式发布，因为OpenAI选择了开放标准。它能在AMD NPU、Intel加速器、NVIDIA GPU上运行，但在NVIDIA Blackwell上，它走的是模拟路径，而非原生张量核操作。

## NVFP4：NVIDIA的原生格式

NVFP4是NVIDIA的4位格式，专为Blackwell张量核设计。它使用16元素块，每块带一个E8M0缩放因子。每个元素是相同的E2M1尾数，但块的大小只有一半，即16个权重而非32个。更小的块尺寸意味着更细粒度的缩放，可以提升精度，并且该格式直接映射到Blackwell的原生FP4张量核指令。

NVIDIA自家的模型（Nemotron、Llama FP4检查点、DeepSeek-R1-FP4）使用NVFP4。当你在DGX Spark上运行NVFP4时，张量核在硬件层面原生执行算术运算，没有模拟，没有回退。

## 为什么这在DGX Spark上很重要

DGX Spark由GB10 Grace Blackwell超级芯片驱动，拥有128GB统一LPDDR5X内存。Blackwell GPU部分原生支持NVFP4张量核，能在硬件层面执行FP4矩阵乘法。MXFP4虽然也是4位，但使用了不同的块结构（带微指数的32元素块），无法直接映射到NVFP4硬件路径。

这带来三点差异：

**相同的内存占用。** 两种格式都以4位存储权重。MXFP4下的GPT-OSS-120B是65.2GB，转成NVFP4大约也是65GB，转换不会带来内存节省。

**可能不同的吞吐量。** NVFP4命中原生张量核硬件，MXFP4可能走模拟路径。问题是原生硬件路径能否在推理时带来可测量的加速。

**质量影响。** 块结构差异（每块16对32个元素）意味着量化粒度不同。NVFP4更小的块可能带来更好的精度，也可能在转换中引入伪影。除非测量，否则无从得知。

## 转换：MXFP4到NVFP4

NVIDIA Model Optimizer 0.45包含一个闭式转换操作，无需重新校准就能把MXFP4权重转换为NVFP4。--cast_mxfp4_to_nvfp4标志告诉hf_ptq.py读取源MXFP4缩放因子，并生成逐位精确的NVFP4权重导出。

<div style="background:#f0f7fa;padding:16px 18px 14px 18px;border-radius:6px;margin:16px 0;border-left:4px solid #5b9bd5;">
<div style="font-size:15px;color:#2c6a9e;line-height:1.7;">
关键细节在于：对于MXFP4缩放指数落在E4M3可表示窗口内（k_max - k_j ≤ 17）的块，NVFP4的反量化与MXFP4反量化逐位一致，这些块没有质量损失。对于缩放因子落在该窗口之外的块，转换回退到数据驱动的逐块amax，即少数需要略微不同缩放方式的块。
</div>
</div>

这不是重新量化，而是格式转换。权重本身不变，只有块结构和缩放表示变了。对于大多数块，结果是完全相同的。

## 我们在测量什么

这是优化研究系列的第1天。优化不是为了塞进去，模型已经能塞进去了，优化是为了原生硬件格式。以下是测量的内容：

**各能力质量。** SMF-Bench，181项测试，8个类别：推理、数学、编程、指令遵循、散文、写作、工具调用、智能体。将NVFP4转换的质量与MXFP4基线对比。如果转换对大多数块真正逐位精确，质量应该不变，但「应该」不是「是」，所以要测。

**吞吐量（tokens/秒）。** 如果NVFP4命中原生张量核路径，而MXFP4走模拟，预期会有吞吐量差异。主要假设就是：原生格式换来速度。

**内存占用。** 应该相同（约65GB），验证格式转换没有带来额外开销。

**上下文长度。** 两种格式应支持相同上下文窗口，在32K和64K下测试。

**稳定性。** 模型在持续推理下能否撑住，没有OOM、没有崩溃、没有随时间退化。

## 更大的图景

GPT-OSS-120B是系列里最简单的模型，也是最有希望干净完成优化的一个，因为格式转换有良好支持，且模型已经能塞进去。从这里开始的意义是建立基线：一次干净格式转换在质量和吞吐量上的代价（或零代价）是什么？

答案将为系列其余部分定调。第2到第5天在没那么容易塞进去的模型上测试单技术优化（Mixtral-8x22B 281GB、Mistral-Large-2411 490GB）。第6到第8天需要组合技术（NVFP4 + KV缓存量化、专家剪枝）。第9到第10天需要完整流水线，剪枝、蒸馏和量化，来塞进那些超出Spark内存3到5倍的模型。

如果GPT-OSS-120B的转换显示仅靠格式转换就能在零质量损失下换来可测量的吞吐量，这是一个值得发布的发现。如果它暴露出意外的质量退化，那同样值得发布，并且能告诉我们关于该转换边界情况的一些事。

## 技术细节

**模型：** openai/gpt-oss-120b，1170亿参数，MoE含128个专家、每token激活4个（32:1稀疏度），36层，隐藏维度2880，上下文长度131072，Apache 2.0许可，430万次下载。

**工具：** NVIDIA Model Optimizer 0.45，hf_ptq.py，参数 --qformat nvfp4_mlp_only --cast_mxfp4_to_nvfp4。

**硬件：** 单台NVIDIA DGX Spark（GB10 Grace Blackwell，128GB统一LPDDR5X，ARM64）。

**基准：** SMF-Bench，跨8个能力类别的181项测试，带确定性评判。

**部署：** vLLM，参数 --quantization modelopt，提供导出的统一HF检查点。

这是「优化不可优化之物」的第1天，一个每日发布的10模型系列。明天是Mixtral-8x22B，系列中第一个在任何地方都没有现成NVFP4版本的模型，目前正在创造它：1410亿参数，281GB BF16，压缩到预计79GB。

<div style="background:#f5f0eb;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:16px;">
<div style="text-align:center;margin-bottom:8px;">
<strong style="font-size:15px;color:#8b6f4c;">结语</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
这篇文章的价值不在结论，而在方法论的诚实：它把「应该无损」和「实测无损」严格分开。大多数量化科普止步于「格式转换理论上等价」，而作者偏要上SMF-Bench、上吞吐量、上32K/64K上下文逐项量一遍。<br><br>
NVFP4与MXFP4的块结构之争，本质是开放标准与厂商原生硬件的张力。OpenAI选OCP换取跨平台可移植性，代价是在Blackwell上只能走模拟；NVIDIA用自家的16元素块换原生性能，代价是生态锁定。<br><br>
真正值得盯的是第2到第10天：当模型大到塞不进128GB时，单纯格式转换不再够用，NVFP4必须和剪枝、蒸馏、KV量化组合。GPT-OSS-120B这第1天的干净基线，恰恰是为了衬托后面那些「不干净」的硬仗。
</div>
</div>

---

<span style="font-size:12px;color:#888888;font-family:'Courier New',monospace;">参考：https://x.com/MichaelGannotti/status/2074552763326091381</span>
