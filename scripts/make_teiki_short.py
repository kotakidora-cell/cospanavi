# ふるさと納税「定期便コスパランキング」TOP3のYouTube Short(縦型・約23秒)を生成。
# 全カテゴリの定期便を横断し、寄付額あたりの単価(円/kg等)のコスパ順TOP3。
import json, os, sys, tempfile
from PIL import ImageDraw
from make_furusato_short import (font, ctext, tsize, wrap, vgrad, rrect, paste_card, dl_image,
                                 build_video, W, H, ORANGE, PINK, YEL, NAVY, WHITE)
from build_furusato import teiki_freq
from furusato_cats import FCATS

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")

def teiki_top(n=3):
    pool = []
    for slug in FCATS:
        f = os.path.join(DATA, f"furusato-{slug}.json")
        if not os.path.exists(f):
            continue
        sf = FCATS[slug]["suffix"]
        for m in json.load(open(f, encoding="utf-8")):
            fr = teiki_freq(m["name"])
            if not fr:
                continue
            pool.append({"cat": FCATS[slug]["label"], "sf": sf, "fr": fr, "cospa": m["cospa"],
                         "unit": m["unit"], "amt": m["amt"], "name": m["name"].replace("【ふるさと納税】", "").strip(),
                         "price": m["price"], "review": m["review"], "rc": m["reviewCount"],
                         "image": m.get("image", ""), "aff": m.get("affiliate") or m.get("url")})
    pool.sort(key=lambda z: -z["cospa"])
    return pool[:n]

def bg(c1, c2):
    img = vgrad(c1, c2)
    return img, ImageDraw.Draw(img)

def scene_intro():
    img, d = bg((255, 138, 76), (255, 92, 138))
    rrect(d, [W/2-260, 150, W/2+260, 250], 50, fill=WHITE)
    ctext(d, W/2, 168, "楽天ふるさと納税", font(46), ORANGE)
    ctext(d, W/2, 430, "定期便", font(180), WHITE, stroke=8, sfill=NAVY)
    ctext(d, W/2, 660, "コスパランキング", font(88), YEL, stroke=6, sfill=NAVY)
    ctext(d, W/2, 850, "TOP3", font(230), WHITE, stroke=10, sfill=ORANGE)
    ctext(d, W/2, 1250, "毎月・全〇回で届く！", font(58), WHITE, stroke=4, sfill=NAVY)
    ctext(d, W/2, 1335, "円/kgでいちばんお得なのは？", font(52), WHITE, stroke=4, sfill=NAVY)
    ctext(d, W/2, 1760, "コスパナビ", font(60), WHITE, stroke=4, sfill=NAVY)
    return img

def scene_rank(rank, m):
    cols = {3: ((120, 170, 255), (90, 130, 220)), 2: ((190, 195, 205), (150, 155, 170)),
            1: ((255, 200, 70), (255, 150, 40))}
    img, d = bg(*cols[rank])
    bx, by = 175, 240
    d.ellipse([bx-130, by-130, bx+130, by+130], fill=NAVY)
    ctext(d, bx, by-95, "第", font(48), WHITE)
    ctext(d, bx, by-55, str(rank), font(150), YEL)
    ctext(d, bx, by+78, "位", font(40), WHITE)
    # カテゴリ＋定期便回数バッジ(右上)
    rrect(d, [W-580, 150, W-90, 250], 40, fill=NAVY)
    ctext(d, W-335, 172, f"{m['cat']}／{m['fr']}", font(46), YEL)
    if rank == 1:
        d.polygon([(W/2-140, 470), (W/2-70, 560), (W/2, 470), (W/2+70, 560), (W/2+140, 470),
                   (W/2+110, 620), (W/2-110, 620)], fill=YEL, outline=NAVY)
    paste_card(img, m["_img"], W/2, 800, 500)
    y = 1090
    for line in wrap(m["name"], 15):
        y = ctext(d, W/2, y, line, font(48), NAVY) + 8
    # ヒーロー: 円/単位
    rrect(d, [90, 1300, W-90, 1560], 44, fill=WHITE)
    ctext(d, W/2, 1315, "総量換算した寄付額あたりの単価", font(38), (120, 120, 130))
    pr = f"{round(m['unit']):,}"
    ctext(d, W/2, 1365, pr, font(160), ORANGE)
    pw, _ = tsize(d, pr, font(160))
    d.text((W/2 + pw/2 + 10, 1443), f"円/{m['sf']}", font=font(52), fill=NAVY)
    amt = m['amt']; amt = round(amt, 1) if amt < 10 else round(amt)
    ctext(d, W/2, 1615, f"総量 {amt}{m['sf']}（{m['fr']}）　寄付 {m['price']:,}円", font(48), NAVY, stroke=3, sfill=WHITE)
    star = "★" * round(m['review'])
    ctext(d, W/2, 1695, f"{star} {m['review']:.2f}（{m['rc']:,}件）", font(46), (230, 90, 30), stroke=3, sfill=WHITE)
    rrect(d, [W/2-150, 1785, W/2+150, 1868], 42, fill=NAVY)
    ctext(d, W/2, 1797, f"コスパ {round(m['cospa'])}", font(48), YEL)
    return img

def scene_outro():
    img, d = bg((255, 138, 76), (255, 92, 138))
    ctext(d, W/2, 300, "全順位＆他カテゴリは", font(64), WHITE, stroke=4, sfill=NAVY)
    ctext(d, W/2, 400, "コチラ！", font(120), WHITE, stroke=6, sfill=NAVY)
    rrect(d, [50, 650, W-50, 1010], 50, fill=WHITE)
    ctext(d, W/2, 700, "コスパナビ", font(72), NAVY)
    ctext(d, W/2, 810, "cospa-navi.com", font(100), ORANGE)
    rrect(d, [W/2-470, 1150, W/2+470, 1300], 40, fill=NAVY)
    ctext(d, W/2, 1178, "▼ リンクは 概要欄・コメント欄", font(50), YEL)
    ctext(d, W/2, 1420, "1回の寄付で毎月届く", font(58), WHITE, stroke=4, sfill=NAVY)
    ctext(d, W/2, 1500, "定期便のコスパを総量換算で比較", font(48), WHITE, stroke=4, sfill=NAVY)
    return img

def main():
    outdir = os.path.join(BASE, "shorts"); os.makedirs(outdir, exist_ok=True)
    top = teiki_top(3)
    for m in top:
        m["_img"] = dl_image(m.get("image", ""))
    scenes = [(scene_intro(), 3.0), (scene_rank(3, top[2]), 5.0), (scene_rank(2, top[1]), 5.0),
              (scene_rank(1, top[0]), 7.0), (scene_outro(), 5.0)]
    tmp = tempfile.mkdtemp(); pngs, durs = [], []
    for i, (im, du) in enumerate(scenes):
        p = os.path.join(tmp, f"s{i}.png"); im.save(p); pngs.append(p); durs.append(du)
    bgm = os.path.join(outdir, "bgm.mp3")
    out = os.path.join(outdir, "furusato-teiki-top3.mp4")
    build_video(pngs, durs, out, bgm=bgm if os.path.exists(bgm) else None)
    print(f"生成: {out}  ({sum(durs):.0f}秒, BGM={'有' if os.path.exists(bgm) else '無'})")
    scenes[3][0].save(os.path.join(outdir, "furusato-teiki-frame1.png"))

if __name__ == "__main__":
    main()
