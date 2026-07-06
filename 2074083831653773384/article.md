<div style="background:#e8f4fd;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:18px;">
<div style="text-align:center;margin-bottom:10px;">
<strong style="font-size:16px;color:#1a6ba0;">要点速览</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
- <strong>七芯片协同时代</strong>：Rubin平台不再只是升级GPU单芯片，而是通过六颗核心芯片协同设计，实现了"机柜即计算机"的根本转变<br><br>
- <strong>五大核心升级</strong>：HBM4显存带宽22 TB/s、自研Vera CPU性能翻倍、NVLink 6带宽3.6 TB/s、无缆化全液设计、800V高压直流供电<br><br>
- <strong>跨代参数对比</strong>：从Blackwell Ultra、Vera Rubin NVL72到2027年的Rubin Ultra NVL576，三代产品完整横向对比<br><br>
- <strong>算力平替建议</strong>：70B以下模型Blackwell仍是主力，200B以上深度推理才需要Rubin
</div>
</div>

---

NVIDIA刚刚发布的Vera Rubin平台，可以说是英伟达历史上架构变化最大的一次迭代。从Blackwell到Rubin，不完全是一颗GPU芯片的升级，而是整个机柜六颗核心芯片的全面协同重构：CPU、GPU、NVLink交换机、网卡、DPU、以太网交换机，全部出自英伟达自己，装在一个无缆化的全液冷机柜里，插上电就是一台巨大的单一计算机。

本文来自X上的独立分析师「老马投资研究」，以Vera Rubin NVL72为中心，和上一代Blackwell Ultra (GB300 NVL72) 以及2027年即将登场的Rubin Ultra (Kyber NVL576) 做了全面的横向对比。以下是核心内容梳理。

## 核心规格：三代产品全景对比

为了直观展现跨代跃升，需要把三代产品放在一起看：**现役Blackwell Ultra（GB300 NVL72）**、**2026年下半年出货的Vera Rubin NVL72**，以及 **2027年的终极版本Rubin Ultra（Kyber NVL576）**。

由于原文提供了详细的参数表，我们直接聚焦几个最核心的跨代数据：

| 维度 | Blackwell Ultra (GB300 NVL72) | Vera Rubin NVL72 | Rubin Ultra (Kyber NVL576) |
|------|------|------|------|
| GPU 数量 | 72 | 72 | 576 |
| 显存技术 | HBM3e | HBM4 | HBM4e |
| 显存带宽 | 8 TB/s | 22 TB/s | 预计更高 |
| 单 GPU 显存 | 288 GB | 288 GB | 1 TB |
| CPU | Grace (ARM Neoverse V2) | Vera (自研 Olympus 88核) | Vera (升级版) |
| GPU 互连 | NVLink 5 (1.8 TB/s) | NVLink 6 (3.6 TB/s) | NVLink 6 |
| 机柜互连总带宽 | 130 TB/s | 260 TB/s | 更高 |
| 功耗 | ~140 kW | ~200 kW | ~600 kW |
| 供电 | 48V | 800V DC | 800V DC |
| 出货时间 | 已出货 | 2026 H2 | 2027 |

一个最直观的数字：单芯片显存带宽从Blackwell的8 TB/s跃升到Rubin的22 TB/s，接近3倍增长。这背后是HBM4总线位宽从1024-bit直接翻倍到2048-bit。

## 五大核心升级详解

### 1. 显存：HBM4开启带宽倍增时代

Blackwell用的是HBM3e，在位宽和频率上都已接近极限。当万亿参数的MoE模型需要在GPU之间高频路由token时，显存带宽率先成为瓶颈。

Vera Rubin引入HBM4，总线位宽直接翻倍到2048-bit，单芯片带宽达到22 TB/s。这还不算完：2027年的Rubin Ultra更进一步，单颗GPU的HBM4e显存飙升至1TB，理论上彻底消除了显存容量对万亿参数模型推理的限制。

### 2. Vera CPU：英伟达第一次完全自研的服务器CPU

这是一个被低估的升级。Blackwell时代的Grace CPU是基于ARM公版架构Neoverse V2改造的，到了Rubin时代，英伟达拿出了完全自研的Vera CPU。

