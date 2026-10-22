# ふるさと納税 旅行モデルプランの縦型Short(約60-70秒)。写真を活かした旅行プラン紹介→cospa-naviへ。
# 栃木・那須 1泊2日プラン(ふるさと納税＋対象外も含む)。使い方: python make_trip_short.py [youtube]
import os, sys, tempfile
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import imageio_ffmpeg

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
W, H = 1080, 1920
FONT = "C:/Windows/Fonts/BIZ-UDGothicB.ttc"
FONT2 = "C:/Windows/Fonts/meiryob.ttc"
IMGDIR = os.path.join(BASE, "site", "local", "nasu")

CREAM1 = (250, 245, 237); CREAM2 = (240, 228, 214)
ORANGE = (255, 90, 31); NAVY = (32, 38, 54); WHITE = (255, 255, 255)
SUB = (120, 104, 94); YEL = (255, 209, 74)

def font(sz):
    try: return ImageFont.truetype(FONT, sz)
    except Exception: return ImageFont.truetype(FONT2, sz)

def vgrad(c1, c2):
    base = Image.new("RGB", (W, H)); px = base.load()
    for y in range(H):
        t = y / H
        px0 = (int(c1[0]*(1-t)+c2[0]*t), int(c1[1]*(1-t)+c2[1]*t), int(c1[2]*(1-t)+c2[2]*t))
        for x in range(W): px[x, y] = px0
    return base

def ograd():
    return vgrad((255, 138, 76), (255, 92, 138))

def tsize(d, s, f):
    b = d.textbbox((0, 0), s, font=f); return b[2]-b[0], b[3]-b[1]

def ctext(d, cx, y, s, f, fill, stroke=0, sfill=(0, 0, 0)):
    w, h = tsize(d, s, f)
    d.text((cx-w/2, y), s, font=f, fill=fill, stroke_width=stroke, stroke_fill=sfill)
    return y+h

def rrect(d, xy, rad, **kw): d.rounded_rectangle(xy, radius=rad, **kw)

def fit(d, s, maxw, start, floor=40):
    fs = start
    while tsize(d, s, font(fs))[0] > maxw and fs > floor:
        fs -= 4
    return fs

