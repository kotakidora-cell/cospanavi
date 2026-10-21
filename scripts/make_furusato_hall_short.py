# ふるさと納税「高評価 殿堂入り Top3」= カテゴリ横断で“★評価の高い定番返礼品”を紹介する縦型Short。
# 既存のmake_furusato_shortは単一カテゴリのコスパTop3。こちらは複数カテゴリを跨いだ「高評価殿堂」版。
import json, os, sys, re, tempfile
from PIL import ImageDraw
from make_furusato_short import (font, ctext, tsize, rrect, vgrad, paste_card, dl_image,
                                 build_video, W, H, ORANGE, PINK, YEL, NAVY, WHITE)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")

def clean_name(nm):
    nm = re.sub(r"[＼／\\/]", "", nm)
    nm = re.sub(r"【[^】]*】", "", nm)
    nm = re.sub(r"\[[^\]]*\]", "", nm)
    nm = re.sub(r"★[0-9.]+", "", nm)
    nm = re.sub(r"高評価", "", nm)
    return re.sub(r"\s+", " ", nm).strip()

def wrap(s, n):
    return [s[i:i+n] for i in range(0, len(s), n)][:2]

def pick(slug, kw=None, kwx=None, minrc=100, by="review"):
    d = json.load(open(os.path.join(DATA, f"furusato-{slug}.json"), encoding="utf-8"))
    items = [m for m in d if m["reviewCount"] >= minrc and m["review"] >= 4.5]
    if kw:  items = [m for m in items if any(k in m["name"] for k in kw)]
    if kwx: items = [m for m in items if not any(k in m["name"] for k in kwx)]
    if by == "count":
        items.sort(key=lambda m: -m["reviewCount"])
    else:
        items.sort(key=lambda m: (-m.get("bayes", m["review"]), -m["reviewCount"]))
    return items[0]

def scene_intro():
    bg = vgrad((255, 138, 76), (255, 92, 138)); d = ImageDraw.Draw(bg)
    rrect(d, [W/2-240, 150, W/2+240, 252], 52, fill=WHITE)
    ctext(d, W/2, 170, "楽天ふるさと納税", font(48), ORANGE)
    ctext(d, W/2, 440, "高評価", font(165), WHITE, stroke=8, sfill=NAVY)
    ctext(d, W/2, 640, "殿堂入り", font(150), YEL, stroke=8, sfill=NAVY)
    ctext(d, W/2, 900, "TOP3", font(230), WHITE, stroke=10, sfill=ORANGE)
    ctext(d, W/2, 1300, "リピーター続出の", font(60), WHITE, stroke=4, sfill=NAVY)
    ctext(d, W/2, 1390, "“当たり”返礼品はコレ", font(60), WHITE, stroke=4, sfill=NAVY)
    ctext(d, W/2, 1770, "コスパナビ", font(60), WHITE, stroke=4, sfill=NAVY)
    return bg

def scene_rank(rank, it, img):
    cols = {3: ((120, 170, 255), (90, 130, 220)), 2: ((190, 195, 205), (150, 155, 170)),
            1: ((255, 200, 70), (255, 150, 40))}
    bg = vgrad(*cols[rank]); d = ImageDraw.Draw(bg)
    # 順位バッジ
    bx, by = 175, 240
    d.ellipse([bx-125, by-125, bx+125, by+125], fill=NAVY)
    ctext(d, bx, by-90, "第", font(46), WHITE)
    ctext(d, bx, by-52, str(rank), font(140), YEL)
    ctext(d, bx, by+74, "位", font(38), WHITE)
    # カテゴリ帯(順位バッジと被らないよう右寄せ・絵文字はフォント非対応のため不使用)
    rrect(d, [330, 150, W-40, 250], 50, fill=WHITE)
    ctext(d, (330 + W - 40) / 2, 170, it["label"], font(56), NAVY)
    if rank == 1:
        d.polygon([(W/2-130, 440), (W/2-65, 525), (W/2, 440), (W/2+65, 525), (W/2+130, 440),
                   (W/2+100, 585), (W/2-100, 585)], fill=YEL, outline=NAVY)
    paste_card(bg, img, W/2, 790, 470)
    # 商品名
    y = 1090
    for line in wrap(clean_name(it["name"]), 15):
        y = ctext(d, W/2, y, line, font(48), NAVY) + 6
    # ヒーロー: ★評価(高評価が主役)
    rrect(d, [90, 1290, W-90, 1560], 44, fill=WHITE)
    ctext(d, W/2, 1308, "レビュー評価", font(42), (120, 120, 130))
    star = f"{it['review']:.2f}"
    ctext(d, W/2, 1352, "★" + star, font(150), ORANGE)
    ctext(d, W/2, 1500, f"（{it['reviewCount']:,}件のレビュー）", font(46), NAVY)
    # 寄付額 + 殿堂バッジ
    ctext(d, W/2, 1610, f"寄付 {it['price']:,}円", font(52), NAVY, stroke=3, sfill=WHITE)
    rrect(d, [W/2-210, 1710, W/2+210, 1800], 42, fill=NAVY)
    ctext(d, W/2, 1722, "殿堂入り★", font(50), YEL)
    return bg

