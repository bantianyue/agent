# SGLang GIF 修复 — 准备完成状态（2026-09-30 21:45）

## 已完成
三张GIF已生成并校验，位于 ~/workspace/articles/unified-radix-cache/：
- fig03.gif：9帧（t=0/8→8/8），840×409，147KB。源文件：#3,#4,#10,#12,#13,#16,#18,#20,#21
- fig04.gif：6帧（t=0/5→5/5），840×368，144KB。源文件：#23-28
- fig07.gif：6帧（t=0/5→5/5），840×217，130KB。源文件：#29-34

校验：帧数✓、尺寸<2MB✓、帧间差异确认动画✓、光标未入图表区✓、裁剪完整✓

## 待用户确认后执行（确认请求19:18已发出，未回复）
1. mkdir -p orig_png && mv fig03.png fig04.png fig07.png orig_png/
2. 更新 article_data.json：三处 src 的 .png → .gif
3. python3 scripts/render-article.py --dir ~/workspace/articles/unified-radix-cache
4. python3 scripts/preflight.py --dir ~/workspace/articles/unified-radix-cache
5. python3 scripts/push-draft.py --dir ~/workspace/articles/unified-radix-cache
   （draft.id=TIqnnVEu6Oy3-wtKttGa0WR3sgXFtbLpl3oYArFaVU_yQdTOHKUshu1LKuSCR8sY，自动覆盖同一草稿）
6. python3 scripts/verify-draft-images.py --draft-id TIqnnVEu6Oy3-wtKttGa0WR3sgXFtbLpl3oYArFaVU_yQdTOHKUshu1LKuSCR8sY

## 铁律
用户明确确认前，不得执行覆盖推送。
