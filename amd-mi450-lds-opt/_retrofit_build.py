# -*- coding: utf-8 -*-
"""把 2026-09-01「格式保留」版 article_zh.html 重建成标准模板 article_data.json。

背景：该篇 2026-09-19 16:58 推的稿子是上一轮私有脚本链（_regen1c/2/3/4.py）直接改写源站
Sphinx DOM 得到的，绕过了标准管线 —— 没有要点速览卡、没有结语卡、正文用源站 pydata 的
<div> 结构（微信图文编辑器不认 div，卡片样式会丢），还残留源站社交图标条、其他资源、
免责声明。本脚本按 templates/article.template.html 的 schema 重建 article_data.json，
正文中文原样复用（不重译），只做：结构重排 + 清源站杂质 + 修两处真实 bug。
"""
import json
import re
import sys

from bs4 import BeautifulSoup

BASE = r"D:/06_Hermes/articles/amd-mi450-lds-opt"
SRC = BASE + "/article_zh.html"
OUT = BASE + "/article_data.json"
URL = "https://rocm.blogs.amd.com/software-tools-optimization/mi450-lds-optimization/README.html"
TITLE = "AMD Instinct MI450 GPU 上的 LDS 优化深度解析"

# 代码块语言（按内容人工判定；Pygments 猜错会让高亮全无或乱色）
CODE_LANGS = ["mlir", "text", "text", "text", "python", "python", "text"]

TAGS = ("h1", "h2", "h3", "h4", "h5", "p", "ul", "ol", "figure", "pre", "table")


def inline_html(el, keep_classes=("pre", "mathreg")):
    """取元素的 inner HTML，丢掉源站 pydata 的样式属性，保留内联代码/公式 span。

    模板会自带 <p class="p" style=...>，这里只喂内层内容；<code> 的浅灰底纹要保留
    （用户 2026-09-01 明确要求变量高亮不丢），所以只清 style 里的字体/颜色以外的东西。
    """
    clone = BeautifulSoup(str(el), "html.parser")
    node = clone.find()
    # 去掉源站行内样式，避免 pydata 的 color/margin 覆盖模板统一样式
    for tag in node.find_all(True):
        if tag.name in ("code", "span"):
            style = tag.get("style") or ""
            if tag.name == "code" and "background" in style:
                tag["style"] = (
                    "background:#f3f4f5;padding:2px 5px;border-radius:3px;"
                    "color:#222832;font-size:13px;font-family:Consolas,Monaco,monospace;"
                )
            else:
                tag.attrs.pop("style", None)
        else:
            tag.attrs.pop("style", None)
        for attr in ("class", "data-src", "loading", "title", "alt"):
            if tag.name not in ("img",) or attr != "src":
                tag.attrs.pop(attr, None)
    return node.decode_contents().strip()


