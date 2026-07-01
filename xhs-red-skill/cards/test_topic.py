"""Try posting with #topic in body text directly - that's how XHS native works."""
import json
import sys
import os
sys.path.insert(0, "D:/ProgramData/miniconda3/Lib/site-packages")

from xhs_cli.client import XhsClient
from xhs_cli.cookies import load_saved_cookies

CARDS_DIR = "D:/06_Hermes/articles/xhs-red-skill/cards/output"

def main():
    cookies = load_saved_cookies()
    if not cookies:
        print("No cookies")
        return
    
    client = XhsClient(cookies)
    
    # Upload just 1 image for a quick test
    path = os.path.join(CARDS_DIR, "xhs-01.png")
    print(f"Uploading image...")
    permit = client.get_upload_permit()
    client.upload_file(permit["fileId"], permit["token"], path)
    file_ids = [permit["fileId"]]
    print(f"Uploaded: {permit['fileId']}")
    
    # Post with #topic in body text - this is how XHS native works
    title = "测试话题标签"
    desc = "这是一条测试笔记，看看话题标签是否生效。\n\n#REDSkill #VibeCoding #AI工具"
    
    result = client.create_image_note(
        title=title,
        desc=desc,
        image_file_ids=file_ids,
        topics=[],  # No API topics, just body text
        is_private=True,  # Private so it doesn't clutter
    )
    
    print(f"\nResult: {json.dumps(result, indent=2, ensure_ascii=False)}")

if __name__ == "__main__":
    main()
