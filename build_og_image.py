#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Vygeneruje sdílecí obrázek og-image.png (1200×630) pro náhled odkazu na FB ap.
Tmavé pozadí v barvách portálu, ikona sloupcového grafu, název a adresa. Plochý soubor
v kořeni (deploy ho kopíruje stejně jako HTML)."""
import sys
from PIL import Image, ImageDraw, ImageFont
sys.stdout.reconfigure(encoding="utf-8")

W, H = 1200, 630
BG = (11, 17, 32)        # --bg2 #0b1120
SURF = (18, 26, 44)      # --surface
TEXT = (232, 237, 246)   # --text
MUTED = (147, 161, 184)  # --muted
ACCENT = (111, 160, 208)  # --accent #6fa0d0
LINE = (31, 42, 64)


def font(size, bold=False):
    cands = ([r"C:\Windows\Fonts\segoeuib.ttf", r"C:\Windows\Fonts\arialbd.ttf"] if bold
             else [r"C:\Windows\Fonts\segoeui.ttf", r"C:\Windows\Fonts\arial.ttf"])
    cands += ["DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"]
    for p in cands:
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            continue
    return ImageFont.load_default()


def center(draw, y, text, fnt, fill, letter=0):
    w = draw.textlength(text, font=fnt)
    draw.text(((W - w) / 2, y), text, font=fnt, fill=fill)


img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)

# jemný rám a spodní akcentní linka
d.rectangle([0, 0, W - 1, H - 1], outline=LINE, width=2)
d.rectangle([0, H - 8, W, H], fill=ACCENT)

# --- logo: sloupcový graf (neutrální ikona portálu) ---
cx, base = W // 2, 222
for i, h in enumerate((70, 115, 92, 150)):
    x = cx - 108 + i * 56
    d.rounded_rectangle([x, base - h, x + 40, base], radius=7, fill=ACCENT if i == 3 else TEXT)
d.line([(cx - 124, base + 6), (cx + 124, base + 6)], fill=MUTED, width=5)

# --- texty ---
center(d, 268, "Jak žijí Ostopovice", font(88, bold=True), TEXT)
center(d, 388, "Otevřená data obce Ostopovice", font(38), MUTED)
center(d, 452, "rozpočet · investice · dotace · zastupitelstvo · školství", font(31), ACCENT)

# adresa v patičce (na akcentním pruhu prostor nad ním)
center(d, 540, "ostopovice.jakzijistrelice.cz", font(40, bold=True), TEXT)

img.save("og-image.png", optimize=True)
import os
print(f"HOTOVO: og-image.png ({W}×{H}, {os.path.getsize('og-image.png')} B)")
