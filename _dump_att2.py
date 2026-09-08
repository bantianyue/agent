import json
j=json.load(open('attention-mechanisms-explained-long/article_data.json',encoding='utf-8'))
for i,sec in enumerate(j['sections']):
    print('== sec%d %s'%(i,sec.get('title')))
    for pi,pa in enumerate(sec['paras']):
        print('  p%d: %s'%(pi,pa))
