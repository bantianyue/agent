# -*- coding: utf-8 -*-
"""生成器：按原文89块序列组装完整版 article_data_build.py"""
import json, os, sys
base=os.path.dirname(os.path.abspath(__file__))

d=json.load(open(os.path.join(base,"x_fast.json") if False else r"D:/06_Hermes/articles/x_fast.json",encoding="utf-8"))
c=d['tweet']['article']['content']
blocks=c['blocks']
em={str(e['key']): {'type':e['value']['type'],'data':e['value']['data']} for e in c['entityMap']}
all_zh=json.load(open(base+"/_all_zh.json",encoding="utf-8"))
block_to_me={12:7,16:14,21:0,33:2,35:12,39:13,41:1,46:8,58:11,60:6,70:4,72:15,82:3,85:9,89:10,102:5}
# fig 命名: 按 block 顺序 1..16
block_order=sorted(block_to_me.keys())
fig_by_block={bi:f"fig{n:02d}.jpg" for n,bi in enumerate(block_order,1)}
def lang_code(md):
    m=json.loads('null')
    import re
    m=re.search(r'```(\w*)', md)
    return m.group(1) if m else ''

# 组装序列
seq=[]
text_ti=0
for bi,b in enumerate(blocks):
    ty=b['type']
    if ty=='atomic':
        er=b.get('entityRanges',[])
        if er:
            e=em.get(str(er[0].get('key')))
            if e:
                if e['type']=='MARKDOWN':
                    seq.append(('CODE',bi,e['data'].get('markdown',''),None))
                elif e['type']=='MEDIA':
                    seq.append(('IMG',bi,fig_by_block.get(bi),None))
        continue
    zh=all_zh.get(str(text_ti), b['text'])
    text_ti+=1
    seq.append(('TEXT',bi,zh,ty))

# 按 header-one 分节（原文 h2 标题块）
SECTION_TITLES={13:"为什么需要批处理",24:"什么让 LLM 出问题",37:"静态批处理",54:"动态批处理",66:"连续批处理",77:"分块预填充（Chunked prefill）",100:"结语"}
h2_blocks=sorted(SECTION_TITLES.keys())
def get_section_title(bi):
    cur=0
    for hb in h2_blocks:
        if bi>=hb: cur=hb
        else: break
    return SECTION_TITLES.get(cur,"")

# 组织 sections：引言语块归"引言"，每 h2 后到下一个 h2 各自成节
raw_sections=[]
cur_title="引言：GPU 为何闲置"
cur_items=[]
for kind,bi,val,ty in seq:
    if kind=='TEXT' and bi in SECTION_TITLES:
        # 新节开始
        if cur_items: raw_sections.append((cur_title,cur_items))
        cur_title=SECTION_TITLES[bi]
        cur_items=[]
        continue
    cur_items.append((kind,bi,val))
if cur_items: raw_sections.append((cur_title,cur_items))

sections=[]
code_counter=0
for title,items in raw_sections:
    paras=[]
    fig_after={}
    para_idx=0
    for kind,bi,val in items:
        if kind=='TEXT':
            txt=val
            # 加粗关键句已在译文里（译文本身含**…**）
            paras.append(txt)
            para_idx+=1
        elif kind=='CODE':
            # 转 __CODE__lang::
            import re
            m=re.search(r'```(\w*)\s*\n(.*?)\n```', val, re.S)
            lang=m.group(1) if m else ''
            content=m.group(2) if m else val
            paras.append(f"__CODE__{lang}::{content}")
            para_idx+=1
        elif kind=='IMG':
            # 图挂到当前最后一段之后
            fig_name=val
            if fig_name:
                key=para_idx-1
                fig_after.setdefault(key,[]).append({"src":fig_name,"caption":""})
    sections.append({"type":"h2","title":title,"paras":paras,"fig_after":fig_after})

DATA={
"title":"⚖️ LLM 批处理三策略全解：静态 / 动态 / 连续（含分块预填充，全中文）",
"summary":[
 {"key":"核心问题","body":"GPU 生成单 token 被读权重卡住、算力空转；批处理把一次权重读取摊给多个序列。"},
 {"key":"三策略","body":"静态/动态/连续批处理区别在批次何时决定，连续批处理是现代高吞吐主力。"},
 {"key":"关键权衡","body":"分块预填充缓解长 prompt 卡顿；块大小在 decode 机会与 prompt 效率间取舍，需实测。"},
],
"lead":[
 "为什么高速 GPU 服务 LLM 时常闲着？因为生成单个 token 就要把全部权重从内存读一遍，**读取耗时主导、算力大部分在等待**。批处理弥合这一差距：权重只读一次、多个序列同一前向通过。",
 "这篇 X 平台博主 Akshay 的长文从第一性原理讲透静态、动态、连续三种批处理策略，各自解决什么问题、留什么缺陷，并落 vLLM / SGLang 真实配置。**本文全中文编译，正文原样照搬不压缩，图片全部保留。**",
],
"sections":sections,
"conclusion":[
 "三种批处理策略唯一区别是何时固定批次：静态适合定长输出、动态适合固定产出模型、连续批处理扛得住长度剧烈变化的实时流量，配以分块预填充可在吞吐与延迟间精细权衡。",
 "整篇地基是 GPU 事实——前向传播瓶颈在读内存而非算数。看清这一点，就明白为何批处理与 KV cache 是推理系统命脉。",
],
"reference_url":"https://x.com/akshay_pachaar/status/2094490705024676272",
}

# 输出 build 文件
out=[]
out.append("# -*- coding: utf-8 -*-")
out.append("import json, os, sys")
out.append("_article_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()")
out.append("DATA = "+json.dumps(DATA,ensure_ascii=False,indent=1))
out.append('out_path = os.path.join(_article_dir, "article_data.json")')
out.append('os.makedirs(_article_dir, exist_ok=True)')
out.append('with open(out_path, "w", encoding="utf-8") as f:')
out.append('    json.dump(DATA, f, ensure_ascii=False, indent=2)')
out.append("print(f'OK {len(DATA[\"sections\"])} sections')")
build=os.path.join(base,"article_data_build.py")
open(build,"w",encoding="utf-8").write("\n".join(out))
print("已生成 article_data_build.py")
# 统计
tot_para=sum(len(s["paras"]) for s in DATA["sections"])
tot_img=sum(len(v) for s in DATA["sections"] for v in s["fig_after"].values())
tot_code=sum(1 for s in DATA["sections"] for p in s["paras"] if p.startswith("__CODE__"))
print(f"段落数:{tot_para} 图:{tot_img} 代码:{tot_code} sections:{len(DATA['sections'])}")
