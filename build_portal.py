#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rozcestník (index.html) prototypu portálu obce Ostopovice."""
import sys, csv, json
import portal_common as pc
sys.stdout.reconfigure(encoding="utf-8")

# data pro KPI + "Co je nového"
pop = [int(r["stav"]) for r in csv.DictReader(open("data/ostopovice_obyvatele.csv", encoding="utf-8-sig"), delimiter=";")]
zo = json.load(open("dataset_ZO.json", encoding="utf-8"))
zo.sort(key=lambda m: m["datum"], reverse=True)
pocet_usn = sum(m["pocet_bodu"] for m in zo)
SHR = json.load(open("data/shrnuti/zo.json", encoding="utf-8"))
ROZ = json.load(open("data/rozpocet_ostopovice.json", encoding="utf-8"))
ZAK = json.load(open("data/zakazky.json", encoding="utf-8"))
A = ROZ["aktualni"]

tiles = [
    ("obdobi.html", "Bilance 2022–2026", "bi", True,
     "Volební období v datech — hospodaření, největší zakázky, časová osa klíčových rozhodnutí a účast zastupitelů na zasedáních.",
     "Otevřít bilanci →", "nové"),
    ("rozpocet.html", "Rozpočet", "ti", True,
     "Příjmy, výdaje a saldo obce 2010–2025, struktura příjmů a kam tečou výdaje. Ze systému MONITOR Státní pokladny (výkaz FIN 2-12 M).",
     "Otevřít rozpočet →", None),
    ("srovnani.html", "Srovnání se sousedy", "sr", True,
     "Ostopovice vedle okolních obcí v přepočtu na obyvatele — příjmy, investice, dluh, rezervy — a semafor finančního zdraví.",
     "Otevřít srovnání →", "nové"),
    ("investice.html", "Investice", "in", True,
     "Kam obec vkládá peníze — veřejné zakázky (stavby, škola) podle oblasti a roku a nákupy pozemků a majetku z usnesení zastupitelstva.",
     "Otevřít investice →", None),
    ("zakazky.html", "Zakázky", "za", True,
     "Veřejné zakázky obce z profilu zadavatele — co obec poptává a staví a za kolik. Žebříček největších a objem podle roku.",
     "Otevřít zakázky →", None),
    ("dotace.html", "Komu obec přispívá", "do", True,
     "Dotace, dary a příspěvky spolkům a dalším subjektům — kolik, komu a na co, schválené zastupitelstvem.",
     "Otevřít dotace →", None),
    ("skolstvi.html", "Školství", "sk", True,
     "Mateřská a základní škola Ostopovice, kapacity a demografický kontext obce. Obec kapacitu školy rozšiřuje dostavbou.",
     "Otevřít školství →", None),
    ("demografie.html", "Demografie", "de", True,
     "Vývoj počtu obyvatel obce od roku 2004 podle Českého statistického úřadu.",
     "Otevřít demografii →", None),
    ("volby.html", "Volby", "vo", True,
     "Jak Ostopovice volí — složení zastupitelstva z komunálních voleb 2022, zvolení zastupitelé, sněmovní i prezidentské volby v obci.",
     "Otevřít volby →", None),
    ("zastupitelstvo.html", "Zastupitelstvo", "zo", True,
     f"Usnesení zastupitelstva ({zo[-1]['rok']}–{zo[0]['rok']}) — shrnutí každého zasedání, výsledky hlasování, témata a částky, s odkazem na originální PDF zápis.",
     "Procházet usnesení →", None),
    ("hledat.html", "Hledat", "hl", True,
     "Jedno hledání přes usnesení, zakázky, dotace i rozpočet — bez ohledu na diakritiku a koncovky.",
     "Hledat →", None),
]
# jednobarevné linkové ikony dlaždic (24×24, tah currentColor — barvu dává CSS .tile .ic)
TILE_ICONS = {
    "ti": '<ellipse cx="12" cy="6" rx="7" ry="3"/><path d="M5 6v6c0 1.7 3.1 3 7 3s7-1.3 7-3V6M5 12v6c0 1.7 3.1 3 7 3s7-1.3 7-3v-6"/>',
    "sr": '<path d="M12 4v16M7 20h10M5 7h14M5 7l-3 6a3 3 0 0 0 6 0zM19 7l-3 6a3 3 0 0 0 6 0z"/>',
    "in": '<path d="M3 21h18M5 21V11l5-3v13M10 21V4l9 4v13M14 11h2M14 15h2"/>',
    "za": '<path d="M6 3h12v18l-3-2-3 2-3-2-3 2zM9 8h6M9 12h6M9 16h3"/>',
    "sk": '<path d="M2 9l10-5 10 5-10 5zM6 11v5c0 1.5 2.7 3 6 3s6-1.5 6-3v-5M22 9v6"/>',
    "do": '<path d="M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.6-7 10-7 10z"/>',
    "zo": '<path d="M3 10l9-6 9 6M5 10v8M9.5 10v8M14.5 10v8M19 10v8M3 21h18"/>',
    "pl": '<path d="M12 5v14M5 12h14"/>',
    "bi": '<path d="M4 20h16M7 16v-4M12 16V8M17 16V5"/>',
    "hl": '<circle cx="11" cy="11" r="6"/><path d="M20 20l-4.5-4.5"/>',
    "de": '<circle cx="9" cy="8" r="3"/><path d="M3 20c0-3.3 2.7-6 6-6s6 2.7 6 6M16 5.5a3 3 0 0 1 0 5.5M18 14.5c1.8.9 3 2.9 3 5.5"/>',
    "vo": '<path d="M4 12h16v8H4zM8 12V5h8v7M10 8.5l1.5 1.5L14 7.5"/>',
}
tile_html = ""
for href, name, ic, active, desc, go, badge in tiles:
    cls = "tile" + ("" if active else " soon")
    badge_html = f'<span class="badge">{badge}</span>' if badge else ""
    go_html = f'<span class="go">{go}</span>' if go else ""
    icon = '<svg viewBox="0 0 24 24" aria-hidden="true">' + TILE_ICONS.get(ic, TILE_ICONS["pl"]) + '</svg>'
    tile_html += (f'<a class="{cls}" href="{href}">{badge_html}'
                  f'<span class="ic">{icon}</span><h3>{name}</h3><p>{desc}</p>{go_html}</a>')

