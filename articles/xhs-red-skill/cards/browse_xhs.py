"""Browse xiaohongshu to find a note with topics and see the HTML structure."""
import asyncio
import json
import websockets

# Use the main xiaohongshu tab
PAGE_WS = "ws://localhost:9222/devtools/page/E023609022A636D83F2C1D5F62EA2C82"

async def browse():
    async with websockets.connect(PAGE_WS, max_size=10*1024*1024) as ws:
        await ws.send(json.dumps({"id": 1, "method": "Page.enable"}))
        await ws.recv()
        
        # Go to explore page
        await ws.send(json.dumps({
            "id": 2, "method": "Page.navigate",
            "params": {"url": "https://www.xiaohongshu.com/explore"}
        }))
        await asyncio.sleep(6)
        
        # Get current URL
        await ws.send(json.dumps({"id": 3, "method": "Runtime.evaluate", "params": {"expression": "window.location.href", "returnByValue": True}}))
        resp = json.loads(await ws.recv())
        url = resp.get("result",{}).get("result",{}).get("value","")
        print(f"URL: {url}")
        
        # Search for REDSkill
        await ws.send(json.dumps({"id": 4, "method": "Runtime.evaluate", "params": {"expression": """
            (() => {
                const input = document.querySelector('input[placeholder*=\"搜索\"], input[type=\"search\"]');
                if (input) {
                    const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                    nativeInputValueSetter.call(input, 'REDSkill');
                    input.dispatchEvent(new Event('input', { bubbles: true }));
                    // Find and click search button
                    const btn = document.querySelector('input[placeholder*=\"搜索\"] + button, button[class*=\"search\"]');
                    if (btn) btn.click();
                    return 'searched';
                }
                return 'no input found';
            })()
        """, "returnByValue": True}}))
        resp = json.loads(await ws.recv())
        print(f"Search: {resp.get('result',{}).get('result',{}).get('value','')}")
        await asyncio.sleep(5)
        
        # Get page text to see if we have results
        await ws.send(json.dumps({"id": 5, "method": "Runtime.evaluate", "params": {"expression": "document.body.innerText.substring(0, 3000)", "returnByValue": True}}))
        resp = json.loads(await ws.recv())
        text = resp.get("result",{}).get("result",{}).get("value","")
        print(f"\nPage text (first 3000):\n{text}")

asyncio.run(browse())
