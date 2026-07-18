# 全カテゴリを一括更新: 各カテゴリで 楽天+Yahoo取得→正規化 → 最後にサイト生成。
# categories.py にカテゴリを足すだけで自動的に対象が増える（ワークフロー変更不要）。
import subprocess, sys, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from categories import CATEGORIES

PY = sys.executable
for slug in CATEGORIES:
    print(f"\n==== {slug} ====")
    subprocess.run([PY, "fetch_rakuten.py", slug], check=True)
    subprocess.run([PY, "fetch_yahoo.py", slug], check=False)   # Yahoo失敗(APIキー未設定等)は楽天のみで継続
    subprocess.run([PY, "normalize_score.py", slug], check=True)
subprocess.run([PY, "build_site.py"], check=True)
print("\n全カテゴリ更新完了")
