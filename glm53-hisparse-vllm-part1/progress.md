✅ 完成 (glm53-hisparse-vllm-part1)
- 源: vLLM 官方博客《GLM 5.3 Optimizations, Part 1: Hybrid HiSparse Offloading in vLLM》 (~11min 阅读)
- 主题: 稀疏-MLA 的 indexer 只 attend top-K → 可把其余 KV(除选中 token)卸到 CPU; Hybrid 进一步 GPU 够用就满驻留、吃紧才按页逐下; 三态(满/混合/零驻留)+共享 HMA 块池的热缓冲页(每请求2×top-K)
- 目标: 8×H200 单节点强装 GLM5.3, 跑满 1M 上下文(此机原不能), 更高并发; 稀疏-MLA与 indexer 各留上层仅1/4层(IndexShare)
- 复用点: HiSparse(arXiv 2608.07009) + IndexShare(2603.12201); MTP 每缓冲需 (投机token+2)×top-K, 计划收紧; v0.30 计划发布
- 正文图: 3 张官方 SVG(经本地 Chrome 渲白底): fig01 one-pool-two-requests, fig02 three-residency-states, fig03 pareto-occupancy
- 封面: og(png) 真封面; preflight ALL PASS; push media=TIqnnVEu6Oy3-wtKttGa0SQ3iIE2uHuH1CL9NNkvBWwPvEXyixcGzS5c_bevwu4E; verify body 3/3; arbiter(queue jid_20260909_174443_3078fb) done
source: https://vllm.ai/blog/2026-09-08-glm53-part1-hybrid-sparse-offloading