def scene_outro(yt=False):
    bg = vgrad((255, 138, 76), (255, 92, 138)); d = ImageDraw.Draw(bg)
    ctext(d, W/2, 280, "ほかの殿堂返礼品も", font(64), WHITE, stroke=4, sfill=NAVY)
    ctext(d, W/2, 380, "コスパナビで！", font(104), WHITE, stroke=6, sfill=NAVY)
    rrect(d, [50, 640, W-50, 1000], 50, fill=WHITE)
    ctext(d, W/2, 690, "コスパナビ", font(72), NAVY)
    ctext(d, W/2, 800, "cospa-navi.com", font(100), ORANGE)
    rrect(d, [W/2-480, 1150, W/2+480, 1300], 40, fill=NAVY)
    sub = "“コスパナビ”で検索／概要欄" if yt else "▼ リンクは プロフィール"
    ctext(d, W/2, 1178, sub, font(48), YEL)
    ctext(d, W/2, 1430, "実質2000円で“当たり”を狙う", font(54), WHITE, stroke=4, sfill=NAVY)
    ctext(d, W/2, 1510, "ふるさと納税コスパ比較", font(54), WHITE, stroke=4, sfill=NAVY)
    return bg

def main():
    yt = (sys.argv[1] if len(sys.argv) > 1 else "") == "youtube"
    outdir = os.path.join(BASE, "shorts"); os.makedirs(outdir, exist_ok=True)
    beef = pick("beef", minrc=500, by="count"); beef.update({"label": "牛肉", "emoji": "🥩"})
    toilet = pick("toilet-paper", minrc=500, by="count"); toilet.update({"label": "トイレットペーパー", "emoji": "🧻"})
    katsuo = pick("seafood", kw=["かつお", "カツオ", "鰹"], kwx=["明太", "いくら", "めんたい"], minrc=100, by="review")
    katsuo.update({"label": "かつおのたたき", "emoji": "🐟"})
    # 高評価順(★)で 3→2→1 に並べる
    ordered = sorted([beef, toilet, katsuo], key=lambda m: m["review"])  # 低→高
    r3, r2, r1 = ordered  # r1=最高評価
    imgs = {id(m): dl_image(m.get("image", "")) for m in ordered}
    scenes = [(scene_intro(), 3.5),
              (scene_rank(3, r3, imgs[id(r3)]), 5.5),
              (scene_rank(2, r2, imgs[id(r2)]), 5.5),
              (scene_rank(1, r1, imgs[id(r1)]), 6.5),
              (scene_outro(yt), 5.0)]
    tmp = tempfile.mkdtemp(); pngs, durs = [], []
    for i, (im, du) in enumerate(scenes):
        p = os.path.join(tmp, f"s{i}.png"); im.save(p); pngs.append(p); durs.append(du)
    for i in (0, 3, 4):
        scenes[i][0].save(os.path.join(outdir, f"furusato-hall-f{i}.png"))
    out = os.path.join(outdir, f"furusato-hall-top3{'-yt' if yt else ''}.mp4")
    bgm = os.path.join(outdir, "bgm.mp3"); bgmp = bgm if os.path.exists(bgm) else None
    def line(rank, it):
        return f"第{rank}位、{it['label']}。レビュー星{it['review']:.1f}、{it['reviewCount']:,}件の高評価。寄付{it['price']:,}円の殿堂入りです。"
    land = "コスパナビのふるさと納税ページ、概要欄のリンクか、コスパナビで検索してね。" if yt else "コスパナビのプロフィールのリンクからどうぞ。"
    texts = [
        "ふるさと納税、レビュー高評価の殿堂入りトップ3！リピーター続出の“当たり”返礼品はこれ。",
        line(3, r3), line(2, r2),
        f"そして堂々の第1位は、{r1['label']}。星{r1['review']:.1f}、{r1['reviewCount']:,}件の圧倒的高評価です。",
        "ほかの殿堂入り返礼品もまとめています。" + land,
    ]
    import narrate
    if narrate.available():
        total = narrate.build_narrated_video(pngs, texts, out, bgm=bgmp)
        print(f"生成(ナレーション付): {out}  約{total:.0f}秒")
    else:
        build_video(pngs, durs, out, bgm=bgmp)
        print(f"生成(BGMのみ/VOICEVOX未起動): {out} ({sum(durs):.0f}秒)")

if __name__ == "__main__":
    main()
