# 楽天アフィリエイト商品を「女子大生ペルソナ」トーンで魅力的に紹介する縦型Short(約60秒)。
# Threads/Instagram向け。上品な配色＋商品画像カード＋VOICEVOXナレーション。
# 商品ごとに下部 PRODUCT を書き換えて使う。
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
WHITE = (255, 255, 255); SUB = (120, 104, 94)

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

def scene_intro(p):
    bg, d = bgbase()
    pill(d, W/2, 230, "秋冬の高見えボトム", font(50), WINE, WHITE)
    ctext(d, W/2, 400, "正直、優勝でした。", font(92), INK)
    ctext(d, W/2, 560, "高見えするのに", font(76), INK)
    y = ctext(d, W/2, 680, "この値段？", font(88), WINE)
    # 商品画像
    place(bg, p["imgs"][0], W/2, 1230, 820, 980)
    ctext(d, W/2, 1800, p["handle"], font(44), SUB)
    return bg

def scene_image(p, idx, cap_top, cap_sub=None):
    bg, d = bgbase()
    y = pill(d, W/2, 190, cap_top, font(56), WINE, WHITE)
    if cap_sub:
        ctext(d, W/2, y+26, cap_sub, font(50), INK)
    place(bg, p["imgs"][idx], W/2, 1230, 940, 1320)
    return bg

def scene_price(p):
    bg, d = bgbase()
    pill(d, W/2, 230, "コスパ良すぎ", font(52), WINE, WHITE)
    ctext(d, W/2, 430, "高見え × 楽ちん", font(78), INK)
    ctext(d, W/2, 560, "× あったか", font(78), INK)
    rrect(d, [120, 820, W-120, 1200], 48, fill=WHITE, outline=WINE, width=6)
    ctext(d, W/2, 870, "税込・送料無料", font(52), SUB)
    num = f"{p['price']:,}"
    ctext(d, W/2, 940, num, font(210), WINE)
    nw, _ = tsize(d, num, font(210))
    d.text((W/2+nw/2+14, 1060), "円", font=font(80), fill=INK)
    ctext(d, W/2, 1320, "これ一本で、秋冬いけます。", font(56), INK)
    ctext(d, W/2, 1430, f"サイズ {p['size']}／選べる2丈", font(52), SUB)
    return bg

def scene_cta(p):
    bg, d = bgbase()
    ctext(d, W/2, 320, "気になった人は", font(76), INK)
    rrect(d, [90, 560, W-90, 980], 50, fill=WINE)
    ctext(d, W/2, 640, "プロフィールの", font(64), WHITE)
    ctext(d, W/2, 760, "リンクからチェック", font(64), YEL if False else WHITE)
    ctext(d, W/2, 1120, "保存して見返してね。", font(58), INK)
    ctext(d, W/2, 1300, p["handle"], font(56), WINE)
    ctext(d, W/2, 1700, "※アフィリエイトを含みます #PR", font(40), SUB)
    return bg

YEL = (255, 209, 74)

def main():
    outdir = os.path.join(BASE, "shorts"); os.makedirs(outdir, exist_ok=True)
    SCR = r"C:\Users\kotak\AppData\Local\Temp\claude\c--cabnavi\29de35d7-5401-4de1-8fb7-04625d152bbd\scratchpad"
    P = {
        "slug": "belluna-gaucho",
        "handle": "miwa_888",
        "price": 3990,
        "size": "M〜5L",
        "imgs": [Image.open(os.path.join(SCR, f"pants-{i}.jpg")).convert("RGB") for i in (2, 4, 3)],
    }
    scenes = [
        (scene_intro(P), "秋冬の神ボトム、見つけちゃいました。たかみえするのに、なんと3990円のガウチョパンツです。"),
        (scene_image(P, 0, "なめらか美ワイド"),
         "まず、このなめらかなびワイドシルエット。とろんと落ちて脚のラインを拾わないから、一本でたかみえします。カラーも落ち着いた3色展開。"),
        (scene_image(P, 1, "両面起毛であったか"),
         "そして嬉しいのが、両面起毛のあったか素材。穿いた瞬間のヒヤッとを抑えてくれるので、寒い季節もこれ一本で乗り切れます。"),
        (scene_image(P, 2, "選べる2丈", "M〜5L"),
         "丈はショートとレギュラーの2タイプから選べて、サイズもMから5Lまで。背の高さや体型に合わせてぴったりが選べます。"),
        (scene_price(P),
         "これで税込3990円、しかも送料無料。たかみえして、楽ちんで、あったかい。コスパ良すぎます。"),
        (scene_cta(P),
         "気になった人は、プロフィールのリンクからチェックしてみてください。ピーアールを含みます。"),
    ]
    tmp = tempfile.mkdtemp(); pngs, texts = [], []
    for i, (img, tx) in enumerate(scenes):
        pth = os.path.join(tmp, f"s{i}.png"); img.save(pth); pngs.append(pth); texts.append(tx)
    # 確認用フレーム
    for i in (0, 1, 4, 5):
        scenes[i][0].save(os.path.join(outdir, f"{P['slug']}-f{i}.png"))
    out = os.path.join(outdir, f"{P['slug']}.mp4")
    bgm = os.path.join(outdir, "bgm.mp3"); bgmp = bgm if os.path.exists(bgm) else None
    import narrate
    from make_furusato_short import build_video
    if narrate.available():
        total = narrate.build_narrated_video(pngs, texts, out, bgm=bgmp)
        print(f"生成(ナレーション付): {out}  約{total:.0f}秒")
    else:
        durs = [4.0]*len(pngs)
        build_video(pngs, durs, out, bgm=bgmp)
        print(f"生成(BGMのみ/VOICEVOX未起動): {out}")

if __name__ == "__main__":
    main()
