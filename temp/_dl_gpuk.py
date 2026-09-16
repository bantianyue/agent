# -*- coding: utf-8 -*-
import os,urllib.request,io
from PIL import Image
os.makedirs('_gpuk_dl',exist_ok=True)
proxy={"http":"http://127.0.0.1:7890","https":"http://127.0.0.1:7890"}
op=urllib.request.build_opener(urllib.request.ProxyHandler(proxy))
IDS=["HRpv4FbbkAAby6R","HRqlbvGa8AE0IEq","HRqQ2Y8bYAA1b6g","HRpFlX3bMAAsFlr","HRoDUjVbEAAAwug"]
H={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64)","Referer":"https://x.com/"}
for i,id_ in enumerate(IDS):
    for fmt in ("jpg","png","webp"):
        u=f"https://pbs.twimg.com/media/{id_}?format={fmt}&name=orig"
        try:
            data=op.open(urllib.request.Request(u,headers=H),timeout=60).read()
            im=Image.open(io.BytesIO(data))
            im.convert('RGB').save(f"_gpuk_dl/probe{i}_{id_[-6:]}.png")
            print(i,id_,fmt,"OK",im.size)
            break
        except Exception as e:
            if fmt=="webp": print(i,id_,"FAIL",str(e)[:60])
