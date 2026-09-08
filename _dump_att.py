import json
j=json.load(open('attention-mechanisms-explained-long/article_data.json',encoding='utf-8'))
for i,s in enumerate(j['sections']):
    fa=s.get('fig_after') or {}
    print('== sec%d %s'%(i,s.get('title')))
    for pi,pa in enumerate(s['paras']):
        figs=fa.get(str(pi)) or []
        print('  p%d: %s...'%(pi,pa[:26].replace(chr(10),' ')))
        for f in figs: print('      >> FIG', f.get('src'))
