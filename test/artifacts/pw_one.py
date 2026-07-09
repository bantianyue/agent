import subprocess, time, os, re, sys

PROXY = "http://127.0.0.1:7890"
EXE = "C:/Users/twfehh7/AppData/Local/ms-playwright/chromium-1228/chrome-win64/chrome.exe"
OUT = "C:/Users/twfehh7/url_extract_test/out"
os.makedirs(OUT, exist_ok=True)
LABEL = sys.argv[1]
URL = sys.argv[2]
WAIT = int(sys.argv[3]) if len(sys.argv) > 3 else 12

t = time.time()
cmd = [
    EXE, "--headless=new", "--no-sandbox",
    "--disable-gpu",
    "--disable-gpu-sandbox",
    "--disable-software-rasterizer",
    "--use-gl=angle", "--use-angle=swiftshader",
    "--disable-accelerated-2d-canvas",
    "--disable-dev-shm-usage", f"--proxy-server={PROXY}",
    "--proxy-bypass-list=<-loopback>",
    f"--timeout={WAIT*1000}",
    "--dump-dom", URL,
]
try:
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=110,
                       encoding="utf-8", errors="replace")
    dom = r.stdout
    dt = round(time.time() - t, 1)
    if len(dom) < 200:
        print(f"{LABEL}: FAIL len={len(dom)} err={r.stderr[:200]}", flush=True)
        sys.exit(0)
    txt = re.sub(r"<script.*?</script>", "", dom, flags=re.S)
    txt = re.sub(r"<style.*?</style>", "", txt, flags=re.S)
    txt = re.sub(r"<[^>]+>", " ", txt)
    txt = re.sub(r"\s+", " ", txt).strip()
    imgs = [x for x in re.findall(r'<img[^>]+src=["\']([^"\']+)', dom) if x and not x.startswith("data:")]
    m = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)', dom)
    hero = m.group(1) if m else ""
    print(f"{LABEL}: OK dom={len(dom)} body={len(txt)} imgs={len(imgs)} hero={'Y' if hero else 'N'} t={dt}s", flush=True)
    if hero: print("  hero:", hero[:160], flush=True)
    with open(f"{OUT}/{LABEL}_dumpdom.html", "w", encoding="utf-8") as f:
        f.write(dom)
except subprocess.TimeoutExpired:
    print(f"{LABEL}: TIMEOUT 110s", flush=True)
except Exception as e:
    print(f"{LABEL}: ERR {e}", flush=True)
print(f"{LABEL} DONE", flush=True)
