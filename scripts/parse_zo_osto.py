#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scraper + parser zápisů ze zasedání zastupitelstva obce Ostopovice u Brna.
Web: ostopovice.cz (CMS ANTEE), zápisy jsou čisté textové PDF se strukturou:
    Usnesení č. X.Y – N/RRRR
    Zastupitelstvo obce Ostopovice <sloveso> ...
    Hlasování: pro N proti N zdržel se N
Vrací dict kompatibilní s dataset_ZO.json (obdoba portálu Střelice).
"""
import re, sys, io, json
from pathlib import Path
import requests
import pdfplumber
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import temata, vydaje, anonym

BASE = "https://www.ostopovice.cz"
ORGANY_URL = BASE + "/organy-obce"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; OstopovicePortalBot/1.0)"}

# odkaz na PDF zápisu ZO: text "Zápis z N. zasedání zastupitelstva obce ze dne D. M. RRRR"
LINK_TITLE_RE = re.compile(
    r'Z[áa]pis\s+z[e]?\s+(\d+)\.\s+zased[áa]n[íi]\s+zastupitelstva\s+obce\s+ze\s+dne\s+'
    r'(\d{1,2})\.\s*(\d{1,2})\.\s*(\d{4})', re.I)

# usnesení: "Usnesení č. 1.1 – 5/2025"
# běžně „Usnesení č. 5.1 – 6/2022", na ustavujícím zasedání
# „Usnesení č. 5. 1 – ustavující zasedání 2022" (čísla s mezerou/tečkou na konci)
USN_MARK_RE = re.compile(
    r'Usnesen[íi]\s+č\.\s*(\d+(?:\.\s*\d+)?)\.?\s*[–\-]\s*'
    r'(?:(\d+)\s*/\s*(\d{4})|(ustavuj[íi]c[íi])\s+zased[áa]n[íi]\s+(\d{4}))', re.I)
# u voleb do funkcí chybí řádek „Hlasování:" — text usnesení pak končí tady
TEXT_END_RE = re.compile(r'Před\s+hlasováním\s+byla\s+dána\s+možnost', re.I)
# hlasování: "Hlasování: pro 12 proti 0 zdržel se 0"
HLAS_RE = re.compile(
    r'Hlasov[áa]n[íi]\s*:?\s*pro\s+(\d+)[,\s]*proti\s+(\d+)[,\s]*zdržel[iy]?\s*se\s+(\d+)', re.I)

DATE_HDR_RE = re.compile(r'konan[éeě]m?\s+dne\s+(\d{1,2})\.\s*(\d{1,2})\.\s*(\d{4})', re.I)
CISLO_HDR_RE = re.compile(r'(\d+)\.\s*ZASED[ÁA]N[ÍI]\s+ZASTUPITELSTVA', re.I)

# druh usnesení (sloveso za "Zastupitelstvo obce ...")
_KATS = [
    (re.compile(r'\bneschvaluje\b', re.I), 'neschvaluje'),
    (re.compile(r'\bschvaluje\b', re.I), 'schvaluje'),
    (re.compile(r'\bbere\s+na\s+vědomí\b', re.I), 'bere na vědomí'),
    (re.compile(r'\bpověřuje\b', re.I), 'pověřuje'),
    (re.compile(r'\bukládá\b', re.I), 'ukládá'),
    (re.compile(r'\bsouhlasí\b', re.I), 'souhlasí'),
    (re.compile(r'\bnesouhlasí\b', re.I), 'nesouhlasí'),
    (re.compile(r'\bvydává\b', re.I), 'vydává'),
    (re.compile(r'\bvolí\b', re.I), 'volí'),
    (re.compile(r'\bzřizuje\b', re.I), 'zřizuje'),
    (re.compile(r'\brozhoduje\b', re.I), 'rozhoduje'),
    (re.compile(r'\bstanov[íi]\b', re.I), 'stanoví'),
    (re.compile(r'\bdeleguje\b', re.I), 'deleguje'),
    (re.compile(r'\bjmenuje\b', re.I), 'jmenuje'),
    (re.compile(r'\bod(?:volává|kládá)\b', re.I), 'jiné'),
]
def detect_kat(text):
    for pat, kat in _KATS:
        if pat.search(text):
            return kat
    return 'jiné'


def _fetch(url, timeout=40):
    r = requests.get(url, headers=HEADERS, timeout=timeout)
    r.raise_for_status()
    return r


def scrape_zo_links():
    """Vrátí seznam dictů {cislo, datum, datum_text, rok, url, titul} pro ZO zápisy."""
    soup = BeautifulSoup(_fetch(ORGANY_URL).text, "html.parser")
    out, seen = [], set()
    for a in soup.find_all("a", href=True):
        title = a.get_text(" ", strip=True)
        m = LINK_TITLE_RE.search(title)
        if not m:
            continue
        cislo = int(m.group(1)); d, mn, y = int(m.group(2)), int(m.group(3)), int(m.group(4))
        href = a["href"]
        url = href if href.startswith("http") else BASE + href
        key = (cislo, y)
        if key in seen:
            continue
        seen.add(key)
        out.append({"cislo": cislo, "datum": f"{y}-{mn:02d}-{d:02d}",
                    "datum_text": f"{d}. {mn}. {y}", "rok": y, "url": url, "titul": title})
    return out


def pdf_text(source):
    if isinstance(source, str) and source.startswith("http"):
        source = io.BytesIO(_fetch(source).content)
    with pdfplumber.open(source) as pdf:
        return "\n".join(p.extract_text() or "" for p in pdf.pages)


def _clean(text):
    text = re.sub(r'\s+', ' ', text).strip()
    # číslo stránky „- 3 -" uprostřed věty (rozdělí třeba „paní - 3 - Jméno" a jméno by unikl anonymizaci)
    text = re.sub(r'\s-\s?\d{1,3}\s?-\s', ' ', text)
    # odstraň osamocená čísla stránek na konci
    text = re.sub(r'\s+\d{1,3}$', '', text)
    return text.strip().rstrip('.').strip()


# docházka v hlavičce zápisu: „Přítomno: 12 zastupitelů … Omluveni: J. Ochvat, J. Šebánek"
PRITOMNO_RE = re.compile(r'Přítomno\s*:?\s*(\d+)', re.I)
OMLUVENI_RE = re.compile(r'Omluven[iíy]\s*:?\s*([^\n]*)', re.I)
DOSTAVIL_RE = re.compile(r'dostavil[ai]?\s+((?:[A-ZÁ-Ž][a-zá-ž]*\.?\s*)?[A-ZÁ-Ž][a-zá-ž]+)')


def dochazka(raw):
    """Vrátí (počet přítomných na začátku, [omluvení], [pozdní příchody]) — jména tak, jak jsou v zápise."""
    head = raw[:4000]
    pm = PRITOMNO_RE.search(head)
    om = OMLUVENI_RE.search(head)
    omluveni = []
    if om:
        val = om.group(1).strip()
        if not re.fullmatch(r'0|nikdo|-|–|', val, re.I):
            omluveni = [x.strip(" .") for x in re.split(r',|\s+a\s+', val) if x.strip(" .")]
    pozdni = [x.strip() for x in DOSTAVIL_RE.findall(head)]
    return (int(pm.group(1)) if pm else None), omluveni, pozdni


def parse(source, cislo_hint=None, datum_hint=None, datum_text_hint=None, rok_hint=None):
    url = source if isinstance(source, str) and source.startswith("http") else ""
    raw = pdf_text(source)

    # číslo a datum: primárně z hintů (z názvu odkazu), jinak z hlavičky
    cislo = cislo_hint
    if cislo is None:
        cm = CISLO_HDR_RE.search(raw); cislo = int(cm.group(1)) if cm else 0
    datum, datum_text, rok = datum_hint, datum_text_hint, rok_hint
    if not datum:
        dm = DATE_HDR_RE.search(raw)
        if dm:
            d, mn, y = int(dm.group(1)), int(dm.group(2)), int(dm.group(3))
            datum, datum_text, rok = f"{y}-{mn:02d}-{d:02d}", f"{d}. {mn}. {y}", y

    pritomno, omluveni, pozdni = dochazka(raw)

    # rozdělení na bloky podle markerů "Usnesení č. ..."
    marks = list(USN_MARK_RE.finditer(raw))
    body = []
    seen_ids = set()
    for i, mk in enumerate(marks):
        num = re.sub(r'\s+', '', mk.group(1))
        usn_id = (f"{num} – {mk.group(2)}/{mk.group(3)}" if mk.group(2)
                  else f"{num} – ustavující {mk.group(5)}")
        start = mk.end()
        end = marks[i + 1].start() if i + 1 < len(marks) else len(raw)
        block = raw[start:end]

        # hlasování v bloku
        hm = HLAS_RE.search(block)
        hlas = [int(hm.group(1)), int(hm.group(2)), int(hm.group(3))] if hm else [None, None, None]
        # text usnesení = od začátku bloku po "Hlasování" (příp. po úvodu k diskuzi)
        text_part = block[:hm.start()] if hm else block
        te = TEXT_END_RE.search(text_part)
        if te:
            text_part = text_part[:te.start()]
        text = _clean(text_part)
        if len(text) < 6:
            continue
        # některé zápisy obsahují na konci ještě jednou výpis všech usnesení
        # (a v textu se na usnesení odkazuje) — každé usnesení bereme jen poprvé
        if usn_id in seen_ids:
            continue
        seen_ids.add(usn_id)
        text = anonym.anonymize(vydaje.fix_ocr_digits(text))
        amt = vydaje.extract_amount(text)
        body.append({
            "usneseni_id": usn_id,
            "kategorie": detect_kat(text),
            "tema": temata.classify(text),
            "castka": amt,
            "vydaj": vydaje.bucket(amt),
            "hlasovani": hlas,
            "text": text,
        })

    return {
        "soubor": url.split("/")[-1] if url else "",
        "url": url,
        "cislo_zasedani": cislo,
        "datum": datum or "",
        "datum_text": datum_text or "",
        "rok": rok,
        "pocet_bodu": len(body),
        "pritomno": pritomno,
        "omluveni": omluveni,
        "pozdni_prichod": pozdni,
        "body": body,
    }


if __name__ == "__main__":
    # smoke test: vypíše nalezené zápisy a naparsuje nejnovější
    links = scrape_zo_links()
    sys.stdout.reconfigure(encoding="utf-8")
    print(f"Nalezeno ZO zápisů: {len(links)}")
    for l in links[:6]:
        print(f"  ZO {l['cislo']}/{l['rok']} — {l['datum_text']}")
    if links:
        e = parse(links[0]["url"], cislo_hint=links[0]["cislo"],
                  datum_hint=links[0]["datum"], datum_text_hint=links[0]["datum_text"], rok_hint=links[0]["rok"])
        print(f"\nNejnovější ZO {e['cislo_zasedani']} ({e['datum_text']}): {e['pocet_bodu']} usnesení")
        for b in e["body"][:4]:
            print(f"  - [{b['kategorie']}] {b['usneseni_id']} | hlas {b['hlasovani']} | {b['text'][:70]}")
