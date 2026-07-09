#!/usr/bin/env python3
"""Download all images from CDP extraction."""
import urllib.request, os

urls = [
    ('img1.jpg', "https://pbs.twimg.com/media/HMoW1q4bAAEYDxz?format=jpg&name=900x900"),
    ('img2.jpg', "https://pbs.twimg.com/media/HMoNtE6bwAAeylL?format=jpg&name=900x900"),
    ('img3.jpg', "https://pbs.twimg.com/amplify_video_thumb/2074496658168336385/img/zb18NrpzK6NNbzhU?format=jpg&name=900x900"),
    ('img4.jpg', "https://pbs.twimg.com/media/HMoPbxxbAAAh-CX?format=jpg&name=900x900"),
    ('img5.jpg', "https://pbs.twimg.com/media/HMoPsZ6agAAMKAt?format=jpg&name=900x900"),
    ('img6.jpg', "https://pbs.twimg.com/media/HMoTIbOa8AEhg6m?format=jpg&name=900x900"),
    ('img7.jpg', "https://pbs.twimg.com/media/HMoUYhSbUAAvbo5?format=jpg&name=900x900"),
    ('img8.jpg', "https://pbs.twimg.com/media/HMoU8p6boAAaCr3?format=jpg&name=900x900"),
    ('img9.jpg', "https://pbs.twimg.com/media/HMoVOZLaYAA75yr?format=jpg&name=900x900"),
    ('img10.jpg', "https://pbs.twimg.com/media/HMoVwfubgAAAZbg?format=jpg&name=900x900"),
]

for fname, url in urls:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            data = r.read()
            # Detect actual format from content-type
            ct = r.headers.get("Content-Type", "")
            if "png" in ct: fname = fname.replace(".jpg", ".png")
            with open(fname, "wb") as f:
                f.write(data)
            print(f"  OK {fname} ({len(data)//1024}KB)")
    except Exception as e:
        print(f"  FAIL {fname}: {e}")