pop_fmt = f'{pop[-1]:,}'.replace(",", " ")


def short(t, n=150):
    return t if len(t) <= n else t[:n].rsplit(" ", 1)[0] + "…"


def row(datum, sec, col, txt, href):
    return (f'<a class="updrow" href="{href}"><span class="upddate">{datum}</span>'
            f'<span class="updsec"><i style="background:{col}"></i>{sec}</span>'
            f'<span class="updtxt">{txt}</span><span class="updarr">&#8594;</span></a>')


upd = []   # (ISO datum, html)
for m in zo[:3]:
    k = f"{m['rok']}-{m['cislo_zasedani']}"
    lab = "Ustavující zasedání" if m["cislo_zasedani"] == 0 else f"{m['cislo_zasedani']}. zasedání"
    upd.append((m["datum"], row(m["datum_text"], "Zastupitelstvo", "#e0a458",
                   f"<b>{lab}</b> ({m['pocet_bodu']} usnesení) — {short(SHR.get(k, ''))}", f"zastupitelstvo.html?zo={k}")))
z0 = ZAK[0]
d, mo, y = (int(x) for x in z0["datum"].split("."))
upd.append((f"{y}-{mo:02d}-{d:02d}", row(f"{d}. {mo}. {y}", "Zakázky", "#0d9488",
               f"Nová zakázka: <b>{z0['nazev']}</b>" + (f" · {z0['hodnota']/1e6:.1f}".replace(".", ",") + " mil. Kč" if z0.get("hodnota") else ""),
               "zakazky.html")))
pl = A["vydaje"]["skut"] / A["vydaje"]["uprav"] * 100 if A["vydaje"]["uprav"] else 0
upd.append((f"{A['rok']}-{A['obdobi'] % 100:02d}-28", row(f"k {A['mesic']} {A['rok']}", "Rozpočet", "#16a34a",
                  f"Plnění rozpočtu {A['rok']}: obec zatím utratila <b>{pl:.0f} %</b> plánovaných výdajů "
                  f"({A['vydaje']['skut']/1e6:.1f} z {A['vydaje']['uprav']/1e6:.1f} mil. Kč)".replace(".", ",", 2), "rozpocet.html")))
upd_html = "".join(h for _, h in sorted(upd, reverse=True))

