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

# --- detail paragraf × položka z otevřených dat MONITORu (build_fin.py, build_fin2026.py) ---
# Konsolidace jako souhrny MONITORu: bez převodů mezi vlastními účty obce (příjmy pol. 4134,
# výdaje § 6330) — součty pak sedí na korunu s API (ověřeno 2013–2025).
import csv


def _num(v):
    v = (v or "").strip()
    return -float(v[:-1]) if v.endswith("-") else float(v or 0)


DET = {"rows": [], "pol": {}, "par": {}, "years": [], "ytd": None}
_ytd_month = None
for fn in ("data/ostopovice_finm201_2013_2025.csv", "data/ostopovice_fin_2026.csv"):
    try:
        f = open(fn, encoding="utf-8-sig")
    except FileNotFoundError:
        continue
    for r in csv.DictReader(f, delimiter=";"):
        if r["polozka"] == "4134" or (r["druh"] == "Výdaje" and r["paragraf"] == "6330"):
            continue
        if r.get("obdobi"):
            _ytd_month = int(r["obdobi"])
        DET["rows"].append([int(r["rok"]), r["paragraf"], r["polozka"], round(_num(r["schvaleny_rozpocet"])),
                            round(_num(r["upraveny_rozpocet"])), round(_num(r["skutecnost"]))])
        DET["pol"][r["polozka"]] = {"n": r["polozka_nazev"], "d": r["druh"], "t": r["trida"], "s": r["seskupeni"]}
        DET["par"][r["paragraf"]] = {"n": r["paragraf_nazev"], "o": r["par_oddil"]}
DET["years"] = sorted({r[0] for r in DET["rows"]})
if _ytd_month:
    DET["ytd"] = [max(DET["years"]), _ytd_month]
try:
    SML = json.load(open("data/smlouvy_obec.json", encoding="utf-8"))
except FileNotFoundError:
    SML = []
_sml_dot = [x for x in SML if x["dotace"] and x["hodnota"]]


def _sml_row(x):
    d = x["datum"]
    dt = f"{int(d[8:10])}. {int(d[5:7])}. {d[:4]}" if d else ""
    hod = f'{x["hodnota"]:,} Kč'.replace(",", "\u00a0") if x["hodnota"] else "neuvedeno"
    tag = '<span class="smtag">dotace</span>' if x["dotace"] else ""
    return (f'<tr><td class="dt">{dt}</td><td>{tag}{x["nazev"]}<div class="sub">{x["partner"]}</div></td>'
            f'<td class="r">{hod}</td><td><a href="{x["url"]}" target="_blank" rel="noopener">registr&nbsp;&#8599;</a></td></tr>')


SMLOUVY_HTML = ""
if SML:
    SMLOUVY_HTML = ('''<section id="smlouvy">
  <div class="sec-h"><h2>Získané dotace a smlouvy s obcí</h2><span class="hint">registr smluv · smlouvy, kde je obec protistranou</span></div>
  <div class="panel">
    <p class="note" style="margin:0 0 10px">Smlouvy, které s obcí uzavřely státní fondy, kraj a další instituce a zveřejnily je v registru smluv — hlavně <b>dotace, které obec získala</b>, a dohody o spolufinancování. ''' + (f"Dotace s uvedenou částkou: <b>{len(_sml_dot)}</b> smluv za <b>{sum(x['hodnota'] for x in _sml_dot)/1e6:.1f} mil. Kč</b>.".replace(".", ",", 1) if _sml_dot else "") + ''' Sama obec do registru smlouvy nezveřejňuje, takže tu nejsou smlouvy s dodavateli.</p>
    <div style="overflow-x:auto"><table class="smtab"><thead><tr><th>Uzavřeno</th><th>Smlouva</th><th class="r">Hodnota</th><th></th></tr></thead><tbody>'''
        + "".join(_sml_row(x) for x in SML) + '''</tbody></table></div>
  </div>
</section>

''')
SMLOUVY_CSS = ".smtab{width:100%;border-collapse:collapse;font-size:13px}.smtab th,.smtab td{padding:8px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}.smtab th{color:var(--muted);font-size:12px;font-weight:600}.smtab .r{text-align:right;white-space:nowrap;font-variant-numeric:tabular-nums}.smtab .dt{white-space:nowrap;color:var(--muted)}.smtab .sub{font-size:11.5px;color:var(--faint);margin-top:2px}.smtab a{color:var(--accent);font-size:12px;white-space:nowrap}.smtag{display:inline-block;font-size:10.5px;font-weight:600;padding:1px 7px;border-radius:999px;margin-right:6px;color:var(--c0);background:color-mix(in srgb,var(--c0) 12%,transparent)}"

