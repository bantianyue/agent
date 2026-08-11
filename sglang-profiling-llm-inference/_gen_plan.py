#!/usr/bin/env python3
"""sglang 重建 FINAL：严格按 _tweet.json 原文 block 流生成 DATA，图文100%与原文一致。
逻辑: 遍历原文 blocks 顺序,
  - 文本块 → 按序取译文(译文=text-only原文块顺序，译文key即 _extract_blocks 序但需剔除)
  - 图锚点块(entityRanges→MEDIA) → 插入对应 figNN + 中文图注
  - markdown 块 → 代码块(保留原文)
  - 顶层 h2: 由"短标题文本块"识别
关键: 译文 key 与原文 text-only 块按顺序对齐(译文翻译自 _extract_blocks 即同序文本块)。
"""
import json, os, re

base = r"D:/06_Hermes/articles/sglang-profiling-llm-inference"
t = json.load(open(base+"/_tweet.json", encoding="utf-8"))
a = t['tweet']['article']
blocks = a['content']['blocks']
em = a['content'].get('entityMap', [])
emap = {}
for e in em: emap[str(e.get('key'))] = e['value']

# 图锚点 original 顺序: block# -> (localId, caption_en)
img_anchors = []
for i,b in enumerate(blocks):
    for er in b.get('entityRanges',[]):
        ent = emap.get(str(er.get('key')))
        if ent and ent.get('type')=='MEDIA':
            local = ent['data'].get('mediaItems',[{}])[0].get('localMediaId')
            cap = ent['data'].get('caption','').strip()
            img_anchors.append((i, str(local), cap))
img_anchors.sort()
print("图锚点:", [(x[0],x[1]) for x in img_anchors])

# figNN 文件名 按 block 顺序: 第k个anchors→ fig{k+1:02d}
n = len(img_anchors)
order_local = [x[1] for x in img_anchors]
print("localId 顺序:", order_local)

# 图注中文: 从译文里按原文 caption 匹配(译文含图注翻译, 但以'同序'匹配不可靠, 改用内容匹配原文caption)
trans = json.load(open(base+"/_translations.json", encoding="utf-8"))
# 已知译文里图注(中文) 按我们读过的内容手工映射 localId->中文caption
zh_cap = {
 '24':'图 1：单个请求的 Prefill 区域。',
 '26':'图 2：调度器准备请求、启动剖析、设置流并构建批次。',
 '28':'图 3：一个小的异步复制，关联回 CPU 端的启动。',
 '30':'图 4：主机到设备的复制量很小，可能是 token id 或请求元数据。',
 '32':'图 5：主 prefill 计算区域，峰值以重复组形式出现。',
 '34':'图 6：第一个峰值稍大，因为它包含额外的初始化和索引/复制工作。',
 '36':'图 7：接下来的峰值与 GDN 块及较小的全注意力块对应。',
 '38':'图 8：prefill 侧内核。',
 '40':'图 9：层堆叠之后，SGLang 准备解码并为采样计算 logits。',
 '42':'图 10：词表投影内核的详细信息。',
 '56':'图 11：',
 '44':'图 12：Decode 区域。由于分析了两个步骤，有两次 decode 阶段。',
 '46':'图 13：高亮区域是需要重点关注的解码计算路径。',
 '48':'图 14：第一个解码步骤，聚焦 CPU 端执行。',
 '50':'图 15：在 graph replay 之前会运行一些设置内核。',
 '52':'图 16：点击图形回放会显示捕获的 CUDA 图中启动的内核。',
 '54':'图 17：重复出现的蓝色条柱是 GEMV 系列内核。',
}

# 判断 h2 标题块(短文本且非列表项非图/代码) —— 用已知标题集合
H2_TITLES = {"Understanding the Model First","Setup","Prefill Section",
 "Pattern 1 - The Repeating Peaks","The Final Vocab Projection",
 "Top Prefill Kernels","Decode Phase","Decode Is Dominated by Skinny GEMV",
 "Where to go from here?"}
H2_ZH = {"Understanding the Model First":"先理解模型","Setup":"设置",
 "Prefill Section":"Prefill 部分","Pattern 1 - The Repeating Peaks":"模式 1：重复的峰值",
 "The Final Vocab Projection":"最终词表投影","Top Prefill Kernels":"主要预填充内核",
 "Decode Phase":"解码阶段","Decode Is Dominated by Skinny GEMV":"Decode 阶段由瘦 GEMV 主导",
 "Where to go from here?":"接下来该怎么做？"}

# 构建 原文 text-only 顺序 → 需要翻译的块
# 译文 key = _extract_blocks 顺序 (含图注误extract). 但我们只取"真正的正文文本块"按序.
# 为避免混乱, 直接用映射: 每个原文非空文本块 在译文里找(按原文文本中文→译文, 用包含匹配)
def zh_for(eng):
    # 在译文里找: eng 中文在译文? 我们已知译文是翻译, 无法反查.
    # 方案: 翻译按顺序存。用法: 顺序对齐 text-only 原文块 与 译文key(去掉图注和代码)
    return ''

# 更稳: 译文 key 顺序 = 原文"可译文本块"顺序. 可译文本块 = 非空、非图锚、非markdown、非纯结构行(如[kernel名]保留原文).
# 需要核对译文是否有代码/内核名保留英文——[47-56]内核名未翻, [19][21]代码未翻. 说明译文的顺序是 _extract_blocks 顺序.
# 结论: 直接复用 _extract_blocks 顺序 = 译文key顺序, 但它含图注. 
# 可靠做法: 遍历原文blocks, 维护"可译文本序号", 译文的 key 按 _extract_blocks 的 type=='text' 对应.

# ---- 用 _extract_blocks 的序号映射 ----
# _extract_blocks 与原文blocks 不同序(图注混入). 
# 稳妥: 手写 build 用已知译文段落(我已全部读到),不依赖自动。--已决定手写--
print("需要手写build; 图锚点顺序与中文caption已就绪")
json.dump({"img_anchors":img_anchors,"zh_cap":zh_cap}, open(base+"/_gen_plan.json","w"), ensure_ascii=False, indent=1)
print("已写 _gen_plan.json 供手写build使用")
