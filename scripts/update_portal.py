#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Automatická aktualizace portálu (GitHub Actions, check_web.yml).

1. stáhne data: zápisy ZO, rozpočet (MONITOR API), zakázky (profil zadavatele)
   — výpadek zdroje nevadí, zůstanou předchozí data,
2. pojistka: web obce servíruje dvě různé cache varianty seznamu zápisů —
   zasedání, která v novém stažení chybí, se doplní z předchozího datasetu,
3. přegeneruje všechny stránky,
4. zapíše .update_summary.md (co přibylo + zasedání bez shrnutí „V kostce",
   které je potřeba dopsat ručně / LLM podle data/shrnuti)."""
import sys, json, subprocess
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable
DS = ROOT / "dataset_ZO.json"


def run(script, required=True):
    print(f"\n=== {script}", flush=True)
    r = subprocess.run([PY, script], cwd=ROOT)
    if r.returncode and required:
        sys.exit(f"!! {script} selhal ({r.returncode})")
    if r.returncode:
        print(f"!! {script} selhal — pokračuji s předchozími daty")
    return r.returncode == 0


def key(m):
    return f"{m['rok']}-{m['cislo_zasedani']}"


old = json.loads(DS.read_text(encoding="utf-8")) if DS.exists() else []
old_keys = {key(m) for m in old}

if run("scripts/build_dataset_zo.py", required=False):
    new = json.loads(DS.read_text(encoding="utf-8"))
    have = {key(m) for m in new}
    kept = [m for m in old if key(m) not in have]
    if kept:
        print(f"doplněno z předchozího datasetu: {[key(m) for m in kept]}")
        new = sorted(new + kept, key=lambda m: m.get("datum") or "")
        DS.write_text(json.dumps(new, ensure_ascii=False, indent=1), encoding="utf-8")
else:
    new = old
    if old:
        DS.write_text(json.dumps(old, ensure_ascii=False, indent=1), encoding="utf-8")

run("scripts/fetch_rozpocet.py", required=False)
run("scripts/fetch_zakazky.py", required=False)

for b in ["build_dotace.py", "build_rozpocet.py", "build_investice.py", "build_zakazky.py",
          "build_zastupitelstvo.py", "build_skolstvi.py", "build_demografie.py", "build_volby.py",
          "build_srovnani.py", "build_obdobi.py", "build_hledat.py", "build_metodika.py", "build_portal.py"]:
    run(b)

# ---- souhrn ----
shr = json.loads((ROOT / "data" / "shrnuti" / "zo.json").read_text(encoding="utf-8"))
added = [m for m in new if key(m) not in old_keys]
missing = [m for m in new if key(m) not in shr]
lines = []
if added:
    lines.append("## Nová zasedání zastupitelstva\n")
    lines += [f"- {m['datum_text']} — {m['cislo_zasedani']}. zasedání ({m['pocet_bodu']} usnesení) · [PDF]({m['url']})" for m in added]
if missing:
    lines.append("\n## Chybí shrnutí „V kostce\"\n")
    lines.append("Doplnit do `data/shrnuti/zo.json` (klíč `rok-číslo`, pravidla jako u ostatních):\n")
    lines += [f"- `{key(m)}` — {m['datum_text']}" for m in missing]
if added:
    (ROOT / ".update_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print("\n".join(lines) or "Žádná nová zasedání.")
