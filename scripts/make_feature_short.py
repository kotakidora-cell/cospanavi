# サイトの使い方を伝える説明型のYouTube Short(縦1080x1920, 約23秒)。
# 流れ: ①控除上限シミュレーターで確認 → ②上限に合った実質還元率の返礼品 → ③コスパ/価格で調整 → ④cospa-navi。
# 通常のTOP3テンプレとは別構成。BGMは shorts/bgm.mp3（前回と同じ）。
import os, tempfile
from PIL import ImageDraw, Image, ImageFilter
from make_furusato_short import (font, ctext, tsize, vgrad, rrect, build_video,
                                 W, H, ORANGE, PINK, YEL, NAVY, WHITE)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOT = os.path.join(BASE, "shorts", "kanpu-slide2.png")  # 実HPのスマホ幅スクショ(shot_kanpu.pyで生成)
LIGHT = (228, 233, 240)
SUB = (120, 126, 140)
GREEN = (34, 160, 90)
CREAM = (255, 244, 238)


def D(img):
    return ImageDraw.Draw(img)


def slider(d, x1, x2, y, frac, h=26, knob=ORANGE):
    rrect(d, [x1, y - h / 2, x2, y + h / 2], h / 2, fill=LIGHT)
    fx = x1 + (x2 - x1) * frac
    rrect(d, [x1, y - h / 2, fx, y + h / 2], h / 2, fill=knob)
    d.ellipse([fx - 32, y - 32, fx + 32, y + 32], fill=WHITE, outline=knob, width=8)


