# ふるさと納税コスパ分析ページを生成。ランディング(furusato.html)＋カテゴリ(furusato-<slug>.html)。
# 通常商品とロジックが違う(寄付額あたりの内容量=お得さ)ため専用ビルダー。styles.cssは共用。
import json, os, sys, html as H, datetime, urllib.parse
from furusato_cats import FCATS
from furusato_guides import FGUIDES

# カテゴリ別 選び方ガイド＋FAQ (HTML, FAQPage構造化データ) を返す
def render_fguide(slug, label):
    g = FGUIDES.get(slug)
    if not g:
        return "", None
    pts = "".join(f'<div class="gpt"><h3>{H.escape(t)}</h3><p>{H.escape(d)}</p></div>' for t, d in g["points"])
    faqs = "".join(f'<div class="faq"><h3>Q. {H.escape(q)}</h3><p>A. {H.escape(a)}</p></div>' for q, a in g["faq"])
    html = (f'<section class="guide"><h2>{H.escape(label)}のふるさと納税・選び方</h2>'
            f'<div class="gpts">{pts}</div>'
            f'<h2>よくある質問</h2><div class="faqs">{faqs}</div></section>')
    ld = {"@context": "https://schema.org", "@type": "FAQPage",
          "mainEntity": [{"@type": "Question", "name": q,
                          "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in g["faq"]]}
    return html, ld

# バリューコマース MyLink(ふるさと納税サイトのアフィリ化)。sid共通、pidは広告主ごと。
def vc_mylink(pid, url):
    return ("//ck.jp.ap.valuecommerce.com/servlet/referral?sid=3776612&pid=" + pid +
            "&vc_url=" + urllib.parse.quote(url, safe=""))

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
SITE = os.path.join(BASE, "site")
SITE_URL = "https://cospa-navi.com"

def breadcrumb_ld(pairs):
    # pairs=[(name, url or None)] 末尾=現在ページ。パンくず構造化データ（SERP表示＆サイト構造の伝達）
    items = []
    for i, (name, url) in enumerate(pairs, 1):
        it = {"@type": "ListItem", "position": i, "name": name}
        if url:
            it["item"] = url
        items.append(it)
    d = {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": items}
    return '<script type="application/ld+json">' + json.dumps(d, ensure_ascii=False) + '</script>'

def bc_furusato(leaf):
    # コスパナビ > ふるさと納税 > leaf
    return breadcrumb_ld([("コスパナビ", SITE_URL + "/"), ("ふるさと納税", SITE_URL + "/furusato"), (leaf, None)])
UPDATED = datetime.date.today().isoformat()
ADSENSE = '<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-8706760047070867" crossorigin="anonymous"></script>'
# バリューコマース LinkSwitch: 提携済みモール(さとふる等)へのリンクを自動でアフィリ化(全ふるさとページ)
LINKSWITCH = '<script type="text/javascript">var vc_pid="892664777";</script><script type="text/javascript" src="//aml.valuecommerce.com/vcdal.js" async></script>'
VERIFY = '<meta name="google-site-verification" content="9Lq7hmAO3CeIlcT6nM2tB2_AksHlZsugoZ_VIeeY5Dc">'
AD = ''
# バリューコマース広告バナー(カテゴリカード風に1枠としてグリッド内へ)。ステマ規制対応で「広告」表記付き。
def _vc(pid, cls="adcard"):
    return (f'<div class="{cls}"><span class="adlabel">広告</span>'
            f'<script language="javascript" src="//ad.jp.ap.valuecommerce.com/servlet/jsbanner?sid=3775700&pid={pid}"></script>'
            f'<noscript><a href="//ck.jp.ap.valuecommerce.com/servlet/referral?sid=3775700&pid={pid}" target="_blank" rel="nofollow sponsored noopener">'
            f'<img src="//ad.jp.ap.valuecommerce.com/servlet/gifbanner?sid=3775700&pid={pid}" border="0"></a></noscript></div>')

IN_GRID_ADS = [_vc("892664055")]   # 食べログ 120×60。偶数行(2,4,6…)の中央に配置(PCのみ表示、スマホは非表示)
# PC用 468×60 帯(現在はグリッド内120×60を使用のため未使用。戻す場合は body に {VC_468_PC} を復活)
VC_468_PC = _vc("892664051", "adbanner-pc")
# スマホ用: 食べログ 320×50 オーバーレイ(VCがスマホ時のみ画面下部に固定表示。スクリプトを置くだけ)
VC_320_OVERLAY = ('<script language="javascript" '
                  'src="//ad.jp.ap.valuecommerce.com/servlet/smartphonebanner?sid=3775700&pid=892664050&position=overlay"></script>')

ICON = {"rice": "🍚", "beef": "🥩", "pork": "🐖", "chicken": "🍗", "hamburg": "🍔", "seafood": "🦐",
        "egg": "🥚", "fruit": "🍇", "sweets": "🍰", "frozen": "🥟", "beer": "🍺", "drink": "🥤",
        "toilet-paper": "🧻", "tissue": "🤧", "detergent": "🧴"}
# ジャンル順(主食・肉→魚介・卵→果物・菓子→冷凍→飲料→日用品)でユーザーが探しやすく
CAT_ORDER = ["rice", "beef", "pork", "chicken", "hamburg", "seafood", "egg", "fruit", "sweets",
             "frozen", "beer", "drink", "toilet-paper", "tissue", "detergent"]
CATS = [{"slug": s, "file": f"furusato-{s}.html", "label": FCATS[s]["label"], "icon": ICON.get(s, "🎁"),
         "unit_label": FCATS[s]["unit_label"], "suffix": FCATS[s]["suffix"],
         "desc": f"楽天ふるさと納税の{FCATS[s]['label']}を、寄付額あたりの内容量（{FCATS[s]['unit_label']}）とレビュー満足度でコスパランキング。"}
        for s in CAT_ORDER]

def U(file):
    # 内部リンクを絶対パス・拡張子なしに（Cloudflareのクリーンurlと一致させリダイレクト回避）
    if file in ("index.html", "index", "", "/"):
        return "/"
    f = file[:-5] if file.endswith(".html") else file
    return "/" + f.lstrip("/")

def nav():
    return ('<header class="nav"><a class="brand" href="/">コスパ<b>ナビ</b></a>'
            '<nav><a href="/">ホーム</a><a href="/furusato">ふるさと納税</a>'
            '<a href="/about">コスパ値とは</a><a href="/privacy">プライバシー</a></nav></header>')

def foot():
    cl = "".join(f'<a href="{U(c["file"])}">{c["label"]}</a>' for c in CATS)
    return (f'<footer class="foot"><nav class="fcats"><a href="/furusato">ふるさと納税トップ</a>{cl}</nav>'
            f'<p>寄付額・レビューは楽天ふるさと納税の情報（{UPDATED}時点）。内容量は商品名から自動抽出のため、必ず各返礼品ページで最新情報をご確認ください。</p>'
            f'<p class="muted">当サイトはアフィリエイト広告を利用しています。<a href="/privacy">プライバシーポリシー</a></p></footer>')

def shell(title, desc, body, path, head=""):
    url = SITE_URL + U(path)
    canon = (f'<link rel="canonical" href="{url}">'
             f'<meta property="og:type" content="website"><meta property="og:title" content="{H.escape(title)}">'
             f'<meta property="og:description" content="{H.escape(desc)}"><meta property="og:url" content="{url}">'
             f'<meta name="twitter:card" content="summary_large_image">')
    return ('<!doctype html><html lang="ja"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{H.escape(title)}</title><meta name="description" content="{H.escape(desc)}">'
            f'{VERIFY}{canon}<link rel="stylesheet" href="/styles.css">{ADSENSE}{head}'
            '<style>.fk{font-weight:800;color:var(--accent)}.metar{display:flex;flex-wrap:wrap;gap:4px 10px;font-size:.8rem;color:var(--sub);margin:2px 0}'
            '.metar b{color:var(--ink)}.badge{background:var(--chip);color:var(--accent);border-radius:6px;padding:1px 7px;font-size:.72rem;font-weight:700}'
            '.scallout{background:var(--chip);border:1px solid var(--line);border-left:4px solid var(--accent);border-radius:10px;padding:10px 14px;margin:12px 0;font-size:.9rem}.scallout a{font-weight:700;white-space:nowrap}'
            '.sguide{margin:20px 0}.sguide h2{margin-top:1.3em}'
            '.adcard{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:8px;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px;min-height:150px}'
            '.adcard img{max-width:100%;height:auto}@media(max-width:640px){.adcard{display:none}}'  # グリッド内広告はPCのみ(スマホはオーバーレイ)
            '.adbanner-pc{display:flex;flex-direction:column;align-items:center;gap:4px;margin:18px 0}.adbanner-pc img{max-width:100%;height:auto}'
            '@media(max-width:640px){.adbanner-pc{display:none}}'  # 横長帯はPCのみ(スマホはオーバーレイ320×50が出る)
            '.adlabel{align-self:flex-start;color:var(--sub);font-size:.68rem;border:1px solid var(--line);border-radius:4px;padding:0 5px}</style>'
            f'</head><body>{nav()}<main>{body}</main>{foot()}{VC_320_OVERLAY}'
            # VC広告バナー(document.writeでtarget=_topで生成される)を別タブで開くよう書き換え
            '<script>window.addEventListener("load",function(){document.querySelectorAll(".adcard a,.adbanner-pc a").forEach(function(a){a.target="_blank";a.rel="nofollow sponsored noopener";});});</script>'
            f'{LINKSWITCH}</body></html>')

TOOL_JS = r"""
const D=JSON.parse(document.getElementById('data').textContent);
const list=document.getElementById('list');
const yen=v=>'¥'+v.toLocaleString();
const wEl=document.getElementById('w'),bEl=document.getElementById('b');
let sortKey='cospa';
function stars(v){let s='';for(let i=1;i<=5;i++)s+=v>=i?'★':(v>=i-0.5?'⯨':'☆');return s;}
function render(){
 const wsat=(+wEl.value)/100, wt=1-wsat, budget=+bEl.value;
 document.getElementById('wtxt').textContent='満足度'+Math.round(wsat*100)+'% / お得さ'+Math.round(wt*100)+'%';
 document.getElementById('btxt').textContent=yen(budget)+'以下';
 let a=D.filter(x=>x.price<=budget).map(x=>({...x,cospa:wsat*x.sat+wt*x.toku}));
 if(sortKey==='cospa')a.sort((p,q)=>q.cospa-p.cospa);
 else if(sortKey==='unit')a.sort((p,q)=>p.unit-q.unit);
 else if(sortKey==='sat')a.sort((p,q)=>q.sat-p.sat);
 else if(sortKey==='rc')a.sort((p,q)=>q.rc-p.rc);
 document.getElementById('cnt').textContent=a.length+'件';
 list.innerHTML='';
 a.slice(0,60).forEach((x,i)=>{const c=document.createElement('div');c.className='card';
  c.innerHTML='<div class="cimg"><img loading="lazy" src="'+x.img+'" alt=""></div>'+
   '<div class="cbody"><div class="ctop"><span class="crank">#'+(i+1)+'</span><span class="badge">'+x.unit.toLocaleString()+UL+'</span></div>'+
   '<a class="cname" href="'+x.aff+'" target="_blank" rel="nofollow sponsored noopener">'+x.name+'</a>'+
   '<div class="cstars">'+stars(x.review)+' <span class="muted">'+x.review.toFixed(2)+'（'+x.rc.toLocaleString()+'件）</span></div>'+
   '<div class="metar"><span>寄付 <b>'+yen(x.price)+'</b></span><span>総量 <b>'+x.amt+SF+'</b></span><span>単価 <b class="fk">'+x.unit.toLocaleString()+UL+'</b></span></div>'+
   '<div class="ccospa">コスパ <b>'+x.cospa.toFixed(0)+'</b><span class="bar"><i style="width:'+Math.max(3,x.cospa)+'%"></i></span></div>'+
   '<a class="buy" href="'+x.aff+'" target="_blank" rel="nofollow sponsored noopener">楽天ふるさと納税で見る<span class="pr">PR</span></a></div>';
  list.appendChild(c);});
}
wEl.oninput=render; bEl.oninput=render;
document.querySelectorAll('.sorts button').forEach(b=>b.onclick=()=>{sortKey=b.dataset.s;
 document.querySelectorAll('.sorts button').forEach(x=>x.classList.toggle('on',x.dataset.s===sortKey));render();});
render();
"""

def build_cat(cfg):
    data = json.load(open(os.path.join(DATA, f"furusato-{cfg['slug']}.json"), encoding="utf-8"))
    slim = [{"id": m["id"], "name": m["name"], "price": m["price"], "amt": m["amt"], "unit": m["unit"],
             "review": m["review"], "rc": m["reviewCount"], "sat": m["sat"], "toku": m["toku"],
             "img": m["image"], "aff": m["affiliate"]} for m in data]
    maxp = ((max(m["price"] for m in data) + 999) // 1000) * 1000
    GUIDE_HTML, faq_ld = render_fguide(cfg["slug"], cfg["label"])
    body = f"""
<nav class="crumb"><a href="/">コスパナビ</a> › <a href="/furusato">ふるさと納税</a> › {cfg['label']}</nav>
<h1>ふるさと納税 {cfg['label']} コスパランキング<span class="yr">2026</span></h1>
<p class="lead">楽天ふるさと納税の{cfg['label']}を、<b>寄付額あたりの内容量（{cfg['unit_label']}）</b>とレビュー満足度から独自コスパ値でランキング。<b>{len(data)}件</b>を比較。定期便も総量に換算しています。<b>スライダーで「満足度／お得さ」を調整</b>できます。</p>
<div class="scallout">💡 掲載は楽天ふるさと納税の寄付額ですが、<b>寄付額は自治体が決めるため他サイトでも同額</b>です。どのサイトで申し込むのが良いかは <a href="/furusato-sites">ふるさと納税サイトの選び方（2025年ポイント廃止後）→</a></div>
{AD}
<div class="tool">
  <div class="ctl"><label>重視ポイント</label>
    <div class="slrow"><span>お得さ</span><input type="range" id="w" min="0" max="100" value="50"><span>満足度</span></div>
    <div class="wlabel"><span id="wtxt"></span></div>
  </div>
  <div class="ctl"><label>寄付額の上限</label>
    <div class="slrow"><input type="range" id="b" min="3000" max="{maxp}" step="1000" value="{maxp}"><span id="btxt"></span></div>
  </div>
  <div class="ctl"><label>並び替え</label>
    <div class="sorts"><button data-s="cospa" class="on">コスパ順</button><button data-s="unit">単価が安い順</button>
      <button data-s="sat">満足度順</button><button data-s="rc">レビュー数順</button></div>
  </div>
</div>
<p class="cnt"><b id="cnt"></b></p>
<div id="list" class="cards"></div>
<p class="note">※コスパ値＝満足度（レビューをレビュー数で信頼補正）×お得さ（{cfg['unit_label']}が安いほど高い）の独自指標。内容量は商品名から自動抽出のため、複数重量が選べる返礼品は掲載していません。<a href="/furusato">ふるさと納税コスパとは</a></p>
<script id="data" type="application/json">{json.dumps(slim, ensure_ascii=False, separators=(",", ":"))}</script>
<script>const UL={json.dumps(cfg['unit_label'], ensure_ascii=False)},SF={json.dumps(cfg['suffix'], ensure_ascii=False)};</script>
<script>{TOOL_JS}</script>
{AD}
{GUIDE_HTML}
"""
    title = f"ふるさと納税 {cfg['label']}のコスパ最強ランキング2026｜{cfg['unit_label']}で比較"
    desc = cfg["desc"]
    ld = {"@context": "https://schema.org", "@type": "ItemList", "name": title,
          "itemListElement": [{"@type": "ListItem", "position": m["rank"], "name": m["name"]} for m in data[:20]]}
    ld_list = [ld] + ([faq_ld] if faq_ld else [])
    head = "".join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in ld_list)
    head += bc_furusato(cfg["label"])
    open(os.path.join(SITE, cfg["file"]), "w", encoding="utf-8").write(shell(title, desc, body, cfg["file"], head))
    return len(data)

# (サイト名, 説明, MyLink pid or None, 公式URL or None)。pidがある広告主(提携済)は公式サイトへのアフィリリンクを付与。
SITES = [
    ("楽天ふるさと納税", "楽天市場と同じ操作感で使える最大級のサイト。返礼品数が多く、楽天カード・楽天ペイ決済に対応。普段から楽天を使う人はカード決済のポイントを貯めやすい。当サイトのランキングも楽天のデータを利用。", None, None),
    ("さとふる", "返礼品の掲載数が最大級で、初心者にも分かりやすいUI。発送が早い返礼品が多く、PayPay・クレジットカード決済に対応。「とにかく選択肢を広く見たい」人に。", None, None),  # 提携見送り(2026-07)→再申請までリンク無し
    ("ふるさとチョイス", "掲載自治体数No.1クラスで、地方の穴場返礼品まで最も網羅的。Amazon Pay・各種決済に対応。「他に無い返礼品を探したい」網羅性重視の人向け。", None, None),
    ("ふるなび", "家電・電化製品の返礼品に強く、初心者向けの見やすさが特徴。独自の「ふるなびコイン」やキャンペーンあり。家電狙いの人に。", None, None),  # 提携見送り(2026-07)→再申請までリンク無し
    ("au PAY ふるさと納税", "au・Pontaユーザーと相性が良く、Pontaポイントでの決済も可能。auの経済圏を使っている人向け。", None, None),
]

def build_guide():
    def card(n, d, pid, url):
        link = (f'<p><a class="buy sm" href="{vc_mylink(pid, url)}" target="_blank" rel="nofollow sponsored noopener">'
                f'{H.escape(n)}を見る<span class="pr">PR</span></a></p>') if pid else ""
        return f'<div class="gpt"><h3>{H.escape(n)}</h3><p>{H.escape(d)}</p>{link}</div>'
    site_cards = "".join(card(*s) for s in SITES)
    faqs = [
        ("結局どのサイトが一番お得ですか？", "2025年10月以降はどのサイトも寄付額・返礼品は同じで、サイト独自のポイント付与も無くなりました。そのため「普段使っているクレジットカード・決済のポイントが貯まるサイト」を選ぶのが実質的に一番お得です。あとは品揃えと使いやすさで選びましょう。"),
        ("寄付額はサイトによって違いますか？", "違いません。ふるさと納税の寄付額は各自治体が定めているため、同じ返礼品ならどのサイトでも寄付額は同額です。だからサイトごとの「最安値比較」は存在しません。"),
        ("ポイントはもう一切もらえないのですか？", "ポータルサイトが独自に付与するポイントは2025年10月から廃止されました。ただし、寄付の支払いに使うクレジットカードや各種Pay決済でカード会社・決済事業者が付与するポイントは、これまで通り受け取れます。"),
        ("控除の上限額はどう決まりますか？", "年収・家族構成・他の控除によって決まります。上限を超えた寄付は自己負担になるため、各サイトの控除額シミュレーターで事前に目安を確認しましょう。"),
    ]
    faq_html = "".join(f'<div class="faq"><h3>Q. {H.escape(q)}</h3><p>A. {H.escape(a)}</p></div>' for q, a in faqs)
    faq_ld = {"@context": "https://schema.org", "@type": "FAQPage",
              "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faqs]}
    body = f"""
<nav class="crumb"><a href="/">コスパナビ</a> › <a href="/furusato">ふるさと納税</a> › サイトの選び方</nav>
<h1>ふるさと納税サイトの選び方<span class="yr">2026</span>｜ポイント廃止後の比較</h1>
<p class="lead">「どのふるさと納税サイトで寄付するのが得？」——2025年10月の制度変更で答えが変わりました。<b>ポイント付与が廃止された今の正しい選び方</b>を、主要サイトの比較とあわせて解説します。</p>
{AD}
<div class="sguide">
<h2>【重要】2025年10月からポイント付与は廃止されました</h2>
<p>2025年10月1日の総務省ルール改正により、<b>楽天・さとふる・ふるなび・ふるさとチョイス・au PAY など全てのポータルサイトで、サイト独自のポイント付与が禁止</b>されました。つまり「還元率が高いサイトを選ぶ」という選び方は<b>もうできません</b>。同じ返礼品なら寄付額もポイントも各サイト横並びです。</p>
<h2>では今、どうやってお得にする？</h2>
<p>ポイント付与の禁止は「ポータルサイトが配るポイント」の話です。<b>寄付の支払いに使うクレジットカードや◯◯Pay決済で、カード会社・決済事業者側が付与するポイントは従来どおり受け取れます</b>。そのため今は「どのサイトか」よりも<b>「どの決済手段（カード）で払うか」</b>のほうが実質的なお得さに直結します。<br>※各社の付与ルールやキャンペーンは変わりやすいので、寄付前に必ず最新の条件をご確認ください。</p>
<h2>主要ふるさと納税サイト比較</h2>
<div class="gpts">{site_cards}</div>
<h2>ポイント廃止後の「サイトの選び方」4つの基準</h2>
<div class="gpts">
<div class="gpt"><h3>① 普段使う決済・経済圏</h3><p>楽天カードなら楽天、au/Pontaならau PAY など、自分が普段ポイントを貯めている決済が使えるサイトを選ぶと、カード側ポイントで実質お得になります。</p></div>
<div class="gpt"><h3>② 返礼品の品揃え</h3><p>欲しい返礼品があるかが最優先。掲載数が多いさとふる、掲載自治体が最も広いふるさとチョイスなどは選択肢が豊富です。</p></div>
<div class="gpt"><h3>③ 使いやすさ・発送の早さ</h3><p>初めてなら操作の分かりやすいサイトを。年末の駆け込みでは発送が早い返礼品が多いサイトが安心です。</p></div>
<div class="gpt"><h3>④ 控除シミュレーターの有無</h3><p>上限額を超えると自己負担になります。各サイトのシミュレーターで、年収・家族構成に応じた目安額を先に確認しましょう。</p></div>
</div>
<h2>よくある質問</h2>
<div class="faqs">{faq_html}</div>
<p class="note">本ページは制度の一般的な解説です。控除・ポイント・キャンペーンの最新条件は各サイト・自治体の公式情報をご確認ください。当サイトのランキングは<a href="/furusato">ふるさと納税コスパ分析</a>から。</p>
</div>
"""
    title = "ふるさと納税サイトの選び方2026｜ポイント廃止後の比較とお得な方法"
    desc = "2025年10月のポイント付与廃止後、ふるさと納税サイトはどう選ぶ？楽天・さとふる・ふるさとチョイス・ふるなび等を比較し、今もお得にする方法（決済ポイント）を解説。"
    head = f'<script type="application/ld+json">{json.dumps(faq_ld, ensure_ascii=False)}</script>'
    head += bc_furusato("ふるさと納税サイトの選び方")
    open(os.path.join(SITE, "furusato-sites.html"), "w", encoding="utf-8").write(shell(title, desc, body, "furusato-sites.html", head))

# ================= 現地で使える体験（全国から県で探す） =================
PREFS = ["北海道","青森県","岩手県","宮城県","秋田県","山形県","福島県","茨城県","栃木県","群馬県",
         "埼玉県","千葉県","東京都","神奈川県","新潟県","富山県","石川県","福井県","山梨県","長野県",
         "岐阜県","静岡県","愛知県","三重県","滋賀県","京都府","大阪府","兵庫県","奈良県","和歌山県",
         "鳥取県","島根県","岡山県","広島県","山口県","徳島県","香川県","愛媛県","高知県","福岡県",
         "佐賀県","長崎県","熊本県","大分県","宮崎県","鹿児島県","沖縄県"]
# 地方別の並び（北→南、地図的に上から）。ページ上で「全国から選ぶ」レイアウトに
REGIONS = [
    ("北海道", ["北海道"]),
    ("東北", ["青森県","岩手県","宮城県","秋田県","山形県","福島県"]),
    ("関東", ["茨城県","栃木県","群馬県","埼玉県","千葉県","東京都","神奈川県"]),
    ("中部", ["新潟県","富山県","石川県","福井県","山梨県","長野県","岐阜県","静岡県","愛知県"]),
    ("近畿", ["三重県","滋賀県","京都府","大阪府","兵庫県","奈良県","和歌山県"]),
    ("中国", ["鳥取県","島根県","岡山県","広島県","山口県"]),
    ("四国", ["徳島県","香川県","愛媛県","高知県"]),
    ("九州・沖縄", ["福岡県","佐賀県","長崎県","熊本県","大分県","宮崎県","鹿児島県","沖縄県"]),
]
LTYPES = ["宿泊", "食事", "温泉", "レジャー・体験", "ゴルフ", "利用券"]

def _ltype(n):
    if any(k in n for k in ("宿泊", "旅館", "ホテル", "1泊", "１泊", "泊2食", "コテージ")): return "宿泊"
    if any(k in n for k in ("温泉", "入浴", "サウナ", "スパ")): return "温泉"
    if any(k in n for k in ("食事券", "お食事券", "ランチ", "ディナー", "レストラン", "飲食", "グルメ券", "食券")): return "食事"
    if "ゴルフ" in n: return "ゴルフ"
    if any(k in n for k in ("入場券", "入園券", "チケット", "レジャー", "水族館", "動物園", "遊園", "スキー", "体験", "招待券", "サファリ", "パーク", "乗車", "クルーズ", "遊覧")): return "レジャー・体験"
    return "利用券"

def _short_pref(p):
    return p[:-1] if p.endswith(("県", "府")) else p  # 東京都/北海道はそのまま、〇〇県/府は末尾を落とす

def _muni(shop, pref):
    return shop[len(pref):] if shop.startswith(pref) else shop

def build_local():
    path = os.path.join(DATA, "furusato-local_raw.json")
    if not os.path.exists(path):
        print("  (furusato-local_raw.json 無し→現地体験ページはスキップ)")
        return 0
    raw = json.load(open(path, encoding="utf-8"))
    items = []
    for x in raw:
        pref = x.get("pref")
        if pref not in PREFS:
            continue
        items.append({
            "p": pref, "t": _ltype(x["name"]),
            "n": x["name"].replace("【ふるさと納税】", "").strip()[:60],
            "m": _muni(x["shop"], pref), "y": x["price"],
            "r": round(float(x.get("review") or 0), 2), "c": x.get("reviewCount") or 0,
            "img": x.get("image", ""), "a": x.get("affiliate") or x.get("url"),
        })
    # レビュー数→寄付額の順で並べておく（JS側は表示順を尊重）
    items.sort(key=lambda z: (-z["c"], z["y"]))
    per_pref = {}
    for it in items:
        per_pref[it["p"]] = per_pref.get(it["p"], 0) + 1
    # 地図（地方→県タイル）
    region_html = ""
    for rname, prefs in REGIONS:
        tiles = ""
        for p in prefs:
            n = per_pref.get(p, 0)
            cls = "ptile" + ("" if n else " off")
            dis = "" if n else " aria-disabled=\"true\""
            tiles += (f'<button class="{cls}" data-pref="{p}"{dis}>'
                      f'<span class="pn">{_short_pref(p)}</span><span class="pc">{n}</span></button>')
        region_html += f'<div class="region"><span class="rname">{rname}</span><div class="ptiles">{tiles}</div></div>'
    type_chips = '<button class="lchip on" data-t="">すべて</button>' + "".join(
        f'<button class="lchip" data-t="{t}">{t}</button>' for t in LTYPES)
    DATA_JSON = json.dumps(items, ensure_ascii=False, separators=(",", ":"))
    total = len(items)
    body = f"""
<nav class="crumb"><a href="/">コスパナビ</a> › <a href="/furusato">ふるさと納税</a> › 現地で使える体験</nav>
<h1>ふるさと納税で「現地で使える」体験を全国から探す<span class="yr">2026</span></h1>
<p class="lead">寄付先の<b>現地で使える</b>食事券・宿泊券・温泉・レジャー施設・ゴルフ・利用券などの返礼品を、<b>全国{total:,}件</b>から都道府県別に探せます。旅行や帰省の予定に合わせて、行き先の自治体に寄付すれば“現地で楽しめる”のが魅力です。<b>地図から県を選ぶ</b>と、その県で使える返礼品が一覧表示されます。</p>
{AD}
<div class="jpmap">{region_html}</div>
<div id="localres">
  <div class="lbar"><h2 id="lhead">県を選んでください</h2><div class="lchips">{type_chips}</div></div>
  <p class="cnt"><b id="lcnt"></b></p>
  <div id="llist" class="cards"></div>
</div>
<section class="guide">
<h2>ふるさと納税の「現地利用型」返礼品とは</h2>
<p>返礼品というと肉や米などの“送られてくる特産品”を思い浮かべがちですが、寄付先の<b>現地に行って使うタイプ</b>の返礼品も数多くあります。旅館・ホテルの宿泊券、レストランの食事券、温泉施設や動物園・水族館などのレジャー施設の入場券、ゴルフ場の利用券、対象施設で使えるクーポンなどです。旅行や帰省、レジャーの予定がある人にとっては、<b>実質2,000円の自己負担で現地での体験費用を大きく賄える</b>ため非常にお得です。</p>
<div class="gpts">
<div class="gpt"><h3>使い方は？</h3><p>行きたいエリアの都道府県を地図から選び、宿泊・食事・レジャーなど目的のタイプで絞り込みます。気になる返礼品は「楽天ふるさと納税で見る」から寄付できます。</p></div>
<div class="gpt"><h3>寄付額はサイトで違う？</h3><p>寄付額は自治体が決めるため、どのふるさと納税サイトでも同額です。掲載は楽天ふるさと納税のデータですが、金額の比較で損得は生じません。</p></div>
<div class="gpt"><h3>注意点は？</h3><p>有効期限・予約要否・対象施設・利用条件は返礼品ごとに異なります。申込前に必ず各返礼品ページの記載をご確認ください。控除上限額は年収・家族構成で変わります。</p></div>
</div>
<h2>よくある質問</h2>
<div class="faqs">
<div class="faq"><h3>Q. 現地で使える返礼品はどんな種類がありますか？</h3><p>A. 宿泊券、食事券、温泉・入浴、動物園や水族館などのレジャー施設の入場券、ゴルフ利用券、対象施設で使えるクーポンなどがあります。本ページでは都道府県×タイプで探せます。</p></div>
<div class="faq"><h3>Q. 旅行先の自治体に寄付すれば現地で使えますか？</h3><p>A. はい。行き先の都道府県・自治体の返礼品を選べば、その土地で使える体験・チケットとして活用できます。旅行や帰省の予定に合わせて選ぶのがおすすめです。</p></div>
<div class="faq"><h3>Q. 予約は必要ですか？有効期限は？</h3><p>A. 返礼品によって異なります。事前予約が必要なものや、発行から半年〜1年程度の有効期限があるものが多いので、必ず各返礼品の記載を確認してください。</p></div>
</div>
</section>
<script id="ldata" type="application/json">{DATA_JSON}</script>
<script>{LOCAL_JS}</script>
"""
    title = "ふるさと納税で現地で使える体験を全国から探す｜食事券・宿泊・レジャー"
    desc = f"寄付先の現地で使える食事券・宿泊券・温泉・レジャー施設・ゴルフ・利用券のふるさと納税返礼品を、全国{total:,}件から都道府県別に探せます。旅行・帰省先で使えてお得。"
    open(os.path.join(SITE, "furusato-local.html"), "w", encoding="utf-8").write(
        shell(title, desc, body, "furusato-local.html", head=LOCAL_CSS + bc_furusato("現地で使える体験")))
    print(f"  現地体験ページ: {total}件 / {len(per_pref)}県")
    return total

LOCAL_CSS = ("<style>"
    ".jpmap{display:flex;flex-direction:column;gap:8px;margin:14px 0}"
    ".region{display:flex;gap:10px;align-items:flex-start;flex-wrap:wrap}"
    ".rname{flex:0 0 68px;font-weight:800;color:var(--accent);font-size:.82rem;padding-top:8px}"
    ".ptiles{display:flex;flex-wrap:wrap;gap:6px;flex:1}"
    ".ptile{position:relative;min-width:58px;background:var(--card);border:1px solid var(--line);border-radius:9px;padding:7px 6px 6px;cursor:pointer;text-align:center;color:var(--ink)}"
    ".ptile:hover{border-color:var(--accent)}.ptile.on{background:var(--accent);color:#fff;border-color:var(--accent)}"
    ".ptile .pn{display:block;font-size:.82rem;font-weight:700;line-height:1.2}"
    ".ptile .pc{display:block;font-size:.68rem;color:var(--sub);margin-top:1px}.ptile.on .pc{color:#ffe}"
    ".ptile.off{opacity:.4;cursor:default;pointer-events:none}"
    ".lbar{display:flex;flex-wrap:wrap;align-items:center;gap:8px 14px;margin-top:8px}"
    ".lchips{display:flex;flex-wrap:wrap;gap:6px}"
    ".lchip{border:1px solid var(--line);background:var(--bg);color:var(--ink);border-radius:16px;padding:5px 12px;font-size:.84rem;cursor:pointer}"
    ".lchip.on{background:var(--accent);color:#fff;border-color:var(--accent)}"
    ".ltag{display:inline-block;background:var(--chip);color:var(--accent);border-radius:6px;padding:1px 7px;font-size:.7rem;font-weight:700;margin-bottom:3px}"
    ".lmuni{font-size:.75rem;color:var(--sub)}"
    "@media(max-width:520px){.rname{flex-basis:100%;padding-top:0}}"
    "</style>")

LOCAL_JS = r"""
const LD=JSON.parse(document.getElementById('ldata').textContent);
const list=document.getElementById('llist'),head=document.getElementById('lhead'),cnt=document.getElementById('lcnt');
let selP='',selT='';
const yen=v=>'¥'+v.toLocaleString();
const star=v=>{v=Math.round(v);return '★'.repeat(v)+'☆'.repeat(5-v);};
function render(){
  if(!selP){list.innerHTML='';cnt.textContent='';return;}
  let a=LD.filter(x=>x.p===selP&&(!selT||x.t===selT));
  head.textContent=selP+'で現地で使える返礼品';
  cnt.innerHTML='<b>'+a.length+'件</b>'+(selT?'（'+selT+'）':'');
  list.innerHTML=a.slice(0,120).map(x=>{
    const img=x.img?'<div class="cimg"><img loading="lazy" src="'+x.img+'" alt=""></div>':'';
    const rev=x.c>0?'<div class="cstars">'+star(x.r)+' <span class="muted">'+x.r.toFixed(2)+'（'+x.c+'）</span></div>':'';
    return '<div class="card">'+img+'<div class="cbody">'
      +'<span class="ltag">'+x.t+'</span>'
      +'<a class="cname" href="'+x.a+'" target="_blank" rel="nofollow sponsored noopener" title="'+x.n.replace(/"/g,'')+'">'+x.n+'</a>'
      +'<div class="lmuni">'+x.m+'</div>'
      +'<div class="cprice">'+yen(x.y)+'<span class="muted"> 寄付</span></div>'+rev
      +'<a class="buy sm" href="'+x.a+'" target="_blank" rel="nofollow sponsored noopener">楽天ふるさと納税で見る<span class="pr">PR</span></a>'
      +'</div></div>';
  }).join('');
  if(a.length>120){list.innerHTML+='<p class="note">上位120件を表示中（レビュー数順）。</p>';}
}
document.querySelectorAll('.ptile').forEach(b=>b.addEventListener('click',()=>{
  document.querySelectorAll('.ptile').forEach(x=>x.classList.remove('on'));
  b.classList.add('on');selP=b.dataset.pref;render();
  document.getElementById('localres').scrollIntoView({behavior:'smooth',block:'start'});
}));
document.querySelectorAll('.lchip').forEach(b=>b.addEventListener('click',()=>{
  document.querySelectorAll('.lchip').forEach(x=>x.classList.remove('on'));
  b.classList.add('on');selT=b.dataset.t;render();
}));
"""

# ================= 高評価殿堂（失敗しない返礼品・全カテゴリ横断） =================
def pref_of(shop):
    for p in PREFS:
        if shop.startswith(p):
            return p
    return ""

# カテゴリ(slug)→グループ（チップ絞り込み用）
HGROUPS = [("all","すべて"),("meat","肉"),("seafood","魚介"),("rice-egg","米・卵"),
           ("fruit-sweets","果物・スイーツ"),("drink","飲料・お酒"),("daily","日用品"),("local","現地体験")]
SLUG2GROUP = {"beef":"meat","pork":"meat","chicken":"meat","hamburg":"meat","seafood":"seafood",
              "rice":"rice-egg","egg":"rice-egg","fruit":"fruit-sweets","sweets":"fruit-sweets",
              "frozen":"fruit-sweets","beer":"drink","drink":"drink","toilet-paper":"daily",
              "tissue":"daily","detergent":"daily","local":"local"}

def build_hall():
    MIN_R, MIN_RC, TOPN = 4.7, 50, 400
    sources = [(s, FCATS[s]["label"], os.path.join(DATA, f"furusato-{s}_raw.json")) for s in FCATS]
    sources.append(("local", "現地体験", os.path.join(DATA, "furusato-local_raw.json")))
    seen = {}
    revs = []
    for slug, label, f in sources:
        if not os.path.exists(f):
            continue
        for x in json.load(open(f, encoding="utf-8")):
            key = x.get("affiliate") or x.get("url")
            if not key or key in seen:
                continue
            rc = x.get("reviewCount") or 0
            r = round(float(x.get("review") or 0), 2)
            pref = x.get("pref") or pref_of(x.get("shop", ""))
            seen[key] = {"slug": slug, "cat": label, "r": r, "rc": rc, "pref": pref,
                         "name": x["name"].replace("【ふるさと納税】", "").strip()[:56],
                         "muni": _muni(x.get("shop", ""), pref) if pref else x.get("shop", ""),
                         "price": x["price"], "img": x.get("image", ""),
                         "aff": x.get("affiliate") or x.get("url")}
            if rc > 0:
                revs.append(r)
    C = (sum(revs) / len(revs)) if revs else 4.5
    m = 100
    pool = [x for x in seen.values() if x["r"] >= MIN_R and x["rc"] >= MIN_RC]
    for x in pool:
        x["bayes"] = (x["rc"] / (x["rc"] + m)) * x["r"] + (m / (x["rc"] + m)) * C
    pool.sort(key=lambda z: -z["bayes"])
    pool = pool[:TOPN]
    items = [{"k": i + 1, "g": SLUG2GROUP.get(x["slug"], "other"), "c": x["cat"],
              "n": x["name"], "p": x["pref"], "m": x["muni"], "y": x["price"],
              "r": x["r"], "rc": x["rc"], "img": x["img"], "a": x["aff"]}
             for i, x in enumerate(pool)]
    total = len(items)
    chips = "".join(f'<button class="lchip{" on" if g=="all" else ""}" data-g="{g}">{lab}</button>' for g, lab in HGROUPS)
    DATA_JSON = json.dumps(items, ensure_ascii=False, separators=(",", ":"))
    body = f"""
<nav class="crumb"><a href="/">コスパナビ</a> › <a href="/furusato">ふるさと納税</a> › 高評価殿堂</nav>
<h1>ふるさと納税 高評価殿堂<span class="yr">2026</span></h1>
<p class="lead">楽天ふるさと納税の全カテゴリ約23,000件の返礼品から、<b>★4.7以上・レビュー多数</b>の「まず失敗しない」返礼品だけを厳選し、レビュー数で信頼補正した独自スコアで横断ランキング。<b>迷ったらここから選べば外さない</b>、殿堂入りの{total}品です。</p>
{AD}
<div class="lbar"><h2>殿堂ランキング</h2><div class="lchips">{chips}</div></div>
<p class="cnt"><b id="hcnt"></b></p>
<div id="hlist" class="cards"></div>
<section class="guide">
<h2>「高評価殿堂」の選び方</h2>
<p>ふるさと納税は種類が多すぎて「どれを選べば失敗しないか」が分かりにくいもの。このページは<b>レビュー★4.7以上かつレビュー件数の多い返礼品</b>だけを全カテゴリから集め、<b>「高評価×たくさんの人が満足」</b>を数値化（ベイズ補正）して並べています。★5.0でもレビュー2件のような“怪しい高評価”は上位に来ないよう補正しているため、<b>本当に多くの人が満足した鉄板返礼品</b>が上位に並びます。</p>
<div class="gpts">
<div class="gpt"><h3>なぜレビュー数も見るの？</h3><p>★の高さだけだと、数件のレビューでたまたま高評価になった商品が紛れ込みます。レビュー件数が多いほど評価は信頼でき、当ランキングは件数で重みづけしています。</p></div>
<div class="gpt"><h3>寄付額はサイトで違う？</h3><p>寄付額は自治体が決めるため、どのふるさと納税サイトでも同額です。掲載は楽天ふるさと納税のデータです。</p></div>
<div class="gpt"><h3>カテゴリで絞れる？</h3><p>上のチップで肉・魚介・米卵・果物スイーツ・飲料お酒・日用品・現地体験に絞り込めます。目的が決まっている人はチップで絞ると探しやすくなります。</p></div>
</div>
<h2>よくある質問</h2>
<div class="faqs">
<div class="faq"><h3>Q. 迷ったら何を選べばいい？</h3><p>A. まずこの殿堂ランキングの上位から、欲しいジャンル（肉・魚介・果物など）で絞って選べば大きく外しません。いずれも多くの人が高評価をつけた実績のある返礼品です。</p></div>
<div class="faq"><h3>Q. ランキングの基準は？</h3><p>A. レビュー★4.7以上・レビュー50件以上を対象に、レビュー件数で信頼補正した独自スコア順です。件数が多く評価も高い返礼品ほど上位になります。</p></div>
<div class="faq"><h3>Q. コスパ（量あたりの安さ）でも選びたい</h3><p>A. 各カテゴリの<a href="/furusato">コスパランキング</a>では、寄付額あたりの内容量（円/kg等）で選べます。殿堂は“満足度”、コスパランキングは“量あたりのお得さ”で見る使い分けがおすすめです。</p></div>
</div>
</section>
<script id="hdata" type="application/json">{DATA_JSON}</script>
<script>{HALL_JS}</script>
"""
    title = "ふるさと納税 高評価殿堂2026｜★4.7以上の失敗しない返礼品ランキング"
    desc = f"楽天ふるさと納税の全カテゴリから★4.7以上・レビュー多数の返礼品だけを厳選、信頼補正した独自スコアで横断ランキング。迷ったら選べば外さない殿堂入り{total}品。"
    open(os.path.join(SITE, "furusato-hall.html"), "w", encoding="utf-8").write(
        shell(title, desc, body, "furusato-hall.html", head=HALL_CSS + bc_furusato("高評価殿堂")))
    print(f"  高評価殿堂ページ: {total}品 (★{MIN_R}+ & レビュー{MIN_RC}+)")
    return total

HALL_CSS = ("<style>"
    ".hrank{position:absolute;top:-6px;left:-6px;background:var(--accent);color:#fff;font-weight:800;"
    "font-size:.8rem;min-width:26px;height:26px;border-radius:50%;display:flex;align-items:center;justify-content:center;box-shadow:0 1px 4px rgba(0,0,0,.2)}"
    ".hrank.top{background:#e8a800}"
    ".card{position:relative}"
    "</style>")

HALL_JS = r"""
const HD=JSON.parse(document.getElementById('hdata').textContent);
const list=document.getElementById('hlist'),cnt=document.getElementById('hcnt');
let selG='all';
const yen=v=>'¥'+v.toLocaleString();
const star=v=>{v=Math.round(v);return '★'.repeat(v)+'☆'.repeat(5-v);};
function render(){
  let a=(selG==='all')?HD:HD.filter(x=>x.g===selG);
  cnt.innerHTML='<b>'+a.length+'品</b>'+(selG==='all'?'（全カテゴリ殿堂）':'');
  list.innerHTML=a.slice(0,150).map(x=>{
    const img=x.img?'<div class="cimg"><img loading="lazy" src="'+x.img+'" alt=""></div>':'';
    const rc='<div class="cstars">'+star(x.r)+' <span class="muted">'+x.r.toFixed(2)+'（'+x.rc.toLocaleString()+'件）</span></div>';
    const loc=x.p?('<div class="lmuni">'+x.p+(x.m&&x.m!==x.p?' '+x.m:'')+'</div>'):'';
    const rk='<span class="hrank'+(x.k<=3?' top':'')+'">'+x.k+'</span>';
    return '<div class="card">'+rk+img+'<div class="cbody">'
      +'<span class="ltag">'+x.c+'</span>'
      +'<a class="cname" href="'+x.a+'" target="_blank" rel="nofollow sponsored noopener" title="'+x.n.replace(/"/g,'')+'">'+x.n+'</a>'
      +loc+'<div class="cprice">'+yen(x.y)+'<span class="muted"> 寄付</span></div>'+rc
      +'<a class="buy sm" href="'+x.a+'" target="_blank" rel="nofollow sponsored noopener">楽天ふるさと納税で見る<span class="pr">PR</span></a>'
      +'</div></div>';
  }).join('');
  if(a.length>150){list.innerHTML+='<p class="note">上位150品を表示中（殿堂スコア順）。</p>';}
}
document.querySelectorAll('.lchip').forEach(b=>b.addEventListener('click',()=>{
  document.querySelectorAll('.lchip').forEach(x=>x.classList.remove('on'));
  b.classList.add('on');selG=b.dataset.g;render();
}));
render();
"""

def build_hub(counts):
    # 3列グリッドで偶数行(2,4,6…)の中央=最終位置4,10,16…(pos%6==4)に広告を差し込む。banner循環。
    parts = []
    ci = pos = adn = 0
    while ci < len(CATS):
        if pos % 6 == 4 and IN_GRID_ADS:   # 偶数行(2,4,6…)の中央を広告で埋める(banner循環)
            parts.append(IN_GRID_ADS[adn % len(IN_GRID_ADS)]); adn += 1; pos += 1
            continue
        c = CATS[ci]
        parts.append(f'<a class="hcard" href="{U(c["file"])}"><div class="hico">{c["icon"]}</div>'
                     f'<div><h3>{c["label"]}<span class="n">{counts[c["slug"]]}件</span></h3><p>{c["desc"]}</p></div></a>')
        ci += 1; pos += 1
    cards = "".join(parts)
    body = f"""
<div class="hero"><h1>ふるさと納税 コスパ分析<span class="yr">2026</span></h1>
<p class="lead">「実質2,000円で本当にお得な返礼品は？」——楽天ふるさと納税の返礼品を、<b>寄付額あたりの内容量（円/kg等）</b>とレビュー満足度から独自コスパ値でランキング。<b>定期便も総量に換算</b>して、量あたり本当にお得な返礼品を選べます。</p></div>
{AD}
<div class="scallout">📢 <b>2025年10月からふるさと納税のポイント付与は廃止されました。</b>今のお得なサイトの選び方は <a href="/furusato-sites">ふるさと納税サイトの選び方（ポイント廃止後）→</a></div>
<a class="fbanner" href="/furusato-hall"><div class="hico">🏆</div><div><h3>高評価殿堂 — 失敗しない返礼品<span class="n">NEW</span></h3><p>全カテゴリ約23,000件から<b>★4.7以上・レビュー多数</b>の鉄板返礼品だけを厳選。<b>迷ったらここから選べば外さない</b>横断ランキング。</p></div><span class="fgo">見る →</span></a>
<a class="fbanner" href="/furusato-local"><div class="hico">🗾</div><div><h3>現地で使える体験を全国から探す<span class="n">NEW</span></h3><p>食事券・宿泊・温泉・レジャー施設・ゴルフ・利用券など、<b>旅行や帰省先の現地で使える</b>返礼品を都道府県別に探せます。地図から県を選ぶだけ。</p></div><span class="fgo">見る →</span></a>
<div class="hgrid">{cards}</div>
<div class="soonbox"><p class="lead">今後追加予定：</p><span class="soon">野菜</span><span class="soon">パン</span><span class="soon">チーズ・乳製品</span><span class="soon">調味料</span><span class="soon">日本酒・焼酎</span><span class="soon">コーヒー</span></div>
<h2>ふるさと納税のコスパの考え方</h2>
<p>ふるさと納税は寄付額のうち自己負担2,000円を除いた分が控除されるため、<b>「いかに安く返礼品を得るか」ではなく「同じ寄付額でどれだけ量・質の良い返礼品がもらえるか」</b>がコスパの本質です。当サイトは返礼品の<b>内容量あたりの寄付額（円/kg など）</b>を軸に、レビュー満足度と組み合わせて独自にランキングしています。控除上限額はご自身の年収・家族構成で異なります。詳しくは<a href="/about">コスパ値とは</a>。</p>
"""
    title = "ふるさと納税コスパ分析2026｜円/kgで選ぶお得な返礼品ランキング"
    desc = "楽天ふるさと納税の返礼品を寄付額あたりの内容量（円/kg等）とレビュー満足度で独自コスパランキング。定期便も総量換算で比較。米など。"
    hub_bc = breadcrumb_ld([("コスパナビ", SITE_URL + "/"), ("ふるさと納税", None)])
    open(os.path.join(SITE, "furusato.html"), "w", encoding="utf-8").write(shell(title, desc, body, "furusato.html", hub_bc))

def add_to_sitemap():
    # build_site生成のsitemap.xmlにふるさと納税ページを追記(未登録なら)
    sp = os.path.join(SITE, "sitemap.xml")
    if not os.path.exists(sp):
        return
    xml = open(sp, encoding="utf-8").read()
    add = ""
    for path in ["furusato.html", "furusato-sites.html", "furusato-local.html", "furusato-hall.html"] + [c["file"] for c in CATS]:
        loc = f"{SITE_URL}{U(path)}"
        if loc not in xml:
            add += f"<url><loc>{loc}</loc><lastmod>{UPDATED}</lastmod></url>"
    if add:
        xml = xml.replace("</urlset>", add + "</urlset>")
        open(sp, "w", encoding="utf-8").write(xml)

if __name__ == "__main__":
    counts = {}
    for c in CATS:
        counts[c["slug"]] = build_cat(c)
    build_guide()
    nloc = build_local()
    nhall = build_hall()
    build_hub(counts)
    add_to_sitemap()
    print(f"生成: furusato.html(ハブ) + サイト選び方 + 現地体験({nloc}件) + 殿堂({nhall}品) + {len(CATS)}カテゴリ  {counts}")
