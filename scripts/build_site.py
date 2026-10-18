# robot-cleaner.json 等から静的サイト生成（ハブ＋カテゴリランキング＋商品ページ）。
# 目玉: クライアント側で「満足度⇄価格の重み」を動かすとコスパ値が即再計算されるツール。
import json, os, sys, html as H, hashlib, datetime

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
SITE = os.path.join(BASE, "site")
PDIR = os.path.join(SITE, "product"); os.makedirs(PDIR, exist_ok=True)
CDIR = os.path.join(SITE, "compare"); os.makedirs(CDIR, exist_ok=True)
UPDATED = datetime.date.today().isoformat()  # ビルド日を自動反映（毎日の更新で日付が進む）
SITE_NAME = "コスパナビ"
SITE_URL = "https://cospa-navi.com"
# AdSense（rankingsjpと同一アカウント pub-8706760047070867。審査用に全ページ<head>へ設置）
ADSENSE = '<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-8706760047070867" crossorigin="anonymous"></script>'
# バリューコマース LinkSwitch: 提携済みモール(Yahoo!ショッピング等)へのリンクを自動でアフィリ化
LINKSWITCH = '<script type="text/javascript">var vc_pid="892664777";</script><script type="text/javascript" src="//aml.valuecommerce.com/vcdal.js" async></script>'
ADSENSE_PUB = "pub-8706760047070867"
SITE_VERIFY = "9Lq7hmAO3CeIlcT6nM2tB2_AksHlZsugoZ_VIeeY5Dc"  # Search Console HTMLメタタグ認証
# Search ConsoleはメタタグSITE_VERIFYで認証済のためHTMLファイル方式は不要（空でOK）
GOOGLE_VERIFY_FILES = []
SITEMAP = []  # (相対URL, 更新日) を収集してsitemap.xml生成

# --- カテゴリ定義（categories.pyから生成。掲載順もここで制御） ---
from categories import CATEGORIES
from guides import GUIDES
from compares import COMPARES
CAT_ORDER = ["robot-cleaner", "air-purifier", "portable-power", "stick-cleaner",
             "microwave", "hair-dryer", "monitor", "earbuds", "humidifier", "kettle",
             "refrigerator", "washer", "rice-cooker", "canister-cleaner", "tv", "tablet", "smartwatch",
             "coffee-maker", "kotatsu", "printer", "fan"]
NICHIYO_ORDER = ["toilet-paper", "rice", "tissue", "detergent"]   # 日用品(section=nichiyo)。別ハブ /nichiyo に出す
ALL_ORDER = CAT_ORDER + NICHIYO_ORDER
CATS = [{"slug": s, "file": s + ".html", "icon": CATEGORIES[s]["icon"],
         "label": CATEGORIES[s]["label"], "genre": CATEGORIES[s]["genre"],
         "section": CATEGORIES[s].get("section", "kaden"),
         "desc": CATEGORIES[s]["desc"]} for s in ALL_ORDER]
KADEN_CATS = [c for c in CATS if c["section"] == "kaden"]
NICHIYO_CATS = [c for c in CATS if c["section"] == "nichiyo"]
COMING = ["ゲーミングチェア", "コーヒーミル", "食洗機"]
NICHIYO_COMING = ["ゴミ袋", "キッチンペーパー", "ラップ", "乾電池", "柔軟剤"]

def pid(m):
    # URLは「ブランド+型番」の安定キーから生成（商品名/代表出品が変わってもURLは不変＝SEO安定）。
    basis = m.get("key") or (m["brand"] + m["name"])
    return "rc" + hashlib.md5(basis.encode("utf-8")).hexdigest()[:8]

def stars(v):
    full = int(v); half = 1 if v - full >= 0.5 else 0
    return "★" * full + ("½" if half else "") + "☆" * (5 - full - half)

def price_stats(data):
    # 「〇〇 相場/値段」検索の意図に答えるため、実売最安値の分布を算出（最安/中央値/ボリュームゾーン25-75%）
    ps = sorted(m["minPrice"] for m in data)
    n = len(ps)
    def pct(q):
        if n == 1:
            return ps[0]
        i = q * (n - 1); lo = int(i); frac = i - lo
        return ps[lo] if lo + 1 >= n else round(ps[lo] + (ps[lo + 1] - ps[lo]) * frac)
    return ps[0], pct(0.5), pct(0.25), pct(0.75)

def U(file):
    # 内部リンクを絶対パス・拡張子なしに統一（Cloudflareのクリーンurlと一致させリダイレクトを避ける）
    if file in ("index.html", "index", "", "/"):
        return "/"
    f = file[:-5] if file.endswith(".html") else file
    return "/" + f.lstrip("/")

def nav(base=""):
    # 全ページ共通のグローバルナビ(スマホは横スクロール・上部固定)。主要セクションへ即移動。
    return ('<header class="navwrap"><div class="nav"><a class="brand" href="/">コスパ<b>ナビ</b></a>'
            '<nav class="gnav">'
            '<span class="ggrp"><span class="gcap">ふるさと納税</span><a href="/furusato">コスパ分析</a><a href="/furusato-kanpu">実質還元率</a></span>'
            '<span class="gdiv"></span>'
            '<span class="ggrp"><span class="gcap">家電</span><a href="/#ranking">ランキング</a><a href="/#compare">徹底比較</a></span>'
            '<span class="gdiv"></span>'
            '<span class="ggrp"><span class="gcap">日用品</span><a href="/nichiyo#ranking">ランキング</a><a href="/nichiyo#compare">徹底比較</a></span>'
            '<span class="gdiv"></span>'
            '<a class="gabout" href="/about">コスパとは</a>'
            '</nav></div></header>')

def foot(base=""):
    catlinks = "".join(f'<a href="{U(c["file"])}">{c["label"]}</a>' for c in CATS)
    return (f'<footer class="foot"><nav class="fcats">{catlinks}</nav>'
            f'<p>価格・レビューは楽天市場・Yahoo!ショッピングの情報（{UPDATED}時点）。実際の価格は各ショップでご確認ください。</p>'
            f'<p class="muted">当サイトはアフィリエイト広告を利用しています。'
            f'<a href="/privacy">プライバシーポリシー</a></p></footer>')

CAT_MAP = {c["slug"]: c for c in CATS}
# 関連カテゴリ（トピッククラスター）＝内部リンクで関連ページ群の評価を底上げ（SEO）
CLUSTERS = [
    ["robot-cleaner", "stick-cleaner", "canister-cleaner"],  # 掃除機
    ["microwave", "rice-cooker", "kettle"],                  # キッチン家電
    ["air-purifier", "humidifier"],                          # 空気・季節
    ["refrigerator", "washer"],                              # 大型家電
    ["monitor", "tablet", "tv", "earbuds"],                  # デジタル・AV
    ["hair-dryer", "portable-power"],                        # 生活・その他
    ["toilet-paper", "rice", "tissue", "detergent"],         # 日用品
]
SLUG2CLUSTER = {s: i for i, cl in enumerate(CLUSTERS) for s in cl}
POPULAR = ["robot-cleaner", "air-purifier", "tablet", "hair-dryer", "microwave"]

def related_cats(slug, k=4):
    out = []
    ci = SLUG2CLUSTER.get(slug)
    if ci is not None:
        out += [s for s in CLUSTERS[ci] if s != slug]
    for s in POPULAR:  # クラスターが小さい場合は人気カテゴリで補完（内部リンクの辺を増やす）
        if len(out) >= k:
            break
        if s != slug and s not in out:
            out.append(s)
    return out[:k]

def render_related(slug):
    rs = [s for s in related_cats(slug) if s in CAT_MAP]
    if not rs:
        return ""
    cards = "".join(
        f'<a class="hcard" href="{U(CAT_MAP[s]["file"])}"><div class="hico">{CAT_MAP[s]["icon"]}</div>'
        f'<div><h3>{CAT_MAP[s]["label"]}</h3><p>{H.escape(CAT_MAP[s]["desc"][:44])}</p></div></a>'
        for s in rs)
    return f'<h2>関連カテゴリのランキング</h2><div class="hgrid">{cards}</div>'

