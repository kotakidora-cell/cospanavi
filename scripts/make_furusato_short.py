# ふるさと納税コスパランキングのYouTube Short(縦型1080x1920,約25秒)を自動生成。
# コスパナビの独自データ(円/kg・コスパ値・総量)を主役にしたPOPなランキング動画→サイト誘導。
# 使い方: python make_furusato_short.py <slug(例:rice)> [出力ディレクトリ]
# 音声は無し(後でフリーBGMを合成)。ffmpegはimageio_ffmpeg同梱を使用。
import json, os, sys, io, subprocess, tempfile, re
import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import imageio_ffmpeg

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
W, H = 1080, 1920
FONT = "C:/Windows/Fonts/BIZ-UDGothicB.ttc"
FONT2 = "C:/Windows/Fonts/meiryob.ttc"

# カテゴリ別の見せ方（単位ラベル・タイトル・絵文字代替の色）
CATS = {
    "rice":  {"title": "お米", "unit": "kg", "unitlabel": "円/kg", "emoji": "🍚"},
    "beef":  {"title": "牛肉", "unit": "kg", "unitlabel": "円/kg", "emoji": "🥩"},
    "toilet-paper": {"title": "トイレットペーパー", "unit": "ロール", "unitlabel": "円/ロール", "emoji": "🧻"},
}

def font(sz, bold=True):
    try:
        return ImageFont.truetype(FONT, sz)
    except Exception:
        return ImageFont.truetype(FONT2, sz)

def vgrad(c1, c2):
    """縦グラデ背景"""
    base = Image.new("RGB", (W, H), c1)
    top = Image.new("RGB", (W, H), c2)
    mask = Image.new("L", (W, H))
    md = mask.load()
    for y in range(H):
        v = int(255 * y / H)
        for x in range(0, W, 4):
            md[x, y] = v
    mask = mask.resize((W, H))
    # 高速化: 行ごとに塗る
    base = Image.new("RGB", (W, H))
    px = base.load()
    for y in range(H):
        t = y / H
        r = int(c1[0] * (1 - t) + c2[0] * t)
        g = int(c1[1] * (1 - t) + c2[1] * t)
        b = int(c1[2] * (1 - t) + c2[2] * t)
        for x in range(W):
            px[x, y] = (r, g, b)
    return base

def rrect(d, xy, rad, fill=None, outline=None, width=0):
    d.rounded_rectangle(xy, radius=rad, fill=fill, outline=outline, width=width)

def tsize(d, s, f):
    b = d.textbbox((0, 0), s, font=f)
    return b[2] - b[0], b[3] - b[1]

def ctext(d, cx, y, s, f, fill, stroke=0, sfill=(0, 0, 0)):
    w, h = tsize(d, s, f)
    d.text((cx - w / 2, y), s, font=f, fill=fill, stroke_width=stroke, stroke_fill=sfill)
    return y + h

def wrap(s, n):
    return [s[i:i + n] for i in range(0, len(s), n)][:2]

def dl_image(url):
    for u in [re.sub(r"\?_ex=\d+x\d+", "", url), url]:
        try:
            r = requests.get(u, timeout=20, headers={"Referer": "https://cospa-navi.com/"})
            if r.status_code == 200 and r.content:
                return Image.open(io.BytesIO(r.content)).convert("RGB")
        except Exception:
            pass
    return None

