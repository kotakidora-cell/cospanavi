# 料率ウォッチ: 全ふるさと生データから「料率が跳ねた返礼品」を検出して記録。
# 楽天イベント(お買い物マラソン/スーパーSALE)や復興支援で affRate は一時的に上がる(通常3-4%→10-15%)。
# 高料率×高寄付額=報酬インパクト大。取りこぼし防止のため日次で data/rate_watch.json に記録＆表示。
import json, os, glob, sys, datetime
sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")

THRESH = 6.0   # ベース3-4%超え=イベント等で跳ねた候補
TOPN = 60

def slug_of(path):
    b = os.path.basename(path)
    return b[len("furusato-"):-len("_raw.json")]

def main():
    hits = []
    for f in glob.glob(os.path.join(DATA, "furusato-*_raw.json")):
        slug = slug_of(f)
        if slug in ("local",):
            continue
        try:
            raw = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        for r in raw:
            ar = float(r.get("affRate") or 0)
            if ar >= THRESH and r.get("price"):
                hits.append({"slug": slug, "affRate": ar, "price": r["price"],
                             "impact": round(r["price"] * ar / 100),  # 1成約あたり想定報酬
                             "name": r["name"].replace("【ふるさと納税】", "").strip()[:60],
                             "shop": r.get("shop", ""), "review": r.get("review", 0),
                             "reviewCount": r.get("reviewCount", 0),
                             "affiliate": r.get("affiliate") or r.get("url", "")})
    # 報酬インパクト(料率×寄付額)順
    hits.sort(key=lambda z: -z["impact"])
    hits = hits[:TOPN]
    out = {"asof": datetime.date.today().isoformat(), "threshold": THRESH, "count": len(hits), "items": hits}
    json.dump(out, open(os.path.join(DATA, "rate_watch.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"[rate_watch] {out['asof']} 料率{THRESH}%以上の返礼品: {len(hits)}件")
    if hits:
        print("  想定報酬(料率×寄付額)の大きい順 TOP15:")
        for h in hits[:15]:
            print(f"   料率{h['affRate']:>4}% 報酬目安¥{h['impact']:>5,} 寄付¥{h['price']:>6,} [{h['slug']}] {h['name'][:34]}")
    else:
        print("  → 現在は全返礼品がベース料率(3-4%)。楽天イベント開催時に跳ねた返礼品がここに出ます。")

if __name__ == "__main__":
    main()