def breadcrumb_ld(pairs):
    # pairs=[(name, url or None)] 末尾=現在ページ。SERPのパンくず表示＆サイト構造の伝達に効く
    items = []
    for i, (name, url) in enumerate(pairs, 1):
        it = {"@type": "ListItem", "position": i, "name": name}
        if url:
            it["item"] = url
        items.append(it)
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": items}

def shell(title, desc, body, base="", head="", path=None, image=None, noindex=False):
    canon = ""
    if path is not None:
        cpath = U(path)   # 拡張子なしの絶対パス（"/"や"/robot-cleaner"）
        if not noindex:   # noindexページ(薄い商品詳細)はsitemapに載せない
            SITEMAP.append(cpath)
        url = SITE_URL + cpath
        img = image or (SITE_URL + "/ogp.png")
        canon = (f'<link rel="canonical" href="{url}">'
                 f'<meta property="og:type" content="website"><meta property="og:site_name" content="{SITE_NAME}">'
                 f'<meta property="og:title" content="{H.escape(title)}"><meta property="og:description" content="{H.escape(desc)}">'
                 f'<meta property="og:url" content="{url}"><meta property="og:image" content="{H.escape(img)}">'
                 f'<meta name="twitter:card" content="summary_large_image">')
    # 薄い量産ページ(商品詳細4199枚)はnoindex,follow=検索非掲載・リンクは辿らせる。AdSense「有用性の低いコンテンツ」対策
    robots = '<meta name="robots" content="noindex,follow">' if noindex else ""
    verify = f'<meta name="google-site-verification" content="{SITE_VERIFY}">' if SITE_VERIFY else ""
    return ("<!doctype html><html lang=\"ja\"><head><meta charset=\"utf-8\">"
            "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
            f"<title>{H.escape(title)}</title><meta name=\"description\" content=\"{H.escape(desc)}\">"
            f"{robots}{verify}{canon}<link rel=\"stylesheet\" href=\"/styles.css?v={CSS_VER}\">{ADSENSE}{head}</head><body>"
            + nav(base) + GO5 + "<main>" + body + "</main>" + foot(base) + LINKSWITCH + "</body></html>")

# 「5と0のつく日」(毎月5/10/15/20/25/30日)は楽天カードでポイントアップ=ふるさと納税が特にお得→その日だけ告知バナー表示
GO5 = ('<div id="go5bar"></div>'
       '<script>(function(){try{var d=new Date().getDate();'
       'if([5,10,15,20,25,30].indexOf(d)>=0){var b=document.getElementById("go5bar");b.className="go5";'
       'b.innerHTML=\'<a href="/furusato"><span class="gift">🎁</span>本日は<b>5と0のつく日</b>！楽天カードで楽天ふるさと納税がポイントアップ<span class="gbtn">お得な返礼品を見る ▶</span></a>\';}}catch(e){}})();</script>')

AD = ''

# 楽天お買い物マラソン告知バナー(トップのふるさと⇔家電の間)。開催中だけTrueにしてビルドするとONになる。
# お買い物マラソンは不定期(月1-2回/数日間)なので、開催に合わせて MARATHON_ON を切り替える運用。
MARATHON_ON = True
# 楽天アフィリエイトID(hgc手動リンク用の4分割ドット形式)。ローカルはsecrets、CIは環境変数。
try:
    from secrets import RAKUTEN_AFFILIATE_ID as _AFFID
except Exception:
    _AFFID = os.environ.get("RAKUTEN_AFFILIATE_ID", "")
def rakuten_afl(url):
    # 任意の楽天ページを成果計測付きアフィリンクに変換(楽天市場トップへ直リンクでも成果は成立)
    import urllib.parse as _up
    e = _up.quote(url, safe="")
    return f"https://hb.afl.rakuten.co.jp/hgc/{_AFFID}/?pc={e}&m={e}" if _AFFID else url
# マラソンバナーは内部ページではなく楽天市場へ直接送客(開催中は買い回りで全市場が対象→直リンクでアフィリ成立)
MARATHON_HREF = rakuten_afl("https://www.rakuten.co.jp/")
MARATHON = (f'<a class="mbanner" href="{MARATHON_HREF}" target="_blank" rel="nofollow sponsored noopener"><span class="mico">🎉</span>'
            '<span class="mtxt"><span class="mtag">楽天お買い物マラソン 開催中</span>'
            '<span class="mmain">掲載アイテムがお得！<b>最大半額クーポン</b>・買い回りでポイント最大<b>10倍</b></span></span>'
            '<span class="mgo">楽天市場でお得に買う →</span></a>') if MARATHON_ON else ''

def load(slug):
    d = json.load(open(os.path.join(DATA, slug + ".json"), encoding="utf-8"))
    for m in d:
        m["id"] = pid(m)
    return d

