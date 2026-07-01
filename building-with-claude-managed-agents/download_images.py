import urllib.request, urllib.error, os, sys

urls = [
    ("https://cdn.prod.website-files.com/68a44d4040f98a4adf2207b6/6a298c28f950480f89a8dfcf_01%20_%20Messages%20API.png", "img1_messages_api.png"),
    ("https://cdn.prod.website-files.com/68a44d4040f98a4adf2207b6/6a298c53aaeeee508f2b3166_02%20_%20Claude%20Agent%20SDK.png", "img2_agent_sdk.png"),
    ("https://cdn.prod.website-files.com/68a44d4040f98a4adf2207b6/6a298c97d4a887f2666a50b6_03%20_%20Claude%20Managed%20Agents.png", "img3_managed_agents.png"),
    ("https://cdn.prod.website-files.com/68a44d4040f98a4adf2207b6/6a29a18bb07e245f8389acb9_04%20_%20Agents_%20environments_%20sessions%20(2).png", "img4_agents_env_sessions.png"),
    ("https://cdn.prod.website-files.com/68a44d4040f98a4adf2207b6/6a29a19cebb4eb7adac0a8ec_05%20_%20Managed%20Agents%20runtime%20(1).png", "img5_runtime.png"),
    ("https://cdn.prod.website-files.com/68a44d4040f98a4adf2207b6/6a298e427c7a804ea4295163_image7.png", "img6_observability.png"),
    ("https://cdn.prod.website-files.com/68a44d4040f98a4adf2207b6/6a298e9b866a4402a3c9bb5d_image5.png", "img7_quickstart.png"),
    ("https://cdn.prod.website-files.com/68a44d4040f98a4adf2207b6/6a298ebdff6d26839e052c63_image9.png", "img8_console_live.png"),
    ("https://cdn.prod.website-files.com/68a44d4040f98a4adf2207b6/6a298ef3765ce453971174cd_image6.png", "img9_claude_api_skill.png"),
]

os.chdir("D:/06_Hermes/articles/building-with-claude-managed-agents")
success = 0
for url, fname in urls:
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
            with open(fname, 'wb') as f:
                f.write(data)
        print(f"OK  {fname} ({len(data)} bytes)")
        success += 1
    except Exception as e:
        print(f"ERR {fname}: {e}")
print(f"\nDownloaded {success}/{len(urls)} images")
