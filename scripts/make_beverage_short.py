# お茶・ドリンクの「種類で絞って1本あたりで最安比較できる」機能訴求ショート(縦型,約35秒)。
# 実データ(種類別の最安単価)を使う。使い方: python make_beverage_short.py [youtube|threads]
import os, sys, json, tempfile
from PIL import ImageDraw
from make_furusato_short import (font, ctext, tsize, rrect, vgrad, build_video,
                                 W, H, ORANGE, PINK, YEL, NAVY, WHITE)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")

def og():
    img = vgrad((255, 138, 76), (255, 92, 138)); return img, ImageDraw.Draw(img)

def chips(d, items, cx, y, fs=52, gap=18, maxw=980):
    # 中央寄せでチップを折り返し描画
    rows, cur, curw = [], [], 0
    for s in items:
        w = tsize(d, s, font(fs))[0] + 56
        if curw + w > maxw and cur:
            rows.append((cur, curw)); cur, curw = [], 0
        cur.append((s, w)); curw += w + gap
    if cur: rows.append((cur, curw - gap))
    for row, rw in rows:
        x = cx - rw / 2
        for s, w in row:
            rrect(d, [x, y, x + w, y + fs + 34], (fs + 34) // 2, fill=WHITE)
            d.text((x + 28, y + 15), s, font=font(fs), fill=ORANGE)
            x += w + gap
        y += fs + 54
    return y

def scene_intro():
    img, d = og()
    rrect(d, [W/2-240, 150, W/2+240, 250], 50, fill=WHITE)
    ctext(d, W/2, 168, "日用品コスパ分析", font(48), ORANGE)
    ctext(d, W/2, 430, "飲み物は", font(100), WHITE, stroke=7, sfill=NAVY)
    ctext(d, W/2, 580, "1本あたり", font(150), YEL, stroke=8, sfill=NAVY)
    ctext(d, W/2, 760, "で選ぶ時代", font(96), WHITE, stroke=7, sfill=NAVY)
    ctext(d, W/2, 1050, "午後の紅茶も、水も、ウーロン茶も", font(52), WHITE, stroke=4, sfill=NAVY)
    ctext(d, W/2, 1130, "“1本いくら”で最安が分かる", font(56), WHITE, stroke=4, sfill=NAVY)
    ctext(d, W/2, 1760, "コスパナビ", font(60), WHITE, stroke=4, sfill=NAVY)
    return img

def scene_varieties():
    img, d = og()
    ctext(d, W/2, 230, "種類で絞れる", font(96), WHITE, stroke=7, sfill=NAVY)
    y = chips(d, ["午後の紅茶", "ミルクティー", "水・天然水"], W/2, 520)
    y = chips(d, ["ウーロン茶", "緑茶", "麦茶"], W/2, y + 10)
    y = chips(d, ["ジャスミン茶", "炭酸水"], W/2, y + 10)
    ctext(d, W/2, 1500, "飲みたい種類だけに絞って比較", font(54), WHITE, stroke=4, sfill=NAVY)
    return img

def scene_table(rows):
    img, d = og()
    ctext(d, W/2, 210, "1本あたりの最安", font(84), WHITE, stroke=6, sfill=NAVY)
    rrect(d, [70, 360, W-70, 360 + len(rows)*150 + 30], 44, fill=WHITE)
    y = 400
    for name, price in rows:
        d.text((130, y), name, font=font(60), fill=NAVY)
        pr = f"{price}円/本"
        pw = tsize(d, pr, font(66))[0]
        d.text((W-130-pw, y-4), pr, font=font(66), fill=ORANGE)
        y += 150
    ctext(d, W/2, 360 + len(rows)*150 + 90, "種類で絞って“単価が安い順”にするだけ", font(48), WHITE, stroke=4, sfill=NAVY)
    return img

def scene_cheapest():
    img, d = og()
    ctext(d, W/2, 360, "同じ飲み物でも", font(88), WHITE, stroke=6, sfill=NAVY)
    ctext(d, W/2, 500, "最安ショップが", font(88), WHITE, stroke=6, sfill=NAVY)
    ctext(d, W/2, 640, "一発で見つかる", font(100), YEL, stroke=7, sfill=NAVY)
    ctext(d, W/2, 980, "もう楽天で探し回らなくてOK", font(58), WHITE, stroke=4, sfill=NAVY)
    ctext(d, W/2, 1120, "ケース買いのコスパが丸わかり", font(56), WHITE, stroke=4, sfill=NAVY)
    return img

def scene_cta(yt):
    img, d = og()
    ctext(d, W/2, 300, "飲み物のコスパは", font(64), WHITE, stroke=4, sfill=NAVY)
    rrect(d, [50, 540, W-50, 900], 50, fill=WHITE)
    ctext(d, W/2, 590, "コスパナビ", font(72), NAVY)
    ctext(d, W/2, 700, "cospa-navi.com", font(96), ORANGE)
    rrect(d, [W/2-430, 1060, W/2+430, 1210], 40, fill=NAVY)
    ctext(d, W/2, 1090, "「お茶 ドリンク」で検索", font(50), YEL)
    sub = "▼ リンクは 概要欄・コメント欄" if yt else "▼ リンクは プロフィール・スレッド"
    ctext(d, W/2, 1360, sub, font(50), WHITE, stroke=4, sfill=NAVY)
    ctext(d, W/2, 1560, "1本あたりで、損しない買い方", font(54), WHITE, stroke=4, sfill=NAVY)
    return img

def variety_rows():
    d = json.load(open(os.path.join(DATA, "beverage.json"), encoding="utf-8"))
    from categories import CATEGORIES
    vs = CATEGORIES["beverage"]["varieties"]
    want = ["水・天然水", "ミルクティー", "緑茶", "麦茶", "午後の紅茶"]
    rows = []
    for lbl in want:
        kw = next((k for l, k in vs if l == lbl), None)
        if not kw: continue
        items = [m for m in d if m.get("unit") and any(k in m["name"] for k in kw)]
        if items:
            rows.append((lbl, min(m["unit"] for m in items)))
    rows.sort(key=lambda r: r[1])
    return rows[:5]

def main():
    plat = sys.argv[1] if len(sys.argv) > 1 else "youtube"
    yt = plat != "threads"
    outdir = os.path.join(BASE, "shorts"); os.makedirs(outdir, exist_ok=True)
    rows = variety_rows()
    scenes = [
        (scene_intro(), "ペットボトル飲料、1本あたりいくらか意識してますか？コスパナビなら一発でわかります。"),
        (scene_varieties(), "午後の紅茶、水、ウーロン茶、緑茶、麦茶。飲みたい種類で絞って比べられます。"),
        (scene_table(rows), "しかも1本あたりの単価で表示。" + "、".join(f"{n}は{p}円" for n, p in rows[:3]) + "から。安さが一目でわかります。"),
        (scene_cheapest(), "同じ飲み物でも、種類で絞って単価が安い順に並べれば、一番安いショップが一発で見つかります。"),
        (scene_cta(yt), "もう楽天で探し回らなくてOK。コスパナビで、お茶ドリンクと検索してみてください。"
         + ("概要欄のリンクからどうぞ。" if yt else "プロフィールのリンクからどうぞ。")),
    ]
    tmp = tempfile.mkdtemp(); pngs, texts = [], []
    for i, (im, tx) in enumerate(scenes):
        p = os.path.join(tmp, f"s{i}.png"); im.save(p); pngs.append(p); texts.append(tx)
    for i in (0, 2): scenes[i][0].save(os.path.join(outdir, f"beverage-feat-f{i}.png"))
    out = os.path.join(outdir, f"beverage-feature{'' if yt else '-threads'}.mp4")
    bgm = os.path.join(outdir, "bgm.mp3"); bgmp = bgm if os.path.exists(bgm) else None
    speaker = int(os.environ["VV_SPEAKER"]) if os.environ.get("VV_SPEAKER") else (13 if yt else 8)
    import narrate
    if narrate.available():
        total = narrate.build_narrated_video(pngs, texts, out, bgm=bgmp, speaker=speaker)
        print(f"生成(ナレーション付 話者{speaker}): {out}  約{total:.0f}秒")
    else:
        build_video(pngs, [5.0]*len(pngs), out, bgm=bgmp)
        print(f"生成(BGMのみ/VOICEVOX未起動): {out}")

if __name__ == "__main__":
    main()
