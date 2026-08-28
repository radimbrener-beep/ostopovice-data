#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sekce Rozpočet (rozpocet.html) — hospodaření obce Ostopovice.
Data z MONITORu Státní pokladny (výkaz FIN 2-12 M), stažená přes API a
uložená v data/rozpocet_ostopovice.json (viz scripts/fetch_rozpocet.py)."""
import sys, json
import portal_common as pc
sys.stdout.reconfigure(encoding="utf-8")

CHARTJS = open("data/vendor/chart.umd.js", encoding="utf-8").read()
D = json.load(open("data/rozpocet_ostopovice.json", encoding="utf-8"))
data_json = json.dumps(D, ensure_ascii=False, separators=(",", ":"))
years = D["years"]
last = years[-1]
LY = last["rok"]
kap = next((x["skut"] for x in D["vydaje_druh"] if "apitál" in x["name"]), 0)
saldo = last["prijmy"]["skut"] - last["vydaje"]["skut"]

def mil(v): return f'{v/1e6:,.1f}'.replace(",", " ").replace(".", ",")

# --- „V kostce": srozumitelné shrnutí posledního uzavřeného roku ---
def _fmt_mil(v):
    return f"{v/1e6:.1f}".replace(".", ",") + " mil. Kč"
FRIENDLY = {"Státní moc, státní správa, územní samospráva a politické strany": "Správa obce a zastupitelstvo",
            "Bydlení, komunální služby a územní rozvoj": "Bydlení, komunální služby a rozvoj obce",
            "Sociální služby a společné činnosti v sociálním zabezpečení a politice zaměstnanosti": "Sociální služby",
            "Vzdělávání a školské služby": "Školství",
            "Ochrana životního prostředí": "Životní prostředí a odpady",
            "Kultura, církve a sdělovací prostředky": "Kultura"}
def _fr(n): return FRIENDLY.get(n, n)
_st = D["struktura"][str(LY)]
_pr, _vy = last["prijmy"]["skut"], last["vydaje"]["skut"]
_dan = next((x["skut"] for x in _st["prijmy_druh"] if x["name"].startswith("Daňov")), 0)
_top = [x for x in _st["vydaje_oblast"] if x["skut"] > 0][:3]
KOSTKA = (f'<section><div class="panel kostka"><h2>V kostce: rok {LY}</h2><p>'
          f'Obec v roce {LY} <b>vybrala {_fmt_mil(_pr)}</b> a <b>utratila {_fmt_mil(_vy)}</b> — '
          + (f'hospodařila tedy s <b>přebytkem {_fmt_mil(saldo)}</b>' if saldo >= 0
             else f'rozdíl <b>{_fmt_mil(-saldo)}</b> pokryla z úspor minulých let a z úvěru')
          + f'. Zhruba <b>{round(_dan/_pr*100)} % příjmů tvoří daně</b> (hlavně podíl na celostátně vybraných daních, který obec dostává podle počtu obyvatel). '
          f'Na <b>investice</b> (stavby, nákupy pozemků a budov) šlo {_fmt_mil(kap)}, tj. {round(kap/_vy*100)} % výdajů. '
          'Nejvíc peněz směřovalo do oblastí: ' + ", ".join(f'{_fr(x["name"]).lower()} ({_fmt_mil(x["skut"])})' for x in _top) + '. '
          'Na dostavbu mateřské a základní školy si obec vzala úvěry u Komerční banky — 105 mil. Kč (schváleno 2024) a 16 mil. Kč (2025), splatné do roku 2039.'
          '</p></div></section>')
KOSTKA_CSS = ".kostka h2{font-size:17px;margin:0 0 8px}.kostka p{margin:0;font-size:14px;line-height:1.65;color:var(--muted)}.kostka b{color:var(--text)}"
SLOVNICEK = """<section id="slovnicek"><details class="panel slov"><summary><b>Slovníček pojmů</b> — co znamenají čísla v rozpočtu</summary><dl>
<dt>Schválený rozpočet</dt><dd>Plán příjmů a výdajů, který zastupitelstvo schválí na začátku roku (obvykle v prosinci předchozího roku).</dd>
<dt>Upravený rozpočet</dt><dd>Plán po všech změnách během roku. Mění se <i>rozpočtovými opatřeními</i> — např. když obec získá dotaci nebo se rozhodne pro novou stavbu.</dd>
<dt>Skutečnost</dt><dd>Kolik peněz obec opravdu vybrala / zaplatila. U uzavřených let k 31. 12.</dd>
<dt>% plnění</dt><dd>Skutečnost ÷ upravený rozpočet. 100 % = vybráno / utraceno přesně podle plánu.</dd>
<dt>Saldo</dt><dd>Příjmy minus výdaje. Kladné = přebytek (obec ušetřila), záporné = schodek (doplatila z úspor minulých let nebo úvěrem).</dd>
<dt>Daňové příjmy</dt><dd>Většinou <i>sdílené daně</i> — obec dostává podíl z celostátně vybrané DPH a daní z příjmů podle počtu obyvatel a dalších kritérií. Vlastní daní obce je daň z nemovitostí.</dd>
<dt>Nedaňové příjmy</dt><dd>Nájemné, poplatky za služby, prodej vody, úroky z vkladů apod.</dd>
<dt>Přijaté transfery</dt><dd>Dotace a příspěvky od státu, kraje, EU nebo jiných obcí.</dd>
<dt>Běžné výdaje</dt><dd>Provoz obce: platy, energie, údržba, příspěvky škole, služby, dotace spolkům.</dd>
<dt>Kapitálové výdaje (investice)</dt><dd>Výdaje na nový majetek: stavby, rekonstrukce, nákup pozemků a budov, stroje.</dd>
<dt>Paragraf / oblast</dt><dd>Na co peníze jdou (školství, doprava, voda…). <i>Položka</i> naopak říká, jakého druhu výdaj je (mzdy, materiál, stavba…).</dd>
</dl></details></section>"""


# --- Sankey „tok peněz": zdroje příjmů → rozpočet obce → oblasti výdajů (po letech) ---
SANKEY = {}
for _y in years:
    _s = D["struktura"].get(str(_y["rok"]))
    if not _s:
        continue
    _src = sorted(((x["name"], x["skut"]) for x in _s["prijmy_druh"] if x["skut"] > 0), key=lambda x: -x[1])
    _d = {}
    for x in _s["vydaje_oblast"]:
        if x["skut"] > 0:
            _d[_fr(x["name"])] = _d.get(_fr(x["name"]), 0) + x["skut"]
    _dst = sorted(_d.items(), key=lambda x: -x[1])
    if len(_dst) > 7:
        _dst = _dst[:7] + [("Ostatní oblasti", sum(v for _, v in _dst[7:]))]
    _p, _v = sum(v for _, v in _src), sum(v for _, v in _dst)
    if _v > _p:
        _src.append(("Z úspor minulých let / úvěru", _v - _p))
    elif _p > _v:
        _dst.append(("Přebytek (do úspor)", _p - _v))
    SANKEY[_y["rok"]] = {"s": _src, "d": _dst}

SANKEY_HTML = """<section id="tok"><div class="sec-h"><h2>Tok peněz</h2><span class="hint">odkud obec peníze má a kam jdou · skutečnost · najeďte na pás pro detail</span></div>
<div class="panel"><div class="ctrls"><span class="lbl">Rok</span><span class="seg" id="skYear"></span></div>
<div class="skwrap"><svg id="sankey" viewBox="0 0 900 440" role="img" aria-label="Sankeyův diagram příjmů a výdajů obce"></svg></div>
<p class="note">Vlevo zdroje příjmů, vpravo oblasti výdajů; šířka pásu odpovídá částce. Když obec utratí víc, než v daném roce vybere, rozdíl kryje z úspor minulých let nebo z úvěru; když méně, přebytek si uloží.</p></div></section>"""

SANKEY_JS = r"""<script>
(function(){
const SK=SANKEY_DATA, YRS=Object.keys(SK).map(Number).sort((a,b)=>a-b);
let yr=YRS[YRS.length-1];
const W=900,H=440,NW=14,GAP=10,PADT=28,PADB=10,MX=(W-NW)/2;
const SRC_C=['#7fb7a4','#9cc8b5','#b7d6c8','#8fb0a0','#c9d9cf'], SAV='#b8bcc6';
const DST_C=['#8fa9cf','#e0a878','#a99bd1','#c9b27f','#86b9c0','#d6a0a0','#a4b98a','#b3a6c9','#b8bcc6'];
const mil=v=>(v/1e6).toLocaleString('cs-CZ',{maximumFractionDigits:1})+' mil. Kč';
const cv=n=>getComputedStyle(document.documentElement).getPropertyValue(n).trim();
function col(list,i,name,base){return /úspor|Přebytek|úvěr/.test(name)?SAV:base[i%base.length];}
function layout(items,x,total,scale){
  let y=PADT; const out=[];
  const free=H-PADT-PADB-GAP*(items.length-1);
  items.forEach((it,i)=>{const h=Math.max(2,it[1]*scale);out.push({n:it[0],v:it[1],x,y,h});y+=h+GAP;});
  const used=y-GAP-PADT, off=(H-PADT-PADB-used)/2; out.forEach(o=>o.y+=off);
  return out;}
function band(x0,y0,h0,x1,y1,h1){const c=(x0+x1)/2;
  return `M${x0},${y0} C${c},${y0} ${c},${y1} ${x1},${y1} L${x1},${y1+h1} C${c},${y1+h1} ${c},${y0+h0} ${x0},${y0+h0} Z`;}
function draw(){
  const d=SK[yr], tot=d.s.reduce((a,x)=>a+x[1],0);
  const maxN=Math.max(d.s.length,d.d.length), scale=(H-PADT-PADB-GAP*(maxN-1))/tot;
  const L=layout(d.s,0,tot,scale), R=layout(d.d,W-NW,tot,scale);
  const mh=tot*scale, my=(H-PADT-PADB-mh)/2+PADT;
  const txt=cv('--text'), mut=cv('--muted');
  let g='';
  // pásy zdroje → střed
  let cy=my; L.forEach((n,i)=>{const c=col(d.s,i,n.n,SRC_C);
    g+=`<path d="${band(n.x+NW,n.y,n.h,MX,cy,n.h)}" fill="${c}" fill-opacity=".45"><title>${n.n}: ${mil(n.v)} (${Math.round(n.v/tot*100)} %)</title></path>`;cy+=n.h;});
  cy=my; R.forEach((n,i)=>{const c=col(d.d,i,n.n,DST_C);
    g+=`<path d="${band(MX+NW,cy,n.h,n.x,n.y,n.h)}" fill="${c}" fill-opacity=".45"><title>${n.n}: ${mil(n.v)} (${Math.round(n.v/tot*100)} %)</title></path>`;cy+=n.h;});
  // uzly
  L.forEach((n,i)=>{g+=`<rect x="${n.x}" y="${n.y}" width="${NW}" height="${n.h}" rx="3" fill="${col(d.s,i,n.n,SRC_C)}"/>`+
    `<text x="${n.x+NW+8}" y="${n.y+n.h/2}" dy=".35em" font-size="13" fill="${txt}">${n.n} <tspan fill="${mut}">${mil(n.v)}</tspan></text>`;});
  R.forEach((n,i)=>{g+=`<rect x="${n.x}" y="${n.y}" width="${NW}" height="${n.h}" rx="3" fill="${col(d.d,i,n.n,DST_C)}"/>`+
    `<text x="${n.x-8}" y="${n.y+n.h/2}" dy=".35em" text-anchor="end" font-size="13" fill="${txt}">${n.n} <tspan fill="${mut}">${mil(n.v)}</tspan></text>`;});
  g+=`<rect x="${MX}" y="${my}" width="${NW}" height="${mh}" rx="3" fill="${cv('--accent')}"/>`+
     `<text x="${MX+NW/2}" y="${my-9}" text-anchor="middle" font-size="13" font-weight="650" fill="${txt}">Rozpočet obce ${yr} · ${mil(tot)}</text>`;
  document.getElementById('sankey').innerHTML=g;
}
const seg=document.getElementById('skYear');
seg.innerHTML=YRS.map(y=>`<button data-y="${y}"${y===yr?' class="on"':''}>${y}</button>`).join('');
seg.querySelectorAll('button').forEach(b=>b.onclick=()=>{yr=+b.dataset.y;seg.querySelectorAll('button').forEach(x=>x.classList.toggle('on',x===b));draw();});
draw();
new MutationObserver(draw).observe(document.documentElement,{attributes:true,attributeFilter:['data-theme']});
})();
</script>"""
SANKEY_CSS = """.skwrap{overflow-x:auto;margin-top:8px}
#sankey{width:100%;min-width:680px;height:auto;display:block}
#sankey path{transition:fill-opacity .15s}#sankey path:hover{fill-opacity:.75}
#skYear{flex-wrap:wrap}"""


