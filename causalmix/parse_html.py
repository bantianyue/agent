from html.parser import HTMLParser
import re, os

class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text = []
        self.in_script = False
        self.in_style = False
        self.in_svg = False
    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            setattr(self, f'in_{tag}', True)
        if tag == 'svg':
            self.in_svg = True
        if tag in ('p', 'h1', 'h2', 'h3', 'h4', 'h5', 'br', 'div', 'section', 'li', 'tr', 'th', 'td'):
            self.text.append('\n')
    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            setattr(self, f'in_{tag}', False)
        if tag == 'svg':
            self.in_svg = False
        if tag in ('p', 'h1', 'h2', 'h3', 'h4', 'h5', 'div', 'section', 'li', 'th', 'td'):
            self.text.append('\n')
    def handle_data(self, data):
        if not self.in_script and not self.in_style and not self.in_svg:
            self.text.append(data.strip())

paper_dir = 'D:\\06_Hermes\\articles\\causalmix'
with open(os.path.join(paper_dir, 'full_paper.html'), 'r', encoding='utf-8') as f:
    html = f.read()

# Extract <article> content specifically
m = re.search(r'<article[^>]*>(.*?)</article>', html, re.DOTALL)
if m:
    article_html = m.group(1)
else:
    # Fallback: whole body
    m2 = re.search(r'<body[^>]*>(.*?)</body>', html, re.DOTALL)
    if m2:
        article_html = m2.group(1)
    else:
        article_html = html

extractor = TextExtractor()
extractor.feed(article_html)
text = ''.join(extractor.text)
text = re.sub(r'\n{3,}', '\n\n', text)
text = re.sub(r'\s*\n\s*', '\n', text)

with open(os.path.join(paper_dir, 'full_text.txt'), 'w', encoding='utf-8') as f:
    f.write(text)
print(f'Extracted {len(text)} chars from article{" via <article>" if m else ""}')
print()
# Print first 1000 chars
print(text[:1000])
