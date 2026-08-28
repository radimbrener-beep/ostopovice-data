#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sekce Komu obec přispívá (dotace.html) — dotace, dary a příspěvky, které
obec Ostopovice poskytuje spolkům a dalším subjektům. Zdroj: usnesení ZO
(schválené poskytnutí dotace/daru/příspěvku s částkou)."""
import sys, json, re
import portal_common as pc
sys.stdout.reconfigure(encoding="utf-8")

CHARTJS = open("data/vendor/chart.umd.js", encoding="utf-8").read()
zo = json.load(open("dataset_ZO.json", encoding="utf-8"))

GRANT = re.compile(r"poskytnut\w*\s+(?:individuáln\w+\s+)?(dotac\w+|dar\w*|příspěv\w+)|schvaluje\s+dar\b", re.I)
# vylučující kontexty: rozpočtová opatření, návrh rozpočtu, jen „bere na vědomí"
EXCL = re.compile(r"rozpočtov\w+\s+opatřen|návrh\w*\s+rozpočt|změn\w+\s+návrhu\s+rozpočt", re.I)

def recipient(text):
    """Věcný příjemce dotace. Některé dotace jdou formálně přes fyzickou osobu
    (předsedu spolku), ale příjemcem/účelem je spolek — uvádíme věcně a
    sjednocujeme opakující se příjemce."""
    t = re.sub(r"\s+", " ", text)
    # sjednocené opakované příjemce (podle názvu spolku/účelu kdekoli v textu)
    if re.search(r"klub\w*\s+senior", t, re.I):        return "Klub Seniorů Ostopovice"
    if re.search(r"dobromysl", t, re.I):               return "Spolek Dobromysl"
    if re.search(r"sokol", t, re.I):                   return "TJ Sokol Ostopovice"
    if re.search(r"včelař", t, re.I):                  return "Včelařský spolek Střelice u Brna"
    if re.search(r"charit", t, re.I) and re.search(r"rajhrad", t, re.I):
        return "Charita Rajhrad"
    if re.search(r"farnost\w*\s+Troubsko", t, re.I):   return "Římskokatolická farnost Troubsko"
    if re.search(r"Háječek", t):                       return "Dětský folklórní soubor Háječek"
    if re.search(r"LuckyCats", t):                     return "LuckyCats, z.s."
    if re.search(r"Obc[ei]\s+Hrušky", t):              return "Obec Hrušky"
    # přímá extrakce: „…dotace/daru/příspěvku [ve výši … Kč] [tituly] <Název>"
    m = re.search(
        r"(?:dotac\w+|dar\w*|příspěv\w+)\s+"
        r"(?:ve\s+výši[^A-Za-zÁ-Žá-ž]*Kč\s+)?"
        r"(?:(?:pan[uíi]?|paní|Ing\.?|Mgr\.?|Bc\.?|doc\.?|prof\.?|MUDr\.?|MVDr\.?)\s+)*"
        r"([A-ZÁ-Ž][^,\.]{2,60}?)"
        r"(?:\s+ve\s+výši|\s+se\s+sídlem|\s+na\s+|\s+za\s+|\s+IČ|,|\.|$)", t)
    if m:
        return re.sub(r"\s+", " ", m.group(1)).strip(" ,")
    # fallback: „…smlouvu mezi Obcí Ostopovice (…) a <Obdarovaný>"
    m = re.search(r"mezi\s+Obcí\s+Ostopovice\s*(?:\([^)]*\))?\s*a\s+([A-ZÁ-Ž][^,]{2,60}?)(?:\s*\(|,|\s+se\s+sídlem|$)", t)
    if m:
        return re.sub(r"\s+", " ", m.group(1)).strip(" ,")
    return "(příjemce neurčen)"

# redakce PII z veřejně zobrazovaného textu (na portál nepatří):
#  - domácí adresa („bytem …")
#  - jméno soukromé osoby uvedené jako prostředník („panu/paní/Ing. Jméno Příjmení")
# Organizace (bez titulu pan/paní/Ing…) zůstávají.
ADDR_RE = re.compile(r",?\s*bytem\s+.*?\d{3}\s?\d{2}\s+[A-Za-zÁ-Žá-ž]+\s*", re.I)
NAME_RE = re.compile(r"\s*\b(?:pan[uíi]?|paní|Ing\.|Mgr\.|Bc\.|MVDr\.|MUDr\.|doc\.|prof\.)\s+"
                     r"[A-ZÁ-Ž][a-zá-ž]+(?:\s+[A-ZÁ-Ž][a-zá-ž]+){1,2}", re.I)
def redact(text):
    t = re.sub(r"\s*-\s*\d+\s*-\s*", " ", text)   # artefakty zalomení stránky „- 3 -"
    t = ADDR_RE.sub(" ", t)
    t = NAME_RE.sub("", t)
    t = re.sub(r"\s+([,\.])", r"\1", t)
    t = re.sub(r"\s{2,}", " ", t).strip()
    return t

items = []
for m in zo:
    for b in m["body"]:
        if not b.get("castka"):
            continue
        if b.get("kategorie") != "schvaluje":
            continue
        if not GRANT.search(b["text"]) or EXCL.search(b["text"]):
            continue
        items.append({"castka": b["castka"], "rok": m["rok"], "zo": f"{m['cislo_zasedani']}/{m['rok']}",
                      "prijemce": recipient(b["text"]), "text": redact(b["text"]), "url": m.get("url", "")})
items.sort(key=lambda x: -x["castka"])
# vedlejší výstup pro Bilanci období a Hledání
open("data/dotace.json", "w", encoding="utf-8").write(json.dumps(items, ensure_ascii=False, indent=1))
total = sum(x["castka"] for x in items)

DATA = {"items": items}
data_json = json.dumps(DATA, ensure_ascii=False, separators=(",", ":"))

body = f'''<header class="hero">
  <h1>Komu obec přispívá</h1>
  <p>Dotace, dary a příspěvky, které obec Ostopovice poskytuje spolkům a dalším subjektům — schválené zastupitelstvem, s částkami.</p>
  <div class="chips"><span class="chip">obec Ostopovice</span><span class="chip">{len(items)} příspěvků · {total/1e6:.1f} mil. Kč</span><span class="chip">zdroj: usnesení ZO</span></div>
</header>

<div class="cards" id="kpis"></div>

<section>
  <div class="grid2">
    <div class="panel">
      <div class="sec-h" style="margin:0 0 8px"><h2 style="font-size:16px">Podle příjemce</h2></div>
      <div class="chartbox sm"><canvas id="recChart"></canvas></div>
    </div>
    <div class="panel">
      <div class="sec-h" style="margin:0 0 8px"><h2 style="font-size:16px">Podle roku</h2></div>
      <div class="chartbox sm"><canvas id="yearChart"></canvas></div>
    </div>
  </div>
</section>

<section>
  <div class="sec-h"><h2>Všechny příspěvky</h2><span class="hint">seřazeno podle částky · proklik na zápis ZO</span></div>
  <div class="panel">
    <div style="overflow-x:auto"><table id="tab"><thead><tr><th>Příjemce / účel</th><th>Zasedání</th><th style="text-align:right">Částka</th></tr></thead><tbody></tbody></table></div>
    <p class="note">Zdroj: usnesení zastupitelstva (schválené poskytnutí dotace/daru/příspěvku). Drobné příspěvky pod hranicí, které schvaluje rada obce, tu nemusí být obsaženy. Příjemce je odvozen z textu usnesení — u některých položek je uveden jen účel.</p>
  </div>
</section>'''

scripts = '<script>' + CHARTJS + '''</script>
<script>
const D=DATA_JSON, IT=D.items;
const nf=new Intl.NumberFormat('cs-CZ');
const kc=v=>v>=1e6?(v/1e6).toLocaleString('cs-CZ',{maximumFractionDigits:2})+' mil. Kč':nf.format(v)+' Kč';
const PAL=['--c0','--c1','--c2','--c3','--c4','--c5','--c6','--c7'];
const charts={};
function axis(){return {grid:{color:isDark()?'#1f2a40':'#eef2f7'},ticks:{color:cssv('--muted')}};}
function mk(id,cfg){if(charts[id])charts[id].destroy();charts[id]=new Chart(document.getElementById(id),cfg);}

function kpis(){
  const tot=IT.reduce((a,x)=>a+x.castka,0);
  const by={}; IT.forEach(x=>by[x.prijemce]=(by[x.prijemce]||0)+x.castka);
  const top=Object.entries(by).sort((a,b)=>b[1]-a[1])[0];
  const C=[
    ['Příspěvků celkem', String(IT.length), 'schválených zastupitelstvem','var(--c0)'],
    ['Objem', kc(tot), 'dotace, dary, příspěvky','var(--c3)'],
    ['Největší příjemce', top?top[0].slice(0,22):'—', top?kc(top[1]):'','var(--c1)'],
    ['Různých příjemců', String(Object.keys(by).length), 'spolky a subjekty','var(--c2)'],
  ];
  document.getElementById('kpis').innerHTML=C.map(c=>`<div class="kpi" style="--bar:${c[3]}"><div class="lab">${c[0]}</div><div class="val" style="font-size:20px">${c[1]}</div><div class="delta" style="color:var(--muted)">${c[2]}</div></div>`).join('');
}
function recChart(){
  const by={}; IT.forEach(x=>by[x.prijemce]=(by[x.prijemce]||0)+x.castka);
  const arr=Object.entries(by).sort((a,b)=>b[1]-a[1]).slice(0,8);
  mk('recChart',{type:'bar',data:{labels:arr.map(e=>e[0].length>28?e[0].slice(0,26)+'…':e[0]),
    datasets:[{data:arr.map(e=>e[1]),backgroundColor:arr.map((e,i)=>cssv(PAL[i%PAL.length])),borderRadius:5}]},
    options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,animation:{duration:600},
      plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>kc(c.parsed.x)}}},
      scales:{x:Object.assign(axis(),{ticks:{color:cssv('--muted'),callback:v=>nf.format(v)}}),y:Object.assign(axis(),{ticks:{color:cssv('--muted'),font:{size:11}}})}}});
}
function yearChart(){
  const by={}; IT.forEach(x=>{if(x.rok)by[x.rok]=(by[x.rok]||0)+x.castka;});
  const yr=Object.keys(by).sort();
  mk('yearChart',{type:'bar',data:{labels:yr,datasets:[{data:yr.map(y=>by[y]),backgroundColor:cssv('--c2'),borderRadius:5}]},
    options:{responsive:true,maintainAspectRatio:false,animation:{duration:600},
      plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>kc(by[yr[c.dataIndex]])}}},
      scales:{x:axis(),y:Object.assign(axis(),{ticks:{color:cssv('--muted'),callback:v=>nf.format(v)}})}}});
}
function tab(){
  document.querySelector('#tab tbody').innerHTML=IT.map(x=>`<tr>
    <td><b>${x.prijemce}</b><div style="color:var(--muted);font-size:12px;margin-top:2px">${x.text.length>120?x.text.slice(0,118)+'…':x.text}</div></td>
    <td style="white-space:nowrap;color:var(--muted)">${x.url?`<a href="${x.url}" target="_blank" rel="noopener" style="color:var(--accent)">ZO ${x.zo} ↗</a>`:'ZO '+x.zo}</td>
    <td style="text-align:right;font-variant-numeric:tabular-nums"><b>${kc(x.castka)}</b></td></tr>`).join('');
}
function render(){kpis();recChart();yearChart();tab();}
render(); bindTheme(render);
window.addEventListener('load',()=>{Object.values(charts).forEach(c=>{try{c.resize();}catch(e){}});});
</script>'''.replace("DATA_JSON", data_json)

CSS = '''<style>
#tab{width:100%;border-collapse:collapse;font-size:13px}
#tab th,#tab td{padding:9px 12px;text-align:left;border-bottom:1px solid var(--line);vertical-align:top}
#tab thead th{color:var(--muted);font-weight:600;font-size:12px}
#tab tbody tr:hover{background:var(--inset)}
</style>'''

open("dotace.html", "w", encoding="utf-8").write(
    pc.page("Dotace spolkům", "Komu obec přispívá — Jak žijí Ostopovice", body, head_scripts=CSS, body_scripts=scripts))
print(f"HOTOVO -> dotace.html ({len(items)} příspěvků, {total/1e6:.2f} mil. Kč)")
