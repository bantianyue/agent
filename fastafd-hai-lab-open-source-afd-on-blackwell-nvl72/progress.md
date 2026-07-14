# FastAFD 文章进度

## 当前状态
- ✅ Step 0: 目录创建完成，D:\06_Hermes\articles\fastafd-hai-lab-open-source-afd-on-blackwell-nvl72\
- ✅ Step 0b: 英文→中文，技术博客
- ✅ Step 1: 原文内容完整提取
- ✅ Step 2: 15 张图片全部下载到 img/
- ❌ Step 3: 封面生成失败（FAL.ai 余额不足），需要手动补
- ✅ Step 4: 文章初稿完成 article.md
- ⏳ Step 4f: Humanize-zh 已通过 delegate_task 派发（后台运行中）
- ⏳ Step 4g: 待格式修复
- ⏳ Step 5: 预发布检查
- ⏳ Step 6: 推送草稿

## 图片清单
img/ 下共 15 个文件：
- attention-moe-decode-axes.png — Colocated MoE 流程图
- colocated-token-flow.gif — Colocated MoE token flow 动图
- fig_starve_colocate.png — 长上下文饿死 MoE 层
- fig_ep_insufficient_nt128.png — EP 不足以解决问题
- fig_afd_mfu.png — AFD 提升 MoE MFU
- afd-token-flow.gif — AFD token flow 动图
- afd-token-flow_hu...360x...gif — 小尺寸版本（缩略图）
- afd-microbatch-pipeline.png — AFD 微批次流水线
- zero-overhead-coordinator.png — 零开销协调器
- zero-overhead-nsys.png — Nsight Systems trace
- fig_win.png — 吞吐提升结果
- fig_vr_lpx_projection_model.svg — Vera Rubin 投影模型
- fig_model_scaling_compare.png — Qwen/MiniMax 缩放对比
- fig_speedup_sources.png — 消融实验

## 待办
1. 手动补封面（FAL 余额）
2. 等 humanize 完成
3. 运行 text-format.py
4. 传送门填充（需要查 published_articles.json）
5. preflight 检查
