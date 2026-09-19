import sys, importlib.util, json
spec = importlib.util.spec_from_file_location("llm_utils", r"C:\Users\twfehh7\.codex\skills\wechat-article-sop\scripts\llm_utils.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
try:
    cfg = m.load_llm_config()
    print("cfg keys:", list(cfg.keys()))
    print("base_url:", cfg.get("base_url"), "model:", cfg.get("model"))
except Exception as e:
    print("cfg err", e)
r = m.translate_batch([{"id":1,"type":"text","content":"Rollout dominates the training time in LLM post-training."}], batch_size=1)
print(r)
