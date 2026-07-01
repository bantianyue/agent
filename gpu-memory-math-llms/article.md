<div style="background:#e8f4fd;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:18px;">
<div style="text-align:center;margin-bottom:10px;">
<strong style="font-size:16px;color:#1a6ba0;">要点速览</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
- <strong>显存计算核心公式</strong>：VRAM（GB）≈ 参数量（B）×（每权重有效位数 ÷ 8），一个公式覆盖 FP16、FP8、4-bit、GGUF 所有格式<br><br>
- <strong>速记口诀</strong>：FP16 = 2 倍模型大小，FP8 = 1 倍，4-bit = 0.5 倍<br><br>
- <strong>权重只是冰山一角</strong>：KV cache、激活值、批处理、框架开销才是真正的显存杀手，预算至少多留 10–30%<br><br>
- <strong>MoE 陷阱</strong>："8x7B"不是 56B——总参数决定内存占用，活跃参数决定推理速度，两者不能混为一谈
</div>
</div>

**一张公式搞定 LLM 显存计算：FP16 到 4-bit 全适用**

如果你在本地跑模型，迟早会碰到这个问题：这个模型我的显卡能装下吗？

大多数人靠查表——7B 模型 FP16 要 14 GB，4-bit 只要 3.5 GB，70B 模型……然后开始心算。但一旦你考虑到权重是怎么训练和量化的，这种"模型→VRAM"的对应关系就不够用了。

有一个更好的思考方式：

> **VRAM（GB）≈ 参数量（B）×（每权重有效位数 ÷ 8）**

**这一个公式能解释所有格式。** FP16、BF16、FP8、INT8、GPTQ、AWQ、NF4、GGUF 变体——基本上你用的每一种。

**你真正需要的唯一换算**

核心直觉其实很简单：

- FP16 / BF16 → 16 位 → 每 1B 参数约 2 GB
- FP8 / INT8 → 8 位 → 每 1B 参数约 1 GB
- 4 位量化 → 约 4 位 → 每 1B 参数约 0.5 GB

GGUF 格式介于之间，取决于具体方案：

- Q6_K → 每 1B 约 0.82 GB
- Q5_K → 每 1B 约 0.69 GB
- Q4_K → 每 1B 约 0.56 GB
- Q3_K → 每 1B 约 0.43 GB
- Q2_K → 每 1B 约 0.33 GB

超激进量化可以更低，但质量损失也在加大。

**如果你只记住一件事：FP16 = 2 倍模型大小，FP8 = 1 倍，4-bit = 0.5 倍。** 其他一切只是这个主题的变体。

**没人谈论的显存税**

在你算权重之前，先明白这一点：**模型本身只是你显存账单的一部分。真正的杀手是它周围的一切。**

KV cache 随上下文长度增长，在 32K、128K 或更高时会悄悄吞噬你的内存。激活值因运行时和优化级别而异，但在某些执行路径下可能飙升。**批处理和并发会快速倍增内存使用，尤其是在 Agent 风格的工作负载中。** 框架开销也因运行时不同——Transformers、vLLM、TensorRT-LLM、llama.cpp 各有各的账。还有 CUDA Graphs，用额外预留内存换取更好的延迟和吞吐量稳定性。

**底线：如果你只为权重做预算，你已经内存不足了。**

**实际中是什么样**

把公式套到真实模型上：

一个 7B 模型：FP16 → 约 14 GB，FP8 → 约 7 GB，4-bit → 约 3.5–4 GB

一个 13B 模型：FP16 → 约 26 GB，FP8 → 约 13 GB，4-bit → 约 6–7 GB

一个 70B 模型：FP16 → 约 140 GB，FP8 → 约 70 GB，4-bit → 约 35–40 GB

一个 405B 模型：FP16 → 约 810 GB，FP8 → 约 405 GB，4-bit → 约 200+ GB

**现在你明白为什么人们要么激进量化，要么跨 GPU 分片，要么干脆说"上云吧"。**

![](img1.jpg)

**GPU 现实：实际能装下什么**

以下是针对常见显卡的实用换算：

8 GB VRAM：约 3B FP16 / 约 6–7B FP8 / 约 12–13B 4-bit

12 GB VRAM：约 5B FP16 / 约 10B FP8 / 约 18–20B 4-bit

16 GB VRAM：约 7B FP16 / 约 13B FP8 / 约 25B 4-bit

24 GB VRAM：约 10–12B FP16 / 约 20B FP8 / 约 35–40B 4-bit

48 GB VRAM：约 20–24B FP16 / 约 40B FP8 / 约 70–80B 4-bit

80 GB VRAM：约 35–40B FP16 / 约 70B FP8 / 约 140B 级 4-bit

**为什么你的模型还是崩**

即使数学上算出来装得下，你仍然可能内存不足。**因为权重只是故事的一部分。**

你还需要为以下内容预留内存：KV cache（长上下文时急剧膨胀）、激活值（取决于运行时）、批处理/并发、框架开销。

**经验法则：额外加 10–30% 的 VRAM 来安全运行。** 如果你在做长上下文（32K、128K 等）、高并发或 Agent 工作流，你还需要更多。

**MoE 陷阱**

混合专家模型让人困惑。**"8x7B"听起来像 56B，但每个 token 只运行一部分专家。** 所以计算成本 ≠ 内存成本。

重要的是：**总参数影响内存占用，活跃参数影响推理速度。** 取决于模型如何加载，你可能仍然需要所有专家的内存，或者你可以将它们分片到多个 GPU。把 MoE 当密集模型处理，你要么严重高估要么严重低估。

**GGUF 不是魔法**

GGUF 被当作作弊码来对待。**但它不是。**

它是一个容器 + 量化策略，针对 llama.cpp 风格的推理、CPU + GPU 混合设置和超高效内存使用做了优化。**但那些内存数字只在该运行时中有效。** 一旦你进入其他框架，权重可能被反量化，内存使用可能急剧增加。

所以"6 GB 装得下"不是普遍真理。它是运行时特定的真理。

**唯一重要的思维模型**

没有你需要记住的巨大的兼容性矩阵。只有这个：

> **VRAM ≈ B × (bits ÷ 8)**

然后调整运行时开销、KV cache 和并发。

**一旦你内化了这个公式，你就不再猜测。你开始设计系统。** 更重要的是，你不再问"我能运行这个吗？"——你开始问"我想怎么运行这个？"

这时候事情才变得有趣。

<div style="background:#f5f0eb;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:16px;">
<div style="text-align:center;margin-bottom:8px;">
<strong style="font-size:15px;color:#8b6f4c;">结语</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
这篇文章最值钱的部分不是那些数字表格——网上到处都能查到。真正有用的是那个简单的思维模型：VRAM ≈ B × (bits ÷ 8)。一旦你接受了这个框架，量化格式之间的换算就不再是查表题，而是心算题。<br><br>
但文章也点明了"权重只是起点"。KV cache 在长上下文下的膨胀速度才是本地推理真正的瓶颈——32K 上下文下 70B 模型的 KV cache 就能吃掉 5–8 GB。这也是为什么 TurboQuant 这类 KV cache 压缩技术（3–6 倍压缩）在实际部署中比模型量化本身更关键。<br><br>
把"能装下"和"能跑好"分开想——从这步开始，你就不再是照着教程跑模型的人了。
</div>
</div>

---
<span style="font-size:12px;color:#888888;">参考：

https://x.com/TheAhmadOsman/status/2040103488714068245</span>
