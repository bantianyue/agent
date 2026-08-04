# beta-opsd - progress.md

## Step 0: 提取 completed
- 2026-08-04: HTTP 提取 arxiv HTML 2607.28582v1
- 图片: 2 张正式图下载（Fig1 x1.png, Fig2 x2.png），代理+缓存buster
- 图注: 从 HTML figcaption 提取原文翻译

## Step 1: 封面 completed
- 2026-08-04: cover-letterbox.py 从 fig00.png 生成

## Step 2: 写文章 completed
- 2026-08-04: 手写 article_data_build.py（首版14段校验未过，补1段至15段）
- 4 个 sections, 15 段, 2 张配图
- write-article-data.py 三重校验通过

## Step 3: 渲染+推送 completed
- 2026-08-04: render-article → preflight --fix → push-draft
| Step 4d-i: 传送门 | completed |