Vera CPU搭载88个自研Olympus核心，支持176线程。单瓦性能是Grace的2倍。更关键的是连接方式：通过NVLink-C2C技术，CPU和GPU之间的双向互连带宽翻倍到1.8 TB/s，CPU几乎可以瞬时读取GPU显存。在超长上下文推理的场景下，这意味着CPU作为「数据搬运」的瓶颈被大幅削弱。

### 3. NVLink 6：MoE推理的通信生命线

在NVL72架构中，72颗GPU通过36颗NVLink 6交换芯片实现了全对全互联。每颗GPU的双向带宽从Blackwell的1.8 TB/s翻倍到3.6 TB/s，整个机柜内部总带宽高达260 TB/s。

为什么带宽翻倍这么重要？因为MoE模型的推理过程中，token需要在不同专家GPU之间高频路由。NVLink 5时代，这个路由过程有可感知的延迟：做多步推理时，通信延迟会叠加。NVLink 6的2倍多对多通信吞吐量，确保延迟完全可预测，这对agentic AI场景至关重要。

### 4. 六芯片极简协同：从线缆混乱到无缆化模块

Blackwell机柜最大的痛点之一是布线。计算托盘、交换机、电源层之间的线缆错综复杂，组装时间长、故障点多。

Vera Rubin NVL72的全新Compute Tray内集成了两颗Vera CPU和四颗Rubin GPU，采用无电缆、无软管、无风扇的全液冷设计。六颗芯片都出自英伟达自己：Rubin GPU、Vera CPU、NVLink 6交换机、ConnectX-9超级网卡、BlueField-4 DPU、Spectrum-6以太网交换机。整个机柜约130万个元件，像一台插上电源就能运转的巨型计算机，而不是一堆需要拼装的零件。

### 5. 供电革命：800V高压直流

单颗Rubin GPU的功耗可能直奔1800W-2300W，整个NVL72机柜突破200kW。2027年的Rubin Ultra搭载576颗GPU，功耗会突破600kW。

48V供电在这个量级下，线缆发热和配电损耗已经不可接受。英伟达在Rubin世代全面转向 **800V高压直流供电**：这是数据中心供电架构的根本性变革，不仅影响英伟达自己的机柜，也会倒逼整个数据中心基础设施升级。

## 实际应用：什么时候需要Rubin？

英伟达官方对Rubin和Blackwell的定位很清晰：

- **70B参数以下的主流模型推理**：Blackwell (GB200/GB300) 依然是性价比极高的选择，不需要为用不到的能力付溢价
- **200B参数以上的深度推理**：涉及多步骤逻辑推理、超长上下文（32K输入/8K输出）、Agentic AI的场景，Vera Rubin的每百万Token推理成本降至Blackwell的十分之一
- **万亿参数MoE训练**：Vera Rubin仅需Blackwell四分之一的GPU数量即可完成相同规模的训练

简而言之，如果你的业务目前跑在70B上，Blackwell够用。如果你已经在思考200B以上模型的推理效率或者训练成本，Rubin的量变到质变就在这里。

<div style="background:#f5f0eb;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:16px;">
<div style="text-align:center;margin-bottom:8px;">
<strong style="font-size:15px;color:#8b6f4c;">结语</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
与其说Rubin是Blackwell的换代产品，不如说英伟达在重新定义「一台计算机」的边界。Blackwell时代，「一台计算机」还是一颗芯片 + 一颗CPU；Rubin时代，「一台计算机」是一个装满72颗GPU、36颗CPU、6种不同芯片的完整机柜。<br><br>
这种变化意味着什么？AI基础设施的采购单位，将从「买了多少张卡」变成「买了多少个机柜」。对云厂和大型企业来说，资本支出的颗粒度变大了很多：但你买到的不是散件，而是一台能直接通电运转的巨型机器。<br><br>
有意思的是，英伟达并没有抛弃上一代。70B以下的推理，Blackwell依然是性价比之王。Rubin的真正价值在大模型、深推理、超长上下文的场景：这些场景现在看起来占比不大，但Agentic AI和深度推理正在快速成为主流。
</div>
</div>

---

<span style="font-size:12px;color:#888888;font-family:'Courier New',monospace;">参考：https://x.com/LMDFinance/status/2074083831653773384</span>