body = f'''<header class="hero">
  <h1>Rozpočet obce <span style="font-size:17px;font-weight:500;color:var(--muted)">· jak obec hospodaří</span></h1>
  <p>Příjmy, výdaje a saldo obce Ostopovice v čase a jejich struktura — podle výkazu FIN 2-12 M ze systému MONITOR Státní pokladny ({years[0]["rok"]}–{LY}).</p>
  <div class="chips"><span class="chip">obec Ostopovice · IČO {D["ic"]}</span><span class="chip">{years[0]["rok"]}–{LY}</span><span class="chip">zdroj: MONITOR Státní pokladny</span></div>
</header>

<div class="cards" id="kpis"></div>

{KOSTKA}

<section>
  <div class="sec-h"><h2>Vývoj příjmů, výdajů a salda</h2><span class="hint">{years[0]["rok"]}–{LY} · roční stav</span></div>
  <div class="panel">
    <div class="ctrls"><span class="lbl">Ukazatel</span>
      <span class="seg" id="mSeg"><button class="on" data-m="skut">Skutečnost</button><button data-m="schv">Schválený</button><button data-m="uprav">Upravený</button></span></div>
    <div class="legend"><span><i class="sw" style="background:var(--prijmy)"></i>Příjmy</span><span><i class="sw" style="background:var(--vydaje)"></i>Výdaje</span><span><i class="sw" style="background:var(--pos)"></i>Saldo +</span><span><i class="sw" style="background:var(--neg)"></i>Saldo −</span></div>
    <div class="chartbox"><canvas id="trend"></canvas></div>
    <p class="note">Rok {LY} je mimořádný — <b>dostavba základní a mateřské školy</b> vyhnala kapitálové výdaje na {mil(kap)} mil. Kč a výdaje celkem na {mil(last["vydaje"]["skut"])} mil. Kč (schodek {mil(-saldo)} mil. Kč kryla obec z úspor a úvěru).</p>
  </div>
</section>

{SANKEY_HTML}

<section>
  <div class="grid2">
    <div class="panel">
      <div class="sec-h" style="margin:0 0 8px"><h2 style="font-size:16px">Struktura příjmů {LY}</h2></div>
      <div class="donutwrap"><div class="chartbox sm" style="max-width:320px"><canvas id="prijmy"></canvas></div>
        <div class="donut-center"><div class="t">příjmy {LY}</div><div class="v">{mil(last["prijmy"]["skut"])}</div></div></div>
      <div class="legend" id="prijmyLeg" style="justify-content:center"></div>
    </div>
    <div class="panel">
      <div class="sec-h" style="margin:0 0 8px"><h2 style="font-size:16px">Kam tečou výdaje {LY}</h2><span class="hint">podle oblasti</span></div>
      <div class="chartbox sm"><canvas id="vydaje"></canvas></div>
    </div>
  </div>
</section>

{SLOVNICEK}

<section>
  <div class="panel">
    <p class="note" style="margin:0;font-size:12.5px">Zdroj: <b>{D["zdroj"]}</b>, IČO {D["ic"]} — data stažená z API MONITORu (<a href="https://monitor.statnipokladna.gov.cz" target="_blank" rel="noopener" style="color:var(--accent)">monitor.statnipokladna.gov.cz</a>). „Skutečnost" = skutečně inkasované příjmy a proplacené výdaje k 31.&nbsp;12.; „Schválený" a „Upravený" jsou verze rozpočtu. Hodnoty v Kč.</p>
  </div>
</section>'''

