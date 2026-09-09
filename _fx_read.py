import json,sys
sys.stdout.reconfigure(encoding='utf-8')
try:
    d=json.load(open(r'D:\06_Hermes\articles\_fx_probe.json',encoding='utf-8'))
except Exception as e:
    print('parse err',e); raise SystemExit
t=d.get('tweet',{})
print('user:',(t.get('author') or {}).get('screen_name'))
print('text:',(t.get('text') or '')[:400])
print('media count:',len(t.get('media',{}).get('all',[]) if t.get('media') else []))
art=t.get('article')
print('article?', bool(art))
if art:
    print('article title:', (art.get('title') or '')[:200])
    print('article blocks:',len((art.get('content') or {}).get('blocks',[]) if isinstance(art.get('content'),dict) else []))
    print('article keys:', list(art.keys())[:20])
