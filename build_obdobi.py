#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bilance volebního období 2022–2026 (obdobi.html).

Zdroje: zápisy ZO (dataset_ZO.json — usnesení, hlasování, docházka),
MONITOR SP (rozpočet), profil zadavatele (zakázky), usnesení ZO (dotace),
volby.cz (složení zastupitelstva). Ostopovice zveřejňují u hlasování jen
počty (pro/proti/zdržel se), ne jména — aktivita zastupitelů proto = docházka."""
import sys, json, re, unicodedata
from collections import Counter
import portal_common as pc
sys.stdout.reconfigure(encoding="utf-8")

CHARTJS = open("data/vendor/chart.umd.js", encoding="utf-8").read()
ZO = json.load(open("dataset_ZO.json", encoding="utf-8"))
ROZ = json.load(open("data/rozpocet_ostopovice.json", encoding="utf-8"))
ZAK = json.load(open("data/zakazky.json", encoding="utf-8"))
DOT = json.load(open("data/dotace.json", encoding="utf-8"))
VOL = json.load(open("data/volby/ostopovice_volby.json", encoding="utf-8"))["komunalni"]

START = "2022-10-20"          # ustavující zasedání
FORMAL = "Jednání a formality"


def mil(v):
    return f"{v/1e6:.1f}".replace(".", ",")


def fold(s):
    return "".join(c for c in unicodedata.normalize("NFD", s or "") if unicodedata.category(c) != "Mn").lower()


def esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def zkey(m):
    return f"{m['rok']}-{m['cislo_zasedani']}"


def zlab(m):
    return "ustavující" if m["cislo_zasedani"] == 0 else f"{m['cislo_zasedani']}/{m['rok']}"


meets = sorted([m for m in ZO if (m.get("datum") or "") >= START], key=lambda m: m["datum"])
n_meet = len(meets)
n_items = sum(len(m["body"]) for m in meets)

# ---------- hospodaření ----------
def skut(rok, cast, name):
    for x in ROZ["struktura"][str(rok)][cast]:
        if x["name"] == name:
            return x["skut"]
    return 0

Y = {y["rok"]: y for y in ROZ["years"]}
hosp = []
for r in (2022, 2023, 2024, 2025):
    hosp.append({"y": r, "pr": Y[r]["prijmy"]["skut"], "vy": Y[r]["vydaje"]["skut"],
                 "kap": skut(r, "vydaje_druh", "Kapitálové výdaje"), "plan": False})
A = ROZ["aktualni"]
kap26 = next(x for x in A["vydaje_druh"] if x["name"] == "Kapitálové výdaje")
hosp.append({"y": A["rok"], "pr": A["prijmy"]["uprav"], "vy": A["vydaje"]["uprav"], "kap": kap26["uprav"], "plan": True})
pr_done = sum(h["pr"] for h in hosp[:4])
vy_done = sum(h["vy"] for h in hosp[:4])
kap_done = sum(h["kap"] for h in hosp[:4])

# ---------- hlasování ----------
votes, contested = [], []
for m in meets:
    for b in m["body"]:
        h = b.get("hlasovani") or [None]
        # bez procedurálních bodů a voleb do funkcí (zvolený se obvykle zdrží)
        if h[0] is None or b.get("tema") == FORMAL or b.get("kategorie") == "volí":
            continue
        votes.append(b)
        if h[1] or h[2]:
            contested.append({"zo": zkey(m), "lab": zlab(m), "datum": m["datum_text"], "cnt": h,
                              "text": b["text"].replace("Zastupitelstvo obce Ostopovice ", "")})
n_unan = len(votes) - len(contested)

tema = Counter(b["tema"] for m in meets for b in m["body"] if b.get("tema") and b["tema"] != FORMAL)
tema = [[t, c] for t, c in tema.most_common()]

# ---------- docházka ----------
TIT = re.compile(r"\b(?:doc|MVDr|MgA|Mgr|Ing|arch|Bc|Ph\.D|PhDr|JUDr|RNDr)\.?\s*,?", re.I)
members = []
for z in VOL["zastupitele"]:
    name = re.sub(r"\s+", " ", TIT.sub("", z["jmeno"])).strip(" ,.")
    members.append({"key": fold(name.split()[-1]), "name": name, "strana": z["strana"], "pritomen": 0, "mozno": 0})
assert len({m["key"] for m in members}) == len(members), "duplicitní příjmení"


def who(entry):
    w = re.findall(r"[a-z]+", fold(entry))
    hit = [m["key"] for m in members if m["key"] in w]
    return hit[0] if hit else None


att = []
unmatched = []
for m in meets:
    om = []
    for e in m.get("omluveni") or []:
        k = who(e)
        (om.append(k) if k else unmatched.append((zlab(m), e)))
    att.append({"zo": zkey(m), "lab": zlab(m), "datum": m["datum_text"], "omluveni": om})
    for mb in members:
        mb["mozno"] += 1
        if mb["key"] not in om:
            mb["pritomen"] += 1
if unmatched:
    print("POZOR — nespárovaní omluvení:", unmatched)
avg_ucast = sum(mb["pritomen"] for mb in members) / sum(mb["mozno"] for mb in members) * 100

# ---------- největší akce (zakázky) ----------
def druh(n):
    n = n.lower()
    if re.search(r"úvěr", n): return "úvěr"
    if re.search(r"svoz|tds|technick\w* dozor|služ|projektov\w* dokumentac|zpracování|zajištění", n): return "služba"
    return "akce"

def zrok(d):
    m = re.search(r"(\d{4})", d or "")
    return int(m.group(1)) if m else 0

def ziso(d):
    m = re.match(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", (d or "").replace(" ", ""))
    return f"{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}" if m else ""

akce = [z for z in ZAK if z.get("hodnota") and druh(z["nazev"]) == "akce" and ziso(z["datum"]) >= START]
akce.sort(key=lambda z: -z["hodnota"])
top_akce = akce[:12]

dot_p = [d for d in DOT if (d.get("rok") or 0) >= 2022]
dot_by = Counter()
for d in dot_p:
    dot_by[d["prijemce"]] += d["castka"]
top_dot = dot_by.most_common(6)

# ---------- časová osa (výběr ze shrnutí zasedání) ----------
TIMELINE = [
    ("2022-10-20", "Ustavující zasedání", "Zvoleni starosta, místostarosta a rada; obě vrcholné funkce jako uvolněné (8 : 6 : 1)."),
    ("2022-12-15", "Rozpočet 2023 a nákup pozemků", "Schválen rozpočet 2023, výkup pozemků za 5,1 mil. Kč a vstup do energetického společenství ENERKOM Bobrava."),
    ("2023-06-29", "Změna č. 2 územního plánu", "Zastupitelstvo rozhodlo o pořízení změny č. 2 územního plánu."),
    ("2024-11-14", "Úvěr 105 mil. Kč na dostavbu školy", "Úvěr u Komerční banky (3,15 %, splatnost do roku 2039) na předfinancování dotace na dostavbu MŠ a ZŠ; zároveň rozhodnuto o konci kabelové televize k 31. 12. 2025."),
    ("2025-05-22", "Most a bezpečnost", "Dar 150 tis. Kč MAS Bobrava na most a smlouva o výkonu městské policie Modřice."),
    ("2025-10-16", "Územní plán a další úvěr", "Vydána změna 2A územního plánu; schválen úvěr 16 mil. Kč na dofinancování dostavby MŠ a ZŠ (10 : 1 : 0)."),
    ("2025-12-18", "Fond obnovy vodovodu a kanalizace", "Zrušena hospodářská činnost obce, zřízen fond obnovy vodovodu a kanalizace."),
    ("2026-03-12", "Změna v radě obce", "Po rezignaci jednoho radního zvolen nový člen rady."),
]
date2key = {m["datum"]: zkey(m) for m in meets}
date2lab = {m["datum"]: zlab(m) for m in meets}
for d, *_ in TIMELINE:
    assert d in date2key, f"časová osa: zasedání {d} není v datasetu"

# ---------- HTML ----------
akce_rows = "".join(
    f'<tr><td class="num">{mil(a["hodnota"])}</td><td><a href="{esc(a["url"])}" target="_blank" rel="noopener"><b>{esc(a["nazev"])}</b></a></td>'
    f'<td class="nw">{esc(a["datum"])}</td></tr>' for a in top_akce)
dot_rows = "".join(f'<tr><td>{esc(p)}</td><td class="num">{mil(v)}</td></tr>' for p, v in top_dot)
tl_html = "".join(
    f'<div class="tl"><div class="tld">{d[8:10].lstrip("0")}. {d[5:7].lstrip("0")}. {d[:4]}</div>'
    f'<div class="tlb"><b>{esc(t)}</b><p>{esc(x)}</p><a href="zastupitelstvo.html?zo={date2key[d]}">ZO {date2lab[d]} →</a></div></div>'
    for d, t, x in TIMELINE)

unan = n_unan / len(votes) * 100
mon26 = A["mesic"]
DATA = {"hosp": hosp, "tema": tema, "members": members, "att": att, "contested": contested}
data_json = json.dumps(DATA, ensure_ascii=False, separators=(",", ":"))

body = f'''<header class="hero">
  <h1>Volební období 2022–2026 v datech</h1>
  <p>Co zastupitelstvo za čtyři roky rozhodlo, kolik obec vybrala, utratila a proinvestovala, a jak se zastupitelé účastnili zasedání. Jen fakta z veřejných zdrojů — bez hodnocení.</p>
  <div class="chips"><span class="chip">říjen 2022 – září 2026</span><span class="chip">zdroje: zápisy ZO · MONITOR SP · profil zadavatele</span></div>
  <nav class="jump"><a href="#bilance">Bilance období</a><a href="#osa">Časová osa</a><a href="#zastupitele">Zastupitelé</a></nav>
</header>

<div class="cards">
  <div class="kpi"><div class="lab">Zasedání zastupitelstva</div><div class="val">{n_meet}</div><div class="delta" style="color:var(--muted)">{n_items} usnesení</div></div>
  <div class="kpi" style="--bar:#16a34a"><div class="lab">Jednomyslná hlasování</div><div class="val">{unan:.0f} %</div><div class="delta" style="color:var(--muted)">{n_unan} z {len(votes)} věcných hlasování</div></div>
  <div class="kpi" style="--bar:#a855f7"><div class="lab">Investice 2022–2025</div><div class="val">{mil(kap_done)} <span style="font-size:14px;color:var(--muted)">mil. Kč</span></div><div class="delta" style="color:var(--muted)">kapitálové výdaje, skutečnost</div></div>
  <div class="kpi" style="--bar:#e11d48"><div class="lab">Nové úvěry</div><div class="val">121 <span style="font-size:14px;color:var(--muted)">mil. Kč</span></div><div class="delta" style="color:var(--muted)">105 mil. (2024) + 16 mil. (2025)</div></div>
</div>

<section id="bilance">
  <div class="sec-h"><h2>Hospodaření obce v období</h2><span class="hint">mil. Kč · 2022–2025 skutečnost, 2026 upravený rozpočet</span></div>
  <div class="panel">
    <div class="chartbox"><canvas id="hospCh"></canvas></div>
    <p class="note">V letech 2022–2025 obec vybrala celkem <b>{mil(pr_done)} mil. Kč</b> a utratila <b>{mil(vy_done)} mil. Kč</b>, z toho <b>{mil(kap_done)} mil. Kč</b> na investice — nejvíc v roce 2025 na dostavbu mateřské a základní školy.
    Rozdíl pokryly úspory minulých let a úvěry na dostavbu školy (105 mil. Kč na předfinancování dotace, schválený v listopadu 2024, a 16 mil. Kč na dofinancování v říjnu 2025).
    Rok 2026 je zobrazen podle upraveného rozpočtu (plán); skutečně zaplacené investice k {mon26} činily {mil(kap26["skut"])} mil. Kč. Detail v sekci <a href="rozpocet.html">Rozpočet</a>.</p>
  </div>
</section>

<section>
  <div class="sec-h"><h2>Největší zakázky období</h2><span class="hint">stavby a dodávky podle předpokládané hodnoty bez DPH · mil. Kč</span></div>
  <div class="panel tblp"><table class="t"><thead><tr><th class="num">mil. Kč</th><th>Zakázka</th><th>Uveřejněno</th></tr></thead><tbody>{akce_rows}</tbody></table>
  <p class="note">Zdroj: profil zadavatele obce. Bez výběru úvěru a služeb (svoz odpadu, technický dozor, projekty). Všechny zakázky v sekci <a href="zakazky.html">Zakázky</a>, investice podle let v sekci <a href="investice.html">Investice</a>.</p></div>
</section>

<section>
  <div class="grid2">
    <div><div class="sec-h"><h2>O čem se rozhodovalo</h2><span class="hint">usnesení ZO podle tématu</span></div>
      <div class="panel"><div class="chartbox sm"><canvas id="temaCh"></canvas></div>
      <p class="note">Bez formálních bodů (program, ověřovatelé, volby do funkcí). Témata přiřazena automaticky podle textu.</p></div></div>
    <div><div class="sec-h"><h2>Největší příjemci dotací a darů</h2><span class="hint">2022–2026 · mil. Kč</span></div>
      <div class="panel tblp"><table class="t"><thead><tr><th>Příjemce</th><th class="num">mil. Kč</th></tr></thead><tbody>{dot_rows}</tbody></table>
      <p class="note">Podle usnesení zastupitelstva. Všechny příspěvky v sekci <a href="dotace.html">Dotace spolkům</a>.</p></div></div>
  </div>
</section>

<section id="osa">
  <div class="sec-h"><h2>Časová osa klíčových rozhodnutí</h2><span class="hint">výběr největších a dlouhodobých rozhodnutí zastupitelstva</span></div>
  <div class="panel"><div class="tlw">{tl_html}</div>
  <p class="note">Výběr podle výše částky a dlouhodobého dopadu. Všechna zasedání se shrnutím najdete v sekci <a href="zastupitelstvo.html">Zastupitelstvo</a>.</p></div>
</section>

<section id="zastupitele">
  <div class="sec-h"><h2>Zastupitelé: účast na zasedáních</h2><span class="hint">{n_meet} zasedání · průměrná účast {avg_ucast:.0f} %</span></div>
  <div class="panel expl">
    <p><b>Co tabulka ukazuje.</b> Účast = na kolika zasedáních zastupitelstva byl zastupitel přítomen, podle seznamu omluvených v zápisu. Kdo přišel se zpožděním, je počítán jako přítomný.
    Zápisy obce Ostopovice uvádějí u hlasování jen <b>počty</b> hlasů (pro / proti / zdržel se), ne jména — jak hlasovali jednotliví zastupitelé, proto z veřejných podkladů zjistit nejde.</p>
    <p class="note" style="margin-top:6px">Aktivita zastupitele se neodráží jen v docházce — velká část práce probíhá ve výborech, komisích a mimo zasedání. Zastupitelé jsou seřazeni podle kandidátních listin, ne podle účasti.</p>
  </div>
  <div class="panel tblp" style="margin-top:14px"><div class="tscroll"><table class="t zt" id="zt"><thead><tr><th>Zastupitel</th><th>Zvolen(a) za</th><th>Účast</th></tr></thead><tbody>{pc.skel_tr(10, 3) if hasattr(pc, "skel_tr") else ""}</tbody></table></div></div>
</section>

<section>
  <div class="sec-h"><h2>Docházka po zasedáních</h2><span class="hint">● přítomen · ○ omluven</span></div>
  <div class="panel tblp"><div class="tscroll"><table class="att" id="att"></table></div></div>
</section>

<section>
  <div class="sec-h"><h2>Nejednomyslná hlasování</h2><span class="hint">{len(contested)} věcných hlasování, kde někdo hlasoval proti nebo se zdržel</span></div>
  <div class="panel tblp"><table class="t"><thead><tr><th>Zasedání</th><th>Usnesení</th><th class="num">pro : proti : zdržel</th></tr></thead><tbody id="cont"></tbody></table></div>
</section>'''

CSS = '''<style>
.jump{display:flex;gap:8px;flex-wrap:wrap;margin-top:14px}
.jump a{font-size:13px;padding:6px 13px;border-radius:10px;background:var(--accent-soft);color:var(--accent);text-decoration:none;font-weight:600}
.t{width:100%;border-collapse:collapse;font-size:13.5px}
.t th{text-align:left;font-size:12px;color:var(--muted);font-weight:600;padding:8px 10px;border-bottom:1px solid var(--line);white-space:nowrap}
.t td{padding:9px 10px;border-bottom:1px solid var(--line);vertical-align:top}
.t tr:last-child td{border-bottom:0}
.t td small{color:var(--muted)}
.t a{color:var(--accent);text-decoration:none}
.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.nw{white-space:nowrap}
.tblp{padding:10px 12px;overflow-x:auto}
@media(max-width:560px){.t{font-size:12.5px}.t td,.t th{padding:7px 6px}}
.tscroll{overflow-x:auto}
.zt td{vertical-align:middle}
.bar{display:inline-block;height:7px;border-radius:4px;background:var(--accent);vertical-align:middle;margin-right:6px}
.att{border-collapse:separate;border-spacing:2px;font-size:12px}
.att th{font-weight:600;color:var(--muted);padding:2px 4px;white-space:nowrap}
.att th.v{writing-mode:vertical-rl;transform:rotate(180deg);font-weight:500;font-size:11px;height:74px}
.att td{text-align:center;width:22px;height:20px;border-radius:4px}
.att td.p{background:var(--pos);color:#fff}.att td.o{background:var(--inset);color:var(--neg);font-weight:700}
.att td.nm{text-align:left;width:auto;white-space:nowrap;padding-right:8px}
.att td.sum{width:auto;padding-left:8px;color:var(--muted);white-space:nowrap}
.att tr.sep td{height:6px;background:none}
.tlw{position:relative;margin-left:8px;border-left:2px solid var(--line);padding-left:18px}
.tl{position:relative;display:grid;grid-template-columns:100px 1fr;gap:12px;padding:8px 0}
.tl::before{content:"";position:absolute;left:-25px;top:14px;width:10px;height:10px;border-radius:50%;background:var(--accent)}
.tld{font-size:12.5px;color:var(--muted);font-variant-numeric:tabular-nums;padding-top:2px}
.tlb p{margin:3px 0 4px;color:var(--muted);font-size:13.5px;line-height:1.5}
.tlb a{font-size:12px;color:var(--accent);text-decoration:none}
.note a{color:var(--accent)}
.expl p{margin:0;font-size:13.5px;line-height:1.6;color:var(--text)}
@media(max-width:560px){.tl{grid-template-columns:1fr;gap:2px}}
</style>'''

JS = '<script>' + CHARTJS + '''</script>
<script>
const D=DATA_JSON, M=D.members;
/*TEMAJS*/
const esc=s=>String(s==null?'':s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
let charts={};
function mk(id,cfg){if(charts[id])charts[id].destroy();charts[id]=new Chart(document.getElementById(id),cfg);}
function axis(){return {grid:{color:isDark()?'#1f2a40':'#eef2f7'},ticks:{color:cssv('--muted')}};}
function drawCharts(){
  const H=D.hosp;
  mk('hospCh',{type:'bar',data:{labels:H.map(h=>h.y+(h.plan?' (plán)':'')),datasets:[
    {label:'Příjmy',data:H.map(h=>h.pr/1e6),backgroundColor:H.map(h=>h.plan?'rgba(127,183,164,.38)':'#7fb7a4')},
    {label:'Výdaje celkem',data:H.map(h=>h.vy/1e6),backgroundColor:H.map(h=>h.plan?'rgba(224,168,120,.38)':'#e0a878')},
    {label:'z toho investice',data:H.map(h=>h.kap/1e6),backgroundColor:H.map(h=>h.plan?'rgba(169,155,209,.38)':'#a99bd1')}]},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{labels:{color:cssv('--muted')}},
      tooltip:{callbacks:{label:c=>c.dataset.label+': '+c.parsed.y.toLocaleString('cs-CZ',{maximumFractionDigits:1})+' mil. Kč'}}},
      scales:{x:axis(),y:Object.assign(axis(),{beginAtZero:true})}}});
  const T=D.tema;
  mk('temaCh',{type:'bar',data:{labels:T.map(t=>(TICO[t[0]]||'')+' '+t[0]),datasets:[{data:T.map(t=>t[1]),backgroundColor:T.map(t=>temaRGB(t[0])),borderRadius:4}]},
    options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}},
      scales:{x:axis(),y:Object.assign(axis(),{grid:{display:false}})}}});
}
document.querySelector('#zt tbody').innerHTML=M.map(m=>`<tr><td><b>${esc(m.name)}</b></td><td><small>${esc(m.strana)}</small></td>`+
  `<td class="nw"><span class="bar" style="width:${Math.round(m.pritomen/m.mozno*60)}px"></span>${m.pritomen}/${m.mozno} <small>(${Math.round(m.pritomen/m.mozno*100)} %)</small></td></tr>`).join('');
(function(){
  const MT=D.att;
  let h='<tr><th></th>'+MT.map(t=>`<th class="v" title="${esc(t.datum)}">${t.lab==='ustavující'?'ustav.':'ZO '+t.lab}</th>`).join('')+'<th></th></tr>';
  let last=null;
  for(const m of M){
    if(last!==null&&m.strana!==last)h+='<tr class="sep"><td></td></tr>';
    last=m.strana;
    h+=`<tr><td class="nm">${esc(m.name)}</td>`+MT.map(t=>t.omluveni.includes(m.key)
      ?`<td class="o" title="ZO ${t.lab} · ${esc(t.datum)} · omluven">○</td>`
      :`<td class="p" title="ZO ${t.lab} · ${esc(t.datum)} · přítomen">●</td>`).join('')+`<td class="sum">${m.pritomen}/${m.mozno}</td></tr>`;
  }
  document.getElementById('att').innerHTML=h;
})();
document.getElementById('cont').innerHTML=D.contested.slice().reverse().map(v=>`<tr><td class="nw"><a href="zastupitelstvo.html?zo=${v.zo}">ZO ${esc(v.lab)}</a><br><small>${esc(v.datum)}</small></td>`+
  `<td>${esc(v.text.slice(0,260))}${v.text.length>260?'…':''}</td><td class="num">${v.cnt.join(' : ')}</td></tr>`).join('');
drawCharts(); bindTheme(drawCharts);
</script>'''.replace("DATA_JSON", data_json).replace("/*TEMAJS*/", pc.TEMA_JS)

html = pc.page("Bilance", "Volební období 2022–2026 — Jak žijí Ostopovice", body, head_scripts=CSS, body_scripts=JS)
open("obdobi.html", "w", encoding="utf-8").write(html)
print(f"HOTOVO: obdobi.html ({len(html)//1024} kB) — {n_meet} zasedání, {len(votes)} věcných hlasování, "
      f"{len(contested)} nejednomyslných, účast {avg_ucast:.0f} %, {len(top_akce)} akcí")
