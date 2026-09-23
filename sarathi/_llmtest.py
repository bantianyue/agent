# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, r"C:\Users\twfehh7\.workbuddy\skills\wechat-article-sop\scripts")
import llm_utils

LOG = r"D:\06_Hermes\articles\sarathi\_llmtest.txt"
buf = []
try:
    cfg = llm_utils.load_llm_config()
    buf.append("CFG " + str({k: (v[:12] + "..." if k == "api_key" and v else v) for k, v in cfg.items()}))
    r = llm_utils.translate("Sarathi splits a prefill request into equal sized chunks, and populates the remaining batch slots with decodes.", stream=False)
    buf.append("OUT " + r)
except Exception as e:
    import traceback
    buf.append("EXC\n" + traceback.format_exc())
open(LOG, "w", encoding="utf-8").write("\n".join(buf))
