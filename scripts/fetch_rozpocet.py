#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stáhne rozpočet obce Ostopovice z API MONITORu Státní pokladny
(monitor.statnipokladna.gov.cz/api) a uloží do data/rozpocet_ostopovice.json.

Endpointy: /rozpocet (souhrn), /rozpocet/druhovy (dle druhu), /rozpocet/odvetvovy
(dle oblastí). Období = loadID ve tvaru RRMM (roční = prosinec, RR12).
Uložené:
  years[]        souhrn po uzavřených letech (schválený / upravený / skutečnost)
  struktura{rok} příjmy dle druhu + výdaje dle druhu a oddílu (pro Sankey a grafy)
  aktualni       průběžné plnění běžícího roku (poslední dostupný měsíc)"""
import sys, json
from pathlib import Path
import requests
sys.stdout.reconfigure(encoding="utf-8")

IC = "00282294"
API = "https://monitor.statnipokladna.gov.cz/api"
H = {"User-Agent": "Mozilla/5.0"}
ROOT = Path(__file__).resolve().parent.parent
# „k <měsíci>" (3. pád)
MESICE = ["lednu", "únoru", "březnu", "dubnu", "květnu", "červnu", "červenci",
          "srpnu", "září", "říjnu", "listopadu", "prosinci"]

def get(path, **params):
    r = requests.get(f"{API}/{path}", params={**params, "ic": IC}, headers=H, timeout=60)
    r.raise_for_status()
    return r.json()

def b3(node):
    b = node.get("budget") or node
    return {"schv": round(b.get("approved") or 0), "uprav": round(b.get("afterChanges") or 0),
            "skut": round(b.get("reality") or 0)}

def souhrn(lid):
    s = get("rozpocet", obdobi=lid)
    return b3(s["incomes"]), b3(s["outgoings"])

def struktura(lid):
    dp = get("rozpocet/druhovy", obdobi=lid, cast="p")
    dv = get("rozpocet/druhovy", obdobi=lid, cast="v")
    ov = get("rozpocet/odvetvovy", obdobi=lid, cast="v")
    oddily = []
    for skup in ov["children"]:
        for k in (skup.get("children") or [skup]):
            v = b3(k)
            if v["skut"] or v["uprav"]:
                oddily.append({"name": k["name"], **v})
    oddily.sort(key=lambda x: -x["skut"])
    return {"prijmy_druh": [{"name": c["name"], **b3(c)} for c in dp["children"] if b3(c)["skut"] or b3(c)["uprav"]],
            "vydaje_druh": [{"name": c["name"], **b3(c)} for c in dv["children"] if b3(c)["skut"] or b3(c)["uprav"]],
            "vydaje_oblast": oddily}

obdobi = requests.get(f"{API}/obdobi", headers=H, timeout=60).json()
po_letech = {}
for e in obdobi:
    po_letech.setdefault(e["year"], []).append(e["loadID"])

years, struk, aktualni = [], {}, None
for y in sorted(po_letech):
    rocni = int(f"{y % 100:02d}12")
    pr, vy = souhrn(rocni) if rocni in po_letech[y] else ({"skut": 0}, {"skut": 0})
    if pr["skut"] or vy["skut"]:
        years.append({"rok": y, "obdobi": rocni, "prijmy": pr, "vydaje": vy})
        struk[str(y)] = struktura(rocni)
        print(f"  {y}: příjmy {pr['skut']/1e6:,.1f} / výdaje {vy['skut']/1e6:,.1f} mil.")
        continue
    # běžící rok: poslední měsíc, za který jsou data
    for lid in sorted(po_letech[y], reverse=True):
        pr, vy = souhrn(lid)
        if pr["skut"] or vy["skut"]:
            aktualni = {"rok": y, "obdobi": lid, "mesic": MESICE[lid % 100 - 1],
                        "prijmy": pr, "vydaje": vy, **struktura(lid)}
            print(f"  {y} (k {aktualni['mesic']}): příjmy {pr['skut']/1e6:,.1f} z {pr['uprav']/1e6:,.1f} "
                  f"/ výdaje {vy['skut']/1e6:,.1f} z {vy['uprav']/1e6:,.1f} mil.")
            break

last = years[-1]["rok"]
DATA = {"obec": "Ostopovice", "ic": IC, "pop": 1751, "posledni_rok": last, "years": years,
        "struktura": struk, "aktualni": aktualni,
        # zpětná kompatibilita (graf posledního roku)
        "prijmy_druh": struk[str(last)]["prijmy_druh"],
        "vydaje_druh": struk[str(last)]["vydaje_druh"],
        "vydaje_oblast": struk[str(last)]["vydaje_oblast"],
        "zdroj": "MONITOR Státní pokladny (MF ČR), výkaz FIN 2-12 M"}
out = ROOT / "data" / "rozpocet_ostopovice.json"
out.write_text(json.dumps(DATA, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"\nHOTOVO -> {out}  ({len(years)} let {years[0]['rok']}-{last}"
      + (f", běžící rok {aktualni['rok']} k {aktualni['mesic']}" if aktualni else "") + ")")
