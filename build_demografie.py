#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sekce Demografie (demografie.html) — vývoj počtu obyvatel Ostopovic.
Zdroj: ČSÚ (počet obyvatel k 1. 1.). Prototyp: úplnou dekompozici (narození,
úmrtí, stěhování, věková struktura) lze doplnit z demografické databáze ČSÚ."""
import sys, csv, json
import portal_common as pc
sys.stdout.reconfigure(encoding="utf-8")

CHARTJS = open("data/vendor/chart.umd.js", encoding="utf-8").read()
rows = []
for r in csv.DictReader(open("data/ostopovice_obyvatele.csv", encoding="utf-8-sig"), delimiter=";"):
    rows.append({"rok": int(r["rok"]), "stav": int(r["stav"])})
rows.sort(key=lambda x: x["rok"])
first, last = rows[0], rows[-1]
peak = max(rows, key=lambda x: x["stav"])
growth = (last["stav"] - first["stav"]) / first["stav"] * 100

DATA = {"obec": "Ostopovice", "rows": rows}
data_json = json.dumps(DATA, ensure_ascii=False, separators=(",", ":"))

body = f'''<header class="hero">
  <h1>Jak Ostopovice rostou <span style="font-size:17px;font-weight:500;color:var(--muted)">· obec v číslech</span></h1>
  <p>Vývoj počtu obyvatel obce Ostopovice u Brna podle Českého statistického úřadu — stav vždy k 1.&nbsp;lednu ({first["rok"]}–{last["rok"]}).</p>
  <div class="chips"><span class="chip">obec Ostopovice · okres Brno-venkov</span><span class="chip">{first["rok"]}–{last["rok"]}</span><span class="chip">zdroj: ČSÚ</span></div>
</header>

<div class="cards" id="kpis"></div>

<section>
  <div class="sec-h"><h2>Vývoj počtu obyvatel</h2><span class="hint">ČSÚ · {first["rok"]}–{last["rok"]} · stav k 1. 1.</span></div>
  <div class="panel">
    <div class="ctrls"><span class="lbl">Zobrazení</span>
      <span class="seg" id="popSeg"><button class="on" data-k="abs">počet obyvatel</button><button data-k="idx">index ({first["rok"]} = 100)</button></span></div>
    <div class="chartbox"><canvas id="popChart"></canvas></div>
    <p class="note">Obec od roku {first["rok"]} vyrostla o {growth:.0f} % (z {first["stav"]:,} na {last["stav"]:,}), s vrcholem {peak["stav"]:,} obyvatel v roce {peak["rok"]}. Kolem let 2021–2022 přišel mírný pokles (mj. revize po sčítání 2021).</p>
  </div>
</section>

<section>
  <div class="panel">
    <p class="note" style="margin:0;font-size:12.5px">Zdroj: <b>Český statistický úřad</b> — počet obyvatel v obcích k 1.&nbsp;1.</p>
  </div>
</section>'''

scripts = '<script>' + CHARTJS + '''</script>
<script>
const D=DATA_JSON, R=D.rows, YRS=R.map(d=>d.rok);
const nf=new Intl.NumberFormat('cs-CZ');
const charts={};
function axis(){return {grid:{color:isDark()?'#1f2a40':'#eef2f7'},ticks:{color:cssv('--muted')}};}
function mk(id,cfg){if(charts[id])charts[id].destroy();charts[id]=new Chart(document.getElementById(id),cfg);}

function kpis(){
  const L=R[R.length-1], F=R[0];
  const peak=R.reduce((a,d)=>d.stav>a.stav?d:a,R[0]);
  const grow=((L.stav-F.stav)/F.stav*100);
  const C=[
    ['Počet obyvatel '+L.rok, nf.format(L.stav), 'stav k 1. 1.','var(--c0)'],
    ['Růst od '+F.rok, (grow>=0?'+':'')+grow.toFixed(0)+' %', 'z '+nf.format(F.stav)+' na '+nf.format(L.stav),'var(--c2)'],
    ['Historické maximum', nf.format(peak.stav), 'v roce '+peak.rok,'var(--c3)'],
    ['Sledované období', (L.rok-F.rok)+' let', F.rok+'–'+L.rok,'var(--c1)'],
  ];
  document.getElementById('kpis').innerHTML=C.map(c=>`<div class="kpi" style="--bar:${c[3]}"><div class="lab">${c[0]}</div><div class="val">${c[1]}</div><div class="delta" style="color:var(--muted)">${c[2]}</div></div>`).join('');
}
let popMode='abs';
function popChart(){
  const base=R[0].stav;
  const val=R.map(d=> popMode==='idx' ? +(d.stav/base*100).toFixed(1) : d.stav);
  mk('popChart',{type:'line',data:{labels:YRS,datasets:[{
    label: popMode==='idx'?'Index':'Počet obyvatel', data:val,
    borderColor:cssv('--c0'), backgroundColor:'transparent', borderWidth:2.6,
    tension:.3, pointRadius:2.4, pointHoverRadius:6, fill:false}]},
    options:{responsive:true,maintainAspectRatio:false,animation:{duration:600},
      plugins:{legend:{display:false},tooltip:{callbacks:{label:c=> popMode==='idx'
        ? 'Index '+c.label+': '+c.parsed.y+' ('+nf.format(R[c.dataIndex].stav)+' obyv.)'
        : nf.format(c.parsed.y)+' obyvatel ('+c.label+')'}}},
      scales:{x:Object.assign(axis(),{ticks:{color:cssv('--muted'),autoSkip:true,maxTicksLimit:12}}),
        y:Object.assign(axis(),{ticks:{color:cssv('--muted')}})}}});
}
function render(){kpis();popChart();}
render(); bindTheme(render);
document.querySelectorAll('#popSeg button').forEach(b=>b.onclick=()=>{document.querySelectorAll('#popSeg button').forEach(x=>x.classList.remove('on'));b.classList.add('on');popMode=b.dataset.k;popChart();});
window.addEventListener('load',()=>{Object.values(charts).forEach(c=>{try{c.resize();}catch(e){}});});
</script>'''.replace("DATA_JSON", data_json)

open("demografie.html", "w", encoding="utf-8").write(
    pc.page("Demografie", "Demografie — Jak žijí Ostopovice", body, body_scripts=scripts))
print(f"HOTOVO -> demografie.html ({len(rows)} let {first['rok']}-{last['rok']}, {last['stav']} obyv.)")
