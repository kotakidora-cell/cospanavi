# PoC: ふるさと納税の「実質還元率」を推定する。
#   実質還元率(%) = 想定市場価格 ÷ 寄付額 × 100
#   想定市場価格 = 通常楽天の「市場円/kg(銘柄別)」 × 返礼品の総量kg
# ポータルが規制で出せない指標を、楽天通常商品APIの相場から自動推定できるかの検証。
# 使い方: python poc_kanpu.py [slug=rice]
import json, os, sys, re, statistics as st, unicodedata
from fetch_rakuten import fetch  # 通常楽天商品検索(genreId+keyword)

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")

def norm(s):
    return unicodedata.normalize("NFKC", s)

KG_MUL = re.compile(r"(\d+(?:\.\d+)?)\s*kg\s*[×xX＊*]\s*(\d+)")
G_MUL = re.compile(r"(\d+(?:\.\d+)?)\s*g\s*[×xX＊*]\s*(\d+)")
KG = re.compile(r"(\d+(?:\.\d+)?)\s*kg")
G = re.compile(r"(\d+(?:\.\d+)?)\s*g")

def amt_weight(name):  # → 総kg (normalize_furusatoと同ロジック)
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

# 米の銘柄バケツ(市場相場を銘柄別に取り、返礼品とマッチさせて精度を上げる)
RICE_BRANDS = ["ゆめぴりか", "つや姫", "ミルキークイーン", "コシヒカリ", "あきたこまち", "ひとめぼれ",
               "ななつぼし", "はえぬき", "ヒノヒカリ", "森のくまさん", "きぬむすめ", "だわら", "無洗米", "玄米"]
NOISE = ["米びつ", "米油", "パックご飯", "パックライス", "レトルト", "おにぎり", "飼料", "ペット",
         "米粉", "餅", "もち", "化粧", "石鹸", "保存容器", "計量", "米袋", "のぼり", "japan", "せんべい"]

def market_benchmarks(genre=201184, pages=8):
    """通常楽天から米を取得→円/kg分布→全体中央値＋銘柄別中央値を返す"""
    rows = []
    for kw in ["無洗米 10kg", "精米 5kg", "コシヒカリ 玄米"]:  # 幅広く相場を拾う
        for it in fetch(kw, pages=pages, genreId=genre):
            nm = it["name"]
            if "ふるさと納税" in nm or "ふるさと" in nm:
                continue
            if any(x in nm for x in NOISE):
                continue
            kg = amt_weight(nm)
            if not kg or not it["price"]:
                continue
            ppk = it["price"] / kg
            if 200 <= ppk <= 1500:  # 妥当な米の円/kgレンジ(送料込み相場)
                rows.append((ppk, norm(nm)))
    allppk = [r[0] for r in rows]
    overall = st.median(allppk) if allppk else 550
    bench = {}
    for b in RICE_BRANDS:
        v = [p for p, n in rows if b in n]
        if len(v) >= 4:
            bench[b] = st.median(v)
    return overall, bench, len(rows), allppk

def market_ppk(name, overall, bench):
    n = norm(name)
    for b in RICE_BRANDS:  # 高級銘柄を優先的にマッチ(リスト前方が高単価)
        if b in n and b in bench:
            return bench[b], b
    return overall, "全体"

def main():
    slug = sys.argv[1] if len(sys.argv) > 1 else "rice"
    print(f"=== 実質還元率PoC: {slug} ===")
    overall, bench, n, allppk = market_benchmarks()
    q1, q3 = (st.quantiles(allppk, n=4)[0], st.quantiles(allppk, n=4)[2]) if len(allppk) >= 4 else (0, 0)
    print(f"市場相場サンプル {n}件  中央値 {overall:.0f}円/kg  (25-75%: {q1:.0f}〜{q3:.0f})")
    print("銘柄別 市場円/kg:", {k: round(v) for k, v in sorted(bench.items(), key=lambda z: -z[1])})
    fr = json.load(open(os.path.join(DATA, f"furusato-{slug}.json"), encoding="utf-8"))
    out = []
    for m in fr:
        amt = m.get("amt")
        if not amt or not m.get("price"):
            continue
        ppk, matched = market_ppk(m["name"], overall, bench)
        mv = ppk * amt          # 想定市場価格
        rate = mv / m["price"] * 100
        out.append((rate, mv, ppk, matched, m))
    out.sort(key=lambda z: -z[0])
    print(f"\n返礼品 {len(out)}件を実質還元率で推定。総務省ルール(調達≤30%)に対し、小売相場基準なので通常30〜60%が目安。\n")
    print("順位 還元率 想定市場価 寄付額 総量kg 相場円/kg(銘柄) 商品")
    for i, (rate, mv, ppk, mt, m) in enumerate(out[:15], 1):
        print(f"{i:2} {rate:5.0f}% {mv:8,.0f}円 {m['price']:7,}円 {m['amt']:5}kg {ppk:4.0f}({mt}) | {m['name'][:30]}")
    rates = [r for r, *_ in out]
    print(f"\n分布: 中央値{st.median(rates):.0f}% / 最大{max(rates):.0f}% / 最小{min(rates):.0f}%")
    hi = sum(1 for r in rates if r >= 50)
    print(f"還元率50%以上(小売比で特にお得)= {hi}件 / {len(rates)}件")

if __name__ == "__main__":
    main()
