# YouTubeチャンネルアイコン(800x800・円形表示前提)を生成 → shorts/cospanavi-icon.png
# サイトブランド(オレンジ×ネイビー×イエロー)のPOPなコスパナビロゴ。
import os
from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "shorts"); os.makedirs(OUT, exist_ok=True)
S = 800
FONT = "C:/Windows/Fonts/BIZ-UDGothicB.ttc"
ORANGE = (255, 90, 31); PINK = (255, 92, 138); YEL = (255, 209, 74)
NAVY = (26, 33, 48); WHITE = (255, 255, 255)

def font(sz):
    return ImageFont.truetype(FONT, sz)

def ctext(d, cx, y, s, f, fill, stroke=0, sfill=NAVY):
    b = d.textbbox((0, 0), s, font=f, stroke_width=stroke)
    d.text((cx - (b[2]-b[0])/2 - b[0], y), s, font=f, fill=fill, stroke_width=stroke, stroke_fill=sfill)
    return b[3]-b[1]

img = Image.new("RGB", (S, S))
px = img.load()
for y in range(S):  # 縦グラデ
    t = y / S
    c = (int(255*(1-t)+255*t), int(138*(1-t)+92*t), int(76*(1-t)+138*t))
    for x in range(S):
        px[x, y] = c
d = ImageDraw.Draw(img)

# 円形フレーム(白リング)
d.ellipse([26, 26, S-26, S-26], outline=WHITE, width=14)

# 王冠(ランキング=コスパ最強の象徴)
cx = S/2
d.polygon([(cx-150, 235), (cx-75, 320), (cx, 210), (cx+75, 320), (cx+150, 235),
           (cx+118, 390), (cx-118, 390)], fill=YEL, outline=NAVY)
for dx in (-118, 0, 118):  # 王冠の玉
    d.ellipse([cx+dx-16, 218-16, cx+dx+16, 218+16], fill=WHITE, outline=NAVY, width=3)

# ロゴ「コスパ」「ナビ」
ctext(d, cx, 420, "コスパ", font(150), WHITE, stroke=10)
ctext(d, cx, 570, "ナビ", font(150), YEL, stroke=10)

img.save(os.path.join(OUT, "cospanavi-icon.png"))
# 円形プレビュー(実際の見え方確認用)
mask = Image.new("L", (S, S), 0)
ImageDraw.Draw(mask).ellipse([0, 0, S, S], fill=255)
prev = Image.new("RGBA", (S, S), (255, 255, 255, 0)); prev.paste(img, (0, 0), mask)
prev.save(os.path.join(OUT, "cospanavi-icon-circle.png"))
print("生成: shorts/cospanavi-icon.png (800x800) + 円形プレビュー")
