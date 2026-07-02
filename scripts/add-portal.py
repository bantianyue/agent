#!/usr/bin/env python3
"""
为公众号文章生成传送门 HTML 区块，插入到 article_human.md 的结语与参考区之间。

用法：
    python scripts/add-portal.py <article_dir> [--dry-run]

选择规则：
    - 4 篇与原文主题相关
    - 4 篇多样性（无关）
    - 从 published_articles.json 读取，只读不写
    - 排除当前文章自身

传送门格式：
    - 字体 14px
    - 链接间用 <br> 无空行
    - 前后各有 --- 分割线
    - 标题【传送门】
"""

import json, os, re, sys

ARTICLES_BASE = r"D:\06_Hermes\articles"
PUBLISHED_FILE = os.path.join(ARTICLES_BASE, "published_articles.json")

# 主题相关关键词（按大类分组）
TOPIC_KEYWORDS = {
    "kv-cache-推理优化": ["Cache", "KV Cache", "kv cache", "Serving", "推理", "Decode", "Prefill", 
                      "SGLang", "vLLM", "量化", "memory", "GPU", "HBM", "Attention", "加速", "TPS", "吞吐"],
    "agent-工具链": ["Agent", "Harness", "Tool", "Skill", "Loop", "编排", "协同", "子任务",
                   "subagent", "managed"],
    "模型-训练": ["训练", "并行", "Distributed", "MoE", "RL", "强化学习", "FP4", "量化"],
    "编程-代码": ["Code", "代码", "编程", "Prompt", "Coding", "Copilot", "重构"],
    "安全-架构": ["安全", "架构", "基础设施", "infra", "Serverless"],
}

def get_article_title_from_dir(article_dir: str) -> str:
    """从 article_human.md 或 article.md 的标题标签中提取文章标题。"""
    for fname in ["article_human.md", "article.md"]:
        path = os.path.join(article_dir, fname)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            # 找要点速览中的关键词或结语前内容
            m = re.search(r'<strong[^>]*>要点速览</strong>', content)
            # 标题不在 markdown 中，退回用 draft.id 或目录名
            break
    return os.path.basename(article_dir)


