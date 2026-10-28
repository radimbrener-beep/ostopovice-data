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

# výběrová řízení z XML exportu profilu (scripts/fetch_profil_rizeni.py): nabídky, vybraná firma, stav
try:
    _pr = json.load(open("data/profil_rizeni.json", encoding="utf-8"))
except FileNotFoundError:
    _pr = {"profil": "", "zakazky": []}
POSTUP = {"výjimka": "zakázka malého rozsahu"}
# [datum, název, url, stav, druh, dodavatel, cena, předpokl. hodnota, lhůta, nabídky[[firma, cena, vyloučen, vítěz]], postup]
pz = []
for z in _pr["zakazky"]:
    nab = [[n["firma"], n["cena"], 1 if n["vyloucen"] else 0,
            1 if z["dodavatel_ico"] and n["ico"] == z["dodavatel_ico"] else 0] for n in z["nabidky"]]
    nab.sort(key=lambda n: (n[1] is None, n[1] or 0))
    pz.append([z["datum"], z["nazev"], z["url"], z["stav"], z["druh"], z["dodavatel"], z["cena"],
               z["predpokladana_hodnota"], z["lhuta"], nab, POSTUP.get(z["postup"], z["postup"])])
pz.sort(key=lambda z: z[0] or "", reverse=True)
pz_s_nab = sum(1 for z in pz if z[9])
pz_prime = sum(1 for z in pz if z[10] == "přímé zadání")

PZ_LEAD = (f"Nabídky obec na profilu uvádí u <b>{pz_s_nab}</b> z {len(pz)} řízení; "
           f"<b>{pz_prime}</b> zakázek zadala přímo, bez soutěže.") if pz else ""

DATA = {"rows": rows, "pz": pz}
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
    <p class="note">Předpokládaná hodnota = odhad zadavatele před soutěží (bez DPH). Kdo zakázku získal a za kolik, je u části zakázek v sekci <a href="#vypsane" style="color:var(--accent)">Výběrová řízení a nabídky</a> níže; skutečně zaplacené investice ukazuje sekce <a href="investice.html" style="color:var(--accent)">Investice</a>. <b>Úvěry</b> (výběr banky) jsou v profilu vedené jako zakázky; v tabulce jsou, ale do objemů a grafů se nepočítají, protože jde o zdroj peněz, ne výdaj. Zakázky spjaté se školou (dostavba MŠ a ZŠ) tvoří velkou část objemu — viz <a href="skolstvi.html" style="color:var(--accent)">Školství</a>.</p>
  </div>
</section>
<div id="pzLive"></div>

