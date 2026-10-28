# -*- coding: utf-8 -*-
"""Data Ostopovic pro MCP server jaksemame.cz/mcp → mcp/ostopovice.sqlite (viz mcp_export.py,
kopie ze Střelic — při změně formátu zkopírovat znovu).

Zápisy zastupitelstva jsou úplné (i s rozpravou v textu), už anonymizované parserem.
Rada obce zápisy nezveřejňuje. Zakázky jsou z profilu zadavatele (bez dodavatele)."""
import json
import os
import sys
from datetime import datetime

import mcp_export as mx

OUT = "mcp/ostopovice.sqlite"


def embedded(path):
    """DATA vložená do vygenerované stránky (`const D=<json>`)."""
    s = open(path, encoding="utf-8").read()
    i = s.index("const D=") + len("const D=")
    return json.JSONDecoder().raw_decode(s, i)[0]


def iso(d):
    return datetime.strptime(d, "%d.%m.%Y").date().isoformat()


def main():
    roz = json.load(open("data/rozpocet_ostopovice.json", encoding="utf-8"))
    ex = mx.Export(OUT, "ostopovice", "Ostopovice", "https://ostopovice.jaksemame.cz",
                   kod_obce="583596", ico="00282294", obyvatel=roz.get("pop"), okres="Brno-venkov",
                   sekce=["jednani_zo", "rozpocet", "investice", "zakazky", "vyberova_rizeni", "dotace"],
                   poznamky={
                       "jednani_zo": "Zápisy zastupitelstva jsou úplné včetně rozpravy (kdo co řekl je přímo "
                                     "v textu usnesení/zápisu). Jména soukromých osob portál zkracuje na iniciály.",
                       "jednani_ro": "Obec zápisy z rady nezveřejňuje.",
                       "castky": "Částky u usnesení jsou automaticky vytažené z textu zápisu; u důležitých "
                                 "rozhodnutí je ověř v PDF.",
                       "zakazky": "Zakázky jsou z profilu zadavatele (vhodne-uverejneni.cz): název, hodnota a "
                                  "datum, bez vítězného dodavatele. Nabídky a vybranou firmu vrací vyberova_rizeni.",
                       "vyberova_rizeni": "Výběrová řízení z XML exportu profilu zadavatele (vhodne-uverejneni.cz). "
                                          "Nabídky a vybranou firmu obec uvádí jen u menší části řízení; většina "
                                          "je přímé zadání bez soutěže. Ceny bez DPH, jak je obec zapsala.",
                       "rozpocet": "Rozpočet z MONITORu MF (FIN 2-12 M) jen v souhrnech: druhové třídění "
                                   "a výdaje podle oblastí; rok 2026 je průběžný stav.",
                   })

    shrnuti = json.load(open("data/shrnuti/zo.json", encoding="utf-8")) if os.path.exists("data/shrnuti/zo.json") else {}
    for z in json.load(open("dataset_ZO.json", encoding="utf-8")):
        n, rok = int(z["cislo_zasedani"]), int(z["rok"])
        jid = f"ZO-{rok}-{n}"
        ex.jednani(jid, "ZO", cislo=n, rok=rok, datum=z["datum"],
                   nazev=f"{n}. zasedání zastupitelstva obce Ostopovice v roce {rok}", url_pdf=z["url"],
                   shrnuti=shrnuti.get(f"{rok}-{n}"), pritomno=int(z["pritomno"]) if z.get("pritomno") else None,
                   omluveni=z.get("omluveni") or None, pocet_usneseni=len(z["body"]))
        for i, b in enumerate(z["body"]):
            h = b.get("hlasovani") if isinstance(b.get("hlasovani"), list) else [None] * 3
            ex.usneseni(jid, i + 1, b["text"], oznaceni=b.get("usneseni_id"), kategorie=b.get("kategorie"),
                        tema=b.get("tema"), castka=mx.num(b.get("castka")), pro=h[0], proti=h[1], zdrzel=h[2])

    def druhy(rok, obdobi, s):
        for strana, key, gran, col in (("prijmy", "prijmy_druh", "druh", "druh"),
                                       ("vydaje", "vydaje_druh", "druh", "druh"),
                                       ("vydaje", "vydaje_oblast", "oblast", "oblast")):
            for r in s.get(key, []):
                ex.rozpocet(rok=rok, obdobi=obdobi, granularita=gran, strana=strana, **{col: r["name"]},
                            schvaleny=r["schv"], upraveny=r["uprav"], skutecnost=r["skut"])

    for rok, s in roz["struktura"].items():
        druhy(int(rok), f"{rok}-12", s)
    a = roz.get("aktualni")
    if a:
        druhy(a["rok"], f'{a["rok"]}-{str(a["obdobi"])[-2:]}', a)

    inv = embedded("investice.html")
    for k in inv["kap"]:
        ex.kapitalove(k["rok"], k["kap"], k["vydaje"])
    for z in inv["zak"]:
        ex.akce(z["nazev"], nazev=z["nazev"], datum=iso(z["datum"]), rok=z["rok"], castka=z["hodnota"],
                skupina=z.get("kat"), url=z["url"], zdroj="profil zadavatele")
    for p in inv["pozemky"]:
        if (p.get("typ") or "").startswith("Financování"):
            continue
        rok_z = p["zo"].split("/")
        ex.akce(p["text"], rok=p["rok"], castka=p["castka"], organ="ZO", skupina=p.get("typ"),
                jednani_id=f"ZO-{rok_z[1]}-{int(rok_z[0])}" if len(rok_z) == 2 else None, url=p["url"],
                zdroj="usnesení ZO")

    for r in embedded("zakazky.html")["rows"]:
        ex.zakazka(r["nazev"], datum=iso(r["datum"]), rok=r["rok"], castka=r["hodnota"], url=r["url"])

    # výběrová řízení z XML exportu profilu (scripts/fetch_profil_rizeni.py)
    if os.path.exists("data/profil_rizeni.json"):
        for z in json.load(open("data/profil_rizeni.json", encoding="utf-8"))["zakazky"]:
            ex.rizeni(z["id"], z["nazev"], datum=z["datum"] or None, rok=int(z["datum"][:4]) if z["datum"] else None,
                      druh=z["druh"], postup=z["postup"], stav=z["stav"], predpokladana_hodnota=z["predpokladana_hodnota"],
                      lhuta=z["lhuta"] or None, dodavatel=z["dodavatel"] or None, dodavatel_ico=z["dodavatel_ico"] or None,
                      cena=z["cena"], url=z["url"],
                      nabidky=[dict(n, vybrana=bool(z["dodavatel_ico"]) and n["ico"] == z["dodavatel_ico"]) for n in z["nabidky"]])

    for d in json.load(open("data/dotace.json", encoding="utf-8")):
        ex.dotace(d["prijemce"], d["text"], rok=d["rok"], castka=d["castka"], url=d["url"])

    meta = ex.close()
    print(OUT, {k: v for k, v in meta.items() if k.startswith("pocet_")})


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
