<div style="background:#e8f4fd;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:18px;">
<div style="text-align:center;margin-bottom:10px;">
<strong style="font-size:16px;color:#1a6ba0;">要点速览</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
- <strong>问题</strong>：推理引擎要适配多模型/量化/GPU代数/厂商后端，"最好的内核"不固定，选择逻辑泄漏进模型代码和runtime，越堆越乱。<br><br>
- <strong>解法</strong>：分层API + 注册-选择机制，runtime只描述算子问题，选择器挑实现，把复杂性收拢到一处。<br><br>
- <strong>性能</strong>：AMD MI355X上GPT-OSS 120B，Gluon prefill比Triton快1.4-2.3倍，端到端输出吞吐量高1.6-3.6倍。<br><br>
- <strong>生态</strong>：AMD专用内核拆包为tokenspeed-kernel-amd，已被vLLM采用，不绑定完整TokenSpeed栈。
</div>
</div>

---

## 为什么需要内核抽象层

内核决定服务栈快慢，但"最好的内核"几乎从不固定：它取决于模型架构、张量形状、量化格式、GPU代数、厂商库，以及这次调用在服务decode还是prefill。引擎为覆盖所有情况堆出一堆路径，没有硬边界时，后端选择逻辑就会泄漏进模型代码和runtime——加新模型要改无关runtime路径，加新芯片要把设备检查贯穿模型各层。TokenSpeed-kernel的设计就是把这种复杂性收拢到一处。

## 三条设计原则

**多芯片支持是根本性的。** 系统直接理解平台能力，而不是把硬件检查当零散条件分支；同操作的多种方案通过同一选择系统竞争。

**可移植与性能共存。** 新模型先走可移植Triton路径尽快跑起来，再逐步上Gluon（AMD）或CuteDSL（NVIDIA）等特化内核。

**快速迭代靠护栏。** 精简依赖 + 独立基准 + 性能分析，让选中的内核可见，缩短从想法到落地的路径。

## 分层内核系统

runtime通过通用公开API（`mha_prefill`、`mha_decode_with_kvcache`、`moe_apply`）进入，这些API与平台无关——只描述算子问题（张量、格式、模型特征、约束），由选择器结合当前平台和已注册特征挑实现。

![](img2.png)
<span style="font-size:12px;color:rgb(153,153,153);">分层内核系统：runtime通过通用公开API进入，选择器将请求映射到后端内核</span>

后端通过 `@register_kernel` 注册进共享注册表，声明算子族/模式、平台能力、张量签名、特征、优先级。选择器过滤不兼容项、排序、返回可调用对象。结果有两个难兼得的特性：模型和runtime保持可移植（不知后端细节），内核层却高度特化（限定到精确架构/数据类型/形状）。

![](img3.png)
<span style="font-size:12px;color:rgb(153,153,153);">NVIDIA与AMD上GPT-OSS相关attention路径的注册代码片段</span>

## 数值、基准与插件

内核系统不只是分发，还提供数值检查、独立基准、性能分析工作流。同一装饰器支持树外插件注册，厂商和研究者可带特化内核而不必fork系统。CLI和程序化接口复用同一套注册表元数据，注册的内核能放进CI或调优流水线，在能力匹配时被自动选中。

![](img4.png)
<span style="font-size:12px;color:rgb(153,153,153);">数值验证与独立基准测试的CLI及程序化接口</span>

## AMD MI355X上的GPT-OSS 120B

GPT-OSS同时压attention（带sinks的MHA + 滑动窗口混合）和MoE（MXFP4专家权重 + FP8激活）。这些细节本易泄漏进runtime，TokenSpeed把它们压在公开API之下：模型代码只需传正确张量和元数据，不必知道MI355X架构、MXFP4的scale怎么排，或哪个内核最快。

![](img5.png)
<span style="font-size:12px;color:rgb(153,153,153);">GPT-OSS的公开内核API边界：runtime只描述算子问题，实现选择留在内核层</span>

## Gluon：AMD内核路径

性能关键的attention和MoE用Gluon实现——它是Triton家族的DSL，暴露CDNA4原语：异步拷贝、scaled MFMA、buffer load/store，以及显式软件流水线（多共享内存缓冲 + `async_wait` 轮转）。decode阶段靠它隐藏内存延迟、让矩阵核保持忙碌，而不把流水线细节推给TokenSpeed runtime。

![](img6.png)
<span style="font-size:12px;color:rgb(153,153,153);">Gluon attention内核代码片段，直接暴露CDNA4原语</span>

## Attention

AMD注册了prefill和分页decode的CDNA4 Gluon内核（含滑动窗口/sinks变体）。实现用分块QK/PV、在线softmax，加CDNA4特性（矩阵核做matmul、打包指令做softmax、buffer load加载K/V），并设计persistent内核在XCD间均衡负载。

![](img7.png)
<span style="font-size:12px;color:rgb(153,153,153);">attention的persistent调度逻辑示意</span>