UPD_CSS = '''<style>
.updrow{display:flex;align-items:center;gap:12px;padding:10px 6px;border-radius:10px;text-decoration:none;color:var(--text)}
.updrow:hover{background:var(--inset)}
.upddate{color:var(--muted);font-size:12.5px;min-width:92px;white-space:nowrap;font-variant-numeric:tabular-nums}
.updsec{display:inline-flex;align-items:center;font-size:11px;font-weight:600;color:var(--muted);background:var(--inset);border:1px solid var(--line);padding:2px 9px;border-radius:999px;white-space:nowrap}
.updsec i{width:8px;height:8px;border-radius:2px;display:inline-block;margin-right:6px}
.updtxt{font-size:13.5px;flex:1}
.updarr{color:var(--faint);font-size:14px}
.warn{background:var(--inset);border:1px solid var(--line);border-left:3px solid var(--vydaje);border-radius:10px;padding:12px 15px;font-size:12.5px;color:var(--muted);margin-top:8px}
@media(max-width:560px){.updrow{flex-wrap:wrap;gap:6px 10px}.updtxt{flex-basis:100%;order:3}.updarr{display:none}}
</style>'''

body = f'''<header class="hero">
  <h1>Jak žijí Ostopovice <span style="font-size:17px;font-weight:500;color:var(--muted)">· občanský datový portál</span></h1>
  <p>Datový portál obce Ostopovice u Brna — jak obec hospodaří, roste a žije, srozumitelně v číslech. Veřejná data z oficiálních zdrojů, přehledně a pro každého.</p>
  <div class="chips"><span class="chip">obec Ostopovice · IČO 00282294</span><span class="chip">≈ {pop_fmt} obyvatel</span><span class="chip">zdroje: MONITOR SP · ČSÚ · volby.cz · ostopovice.cz</span></div>
</header>

<div class="cards">
  <div class="kpi" style="--bar:var(--c0)"><div class="lab">Počet obyvatel</div><div class="val">{pop_fmt}</div><div class="delta" style="color:var(--muted)">ČSÚ, k 1. 1. 2025</div></div>
  <div class="kpi" style="--bar:var(--c1)"><div class="lab">Zasedání zastupitelstva</div><div class="val">{len(zo)}</div><div class="delta" style="color:var(--muted)">{zo[-1]['rok']}–{zo[0]['rok']}</div></div>
  <div class="kpi" style="--bar:var(--c2)"><div class="lab">Usnesení ZO</div><div class="val">{pocet_usn}</div><div class="delta" style="color:var(--muted)">strojově zpracováno z PDF</div></div>
  <div class="kpi" style="--bar:var(--c3)"><div class="lab">Investice 2025</div><div class="val">{ROZ["struktura"]["2025"]["vydaje_druh"][1]["skut"]/1e6:.0f} <span style="font-size:14px;color:var(--muted)">mil. Kč</span></div><div class="delta" style="color:var(--muted)">hlavně dostavba MŠ a ZŠ</div></div>
</div>

<section><div class="panel">
  <div class="sec-h" style="margin:0 0 8px"><h2 style="font-size:16px">Co je nového</h2><span class="hint">poslední zasedání, rozpočet a zakázky</span></div>
  {upd_html}
</div></section>

<section><div class="tiles">{tile_html}</div></section>

<section><div class="panel">
  <div class="sec-h" style="margin:0 0 6px"><h2 style="font-size:16px">O portálu</h2></div>
  <p style="color:var(--muted);font-size:13.5px;margin:0;line-height:1.6">Občanský datový portál obce Ostopovice zpracovává <b>veřejná data</b> o obci do přehledných interaktivních vizualizací. Zdroje jsou oficiální: zápisy zastupitelstva z webu obce <a href="https://www.ostopovice.cz" target="_blank" rel="noopener" style="color:var(--accent)">ostopovice.cz</a>, veřejné zakázky z profilu zadavatele, počet obyvatel z Českého statistického úřadu a výsledky voleb z <a href="https://www.volby.cz" target="_blank" rel="noopener" style="color:var(--accent)">volby.cz</a>. Zdroj je u každé sekce uveden.</p>
  <div class="warn"><b>Co portál nezahrnuje:</b> Zápisy z <b>rady obce</b> obec nezveřejňuje, proto tu nejsou (o části zakázek rozhoduje rada — ty jsou vidět jen v profilu zadavatele). U zakázek je z profilu dostupná jen předpokládaná hodnota, ne vítězný dodavatel.</div>
</div></section>'''

open("index.html", "w", encoding="utf-8").write(
    pc.page("Přehled", "Jak žijí Ostopovice — otevřená data obce", body,
            head_scripts=UPD_CSS, body_scripts='<script>bindTheme();</script>'))
print(f"HOTOVO -> index.html (obyvatel {pop[-1]}, ZO {len(zo)}, usnesení {pocet_usn})")
