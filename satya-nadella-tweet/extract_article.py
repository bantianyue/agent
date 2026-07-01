import asyncio, json

async def main():
    from playwright.async_api import async_playwright
    
    async with async_playwright() as p:
        # Use the user's actual Chrome profile (Profile 1) which has X login
        profile_path = "C:/Users/twfehh7/AppData/Local/Google/Chrome/User Data/Profile 1"
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=profile_path,
            channel='chrome',
            headless=False,  # non-headless to preserve login state
            no_viewport=True,
        )
        page = await browser.new_page()
        
        try:
            await page.goto('https://x.com/satyanadella/status/2066182223213293753', 
                            wait_until='domcontentloaded', timeout=30000)
            await asyncio.sleep(10)
            
            print(f'URL: {page.url}')
            
            full_text = await page.evaluate('document.body.innerText')
            print(f'\n=== FULL TEXT (length: {len(full_text)}) ===')
            print(full_text[:15000])
            
        except Exception as e:
            print(f'Error: {e}')
            try:
                text = await page.evaluate('document.body.innerText')
                print(f'Partial text: {text[:3000]}')
            except:
                pass
        
        await browser.close()

asyncio.run(main())