def place(bg, img, cx, cy, maxw, maxh, rad=28):
    iw, ih = img.size
    s = min(maxw/iw, maxh/ih); w, h = int(iw*s), int(ih*s)
    im2 = img.resize((w, h), Image.LANCZOS)
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, w, h], radius=rad, fill=255)
    sh = Image.new("RGBA", (w+70, h+70), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([35, 46, w+35, h+46], radius=rad, fill=(40, 25, 15, 110))
    sh = sh.filter(ImageFilter.GaussianBlur(20))
    bg.paste(sh, (int(cx-w/2-35), int(cy-h/2-35)), sh)
    bg.paste(im2, (int(cx-w/2), int(cy-h/2)), mask)
    return h

def img(name): return Image.open(os.path.join(IMGDIR, name)).convert("RGB")

def pill(d, cx, y, s, f, bg, fg, padx=40, pady=18):
    w, h = tsize(d, s, f)
    rrect(d, [cx-w/2-padx, y, cx+w/2+padx, y+h+pady*2], (h+pady*2)//2, fill=bg)
    d.text((cx-w/2, y+pady-2), s, font=f, fill=fg)
    return y+h+pady*2

def scene_intro():
    bg = ograd(); d = ImageDraw.Draw(bg)
    rrect(d, [W/2-290, 150, W/2+290, 250], 50, fill=WHITE)
    ctext(d, W/2, 168, "楽天ふるさと納税 × 家族旅行", font(42), ORANGE)
    ctext(d, W/2, 330, "ふるさと納税で", font(76), WHITE, stroke=6, sfill=NAVY)
    ctext(d, W/2, 440, "贅沢 家族旅行", font(104), YEL, stroke=7, sfill=NAVY)
    ctext(d, W/2, 590, "栃木・那須 1泊2日", font(60), WHITE, stroke=5, sfill=NAVY)
    place(bg, img("rindo.jpg"), W/2, 1030, 860, 620)
    ctext(d, W/2, 1430, "〜父の威厳を取り戻せ〜", font(58), WHITE, stroke=4, sfill=NAVY)
    ctext(d, W/2, 1560, "実質2,000円で、どこまで贅沢できる？", font(50), WHITE, stroke=4, sfill=NAVY)
    ctext(d, W/2, 1770, "コスパナビ", font(56), WHITE, stroke=4, sfill=NAVY)
    return bg

def scene_tip():
    bg = ograd(); d = ImageDraw.Draw(bg)
    pill(d, W/2, 300, "知らないと損！", font(56), NAVY, YEL)
    ctext(d, W/2, 560, "ホテルには", font(84), WHITE, stroke=6, sfill=NAVY)
    ctext(d, W/2, 700, "ふるさと納税を", font(84), WHITE, stroke=6, sfill=NAVY)
    ctext(d, W/2, 840, "使わない！", font(110), YEL, stroke=7, sfill=NAVY)
    ctext(d, W/2, 1120, "宿泊に使うと控除上限をすぐ使い切り、", font(48), WHITE, stroke=4, sfill=NAVY)
    ctext(d, W/2, 1200, "現地で“豪遊”できなくなるから。", font(48), WHITE, stroke=4, sfill=NAVY)
    ctext(d, W/2, 1380, "遊び・食事はふるさと納税、", font(52), WHITE, stroke=4, sfill=NAVY)
    ctext(d, W/2, 1460, "宿泊は現金で確保が鉄則。", font(52), WHITE, stroke=4, sfill=NAVY)
    return bg

def scene_spot(day, name, line1, line2, image, hero=False, obj=False):
    bg = vgrad(CREAM1, CREAM2); d = ImageDraw.Draw(bg)
    # 日付/ラベル バッジ
    label = day
    lb = NAVY if not obj else SUB
    pill(d, W/2, 150, label, font(52), (ORANGE if hero else lb), WHITE if not hero else WHITE)
    place(bg, img(image), W/2, 760, 980, 940)
    # 店名/スポット名
    fs = fit(d, name, 960, 64)
    y = ctext(d, W/2, 1300, name, font(fs), NAVY)
    # 補足2行
    ctext(d, W/2, 1420, line1, font(52), (210, 70, 20) if hero else SUB)
    if line2:
        if obj:
            pill(d, W/2, 1520, line2, font(46), SUB, WHITE)
        else:
            rrect(d, [W/2-330, 1520, W/2+330, 1610], 44, fill=NAVY)
            ctext(d, W/2, 1534, line2, font(50), YEL)
    return bg

def scene_outro(yt=False):
    bg = ograd(); d = ImageDraw.Draw(bg)
    ctext(d, W/2, 230, "寄付 合計", font(58), WHITE, stroke=4, sfill=NAVY)
    ctext(d, W/2, 320, "約210,000円", font(130), YEL, stroke=7, sfill=NAVY)
    ctext(d, W/2, 560, "実質2,000円の自己負担で", font(52), WHITE, stroke=4, sfill=NAVY)
    ctext(d, W/2, 640, "1泊2日が超贅沢に！", font(58), WHITE, stroke=4, sfill=NAVY)
    rrect(d, [60, 820, W-60, 1180], 50, fill=WHITE)
    ctext(d, W/2, 870, "詳しいプランは", font(56), NAVY)
    ctext(d, W/2, 960, "コスパナビ", font(80), NAVY)
    ctext(d, W/2, 1070, "cospa-navi.com", font(84), ORANGE)
    sub = "“コスパナビ”で検索／概要欄リンク" if yt else "▼ プロフィールのリンクから"
    rrect(d, [W/2-470, 1300, W/2+470, 1450], 40, fill=NAVY)
    ctext(d, W/2, 1330, sub, font(46), YEL)
    ctext(d, W/2, 1600, "父親尊敬度アップ、間違いなし！", font(54), WHITE, stroke=4, sfill=NAVY)
    return bg

def main():
    yt = (sys.argv[1] if len(sys.argv) > 1 else "") == "youtube"
    outdir = os.path.join(BASE, "shorts"); os.makedirs(outdir, exist_ok=True)
    scenes = [
        (scene_intro(),
         "ふるさと納税だけで、家族旅行をどこまで贅沢にできるのか。栃木・那須の1泊2日、やってみました。"),
        (scene_tip(),
         "まず最重要ポイント。ホテルには、ふるさと納税を使わないこと。宿泊に使うと上限をすぐ使い切って、現地で豪遊できなくなります。"),
        (scene_spot("1日目", "りんどう湖ファミリー牧場", "乗り放題付ペア券×2＝家族4名", "寄付 60,000円", "rindo.jpg"),
         "1日目は、那須高原りんどうこファミリー牧場。乗り放題付きのペア入園券を2組、寄付6万円で家族4人。一日ここだけで十分楽しめます。"),
        (scene_spot("2日目", "南ヶ丘牧場", "あゆ釣り・お土産・手作りDIY", "利用券 6,000円分", "minamigaoka.jpg"),
         "2日目は南ヶ丘牧場。あゆ釣りにお土産、DIYコーナーまで、利用券で遊べます。お土産はここで贅沢に。"),
        (scene_spot("宝石探しに夢中✨", "トレジャーストーンパーク", "クリスタルリバーがおすすめ", "※ふるさと納税 対象外・現地払い", "tsp.jpg", obj=True),
         "そしてトレジャーストーンパーク。宝石探しに子どもが夢中になります。ここはふるさと納税の対象外なので、現地で支払います。"),
        (scene_spot("ここで豪遊！", "あ・かうはーど お食事券", "ステーキ＋デザートを気にせず", "39,000円分(寄付13万)", "akauhard.jpg", hero=True),
         "しめは、あ・かうはーどで豪遊。3万9千円分のお食事券で、ステーキもデザートも、金額を気にせず楽しめます。"),
        (scene_outro(yt),
         "寄付の合計はおよそ21万円。実質2千円の自己負担で、ここまで贅沢できます。詳しいプランはコスパナビで。"
         + ("概要欄のリンクか、コスパナビで検索してね。" if yt else "")),
    ]
    tmp = tempfile.mkdtemp(); pngs, texts = [], []
    for i, (im, tx) in enumerate(scenes):
        p = os.path.join(tmp, f"s{i}.png"); im.save(p); pngs.append(p); texts.append(tx)
    for i in (0, 1, 5, 6):
        scenes[i][0].save(os.path.join(outdir, f"nasu-trip-f{i}.png"))
    out = os.path.join(outdir, f"nasu-trip{'-yt' if yt else ''}.mp4")
    bgm = os.path.join(outdir, "bgm.mp3"); bgmp = bgm if os.path.exists(bgm) else None
    speaker = int(os.environ["VV_SPEAKER"]) if os.environ.get("VV_SPEAKER") else 108  # 東北きりたん
    import narrate
    from make_furusato_short import build_video
    if narrate.available():
        total = narrate.build_narrated_video(pngs, texts, out, bgm=bgmp, speaker=speaker)
        print(f"生成(ナレーション付 話者{speaker}): {out}  約{total:.0f}秒")
    else:
        build_video(pngs, [4.5]*len(pngs), out, bgm=bgmp)
        print(f"生成(BGMのみ/VOICEVOX未起動): {out}")

if __name__ == "__main__":
    main()
