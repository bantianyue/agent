# codex skills 安装前安全审计

## 体量

| skill | 文件数（排除 .git/node_modules/__pycache__） | 大小 |
|---|---:|---:|
| article-collect | 3 | 16.0 KB |
| article-tracker-maintenance | 4 | 33.8 KB |
| articles-content-edit | 1 | 4.3 KB |
| baoyu-post-to-wechat | 38 | 381.5 KB |
| figure-extraction | 2 | 22.1 KB |
| paper-analysis-wechat | 18 | 156.5 KB |
| url-content-extraction | 6 | 30.8 KB |
| video-to-article | 1 | 6.7 KB |
| video-to-wechat-article | 4 | 25.3 KB |
| web-content-fetch | 4 | 11.3 KB |
| wechat-article-sop | 277 | 2404.0 KB |
| **合计** | **358** | **3.0 MB** |

## 扫描命中统计

| 类别 | 命中条数 |
|---|---:|
| secrets | 19 |
| credential_access | 80 |
| destructive | 13 |
| exec | 56 |
| network | 80 |
| b64_blob | 0 |

## 外联域名 top 30

| 域名 | 出现次数 |
|---|---:|
| 127.0.0.1 | 222 |
| arxiv.org | 100 |
| github.com | 80 |
| api.weixin.qq.com | 62 |
| localhost | 41 |
| mp.weixin.qq.com | 38 |
| opencollective.com | 34 |
| x.com | 32 |
| pytorch.org | 25 |
| r.jina.ai | 17 |
| mmbiz.qpic.cn | 14 |
| ... | 14 |
| pbs.twimg.com | 12 |
| api.ipify.org | 12 |
| api.fxtwitter.com | 9 |
| huggingface.co | 8 |
| example.com | 7 |
| mmbiz | 7 |
| gemini.google.com | 7 |
| pbs | 6 |
| substackcdn.com | 5 |
| youtu.be | 5 |
| www.lmsys.org | 5 |
| www.google.com | 5 |
| raw.githubusercontent.com | 5 |
| developer.nvidia.com | 5 |
| dns.google | 4 |
| cdn.example.com | 4 |
| ptht05hbb1ssoooe.public.blob.vercel-storage.com | 4 |
| developer-blogs | 4 |

## 明细：secrets

- `baoyu-post-to-wechat\SKILL.md:215` — access_token = <redacted>
- `baoyu-post-to-wechat\references\multi-account.md:29` — app_secret = <redacted>
- `baoyu-post-to-wechat\references\multi-account.md:76` — APP_SECRET = <redacted>
- `baoyu-post-to-wechat\references\multi-account.md:80` — APP_SECRET = <redacted>
- `baoyu-post-to-wechat\references\multi-account.md:121` — app_secret = <redacted>
- `baoyu-post-to-wechat\references\multi-account.md:127` — app_secret = <redacted>
- `baoyu-post-to-wechat\scripts\wechat-extend-config.test.ts:110` — APP_SECRET = <redacted>
- `baoyu-post-to-wechat\scripts\wechat-extend-config.test.ts:113` — APP_SECRET = <redacted>
- `baoyu-post-to-wechat\scripts\wechat-extend-config.test.ts:114` — APP_SECRET = <redacted>
- `baoyu-post-to-wechat\scripts\wechat-extend-config.test.ts:134` — APP_SECRET = <redacted>
- `baoyu-post-to-wechat\scripts\wechat-extend-config.test.ts:137` — APP_SECRET = <redacted>
- `baoyu-post-to-wechat\scripts\wechat-extend-config.test.ts:138` — APP_SECRET = <redacted>
- `baoyu-post-to-wechat\scripts\wechat-extend-config.test.ts:302` — APP_SECRET = <redacted>
- `baoyu-post-to-wechat\scripts\wechat-extend-config.ts:321` — appSecret = <redacted>
- `baoyu-post-to-wechat\scripts\wechat-extend-config.ts:372` — appSecret = <redacted>
- `wechat-article-sop\references\wechat-video-embed.md:73` — access_token = <redacted>
- `wechat-article-sop\references\wechat-video-embed.md:83` — access_token = <redacted>
- `wechat-article-sop\references\wechat-video-embed.md:102` — access_token = <redacted>
- `wechat-article-sop\scripts\verify-draft-images.py:38` — secret = <redacted>

