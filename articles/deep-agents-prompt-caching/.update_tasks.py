#!/usr/bin/env python3
"""Update TASKS.md - add new task entry and status history."""
import os

tasks_path = "D:/06_Hermes/articles/TASKS.md"

with open(tasks_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find the last task number
import re
nums = re.findall(r'^\|\| (\d+) \|', content, re.MULTILINE)
last_num = max(int(n) for n in nums) if nums else 0
new_num = last_num + 1

# Add to task table - find the last table row
table_insert = f"\n|| {new_num} | 2026-06-27 | https://www.langchain.com/blog/deep-agents-prompt-caching | Prompt Caching with Deep Agents | deep-agents-prompt-caching | TBD | TBD | 📥 进行中 |"

# Insert before the first Status History section
insert_pos = content.find("\n## 状态历史")
if insert_pos == -1:
    insert_pos = len(content)

new_content = content[:insert_pos] + table_insert + content[insert_pos:]

# Add status history
status_entry = f"""
### #{new_num} - deep-agents-prompt-caching

| 时间戳 | 状态 | 说明 |
|--------|------|------|
| 2026-06-27 14:30 | 📥 开始 | 收到 URL，Jina Reader 提取完整文章 + 4 张配图 |
"""

# Insert status history before the first status history or at the end
# Find where to insert (before the first status entry)
existing_statuses = re.findall(r'^### #', new_content, re.MULTILINE)
if existing_statuses:
    # Insert after the last status history entry - find end of file
    new_content += status_entry
else:
    # Add status history section if it doesn't exist
    new_content += f"\n\n## 状态历史\n{status_entry}"

with open(tasks_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print(f"Added task #{new_num}: deep-agents-prompt-caching")
