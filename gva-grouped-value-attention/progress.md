✅ 完成 (gva-grouped-value-attention)
- 源: GitHub 论文 PDF《Grouped Value Attention: Efficient KV Caching via On-Demand Key Reconstruction》(FrontiersMind, GVA_Efficient-KV.pdf) 16p/27.8k字
- 用户要求: 去掉实验和消融、去掉引用部分 → 本稿只保留 摘要/引言/记法与现状(MHA/MQA/GQA/MLA)/方法(3.1 K=V·M + per-head 映射/吸收进 query/deco ep decoupled RoPE + 共享 ro轮通道/缓存规模估算); 4 Experiments 起(含变体消融) 与 References 整段省略
- 核心: 只缓存分组 value, 用每 head 线性映射在线重建 key; content-key 写作非必要; KV 缓存标量相对同级 GQA ~省45-47%; dec 结构沿 MLA 共享 decoup RoPE, 每 token 仅补 dr 维
- 说明: 原文为论文型(无嵌入正文图) -> 0 正文图, 信息卡封面; 实验/消融/参考章节因指令未纳入
- preflight ALL PASS; push media=TIqnnVEu6Oy3-wtKttGa0ci4836WGr4qvl59f6oOCfE6joq37Lud1YgOwZO-pi1O; verify body 0; arbiter(queue jid_20260909_174813_1db501) done
source: https://github.com/FrontiersMindAI/GVA/blob/main/GVA_Efficient-KV.pdf
