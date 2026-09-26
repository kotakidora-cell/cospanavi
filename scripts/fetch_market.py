# ふるさと返礼品の「実質還元率」推定用に、通常楽天商品APIから市場相場(銘柄別 円/kg)を取得しキャッシュ。
#   data/market_bench.json = {slug: {unit, overall, brands:{...}, order:[...], n, asof}}
# 取得サンプルが少ない場合は既存キャッシュを保持(no-clobber)＝日次で相場が壊れない。
# 使い方: python fetch_market.py [slug ...]   (省略時はMARKET全カテゴリ)
import json, os, sys, re, statistics as st, unicodedata, datetime
from fetch_rakuten import fetch

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
CACHE = os.path.join(DATA, "market_bench.json")

def norm(s):
    return unicodedata.normalize("NFKC", s)

KG_MUL = re.compile(r"(\d+(?:\.\d+)?)\s*kg\s*[×xX＊*]\s*(\d+)")
G_MUL = re.compile(r"(\d+(?:\.\d+)?)\s*g\s*[×xX＊*]\s*(\d+)")
KG = re.compile(r"(\d+(?:\.\d+)?)\s*kg")
G = re.compile(r"(\d+(?:\.\d+)?)\s*g")

def amt_weight(name):
    n = norm(name)
    m = KG_MUL.findall(n)
    if m:
        return max(float(a) * int(b) for a, b in m)
    m = G_MUL.findall(n)
    if m:
        return max(float(a) * int(b) for a, b in m) / 1000
    kgs = {round(float(x), 3) for x in KG.findall(n) if 0.1 <= float(x) <= 50}
    gs = {round(float(x) / 1000, 3) for x in G.findall(n) if 50 <= float(x) <= 50000}
    vals = sorted(kgs | gs)
    return vals[0] if len(vals) == 1 else None

# カテゴリ別の相場取得設定。orderは前方ほど高単価銘柄(返礼品マッチ時に優先)。
MARKET = {
    "rice": {
        "genre": 201184, "unit": "weight", "ppk_min": 200, "ppk_max": 1500,
        "keywords": ["無洗米 10kg", "精米 5kg", "コシヒカリ 玄米", "あきたこまち 5kg"],
        "order": ["ゆめぴりか", "つや姫", "ミルキークイーン", "コシヒカリ", "あきたこまち", "ひとめぼれ",
                  "ななつぼし", "はえぬき", "ヒノヒカリ", "森のくまさん", "きぬむすめ", "無洗米", "玄米"],
        "noise": ["米びつ", "米油", "パックご飯", "パックライス", "レトルト", "おにぎり", "飼料", "ペット",
                  "米粉", "餅", "もち", "化粧", "石鹸", "保存容器", "計量", "米袋", "のぼり", "せんべい"],
    },
}

def bench_for(slug, cfg, pages=6):
    rows = []
    for kw in cfg["keywords"]:
        for it in fetch(kw, pages=pages, genreId=cfg["genre"]):
            nm = it["name"]
            if "ふるさと" in nm or any(x in nm for x in cfg["noise"]):
                continue
            amt = amt_weight(nm) if cfg["unit"] == "weight" else None
            if not amt or not it["price"]:
                continue
            ppk = it["price"] / amt
            if cfg["ppk_min"] <= ppk <= cfg["ppk_max"]:
                rows.append((ppk, norm(nm)))
    if len(rows) < 30:
        return None  # サンプル不足→呼び出し側で既存キャッシュ保持
    allppk = [p for p, _ in rows]
    brands = {}
    for b in cfg["order"]:
        v = [p for p, n in rows if b in n]
        if len(v) >= 4:
            brands[b] = round(st.median(v))
    return {"unit": cfg["unit"], "overall": round(st.median(allppk)), "brands": brands,
            "order": cfg["order"], "n": len(rows), "asof": datetime.date.today().isoformat()}

def main():
    slugs = sys.argv[1:] or list(MARKET)
    cache = {}
    if os.path.exists(CACHE):
        cache = json.load(open(CACHE, encoding="utf-8"))
    for slug in slugs:
        if slug not in MARKET:
            print(f"  {slug}: MARKET未定義スキップ"); continue
        b = bench_for(slug, MARKET[slug])
        if b:
            cache[slug] = b
            print(f"  {slug}: 相場{b['n']}件 中央値{b['overall']}円/{'kg' if b['unit']=='weight' else 'L'} "
                  f"銘柄{len(b['brands'])}種 更新")
        else:
            print(f"  {slug}: サンプル不足→既存キャッシュ保持")
    json.dump(cache, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"保存: {CACHE}")

if __name__ == "__main__":
    main()
