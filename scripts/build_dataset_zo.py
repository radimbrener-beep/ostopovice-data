#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stáhne a naparsuje všechny ZO zápisy Ostopovic -> dataset_ZO.json."""
import sys, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import parse_zo_osto as P
sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://www.ostopovice.cz"

# Web obce renderuje accordion se zápisy NEKONZISTENTNĚ (dvě cache varianty,
# každá s jiným výběrem zápisů). Scraper vezme, co je právě k dispozici, a
# doplní se známé přímé oidy (zachycené z obou variant). Nové zápisy přibydou
# scrapem; když je některá varianta neukáže, stačí oid doplnit sem.
# cislo 0 = ustavující zasedání.
EXTRA = [
    {"cislo": 1, "rok": 2022, "datum": "2022-03-03", "datum_text": "3. 3. 2022", "oid": "9003738"},
    {"cislo": 2, "rok": 2022, "datum": "2022-05-26", "datum_text": "26. 5. 2022", "oid": "9172850"},
    {"cislo": 3, "rok": 2022, "datum": "2022-06-23", "datum_text": "23. 6. 2022", "oid": "9172859"},
    {"cislo": 4, "rok": 2022, "datum": "2022-09-08", "datum_text": "8. 9. 2022", "oid": "9379030"},
    {"cislo": 0, "rok": 2022, "datum": "2022-10-20", "datum_text": "20. 10. 2022", "oid": "9461158"},
    {"cislo": 6, "rok": 2022, "datum": "2022-12-15", "datum_text": "15. 12. 2022", "oid": "9672222"},
    {"cislo": 1, "rok": 2023, "datum": "2023-03-02", "datum_text": "2. 3. 2023", "oid": "9834392"},
    {"cislo": 2, "rok": 2023, "datum": "2023-05-18", "datum_text": "18. 5. 2023", "oid": "10202174"},
    {"cislo": 3, "rok": 2023, "datum": "2023-06-29", "datum_text": "29. 6. 2023", "oid": "10249323"},
    {"cislo": 4, "rok": 2023, "datum": "2023-08-31", "datum_text": "31. 8. 2023", "oid": "10320700"},
    {"cislo": 5, "rok": 2023, "datum": "2023-10-12", "datum_text": "12. 10. 2023", "oid": "10502299"},
    {"cislo": 6, "rok": 2023, "datum": "2023-12-14", "datum_text": "14. 12. 2023", "oid": "10799021"},
    {"cislo": 1, "rok": 2024, "datum": "2024-03-14", "datum_text": "14. 3. 2024", "oid": "10903355"},
    {"cislo": 2, "rok": 2024, "datum": "2024-06-13", "datum_text": "13. 6. 2024", "oid": "11330646"},
    {"cislo": 3, "rok": 2024, "datum": "2024-09-12", "datum_text": "12. 9. 2024", "oid": "11617153"},
    {"cislo": 4, "rok": 2024, "datum": "2024-11-14", "datum_text": "14. 11. 2024", "oid": "11710279"},
    {"cislo": 5, "rok": 2024, "datum": "2024-12-19", "datum_text": "19. 12. 2024", "oid": "12531133"},
    {"cislo": 1, "rok": 2025, "datum": "2025-03-13", "datum_text": "13. 3. 2025", "oid": "12166163"},
    {"cislo": 2, "rok": 2025, "datum": "2025-05-22", "datum_text": "22. 5. 2025", "oid": "12501923"},
    {"cislo": 3, "rok": 2025, "datum": "2025-08-21", "datum_text": "21. 8. 2025", "oid": "12643013"},
    {"cislo": 4, "rok": 2025, "datum": "2025-10-16", "datum_text": "16. 10. 2025", "oid": "12852929"},
    {"cislo": 5, "rok": 2025, "datum": "2025-12-18", "datum_text": "18. 12. 2025", "oid": "13035273"},
    {"cislo": 1, "rok": 2026, "datum": "2026-03-12", "datum_text": "12. 3. 2026", "oid": "13655482"},
    {"cislo": 2, "rok": 2026, "datum": "2026-06-11", "datum_text": "11. 6. 2026", "oid": "13834950"},
]

# scrape s opakováním + sloučení (kvůli nekonzistentnímu webu)
links = {}
for _ in range(3):
    for l in P.scrape_zo_links():
        links[(l["rok"], l["cislo"])] = l
for e in EXTRA:
    key = (e["rok"], e["cislo"])
    if key not in links:
        links[key] = {"cislo": e["cislo"], "rok": e["rok"], "datum": e["datum"],
                      "datum_text": e["datum_text"],
                      "url": f"{BASE}/file.php?nid=18899&oid={e['oid']}", "titul": ""}
links = list(links.values())
print(f"Nalezeno {len(links)} ZO zápisů (scrape + známé oidy), parsuju…")
data = []
for l in sorted(links, key=lambda x: (x["rok"], x["cislo"])):
    try:
        e = P.parse(l["url"], cislo_hint=l["cislo"], datum_hint=l["datum"],
                    datum_text_hint=l["datum_text"], rok_hint=l["rok"])
        data.append(e)
        print(f"  ZO {e['cislo_zasedani']}/{e['rok']} {e['datum_text']:>12} -> {e['pocet_bodu']} usnesení")
    except Exception as ex:
        print(f"  CHYBA ZO {l['cislo']}/{l['rok']}: {ex}")

(ROOT / "dataset_ZO.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
tot = sum(m["pocet_bodu"] for m in data)
yrs = sorted({m["rok"] for m in data})
print(f"\nHOTOVO -> dataset_ZO.json | {len(data)} zasedání, {tot} usnesení, roky {yrs}")
