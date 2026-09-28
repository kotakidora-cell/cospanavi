# ふるさと納税 控除上限シミュレーター + 年内発送フラグ（build_furusatoから利用）。
# 純JS計算(API不要)。簡易版(年収から概算)と詳細版(源泉徴収票の実額入力)をタブ切替。
# 給与収入/実額 + 家族構成 → 控除上限の目安 → 還元率ランキングへ誘導/連動(?budget= or window.__kanpuSetBudget)。

NENNAI_KW = ["年内発送", "年内お届け", "年内配送", "年内に発送", "即納", "スピード発送", "最短", "すぐ発送",
             "即日発送", "翌日発送", "12月発送", "年内", "在庫あり"]


def nennai_flag(name):
    return any(k in name for k in NENNAI_KW)


SIM_CSS = (
    "<style>.simbox{background:linear-gradient(135deg,var(--chip),var(--card));border:1px solid var(--line);"
    "border-radius:16px;padding:16px 18px;margin:14px 0}.simbox h2{margin:.2em 0}"
    ".simlead{color:var(--sub);font-size:.9rem;margin:.2em 0 .6em}"
    ".simtabs{display:flex;gap:6px;margin:6px 0 10px}.simtab{flex:1;border:1px solid var(--line);background:var(--card);"
    "color:var(--sub);border-radius:10px;padding:7px 10px;font-weight:700;font-size:.85rem;cursor:pointer}"
    ".simtab.on{background:var(--accent);color:#fff;border-color:var(--accent)}"
    ".simgrid{display:grid;grid-template-columns:1fr 1fr;gap:10px 14px}@media(max-width:560px){.simgrid{grid-template-columns:1fr}}"
    ".simgrid label{font-size:.82rem;font-weight:700;color:var(--ink);display:flex;flex-direction:column;gap:4px}"
    ".simgrid label.wide{grid-column:1 / -1}"
    ".simgrid select,.simgrid input{width:100%}.simrow{display:flex;align-items:center;gap:8px}.simrow span{white-space:nowrap;font-size:.9rem}"
    ".simhint{font-size:.72rem;color:var(--sub);font-weight:400}"
    ".simout{display:flex;align-items:baseline;justify-content:center;gap:10px;margin:14px 0 6px;flex-wrap:wrap}"
    ".simlabel{color:var(--sub);font-size:.85rem}.simval{color:var(--accent);font-size:2.1rem;font-weight:800;line-height:1}"
    ".simcta{display:block;text-align:center;margin:8px 0 4px}.simbox .note{font-size:.72rem;color:var(--sub);margin:.5em 0 0}</style>"
)

SIM_JS = r"""
(function(){
  var box=document.querySelector('.simbox'); if(!box)return;
  var q=function(id){return document.getElementById(id);};
  function irate(t){return t<=1950000?0.05:t<=3300000?0.10:t<=6950000?0.20:t<=9000000?0.23:t<=18000000?0.33:t<=40000000?0.40:0.45;}
  function limitFrom(tIT,tRT){var lim=(tRT*0.10)*0.2/(0.9-irate(tIT)*1.021)+2000;return Math.max(0,Math.floor(lim/1000)*1000);}
  var mode='easy';
  function calc(){
    var tIT,tRT;
    if(mode==='easy'){
      var income=(+q('sinc').value)*10000; q('sincv').textContent=(+q('sinc').value).toLocaleString();
      var sp=q('sspouse').value==='1', kh=+q('skhigh').value, ku=+q('skuniv').value, ded;
      if(income<=1625000)ded=550000;else if(income<=1800000)ded=income*0.4-100000;
      else if(income<=3600000)ded=income*0.3+80000;else if(income<=6600000)ded=income*0.2+440000;
      else if(income<=8500000)ded=income*0.1+1100000;else ded=1950000;
      var kyuyo=income-ded, shaho=income*0.15;
      var fIT=(sp?380000:0)+kh*380000+ku*630000, fRT=(sp?330000:0)+kh*330000+ku*450000;
      tIT=Math.max(0,kyuyo-480000-shaho-fIT); tRT=Math.max(0,kyuyo-430000-shaho-fRT);
    }else{
      var A=(+q('dA').value)*10000, S=(+q('dS').value)*10000, other=(+q('dother').value||0)*10000;
      var sp2=q('dspouse').value==='1', kh2=+q('dkhigh').value, ku2=+q('dkuniv').value;
      var gIT=(sp2?380000:0)+kh2*380000+ku2*630000, gRT=(sp2?330000:0)+kh2*330000+ku2*450000;
      tIT=Math.max(0,A-480000-S-other-gIT); tRT=Math.max(0,A-430000-S-other-gRT);
      if(!A){q('simval').textContent='—';return;}
    }
    var limit=limitFrom(tIT,tRT);
    q('simval').textContent='¥'+limit.toLocaleString();
    var cta=q('simcta'); if(cta)cta.href='/furusato-kanpu?budget='+limit;
    if(window.__kanpuSetBudget)window.__kanpuSetBudget(limit);
    return limit;
  }
  document.querySelectorAll('.simtab').forEach(function(b){b.addEventListener('click',function(){
    mode=b.dataset.mode;
    document.querySelectorAll('.simtab').forEach(function(x){x.classList.toggle('on',x.dataset.mode===mode);});
    q('simpane-easy').hidden=(mode!=='easy'); q('simpane-detail').hidden=(mode!=='detail');
    q('simnote-easy').hidden=(mode!=='easy'); q('simnote-detail').hidden=(mode!=='detail');
    calc();
  });});
  ['sinc','sspouse','skhigh','skuniv','dA','dS','dother','dspouse','dkhigh','dkuniv'].forEach(function(id){
    var e=q(id); if(e)e.addEventListener('input',calc);});
  calc();
})();
"""