# 選び方ガイド＋FAQ（ランキング下部の独自コンテンツ）。(HTML, FAQPage構造化データ) を返す
def render_guide(slug, label):
    g = GUIDES.get(slug)
    if not g:
        return "", None
    pts = "".join(f'<div class="gpt"><h3>{H.escape(t)}</h3><p>{H.escape(d)}</p></div>' for t, d in g["points"])
    faqs = "".join(f'<div class="faq"><h3>Q. {H.escape(q)}</h3><p>A. {H.escape(a)}</p></div>' for q, a in g["faq"])
    html = (f'<section class="guide"><h2>{H.escape(label)}の選び方</h2>'
            f'<div class="gpts">{pts}</div>'
            f'<h2>よくある質問</h2><div class="faqs">{faqs}</div></section>')
    ld = {"@context": "https://schema.org", "@type": "FAQPage",
          "mainEntity": [{"@type": "Question", "name": q,
                          "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in g["faq"]]}
    return html, ld

# 「価格帯別おすすめ」＋「安い順TOP5」の静的ブロック。「〇〇 安い/値段/おすすめ/相場」検索に直答する実コンテンツ（SEO）。
def render_picks(cfg, data):
    label = cfg["label"]
    lo, med, q1, q3 = price_stats(data)
    # 価格帯別おすすめ（各予算帯の最コスパ機種）
    bands = [("安く抑えたい", f"〜¥{q1:,}", lambda p: p <= q1),
             ("価格と満足のバランス", f"¥{q1:,}〜¥{q3:,}", lambda p: q1 < p <= q3),
             ("高性能・上位モデル", f"¥{q3:,}〜", lambda p: p > q3)]
    cards = ""
    for name, rng, cond in bands:
        cand = [m for m in data if cond(m["minPrice"])]
        if not cand:
            continue
        m = max(cand, key=lambda x: x["cospa"])
        cards += (f'<div class="gpt"><h3>{name}<span class="pk-rng">{rng}</span></h3>'
                  f'<a class="pk-nm" href="/product/{m["id"]}">{H.escape(m["name"][:34])}</a>'
                  f'<div class="pk-meta">¥{m["minPrice"]:,}／コスパ{m["cospa"]:.0f}／★{m["review"]:.2f}（{m["reviewCount"]:,}）</div>'
                  f'<a class="buy sm" href="{m["affiliate"]}" target="_blank" rel="nofollow sponsored noopener">最安値を見る<span class="pr">PR</span></a></div>')
    band_sec = (f'<h2>{label}の価格帯別おすすめ（予算別ベストコスパ）</h2>'
                f'<p class="note">価格相場をもとに予算帯を3段階に分け、各帯で最もコスパの良い機種を選びました。</p>'
                f'<div class="gpts">{cards}</div>') if cards else ""
    # 安い順TOP5（安いだけの地雷を除き、レビュー多数＆コスパ60以上の「安くてコスパ良い」機種に限定）
    rel = [m for m in data if m["reviewCount"] >= 10 and m["cospa"] >= 60]
    if len(rel) < 5:
        rel = [m for m in data if m["reviewCount"] >= 10] or data
    cheap = sorted(rel, key=lambda m: m["minPrice"])[:5]
    rows = "".join(
        f'<tr><td class="pk-r">{i+1}</td>'
        f'<td><a href="/product/{m["id"]}">{H.escape(m["name"][:28])}</a> <span class="pk-br">{H.escape(m["brand"])}</span></td>'
        f'<td class="pk-p">¥{m["minPrice"]:,}</td><td class="pk-cc">コスパ{m["cospa"]:.0f}</td>'
        f'<td><a class="buy sm" href="{m["affiliate"]}" target="_blank" rel="nofollow sponsored noopener">見る<span class="pr">PR</span></a></td></tr>'
        for i, m in enumerate(cheap))
    cheap_sec = (f'<h2>{label}の安い順TOP5（最安値でコスパの良い格安モデル）</h2>'
                 f'<table class="kv pk"><tr><th></th><th>機種</th><th>最安値</th><th></th><th></th></tr>{rows}</table>')
    return f'<section class="picks">{band_sec}{cheap_sec}</section>'

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
    GUIDE_HTML, faq_ld = render_guide(cfg["slug"], cfg["label"])
    lo, med, q1, q3 = price_stats(data)
    sec = CATEGORIES[cfg["slug"]].get("section", "kaden")
    unit = "品" if sec == "nichiyo" else "機種"
    soba = (f'<div class="soba"><span class="sicon">💰</span><div><b>{cfg["label"]}の価格相場</b>'
            f'<span class="smt">（{UPDATED}時点・{len(data)}{unit}の実売最安値より）</span><br>'
            f'最安 <b>¥{lo:,}</b> ／ 相場（中央値） <b>¥{med:,}</b> ／ ボリュームゾーン <b>¥{q1:,}〜¥{q3:,}</b></div></div>')
    crumb = ('<a href="/">コスパナビ</a> › <a href="/nichiyo">日用品</a> › ' + cfg["label"]) if sec == "nichiyo" \
            else ('<a href="/">コスパナビ</a> › ' + cfg["label"])
    body = f"""
<nav class="crumb">{crumb}</nav>
<h1>{cfg['label']} コスパ最強ランキング＆価格相場<span class="yr">2026</span></h1>
<p class="lead">{cfg['desc']} <b>{len(data)}{unit}</b>を、価格相場と満足度から比較。<b>スライダーで「満足度重視／価格重視」を調整</b>すると、あなた基準のランキングに変わります。</p>
{soba}
{render_compare_box(cfg['slug'])}
{render_brand_links(cfg['slug'])}
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
<p class="note">※コスパ値＝満足度（レビュー評価をレビュー数で信頼補正）×安さ の独自指標（0〜100）。<a href="/about">算出方法</a></p>
{AD}
{render_picks(cfg, data)}
<a class="ebridge" href="/furusato"><span class="eico">🍚</span><div><h3>年末はふるさと納税でもっとお得に</h3><p>実質2,000円で返礼品がもらえる「ふるさと納税」。控除上限シミュレーター＆実質還元率ランキングで、あなたに一番お得な返礼品が見つかります。</p></div><span class="ego">見る →</span></a>
{GUIDE_HTML}
{render_related(cfg['slug'])}
<script id="data" type="application/json">{DATA_JSON}</script>
<script>window.UNIT={json.dumps(unit, ensure_ascii=False)};</script>
<script>{TOOL_JS}</script>
"""
    title = f"{cfg['label']}のコスパ最強ランキング2026｜価格相場・安い順に比較"
    desc = (f"{cfg['label']}の価格相場は最安¥{lo:,}〜中央値¥{med:,}。満足度×価格の独自コスパ値で"
            f"{len(data)}機種を安い順・コスパ順に比較し、値段とおすすめが一目で分かります。楽天・Yahoo!の最安値も掲載。")
    ld = {"@context": "https://schema.org", "@type": "ItemList", "name": title,
          "itemListElement": [{"@type": "ListItem", "position": m["rank"],
                               "url": f"{SITE_URL}/product/{m['id']}", "name": m["name"]} for m in data[:20]]}
    bc_items = [("コスパナビ", SITE_URL + "/")]
    if sec == "nichiyo":
        bc_items.append(("日用品", SITE_URL + "/nichiyo"))
    bc_items.append((cfg["label"], None))
    ld_list = [ld, breadcrumb_ld(bc_items)]
    if faq_ld:
        ld_list.append(faq_ld)
    head = "".join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in ld_list)
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
 document.getElementById('cnt').textContent=a.length+(window.UNIT||'機種');
 list.innerHTML='';
 a.slice(0,60).forEach((x,i)=>{const c=document.createElement('div');c.className='card';
  c.innerHTML='<div class="cimg"><img loading="lazy" src="'+x.img+'" alt=""></div>'+
   '<div class="cbody"><div class="ctop"><span class="crank">#'+(i+1)+'</span><span class="cbrand">'+x.brand+'</span></div>'+
   '<a class="cname" href="/product/'+x.id+'">'+x.name+'</a>'+
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
        rel_html = "".join(f'<a href="/product/{o["id"]}">{H.escape(o["name"][:24])}</a>' for o in rel)
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
<nav class="crumb"><a href="/">コスパナビ</a> › <a href="{U(cfg['file'])}">{cfg['label']}</a> › {H.escape(m['name'][:20])}</nav>
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
<p class="note">コスパ値は「満足度（レビュー評価をレビュー数で信頼補正）×安さ」の独自指標です。詳しくは<a href="/about">コスパ値とは</a>。</p>
<h2>他の機種と比べる</h2>
<p class="rel">{rel_html}</p>
<p class="src"><a href="{U(cfg['file'])}">{cfg['label']}ランキングへ戻る</a></p>
"""
        title = f"{m['name'][:30]}のコスパ・価格・レビュー【{cfg['label']}{r}位】"
        desc = f"{m['brand']} {m['name'][:24]}のコスパ値{m['cospa']:.0f}、最安¥{m['minPrice']:,}、レビュー★{m['review']:.2f}（{m['reviewCount']:,}件）。{cfg['label']}コスパ{r}位。"
        _prices = [o["price"] for o in m.get("offers", [])] or [m["minPrice"]]
        ld = {"@context": "https://schema.org", "@type": "Product", "name": m["name"], "brand": m["brand"],
              "description": desc, "image": m["image"],
              "aggregateRating": {"@type": "AggregateRating", "ratingValue": m["review"],
              "reviewCount": m["reviewCount"], "bestRating": 5},
              "offers": {"@type": "AggregateOffer", "priceCurrency": "JPY",
                         "lowPrice": min(_prices), "highPrice": max(_prices), "offerCount": len(_prices),
                         "availability": "https://schema.org/InStock"}}
        bc = breadcrumb_ld([("コスパナビ", SITE_URL + "/"), (cfg["label"], SITE_URL + U(cfg["file"])),
                            (m["name"][:40], None)])
        head = "".join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in (ld, bc))
        open(os.path.join(PDIR, rid + ".html"), "w", encoding="utf-8").write(
            shell(title, desc, body, base="../", head=head, path="product/" + rid + ".html", image=m["image"], noindex=True))

# ================= 徹底比較記事 =================
CAT_BY_SLUG = {c["slug"]: c for c in CATS}

def compares_for(slug):
    return [c for c in COMPARES if c["category"] == slug]

def render_compare_box(slug):
    # カテゴリページ上部に、そのカテゴリの比較記事へのリンクを出す（内部リンク＆回遊）
    cs = compares_for(slug)
    if not cs:
        return ""
    links = "".join(f'<a class="cmpbox-a" href="/compare/{c["slug"]}">{H.escape(c["title"].split("｜")[0])} →</a>' for c in cs)
    return f'<div class="cmpbox"><span class="cmpbox-t">🔍 徹底比較</span>{links}</div>'

def _top_model(data, match, name_incl=None, name_excl=None):
    # ブランド部分一致で、現在の最コスパ機種を1台返す（無ければNone）
    # name_incl指定時は機種名にもいずれかのトークンを含む機種に限定（例: パナソニックの"ナノケア"）。該当0ならブランド全体にフォールバック
    # name_excl指定時は機種名にいずれかのトークンを含む機種を除外（例: AirPodsの"片耳/単品/交換品"を除く）
    cand = [m for m in data if match in m["brand"]]
    if name_excl:
        f = [m for m in cand if not any(t.lower() in m["name"].lower() for t in name_excl)]
        cand = f or cand
    if name_incl:
        f = [m for m in cand if any(t.lower() in m["name"].lower() for t in name_incl)]
        cand = f or cand
    return max(cand, key=lambda m: m["cospa"]) if cand else None

def build_compares():
    for c in COMPARES:
        cfg = CAT_BY_SLUG.get(c["category"])
        if not cfg:
            continue
        data = load(c["category"])
        ranked = sorted(data, key=lambda m: m["cospa"], reverse=True)
        rank_of = {m["id"]: i + 1 for i, m in enumerate(ranked)}
        picks = []
        for b in c["brands"]:
            m = _top_model(data, b["match"], b.get("name_incl"), b.get("name_excl"))
            if m:
                picks.append((b, m))
        if len(picks) < 2:
            continue  # データ不足の対決はスキップ（記事を破綻させない）
        # 上部の対決カード（現在の最コスパ機種を自動注入＝常に最新・リンク切れなし）
        vcards = []
        for i, (b, m) in enumerate(picks):
            buy = (f'<a class="buy sm" href="{m["affiliate"]}" target="_blank" rel="nofollow sponsored noopener">'
                   f'最安値を見る<span class="pr">PR</span></a>')
            vcards.append(
                f'<div class="vcard"><div class="vb">{H.escape(b["name"])}</div>'
                f'<img src="{m["image"]}" alt="{H.escape(m["name"])}">'
                f'<div class="vn">{H.escape(m["name"][:34])}</div>'
                f'<div class="vp">¥{m["minPrice"]:,}〜</div>'
                f'<div class="ccospa">コスパ値 <b>{m["cospa"]:.0f}</b> ／ {cfg["label"]}{rank_of[m["id"]]}位</div>'
                f'<div class="cstars">{stars(m["review"])} {m["review"]:.2f}（{m["reviewCount"]:,}件）</div>'
                f'{buy}</div>')
        vs_html = f'<div class="vs">{vcards[0]}<div class="vsbadge">VS</div>{vcards[1]}</div>'
        # 比較表（ライブ数値 ＋ 編集の定性項目）
        b0, m0 = picks[0]; b1, m1 = picks[1]
        def row(label, v0, v1):
            return f'<tr><td>{label}</td><td>{v0}</td><td>{v1}</td></tr>'
        rows = [
            row("現在の最コスパ機種", H.escape(m0["name"][:26]), H.escape(m1["name"][:26])),
            row("最安値", f'¥{m0["minPrice"]:,}〜', f'¥{m1["minPrice"]:,}〜'),
            row("コスパ値", f'<b>{m0["cospa"]:.0f}</b>/100', f'<b>{m1["cospa"]:.0f}</b>/100'),
            row(f'{cfg["label"]}内順位', f'{rank_of[m0["id"]]}位', f'{rank_of[m1["id"]]}位'),
            row("レビュー", f'★{m0["review"]:.2f}（{m0["reviewCount"]:,}）', f'★{m1["review"]:.2f}（{m1["reviewCount"]:,}）'),
        ]
        for k in ("タイプ", "強み", "注意点", "向いている人"):
            rows.append(row(k, H.escape(b0["traits"].get(k, "—")), H.escape(b1["traits"].get(k, "—"))))
        cmp_table = (f'<table class="kv cmp3"><tr><th>項目</th><th>{H.escape(b0["name"])}</th>'
                     f'<th>{H.escape(b1["name"])}</th></tr>{"".join(rows)}</table>')
        # 各ブランドの解説（独自文）
        brand_sections = "".join(
            f'<h2>{H.escape(b["name"])}の特徴</h2><p>{b["body"]}</p>' for b in c["brands"])
        # FAQ（FAQPage構造化データも）
        faq_html = "".join(
            f'<div class="faq"><h3>{H.escape(q)}</h3><p>{H.escape(a)}</p></div>' for q, a in c["faq"])
        faq_ld = {"@context": "https://schema.org", "@type": "FAQPage",
                  "mainEntity": [{"@type": "Question", "name": q,
                                  "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in c["faq"]]}
        body = f"""
<nav class="crumb"><a href="/">コスパナビ</a> › <a href="{U(cfg['file'])}">{cfg['label']}</a> › 徹底比較</nav>
<h1>{H.escape(c['title'].split('｜')[0])}</h1>
<p class="lead">{c['lead']}</p>
{AD}
{vs_html}
<p class="note">※価格・レビュー・コスパ値・順位は毎日更新される最新データ（{UPDATED}時点）。各ブランドで現在最もコスパの良い機種を自動表示しています。</p>
<h2>比較表</h2>
{cmp_table}
{brand_sections}
<h2>結局どっちがおすすめ？</h2>
<p>{c['verdict']}</p>
{AD}
<h2>よくある質問</h2>
<div class="faqs">{faq_html}</div>
<p class="src"><a href="{U(cfg['file'])}">{cfg['label']}コスパランキングをすべて見る →</a></p>
<script type="application/ld+json">{json.dumps(faq_ld, ensure_ascii=False)}</script>
"""
        bc = breadcrumb_ld([("コスパナビ", SITE_URL + "/"), (cfg["label"], SITE_URL + U(cfg["file"])),
                            (c["title"].split("｜")[0], None)])
        head = f'<script type="application/ld+json">{json.dumps(bc, ensure_ascii=False)}</script>'
        open(os.path.join(CDIR, c["slug"] + ".html"), "w", encoding="utf-8").write(
            shell(c["title"], c["desc"], body, base="../", head=head,
                  path="compare/" + c["slug"] + ".html", image=picks[0][1]["image"]))
    return len(COMPARES)

# ================= ブランド別ページ（「〇〇 レビュー/コスパ」検索の受け皿） =================
BDIR = os.path.join(SITE, "brand"); os.makedirs(BDIR, exist_ok=True)
BRAND_SLUGS = {"iRobot": "roomba", "Anker": "eufy", "Roborock": "roborock", "Ecovacs": "deebot",
               "EcoFlow": "ecoflow", "Jackery": "jackery", "Dyson": "dyson", "パナソニック": "panasonic"}

def _brands_from_compares():
    # COMPARESのbrand定義(独自解説を執筆済)を(カテゴリ,match)単位で集約→ブランドページの素に
    seen = {}
    for c in COMPARES:
        for b in c["brands"]:
            key = (c["category"], b["match"])
            if key not in seen and b["match"] in BRAND_SLUGS:
                seen[key] = {"cat": c["category"], "match": b["match"], "name": b["name"],
                             "body": b.get("body", ""), "traits": b.get("traits", {}),
                             "name_incl": b.get("name_incl"), "slug": BRAND_SLUGS[b["match"]]}
    return list(seen.values())

def brands_for(cat_slug):
    return [b for b in _brands_from_compares() if b["cat"] == cat_slug]

def render_brand_links(cat_slug):
    bs = brands_for(cat_slug)
    if not bs:
        return ""
    links = "".join(f'<a class="cmpbox-a" href="/brand/{b["slug"]}">{H.escape(b["name"].split("（")[0])}のコスパ・レビュー →</a>' for b in bs)
    return f'<div class="cmpbox"><span class="cmpbox-t">🔖 ブランドで選ぶ</span>{links}</div>'

def _mcard(m, rank):
    return (f'<div class="card"><div class="cimg"><img loading="lazy" src="{m["image"]}" alt="{H.escape(m["name"][:30])}"></div>'
            f'<div class="cbody"><div class="ctop"><span class="crank">#{rank}</span>'
            f'<span class="ccospa">コスパ <b>{m["cospa"]:.0f}</b></span></div>'
            f'<a class="cname" href="/product/{m["id"]}" title="{H.escape(m["name"])}">{H.escape(m["name"][:40])}</a>'
            f'<div class="cstars">{stars(m["review"])} <span class="muted">{m["review"]:.2f}（{m["reviewCount"]:,}件）</span></div>'
            f'<div class="cprice">¥{m["minPrice"]:,}<span class="muted">〜</span></div>'
            f'<a class="buy sm" href="{m["affiliate"]}" target="_blank" rel="nofollow sponsored noopener">最安値を見る<span class="pr">PR</span></a>'
            f'</div></div>')

def build_brands():
    n = 0
    for b in _brands_from_compares():
        cfg = CAT_MAP.get(b["cat"])
        if not cfg:
            continue
        data = load(b["cat"])
        def ok(m):
            if b["match"] not in m["brand"]:
                return False
            if b["name_incl"] and not any(t.lower() in m["name"].lower() for t in b["name_incl"]):
                return False
            return True
        models = sorted([m for m in data if ok(m)], key=lambda m: -m["cospa"])
        if len(models) < 2:
            continue
        short = b["name"].split("（")[0]  # 「ルンバ」など検索語に近い短名
        lo, med, q1, q3 = price_stats(models)
        soba = (f'<div class="soba"><span class="sicon">💰</span><div><b>{short}（{cfg["label"]}）の価格相場</b>'
                f'<span class="smt">（{UPDATED}時点・{len(models)}機種の実売最安値より）</span><br>'
                f'最安 <b>¥{lo:,}</b> ／ 中央値 <b>¥{med:,}</b> ／ ボリュームゾーン <b>¥{q1:,}〜¥{q3:,}</b></div></div>')
        traits = "".join(f'<tr><td>{H.escape(k)}</td><td>{H.escape(v)}</td></tr>' for k, v in b["traits"].items())
        cards = "".join(_mcard(m, i + 1) for i, m in enumerate(models[:24]))
        more = f'<p class="note">上位24機種を表示中（全{len(models)}機種）。すべては<a href="{U(cfg["file"])}">{cfg["label"]}コスパランキング</a>で確認できます。</p>' if len(models) > 24 else ""
        cmps = [c for c in COMPARES if c["category"] == b["cat"] and any(b["match"] == x["match"] for x in c["brands"])]
        cmp_links = "".join(f'<li><a href="/compare/{c["slug"]}">{H.escape(c["title"].split("｜")[0])}</a></li>' for c in cmps)
        cmp_sec = f'<h2>{short}を他ブランドと比較</h2><ul class="rel-list">{cmp_links}</ul>' if cmp_links else ""
        body = f"""
<nav class="crumb"><a href="/">コスパナビ</a> › <a href="{U(cfg['file'])}">{cfg['label']}</a> › {H.escape(short)}</nav>
<h1>{H.escape(b["name"])}の{cfg['label']} コスパ・レビュー比較<span class="yr">2026</span></h1>
<p class="lead">{H.escape(b["name"])}の{cfg['label']}を全<b>{len(models)}機種</b>、レビュー満足度と価格の独自コスパ値で比較。{short}のどの機種がコスパが良いか、価格相場と口コミ評価から分かります。</p>
{soba}
<h2>{H.escape(short)}ってどう？特徴と評判</h2>
<p>{b["body"]}</p>
<table class="kv">{traits}</table>
{render_compare_box(b['cat'])}
{AD}
<h2>{H.escape(short)}の{cfg['label']} コスパランキング</h2>
<div class="cards">{cards}</div>
{more}
{cmp_sec}
<p class="src"><a href="{U(cfg['file'])}">{cfg['label']}の全機種ランキングへ →</a></p>
"""
        title = f"{b['name']}の{cfg['label']}｜全{len(models)}機種のコスパ・価格・レビュー比較【2026】"
        desc = (f"{b['name']}の{cfg['label']}の価格相場は最安¥{lo:,}〜中央値¥{med:,}。全{len(models)}機種を"
                f"コスパ値・レビュー・価格で比較。{short}のおすすめ機種とコスパが分かります。")
        bc = breadcrumb_ld([("コスパナビ", SITE_URL + "/"), (cfg["label"], SITE_URL + U(cfg["file"])),
                            (short, None)])
        head = f'<script type="application/ld+json">{json.dumps(bc, ensure_ascii=False)}</script>'
        open(os.path.join(BDIR, b["slug"] + ".html"), "w", encoding="utf-8").write(
            shell(title, desc, body, base="../", head=head, path="brand/" + b["slug"] + ".html", image=models[0]["image"]))
        n += 1
    return n

# ================= ハブ =================
FURU_BANNER = ('<a class="fbanner" href="/furusato"><div class="hico">🍚</div><div><h3>ふるさと納税コスパ分析<span class="n">NEW</span></h3>'
               '<p>「実質2,000円で本当にお得な返礼品は？」楽天ふるさと納税を<b>寄付額あたりの内容量（円/kg）</b>とレビューでコスパランキング。定期便も総量換算。</p></div><span class="fgo">見る →</span></a>')
NICHIYO_BANNER = ('<a class="fbanner" href="/nichiyo"><div class="hico">🧻</div><div><h3>日用品コスパ分析<span class="n">NEW</span></h3>'
                  '<p>トイレットペーパー・米・ティッシュなど<b>毎日使う日用品</b>を、価格×満足度の独自コスパ値でランキング。まとめ買い・大容量の最適解が分かる。</p></div><span class="fgo">見る →</span></a>')
KADEN_BANNER = ('<a class="fbanner" href="/"><div class="hico">🔌</div><div><h3>家電コスパ ランキング</h3>'
                '<p>ロボット掃除機・空気清浄機・イヤホンなど、満足度×価格の独自コスパ値で家電をランキング。重視ポイントや予算で選べる。</p></div><span class="fgo">見る →</span></a>')

def _hubcards(cats, built):
    return "".join(f'<a class="hcard" href="{U(c["file"])}"><div class="hico">{c["icon"]}</div>'
                   f'<div><h3>{c["label"]}<span class="n">{built.get(c["slug"], 0)}{"品" if c["section"]=="nichiyo" else "機種"}</span></h3>'
                   f'<p>{c["desc"]}</p></div></a>' for c in cats)

def _nichiyo_cards(cats, built):
    # 「選びやすい」リッチカード: 各カテゴリの一番人気(コスパ1位)を画像・最安・評価・コスパ値付きで提示
    out = []
    for c in cats:
        slug = c["slug"]
        try:
            data = load(slug)
        except Exception:
            data = []
        n = built.get(slug, len(data))
        lo = min((m["minPrice"] for m in data), default=0)
        top = max(data, key=lambda m: m["cospa"]) if data else None
        href = U(c["file"])
        if top:
            nm = H.escape(top["name"][:40])
            brand = "" if "ノーブランド" in top["brand"] else f'<span class="npbrand">{H.escape(top["brand"])}</span>'
            star = round(top["review"], 2)
            pick = (f'<div class="npick"><div class="npimg"><img loading="lazy" src="{H.escape(top.get("image",""))}" alt=""></div>'
                    f'<div class="npinfo"><span class="nplabel">👑 コスパ1位</span>'
                    f'{brand}<span class="npname">{nm}</span>'
                    f'<div class="npmeta"><span class="npstar">★{star}</span><span class="npprice">¥{top["minPrice"]:,}〜</span></div>'
                    f'<div class="npbar"><i style="width:{min(100,top["cospa"]):.0f}%"></i></div>'
                    f'<div class="npcospa">コスパ値 <b>{round(top["cospa"])}</b> / 100</div></div></div>')
            lorow = f'<div class="nlo">最安 <b>¥{lo:,}</b>〜 · <b>{n}品</b>から比較</div>'
        else:
            pick, lorow = "", ""
        out.append(
            f'<a class="ncard" href="{href}">'
            f'<div class="nhead"><span class="nicon">{c["icon"]}</span>'
            f'<div><h3>{c["label"]}</h3><span class="ncount">{n}品を毎日更新</span></div></div>'
            f'<p class="ndesc">{c["desc"]}</p>{pick}{lorow}'
            f'<span class="ngo">ランキングを見る →</span></a>')
    return '<div class="ngrid">' + "".join(out) + '</div>'

def _cmp_section(cats, section_label):
    sec = {c["slug"] for c in cats}
    comps = [c for c in COMPARES if c["category"] in sec]
    if not comps:
        return f'<h2 id="compare">徹底比較</h2><p class="lead">{section_label}の人気ブランド対決は準備中です。近日公開します。</p>'
    cards = "".join(
        f'<a class="hcard" href="/compare/{c["slug"]}"><div class="hico">🔍</div>'
        f'<div><h3>{H.escape(c["title"].split("｜")[0])}</h3>'
        f'<p>{H.escape(CAT_BY_SLUG[c["category"]]["label"])}の人気ブランドを徹底比較</p></div></a>' for c in comps)
    return (f'<h2 id="compare">徹底比較</h2><p class="lead">人気ブランドを1対1で比較。価格・満足度・機能・向いている人がひと目で分かります。</p>'
            f'<div class="hgrid">{cards}</div>')

ABOUT_SEC = ('<h2>コスパナビとは</h2><p>価格.comのように"全部載せ"で迷わせるのではなく、<b>「満足度×価格」の独自コスパ値</b>と'
             '<b>調整できるツール</b>で、あなたの条件に合う最適解を提示します。データは楽天市場・Yahoo!ショッピングのレビュー・価格に基づき毎日更新。'
             '詳しくは<a href="/about">コスパ値とは</a>。</p>')

def build_hub(built):
    # 家電ハブ(トップ /)
    coming = "".join(f'<span class="soon">{c}</span>' for c in COMING)
    body = f"""
<div class="hero"><h1>コスパナビ<span class="yr">2026</span></h1>
<p class="lead">レビュー満足度と価格から、<b>本当にコスパの良い製品</b>を独自スコアでランキング。<b>重視ポイントや予算を調整</b>して、あなたに最適な1台が見つかります。<b>毎日価格を調査・更新</b>し、現時点で最もコスパの良い商品を選択できます。</p></div>
{AD}{FURU_BANNER}{NICHIYO_BANNER}{MARATHON}
<h2 id="ranking">家電コスパ ランキング</h2>
<div class="hgrid">{_hubcards(KADEN_CATS, built)}</div>
<div class="soonbox"><p class="lead">今後追加予定：</p>{coming}</div>
{_cmp_section(KADEN_CATS, "家電")}
{ABOUT_SEC}
"""
    open(os.path.join(SITE, "index.html"), "w", encoding="utf-8").write(
        shell("コスパナビ2026｜満足度×価格で選ぶ商品コスパ比較", "レビュー満足度と価格から独自コスパ値で製品をランキング。家電・日用品・ふるさと納税。重視ポイント・予算で最適な1台が選べる。", body, path="index.html"))

def build_nichiyo_hub(built):
    # 日用品ハブ(/nichiyo) — 「選びやすくてかっこいい」リデザイン版(.nv2スコープ)
    coming = "".join(f'<span class="soon">{c}</span>' for c in NICHIYO_COMING)
    body = f"""
<div class="nv2">
<nav class="crumb"><a href="/">コスパナビ</a> › 日用品</nav>
<div class="nhero"><h1>日用品コスパ分析<span class="yr">2026</span></h1>
<p>トイレットペーパー・米・ティッシュ・洗剤など<b>毎日使う日用品</b>を、価格×レビュー満足度の独自コスパ値でランキング。<b>まとめ買い・大容量の「本当にお得な1つ」</b>がすぐ見つかります。</p>
<div class="nbadges"><span>🔄 毎日 価格を自動更新</span><span>🛒 楽天市場で比較</span><span>⭐ レビュー×価格で厳選</span></div></div>
<h2 id="ranking">カテゴリから選ぶ</h2>
{_nichiyo_cards(NICHIYO_CATS, built)}
<div class="soonbox"><p class="lead">今後追加予定：</p>{coming}</div>
{MARATHON}
{_cmp_section(NICHIYO_CATS, "日用品")}
<h2>ほかのコスパ分析</h2>
{FURU_BANNER}{KADEN_BANNER}
{ABOUT_SEC}
</div>
"""
    bc = breadcrumb_ld([("コスパナビ", SITE_URL + "/"), ("日用品", None)])
    bc_head = f'<script type="application/ld+json">{json.dumps(bc, ensure_ascii=False)}</script>'
    open(os.path.join(SITE, "nichiyo.html"), "w", encoding="utf-8").write(
        shell("日用品コスパ分析2026｜トイレットペーパー・米・ティッシュを価格×満足度で比較",
              "毎日使う日用品を独自コスパ値でランキング。トイレットペーパー・米・ティッシュの大容量・まとめ買いのコスパ最強が分かる。毎日自動更新。",
              body, path="nichiyo.html", head=bc_head))

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
    urls = "".join(f"<url><loc>{SITE_URL}{p}</loc><lastmod>{UPDATED}</lastmod></url>" for p in SITEMAP)
    xml = f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>'
    open(os.path.join(SITE, "sitemap.xml"), "w", encoding="utf-8").write(xml)
    robots = f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n"
    open(os.path.join(SITE, "robots.txt"), "w", encoding="utf-8").write(robots)
    # AdSense認証用 ads.txt（f08c47fec0942fa0はGoogle固定の認証局ID）
    open(os.path.join(SITE, "ads.txt"), "w", encoding="utf-8").write(
        f"google.com, {ADSENSE_PUB}, DIRECT, f08c47fec0942fa0\n")
    # Search Console HTMLファイル認証（中身は "google-site-verification: <ファイル名>"）
    for fn in GOOGLE_VERIFY_FILES:
        open(os.path.join(SITE, fn), "w", encoding="utf-8").write(f"google-site-verification: {fn}\n")

CSS = r"""
:root{--bg:#f6f7f9;--card:#fff;--ink:#1a2130;--sub:#5a6478;--line:#e6e9ef;--accent:#ff5a1f;--accent2:#2563eb;--bar:#ffe0d3;--chip:#fff1eb}
@media(prefers-color-scheme:dark){:root{--bg:#0f141c;--card:#161d29;--ink:#e8ecf3;--sub:#9aa6b8;--line:#26303f;--accent:#ff7a45;--accent2:#5b8cff;--bar:#3a2418;--chip:#241a14}}
:root[data-theme=dark]{--bg:#0f141c;--card:#161d29;--ink:#e8ecf3;--sub:#9aa6b8;--line:#26303f;--accent:#ff7a45;--accent2:#5b8cff;--bar:#3a2418;--chip:#241a14}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--bg);color:var(--ink);font-family:-apple-system,"Hiragino Kaku Gothic ProN","Yu Gothic",Meiryo,sans-serif;line-height:1.7}
a{color:var(--accent2)}
:target{scroll-margin-top:72px}h2[id]{scroll-margin-top:72px}
.navwrap{position:sticky;top:0;z-index:50;background:var(--card);border-bottom:1px solid var(--line);box-shadow:0 2px 10px rgba(0,0,0,.06)}
.nav{display:flex;align-items:center;gap:12px;max-width:1040px;margin:0 auto;padding:9px 14px}
.brand{flex:none;font-weight:900;text-decoration:none;color:var(--ink);font-size:1.3rem;letter-spacing:.01em}.brand b{color:var(--accent)}
.gnav{display:flex;align-items:center;gap:0;overflow-x:auto;min-width:0;scrollbar-width:none;-webkit-overflow-scrolling:touch;margin-left:auto}
.gnav::-webkit-scrollbar{display:none}
.ggrp{flex:none;display:flex;align-items:center;gap:18px}
.gcap{flex:none;font-size:.7rem;color:var(--sub);font-weight:800;white-space:nowrap;letter-spacing:.03em}
.gnav a{flex:none;white-space:nowrap;text-decoration:none;color:var(--ink);font-size:.92rem;font-weight:700;padding:4px 0;transition:color .15s}
.gnav a:hover{color:var(--accent)}
.gdiv{flex:none;width:1px;height:20px;background:var(--line);margin:0 18px}
.gabout{color:var(--sub);font-size:.88rem;font-weight:700}
.go5{background:linear-gradient(90deg,#e0242b,#ff6a3d);box-shadow:0 3px 12px rgba(224,36,43,.28)}
.go5 a{display:flex;align-items:center;justify-content:center;flex-wrap:wrap;gap:10px;color:#fff;text-decoration:none;padding:9px 14px;font-size:.92rem;font-weight:800}
.go5 a b{color:#ffe14d}.go5 .gift{font-size:1.25rem}
.go5 .gbtn{background:#fff;color:#e0242b;border-radius:999px;padding:4px 14px;font-size:.82rem;font-weight:800;white-space:nowrap;box-shadow:0 1px 4px rgba(0,0,0,.15)}
.mbanner{display:flex;align-items:center;gap:14px;background:linear-gradient(100deg,#ff6b8a,#e81f46);border-radius:16px;padding:14px 20px;margin:16px 0;text-decoration:none;color:#fff;box-shadow:0 5px 20px rgba(232,31,70,.30)}
.mbanner .mico{font-size:2rem;flex:none}
.mbanner .mtxt{flex:1;min-width:0}
.mbanner .mtag{display:inline-block;background:rgba(255,255,255,.22);border-radius:999px;padding:2px 11px;font-size:.73rem;font-weight:800;margin-bottom:4px}
.mbanner .mmain{display:block;font-size:.96rem;font-weight:800;line-height:1.45}.mbanner .mmain b{color:#ffe14d}
.mbanner .mgo{flex:none;background:#fff;color:#e0243a;border-radius:999px;padding:9px 18px;font-size:.84rem;font-weight:800;white-space:nowrap;box-shadow:0 2px 6px rgba(0,0,0,.18)}
@media(max-width:560px){.mbanner{flex-wrap:wrap;gap:4px 10px;padding:12px 16px}.mbanner .mico{font-size:1.5rem}
.mbanner .mtag{font-size:.68rem;padding:1px 9px;margin-bottom:2px}.mbanner .mmain{font-size:.82rem;line-height:1.35}
.mbanner .mgo{flex:1 1 100%;text-align:center;margin-top:9px;padding:9px;font-size:.84rem;white-space:normal}}
.ebridge{display:flex;align-items:center;gap:14px;background:linear-gradient(135deg,#fff3ec,#ffe6f0);border:1px solid var(--line);border-left:5px solid var(--accent);border-radius:14px;padding:14px 18px;margin:16px 0;text-decoration:none;color:var(--ink);box-shadow:0 2px 10px rgba(255,122,69,.12)}
.ebridge .eico{font-size:2rem;flex:none}.ebridge h3{margin:0;font-size:1.05rem;color:#c2410c}.ebridge p{margin:3px 0 0;font-size:.82rem;color:#6b5a52}.ebridge .ego{margin-left:auto;color:#fff;background:var(--accent);border-radius:999px;padding:7px 16px;font-weight:800;white-space:nowrap}
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
.fbanner{display:flex;align-items:center;gap:14px;background:var(--chip);border:1px solid var(--accent);border-radius:14px;padding:14px 18px;margin:14px 0;text-decoration:none;color:var(--ink)}
.fbanner:hover{box-shadow:0 2px 10px rgba(255,90,31,.15)}.fbanner .hico{font-size:2rem}.fbanner h3{margin:.1em 0;font-size:1.1rem}.fbanner .n{background:var(--accent);color:#fff;border-radius:6px;padding:1px 7px;font-size:.68rem;margin-left:8px;vertical-align:middle}
.fbanner p{margin:.2em 0 0;color:var(--sub);font-size:.85rem}.fbanner .fgo{margin-left:auto;color:var(--accent);font-weight:700;white-space:nowrap}
@media(max-width:520px){.fbanner .fgo{display:none}}
.hero{margin:.4em 0 1em}.hgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:12px;margin:14px 0}
.hcard{display:flex;gap:12px;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px;text-decoration:none;color:var(--ink)}
.hcard:hover{border-color:var(--accent)}.hico{font-size:1.8rem}.hcard h3{margin:.1em 0;font-size:1.05rem}.hcard .n{color:var(--accent);font-size:.8rem;margin-left:8px}.hcard p{margin:.2em 0 0;color:var(--sub);font-size:.85rem}
.soonbox{margin:16px 0}.soon{display:inline-block;background:var(--chip);color:var(--sub);border-radius:16px;padding:4px 12px;margin:3px;font-size:.82rem}
.pdetail{display:flex;gap:18px;flex-wrap:wrap}.pimg{flex:0 0 240px;max-width:100%;background:#fff;border-radius:12px;padding:10px}.pimg img{width:100%;object-fit:contain}
.pinfo{flex:1;min-width:240px}.pbrand{color:var(--sub);font-size:.85rem}.pinfo h1{font-size:1.25rem;margin:.2em 0}
.prank{color:var(--accent);font-weight:700}.pstars{color:#f5a623}.pprice{font-size:1.6rem;font-weight:800;margin:.2em 0}.pprice .muted{font-size:.8rem;font-weight:400}
.kv{width:100%;margin:.4em 0}.kv td{border-bottom:1px solid var(--line);padding:8px}.kv td:first-child{color:var(--sub);width:42%}
.rel{display:flex;flex-wrap:wrap;gap:8px}.rel a{font-size:.85rem;border:1px solid var(--line);border-radius:8px;padding:5px 10px;text-decoration:none}
.rel-list{margin:.4em 0;padding-left:1.2em}.rel-list li{margin:.2em 0}
.guide{margin:28px 0 8px}.guide h2{margin-top:1.4em}
.gpts{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px;margin:10px 0}
.gpt{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px 14px}
.gpt h3{margin:.1em 0 .3em;font-size:.98rem;color:var(--accent)}.gpt p{margin:0;font-size:.9rem}
.picks{margin:8px 0}.pk-rng{font-size:.78rem;color:var(--sub);font-weight:400;margin-left:8px}
.pk-nm{display:block;font-weight:700;text-decoration:none;color:var(--ink);font-size:.92rem;margin:2px 0}.pk-nm:hover{color:var(--accent2)}
.pk-meta{font-size:.82rem;color:var(--sub);margin-bottom:6px}
table.pk{border-collapse:collapse}table.pk th{text-align:left;color:var(--sub);font-size:.78rem;padding:6px 8px;border-bottom:1px solid var(--line)}
table.pk td{border-bottom:1px solid var(--line);padding:8px;font-size:.88rem;vertical-align:middle}
.pk-r{font-weight:800;color:var(--accent);width:1.6em}.pk-br{font-size:.72rem;color:var(--sub)}.pk-p{font-weight:800;white-space:nowrap}.pk-cc{color:var(--sub);font-size:.8rem;white-space:nowrap}
.faqs{display:grid;gap:10px;margin:10px 0}
.faq{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px 14px}
.faq h3{margin:.1em 0 .3em;font-size:.95rem}.faq p{margin:0;font-size:.9rem;color:var(--sub)}
.src{margin-top:14px}.foot{max-width:1000px;margin:0 auto;padding:20px 16px 40px;color:var(--sub);font-size:.8rem;border-top:1px solid var(--line)}
.fcats{display:flex;flex-wrap:wrap;gap:8px 16px;margin-bottom:12px}.fcats a{color:var(--sub);text-decoration:none;font-size:.85rem}.fcats a:hover{color:var(--accent)}
@media(max-width:520px){.cards{grid-template-columns:1fr}}
.soba{display:flex;gap:10px;align-items:flex-start;background:var(--chip);border:1px solid var(--line);border-left:4px solid var(--accent);border-radius:10px;padding:11px 14px;margin:12px 0;font-size:.92rem}
.soba .sicon{font-size:1.2rem;line-height:1.3}.soba b{color:var(--accent)}.soba .smt{color:var(--sub);font-size:.78rem;font-weight:400}
.cmpbox{display:flex;flex-wrap:wrap;align-items:center;gap:8px 14px;background:var(--chip);border:1px solid var(--line);border-left:4px solid var(--accent);border-radius:10px;padding:10px 14px;margin:12px 0}
.cmpbox-t{font-weight:800;color:var(--accent);font-size:.9rem}.cmpbox-a{font-weight:700;font-size:.88rem;text-decoration:none}
.vs{display:grid;grid-template-columns:1fr auto 1fr;gap:10px;align-items:stretch;margin:16px 0}
.vcard{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px;text-align:center;display:flex;flex-direction:column;gap:4px}
.vcard img{height:120px;object-fit:contain;max-width:100%;margin:4px 0}
.vcard .vb{font-size:.78rem;color:var(--accent);font-weight:700}
.vcard .vn{font-weight:700;font-size:.88rem;min-height:2.6em;line-height:1.3}
.vcard .vp{font-weight:800;font-size:1.25rem;color:var(--accent)}
.vcard .ccospa{justify-content:center}.vcard .cstars{font-size:.8rem}.vcard .buy{margin-top:8px}
.vsbadge{align-self:center;font-weight:800;color:var(--sub);font-size:1.1rem}
.cmp3 th{text-align:left;color:var(--sub);font-size:.82rem;padding:6px 8px;border-bottom:1px solid var(--line)}
.cmp3 td{vertical-align:top;font-size:.9rem}.cmp3 td:first-child{color:var(--sub);width:26%}
@media(max-width:560px){.vs{grid-template-columns:1fr 1fr;gap:8px}.vsbadge{grid-column:1/3;order:-1;padding:2px}.cmp3 td:first-child{width:34%}}
/* ===== 日用品ハブ リデザイン(.nv2スコープ=このページ限定) ===== */
.nv2 .nhero{position:relative;overflow:hidden;border-radius:22px;padding:30px 26px;margin:8px 0 22px;background:linear-gradient(135deg,#ff8a4c 0%,#ff5a1f 52%,#ff3d8b 100%);color:#fff;box-shadow:0 14px 34px rgba(255,90,31,.30)}
.nv2 .nhero::before{content:"";position:absolute;right:-50px;top:-50px;width:210px;height:210px;border-radius:50%;background:rgba(255,255,255,.13)}
.nv2 .nhero::after{content:"";position:absolute;right:70px;bottom:-70px;width:150px;height:150px;border-radius:50%;background:rgba(255,255,255,.10)}
.nv2 .nhero h1{position:relative;color:#fff;font-size:1.9rem;font-weight:900;margin:0 0 .35em;letter-spacing:.01em;border:0;padding:0}
.nv2 .nhero h1 .yr{color:#fff2cc}
.nv2 .nhero p{position:relative;color:rgba(255,255,255,.96);font-size:.95rem;margin:0;max-width:660px}
.nv2 .nhero p b{color:#fff;font-weight:800}
.nv2 .nbadges{position:relative;display:flex;flex-wrap:wrap;gap:8px;margin-top:18px}
.nv2 .nbadges span{background:rgba(255,255,255,.18);border:1px solid rgba(255,255,255,.4);border-radius:999px;padding:6px 14px;font-size:.78rem;font-weight:700}
.nv2 h2{font-size:1.25rem;border-left:5px solid var(--accent);padding-left:10px;margin:1.4em 0 .6em}
.nv2 .ngrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(310px,1fr));gap:16px;margin:16px 0}
.nv2 .ncard{display:flex;flex-direction:column;background:var(--card);border:1px solid var(--line);border-radius:20px;padding:18px;text-decoration:none;color:var(--ink);box-shadow:0 3px 12px rgba(0,0,0,.05);transition:transform .18s ease,box-shadow .18s ease,border-color .18s ease}
.nv2 .ncard:hover{transform:translateY(-5px);box-shadow:0 18px 36px rgba(255,90,31,.17);border-color:var(--accent)}
.nv2 .nhead{display:flex;align-items:center;gap:13px;margin-bottom:10px}
.nv2 .nicon{width:54px;height:54px;flex:none;display:flex;align-items:center;justify-content:center;font-size:1.75rem;background:linear-gradient(135deg,var(--chip),#fff);border:1px solid var(--line);border-radius:16px}
.nv2 .nhead h3{margin:0;font-size:1.2rem;font-weight:800}
.nv2 .ncount{display:inline-block;margin-top:4px;color:var(--accent);font-size:.76rem;font-weight:800}
.nv2 .ndesc{color:var(--sub);font-size:.84rem;margin:.1em 0 13px;line-height:1.55}
.nv2 .npick{display:flex;gap:13px;align-items:center;background:var(--bg);border:1px solid var(--line);border-radius:15px;padding:12px;margin-bottom:12px}
.nv2 .npimg{width:74px;height:74px;flex:none;background:#fff;border-radius:11px;display:flex;align-items:center;justify-content:center;overflow:hidden}
.nv2 .npimg img{max-width:100%;max-height:100%;object-fit:contain}
.nv2 .npinfo{min-width:0;flex:1}
.nv2 .nplabel{display:inline-block;background:linear-gradient(135deg,#ffd23f,#ffab2e);color:#5c3d00;font-weight:800;font-size:.68rem;border-radius:999px;padding:2px 10px}
.nv2 .npbrand{display:block;color:var(--sub);font-size:.72rem;margin-top:5px}
.nv2 .npname{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;font-size:.86rem;font-weight:700;margin:2px 0 5px;line-height:1.35}
.nv2 .npmeta{display:flex;align-items:center;gap:11px}
.nv2 .npstar{color:#f5a623;font-weight:700;font-size:.82rem}
.nv2 .npprice{color:var(--accent);font-weight:900;font-size:1.05rem}
.nv2 .npbar{height:7px;background:var(--bar);border-radius:5px;overflow:hidden;margin-top:9px}
.nv2 .npbar i{display:block;height:100%;background:linear-gradient(90deg,#ff9a5c,#ff5a1f);border-radius:5px}
.nv2 .npcospa{font-size:.72rem;color:var(--sub);margin-top:5px}.nv2 .npcospa b{color:var(--accent);font-size:.9rem}
.nv2 .nlo{font-size:.82rem;color:var(--sub);margin-bottom:13px}.nv2 .nlo b{color:var(--ink)}
.nv2 .ngo{margin-top:auto;text-align:center;background:var(--accent);color:#fff;border-radius:13px;padding:11px;font-weight:800;font-size:.92rem;transition:background .15s}
.nv2 .ncard:hover .ngo{background:#e8440f}
@media(max-width:560px){.nv2 .nhero{padding:24px 18px;border-radius:18px}.nv2 .nhero h1{font-size:1.55rem}.nv2 .nhero p{font-size:.9rem}.nv2 .ngrid{grid-template-columns:1fr}}
"""

# CSS内容のハッシュでキャッシュバスト(?v=)。CSSを変えるたびURLが変わり、ブラウザが必ず再取得する。
# build_furusatoも同じ版を使えるよう data/css_ver.txt に書き出す。
CSS_VER = hashlib.md5(CSS.encode("utf-8")).hexdigest()[:8]
try:
    open(os.path.join(DATA, "css_ver.txt"), "w", encoding="utf-8").write(CSS_VER)
except Exception:
    pass

if __name__ == "__main__":
    built = {}
    for cfg in CATS:
        data = build_category(cfg)
        build_products(cfg, data)
        built[cfg["slug"]] = len(data)
    ncmp = build_compares()
    nbrand = build_brands()
    build_hub(built)
    build_nichiyo_hub(built)
    build_static()
    build_seo()
    # styles.css
    open(os.path.join(SITE, "styles.css"), "w", encoding="utf-8").write(CSS)
    total = sum(built.values())
    print(f"生成: index / {len(CATS)}カテゴリ / product×{total} / 比較×{ncmp} / ブランド×{nbrand} / about / privacy / sitemap({len(SITEMAP)}URL) / robots / styles.css")
