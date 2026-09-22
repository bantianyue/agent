import os, re, shutil, hashlib, json

SRC = r"C:\Users\twfehh7\.codex\skills"
DST = r"C:\Users\twfehh7\.workbuddy\skills"
OUTDIR = r"D:\06_Hermes\articles\_tmp_skillmig"

SKILLS = [
    "article-collect", "article-tracker-maintenance", "articles-content-edit",
    "baoyu-post-to-wechat", "figure-extraction", "paper-analysis-wechat",
    "url-content-extraction", "video-to-article", "video-to-wechat-article",
    "web-content-fetch", "wechat-article-sop",
]

SKIP_DIRS = {".git", "__pycache__", ".idea", ".github"}
SKIP_FILE_RE = re.compile(r"^(?!x)x")
SKIP_EXT = {".pyc", ".pyo"}

REWRITE_EXT = {".md", ".json", ".py", ".ts", ".js", ".txt", ".yml", ".yaml",
               ".vbs", ".html", ".sh", ".cjs", ".mjs", ".toml", ".ini",
               ".cfg", ".ps1", ".bat", ".jsonl", ".tex", ".bib", ".css"}

OLD_A = "C:/Users/twfehh7/.codex/skills"
NEW_A = "C:/Users/twfehh7/.workbuddy/skills"
OLD_B = "C:\\Users\\twfehh7\\.codex\\skills"
NEW_B = "C:\\Users\\twfehh7\\.workbuddy\\skills"


def snapshot(root):
    n = b = 0
    digests = {}
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if d not in SKIP_DIRS]
        for fn in fns:
            fp = os.path.join(dp, fn)
            rel = os.path.relpath(fp, SRC)
            n += 1
            try:
                b += os.path.getsize(fp)
            except OSError:
                pass
            if fn == "SKILL.md":
                with open(fp, "rb") as f:
                    digests[rel] = hashlib.sha256(f.read()).hexdigest()[:16]
    return n, b, digests


before = snapshot(SRC)

copied_files = copied_bytes = 0
rewrite_log = {}
errors = []

for sk in SKILLS:
    s = os.path.join(SRC, sk)
    d = os.path.join(DST, sk)
    if os.path.exists(d):
        errors.append("目标已存在，跳过：%s" % d)
        continue

    def ignore(dirpath, names, _sk=sk):
        out = []
        for nm in names:
            full = os.path.join(dirpath, nm)
            if os.path.isdir(full):
                if nm in SKIP_DIRS:
                    out.append(nm)
            else:
                if SKIP_FILE_RE.match(nm) or os.path.splitext(nm)[1].lower() in SKIP_EXT:
                    out.append(nm)
        return out

    try:
        shutil.copytree(s, d, ignore=ignore)
    except Exception as e:
        errors.append("复制失败 %s: %r" % (sk, e))
        continue

    for dp, dns, fns in os.walk(d):
        if "node_modules" in dp.split(os.sep):
            continue
        for fn in fns:
            fp = os.path.join(dp, fn)
            copied_files += 1
            try:
                copied_bytes += os.path.getsize(fp)
            except OSError:
                pass
            if os.path.splitext(fn)[1].lower() not in REWRITE_EXT:
                continue
            with open(fp, "rb") as f:
                raw = f.read()
            try:
                txt = raw.decode("utf-8")
            except UnicodeDecodeError:
                continue
            c = txt.count(OLD_A) + txt.count(OLD_B)
            if c == 0:
                continue
            new = txt.replace(OLD_A, NEW_A).replace(OLD_B, NEW_B)
            with open(fp, "wb") as f:
                f.write(new.encode("utf-8"))
            rewrite_log[os.path.relpath(fp, DST)] = c

after = snapshot(SRC)

lines = []
A = lines.append
A("# skill 迁移报告")
A("")
A("源：`%s`（未改动）" % SRC)
A("目标：`%s`" % DST)
A("")
A("## 复制结果")
A("")
A("| 项 | 值 |")
A("|---|---|")
A("| 复制 skill 数 | %d |" % len(SKILLS))
A("| 复制文件数（不含 node_modules 计数） | %d |" % copied_files)
A("| 复制体积（不含 node_modules） | %.1f MB |" % (copied_bytes / 1048576))
A("| 路径改写文件数 | %d |" % len(rewrite_log))
A("| 路径改写总处数 | %d |" % sum(rewrite_log.values()))
A("")
A("## 源目录完整性校验（复制前后应完全一致）")
A("")
A("| 项 | 复制前 | 复制后 | 一致 |")
A("|---|---:|---:|:--:|")
A("| 文件总数 | %d | %d | %s |" % (before[0], after[0], "是" if before[0] == after[0] else "否"))
A("| 总字节 | %d | %d | %s |" % (before[1], after[1], "是" if before[1] == after[1] else "否"))
A("| SKILL.md 哈希 | %d 个 | %d 个 | %s |" % (
    len(before[2]), len(after[2]), "是" if before[2] == after[2] else "否"))
A("")
A("## 路径改写明细（按处数降序）")
A("")
A("| 副本内文件 | 改写处数 |")
A("|---|---:|")
for k, v in sorted(rewrite_log.items(), key=lambda x: -x[1]):
    A("| `%s` | %d |" % (k.replace("\\", "/"), v))
A("")
A("## 各 skill 副本落点校验")
A("")
A("| skill | 目标存在 | SKILL.md | frontmatter name |")
A("|---|---|:--:|---|")
for sk in SKILLS:
    d = os.path.join(DST, sk)
    skmd = os.path.join(d, "SKILL.md")
    exists = os.path.isdir(d)
    has = os.path.isfile(skmd)
    name = "-"
    if has:
        with open(skmd, "r", encoding="utf-8", errors="replace") as f:
            head = f.read(600)
        m = re.search(r"^name:\s*(.+)$", head, re.M)
        if m:
            name = m.group(1).strip()
    A("| %s | %s | %s | %s |" % (sk, "是" if exists else "否",
                                 "有" if has else "无", name))
A("")
A("## 残留 .codex 路径扫描（副本内）")
A("")
leftover = {}
for sk in SKILLS:
    for dp, dns, fns in os.walk(os.path.join(DST, sk)):
        if "node_modules" in dp.split(os.sep):
            continue
        for fn in fns:
            fp = os.path.join(dp, fn)
            if os.path.splitext(fn)[1].lower() not in REWRITE_EXT:
                continue
            try:
                with open(fp, "r", encoding="utf-8", errors="replace") as f:
                    t = f.read()
            except OSError:
                continue
            c = t.count(".codex/skills") + t.count(".codex\\skills")
            if c:
                leftover[os.path.relpath(fp, DST)] = c
if leftover:
    A("仍有残留（需人工确认）：")
    A("")
    for k, v in sorted(leftover.items(), key=lambda x: -x[1]):
        A("- `%s` — %d 处" % (k.replace("\\", "/"), v))
else:
    A("无残留，全部 11 个副本已不含 .codex/skills 引用。")
A("")
if errors:
    A("## 异常")
    A("")
    for e in errors:
        A("- %s" % e)
    A("")

with open(os.path.join(OUTDIR, "migration_report.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
with open(os.path.join(OUTDIR, "migration_report.json"), "w", encoding="utf-8") as f:
    json.dump({"rewrite_log": rewrite_log, "leftover": leftover, "errors": errors,
               "copied_files": copied_files, "copied_bytes": copied_bytes,
               "source_unchanged": before[0] == after[0] and before[1] == after[1]
                                   and before[2] == after[2]}, f,
              ensure_ascii=False, indent=1)
print("MIGRATION_DONE")
