# 実質還元率ランキングをスマホ幅(1カラム)で撮影し、説明型Shortのスライド2素材にする。
# 商品写真そのまま(ユーザー選択=リスク許容)。上位カードのみをクリップ。
import os
from playwright.sync_api import sync_playwright

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "shorts"); os.makedirs(OUT, exist_ok=True)
URL = "https://cospa-navi.com/furusato-kanpu?budget=77000"

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 440, "height": 2200}, device_scale_factor=2)
    pg.goto(URL, wait_until="networkidle")
    pg.wait_for_timeout(1500)
    box = pg.eval_on_selector("#klist", """el => {
        const r = el.getBoundingClientRect();
        return {x: r.x + window.scrollX, y: r.y + window.scrollY};
    }""")
    # 先頭3カードぶんをクリップ(スマホ1カラム)
    pg.screenshot(path=os.path.join(OUT, "kanpu-slide2.png"),
                  clip={"x": max(0, box["x"]-6), "y": box["y"]-4, "width": 440, "height": 1380})
    b.close()
print("生成: shorts/kanpu-slide2.png")