def framed(bg, img, cx, cy, w, h, rad=28):
    """スクショを角丸＋影付きで貼る"""
    im = img.resize((w, h), Image.LANCZOS)
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, w, h], rad, fill=255)
    sh = Image.new("RGBA", (w + 70, h + 70), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([35, 42, w + 35, h + 42], rad, fill=(0, 0, 0, 110))
    sh = sh.filter(ImageFilter.GaussianBlur(16))
    bg.paste(sh, (int(cx - w / 2 - 35), int(cy - h / 2 - 35)), sh)
    bg.paste(im, (int(cx - w / 2), int(cy - h / 2)), mask)


def scene1():
    img = vgrad((255, 138, 76), (255, 92, 138)); d = D(img)
    rrect(d, [W/2-300, 140, W/2+300, 240], 50, fill=WHITE)
    ctext(d, W/2, 160, "楽天ふるさと納税", font(48), ORANGE)
    ctext(d, W/2, 300, "ふるさと納税", font(82), WHITE, stroke=6, sfill=NAVY)
    ctext(d, W/2, 415, "いくらまで？", font(118), YEL, stroke=8, sfill=NAVY)
    rrect(d, [70, 630, W-70, 1200], 44, fill=WHITE)
    ctext(d, W/2, 680, "控除上限シミュレーター", font(54), NAVY)
    d.text((150, 790), "年収  600万円", font=font(46), fill=NAVY)
    slider(d, 150, W-150, 900, 0.62)
    rrect(d, [150, 1000, W-150, 1150], 30, fill=CREAM)
    d.text((190, 1035), "控除上限の目安", font=font(40), fill=SUB)
    tw, _ = tsize(d, "¥77,000", font(88))
    d.text((W-190-tw, 1018), "¥77,000", font=font(88), fill=ORANGE)
    rrect(d, [60, 1320, W-60, 1445], 32, fill=NAVY)
    ctext(d, W/2, 1345, "① まずは上限額をチェック", font(56), WHITE)
    ctext(d, W/2, 1560, "年収と家族構成を選ぶだけ", font(52), WHITE, stroke=4, sfill=NAVY)
    ctext(d, W/2, 1760, "コスパナビ", font(60), WHITE, stroke=4, sfill=NAVY)
    return img


def scene2():
    img = vgrad((120, 170, 255), (86, 124, 214)); d = D(img)
    ctext(d, W/2, 60, "あなたの上限に合った", font(52), WHITE, stroke=4, sfill=NAVY)
    ctext(d, W/2, 140, "\"実質還元率\"の高い返礼品", font(58), YEL, stroke=5, sfill=NAVY)
    if os.path.exists(SHOT):
        s = Image.open(SHOT).convert("RGB")
        w = 830; h = int(w * s.height / s.width)
        if h > 1470:
            h = 1470; w = int(h * s.width / s.height)
        framed(img, s, W/2, 250 + h/2, w, h)
        ctext(d, W/2, 1770, "② 市場価格から独自に算出（実際の画面）", font(46), WHITE, stroke=4, sfill=NAVY)
    else:
        rows = [("お米 無洗米 10kg", "66%"), ("牛こま切れ 1.8kg", "62%"), ("じゃがいも 10kg", "60%")]
        for i, (nm, rt) in enumerate(rows):
            y = 560 + i * 250
            rrect(d, [70, y, W-70, y+210], 34, fill=WHITE)
            d.ellipse([120, y+68, 200, y+148], fill=NAVY)
            ctext(d, 160, y+78, str(i+1), font(64), YEL)
            d.text((250, y+55), nm, font=font(48), fill=NAVY)
            rrect(d, [W-370, y+55, W-110, y+155], 28, fill=GREEN)
            ctext(d, W-240, y+63, "還元率", font(34), WHITE)
            ctext(d, W-240, y+98, rt, font(50), WHITE)
        ctext(d, W/2, 1370, "② 市場価格から独自に算出", font(54), WHITE, stroke=4, sfill=NAVY)
        ctext(d, W/2, 1560, "ポータルにはない指標", font(52), WHITE, stroke=4, sfill=NAVY)
        ctext(d, W/2, 1760, "コスパナビ", font(60), WHITE, stroke=4, sfill=NAVY)
    return img


def scene3():
    img = vgrad((255, 138, 76), (255, 92, 138)); d = D(img)
    ctext(d, W/2, 160, "コスパ重視？ 価格重視？", font(62), WHITE, stroke=4, sfill=NAVY)
    ctext(d, W/2, 285, "自由に調整", font(120), YEL, stroke=8, sfill=NAVY)
    rrect(d, [70, 500, W-70, 980], 44, fill=WHITE)
    d.text((150, 545), "重視ポイント", font=font(46), fill=NAVY)
    d.text((150, 640), "お得さ", font=font(38), fill=SUB)
    tw, _ = tsize(d, "満足度", font(38))
    d.text((W-150-tw, 640), "満足度", font=font(38), fill=SUB)
    slider(d, 150, W-150, 730, 0.5)
    d.text((150, 830), "寄付額の上限", font=font(38), fill=SUB)
    slider(d, 150, W-150, 915, 0.7)
    ctext(d, W/2, 1080, "スライダーを動かすと", font(54), WHITE, stroke=4, sfill=NAVY)
    ctext(d, W/2, 1160, "ランキングが即並び替え", font(54), WHITE, stroke=4, sfill=NAVY)
    rrect(d, [60, 1360, W-60, 1485], 32, fill=NAVY)
    ctext(d, W/2, 1385, "③ 自分基準で選べる", font(58), WHITE)
    ctext(d, W/2, 1600, "予算内で一番お得な返礼品へ", font(50), WHITE, stroke=4, sfill=NAVY)
    ctext(d, W/2, 1770, "コスパナビ", font(56), WHITE, stroke=4, sfill=NAVY)
    return img


def scene4():
    img = vgrad((255, 138, 76), (255, 92, 138)); d = D(img)
    ctext(d, W/2, 250, "ふるさと納税を、", font(72), WHITE, stroke=4, sfill=NAVY)
    ctext(d, W/2, 355, "かしこく。", font(112), WHITE, stroke=6, sfill=NAVY)
    rrect(d, [60, 640, W-60, 1010], 50, fill=WHITE)
    ctext(d, W/2, 690, "コスパナビ", font(72), NAVY)
    ctext(d, W/2, 800, "cospa-navi.com", font(100), ORANGE)
    rrect(d, [W/2-480, 1150, W/2+480, 1300], 40, fill=NAVY)
    ctext(d, W/2, 1178, "▼ リンクは 概要欄・コメント欄", font(50), YEL)
    ctext(d, W/2, 1450, "控除上限シミュレーター＆", font(52), WHITE, stroke=4, sfill=NAVY)
    ctext(d, W/2, 1530, "実質還元率ランキング", font(52), WHITE, stroke=4, sfill=NAVY)
    return img


def main():
    outdir = os.path.join(BASE, "shorts"); os.makedirs(outdir, exist_ok=True)
    scenes = [(scene1(), 5.5), (scene2(), 6.5), (scene3(), 6.0), (scene4(), 5.0)]
    tmp = tempfile.mkdtemp(); pngs, durs = [], []
    for i, (im, du) in enumerate(scenes):
        p = os.path.join(tmp, f"s{i}.png"); im.save(p); pngs.append(p); durs.append(du)
    bgm = os.path.join(outdir, "bgm.mp3")
    out = os.path.join(outdir, "furusato-howto.mp4")
    build_video(pngs, durs, out, bgm=bgm if os.path.exists(bgm) else None)
    print(f"生成: {out}  ({sum(durs):.0f}秒, BGM={'有' if os.path.exists(bgm) else '無'})")
    for i, (im, _) in enumerate(scenes, 1):
        im.save(os.path.join(outdir, f"howto-scene{i}.png"))


if __name__ == "__main__":
    main()
