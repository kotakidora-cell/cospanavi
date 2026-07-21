# 楽天市場商品検索APIで、指定キーワードの商品を複数ページ取得 → data/<slug>_raw.json
import json, os, sys, time
import requests
try:  # ローカルは secrets.py、CI(GitHub Actions)は環境変数から
    from secrets import RAKUTEN_APP_ID, RAKUTEN_ACCESS_KEY, RAKUTEN_AFFILIATE_ID, REFERER
except (ImportError, ModuleNotFoundError):
    RAKUTEN_APP_ID = os.environ["RAKUTEN_APP_ID"]
    RAKUTEN_ACCESS_KEY = os.environ["RAKUTEN_ACCESS_KEY"]
    RAKUTEN_AFFILIATE_ID = os.environ["RAKUTEN_AFFILIATE_ID"]
    REFERER = os.environ.get("REFERER", "https://cospa-navi.com/")

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
URL = "https://openapi.rakuten.co.jp/ichibams/api/IchibaItem/Search/20220601"
HDR = {"Referer": REFERER, "Origin": REFERER.rstrip("/")}

def fetch(keyword, pages=15, sort="-reviewCount", genreId=None):
    items = []
    for pg in range(1, pages + 1):
        p = {"applicationId": RAKUTEN_APP_ID, "accessKey": RAKUTEN_ACCESS_KEY,
             "affiliateId": RAKUTEN_AFFILIATE_ID,
             "format": "json", "hits": 30, "page": pg, "sort": sort}
        if keyword: p["keyword"] = keyword
        if genreId: p["genreId"] = genreId
        try:
            r = requests.get(URL, params=p, headers=HDR, timeout=25)
            j = r.json()
            if "error" in j:
                print(f"  page{pg} error: {j['error']} {j.get('error_description')}")
                break
            batch = j.get("Items", [])
            for it in batch:
                i = it["Item"]
                items.append({
                    "name": i["itemName"], "price": i["itemPrice"],
                    "review": i["reviewAverage"], "reviewCount": i["reviewCount"],
                    "shop": i["shopName"], "url": i["itemUrl"], "affiliate": i["affiliateUrl"],
                    "image": (i.get("mediumImageUrls") or [{}])[0].get("imageUrl", "") if i.get("mediumImageUrls") else "",
                    "itemCode": i.get("itemCode", ""),
                })
            print(f"  page{pg}: +{len(batch)} (計{len(items)}) / 総{j.get('count')}")
            if pg >= j.get("pageCount", pg):
                break
        except Exception as e:
            print(f"  page{pg} ERR {type(e).__name__}")
        time.sleep(1.0)
    return items

if __name__ == "__main__":
    # 使い方: python fetch_rakuten.py <slug> [pages]  （genreIdはcategories.pyから取得）
    from categories import CATEGORIES
    slug = sys.argv[1] if len(sys.argv) > 1 else "robot-cleaner"
    cfg = CATEGORIES[slug]
    genreId = cfg["rakuten_genre"]
    q = cfg.get("rakuten_query")  # ジャンルが他カテゴリと共通の時にキーワード併用で絞る(例:紙パック掃除機)
    pages = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    print(f"取得(楽天): {slug} genreId={genreId} query={q} pages={pages}")
    items = fetch(q, pages=pages, genreId=genreId)
    json.dump(items, open(os.path.join(DATA, slug + "_raw.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"保存: {slug}_raw.json  {len(items)}件")
