import re
html = open("server_draft.html", encoding="utf-8").read()

KP_OPEN  = '<div style="background:#e8f4fd;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:18px;">'
CJ_OPEN  = '<div style="background:#f5f0eb;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:16px;">'
CLOSE = '</div>'

# --- 要点速览 block ---
kp_head = html.find('<p><strong style="font-weight: bold;font-size: 16px;color: #1a6ba0;">')
assert kp_head >= 0, "要点速览 heading not found"
kp_end = html.find("<hr ")
assert kp_end >= 0, "hr after 要点速览 not found"
# wrap [kp_head:kp_end)
new = html[:kp_head] + KP_OPEN + html[kp_head:kp_end] + CLOSE + html[kp_end:]

# --- 结语 block ---
cj_head = new.find('<strong style="font-weight: bold;font-size: 15px;color: #8b6f4c;">')
assert cj_head >= 0, "结语 heading not found"
# back up to the preceding <p>
cj_start = new.rfind("<p>", 0, cj_head)
# end before 参考 line
cj_end = new.find("参考")
assert cj_end >= 0, "参考 line not found"
new2 = new[:cj_start] + CJ_OPEN + new[cj_start:cj_end] + CLOSE + new[cj_end:]

open("fixed_draft.html", "w", encoding="utf-8").write(new2)
print("done. len", len(new2))
print("has #e8f4fd:", "#e8f4fd" in new2, "has #f5f0eb:", "#f5f0eb" in new2)
print("dash count:", new2.count("——"))
