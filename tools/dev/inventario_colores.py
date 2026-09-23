"""Lista cada color escrito a mano en src/styles (menos 00-tokens.css) con su primer contexto."""
import collections
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
RX = re.compile(r"#[0-9a-fA-F]{8}\b|#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b|rgba?\([^)]*\)")

cuenta = collections.Counter()
contexto = {}
for f in sorted((RAIZ / "src" / "styles").glob("*.css")):
    if f.name == "00-tokens.css":
        continue
    for ln in f.read_text(encoding="utf-8").splitlines():
        for m in RX.findall(ln):
            k = m.lower()
            cuenta[k] += 1
            contexto.setdefault(k, (f.name, ln.strip()[:100]))

print(len(cuenta), "colores distintos,", sum(cuenta.values()), "usos")
for k, v in sorted(cuenta.items(), key=lambda x: -x[1]):
    print(f"{v:3d} {k:22s} {contexto[k][0]:20s} {contexto[k][1]}")
