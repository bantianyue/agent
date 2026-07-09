import httpx, time, os, re, json

PROXY = "http://127.0.0.1:7890"
URLS = [
    ("arxiv", "https://arxiv.org/html/2607.05794v1"),
    ("claude_blog", "https://claude.com/blog/claude-model-and-effort-level-in-claude-code"),
    ("cognition", "https://cognition.com/blog/swe-1-7"),
    ("x_sergio", "https://x.com/SergioPaniego/status/2074863503312044499"),
    ("x_christine", "https://x.com/christinexzhu/status/2074847461588267466"),
]
OUT = "C:/Users/twfehh7/url_extract_test/out"
RES = "C:/Users/twfehh7/url_extract_test/results_f.json"
os.makedirs(OUT, exist_ok=True)
results = {}

# Jina Reader: GET https://r.jina.ai/<url>  -> markdown
# Optional headers: X-With-Images-Summary: true to embed image URLs
HDR = {
    "User-Agent": "Mozilla/5.0",
    "X-With-Images-Summary": "true",
    "X-Return-Format": "markdown",
}

def main():
    for name, url in URLS:
        t = time.time()
        try:
            r = httpx.get("https://r.jina.ai/" + url, proxy=PROXY,
                          follow_redirects=True, timeout=90, headers=HDR)
            md = r.text or ""
            dt = round(time.time() - t, 1)
            # stats
            imgs = re.findall(r'!\[[^\]]*\]\(([^)]+)\)', md)  # markdown image syntax
            imgs += re.findall(r'https?://[^\s)\]]+\.(?:png|jpg|jpeg|webp|gif)', md, re.I)
            imgs = [x for x in imgs if x.startswith("http")]
            # hero: first image or og
            hero = imgs[0] if imgs else ""
            results[name] = {
                "F_jina": {
                    "time_s": dt, "status": r.status_code,
                    "md_len": len(md), "body_chars": len(md),
                    "img_count": len(set(imgs)),
                    "hero": hero[:200] if hero else "",
                    "title_line": (md.splitlines()[0] if md else ""),
                }
            }
            with open(f"{OUT}/{name}_jina.md", "w", encoding="utf-8") as f:
                f.write(md)
            print(f"{name}: OK {dt}s status={r.status_code} md={len(md)} imgs={len(set(imgs))} hero={'Y' if hero else 'N'}", flush=True)
        except Exception as e:
            results[name] = {"F_jina": {"error": str(e)[:200], "time_s": round(time.time()-t,1)}}
            print(f"{name}: ERR {str(e)[:120]}", flush=True)
        with open(RES, "w") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
    print("F DONE", flush=True)
    with open(RES, "w") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
