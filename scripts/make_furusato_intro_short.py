# ふるさと納税「1位の返礼品を個人のおすすめトーンで紹介」する縦型Short(約25秒)。
# TOP3ランキングではなく、1商品にフォーカスして紹介文を読み上げる→Threads/YouTube向け。
# 使い方: python make_furusato_intro_short.py <slug(例:toilet-paper)> [出力先]
import json, os, sys, re, tempfile
from PIL import ImageDraw
from make_furusato_short import (font, ctext, tsize, rrect, vgrad, paste_card, dl_image,
                                 build_video, CATS, W, H, ORANGE, PINK, YEL, NAVY, WHITE)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")

def clean_name(nm):
    nm = re.sub(r"[＼／\\/]", "", nm)
    nm = re.sub(r"【[^】]*】", "", nm)
    nm = re.sub(r"\[[^\]]*\]", "", nm)
    nm = re.sub(r"（[^）]*）", "", nm)
    return re.sub(r"\s+", " ", nm).strip()

def wrap_fit(d, s, fs, maxw=980, lines=2):
    # 指定幅に収まるよう1行文字数を決めて最大lines行に折り返す
    out, cur = [], ""
    for ch in s:
        if tsize(d, cur + ch, font(fs))[0] > maxw:
            out.append(cur); cur = ch
            if len(out) >= lines:
                break
        else:
            cur += ch
    if cur and len(out) < lines:
        out.append(cur)
    return out[:lines]

def scene_intro(cat):
    bg = vgrad((255, 138, 76), (255, 92, 138)); d = ImageDraw.Draw(bg)
    rrect(d, [W/2-260, 170, W/2+260, 272], 52, fill=WHITE)
    ctext(d, W/2, 190, "楽天ふるさと納税", font(48), ORANGE)
    ctext(d, W/2, 470, "コスパ最強", font(150), WHITE, stroke=8, sfill=NAVY)
    lbl = f"【{cat['title']}編】"
    fs = 92
    while tsize(d, lbl, font(fs))[0] > 980 and fs > 48:
        fs -= 4
    ctext(d, W/2, 680, lbl, font(fs), YEL, stroke=7, sfill=NAVY)
    ctext(d, W/2, 980, f"1{cat['unit']}あたり", font(84), WHITE, stroke=6, sfill=NAVY)
    ctext(d, W/2, 1120, "いくらお得？", font(84), WHITE, stroke=6, sfill=NAVY)
    ctext(d, W/2, 1430, "毎年リピートしてる", font(56), WHITE, stroke=4, sfill=NAVY)
    ctext(d, W/2, 1510, "本命を紹介します", font(56), WHITE, stroke=4, sfill=NAVY)
    ctext(d, W/2, 1770, "コスパナビ", font(60), WHITE, stroke=4, sfill=NAVY)
    return bg

def scene_product(cat, m, img):
    bg = vgrad((255, 200, 70), (255, 150, 40)); d = ImageDraw.Draw(bg)
    # コスパ1位バッジ
    rrect(d, [W/2-240, 150, W/2+240, 272], 58, fill=NAVY)
    ctext(d, W/2, 172, "コスパ 第1位", font(66), YEL)
    paste_card(bg, img, W/2, 660, 470)
    # 商品名
    y = 930
    for line in wrap_fit(d, clean_name(m["name"]), 46, 980, 2):
        y = ctext(d, W/2, y, line, font(46), NAVY) + 8
    # ヒーロー: 1単位あたり単価
    rrect(d, [80, 1120, W-80, 1400], 44, fill=WHITE)
    ctext(d, W/2, 1140, f"1{cat['unit']}あたり", font(46), (120, 120, 130))
    num = f"{round(m['unit']):,}"
    ctext(d, W/2, 1190, num, font(190), ORANGE)
    nw, _ = tsize(d, num, font(190))
    d.text((W/2 + nw/2 + 12, 1290), "円", font=font(70), fill=NAVY)
    # 情報行
    amt = m['amt']; amt = round(amt, 1) if amt < 10 else round(amt)
    ctext(d, W/2, 1450, f"総量 {amt}{cat['unit']}相当 ／ 寄付 {m['price']:,}円", font(50), NAVY, stroke=3, sfill=WHITE)
    star = "★" * round(m['review'])
    ctext(d, W/2, 1540, f"{star} {m['review']:.2f}（{m['reviewCount']:,}件）", font(48), (210, 70, 20), stroke=3, sfill=WHITE)
    rrect(d, [W/2-300, 1660, W/2+300, 1750], 42, fill=NAVY)
    ctext(d, W/2, 1673, "楽天ランキング上位の定番", font(44), YEL)
    return bg

