"""Search for REDSkill notes and check topic structure."""
import json
import sys
sys.path.insert(0, "D:/ProgramData/miniconda3/Lib/site-packages")

from xhs_cli.client import XhsClient
from xhs_cli.cookies import load_saved_cookies

def main():
    cookies = load_saved_cookies()
    if not cookies:
        print("No cookies")
        return
    
    client = XhsClient(cookies)
    
    # Search for notes with REDSkill topic
    try:
        search = client._main_api_post("/api/sns/web/v1/search/notes", {
            "keyword": "REDSkill",
            "page": 1,
            "page_size": 6,
            "sort": "general",
            "note_type": 0,
            "ext_flags": [],
            "image_formats": ["jpg", "webp", "avif"],
        })
        print("Search result keys:", list(search.keys()))
        
        items = search.get("data", {}).get("items", [])
        print(f"Found {len(items)} items")
        
        if items:
            for i, item in enumerate(items[:3]):
                note_card = item.get("note_card", {})
                tags = note_card.get("tag_list", [])
                display_title = note_card.get("display_title", "")
                print(f"\n=== Note {i+1}: {display_title[:60] if display_title else 'no title'} ===")
                print(f"Tags count: {len(tags)}")
                for t in tags:
                    print(f"  - {json.dumps(t, ensure_ascii=False)}")
        else:
            print("Raw response (first 3000 chars):")
            print(json.dumps(search, indent=2, ensure_ascii=False)[:3000])
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
