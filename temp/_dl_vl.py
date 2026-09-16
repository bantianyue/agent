# -*- coding: utf-8 -*-
import os,urllib.request,concurrent.futures,io
from PIL import Image
op=urllib.request.build_opener(urllib.request.ProxyHandler({"http":"http://127.0.0.1:7890","https":"http://127.0.0.1:7890"}))
DIR=r"D:/06_Hermes/articles/vllm-agentx-agentic-serving"
IDS=["HRuGTJta0AAtqjg","HRuGtNsb0AEYcDh","HRuG2Axb0AAtywo","HRuHIJAbUAA9-8Y","HRuHYB8acAA-JHz","HRuH0nNaIAAiIfS","HRuICi6WkAAexvI","HRuIJF-XoAA0_E0"]
H={"User-Agent":"Mozilla/5.0","Referer":"https://x.com/"}
def ff(i,id_):
    u=f"https://pbs.twimg.com/media/{id_}?format=jpg&name=900x900"
    try:
        d=op.open(urllib.request.Request(u,headers=H),timeout=90).read()
        im=Image.open(io.BytesIO(d)).convert('RGB')
        im.save(os.path.join(DIR,f"fig{i+1:02d}.png"))
        return (i+1,im.size,True)
    except Exception as e:
        return (i+1,str(e)[:60],False)
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
    for i,id_ in enumerate(IDS):
        n,info,ok=ff(i,id_)
        print(("ok " if ok else "fail"),n,info)
