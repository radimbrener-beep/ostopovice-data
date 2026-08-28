#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generuje stránku Metodika a zdroje dat (metodika.html) — centrální
vysvětlení, odkud data pocházejí, jak se zpracovávají a jaká mají omezení.
Odkazuje se z patičky všech stránek portálu."""
import sys
import portal_common as pc
sys.stdout.reconfigure(encoding="utf-8")

A = 'target="_blank" rel="noopener" style="color:var(--accent)"'
body = f'''<header class="hero">
  <h1>Metodika a zdroje dat</h1>
  <p>Jak číst data na tomto portálu: odkud pocházejí, jak se zpracovávají, jak často se aktualizují a jaká mají omezení. Když si nejste jistí, co které číslo znamená, odpověď je tady.</p>
  <div class="chips"><span class="chip">nezávislý projekt</span><span class="chip">otevřené zdroje</span><span class="chip">vše ověřitelné v originálech</span></div>
</header>

<section>
  <div class="sec-h"><h2>O portálu</h2></div>
  <div class="panel">
    <p>„Jak žijí Ostopovice" je <b>nezávislý občanský projekt</b> — není to oficiální web obce Ostopovice. Všechna data pocházejí z veřejných zdrojů (státní pokladna, ČSÚ, volby.cz, úřední dokumenty obce) a u každé sekce je uveden zdroj i odkaz na originál. Portál data nehodnotí — jen je skládá dohromady a vizualizuje, aby byla srozumitelná bez účetního vzdělání.</p>
    <p class="note"><b>Kontakt:</b> Radim Brener · {pc.MAIL_LINK}. Našli jste chybu nebo nesoulad? Napište — rozhoduje vždy originální dokument, ne tento portál.</p>
  </div>
</section>

<section>
  <div class="sec-h"><h2>Aktualizace dat</h2></div>
  <div class="panel">
    <p>Datum poslední aktualizace je v patičce každé stránky. Jednotlivé sekce se obnovují různým tempem podle toho, kdy jejich zdroj zveřejní nová data:</p>
    <table class="mtab"><tbody>
      <tr><td><b>Zastupitelstvo, Dotace spolkům</b></td><td>průběžně — automatická kontrola nových zápisů na webu obce</td></tr>
      <tr><td><b>Zakázky</b></td><td>průběžně — automatická kontrola profilu zadavatele</td></tr>
      <tr><td><b>Rozpočet, Investice</b></td><td>měsíčně (plnění letošního rozpočtu) a ročně (uzavřený rok, zpravidla v březnu–dubnu následujícího roku)</td></tr>
      <tr><td><b>Srovnání</b></td><td>ročně — po zveřejnění ročních výkazů a rozvah všech obcí</td></tr>
      <tr><td><b>Školství, Demografie, Volby</b></td><td>ročně, resp. po volbách</td></tr>
    </tbody></table>
  </div>
</section>

<section>
  <div class="sec-h"><h2>Rozpočet</h2><span class="hint">sekce Rozpočet, Investice, Bilance</span></div>
  <div class="panel">
    <p><b>Zdroj:</b> <a href="https://monitor.statnipokladna.gov.cz" {A}>MONITOR Státní pokladny</a> (Ministerstvo financí), výkaz <b>FIN 2-12 M</b> — plnění rozpočtu obce, IČO 00282294. Roční stav k&nbsp;31.&nbsp;12. za uzavřené roky, pro letošní rok poslední zveřejněný měsíc.</p>
    <p><b>Tři varianty čísel</b>:</p>
    <table class="mtab"><tbody>
      <tr><td><b>Schválený rozpočet</b></td><td>plán, který zastupitelstvo schválilo na začátku roku</td></tr>
      <tr><td><b>Upravený rozpočet</b></td><td>plán po rozpočtových opatřeních v průběhu roku (přesuny, zapojení dotací a rezerv)</td></tr>
      <tr><td><b>Skutečnost</b></td><td>co se opravdu přijalo a utratilo — pokud není uvedeno jinak, grafy ukazují skutečnost</td></tr>
    </tbody></table>
    <p><b>Třídění:</b> příjmy podle tříd (daňové, nedaňové, kapitálové, transfery), výdaje podle odvětví („na co") i druhu (běžné × kapitálové). Splátky a čerpání úvěrů jsou financování, ne příjem ani výdaj.</p>
    <p class="note">Hodnoty jsou v běžných cenách (bez očištění o inflaci). Shrnutí „V kostce" v sekci Rozpočet je ručně sepsaný výtah z těchto čísel.</p>
  </div>
</section>

<section>
  <div class="sec-h"><h2>Srovnání s okolními obcemi</h2></div>
  <div class="panel">
    <p>Finanční data všech obcí pocházejí ze stejného zdroje (MONITOR, FIN 2-12 M a rozvaha) a stejného výpočtu — čísla jsou plně srovnatelná. Počty obyvatel pro přepočet na hlavu jsou z ČSÚ. Vybrány jsou sousední a blízké obce okresu Brno-venkov; u menší obce umí jedna velká investice „rozkmitat" přepočet na obyvatele — proto grafy ukazují i víceleté průměry.</p>
    <p><b>Ukazatele finančního zdraví</b> vycházejí z metodiky monitoringu MF ČR (fiskální pravidlo): dlouhodobě záporné saldo, vysoký dluh vůči průměru příjmů (limit 60&nbsp;%) nebo nízká likvidita signalizují riziko. <b>Dluh</b> = úvěry, dluhopisy a návratné výpomoci podle rozvahy k 31. 12. — u úvěru se počítá jen skutečně vyčerpaná část. Podrobná metodika: <a href="https://monitor.statnipokladna.gov.cz/metodika" {A}>monitor.statnipokladna.gov.cz/metodika</a>.</p>
  </div>
</section>

<section>
  <div class="sec-h"><h2>Investice a zakázky</h2></div>
  <div class="panel">
    <p><b>Kapitálové výdaje</b> (grafy) jsou z výkazu FIN 2-12 M — výdaje na pořízení a zhodnocení majetku (stavby, pozemky, projekty), na rozdíl od běžných provozních výdajů.</p>
    <p><b>Konkrétní akce</b> v sekci Investice jsou automaticky vytažené z usnesení zastupitelstva (body s částkou v investičních tématech). <b>Zakázky</b> jsou z <a href="https://www.vhodne-uverejneni.cz/profil/obec-ostopovice" {A}>profilu zadavatele obce</a>.</p>
    <table class="mtab"><tbody>
      <tr><td><b>Částka je orientační</b></td><td>u usnesení je to cena v okamžiku rozhodnutí, u zakázek předpokládaná hodnota bez DPH z profilu zadavatele — skutečně proplacená částka se může lišit (dodatky, vícepráce, výsledek soutěže)</td></tr>
      <tr><td><b>Úvěry</b></td><td>výběr banky na úvěr je v profilu zadavatele vedený jako zakázka; do objemů zakázek se nepočítá, protože to není výdaj</td></tr>
      <tr><td><b>Úplnost</b></td><td>zakázky malého rozsahu, které obec nemusí zveřejňovat, v přehledu nejsou — souhrnné roční investice v grafech ale úplné jsou</td></tr>
    </tbody></table>
  </div>
</section>

<section>
  <div class="sec-h"><h2>Dotace spolkům</h2></div>
  <div class="panel">
    <p><b>Zdroj:</b> usnesení zastupitelstva, kterými schválilo poskytnutí dotace, daru nebo příspěvku s uvedenou částkou. Příjemce je odvozen z textu usnesení; u dotací, které formálně přijímá zástupce spolku jako fyzická osoba, je uveden spolek, pro který jsou peníze určeny. Příspěvky, které schvaluje rada obce, a transfery příspěvkovým organizacím obce (škola) tu nejsou.</p>
  </div>
</section>

<section>
  <div class="sec-h"><h2>Zastupitelstvo</h2></div>
  <div class="panel">
    <p><b>Zdroj:</b> oficiální zápisy ze zasedání zastupitelstva (PDF) z <a href="https://www.ostopovice.cz/organy-obce" {A}>webu obce</a>. Texty usnesení se z PDF vytahují automaticky, proto se mohou ojediněle objevit drobné chyby převodu. U každého zasedání je odkaz na originální PDF — to je vždy rozhodující verze. Obec Ostopovice nezveřejňuje zápisy z rady obce ani videozáznamy zasedání, portál proto pracuje jen se zápisy zastupitelstva.</p>
    <table class="mtab"><tbody>
      <tr><td><b>Anonymizace</b></td><td>zápisy obce obsahují jména, adresy a data narození soukromých osob (kupní smlouvy, dary, volba přísedících). <b>Portál je anonymizuje sám</b> (GDPR): jména fyzických osob nahrazuje iniciálami, adresy bydliště a data narození vypouští. Jména zastupitelů a názvy firem, spolků a úřadů zůstávají.</td></tr>
      <tr><td><b>Témata</b></td><td>přiřazují se automaticky podle klíčových slov v textu — orientační pomůcka pro filtrování, ne úřední kategorizace</td></tr>
      <tr><td><b>Částky</b></td><td>vytažené z textu usnesení, orientační</td></tr>
      <tr><td><b>Shrnutí „V kostce"</b></td><td>krátké shrnutí každého zasedání napsal <b>jazykový model (AI)</b> výhradně z textu usnesení podle pevných pravidel (jen fakta, bez hodnocení, bez jmen fyzických osob) a bylo namátkově zkontrolováno. Může obsahovat zjednodušení — rozhoduje vždy text usnesení a originální PDF.</td></tr>
      <tr><td><b>Jednání a formality</b></td><td>samostatné téma pro procedurální body (program, ověřovatelé, volby do funkcí, zprávy o činnosti rady), aby nezahlcovaly věcná témata</td></tr>
    </tbody></table>
  </div>
</section>

<section>
  <div class="sec-h"><h2>Bilance období a účast zastupitelů</h2></div>
  <div class="panel">
    <p><b>Zdroj:</b> zápisy zastupitelstva od ustavujícího zasedání 20. 10. 2022 a data ostatních sekcí portálu.</p>
    <table class="mtab"><tbody>
      <tr><td><b>Účast</b></td><td>podle údajů „Přítomno" a „Omluveni" v hlavičce zápisu; zastupitel, který přišel během zasedání, je počítán jako přítomný. Ve volebním období se složení zastupitelstva neměnilo.</td></tr>
      <tr><td><b>Hlasování</b></td><td>zápisy uvádějí jen počty hlasů pro / proti / zdržel se, ne jména. Portál proto ukazuje podíl jednomyslných hlasování a seznam těch nejednomyslných, ale ne to, jak hlasovali jednotliví zastupitelé. Nepočítají se procedurální body (téma Jednání a formality) ani volby do funkcí, kde se zvolený obvykle zdrží.</td></tr>
      <tr><td><b>Nestrannost</b></td><td>portál zastupitele nehodnotí ani neřadí; zastupitelé jsou uvedeni v pořadí kandidátních listin. Docházka nezachycuje práci ve výborech, komisích a mimo zasedání.</td></tr>
      <tr><td><b>Časová osa</b></td><td>ručně vybrané milníky podle výše částky a dlouhodobého dopadu; úplný přehled je v sekci Zastupitelstvo</td></tr>
    </tbody></table>
  </div>
</section>

<section>
  <div class="sec-h"><h2>Školství, demografie a volby</h2></div>
  <div class="panel">
    <p><b>Demografie:</b> počty obyvatel obce k 1. 1. z ČSÚ. <b>Školství:</b> data ČSÚ a rejstříku škol MŠMT (kapacita = nejvyšší povolený počet dětí/žáků v rejstříku, ne aktuální prostorové možnosti). <b>Volby:</b> výsledky voleb v obci z <a href="https://www.volby.cz" {A}>volby.cz</a> (ČSÚ).</p>
  </div>
</section>

<section>
  <div class="sec-h"><h2>Hledání</h2></div>
  <div class="panel">
    <p>Hledání prochází usnesení zastupitelstva, zakázky, příjemce dotací a rozpočtové oblasti — přímo v prohlížeči, nic se nikam neodesílá.</p>
  </div>
</section>

<section>
  <div class="sec-h"><h2>Stažení dat</h2></div>
  <div class="panel">
    <p>U hlavních tabulek najdete tlačítko <span class="dlbtn" style="cursor:default">⬇ Stáhnout CSV</span> — stáhne právě zobrazená data (oddělovač středník, kódování UTF-8, otevře se přímo v Excelu). Surová zdrojová data jsou k dispozici v původních zdrojích: <a href="https://monitor.statnipokladna.gov.cz/datovy-katalog/open-data" {A}>MONITOR open data</a>, <a href="https://data.csu.gov.cz" {A}>ČSÚ</a>, <a href="https://www.ostopovice.cz" {A}>web obce</a>.</p>
  </div>
</section>'''

body += '<style>.mtab{{width:100%;border-collapse:collapse;font-size:13.5px;margin:10px 0}}.mtab td{{padding:8px 10px;border-bottom:1px solid var(--line);vertical-align:top;text-align:left;white-space:normal}}.mtab td:first-child{{width:32%}}.panel p{{line-height:1.6}}</style>'.replace("{{", "{").replace("}}", "}")
html = pc.page("Metodika", "Metodika a zdroje dat — Jak žijí Ostopovice", body)
open("metodika.html", "w", encoding="utf-8").write(html)
print("HOTOVO: metodika.html")
