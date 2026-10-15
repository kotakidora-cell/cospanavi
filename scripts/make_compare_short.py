# 「〇〇 vs 〇〇 徹底比較」のYouTube Short(縦1080x1920,約22秒)を生成。
# compares.pyのCOMPARESから対決を取り、各ブランドの現在の最コスパ機種を自動注入してVS動画化。
# 使い方: python make_compare_short.py <compare-slug(例:earbuds-airpods-vs-anker)>
import json, os, sys, tempfile
from PIL import ImageDraw
from make_furusato_short import (font, ctext, tsize, wrap, vgrad, rrect, paste_card, dl_image,
                                 build_video, W, H, ORANGE, PINK, YEL, NAVY, WHITE)
from compares import COMPARES

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
# 家電カテゴリの日本語ラベル(make_product_shortと同じ主要分)
CATLABEL = {"earbuds": "ワイヤレスイヤホン", "robot-cleaner": "ロボット掃除機", "portable-power": "ポータブル電源",
            "hair-dryer": "ドライヤー", "air-purifier": "空気清浄機", "tablet": "タブレット",
            "coffee-maker": "コーヒーメーカー", "smartwatch": "スマートウォッチ", "kettle": "電気ケトル"}


def top_model(data, match, name_incl=None, name_excl=None):
    cand = [m for m in data if match in m["brand"]]
    if name_excl:
        cand = [m for m in cand if not any(t.lower() in m["name"].lower() for t in name_excl)] or cand
    if name_incl:
        cand = [m for m in cand if any(t.lower() in m["name"].lower() for t in name_incl)] or cand
    return max(cand, key=lambda m: m["cospa"]) if cand else None


def bg(c1, c2):
    img = vgrad(c1, c2)
    return img, ImageDraw.Draw(img)


def scene_intro(label, na, nb):
    img, d = bg((255, 138, 76), (255, 92, 138))
    rrect(d, [W/2-320, 150, W/2+320, 250], 50, fill=WHITE)
    ctext(d, W/2, 170, f"{label} コスパ比較", font(44), ORANGE)
    ctext(d, W/2, 430, na, font(130), WHITE, stroke=8, sfill=NAVY)
    ctext(d, W/2, 620, "vs", font(110), YEL, stroke=6, sfill=NAVY)
    ctext(d, W/2, 760, nb, font(130), WHITE, stroke=8, sfill=NAVY)
    ctext(d, W/2, 1060, "コスパ最強は", font(70), WHITE, stroke=5, sfill=NAVY)
    ctext(d, W/2, 1160, "どっち？", font(150), YEL, stroke=8, sfill=NAVY)
    ctext(d, W/2, 1500, "価格・満足度・機能で直接対決", font(52), WHITE, stroke=4, sfill=NAVY)
    ctext(d, W/2, 1760, "コスパナビ", font(60), WHITE, stroke=4, sfill=NAVY)
    return img


def card(img, d, cx, m, name, col):
    paste_card(img, m["_img"], cx, 560, 420)
    bw = tsize(d, name, font(42))[0]
    rrect(d, [cx-bw/2-24, 300, cx+bw/2+24, 372], 34, fill=col)
    ctext(d, cx, 312, name, font(42), WHITE)
    y = 820
    for line in wrap(m["name"], 11):
        y = ctext(d, cx, y, line, font(40), NAVY) + 6
    rrect(d, [cx-215, 1010, cx+215, 1130], 36, fill=WHITE)
    ctext(d, cx, 1022, "最安値", font(34), (120, 120, 130))
    ctext(d, cx, 1058, f"¥{m['minPrice']:,}", font(60), ORANGE)
    rrect(d, [cx-120, 1170, cx+120, 1250], 40, fill=NAVY)
    ctext(d, cx, 1182, f"コスパ {round(m['cospa'])}", font(46), YEL)
    star = "★" * round(m['review'])
    ctext(d, cx, 1285, f"{m['review']:.2f}（{m['reviewCount']:,}）", font(36), (230, 90, 30), stroke=3, sfill=WHITE)


def scene_vs(la, ma, lb, mb):
    img, d = bg((150, 190, 255), (120, 150, 230))
    ctext(d, W/2, 120, "コスパで直接対決", font(64), WHITE, stroke=4, sfill=NAVY)
    card(img, d, 290, ma, la, (60, 100, 220))
    card(img, d, 790, mb, lb, ORANGE)
    d.ellipse([W/2-85, 520-85, W/2+85, 520+85], fill=NAVY, outline=WHITE, width=6)
    ctext(d, W/2, 468, "VS", font(80), YEL)
    ctext(d, W/2, 1420, "数字はすべて最新の実データ", font(46), WHITE, stroke=4, sfill=NAVY)
    ctext(d, W/2, 1500, "毎日自動更新", font(60), YEL, stroke=5, sfill=NAVY)
    ctext(d, W/2, 1770, "コスパナビ", font(56), WHITE, stroke=4, sfill=NAVY)
    return img


