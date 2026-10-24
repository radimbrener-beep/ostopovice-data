#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Seznam položek pro upozornění → push/feed.json (spouští deploy.yml před nahráním).
(Převzato z portálu Střelic.)

Položky: zasedání zastupitelstva (z datasetu) a ručně ohlášené novinky portálu
(data/push_novinky.json). Server (push/send.php) oznámí jen ty, které ještě neoznámil
a jsou novější než stav při zapnutí upozornění — viz push/lib/Send.php.

Novinka portálu = záznam v data/push_novinky.json:
    {"id": "volby-2026", "title": "…", "body": "…", "url": "/volby.html", "date": "2026-10-24"}
"""
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "push", "feed.json")
PER_TOPIC = 30


def load(path, default):
    p = os.path.join(HERE, path)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else default


def meetings():
    """Zasedání zastupitelstva Ostopovic: číslují se v každém roce od 1 (0 = ustavující)."""
    data = load("dataset_ZO.json", [])
    shrnuti = load("data/shrnuti/zo.json", {})
    out = []
    for m in sorted(data, key=lambda m: m["datum"], reverse=True)[:PER_TOPIC]:
        key = f"{m['rok']}-{m['cislo_zasedani']}"
        nazev = "Ustavující zasedání zastupitelstva" if m["cislo_zasedani"] == 0 else \
            f"Zastupitelstvo, {m['cislo_zasedani']}. zasedání {m['rok']}"
        body = shrnuti.get(key) or f"Zápis ze zasedání: {len(m.get('body', []))} usnesení."
        out.append({
            "id": f"zastupitelstvo-{key}", "topic": "zastupitelstvo",
            "title": f"{nazev} · {m['datum_text']}",
            "body": body if len(body) <= 240 else body[:237].rsplit(" ", 1)[0] + "…",
            "url": f"/zastupitelstvo.html?zo={key}", "date": m["datum"],
        })
    return out


def main():
    items = meetings()
    for n in load("data/push_novinky.json", []):
        items.append({"id": "portal-" + n["id"], "topic": "portal", "title": n["title"], "body": n.get("body", ""),
                      "url": n.get("url", "/"), "date": n["date"]})
    items.sort(key=lambda i: i["date"], reverse=True)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=1)
    by = {}
    for i in items:
        by[i["topic"]] = by.get(i["topic"], 0) + 1
    print(f"HOTOVO: push/feed.json — {len(items)} položek {by}, nejnovější: {items[0]['title'] if items else '—'}")


if __name__ == "__main__":
    main()
