import time, os, json
import trafilatura
from newspaper import Article
from bs4 import BeautifulSoup
import httpx

PROXY = "http://127.0.0.1:7890"
URLS = [
    ("arxiv", "https://arxiv.org/html/2607.05794v1"),
    ("claude_blog", "https://claude.com/blog/claude-model-and-effort-level-in-claude-code"),
    ("cognition", "https://cognition.com/blog/swe-1-7"),
    ("x_sergio", "https://x.com/SergioPaniego/status/2074863503312044499"),
    ("x_christine", "https://x.com/christinexzhu/status/2074847461588267466"),
]
OUT = "C:/Users/twfehh7/url_extract_test/out"
RES = "C:/Users/twfehh7/url_extract_test/results_bce.json"
os.makedirs(OUT, exist_ok=True)
results = {}

def log(msg):
    print(msg, flush=True)

def fetch(url):
    r = httpx.get(url, proxy=PROXY, follow_redirects=True, timeout=40,
                  headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
                           "Accept-Encoding": "gzip, deflate"})
    return r.text, r.status_code

def img_stats(html):
    soup = BeautifulSoup(html, "lxml")
    imgs = soup.find_all("img")
    n = 0
    for im in imgs:
        s = im.get("src") or im.get("data-src") or im.get("srcset")
        if s: n += 1
    og = soup.find("meta", attrs={"property": "og:image"})
    twitter = soup.find("meta", attrs={"name": "twitter:image"})
    hero = og.get("content") if og else (twitter.get("content") if twitter else "")
    return n, hero

for name, url in URLS:
    results[name] = {}
    log(f"[fetch] {name} ...")
    t0 = time.time()
    try:
        html, code = fetch(url)
    except Exception as e:
        log(f"  fetch failed: {e}")
        with open(RES,"w") as f: json.dump(results,f,ensure_ascii=False,indent=2)
        continue
    t_e = time.time() - t0
    n_imgs, hero = img_stats(html)
    results[name]["E_curl_bs4"] = {
        "time_s": round(t_e,2), "status": code, "html_len": len(html),
        "img_count": n_imgs, "hero_og": hero,
        "body_text_len": len(BeautifulSoup(html,"lxml").get_text()),
    }
    log(f"  E done {t_e:.1f}s imgs={n_imgs} hero={'Y' if hero else 'N'}")

    t0 = time.time()
    extracted = trafilatura.extract(html, include_images=True, include_links=True)
    t_b = time.time() - t0
    tcount = len(extracted) if extracted else 0
    try:
        jr = trafilatura.extract(html, output_format="json", with_metadata=True)
        timgs = 0
        if jr:
            j = json.loads(jr)
            timgs = len(j.get("image", []) or []) if isinstance(j.get("image"), list) else 0
    except Exception:
        timgs = 0
    results[name]["B_trafilatura"] = {
        "time_s": round(t_b + t_e,2), "body_chars": tcount, "img_count": timgs, "hero": "",
    }
    if extracted:
        with open(f"{OUT}/{name}_trafilatura.txt","w",encoding="utf-8") as f: f.write(extracted)
    log(f"  B done body={tcount} imgs={timgs}")

    t0 = time.time()
    try:
        a = Article(url, language="en")
        a.download(input_html=html)
        a.parse()
        body = a.text or ""
        t_c = time.time() - t0
        results[name]["C_newspaper3k"] = {
            "time_s": round(t_c,2), "body_chars": len(body),
            "img_count": len(a.images), "top_image": a.top_image, "title": a.title,
        }
    except Exception as e:
        results[name]["C_newspaper3k"] = {"error": str(e)[:200]}
    log(f"  C done: {results[name].get('C_newspaper3k',{}).get('body_chars','ERR')}")

    with open(f"{OUT}/{name}.html","w",encoding="utf-8") as f: f.write(html)
    with open(RES,"w") as f: json.dump(results,f,ensure_ascii=False,indent=2)
    log(f"[done] {name}")

log("ALL DONE")
with open(RES,"w") as f: json.dump(results,f,ensure_ascii=False,indent=2)
