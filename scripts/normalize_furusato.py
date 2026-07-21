# ふるさと納税の返礼品: 商品名から内容量(kg/本/ロール)を抽出→寄付額あたり単価→満足度×お得さでコスパ算出。
# カテゴリ設定は furusato_cats.py。単位(weight/count)ごとに抽出ロジックを切替。
import json, os, sys, re, math, statistics as st, unicodedata, hashlib
from furusato_cats import FCATS

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
slug = sys.argv[1] if len(sys.argv) > 1 else "rice"
cfg = FCATS[slug]
raw = json.load(open(os.path.join(DATA, f"furusato-{slug}_raw.json"), encoding="utf-8"))

def norm(s):
    return unicodedata.normalize("NFKC", s)

KG_MUL = re.compile(r"(\d+(?:\.\d+)?)\s*kg\s*[×xX＊*]\s*(\d+)")
G_MUL = re.compile(r"(\d+(?:\.\d+)?)\s*g\s*[×xX＊*]\s*(\d+)")
KG = re.compile(r"(\d+(?:\.\d+)?)\s*kg")
G = re.compile(r"(\d+(?:\.\d+)?)\s*g")   # 「1kg」の"g"は直前がkのため誤マッチしない

def amt_weight(name):   # → 総kg
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
    return vals[0] if len(vals) == 1 else None   # 複数重量(選べる等)は曖昧→スキップ

def amt_count(name, noun):   # → 総数(本/ロール)
    n = norm(name)
    mul = re.findall(rf"(\d+)\s*{noun}\s*[×xX＊*]\s*(\d+)", n)   # 12ロール×8, 24本×2
    if mul:
        return max(int(a) * int(b) for a, b in mul)
    cnts = sorted({int(x) for x in re.findall(rf"(\d+)\s*{noun}", n)})
    # 最大数量を採用。過大カウント(選べる/○相当)は単価が非現実的に安くなり min_unit で除外される
    return cnts[-1] if cnts else None

def amount(name):
    if cfg["unit"] == "weight":
        return amt_weight(name)
    return amt_count(name, cfg["count_noun"])

items = []
for r in raw:
    nm = r["name"]
    if any(x in nm for x in cfg["exclude"]):
        continue
    if not any(x in nm for x in cfg["include"]):
        continue
    if not r["price"] or r["reviewCount"] < cfg["min_review"]:
        continue
    amt = amount(nm)
    if not amt:
        continue
    unit = r["price"] / amt
    if unit < cfg["min_unit"] or unit > cfg["max_unit"]:
        continue
    r["amt"] = round(amt, 1); r["unit"] = round(unit)
    items.append(r)

# 重複除去: ショップ+内容量+単価帯でまとめ、レビュー最多を代表に
groups = {}
for r in items:
    key = r["shop"] + "|" + str(r["amt"]) + "|" + str(round(r["unit"] / (r["unit"] * 0.05 + 1)))
    groups.setdefault(r["shop"] + "|" + str(r["amt"]) + "|" + str(round(r["unit"] / 50)), []).append(r)
models = [max(g, key=lambda x: x["reviewCount"]) for g in groups.values()]

C = st.mean([m["review"] for m in models]); M = 50
def bayes(m):
    v, R = m["reviewCount"], m["review"]
    return (v / (v + M)) * R + (M / (v + M)) * C
us_ = [math.log10(m["unit"]) for m in models]
um, usd = st.mean(us_), (st.pstdev(us_) or 1)
bs = [bayes(m) for m in models]; bmin, bmax = min(bs), max(bs)
for m in models:
    sat = (bayes(m) - bmin) / (bmax - bmin) * 100 if bmax > bmin else 50
    toku = max(0, min(100, 100 - (50 + 10 * (math.log10(m["unit"]) - um) / usd)))
    m["sat"] = round(sat, 1); m["toku"] = round(toku, 1)
    m["cospa"] = round(0.5 * sat + 0.5 * toku, 1)
    m["bayes"] = round(bayes(m), 2)
    m["id"] = "fr" + hashlib.md5((m["shop"] + m["name"]).encode()).hexdigest()[:8]
    m["name"] = re.sub(r"【ふるさと納税】", "", m["name"]).strip()[:70]

models.sort(key=lambda m: m["cospa"], reverse=True)
for i, m in enumerate(models, 1):
    m["rank"] = i
keep = ["id", "rank", "name", "price", "amt", "unit", "review", "reviewCount", "sat", "toku", "cospa", "bayes", "shop", "image", "affiliate", "url"]
out = [{k: m[k] for k in keep} for m in models]
json.dump(out, open(os.path.join(DATA, f"furusato-{slug}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

print(f"[{cfg['label']}] 返礼品数 {len(models)}  (raw {len(raw)}→本体{len(items)}→重複除去{len(models)})  単位={cfg['unit_label']}")
for m in models[:12]:
    print(f"  {m['rank']:>2} コスパ{m['cospa']:>5} ¥{m['price']:>6,} {m['amt']}{cfg['suffix']} {m['unit']:>6,}{cfg['unit_label']} ★{m['review']}({m['reviewCount']}) {m['name'][:26]}")
