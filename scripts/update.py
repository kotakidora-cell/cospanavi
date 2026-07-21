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

# ふるさと納税(楽天のみ・別ロジック)
from fetch_furusato import FURUSATO
for slug in FURUSATO:
    print(f"\n==== furusato-{slug} ====")
    subprocess.run([PY, "fetch_furusato.py", slug], check=False)
    subprocess.run([PY, "normalize_furusato.py", slug], check=False)
subprocess.run([PY, "build_furusato.py"], check=False)   # build_site後に実行(sitemap追記のため)
print("\n全カテゴリ更新完了")
