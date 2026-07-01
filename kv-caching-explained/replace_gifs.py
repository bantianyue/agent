import sys

with open('temp-article.html', 'r', encoding='utf-8') as f:
    html = f.read()

gif_urls = {
    'WECHATIMGPH_2': 'http://mmbiz.qpic.cn/sz_mmbiz_gif/MJRkdzPjdxQAX5Nt2ms0BHOD27FM6l1uLJEtlZK6wIAdHvlRF80ibIWzMVlibIkkTRibHWy0aDGKR71kfuYx0eibbvV96ib7N1TlnBsYj8FmpShA/0?wx_fmt=gif',
    'WECHATIMGPH_3': 'http://mmbiz.qpic.cn/mmbiz_gif/MJRkdzPjdxQ9n4j0aWLF0l4vovejGm50jHZ6xbYG74PkgmsUlIfbSbcHcYCR8N97By8fyDywmvXqJ2QTOPhQpiaogOPKrTMZ3qkAjicUic1KVQ/0?wx_fmt=gif',
    'WECHATIMGPH_4': 'http://mmbiz.qpic.cn/sz_mmbiz_gif/MJRkdzPjdxSYzL3p9iaiaBVp5ibsiclJ8c0Y18Ora0xNk8GIUic0QnEjanUxibWtcro3yrxhBsY826WKdhUhY348TlaiakQD00HHgBeMnFOCPlFFcw/0?wx_fmt=gif',
    'WECHATIMGPH_5': 'http://mmbiz.qpic.cn/mmbiz_gif/MJRkdzPjdxRibdQAooczHVW8UdN2ib8Q7ZAYUhJicBCzojnQU7TmR4bV7zElibq1SibcIOs90n46yia1AnYiapzHY69UcmoVpMJvaoEicicoMRDibQzHY/0?wx_fmt=gif',
    'WECHATIMGPH_6': 'http://mmbiz.qpic.cn/mmbiz_gif/MJRkdzPjdxTbWY9iaPdq1H0JzdeyoGCNEiaCdxS63hdcRzAZKVNfwLbFu0icWjS9uTmKwtqBqKPLC6GpLJUiaFWBDquLFCRxlviaKBYVVf7Ezobc/0?wx_fmt=gif',
    'WECHATIMGPH_8': 'http://mmbiz.qpic.cn/mmbiz_gif/MJRkdzPjdxSq29icNPREHSXkUY0Tc5ricDoYYkkwNHwXRsTsbZK5aDxSLib4EFAiawsxEIE38vZcu2w731BTjTiaic43m5RzBB71aaQWCIsIjtXxk/0?wx_fmt=gif',
}

for placeholder, url in gif_urls.items():
    img_tag = f'<img src="{url}" alt="" style="max-width:100%;height:auto;">'
    count = html.count(placeholder)
    if count > 0:
        html = html.replace(placeholder, img_tag)
        print(f'Replaced {placeholder} -> GIF ({count} occurrence)')
    else:
        print(f'WARNING: {placeholder} not found in HTML')

with open('article_final.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f'\nFinal HTML length: {len(html)} chars')