<section id="vypsane">
  <div class="sec-h"><h2>Výběrová řízení a nabídky</h2><span class="hint">profil zadavatele · {len(pz)} řízení</span></div>
  <div class="panel">
    <p class="pz-lead">Jak obec zakázky zadávala: druh řízení, kdo podal nabídku, za kolik a kdo vyhrál. {PZ_LEAD}</p>
    <div class="pz-ctrl"><span class="seg" id="pzSeg"></span><input id="pzQ" type="text" placeholder="hledat zakázku / firmu…"></div>
    <div style="overflow-x:auto"><table id="pzTbl"><thead><tr><th>Vypsáno</th><th>Zakázka</th><th>Stav</th><th class="r">Nabídky</th><th>Vybraná firma</th><th class="r">Cena bez DPH</th></tr></thead><tbody></tbody></table></div>
    <div id="pzMore"></div>
    <p class="note"><b>Klikni na řádek</b> s nabídkami — rozbalí se všechny nabídky s cenami. Ceny jsou bez DPH tak, jak je obec uvedla na profilu; když smluvní cena chybí, je uvedena vítězná nabídka. Stav <i>zadáno</i> = je vybraná firma, nebo obec řízení vede jako dokončené. Nové zakázky se kontrolují denně a lze si na ně zapnout upozornění (zvonek nahoře).</p>
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
// --- výběrová řízení (XML profilu zadavatele) ---
const PZ=D.pz, PZST={'zadáno':'zad','zrušeno':'zru','probíhá':'pro','bez výsledku':'bez'}, PZP=15;
let pzStav='vse', pzQ='', pzShown=PZP; const pzOpen=new Set();
const pkc=v=>v?nf.format(v)+'&nbsp;Kč':'—';
const fdat=iso=>{if(!iso)return '—';const p=iso.slice(0,10).split('-');return p[2]+'. '+(+p[1])+'. '+p[0];};
const lhuta=l=>l?fdat(l)+(l.includes('T')?' '+l.split('T')[1]:''):'';
function pzTable(){
  const nq=norm(pzQ);
  let rr=PZ.filter(z=>pzStav==='vse'||z[3]===pzStav);
  if(nq)rr=rr.filter(z=>norm(z[1]).includes(nq)||z[9].some(n=>norm(n[0]).includes(nq)));
  document.querySelector('#pzTbl tbody').innerHTML=rr.length?rr.slice(0,pzShown).map(z=>{
    const id=z[2]+'|'+z[1], open=pzOpen.has(id);
    const sub=[z[4], z[10], z[7]?'předpokládaná hodnota '+nf.format(z[7])+' Kč':'', z[3]==='probíhá'&&z[8]?'nabídky do '+lhuta(z[8]):''].filter(Boolean).join(' · ');
    let h=`<tr class="prow${open?' open':''}${z[9].length?'':' nox'}" data-id="${esc(id)}"><td class="dt">${fdat(z[0])}</td>
      <td class="zn"><span class="car">${z[9].length?'▶':''}</span><span class="pzn">${esc(z[1])}</span><a class="zsrc" href="${z[2]}" target="_blank" rel="noopener" onclick="event.stopPropagation()" title="Detail na profilu zadavatele">profil&nbsp;&#8599;</a>
        <div class="pzsub">${esc(sub)}</div></td>
      <td><span class="pst ${PZST[z[3]]}">${z[3]}</span></td>
      <td class="r">${z[9].length?z[9].length+'<span class="pzsub" style="display:inline"> nab.</span>':'—'}</td><td>${esc(z[5])||'—'}</td><td class="r"><b>${pkc(z[6])}</b></td></tr>`;
    if(open)h+=z[9].map(n=>`<tr class="nab${n[3]?' win':''}"><td></td><td class="zn"><span class="${n[2]?'vyl':''}">${esc(n[0])}</span>${n[3]?' ✓ vybrána':''}${n[2]?' <span class="pzsub" style="display:inline">vyloučen / odstoupil</span>':''}</td><td></td><td></td><td></td><td class="r">${pkc(n[1])}</td></tr>`).join('');
    return h;}).join(''):'<tr><td colspan="6" style="color:var(--faint);text-align:center;padding:22px">Nic nenalezeno.</td></tr>';
  document.getElementById('pzMore').innerHTML=rr.length>pzShown?`<button class="morebtn" id="pzMoreB">Zobrazit další (${rr.length-pzShown})</button>`:'';
  const mb=document.getElementById('pzMoreB'); if(mb)mb.onclick=()=>{pzShown+=PZP;pzTable();};
}
if(PZ.length){
  const cnt=s=>PZ.filter(z=>z[3]===s).length;
  document.getElementById('pzSeg').innerHTML=[['vse','Vše ('+PZ.length+')'],...['probíhá','zadáno','zrušeno','bez výsledku'].filter(cnt).map(s=>[s,s[0].toUpperCase()+s.slice(1)+' ('+cnt(s)+')'])]
    .map(([k,l])=>`<button data-s="${k}"${k==='vse'?' class="on"':''}>${l}</button>`).join('');
  document.querySelectorAll('#pzSeg button').forEach(b=>b.onclick=()=>{pzStav=b.dataset.s;pzShown=PZP;
    document.querySelectorAll('#pzSeg button').forEach(x=>x.classList.toggle('on',x===b));pzTable();});
  document.getElementById('pzQ').oninput=e=>{pzQ=e.target.value.trim();pzShown=PZP;pzTable();};
  document.querySelector('#pzTbl tbody').addEventListener('click',e=>{const tr=e.target.closest('tr.prow');
    if(tr&&!tr.classList.contains('nox')){const id=tr.dataset.id;pzOpen.has(id)?pzOpen.delete(id):pzOpen.add(id);pzTable();}});
  pzTable();
  const live=PZ.filter(z=>z[3]==='probíhá');
  if(live.length)document.getElementById('pzLive').innerHTML=`<div class="pzlive"><b>Právě vypsané zakázky</b>
    <ul>${live.map(z=>`<li><a href="${z[2]}" target="_blank" rel="noopener" style="color:var(--accent)">${esc(z[1])}</a>${z[8]?' — nabídky do '+lhuta(z[8]):''}</li>`).join('')}</ul>
    <div class="pzsub">Podrobnosti v sekci <a href="#vypsane" style="color:var(--accent)">Výběrová řízení a nabídky</a>.</div></div>`;
} else document.getElementById('vypsane').hidden=true;
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
#pzTbl{width:100%;border-collapse:collapse;font-size:13.5px}
#pzTbl thead th{text-align:left;color:var(--muted);font-weight:600;font-size:11.5px;padding:8px 12px 8px 0;border-bottom:1px solid var(--line)}
#pzTbl th.r,#pzTbl td.r{text-align:right}
#pzTbl tbody td{padding:10px 12px 10px 0;border-bottom:1px solid var(--line);vertical-align:top}
#pzTbl td.r{white-space:nowrap;font-variant-numeric:tabular-nums}
#pzTbl td.dt{white-space:nowrap;color:var(--muted);font-size:12.5px}
#pzTbl tr.prow{cursor:pointer;transition:background .12s}
#pzTbl tr.prow.nox{cursor:default}
#pzTbl tr.prow:hover{background:var(--inset)}
#pzTbl tr.prow .car{display:inline-block;width:16px;color:var(--faint);font-size:11px;transition:transform .15s}
#pzTbl tr.prow.open .car{transform:rotate(90deg)}
#pzTbl .pzn{font-weight:600;margin-right:6px}
.pzsub{font-size:11.5px;color:var(--faint);margin-top:2px}
#pzTbl tr.nab td{background:var(--surface2);font-size:12.5px;padding-top:7px;padding-bottom:7px}
#pzTbl tr.nab td.zn{padding-left:16px}
#pzTbl tr.nab.win td{color:var(--text);font-weight:600}
#pzTbl tr.nab .vyl{color:var(--faint);text-decoration:line-through}
.zsrc{display:inline-block;font-size:11.5px;padding:2px 8px;border-radius:999px;background:var(--inset);color:var(--muted);text-decoration:none;border:1px solid var(--line);white-space:nowrap}
.zsrc:hover{color:var(--accent);border-color:var(--accent)}
.pst{display:inline-block;font-size:11px;font-weight:600;padding:2px 9px;border-radius:999px;border:1px solid var(--line);white-space:nowrap}
.pst.zad{color:var(--c0);background:color-mix(in srgb,var(--c0) 12%,transparent)}
.pst.zru,.pst.bez{color:var(--muted);background:var(--inset)}
.pst.pro{color:var(--amber);background:color-mix(in srgb,var(--amber) 14%,transparent);border-color:color-mix(in srgb,var(--amber) 40%,transparent)}
.pz-lead{margin:0 0 12px;line-height:1.6}
.pz-ctrl{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin-bottom:8px}
#pzQ{min-width:220px;margin-left:auto}
.morebtn{margin:14px auto 0;display:block;background:var(--inset);border:1px solid var(--line);color:var(--text);font:inherit;font-size:13px;font-weight:500;padding:9px 20px;border-radius:10px;cursor:pointer}
.morebtn:hover{border-color:var(--accent);color:var(--accent)}
.pzlive{margin:18px 0;padding:14px 16px;border-radius:var(--radius);background:var(--surface);border:1px solid var(--line);border-left:4px solid var(--amber)}
.pzlive ul{margin:6px 0 0;padding-left:18px;line-height:1.6}
@media(max-width:640px){
  #pzTbl thead{display:none}
  #pzTbl,#pzTbl tbody{display:block}
  #pzTbl tbody tr{display:block;padding:10px 4px;border-bottom:1px solid var(--line)}
  #pzTbl tbody td{display:inline-block;padding:2px 10px 2px 0;border:none;text-align:left}
  #pzTbl tbody td:empty{display:none}
  #pzTbl tr.prow td.zn{display:block}
  #pzQ{margin-left:0;min-width:0;flex:1}
}
</style>'''

open("zakazky.html", "w", encoding="utf-8").write(
    pc.page("Zakázky", "Veřejné zakázky — Jak žijí Ostopovice", body, head_scripts=CSS, body_scripts=scripts))
print(f"HOTOVO -> zakazky.html ({len(rows)} zakázek, objem {total/1e6:.1f} mil. Kč)")
