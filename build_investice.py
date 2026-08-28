#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sekce Investice (investice.html) — kam obec Ostopovice investuje.
Přehled: kapitálové výdaje obce z MONITORu (FIN 2-12 M), veřejné zakázky
(stavby/majetek) kategorizované a přímá investiční rozhodnutí ZO (úvěry, pozemky)."""
import sys, json, re
import portal_common as pc
sys.stdout.reconfigure(encoding="utf-8")

CHARTJS = open("data/vendor/chart.umd.js", encoding="utf-8").read()
zak = json.load(open("data/zakazky.json", encoding="utf-8"))
zo = json.load(open("dataset_ZO.json", encoding="utf-8"))
ROZ = json.load(open("data/rozpocet_ostopovice.json", encoding="utf-8"))
# kapitálové výdaje (skutečnost) po letech z MONITORu
kap = []
for y in ROZ["years"]:
    st = ROZ["struktura"].get(str(y["rok"]), {})
    k = next((x["skut"] for x in st.get("vydaje_druh", []) if "apitál" in x["name"]), 0)
    kap.append({"rok": y["rok"], "kap": k, "vydaje": y["vydaje"]["skut"]})

def rok(d):
    m = re.search(r"(\d{4})", d or ""); return int(m.group(1)) if m else None

def kategorie(n):
    n = n.lower()
    if re.search(r"úvěr", n): return "Financování"
    if re.search(r"škol|mš|zš|gastro|družin|terasa|učeb", n): return "Škola (MŠ a ZŠ)"
    if re.search(r"kanaliz|vodovod|přípoj|čistírn", n): return "Voda a kanalizace"
    if re.search(r"chodník|osvětlen|ulic|komunikac|silnic|křižovatk|uzavřen|[–-]\s*lipová$", n): return "Doprava a prostranství"
    if re.search(r"hřiště|sportov|pumptrack|cyklist|knihovn|sál|vodní prvek|vodárn|park|mobiliář|úřad", n): return "Občanská vybavenost"
    if re.search(r"vozidl|traktor|stroj|sekačk|odpad|kompost", n): return "Technika a odpady"
    return "Ostatní"

# do investic nepatří úvěry (zdroj peněz) ani provozní služby (svoz odpadu, provoz vodovodu)
_PROVOZ = re.compile(r"svoz a likvidac|vodohospodářských služeb", re.I)
zak = [z for z in zak if z.get("hodnota") and not re.search(r"úvěr", z["nazev"], re.I) and not _PROVOZ.search(z["nazev"])]
for z in zak:
    z["rok"] = rok(z["datum"]); z["kat"] = kategorie(z["nazev"])
objem = sum(z["hodnota"] for z in zak)

# přímá investiční rozhodnutí zastupitelstva (s částkou):
#  - financování (úvěry na dostavbu školy)
#  - nákupy pozemků a majetku
# Velké stavební investice v usneseních ZO nejsou — o zadání rozhoduje rada
# a výběrová řízení (viz Zakázky). Proto se objem ZO a zakázek nesčítá.
zo_invest = []
for m in zo:
    for b in m["body"]:
        t = b["text"]
        castka = b.get("castka")
        if re.search(r"smlouv\w* o úvěru|úvěr\w* ve výši", t, re.I):
            # výši úvěru čteme napřímo (společný vydaje.py má strop 80 mil. proti
            # artefaktům z tabulek — úvěr 105 mil. Kč na dostavbu školy je ale skutečný)
            mu = re.search(r"úvěr\w*\s+ve\s+výši\s+(\d+(?:,\d+)?)\s*mil", t)
            if mu:
                castka = round(float(mu.group(1).replace(",", ".")) * 1e6)
            typ = "Financování (úvěr)"
        elif b.get("tema") == "Pozemky, majetek a bydlení" and re.search(r"koup|kupní|nákup|pozem|nemovit|směn", t, re.I):
            typ = "Pozemek / majetek"
        else:
            continue
        if not castka:
            continue
        zo_invest.append({"castka": castka, "rok": m["rok"], "text": t, "typ": typ,
                          "url": m.get("url", ""), "zo": f"{m['cislo_zasedani']}/{m['rok']}"})
zo_invest.sort(key=lambda x: -x["castka"])
objem_poz = sum(p["castka"] for p in zo_invest)

DATA = {"zak": zak, "pozemky": zo_invest, "kap": kap}
data_json = json.dumps(DATA, ensure_ascii=False, separators=(",", ":"))

body = f'''<header class="hero">
  <h1>Kam obec investuje</h1>
  <p>Do čeho Ostopovice vkládají peníze — veřejné zakázky na stavby a vybavení a nákupy pozemků a majetku schválené zastupitelstvem.</p>
  <div class="chips"><span class="chip">obec Ostopovice</span><span class="chip">zakázky {objem/1e6:.0f} mil. Kč</span><span class="chip">zdroj: profil zadavatele · usnesení ZO</span></div>
</header>

<div class="cards" id="kpis"></div>

<div class="callout">
  <b>Jak číst tuto stránku.</b> <b>Kapitálové výdaje</b> jsou to, co obec za investice skutečně zaplatila (účetnictví obce). <b>Veřejné zakázky</b> ukazují, co obec poptala a za kolik to odhadovala — o jejich zadání rozhoduje <b>rada obce a výběrová řízení</b>. Tabulka dole je <b>to, co přímo schválilo zastupitelstvo</b> (úvěry a nákupy pozemků). Čísla se <b>nesčítají</b>: velké stavby (Lipová, chodníky, hřiště, vodní prvek…) v usneseních zastupitelstva nejsou a úvěr je zdroj peněz, ne další výdaj.
</div>

<section>
  <div class="sec-h"><h2>Kapitálové výdaje obce</h2><span class="hint">MONITOR Státní pokladny · skutečnost {kap[0]["rok"]}–{kap[-1]["rok"]}</span></div>
  <div class="panel">
    <div class="chartbox sm"><canvas id="kapChart"></canvas></div>
    <p class="note">Kapitálové výdaje = skutečně zaplacené investice (stavby, rekonstrukce, nákupy pozemků a budov, stroje) podle účetnictví obce. Rok 2025 je výjimečný — <b>dostavba MŠ a ZŠ</b>, financovaná dotací a úvěrem.</p>
  </div>
</section>

<section>
  <div class="sec-h"><h2>Veřejné zakázky podle oblasti a roku</h2><span class="hint">skutečné investice · předpokládané hodnoty</span></div>
  <div class="grid2">
    <div class="panel">
      <div class="sec-h" style="margin:0 0 8px"><h2 style="font-size:16px">Podle oblasti</h2></div>
      <div class="donutwrap"><div class="chartbox sm" style="max-width:320px"><canvas id="catChart"></canvas></div></div>
      <div class="legend" id="catLeg" style="justify-content:center"></div>
    </div>
    <div class="panel">
      <div class="sec-h" style="margin:0 0 8px"><h2 style="font-size:16px">Podle roku</h2></div>
      <div class="chartbox sm"><canvas id="yearChart"></canvas></div>
    </div>
  </div>
  <p class="note">Největší investiční vlna souvisí s <b>dostavbou MŠ a ZŠ</b> — školské zakázky tvoří velkou část objemu (viz sekce <a href="skolstvi.html" style="color:var(--accent)">Školství</a> a <a href="zakazky.html" style="color:var(--accent)">Zakázky</a>).</p>
</section>

<section>
  <div class="sec-h"><h2>Co přímo rozhodlo zastupitelstvo</h2><span class="hint">financování a nákupy pozemků · {len(zo_invest)} rozhodnutí · {objem_poz/1e6:.1f} mil. Kč</span></div>
  <div class="panel">
    <p class="note" style="margin:0 0 10px">Zastupitelstvo rozhoduje přímo hlavně o <b>financování</b> (úvěry na dostavbu školy) a o <b>nákupech pozemků a majetku</b>. Samotnou realizaci staveb zadává rada obce přes veřejné zakázky (nahoře) — tyto částky se proto nesčítají se zakázkami.</p>
    <div style="overflow-x:auto"><table id="pozTab"><thead><tr><th>Rozhodnutí zastupitelstva</th><th>Typ</th><th>Zasedání</th><th style="text-align:right">Částka</th></tr></thead><tbody></tbody></table></div>
  </div>
</section>

<section>
  <div class="panel">
    <p class="note" style="margin:0;font-size:12.5px">Zdroj: profil zadavatele (<a href="https://www.vhodne-uverejneni.cz/profil/obec-ostopovice" target="_blank" rel="noopener" style="color:var(--accent)">vhodne-uverejneni.cz</a>) a usnesení zastupitelstva. Kapitálové výdaje: <b>MONITOR Státní pokladny</b> (výkaz FIN 2-12 M). Zakázky uvádějí předpokládanou hodnotu z výběrového řízení, kapitálové výdaje skutečně zaplacené částky — proto se liší.</p>
  </div>
</section>'''

scripts = '<script>' + CHARTJS + '''</script>
<script>
const D=DATA_JSON, ZAK=D.zak, POZ=D.pozemky, KAP=D.kap;
const nf=new Intl.NumberFormat('cs-CZ');
const mil=v=>(v/1e6).toLocaleString('cs-CZ',{maximumFractionDigits:2});
const kc=v=>v>=1e6?mil(v)+' mil. Kč':nf.format(v)+' Kč';
const PAL=['--c0','--c1','--c2','--c3','--c4','--c5','--c6','--c7'];
const charts={};
function axis(){return {grid:{color:isDark()?'#1f2a40':'#eef2f7'},ticks:{color:cssv('--muted')}};}
function mk(id,cfg){if(charts[id])charts[id].destroy();charts[id]=new Chart(document.getElementById(id),cfg);}

function kpis(){
  const objem=ZAK.reduce((a,z)=>a+z.hodnota,0);
  const skola=ZAK.filter(z=>z.kat==='Škola (MŠ a ZŠ)').reduce((a,z)=>a+z.hodnota,0);
  const objPoz=POZ.reduce((a,p)=>a+p.castka,0);
  const C=[
    ['Objem zakázek', mil(objem)+' mil. Kč', ZAK.length+' zakázek (rada / výběrko)','var(--c0)'],
    ['Do školy (MŠ+ZŠ)', mil(skola)+' mil. Kč', Math.round(skola/objem*100)+' % objemu zakázek','var(--c1)'],
    ['Přímá rozhodnutí ZO', mil(objPoz)+' mil. Kč', POZ.length+'× financování + pozemky','var(--c3)'],
    (()=>{const k=KAP.filter(x=>x.rok>=2022);const s=k.reduce((a,x)=>a+x.kap,0);return ['Kapitálové výdaje '+k[0].rok+'–'+k[k.length-1].rok, mil(s)+' mil. Kč', 'skutečně zaplaceno (MONITOR)','#a855f7'];})(),
  ];
  document.getElementById('kpis').innerHTML=C.map(c=>`<div class="kpi" style="--bar:${c[3]}"><div class="lab">${c[0]}</div><div class="val" style="font-size:21px">${c[1]}</div><div class="delta" style="color:var(--muted)">${c[2]}</div></div>`).join('');
}
function catChart(){
  const by={}; ZAK.forEach(z=>by[z.kat]=(by[z.kat]||0)+z.hodnota);
  const arr=Object.entries(by).sort((a,b)=>b[1]-a[1]);
  mk('catChart',{type:'doughnut',data:{labels:arr.map(e=>e[0]),
    datasets:[{data:arr.map(e=>e[1]),backgroundColor:arr.map((e,i)=>cssv(PAL[i%PAL.length])),borderColor:cssv('--surface'),borderWidth:2,hoverOffset:6}]},
    options:{responsive:true,maintainAspectRatio:false,cutout:'60%',animation:{duration:600},
      plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>c.label+': '+kc(c.parsed)}}}}});
  document.getElementById('catLeg').innerHTML=arr.map((e,i)=>`<span><i class="sw" style="background:${cssv(PAL[i%PAL.length])}"></i>${e[0]} · ${mil(e[1])} mil.</span>`).join('');
}
function yearChart(){
  const by={}; ZAK.forEach(z=>{if(z.rok)by[z.rok]=(by[z.rok]||0)+z.hodnota;});
  const yr=Object.keys(by).sort();
  mk('yearChart',{type:'bar',data:{labels:yr,datasets:[{data:yr.map(y=>by[y]/1e6),backgroundColor:cssv('--c0'),borderRadius:5}]},
    options:{responsive:true,maintainAspectRatio:false,animation:{duration:600},
      plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>mil(by[yr[c.dataIndex]])+' mil. Kč'}}},
      scales:{x:axis(),y:Object.assign(axis(),{ticks:{color:cssv('--muted'),callback:v=>v+' mil.'}})}}});
}
function kapChart(){
  mk('kapChart',{type:'bar',data:{labels:KAP.map(x=>x.rok),datasets:[
    {label:'Kapitálové výdaje',data:KAP.map(x=>x.kap/1e6),backgroundColor:'#a855f7',borderRadius:5},
    {label:'Běžné výdaje',data:KAP.map(x=>(x.vydaje-x.kap)/1e6),backgroundColor:cssv('--c5'),borderRadius:5}]},
    options:{responsive:true,maintainAspectRatio:false,animation:{duration:600},interaction:{mode:'index',intersect:false},
      plugins:{legend:{display:true,labels:{color:cssv('--muted'),boxWidth:12}},tooltip:{callbacks:{label:c=>c.dataset.label+': '+c.parsed.y.toLocaleString('cs-CZ',{maximumFractionDigits:1})+' mil. Kč'}}},
      scales:{x:Object.assign(axis(),{stacked:true}),y:Object.assign(axis(),{stacked:true,ticks:{color:cssv('--muted'),callback:v=>v+' mil.'}})}}});
}
function pozTab(){
  const TCOL={'Financování (úvěr)':'var(--c4)','Pozemek / majetek':'var(--c2)'};
  document.querySelector('#pozTab tbody').innerHTML=POZ.map(p=>`<tr>
    <td>${p.url?`<a href="${p.url}" target="_blank" rel="noopener" style="color:inherit;text-decoration:none">${p.text.length>140?p.text.slice(0,138)+'…':p.text}</a>`:p.text}</td>
    <td style="white-space:nowrap"><span class="pill" style="background:var(--inset);color:${TCOL[p.typ]||'var(--muted)'};border:1px solid var(--line)">${p.typ}</span></td>
    <td style="white-space:nowrap;color:var(--muted)">ZO ${p.zo}</td>
    <td style="text-align:right;font-variant-numeric:tabular-nums"><b>${kc(p.castka)}</b></td></tr>`).join('')
    || '<tr><td colspan="4" class="note">Žádné záznamy.</td></tr>';
}
function render(){kpis();kapChart();catChart();yearChart();pozTab();}
render(); bindTheme(render);
window.addEventListener('load',()=>{Object.values(charts).forEach(c=>{try{c.resize();}catch(e){}});});
</script>'''.replace("DATA_JSON", data_json)

CSS = '''<style>
.callout{background:var(--inset);border:1px solid var(--line);border-left:3px solid var(--accent);border-radius:12px;padding:14px 16px;margin:18px 0 6px;font-size:13px;color:var(--muted);line-height:1.6}
.callout b{color:var(--text)}
.pill{font-size:11px;font-weight:600;padding:2px 9px;border-radius:999px}
#pozTab{width:100%;border-collapse:collapse;font-size:13px}
#pozTab th,#pozTab td{padding:9px 12px;text-align:left;border-bottom:1px solid var(--line);vertical-align:top}
#pozTab thead th{color:var(--muted);font-weight:600;font-size:12px}
#pozTab tbody tr:hover{background:var(--inset)}
</style>'''

open("investice.html", "w", encoding="utf-8").write(
    pc.page("Investice", "Investice — Jak žijí Ostopovice", body, head_scripts=CSS, body_scripts=scripts))
print(f"HOTOVO -> investice.html (zakázky {objem/1e6:.1f} mil., rozhodnutí ZO {len(zo_invest)} / {objem_poz/1e6:.1f} mil.)")
