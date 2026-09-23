"""Convierte las fotos generadas en ChatGPT a los WebP que usa el sitio.

- Iguala el color entre todas (misma penumbra cálida) para que se vean como una serie.
- Reduce a 1000 px de ancho y exporta WebP por debajo del presupuesto de BRIEF §9.

Uso:  py -3 tools/dev/og/procesar_fotos.py <carpeta_con_p1..p6.png> [--natural]

--natural  solo recorta, reduce y exporta, sin graduar el color. Es lo que se usa desde la
           serie v2 (22 sep 2026): la penumbra cálida era parte de lo que las hacía ver de IA.
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageEnhance, ImageStat

RAIZ = Path(__file__).resolve().parents[3]
DESTINO = RAIZ / "src" / "assets" / "img" / "productos"

# Cada foto generada -> el producto al que pertenece (slug de data/products.json)
MAPA = {
    "p1": "agenda-citas-whatsapp",
    "p2": "pedidos-whatsapp",
    "p3": "menu-digital-qr",
    "p4": "tarjeta-lealtad",
    "p5": "inventario-ventas",
    "p6": "pagina-web",
}

ANCHO = 1000          # el doble de lo que mide la tarjeta más grande en pantalla
LUMA_OBJETIVO = 74.0  # penumbra cálida: todas las fotos terminan cerca de este brillo medio
NATURAL = False       # --natural: sin graduar (ver docstring)


def luma(im: Image.Image) -> float:
    return ImageStat.Stat(im.convert("L")).mean[0]


def graduar(im: Image.Image) -> Image.Image:
    """Lleva la foto al mismo brillo, contraste y temperatura que el resto de la serie."""
    factor = LUMA_OBJETIVO / max(luma(im), 1.0)
    factor = min(max(factor, 0.55), 1.35)          # sin apagar ni quemar de más
    im = ImageEnhance.Brightness(im).enhance(factor)
    im = ImageEnhance.Contrast(im).enhance(1.06)
    im = ImageEnhance.Color(im).enhance(0.92)      # un punto menos de saturación: se ve más caro
    r, g, b = im.split()                            # sombras tibias, sin azules fríos
    r = r.point(lambda v: min(255, int(v * 1.035)))
    b = b.point(lambda v: int(v * 0.955))
    return Image.merge("RGB", (r, g, b))


def main() -> None:
    global NATURAL
    args = [a for a in sys.argv[1:] if a != "--natural"]
    NATURAL = "--natural" in sys.argv[1:]
    origen = Path(args[0]) if args else Path.cwd()
    DESTINO.mkdir(parents=True, exist_ok=True)
    total = 0

    for clave, slug in MAPA.items():
        src = origen / f"{clave}.png"
        if not src.exists():
            print(f"{clave}: falta {src}")
            continue

        im = Image.open(src).convert("RGB")
        antes = luma(im)

        # Las de ChatGPT ya vienen en 3:2; si no, se recorta al centro.
        w, h = im.size
        if abs(w / h - 1.5) > 0.01:
            if w / h > 1.5:
                nuevo = int(h * 1.5)
                im = im.crop(((w - nuevo) // 2, 0, (w + nuevo) // 2, h))
            else:
                nuevo = int(w / 1.5)
                im = im.crop((0, (h - nuevo) // 2, w, (h + nuevo) // 2))

        if not NATURAL:
            im = graduar(im)
        im = im.resize((ANCHO, int(ANCHO / 1.5)), Image.LANCZOS)
        salida = DESTINO / f"{slug}.webp"
        im.save(salida, "WEBP", quality=74, method=6)
        kb = salida.stat().st_size / 1024
        total += kb
        print(f"{slug + '.webp':28s} {im.size[0]}x{im.size[1]}  {kb:5.0f} KB   brillo {antes:5.1f} -> {luma(im):5.1f}")

    print(f"\ntotal {total:.0f} KB en {len(MAPA)} fotos (presupuesto: 120 KB por imagen)")


if __name__ == "__main__":
    main()
