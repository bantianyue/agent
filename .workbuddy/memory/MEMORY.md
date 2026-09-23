# 项目长期记忆 — articles

## 工作环境约定

- **Bash 工具在本机不可用**（shim 报 `dirname: command not found`）。所有命令走 PowerShell。
- **PowerShell 的 stdout 不回传**给 agent。需要看输出时一律 `... | Out-File <path> -Encoding UTF8`，再用 Read 工具读该文件。
- PowerShell 捕获子进程**中文**输出会乱码（`Out-File -Encoding UTF8` 也救不回），属工具链现象，不代表文件损坏。
- `Remove-Item` 走 safe-delete 包装，**D 盘回收站操作会 fail-closed**（`[SAFE_DELETE_FAIL_CLOSED] reason: trash-failed`），文件删不掉。清理临时文件时要么接受残留，要么改用移动/覆盖，别在这上面反复重试。

## Skill 资产

- **公众号文章流水线**（wcsop）位于 WorkBuddy 用户级目录 `C:\Users\twfehh7\.workbuddy\skills\`，共 11 个 skill，2026-09-20 自 `C:\Users\twfehh7\.codex\skills\` 迁移而来（源目录保留、仍为权威原版，两边会各自演进）。
- 核心编排器 `wechat-article-sop`：`SKILL.md` + `pipeline.json`（步骤单一真相源）+ `scripts/wcsop-step.py` 驱动；215 篇 `references/`。
- 硬依赖 `baoyu-post-to-wechat`（`scripts/wechat-api.ts` 是推送引擎，被绝对路径调用）。
- 副本内 `node_modules` 已在 2026-09-21 用 `bun install` 重建（164 包 / 55MB，`bun wechat-api.ts --help` 实测可加载）。若依赖损坏，重跑：`cd C:\Users\twfehh7\.workbuddy\skills\baoyu-post-to-wechat\scripts && bun install`。
- `bun` 位置：`C:\Users\twfehh7\AppData\Roaming\npm\bun.ps1`（v1.3.14）。
- 统一运行时：`C:/Users/twfehh7/AppData/Local/hermes/hermes-agent/venv/Scripts/python.exe`，每条命令前先设 `PYTHONIOENCODING=utf-8`。

## wcsop 稳定踩坑（跨篇复用）

- **figNN.png 必须是真 PNG**：arXiv HTML 的 SVG 图会以 `.svg` 落盘，按 manifest 复制 figNN.png 时可能拿到 SVG 文本（坏图但计数正常）。校验读前 8 字节 == `\x89PNG\r\n\x1a\n`；修复时 `.svg` 换成同 stem 的 `.png`。
- **编号列表**：`<span style="color:#0F4C81;font-weight:bold;">N</span>&nbsp;` + `**小标题**：正文`（模板不放行 `<ul>/<li>`）。核对口径 `font-weight:bold` 数 == 源文编号条数。
- **机翻残留三形态**：术语自重复 `X（X）`、术语两侧空格（`在 X 中`、`P:D 比例 为`）、`如 所述`（`§` 清洗残留）。preflight 的中英间距检查不管中日韩间空格。
- **核验脚本**：`verify-draft-images.py <media_id>`（不是目录）；draft/get 用 `json.loads(r.content.decode('utf-8'))` 才不乱码；草稿里传送门被重写成长链，用 `mp.weixin.qq.com/s\?` 匹配（`/s/` 会数成 0）；覆盖推送回显 `media_id: undefined` 属正常。

## 待清理的技术债

- 迁移过来的 skill 文档里仍有 18+ 处 Codex/Hermes 专属工具引用（`delegate_task`、`execute_code`、`process poll`、`read_file`、`terminal()`、`hermes send`、ClawBot 通知），WorkBuddy 无对应能力。脚本链本身可正常运行，受影响的是 SOP 中若干编排指令。若要长期用 wcsop，建议按 WorkBuddy 的实际工具名逐条改写。

## 用户偏好

- 做事要求先报方案/落点再动手；破坏性操作必须显式确认。
- 喜欢结论有实证支撑（要求「用实测数据说话」而非拍脑袋结论）。
- 明确要求源目录只读复制，不允许改动原件。