## 明细：credential_access

- `baoyu-post-to-wechat\skill-card.md:42` — credentials
- `baoyu-post-to-wechat\SKILL.md:78` — .ssh/
- `baoyu-post-to-wechat\SKILL.md:79` — .ssh/
- `baoyu-post-to-wechat\SKILL.md:105` — credentials
- `baoyu-post-to-wechat\SKILL.md:115` — credentials
- `baoyu-post-to-wechat\SKILL.md:115` — .env
- `baoyu-post-to-wechat\SKILL.md:134` — credentials
- `baoyu-post-to-wechat\SKILL.md:164` — credentials
- `baoyu-post-to-wechat\SKILL.md:166` — credentials
- `baoyu-post-to-wechat\SKILL.md:168` — credentials
- `baoyu-post-to-wechat\SKILL.md:168` — .env
- `baoyu-post-to-wechat\SKILL.md:240` — credentials
- `baoyu-post-to-wechat\SKILL.md:240` — .env
- `baoyu-post-to-wechat\SKILL.md:282` — credentials
- `baoyu-post-to-wechat\SKILL.md:290` — credentials
- `baoyu-post-to-wechat\SKILL.md:291` — credentials
- `baoyu-post-to-wechat\SKILL.md:312` — credentials
- `baoyu-post-to-wechat\references\api-setup.md:7` — credentials
- `baoyu-post-to-wechat\references\api-setup.md:10` — .env
- `baoyu-post-to-wechat\references\api-setup.md:11` — .env
- `baoyu-post-to-wechat\references\api-setup.md:20` — credentials
- `baoyu-post-to-wechat\references\api-setup.md:22` — credentials
- `baoyu-post-to-wechat\references\api-setup.md:28` — .env
- `baoyu-post-to-wechat\references\api-setup.md:29` — .env
- `baoyu-post-to-wechat\references\mass-send.md:6` — .env
- `baoyu-post-to-wechat\references\mass-send.md:14` — .env
- `baoyu-post-to-wechat\references\multi-account.md:3` — credentials
- `baoyu-post-to-wechat\references\multi-account.md:67` — .env
- `baoyu-post-to-wechat\references\multi-account.md:68` — .env
- `baoyu-post-to-wechat\references\multi-account.md:71` — .env
- `baoyu-post-to-wechat\references\multi-account.md:131` — .ssh/
- `baoyu-post-to-wechat\references\multi-account.md:132` — .ssh/
- `baoyu-post-to-wechat\references\win-body-image-upload.md:28` — .env
- `baoyu-post-to-wechat\references\win-body-image-upload.md:30` — Credentials
- `baoyu-post-to-wechat\references\win-body-image-upload.md:35` — Credentials
- `baoyu-post-to-wechat\references\config\first-time-setup.md:86` — credentials
- `baoyu-post-to-wechat\scripts\cdp.ts:46` — .env
- `baoyu-post-to-wechat\scripts\check-permissions.ts:188` — Credentials
- `baoyu-post-to-wechat\scripts\check-permissions.ts:190` — .env
- `baoyu-post-to-wechat\scripts\check-permissions.ts:191` — .env
- `baoyu-post-to-wechat\scripts\check-permissions.ts:198` — credentials
- `baoyu-post-to-wechat\scripts\check-permissions.ts:206` — credentials
- `baoyu-post-to-wechat\scripts\check-permissions.ts:232` — Credentials
- `baoyu-post-to-wechat\scripts\wechat-api.ts:8` — Credentials
- `baoyu-post-to-wechat\scripts\wechat-api.ts:527` — .env
- `baoyu-post-to-wechat\scripts\wechat-api.ts:528` — .env
- `baoyu-post-to-wechat\scripts\wechat-api.ts:799` — Credentials
- `baoyu-post-to-wechat\scripts\wechat-api.ts:803` — Credentials
- `baoyu-post-to-wechat\scripts\wechat-article.ts:38` — .env
- `baoyu-post-to-wechat\scripts\wechat-article.ts:39` — .env
- `baoyu-post-to-wechat\scripts\wechat-article.ts:76` — cookies
- `baoyu-post-to-wechat\scripts\wechat-article.ts:81` — credentials
- `baoyu-post-to-wechat\scripts\wechat-article.ts:918` — .env
- `baoyu-post-to-wechat\scripts\wechat-article.ts:918` — .env
- `baoyu-post-to-wechat\scripts\wechat-extend-config.test.ts:9` — Credentials
- `baoyu-post-to-wechat\scripts\wechat-extend-config.test.ts:23` — .env
- `baoyu-post-to-wechat\scripts\wechat-extend-config.test.ts:24` — .env
- `baoyu-post-to-wechat\scripts\wechat-extend-config.test.ts:27` — .env
- `baoyu-post-to-wechat\scripts\wechat-extend-config.test.ts:30` — .env
- `baoyu-post-to-wechat\scripts\wechat-extend-config.test.ts:39` — .env
- `baoyu-post-to-wechat\scripts\wechat-extend-config.test.ts:40` — .env
- `baoyu-post-to-wechat\scripts\wechat-extend-config.test.ts:44` — .env
- `baoyu-post-to-wechat\scripts\wechat-extend-config.test.ts:46` — .env
- `baoyu-post-to-wechat\scripts\wechat-extend-config.test.ts:50` — .env
- `baoyu-post-to-wechat\scripts\wechat-extend-config.test.ts:52` — .env
- `baoyu-post-to-wechat\scripts\wechat-extend-config.test.ts:57` — .env
- `baoyu-post-to-wechat\scripts\wechat-extend-config.test.ts:59` — .env
- `baoyu-post-to-wechat\scripts\wechat-extend-config.test.ts:63` — .env
- `baoyu-post-to-wechat\scripts\wechat-extend-config.test.ts:65` — .env
- `baoyu-post-to-wechat\scripts\wechat-extend-config.test.ts:75` — .env
- `baoyu-post-to-wechat\scripts\wechat-extend-config.test.ts:87` — .env
- `baoyu-post-to-wechat\scripts\wechat-extend-config.test.ts:89` — .env
- `baoyu-post-to-wechat\scripts\wechat-extend-config.test.ts:91` — .env
- `baoyu-post-to-wechat\scripts\wechat-extend-config.test.ts:95` — .env
- `baoyu-post-to-wechat\scripts\wechat-extend-config.test.ts:98` — .env
- `baoyu-post-to-wechat\scripts\wechat-extend-config.test.ts:102` — Credentials
- `baoyu-post-to-wechat\scripts\wechat-extend-config.test.ts:116` — credentials
- `baoyu-post-to-wechat\scripts\wechat-extend-config.test.ts:116` — Credentials
- `baoyu-post-to-wechat\scripts\wechat-extend-config.test.ts:118` — credentials
- `baoyu-post-to-wechat\scripts\wechat-extend-config.test.ts:119` — credentials

