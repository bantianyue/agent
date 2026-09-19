# 进度追踪 - amd-mi450-lds-opt

✅ 完成 (amd-mi450-lds-opt)

- 2026-09-19 二次重生成（模板化改造）：上一版走的是私有脚本链（_regen1c/2/3/4.py）直改源站 Sphinx DOM，
  绕过了标准管线 —— 无要点速览卡、无结语卡、正文是源站 pydata 的 `<div>` 结构（微信图文编辑器不认 div，
  卡片背景会被丢），且残留源站社交图标条、「其他资源」「免责声明」。本次按 templates/article.template.html
  重建 article_data.json（复用已有中文译文，不重译）：要点速览 + lead + h2/h3 + 17 图内联 + 7 代码块
  （Pygments monokai + &nbsp; 防塌缩）+ 1 表格 + 结语暖灰卡（原文「总结」并入）+ 传送门 + 参考，全程 `<section>` 容器。
  修掉两处真实 bug：正文直出的 LaTeX `\begin{split}` 与一条误入正文的 blocks JSON 记录。
- source: https://rocm.blogs.amd.com/software-tools-optimization/mi450-lds-optimization/README.html
- 迁移脚本：`_retrofit_build.py`（源 article_zh.html → article_data.json）；推送 mode=覆盖草稿

| Step | 状态 |
|------|------|
| Step 0: 原文提取 + 图片下载 | completed |
| Step 1: 封面生成（900x383 + 500x500） | completed |
| Step 2: 全文中译 + 格式保留组装 | completed |
| Step 2b: 标准模板重建（article_data.json → render） | completed |
| Step 4d-i: 传送门 | completed |
| Step 5: 预发布检查（preflight ALL CHECKS PASSED） | completed |
| Step 5: 推送草稿（覆盖）+ draft/get 回读核验 | completed |
| Step 4d-i: 传送门 | completed |
| Step 5: 预发布检查 | completed |
