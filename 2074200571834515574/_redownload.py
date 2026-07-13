import urllib.request, os, base64
here = os.path.dirname(os.path.abspath(__file__))
urls = []
with open(os.path.join(here,"image_list.txt"),encoding="utf-8") as f:
    for line in f:
        line=line.strip()
        if line.startswith("[img"):
            urls.append(line.split("] ",1)[1].strip())
print("total", len(urls))
n=0
for i,src in enumerate(urls,1):
    if i==1:
        fname="cover.jpg"
    else:
        n+=1
        fname=f"fig{n:02d}.jpg"
    try:
        req=urllib.request.Request(src, headers={"User-Agent":"Mozilla/5.0"})
        data=urllib.request.urlopen(req, timeout=30).read()
        open(os.path.join(here,fname),"wb").write(data)
        print(f"OK {fname} ({len(data)//1024}KB)")
    except Exception as e:
        print(f"FAIL {fname}: {e}")
