#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Sekce Investice (investice.html) — kam obec Ostopovice investuje.
Přehled: kapitálové výdaje obce z MONITORu (FIN 2-12 M), veřejné zakázky
(stavby/majetek) kategorizované a přímá investiční rozhodnutí ZO (úvěry, pozemky)."""
import sys, json, re
import portal_common as pc
sys.stdout.reconfigure(encoding="utf-8")

CHARTJS = open("data/vendor/chart.umd.js", encoding="utf-8").read()
LEAFLET_JS = open("data/vendor/leaflet.js", encoding="utf-8").read()
LEAFLET_CSS = open("data/vendor/leaflet.css", encoding="utf-8").read()
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

# --- mapa: poloha akce z čísla parcely, známého místa nebo ulice (jako portál Střelic) ---
# parcely: geocode_parcely.py (ČÚZK); ulice a místa: OpenStreetMap (data/ulice_geo.json, data/mista_geo.json)
def _geo(path):
    try:
        return json.load(open(path, encoding="utf-8"))
    except FileNotFoundError:
        return {}


PGEO, UGEO, MGEO = _geo("data/parcely_geo.json"), _geo("data/ulice_geo.json"), _geo("data/mista_geo.json")
PARC_RE = re.compile(r"(?:p\.\s*č\.|parc\.\s*č\.|pozem\w*\s+(?:p\.\s*č\.\s*)?)\s*(\d{1,5}(?:/\d{1,4})?)", re.I)
MISTA_RE = [(re.compile(r"mateřsk|základní škol|škol|gastro|družin", re.I), "zs"), (re.compile(r"ZŠ|MŠ"), "zs"),
            (re.compile(r"(?<!\w)ZUŠ(?!\w)|uměleck", re.I), "zus"),
            (re.compile(r"obecní\w*\s+úřad", re.I), "ou"), (re.compile(r"knihovn", re.I), "knihovna"),
            (re.compile(r"kostel", re.I), "kostel"), (re.compile(r"pumptrack|cyklistick\w* centr", re.I), "pumptrack"),
            (re.compile(r"sokol|fotbal|sportovní areál", re.I), "sokol")]


def _ulice_rx(nm):
    # skloňování: Lípová/Lipová -> Lipové/Lipovou, Školní -> Školního…, víceslovné názvy bez skloňování
    base = re.escape(nm).replace("í", "[íi]", 1) if nm.startswith("L") else re.escape(nm)
    if nm.endswith("á"):
        return re.compile(r"(?<!\w)" + base[:-1] + r"(á|é|ou)(?!\w)", re.I)
    if nm.endswith("í"):
        return re.compile(r"(?<!\w)" + base + r"(ho|mu|m|ch)?(?!\w)", re.I)
    return re.compile(r"(?<!\w)" + base + r"(?!\w)", re.I)


ULICE_RE = [(_ulice_rx(nm), nm) for nm in sorted(UGEO, key=len, reverse=True)]


SIDLO_RE = re.compile(r"(?:se\s+)?sídlem\s+[^,]+(?:,\s*\d{3}\s?\d{2})?", re.I)   # adresy stran smlouvy


def poloha(text):
    """[lat, lon, presne] — presne=False: akce bez místa, zobrazí se čárkovaně u obecního úřadu."""
    text = SIDLO_RE.sub(" ", text)
    for m in PARC_RE.finditer(text):
        if m.group(1) in PGEO:
            return PGEO[m.group(1)] + [True]
    for rx, k in MISTA_RE:
        if rx.search(text) and k in MGEO:
            return MGEO[k] + [True]
    for rx, nm in ULICE_RE:
        if rx.search(text):
            return UGEO[nm] + [True]
    return MGEO["ou"] + [False] if "ou" in MGEO else None


# [rok, datum, název, částka, kategorie, url, lat, lon, přesně, zdroj]
mapa = []
for z in zak:
    g = poloha(z["nazev"])
    if g:
        mapa.append([z["rok"], z["datum"], z["nazev"], z["hodnota"], z["kat"], z["url"], g[0], g[1], g[2], "zakázka"])
for x in zo_invest:
    if x["typ"] != "Pozemek / majetek":
        continue
    g = poloha(x["text"])
    if g and g[2]:   # pozemek bez dohledatelné parcely na mapu nedáváme
        nazev = x["text"] if len(x["text"]) <= 170 else x["text"][:167].rsplit(" ", 1)[0] + "…"
        mapa.append([x["rok"], "", nazev, x["castka"], "Pozemek / majetek", x["url"], g[0], g[1], True, "ZO " + x["zo"]])

DATA = {"zak": zak, "pozemky": zo_invest, "kap": kap, "mapa": mapa}
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
  <div class="sec-h"><h2>Kapitálové výdaje obce</h2>{pc.mascot_help("Kapitálové výdaje", "<p>Investice jsou kapitálové výdaje: peníze na pořízení nebo zhodnocení majetku obce, třeba stavby, rekonstrukce, pozemky a vybavení. Graf ukazuje skutečně utracené částky v každém roce podle výkazu pro Státní pokladnu.</p>", "06-investice")}<span class="hint">MONITOR Státní pokladny · skutečnost {kap[0]["rok"]}–{kap[-1]["rok"]}</span></div>
  <div class="panel">
    <div class="chartbox sm"><canvas id="kapChart"></canvas></div>
    <p class="note">Kapitálové výdaje = skutečně zaplacené investice (stavby, rekonstrukce, nákupy pozemků a budov, stroje) podle účetnictví obce. Rok 2025 je výjimečný — <b>dostavba MŠ a ZŠ</b>, financovaná dotací a úvěrem.</p>
  </div>
</section>

<section>
  <div class="sec-h"><h2>Mapa investic</h2>{pc.mascot_help("Mapa investic", "<p>Body ukazují, kde obec stavěla, opravovala nebo kupovala pozemky. Velikost bodu odpovídá částce, po kliknutí na bod uvidíte detail. Nahoře vyberete rok.</p><p>Poloha se určuje automaticky z čísla parcely, názvu ulice nebo známého místa (škola, úřad, kostel), takže je přibližná. Zakázky bez takového údaje jsou čárkovaně u obecního úřadu.</p>", "06-investice")}<span class="hint">zakázky a nákupy pozemků · klikni na bod</span></div>
  <div class="ctrls"><span class="lbl">Rok</span><span class="seg" id="mapYrSeg"></span></div>
  <div class="panel" style="padding:10px">
    <div id="map"></div>
    <div class="legend" id="mapLeg" style="margin:10px 4px 0"></div>
    <p class="note" id="mapMiss" style="margin:6px 4px 0"></p>
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
<script>''' + LEAFLET_JS + '''</script>
<script>
const D=DATA_JSON, ZAK=D.zak, POZ=D.pozemky, KAP=D.kap;
const nf=new Intl.NumberFormat('cs-CZ');
const mil=v=>(v/1e6).toLocaleString('cs-CZ',{maximumFractionDigits:2});
const kc=v=>v>=1e6?mil(v)+' mil. Kč':nf.format(v)+' Kč';
const PAL=['--c0','--c1','--c2','--c3','--c4','--c5','--c6','--c7'];
const charts={};
function axis(){return {grid:{color:cssv('--line')},ticks:{color:cssv('--muted')}};}
function mk(id,cfg){if(charts[id])charts[id].destroy();charts[id]=new Chart(document.getElementById(id),cfg);}

function kpis(){
  const objem=ZAK.reduce((a,z)=>a+z.hodnota,0);
  const skola=ZAK.filter(z=>z.kat==='Škola (MŠ a ZŠ)').reduce((a,z)=>a+z.hodnota,0);
  const objPoz=POZ.reduce((a,p)=>a+p.castka,0);
  const C=[
    ['Objem zakázek', mil(objem)+' mil. Kč', ZAK.length+' zakázek (rada / výběrko)','var(--c0)'],
    ['Do školy (MŠ+ZŠ)', mil(skola)+' mil. Kč', Math.round(skola/objem*100)+' % objemu zakázek','var(--c1)'],
    ['Přímá rozhodnutí ZO', mil(objPoz)+' mil. Kč', POZ.length+'× financování + pozemky','var(--c3)'],
    (()=>{const k=KAP.filter(x=>x.rok>=2022);const s=k.reduce((a,x)=>a+x.kap,0);return ['Kapitálové výdaje '+k[0].rok+'–'+k[k.length-1].rok, mil(s)+' mil. Kč', 'skutečně zaplaceno (MONITOR)','var(--amber)'];})(),
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
    {label:'Kapitálové výdaje',data:KAP.map(x=>x.kap/1e6),backgroundColor:cssv('--amber'),borderRadius:5},
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

// ---- mapa investic ----
const MAPA=D.mapa||[], MCAT={};
let map=null, mapLayer=null, mapYear='vse';
function renderMap(){
  if(typeof L==='undefined'||!document.getElementById('map')||!MAPA.length)return;
  if(!map){
    map=L.map('map',{scrollWheelZoom:false});
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:19,attribution:'&copy; přispěvatelé OpenStreetMap'}).addTo(map);
    map.setView([49.1605,16.5440],15);
  }
  if(mapLayer)mapLayer.remove();
  mapLayer=L.layerGroup().addTo(map);
  const cats=[...new Set(MAPA.map(x=>x[4]))].sort(); cats.forEach((c,i)=>{if(!(c in MCAT))MCAT[c]=PAL[i%PAL.length];});
  const seen={}, pts=[], used=new Set(); let fb=0;
  const esc=t=>String(t).replace(/&/g,'&amp;').replace(/</g,'&lt;');
  MAPA.forEach(x=>{
    if(mapYear!=='vse'&&String(x[0])!==mapYear)return;
    const key=x[6]+','+x[7], n=(seen[key]=(seen[key]||0)+1);
    const lat=x[6]+(n>1?Math.cos(n*2.4)*0.00009:0), lon=x[7]+(n>1?Math.sin(n*2.4)*0.00013:0);
    const clr=cssv(MCAT[x[4]]), r=Math.min(24,5+Math.sqrt(x[3]/1e6)*3.4);
    if(!x[8])fb++; used.add(x[4]);
    const pop=`<div class="mpop"><div class="dt">${x[1]||x[0]} · ${esc(x[4])} · ${esc(x[9])}</div><p>${esc(x[2])}</p><div class="amt">${kc(x[3])}</div>`+
      (x[8]?'':'<div class="dt">bez konkrétního místa — zobrazeno u obecního úřadu</div>')+
      (x[5]?`<p><a href="${x[5]}" target="_blank" rel="noopener" style="color:var(--accent)">detail ↗</a></p>`:'')+'</div>';
    L.circleMarker([lat,lon],{radius:r,color:clr,weight:1.6,fillColor:clr,fillOpacity:x[8]?.5:.2,dashArray:x[8]?null:'4 4'}).bindPopup(pop).addTo(mapLayer);
    pts.push([lat,lon]);
  });
  if(pts.length)map.fitBounds(pts,{padding:[28,28],maxZoom:16});
  document.getElementById('mapLeg').innerHTML=[...used].sort().map(c=>`<span><i class="sw" style="background:${cssv(MCAT[c])}"></i>${c}</span>`).join('');
  document.getElementById('mapMiss').textContent=fb?`${fb} zakázek bez konkrétního místa (vybavení, služby, akce po celé obci) je zobrazeno čárkovaně u obecního úřadu.`:'';
}
(function(){const yrs=[...new Set(MAPA.map(x=>String(x[0])))].sort();
  const sg=document.getElementById('mapYrSeg'); if(!sg)return;
  sg.innerHTML='<button class="on" data-y="vse">Vše</button>'+yrs.map(y=>`<button data-y="${y}">${y}</button>`).join('');
  sg.querySelectorAll('button').forEach(b=>b.onclick=()=>{sg.querySelectorAll('button').forEach(x=>x.classList.toggle('on',x===b));mapYear=b.dataset.y;renderMap();});})();
function render(){kpis();kapChart();catChart();yearChart();pozTab();renderMap();}
render(); bindTheme(render);
window.addEventListener('load',()=>{Object.values(charts).forEach(c=>{try{c.resize();}catch(e){}});});
</script>'''.replace("DATA_JSON", data_json)

CSS = '''<style>''' + LEAFLET_CSS + '''
#map{height:440px;border-radius:12px;z-index:0}
.leaflet-tile-pane{filter:grayscale(.92) contrast(.92) brightness(1.04)}
html[data-theme="dark"] .leaflet-tile-pane{filter:grayscale(.5) brightness(.6) invert(1) contrast(3.2) hue-rotate(200deg) saturate(.1) brightness(.75)}
html[data-theme="dark"] .leaflet-container{background:#0d1424}
.leaflet-container{font-family:inherit}
.leaflet-popup-content-wrapper,.leaflet-popup-tip{background:var(--surface);color:var(--text);box-shadow:var(--shadow-h)}
.leaflet-popup-content{font-size:12.5px;line-height:1.5;margin:12px 14px;max-width:270px}
.mpop .dt{font-size:11.5px;color:var(--muted)}
.mpop p{margin:5px 0}
.mpop .amt{font-weight:700}
.legend .sw{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:5px;vertical-align:middle}
.legend span{margin-right:12px;font-size:12px;color:var(--muted)}
@media(max-width:640px){#map{height:340px}}
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
