#!/usr/bin/env python3
"""Download all images from CDP extraction."""
import urllib.request, os

urls = [
    ('img1.jpg', "https://cdn.prod.website-files.com/68a44d4040f98a4adf2207b6/6903d22651dd05046d0fdb0b_39c40393e610cc0a5e65f50ad12ff5ada273f792-1000x1000.svg"),
    ('img2.jpg', "https://cdn.prod.website-files.com/6889473510b50328dbb70ae6/6889473610b50328dbb70b58_placeholder.svg"),
    ('img3.jpg', "https://cdn.prod.website-files.com/68a44d4040f98a4adf2207b6/6a4d058625e4fe8fe674684f_1a1b01b4.png"),
    ('img4.jpg', "https://cdn.prod.website-files.com/68a44d4040f98a4adf2207b6/6a4d058625e4fe8fe674684c_32d50939.png"),
    ('img5.jpg', "https://cdn.prod.website-files.com/68a44d4040f98a4adf2207b6/6a4d058625e4fe8fe6746855_41fef15e.png"),
    ('img6.jpg', "https://cdn.prod.website-files.com/68a44d4040f98a4adf2207b6/6a4d058625e4fe8fe6746852_ac6d87ee.png"),
    ('img7.jpg', "https://cdn.prod.website-files.com/68a44d4040f98a4adf2207b6/6a4d058625e4fe8fe674685d_45cfd994.png"),
    ('img8.jpg', "https://cdn.prod.website-files.com/68a44d4040f98a4adf2207b6/6a4d058625e4fe8fe6746860_ab0cbec6.png"),
    ('img9.jpg', "https://cdn.prod.website-files.com/68a44d4040f98a4adf2207b6/6a4d058625e4fe8fe6746865_c62704ad.png"),
    ('img10.jpg', "https://cdn.prod.website-files.com/68a44d4040f98a4adf2207b6/6a4d058625e4fe8fe6746868_e1c52525.png"),
    ('img11.jpg', "https://cdn.prod.website-files.com/68a44d4040f98a4adf2207b6/6a4d058625e4fe8fe674686b_dc7b4801.png"),
    ('img12.jpg', "https://cdn.prod.website-files.com/68a44d4040f98a4adf2207b6/6a4d058625e4fe8fe674686e_80670a42.png"),
    ('img13.jpg', "https://cdn.prod.website-files.com/68a44d4040f98a4adf2207b6/6903d22d7d4c10df6024f7bc_ee580919acaba2ddc07425f7a7390c8962cadc94-1000x1000.svg"),
    ('img14.jpg', "https://cdn.prod.website-files.com/68a44d4040f98a4adf2207b6/6903d229e73ca2d0d73d78f7_682ac293884c9d4ee4ebe2355a2f6c4ecfdd9c1b-1000x1000.svg"),
    ('img15.jpg', "https://cdn.prod.website-files.com/68a44d4040f98a4adf2207b6/6903d2287f90c57df4c9dd97_c1ef4c0b6882dfe985555b52999d370ea88a3c50-1000x1000.svg"),
    ('img16.jpg', "https://cdn.prod.website-files.com/68a44d4040f98a4adf2207b6/6903d22e6fa9211768bbce0b_6e00dbffcddc82df5e471c43453abfc74ca94e8d-1000x1000.svg"),
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
