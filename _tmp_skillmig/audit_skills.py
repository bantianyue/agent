import os, re, json
from collections import Counter

SRC = r"C:\Users\twfehh7\.codex\skills"
OUTDIR = r"D:\06_Hermes\articles\_tmp_skillmig"

SKILLS = [
    "article-collect", "article-tracker-maintenance", "articles-content-edit",
    "baoyu-post-to-wechat", "figure-extraction", "paper-analysis-wechat",
    "url-content-extraction", "video-to-article", "video-to-wechat-article",
    "web-content-fetch", "wechat-article-sop",
]
SKIP_DIRS = {".git", "node_modules", "__pycache__", ".system", ".idea", ".github"}
TEXT_EXT = {".md", ".json", ".py", ".ts", ".js", ".txt", ".yml", ".yaml", ".vbs",
            ".html", ".sh", ".cjs", ".mjs", ".toml", ".ini", ".cfg", ".ps1",
            ".bat", ".jsonl", ".tex", ".bib", ".css"}

PATTERNS = {
    "secrets": re.compile(r"""(?i)(api[_-]?key|app[_-]?secret|secret|password|passwd|access[_-]?token|bearer)\s*[=:"'\s]{1,4}["']?([A-Za-z0-9_\-]{12,})"""),
    "credential_access": re.compile(r"""(?i)(\.env\b|\.netrc|id_rsa|\.ssh[/\\]|credentials|login[_-]?data|Cookies?\b|cookie[_-]?file|Local Storage|Login Data)"""),
    "destructive": re.compile(r"""(?i)(rm\s+-[rf]{1,2}\s|rmtree|del\s+/[sq]\b|Remove-Item[^\n]{0,40}-Recurse|drop\s+table|git\s+clean\s+-[fdx]|git\s+reset\s+--hard|format\s+[a-z]:|shutil\.move)"""),
    "exec": re.compile(r"""(?i)\b(eval|exec)\s*\(|os\.system|subprocess\.(run|call|Popen|check_output)|child_process|new\s+Function\s*\(|Invoke-Expression"""),
    "network": re.compile(r"""(?i)(requests?\.(post|put|patch)|urllib\.request|fetch\s*\(|Invoke-WebRequest|Invoke-RestMethod|axios\.|http\.request)"""),
}
B64 = re.compile(r"""[A-Za-z0-9+/]{200,}={0,2}""")
URL = re.compile(r"""https?://([A-Za-z0-9\.\-]+)""")

findings = {k: [] for k in PATTERNS}
findings["b64_blob"] = []
hosts = Counter()
counts, sizes = {}, {}

for sk in SKILLS:
    root = os.path.join(SRC, sk)
    n, b = 0, 0
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if d not in SKIP_DIRS]
        for fn in fns:
            fp = os.path.join(dp, fn)
            rel = os.path.relpath(fp, SRC)
            n += 1
            try:
                b += os.path.getsize(fp)
            except OSError:
                continue
            if os.path.splitext(fn)[1].lower() not in TEXT_EXT:
                continue
            try:
                with open(fp, "r", encoding="utf-8", errors="replace") as f:
                    txt = f.read()
            except OSError:
                continue
            for h in URL.findall(txt):
                hosts[h] += 1
            for cat, rx in PATTERNS.items():
                for m in rx.finditer(txt):
                    if len(findings[cat]) < 80:
                        line_no = txt[:m.start()].count("\n") + 1
                        snip = m.group(0).replace("\n", " ")[:120]
                        if cat == "secrets":
                            snip = m.group(1) + " = <redacted>"
                        findings[cat].append({"file": rel, "line": line_no, "snippet": snip})
            for m in B64.finditer(txt):
                if len(findings["b64_blob"]) < 20:
                    findings["b64_blob"].append({"file": rel, "len": len(m.group(0))})
    counts[sk], sizes[sk] = n, b

lines = []
A = lines.append
A("# codex skills 安装前安全审计")
A("")
A("## 体量")
A("")
A("| skill | 文件数（排除 .git/node_modules/__pycache__） | 大小 |")
A("|---|---:|---:|")
for sk in SKILLS:
    A("| %s | %d | %.1f KB |" % (sk, counts[sk], sizes[sk] / 1024))
A("| **合计** | **%d** | **%.1f MB** |" % (sum(counts.values()), sum(sizes.values()) / 1048576))
A("")
A("## 扫描命中统计")
A("")
A("| 类别 | 命中条数 |")
A("|---|---:|")
for cat in PATTERNS:
    A("| %s | %d |" % (cat, len(findings[cat])))
A("| b64_blob | %d |" % len(findings["b64_blob"]))
A("")
A("## 外联域名 top 30")
A("")
A("| 域名 | 出现次数 |")
A("|---|---:|")
for h, c in hosts.most_common(30):
    A("| %s | %d |" % (h, c))
A("")
for cat in list(PATTERNS) + ["b64_blob"]:
    A("## 明细：%s" % cat)
    A("")
    if not findings[cat]:
        A("（无命中）")
        A("")
        continue
    for it in findings[cat]:
        if cat == "b64_blob":
            A("- `%s` — base64 长度 %d" % (it["file"], it["len"]))
        else:
            A("- `%s:%d` — %s" % (it["file"], it["line"], it["snippet"]))
    A("")

with open(os.path.join(OUTDIR, "audit_report.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
with open(os.path.join(OUTDIR, "audit_report.json"), "w", encoding="utf-8") as f:
    json.dump({"counts": counts, "sizes": sizes, "hosts": hosts.most_common(),
               "findings": findings}, f, ensure_ascii=False, indent=1)
print("AUDIT_DONE")