scripts = '<script>' + CHARTJS + '''</script>
<script>
const D=DATA_JSON, Y=D.years;
const nf=new Intl.NumberFormat('cs-CZ');
const charts={};
const PAL=['--c0','--c1','--c2','--c3','--c4','--c5','--c6','--c7','--c8','--c9'];
function axis(){return {grid:{color:isDark()?'#1f2a40':'#eef2f7'},ticks:{color:cssv('--muted')}};}
function mk(id,cfg){if(charts[id])charts[id].destroy();charts[id]=new Chart(document.getElementById(id),cfg);}
const M=v=>(v/1e6);
const milTxt=v=>M(v).toLocaleString('cs-CZ',{maximumFractionDigits:1})+' mil. Kč';

function kpis(){
  const L=Y[Y.length-1], P=Y[Y.length-2];
  const s=L.prijmy.skut-L.vydaje.skut;
  const kap=D.vydaje_druh.find(x=>x.name.indexOf('apitál')>=0);
  const dd=(a,b)=>b?((a-b)/b*100):0;
  const C=[
    ['Příjmy '+L.rok, milTxt(L.prijmy.skut), (dd(L.prijmy.skut,P.prijmy.skut)>=0?'▲ ':'▼ ')+Math.abs(dd(L.prijmy.skut,P.prijmy.skut)).toFixed(0)+' % r/r','var(--prijmy)'],
    ['Výdaje '+L.rok, milTxt(L.vydaje.skut), (dd(L.vydaje.skut,P.vydaje.skut)>=0?'▲ ':'▼ ')+Math.abs(dd(L.vydaje.skut,P.vydaje.skut)).toFixed(0)+' % r/r','var(--vydaje)'],
    ['Saldo '+L.rok, (s>=0?'+':'')+milTxt(s), s>=0?'přebytek':'schodek (dostavba školy)', s>=0?'var(--pos)':'var(--neg)'],
    ['Kapitálové výdaje '+L.rok, milTxt(kap?kap.skut:0), 'investice (z toho škola)','#a855f7'],
  ];
  document.getElementById('kpis').innerHTML=C.map(c=>`<div class="kpi" style="--bar:${c[3]}"><div class="lab">${c[0]}</div><div class="val" style="font-size:22px">${c[1]}</div><div class="delta" style="color:var(--muted)">${c[2]}</div></div>`).join('');
}

let metric='skut';
function trend(){
  const labels=Y.map(y=>y.rok);
  const pr=Y.map(y=>M(y.prijmy[metric])), vy=Y.map(y=>M(y.vydaje[metric]));
  const sa=pr.map((p,i)=>p-vy[i]);
  mk('trend',{data:{labels,datasets:[
    {type:'bar',label:'Saldo',data:sa,order:3,borderRadius:4,backgroundColor:sa.map(v=>v>=0?cssv('--pos'):cssv('--neg')),barPercentage:.6},
    {type:'line',label:'Příjmy',data:pr,order:1,borderColor:cssv('--prijmy'),backgroundColor:'transparent',borderWidth:2.6,tension:.3,pointRadius:2,pointHoverRadius:5},
    {type:'line',label:'Výdaje',data:vy,order:2,borderColor:cssv('--vydaje'),backgroundColor:'transparent',borderWidth:2.6,borderDash:[7,4],tension:.3,pointRadius:2,pointHoverRadius:5}
  ]},options:{responsive:true,maintainAspectRatio:false,animation:{duration:600},interaction:{mode:'index',intersect:false},
    plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>c.dataset.label+': '+c.parsed.y.toLocaleString('cs-CZ',{maximumFractionDigits:1})+' mil. Kč'}}},
    scales:{x:Object.assign(axis(),{ticks:{color:cssv('--muted'),maxRotation:40}}),y:Object.assign(axis(),{ticks:{color:cssv('--muted'),callback:v=>v+' mil.'}})}}});
}
function prijmyChart(){
  const a=D.prijmy_druh.slice().sort((x,y)=>y.skut-x.skut);
  mk('prijmy',{type:'doughnut',data:{labels:a.map(x=>x.name),datasets:[{data:a.map(x=>x.skut),backgroundColor:a.map((x,i)=>cssv(PAL[i%PAL.length])),borderColor:cssv('--surface'),borderWidth:2,hoverOffset:6}]},
    options:{responsive:true,maintainAspectRatio:false,cutout:'62%',animation:{duration:600},
      plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>c.label+': '+milTxt(c.parsed)}}}}});
  const tot=a.reduce((s,x)=>s+x.skut,0);
  document.getElementById('prijmyLeg').innerHTML=a.map((x,i)=>`<span><i class="sw" style="background:${cssv(PAL[i%PAL.length])}"></i>${x.name} · ${Math.round(x.skut/tot*100)} %</span>`).join('');
}
function vydajeChart(){
  let a=D.vydaje_oblast.slice().sort((x,y)=>y.skut-x.skut);
  const TOP=8; if(a.length>TOP){const rest=a.slice(TOP).reduce((s,x)=>s+x.skut,0);a=a.slice(0,TOP);if(rest>0)a.push({name:'ostatní oblasti',skut:rest});}
  mk('vydaje',{type:'bar',data:{labels:a.map(x=>x.name.length>34?x.name.slice(0,32)+'…':x.name),datasets:[{label:'Výdaje',data:a.map(x=>M(x.skut)),backgroundColor:a.map((x,i)=>cssv(PAL[i%PAL.length])),borderRadius:5}]},
    options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,animation:{duration:600},
      plugins:{legend:{display:false},tooltip:{callbacks:{title:items=>a[items[0].dataIndex].name,label:c=>milTxt(a[c.dataIndex].skut)}}},
      scales:{x:Object.assign(axis(),{ticks:{color:cssv('--muted'),callback:v=>v+' mil.'}}),y:Object.assign(axis(),{ticks:{color:cssv('--muted'),font:{size:11}}})}}});
}
function render(){kpis();trend();prijmyChart();vydajeChart();}
render(); bindTheme(render);
document.querySelectorAll('#mSeg button').forEach(b=>b.onclick=()=>{document.querySelectorAll('#mSeg button').forEach(x=>x.classList.remove('on'));b.classList.add('on');metric=b.dataset.m;trend();});
window.addEventListener('load',()=>{Object.values(charts).forEach(c=>{try{c.resize();}catch(e){}});});
</script>'''.replace("DATA_JSON", data_json)

open("rozpocet.html", "w", encoding="utf-8").write(
    pc.page("Rozpočet", "Rozpočet obce — Jak žijí Ostopovice", body,
            head_scripts="<style>" + SANKEY_CSS + KOSTKA_CSS + "</style>",
            body_scripts=scripts + SANKEY_JS.replace("SANKEY_DATA", json.dumps(SANKEY, ensure_ascii=False))))
print(f"HOTOVO -> rozpocet.html ({years[0]['rok']}-{LY}, {len(years)} let, výdaje {LY} {mil(last['vydaje']['skut'])} mil.)")
