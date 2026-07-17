# 素材清单 / 要点速览 / 独立观点

## 一、图片清单（与 Step2 下载一一对应，10 张独立图）

| 文件 | Figure | 说明 |
|------|--------|------|
| flops_vs_seqlen.png | Figure 1 | Attention FLOPs & KVCache vs seqlen（a: FLOPs, b: KVCache）— Hybrid SWA 比 Full Attention 约 1/7 |
| kv_cache_vs_seqlen.png | Figure 2(a) | KVCache 内存 vs 序列长度（<500B 组） |
| kv_cache_group1.png | Figure 2(a) | Models under 500B parameters |
| kv_cache_group2.png | Figure 2(b) | Models over 500B parameters |
| layerwise_kvcache_prefetch.png | Figure 3 | 分层 KVCache 预取示意 |
| swa_aware_prefix_cache.png | Figure 4 | SWA 感知前缀缓存树 |
| x1.png | Figure 5 | GCache 架构图 |
| ttft_compare.png | Figure 6 | FCFS vs 本文策略 TTFT 对比 |
| prefill_throughput.png | Figure 7 | 不同前缀长度下相对 prefill 吞吐 |
| expert_balance.png | Figure 8 | 每层 expert 均衡（mean/max） |

> 注：Figure 2 含子图 a/b，原文三张图（kv_cache_vs_seqlen / group1 / group2）共用"Figure 2"编号。按铁律图↔注一一对应，写文时 Figure 2 用一张代表图（kv_cache_group1.png）并在图注说明对比组，其余两张作为补充嵌入同节。

## 二、关键数据（来自原文，写文时直接引用）

- Hybrid SWA：KVCache 压缩到约 1/7 Full Attention；总计算量约 1/7
- MiMo-V2.5-Pro：70 层 = 10 Full Attention + 60 SWA，窗口 128
- KVCache 双池设计：容量效率 +7×
- EP 减半（因只需存窗口内 token）→ 端到端性能 +40%
- NUMA 冲突修复 → 端到端 +10%
- Decode KVCache SWA 支持 → 有效容量 ~5×
- MTP：0–128 token 加速 2.3×，128–256 加速 1.5×
- 视频解码 156s → 23s（1 小时视频）
- KVCache 命中率：主流 harness 框架平均 93%，重度用户 95%+
- KVCache 亲和调度：L2 命中率 +25%，单节点输入吞吐 +30%
- TTFT：长请求 P90 最多降 30%
- GCache RDMA：1MB IO 单进程 170 GB/s @ 280μs；GDR 场景 ~350 GB/s
- Encoder 一致性哈希：多模态缓存命中率 +30%
- 三级长度分桶：0–64K / 64K–256K / 256K–1M

## 三、要点速览（放文首，≤50 字/条，2~5 条）

1. **Hybrid SWA 把 KVCache 压到全注意力的 1/7**，但收益不会自动变现——需 KVCache 系统级重构。
2. **KVCache 双池 + SWA 感知前缀树 + 分层预取**，系统级兑现 O(W) 存储约束，容量效率 +7×。
3. **GCache 分布式缓存**（RDMA 350 GB/s、零额外存储成本）让命中率冲到 93%~95%。
4. **EP 减半 / 长度分桶 / MTP 预填充** 等组合拳，端到端 prefill +40%、长请求 TTFT P90 降 30%。
5. **视频解码 156s→23s、Encoder 吞吐翻倍**，多模态推理不再是长视频/大图瓶颈。

## 四、独立观点（仅放文末结语，不分散）

- Hybrid SWA 的架构优势是「纸面红利」，真正落地靠的是 KVCache 管理、分级缓存、前缀树、调度、PD 流水线的全链路工程，而非单点 trick。小米把这做成了一套协同优化方法论，并通过开源 PR + API 降价把红利外溢——这对行业探索「高性能+高效率」复合架构是稀缺的工程样本。
