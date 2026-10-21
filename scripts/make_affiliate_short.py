# 楽天アフィリエイト商品を「女子大生ペルソナ」トーンで紹介する縦型Short(約50-60秒)。
# recommend.py の PICKS["video"] を台本に、商品ごとに使い回せる。
# 使い方: python make_affiliate_short.py <slug> [threads|youtube]
#   例) python make_affiliate_short.py ajiro-hairclip youtube
import os, sys, tempfile
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import imageio_ffmpeg

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
W, H = 1080, 1920
FONT = "C:/Windows/Fonts/BIZ-UDGothicB.ttc"
FONT2 = "C:/Windows/Fonts/meiryob.ttc"

CREAM1 = (250, 245, 237); CREAM2 = (238, 226, 212)
WINE = (122, 31, 61); INK = (45, 37, 33); GOLD = (178, 142, 78)
WHITE = (255, 255, 255); SUB = (120, 104, 94); YEL = (255, 209, 74)

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

def tsize(d, s, f):
    b = d.textbbox((0, 0), s, font=f); return b[2]-b[0], b[3]-b[1]

def ctext(d, cx, y, s, f, fill, stroke=0, sfill=(0, 0, 0)):
    w, h = tsize(d, s, f)
    d.text((cx-w/2, y), s, font=f, fill=fill, stroke_width=stroke, stroke_fill=sfill)
    return y+h

def rrect(d, xy, rad, **kw): d.rounded_rectangle(xy, radius=rad, **kw)

