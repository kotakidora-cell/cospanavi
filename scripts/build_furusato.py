# ふるさと納税コスパ分析ページを生成。ランディング(furusato.html)＋カテゴリ(furusato-<slug>.html)。
# 通常商品とロジックが違う(寄付額あたりの内容量=お得さ)ため専用ビルダー。styles.cssは共用。
import json, os, sys, html as H, datetime
from furusato_cats import FCATS

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
SITE = os.path.join(BASE, "site")
SITE_URL = "https://cospa-navi.com"
UPDATED = datetime.date.today().isoformat()
ADSENSE = '<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-8706760047070867" crossorigin="anonymous"></script>'
VERIFY = '<meta name="google-site-verification" content="9Lq7hmAO3CeIlcT6nM2tB2_AksHlZsugoZ_VIeeY5Dc">'
AD = '<div class="ad">広告スペース（Google AdSense）</div>'
# バリューコマース広告バナー(カテゴリカード風に1枠としてグリッド内へ)。ステマ規制対応で「広告」表記付き。
def _vc(pid, cls="adcard"):
    return (f'<div class="{cls}"><span class="adlabel">広告</span>'
            f'<script language="javascript" src="//ad.jp.ap.valuecommerce.com/servlet/jsbanner?sid=3775700&pid={pid}"></script>'
            f'<noscript><a href="//ck.jp.ap.valuecommerce.com/servlet/referral?sid=3775700&pid={pid}" rel="nofollow">'
            f'<img src="//ad.jp.ap.valuecommerce.com/servlet/gifbanner?sid=3775700&pid={pid}" border="0"></a></noscript></div>')

IN_GRID_ADS = []   # グリッド内広告は余白が出て見た目が悪いため無し(横長バナーはグリッド下の帯＋スマホはオーバーレイ)
# PC用: 食べログ 468×60 横長バナー(グリッド下に中央の帯。スマホでは非表示=CSSで制御)
VC_468_PC = _vc("892664051", "adbanner-pc")
# スマホ用: 食べログ 320×50 オーバーレイ(VCがスマホ時のみ画面下部に固定表示。スクリプトを置くだけ)
VC_320_OVERLAY = ('<script language="javascript" '
                  'src="//ad.jp.ap.valuecommerce.com/servlet/smartphonebanner?sid=3775700&pid=892664050&position=overlay"></script>')

ICON = {"rice": "🍚", "beef": "🥩", "pork": "🐖", "chicken": "🍗", "hamburg": "🍔", "seafood": "🦐",
        "fruit": "🍇", "beer": "🍺", "drink": "🥤", "toilet-paper": "🧻", "tissue": "🤧", "detergent": "🧴"}
# ジャンル順(米→肉→魚介→果物→飲料→日用品)でユーザーが探しやすく
CAT_ORDER = ["rice", "beef", "pork", "chicken", "hamburg", "seafood", "fruit", "beer", "drink",
             "toilet-paper", "tissue"]
CATS = [{"slug": s, "file": f"furusato-{s}.html", "label": FCATS[s]["label"], "icon": ICON.get(s, "🎁"),
         "unit_label": FCATS[s]["unit_label"], "suffix": FCATS[s]["suffix"],
         "desc": f"楽天ふるさと納税の{FCATS[s]['label']}を、寄付額あたりの内容量（{FCATS[s]['unit_label']}）とレビュー満足度でコスパランキング。"}
        for s in CAT_ORDER]

def nav():
    return ('<header class="nav"><a class="brand" href="index.html">コスパ<b>ナビ</b></a>'
            '<nav><a href="index.html">ホーム</a><a href="furusato.html">ふるさと納税</a>'
            '<a href="about.html">コスパ値とは</a><a href="privacy.html">プライバシー</a></nav></header>')

def foot():
    cl = "".join(f'<a href="{c["file"]}">{c["label"]}</a>' for c in CATS)
    return (f'<footer class="foot"><nav class="fcats"><a href="furusato.html">ふるさと納税トップ</a>{cl}</nav>'
            f'<p>寄付額・レビューは楽天ふるさと納税の情報（{UPDATED}時点）。内容量は商品名から自動抽出のため、必ず各返礼品ページで最新情報をご確認ください。</p>'
            f'<p class="muted">当サイトはアフィリエイト広告を利用しています。<a href="privacy.html">プライバシーポリシー</a></p></footer>')

