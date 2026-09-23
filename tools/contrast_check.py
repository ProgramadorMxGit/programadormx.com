#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
contrast_check.py — verifica ratios de contraste WCAG 2.1 de los tokens de DESIGN.md.

Uso:
  py -3 tools/contrast_check.py            # tabla completa
  py -3 tools/contrast_check.py --tokens   # lee los hex desde src/styles/00-tokens.css

Criterios usados:
  AA texto normal  >= 4.5:1
  AA texto grande  >= 3.0:1   (>= 24 px, o >= 18.66 px en negrita)
  AA componentes   >= 3.0:1   (bordes de inputs, iconos, indicadores: 1.4.11)
  AAA texto normal >= 7.0:1
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Valores decididos en DESIGN.md (fuente de verdad: src/styles/00-tokens.css).
PALETTE = {
    "bg-0": "#15120F",
    "bg-1": "#1C1814",
    "bg-2": "#241F1A",
    "bg-3": "#2E2823",
    "ink": "#F4EEE6",
    "ink-2": "#BDB3A7",
    "ink-3": "#9C938A",
    "line": "#2A241F",
    "line-2": "#726B61",
    "accent": "#F0A63C",
    "accent-ink": "#1C1206",
    "accent-2": "#7FB8C9",
    "accent-soft": "#33240F",
    "ok": "#7CC48B",
    "warn": "#E8785A",
    "wa": "#25D366",
    "wa-ink": "#072D16",
}

# (primer plano, fondo, criterio, nota)
# criterio: "text" 4.5 · "large" 3.0 · "ui" 3.0 · "deco" sin exigencia
PAIRS = [
    # Obligatorios del encargo
    ("ink", "bg-0", "text", "texto principal sobre body/hero"),
    ("ink", "bg-1", "text", "texto principal sobre bandas y tarjetas"),
    ("ink-2", "bg-1", "text", "texto secundario sobre bandas y tarjetas"),
    ("ink-3", "bg-0", "text", "meta mono atenuada sobre body"),
    ("accent-ink", "accent", "text", "texto sobre chip/badge ámbar"),
    ("wa-ink", "wa", "text", "texto del botón WhatsApp"),
    ("accent", "bg-0", "text", "eyebrows y 'desde' en ámbar como texto"),
    # Resto de combinaciones que usa el sistema
    ("ink", "bg-2", "text", "texto en superficies internas"),
    ("ink", "bg-3", "text", "texto en hover/elevado"),
    ("ink-2", "bg-0", "text", "ledes sobre body"),
    ("ink-2", "bg-2", "text", "texto secundario en chips"),
    ("ink-2", "bg-3", "text", "texto secundario en hover"),
    ("ink-3", "bg-1", "text", "meta mono en tarjetas"),
    ("ink-3", "bg-2", "text", "meta mono en chips"),
    ("ink-3", "bg-3", "text", "meta mono en hover (regla: solo si pasa)"),
    ("ink-3", "accent-soft", "text", "meta mono sobre lavado ámbar (regla: solo si pasa)"),
    ("ink-2", "accent-soft", "text", "texto secundario sobre lavado ámbar"),
    ("ink", "accent-soft", "text", "texto principal sobre lavado ámbar"),
    ("accent", "bg-1", "text", "ámbar como texto en bandas"),
    ("accent", "bg-2", "text", "ámbar como texto en chips"),
    ("accent", "bg-3", "text", "ámbar como texto en hover"),
    ("accent", "accent-soft", "text", "chip destacado: texto ámbar sobre lavado"),
    ("accent-2", "bg-0", "text", "azul-verdoso: iconos y .mono en párrafos"),
    ("accent-2", "bg-1", "text", "azul-verdoso en tarjetas"),
    ("accent-2", "bg-2", "ui", "icono de producto en caja bg-2"),
    ("ok", "bg-0", "text", "mensaje de éxito"),
    ("ok", "bg-1", "text", "mensaje de éxito en tarjeta"),
    ("warn", "bg-0", "text", "mensaje de error"),
    ("warn", "bg-1", "text", "mensaje de error en tarjeta"),
    ("wa", "bg-0", "ui", "botón WhatsApp como componente sobre body"),
    ("bg-0", "ink", "text", "texto oscuro del botón papel"),
    ("wa", "ink", "deco", "glifo WA verde sobre papel (NO usar: por eso el glifo va en bg-0)"),
    # Bordes
    ("line", "bg-0", "deco", "hairline decorativa (tarjetas, divisores)"),
    ("line", "bg-1", "deco", "hairline decorativa en bandas"),
    ("line-2", "bg-0", "ui", "borde de inputs y botón ghost sobre body (1.4.11)"),
    ("line-2", "bg-1", "ui", "borde de inputs y botón ghost sobre banda (1.4.11)"),
    ("line-2", "bg-2", "ui", "borde de control sobre bg-2"),
]

THRESH = {"text": 4.5, "large": 3.0, "ui": 3.0, "deco": 0.0}


def hex_to_rgb(h):
    h = h.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def channel(c):
    c = c / 255.0
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def luminance(rgb):
    r, g, b = (channel(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def ratio(fg, bg):
    l1, l2 = luminance(hex_to_rgb(fg)), luminance(hex_to_rgb(bg))
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


def load_tokens_css(path):
    css = path.read_text(encoding="utf-8")
    found = {}
    for name, val in re.findall(r"--([a-z0-9-]+)\s*:\s*(#[0-9a-fA-F]{6})", css):
        found[name] = val
    return found


def grade(r, crit):
    if crit == "deco":
        return "deco"
    if r >= 7.0 and crit == "text":
        return "AAA"
    if r >= THRESH[crit]:
        return "AA"
    if crit == "text" and r >= 3.0:
        return "AA-grande"
    return "FALLA"


def main(argv):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    palette = dict(PALETTE)
    if "--tokens" in argv:
        css_path = ROOT / "src" / "styles" / "00-tokens.css"
        palette.update({k: v for k, v in load_tokens_css(css_path).items() if k in palette})
        print(f"# tokens leídos de {css_path.relative_to(ROOT)}")

    print("# Ratios de contraste WCAG 2.1 (luminancia relativa sRGB)")
    print(f"{'par':<28}{'hex':<20}{'ratio':>7}  {'nivel':<10} nota")
    print("-" * 96)
    failures = 0
    for fg, bg, crit, note in PAIRS:
        r = ratio(palette[fg], palette[bg])
        g = grade(r, crit)
        if g == "FALLA" or (crit == "text" and g == "AA-grande"):
            failures += 1
        pair = f"{fg}/{bg}"
        hexes = f"{palette[fg]}/{palette[bg]}"
        print(f"{pair:<28}{hexes:<20}{r:>6.2f}:1  {g:<10} {note}")
    print("-" * 96)
    if failures:
        print(f"{failures} par(es) por debajo del criterio de texto normal. Revisa las reglas de uso en DESIGN.md.")
    else:
        print("Todos los pares de texto cumplen AA (4.5:1); todos los bordes de control cumplen 3:1.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
