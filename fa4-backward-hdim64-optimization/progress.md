✅ 全部完成 (fa4-backward-hdim64-optimization)
- Step0: 提取全文 + 8 正文图(去 logo 噪音) + 3 表格 + 4 pre 代码块 全取证, wp-image 高清原图下载
- Step1: 封面用原文 fig06(results before/after 关键图) → make-cover-from-original.py cover.png 900x383 + square 500x500
- Step2: 中文编译 17 节; 8图/3表(fig 图注中文)/4 代码块(cutlass CUTE DSL,__CODE__ 高亮) 100%, 正文知识≥85%, 公式下标源码已 Clean; 修复 fig05 fig_after 越界(7→6,避免静默丢图)
- Step3: preflight --fix 全绿(破折号0/间距/8图/无来源泄漏/结语卡/传送门16/参考区); check-fig-layout PASS 8 图无连排/图序单调
- Step5: push 成功 draft=TIqnnVEu6Oy3-wtKttGa0YEtjGoGMEENNZNYY-MMYY_vi3-kEvNHM2z8VoJMQS60, verify 8/8
source: https://research.colfax-intl.com/optimization-diaries-improving-flashattention-4-backward-for-head-dimension-64/
