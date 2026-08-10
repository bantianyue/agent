#!/usr/bin/env python3
"""临时：组装 Kimi K3 sections 预览。"""
import json, re

c = json.load(open(r"D:/06_Hermes/articles/kimi-k3-kda-norope/_content.json", encoding="utf-8"))
t = json.load(open(r"D:/06_Hermes/articles/kimi-k3-kda-norope/_translations.json", encoding="utf-8"))
bid=0; tid_map={}
for i,x in enumerate(c):
    if x['type'] in ('p','oli','uli','h2'):
        tid_map[i]=bid; bid+=1
    elif x['type']=='img' and x.get('caption'):
        tid_map[i]=bid; bid+=1
def tr(i): 
    tid=tid_map.get(i); return t.get(str(tid),'') if tid is not None else ''

ORDERED_CN = {}  # 有序列表序号计数
def list_item(txt, kind):
    """列表项：有序保序号、无序加项目符号。"""
    txt = txt.strip()
    if kind=='oli':
        m = re.match(r'^(\d+)\.\s?(.*)$', txt, re.S)
        if m:
            return f"{m.group(1)}. {m.group(2)}"
        return txt
    return f"• {txt}"

def split_nested(text):
    """把 p 中含 '\\nN. ' 的内嵌序号列表拆成多条 (prefix_para, [(num, item)])。"""
    parts = re.split(r'\n(?=\d+\.\s)', text)
    out = []
    for part in parts:
        if re.match(r'^\d+\.\s', part):
            out.append(('li', part.strip()))
        else:
            out.append(('p', part.strip()))
    return out

# 需要保留原文结构的子节标题（作为 h3）：这些是 p 但以 8.x 开头的加粗子标题
SUBHEAD_PAT = re.compile(r'^(8\.\d|Proposal\s\d|8\.\d\s)')

content_out = []
img_idx = 0
# capture lead
lead = tr(0) if len(c)>0 else ''

# 记录 idx0 为 lead 后，正文从 idx1 开始
sections = []
cur = None
para_list = []
fig_list = []

def flush():
    global cur, para_list, fig_list
    if cur is None: return
    if para_list or fig_list:
        fa = {}
        for pi, figs in fig_list:
            fa.setdefault(str(pi), []).extend(figs)
        sec = {'type':'h2','title':cur}
        sec['paras'] = para_list
        if fa: sec['fig_after'] = fa
        sections.append(sec)
    para_list = []; fig_list = []; cur = None

for i, x in enumerate(c):
    if i == 0:
        continue  # lead
    typ = x['type']
    if typ == 'h2':
        flush()
        cur = tr(i)
    elif typ == 'p':
        txt = tr(i).strip()
        if not txt: continue
        # 内嵌序号列表拆分
        subs = split_nested(txt)
        for st, s_txt in subs:
            if st == 'li':
                para_list.append(list_item(s_txt, 'oli'))
            else:
                para_list.append(s_txt)
    elif typ == 'oli':
        para_list.append(list_item(tr(i), 'oli'))
    elif typ == 'uli':
        para_list.append(list_item(tr(i), 'uli'))
    elif typ == 'img':
        pi = max(0, len(para_list)-1) if para_list else 0
        cap = tr(i)
        fig_list.append((pi, [{"src": x['file'], "caption": cap}]))
    elif typ == 'link':
        para_list.append(f"🔗 {x['text']}")

flush()

json.dump({"lead": lead, "sections": sections}, open(r"D:/06_Hermes/articles/kimi-k3-kda-norope/_sections_preview.json","w",encoding="utf-8"), ensure_ascii=False, indent=2)
print("lead len:", len(lead))
print("sections:", len(sections))
total_paras = sum(len(s.get('paras',[])) for s in sections)
print("total paras:", total_paras)
for s in sections:
    fa = s.get('fig_after',{})
    figs = sum(len(v) for v in fa.values())
    print(f"  [{s['title']}] paras={len(s.get('paras',[]))} figs={figs}")