def main():
    soup = BeautifulSoup(open(SRC, encoding="utf-8").read(), "html.parser")
    art = soup.find("article")
    if art is None:
        sys.exit("找不到 <article>")

    # 源站社交图标条（LinkedIn/X/Reddit/Facebook/Email SVG）：正文杂质，直接删
    for d in art.select("div.icon-bar"):
        d.decompose()

    ordered = []
    for el in art.descendants:
        if getattr(el, "name", None) not in TAGS:
            continue
        if el.find_parent(["pre", "table", "li", "figcaption", "figure"]) and el.name != "figure":
            continue
        if el.find_parent("figure") and el.name != "figure":
            continue
        ordered.append(el)

    lead_pool, sections = [], []
    cur = None
    pre_idx = 0
    drop_roadmap_list = False
    seen_first_h2 = False

    def add_para(html):
        if cur is not None:
            cur["paras"].append(html)
        else:
            lead_pool.append(html)

    for el in ordered:
        name = el.name
        text = re.sub(r"\s+", " ", el.get_text(" ", strip=True))

        if name == "h1":
            continue
        if name in ("h4", "h5"):
            continue

        if name == "h2":
            # 「其他资源」起（含）之后是源站附录/免责声明，整块丢弃
            if text.startswith("其他资源") or text.startswith("免责声明"):
                break
            if text.startswith("分区冲突"):
                text = "第二部分：分区冲突"
            cur = {"type": "h2", "title": text, "paras": [], "fig_after": {}}
            sections.append(cur)
            seen_first_h2 = True
            drop_roadmap_list = False
            continue

        if name == "h3":
            cur = {"type": "h3", "title": text, "paras": [], "fig_after": {}}
            sections.append(cur)
            continue

        if name == "figure":
            if cur is None:
                sys.exit("首个 figure 出现在任何 h2 之前，无法挂载")
            img = el.find("img")
            cap = el.find("figcaption")
            fig = {
                "src": (img.get("src") or "").rsplit("/", 1)[-1],
                "caption": (re.sub(r"\s+", " ", cap.get_text(" ", strip=True)) if cap else ""),
            }
            key = str(max(0, len(cur["paras"]) - 1))
            cur["fig_after"].setdefault(key, []).append(fig)
            continue

        if name == "pre":
            code = el.get_text().replace("\xa0", " ")
            lang = CODE_LANGS[pre_idx] if pre_idx < len(CODE_LANGS) else "text"
            pre_idx += 1
            add_para("__CODE__%s::%s" % (lang, code))
            continue

        if name == "table":
            head = [th.get_text(" ", strip=True) for th in el.find_all("th")]
            rows = []
            for tr in el.find_all("tr"):
                tds = tr.find_all("td")
                if tds:
                    rows.append([td.get_text(" ", strip=True) for td in tds])
            if cur is None or not head or not rows:
                sys.exit("表格提取异常 head=%s rows=%s" % (head, len(rows)))
            cur["table"] = {"head": head, "rows": rows}
            continue

        if name in ("ul", "ol"):
            if drop_roadmap_list:
                drop_roadmap_list = False
                continue
            items = [inline_html(li) for li in el.find_all("li")]
            for it in items:
                if it:
                    add_para("· " + it)
            continue

        if name != "p":
            continue

        # —— 下面是 p 的清洗规则 ——
        if text.startswith("The first two authors"):
            continue  # 作者署名行：正文不留作者信息
        if text in ("说明", "注意"):
            continue  # admonition 的标题词单独成段，删掉只留正文
        if text == "本文将介绍：":
            drop_roadmap_list = True  # 其后的路线图列表一并丢（章节标题已自解释）
            continue
        if text.startswith('{"id":') and '"content"' in text:
            # bug：上一轮把 blocks.jsonl 的一条 JSON 记录当正文写进了段落
            payload = json.loads(text)
            el = BeautifulSoup("<div>%s</div>" % payload["content"], "html.parser").div
        if "\\begin{split}" in text:
            # bug：LaTeX 源码直出（微信不渲染），转成 Unicode 文本
            add_para("<strong>L = [ T 0 ; 0 R ]</strong>")
            continue

        html = inline_html(el)
        # 修补翻译残缺：「矩阵 L 可被 <em> </em>左可除 T」→ 正常语序
        html = html.replace("<em> </em>左可除<span class=\"mathreg\">T</span>", "左除 T")
        html = re.sub(r"<em>\s*</em>", "", html)
        if not html.strip():
            continue
        add_para(html)

    if pre_idx != len(CODE_LANGS):
        print("⚠️ 代码块数 %d != 语言表 %d" % (pre_idx, len(CODE_LANGS)))

    lead = lead_pool
    data = {
        "title": TITLE,
        "summary": [
            {"key": "两个瓶颈", "body": "LDS 有两处开销悄悄吃掉吞吐：layout 与矩阵核心期望不一致时 load 退化；跨 SIMD pair 的 warp 撞上同一物理分区时访问串行化。"},
            {"key": "转置加载", "body": "ds_load_tr 让每个 lane 发一次宽读，跨 lane 重分布交给硬件，是否可用归结为一次左除（divideLeft）判定。"},
            {"key": "分区冲突", "body": "swizzle 后的 ctaLayout 加上 PartitionedSharedLayout 与分区感知分配器把两个 pair 在物理上拆开，微基准测得带宽 1.65 倍。"},
        ],
        "lead": lead,
        "sections": sections,
        "conclusion": [
            "在 AMD Instinct™ MI450 GPU 上，有两个 LDS 效应会悄然限制 kernel 吞吐。transposed LDS load：ds_load_tr 的 cooperative-transpose 指令让每个 lane 发出一次宽读，由硬件把数据重分布成 matrix core 期望的 layout；编译器不模式匹配转置，而是把两侧表示为 linear layout 并通过 left division 判定可用性。",
            "partition conflict：为什么到达同一物理 LDS partition 的 cross-pair warp 会串行化，对 WMMA ctaLayout 做 swizzle 并用 PartitionedSharedLayout 固定 piece 归属，再加上 partition 感知分配器与循环不变的 base-pointer 求解，以几乎零运行时代价让这种分离落到物理层面。一个只读 LDS 的微基准测试给出收益：冲突解决后 LDS 带宽提升 1.65 倍。",
            "**这是可以直接套用的判断顺序**：先看 layout 是否匹配指令（能否用 ds_load_tr），再看物理分区有没有被拆开（ctaLayout、PartitionedSharedLayout、分配器），最后才轮到调参。LDS 只是 global memory 到 matrix core 之间的一站，但这一站决定了 kernel 能不能摸到理论带宽。",
        ],
        "reference_url": URL,
    }

    # —— 自检 ——
    figs = [f["src"] for s in sections for fl in s["fig_after"].values() for f in fl]
    body = [p for s in sections for p in s["paras"]]
    for s in sections:
        for k in s["fig_after"]:
            if int(k) >= len(s["paras"]) or int(k) < 0:
                sys.exit("fig_after 越界: %s key=%s paras=%d" % (s["title"], k, len(s["paras"])))
    dup = [f for f in figs if figs.count(f) > 1]
    if dup:
        sys.exit("图片重复引用: %s" % sorted(set(dup)))
    import os
    on_disk = sorted(f for f in os.listdir(BASE) if re.match(r"^fig\d+\.(png|webp)$", f))
    missing = [f for f in on_disk if f not in figs]
    extra = [f for f in figs if f not in on_disk]
    json.dump(data, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    print("sections=%d paras=%d code=%d figs=%d lead=%d" %
          (len(sections), len(body), sum(1 for p in body if p.startswith("__CODE__")), len(figs), len(lead)))
    print("磁盘 fig=%d  引用=%d  未引用=%s  无文件=%s" % (len(on_disk), len(set(figs)), missing, extra))
    print("h2=%d h3=%d" % (
        sum(1 for s in sections if s["type"] == "h2"),
        sum(1 for s in sections if s["type"] == "h3")))
    print("中文字符=%d  残留 latex=%d" % (
        len(re.findall(r"[\u4e00-\u9fff]", json.dumps(data, ensure_ascii=False))),
        len(re.findall(r"\\\\begin|\\\\frac|\\\\mathbb", json.dumps(data, ensure_ascii=False)))))


if __name__ == "__main__":
    main()