Gluon attention在15个被测prefill形状中14个最快，整体比Triton快1.4-2.3倍，比厂商方案AITER快1.1-1.3倍。

![](img8.png)
<span style="font-size:12px;color:rgb(153,153,153);">GPT-OSS 120B在单卡MI355X(CDNA4)上的attention prefill吞吐量（TFLOP/s，越高越好）</span>

## MoE

MoE不是两个孤立GEMM，而是路由→聚集→专家GEMM→激活→组合的完整结构，Gluon围绕它整体调优。

prefill瓶颈是专家间token分布不均时保持计算单元忙碌：ragged block调度跟随实际分布，按token数/切片选tile，swizzle到XCD交错MFMA，权重用MXFP4 scale swizzling + 预混洗。decode按批大小分两条路：最小批用warp-decode融合top-k路由与gate/up投影共享一次启动；中等批切grouped GEMM复用权重tile。

结果：最小批比Triton快1.7-2.1倍、比AITER快1.1-1.6倍；中等decode区间AITER略领先，Gluon仍在其0.9倍内、比Triton快1.3-1.4倍。

![](img9.png)
<span style="font-size:12px;color:rgb(153,153,153);">GPT-OSS-120B在单卡MI355(CDNA4)上的MoE延迟：Gluon vs AITER vs Triton（越低越好）</span>

## 多芯片支持

同一套API也支持NVIDIA（Blackwell上attention走trtllm MHA、MoE用flashinfer_trtllm）。AMD和NVIDIA是同一API、注册表、选择模型背后的兄弟实现，不是两个无关栈。

## 端到端性能

AMD MI355X上GPT-OSS 120B，Gluon路径在20个被测点全部超越可移植Triton路径，输出吞吐量提升1.6-3.6倍。

![](img10.png)
<span style="font-size:12px;color:rgb(153,153,153);">GPT-OSS 120B在单卡MI355X(CDNA4)上的端到端输出吞吐量：TokenSpeed Triton后端vs Gluon后端</span>

增益不需要单独的AMD服务路径：用特化Gluon内核实现同样的公开契约、注册平台/形状约束、请求匹配时由选择器分发即可。分层设计在保留可移植基线的同时缩短优化周期。更重要的是，这些AMD内核已拆包为tokenspeed-kernel-amd，被vLLM采用，不绑定完整TokenSpeed栈。

<div style="background:#f5f0eb;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:16px;">
<div style="text-align:center;margin-bottom:8px;">
<strong style="font-size:15px;color:#8b6f4c;">结语</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
- <strong>分层抽象的价值不在"快"而在"可堆叠"。</strong> AMD专用内核能被vLLM直接复用，把内核做成与runtime解耦的一等公民，生态收益远大于单栈优化。<br><br>
- <strong>厂商抢的是"内核抽象层"身位。</strong> AMD、NVIDIA都收敛到同一套公开API背后做兄弟实现，谁定义接口谁就定义生态入口，比单点性能更易成壁垒。<br><br>
- <strong>诚实披露比营销话术更可信。</strong> 作者明写中等decode区间AITER略快于Gluon、且是持续改进点，这种不藏拙的基准呈现反而让技术拆解更可信。
</div>
</div>

---

<span style="font-size:14px;color:#888888;font-family:'Courier New',monospace;">【传送门】<br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/kJHYTWqIl2HwdUYNjG7_aw" target="_blank" data-linktype="2">Loop工程续篇：15个高赞Loop一次性拆解</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/PLNx54PxO1A0oYc47hz99g" target="_blank" data-linktype="2">Anthropic三连：Claude Opus 4.8更聪明+诚实；CC动态工作流+算力控制</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/-xmiwcQP--wVA2iihg28vg" target="_blank" data-linktype="2">Hermes Agent创始团队揭秘：会自我进化的AI智能体</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/RDycs9d7mvV3NkPkJeagxQ" target="_blank" data-linktype="2">Google Cloud发布OKF：让AI Agent真正读懂企业知识的开放格式</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/YnMyg85RydYrJvk6C5cLdQ" target="_blank" data-linktype="2">微软$25亿砸向FDE，四巨头AI军备竞赛最后一公里的FDE之战</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/0dQ7pBJ0NmFt-bOwUCQ5ew" target="_blank" data-linktype="2">Torch解析系列二：Dynamo字节码级的计算图捕获</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/o6pnSWW01pahFQelJSbSPA" target="_blank" data-linktype="2">华为「韬定律」全解析：从τ常数到4GHz麒麟</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/0zKdjRmWg3TbL5Y3HGO3fA" target="_blank" data-linktype="2">从P/D分离到A/F分离：从学术原型变成行业标准</a><br>
</span>

---

<span style="font-size:12px;color:#888888;font-family:'Courier New',monospace;">参考：https://pytorch.org/blog/lightseek-tokenspeed-kernel/</span>
