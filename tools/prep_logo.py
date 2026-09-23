"""Genera las versiones ligeras del logo a partir de los PNG originales del sitio viejo.

Uso:  py -3 tools/prep_logo.py [ruta_a_LOGO_WHITE.png] [ruta_a_LOGO_BLACK.png]

Salida en src/assets/:
  logo-96.png, logo-192.png       logo blanco recortado, fondo transparente (nav y footer)
  logo-dark-512.png               logo negro recortado (para fondos claros, p. ej. el og-image si hace falta)
  favicon-32.png, favicon-192.png  logo blanco sobre cuadro oscuro redondeado
  apple-touch-icon.png (180 px)    idem, sin transparencia
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "src" / "assets"
OLD = Path("C:/Users/Programador Mx/Documents/web-programador-mx/assets")


def theme_color() -> str:
    cfg = json.loads((ROOT / "site.config.json").read_text(encoding="utf-8"))
    return cfg.get("theme_color", "#0B0F14")


def trimmed(path: Path) -> Image.Image:
    img = Image.open(path).convert("RGBA")
    bbox = img.getchannel("A").getbbox()
    if bbox:
        img = img.crop(bbox)
    return img


def fit(img: Image.Image, size: int) -> Image.Image:
    w, h = img.size
    scale = size / max(w, h)
    return img.resize((max(1, round(w * scale)), max(1, round(h * scale))), Image.LANCZOS)


def save(img: Image.Image, name: str) -> None:
    out = ASSETS / name
    img.save(out, optimize=True)
    print(f"{name:24s} {img.size[0]}x{img.size[1]}  {out.stat().st_size / 1024:.1f} KB")


def on_square(glyph: Image.Image, size: int, bg: str, radius_ratio: float = 0.22, pad_ratio: float = 0.16) -> Image.Image:
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)
    draw.rounded_rectangle((0, 0, size - 1, size - 1), radius=int(size * radius_ratio), fill=bg)
    inner = fit(glyph, int(size * (1 - 2 * pad_ratio)))
    x = (size - inner.size[0]) // 2
    y = (size - inner.size[1]) // 2
    canvas.alpha_composite(inner, (x, y))
    return canvas


def main() -> None:
    white_src = Path(sys.argv[1]) if len(sys.argv) > 1 else OLD / "LOGO_WHITE.png"
    black_src = Path(sys.argv[2]) if len(sys.argv) > 2 else OLD / "LOGO_BLACK.png"
    ASSETS.mkdir(parents=True, exist_ok=True)
    bg = theme_color()

    white = trimmed(white_src)
    black = trimmed(black_src)
    print(f"original blanco {Image.open(white_src).size} -> recortado {white.size}")

    save(fit(white, 96), "logo-96.png")
    save(fit(white, 192), "logo-192.png")
    save(fit(black, 512), "logo-dark-512.png")
    save(on_square(white, 32, bg), "favicon-32.png")
    save(on_square(white, 192, bg), "favicon-192.png")
    save(on_square(white, 180, bg).convert("RGB"), "apple-touch-icon.png")


if __name__ == "__main__":
    main()
