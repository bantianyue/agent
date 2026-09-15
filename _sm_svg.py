import re,sys,os,subprocess
sys.stdout.reconfigure(encoding='utf-8')
from PIL import Image, ImageChops
chrome=r"C:\Program Files\Google\Chrome\Application\chrome.exe"
pairs=[('_sm2.svg','_sm2.png'),('_sm3.svg','_sm3.png'),('_sm4.svg','_sm4.png'),('_sm5.svg','_sm5.png')]
for svg,out in pairs:
    s=open(svg,encoding='utf-8',errors='ignore').read()
    vb=re.search(r'viewBox="([^"]+)"',s)
    w=h=None
    if vb:
        parts=vb.group(1).split()
        if len(parts)==4: w=float(parts[2]); h=float(parts[3])
    ww=int(w or 1200); hh=int(h or 800)
    path=os.path.abspath(svg).replace('\\','/')
    tmp=out.replace('.png','_raw.png')
    subprocess.run([chrome,'--headless=new','--disable-gpu','--hide-scrollbars','--force-device-scale-factor=2',
                    f'--window-size={ww+40},{hh+40}',f'--screenshot={os.path.abspath(tmp)}',f'file:///{path}'],capture_output=True)
    im=Image.open(tmp).convert('RGB')
    bg=Image.new('RGB',im.size,(255,255,255))
    bbox=ImageChops.difference(im,bg).convert('L').getbbox()
    if bbox:
        pad=10
        im=im.crop((max(0,bbox[0]-pad),max(0,bbox[1]-pad),min(im.size[0],bbox[2]+pad),min(im.size[1],bbox[3]+pad)))
    if im.size[0]<1400:
        r=1400/im.size[0]; im=im.resize((1400,int(im.size[1]*r)),Image.LANCZOS)
    if im.size[0]>1400:
        r=1400/im.size[0]; im=im.resize((1400,int(im.size[1]*r)),Image.LANCZOS)
    im.save(out); os.remove(tmp)
    print(svg,'->',out,im.size)
