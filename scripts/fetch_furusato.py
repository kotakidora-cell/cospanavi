# 楽天ふるさと納税の返礼品を取得 → data/furusato-<slug>_raw.json
# 通常商品と別ロジック（寄付額あたりの内容量=コスパ）なので専用パイプライン。
import json, os, sys, time
import requests
try:
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

# カテゴリ設定は furusato_cats.py に集約
from furusato_cats import FCATS as FURUSATO

def fetch(keyword, pages=30):
    items = []
    for pg in range(1, pages + 1):
        p = {"applicationId": RAKUTEN_APP_ID, "accessKey": RAKUTEN_ACCESS_KEY, "affiliateId": RAKUTEN_AFFILIATE_ID,
             "format": "json", "hits": 30, "page": pg, "sort": "-reviewCount", "keyword": keyword}
        try:
            j = requests.get(URL, params=p, headers=HDR, timeout=25).json()
            if "error" in j:
                print(f"  page{pg} error: {j['error']}"); break
            for it in j.get("Items", []):
                i = it["Item"]
                items.append({
                    "name": i["itemName"], "price": i["itemPrice"],
                    "review": i["reviewAverage"], "reviewCount": i["reviewCount"],
                    "shop": i["shopName"], "url": i["itemUrl"], "affiliate": i["affiliateUrl"],
                    "image": (i.get("mediumImageUrls") or [{}])[0].get("imageUrl", "") if i.get("mediumImageUrls") else "",
                })
            print(f"  page{pg}: 計{len(items)} / 総{j.get('count')}")
            if pg >= j.get("pageCount", pg):
                break
        except Exception as e:
            print(f"  page{pg} ERR {type(e).__name__}")
        time.sleep(1.0)
    return items

if __name__ == "__main__":
    slug = sys.argv[1] if len(sys.argv) > 1 else "rice"
    pages = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    kw = FURUSATO[slug]["keyword"]
    print(f"取得(楽天ふるさと納税): {slug} kw={kw} pages={pages}")
    items = fetch(kw, pages=pages)
    json.dump(items, open(os.path.join(DATA, f"furusato-{slug}_raw.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"保存: furusato-{slug}_raw.json  {len(items)}件")
