# ふるさと納税コスパ分析ページを生成。ランディング(furusato.html)＋カテゴリ(furusato-<slug>.html)。
# 通常商品とロジックが違う(寄付額あたりの内容量=お得さ)ため専用ビルダー。styles.cssは共用。
import json, os, sys, html as H, datetime

sys.stdout.reconfigure(encoding="utf-8")
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data")
SITE = os.path.join(BASE, "site")
SITE_URL = "https://cospa-navi.com"
UPDATED = datetime.date.today().isoformat()
ADSENSE = '<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-8706760047070867" crossorigin="anonymous"></script>'
VERIFY = '<meta name="google-site-verification" content="9Lq7hmAO3CeIlcT6nM2tB2_AksHlZsugoZ_VIeeY5Dc">'
AD = '<div class="ad">広告スペース（Google AdSense）</div>'

CATS = [
    {"slug": "rice", "file": "furusato-rice.html", "label": "米", "unit_label": "円/kg", "amount_label": "総重量",
     "amount_key": "kg", "amount_suffix": "kg",
     "desc": "楽天ふるさと納税の米を、寄付額あたりの内容量（円/kg）とレビュー満足度でコスパランキング。定期便もkg換算で比較。"},
]

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
            '.metar b{color:var(--ink)}.badge{background:var(--chip);color:var(--accent);border-radius:6px;padding:1px 7px;font-size:.72rem;font-weight:700}</style>'
            f'</head><body>{nav()}<main>{body}</main>{foot()}</body></html>')

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
   '<div class="cbody"><div class="ctop"><span class="crank">#'+(i+1)+'</span><span class="badge">'+x.unit.toLocaleString()+'円/kg</span></div>'+
   '<a class="cname" href="'+x.aff+'" target="_blank" rel="nofollow sponsored noopener">'+x.name+'</a>'+
   '<div class="cstars">'+stars(x.review)+' <span class="muted">'+x.review.toFixed(2)+'（'+x.rc.toLocaleString()+'件）</span></div>'+
   '<div class="metar"><span>寄付 <b>'+yen(x.price)+'</b></span><span>総量 <b>'+x.kg+'kg</b></span><span>単価 <b class="fk">'+x.unit.toLocaleString()+'円/kg</b></span></div>'+
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
    slim = [{"id": m["id"], "name": m["name"], "price": m["price"], "kg": m["kg"], "unit": m["unit"],
             "review": m["review"], "rc": m["reviewCount"], "sat": m["sat"], "toku": m["toku"],
             "img": m["image"], "aff": m["affiliate"]} for m in data]
    maxp = ((max(m["price"] for m in data) + 999) // 1000) * 1000
    body = f"""
<nav class="crumb"><a href="index.html">コスパナビ</a> › <a href="furusato.html">ふるさと納税</a> › {cfg['label']}</nav>
<h1>ふるさと納税 {cfg['label']} コスパランキング<span class="yr">2026</span></h1>
<p class="lead">楽天ふるさと納税の{cfg['label']}を、<b>寄付額あたりの内容量（{cfg['unit_label']}）</b>とレビュー満足度から独自コスパ値でランキング。<b>{len(data)}件</b>を比較。定期便も総量に換算しています。<b>スライダーで「満足度／お得さ」を調整</b>できます。</p>
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
<script>{TOOL_JS}</script>
"""
    title = f"ふるさと納税 {cfg['label']}のコスパ最強ランキング2026｜{cfg['unit_label']}で比較"
    desc = cfg["desc"]
    ld = {"@context": "https://schema.org", "@type": "ItemList", "name": title,
          "itemListElement": [{"@type": "ListItem", "position": m["rank"], "name": m["name"]} for m in data[:20]]}
    head = f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>'
    open(os.path.join(SITE, cfg["file"]), "w", encoding="utf-8").write(shell(title, desc, body, cfg["file"], head))
    return len(data)

def build_hub(counts):
    cards = ""
    for c in CATS:
        cards += (f'<a class="hcard" href="{c["file"]}"><div class="hico">🍚</div>'
                  f'<div><h3>{c["label"]}<span class="n">{counts[c["slug"]]}件</span></h3><p>{c["desc"]}</p></div></a>')
    body = f"""
<div class="hero"><h1>ふるさと納税 コスパ分析<span class="yr">2026</span></h1>
<p class="lead">「実質2,000円で本当にお得な返礼品は？」——楽天ふるさと納税の返礼品を、<b>寄付額あたりの内容量（円/kg等）</b>とレビュー満足度から独自コスパ値でランキング。<b>定期便も総量に換算</b>して、量あたり本当にお得な返礼品を選べます。</p></div>
{AD}
<div class="hgrid">{cards}</div>
<div class="soonbox"><p class="lead">今後追加予定：</p><span class="soon">牛肉・豚肉</span><span class="soon">海鮮</span><span class="soon">果物</span><span class="soon">ビール</span><span class="soon">トイレットペーパー</span></div>
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
    for path in ["furusato.html"] + [c["file"] for c in CATS]:
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
    build_hub(counts)
    add_to_sitemap()
    print(f"生成: furusato.html(ハブ) + {len(CATS)}カテゴリ  {counts}")
