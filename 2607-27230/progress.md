# 2607-27230 - progress.md

## Step 0: 提取 completed
- 2026-08-05: HTTP 提取 arxiv HTML 2607.27230v2 (Multi-Head Attention Residuals)
- 图片: 8 张正式图全下载（x1-x8 → fig00-fig07），代理+cache-buster

## Step 1: 封面 completed
- 2026-08-05: cover-letterbox.py 从 fig00.png 生成

## Step 2: 写文章 completed
- 2026-08-05: 手写 article_data_build.py（中文引号用「」）
- 6 个 sections, 16 段正文, 8 张配图全收录 (Fig1/2/4/5x2panel/7/8/11)
- write 三重校验通过

## Step 3: 渲染+推送 completed
- 2026-08-05: render-article → preflight --fix → push-draft
