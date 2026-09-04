# -*- coding: utf-8 -*-
"""PyTorch 2.14 release — 写 article_data.json"""
import json, os, re, sys
base=r"D:/06_Hermes/articles/pytorch-2-14-release"
_S=json.load(open(base+"/_S.json",encoding="utf-8"))
S=_S['S']; intro=_S['intro']
# 丢弃尾两chapter
DROP={'非功能更新','保持联系，获取更新、活动信息及最新动态'}
S=[x for x in S if x['title'] not in DROP]
# 内部 **标题** 清理 markdown中可能有**，但保持

# 去掉每个 feature paras 中孤立的 # tag
def clean(p):
    p=re.sub(r'\s+',' ', p).strip()
    return p
S=[{'type':'h2','title':x['title'].strip(),'paras':[clean(p) for p in x['paras']]} for x in S]

# summary 3条 (来自 highlights)
DATA={
 "title":"PyTorch 2.14 发布：NVGEMM GPU 内核后端、nccl2 分布式、容错集合通信与更广平台支持",
 "summary":[
   {"key":"编译/GPU","body":"NVGEMM 把 CuTeDSL 生成的 CUTLASS 内核带进 Inductor，支持 NVFP4 与分组归约 epilogue，自动调优；默认重叠通信与计算。"},
   {"key":"分布式","body":"新增 nccl2 后端；容错成为 c10d 一等概念——原地重组、单边 RMA 窗口、任意后端的飞行记录器。"},
   {"key":"核心特性","body":"torch.switch/while_loop CUDA 图捕获、SDPA Rank-3、复数 tensor compile、@dynamic_spec 声明动态形状、Apple 原生线性代数。"},
 ],
 "lead":[],
 "sections":S,
 "conclusion":[],
 "reference_url":"https://pytorch.org/blog/pytorch-2-14-release-blog/",
}
# lead = intro 主体选 P (公告) , 高亮bullets不重复summary
# intro_buf 全部含 P 与 highlight(LI带·)。分开
leadp=[p for p in intro if not p.startswith('· ')]
leadp=[clean(p) for p in leadp]
DATA['lead']=leadp
# conclusion 添加一小段收尾(已含 PyTorch conference/CTA)——用补充 summary后请用户看,不用太长
DATA['conclusion']=[
  "自 2.13 起，本版本由 487 位贡献者 2,995 个 commit 构成；PyTorch 正从研究优先演化为统一、硬件无关的大规模生产训练与推理平台。值得升级试用的新特性集中在 NVGEMM 编译后端、nccl2/容错分布式与声明式动态形状。"
]
# 存 (中间,用于校验) - 将直接写
json.dump(DATA,open(base+"/article_data.json","w",encoding="utf-8"),ensure_ascii=False,indent=2)
np=sum(len(x['paras']) for x in S)
print("title size:",len(DATA['title']))
print("paras总数:",np)
# cover
