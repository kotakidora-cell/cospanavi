# 家電コスパランキングのYouTube Short(縦型1080x1920,約23秒)を生成。
# 家電は「最安値・コスパ値」主役(ふるさと版の円/kgとは別)。描画部品はmake_furusato_shortを再利用。
# 使い方: python make_product_short.py <slug(例:microwave)>
import json, os, sys, tempfile
from PIL import ImageDraw
from make_furusato_short import (font, ctext, tsize, wrap, vgrad, rrect, paste_card, dl_image,
                                 build_video, W, H, ORANGE, PINK, YEL, NAVY, WHITE)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
PCATS = {"microwave": "電子レンジ", "hair-dryer": "ドライヤー", "humidifier": "加湿器",
         "tablet": "タブレット", "air-purifier": "空気清浄機", "robot-cleaner": "ロボット掃除機",
         "earbuds": "ワイヤレスイヤホン", "monitor": "モニター", "kettle": "電気ケトル"}

def bg_scene(c1, c2):
    from PIL import Image
    img = vgrad(c1, c2)
    return img, ImageDraw.Draw(img)

def scene_intro(label):
    img, d = bg_scene((255, 138, 76), (255, 92, 138))
    rrect(d, [W/2-260, 150, W/2+260, 250], 50, fill=WHITE)
    ctext(d, W/2, 168, "家電のコスパ比較", font(48), ORANGE)
    ctext(d, W/2, 430, "コスパ", font(170), WHITE, stroke=8, sfill=NAVY)
    ctext(d, W/2, 620, "ランキング", font(150), YEL, stroke=8, sfill=NAVY)
    rrect(d, [W/2-400, 850, W/2+400, 1000], 40, fill=NAVY)
    ctext(d, W/2, 872, f"【{label}編】", font(88), WHITE)
    ctext(d, W/2, 1080, "TOP3", font(240), WHITE, stroke=10, sfill=ORANGE)
    ctext(d, W/2, 1420, "安くて満足度が高いのは？", font(56), WHITE, stroke=4, sfill=NAVY)
    ctext(d, W/2, 1500, "損しない1台はコレ", font(56), WHITE, stroke=4, sfill=NAVY)
    ctext(d, W/2, 1760, "コスパナビ", font(60), WHITE, stroke=4, sfill=NAVY)
    return img

def scene_rank(rank, m):
    cols = {3: ((120, 170, 255), (90, 130, 220)), 2: ((190, 195, 205), (150, 155, 170)),
            1: ((255, 200, 70), (255, 150, 40))}
    img, d = bg_scene(*cols[rank])
    bx, by = 175, 250
    d.ellipse([bx-130, by-130, bx+130, by+130], fill=NAVY)
    ctext(d, bx, by-95, "第", font(48), WHITE)
    ctext(d, bx, by-55, str(rank), font(150), YEL)
    ctext(d, bx, by+78, "位", font(40), WHITE)
    if rank == 1:
        d.polygon([(W/2-140, 470), (W/2-70, 560), (W/2, 470), (W/2+70, 560), (W/2+140, 470),
                   (W/2+110, 620), (W/2-110, 620)], fill=YEL, outline=NAVY)
    paste_card(img, m["_img"], W/2, 800, 520)
    # ブランド(ノーブランドは非表示)
    y = 1110
    br = m["brand"]
    if "ノーブランド" not in br:
        ctext(d, W/2, y, br[:16], font(44), (90, 90, 100)); y += 60
    for line in wrap(m["name"], 15):
        y = ctext(d, W/2, y, line, font(48), NAVY) + 8
    # ヒーロー: 最安値
    rrect(d, [90, 1310, W-90, 1560], 44, fill=WHITE)
    ctext(d, W/2, 1325, "最安値", font(42), (120, 120, 130))
    pr = f"{m['minPrice']:,}"
    ctext(d, W/2, 1372, pr, font(160), ORANGE)
    pw, _ = tsize(d, pr, font(160))
    d.text((W/2 + pw/2 + 12, 1450), "円〜", font=font(56), fill=NAVY)
    # コスパ値 + レビュー
    star = "★" * round(m['review'])
    ctext(d, W/2, 1620, f"{star} {m['review']:.2f}（{m['reviewCount']:,}件）", font(48), (230, 90, 30), stroke=3, sfill=WHITE)
    rrect(d, [W/2-160, 1710, W/2+160, 1795], 42, fill=NAVY)
    ctext(d, W/2, 1722, f"コスパ {round(m['cospa'])}", font(50), YEL)
    return img

def scene_outro(label, slug):
    img, d = bg_scene((255, 138, 76), (255, 92, 138))
    ctext(d, W/2, 300, "全順位＆他の家電も", font(64), WHITE, stroke=4, sfill=NAVY)
    ctext(d, W/2, 400, "コチラ！", font(120), WHITE, stroke=6, sfill=NAVY)
    rrect(d, [50, 650, W-50, 1010], 50, fill=WHITE)
    ctext(d, W/2, 700, "コスパナビ", font(72), NAVY)
    ctext(d, W/2, 810, "cospa-navi.com", font(100), ORANGE)
    rrect(d, [W/2-470, 1150, W/2+470, 1300], 40, fill=NAVY)
    ctext(d, W/2, 1178, "▼ リンクは 概要欄・コメント欄", font(50), YEL)
    ctext(d, W/2, 1420, "満足度×価格で選べる", font(58), WHITE, stroke=4, sfill=NAVY)
    ctext(d, W/2, 1500, "調整できるコスパ比較ツール", font(52), WHITE, stroke=4, sfill=NAVY)
    return img

def main():
    slug = sys.argv[1] if len(sys.argv) > 1 else "microwave"
    outdir = os.path.join(BASE, "shorts"); os.makedirs(outdir, exist_ok=True)
    label = PCATS.get(slug, slug)
    data = json.load(open(os.path.join(DATA, f"{slug}.json"), encoding="utf-8"))
    top = sorted(data, key=lambda z: -z["cospa"])[:3]
    for m in top:
        m["_img"] = dl_image(m.get("image", ""))
    scenes = [(scene_intro(label), 3.0),
              (scene_rank(3, top[2]), 5.0), (scene_rank(2, top[1]), 5.0),
              (scene_rank(1, top[0]), 7.0), (scene_outro(label, slug), 5.0)]
    tmp = tempfile.mkdtemp(); pngs, durs = [], []
    for i, (im, du) in enumerate(scenes):
        p = os.path.join(tmp, f"s{i}.png"); im.save(p); pngs.append(p); durs.append(du)
    bgm = os.path.join(outdir, "bgm.mp3")
    out = os.path.join(outdir, f"{slug}-top3.mp4")
    build_video(pngs, durs, out, bgm=bgm if os.path.exists(bgm) else None)
    print(f"生成: {out}  ({sum(durs):.0f}秒, BGM={'有' if os.path.exists(bgm) else '無'})")
    scenes[3][0].save(os.path.join(outdir, f"{slug}-frame1.png"))

if __name__ == "__main__":
    main()
