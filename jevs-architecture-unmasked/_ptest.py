import urllib.request, ssl, os, socket
socket.setdefaulttimeout(20)
for k in ("HTTP_PROXY","HTTPS_PROXY","http_proxy","https_proxy","ALL_PROXY","all_proxy"):
    os.environ.pop(k, None)
url = "https://archerhume.com/posts/jevs-architecture-unmasked/?v=3"
UA = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0 Safari/537.36"}
res = []
for name, ph in [("7890", {"http":"http://127.0.0.1:7890","https":"http://127.0.0.1:7890"}),
                 ("7897", {"http":"http://127.0.0.1:7897","https":"http://127.0.0.1:7897"}),
                 ("none", {})]:
    try:
        op = urllib.request.build_opener(urllib.request.ProxyHandler(ph))
        r = op.open(urllib.request.Request(url, headers=UA), timeout=30)
        b = r.read()
        res.append("%s OK %s len=%d" % (name, r.status, len(b)))
        if len(b) > 5000:
            open("_page.html","wb").write(b)
            res.append("saved to _page.html via %s" % name)
    except Exception as e:
        res.append("%s FAIL %r" % (name, e))
open("_ptest.txt","w",encoding="utf-8").write("\n".join(res))
print("done")
