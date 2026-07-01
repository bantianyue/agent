import asyncio
import json
import websockets
import os

PAGE_WS = "ws://localhost:9222/devtools/page/E023609022A636D83F2C1D5F62EA2C82"

async def get_cookies():
    async with websockets.connect(PAGE_WS, max_size=1024*1024) as ws:
        await ws.send(json.dumps({"id": 1, "method": "Network.enable"}))
        await ws.recv()
        
        await ws.send(json.dumps({
            "id": 2, "method": "Network.getCookies",
            "params": {"urls": ["https://www.xiaohongshu.com"]}
        }))
        resp = json.loads(await ws.recv())
        cookies = resp["result"]["cookies"]
        
        result = {}
        for c in cookies:
            if c["name"] in ["web_session", "id_token", "a1"]:
                result[c["name"]] = c["value"]
        
        print(json.dumps(result, indent=2))
        
        # Also save to cookies file
        if "web_session" in result and "id_token" in result:
            cookie_data = {
                "a1": result.get("a1", "dummy"),
                "web_session": result["web_session"],
                "id_token": result["id_token"],
                "saved_at": int(asyncio.get_event_loop().time())
            }
            cookie_dir = os.path.expanduser("~/.xiaohongshu-cli")
            os.makedirs(cookie_dir, exist_ok=True)
            with open(os.path.join(cookie_dir, "cookies.json"), "w") as f:
                json.dump(cookie_data, f, indent=2)
            print("\nCookies saved to ~/.xiaohongshu-cli/cookies.json")

asyncio.run(get_cookies())
