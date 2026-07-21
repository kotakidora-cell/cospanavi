# ふるさと納税の返礼品: 商品名から内容量(kg)を抽出→寄付額あたり単価(円/kg)→満足度×お得さでコスパ算出。
import json, os, sys, re, math, statistics as st, unicodedata, hashlib

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
slug = sys.argv[1] if len(sys.argv) > 1 else "rice"
raw = json.load(open(os.path.join(DATA, f"furusato-{slug}_raw.json"), encoding="utf-8"))

# 米以外・単価が量で測れない物を除外
EXCLUDE = ["豚", "牛", "鶏", "肉", "おかず", "パックご飯", "パックライス", "レトルト", "米粉", "餅", "もち",
           "日本酒", "焼酎", "味噌", "パン", "スイーツ", "菓子", "ペットフード", "玄米茶", "米油", "甘酒",
           "せんべい", "米菓", "食器", "米びつ", "保存容器", "ナッツ", "しらす", "海老", "エビ", "えび",
           "カニ", "かに", "蟹", "牡蠣", "ホタテ", "帆立", "明太子", "いくら", "うなぎ", "鰻", "貝", "干物"]
# 重量が複数表記の品(選べる/食べ比べ等)はtotal_kgがNone判定で自動スキップするので語での除外は不要
# 米であることを担保する語（いずれか含む）
RICE_OK = ["米", "無洗米", "精米", "白米", "玄米", "新米", "コシヒカリ", "ひとめぼれ", "あきたこまち",
           "ゆめぴりか", "ななつぼし", "はえぬき", "つや姫", "ミルキークイーン", "森のくまさん", "おぼろづき",
           "ふっくりんこ", "さがびより", "ヒノヒカリ", "きぬむすめ", "夢しずく", "ゆきむすび", "だわら"]

def norm(s):
    return unicodedata.normalize("NFKC", s)

KG_MUL = re.compile(r"(\d+(?:\.\d+)?)\s*kg\s*[×xX＊*]\s*(\d+)")   # 5kg×2, 5kg×6(回)
KG = re.compile(r"(\d+(?:\.\d+)?)\s*kg")

def total_kg(name):
    n = norm(name)
    # 「5kg×6回」等の定期便/セット: kg×回数 = 総量
    muls = KG_MUL.findall(n)
    if muls:
        return max(float(a) * int(b) for a, b in muls)
    kgs = sorted({float(x) for x in KG.findall(n) if 1 <= float(x) <= 100})
    if len(kgs) != 1:   # 0個=不明、複数=重量が曖昧(選べる等)→スキップ
        return None
    return kgs[0]

items = []
for r in raw:
    nm = r["name"]
    if any(x in nm for x in EXCLUDE):
        continue
    if not any(x in nm for x in RICE_OK):   # 米と確認できる語が無ければ除外
        continue
    if not r["price"] or r["reviewCount"] < 10:
        continue
    kg = total_kg(nm)
    if not kg:
        continue
    unit = r["price"] / kg   # 円/kg
    if unit < 500 or unit > 2200:   # 抽出ミス/外れ値を除外(米ふるさと納税は概ね¥700-1800/kg)
        continue
    r["kg"] = round(kg, 1); r["unit"] = round(unit)
    items.append(r)

# 重複除去: ショップ+kg+単価帯でまとめ、レビュー最多を代表に
groups = {}
for r in items:
    key = r["shop"] + "|" + str(r["kg"]) + "|" + str(round(r["unit"] / 50))
    g = groups.setdefault(key, [])
    g.append(r)
models = [max(g, key=lambda x: x["reviewCount"]) for g in groups.values()]

# 満足度(ベイズ) × お得さ(円/kgの逆偏差値)
C = st.mean([m["review"] for m in models]); M = 50
def bayes(m):
    v, R = m["reviewCount"], m["review"]
    return (v / (v + M)) * R + (M / (v + M)) * C
units = [math.log10(m["unit"]) for m in models]
um, us = st.mean(units), (st.pstdev(units) or 1)
bs = [bayes(m) for m in models]; bmin, bmax = min(bs), max(bs)
for m in models:
    sat = (bayes(m) - bmin) / (bmax - bmin) * 100 if bmax > bmin else 50
    toku = max(0, min(100, 100 - (50 + 10 * (math.log10(m["unit"]) - um) / us)))  # 単価安いほど高い
    m["sat"] = round(sat, 1); m["toku"] = round(toku, 1)
    m["cospa"] = round(0.5 * sat + 0.5 * toku, 1)
    m["bayes"] = round(bayes(m), 2)
    m["id"] = "fr" + hashlib.md5((m["shop"] + m["name"]).encode()).hexdigest()[:8]
    m["name"] = re.sub(r"【ふるさと納税】", "", m["name"]).strip()[:70]

models.sort(key=lambda m: m["cospa"], reverse=True)
for i, m in enumerate(models, 1):
    m["rank"] = i
keep = ["id", "rank", "name", "price", "kg", "unit", "review", "reviewCount", "sat", "toku", "cospa", "bayes", "shop", "image", "affiliate", "url"]
out = [{k: m[k] for k in keep} for m in models]
json.dump(out, open(os.path.join(DATA, f"furusato-{slug}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

print(f"返礼品数 {len(models)}  (raw {len(raw)}→本体{len(items)}→重複除去{len(models)})")
print(f"\n{'順':>2} {'コスパ':>5}{'満足':>5}{'お得':>5}{'寄付':>8}{'kg':>5}{'円/kg':>6}{'評価数':>6} 返礼品")
for m in models[:20]:
    print(f"{m['rank']:>2} {m['cospa']:>5}{m['sat']:>5}{m['toku']:>5}¥{m['price']:>6,}{m['kg']:>5}{m['unit']:>6,}{m['reviewCount']:>6}  {m['name'][:30]}")