def shell(title, desc, body, path, head=""):
    url = SITE_URL + "/" + path
    canon = (f'<link rel="canonical" href="{url}">'
             f'<meta property="og:type" content="website"><meta property="og:title" content="{H.escape(title)}">'
             f'<meta property="og:description" content="{H.escape(desc)}"><meta property="og:url" content="{url}">'
             f'<meta name="twitter:card" content="summary_large_image">')
    return ('<!doctype html><html lang="ja"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{H.escape(title)}</title><meta name="description" content="{H.escape(desc)}">'
            f'{VERIFY}{canon}<link rel="stylesheet" href="styles.css">{ADSENSE}{head}'
            '<style>.fk{font-weight:800;color:var(--accent)}.metar{display:flex;flex-wrap:wrap;gap:4px 10px;font-size:.8rem;color:var(--sub);margin:2px 0}'
            '.metar b{color:var(--ink)}.badge{background:var(--chip);color:var(--accent);border-radius:6px;padding:1px 7px;font-size:.72rem;font-weight:700}'
            '.scallout{background:var(--chip);border:1px solid var(--line);border-left:4px solid var(--accent);border-radius:10px;padding:10px 14px;margin:12px 0;font-size:.9rem}.scallout a{font-weight:700;white-space:nowrap}'
            '.sguide{margin:20px 0}.sguide h2{margin-top:1.3em}'
            '.adcard{display:flex;flex-direction:column;align-items:center;justify-content:center;gap:8px;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px;min-height:150px}'
            '.adcard img{max-width:100%;height:auto}'
            '.adbanner-pc{display:flex;flex-direction:column;align-items:center;gap:4px;margin:18px 0}.adbanner-pc img{max-width:100%;height:auto}'
            '@media(max-width:640px){.adbanner-pc{display:none}}'  # 横長帯はPCのみ(スマホはオーバーレイ320×50が出る)
            '.adlabel{align-self:flex-start;color:var(--sub);font-size:.68rem;border:1px solid var(--line);border-radius:4px;padding:0 5px}</style>'
            f'</head><body>{nav()}<main>{body}</main>{foot()}{VC_320_OVERLAY}</body></html>')

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
    body = f"""
<nav class="crumb"><a href="index.html">コスパナビ</a> › <a href="furusato.html">ふるさと納税</a> › {cfg['label']}</nav>
<h1>ふるさと納税 {cfg['label']} コスパランキング<span class="yr">2026</span></h1>
<p class="lead">楽天ふるさと納税の{cfg['label']}を、<b>寄付額あたりの内容量（{cfg['unit_label']}）</b>とレビュー満足度から独自コスパ値でランキング。<b>{len(data)}件</b>を比較。定期便も総量に換算しています。<b>スライダーで「満足度／お得さ」を調整</b>できます。</p>
<div class="scallout">💡 掲載は楽天ふるさと納税の寄付額ですが、<b>寄付額は自治体が決めるため他サイトでも同額</b>です。どのサイトで申し込むのが良いかは <a href="furusato-sites.html">ふるさと納税サイトの選び方（2025年ポイント廃止後）→</a></div>
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
<p class="note">※コスパ値＝満足度（レビューをレビュー数で信頼補正）×お得さ（{cfg['unit_label']}が安いほど高い）の独自指標。内容量は商品名から自動抽出のため、複数重量が選べる返礼品は掲載していません。<a href="furusato.html">ふるさと納税コスパとは</a></p>
<script id="data" type="application/json">{json.dumps(slim, ensure_ascii=False, separators=(",", ":"))}</script>
<script>const UL={json.dumps(cfg['unit_label'], ensure_ascii=False)},SF={json.dumps(cfg['suffix'], ensure_ascii=False)};</script>
<script>{TOOL_JS}</script>
"""
    title = f"ふるさと納税 {cfg['label']}のコスパ最強ランキング2026｜{cfg['unit_label']}で比較"
    desc = cfg["desc"]
    ld = {"@context": "https://schema.org", "@type": "ItemList", "name": title,
          "itemListElement": [{"@type": "ListItem", "position": m["rank"], "name": m["name"]} for m in data[:20]]}
    head = f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>'
    open(os.path.join(SITE, cfg["file"]), "w", encoding="utf-8").write(shell(title, desc, body, cfg["file"], head))
    return len(data)

SITES = [
    ("楽天ふるさと納税", "楽天市場と同じ操作感で使える最大級のサイト。返礼品数が多く、楽天カード・楽天ペイ決済に対応。普段から楽天を使う人はカード決済のポイントを貯めやすい。当サイトのランキングも楽天のデータを利用。"),
    ("さとふる", "返礼品の掲載数が最大級で、初心者にも分かりやすいUI。発送が早い返礼品が多く、PayPay・クレジットカード決済に対応。「とにかく選択肢を広く見たい」人に。"),
    ("ふるさとチョイス", "掲載自治体数No.1クラスで、地方の穴場返礼品まで最も網羅的。Amazon Pay・各種決済に対応。「他に無い返礼品を探したい」網羅性重視の人向け。"),
    ("ふるなび", "家電・電化製品の返礼品に強く、初心者向けの見やすさが特徴。独自の「ふるなびコイン」やキャンペーンあり。家電狙いの人に。"),
    ("au PAY ふるさと納税", "au・Pontaユーザーと相性が良く、Pontaポイントでの決済も可能。auの経済圏を使っている人向け。"),
]

