#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sekce Zakázky (zakazky.html) — veřejné zakázky obce z profilu zadavatele
(vhodne-uverejneni.cz). Předpokládané hodnoty z detailů zakázek."""
import sys, json, re
import portal_common as pc
sys.stdout.reconfigure(encoding="utf-8")

CHARTJS = open("data/vendor/chart.umd.js", encoding="utf-8").read()
rows = json.load(open("data/zakazky.json", encoding="utf-8"))

def rok(d):
    m = re.search(r"(\d{4})", d or "")
    return int(m.group(1)) if m else None
def druh(n):
    n = n.lower()
    if re.search(r"úvěr", n): return "úvěr"
    if re.search(r"svoz|tds|technick\w* dozor|služ|projektov\w* dokumentac|zpracování|zajištění", n): return "služba"
    if re.search(r"dodávk|pořízení|mobiliář|vozidl|traktor|technologi", n): return "dodávka"
    return "stavba"
for x in rows:
    x["rok"] = rok(x["datum"])
    x["druh"] = druh(x["nazev"])

# úvěry jsou v profilu jako zakázky (výběr banky), ale nejsou výdaj → do objemů nepočítat
withval = [x for x in rows if x.get("hodnota") and x["druh"] != "úvěr"]
total = sum(x["hodnota"] for x in withval)
biggest = max(withval, key=lambda x: x["hodnota"]) if withval else None
rows.sort(key=lambda x: (x.get("hodnota") or 0), reverse=True)

DATA = {"rows": rows}
data_json = json.dumps(DATA, ensure_ascii=False, separators=(",", ":"))

body = f'''<header class="hero">
  <h1>Veřejné zakázky obce</h1>
  <p>Zakázky obce Ostopovice z profilu zadavatele — co obec poptává a staví, a za kolik. U každé zakázky je předpokládaná hodnota, kterou obec uvedla při vyhlášení.</p>
  <div class="chips"><span class="chip">obec Ostopovice · IČO 00282294</span><span class="chip">{len(rows)} zakázek</span><span class="chip">zdroj: vhodne-uverejneni.cz</span></div>
</header>

<div class="cards" id="kpis"></div>

<section>
  <div class="sec-h"><h2>Největší zakázky</h2><span class="hint">podle předpokládané hodnoty</span></div>
  <div class="panel"><div class="chartbox"><canvas id="topChart"></canvas></div></div>
</section>

<section>
  <div class="sec-h"><h2>Objem zakázek podle roku</h2><span class="hint">součet předpokládaných hodnot</span></div>
  <div class="panel"><div class="chartbox sm"><canvas id="yearChart"></canvas></div></div>
</section>

<section>
  <div class="sec-h"><h2>Všechny zakázky</h2><span class="hint">řaď a hledej · proklik na detail</span></div>
  <div class="panel">
    <div class="tbar" style="display:flex;gap:12px;flex-wrap:wrap;align-items:center;margin-bottom:12px">
      <input type="text" id="q" placeholder="hledat zakázku…" style="flex:1;min-width:200px">
      <span><span class="lbl">Řadit</span>
        <select id="sort"><option value="val">Nejdražší</option><option value="new">Nejnovější</option></select></span>
      <button class="dlbtn" id="dl" type="button">⬇ Stáhnout CSV</button>
    </div>
    <div style="overflow-x:auto"><table id="tab"><thead><tr><th>Zakázka</th><th>Druh</th><th>Datum</th><th style="text-align:right">Předp. hodnota</th><th></th></tr></thead><tbody></tbody></table></div>
    <p class="note">Předpokládaná hodnota = odhad zadavatele před soutěží (bez DPH). Vítězný dodavatel a konečná cena nejsou v profilu veřejně dostupné — skutečně zaplacené investice ukazuje sekce <a href="investice.html" style="color:var(--accent)">Investice</a>. <b>Úvěry</b> (výběr banky) jsou v profilu vedené jako zakázky; v tabulce jsou, ale do objemů a grafů se nepočítají, protože jde o zdroj peněz, ne výdaj. Zakázky spjaté se školou (dostavba MŠ a ZŠ) tvoří velkou část objemu — viz <a href="skolstvi.html" style="color:var(--accent)">Školství</a>.</p>
  </div>
</section>'''

scripts = '<script>' + CHARTJS + '''</script>
<script>
const D=DATA_JSON, R=D.rows, RV=R.filter(x=>x.druh!=='úvěr');
const esc=s=>String(s==null?'':s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const DCOL={'stavba':'var(--c7)','služba':'var(--c1)','dodávka':'var(--c3)','úvěr':'var(--c4)'};
const nf=new Intl.NumberFormat('cs-CZ');
const norm=s=>(s||'').normalize('NFD').replace(/[\\u0300-\\u036f]/g,'').toLowerCase();
const mil=v=>(v/1e6).toLocaleString('cs-CZ',{maximumFractionDigits:2});
const kc=v=>v==null?'—':(v>=1e6?mil(v)+' mil. Kč':nf.format(v)+' Kč');
const charts={};
function axis(){return {grid:{color:cssv('--line')},ticks:{color:cssv('--muted')}};}
function mk(id,cfg){if(charts[id])charts[id].destroy();charts[id]=new Chart(document.getElementById(id),cfg);}

function kpis(){
  const wv=RV.filter(x=>x.hodnota);
  const tot=wv.reduce((a,x)=>a+x.hodnota,0);
  const big=wv.reduce((a,x)=>x.hodnota>a.hodnota?x:a,wv[0]);
  const C=[
    ['Zakázek', String(RV.length), 'bez úvěrů · z profilu zadavatele','var(--c0)'],
    ['Celkový objem', mil(tot)+' mil. Kč', 'součet předp. hodnot','var(--c3)'],
    ['Největší zakázka', mil(big.hodnota)+' mil.', big.nazev.slice(0,30)+'…','var(--c1)'],
    ['Období', (Math.min.apply(0,R.map(x=>x.rok||9999)))+'–'+(Math.max.apply(0,R.map(x=>x.rok||0))), 'dle profilu','var(--c2)'],
  ];
  document.getElementById('kpis').innerHTML=C.map(c=>`<div class="kpi" style="--bar:${c[3]}"><div class="lab">${c[0]}</div><div class="val" style="font-size:22px">${c[1]}</div><div class="delta" style="color:var(--muted)">${c[2]}</div></div>`).join('');
}
function topChart(){
  const top=RV.filter(x=>x.hodnota).sort((a,b)=>b.hodnota-a.hodnota).slice(0,10);
  mk('topChart',{type:'bar',data:{labels:top.map(x=>x.nazev.length>42?x.nazev.slice(0,40)+'…':x.nazev),
    datasets:[{data:top.map(x=>x.hodnota/1e6),backgroundColor:cssv('--c0'),borderRadius:5}]},
    options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,animation:{duration:600},
      plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>kc(top[c.dataIndex].hodnota)}}},
      scales:{x:Object.assign(axis(),{ticks:{color:cssv('--muted'),callback:v=>v+' mil.'}}),
        y:Object.assign(axis(),{ticks:{color:cssv('--muted'),font:{size:10}}})}}});
}
function yearChart(){
  const by={}; RV.forEach(x=>{if(x.rok&&x.hodnota)by[x.rok]=(by[x.rok]||0)+x.hodnota;});
  const yr=Object.keys(by).sort();
  mk('yearChart',{type:'bar',data:{labels:yr,datasets:[{data:yr.map(y=>by[y]/1e6),backgroundColor:cssv('--c2'),borderRadius:5}]},
    options:{responsive:true,maintainAspectRatio:false,animation:{duration:600},
      plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>mil(by[yr[c.dataIndex]])+' mil. Kč'}}},
      scales:{x:axis(),y:Object.assign(axis(),{ticks:{color:cssv('--muted'),callback:v=>v+' mil.'}})}}});
}
function table(){
  const q=norm(document.getElementById('q').value.trim());
  const sort=document.getElementById('sort').value;
  let list=R.slice().filter(x=>!q||norm(x.nazev).includes(q));
  const dk=d=>(d||'').split('.').reverse().join('');
  list.sort((a,b)=> sort==='new' ? dk(b.datum).localeCompare(dk(a.datum)) : ((b.hodnota||0)-(a.hodnota||0)));
  CUR=list;
  document.querySelector('#tab tbody').innerHTML=list.map(x=>`<tr>
    <td>${esc(x.nazev)}</td><td><span class="dpill" style="color:${DCOL[x.druh]}">${x.druh}</span></td><td style="white-space:nowrap;color:var(--muted)">${x.datum||''}</td>
    <td style="text-align:right;font-variant-numeric:tabular-nums"><b>${kc(x.hodnota)}</b></td>
    <td><a href="${x.url}" target="_blank" rel="noopener" style="color:var(--accent);font-size:12px">detail ↗</a></td></tr>`).join('');
}
let CUR=[];
function render(){kpis();topChart();yearChart();table();}
render(); bindTheme(render);
document.getElementById('q').addEventListener('input',table);
document.getElementById('sort').addEventListener('change',table);
document.getElementById('dl').onclick=()=>dlCSV('zakazky-ostopovice.csv',['Zakázka','Druh','Datum uveřejnění','Předpokládaná hodnota (Kč, bez DPH)','Odkaz'],CUR.map(x=>[x.nazev,x.druh,x.datum,x.hodnota,x.url]));
window.addEventListener('load',()=>{Object.values(charts).forEach(c=>{try{c.resize();}catch(e){}});});
</script>'''.replace("DATA_JSON", data_json)

CSS = '''<style>
table{width:100%;border-collapse:collapse;font-size:13px}
#tab th,#tab td{padding:9px 12px;text-align:left;border-bottom:1px solid var(--line);vertical-align:top}
#tab thead th{color:var(--muted);font-weight:600;font-size:12px;position:sticky;top:0;background:var(--surface)}
#tab tbody tr:hover{background:var(--inset)}
.dpill{font-size:11px;font-weight:600;padding:2px 9px;border-radius:999px;background:var(--inset);border:1px solid var(--line);white-space:nowrap}
.dlbtn{font:inherit;font-size:12.5px;padding:7px 12px;border:1px solid var(--line);border-radius:10px;background:var(--surface);color:var(--text);cursor:pointer}
.dlbtn:hover{border-color:var(--accent)}
select,input[type=text]{font:inherit;font-size:13.5px;padding:7px 11px;border:1px solid var(--line);border-radius:10px;background:var(--surface);color:var(--text);outline:none}
select:focus,input[type=text]:focus{border-color:var(--accent)}
</style>'''

open("zakazky.html", "w", encoding="utf-8").write(
    pc.page("Zakázky", "Veřejné zakázky — Jak žijí Ostopovice", body, head_scripts=CSS, body_scripts=scripts))
print(f"HOTOVO -> zakazky.html ({len(rows)} zakázek, objem {total/1e6:.1f} mil. Kč)")
