#!/usr/bin/env python3
"""
article_data_build.py 模板
=====================
写新文章时：cp 到文章目录下，填入 DATA 字典内容，然后：
    python write-article-data.py <文章目录>
    python render-article.py <文章目录>
    python add-portal.py <文章目录>

字段说明：
  - summary: 要点速览，列表格式 [{key, body}]。每条 key 是一两个词的标题，body 是一条结论（≤50字）。
            ⚠️ 必须为 [{key, body}] 列表，不能是字符串！template.html 用 {% for item in summary %} 遍历。
  - lead: 导语段落列表，每段用 **加粗** 标核心句
  - sections: 正文章节。type 为 'h2'（大标题）或 'h3'（子标题）。
              figs 可选，每个 {src: 文件名, caption: 图注文字}
  - conclusion: 结语段落列表
  - reference_url: 原文出处 URL
"""

import json, os, sys

# 获取文章目录（兼容 write-article-data.py 的 exec 调用）
_article_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()

DATA = {
    # ⚠️ 要点速览：必须为 [{key, body}] 列表，不可为字符串。**必须恰好 3 条**（write-article-data.py 三重校验要求 len(summary) == 3）
    "summary": [
        {"key": "核心观点", "body": "一句话说清论文/文章最关键的结论"},
        {"key": "关键数据", "body": "支撑核心结论的具体数字或对比"},
        {"key": "方法创新", "body": "区别于已有工作的核心创新点"},
    ],

    "lead": [
        "引导段第一句。介绍背景和问题定位。",
        "引导段第二句。点明本文核心内容。",
    ],

    "sections": [
        {
            "type": "h2",
            "title": "第一节标题",
            "paras": [
                "段落一正文。**加粗** 标核心结论。",
                "段落二正文。",
            ],
            # 可选：图嵌入。src 是文件名（相对文章目录），caption 是图注
            "figs": [
                {"src": "fig01.png", "caption": "图 1：说明文字"},
            ],
        },
        {
            "type": "h3",
            "title": "子节标题",
            "paras": [
                "子节段落。",
            ],
        },
        {
            "type": "h2",
            "title": "第二节标题",
            "paras": [
                "段落正文。",
            ],
        },
    ],

    "conclusion": [
        "结语第一段。总结核心结论。",
        "结语第二段。行业影响或展望。",
    ],

    "reference_url": "https://arxiv.org/html/XXXX.XXXXXv1",
    # ⚠️ 必须设置！push-draft.py 从此字段读取公众号标题
    "title": "公众号文章标题",
}

# ── 写入 article_data.json ──
out_path = os.path.join(_article_dir, "article_data.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)
print(f"✅ 写入 {out_path} ({len(json.dumps(DATA, ensure_ascii=False))} chars, {len(DATA.get('sections', []))} sections)")
