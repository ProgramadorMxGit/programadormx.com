#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build.py — genera dist/ a partir de src/, data/ y site.config.json.

Uso (desde la raíz del proyecto):
  py -3 tools/build.py            construye dist/ (la borra y la regenera completa)
  py -3 tools/build.py --check    valida todo sin escribir nada
  py -3 tools/build.py --verbose  además lista los archivos generados

Sintaxis de plantillas: CONTRACT.md §2. Reglas de build: CONTRACT.md §3.
Solo librería estándar. Todo se lee y escribe en UTF-8 sin BOM con saltos LF.

Códigos de salida: 0 = todo bien (puede haber avisos), 1 = error de build.
Cada error indica archivo y línea cuando aplica, con la cadena de inclusión.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
import json
import re
import shutil
import sys
import urllib.parse
from pathlib import Path

MISSING = object()
HELPERS = ("asset", "icon", "join")
MAX_INCLUDE_DEPTH = 40
KB = 1024

# Presupuesto de rendimiento (BRIEF §9). Se avisa, no se falla.
BUDGET = {
    "html_home": 60 * KB,
    "css_total": 70 * KB,
    "js_total": 45 * KB,
    "webp_each": 120 * KB,
    "nav_logo": 15 * KB,
}
NAV_LOGO_KEYS = ("assets/logo-96.png", "assets/logo.svg")


class BuildError(Exception):
    """Error de build. El mensaje ya trae archivo y línea cuando aplica."""


def fmt_price(value) -> str:
    """7900 -> '$7,900' (formato de precio del sitio)."""
    try:
        return f"${int(value):,}"
    except (TypeError, ValueError):
        raise BuildError(f"precio inválido {value!r}: debe ser un entero en MXN") from None


def wa_url(number, message: str = "") -> str:
    """https://wa.me/<número>?text=<mensaje url-encoded>."""
    base = f"https://wa.me/{number}"
    if message:
        return base + "?text=" + urllib.parse.quote(str(message), safe="")
    return base


def hash8(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:8]


def strip_bom(text: str) -> str:
    return text[1:] if text.startswith("﻿") else text


# ============================================================================
# Motor de plantillas
# ============================================================================

TAG_RE = re.compile(r"\{\{\{\s*(?P<raw>.*?)\s*\}\}\}|\{\{\s*(?P<tag>.*?)\s*\}\}")
PATH_RE = re.compile(r"^(?:@?[A-Za-z_][\w-]*|this)(?:\.[\w@-]+)*$")
ARG_RE = re.compile(r'"([^"]*)"|\'([^\']*)\'|(\S+)')
BLOCK_OPEN_RE = re.compile(r"^#(if|unless|each)\s+(\S+)\s*$")
BLOCK_CLOSE_RE = re.compile(r"^/(if|unless|each)\s*$")
INCLUDE_RE = re.compile(r"^[\w-]+(?:/[\w-]+)*$")
ICON_NAME_RE = re.compile(r"^[\w-]+$")


class Node:
    __slots__ = ("line",)


class TextNode(Node):
    __slots__ = ("text",)

    def __init__(self, text: str, line: int):
        self.text = text
        self.line = line


class VarNode(Node):
    __slots__ = ("path", "escape")

    def __init__(self, path: str, escape: bool, line: int):
        self.path = path
        self.escape = escape
        self.line = line


class HelperNode(Node):
    __slots__ = ("name", "args", "escape")

    def __init__(self, name: str, args: list, escape: bool, line: int):
        self.name = name
        self.args = args  # lista de ("lit", texto) | ("path", ruta)
        self.escape = escape
        self.line = line


class IncludeNode(Node):
    __slots__ = ("target",)

    def __init__(self, target: str, line: int):
        self.target = target
        self.line = line


class BlockNode(Node):
    __slots__ = ("kind", "expr", "body", "otherwise")

    def __init__(self, kind: str, expr: str, body: list, otherwise, line: int):
        self.kind = kind  # if | unless | each
        self.expr = expr
        self.body = body
        self.otherwise = otherwise  # lista o None ({{else}})
        self.line = line


