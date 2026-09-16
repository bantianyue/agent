# -*- coding: utf-8 -*-
import urllib.request, os
proxy={'http':'http://127.0.0.1:7890','https':'http://127.0.0.1:7890'}
op=urllib.request.build_opener(urllib.request.ProxyHandler(proxy))
# slug -> (hero-id, ext)
jobs=[
 ("math-for-ai-inference-roadmap","HRoQG3EaQAAy5NX","jpg"),
 ("what-is-a-gpu-kernel-intro","HRqJ1kpaoAAcpfY","jpg"),
 ("attention-mechanisms-explained-long","HRc6Z2oasAArIQ-","png"),
]
for slug,fid,ext in jobs:
    u=f"https://pbs.twimg.com/media/{fid}?format={ext}&name=orig"
    d=os.path.join(r"D:/06_Hermes/articles",slug)
    dest=os.path.join(d,f"hero_src.{ext}")
    try:
        r=op.open(urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0","Referer":"https://x.com/"}),timeout=90).read()
        open(dest,'wb').write(r)
        from PIL import Image
        im=Image.open(dest)
        print(slug,"saved",dest,len(r),"px",im.size)
    except Exception as e:
        print(slug,"ERR",str(e)[:150])
