import urllib.request, os

urls = [
    ('img1.jpg', "https://substackcdn.com/image/fetch/$s_!3H8p!,w_1456,c_limit,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2Fdc703e1b-8ade-4ed0-80d9-f1ac48e985cc_720x255.avif"),
    ('img2.jpg', "https://substackcdn.com/image/fetch/$s_!_LM-!,w_1456,c_limit,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2Fb8d5f4c2-ac8b-4c55-81c4-a639948c8fea_1271x654.png"),
    ('img3.jpg', "https://substackcdn.com/image/fetch/$s_!3dg3!,w_1456,c_limit,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F36b70328-c6bd-46bd-bfce-5030bc0230b3_1600x586.png"),
    ('img4.jpg', "https://substackcdn.com/image/fetch/$s_!1hon!,w_1456,c_limit,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2Fb761e340-8b62-4252-ac1d-a0b1d9969ead_1648x254.png"),
    ('img5.jpg', "https://substackcdn.com/image/fetch/$s_!TjlX!,w_1456,c_limit,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2Fe8988cdf-b29f-4dc1-960a-f8f06b5412ae_1628x864.png"),
    ('img6.jpg', "https://substackcdn.com/image/fetch/$s_!IexE!,w_1456,c_limit,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F9d889303-a46f-43f8-9926-14ac14d28ecb_1594x450.png"),
    ('img7.jpg', "https://substackcdn.com/image/fetch/$s_!e0Da!,w_1456,c_limit,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2Fb766c567-3aec-4e49-aa4f-3f00f4d46ff5_1600x214.png"),
    ('img8.jpg', "https://substackcdn.com/image/fetch/$s_!_fQs!,w_1456,c_limit,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F62208cab-1d19-4d96-8e02-d10ead83b0e7_1596x360.png"),
    ('img9.jpg', "https://substackcdn.com/image/fetch/$s_!UbqF!,w_1456,c_limit,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F5e0f79e7-0a2e-490b-b66b-0ba72048a86d_1590x212.png"),
    ('img10.jpg', "https://substackcdn.com/image/fetch/$s_!9OsU!,w_1456,c_limit,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F28464895-5837-4f9c-845a-4487a5ef30ae_1592x212.png"),
    ('img11.jpg', "https://substackcdn.com/image/fetch/$s_!536T!,w_1456,c_limit,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F81fba8ef-fc97-438f-8b95-2144e52f1b41_1596x212.png"),
    ('img12.jpg', "https://substackcdn.com/image/fetch/$s_!g0LZ!,w_1456,c_limit,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2Ff9629b42-aabd-4a2c-a463-2a6b9e165f75_1596x212.png"),
    ('img13.jpg', "https://substackcdn.com/image/fetch/$s_!EzPx!,w_1456,c_limit,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2Ff69d4af8-c2a9-412d-bd40-2d5b34ebc630_1596x214.png"),
    ('img14.jpg', "https://substackcdn.com/image/fetch/$s_!wkRm!,w_1456,c_limit,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F6ce81372-4167-4084-be1e-c334672b2a8a_1602x212.png"),
    ('img15.jpg', "https://substackcdn.com/image/fetch/$s_!8EhS!,w_1456,c_limit,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2Fb9d5f675-6287-496a-80a4-5853de9913f4_3004x1488.png"),
    ('img16.jpg', "https://substackcdn.com/image/fetch/$s_!vPka!,w_1456,c_limit,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F522358b1-8d9b-42d1-807c-a7ec99d9094c_2998x1478.png"),
    ('img17.jpg', "https://substackcdn.com/image/fetch/$s_!IzIg!,w_1456,c_limit,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2Fcd3de3d7-53f9-4636-a494-6ae7583f4327_1600x164.png"),
    ('img18.jpg', "https://substackcdn.com/image/fetch/$s_!YUVw!,w_1456,c_limit,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2Fb51639b8-563d-405c-8030-2b881a24501d_1592x300.png"),
    ('img19.jpg', "https://substackcdn.com/image/fetch/$s_!qBMO!,w_1456,c_limit,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2Fb46377af-ffca-4ac7-97d0-6621c69a60e0_1594x442.png"),
    ('img20.jpg', "https://substackcdn.com/image/fetch/$s_!QIDW!,w_1456,c_limit,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2Fc0a808f9-e396-4995-b54c-2a0b01ef4004_3008x1786.png"),
]

for fname, url in urls:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            with open(fname, 'wb') as f:
                f.write(r.read())
        print(f'OK {fname} ({os.path.getsize(fname)//1024}KB)')
    except Exception as e:
        print(f'FAIL {fname}: {e}')
print('All images downloaded')
