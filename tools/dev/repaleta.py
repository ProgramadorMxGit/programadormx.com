"""Pasa la paleta cálida-olivo del sitio a grafito frío con un solo acento índigo (23 sep 2026).

Base: la investigación de 20 apps exitosas (Documents\\AI Claude\\_investigacion-color\\INFORME.md):
neutros casi totales, casi negro teñido, texto casi blanco, un único acento y botón principal
monocromo. Cada color escrito a mano se reclasifica en OKLCH conservando su luminosidad relativa,
así que la jerarquía y el contraste que ya tenía el diseño se mantienen:

- neutros y olivos/caquis apagados -> grafito frío (tono 265°, croma mínimo);
- durazno/naranja y verdes "de estado" de la demo -> índigo del acento;
- WhatsApp -> su verde, solo en su botón y su ícono;
- el panel de contacto durazno -> banda casi blanca con texto grafito (inversión monocroma).

Uso:  py -3 tools/dev/repaleta.py            aplica sobre src/styles
      py -3 tools/dev/repaleta.py --dry      solo muestra la tabla
La paleta anterior quedó copiada en tools/dev/paleta-anterior/.
"""
from __future__ import annotations

import math
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
ARCHIVOS = ["10-premium.css", "15-media.css"]
HEX = re.compile(r"#([0-9a-fA-F]{8}|[0-9a-fA-F]{6})\b")

VIEJO_BG, NUEVO_BG = "#141411", "#0a0b0d"
ACENTO = "#7c85f0"
TONO_NEUTRO = 265.0

# Casos que no se deciden por fórmula.
FIJOS = {
    "#141411": NUEVO_BG,
    "#ffb77b": ACENTO,
    "#ffc89a": "#959cf4",            # hover del acento
    # WhatsApp: el único verde saturado del sitio.
    "#c0d1a3": "#25d366", "#24331b": "#072d16",
    "#b7c99d": "#25d366", "#2c3b20": "#072d16",
}
# Panel de contacto: pasa de durazno a banda casi blanca; sus cafés se vuelven grafito.
CONTACTO = {"#262316", "#5e4325", "#7a4e27", "#634326", "#8b572d", "#724723", "#684525", "#865327"}
PANEL_CONTACTO = ("#ffb77b", "#ededef")
NO_TOCAR = {"#000000", "#ffffff", "#ededef"}
# Líneas y órbitas caqui: son decoración, no acento; van a neutro para que el índigo no se riegue.
DECORATIVOS = {"#adad81", "#85885d", "#666c42", "#b89960"}


# ---- sRGB <-> OKLCH -------------------------------------------------------------
def _lin(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _gam(c):
    c = max(0.0, min(1.0, c))
    return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


def a_oklch(h):
    r, g, b = (_lin(int(h[i:i + 2], 16) / 255) for i in (1, 3, 5))
    l = (0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b) ** (1 / 3)
    m = (0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b) ** (1 / 3)
    s = (0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b) ** (1 / 3)
    L = 0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s
    A = 1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s
    B = 0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s
    return L, math.hypot(A, B), math.degrees(math.atan2(B, A)) % 360


def de_oklch(L, C, H):
    A, B = C * math.cos(math.radians(H)), C * math.sin(math.radians(H))
    l = (L + 0.3963377774 * A + 0.2158037573 * B) ** 3
    m = (L - 0.1055613458 * A - 0.0638541728 * B) ** 3
    s = (L - 0.0894841775 * A - 1.2914855480 * B) ** 3
    r = 4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s
    g = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s
    b = -0.0041960863 * l - 0.7034186147 * m + 1.7076956932 * s
    return "#" + "".join(f"{round(_gam(v) * 255):02x}" for v in (r, g, b))


L_VIEJO, L_NUEVO = a_oklch(VIEJO_BG)[0], a_oklch(NUEVO_BG)[0]
_, C_ACENTO, H_ACENTO = a_oklch(ACENTO)


def luz(L):
    """Oscurece el piso como el nuevo fondo y deja intactos los claros."""
    if L <= L_VIEJO:
        return L * L_NUEVO / L_VIEJO
    return L_NUEVO + (L - L_VIEJO) * (1 - L_NUEVO) / (1 - L_VIEJO)


def neutro(L):
    return de_oklch(luz(L), 0.012 if L < 0.85 else 0.007, TONO_NEUTRO)


def convierte(h):
    h = h.lower()
    if h in FIJOS:
        return FIJOS[h], "fijo"
    if h in NO_TOCAR:
        return h, "igual"
    L, C, H = a_oklch(h)
    if h in CONTACTO:
        return de_oklch(L, 0.012, TONO_NEUTRO), "contacto"
    if h in DECORATIVOS:
        return neutro(L), "neutro"
    calido = 30 <= H <= 95
    verde_estado = 95 < H <= 160 and C >= 0.06
    if (calido and C >= 0.05) or verde_estado:
        return de_oklch(luz(L), min(C_ACENTO, max(C, 0.05) * 1.25), H_ACENTO), "acento"
    return neutro(L), "neutro"


def main():
    dry = "--dry" in sys.argv
    vistos = {}
    for nombre in ARCHIVOS:
        f = RAIZ / "src" / "styles" / nombre
        txt = f.read_text(encoding="utf-8")
        # El panel de contacto es el único uso del durazno como fondo grande.
        txt = txt.replace(".contact-panel { background:#ffb77b;", f".contact-panel {{ background:{PANEL_CONTACTO[1]};")

        def sub(m):
            raw = m.group(0).lower()
            base, alfa = raw[:7], raw[7:]
            nuevo, tipo = convierte(base)
            vistos[base] = (nuevo, tipo)
            return nuevo + alfa

        nuevo_txt = HEX.sub(sub, txt)
        if not dry:
            f.write_text(nuevo_txt, encoding="utf-8", newline="\n")
    for k, (v, t) in sorted(vistos.items(), key=lambda x: x[1][1]):
        print(f"{t:9s} {k} -> {v}")
    print(len(vistos), "colores", "(sin escribir)" if dry else "reescritos")


if __name__ == "__main__":
    main()
