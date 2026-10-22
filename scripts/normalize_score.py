# raw listing → 機種正規化(ブランド+型番) → 満足度コスパ値算出 → data/<slug>.json
import json, os, sys, re, math, statistics as st, urllib.parse, unicodedata

# 内容量(総ロール/総kg/総箱)を商品名から抽出 → 1単位あたり単価。unit指定カテゴリ(日用品)で使用。
def _norm(s): return unicodedata.normalize("NFKC", s)
_KG_MUL = re.compile(r"(\d+(?:\.\d+)?)\s*kg\s*[×xX＊*]\s*(\d+)")
_G_MUL = re.compile(r"(\d+(?:\.\d+)?)\s*g\s*[×xX＊*]\s*(\d+)")
_KG = re.compile(r"(\d+(?:\.\d+)?)\s*kg")
_G = re.compile(r"(\d+(?:\.\d+)?)\s*g")
def amt_weight(name):   # → 総kg
    n = _norm(name)
    m = _KG_MUL.findall(n)
    if m: return max(float(a) * int(b) for a, b in m)
    m = _G_MUL.findall(n)
    if m: return max(float(a) * int(b) for a, b in m) / 1000
    kgs = {round(float(x), 3) for x in _KG.findall(n) if 0.3 <= float(x) <= 60}
    gs = {round(float(x) / 1000, 3) for x in _G.findall(n) if 100 <= float(x) <= 60000}
    vals = sorted(kgs | gs)
    return vals[0] if len(vals) == 1 else None   # 複数重量(選べる等)は曖昧→スキップ
def amt_count(name, noun):   # → 総数(ロール/箱 等)。「8ロール×8」「60箱(5箱×12)」等に対応
    n = _norm(name)
    mul = re.findall(rf"(\d+)\s*{noun}\s*(?:入り|入|巻)?\s*[×xX＊*]\s*(\d+)", n)
    mul += re.findall(rf"(\d+)\s*{noun}\s*入り?\s*[（(]\s*(\d+)\s*(?:個|袋|箱|梱|ケース|パック|セット|Ｐ|P)", n)
    if mul: return max(int(a) * int(b) for a, b in mul)
    cnts = sorted({int(x) for x in re.findall(rf"(\d+)\s*{noun}", n)})
    return cnts[-1] if cnts else None

# Yahoo!ショッピングのアフィリ化(バリューコマース MyLink)。生Yahoo URLをVC計測URLに変換して成果を発生させる。
VC_YAHOO_SID, VC_YAHOO_PID = "3776612", "892664780"
def vc_yahoo(url):
    if not url:
        return url
    return ("https://ck.jp.ap.valuecommerce.com/servlet/referral?sid=" + VC_YAHOO_SID +
            "&pid=" + VC_YAHOO_PID + "&vc_url=" + urllib.parse.quote(url, safe=""))

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
slug = sys.argv[1] if len(sys.argv) > 1 else "robot-cleaner"
raw = json.load(open(os.path.join(DATA, slug + "_raw.json"), encoding="utf-8"))
for r in raw:
    r.setdefault("mall", "rakuten")
# 付属品除外語・ブランド正規化はカテゴリ毎に異なるためcategories.pyから取得
from categories import CATEGORIES
_cat = CATEGORIES[slug]
# Yahoo取得分があれば統合（複数モール最安値比較）。ただし rakuten_only のカテゴリ(日用品)は楽天のみで集計
_yahoo = os.path.join(DATA, slug + "_yahoo_raw.json")
if _cat.get("rakuten_only"):
    print("rakuten_only: Yahoo統合をスキップ(楽天のみで集計)")
elif os.path.exists(_yahoo):
    _yr = json.load(open(_yahoo, encoding="utf-8"))
    raw += _yr
    print(f"Yahoo統合: +{len(_yr)}件")
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
_minp = _cat.get("min_price", 3000)   # 価格下限(家電は3000既定、日用品は安いのでカテゴリ毎に引き下げ)
items = [r for r in raw if not any(x in r["name"] for x in EXCLUDE) and r["price"] and r["price"] >= _minp]
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
            aff = vc_yahoo(l["url"]) if mall == "yahoo" else l["affiliate"]   # Yahooはバリューコマースでアフィリ化
            offers[mall] = {"mall": mall, "price": l["price"], "url": l["url"], "affiliate": aff}
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

# --- 単価(1ロール/1kg/1箱あたり)算出: unit指定カテゴリ(日用品)のみ。これが他サイトとの差別化軸 ---
_unit = _cat.get("unit")
if _unit:
    _noun = _cat.get("count_noun", "個")
    _lo_u, _hi_u = _cat.get("min_unit", 0), _cat.get("max_unit", 10 ** 9)
    _kept = []
    for m in models:
        amt = amt_weight(m["name"]) if _unit == "weight" else amt_count(m["name"], _noun)
        if not amt:
            continue
        up = m["minPrice"] / amt
        if up < _lo_u or up > _hi_u:   # 単価が非現実的（内容量抽出ミス）は除外
            continue
        m["amt"] = round(amt, 1)
        m["unit"] = round(up)   # 1単位あたり単価（円/ロール・円/kg 等）
        _kept.append(m)
    models = _kept

# --- 満足度コスパ算出 ---
# 「お得さ」の軸は、unit指定カテゴリ(日用品)では“1単位あたり単価”、それ以外(家電)は最安値を使う
def _pv(m): return m["unit"] if _unit else m["minPrice"]
C = st.mean([m["review"] for m in models]); M = 50  # ベイズの事前
def bayes(m):
    v, R = m["reviewCount"], m["review"]
    return (v / (v + M)) * R + (M / (v + M)) * C
prices = [math.log10(_pv(m)) for m in models]
pm, ps = st.mean(prices), (st.pstdev(prices) or 1)
bs = [bayes(m) for m in models]
bmin, bmax = min(bs), max(bs)
for m in models:
    sat = (bayes(m) - bmin) / (bmax - bmin) * 100 if bmax > bmin else 50   # 満足度0-100
    cheap = max(0, min(100, 100 - (50 + 10 * (math.log10(_pv(m)) - pm) / ps)))  # 単価/価格が安いほど高い(逆偏差値)
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
