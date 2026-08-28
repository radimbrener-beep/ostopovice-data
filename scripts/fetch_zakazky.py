#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stáhne veřejné zakázky obce Ostopovice z profilu zadavatele
(vhodne-uverejneni.cz/profil/obec-ostopovice) → data/zakazky.json.

Profil má několik tabulek (probíhající, ukončené, starší) se samostatným
stránkováním (?page-<sekce>=N). Projdeme všechny stránky všech sekcí,
z řádku vezmeme název, předpokládanou hodnotu (bez DPH) a datum uveřejnění."""
import sys, re, json
from pathlib import Path
import requests
from bs4 import BeautifulSoup
sys.stdout.reconfigure(encoding="utf-8")

PROFIL = "https://www.vhodne-uverejneni.cz/profil/obec-ostopovice"
H = {"User-Agent": "Mozilla/5.0 (compatible; OstopovicePortalBot/1.0)"}
ROOT = Path(__file__).resolve().parent.parent


def soup(params=None):
    r = requests.get(PROFIL, params=params, headers=H, timeout=60)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")


def num(s):
    s = re.sub(r"[^\d,]", "", s or "").replace(",", ".")
    try:
        return round(float(s))
    except ValueError:
        return None


def rows(s):
    out = []
    for t in s.find_all("table"):
        heads = [th.get_text(" ", strip=True) for th in t.find_all("th")]
        if not heads or not heads[0].startswith("Název zakázky"):
            continue
        for tr in t.find_all("tr"):
            a = tr.find("a", href=re.compile(r"/zakazka/"))
            if not a:
                continue
            cells = [c.get_text(" ", strip=True) for c in tr.find_all("td")]
            out.append({"nazev": a.get_text(" ", strip=True),
                        "hodnota": num(cells[1]) if len(cells) > 1 else None,
                        "datum": cells[3] if len(cells) > 3 else "",
                        "url": a["href"] if a["href"].startswith("http") else "https://www.vhodne-uverejneni.cz" + a["href"]})
    return out


first = soup()
found = {r["url"]: r for r in rows(first)}
# všechny stránkovací parametry (page-supply, page-finished, …) a jejich maxima
pages = {}
for a in first.find_all("a", href=True):
    m = re.search(r"\?(page-[\w-]+)=(\d+)", a["href"])
    if m:
        pages[m.group(1)] = max(pages.get(m.group(1), 1), int(m.group(2)))
for par, mx in pages.items():
    for n in range(2, mx + 1):
        for r in rows(soup({par: n})):
            found.setdefault(r["url"], r)

data = sorted(found.values(), key=lambda r: (r["datum"][6:10], r["datum"][3:5], r["datum"][:2]), reverse=True)
if len(data) < 5:
    sys.exit(f"Podezřele málo zakázek ({len(data)}) — profil se asi změnil, data neukládám.")
(ROOT / "data" / "zakazky.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
tot = sum(r["hodnota"] or 0 for r in data)
print(f"HOTOVO -> data/zakazky.json | {len(data)} zakázek, {tot/1e6:.1f} mil. Kč (stránky: {pages})")