def paste_card(bg, img, cx, cy, size, rad=40):
    """商品画像を角丸カードに収める"""
    card = Image.new("RGB", (size, size), (255, 255, 255))
    if img:
        iw, ih = img.size
        s = size / min(iw, ih)
        img2 = img.resize((int(iw * s), int(ih * s)), Image.LANCZOS)
        img2 = img2.crop(((img2.width - size) // 2, (img2.height - size) // 2,
                          (img2.width - size) // 2 + size, (img2.height - size) // 2 + size))
        card.paste(img2, (0, 0))
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, size, size], radius=rad, fill=255)
    # 影
    sh = Image.new("RGBA", (size + 40, size + 40), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([20, 26, size + 20, size + 26], radius=rad, fill=(0, 0, 0, 90))
    sh = sh.filter(ImageFilter.GaussianBlur(12))
    bg.paste(sh, (int(cx - size / 2 - 20), int(cy - size / 2 - 20)), sh)
    bg.paste(card, (int(cx - size / 2), int(cy - size / 2)), mask)

ORANGE = (255, 90, 31); PINK = (255, 92, 138); YEL = (255, 209, 74)
NAVY = (26, 33, 48); WHITE = (255, 255, 255)

def scene_intro(cat):
    bg = vgrad((255, 138, 76), (255, 92, 138))
    d = ImageDraw.Draw(bg)
    rrect(d, [W/2-230, 150, W/2+230, 250], 50, fill=WHITE)
    ctext(d, W/2, 168, "楽天ふるさと納税", font(46), ORANGE)
    ctext(d, W/2, 430, "コスパ", font(170), WHITE, stroke=8, sfill=NAVY)
    ctext(d, W/2, 620, "ランキング", font(150), YEL, stroke=8, sfill=NAVY)
    rrect(d, [W/2-360, 850, W/2+360, 1000], 40, fill=NAVY)
    ctext(d, W/2, 872, f"【{cat['title']}編】", font(96), WHITE)
    ctext(d, W/2, 1080, "TOP3", font(240), WHITE, stroke=10, sfill=ORANGE)
    ctext(d, W/2, 1420, f"1{cat['unit']}あたりの価格で選ぶ！", font(56), WHITE, stroke=4, sfill=NAVY)
    ctext(d, W/2, 1500, "損しない返礼品はコレ", font(56), WHITE, stroke=4, sfill=NAVY)
    ctext(d, W/2, 1760, "コスパナビ", font(60), WHITE, stroke=4, sfill=NAVY)
    return bg

def scene_rank(cat, rank, m, img):
    cols = {3: ((120, 170, 255), (90, 130, 220), "🥉"), 2: ((190, 195, 205), (150, 155, 170), "🥈"),
            1: ((255, 200, 70), (255, 150, 40), "🥇")}
    c1, c2, _ = cols[rank]
    bg = vgrad(c1, c2)
    d = ImageDraw.Draw(bg)
    # 順位バッジ
    bx, by = 175, 250
    d.ellipse([bx-130, by-130, bx+130, by+130], fill=NAVY)
    ctext(d, bx, by-95, "第", font(48), WHITE)
    ctext(d, bx, by-55, str(rank), font(150), YEL)
    ctext(d, bx, by+78, "位", font(40), WHITE)
    if rank == 1:
        d.polygon([(W/2-140, 470), (W/2-70, 560), (W/2, 470), (W/2+70, 560), (W/2+140, 470),
                   (W/2+110, 620), (W/2-110, 620)], fill=YEL, outline=NAVY)
    # 商品画像
    paste_card(bg, img, W/2, 800, 520)
    # 商品名
    y = 1120
    for line in wrap(m["name"], 15):
        y = ctext(d, W/2, y, line, font(50), NAVY) + 8
    # ヒーロー数値: 円/unit
    rrect(d, [90, 1300, W-90, 1560], 44, fill=WHITE)
    ctext(d, W/2, 1315, "寄付額あたりの単価", font(42), (120, 120, 130))
    ctext(d, W/2, 1370, f"{round(m['unit']):,}", font(170), ORANGE)
    uw, _ = tsize(d, f"{round(m['unit']):,}", font(170))
    d.text((W/2 + uw/2 + 10, 1450), cat["unitlabel"], font=font(56), fill=NAVY)
    # 情報行
    amt = m['amt']; amt = round(amt, 1) if amt < 10 else round(amt)
    info = f"総量 {amt}{cat['unit']}　寄付 {m['price']:,}円"
    ctext(d, W/2, 1620, info, font(52), NAVY, stroke=3, sfill=WHITE)
    star = "★" * round(m['review'])
    ctext(d, W/2, 1700, f"{star} {m['review']:.2f}（{m['reviewCount']:,}件）", font(46), (230, 90, 30), stroke=3, sfill=WHITE)
    rrect(d, [W/2-150, 1790, W/2+150, 1870], 40, fill=NAVY)
    ctext(d, W/2, 1802, f"コスパ {round(m['cospa'])}", font(48), YEL)
    return bg

def scene_outro(cat):
    bg = vgrad((255, 138, 76), (255, 92, 138))
    d = ImageDraw.Draw(bg)
    ctext(d, W/2, 320, "気になる続きは…", font(70), WHITE, stroke=4, sfill=NAVY)
    ctext(d, W/2, 520, "全順位＆", font(96), WHITE, stroke=6, sfill=NAVY)
    ctext(d, W/2, 660, "他カテゴリも！", font(96), WHITE, stroke=6, sfill=NAVY)
    rrect(d, [80, 900, W-80, 1240], 50, fill=WHITE)
    ctext(d, W/2, 950, "コスパナビ", font(150), ORANGE)
    ctext(d, W/2, 1130, "cospa-navi.com", font(72), NAVY)
    ctext(d, W/2, 1360, "「コスパナビ」で検索🔍", font(60), WHITE, stroke=4, sfill=NAVY)
    ctext(d, W/2, 1520, "円/kgで選ぶ、損しない", font(56), WHITE, stroke=4, sfill=NAVY)
    ctext(d, W/2, 1600, "ふるさと納税コスパ比較", font(56), WHITE, stroke=4, sfill=NAVY)
    return bg

def build_video(pngs, durs, out, bgm=None, xf=0.45):
    # 静止カードをクロスフェードで繋ぐ(zoompanのカクつき回避。切替のみ滑らかに動かす)
    inputs = []
    for p, d in zip(pngs, durs):
        inputs += ["-loop", "1", "-t", str(d), "-i", p]
    fc = [f"[{i}:v]fps=30,format=yuv420p,setsar=1,scale={W}:{H}[v{i}]" for i in range(len(pngs))]
    prev, offset, chain = "v0", durs[0] - xf, []
    for i in range(1, len(pngs)):
        lbl = "vout" if i == len(pngs) - 1 else f"x{i}"
        chain.append(f"[{prev}][v{i}]xfade=transition=fade:duration={xf}:offset={offset:.2f}[{lbl}]")
        prev = lbl
        offset += durs[i] - xf
    fcx = ";".join(fc + chain)
    cmd = [FFMPEG, "-y"] + inputs
    if bgm and os.path.exists(bgm):
        cmd += ["-i", bgm, "-filter_complex", fcx, "-map", "[vout]", "-map", f"{len(pngs)}:a",
                "-c:v", "libx264", "-c:a", "aac", "-shortest"]
    else:
        cmd += ["-filter_complex", fcx, "-map", "[vout]", "-c:v", "libx264"]
    cmd += ["-r", "30", "-pix_fmt", "yuv420p", out]
    subprocess.run(cmd, check=True, capture_output=True)

def main():
    slug = sys.argv[1] if len(sys.argv) > 1 else "rice"
    outdir = sys.argv[2] if len(sys.argv) > 2 else os.path.join(BASE, "shorts")
    os.makedirs(outdir, exist_ok=True)
    cat = CATS.get(slug, {"title": slug, "unit": "", "unitlabel": "円", "emoji": ""})
    data = json.load(open(os.path.join(DATA, f"furusato-{slug}.json"), encoding="utf-8"))
    top = sorted(data, key=lambda z: -z["cospa"])[:3]
    imgs = [dl_image(m.get("image", "")) for m in top]
    tmp = tempfile.mkdtemp()
    scenes = [(scene_intro(cat), 3.0),
              (scene_rank(cat, 3, top[2], imgs[2]), 5.0),
              (scene_rank(cat, 2, top[1], imgs[1]), 5.0),
              (scene_rank(cat, 1, top[0], imgs[0]), 7.0),
              (scene_outro(cat), 5.0)]
    pngs, durs = [], []
    for i, (img, dur) in enumerate(scenes):
        p = os.path.join(tmp, f"s{i}.png"); img.save(p); pngs.append(p); durs.append(dur)
    out = os.path.join(outdir, f"furusato-{slug}-top3.mp4")
    bgm = os.path.join(BASE, "shorts", "bgm.mp3")
    build_video(pngs, durs, out, bgm=bgm if os.path.exists(bgm) else None)
    print(f"生成: {out}  ({sum(durs):.0f}秒, BGM={'有' if os.path.exists(bgm) else '無'})")
    # 確認用に1位フレームも書き出し
    scenes[3][0].save(os.path.join(outdir, f"furusato-{slug}-frame1.png"))

if __name__ == "__main__":
    main()