## 明细：destructive

- `article-tracker-maintenance\SKILL.md:27` — DROP TABLE
- `wechat-article-sop\SKILL.md:106` — rm -f 
- `wechat-article-sop\SKILL.md:131` — rm -f 
- `wechat-article-sop\SKILL.md:138` — rm -f 
- `wechat-article-sop\SKILL.md:266` — rm -f 
- `wechat-article-sop\references\article-git-watcher.md:178` — rm -rf 
- `wechat-article-sop\references\blog-arxiv-image-extraction.md:40` — rm -rf 
- `wechat-article-sop\references\chrome-publish-fallback.md:26` — Remove-Item "$dst\Default" -Recurse
- `wechat-article-sop\references\cover-design.md:124` — rm -f 
- `wechat-article-sop\references\cover-design.md:134` — rm -f 
- `wechat-article-sop\references\draft-lifecycle.md:41` — rm -f 
- `wechat-article-sop\references\standard-template-retrofit.md:37` — rm -f 
- `wechat-article-sop\references\wcsop-extraction-render-pitfalls.md:15` — rm -f 

## 明细：exec

- `baoyu-post-to-wechat\scripts\cdp.ts:1` — child_process
- `baoyu-post-to-wechat\scripts\check-permissions.ts:1` — child_process
- `baoyu-post-to-wechat\scripts\copy-to-clipboard.ts:1` — child_process
- `baoyu-post-to-wechat\scripts\paste-from-clipboard.ts:1` — child_process
- `baoyu-post-to-wechat\scripts\wechat-agent-browser.ts:1` — child_process
- `baoyu-post-to-wechat\scripts\wechat-api.ts:3` — child_process
- `baoyu-post-to-wechat\scripts\wechat-article.ts:4` — child_process
- `baoyu-post-to-wechat\scripts\wechat-article.ts:858` — child_process
- `baoyu-post-to-wechat\scripts\wechat-helper.ts:34` — child_process
- `baoyu-post-to-wechat\scripts\wechat-http.ts:109` — child_process
- `baoyu-post-to-wechat\scripts\wechat-remote-publish.ts:1` — child_process
- `figure-extraction\SKILL.md:149` — subprocess.run
- `figure-extraction\SKILL.md:155` — exec(
- `paper-analysis-wechat\SKILL.md:198` — subprocess.run
- `paper-analysis-wechat\references\scanned-pdf-ocr.md:31` — subprocess.run
- `url-content-extraction\SKILL.md:108` — subprocess.run
- `url-content-extraction\references\chromium-bypass.md:20` — subprocess.run
- `url-content-extraction\references\self-hosted-blog-extraction.md:79` — subprocess.run
- `url-content-extraction\references\self-hosted-blog-extraction.md:94` — subprocess.run
- `wechat-article-sop\SKILL.md:189` — exec(
- `wechat-article-sop\SKILL.md:254` — exec(
- `wechat-article-sop\SKILL.md:275` — exec(
- `wechat-article-sop\references\100-percent-preserve-programmatic-pipeline.md:77` — exec(
- `wechat-article-sop\references\append-official-thread-to-article.md:26` — eval(
- `wechat-article-sop\references\append-official-thread-to-article.md:46` — eval(
- `wechat-article-sop\references\arxiv-html-curl-extraction.md:105` — exec(
- `wechat-article-sop\references\cover-design.md:289` — subprocess.run
- `wechat-article-sop\references\cover-design.md:293` — subprocess.run
- `wechat-article-sop\references\cover-design.md:299` — subprocess.run
- `wechat-article-sop\references\cover-design.md:349` — subprocess.run
- `wechat-article-sop\references\cover-design.md:352` — subprocess.run
- `wechat-article-sop\references\full-translation-degeneration.md:74` — exec(
- `wechat-article-sop\references\full-translation-degeneration.md:116` — exec(
- `wechat-article-sop\references\playwright-headless-extraction.md:27` — subprocess.run
- `wechat-article-sop\references\skill-maintenance-gotchas.md:39` — subprocess.run
- `wechat-article-sop\references\tasks-md-corruption-recovery.md:68` — subprocess.run
- `wechat-article-sop\references\tasks-md-corruption-recovery.md:94` — subprocess.run
- `wechat-article-sop\references\wcsop-authoring-pitfalls.md:78` — exec(
- `wechat-article-sop\scripts\add-portal.py:230` — subprocess.run
- `wechat-article-sop\scripts\article-watcher.py:74` — subprocess.run
- `wechat-article-sop\scripts\article-watcher.py:93` — subprocess.Call
- `wechat-article-sop\scripts\check-fetch-path.py:72` — subprocess.run
- `wechat-article-sop\scripts\check-fetch-path.py:84` — subprocess.run
- `wechat-article-sop\scripts\check-fetch-path.py:158` — subprocess.run
- `wechat-article-sop\scripts\create-article-dir.py:151` — subprocess.run
- `wechat-article-sop\scripts\create-article-dir.py:213` — subprocess.run
- `wechat-article-sop\scripts\extract_figures.py:28` — subprocess.run
- `wechat-article-sop\scripts\preflight-check.py:375` — subprocess.run
- `wechat-article-sop\scripts\preflight-check.py:387` — subprocess.run
- `wechat-article-sop\scripts\preflight-check.py:748` — subprocess.run
- `wechat-article-sop\scripts\push-draft.py:131` — subprocess.run
- `wechat-article-sop\scripts\pw-extract.py:83` — subprocess.Popen
- `wechat-article-sop\scripts\render-article.py:241` — subprocess.run
- `wechat-article-sop\scripts\test_get_by_url.py:69` — subprocess.run
- `wechat-article-sop\scripts\test_get_by_url.py:78` — subprocess.run
- `wechat-article-sop\scripts\write-article-data.py:649` — exec(

## 明细：network

- `article-tracker-maintenance\SKILL.md:250` — fetch(
- `baoyu-post-to-wechat\SKILL.md:302` — fetch(
- `baoyu-post-to-wechat\references\dns-doh-patch.md:13` — fetch(
- `baoyu-post-to-wechat\references\dns-doh-patch.md:19` — fetch(
- `baoyu-post-to-wechat\references\dns-doh-patch.md:45` — fetch(
- `baoyu-post-to-wechat\references\mass-send.md:12` — urllib.request
- `baoyu-post-to-wechat\references\mass-send.md:26` — urllib.request
- `baoyu-post-to-wechat\references\mass-send.md:27` — urllib.request
- `baoyu-post-to-wechat\references\win-body-image-upload.md:37` — fetch(
- `baoyu-post-to-wechat\scripts\wechat-agent-browser.ts:222` — fetch(
- `baoyu-post-to-wechat\scripts\wechat-article.ts:81` — fetch(
- `baoyu-post-to-wechat\scripts\wechat-article.ts:109` — fetch(
- `baoyu-post-to-wechat\scripts\wechat-http.ts:135` — fetch(
- `baoyu-post-to-wechat\scripts\wechat-image-loader.ts:34` — fetch(
- `paper-analysis-wechat\SKILL.md:830` — urllib.request
- `paper-analysis-wechat\SKILL.md:841` — urllib.request
- `paper-analysis-wechat\SKILL.md:842` — urllib.request
- `paper-analysis-wechat\SKILL.md:856` — urllib.request
- `paper-analysis-wechat\SKILL.md:857` — urllib.request
- `paper-analysis-wechat\references\arxiv-html-figure-availability.md:24` — urllib.request
- `paper-analysis-wechat\references\arxiv-html-figure-availability.md:26` — urllib.request
- `paper-analysis-wechat\references\arxiv-html-figure-availability.md:27` — urllib.request
- `url-content-extraction\SKILL.md:49` — urllib.request
- `url-content-extraction\SKILL.md:57` — urllib.request
- `url-content-extraction\SKILL.md:58` — urllib.request
- `url-content-extraction\references\fxtwitter-extraction.md:50` — urllib.request
- `url-content-extraction\references\fxtwitter-extraction.md:56` — urllib.request
- `url-content-extraction\references\fxtwitter-extraction.md:57` — urllib.request
- `url-content-extraction\scripts\cdp_loggedin_x_extract.py:26` — urllib.request
- `url-content-extraction\scripts\cdp_loggedin_x_extract.py:33` — urllib.request
- `video-to-article\SKILL.md:84` — fetch(
- `video-to-wechat-article\SKILL.md:132` — fetch(
- `web-content-fetch\references\pitfalls.md:4` — urllib.request
- `web-content-fetch\scripts\native_cdp_x_extract.py:6` — urllib.request
- `web-content-fetch\scripts\native_cdp_x_extract.py:12` — urllib.request
- `wechat-article-sop\references\append-official-thread-to-article.md:17` — urllib.request
- `wechat-article-sop\references\append-official-thread-to-article.md:20` — urllib.request
- `wechat-article-sop\references\arxiv-figure-404-recovery.md:35` — urllib.request
- `wechat-article-sop\references\arxiv-figure-404-recovery.md:41` — urllib.request
- `wechat-article-sop\references\arxiv-html-image-direct-download-pitfall.md:13` — urllib.request
- `wechat-article-sop\references\arxiv-html-image-direct-download-pitfall.md:16` — urllib.request
- `wechat-article-sop\references\arxiv-html-image-direct-download-pitfall.md:17` — urllib.request
- `wechat-article-sop\references\arxiv-html-image-direct-download-pitfall.md:21` — urllib.request
- `wechat-article-sop\references\arxiv-html-image-direct-download-pitfall.md:94` — urllib.request
- `wechat-article-sop\references\arxiv-html-image-direct-download-pitfall.md:96` — urllib.request
- `wechat-article-sop\references\arxiv-html-image-direct-download-pitfall.md:97` — urllib.request
- `wechat-article-sop\references\arxiv-html-image-direct-download-pitfall.md:138` — urllib.request
- `wechat-article-sop\references\arxiv-pdf-fallback.md:14` — urllib.request
- `wechat-article-sop\references\arxiv-pdf-fallback.md:17` — urllib.request
- `wechat-article-sop\references\base64-inline-image-extraction.md:12` — urllib.request
- `wechat-article-sop\references\base64-inline-image-extraction.md:13` — urllib.request
- `wechat-article-sop\references\base64-inline-image-extraction.md:14` — urllib.request
- `wechat-article-sop\references\cdp-405-and-x-article-extraction.md:7` — urllib.request
- `wechat-article-sop\references\cdp-405-and-x-article-extraction.md:12` — urllib.request
- `wechat-article-sop\references\cdp-405-and-x-article-extraction.md:15` — urllib.request
- `wechat-article-sop\references\cdp-vs-playwright-x-extraction.md:67` — fetch(
- `wechat-article-sop\references\cdp-x-extract-chrome149.md:74` — urllib.request
- `wechat-article-sop\references\cdp-x-extract-chrome149.md:75` — urllib.request
- `wechat-article-sop\references\cdp-x-extract-chrome149.md:89` — urllib.request
- `wechat-article-sop\references\cover-replacement.md:8` — urllib.request
- `wechat-article-sop\references\cover-replacement.md:13` — urllib.request
- `wechat-article-sop\references\cover-replacement.md:21` — urllib.request
- `wechat-article-sop\references\cover-replacement.md:38` — urllib.request
- `wechat-article-sop\references\cover-replacement.md:40` — urllib.request
- `wechat-article-sop\references\cover-replacement.md:56` — urllib.request
- `wechat-article-sop\references\cover-replacement.md:58` — urllib.request
- `wechat-article-sop\references\draft-get-verify.md:20` — urllib.request
- `wechat-article-sop\references\draft-get-verify.md:22` — urllib.request
- `wechat-article-sop\references\draft-get-verify.md:25` — urllib.request
- `wechat-article-sop\references\draft-sync-workflow.md:13` — urllib.request
- `wechat-article-sop\references\draft-sync-workflow.md:21` — urllib.request
- `wechat-article-sop\references\draft-sync-workflow.md:22` — urllib.request
- `wechat-article-sop\references\draft-sync-workflow.md:25` — urllib.request
- `wechat-article-sop\references\draft-sync-workflow.md:27` — urllib.request
- `wechat-article-sop\references\draft-sync-workflow.md:38` — urllib.request
- `wechat-article-sop\references\draft-sync-workflow.md:40` — urllib.request
- `wechat-article-sop\references\draft-sync-workflow.md:105` — urllib.request
- `wechat-article-sop\references\draft-sync-workflow.md:119` — urllib.request
- `wechat-article-sop\references\draft-sync-workflow.md:120` — urllib.request
- `wechat-article-sop\references\draft-sync-workflow.md:130` — urllib.request

## 明细：b64_blob

（无命中）
