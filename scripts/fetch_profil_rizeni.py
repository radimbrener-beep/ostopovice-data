#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stáhne výběrová řízení obce Ostopovice z XML exportu profilu zadavatele
(vhodne-uverejneni.cz, formát MMR vz-z-profilu-zadavatele v100) → data/profil_rizeni.json.
Doplňuje data/zakazky.json (seznam z HTML profilu) o nabídky, vybranou firmu, cenu,
lhůtu a druh řízení. Používá ho MCP export (build_mcp.py, nástroj vyberova_rizeni).

Export vrací nejvýš 365 dní na dotaz a je pomalý (až desítky sekund), proto se stahuje
po pololetích a denně jen poslední rok; starší pololetí se berou z minulého běhu.
Předpokládanou hodnotu a odkaz na detail export nemá → páruje se s data/zakazky.json
podle názvu.

Stav: zadáno (vybraná firma, nebo obec řízení vede jako dokončené) / zrušeno /
probíhá (běží lhůta nebo od jejího konce uplynulo méně než 120 dní) / bez výsledku.

    python scripts/fetch_profil_rizeni.py
"""
import json
import re
import sys
import unicodedata
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date, timedelta
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "profil_rizeni.json"
PROFIL = "https://www.vhodne-uverejneni.cz/profil/obec-ostopovice"
OD_ROKU = 2018
H = {"User-Agent": "Mozilla/5.0 (compatible; OstopovicePortalBot/1.0)"}
CEKANI_DNU = 120
HOTOVO = {"dokončen", "ukončeno plnění"}


def tag(e):
    return e.tag.split("}")[1]


def find(e, name):
    return [x for x in e.iter() if tag(x) == name]


def txt(e, name):
    x = find(e, name)
    return (x[0].text or "").strip() if x else ""


def num(s):
    try:
        v = float(s)
    except (TypeError, ValueError):
        return None
    return round(v) if v else None


def klic(s):
    s = unicodedata.normalize("NFD", s or "")
    return re.sub(r"[^a-z0-9]+", "", "".join(c for c in s if not unicodedata.combining(c)).lower())


def firma(subjekt):
    n = re.sub(r"\s+", " ", txt(subjekt, "nazev_subjektu"))
    n = re.split(r",?\s+(?:sídlem|se sídlem|IČO?:?)\s", n)[0]
    n = re.split(r",\s+(?=[^,]*\d)", n)[0]
    return n.strip(" ,")


def ico(subjekt):
    return re.sub(r"\D", "", txt(subjekt, "ico"))


def pololeti(dnes):
    for y in range(OD_ROKU, dnes.year + 1):
        for a, b in ((date(y, 1, 1), date(y, 6, 30)), (date(y, 7, 1), date(y, 12, 31))):
            if a <= dnes:
                yield a, min(b, dnes)


def stahni(a, b):
    url = f"{PROFIL}/XMLdataVZ?od={a:%d%m%Y}&do={b:%d%m%Y}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=H), timeout=120) as r:
        return ET.fromstring(r.read())


def rizeni(zk, dnes, seznam):
    zid = txt(zk, "id_objektu")
    casti = find(zk, "cast_zakazky") or [zk]
    for i, cast in enumerate(casti, 1):
        nazev = re.sub(r"\s+", " ", txt(cast, "nazev_casti_vz") or txt(zk, "nazev_vz")).strip(" „“\"")
        vyb = find(cast, "vybrany_dodavatel")
        vyb_ico = ico(vyb[0]) if vyb else ""
        nabidky = [{"firma": firma(u), "ico": ico(u), "cena": num(txt(u, "nabidkova_cena_bez_dph")),
                    "vyloucen": txt(u, "ucastnik_vyloucen") == "1" or txt(u, "ucastnik_odstoupil") == "1"}
                   for u in find(cast, "ucastnik") if firma(u)]   # prázdní účastníci bez firmy a ceny
        cena = num(txt(vyb[0], "smluvni_cena_bez_DPH")) if vyb else None
        if vyb and not cena:
            cena = next((n["cena"] for n in nabidky if n["ico"] and n["ico"] == vyb_ico), None)
        lhuta = next((txt(l, "datum_konce_lhuty") for l in find(cast, "lhuta")
                      if "nabídk" in txt(l, "druh_lhuty")), "")[:16]
        z = seznam.get(klic(nazev), {})
        datum = (txt(cast, "datum_uverejneni") or txt(zk, "datum_uverejneni"))[:10]
        if not datum and re.match(r"\d\d\.\d\d\.\d{4}$", z.get("datum") or ""):
            datum = f"{z['datum'][6:]}-{z['datum'][3:5]}-{z['datum'][:2]}"
        stav_profil = txt(cast, "stav_zadavaciho_postupu")
        if vyb or stav_profil in HOTOVO:
            stav = "zadáno"
        elif stav_profil.startswith("zrušen"):
            stav = "zrušeno"
        else:
            konec = (lhuta or datum)[:10]
            stav = "probíhá" if konec and (dnes - date.fromisoformat(konec)).days <= CEKANI_DNU else "bez výsledku"
        yield {
            "id": zid if len(casti) == 1 else f"{zid}/{i}",
            "url": z.get("url") or PROFIL,
            "nazev": nazev,
            "druh": txt(cast, "druh_casti_vz") or txt(zk, "druh_vz"),
            "postup": txt(cast, "druh_zadavaciho_postupu"),
            "datum": datum,
            "lhuta": lhuta,
            "predpokladana_hodnota": z.get("hodnota"),
            "nabidky": nabidky,
            "dodavatel": firma(vyb[0]) if vyb else "",
            "dodavatel_ico": vyb_ico,
            "cena": cena,
            "stav": stav,
        }


def main():
    dnes = date.today()
    old = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {"zakazky": [], "stazeno": []}
    hotova = set(old.get("stazeno", []))   # pololetí starší než rok se už nemění
    seznam = {klic(z["nazev"]): z for z in json.loads((ROOT / "data" / "zakazky.json").read_text(encoding="utf-8"))}
    nove, stazeno, chyby = {}, [], 0
    for a, b in pololeti(dnes):
        okno = f"{a:%Y-%m-%d}"
        if okno in hotova and b < dnes - timedelta(days=366):
            stazeno.append(okno)
            continue
        try:
            root = stahni(a, b)
        except Exception as e:   # výpadek okna: ponechat stará data z tohoto období
            print(f"  {okno}: export nedostupný ({e})")
            chyby += 1
            continue
        for zk in (c for c in root if tag(c) == "zakazka"):
            for r in rizeni(zk, dnes, seznam):
                nove[r["id"]] = r
        if b < dnes - timedelta(days=366):
            stazeno.append(okno)
    # zakázky z nestažených oken (starší nebo výpadek) převzít z minulého běhu
    for r in old["zakazky"]:
        nove.setdefault(r["id"], r)
    data = sorted(nove.values(), key=lambda r: r["datum"], reverse=True)
    pribylo = [r for r in data if r["id"] not in {o["id"] for o in old["zakazky"]}]
    OUT.write_text(json.dumps({"profil": PROFIL, "stazeno": sorted(set(stazeno)), "zakazky": data},
                              ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"HOTOVO -> data/profil_rizeni.json | {len(data)} řízení, s nabídkami "
          f"{sum(1 for r in data if r['nabidky'])}, nových {len(pribylo)}, výpadků oken {chyby}")


if __name__ == "__main__":
    main()
