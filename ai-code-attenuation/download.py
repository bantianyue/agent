import urllib.request
import os

urls = {
    "methodology.jpg": "https://pbs.twimg.com/media/HKREvipaAAAq1hP?format=jpg&name=orig",
    "attenuation.jpg": "https://pbs.twimg.com/media/HKRFArJbsAAfs4A?format=jpg&name=orig"
}

dest = r"D:\06_Hermes\articles\ai-code-attenuation"

for name, url in urls.items():
    path = os.path.join(dest, name)
    if os.path.exists(path):
        print(f"{name}: already exists ({os.path.getsize(path)} bytes)")
        continue
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
            with open(path, "wb") as f:
                f.write(data)
        print(f"{name}: OK ({len(data)} bytes)")
    except Exception as e:
        print(f"{name}: FAILED - {e}")
