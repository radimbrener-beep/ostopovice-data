#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stránka Jak často se data kontrolují (aktualizace.html) — pro každý zdroj
portálu: odkud se bere, jak často se kontroluje (automaticky / ručně) a jak čerstvá
jsou data teď. Čas automatické kontroly odpovídá cronu v .github/workflows/check_web.yml.
Odkazuje se z patičky a ze stránky Metodika; přegeneruje ji scripts/update_portal.py."""
import sys, json
from datetime import date, datetime
import portal_common as pc
sys.stdout.reconfigure(encoding="utf-8")

A = 'target="_blank" rel="noopener" style="color:var(--accent)"'

zo = max(json.load(open("dataset_ZO.json", encoding="utf-8")), key=lambda m: m["datum"])
zo_d = date.fromisoformat(zo["datum"])
akt = json.load(open("data/rozpocet_ostopovice.json", encoding="utf-8"))["aktualni"]
zak_d = max(datetime.strptime(z["datum"], "%d.%m.%Y").date()
            for z in json.load(open("data/zakazky.json", encoding="utf-8")) if z.get("datum"))

body = f'''<header class="hero">
  <h1>Jak často se data kontrolují</h1>
  <p>Portál nic nevymýšlí — jen přebírá, co zveřejní obec a státní instituce. Tady je u každého zdroje vidět, jak často se kontroluje, jestli to dělá automat, nebo ruka, a jak čerstvá data na portálu právě jsou.</p>
  <div class="chips"><span class="chip">automat 1× denně</span><span class="chip">ruční zdroje průběžně</span><span class="chip">vše s odkazem na originál</span></div>
</header>

<div class="cards">
  <div class="kpi" style="--bar:var(--accent)"><div class="lab">Automatická kontrola zdrojů</div><div class="val">1× denně</div><div class="delta" style="color:var(--muted)">orientačně kolem 7 h ráno</div></div>
  <div class="kpi" style="--bar:var(--c0)"><div class="lab">Nejnovější zastupitelstvo</div><div class="val">{zo_d.day}.&nbsp;{zo_d.month}.</div><div class="delta" style="color:var(--muted)">{zo["cislo_zasedani"]}. zasedání, {zo_d.year}</div></div>
  <div class="kpi" style="--bar:var(--c2)"><div class="lab">Nejnovější zakázka</div><div class="val">{zak_d.day}.&nbsp;{zak_d.month}.</div><div class="delta" style="color:var(--muted)">uveřejněna {zak_d.year}</div></div>
  <div class="kpi" style="--bar:var(--c3)"><div class="lab">Plnění rozpočtu {akt["rok"]}</div><div class="val">k {akt["mesic"]}</div><div class="delta" style="color:var(--muted)">poslední měsíc v MONITORu</div></div>
</div>

<section>
  <div class="sec-h"><h2>Zdroje a jejich kontrola</h2><span class="hint">od nejčastěji kontrolovaných</span></div>
  <div class="panel"><div class="tw"><table class="mtab ak">
    <thead><tr><th>Sekce</th><th>Zdroj</th><th>Jak často</th><th>Jak</th></tr></thead>
    <tbody>
      <tr><td><b>Zastupitelstvo</b><br><span class="sub">zápisy, usnesení</span></td><td><a href="https://www.ostopovice.cz" {A}>zápisy ZO na webu obce</a></td><td>denně<br><span class="sub">kolem 7 h ráno</span></td><td><span class="tag auto">automaticky</span> nový zápis se stáhne, rozebere a ještě týž den je na portálu, včetně upozornění odběratelům</td></tr>
      <tr><td><b>Zakázky</b></td><td><a href="https://www.vhodne-uverejneni.cz/profil/obec-ostopovice" {A}>profil zadavatele obce</a></td><td>denně<br><span class="sub">kolem 7 h ráno</span></td><td><span class="tag auto">automaticky</span> projdou se probíhající i ukončené zakázky</td></tr>
      <tr><td><b>Plnění rozpočtu letos</b></td><td><a href="https://monitor.statnipokladna.gov.cz" {A}>MONITOR Státní pokladny</a></td><td>denně<br><span class="sub">kolem 7 h ráno</span></td><td><span class="tag auto">automaticky</span> nový měsíc se převezme, jakmile ho MONITOR zveřejní — výkazy obcí tam přibývají s odstupem několika týdnů</td></tr>
      <tr><td><b>Dotace spolkům, Investice (rozhodnutí), Bilance období, Hledání</b></td><td>odvozeno z usnesení zastupitelstva</td><td>s každým novým zápisem<br><span class="sub">kolem 7 h ráno</span></td><td><span class="tag auto">automaticky</span> přepočítá se spolu s novým zápisem</td></tr>
      <tr><td><b>Shrnutí „V kostce"</b></td><td>zápis zastupitelstva</td><td>po každém zasedání</td><td><span class="tag ruc">ručně</span> krátké shrnutí se dopisuje po zveřejnění zápisu</td></tr>
      <tr><td><b>Rozpočet (uzavřené roky), Investice (grafy)</b></td><td><a href="https://monitor.statnipokladna.gov.cz" {A}>MONITOR Státní pokladny</a></td><td>denně<br><span class="sub">kolem 7 h ráno</span></td><td><span class="tag auto">automaticky</span> uzavřený rok bývá v MONITORu v březnu–dubnu následujícího roku</td></tr>
      <tr><td><b>Srovnání s okolními obcemi</b></td><td><a href="https://monitor.statnipokladna.gov.cz" {A}>MONITOR Státní pokladny</a></td><td>ročně</td><td><span class="tag ruc">ručně</span> po zveřejnění ročních výkazů a rozvah všech obcí</td></tr>
      <tr><td><b>Školství, Demografie</b></td><td><a href="https://data.csu.gov.cz" {A}>ČSÚ</a>, MŠMT</td><td>ročně</td><td><span class="tag ruc">ručně</span> po zveřejnění nových ročních dat</td></tr>
      <tr><td><b>Volby</b></td><td><a href="https://www.volby.cz" {A}>volby.cz</a> (ČSÚ)</td><td>po volbách</td><td><span class="tag ruc">ručně</span> po vyhlášení výsledků</td></tr>
    </tbody>
  </table></div></div>
</section>

<section>
  <div class="sec-h"><h2>Jak automatická kontrola funguje</h2></div>
  <div class="panel">
    <p>Každé ráno, orientačně kolem 7 hodin, se spustí skript, který stáhne seznam zápisů zastupitelstva z webu obce, rozpočet obce z MONITORu a zakázky z profilu zadavatele a porovná je s tím, co už portál zná. Když je něco nového, přegeneruje stránky a portál se sám nasadí; při novém zasedání přijde odběratelům upozornění. Když některý zdroj zrovna nefunguje, zůstanou na portálu předchozí data a zkusí se to další den.</p>
    <p>Když se nic nového neobjeví, nic se nemění — datum v patičce tedy ukazuje poslední skutečnou změnu, ne poslední kontrolu.</p>
    <p class="note">Čas je orientační: kontrola běží na GitHubu, který naplánované úlohy spouští s proměnlivým, často několikahodinovým zpožděním. Kontrola je proto naplánovaná s předstihem a skutečný čas se může o hodinu i víc lišit oběma směry. V letním čase běží zhruba o hodinu později.</p>
  </div>
</section>

<section>
  <div class="sec-h"><h2>Proč tu něco ještě není</h2></div>
  <div class="panel">
    <table class="mtab"><tbody>
      <tr><td><b>Obec dokument ještě nezveřejnila</b></td><td>zápis zastupitelstva se zveřejňuje až po ověření, obvykle několik dní až dva týdny po zasedání — portál ho převezme nejpozději následující den</td></tr>
      <tr><td><b>Rada obce</b></td><td>Ostopovice zápisy ze schůzí rady nezveřejňují, proto na portálu nejsou</td></tr>
      <tr><td><b>Zdroj zveřejňuje s odstupem</b></td><td>MONITOR, ČSÚ i školské statistiky vycházejí měsíce po skončení období, které popisují</td></tr>
      <tr><td><b>Ruční krok ještě neproběhl</b></td><td>sekce označené „ručně" aktualizuje autor portálu ve volném čase — když něco chybí déle, než je uvedeno výše, dejte vědět: ''' + pc.MAIL_LINK + '''</td></tr>
    </tbody></table>
    <p class="note">Podrobnosti o tom, jak se data zpracovávají a jaká mají omezení, jsou na stránce <a href="metodika.html" style="color:var(--accent)">Metodika a zdroje dat</a>.</p>
  </div>
</section>'''

CSS = '''<style>
.tw{overflow-x:auto}
.mtab{width:100%;border-collapse:collapse;font-size:13.5px;margin:10px 0}
.mtab th,.mtab td{padding:8px 10px;border-bottom:1px solid var(--line);text-align:left;white-space:normal;vertical-align:top}
.mtab th{font-size:12px;color:var(--muted);font-weight:600}
.mtab td:first-child{width:28%}
.ak td:nth-child(3){white-space:nowrap}
.ak .sub{font-size:11.5px;color:var(--faint)}
.tag{display:inline-block;font-size:11px;font-weight:600;padding:1px 8px;border-radius:999px;margin:0 6px 3px 0;border:1px solid var(--line)}
.tag.auto{color:var(--c0);background:color-mix(in srgb,var(--c0) 12%,transparent)}
.tag.ruc{color:var(--muted);background:var(--inset)}
.panel p{line-height:1.6}
@media(max-width:640px){.ak td:nth-child(3){white-space:normal}.mtab td:first-child{width:auto}}
</style>'''

open("aktualizace.html", "w", encoding="utf-8").write(
    pc.page("Aktualizace", "Jak často se data kontrolují — " + pc.BRAND, body, head_scripts=CSS))
print("HOTOVO: aktualizace.html")
