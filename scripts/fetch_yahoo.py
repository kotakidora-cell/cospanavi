# Yahoo!ショッピングAPI(V3 itemSearch)で商品取得 → data/<slug>_yahoo_raw.json
# 楽天(fetch_rakuten.py)と同じスキーマ＋mall/jan を付与し、normalize_score.pyで統合する。
import json, os, sys, time
import requests
try:  # ローカルは secrets.py、CIは環境変数
    from secrets import YAHOO_APP_ID
except (ImportError, ModuleNotFoundError):
    YAHOO_APP_ID = os.environ["YAHOO_APP_ID"]

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
URL = "https://shopping.yahooapis.jp/ShoppingWebService/V3/itemSearch"

def fetch(query, pages=20, genre=None, sort="-review_count"):
    items = []
    for pg in range(pages):
        start = pg * 50 + 1
        if start > 1000:  # start+results<=1000 制限
            break
        p = {"appid": YAHOO_APP_ID, "results": 50, "start": start, "sort": sort, "in_stock": "true"}
        if query: p["query"] = query
        if genre: p["genre_category_id"] = genre
        try:
            r = requests.get(URL, params=p, timeout=25)
            if r.status_code == 429:
                print(f"  page{pg+1} rate-limited, wait"); time.sleep(3); continue
            j = r.json()
            hits = j.get("hits", [])
            for h in hits:
                items.append({
                    "name": h.get("name", ""),
                    "price": h.get("price", 0),
                    "review": (h.get("review") or {}).get("rate", 0) or 0,
                    "reviewCount": (h.get("review") or {}).get("count", 0) or 0,
                    "shop": (h.get("seller") or {}).get("name", ""),
                    "url": h.get("url", ""),
                    "affiliate": h.get("url", ""),  # VC設定後にアフィリURLへ差し替え
                    "image": (h.get("image") or {}).get("medium", ""),
                    "jan": h.get("janCode", "") or "",
                    "mall": "yahoo",
                })
            print(f"  start{start}: +{len(hits)} (計{len(items)}) / 総{j.get('totalResultsAvailable')}")
            if not hits or start + 50 > (j.get("totalResultsAvailable") or 0):
                break
        except Exception as e:
            print(f"  page{pg+1} ERR {type(e).__name__}: {e}")
        time.sleep(1.1)  # 1req/秒制限
    return items

if __name__ == "__main__":
    # 使い方: python fetch_yahoo.py <slug> <query> [pages] [genre_category_id]
    slug = sys.argv[1] if len(sys.argv) > 1 else "robot-cleaner"
    query = sys.argv[2] if len(sys.argv) > 2 else "ロボット掃除機"
    pages = int(sys.argv[3]) if len(sys.argv) > 3 else 20
    genre = sys.argv[4] if len(sys.argv) > 4 else None
    print(f"取得(Yahoo): query={query} pages={pages} genre={genre}")
    items = fetch(query, pages=pages, genre=genre)
    json.dump(items, open(os.path.join(DATA, slug + "_yahoo_raw.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"保存: {slug}_yahoo_raw.json  {len(items)}件")