def scene_cta(cat):
    bg = vgrad((255, 138, 76), (255, 92, 138)); d = ImageDraw.Draw(bg)
    ctext(d, W/2, 260, "私も毎年", font(84), WHITE, stroke=5, sfill=NAVY)
    ctext(d, W/2, 400, "リピートしてます", font(84), YEL, stroke=5, sfill=NAVY)
    rrect(d, [60, 680, W-60, 1030], 50, fill=WHITE)
    ctext(d, W/2, 730, "コスパナビ", font(72), NAVY)
    ctext(d, W/2, 840, "cospa-navi.com", font(96), ORANGE)
    rrect(d, [W/2-480, 1180, W/2+480, 1330], 40, fill=NAVY)
    ctext(d, W/2, 1208, "▼ 詳細はプロフィールのリンク", font(50), YEL)
    ctext(d, W/2, 1470, "1ロールあたりで選ぶ", font(56), WHITE, stroke=4, sfill=NAVY)
    ctext(d, W/2, 1550, "ふるさと納税コスパ比較", font(56), WHITE, stroke=4, sfill=NAVY)
    return bg

def main():
    slug = sys.argv[1] if len(sys.argv) > 1 else "toilet-paper"
    outdir = sys.argv[2] if len(sys.argv) > 2 else os.path.join(BASE, "shorts")
    os.makedirs(outdir, exist_ok=True)
    cat = CATS.get(slug, {"title": slug, "unit": "", "unitlabel": "円", "emoji": ""})
    data = json.load(open(os.path.join(DATA, f"furusato-{slug}.json"), encoding="utf-8"))
    m = sorted(data, key=lambda z: -z["cospa"])[0]
    img = dl_image(m.get("image", ""))
    tmp = tempfile.mkdtemp()
    scenes = [(scene_intro(cat), 3.5), (scene_product(cat, m, img), 10.0), (scene_cta(cat), 5.0)]
    pngs, durs = [], []
    for i, (im, du) in enumerate(scenes):
        p = os.path.join(tmp, f"s{i}.png"); im.save(p); pngs.append(p); durs.append(du)
    # 確認用フレーム
    scenes[1][0].save(os.path.join(outdir, f"furusato-{slug}-intro-product.png"))
    out = os.path.join(outdir, f"furusato-{slug}-intro.mp4")
    bgm = os.path.join(BASE, "shorts", "bgm.mp3"); bgmp = bgm if os.path.exists(bgm) else None
    ul = cat.get("unit", "ロール")
    unit_price = round(m['unit'])
    amt = m['amt']; amt = round(amt, 1) if amt < 10 else round(amt)
    texts = [
        f"ふるさと納税で、コスパ最強の{cat['title']}、これです。",
        (f"ペンギンの5倍巻き。なんと1{ul}あたり、たったの{unit_price}円。"
         f"{amt}{ul}分で、寄付は{m['price']:,}円。レビューも星{m['review']:.1f}、"
         f"{m['reviewCount']:,}件超えで、楽天の総合ランキングでも上位の人気です。"),
        (f"かさばらない5倍巻きで、買い物も収納もラク。私も毎年これをリピートしています。"
         f"気になったら、プロフィールのリンクから詳細をチェックしてみてください。"),
    ]
    import narrate
    if narrate.available():
        narrate.build_narrated_video(pngs, texts, out, bgm=bgmp)
        print(f"生成(ナレーション付): {out}")
    else:
        build_video(pngs, durs, out, bgm=bgmp)
        print(f"生成(BGMのみ/VOICEVOX未起動): {out} ({sum(durs):.0f}秒)")

if __name__ == "__main__":
    main()
