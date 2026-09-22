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

PURGE = [r"C:\Users\twfehh7\.workbuddy\skills\baoyu-post-to-wechat\scripts\node_modules"]

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".idea", ".github"}
SKIP_EXT = {".pyc", ".pyo"}
REWRITE_EXT = {".md", ".json", ".py", ".ts", ".js", ".txt", ".yml", ".yaml",
               ".vbs", ".html", ".sh", ".cjs", ".mjs", ".toml", ".ini",
               ".cfg", ".ps1", ".bat", ".jsonl", ".tex", ".bib", ".css"}

OLD_A, NEW_A = "C:/Users/twfehh7/.codex/skills", "C:/Users/twfehh7/.workbuddy/skills"
OLD_B = "C:\\Users\\twfehh7\\.codex\\skills"
NEW_B = "C:\\Users\\twfehh7\\.workbuddy\\skills"

purged = []
for p in PURGE:
    pn = os.path.normpath(p)
    assert pn.startswith(os.path.normpath(DST) + os.sep), "拒绝删除目标目录外路径: " + pn
    assert os.path.basename(pn) == "node_modules", "拒绝删除非 node_modules 路径: " + pn
    if os.path.isdir(pn):
        n = sum(len(f) for _, _, f in os.walk(pn))
        shutil.rmtree(pn)
        purged.append((pn, n))


def snapshot(root):
    n = b = 0
    dig = {}
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if d not in SKIP_DIRS]
        for fn in fns:
            fp = os.path.join(dp, fn)
            n += 1
            try:
                b += os.path.getsize(fp)
            except OSError:
                pass
            if fn == "SKILL.md":
                with open(fp, "rb") as f:
                    dig[os.path.relpath(fp, SRC)] = hashlib.sha256(f.read()).hexdigest()[:16]
    return n, b, dig


before = snapshot(SRC)


def ignore(dirpath, names):
    out = []
    for nm in names:
        full = os.path.join(dirpath, nm)
        if os.path.isdir(full):
            if nm in SKIP_DIRS:
                out.append(nm)
        elif os.path.splitext(nm)[1].lower() in SKIP_EXT:
            out.append(nm)
    return out


copied = {}
rewrite_log = {}
errors = []

for sk in SKILLS:
    s, d = os.path.join(SRC, sk), os.path.join(DST, sk)
    try:
        shutil.copytree(s, d, ignore=ignore, dirs_exist_ok=True)
    except Exception as e:
        errors.append("复制失败 %s: %r" % (sk, e))
        continue
    n = b = 0
    for dp, dns, fns in os.walk(d):
        for fn in fns:
            fp = os.path.join(dp, fn)
            n += 1
            try:
                b += os.path.getsize(fp)
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
            with open(fp, "wb") as f:
                f.write(txt.replace(OLD_A, NEW_A).replace(OLD_B, NEW_B).encode("utf-8"))
            rewrite_log[os.path.relpath(fp, DST)] = rewrite_log.get(
                os.path.relpath(fp, DST), 0) + c
    copied[sk] = (n, b)

after = snapshot(SRC)

leftover = {}
for sk in SKILLS:
    for dp, dns, fns in os.walk(os.path.join(DST, sk)):
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

L = []
A = L.append
A("# skill 迁移报告（第二轮 · 排除 node_modules）")
A("")
A("源 `%s`（只读，未改动） → 目标 `%s`" % (SRC, DST))
A("")
A("## 清理残缺副本")
A("")
if purged:
    for p, n in purged:
        A("- 已删除 `%s`（%d 个文件）" % (p, n))
else:
    A("- 无需清理")
A("")
A("## 复制结果")
A("")
A("| skill | 副本文件数 | 副本体积 |")
A("|---|---:|---:|")
for sk in SKILLS:
    if sk in copied:
        A("| %s | %d | %.2f MB |" % (sk, copied[sk][0], copied[sk][1] / 1048576))
A("| **合计** | **%d** | **%.2f MB** |" % (sum(v[0] for v in copied.values()),
                                            sum(v[1] for v in copied.values()) / 1048576))
A("")
A("## 源目录完整性校验")
A("")
A("| 项 | 复制前 | 复制后 | 一致 |")
A("|---|---:|---:|:--:|")
A("| 文件总数 | %d | %d | %s |" % (before[0], after[0], "是" if before[0] == after[0] else "否"))
A("| 总字节 | %d | %d | %s |" % (before[1], after[1], "是" if before[1] == after[1] else "否"))
A("| SKILL.md 哈希 | %d | %d | %s |" % (len(before[2]), len(after[2]),
                                        "是" if before[2] == after[2] else "否"))
A("")
A("## 路径改写（.codex/skills → .workbuddy/skills）")
A("")
A("共 %d 个文件、%d 处。" % (len(rewrite_log), sum(rewrite_log.values())))
A("")
A("| 副本内文件 | 处数 |")
A("|---|---:|")
for k, v in sorted(rewrite_log.items(), key=lambda x: -x[1]):
    A("| `%s` | %d |" % (k.replace("\\", "/"), v))
A("")
A("## 副本可用性校验")
A("")
A("| skill | SKILL.md | frontmatter name |")
A("|---|:--:|---|")
for sk in SKILLS:
    md = os.path.join(DST, sk, "SKILL.md")
    name = "-"
    if os.path.isfile(md):
        with open(md, "r", encoding="utf-8", errors="replace") as f:
            head = f.read(600)
        m = re.search(r"^name:\s*(.+)$", head, re.M)
        name = m.group(1).strip() if m else "（缺 name）"
    A("| %s | %s | %s |" % (sk, "有" if os.path.isfile(md) else "无", name))
A("")
A("## 残留 .codex 路径")
A("")
if leftover:
    for k, v in sorted(leftover.items(), key=lambda x: -x[1]):
        A("- `%s` — %d 处" % (k.replace("\\", "/"), v))
else:
    A("无残留：11 个副本已不含任何 `.codex/skills` 引用。")
A("")
if errors:
    A("## 异常")
    A("")
    for e in errors:
        A("- %s" % e)
    A("")

with open(os.path.join(OUTDIR, "migration_report.md"), "w", encoding="utf-8") as f:
    f.write("\n".join(L))
with open(os.path.join(OUTDIR, "migration_report.json"), "w", encoding="utf-8") as f:
    json.dump({"purged": purged, "copied": copied, "rewrite_log": rewrite_log,
               "leftover": leftover, "errors": errors,
               "source_unchanged": before[0] == after[0] and before[1] == after[1]
                                   and before[2] == after[2]}, f,
              ensure_ascii=False, indent=1)
print("MIGRATION2_DONE")
