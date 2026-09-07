#!/usr/bin/env bash
# Persistent retry downloader for p4 figures
cd /d/06_Hermes/articles/_tmp_p4figs
files="ep_schema.png what_we_learnt_heatmap.svg 5Dparallelism_8Bmemoryusage.svg 5d_full.svg 5d_nutshell_tp_sp.svg 5d_nutshell_cp.svg 5d_nutshell_ep.svg"
for f in $files; do
  echo "=== $f start" >> dl.log
  ok=0
  for i in $(seq 1 30); do
    code=$(curl -sL -o "$f" -w "%{http_code}" --max-time 60 -x http://127.0.0.1:7890 "https://huggingface.co/spaces/nanotron/ultrascale-playbook/resolve/main/assets/images/$f" 2>>dl.log)
    sz=$(stat -c%s "$f" 2>/dev/null || echo 0)
    if [ "$code" = "200" ] && [ "$sz" -gt 1000 ]; then echo "OK $f http=$code size=$sz" >> dl.log; ok=1; break; fi
    sleep 8
  done
  echo "=== $f done ok=$ok" >> dl.log
done
