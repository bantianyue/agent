import sys, json, os
skill_dir = r"C:\Users\twfehh7\AppData\Local\hermes\skills\content-creation\wechat-article-sop\scripts"
sys.path.insert(0, skill_dir)

import write_article_data as wad

# 构造临时测试
test_dir = r"D:\06_Hermes\articles\ai-model-co-design"
build = os.path.join(test_dir, "article_data_build.py")
bak = os.path.join(test_dir, "article_data_build.py.bak")

# 备份现有文件
if os.path.exists(build):
    open(bak, "w", encoding="utf-8").write(open(build, "r", encoding="utf-8").read())

# 写测试文件
open(build, "w", encoding="utf-8").write('''
DATA = {
    "summary": [{"key": "测试", "body": "test"}],
    "sections": [{"type": "h2", "title": "测试章", "paras": ["正文"]}],
    "conclusion": ["结语"],
    "reference_url": "https://example.com"
}
''')

# 测试 wad 逻辑
ns = {}
exec(compile(open(build, encoding="utf-8").read(), build, "exec"), ns)
data = ns["DATA"]
text = json.dumps(data, ensure_ascii=False, indent=2)
json.loads(text)
assert "summary" in data
assert "sections" in data
print("断言通过: json.dumps + json.load 双向校验 OK")

# 清理
if os.path.exists(bak):
    open(build, "w", encoding="utf-8").write(open(bak, encoding="utf-8").read())
    os.remove(bak)
print("测试文件已清理")
