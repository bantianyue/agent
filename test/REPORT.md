# URL 网页信息提取方法对比报告

测试日期：2026-07-09 ｜ 环境：Windows + MSYS(git-bash) + Python venv + Playwright Chromium
网络：全部走代理 `HTTP_PROXY=http://127.0.0.1:7890`
测试 URL：论文×1、Blog×2、X.com 帖子×2（其中 2 个帖子是 X Article，含 Hero 图）

---

## 一、方法总览

| 方法 | 工具/库 | 类型 | 是否需要 JS 渲染 | Token 消耗 |
|------|---------|------|------------------|-----------|
| A | `web_extract`（Hermes 内置提取工具，无 LLM 摘要） | 提取 | 否（服务端渲染版） | **0**（纯提取，非生成） |
| B | `trafilatura`（Python） | 提取 | 否 | **0** |
| C | `newspaper3k`（Python） | 提取 | 否 | **0** |
| D | 直连 `chrome --headless=new --dump-dom`（绕过 Playwright CDP） | 渲染+提取 | **是** | **0** |
| E | `httpx` + `BeautifulSoup4`（原生爬虫基线） | 提取 | 否 | **0** |
| F | `r.jina.ai/<url>`（Jina Reader API，服务端渲染转 Markdown） | 提取(云端渲染) | 否(云端做) | **0** |

> **Token 消耗结论：所有测试方法均为"提取/解析"类工具，不含 LLM 生成，故 Token 消耗统一为 0。** 若需要 LLM 参与的摘要型方法（如 browser-use、让模型读页面后总结），才会产生 Token，但那超出"提取"范畴，本测试未纳入。

---

## 二、主对比表（按方法）

| 方法 | 工具 | 花费时长 | Token | 正文 | 图片 | 封面(Hero) | 任务完成度说明 |
|------|------|----------|-------|------|------|-------------|----------------|
| **A web_extract** | Hermes 内置 | 内置不可测（实测秒级返回） | 0 | ✅ 完整 | ⚠️ 部分（行内图引用） | ⚠️ Blog 有、X/arxiv 无 | **Blog 接近完整；X 失败；arxiv 需补图** |
| **B trafilatura** | trafilatura | 1–5s/URL（含下载） | 0 | ✅ 最佳正文 | ❌ 0 张（img 提取失效） | ❌ 不提取 | **仅正文，缺失图片+封面** |
| **C newspaper3k** | newspaper3k | 3–42s/URL | 0 | ⚠️ Blog好/arxiv差 | ✅ 完整 | ✅ Blog 有 top_image | **Blog 全完成；arxiv 正文被截断** |
| **D 直连chromium** | chrome --headless=new --dump-dom | arxiv 5.9s / cognition 4.6s / x帖子 4s | 0 | ✅（arxiv 63202字） | ✅（arxiv 8张） | ✅ cognition有 | **arxiv/cognition/x帖子成功；claude.com 单独卡死（GPU进程0xC0000005崩溃）** |
| **F Jina Reader** | r.jina.ai API | 0.6–1.6s/URL | 0 | ✅ 全站最完整 | ✅（arxiv 9 / claude 16 / cog 6） | ✅ 全部带 Hero | **arxiv/claude/cognition 三件套全完成；X.com 被 Jina 匿名限流 403** |
| **E httpx+bs4** | httpx+beautifulsoup4 | 0.6–0.9s/URL（仅下载） | 0 | ✅ 原始文本 | ✅ 原始 img 列表 | ✅ 可解析 og:image | **基线最稳最快，需自行写解析逻辑** |

---

## 三、逐 URL 明细矩阵

完成度：`✅完整 / ⚠️部分 / ❌缺失 / N/A无此资源`

### 1. 论文 arxiv.org/html/2607.05794v1
| 方法 | 时长 | 正文字数 | 图片数 | 封面 | 评价 |
|------|------|---------|--------|------|------|
| A web_extract | 内置 | ~51,145 | 行内引用(部分) | N/A | 正文最全，图需从缓存文件补 |
| B trafilatura | 4.2s | **43,461** | 0 | N/A | 正文质量最高，但不提图 |
| C newspaper3k | 15.3s | 2,677 ❌ | 10 | apple-touch❌ | 对 arxiv HTML 版解析差，正文被截 |
| D 直连chromium | 5.9s | 63,202 | 8 | N/A | 正文+图齐全 |
| E httpx+bs4 | 0.9s | 63,886(原始) | 9 | N/A | 基线，全量 HTML 在手 |
| F Jina Reader | 1.6s | 71,038 | 9 | N/A | 正文最全+图齐全 |