MESICE_2 = ["leden", "únor", "březen", "duben", "květen", "červen", "červenec", "srpen", "září", "říjen", "listopad", "prosinec"]
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

SANKEY_HTML = """<section id="tok"><div class="sec-h"><h2>Tok peněz</h2>""" + pc.mascot_help("Tok peněz", "<p>Pásy vedou zleva od zdrojů příjmů doprava k oblastem, kam peníze šly. Čím širší pás, tím víc peněz. Po najetí na pás uvidíte přesnou částku. Graf ukazuje skutečnost za poslední uzavřený rok.</p>", "02-rozpocet") + """<span class="hint">odkud obec peníze má a kam jdou · skutečnost · najeďte na pás pro detail</span></div>
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


DET_YTD = (f"Rok {DET['ytd'][0]} je průběžný stav ({MESICE_2[DET['ytd'][1] - 1]}); schválený a upravený rozpočet jsou za celý rok."
           if DET["ytd"] else "")

MH_TREND = pc.mascot_help("Vývoj příjmů, výdajů a salda", "<p>Graf ukazuje, kolik obec v každém roce vybrala a utratila. Saldo je rozdíl příjmů a výdajů: přebytek znamená, že obec vybrala víc, než utratila, schodek se hradí z úspor z minulých let nebo úvěrem.</p><p>Přepínač nahoře volí <b>skutečnost</b>, <b>schválený</b> rozpočet ze začátku roku, nebo <b>upravený</b> rozpočet po změnách během roku.</p>", "02-rozpocet")
MH_PRIJMY = pc.mascot_help("Struktura příjmů", "<p>Příjmy obce za poslední uzavřený rok rozdělené podle druhu tak, jak je člení rozpočtová skladba: daně, poplatky a pronájmy, prodej majetku a dotace (transfery).</p>", "02-rozpocet")
MH_VYDAJE = pc.mascot_help("Kam tečou výdaje", "<p>Výdaje obce podle oblasti, na kterou šly, například školství, doprava nebo bydlení a komunální služby. Jsou to skutečně utracené peníze podle výkazu pro Státní pokladnu.</p>", "02-rozpocet")
MH_DETAIL = pc.mascot_help("Detail rozpočtu", "<p>Tabulka se všemi položkami rozpočtu. Vyberte rok (nebo souhrn všech let) a stranu výdajů či příjmů. Kliknutím na záhlaví sloupce řadíte, políčkem hledáte položku nebo oblast a kliknutím na řádek oblasti či třídy ji rozbalíte na konkrétní položky.</p>", "02-rozpocet")

body = f'''<header class="hero">
  <h1>Rozpočet obce <span style="font-size:17px;font-weight:500;color:var(--muted)">· jak obec hospodaří</span></h1>
  <p>Příjmy, výdaje a saldo obce Ostopovice v čase a jejich struktura — podle výkazu FIN 2-12 M ze systému MONITOR Státní pokladny ({years[0]["rok"]}–{LY}). Dole <a href="#detail" style="color:var(--accent)">detail</a> až na jednotlivé paragrafy a položky.</p>
  <div class="chips"><span class="chip">obec Ostopovice · IČO {D["ic"]}</span><span class="chip">{years[0]["rok"]}–{LY}</span><span class="chip">zdroj: MONITOR Státní pokladny</span></div>
</header>

<div class="cards" id="kpis"></div>

{KOSTKA}

<section>
  <div class="sec-h"><h2>Vývoj příjmů, výdajů a salda</h2>{MH_TREND}<span class="hint">{years[0]["rok"]}–{LY} · roční stav</span></div>
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
      <div class="sec-h" style="margin:0 0 8px"><h2 style="font-size:16px">Struktura příjmů {LY}</h2>{MH_PRIJMY}</div>
      <div class="donutwrap"><div class="chartbox sm" style="max-width:320px"><canvas id="prijmy"></canvas></div>
        <div class="donut-center"><div class="t">příjmy {LY}</div><div class="v">{mil(last["prijmy"]["skut"])}</div></div></div>
      <div class="legend" id="prijmyLeg" style="justify-content:center"></div>
    </div>
    <div class="panel">
      <div class="sec-h" style="margin:0 0 8px"><h2 style="font-size:16px">Kam tečou výdaje {LY}</h2>{MH_VYDAJE}<span class="hint">podle oblasti</span></div>
      <div class="chartbox sm"><canvas id="vydaje"></canvas></div>
    </div>
  </div>
</section>

{SMLOUVY_HTML}<section id="detail">
  <div class="sec-h"><h2>Detail — rozklikni rozpočet</h2>{MH_DETAIL}<span class="hint">řaď, hledej, rozbaluj · paragrafy a položky</span></div>
  <div class="panel">
    <div class="ctrls">
      <span><span class="lbl">Rok</span><select id="dYear"></select></span>
      <span class="seg" id="sideSeg"><button class="on" data-s="Výdaje">Výdaje</button><button data-s="Příjmy">Příjmy</button></span>
      <span><span class="lbl">Seskupit</span>
        <select id="dGroup">
          <option value="o">dle oblasti (na co)</option>
          <option value="t">dle třídy (běžné/kapitál/transfery)</option>
          <option value="s">dle seskupení položek</option>
          <option value="pol">dle konkrétní položky</option>
        </select></span>
    </div>
    <div class="tbar">
      <span class="search"><i>⌕</i><input type="text" id="dSearch" placeholder="hledat položku / oblast…"></span>
      <button class="dlbtn" id="dlDrill" type="button" title="Stáhnout aktuální pohled tabulky jako CSV">⬇ Stáhnout CSV</button>
    </div>
    <div class="tablewrap"><table id="drill"><thead></thead><tbody></tbody></table></div>
    <p class="note">Klik na řádek (u oblasti nebo třídy) rozbalí konkrétní položky. „% plnění“ = skutečnost ÷ upravený rozpočet. Detail je z otevřených dat výkazu FIN 2-12 M; převody mezi vlastními účty obce jsou vynechané stejně jako v souhrnech výše, takže součty sedí. {DET_YTD}</p>
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
function axis(){return {grid:{color:cssv('--line')},ticks:{color:cssv('--muted')}};}
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
    ['Kapitálové výdaje '+L.rok, milTxt(kap?kap.skut:0), 'investice (z toho škola)','var(--amber)'],
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

/* ---------- detail paragraf × položka ---------- */
const DT=DETAIL_JSON, DR=DT.rows, DPOL=DT.pol, DPAR=DT.par, DY=DT.years;
let dSide='Výdaje', dExpand=null, dSort=[3,true], dQ='';
const dDruh=r=>(DPOL[r[2]]||{}).d||'?';
function drill(){
  const yr=document.getElementById('dYear').value, grp=document.getElementById('dGroup').value;
  const yf=r=>(yr=='*'||r[0]==+yr);
  const keyName=r=> grp=='o'?((DPAR[r[1]]||{}).o||'(neuvedeno)') : grp=='t'?((DPOL[r[2]]||{}).t||'(neuvedeno)')
    : grp=='s'?((DPOL[r[2]]||{}).s||'(neuvedeno)') : (r[2]+' — '+((DPOL[r[2]]||{}).n||''));
  const agg={}, expandable=(grp=='o'||grp=='t')&&!dExpand;
  const add=(k,r)=>{(agg[k]=agg[k]||[0,0,0])[0]+=r[3];agg[k][1]+=r[4];agg[k][2]+=r[5];};
  DR.forEach(r=>{if(dDruh(r)!==dSide||!yf(r))return;
    if(dExpand&&(grp=='o'||grp=='t')){if(keyName(r)===dExpand)add(r[2]+' — '+((DPOL[r[2]]||{}).n||''),r);}
    else add(keyName(r),r);});
  let arr=Object.entries(agg).map(([k,v])=>[k,v[0],v[1],v[2],v[1]?v[2]/v[1]*100:0]).filter(r=>r[1]||r[2]||r[3]);
  if(dQ)arr=arr.filter(r=>r[0].toLowerCase().includes(dQ));
  const [sc,desc]=dSort; arr.sort((a,b)=>(desc?-1:1)*(typeof a[sc]=='string'?a[sc].localeCompare(b[sc],'cs'):a[sc]-b[sc]));
  drill._arr=arr;
  const tot=arr.reduce((a,r)=>[a[0]+r[1],a[1]+r[2],a[2]+r[3]],[0,0,0]);
  const maxv=Math.max(1,...arr.map(r=>r[3]));
  const H=['Položka / oblast','Schválený','Upravený','Skutečnost','% plnění','podíl'];
  const ar=i=>dSort[0]==i?(dSort[1]?' ▼':' ▲'):'';
  document.querySelector('#drill thead').innerHTML='<tr>'+H.map((h,i)=>`<th data-i="${i==5?3:i}">${h}<span class="ar">${ar(i==5?3:i)}</span></th>`).join('')+'</tr>';
  document.querySelectorAll('#drill thead th').forEach(th=>th.onclick=()=>{const i=+th.dataset.i;dSort=[i,dSort[0]==i?!dSort[1]:true];drill();});
  const pcl=p=>p>105?'warn':p<85?'bad':'ok';
  const esc=t=>String(t).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/"/g,'&quot;');
  const crumb=dExpand?`<tr class="subrow"><td colspan="6"><span class="back" style="cursor:pointer;color:var(--accent)">← zpět</span> · ${esc(dExpand)}</td></tr>`:'';
  const tb=document.querySelector('#drill tbody');
  tb.className='fade';
  tb.innerHTML=crumb+arr.map(r=>`<tr class="${expandable?'clk':''}" data-k="${esc(r[0])}">
      <td><span class="nm">${expandable?'<i>▸</i>':''}${esc(r[0])}</span></td>
      <td>${nf.format(r[1])}</td><td>${nf.format(r[2])}</td><td><b>${nf.format(r[3])}</b></td>
      <td>${r[2]?`<span class="pill ${pcl(r[4])}">${r[4].toFixed(0)} %</span>`:'–'}</td>
      <td class="barcell"><span class="b" style="width:${(Math.max(0,r[3])/maxv*96).toFixed(0)}px"></span></td></tr>`).join('')+
    `<tr class="total"><td>Celkem ${dSide.toLowerCase()}</td><td>${nf.format(tot[0])}</td><td>${nf.format(tot[1])}</td>
      <td>${nf.format(tot[2])}</td><td>${tot[1]?(tot[2]/tot[1]*100).toFixed(0)+' %':''}</td><td></td></tr>`;
  const bk=tb.querySelector('.back'); if(bk)bk.onclick=()=>{dExpand=null;drill();};
  if(expandable)tb.querySelectorAll('tr.clk').forEach(tr=>tr.onclick=()=>{dExpand=tr.dataset.k;drill();});
}
if(DR.length){
  const ys=document.getElementById('dYear');
  ys.innerHTML='<option value="*">souhrn všech let</option>'+DY.slice().reverse().map(y=>`<option value="${y}">${y}${DT.ytd&&DT.ytd[0]==y?' (průběžně)':''}</option>`).join('');
  ys.value=DT.ytd&&DY.length>1?DY[DY.length-2]:DY[DY.length-1];
  ys.onchange=()=>{dExpand=null;drill();};
  document.getElementById('dGroup').onchange=()=>{dExpand=null;drill();};
  document.getElementById('dSearch').oninput=e=>{dQ=e.target.value.toLowerCase().trim();drill();};
  document.querySelectorAll('#sideSeg button').forEach(b=>b.onclick=()=>{document.querySelectorAll('#sideSeg button').forEach(x=>x.classList.remove('on'));b.classList.add('on');dSide=b.dataset.s;dExpand=null;drill();});
  document.getElementById('dlDrill').onclick=()=>{const y=ys.value;
    dlCSV('ostopovice_rozpocet_'+dSide.toLowerCase()+'_'+(y=='*'?'vse':y)+'.csv',['polozka_oblast','schvaleny_kc','upraveny_kc','skutecnost_kc','plneni_pct'],
      (drill._arr||[]).map(r=>[r[0],r[1],r[2],r[3],r[4].toFixed(1)]));};
  drill();
} else document.getElementById('detail').hidden=true;
function render(){kpis();trend();prijmyChart();vydajeChart();}
render(); bindTheme(render);
document.querySelectorAll('#mSeg button').forEach(b=>b.onclick=()=>{document.querySelectorAll('#mSeg button').forEach(x=>x.classList.remove('on'));b.classList.add('on');metric=b.dataset.m;trend();});
window.addEventListener('load',()=>{Object.values(charts).forEach(c=>{try{c.resize();}catch(e){}});});
</script>'''.replace("DATA_JSON", data_json).replace("DETAIL_JSON", json.dumps(DET, ensure_ascii=False, separators=(",", ":")))

DETAIL_CSS = """.lbl{font-size:12.5px;color:var(--muted);font-weight:500;margin-right:2px}
#detail select,#detail input[type=text]{font:inherit;font-size:13.5px;padding:7px 11px;border:1px solid var(--line);border-radius:10px;background:var(--surface);color:var(--text);outline:none}
#detail select:focus,#detail input[type=text]:focus{border-color:var(--accent);box-shadow:0 0 0 3px var(--accent-soft)}
#detail .tbar{display:flex;gap:12px;align-items:center;flex-wrap:wrap;margin:10px 0}
#detail .dlbtn{display:inline-flex;align-items:center;gap:6px;font:inherit;font-size:12px;font-weight:500;color:var(--muted);background:var(--inset);border:1px solid var(--line);border-radius:9px;padding:5px 11px;cursor:pointer;white-space:nowrap}
#detail .dlbtn:hover{color:var(--accent);border-color:var(--accent)}
#detail .search{flex:1;min-width:180px;position:relative}
#detail .search i{position:absolute;left:11px;top:50%;transform:translateY(-50%);color:var(--faint);font-size:15px;font-style:normal}
#detail .search input{width:100%;padding-left:34px}
#detail .tablewrap{max-height:540px;overflow:auto;border:1px solid var(--line);border-radius:var(--radius-sm)}
#drill{width:100%;border-collapse:collapse;font-size:13px}
#drill th,#drill td{padding:9px 12px;text-align:right;white-space:nowrap;border-bottom:1px solid var(--line)}
#drill th:first-child,#drill td:first-child{text-align:left;white-space:normal}
#drill thead th{position:sticky;top:0;z-index:2;background:var(--surface2);color:var(--muted);font-weight:600;cursor:pointer;user-select:none;font-size:12px}
#drill thead th:hover{color:var(--text)}
#drill thead th .ar{opacity:.5;font-size:10px}
#drill tbody tr.clk{cursor:pointer}
#drill tbody tr:hover{background:var(--inset)}
#drill td .nm{display:flex;align-items:center;gap:7px}
#drill td .nm i{color:var(--faint);font-size:14px;font-style:normal}
#drill .barcell{position:relative;min-width:120px}
#drill .barcell .b{position:absolute;left:12px;top:50%;transform:translateY(-50%);height:7px;border-radius:4px;background:var(--accent);opacity:.85}
#drill .pill{font-size:11px;padding:2px 9px;border-radius:999px;font-weight:600}
#drill .pill.ok{background:rgba(16,185,129,.15);color:var(--pos)}
#drill .pill.warn{background:rgba(249,115,22,.16);color:var(--vydaje)}
#drill .pill.bad{background:rgba(239,68,68,.15);color:var(--neg)}
#drill tr.total td{font-weight:680;border-top:2px solid var(--text);background:var(--surface2)}
#drill tr.subrow td{background:var(--inset);font-size:12.5px}
#drill .fade{animation:dfade .35s ease}
@keyframes dfade{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}"""

open("rozpocet.html", "w", encoding="utf-8").write(
    pc.page("Rozpočet", "Rozpočet obce — Jak žijí Ostopovice", body,
            head_scripts="<style>" + SANKEY_CSS + KOSTKA_CSS + DETAIL_CSS + SMLOUVY_CSS + "</style>",
            body_scripts=scripts + SANKEY_JS.replace("SANKEY_DATA", json.dumps(SANKEY, ensure_ascii=False))))
print(f"HOTOVO -> rozpocet.html ({years[0]['rok']}-{LY}, {len(years)} let, výdaje {LY} {mil(last['vydaje']['skut'])} mil.)")
