"""嵌入图片到 article.md 和 article_human.md"""
import re

ARTICLE_DIR = r"D:\06_Hermes\articles\chatgpt-memory-works"

# 图片嵌入映射：在原文中找到插入点，嵌入图片+说明
# 说明从原文DOM context提取，或使用简洁来源声明
insertions = [
    # img2: Profile 结构图 — 放在"细节让这个机制变得具体"段落之前
    ("细节让这个机制变得具体", 
     "![](img2_profile.png)\n<span style=\"font-size:12px;color:rgb(153,153,153);\">Rehberger 逆向工程发现的 ChatGPT Profile 六个段落结构</span>\n\n"),
    # img3: Dreaming 图 — 放在"预加载的Profile会腐烂"段落之前
    ("预加载的Profile会腐烂", 
     "![](img3_dreaming.png)\n<span style=\"font-size:12px;color:rgb(153,153,153);\">OpenAI Dreaming 系统架构示意</span>\n\n"),
    # img4: 安全研究截图 — 放在"还有安全层面"段落之前
    ("还有安全层面", 
     "![](img4_security.png)\n<span style=\"font-size:12px;color:rgb(153,153,153);\">Rehberger 展示 Google Doc 引用可写入攻击者控制的记忆条目</span>\n\n"),
    # img5: Willison 评论 — 放在"持久的教训是结构性的"段落之前
    ("持久的教训是结构性的", 
     "![](img5_willison.png)\n<span style=\"font-size:12px;color:rgb(153,153,153);\">Simon Willison 对 ChatGPT 持久 Profile 的隐私担忧</span>\n\n"),
    # img6: 边界/Mem0对比图 — 放在"它的边界在哪里"之后
    ("它是封闭的、单应用的", 
     "![](img6_boundary.png)\n<span style=\"font-size:12px;color:rgb(153,153,153);\">ChatGPT 记忆边界与 Mem0 可移植层的对比</span>\n\n"),
]

def embed_images(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    for anchor, img_block in insertions:
        # 只在每个锚点第一次出现时嵌入
        if anchor not in content:
            print(f"  [WARN] Anchor not found: '{anchor}'")
            continue
        
        marker = f"\n{img_block}"
        new_content = content.replace(anchor, marker + anchor, 1)
        if new_content != content:
            content = new_content
            print(f"  [OK] Embedded before '{anchor}'")
        else:
            print(f"  [FAIL] Could not embed before '{anchor}'")
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"\n[OK] Saved: {filepath}")

embed_images(f"{ARTICLE_DIR}\\article.md")
embed_images(f"{ARTICLE_DIR}\\article_human.md")