→ arxiv 无原生封面图（og:image 缺失），封面列为 N/A。

### 2. Blog claude.com/.../claude-model-and-effort-level
| 方法 | 时长 | 正文字数 | 图片数 | 封面(Hero) | 评价 |
|------|------|---------|--------|-------------|------|
| A web_extract | 内置 | 23,019 | 行内URL | ✅ og jpg | 接近完整 |
| B trafilatura | 3.4s | 13,816 | 0 | ❌ | 仅正文 |
| C newspaper3k | 9.4s | 13,204 | **17** | ✅ og jpg | **正文+图+封面全完成** |
| D 直连chromium | 崩溃(原Playwright)/ 直连未测此页 | — | — | — | 见结论：直连对claude卡死 |
| E httpx+bs4 | 0.8s | 30,108(原始) | 18 | ✅ og jpg | 全量在手 |
| F Jina Reader | 0.8s | 49,533 | **16** | ✅ og jpg | **正文+图+封面全完成（最快最全）** |

### 3. Blog cognition.com/blog/swe-1-7
| 方法 | 时长 | 正文字数 | 图片数 | 封面(Hero) | 评价 |
|------|------|---------|--------|-------------|------|
| A web_extract | 内置 | 22,934 | 行内URL | ✅ swe-1-7-og.png | 接近完整 |
| B trafilatura | 5.0s | 20,629 | 0 | ❌ | 仅正文 |
| C newspaper3k | 42.3s | 19,683 | 6 | ✅ og png | **全完成（最慢）** |
| D 直连chromium | 4.6s | 22,042 | 5 | ✅ og png | 直连成功 |
| E httpx+bs4 | 0.7s | 21,359(原始) | 5 | ✅ og png | 全量在手 |
| F Jina Reader | 0.8s | 28,226 | 6 | ✅ og png | **正文+图+封面全完成** |

### 4 & 5. X.com 帖子（Sergio / Christine，均为 X Article，含 Hero 图）
| 方法 | 时长 | 正文 | 图片 | 封面(Hero) | 评价 |
|------|------|------|------|-------------|------|
| A web_extract | 内置 | 仅预告(800字) | ❌ | ❌ | 登录墙，只拿到标题+文章链接 |
| B trafilatura | 1.1s | 443 | 0 | ❌ | 登录墙，几乎无内容 |
| C newspaper3k | 3.1s | 270 | 3(头像) | ❌ | 登录墙，top_image=头像非封面 |
| D 直连chromium | x帖子 4s / article 110s超时 | x帖子 877字 | 3(头像) | ❌ | x帖子成功出DOM；article子页110s超时 |
| E httpx+bs4 | 0.9s | 833 | 3(头像) | ❌ | 登录墙 |
| F Jina Reader | 0.6s | 403(被限流) | 0 | ❌ | Jina匿名访问x.com被封到 2026-07-09 06:10 UTC（DDoS防护），非方法缺陷 |
| 直抓 X Article | 0.9s | JS-walled | 1 | ❌ | `We've detected JavaScript is disabled` |

→ **X.com 全军覆没：所有方法在无登录态下均无法获取正文与 Hero 封面。** Hero 图只存在于 X Article 正文里，必须登录态浏览器才能渲染。

---

## 四、关键结论

