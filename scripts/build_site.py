# robot-cleaner.json 等から静的サイト生成（ハブ＋カテゴリランキング＋商品ページ）。
# 目玉: クライアント側で「満足度⇄価格の重み」を動かすとコスパ値が即再計算されるツール。
import json, os, sys, html as H, hashlib

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
SITE = os.path.join(BASE, "site")
PDIR = os.path.join(SITE, "product"); os.makedirs(PDIR, exist_ok=True)
UPDATED = "2026-07-18"
SITE_NAME = "コスパナビ"
SITE_URL = "https://cospa-navi.com"
ADSENSE = ""  # AdSense承認後にスクリプトを入れる
SITEMAP = []  # (相対URL, 更新日) を収集してsitemap.xml生成

# --- カテゴリ定義（categories.pyから生成。掲載順もここで制御） ---
from categories import CATEGORIES
CAT_ORDER = ["robot-cleaner", "air-purifier"]
CATS = [{"slug": s, "file": s + ".html", "icon": CATEGORIES[s]["icon"],
         "label": CATEGORIES[s]["label"], "genre": CATEGORIES[s]["genre"],
         "desc": CATEGORIES[s]["desc"]} for s in CAT_ORDER]
COMING = ["スティック掃除機", "ポータブル電源", "電子レンジ", "ドライヤー", "モニター", "ワイヤレスイヤホン"]

def pid(m):
    # URLは「ブランド+型番」の安定キーから生成（商品名/代表出品が変わってもURLは不変＝SEO安定）。
    basis = m.get("key") or (m["brand"] + m["name"])
    return "rc" + hashlib.md5(basis.encode("utf-8")).hexdigest()[:8]

def stars(v):
    full = int(v); half = 1 if v - full >= 0.5 else 0
    return "★" * full + ("½" if half else "") + "☆" * (5 - full - half)

def nav(base=""):
    catlinks = "".join(f'<a href="{base}{c["file"]}">{c["label"]}</a>' for c in CATS)
    return (f'<header class="nav"><a class="brand" href="{base}index.html">コスパ<b>ナビ</b></a>'
            f'<nav><a href="{base}index.html">ホーム</a>{catlinks}'
            f'<a href="{base}about.html">コスパ値とは</a><a href="{base}privacy.html">プライバシー</a></nav></header>')

def foot(base=""):
    return (f'<footer class="foot"><p>価格・レビューは楽天市場の情報（{UPDATED}時点）。実際の価格は各ショップでご確認ください。</p>'
            f'<p class="muted">当サイトはアフィリエイト広告を利用しています。'
            f'<a href="{base}privacy.html">プライバシーポリシー</a></p></footer>')

def shell(title, desc, body, base="", head="", path=None, image=None):
    canon = ""
    if path is not None:
        SITEMAP.append(path)
        url = SITE_URL + "/" + path
        img = image or (SITE_URL + "/ogp.png")
        canon = (f'<link rel="canonical" href="{url}">'
                 f'<meta property="og:type" content="website"><meta property="og:site_name" content="{SITE_NAME}">'
                 f'<meta property="og:title" content="{H.escape(title)}"><meta property="og:description" content="{H.escape(desc)}">'
                 f'<meta property="og:url" content="{url}"><meta property="og:image" content="{H.escape(img)}">'
                 f'<meta name="twitter:card" content="summary_large_image">')
    return ("<!doctype html><html lang=\"ja\"><head><meta charset=\"utf-8\">"
            "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
            f"<title>{H.escape(title)}</title><meta name=\"description\" content=\"{H.escape(desc)}\">"
            f"{canon}<link rel=\"stylesheet\" href=\"{base}styles.css\">{ADSENSE}{head}</head><body>"
            + nav(base) + "<main>" + body + "</main>" + foot(base) + "</body></html>")

AD = '<div class="ad">広告スペース（Google AdSense）</div>'

def load(slug):
    d = json.load(open(os.path.join(DATA, slug + ".json"), encoding="utf-8"))
    for m in d:
        m["id"] = pid(m)
    return d

