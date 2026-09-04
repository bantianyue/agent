# -*- coding: utf-8 -*-
# Re-capture DOM of the 供电/散热 region to confirm each image's context in ORIGINAL
from playwright.sync_api import sync_playwright
url="https://www.cerebras.ai/blog/ultrafast-frontier-inference-cerebras-deep-dive-at-hot-chips-2026"
with sync_playwright() as p:
    b=p.chromium.launch()
    pg=b.new_page(viewport={"width":1500,"height":1100})
    pg.goto(url, wait_until="domcontentloaded", timeout=45000)
    pg.wait_for_timeout(4000)
    try:
        for t in ["Accept all"]:
            el=pg.get_by_role("button",name=t).first
            if el.count():
                el.click(timeout=1500); pg.wait_for_timeout(1800); break
    except Exception: pass
    seg=pg.evaluate("""()=>{
      const out=[];
      const h1=document.querySelector('h1'); let node=h1;
      for(let i=0;i<8&&node&&node.parentElement;i++){node=node.parentElement; if(node.querySelectorAll('p').length>6)break;}
      const root=node||document.body;
      let inTarget=false;
      function nid(el){(el.getAttribute&&el.getAttribute('id'))||''}
      function walk(el,depth){
        if(!el||depth>30)return;
        if(el.nodeType===1){
          const T=el.tagName.toLowerCase();
          if(T==='script'||T==='style'||T==='nav')return;
          const txt=(el.innerText||'').replace(/\\s+/g,' ').trim();
          if(T==='h1'||T==='h2'||T==='h3'||T==='h4'){
            if(/CS-4：下一个速度标准|CS-6|晶圆级处理器|CS-4 是第一款|围绕晶圆|Power delivery|Cooling|CS-4/.test(txt)){
              if(/供电|Cooling|散热|供电子|围绕/.test(txt)) inTarget=true;
              else if(/CS-5|下一个速度标准|CS-6/.test(txt)) inTarget=false;
            }
          }
          if(T==='p'&&txt&&/(CS-4 把|先把电流|散热做进|Leak|每个 CS-4|0.5 毫米|converter|0.5 millimeter)/.test(txt)){ out.push('P:'+txt.slice(0,90)); return; }
        }
        // img at any depth w/in target para vicinity
        if(el.tagName&&el.tagName.toLowerCase()==='img'){
          const s=el.currentSrc||el.src||'';
          if(s.indexOf('sanity')>=0) out.push('IMG:'+s.split('/production/')[1].slice(0,8));
          return;
        }
        for(const c of Array.from(el.childNodes||[])) if(c.nodeType===1) walk(c,depth+1);
      }
      walk(root,0);
      return out;
    }""")
    print("\n".join(seg))
    b.close()