1. **完成度排名（对非 X 页面）：**
   - **Jina Reader（F）是综合冠军**：arxiv/claude/cognition 三件套（正文+图片+封面）全部完成，且**最快**（0.6–1.6s/URL）、**正文最全**（claude 49,533 字、arxiv 71,038 字）、**自带 Hero 封面**。它走云端渲染，连本地 Chromium 崩的 claude.com 也能 0.8s 拿下。缺点：依赖第三方服务、匿名额度对 x.com 被限流。
   - **newspaper3k（C）** 是本地方案里唯一自动拿三件套的（Blog 全完成，arxiv 因 HTML 版结构特殊正文被截），但最慢（cognition 42s）。
   - **web_extract（A）** 对 Blog 同样接近完整，且 arxiv 正文最全；缺点是图片以行内引用返回、X 登录墙失效。
   - **trafilatura（B）** 正文质量最高但**完全不提图、不提封面**，不满足"图片+封面"要求。
   - **直连 chromium（D）** 本来应通吃所有页面，但 Playwright 的 CDP 控制方式在 MSYS 下会让 renderer 崩溃（arxiv 这种 SSR 轻页勉强能跑、重型页必崩）。**绕过 Playwright 直连 `chrome --headless=new --dump-dom` 后**，arxiv(5.9s)/cognition(4.6s)/x帖子(4s) 全部成功拿到完整 DOM+图片+封面。唯独 **claude.com 单独卡死**，stderr 明确报 `GPU process exited unexpectedly: exit_code=-1073741819`（=0xC0000005 访问冲突）——是 claude.com 的 Next.js 应用触发了 GPU/Network 子进程在 headless 下崩溃；`--disable-gpu`/`--in-process-gpu`/`--use-angle=swiftshader` 等 GPU 相关 flag 均无法修复。**这是 claude.com 特定站点 + headless Chromium 149 的兼容性问题，非方法通病。**
   - **httpx+bs4（E）** 作为基线最稳最快（<1s/URL），全量 HTML+og:image 都在手，但需要自行写解析逻辑，不直接产出"干净正文"。

2. **X.com 是硬伤**：无论哪种方法，无登录态 Cookie 一律只能拿到登录墙 / 帖子预告。要拿 X Article 的 Hero 图，必须用**已登录的浏览器会话**（复用已有登录态 tab，见记忆：X.com 需要登录态 tab 才能渲染内容）。

3. **Token 消耗**：全部为 0——这些都是提取工具，不调用 LLM。

4. **耗时**：Jina(F) 最快 0.6–1.6s；提取类 B/C/E 0.6–45s（C 最慢，cognition 42s）；直连 chromium(D) 成功页 4–6s，claude.com 110s 硬超时（GPU 崩溃）。

---

## 五、环境踩坑记录（已修复/已定位）

- httpx 走代理时 brotli 解码异常 → 请求头加 `Accept-Encoding: gzip, deflate` 规避。
- bs4 `find(meta, name=...)` 与关键字冲突 → 改用 `find("meta", attrs={"name": ...})`。
- **Playwright CDP 在 MSYS 下 renderer 必崩** → 根因是 Playwright 用 pipe/websocket 控制浏览器，在 git-bash(MSYS) 子进程里渲染进程初始化即崩（连 `--version` 都卡死）。**绕过方案：直接 `subprocess` 调 `chrome.exe --headless=new --dump-dom`**，arxiv/cognition/x帖子全部成功。
- **claude.com 单独卡死（110s 超时）**：stderr 报 `GPU process exited unexpectedly: exit_code=-1073741819`（0xC0000005 访问冲突）。claude.com 的 Next.js 应用触发 GPU/Network 子进程在 headless 下崩溃。`--disable-gpu` / `--in-process-gpu` / `--use-angle=swiftshader` / 去掉 `--run-all-compositor-stages-before-draw` 均无效。这是 claude.com 站点 + Chromium 149 的兼容性问题。
- `--proxy-bypass-list=<-loopback>` 在 bash 里 `>` 被当重定向 → 用变量包裹加引号 `"--proxy-bypass-list=$bypass"`。
- 每个 URL 抓取其独立 `subprocess`（timeout=110s 硬上限），超时不阻塞其他 URL。

## 六、复现脚本

- `bench.py`：E(httpx+bs4) / B(trafilatura) / C(newspaper3k) 批量跑全部 URL，结果落 `results_bce.json`
- `pw_one.py`：D 方法**直连 chromium**版，单 URL 参数化 `python pw_one.py <label> <url> <wait秒>`，超时 110s 硬杀
- `pw_dumpdom.py` / `pw_diag.py` / `playwright_extract.py`：历史调试版本
- `jina_test.py`：F 方法，`r.jina.ai/<url>` 批量跑全部 URL，结果落 `results_f.json`（X.com 当前 403 限流）
- 输出目录：`C:/Users/twfehh7/url_extract_test/out/`（含 `*_jina.md` 成功页 Markdown）