def _kopt():
    return "".join('<option value="%d">%d人</option>' % (i, i) for i in range(4))


def simulator_html():
    return (
        '<section class="simbox">'
        '<h2>💰 控除上限シミュレーター</h2>'
        '<p class="simlead">実質2,000円で寄付できる<b>控除上限額の目安</b>を計算します。かんたん試算と、源泉徴収票で正確に出す詳細版が選べます。</p>'
        '<div class="simtabs">'
        '<button type="button" class="simtab on" data-mode="easy">かんたん（年収から）</button>'
        '<button type="button" class="simtab" data-mode="detail">詳細（源泉徴収票から）</button>'
        '</div>'
        # --- 簡易版 ---
        '<div class="simgrid" id="simpane-easy">'
        '<label>年収（給与収入）<div class="simrow"><input type="range" id="sinc" min="150" max="2000" step="10" value="500"><span><b id="sincv">500</b>万円</span></div></label>'
        '<label>配偶者控除<select id="sspouse"><option value="0">なし（独身・共働き）</option><option value="1">あり（配偶者を扶養）</option></select></label>'
        '<label>高校生の子（16〜18歳）<select id="skhigh">' + _kopt() + '</select></label>'
        '<label>大学生の子（19〜22歳）<select id="skuniv">' + _kopt() + '</select></label>'
        '</div>'
        # --- 詳細版 ---
        '<div class="simgrid" id="simpane-detail" hidden>'
        '<label class="wide">給与所得控除後の金額 <span class="simhint">源泉徴収票の「給与所得控除後の金額」</span>'
        '<div class="simrow"><input type="number" id="dA" min="0" step="1" placeholder="例: 356" inputmode="numeric"><span>万円</span></div></label>'
        '<label>社会保険料等の金額 <span class="simhint">源泉徴収票の同名の欄</span>'
        '<div class="simrow"><input type="number" id="dS" min="0" step="1" placeholder="例: 75" inputmode="numeric"><span>万円</span></div></label>'
        '<label>その他の所得控除（任意）<span class="simhint">生命保険料控除・iDeCo等の合計</span>'
        '<div class="simrow"><input type="number" id="dother" min="0" step="1" placeholder="0" inputmode="numeric"><span>万円</span></div></label>'
        '<label>配偶者控除<select id="dspouse"><option value="0">なし（独身・共働き）</option><option value="1">あり（配偶者を扶養）</option></select></label>'
        '<label>高校生の子（16〜18歳）<select id="dkhigh">' + _kopt() + '</select></label>'
        '<label>大学生の子（19〜22歳）<select id="dkuniv">' + _kopt() + '</select></label>'
        '</div>'
        '<div class="simout"><span class="simlabel">控除上限額の目安</span><span class="simval" id="simval">—</span></div>'
        '<a class="buy simcta" id="simcta" href="/furusato-kanpu">この上限で還元率の高い返礼品を見る →</a>'
        '<p class="note" id="simnote-easy">※給与収入のみ・社会保険料を概算（収入の約15%）で計算した目安です。医療費控除・住宅ローン控除などがある場合は上限が変わります。より正確には「詳細（源泉徴収票から）」をご利用ください。</p>'
        '<p class="note" id="simnote-detail" hidden>※源泉徴収票の実額で計算するため精度が上がります。住宅ローン控除（税額控除）がある場合は上限がさらに下がることがあります。最終的な額は各自治体・専門情報でご確認ください。</p>'
        '</section><script>' + SIM_JS + '</script>'
    )
