#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
serve.py — sirve dist/ en local imitando al nginx del hosting.

Uso (desde la raíz del proyecto):
  py -3 tools/serve.py              http://localhost:8080/
  py -3 tools/serve.py 8081         otro puerto
  py -3 tools/serve.py --dist ruta  otra carpeta de salida

Qué hace:
  - URLs bonitas: /carpeta/ sirve /carpeta/index.html; /carpeta redirige a /carpeta/.
  - 404 real: lo que no existe responde con estado 404 y el contenido de dist/404.html.
  - Cabeceras no-cache para que cada recarga traiga el build más reciente.
  - Nunca lista carpetas.
Solo librería estándar. No modifica nada en dist/.
"""
from __future__ import annotations

import argparse
import http.server
import io
import os
import sys
from functools import partial
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DIST = ROOT / "dist"
DEFAULT_PORT = 8080

MIME = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".mjs": "text/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".xml": "application/xml; charset=utf-8",
    ".txt": "text/plain; charset=utf-8",
    ".svg": "image/svg+xml",
    ".webp": "image/webp",
    ".png": "image/png",
    ".ico": "image/x-icon",
    ".woff2": "font/woff2",
    ".woff": "font/woff",
    ".webmanifest": "application/manifest+json",
}


class DistHandler(http.server.SimpleHTTPRequestHandler):
    """SimpleHTTPRequestHandler con 404 real, sin listado de carpetas y sin caché."""

    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map, **MIME}
    server_version = "pmx-serve/1.0"

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def send_head(self):
        fs_path = self.translate_path(self.path)
        if os.path.isdir(fs_path):
            # La clase base redirige /carpeta -> /carpeta/ (301) y busca index.html;
            # si no hay index, cae en list_directory, que aquí responde 404.
            return super().send_head()
        if os.path.isfile(fs_path):
            return super().send_head()
        return self.send_not_found()

    def list_directory(self, path):
        return self.send_not_found()

    def send_not_found(self):
        page = Path(self.directory) / "404.html"
        if not page.is_file():
            self.send_error(404, "No encontrado")
            return None
        data = page.read_bytes()
        self.send_response(404)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        return io.BytesIO(data)

    def log_message(self, fmt, *args):
        sys.stdout.write(f"{self.log_date_time_string()}  {fmt % args}\n")
        sys.stdout.flush()


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except (ValueError, AttributeError):
                pass
    ap = argparse.ArgumentParser(description="Sirve dist/ en local con URLs bonitas y 404 real.")
    ap.add_argument("port", nargs="?", type=int, default=None, help=f"puerto (por defecto {DEFAULT_PORT})")
    ap.add_argument("--port", dest="port_opt", type=int, default=None, help="puerto (alternativa al argumento posicional)")
    ap.add_argument("--dist", default=str(DEFAULT_DIST), help="carpeta a servir (por defecto <raíz>/dist)")
    ap.add_argument("--host", default="127.0.0.1", help="interfaz donde escuchar (por defecto 127.0.0.1)")
    args = ap.parse_args(argv)
    port = args.port_opt or args.port or DEFAULT_PORT
    dist = Path(args.dist).resolve()

    if not (dist / "index.html").is_file():
        print(f"error: no existe {dist / 'index.html'}. Corre antes: py -3 tools/build.py", file=sys.stderr)
        return 1

    handler = partial(DistHandler, directory=str(dist))
    try:
        server = http.server.ThreadingHTTPServer((args.host, port), handler)
    except OSError as e:
        print(f"error: no se pudo abrir el puerto {port} ({e}). Prueba otro: py -3 tools/serve.py {port + 1}", file=sys.stderr)
        return 1
    shown_host = "localhost" if args.host in ("127.0.0.1", "0.0.0.0", "") else args.host
    print(f"Sirviendo {dist}")
    print(f"  http://{shown_host}:{port}/   (Ctrl+C para detener)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDetenido.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
