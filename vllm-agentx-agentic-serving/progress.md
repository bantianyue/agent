✅ 完成 (vllm-agentx-agentic-serving)
- 源: X Article @vllm_project《vLLM x AgentX: Optimizing for Real-World Agentic Serving》 ~24.9K
- 主题: agentic 负载(多轮/长上下文/96%+前缀复用) 的 serving 优化: 数据面(混合KV/紧凑布局/分级外置/会话感知保留) · 执行面(K3 DCP · V4 PCP/DEP · 双层调度 · P:D率匹配) · kernel与社区 · 性能与成本数字 · 苦涩教训 · 下一步
- 体验: AgentX: V4 Pro 130K tok/GPU·s · MiniMax 最高376tok/s; 对 Opus5 14.6x-106x cost优势  (以正文数据为准)
- 正文图: 8 (来自登录DOM按序截的正文静态图 fig01-08, 已剔除嵌入式视频占位; 封面用真实 hero)
- preflight ALL PASS; push media=TIqnnVEu6Oy3-wtKttGa0TuzAyQyIA87ku7GuXaXLh0ZfpNcKsXvTHYcoJ9Ixme5; verify body 8/8
- progress note: 覆盖推送同 id 时返回 "media undefined" 属正常覆盖路径
source: https://x.com/vllm_project/status/2097427730983776758
| Step 4d-i: 传送门 | completed |
- 2026-09-13 修复(GIF丢失): 原文 3 张动图此前被当嵌入式视频占位剔除，已按源 tweet_video 原片(HRuHPcCagAA1OBj / HRuHi7kaEAAQsyr / HRuHranbIAAWJc8)转 900px GIF 保动画（249/169/97 帧，1.81/1.10/1.00MB），插回源文顺序 fig05/fig07/fig08；同时按源文真实顺序重排全部图位(8张静态图重编号 fig01-fig11)并补 7 条原文图注；正文图 8 -> 11。
- 覆盖重推同一 draft.id；draft/get 核验: body 图 11 张，其中 mmbiz_gif 3 张(GIF89a，帧数 249/169/97 与本地一致)，其余 8 张 mmbiz_png。
