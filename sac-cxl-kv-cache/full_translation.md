SAC: Disaggregated KV Cache System for Sparse Attention LLMs with CXL

Ruiyang Ma (Peking Univ), Teng Ma (Alibaba Cloud), Junru Li (Alibaba Cloud), Hantian Zha (Renmin Univ), Xuchun Shang (Alibaba Cloud), Qingda Hu (Alibaba Cloud), Zheng Liu (Alibaba Cloud), Xinjun Yang (Alibaba Cloud), Tao Ma (Alibaba Cloud), Guojie Luo (Peking Univ)

Abstract: LLM 长上下文推理→瓶颈从计算转移到内存。RDMA 解耦存储池把完整 prefix KV cache 全量拉到本地，对稀疏注意力模型（如 DeepSeek-V3.2）极度低效——解码时只有少量 KV 条目活跃，却要拉全部。SAC 用 CXL（Compute Express Link）的 cache-line 粒度 load/store 语义，按需只取 top-k KV 条目。在 DeepSeek-V3.2 + SGLang 上：2.1×更高吞吐、9.7×更低 TTFT、1.8×更低 TBT。

1 Introduction
LLM 参数快速增长+长上下文推理→瓶颈从计算→内存。RDMA 解耦 KV cache 系统成为标准方案。但对稀疏注意力模型（DeepSeek-V3.2, GLM-5.1, DeepSeek-V4），只有少数 KV 条目活跃，RDMA 仍全量取所有 KV cache，带来两个问题：
(P1) 传输瓶颈：稀疏注意力吞吐受 batch size 限制而非计算能力。长上下文 KV cache 达几十 GB，高并发下 RDMA 传输队列延迟严重。
(P2) 本地内存浪费：解码时只有 top-k KV 条目被使用，但完整 prefix KV cache 必须导入本地内存。需要 TB 级本地内存维持高并发。

直观方案：只传需要的 top-k KV 条目。但对 RDMA 不可行——(1) top-k 索引运行时动态确定，RDMA 延迟无法满足实时要求；(2) 稀疏 top-k 条目是离散小块数据，RDMA 需数十次独立请求。

CXL（Compute Express Link）提供新机会：基于 PCIe 物理层+精简协议栈，延迟显著低于 RDMA；支持 cache-line 粒度 load/store 语义，零消息协议开销，天然适合细粒度稀疏读取。

SAC 方案：KV cache 存储在解耦 CXL 内存中，多服务器共享。利用近 DRAM 延迟+细粒度 load/store，解码时实时取 top-k KV 条目。消除传输瓶颈(P1)和本地内存浪费(P2)。

评估：DeepSeek-V3.2 + SGLang，上下文 16K-128K。相比 RDMA：2.1×更高吞吐，9.7×更低 TTFT，1.8×更低 TBT。相比非解耦上限仅降 9%。

2 Background
2.1 稀疏注意力：DeepSeek Sparse Attention(DSA)用 Lightning Indexer 动态计算相关性分数，只取 top-k(2048) KV latent vectors 做 MLA 计算。复杂度从 O(L²)降到 O(kL)。

2.2 解耦内存：RDMA解耦系统(MoonCake, LMCache)用 CPU 驱动 RDMA 取远程数据。延迟微秒级。对稀疏 KV 访问——每层需独立读取小块数据——RDMA 协议栈开销不可接受。

2.3 CXL：基于 PCIe 物理层的新型互连协议。Type-3 内存设备通过 CXL.mem 协议实现内存扩展。CXL 2.0/3.0 交换机支持多节点共享。相比 RDMA，CXL 数据路径更简单，硬件管理 load/store 语义，cache-line 粒度访问，延迟接近本地 DRAM。

现有工作 Beluga 和 TraCT 针对密集注意力模型做 prefix KV cache 管理（全量预取）。稀疏注意力模型需要每层按需读取。

3 Motivation
3.1 RDMA 瓶颈
P1 传输瓶颈：KV cache 块传输消耗 RDMA 带宽。高并发下延迟达数十秒。
P2 本地内存浪费：128K 上下文仅 21% 的 KV cache 被实际使用。DeepSeek-V3.2 每请求需 9.2GB(128K 上下文)，维持高并发需 TB 级内存。

3.2 稀疏 KV 访问延迟对比
CXL 解耦内存延迟为本地 DRAM 的 1.04-1.64×。RDMA 延迟为 DRAM 的 4-19.7×，达毫秒级。RDMA 做实时 top-k 取不可行。

4 System Design
4.1 SAC Workflow
三组件：(1) Prefill Instance——计算预填充阶段，KV cache 写入 CXL；(2) Decode Instance——基于 HiSparse 框架，每层注意力从 CXL 直接取 top-k KV；(3) CXL Disaggregated KV Cache System——管理 KV cache 和元数据，全局 CXL 地址空间。

4.2 System Topology
XConn XC50256 CXL 交换机芯片(256 PCIe 5.0 lanes)，512 GB/s 总带宽，连接 8 台服务器。每服务器通过 PCIe 5.0 x16 适配器连接 CXL 交换机。

4.3 CXL KV Cache Management
- 统一 CXL 内存资源：天然局部性透明+基于 CXL 的元数据管理（全局共享内存替代 RPC）
- CXL 操作实现：DAX 设备→mmap→cudaHostRegister，GPU 读写用 vectorized load/store
- 带宽优化：CXL device interleaving，轮询分配请求到不同 CXL 设备，减少竞争，提升 9.2%

5 Evaluation
硬件：8×H20 GPU + 2TB CXL 内存池 + XConn CXL 交换机
软件：SGLang + HiSparse，DeepSeek-V3.2 (AWQ 4-bit)

5.1 端到端对比
Round-1 (Cache Populate)：CXL 和 RDMA 表现接近（都算新生成的 KV cache）
Round-2 (Cache Hit)：SAC 显著优于 RDMA——吞吐 2.1×，TTFT 9.7×更低，TBT 1.8×更低
SAC 达到本地 DRAM 上限的 91%

5.2 吞吐可扩展性
32K 上下文：SAC 吞吐 RDMA 的 2.0×
64K 上下文：SAC 吞吐 RDMA 的 2.5×
128K 上下文：SAC 吞吐 RDMA 的 3.1×
RDMA 因全量取 KV cache 快速达到吞吐平台

5.3 非解耦基线对比
SAC 接近本地 DRAM 基线。GPU HBM-only 在低并发下更好，但高并发下 HBM 容量受限。

5.4 CXL Device Interleaving
双设备交错比单设备提升 9.2%，峰值 14.2%(128K 上下文)

5.5 HiSparse 配置影响
device_buffer_size 6K vs 4K：吞吐提升 10.4%

6 Discussion
DeepSeek-V4 共享相同的 top-k 访问模式，可直接受益。CXL 作为内存语义互连正成为 LLM 服务基础设施的关键基石。

7 Conclusion
SAC 用 CXL 替代 RDMA，按需取 top-k KV 条目，消除传输瓶颈和本地内存浪费。相比 RDMA：2.1×吞吐、9.7×TTFT、1.8×TBT。
