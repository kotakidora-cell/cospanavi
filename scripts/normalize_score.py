# raw listing → 機種正規化(ブランド+型番) → 満足度コスパ値算出 → data/<slug>.json
import json, os, sys, re, math, statistics as st

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
slug = sys.argv[1] if len(sys.argv) > 1 else "robot-cleaner"
raw = json.load(open(os.path.join(DATA, slug + "_raw.json"), encoding="utf-8"))
for r in raw:
    r.setdefault("mall", "rakuten")
# Yahoo取得分があれば統合（複数モール最安値比較）
_yahoo = os.path.join(DATA, slug + "_yahoo_raw.json")
if os.path.exists(_yahoo):
    _yr = json.load(open(_yahoo, encoding="utf-8"))
    raw += _yr
    print(f"Yahoo統合: +{len(_yr)}件")

# 付属品除外語・ブランド正規化はカテゴリ毎に異なるためcategories.pyから取得
from categories import CATEGORIES
_cat = CATEGORIES[slug]
EXCLUDE = _cat["exclude"]
BRANDS = _cat["brands"]
def brand_of(nm):
    low = nm.lower()   # 大文字小文字を無視（levoit/Levoit/LEVOIT等を同一視）
    for al, canon in BRANDS:
        if any(a.lower() in low for a in al):
            return canon
    return "その他・ノーブランド"

def clean(nm):
    nm = re.sub(r"【[^】]*】", "", nm)
    nm = re.sub(r"\[[^\]]*\]", "", nm)
    nm = re.sub(r"（[^）]*OFF[^）]*）", "", nm)
    return re.sub(r"\s+", " ", nm).strip()

MODEL_RE = re.compile(r"[A-Za-z]{1,7}\s?-?\s?[0-9]{1,4}[A-Za-z+]{0,4}")
def model_key(brand, nm):
    c = clean(nm)
    m = MODEL_RE.search(c)
    tok = re.sub(r"\s", "", m.group(0)).upper() if m else ""
    if not tok:  # 型番が拾えない→名前の頭で代替キー
        tok = re.sub(r"[^\w一-龠ぁ-んァ-ヶ]", "", c)[:10]
    return brand + "|" + tok

# --- 機種にまとめる ---
items = [r for r in raw if not any(x in r["name"] for x in EXCLUDE) and r["price"] and r["price"] >= 3000]
groups = {}
for r in items:
    b = brand_of(r["name"]); k = model_key(b, r["name"])
    g = groups.setdefault(k, {"brand": b, "listings": []})
    g["listings"].append(r)

models = []
for k, g in groups.items():
    ls = g["listings"]
    rep = max(ls, key=lambda x: x["reviewCount"])   # レビュー最多＝人気の実機を代表に
    # 価格外れ値ガード: 代表機種の価格から2.2倍以上乖離するlistingは別モデル/中古/セット違いの誤マッチとみなし除外
    rp = rep["price"] or 1
    ls = [l for l in ls if rp / 2.2 <= l["price"] <= rp * 2.2] or [rep]
    tot_rc = sum(l["reviewCount"] for l in ls)
    # レビュー加重平均（listingをまとめる）
    if tot_rc > 0:
        avg = sum(l["review"] * l["reviewCount"] for l in ls if l["reviewCount"]) / tot_rc
    else:
        avg = rep["review"]
    # モール別に最安listingを1件ずつ → offers（最安値比較）
    offers = {}
    for l in ls:
        mall = l.get("mall", "rakuten")
        if mall not in offers or l["price"] < offers[mall]["price"]:
            offers[mall] = {"mall": mall, "price": l["price"], "url": l["url"], "affiliate": l["affiliate"]}
    offer_list = sorted(offers.values(), key=lambda o: o["price"])
    best = offer_list[0]   # 全モール横断の最安（アフィリ主導線）
    # 代表画像は楽天優先（画像URLが安定）→無ければ最初
    img = next((l["image"] for l in ls if l.get("mall") == "rakuten" and l.get("image")), rep.get("image", ""))
    models.append({"brand": g["brand"], "name": clean(rep["name"])[:60], "minPrice": best["price"],
                   "review": round(avg, 2), "reviewCount": tot_rc,
                   "affiliate": best["affiliate"], "image": img, "url": best["url"],
                   "offers": offer_list, "key": k})   # key=ブランド+型番の安定キー(URL生成用。商品名変更に影響されない)

# レビューが極端に少ない/無い機種は除外（信頼性）
models = [m for m in models if m["reviewCount"] >= 5]

# --- 満足度コスパ算出 ---
C = st.mean([m["review"] for m in models]); M = 50  # ベイズの事前
def bayes(m):
    v, R = m["reviewCount"], m["review"]
    return (v / (v + M)) * R + (M / (v + M)) * C
prices = [math.log10(m["minPrice"]) for m in models]
pm, ps = st.mean(prices), (st.pstdev(prices) or 1)
bs = [bayes(m) for m in models]
bmin, bmax = min(bs), max(bs)
for m in models:
    sat = (bayes(m) - bmin) / (bmax - bmin) * 100 if bmax > bmin else 50   # 満足度0-100
    cheap = max(0, min(100, 50 - 10 * (math.log10(m["minPrice"]) - pm) / ps + 50 - 50))  # placeholder
    cheap = max(0, min(100, 50 - 10 * (math.log10(m["minPrice"]) - pm) / ps))  # 安いほど高い(逆偏差値)
    cheap = cheap + 50  # 偏差値中心を50に
    cheap = max(0, min(100, 100 - (50 + 10 * (math.log10(m["minPrice"]) - pm) / ps)))  # 明快版:高価格ほど低い
    m["sat"] = round(sat, 1)
    m["cheap"] = round(cheap, 1)
    m["cospa"] = round(0.6 * sat + 0.4 * cheap, 1)
    m["bayes"] = round(bayes(m), 2)

models.sort(key=lambda m: m["cospa"], reverse=True)
for i, m in enumerate(models, 1):
    m["rank"] = i
json.dump(models, open(os.path.join(DATA, slug + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

print(f"機種数 {len(models)}  (raw {len(raw)}件→本体{len(items)}→機種{len(groups)}→レビュー5+ {len(models)})")
print(f"\n{'順':>2} {'コスパ':>5}{'満足':>5}{'安さ':>5} {'ベイズ★':>6}{'最安':>8}{'評価数':>6} 機種")
for m in models[:25]:
    print(f"{m['rank']:>2} {m['cospa']:>5}{m['sat']:>5}{m['cheap']:>5} {m['bayes']:>6}¥{m['minPrice']:>7,}{m['reviewCount']:>6}  [{m['brand'][:10]}] {m['name'][:30]}")
