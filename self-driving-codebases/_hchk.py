import re,sys
sys.stdout.reconfigure(encoding='utf-8')
h=open('article.html',encoding='utf-8').read()
print('imgs',len(re.findall(r'<img',h)),'figsrc',sorted(set(re.findall(r'src="(fig\d+\.png)"',h))))
print('figcaption',len(re.findall(r'<figcaption',h)),'h2',len(re.findall(r'<h2',h)))
print('portal',len(re.findall(r'mp.weixin.qq.com/s/',h)))
for kw in ['结语','传送门','参考']:
    print(kw,[m.start() for m in re.finditer(kw,h)][:4])
i=h.find('结语'); j=h.find('参考')
print('order',0<i<j)
