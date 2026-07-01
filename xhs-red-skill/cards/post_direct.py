"""Post with proper topic attachment using xhs-cli internals."""
import json
import os
import sys

# Add xhs_cli to path
sys.path.insert(0, "D:/ProgramData/miniconda3/Lib/site-packages")

from xhs_cli.client import XhsClient
from xhs_cli.cookies import load_saved_cookies
from xhs_cli.command_normalizers import select_topic_payload

CARDS_DIR = "D:/06_Hermes/articles/xhs-red-skill/cards/output"

def main():
    # Load cookies
    cookies = load_saved_cookies()
    if not cookies:
        print("No cookies found")
        return
    
    client = XhsClient(cookies)
    
    # Upload images
    image_files = sorted([f for f in os.listdir(CARDS_DIR) if f.endswith(".png")])
    file_ids = []
    for fname in image_files:
        path = os.path.join(CARDS_DIR, fname)
        print(f"Uploading {fname}...")
        permit = client.get_upload_permit()
        client.upload_file(permit["fileId"], permit["token"], path)
        file_ids.append(permit["fileId"])
        print(f"  -> file_id: {permit['fileId']}")
    
    # Search topics
    topic_names = ["REDSkill", "VibeCoding", "AI工具", "小红书", "效率工具"]
    topics = []
    for name in topic_names:
        try:
            topic_data = client.search_topics(name)
            found = select_topic_payload(topic_data, name)
            if found:
                topics.append(found[0])
                print(f"Topic '{name}' -> id={found[0]['id']}")
            else:
                print(f"Topic '{name}' not found")
        except Exception as e:
            print(f"Topic '{name}' error: {e}")
    
    print(f"\nTopics to attach: {json.dumps(topics, indent=2)}")
    
    # Create note
    title = "为什么你天天刷小红书，其实是在逛 GitHub？🔥"
    desc = """刷了 3 年小红书，今天才发现我一直在逛一个「粉色 GitHub」。

最近小红书内测了一个叫 RED Skill 的东西——笔记里直接挂 Skill，看到就能一键复制安装。不用 clone，不用敲命令行，不用 star。

归藏的 PPT Skill，在小红书里已经有 3000 多人用过了。

还有 AI 渣男识别器、小红书自动发布工具、Vibe Coding 入门教程……全挂在笔记下面。

GitHub 上那些几万 star 的项目，也开始往小红书搬了。

小红书把「发现工具」这件事的门槛降到了零。你不需要会 git，不需要懂命令行，不需要知道什么是 README。

看到 → 复制 → 用。

更离谱的是，小红书还在办黑客松。一个种草社区在办黑客松。

2026 年的 Vibe Coding 浪潮，加上 RED Skill 这个基础设施，小红书正在从一个「逛吃逛吃」的社区，长成一个「逛着逛着就写了个 App」的创作平台。

如果你还在 GitHub 上苦哈哈地翻 README，不妨来小红书搜搜。说不定你想要的工具，已经在某条笔记下面躺好了。"""
    
    result = client.create_image_note(
        title=title,
        desc=desc,
        image_file_ids=file_ids,
        topics=topics,
        is_private=False,
    )
    
    print(f"\nResult: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    if isinstance(result, dict):
        note_id = result.get("data", {}).get("id", "unknown")
        print(f"\n✅ Published! Note ID: {note_id}")

if __name__ == "__main__":
    main()
