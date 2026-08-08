# 楽天ふるさと納税の「現地で使える体験型返礼品」を取得 → data/furusato-local_raw.json
# 食事券/宿泊/施設利用/レジャー/温泉/体験 等、寄付先の現地で使うタイプを複数キーワードで集めて統合。
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

PREFS = ["北海道","青森県","岩手県","宮城県","秋田県","山形県","福島県","茨城県","栃木県","群馬県",
         "埼玉県","千葉県","東京都","神奈川県","新潟県","富山県","石川県","福井県","山梨県","長野県",
         "岐阜県","静岡県","愛知県","三重県","滋賀県","京都府","大阪府","兵庫県","奈良県","和歌山県",
         "鳥取県","島根県","岡山県","広島県","山口県","徳島県","香川県","愛媛県","高知県","福岡県",
         "佐賀県","長崎県","熊本県","大分県","宮崎県","鹿児島県","沖縄県"]

# 現地利用型を集めるキーワード（「ふるさと納税」と組み合わせて自治体返礼品に寄せる）
KEYWORDS = [
    "ふるさと納税 食事券", "ふるさと納税 お食事券", "ふるさと納税 宿泊券", "ふるさと納税 宿泊",
    "ふるさと納税 温泉", "ふるさと納税 利用券", "ふるさと納税 入場券", "ふるさと納税 体験",
    "ふるさと納税 チケット", "ふるさと納税 レジャー", "ふるさと納税 ゴルフ", "ふるさと納税 旅行",
    "ふるさと納税 ペア宿泊", "ふるさと納税 招待券", "ふるさと納税 クーポン",
]

# 現地で使う強いシグナル（これを含むものだけ採用＝配送物の食品等を除外）
ONSITE = ["食事券", "宿泊券", "宿泊", "利用券", "入場券", "入園券", "招待券", "体験", "チケット",
          "温泉", "旅行券", "ゴルフ", "レジャー", "アクティビティ", "クーポン", "回数券", "ペア"]
# 明らかに配送物・食品（現地利用でない）を除外
EXCLUDE = ["kg", "ｋｇ", "g）", "ｇ）", "定期便", "冷凍", "詰め合わせ", "食べ比べ", "訳あり",
           "送料", "ml", "ｍｌ", "リットル", "米 ", "精米", "無洗米"]

def pref_of(shop):
    for p in PREFS:
        if shop.startswith(p):
            return p
    return None

def fetch(keyword, pages):
    out = []
    for pg in range(1, pages + 1):
        p = {"applicationId": RAKUTEN_APP_ID, "accessKey": RAKUTEN_ACCESS_KEY, "affiliateId": RAKUTEN_AFFILIATE_ID,
             "format": "json", "hits": 30, "page": pg, "sort": "-reviewCount", "keyword": keyword}
        try:
            j = requests.get(URL, params=p, headers=HDR, timeout=25).json()
            if "error" in j:
                print(f"  {keyword} p{pg} error: {j['error']}"); break
            for it in j.get("Items", []):
                i = it["Item"]
                out.append({
                    "name": i["itemName"], "price": i["itemPrice"],
                    "review": i["reviewAverage"], "reviewCount": i["reviewCount"],
                    "shop": i["shopName"], "url": i["itemUrl"], "affiliate": i["affiliateUrl"],
                    "image": (i.get("mediumImageUrls") or [{}])[0].get("imageUrl", "") if i.get("mediumImageUrls") else "",
                })
            if pg >= j.get("pageCount", pg):
                break
        except Exception as e:
            print(f"  {keyword} p{pg} ERR {type(e).__name__}")
        time.sleep(1.0)
    return out

def keep(name):
    if "ふるさと納税" not in name and "納税" not in name:
        return False
    if not any(s in name for s in ONSITE):
        return False
    if any(x in name for x in EXCLUDE):
        return False
    return True

if __name__ == "__main__":
    pages = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    seen = {}
    for kw in KEYWORDS:
        got = fetch(kw, pages)
        kept = 0
        for x in got:
            if x["url"] in seen:
                continue
            if not keep(x["name"]):
                continue
            pr = pref_of(x["shop"])
            if not pr:
                continue
            x["pref"] = pr
            seen[x["url"]] = x
            kept += 1
        print(f"{kw}: 取得{len(got)} 採用{kept} 累計{len(seen)}")
    items = list(seen.values())
    json.dump(items, open(os.path.join(DATA, "furusato-local_raw.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"保存: furusato-local_raw.json  {len(items)}件")