class Template:
    """Plantilla parseada a un árbol (bloques anidados). Los errores traen nombre:línea."""

    def __init__(self, source: str, name: str, line_offset: int = 0):
        self.source = strip_bom(source)
        self.name = name
        self.line_offset = line_offset
        self._tokens: list = []
        self._i = 0
        self.nodes = self._parse()

    # -- utilidades -----------------------------------------------------------
    def _line(self, pos: int) -> int:
        return self.line_offset + self.source.count("\n", 0, pos) + 1

    def _err(self, line: int, msg: str):
        raise BuildError(f"{self.name}:{line}: {msg}")

    # -- tokenización ---------------------------------------------------------
    def _check_text(self, text: str, pos: int) -> None:
        i = text.find("{{")
        if i >= 0:
            self._err(self._line(pos + i), "'{{' sin cerrar: falta '}}' en la misma línea")

    def _tokenize(self) -> list:
        tokens = []
        pos = 0
        for m in TAG_RE.finditer(self.source):
            text = self.source[pos:m.start()]
            if text:
                self._check_text(text, pos)
                tokens.append(("text", text, self._line(pos)))
            raw = m.group("raw") is not None
            inner = m.group("raw") if raw else m.group("tag")
            line = self._line(m.start())
            if inner == "":
                self._err(line, "etiqueta vacía '{{ }}'")
            if inner.startswith("{"):
                self._err(line, f"llaves desbalanceadas en '{m.group(0)}': usa {{{{ var }}}} o {{{{{{ var }}}}}}")
            tokens.append(("tag", inner, raw, line))
            pos = m.end()
        text = self.source[pos:]
        if text:
            self._check_text(text, pos)
            tokens.append(("text", text, self._line(pos)))
        return tokens

    # -- parser recursivo -----------------------------------------------------
    def _parse(self) -> list:
        self._tokens = self._tokenize()
        self._i = 0
        nodes, _ = self._parse_nodes(None)
        return nodes

    def _parse_nodes(self, open_block):
        """Devuelve (nodos, nodos_else). open_block = (kind, line) del bloque abierto o None."""
        nodes: list = []
        otherwise = None
        current = nodes
        while self._i < len(self._tokens):
            tok = self._tokens[self._i]
            self._i += 1
            if tok[0] == "text":
                current.append(TextNode(tok[1], tok[2]))
                continue
            _, inner, raw, line = tok
            if inner.startswith("!"):
                continue  # comentario {{! ... }}
            m = BLOCK_OPEN_RE.match(inner)
            if m:
                kind, expr = m.group(1), m.group(2)
                if not PATH_RE.match(expr):
                    self._err(line, f"expresión inválida en {{{{#{kind} {expr}}}}}: se espera una ruta de variable")
                body, body_else = self._parse_nodes((kind, line))
                current.append(BlockNode(kind, expr, body, body_else, line))
                continue
            if inner.startswith("#"):
                self._err(line, f"bloque no reconocido '{{{{{inner}}}}}': solo existen #if, #unless y #each")
            m = BLOCK_CLOSE_RE.match(inner)
            if m:
                if open_block is None:
                    self._err(line, f"'{{{{/{m.group(1)}}}}}' sin bloque abierto")
                if m.group(1) != open_block[0]:
                    self._err(
                        line,
                        f"se cierra '{{{{/{m.group(1)}}}}}' pero el bloque abierto es "
                        f"'{{{{#{open_block[0]}}}}}' (abierto en la línea {open_block[1]})",
                    )
                return nodes, otherwise
            if inner.startswith("/"):
                self._err(line, f"cierre no reconocido '{{{{{inner}}}}}': solo existen /if, /unless y /each")
            if inner == "else":
                if open_block is None:
                    self._err(line, "'{{else}}' fuera de un bloque")
                if otherwise is not None:
                    self._err(line, "dos '{{else}}' en el mismo bloque")
                otherwise = []
                current = otherwise
                continue
            if inner.startswith(">"):
                target = inner[1:].strip()
                if not INCLUDE_RE.match(target):
                    self._err(line, f"ruta de inclusión inválida '{target}': usa {{{{> partials/nombre}}}} sin .html")
                current.append(IncludeNode(target, line))
                continue
            current.append(self._parse_expr(inner, raw, line))
        if open_block is not None:
            kind, oline = open_block
            self._err(oline, f"'{{{{#{kind}}}}}' sin cerrar: falta '{{{{/{kind}}}}}'")
        return nodes, otherwise

    def _parse_expr(self, inner: str, raw: bool, line: int):
        args = []
        for m in ARG_RE.finditer(inner):
            if m.group(1) is not None:
                args.append(("lit", m.group(1)))
            elif m.group(2) is not None:
                args.append(("lit", m.group(2)))
            else:
                args.append(("path", m.group(3)))
        if not args:
            self._err(line, "etiqueta vacía '{{ }}'")
        kind, name = args[0]
        if kind == "path" and name in HELPERS:
            rest = args[1:]
            if name in ("asset", "icon") and len(rest) != 1:
                self._err(line, f'uso: {{{{ {name} "nombre" }}}} o {{{{ {name} variable.ruta }}}}')
            if name == "join" and (len(rest) not in (1, 2) or rest[0][0] != "path"):
                self._err(line, 'uso: {{ join lista "separador" }}')
            for k, v in rest:
                if k == "path" and not PATH_RE.match(v):
                    self._err(line, f"ruta de variable inválida '{v}' en {{{{ {inner} }}}}")
            return HelperNode(name, rest, not raw, line)
        if len(args) == 1 and kind == "path":
            if PATH_RE.match(name):
                return VarNode(name, not raw, line)
            self._err(line, f"nombre de variable inválido '{name}'")
        self._err(line, f"expresión no reconocida '{{{{ {inner} }}}}'")


