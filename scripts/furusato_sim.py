# ふるさと納税 控除上限シミュレーター + 年内発送フラグ（build_furusatoから利用）。
# 純JS計算(API不要)。給与収入+家族構成→控除上限の目安→還元率ランキングへ誘導/連動。
# ※詳細版タブは2026-09-28に一度追加したがユーザー判断で簡易版のみに戻した。

NENNAI_KW = ["年内発送", "年内お届け", "年内配送", "年内に発送", "即納", "スピード発送", "最短", "すぐ発送",
             "即日発送", "翌日発送", "12月発送", "年内", "在庫あり"]


def nennai_flag(name):
    return any(k in name for k in NENNAI_KW)


SIM_CSS = (
    "<style>.simbox{background:linear-gradient(135deg,var(--chip),var(--card));border:1px solid var(--line);"
    "border-radius:16px;padding:16px 18px;margin:14px 0}.simbox h2{margin:.2em 0}"
    ".simlead{color:var(--sub);font-size:.9rem;margin:.2em 0 .8em}"
    ".simgrid{display:grid;grid-template-columns:1fr 1fr;gap:10px 14px}@media(max-width:560px){.simgrid{grid-template-columns:1fr}}"
    ".simgrid label{font-size:.82rem;font-weight:700;color:var(--ink);display:flex;flex-direction:column;gap:4px}"
    ".simgrid select,.simgrid input[type=range]{width:100%}.simrow{display:flex;align-items:center;gap:8px}"
    ".simrow span{white-space:nowrap;font-size:.9rem}"
    ".simout{display:flex;align-items:baseline;justify-content:center;gap:10px;margin:14px 0 6px;flex-wrap:wrap}"
    ".simlabel{color:var(--sub);font-size:.85rem}.simval{color:var(--accent);font-size:2.1rem;font-weight:800;line-height:1}"
    ".simcta{display:block;text-align:center;margin:8px 0 4px}.simbox .note{font-size:.72rem;color:var(--sub);margin:.5em 0 0}</style>"
)

SIM_JS = r"""
(function(){
  var inc=document.getElementById('sinc'); if(!inc)return;
  var q=function(id){return document.getElementById(id);};
  function calc(){
    var income=(+inc.value)*10000; q('sincv').textContent=(+inc.value).toLocaleString();
    var spouse=q('sspouse').value==='1', kHigh=+q('skhigh').value, kUniv=+q('skuniv').value, ded;
    if(income<=1625000)ded=550000;else if(income<=1800000)ded=income*0.4-100000;
    else if(income<=3600000)ded=income*0.3+80000;else if(income<=6600000)ded=income*0.2+440000;
    else if(income<=8500000)ded=income*0.1+1100000;else ded=1950000;
    var kyuyo=income-ded, shaho=income*0.15;
    var fIT=(spouse?380000:0)+kHigh*380000+kUniv*630000, fRT=(spouse?330000:0)+kHigh*330000+kUniv*450000;
    var tIT=Math.max(0,kyuyo-480000-shaho-fIT), tRT=Math.max(0,kyuyo-430000-shaho-fRT);
    var r=function(t){return t<=1950000?0.05:t<=3300000?0.10:t<=6950000?0.20:t<=9000000?0.23:t<=18000000?0.33:t<=40000000?0.40:0.45;};
    var limit=(tRT*0.10)*0.2/(0.9-r(tIT)*1.021)+2000;
    limit=Math.max(0,Math.floor(limit/1000)*1000);
    q('simval').textContent='¥'+limit.toLocaleString();
    var cta=q('simcta'); if(cta)cta.href='/furusato-kanpu?budget='+limit;
    if(window.__kanpuSetBudget)window.__kanpuSetBudget(limit);
    return limit;
  }
  ['sinc','sspouse','skhigh','skuniv'].forEach(function(id){var e=q(id); if(e)e.addEventListener('input',calc);});
  calc();
})();
"""


def _kopt():
    return "".join('<option value="%d">%d人</option>' % (i, i) for i in range(4))


def simulator_html():
    return (
        '<section class="simbox">'
        '<h2>💰 控除上限シミュレーター</h2>'
        '<p class="simlead">年収と家族構成を選ぶと、<b>実質2,000円で寄付できる上限額の目安</b>が分かります。そのままお得な返礼品も探せます。</p>'
        '<div class="simgrid">'
        '<label>年収（給与収入）<div class="simrow"><input type="range" id="sinc" min="150" max="2000" step="10" value="500"><span><b id="sincv">500</b>万円</span></div></label>'
        '<label>配偶者控除<select id="sspouse"><option value="0">なし（独身・共働き）</option><option value="1">あり（配偶者を扶養）</option></select></label>'
        '<label>高校生の子（16〜18歳）<select id="skhigh">' + _kopt() + '</select></label>'
        '<label>大学生の子（19〜22歳）<select id="skuniv">' + _kopt() + '</select></label>'
        '</div>'
        '<div class="simout"><span class="simlabel">控除上限額の目安</span><span class="simval" id="simval">—</span></div>'
        '<a class="buy simcta" id="simcta" href="/furusato-kanpu">この上限で還元率の高い返礼品を見る →</a>'
        '<p class="note">※給与収入のみ・社会保険料を概算（収入の約15%）で計算した目安です。医療費控除・住宅ローン控除などがある場合は上限が変わります。正確な額は各自治体・専門情報でご確認ください。</p>'
        '</section><script>' + SIM_JS + '</script>'
    )