def build_guide():
    site_cards = "".join(f'<div class="gpt"><h3>{H.escape(n)}</h3><p>{H.escape(d)}</p></div>' for n, d in SITES)
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
<nav class="crumb"><a href="index.html">コスパナビ</a> › <a href="furusato.html">ふるさと納税</a> › サイトの選び方</nav>
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
<p class="note">本ページは制度の一般的な解説です。控除・ポイント・キャンペーンの最新条件は各サイト・自治体の公式情報をご確認ください。当サイトのランキングは<a href="furusato.html">ふるさと納税コスパ分析</a>から。</p>
</div>
"""
    title = "ふるさと納税サイトの選び方2026｜ポイント廃止後の比較とお得な方法"
    desc = "2025年10月のポイント付与廃止後、ふるさと納税サイトはどう選ぶ？楽天・さとふる・ふるさとチョイス・ふるなび等を比較し、今もお得にする方法（決済ポイント）を解説。"
    head = f'<script type="application/ld+json">{json.dumps(faq_ld, ensure_ascii=False)}</script>'
    open(os.path.join(SITE, "furusato-sites.html"), "w", encoding="utf-8").write(shell(title, desc, body, "furusato-sites.html", head))

def build_hub(counts):
    # 3列グリッドで偶数行(2,4,6…)の中央=最終位置4,10,16…(pos%6==4)に広告を差し込む。banner循環。
    parts = []
    ci = pos = adn = 0
    while ci < len(CATS):
        if pos % 6 == 4 and IN_GRID_ADS:   # 偶数行(2,4,6…)の中央を広告で埋める(banner循環)
            parts.append(IN_GRID_ADS[adn % len(IN_GRID_ADS)]); adn += 1; pos += 1
            continue
        c = CATS[ci]
        parts.append(f'<a class="hcard" href="{c["file"]}"><div class="hico">{c["icon"]}</div>'
                     f'<div><h3>{c["label"]}<span class="n">{counts[c["slug"]]}件</span></h3><p>{c["desc"]}</p></div></a>')
        ci += 1; pos += 1
    cards = "".join(parts)
    body = f"""
<div class="hero"><h1>ふるさと納税 コスパ分析<span class="yr">2026</span></h1>
<p class="lead">「実質2,000円で本当にお得な返礼品は？」——楽天ふるさと納税の返礼品を、<b>寄付額あたりの内容量（円/kg等）</b>とレビュー満足度から独自コスパ値でランキング。<b>定期便も総量に換算</b>して、量あたり本当にお得な返礼品を選べます。</p></div>
{AD}
<div class="scallout">📢 <b>2025年10月からふるさと納税のポイント付与は廃止されました。</b>今のお得なサイトの選び方は <a href="furusato-sites.html">ふるさと納税サイトの選び方（ポイント廃止後）→</a></div>
<div class="hgrid">{cards}</div>
{VC_468_PC}
<div class="soonbox"><p class="lead">今後追加予定：</p><span class="soon">日用品（洗剤）</span><span class="soon">お菓子・スイーツ</span><span class="soon">卵</span><span class="soon">冷凍食品</span></div>
<h2>ふるさと納税のコスパの考え方</h2>
<p>ふるさと納税は寄付額のうち自己負担2,000円を除いた分が控除されるため、<b>「いかに安く返礼品を得るか」ではなく「同じ寄付額でどれだけ量・質の良い返礼品がもらえるか」</b>がコスパの本質です。当サイトは返礼品の<b>内容量あたりの寄付額（円/kg など）</b>を軸に、レビュー満足度と組み合わせて独自にランキングしています。控除上限額はご自身の年収・家族構成で異なります。詳しくは<a href="about.html">コスパ値とは</a>。</p>
"""
    title = "ふるさと納税コスパ分析2026｜円/kgで選ぶお得な返礼品ランキング"
    desc = "楽天ふるさと納税の返礼品を寄付額あたりの内容量（円/kg等）とレビュー満足度で独自コスパランキング。定期便も総量換算で比較。米など。"
    open(os.path.join(SITE, "furusato.html"), "w", encoding="utf-8").write(shell(title, desc, body, "furusato.html"))

def add_to_sitemap():
    # build_site生成のsitemap.xmlにふるさと納税ページを追記(未登録なら)
    sp = os.path.join(SITE, "sitemap.xml")
    if not os.path.exists(sp):
        return
    xml = open(sp, encoding="utf-8").read()
    add = ""
    for path in ["furusato.html", "furusato-sites.html"] + [c["file"] for c in CATS]:
        loc = f"{SITE_URL}/{path}"
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
    build_hub(counts)
    add_to_sitemap()
    print(f"生成: furusato.html(ハブ) + サイト選び方 + {len(CATS)}カテゴリ  {counts}")
