#!/usr/bin/env python3
"""Rebuild blocks.jsonl figure order for quantization-fit-model-quality.

Why: the first pw-extract run could not read the rendered DOM (proxy broke the
local CDP call) and fell back to a degraded fxtwitter order. The rendered DOM
was then read directly with cdp_x_extract.py (NO_PROXY for 127.0.0.1) and it
agrees with the fxtwitter Draft.js atomic-block order, which is the order
written here.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))

HERO = "https://pbs.twimg.com/media/HSSH_mRXMAAwQQN.jpg"

# (url, after_para_index_within_whole_document_flow) -- DOM order == atomic order
DOM_FIGS = [
    "https://pbs.twimg.com/media/HSR3C0AWYAAD4QB.jpg",
    "https://pbs.twimg.com/media/HSR3GbnWoAAPHqb.jpg",
    "https://pbs.twimg.com/media/HSR3JhrXAAE_d5S.jpg",
    "https://pbs.twimg.com/media/HSR2j6_WgAAwPoO.jpg",
    "https://pbs.twimg.com/media/HSSB9ksWIAAJ8GY.jpg",
    "https://pbs.twimg.com/media/HSR3NrMX0AEOoD0.jpg",
    "https://pbs.twimg.com/media/HSSCR_nWYAAdZ6n.jpg",
    "https://pbs.twimg.com/media/HSSBfuNWwAEvKXD.jpg",
    "https://pbs.twimg.com/media/HSSBqtdXMAAh79S.jpg",
]


def main():
    blocks_path = os.path.join(HERE, "blocks.jsonl")
    text_block = None
    with open(blocks_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            b = json.loads(line)
            if b.get("type") == "text":
                text_block = b
            elif b.get("hero") and text_block is None:
                text_block = None
    if text_block is None:
        raise SystemExit("text block not found in blocks.jsonl")

    out = [text_block]
    out.append({"type": "figure", "img": HERO,
                "caption": "Quantization: Fit a Model Without Losing Required Quality",
                "after_para": 0, "hero": True})
    for i, url in enumerate(DOM_FIGS, start=1):
        out.append({
            "type": "figure",
            "img": url,
            "caption": "",
            "after_para": 0,
            "hero": False,
            "fig_index": i,
            "media_id": url.rsplit("/", 1)[-1].split(".")[0],
            "caption_slot": "empty",
            "order_source": "rendered DOM (cdp_x_extract) == fxtwitter atomic blocks",
        })
    with open(blocks_path, "w", encoding="utf-8") as fh:
        for b in out:
            fh.write(json.dumps(b, ensure_ascii=False) + "\n")

    with open(os.path.join(HERE, "image_list.txt"), "w", encoding="utf-8") as fh:
        fh.write("Total images: %d\n\n" % (len(DOM_FIGS) + 1))
        fh.write("[hero] %s\n" % HERO)
        for i, url in enumerate(DOM_FIGS, start=1):
            fh.write("[fig%02d] %s\n" % (i, url))
    print("blocks.jsonl rewritten: 1 hero + %d figs (DOM order)" % len(DOM_FIGS))


if __name__ == "__main__":
    main()
