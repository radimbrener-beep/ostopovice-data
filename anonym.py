#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Anonymizace textů usnesení (GDPR).

Obec Ostopovice zveřejňuje v zápisech ZO plná jména soukromých osob, jejich
adresy a data narození (kupní smlouvy, dary, volba přísedících…). Na portál
patří jen to podstatné, proto:
  - jména osob uvozená oslovením / titulem → iniciály („pana Karla Nováka" →
    „pana K. N.", stejně jako anonymizuje zápisy např. obec Střelice),
  - adresa bydliště („bytem …") → vypuštěna,
  - datum narození → vypuštěno.
Organizace, firmy, obce a funkce zůstávají beze změny."""
import re

TITUL = r"(?:Ing|Mgr|MgA|Bc|BcA|MUDr|MVDr|MDDr|JUDr|PhDr|RNDr|PaedDr|doc|prof|DiS|Ph\.\s?D)\.?"
OSLOV = r"(?:pan|pana|panu|panem|paní|panÍ|manžel\w*|manželé)"
SLOVO = r"[A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][a-záčďéěíňóřšťúůýž]+"

# oslovení/titul + (tituly) + Jméno (Příjmení) [a (tituly) Jméno (Příjmení)]
_NAME_RE = re.compile(
    rf"\b(?P<lead>{OSLOV}\s+|(?={TITUL}\s))"
    rf"(?P<names>(?:(?:{TITUL}\s*,?\s*)*{SLOVO}(?:\s+{SLOVO}){{0,2}})"
    rf"(?:\s+a\s+(?:{TITUL}\s*,?\s*)*{SLOVO}(?:\s+{SLOVO}){{0,2}})?"
    rf"(?:\s*,?\s*{TITUL})*)")

_BIRTH_RE = re.compile(r",?\s*(?:narozen\w*|datum narození|nar\.)\s*:?\s*\d{1,2}\.\s*\d{1,2}\.\s*\d{4}", re.I)


def _initials(m):
    lead = m.group("lead") or ""
    names = re.sub(rf"{TITUL}\s*,?\s*", "", m.group("names"))
    out = re.sub(SLOVO, lambda w: w.group(0)[0] + ".", names)
    return lead + re.sub(r"\s+", " ", out).strip(" ,")


# konec adresy: čárka + slovo malým písmenem („…, jako kupující"), slovo
# jako/doručen…/ze dne bez čárky („…191 doručenou dne"), nebo tečka na konci věty
_ADDR_END = re.compile(r",\s*(?=[a-záčďéěíňóřšťúůýž])|\s+(?=(?:jako|doručen\w*|ze dne|a pověřuje)\b)|\.(?=\s|$)|;")


def _drop_address(text):
    """Vypustí „(oba) bytem <adresa>" až po konec adresy."""
    out, pos = [], 0
    for m in re.finditer(r",?\s*(?:oba\s+|obě\s+)?(?:trvale\s+)?(?:bytem|bydlišt\w*|s\s+trvalým\s+pobytem)[\s,:]+(?:na\s+|v\s+)?", text):
        if m.start() < pos:
            continue
        rest = text[m.end():]
        e = _ADDR_END.search(rest)
        end = e.start() if e else len(rest)
        if end > 110:          # nevypadá jako adresa — raději nechat
            continue
        out.append(text[pos:m.start()])
        pos = m.end() + end
    out.append(text[pos:])
    return "".join(out)


# jméno občana za podáním: „stížnost Karla Dvořáka", „přípis Jana Nováka"
_ORG = (r"(?!(?:Obc|Obec|Měst|Mikroregion|Sdružen|Svaz|Spolk|Kraj|Jihomoravsk|Odbor|Úřad|Městsk|"
        r"Mateřsk|Základn|Charit|Farnost|Klub|Polici|Hasič|Sbor|Správ|Ředitelstv|Ministerstv|Krajsk|"
        r"Česk|Státn|Povodí|Lesy|Vodárensk|Společenstv|Honebn|Tělocvičn|Tělovýchovn|Ostopovic)\w*\b)")
_AFTER_RE = re.compile(rf"\b((?:přípis|žádost|stížnost|dopis|podnět|petic)\w*\s+){_ORG}({SLOVO})\s+({SLOVO})\b")

# jméno bez oslovení ve 7. pádě: „Josefem a Stanislavem Šmídovými"
_PAIR_RE = re.compile(rf"\b({SLOVO}(?:em|ou))\s+a\s+({SLOVO}(?:em|ou))\s+({SLOVO}(?:ými|ovými|ým|ovou))\b")


def anonymize(text):
    if not text:
        return text
    t = _BIRTH_RE.sub("", text)
    t = _drop_address(t)
    t = _NAME_RE.sub(_initials, t)
    t = _PAIR_RE.sub(lambda m: f"{m.group(1)[0]}. a {m.group(2)[0]}. {m.group(3)[0]}.", t)
    t = _AFTER_RE.sub(lambda m: f"{m.group(1)}{m.group(2)[0]}. {m.group(3)[0]}.", t)
    t = re.sub(r"\s+,", ",", t)
    t = re.sub(r",\s*,", ",", t)
    return re.sub(r"\s{2,}", " ", t).strip()


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    for s in [
        # smyšlené osoby a adresy (vzor zápisů obce)
        "schvaluje nabídku pana Karla Nováka, bytem Polní 12, Želešice 664 43, ze dne 1. 2. 2020 na koupi pozemku",
        "volí přísedícího pana Ing. Jana Dvořáka, narozeného 1. 1. 1970, bytem Ostopovice, Hlavní 1/1, na funkční období 2020 – 2023",
        "nabídku paní Evy Svobodové, bytem Na Návsi 5, 664 49 Ostopovice, doručené dne 1. 2.",
        "darovací smlouvu mezi Obcí Ostopovice jako obdarovanou a manžely Janou a Ing. Petrem Černými, bytem Zahradní 10/2, 664 49 Ostopovice, jako dárci",
        "nabídku manželů Pavla a Věry Malých, oba bytem Školní náměstí 1/1, Brno, na odkup",
        "dotace „Klubu Seniorů“ paní Marii Veselé, datum narození 1. 1. 1950, bytem Krátká 1/1, 66449 Ostopovice, ve výši 40.000,- Kč",
        "schvaluje za ověřovatele zápisu Jana Modrého a Petra Zeleného",
        "uzavření smlouvy s firmou STRABAG a.s., IČ 60838744, na stavbu",
    ]:
        print("-", anonymize(s))