def load_published() -> list[dict]:
    """只读加载 published_articles.json。"""
    if not os.path.exists(PUBLISHED_FILE):
        print(f"⚠️  未找到 {PUBLISHED_FILE}")
        return []
    with open(PUBLISHED_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def score_relevance(title: str, keywords: list[str]) -> int:
    """计算文章标题与关键词的相关性分数。"""
    t_lower = title.lower()
    score = 0
    for kw in keywords:
        if kw.lower() in t_lower:
            score += 1
    return score


def pick_articles(current_title: str, published: list[dict], n_related: int = 4, n_diverse: int = 4) -> list[dict]:
    """
    选 8 篇文章：4 篇相关 + 4 篇多样性。
    相关按所有关键词组的最高分排序，多样性按最低分排序（不相关）。
    """
    exclude_titles = [current_title, current_title.replace("：", ":"),
                      current_title.replace(":", "："),
                      "VeriCache"]
    
    # 合并所有关键词
    all_keywords = []
    for group_kws in TOPIC_KEYWORDS.values():
        all_keywords.extend(group_kws)
    all_keywords = list(set(all_keywords))
    
    # 计算每篇文章的分数
    scored = []
    for a in published:
        title = a.get("title", "")
        # 排除当前文章
        if any(e in title for e in exclude_titles):
            continue
        score = score_relevance(title, all_keywords)
        scored.append((score, a))
    
    # 按分数排序
    scored.sort(key=lambda x: -x[0])
    
    related = [a for s, a in scored if s >= 2][:n_related]
    diverse = [a for s, a in scored if s < 1][:n_diverse]
    
    # 如果相关不够，从多样性中补
    if len(related) < n_related:
        needed = n_related - len(related)
        diverse_candidates = [a for s, a in scored if s < 2 and a not in related]
        related.extend(diverse_candidates[:needed])
        diverse = [a for a in diverse if a not in related]
    
    # 如果多样不够，从相关中补（去掉高分项）
    if len(diverse) < n_diverse:
        needed = n_diverse - len(diverse)
        for a in reversed(related):
            if len(diverse) >= n_diverse:
                break
            diverse.append(a)
            related.remove(a)
    
    return related + diverse


def generate_portal_html(articles: list[dict]) -> str:
    """生成传送门 HTML 区块（含分割线）。"""
    lines = []
    lines.append("---")
    lines.append("")
    lines.append('<span style="font-size:14px;color:#888888;font-family:\'Courier New\',monospace;">【传送门】<br>')
    
    for i, a in enumerate(articles):
        url = a.get("url", "")
        title = a.get("title", "")
        tag = f'<a class="normal_text_link mp_article_text_link" href="{url}" target="_blank" data-linktype="2">{title}</a><br>'
        lines.append(tag)
    
    lines.append("</span>")
    lines.append("")
    lines.append("---")
    
    return "\n".join(lines)


def inject_portal(article_dir: str, portal_html: str, dry_run: bool = False) -> bool:
    """将传送门插入到结语卡片之后、参考区之前。"""
    fname = "article_human.md" if os.path.exists(os.path.join(article_dir, "article_human.md")) else "article.md"
    path = os.path.join(article_dir, fname)
    
    if not os.path.exists(path):
        print(f"❌ 未找到 {path}")
        return False
    
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 找结语卡片的结束
    jieyu_end = '</div>\n\n'
    pos = content.find(jieyu_end, content.find('结语'))
    if pos == -1:
        print("❌ 找不到结语卡片结束位置")
        return False
    
    # 找参考区开始（在传送门之后）
    ref_start = content.find('<span', content.find('参考：'))
    if ref_start == -1:
        print("❌ 找不到参考区")
        return False
    
    # 替换结语与参考区之间的内容为传送门
    new_content = content[:pos + len(jieyu_end)] + portal_html + "\n\n" + content[ref_start:]
    
    if dry_run:
        print("🔍 DRY RUN - 修改预览:")
        print(f"   文件: {path}")
        print(f"   结语后插入传送门 ({len([a for a in portal_html.split('<a ') if 'href' in a])} 篇)")
        print(f"   原文件大小: {len(content)} -> 新文件大小: {len(new_content)}")
        return True
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)
    
    print(f"✅ 已写入 {len(articles)} 篇传送门到 {path}")
    return True


def main():
    if len(sys.argv) < 2:
        print("用法: python scripts/add-portal.py <article_dir> [--dry-run]")
        sys.exit(1)
    
    article_dir = sys.argv[1].rstrip("/\\")
    dry_run = "--dry-run" in sys.argv
    
    if not os.path.isdir(article_dir):
        print(f"❌ 目录不存在: {article_dir}")
        sys.exit(1)
    
    published = load_published()
    if not published:
        sys.exit(1)
    
    current_title = os.path.basename(article_dir)
    picks = pick_articles(current_title, published, n_related=4, n_diverse=4)
    
    print(f"📚 已选 {len(picks)} 篇文章:")
    for i, a in enumerate(picks):
        label = "相关" if i < 4 else "多样"
        # 用相关关键词打分
        all_kw = []
        for g in TOPIC_KEYWORDS.values():
            all_kw.extend(g)
        score = score_relevance(a["title"], all_kw)
        print(f"  [{label}] (得分{score}) {a['title'][:50]} -> {a['url']}")
    
    portal_html = generate_portal_html(picks)
    
    print(f"\n📝 生成的传送门 HTML ({len(picks)} 篇):")
    print(portal_html[:300] + "...")
    
    success = inject_portal(article_dir, portal_html, dry_run=dry_run)
    
    if success and not dry_run:
        print("\n💡 推送前运行: cd <dir> && npx -y bun <wechat-api> ... --draft-media-id \"$(cat draft.id)\"")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