class Renderer:
    """Evalúa plantillas con includes, iconos y assets relativos a src/."""

    def __init__(self, src_dir, assets: dict | None = None, root=None):
        self.src_dir = Path(src_dir)
        self.assets = dict(assets or {})
        self.root = Path(root) if root else self.src_dir.parent
        self._templates: dict[str, Template] = {}
        self._icons: dict[str, str] = {}

    def name_of(self, path: Path) -> str:
        try:
            return path.resolve().relative_to(self.root.resolve()).as_posix()
        except ValueError:
            return path.as_posix()

    def load(self, target: str) -> Template:
        """Carga y cachea src/<target>.html (p. ej. 'partials/nav')."""
        tpl = self._templates.get(target)
        if tpl is not None:
            return tpl
        path = self.src_dir / f"{target}.html"
        if not path.is_file():
            raise BuildError(f"partial inexistente '{target}': no existe {self.name_of(path)}")
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as e:
            raise BuildError(f"{self.name_of(path)}: no es UTF-8 válido ({e.reason} en el byte {e.start})") from None
        tpl = Template(text, self.name_of(path))
        self._templates[target] = tpl
        return tpl

    def render(self, tpl: Template, ctx: dict) -> str:
        out: list[str] = []
        self._render_nodes(tpl.nodes, tpl, ctx, [], 0, out)
        return "".join(out)

    def render_string(self, source: str, ctx: dict, name: str = "<string>") -> str:
        return self.render(Template(source, name), ctx)

    # -- evaluación -----------------------------------------------------------
    def _render_nodes(self, nodes, tpl, ctx, scopes, depth, out) -> None:
        for node in nodes:
            if isinstance(node, TextNode):
                out.append(node.text)
            elif isinstance(node, VarNode):
                out.append(self._var(node, tpl, ctx, scopes))
            elif isinstance(node, HelperNode):
                out.append(self._helper(node, tpl, ctx, scopes))
            elif isinstance(node, IncludeNode):
                self._include(node, tpl, ctx, scopes, depth, out)
            elif isinstance(node, BlockNode):
                self._block(node, tpl, ctx, scopes, depth, out)

    def _lookup(self, path: str, ctx: dict, scopes: list):
        parts = path.split(".")
        head = parts[0]
        val = MISSING
        for scope in reversed(scopes):
            if head in scope:
                val = scope[head]
                break
        if val is MISSING:
            val = ctx.get(head, MISSING)
        for part in parts[1:]:
            if val is MISSING:
                break
            if isinstance(val, dict):
                val = val.get(part, MISSING)
            elif isinstance(val, (list, tuple)) and part.isdigit() and int(part) < len(val):
                val = val[int(part)]
            else:
                val = MISSING
        return val

    def _missing_msg(self, path: str, ctx: dict, scopes: list) -> str:
        parts = path.split(".")
        head = parts[0]
        if (head.startswith("@") or head == "this") and not scopes:
            return f"variable inexistente '{path}': '{head}' solo existe dentro de un bloque {{{{#each}}}}"
        val = MISSING
        for scope in reversed(scopes):
            if head in scope:
                val = scope[head]
                break
        if val is MISSING:
            val = ctx.get(head, MISSING)
        if val is MISSING:
            avail = sorted(set(ctx) | {k for s in scopes for k in s})
            return f"variable inexistente '{path}': '{head}' no está en el contexto (disponibles: {', '.join(avail)})"
        prefix = head
        for part in parts[1:]:
            if isinstance(val, dict) and part in val:
                val = val[part]
                prefix += "." + part
                continue
            if isinstance(val, dict):
                keys = ", ".join(sorted(map(str, val)))
                return f"variable inexistente '{path}': '{prefix}' existe pero no tiene '{part}' (claves: {keys})"
            return f"variable inexistente '{path}': '{prefix}' no es un objeto (es {type(val).__name__})"
        return f"variable inexistente '{path}'"

    def _to_str(self, val, path: str, tpl: Template, line: int) -> str:
        if val is None:
            return ""
        if isinstance(val, bool):
            return "true" if val else "false"
        if isinstance(val, (int, float)):
            return str(val)
        if isinstance(val, str):
            return val
        if isinstance(val, (list, tuple)):
            raise BuildError(
                f"{tpl.name}:{line}: '{path}' es una lista: usa {{{{ join {path} \" · \" }}}} o {{{{#each {path}}}}}"
            )
        if isinstance(val, dict):
            raise BuildError(f"{tpl.name}:{line}: '{path}' es un objeto: usa una ruta con punto ({path}.clave)")
        return str(val)

    def _strict(self, path: str, tpl: Template, line: int, ctx: dict, scopes: list):
        val = self._lookup(path, ctx, scopes)
        if val is MISSING:
            raise BuildError(f"{tpl.name}:{line}: {self._missing_msg(path, ctx, scopes)}")
        return val

    def _var(self, node: VarNode, tpl, ctx, scopes) -> str:
        val = self._strict(node.path, tpl, node.line, ctx, scopes)
        text = self._to_str(val, node.path, tpl, node.line)
        return html.escape(text, quote=True) if node.escape else text

    def _arg(self, arg, tpl, line, ctx, scopes):
        kind, val = arg
        if kind == "lit":
            return val
        return self._strict(val, tpl, line, ctx, scopes)

    def _helper(self, node: HelperNode, tpl, ctx, scopes) -> str:
        line = node.line
        if node.name == "asset":
            name = self._to_str(self._arg(node.args[0], tpl, line, ctx, scopes), node.args[0][1], tpl, line)
            url = self.assets.get(name)
            if url is None:
                avail = ", ".join(sorted(self.assets)) or "ninguno"
                raise BuildError(f"{tpl.name}:{line}: asset inexistente '{name}' (disponibles: {avail})")
            return html.escape(url, quote=True) if node.escape else url
        if node.name == "icon":
            name = self._to_str(self._arg(node.args[0], tpl, line, ctx, scopes), node.args[0][1], tpl, line)
            return self._icon(name, tpl, line)  # nunca se escapa
        if node.name == "join":
            path = node.args[0][1]
            val = self._strict(path, tpl, line, ctx, scopes)
            if val is None:
                val = []
            if isinstance(val, (str, dict)) or not isinstance(val, (list, tuple)):
                raise BuildError(f"{tpl.name}:{line}: join: '{path}' no es una lista (es {type(val).__name__})")
            sep = ", "
            if len(node.args) == 2:
                sep = self._to_str(self._arg(node.args[1], tpl, line, ctx, scopes), node.args[1][1], tpl, line)
            text = sep.join(self._to_str(item, f"{path}[{i}]", tpl, line) for i, item in enumerate(val))
            return html.escape(text, quote=True) if node.escape else text
        raise BuildError(f"{tpl.name}:{line}: helper desconocido '{node.name}'")

    def _icon(self, name: str, tpl: Template, line: int) -> str:
        if not ICON_NAME_RE.match(name):
            raise BuildError(f"{tpl.name}:{line}: nombre de icono inválido '{name}'")
        svg = self._icons.get(name)
        if svg is None:
            path = self.src_dir / "assets" / "icons" / f"{name}.svg"
            if not path.is_file():
                raise BuildError(f"{tpl.name}:{line}: icono inexistente '{name}': no existe {self.name_of(path)}")
            svg = strip_bom(path.read_text(encoding="utf-8")).strip()
            svg = re.sub(r"^<\?xml[^>]*\?>\s*", "", svg)
            self._icons[name] = svg
        return svg

    def _include(self, node: IncludeNode, tpl, ctx, scopes, depth, out) -> None:
        if depth > MAX_INCLUDE_DEPTH:
            raise BuildError(
                f"{tpl.name}:{node.line}: inclusión recursiva de '{node.target}' (más de {MAX_INCLUDE_DEPTH} niveles)"
            )
        try:
            sub = self.load(node.target)
        except BuildError as e:
            raise BuildError(f"{tpl.name}:{node.line}: {e}") from None
        try:
            self._render_nodes(sub.nodes, sub, ctx, scopes, depth + 1, out)
        except BuildError as e:
            raise BuildError(f"{e}\n    ← incluido desde {tpl.name}:{node.line}") from None

    def _block(self, node: BlockNode, tpl, ctx, scopes, depth, out) -> None:
        if node.kind in ("if", "unless"):
            # Condición laxa: una variable inexistente cuenta como falsa.
            val = self._lookup(node.expr, ctx, scopes)
            cond = val is not MISSING and bool(val)
            if node.kind == "unless":
                cond = not cond
            branch = node.body if cond else node.otherwise
            if branch:
                self._render_nodes(branch, tpl, ctx, scopes, depth, out)
            return
        # each (estricto: la lista debe existir)
        val = self._lookup(node.expr, ctx, scopes)
        if val is MISSING:
            raise BuildError(f"{tpl.name}:{node.line}: {self._missing_msg(node.expr, ctx, scopes)} (en {{{{#each}}}})")
        if val is None:
            val = []
        if isinstance(val, dict):
            raise BuildError(f"{tpl.name}:{node.line}: {{{{#each {node.expr}}}}}: es un objeto, no una lista")
        if isinstance(val, str) or not isinstance(val, (list, tuple)):
            raise BuildError(f"{tpl.name}:{node.line}: {{{{#each {node.expr}}}}}: no es una lista (es {type(val).__name__})")
        if not val:
            if node.otherwise:
                self._render_nodes(node.otherwise, tpl, ctx, scopes, depth, out)
            return
        n = len(val)
        for i, item in enumerate(val):
            scope = dict(item) if isinstance(item, dict) else {}
            scope["this"] = item
            scope["@index"] = i
            scope["@first"] = i == 0
            scope["@last"] = i == n - 1
            self._render_nodes(node.body, tpl, ctx, scopes + [scope], depth, out)