def scene_verdict(va, vb, na, nb):
    img, d = bg((255, 138, 76), (255, 92, 138))
    ctext(d, W/2, 220, "結論", font(150), WHITE, stroke=8, sfill=NAVY)
    rrect(d, [70, 520, W-70, 820], 40, fill=WHITE)
    ctext(d, W/2, 560, va, font(50), (90, 90, 100))
    ctext(d, W/2, 660, f"→ {na}", font(84), (60, 100, 220))
    rrect(d, [70, 900, W-70, 1200], 40, fill=WHITE)
    ctext(d, W/2, 940, vb, font(50), (90, 90, 100))
    ctext(d, W/2, 1040, f"→ {nb}", font(84), ORANGE)
    ctext(d, W/2, 1360, "全順位＆比較表はサイトで", font(56), WHITE, stroke=4, sfill=NAVY)
    ctext(d, W/2, 1760, "コスパナビ", font(60), WHITE, stroke=4, sfill=NAVY)
    return img


def scene_cta():
    img, d = bg((255, 138, 76), (255, 92, 138))
    ctext(d, W/2, 320, "どっちも最新価格で", font(64), WHITE, stroke=4, sfill=NAVY)
    ctext(d, W/2, 410, "比較できる", font(120), WHITE, stroke=6, sfill=NAVY)
    rrect(d, [50, 650, W-50, 1010], 50, fill=WHITE)
    ctext(d, W/2, 700, "コスパナビ", font(72), NAVY)
    ctext(d, W/2, 810, "cospa-navi.com", font(100), ORANGE)
    rrect(d, [W/2-470, 1150, W/2+470, 1300], 40, fill=NAVY)
    ctext(d, W/2, 1178, "▼ リンクは 概要欄・コメント欄", font(50), YEL)
    ctext(d, W/2, 1450, "満足度×価格で選べる", font(56), WHITE, stroke=4, sfill=NAVY)
    ctext(d, W/2, 1530, "徹底比較ページへ", font(56), WHITE, stroke=4, sfill=NAVY)
    return img


def main():
    slug = sys.argv[1] if len(sys.argv) > 1 else "earbuds-airpods-vs-anker"
    c = next((x for x in COMPARES if x["slug"] == slug), None)
    if not c:
        print("該当の比較slugが見つかりません:", slug); sys.exit(1)
    data = json.load(open(os.path.join(DATA, f"{c['category']}.json"), encoding="utf-8"))
    label = CATLABEL.get(c["category"], c["category"])
    picks = []
    for b in c["brands"]:
        m = top_model(data, b["match"], b.get("name_incl"), b.get("name_excl"))
        if m:
            m = dict(m); m["_img"] = dl_image(m.get("image", "")); m["_bn"] = b["name"]
            picks.append(m)
    if len(picks) < 2:
        print("ブランド2つ分の機種が取れませんでした"); sys.exit(1)
    (ma, mb) = picks[0], picks[1]
    # 短い対決名(タイトル "A vs B" から)
    t = c["title"].split("｜")[0].replace("徹底比較", "").strip()
    na, nb = (t.split(" vs ") + ["A", "B"])[:2] if " vs " in t else (ma["_bn"], mb["_bn"])
    na, nb = na.strip()[:7], nb.strip()[:7]
    va = c.get("short_a", "連携・所有感なら")
    vb = c.get("short_b", "コスパ重視なら")
    outdir = os.path.join(BASE, "shorts"); os.makedirs(outdir, exist_ok=True)
    scenes = [(scene_intro(label, na, nb), 4.5), (scene_vs(na, ma, nb, mb), 7.0),
              (scene_verdict(va, vb, na, nb), 5.5), (scene_cta(), 4.5)]
    tmp = tempfile.mkdtemp(); pngs, durs = [], []
    for i, (im, du) in enumerate(scenes):
        p = os.path.join(tmp, f"s{i}.png"); im.save(p); pngs.append(p); durs.append(du)
    bgm = os.path.join(outdir, "bgm.mp3")
    out = os.path.join(outdir, f"compare-{slug}.mp4")
    build_video(pngs, durs, out, bgm=bgm if os.path.exists(bgm) else None)
    print(f"生成: {out} ({sum(durs):.0f}秒)")
    scenes[1][0].save(os.path.join(outdir, f"compare-{slug}-frame.png"))


if __name__ == "__main__":
    main()
