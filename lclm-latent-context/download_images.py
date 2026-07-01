import urllib.request
import os

urls = [
    ("https://pbs.twimg.com/media/HKizmVSboAEPqxO?format=jpg&name=orig", "img1_hero.jpg"),
    ("https://pbs.twimg.com/media/HKijU_QawAA69xi?format=png&name=orig", "img2_arch.png"),
    ("https://pbs.twimg.com/media/HKikZNVbsAA9l1o?format=jpg&name=orig", "img3_loss_chart.jpg"),
    ("https://pbs.twimg.com/media/HKilyqwaIAAtMta?format=jpg&name=orig", "img4_benchmark.jpg"),
    ("https://pbs.twimg.com/media/HKipoaOaEAAqlV7?format=jpg&name=orig", "img5_ttft.jpg"),
    ("https://pbs.twimg.com/media/HKiqHIraoAAnUGk?format=jpg&name=orig", "img6_memory.jpg"),
    ("https://pbs.twimg.com/media/HKist57aYAAaq81?format=jpg&name=orig", "img7_agent.jpg"),
    ("https://pbs.twimg.com/media/HKis7fNbQAAmtQ7?format=jpg&name=orig", "img8_expand.jpg"),
    ("https://pbs.twimg.com/media/HKivnq4aQAIlwMC?format=jpg&name=orig", "img9_training.jpg"),
]

outdir = "D:\\06_Hermes\\articles\\lclm-latent-context"
proxy_handler = urllib.request.ProxyHandler({'http': 'http://127.0.0.1:7890', 'https': 'http://127.0.0.1:7890'})
opener = urllib.request.build_opener(proxy_handler)

for url, fname in urls:
    path = os.path.join(outdir, fname)
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with opener.open(req, timeout=30) as resp:
            with open(path, 'wb') as f:
                f.write(resp.read())
        print(f"OK: {fname} ({os.path.getsize(path)} bytes)")
    except Exception as e:
        print(f"FAIL: {fname} - {e}")
