# YouTubeチャンネルバナー(2560x1440)を生成 → shorts/cospanavi-banner.png
# 重要テキストは全デバイス表示の安全域(中央1546x423)内に収める。
import os
from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "shorts"); os.makedirs(OUT, exist_ok=True)
Wd, Hd = 2560, 1440
FONT = "C:/Windows/Fonts/BIZ-UDGothicB.ttc"
ORANGE = (255, 90, 31); PINK = (255, 92, 138); YEL = (255, 209, 74)
NAVY = (26, 33, 48); WHITE = (255, 255, 255)

def font(sz):
    return ImageFont.truetype(FONT, sz)

def ctext(d, cx, y, s, f, fill, stroke=0, sfill=NAVY):
    b = d.textbbox((0, 0), s, font=f, stroke_width=stroke)
    d.text((cx - (b[2]-b[0])/2 - b[0], y), s, font=f, fill=fill, stroke_width=stroke, stroke_fill=sfill)

img = Image.new("RGB", (Wd, Hd))
px = img.load()
for y in range(Hd):  # 縦グラデ
    t = y / Hd
    c = (int(255*(1-t)+255*t), int(150*(1-t)+92*t), int(80*(1-t)+138*t))
    for x in range(Wd):
        px[x, y] = c
d = ImageDraw.Draw(img)

# 外側の飾り(安全域の外。うっすら円・¥)
for (x, y, r, col) in [(300, 300, 120, (255,255,255)), (2250, 1150, 150, (255,255,255)),
                       (180, 1150, 80, YEL), (2380, 300, 90, YEL), (2100, 800, 60, (255,255,255))]:
    d.ellipse([x-r, y-r, x+r, y+r], outline=col, width=8)
for (x, y) in [(430, 950), (2150, 420), (350, 620)]:
    ctext(d, x, y, "¥", font(140), (255, 255, 255))

# ===== 安全域(中央 x:507-2053, y:509-931)=====
cx = Wd // 2
# 王冠
d.polygon([(cx-140, 560), (cx-70, 640), (cx, 535), (cx+70, 640), (cx+140, 560),
           (cx+110, 705), (cx-110, 705)], fill=YEL, outline=NAVY)
for dx in (-110, 0, 110):
    d.ellipse([cx+dx-15, 543-15, cx+dx+15, 543+15], fill=WHITE, outline=NAVY, width=3)
# ロゴ
ctext(d, cx, 700, "コスパナビ", font(150), WHITE, stroke=11)
# タグライン
ctext(d, cx, 878, "円/kgで選ぶ、損しない ふるさと納税・家電のコスパ比較", font(50), NAVY)
# URLピル
pw = 560
d.rounded_rectangle([cx-pw/2, 968, cx+pw/2, 1058], radius=45, fill=NAVY)
ctext(d, cx, 985, "cospa-navi.com", font(56), YEL)

img.save(os.path.join(OUT, "cospanavi-banner.png"))
# 安全域プレビュー(モバイル表示相当=中央1546x423を切り出し)
img.crop((cx-773, 720-211, cx+773, 720+211)).save(os.path.join(OUT, "cospanavi-banner-safe.png"))
print("生成: shorts/cospanavi-banner.png (2560x1440) + 安全域プレビュー")