def pill(d, cx, y, s, f, bg, fg, padx=40, pady=18):
    w, h = tsize(d, s, f)
    rrect(d, [cx-w/2-padx, y, cx+w/2+padx, y+h+pady*2], (h+pady*2)//2, fill=bg)
    d.text((cx-w/2, y+pady-2), s, font=f, fill=fg)
    return y+h+pady*2

def fit_font(d, s, maxw, start=92, floor=48):
    fs = start
    while tsize(d, s, font(fs))[0] > maxw and fs > floor:
        fs -= 4
    return fs

def place(bg, img, cx, cy, maxw, maxh, rad=36):
    iw, ih = img.size
    s = min(maxw/iw, maxh/ih); w, h = int(iw*s), int(ih*s)
    im2 = img.resize((w, h), Image.LANCZOS)
    mask = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, w, h], radius=rad, fill=255)
    sh = Image.new("RGBA", (w+70, h+70), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([35, 44, w+35, h+44], radius=rad, fill=(70, 45, 35, 95))
    sh = sh.filter(ImageFilter.GaussianBlur(18))
    bg.paste(sh, (int(cx-w/2-35), int(cy-h/2-35)), sh)
    bg.paste(im2, (int(cx-w/2), int(cy-h/2)), mask)
    return w, h

def bgbase():
    bg = vgrad(CREAM1, CREAM2)
    return bg, ImageDraw.Draw(bg)

def scene_intro(v, hero, label):
    bg, d = bgbase()
    y = pill(d, W/2, 220, v["intro"]["pill"], font(50), WINE, WHITE)
    big = v["intro"]["big"]
    yy = 380
    for i, line in enumerate(big):
        fs = fit_font(d, line, 960, start=88)
        col = WINE if i == len(big)-1 else INK
        yy = ctext(d, W/2, yy, line, font(fs), col) + 24
    place(bg, hero, W/2, 1260, 820, 980)
    ctext(d, W/2, 1800, label, font(44), SUB)
    return bg

def scene_shot(img, cap, sub=None):
    bg, d = bgbase()
    y = pill(d, W/2, 190, cap, font(56), WINE, WHITE)
    if sub:
        ctext(d, W/2, y+26, sub, font(50), INK)
    place(bg, img, W/2, 1230, 940, 1320)
    return bg

def scene_price(pick, v):
    bg, d = bgbase()
    pr = v["price"]
    pill(d, W/2, 230, pr["pill"], font(52), WINE, WHITE)
    yy = 430
    for line in pr["lines"]:
        fs = fit_font(d, line, 940, start=78)
        yy = ctext(d, W/2, yy, line, font(fs), INK) + 20
    rrect(d, [120, 820, W-120, 1200], 48, fill=WHITE, outline=WINE, width=6)
    ctext(d, W/2, 870, pick["price_note"], font(52), SUB)
    num = f"{pick['price']:,}"
    ctext(d, W/2, 940, num, font(210), WINE)
    nw, _ = tsize(d, num, font(210))
    d.text((W/2+nw/2+14, 1060), "円", font=font(80), fill=INK)
    ctext(d, W/2, 1320, pr["tail1"], font(56), INK)
    ctext(d, W/2, 1430, pr["tail2"], font(50), SUB)
    return bg

def scene_cta(pick, yt=False):
    bg, d = bgbase()
    if yt:
        ctext(d, W/2, 300, "詳細はコスパナビの", font(66), INK)
        ctext(d, W/2, 410, "「イチオシ商品」へ", font(66), WINE)
        rrect(d, [70, 620, W-70, 980], 50, fill=WINE)
        ctext(d, W/2, 690, "cospa-navi.com", font(74), WHITE)
        ctext(d, W/2, 830, "で検索／概要欄リンク", font(50), WHITE)
        ctext(d, W/2, 1120, "保存して見返してね。", font(58), INK)
        ctext(d, W/2, 1300, "コスパナビ", font(56), WINE)
    else:
        ctext(d, W/2, 320, "気になった人は", font(76), INK)
        rrect(d, [90, 560, W-90, 980], 50, fill=WINE)
        ctext(d, W/2, 640, "プロフィールの", font(64), WHITE)
        ctext(d, W/2, 760, "リンクからチェック", font(64), WHITE)
        ctext(d, W/2, 1120, "保存して見返してね。", font(58), INK)
        ctext(d, W/2, 1300, pick.get("handle", "miwa_888"), font(56), WINE)
    ctext(d, W/2, 1700, "※アフィリエイトを含みます #PR", font(40), SUB)
    return bg

def main():
    if len(sys.argv) < 2:
        print("使い方: python make_affiliate_short.py <slug> [threads|youtube]"); return
    slug = sys.argv[1]
    platform = sys.argv[2] if len(sys.argv) > 2 else "threads"
    yt = platform == "youtube"
    from recommend import PICKS_BY_SLUG
    pick = PICKS_BY_SLUG[slug]
    pick.setdefault("handle", "miwa_888")
    v = pick["video"]
    imgdir = os.path.join(BASE, "site", "osusume", slug)
    imgs = {name: Image.open(os.path.join(imgdir, name)).convert("RGB") for name in pick["images"]}
    outdir = os.path.join(BASE, "shorts"); os.makedirs(outdir, exist_ok=True)

    intro_label = "コスパナビ" if yt else pick["handle"]   # YouTubeはブランド、Threads/Instagramはペルソナ
    scenes = [(scene_intro(v, imgs[pick["images"][0]], intro_label), v["intro"]["narr"])]
    for s in v["shots"]:
        scenes.append((scene_shot(imgs[s["img"]], s["cap"], s.get("sub")), s["narr"]))
    scenes.append((scene_price(pick, v), v["price"]["narr"]))
    cta_narr = ("気になった人は、コスパナビのイチオシ商品でチェックしてみてください。概要欄のリンクか、コスパナビで検索してね。ピーアールを含みます。"
                if yt else "気になった人は、プロフィールのリンクからチェックしてみてください。ピーアールを含みます。")
    scenes.append((scene_cta(pick, yt), cta_narr))

    tmp = tempfile.mkdtemp(); pngs, texts = [], []
    for i, (img, tx) in enumerate(scenes):
        p = os.path.join(tmp, f"s{i}.png"); img.save(p); pngs.append(p); texts.append(tx)
    # 確認用フレーム
    scenes[0][0].save(os.path.join(outdir, f"{slug}-f0.png"))
    scenes[-1][0].save(os.path.join(outdir, f"{slug}-cta.png"))
    out = os.path.join(outdir, f"{slug}{'-yt' if yt else ''}.mp4")
    bgm = os.path.join(outdir, "bgm.mp3"); bgmp = bgm if os.path.exists(bgm) else None
    speaker = int(os.environ["VV_SPEAKER"]) if os.environ.get("VV_SPEAKER") else v.get("voice", 8)
    import narrate
    from make_furusato_short import build_video
    if narrate.available():
        total = narrate.build_narrated_video(pngs, texts, out, bgm=bgmp, speaker=speaker)
        print(f"生成(ナレーション付 話者{speaker}): {out}  約{total:.0f}秒")
    else:
        build_video(pngs, [4.0]*len(pngs), out, bgm=bgmp)
        print(f"生成(BGMのみ/VOICEVOX未起動): {out}")

if __name__ == "__main__":
    main()
