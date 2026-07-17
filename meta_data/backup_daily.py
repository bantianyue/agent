#!/usr/bin/env python3
# 方案B：每日定时备份 articles.db -> articles.db.YYYYMMDD-HHMMSS
# 保留最近 7 份（按文件名时间排序），自动清理更早的。
# cron 调用：每天 02:00 跑一次
import os, shutil, glob, datetime

ROOT = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(ROOT, "articles.db")
PREFIX = "articles.db."

def main():
    if not os.path.isfile(DB):
        print("no db, skip")
        return
    ts = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).strftime("%Y%m%d-%H%M%S")
    dst = os.path.join(ROOT, PREFIX + ts)
    shutil.copy2(DB, dst)
    print("backup ->", os.path.basename(dst))
    # 清理：保留最新 7 份
    files = sorted(glob.glob(os.path.join(ROOT, PREFIX + "*")), reverse=True)
    # 排除 .bak（方案A的热备）不参与计数
    dailies = [f for f in files if not f.endswith(".bak")]
    for old in dailies[7:]:
        try:
            os.remove(old)
            print("prune ->", os.path.basename(old))
        except Exception:
            pass

if __name__ == "__main__":
    main()
