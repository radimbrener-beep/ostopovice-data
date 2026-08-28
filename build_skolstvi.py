#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sekce Školství (skolstvi.html) — MŠ a ZŠ Ostopovice + demografický kontext.
Data: rejstřík škol / web školy (zsostopovice.cz) + počet obyvatel z ČSÚ."""
import sys, csv, json
import portal_common as pc
sys.stdout.reconfigure(encoding="utf-8")

CHARTJS = open("data/vendor/chart.umd.js", encoding="utf-8").read()
pop = []
for r in csv.DictReader(open("data/ostopovice_obyvatele.csv", encoding="utf-8-sig"), delimiter=";"):
    pop.append({"rok": int(r["rok"]), "stav": int(r["stav"])})

# reálná fakta o škole (rejstřík MŠMT / zsostopovice.cz)
skoly = [
    {"nazev": "Mateřská škola", "big": "73", "unit": "míst", "pozn": "trojtřídní · kapacita 73 dětí", "bar": "--c1"},
    {"nazev": "Základní škola", "big": "78", "unit": "žáků", "pozn": "pouze 1. stupeň (2. stupeň žáci dojíždějí mimo obec)", "bar": "--c0"},
    {"nazev": "Školní družina", "big": "60", "unit": "míst", "pozn": "součást školy", "bar": "--c2"},
]
DATA = {"pop": pop, "skoly": skoly}
data_json = json.dumps(DATA, ensure_ascii=False, separators=(",", ":"))

body = f'''<header class="hero">
  <h1>Školství v Ostopovicích</h1>
  <p>Mateřská a základní škola Ostopovice (jedna příspěvková organizace) a demografický kontext obce — kolik dětí v obci vyrůstá.</p>
  <div class="chips"><span class="chip">MŠ a ZŠ Ostopovice</span><span class="chip">RED-IZO 600111245</span><span class="chip">zdroj: rejstřík škol · zsostopovice.cz · ČSÚ</span></div>
</header>

<div class="cards" id="skoly"></div>

<section>
  <div class="sec-h"><h2>Demografický kontext</h2><span class="hint">počet obyvatel obce · ČSÚ · {pop[0]["rok"]}–{pop[-1]["rok"]}</span></div>
  <div class="panel">
    <div class="chartbox"><canvas id="popChart"></canvas></div>
    <p class="note">Počet obyvatel obce naznačuje dlouhodobou poptávku po místech ve školce a škole. Vývoj počtu obyvatel podrobněji v sekci <a href="demografie.html" style="color:var(--accent)">Demografie</a>.</p>
  </div>
</section>

<section>
  <div class="panel">
    <div class="sec-h" style="margin:0 0 8px"><h2 style="font-size:16px">Obec investuje do školy</h2></div>
    <p class="note" style="margin:0;font-size:13px">Škola je zároveň komunitním centrem obce a prochází <b>dostavbou a rozšířením kapacity MŠ i ZŠ</b> (II. etapa). Související zakázky — dostavba, gastro technologie, vybavení interiérů, pobytová terasa, vstupní objekt i úvěr na dofinancování — najdete v sekci <a href="zakazky.html" style="color:var(--accent)">Zakázky</a> (školské zakázky tvoří velkou část investic obce). Provoz školy obec podporuje ročním příspěvkem ze svého rozpočtu.</p>
  </div>
</section>

<section>
  <div class="panel">
    <p class="note" style="margin:0;font-size:12.5px">Zdroj: rejstřík škol MŠMT (RED-IZO 600111245), web školy <a href="https://www.zsostopovice.cz" target="_blank" rel="noopener" style="color:var(--accent)">zsostopovice.cz</a>, počet obyvatel ČSÚ.</p>
  </div>
</section>'''

scripts = '<script>' + CHARTJS + '''</script>
<script>
const D=DATA_JSON, POP=D.pop, YRS=POP.map(d=>d.rok);
const nf=new Intl.NumberFormat('cs-CZ');
const charts={};
function axis(){return {grid:{color:isDark()?'#1f2a40':'#eef2f7'},ticks:{color:cssv('--muted')}};}
function mk(id,cfg){if(charts[id])charts[id].destroy();charts[id]=new Chart(document.getElementById(id),cfg);}
function skoly(){
  document.getElementById('skoly').innerHTML=D.skoly.map(s=>`<div class="kpi" style="--bar:${s.bar}"><div class="lab">${s.nazev}</div>
    <div class="val">${s.big}<span class="unit" style="font-size:13px;color:var(--muted);font-weight:500"> ${s.unit}</span></div>
    <div class="delta" style="color:var(--muted)">${s.pozn}</div></div>`).join('')
    + `<div class="kpi" style="--bar:var(--c3)"><div class="lab">Organizace</div><div class="val" style="font-size:20px">1 spojená</div><div class="delta" style="color:var(--muted)">MŠ + ZŠ + družina + jídelna</div></div>`;
}
function popChart(){
  mk('popChart',{type:'line',data:{labels:YRS,datasets:[{label:'Počet obyvatel',data:POP.map(d=>d.stav),
    borderColor:cssv('--c0'),backgroundColor:'transparent',borderWidth:2.6,tension:.3,pointRadius:2,pointHoverRadius:6}]},
    options:{responsive:true,maintainAspectRatio:false,animation:{duration:600},
      plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>nf.format(c.parsed.y)+' obyvatel ('+c.label+')'}}},
      scales:{x:Object.assign(axis(),{ticks:{color:cssv('--muted'),autoSkip:true,maxTicksLimit:12}}),y:Object.assign(axis(),{ticks:{color:cssv('--muted')}})}}});
}
function render(){skoly();popChart();}
render(); bindTheme(render);
window.addEventListener('load',()=>{Object.values(charts).forEach(c=>{try{c.resize();}catch(e){}});});
</script>'''.replace("DATA_JSON", data_json)

open("skolstvi.html", "w", encoding="utf-8").write(
    pc.page("Školství", "Školství — Jak žijí Ostopovice", body, body_scripts=scripts))
print("HOTOVO -> skolstvi.html (MŠ+ZŠ Ostopovice, demografický kontext " + str(pop[0]["rok"]) + "-" + str(pop[-1]["rok"]) + ")")
