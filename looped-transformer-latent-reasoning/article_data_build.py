# -*- coding: utf-8 -*-
"""从 full_translation.md 派生 article_data.json 的 DATA。"""
import re, os

HERE = "D:/06_Hermes/articles/looped-transformer-latent-reasoning"
ft = open(os.path.join(HERE, "full_translation.md"), encoding="utf-8").read()
blocks = [b.strip() for b in re.split(r"\n\s*\n", ft) if b.strip()]

def is_h2(b): return b.startswith("## ")
def is_h3(b): return b.startswith("### ")
def is_h4(b): return b.startswith("#### ")

# 解析：把 #### 折叠进最近的 ### 段内（作为带粗体小标题的段落），### 为 h3，## 为 h2
sections = []
cur = None          # 当前 section dict
cur_sub = None      # 当前 h3 subsection dict
lead = []

for b in blocks:
    if b.startswith("## 致谢"):
        break
    if is_h2(b):
        # 收尾上一个
        if cur_sub is not None:
            cur["paras"].extend(cur_sub["paras"])
            cur_sub = None
        if cur is not None:
            sections.append(cur)
        title = b[3:].strip()
        cur = {"type": "h2", "title": title, "paras": []}
    elif is_h3(b):
        if cur is None:
            cur = {"type": "h2", "title": "正文", "paras": []}
        # 先把正在累积的 h3 合并进父
        if cur_sub is not None:
            cur["paras"].extend(cur_sub["paras"])
        title = b[4:].strip()
        cur_sub = {"type": "h3", "title": title, "paras": []}
    elif is_h4(b):
        # 折叠进当前 h3（或 h2）作为带粗体引导的段落
        sub = b[5:].strip()
        target = cur_sub if cur_sub is not None else cur
        if target is not None:
            target["paras"].append("**" + sub + "**")
    else:
        target = cur_sub if cur_sub is not None else cur
        if target is not None:
            target["paras"].append(b)

# 收尾
if cur_sub is not None and cur is not None:
    cur["paras"].extend(cur_sub["paras"])
if cur is not None:
    sections.append(cur)

# lead：取 1 引言 的前两段（scaling + latent）作为引导
intro = next((s for s in sections if s["title"].startswith("1 ")), None)
if intro:
    lead = intro["paras"][:2]
    intro["paras"] = intro["paras"][2:]

# conclusion：取 6 结论 的正文
concl_sec = next((s for s in sections if s["title"].startswith("6 ")), None)
conclusion = []
if concl_sec:
    conclusion = concl_sec["paras"]
    sections = [s for s in sections if not s["title"].startswith("6 ")]

# 独立观点（结语卡片补充）
conclusion.append("**独立观点**：LOTUS 的意义不只在「快」，而在于它把隐式推理从黑箱变成了可读的对象。它用最朴素的交叉熵、最朴素的循环复用，就追平了显式 CoT，而且隐状态里能读出模型从未被训练过的有效推理路径。这暗示一个大方向：很多「必须显式生成」的中间过程，其实可以在隐藏状态里并行完成，只要监督信号足够直接。")

summary = [
    {"key": "追上显式CoT", "body": "在 Llama-3.2-3B-Instruct 上，LOTUS 把 GSM8K 域内差距缩到 1.5 分以内，域外平均反超显式 CoT，是首个在 3B 规模弥合隐式-显式差距的方法。"},
    {"key": "思考快 2.5–6.9 倍", "body": "把 N 步顺序生成的 CoT 压缩为 R≪N 次并行循环迭代：数学设定思维快 2.5 倍，自然语言 CoT 压力测试快 6.9 倍。"},
    {"key": "循环填充式骨干", "body": "在问题-答案间插入 K 个可学习隐式块，复用同一套权重循环 R 次，不增参数即获得计算深度。"},
    {"key": "并行CoT监督", "body": "直接经基础 LM 头用交叉熵把每个隐式位置对齐到金标准 CoT token，简单且跨规模稳健；辅助解码器路由在 3B 上与之持平。"},
    {"key": "隐空间可读", "body": "循环后隐状态可直接读出金标准推理步骤，还能浮现未见但有效的备选中间路径，证明隐状态真正与 CoT 对齐。"},
]

DATA = {
    "title": "用循环 Transformer 弥合隐式与显式推理的鸿沟：LOTUS 让「不说话的思考」追上思维链",
    "summary": summary,
    "lead": lead,
    "sections": sections,
    "conclusion": conclusion,
    "reference_url": "https://arxiv.org/html/2606.31779v2",
    # 图注保留英文原文（用户铁律：默认不翻译），故 caption_translations 留空
    "caption_translations": {},
}
