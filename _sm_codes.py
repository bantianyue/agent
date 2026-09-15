import re,sys
sys.stdout.reconfigure(encoding='utf-8')
t=open('_sm_body.txt',encoding='utf-8').read()
blocks=re.findall(r'\[CODE\]\n(.*?)\n\[/CODE\]', t, re.S)
print('blocks',len(blocks))
for i,b in enumerate(blocks,1):
    lines=b.splitlines()
    first=next((l for l in lines if l.strip()), '')
    last=lines[-1] if lines else ''
    print('%02d lines=%3d | %s | %s' % (i, len(lines), first[:66], last[:40]))
