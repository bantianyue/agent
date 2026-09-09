import re,sys,json
sys.stdout.reconfigure(encoding='utf-8')
# find figNN -> original url mapping in 8/11 artifacts
for fn in ['_extract_blocks.json','_content.json']:
    try:
        raw=open(fn,encoding='utf-8',errors='ignore').read()
        pairs=re.findall(r'"(?:fig\d+|fig\d+\.png)"\s*:\s*"[^"]*"', raw)
        print(fn, 'pairs:', len(pairs))
        for p in pairs[:40]:
            if 'fig' in p: print('  ',p[:200])
    except Exception as e:
        print(fn,'ERR',e)
# build figs section
b=open('article_data_build.py',encoding='utf-8').read()
print('build mentions fig04:', b.count('fig04'))
print('build fig srcs used:', sorted(set(re.findall(r'fig\d\d\.png',b))))