# ============================================================================
# Build
# ============================================================================

META_RE = re.compile(r"\A\s*<!--\s*meta\b(?P<json>.*?)-->", re.S)
ATTR_RE = re.compile(r"""\b(href|src|content|action|poster)\s*=\s*(?:"([^"]*)"|'([^']*)')""", re.I)
CSS_URL_RE = re.compile(r"""url\(\s*['"]?(/[^'")\s]+)""")
SKIP_SCHEMES = ("mailto:", "tel:", "sms:", "data:", "javascript:", "whatsapp:")


class Builder:
    """Construye el sitio. Con check=True valida sin escribir."""

    def __init__(self, root, out=None, check: bool = False, verbose: bool = False, today: dt.date | None = None):
        self.root = Path(root).resolve()
        self.src = self.root / "src"
        self.dist = Path(out).resolve() if out else self.root / "dist"
        self.check = check
        self.verbose = verbose
        self.today = today or dt.date.today()
        self.outputs: dict[str, str | Path] = {}  # ruta en dist -> texto o archivo a copiar
        self.warnings: list[str] = []
        self.errors: list[str] = []
        self.assets: dict[str, str] = {}
        self.pages: list[dict] = []
        self.site: dict = {}
        self.products: list = []
        self.faq: list = []
        self.build: dict = {}
        self.css_bytes = 0
        self.js_bytes = 0
        self.renderer: Renderer | None = None

    # -- utilidades -----------------------------------------------------------
    def rel(self, path) -> str:
        try:
            return Path(path).resolve().relative_to(self.root).as_posix()
        except ValueError:
            return Path(path).as_posix()

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def read_text(self, path) -> str:
        path = Path(path)
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as e:
            raise BuildError(f"{self.rel(path)}: no es UTF-8 válido ({e.reason} en el byte {e.start})") from None
        if text.startswith("﻿"):
            self.warn(f"{self.rel(path)}: tiene BOM; guárdalo como UTF-8 sin BOM")
            text = text[1:]
        return text

    def read_json(self, path):
        text = self.read_text(path)
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            raise BuildError(f"{self.rel(path)}:{e.lineno}: JSON inválido: {e.msg}") from None

    # -- datos ----------------------------------------------------------------
    def load_data(self) -> None:
        cfg_path = self.root / "site.config.json"
        if not cfg_path.is_file():
            raise BuildError("falta site.config.json en la raíz del proyecto")
        cfg = self.read_json(cfg_path)
        if not isinstance(cfg, dict):
            raise BuildError("site.config.json: debe ser un objeto JSON")
        for key in ("name", "url", "whatsapp"):
            if not cfg.get(key):
                raise BuildError(f"site.config.json: falta la clave '{key}'")
        site = dict(cfg)
        site["url"] = str(site["url"]).rstrip("/")
        site["whatsapp_url"] = wa_url(site["whatsapp"], site.get("whatsapp_message", ""))
        plan = site.get("monthly_plan")
        if isinstance(plan, dict):
            plan = dict(plan)
            if "price" in plan:
                plan["price_fmt"] = fmt_price(plan["price"])
            site["monthly_plan"] = plan

        products_path = self.root / "data" / "products.json"
        raw_products = self.read_json(products_path) if products_path.is_file() else []
        if not isinstance(raw_products, list):
            raise BuildError("data/products.json: debe ser una lista de productos")
        products = []
        slugs = set()
        for i, p in enumerate(raw_products):
            if not isinstance(p, dict):
                raise BuildError(f"data/products.json: el producto #{i + 1} no es un objeto")
            for key in ("slug", "nombre", "precio_desde", "mensaje_whatsapp"):
                if key not in p:
                    raise BuildError(f"data/products.json: al producto #{i + 1} ({p.get('slug', '?')}) le falta '{key}'")
            if p["slug"] in slugs:
                raise BuildError(f"data/products.json: slug duplicado '{p['slug']}'")
            slugs.add(p["slug"])
            q = dict(p)
            q["whatsapp_url"] = wa_url(site["whatsapp"], p["mensaje_whatsapp"])
            q["precio_fmt"] = fmt_price(p["precio_desde"])
            q["href"] = p.get("landing_path") or "/#productos"
            products.append(q)
        if products:
            prices = [int(p["precio_desde"]) for p in products]
            site["price_min_fmt"] = fmt_price(min(prices))
            site["price_max_fmt"] = fmt_price(max(prices))

        faq_path = self.root / "data" / "faq.json"
        faq = self.read_json(faq_path) if faq_path.is_file() else []
        if not isinstance(faq, list) or not all(isinstance(x, dict) and "q" in x and "a" in x for x in faq):
            raise BuildError("data/faq.json: debe ser una lista de objetos { \"q\": ..., \"a\": ... }")

        self.site, self.products, self.faq = site, products, faq

    def compute_hash(self) -> str:
        h = hashlib.sha256()
        files = [self.root / "site.config.json"]
        for folder in (self.root / "data", self.src):
            if folder.is_dir():
                files.extend(p for p in folder.rglob("*") if p.is_file())
        for f in sorted(files, key=lambda p: p.as_posix()):
            h.update(self.rel(f).encode("utf-8"))
            h.update(f.read_bytes())
        return h.hexdigest()[:8]

    # -- assets ---------------------------------------------------------------
    def collect_assets(self) -> None:
        styles = self.src / "styles"
        css_files = sorted(styles.glob("*.css"), key=lambda p: p.name) if styles.is_dir() else []
        if css_files:
            parts = []
            for f in css_files:
                parts.append(f"/* ---- {f.name} ---- */\n" + self.read_text(f).rstrip("\n") + "\n")
            css = "\n".join(parts)
            key = f"assets/site.{hash8(css)}.css"
            self.outputs[key] = css
            self.assets["site.css"] = "/" + key
            self.css_bytes = len(css.encode("utf-8"))

        scripts = self.src / "scripts"
        js_files = sorted(scripts.glob("*.js"), key=lambda p: p.name) if scripts.is_dir() else []
        for f in js_files:
            js = self.read_text(f)
            key = f"assets/{f.stem}.{hash8(js)}.js"
            self.outputs[key] = js
            self.assets[f.name] = "/" + key
            self.js_bytes += len(js.encode("utf-8"))

        assets_dir = self.src / "assets"
        if assets_dir.is_dir():
            for f in sorted(assets_dir.rglob("*"), key=lambda p: p.as_posix()):
                if not f.is_file():
                    continue
                sub = f.relative_to(assets_dir).as_posix()
                key = "assets/" + sub
                self.outputs[key] = f
                self.assets.setdefault(sub, "/" + key)

    # -- páginas --------------------------------------------------------------
    def parse_meta(self, source: str, rel: str):
        m = META_RE.match(source)
        if not m:
            raise BuildError(f"{rel}:1: falta el bloque <!--meta {{ ... }} --> al inicio del archivo")
        raw = m.group("json").strip()
        if not raw:
            raise BuildError(f"{rel}:1: el bloque <!--meta --> está vacío")
        try:
            meta = json.loads(raw)
        except json.JSONDecodeError as e:
            off = source.index(raw, m.start("json"))
            line = source.count("\n", 0, off) + e.lineno
            raise BuildError(f"{rel}:{line}: JSON inválido en el bloque meta: {e.msg}") from None
        if not isinstance(meta, dict):
            raise BuildError(f"{rel}:1: el bloque meta debe ser un objeto JSON")
        body = source[m.end():]
        body_offset = source.count("\n", 0, m.end())
        return meta, body, body_offset

    def build_pages(self) -> None:
        pages_dir = self.src / "pages"
        if not pages_dir.is_dir():
            raise BuildError("no existe src/pages/")
        files = sorted(pages_dir.rglob("*.html"), key=lambda p: p.as_posix())
        if not files:
            raise BuildError("src/pages/ no tiene páginas .html")
        if not (self.src / "layouts" / "base.html").is_file():
            raise BuildError("falta src/layouts/base.html")
        seen_paths: dict[str, str] = {}
        for f in files:
            rel = self.rel(f)
            try:
                self.build_page(f, rel, seen_paths)
            except BuildError as e:
                self.errors.append(str(e))

    def build_page(self, f: Path, rel: str, seen_paths: dict) -> None:
        source = self.read_text(f)
        meta, body, body_offset = self.parse_meta(source, rel)

        path = meta.get("path")
        if not isinstance(path, str) or not path.startswith("/") or path.startswith("//"):
            raise BuildError(f"{rel}: 'path' debe empezar por '/' (p. ej. \"/politica-de-privacidad/\")")
        if ".." in path or " " in path or not (path.endswith("/") or path.endswith(".html")):
            raise BuildError(f"{rel}: 'path' inválido '{path}': debe terminar en '/' (o ser /404.html)")
        for key in ("title", "description"):
            v = meta.get(key)
            if not isinstance(v, str) or not v.strip():
                raise BuildError(f"{rel}: la página no tiene '{key}' en el bloque meta")
        if path in seen_paths:
            raise BuildError(f"{rel}: path duplicado '{path}' (ya lo usa {seen_paths[path]})")
        seen_paths[path] = rel

        sections = meta.get("sections", [])
        if sections is None:
            sections = []
        if not isinstance(sections, list) or not all(isinstance(s, str) for s in sections):
            raise BuildError(f"{rel}: 'sections' debe ser una lista de nombres de src/sections/")
        own_faq = meta.get("faq")
        if own_faq is not None and not isinstance(own_faq, list):
            raise BuildError(f"{rel}: 'faq' debe ser una lista de {{ \"q\": ..., \"a\": ... }}")

        page = {"body_class": "", "noindex": False, "og_image": "/assets/og/og-image.png"}
        page.update(meta)
        page["path"] = path
        page["sections"] = sections
        page["url"] = self.site["url"] + path
        page["is_home"] = path == "/"
        page["has_faq"] = bool("faq" in sections or "landing-faq" in sections or own_faq)
        faq_items = own_faq if own_faq else self.faq

        ctx = {
            "site": self.site,
            "page": page,
            "products": self.products,
            "faq": self.faq,
            "faq_items": faq_items,
            "build": self.build,
        }
        slug = meta.get("product")
        if slug:
            prod = next((p for p in self.products if p["slug"] == slug), None)
            if prod is None:
                known = ", ".join(p["slug"] for p in self.products) or "ninguno"
                raise BuildError(f"{rel}: el producto '{slug}' no existe en data/products.json (slugs: {known})")
            ctx["product"] = prod

        renderer = self.renderer
        assert renderer is not None
        parts: list[str] = []
        mtimes = [f.stat().st_mtime]
        try:
            for name in sections:
                sec_path = self.src / "sections" / f"{name}.html"
                if not sec_path.is_file():
                    raise BuildError(f"{rel}: sección inexistente '{name}' (no existe {self.rel(sec_path)})")
                mtimes.append(sec_path.stat().st_mtime)
                parts.append(renderer.render(renderer.load(f"sections/{name}"), ctx))
            if body.strip():
                parts.append(renderer.render(Template(body, rel, body_offset), ctx))
            content = "".join(parts)
            html_out = renderer.render(renderer.load("layouts/base"), {**ctx, "content": content})
        except BuildError as e:
            raise BuildError(f"{e}\n    ← página {rel}") from None

        key = path[1:] + "index.html" if path.endswith("/") else path[1:]
        self.outputs[key] = html_out
        self.pages.append(
            {
                "path": path,
                "url": page["url"],
                "noindex": bool(page.get("noindex")),
                "source": rel,
                "key": key,
                "lastmod": dt.datetime.fromtimestamp(max(mtimes)).date().isoformat(),
                "size": len(html_out.encode("utf-8")),
            }
        )

    # -- sitemap y robots -----------------------------------------------------
    def build_sitemap_robots(self) -> None:
        urls = [p for p in sorted(self.pages, key=lambda p: p["path"]) if not p["noindex"] and p["path"] != "/404.html"]
        lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
        for p in urls:
            lines += ["  <url>", f"    <loc>{html.escape(p['url'], quote=True)}</loc>", f"    <lastmod>{p['lastmod']}</lastmod>", "  </url>"]
        lines.append("</urlset>")
        self.outputs["sitemap.xml"] = "\n".join(lines) + "\n"
        self.outputs["robots.txt"] = f"User-agent: *\nAllow: /\n\nSitemap: {self.site['url']}/sitemap.xml\n"

    # -- validación -----------------------------------------------------------
    def _check_link(self, value: str, attr: str, where: str) -> None:
        value = value.strip()
        if not value or value.startswith(("#", "?")) or value.lower().startswith(SKIP_SCHEMES):
            return
        site_url = self.site["url"]
        if value == site_url or value.startswith(site_url + "/"):
            target = value[len(site_url):] or "/"
        elif value.startswith("/") and not value.startswith("//"):
            target = value
        else:
            return  # externo o relativo: no se valida
        path = urllib.parse.unquote(urllib.parse.urlsplit(target).path) or "/"
        key = path[1:] + "index.html" if path.endswith("/") else path[1:]
        if key in self.outputs:
            return
        if not path.endswith("/") and (path[1:] + "/index.html") in self.outputs:
            self.warn(f"{where}: {attr}=\"{value}\" existe pero le falta la barra final ('{path}/')")
            return
        self.errors.append(f"{where}: {attr}=\"{value}\" apunta a algo que no existe en dist/ ({key})")

    def validate_outputs(self) -> None:
        for p in self.pages:
            out = self.outputs[p["key"]]
            assert isinstance(out, str)
            i = out.find("{{")
            if i >= 0:
                snippet = out[i:i + 60].splitlines()[0]
                self.errors.append(f"dist/{p['key']}: queda '{{{{' sin resolver: {snippet!r} (página {p['source']})")
            where = f"dist/{p['key']} (página {p['source']})"
            for m in ATTR_RE.finditer(out):
                raw = m.group(2) if m.group(2) is not None else m.group(3)
                self._check_link(html.unescape(raw), m.group(1).lower(), where)
            n_h1 = len(re.findall(r"<h1\b", out, re.I))
            if n_h1 != 1:
                self.warn(f"{p['source']}: la página tiene {n_h1} <h1> (debe tener exactamente uno)")
            if not re.search(r"<title\b", out, re.I):
                self.warn(f"{p['source']}: la página no tiene <title>")
        for key, val in self.outputs.items():
            if key.endswith(".css") and isinstance(val, str):
                for m in CSS_URL_RE.finditer(val):
                    self._check_link(m.group(1), "url()", f"dist/{key}")

    def check_budget(self) -> None:
        def kb(n: int) -> str:
            return f"{n / KB:.1f} KB"

        home = next((p for p in self.pages if p["path"] == "/"), None)
        if home and home["size"] > BUDGET["html_home"]:
            self.warn(f"presupuesto: dist/index.html pesa {kb(home['size'])} (máx. {kb(BUDGET['html_home'])})")
        if self.css_bytes > BUDGET["css_total"]:
            self.warn(f"presupuesto: el CSS total pesa {kb(self.css_bytes)} (máx. {kb(BUDGET['css_total'])})")
        if self.js_bytes > BUDGET["js_total"]:
            self.warn(f"presupuesto: el JS total pesa {kb(self.js_bytes)} (máx. {kb(BUDGET['js_total'])})")
        for key, val in self.outputs.items():
            if not isinstance(val, Path):
                continue
            size = val.stat().st_size
            if key.endswith(".webp") and size > BUDGET["webp_each"]:
                self.warn(f"presupuesto: {key} pesa {kb(size)} (máx. {kb(BUDGET['webp_each'])} por imagen)")
            if key in NAV_LOGO_KEYS and size > BUDGET["nav_logo"]:
                self.warn(f"presupuesto: {key} pesa {kb(size)} (el logo de la nav debe pesar ≤ {kb(BUDGET['nav_logo'])})")

    # -- escritura ------------------------------------------------------------
    def write(self) -> None:
        if self.dist == self.root or self.dist in self.root.parents:
            raise BuildError("la carpeta de salida no puede ser la raíz del proyecto ni contenerla")
        if self.dist.exists():
            shutil.rmtree(self.dist)
        for key, val in self.outputs.items():
            dest = self.dist / key
            dest.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(val, Path):
                shutil.copy2(val, dest)
            else:
                with open(dest, "w", encoding="utf-8", newline="\n") as fh:
                    fh.write(val)

    # -- orquestación ---------------------------------------------------------
    def run(self) -> "Builder":
        self.load_data()
        self.build = {"year": self.today.year, "date": self.today.isoformat(), "hash": self.compute_hash()}
        self.collect_assets()
        self.renderer = Renderer(self.src, self.assets, self.root)
        self.build_pages()
        if not self.errors:
            self.build_sitemap_robots()
            self.validate_outputs()
        self.check_budget()
        if self.errors:
            raise BuildError("\n".join(self.errors))
        if not self.check:
            self.write()
        return self

    def output_size(self, key: str) -> int:
        val = self.outputs[key]
        return val.stat().st_size if isinstance(val, Path) else len(val.encode("utf-8"))