# ================= カテゴリランキングページ（ツール付き） =================
def build_category(cfg):
    data = load(cfg["slug"])
    slim = [{"id": m["id"], "brand": m["brand"], "name": m["name"], "sat": m["sat"],
             "cheap": m["cheap"], "review": m["review"], "rc": m["reviewCount"],
             "price": m["minPrice"], "img": m["image"], "aff": m["affiliate"],
             "offers": [{"m": o["mall"], "p": o["price"], "a": o["affiliate"]} for o in m.get("offers", [])]}
            for m in data]
    DATA_JSON = json.dumps(slim, ensure_ascii=False, separators=(",", ":"))
    maxp = ((max(m["minPrice"] for m in data) + 999) // 1000) * 1000  # step1000に切り上げ（最高額機種も含める）
    body = f"""
<nav class="crumb"><a href="index.html">コスパナビ</a> › {cfg['label']}</nav>
<h1>{cfg['label']} コスパランキング<span class="yr">2026</span></h1>
<p class="lead">{cfg['desc']} <b>{len(data)}機種</b>を比較。<b>スライダーで「満足度重視／価格重視」を調整</b>すると、あなた基準のランキングに変わります。</p>
{AD}
<div class="tool">
  <div class="ctl"><label>重視ポイント</label>
    <div class="slrow"><span>価格</span><input type="range" id="w" min="0" max="100" value="60"><span>満足度</span></div>
    <div class="wlabel"><span id="wtxt">満足度60% / 価格40%</span></div>
  </div>
  <div class="ctl"><label>予算上限</label>
    <div class="slrow"><input type="range" id="b" min="3000" max="{maxp}" step="1000" value="{maxp}"><span id="btxt"></span></div>
  </div>
  <div class="ctl"><label>並び替え</label>
    <div class="sorts">
      <button data-s="cospa" class="on">コスパ順</button><button data-s="price">安い順</button>
      <button data-s="sat">満足度順</button><button data-s="rc">レビュー数順</button>
    </div>
  </div>
</div>
<p class="cnt"><b id="cnt"></b></p>
<div id="list" class="cards"></div>
<p class="note">※コスパ値＝満足度（レビュー評価をレビュー数で信頼補正）×安さ の独自指標（0〜100）。<a href="about.html">算出方法</a></p>
<script id="data" type="application/json">{DATA_JSON}</script>
<script>{TOOL_JS}</script>
"""
    title = f"{cfg['label']}のコスパ最強ランキング2026｜満足度×価格で比較"
    desc = f"{cfg['label']}を満足度（レビュー）と価格から独自コスパ値でランキング。重視ポイントや予算で自分に最適な1台が選べます。"
    ld = {"@context": "https://schema.org", "@type": "ItemList", "name": title,
          "itemListElement": [{"@type": "ListItem", "position": m["rank"],
                               "url": f"{SITE_URL}/product/{m['id']}.html", "name": m["name"]} for m in data[:20]]}
    head = f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>'
    open(os.path.join(SITE, cfg["file"]), "w", encoding="utf-8").write(shell(title, desc, body, head=head, path=cfg["file"]))
    return data

TOOL_JS = r"""
const D=JSON.parse(document.getElementById('data').textContent);
const list=document.getElementById('list');
const yen=v=>'¥'+v.toLocaleString();
const MALL={rakuten:'楽天',yahoo:'Yahoo!',amazon:'Amazon'};
function mallsHtml(offers){
 if(!offers||offers.length<2)return '';
 const min=Math.min(...offers.map(o=>o.p));
 return '<div class="malls">'+offers.map(o=>'<span class="'+(o.p===min?'mlow':'')+'">'+(MALL[o.m]||o.m)+' '+yen(o.p)+'</span>').join('')+'</div>';
}
function buyLabel(offers){
 if(offers&&offers.length>=2){const min=Math.min(...offers.map(o=>o.p));const b=offers.find(o=>o.p===min);return '最安 '+(MALL[b.m]||b.m)+'で見る';}
 const m=offers&&offers[0]?MALL[offers[0].m]||offers[0].m:'楽天';return m+'で価格を見る';
}
const wEl=document.getElementById('w'),bEl=document.getElementById('b');
let sortKey='cospa';
function starHtml(v){let s='';for(let i=1;i<=5;i++){s+= v>=i?'★':(v>=i-0.5?'⯨':'☆');}return s;}
function render(){
 const wsat=(+wEl.value)/100, wch=1-wsat, budget=+bEl.value;
 document.getElementById('wtxt').textContent='満足度'+Math.round(wsat*100)+'% / 価格'+Math.round(wch*100)+'%';
 document.getElementById('btxt').textContent=yen(budget)+'以下';
 let a=D.filter(x=>x.price<=budget).map(x=>({...x,cospa:wsat*x.sat+wch*x.cheap}));
 if(sortKey==='cospa')a.sort((p,q)=>q.cospa-p.cospa);
 else if(sortKey==='price')a.sort((p,q)=>p.price-q.price);
 else if(sortKey==='sat')a.sort((p,q)=>q.sat-p.sat);
 else if(sortKey==='rc')a.sort((p,q)=>q.rc-p.rc);
 document.getElementById('cnt').textContent=a.length+'機種';
 list.innerHTML='';
 a.slice(0,60).forEach((x,i)=>{const c=document.createElement('div');c.className='card';
  c.innerHTML='<div class="cimg"><img loading="lazy" src="'+x.img+'" alt=""></div>'+
   '<div class="cbody"><div class="ctop"><span class="crank">#'+(i+1)+'</span><span class="cbrand">'+x.brand+'</span></div>'+
   '<a class="cname" href="product/'+x.id+'.html">'+x.name+'</a>'+
   '<div class="cstars">'+starHtml(x.review)+' <span class="muted">'+x.review.toFixed(2)+'（'+x.rc.toLocaleString()+'件）</span></div>'+
   '<div class="cprice">'+yen(x.price)+'<span class="muted">〜（最安）</span></div>'+
   mallsHtml(x.offers)+
   '<div class="ccospa">コスパ <b>'+x.cospa.toFixed(0)+'</b><span class="bar"><i style="width:'+Math.max(3,x.cospa)+'%"></i></span></div>'+
   '<a class="buy" href="'+x.aff+'" target="_blank" rel="nofollow sponsored noopener">'+buyLabel(x.offers)+'<span class="pr">PR</span></a></div>';
  list.appendChild(c);});
}
wEl.oninput=render; bEl.oninput=render;
document.querySelectorAll('.sorts button').forEach(b=>b.onclick=()=>{sortKey=b.dataset.s;
 document.querySelectorAll('.sorts button').forEach(x=>x.classList.toggle('on',x.dataset.s===sortKey));render();});
render();
"""

# ================= 商品ページ =================
def build_products(cfg, data):
    N = len(data)
    data_sorted = sorted(data, key=lambda m: m["cospa"], reverse=True)
    rank_of = {m["id"]: i + 1 for i, m in enumerate(data_sorted)}
    MALL = {"rakuten": "楽天市場", "yahoo": "Yahoo!ショッピング", "amazon": "Amazon"}
    for m in data:
        rid = m["id"]; r = rank_of[rid]
        rel = [o for o in data_sorted if o["id"] != rid][:6]
        rel_html = "".join(f'<a href="{o["id"]}.html">{H.escape(o["name"][:24])}</a>' for o in rel)
        offers = m.get("offers", [])
        if len(offers) >= 2:
            lowest = min(o["price"] for o in offers)
            rows = "".join(
                f'<tr class="{"mlow" if o["price"]==lowest else ""}"><td>{MALL.get(o["mall"],o["mall"])}</td>'
                f'<td>¥{o["price"]:,}{"　最安" if o["price"]==lowest else ""}</td>'
                f'<td><a class="buy sm" href="{o["affiliate"]}" target="_blank" rel="nofollow sponsored noopener">見る<span class="pr">PR</span></a></td></tr>'
                for o in offers)
            price_cmp = f'<h2>最安値を比較</h2><table class="kv cmp"><tr><th>モール</th><th>価格</th><th></th></tr>{rows}</table>'
        else:
            price_cmp = ""
        low_mall = MALL.get(offers[0]["mall"], "楽天市場") if offers else "楽天市場"
        body = f"""
<nav class="crumb"><a href="../index.html">コスパナビ</a> › <a href="../{cfg['file']}">{cfg['label']}</a> › {H.escape(m['name'][:20])}</nav>
<div class="pdetail">
  <div class="pimg"><img src="{m['image']}" alt="{H.escape(m['name'])}"></div>
  <div class="pinfo">
    <div class="pbrand">{H.escape(m['brand'])}</div>
    <h1>{H.escape(m['name'])}</h1>
    <p class="prank">{cfg['label']} コスパ <b>{r}位</b> / {N}機種中</p>
    <div class="pstars">{stars(m['review'])} {m['review']:.2f}（{m['reviewCount']:,}件）</div>
    <div class="pprice">{('¥{:,}'.format(m['minPrice']))}<span class="muted">〜（{low_mall}最安）</span></div>
    <a class="buy big" href="{m['affiliate']}" target="_blank" rel="nofollow sponsored noopener">{low_mall}で価格・在庫を見る<span class="pr">PR</span></a>
  </div>
</div>
{price_cmp}
{AD}
<h2>コスパ内訳</h2>
<table class="kv">
<tr><td>コスパ値</td><td><b>{m['cospa']:.0f}</b> / 100</td></tr>
<tr><td>満足度スコア</td><td>{m['sat']:.0f}（ベイズ補正評価 ★{m['bayes']}）</td></tr>
<tr><td>安さスコア</td><td>{m['cheap']:.0f}</td></tr>
<tr><td>最安値</td><td>¥{m['minPrice']:,}</td></tr>
<tr><td>レビュー</td><td>★{m['review']:.2f}（{m['reviewCount']:,}件）</td></tr>
</table>
<p class="note">コスパ値は「満足度（レビュー評価をレビュー数で信頼補正）×安さ」の独自指標です。詳しくは<a href="../about.html">コスパ値とは</a>。</p>
<h2>他の機種と比べる</h2>
<p class="rel">{rel_html}</p>
<p class="src"><a href="../{cfg['file']}">{cfg['label']}ランキングへ戻る</a></p>
"""
        title = f"{m['name'][:30]}のコスパ・価格・レビュー【{cfg['label']}{r}位】"
        desc = f"{m['brand']} {m['name'][:24]}のコスパ値{m['cospa']:.0f}、最安¥{m['minPrice']:,}、レビュー★{m['review']:.2f}（{m['reviewCount']:,}件）。{cfg['label']}コスパ{r}位。"
        ld = {"@context": "https://schema.org", "@type": "Product", "name": m["name"], "brand": m["brand"],
              "image": m["image"], "aggregateRating": {"@type": "AggregateRating", "ratingValue": m["review"],
              "reviewCount": m["reviewCount"], "bestRating": 5}, "offers": {"@type": "Offer",
              "price": m["minPrice"], "priceCurrency": "JPY", "availability": "https://schema.org/InStock"}}
        head = f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>'
        open(os.path.join(PDIR, rid + ".html"), "w", encoding="utf-8").write(
            shell(title, desc, body, base="../", head=head, path="product/" + rid + ".html", image=m["image"]))

# ================= ハブ =================
def build_hub(built):
    cards = ""
    for cfg in CATS:
        n = built.get(cfg["slug"], 0)
        cards += (f'<a class="hcard" href="{cfg["file"]}"><div class="hico">{cfg["icon"]}</div>'
                  f'<div><h3>{cfg["label"]}<span class="n">{n}機種</span></h3><p>{cfg["desc"]}</p></div></a>')
    coming = "".join(f'<span class="soon">{c}</span>' for c in COMING)
    body = f"""
<div class="hero"><h1>コスパナビ<span class="yr">2026</span></h1>
<p class="lead">レビュー満足度と価格から、<b>本当にコスパの良い製品</b>を独自スコアでランキング。<b>重視ポイントや予算を調整</b>して、あなたに最適な1台が見つかります。</p></div>
{AD}
<div class="hgrid">{cards}</div>
<div class="soonbox"><p class="lead">今後追加予定：</p>{coming}</div>
<h2>コスパナビとは</h2>
<p>価格.comのように"全部載せ"で迷わせるのではなく、<b>「満足度×価格」の独自コスパ値</b>と<b>調整できるツール</b>で、あなたの条件に合う最適解を提示します。データは楽天市場のレビュー・価格に基づき毎日更新。詳しくは<a href="about.html">コスパ値とは</a>。</p>
"""
    open(os.path.join(SITE, "index.html"), "w", encoding="utf-8").write(
        shell("コスパナビ2026｜満足度×価格で選ぶ商品コスパ比較", "レビュー満足度と価格から独自コスパ値で製品をランキング。ロボット掃除機など。重視ポイント・予算で最適な1台が選べる。", body, path="index.html"))

# ================= about / privacy =================
def build_static():
    about = f"""
<h1>コスパ値とは（算出方法）</h1>
<p class="lead">コスパナビの「コスパ値」は、<b>満足度（レビュー）と価格</b>から独自に算出する0〜100のスコアです。</p>
{AD}
<h2>計算式</h2>
<p><b>コスパ値 ＝ 満足度スコア × 重み ＋ 安さスコア × 重み</b>（既定は満足度60%・価格40%。サイト上のスライダーで変更可）</p>
<h2>満足度スコア（信頼補正）</h2>
<p>単純な★評価だと「★5.0だがレビュー2件」の商品が上位に来てしまいます。そこで<b>ベイズ平均</b>で、レビュー数が少ない商品は全体平均に引き寄せ、レビューが多い商品ほど実際の評価を反映します。「高評価かつ多レビュー」ほど満足度スコアが高くなります。</p>
<h2>安さスコア</h2>
<p>価格を対数変換して正規化し、<b>安いほど高スコア</b>にしています。</p>
<h2>データについて</h2>
<p>価格・レビューは楽天市場の情報を用い、同一機種は最安値にまとめています。数値は取得時点のもので、実際の価格・在庫は各ショップでご確認ください。当サイトはアフィリエイト広告を利用しています。</p>
"""
    open(os.path.join(SITE, "about.html"), "w", encoding="utf-8").write(
        shell("コスパ値とは（算出方法）｜コスパナビ", "コスパナビの独自コスパ値の算出方法。満足度（ベイズ補正レビュー）×安さで0-100スコア化。", about, path="about.html"))
    privacy = f"""
<h1>プライバシーポリシー</h1>
<p class="lead">当サイト（コスパナビ）における情報の取り扱い方針です。</p>
<h2>広告について</h2>
<p>当サイトは第三者配信の広告サービス（Google AdSense 等）およびアフィリエイトプログラム（楽天アフィリエイト等）を利用しています。これらはCookieを使用し、ユーザーの興味に応じた広告表示や成果測定を行う場合があります（氏名・住所等の個人情報は含みません）。パーソナライズ広告は<a href="https://www.google.com/settings/ads" rel="nofollow">広告設定</a>で無効化できます。</p>
<h2>アフィリエイト</h2>
<p>当サイトの商品リンクは楽天アフィリエイト等の成果報酬型広告です。リンク経由の購入で当サイトが報酬を得る場合がありますが、価格・順位はデータに基づき算出しており、報酬額で操作していません。</p>
<h2>免責事項</h2>
<p>掲載情報は正確性に努めていますが、完全性を保証しません。価格・在庫・仕様は必ず各ショップの最新情報をご確認ください。制定日: {UPDATED}</p>
<h2>お問い合わせ</h2>
<p>lycoris8889@gmail.com</p>
"""
    open(os.path.join(SITE, "privacy.html"), "w", encoding="utf-8").write(
        shell("プライバシーポリシー｜コスパナビ", "コスパナビのプライバシーポリシー。広告・アフィリエイト・Cookieの取り扱いについて。", privacy, path="privacy.html"))

def build_seo():
    urls = "".join(f"<url><loc>{SITE_URL}/{p}</loc><lastmod>{UPDATED}</lastmod></url>" for p in SITEMAP)
    xml = f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>'
    open(os.path.join(SITE, "sitemap.xml"), "w", encoding="utf-8").write(xml)
    robots = f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n"
    open(os.path.join(SITE, "robots.txt"), "w", encoding="utf-8").write(robots)

CSS = r"""
:root{--bg:#f6f7f9;--card:#fff;--ink:#1a2130;--sub:#5a6478;--line:#e6e9ef;--accent:#ff5a1f;--accent2:#2563eb;--bar:#ffe0d3;--chip:#fff1eb}
@media(prefers-color-scheme:dark){:root{--bg:#0f141c;--card:#161d29;--ink:#e8ecf3;--sub:#9aa6b8;--line:#26303f;--accent:#ff7a45;--accent2:#5b8cff;--bar:#3a2418;--chip:#241a14}}
:root[data-theme=dark]{--bg:#0f141c;--card:#161d29;--ink:#e8ecf3;--sub:#9aa6b8;--line:#26303f;--accent:#ff7a45;--accent2:#5b8cff;--bar:#3a2418;--chip:#241a14}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font-family:-apple-system,"Hiragino Kaku Gothic ProN","Yu Gothic",Meiryo,sans-serif;line-height:1.7}
a{color:var(--accent2)}
.nav{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;max-width:1000px;margin:0 auto;padding:12px 16px}
.brand{font-weight:800;text-decoration:none;color:var(--ink);font-size:1.1rem}.brand b{color:var(--accent)}
.nav nav a{margin-left:14px;text-decoration:none;color:var(--sub);font-size:.9rem}.nav nav a:hover{color:var(--accent)}
main{max-width:1000px;margin:0 auto;padding:8px 16px 50px}
h1{font-size:1.6rem;margin:.3em 0}.yr{color:var(--accent);margin-left:.2em}
h2{font-size:1.15rem;margin:1.3em 0 .4em;border-left:4px solid var(--accent);padding-left:8px}
.lead{color:var(--sub)}.note,.muted{color:var(--sub);font-size:.85rem}
.crumb{font-size:.82rem;color:var(--sub);margin:.4em 0}.crumb a{text-decoration:none}
.ad{border:1px dashed var(--line);color:var(--sub);text-align:center;padding:14px;border-radius:10px;font-size:.85rem;margin:14px 0}
.tool{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px 16px;margin:14px 0;display:grid;gap:12px}
.tool label{font-weight:700;font-size:.9rem;display:block;margin-bottom:4px}
.slrow{display:flex;align-items:center;gap:10px}.slrow span{font-size:.82rem;color:var(--sub);white-space:nowrap}
input[type=range]{flex:1;accent-color:var(--accent)}
.wlabel{font-size:.82rem;color:var(--accent);font-weight:700;margin-top:2px}
.sorts{display:flex;flex-wrap:wrap;gap:6px}
.sorts button{border:1px solid var(--line);background:var(--bg);color:var(--ink);border-radius:16px;padding:5px 12px;font-size:.85rem;cursor:pointer}
.sorts button.on{background:var(--accent);color:#fff;border-color:var(--accent)}
.cnt{font-weight:700;font-size:.9rem;margin:.4em 0}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px}
.card{display:flex;gap:12px;background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px;overflow:hidden}
.cimg{flex:0 0 88px;height:88px;background:#fff;border-radius:8px;overflow:hidden;display:flex;align-items:center;justify-content:center}
.cimg img{max-width:100%;max-height:100%;object-fit:contain}
.cbody{flex:1;min-width:0}.ctop{display:flex;align-items:center;gap:8px}
.crank{font-weight:800;color:var(--accent)}.cbrand{font-size:.75rem;color:var(--sub)}
.cname{display:block;font-weight:700;text-decoration:none;color:var(--ink);font-size:.92rem;margin:2px 0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.cname:hover{color:var(--accent2)}
.cstars{color:#f5a623;font-size:.85rem}.cstars .muted{color:var(--sub)}
.cprice{font-weight:800;font-size:1.05rem;margin:2px 0}.cprice .muted{font-weight:400;font-size:.75rem}
.malls{display:flex;flex-wrap:wrap;gap:4px 8px;margin:2px 0}.malls span{font-size:.72rem;color:var(--sub)}.malls .mlow{color:var(--accent);font-weight:700}
.buy.sm{padding:4px 12px;font-size:.8rem;margin:0}
.cmp th{text-align:left;color:var(--sub);font-size:.8rem;padding:6px 8px;border-bottom:1px solid var(--line)}
.cmp tr.mlow td{color:var(--accent);font-weight:700}
.ccospa{font-size:.82rem;color:var(--sub);display:flex;align-items:center;gap:6px}.ccospa b{color:var(--accent);font-size:1rem}
.bar{flex:1;height:6px;background:var(--bar);border-radius:4px;overflow:hidden;max-width:120px}.bar i{display:block;height:100%;background:var(--accent)}
.buy{display:inline-block;margin-top:6px;background:var(--accent);color:#fff;text-decoration:none;padding:7px 14px;border-radius:8px;font-weight:700;font-size:.88rem;position:relative}
.buy .pr{font-size:.6rem;opacity:.8;margin-left:6px;vertical-align:middle}
.buy.big{display:block;text-align:center;padding:12px;font-size:1rem;margin-top:10px}
.hero{margin:.4em 0 1em}.hgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px;margin:14px 0}
.hcard{display:flex;gap:12px;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px;text-decoration:none;color:var(--ink)}
.hcard:hover{border-color:var(--accent)}.hico{font-size:1.8rem}.hcard h3{margin:.1em 0;font-size:1.05rem}.hcard .n{color:var(--accent);font-size:.8rem;margin-left:8px}.hcard p{margin:.2em 0 0;color:var(--sub);font-size:.85rem}
.soonbox{margin:16px 0}.soon{display:inline-block;background:var(--chip);color:var(--sub);border-radius:16px;padding:4px 12px;margin:3px;font-size:.82rem}
.pdetail{display:flex;gap:18px;flex-wrap:wrap}.pimg{flex:0 0 240px;max-width:100%;background:#fff;border-radius:12px;padding:10px}.pimg img{width:100%;object-fit:contain}
.pinfo{flex:1;min-width:240px}.pbrand{color:var(--sub);font-size:.85rem}.pinfo h1{font-size:1.25rem;margin:.2em 0}
.prank{color:var(--accent);font-weight:700}.pstars{color:#f5a623}.pprice{font-size:1.6rem;font-weight:800;margin:.2em 0}.pprice .muted{font-size:.8rem;font-weight:400}
.kv{width:100%;margin:.4em 0}.kv td{border-bottom:1px solid var(--line);padding:8px}.kv td:first-child{color:var(--sub);width:42%}
.rel{display:flex;flex-wrap:wrap;gap:8px}.rel a{font-size:.85rem;border:1px solid var(--line);border-radius:8px;padding:5px 10px;text-decoration:none}
.src{margin-top:14px}.foot{max-width:1000px;margin:0 auto;padding:20px 16px 40px;color:var(--sub);font-size:.8rem;border-top:1px solid var(--line)}
@media(max-width:520px){.cards{grid-template-columns:1fr}}
"""

if __name__ == "__main__":
    built = {}
    for cfg in CATS:
        data = build_category(cfg)
        build_products(cfg, data)
        built[cfg["slug"]] = len(data)
    build_hub(built)
    build_static()
    build_seo()
    # styles.css
    open(os.path.join(SITE, "styles.css"), "w", encoding="utf-8").write(CSS)
    total = sum(built.values())
    print(f"生成: index / {len(CATS)}カテゴリ / product×{total} / about / privacy / sitemap({len(SITEMAP)}URL) / robots / styles.css")
