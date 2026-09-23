"""Convierte las fotos 4k de OpenArt en los WebP que usa el sitio.

A diferencia de procesar_fotos.py, este NO iguala el brillo: estas fotos son
documentales y su penumbra es parte de la foto. Solo baja un punto la saturación
y calienta las sombras, y exporta dos tamaños para pantallas normales y grandes.

Uso:  py -3 tools/dev/og/procesar_4k.py <origen.png> <destino-sin-extension> [ancho_grande]
Ejemplo:
  py -3 tools/dev/og/procesar_4k.py C:/tmp/oa-home-1.png src/assets/img/landing/home-hero 2400
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageEnhance

RAIZ = Path(__file__).resolve().parents[3]


def graduar_suave(im: Image.Image) -> Image.Image:
    im = ImageEnhance.Color(im).enhance(0.94)
    im = ImageEnhance.Contrast(im).enhance(1.03)
    r, g, b = im.split()
    r = r.point(lambda v: min(255, int(v * 1.02)))
    b = b.point(lambda v: int(v * 0.97))
    return Image.merge("RGB", (r, g, b))


def main() -> None:
    origen = Path(sys.argv[1])
    destino = RAIZ / sys.argv[2] if not Path(sys.argv[2]).is_absolute() else Path(sys.argv[2])
    ancho_grande = int(sys.argv[3]) if len(sys.argv) > 3 else 2400

    im = graduar_suave(Image.open(origen).convert("RGB"))
    print(f"origen {im.size[0]}x{im.size[1]}")
    destino.parent.mkdir(parents=True, exist_ok=True)

    for ancho, sufijo, calidad in ((ancho_grande, "@2x", 70), (ancho_grande // 2, "", 74)):
        alto = round(ancho * im.size[1] / im.size[0])
        salida = destino.with_name(destino.name + sufijo).with_suffix(".webp")
        im.resize((ancho, alto), Image.LANCZOS).save(salida, "WEBP", quality=calidad, method=6)
        print(f"{salida.name:34s} {ancho}x{alto}  {salida.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
