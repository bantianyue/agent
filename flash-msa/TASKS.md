# flash-msa 任务清单

| 步骤 | 状态 | 备注 |
|------|------|------|
| Step 0: 目录创建 | ✅ 已完成 | 目录 D:/06_Hermes/articles/flash-msa |
| Step 0a: 语言类型判断 | ✅ 已完成 | 英文 |
| Step 0c: 来源类型确认 | ✅ 已完成 | 个人技术博客 |
| Step 1: 内容提取 | ✅ 已完成 | CDP browser ws + attachToTarget；blocks.jsonl 61 文本块 + 4 图 |
| Step 2: 图片下载 | ✅ 已完成 | cover.png + fig01/02/03.png 共 4 张 |
| Step 3: 封面生成 | ✅ 已完成 | cover.png (hero msa_fig_1) + cover-square.png 500x500 |
| Step 4a: 关键素材清单 | ✅ 已完成 | |
| Step 4a-i: 要点速览 | ✅ 已完成 | 5 条 |
| Step 4b: 独立观点 | ✅ 已完成 | 结语 4 条 |
| Step 4c: 正文 | ✅ 已完成 | 逐章对齐 + full_translation.md |
| Step 4d: 结语 | ✅ 已完成 | |
| Step 4d-i: 传送门 | ✅ 已完成 | 8 篇（add-portal.py） |
| Step 4e: 参考区 | ✅ 已完成 | 原 URL |
| Step 4f: Humanizer 润色 | ✅ 已完成 | 破折号 5 处修复（已知 humanize 差异微小误报，跳过） |
| Step 4g: 文本格式修复 | ✅ 已完成 | 两次 text-format |
| Step 5: 预发布检查 | ✅ 已完成 | preflight 通过（humanize 差异微小为已知误报） |
| Step 6: 推送草稿 | ✅ 已推送 | media_id: TIqnnVEu6Oy3-wtKttGa0QA8syMbtCn1bEHPOadRdYwycSSXu37sYd0wqvyuJZ5V |

## 标题
Flash-MSA：用稀疏注意力 Kernel 加速百万 token 训练

## 来源
https://nanduruganesh.github.io/flash-msa/

## media_id
TIqnnVEu6Oy3-wtKttGa0QA8syMbtCn1bEHPOadRdYwycSSXu37sYd0wqvyuJZ5V

## 图片映射
- cover.png ← msa_fig_1.png (hero, Fig.1)
- fig01.png ← plot.png (训练步对比)
- fig02.png ← msa_fig_2.png (kernel 概览)
- fig03.png ← topk_sweep.png (Top-k 扫描)
