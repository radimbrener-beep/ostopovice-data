#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stáhne z registru smluv (smlouvy.gov.cz) smlouvy, kde je obec Ostopovice protistranou,
→ data/smlouvy_obec.json. Jsou to hlavně dotace, které obec získala (SZIF, SFDI, SFŽP…),
a dohody o spolufinancování se správci silnic. Sama obec do registru nezveřejňuje
(vyhledávání podle její datové schránky nic nevrací), takže tohle je jediný zdroj z registru.

Postup jako ruční export: podrobné vyhledávání → „Exportovat do XLSX“ (jen poslední verze).

    python scripts/fetch_smlouvy.py
"""
import io
import json
import re
import sys
from pathlib import Path

import openpyxl
import requests

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "smlouvy_obec.json"
ICO = "00282294"
URL = "https://smlouvy.gov.cz/vyhledavani"
# získané dotace (ne spolufinancování ani návratná výpomoc — tam obec platí, nebo si půjčuje)
DOTACE = re.compile(r"dotac|poskytnutí podpory|poskytnutí finančních prostředků", re.I)


def hodnota(*vals):
    for v in vals:
        if isinstance(v, (int, float)) and v:
            return round(v)
    return None


def datum(s):
    m = re.match(r"(\d{2})\.(\d{2})\.(\d{4})", s or "")
    return f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else ""


def main():
    s = requests.Session()
    s.headers["User-Agent"] = "Mozilla/5.0 (compatible; OstopovicePortalBot/1.0)"
    s.get(URL, timeout=60)   # cookie sezení, bez něj export nevrátí soubor
    r = s.get(URL, timeout=300, params={"party_idnum": ICO, "search_type": "0",
                                        "do": "detailedSearchForm-submit", "export": "Exportovat do XLSX"})
    r.raise_for_status()
    if "spreadsheet" not in r.headers.get("Content-Type", ""):
        sys.exit("Registr smluv nevrátil XLSX — data neukládám.")
    rows = list(openpyxl.load_workbook(io.BytesIO(r.content), read_only=True).active.iter_rows(values_only=True))
    h = {n: i for i, n in enumerate(rows[0]) if n}
    g = lambda row, n: row[h[n]] if n in h and h[n] < len(row) else None
    out = []
    for row in rows[1:]:
        nazev = re.sub(r"\s+", " ", str(g(row, "Textové označení smlouvy") or "")).strip()
        out.append({
            "datum": datum(g(row, "Datum uzavření")) or datum(g(row, "Publikováno")),
            "partner": re.sub(r"\s+", " ", str(g(row, "Publikující smluvní strana") or "")).strip(),
            "nazev": nazev,
            "hodnota": hodnota(g(row, "Hodnota smlouvy vč. DPH"), g(row, "Hodnota smlouvy bez DPH")),
            "url": g(row, "Adresa záznamu") or "",
            "dotace": bool(DOTACE.search(nazev)),
        })
    out.sort(key=lambda x: x["datum"], reverse=True)
    if not out:
        sys.exit("Registr smluv nevrátil žádnou smlouvu — data neukládám.")
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"HOTOVO -> {OUT.name} | {len(out)} smluv, z toho získané dotace {sum(x['dotace'] for x in out)}")


if __name__ == "__main__":
    main()
