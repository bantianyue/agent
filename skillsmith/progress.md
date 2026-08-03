# SkillSmith - progress.md

## Step 0: 提取 completed
- 2026-08-02: web_extract 提取 arxiv HTML 2607.27497v1
- 图片: 10 张下载（带 Referer 头）
- 图注: 从 HTML figcaption 提取原文翻译

## Step 1: 封面 completed
- 2026-08-02: cover-letterbox.py 从 fig00.png 生成

## Step 2: 写文章 completed
- 2026-08-02: 手写 article_data_build.py
- 6 个 sections, 17 段, 6 张配图
- write-article-data.py 三重校验通过

## Step 3: 渲染+推送 completed
- 2026-08-02: render-article → preflight --fix → push-draft
