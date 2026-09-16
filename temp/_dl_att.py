# -*- coding: utf-8 -*-
import os,urllib.request,concurrent.futures,io
from PIL import Image
proxy={"http":"http://127.0.0.1:7890","https":"http://127.0.0.1:7890"}
op=urllib.request.build_opener(urllib.request.ProxyHandler(proxy))
DIR=r"D:/06_Hermes/articles/attention-mechanisms-explained-long"
BOD=["HRc63ipbwAAJQOk","HRc7Cs0a4AArnck","HRc7JIUbAAAhuFp","HRc7QVKaoAA0atQ","HRc7TFBbcAAzJip","HRc7ZwNb0AAKIDU","HRc7fzKaAAAO4nG","HRc7l-ebwAAYsZl","HRc7qrCbQAAMHDu","HRc7vl6aoAALfcK","HRc72RybkAA_ecF","HRc78OBboAAZyS1","HRc8ddZaQAAhxyv","HRc8hh7bUAARcqI","HRc97jtbUAA7fWf","HRc9_kLbEAI-F0j"]
H={"User-Agent":"Mozilla/5.0","Referer":"https://x.com/"}
def fetch(id_):
    u=f"https://pbs.twimg.com/media/{id_}?format=jpg&name=900x900"
    try:
        data=op.open(urllib.request.Request(u,headers=H),timeout=90).read()
        return id_,data
    except Exception as e:
        return id_,("ERR"+str(e)[:80]).encode()
ok=0
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
    for id_,data in ex.map(fetch,BOD):
        if data.startswith(b'ERR'):
            print("fail",id_,data[:60]); continue
        try:
            im=Image.open(io.BytesIO(data)).convert('RGB')
        except Exception as e:
            print("imgfail",id_,str(e)[:80]); continue
        idx=BOD.index(id_)+1
        im.save(os.path.join(DIR,f"fig{idx:02d}.png"))
        ok+=1
print("saved ok",ok)
