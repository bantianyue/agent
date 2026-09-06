import re, json
s=open('D:/06_Hermes/articles/art_fx_probe.json',encoding='utf-8',errors='replace').read()
s2=re.sub(r"\\\\(?![\\\\\"bfnrt/])", "", s)
d=json.loads(s2)
tw=d.get('tweet',{})
print('keys', list(tw.keys()))
print('user', (tw.get('author') or {}).get('screen_name'))
print('text', (tw.get('text') or '')[:120])
print("has 'article':", 'article' in tw)
a=tw.get('article') or {}
if a:
    print('article id', a.get('id'))
    print('article url', (a.get('url') or '')[:90])
    c=a.get('content') or {}
    blocks=c.get('blocks',[]); emap=c.get('entityMap',[])
    from collections import Counter
    etc=Counter()
    for e in emap: etc[e.get('value',{}).get('type')]+=1
    btc=Counter(b.get('type') for b in blocks)
    print('nblocks',len(blocks),'nemap',len(emap),'nmedia_entities',len(a.get('media_entities') or []))
    print('entity types',dict(etc))
    print('block types',dict(btc))
else:
    print('twitter_error', d.get('twitter_error'))
