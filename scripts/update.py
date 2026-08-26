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
    subprocess.run([PY, "fetch_furusato.py", slug, "15"], check=False)  # 日次は15ページに抑制(商品取得後のレート制限回避)
    subprocess.run([PY, "normalize_furusato.py", slug], check=False)
# ふるさと納税「現地で使える体験」(全国を県別に。複数キーワードで取得)
print("\n==== furusato-local(現地体験) ====")
subprocess.run([PY, "fetch_local.py", "6"], check=False)
subprocess.run([PY, "build_furusato.py"], check=False)   # build_site後に実行(sitemap追記のため。build_localも内包)

# 空データでのデプロイ防止ガード: ふるさと納税の取得が失敗(レート制限等)して空になった場合、
# 非ゼロ終了してCIのデプロイstep(別step)をスキップ→本番の既存ページを保持し、空上書きを防ぐ。
import json as _json, glob as _glob
_DATA = os.path.join(os.path.dirname(os.getcwd()), "data")
def _cnt(p):
    try:
        return len(_json.load(open(p, encoding="utf-8")))
    except Exception:
        return 0
_loc = _cnt(os.path.join(_DATA, "furusato-local_raw.json"))
_raw = sum(_cnt(f) for f in _glob.glob(os.path.join(_DATA, "furusato-*_raw.json")))
if _loc == 0 or _raw < 500:
    print(f"\n[ABORT] ふるさと納税データ不足 (現地体験={_loc}件, カテゴリ生データ計={_raw}件)。"
          f"取得失敗の可能性→空デプロイ防止のため異常終了します(本番は保持されます)。")
    sys.exit(1)
print("\n全カテゴリ更新完了")