# ============================================================================
# CLI
# ============================================================================

def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except (ValueError, AttributeError):
                pass
    ap = argparse.ArgumentParser(description="Genera dist/ del sitio programadormx.online (ver CONTRACT.md §3).")
    ap.add_argument("--check", action="store_true", help="valida todo sin escribir dist/")
    ap.add_argument("--verbose", "-v", action="store_true", help="lista los archivos generados")
    ap.add_argument("--root", default=None, help="raíz del proyecto (por defecto, la carpeta padre de tools/)")
    ap.add_argument("--out", default=None, help="carpeta de salida (por defecto <raíz>/dist)")
    args = ap.parse_args(argv)
    root = Path(args.root).resolve() if args.root else Path(__file__).resolve().parents[1]

    builder = Builder(root, out=args.out, check=args.check, verbose=args.verbose)
    try:
        builder.run()
    except BuildError as e:
        for w in builder.warnings:
            print(f"aviso: {w}", file=sys.stderr)
        for line in str(e).split("\n"):
            prefix = "error: " if not line.startswith("    ") else "       "
            print(prefix + line, file=sys.stderr)
        print("build fallido.", file=sys.stderr)
        return 1

    for w in builder.warnings:
        print(f"aviso: {w}", file=sys.stderr)
    if args.verbose:
        for key in sorted(builder.outputs):
            print(f"  {builder.output_size(key):>8,} B  {key}")
    summary = (
        f"{len(builder.pages)} páginas · CSS {builder.css_bytes / KB:.1f} KB · JS {builder.js_bytes / KB:.1f} KB · "
        f"{len(builder.outputs)} archivos · {len(builder.warnings)} avisos"
    )
    if args.check:
        print(f"OK (--check, no se escribió nada) · {summary}")
    else:
        print(f"OK · {summary} → {builder.dist}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
