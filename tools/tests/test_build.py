#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pruebas del motor de plantillas y de los invariantes de build (CONTRACT.md §2 y §3).

Se corren desde la raíz del proyecto con cualquiera de las dos formas:
  py -3 -m unittest discover -s tools/tests -t .
  py -3 tools/tests/test_build.py

Cada prueba construye un proyecto mínimo en una carpeta temporal: nunca toca src/ ni dist/.
"""
from __future__ import annotations

import contextlib
import io
import json
import re
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # tools/
import build  # noqa: E402
from build import BuildError, Builder, Renderer, Template  # noqa: E402

SITE = {
    "name": "ProgramadorMX",
    "url": "https://ejemplo.test",
    "whatsapp": "5218331080178",
    "whatsapp_display": "833 108 0178",
    "whatsapp_message": "Hola, quiero una app & más.",
    "email": "correo@ejemplo.test",
    "owner_name": "",
    "city": "Ciudad Madero, Tamaulipas",
    "hours": "Lunes a viernes",
    "ga4_id": "",
    "monthly_plan": {"price": 249, "label": "Hosting, dominio y soporte"},
}

PRODUCTS = [
    {
        "slug": "agenda",
        "nombre": "Agenda de citas",
        "para_quien": ["barberías", "salones & spa"],
        "incluye": ["a", "b"],
        "precio_desde": 7900,
        "entrega": "2 semanas",
        "mensaje_whatsapp": "Hola, quiero la agenda",
        "icon": "check",
        "landing_path": "/app-agenda/",
        "destacado": True,
    },
    {
        "slug": "menu",
        "nombre": "Menú QR",
        "para_quien": ["restaurantes"],
        "incluye": ["c"],
        "precio_desde": 3900,
        "entrega": "1 semana",
        "mensaje_whatsapp": "Hola, quiero el menú",
        "icon": "check",
        "destacado": False,
    },
]

FAQ = [{"q": "¿Cuánto cuesta?", "a": "Depende."}, {"q": "¿Cuánto tarda?", "a": "Poco."}]

BASE_LAYOUT = (
    "<!doctype html>\n<html lang=\"es-MX\">\n<head><title>{{ page.title }}</title>"
    '<link rel="stylesheet" href="{{ asset "site.css" }}"></head>\n'
    '<body class="{{ page.body_class }}">\n<main>{{{ content }}}</main>\n'
    '<script src="{{ asset "site.js" }}" defer></script>\n</body>\n</html>\n'
)

ICON_SVG = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 12l5 5L20 6"/></svg>\n'


def meta(**kw) -> str:
    return "<!--meta\n" + json.dumps(kw, ensure_ascii=False, indent=2) + "\n-->\n"


HOME_PAGE = meta(path="/", title="Inicio", description="Descripción de la home.") + "<h1>Hola</h1>\n"


class ProjectCase(unittest.TestCase):
    """Base: crea un proyecto temporal mínimo y ayuda a escribir archivos y construir."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name) / "proyecto"
        self.write("site.config.json", json.dumps(SITE, ensure_ascii=False))
        self.write("data/products.json", json.dumps(PRODUCTS, ensure_ascii=False))
        self.write("data/faq.json", json.dumps(FAQ, ensure_ascii=False))
        self.write("src/layouts/base.html", BASE_LAYOUT)
        self.write("src/styles/00-tokens.css", ":root { --bg-0: #15120F; }\n")
        self.write("src/styles/10-base.css", "body { margin: 0; }\n")
        self.write("src/scripts/site.js", "window.PMX = {};\n")
        self.write("src/assets/icons/check.svg", ICON_SVG)
        self.write("src/assets/img/foto.webp", b"RIFF....WEBP")
        self.write("src/pages/index.html", HOME_PAGE)

    def tearDown(self):
        self._tmp.cleanup()

    def write(self, rel: str, content) -> Path:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, bytes):
            path.write_bytes(content)
        else:
            with open(path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(content)
        return path

    def build(self, check: bool = False) -> Builder:
        return Builder(self.root, check=check).run()

    def dist(self, rel: str) -> str:
        return (self.root / "dist" / rel).read_text(encoding="utf-8")

    def assert_build_error(self, *fragments: str) -> str:
        with self.assertRaises(BuildError) as cm:
            self.build(check=True)
        msg = str(cm.exception)
        for frag in fragments:
            self.assertIn(frag, msg)
        return msg


# ----------------------------------------------------------------------------
# Motor de plantillas
# ----------------------------------------------------------------------------

class TemplateEngineTests(ProjectCase):
    def render(self, source: str, ctx: dict, assets: dict | None = None) -> str:
        return Renderer(self.root / "src", assets or {}, self.root).render_string(source, ctx, "src/prueba.html")

    def test_variables_y_escape(self):
        ctx = {"site": {"name": "Tom & Jerry <b>", "n": 7, "ok": True, "nada": None}, "raw": "<em>x</em>"}
        self.assertEqual(self.render("{{ site.name }}", ctx), "Tom &amp; Jerry &lt;b&gt;")
        self.assertEqual(self.render("{{{ raw }}}", ctx), "<em>x</em>")
        self.assertEqual(self.render("{{ raw }}", ctx), "&lt;em&gt;x&lt;/em&gt;")
        self.assertEqual(self.render("{{ site.n }}|{{ site.ok }}|{{ site.nada }}|", ctx), "7|true||")
        self.assertEqual(self.render('a="{{ q }}"', {"q": 'x"y'}), 'a="x&quot;y"')

    def test_includes_anidados(self):
        self.write("src/partials/a.html", "A[{{> partials/b}}]")
        self.write("src/partials/b.html", "B={{ site.name }}")
        out = self.render("<{{> partials/a}}>", {"site": {"name": "PMX"}})
        self.assertEqual(out, "<A[B=PMX]>")

    def test_partial_inexistente_da_error_con_linea(self):
        with self.assertRaises(BuildError) as cm:
            self.render("x\n{{> partials/nope}}", {})
        self.assertIn("src/prueba.html:2", str(cm.exception))
        self.assertIn("partial inexistente 'partials/nope'", str(cm.exception))

    def test_if_unless(self):
        tpl = "{{#if a}}A{{/if}}{{#unless a}}noA{{/unless}}"
        self.assertEqual(self.render(tpl, {"a": "x"}), "A")
        self.assertEqual(self.render(tpl, {"a": ""}), "noA")
        self.assertEqual(self.render(tpl, {"a": []}), "noA")
        self.assertEqual(self.render(tpl, {"a": False}), "noA")
        self.assertEqual(self.render(tpl, {"a": ["x"]}), "A")
        # variable inexistente en la condición: falsa, sin error
        self.assertEqual(self.render(tpl, {}), "noA")
        self.assertEqual(self.render("{{#if site.ga4_id}}GA{{/if}}", {"site": {}}), "")
        # else
        self.assertEqual(self.render("{{#if a}}sí{{else}}no{{/if}}", {"a": 0}), "no")
        # anidado
        out = self.render("{{#if a}}[{{#unless b}}sin-b{{/unless}}]{{/if}}", {"a": 1})
        self.assertEqual(out, "[sin-b]")

    def test_each_anidado_con_index_first_last(self):
        tpl = (
            "{{#each products}}"
            "{{ @index }}:{{ nombre }}({{#if @first}}F{{/if}}{{#if @last}}L{{/if}})"
            "[{{#each para_quien}}{{ @index }}={{ this }}{{#unless @last}},{{/unless}}{{/each}}]"
            "{{ this.slug }};"
            "{{/each}}"
        )
        ctx = {"products": PRODUCTS}
        out = self.render(tpl, ctx)
        self.assertEqual(out, "0:Agenda de citas(F)[0=barberías,1=salones &amp; spa]agenda;1:Menú QR(L)[0=restaurantes]menu;")

    def test_each_ve_el_contexto_exterior(self):
        out = self.render("{{#each products}}{{ site.name }}-{{ slug }} {{/each}}", {"products": PRODUCTS, "site": {"name": "S"}})
        self.assertEqual(out, "S-agenda S-menu ")

    def test_each_lista_vacia_y_else(self):
        self.assertEqual(self.render("{{#each xs}}x{{else}}vacío{{/each}}", {"xs": []}), "vacío")
        self.assertEqual(self.render("{{#each xs}}x{{/each}}", {"xs": None}), "")

    def test_each_lista_inexistente_es_error(self):
        with self.assertRaises(BuildError) as cm:
            self.render("{{#each nada}}x{{/each}}", {})
        self.assertIn("variable inexistente 'nada'", str(cm.exception))

    def test_index_fuera_de_each_es_error(self):
        with self.assertRaises(BuildError) as cm:
            self.render("{{ @index }}", {})
        self.assertIn("solo existe dentro de un bloque {{#each}}", str(cm.exception))

    def test_join(self):
        ctx = {"p": PRODUCTS[0]}
        self.assertEqual(self.render('{{ join p.para_quien " · " }}', ctx), "barberías · salones &amp; spa")
        self.assertEqual(self.render("{{ join p.para_quien }}", ctx), "barberías, salones &amp; spa")
        self.assertEqual(self.render('{{{ join p.para_quien " · " }}}', ctx), "barberías · salones & spa")
        with self.assertRaises(BuildError) as cm:
            self.render('{{ join p.nombre "," }}', ctx)
        self.assertIn("no es una lista", str(cm.exception))

    def test_variable_lista_sugiere_join(self):
        with self.assertRaises(BuildError) as cm:
            self.render("{{ p.para_quien }}", {"p": PRODUCTS[0]})
        self.assertIn("es una lista", str(cm.exception))
        self.assertIn("join", str(cm.exception))

    def test_icon_literal_y_variable_sin_escapar(self):
        svg = ICON_SVG.strip()
        self.assertEqual(self.render('{{ icon "check" }}', {}), svg)
        self.assertEqual(self.render("{{ icon product.icon }}", {"product": PRODUCTS[0]}), svg)
        self.assertEqual(self.render('{{{ icon "check" }}}', {}), svg)

    def test_icon_inexistente_es_error(self):
        with self.assertRaises(BuildError) as cm:
            self.render('a\nb\n{{ icon "cohete" }}', {})
        msg = str(cm.exception)
        self.assertIn("src/prueba.html:3", msg)
        self.assertIn("icono inexistente 'cohete'", msg)
        self.assertIn("src/assets/icons/cohete.svg", msg)

    def test_asset_helper(self):
        assets = {"site.css": "/assets/site.abcdef12.css", "site.js": "/assets/site.12345678.js"}
        self.assertEqual(self.render('{{ asset "site.css" }}', {}, assets), "/assets/site.abcdef12.css")
        with self.assertRaises(BuildError) as cm:
            self.render('{{ asset "nope.js" }}', {}, assets)
        self.assertIn("asset inexistente 'nope.js'", str(cm.exception))

    def test_variable_inexistente_es_error_con_archivo_y_linea(self):
        with self.assertRaises(BuildError) as cm:
            self.render("línea 1\nlínea 2\n{{ site.nombre }}", {"site": {"name": "x"}})
        msg = str(cm.exception)
        self.assertIn("src/prueba.html:3", msg)
        self.assertIn("variable inexistente 'site.nombre'", msg)
        self.assertIn("claves: name", msg)
        with self.assertRaises(BuildError) as cm:
            self.render("{{ nada }}", {"site": {}})
        self.assertIn("'nada' no está en el contexto", str(cm.exception))

    def test_llave_sin_cerrar_es_error_con_linea(self):
        with self.assertRaises(BuildError) as cm:
            Template("<p>ok</p>\n<p>{{ site.name </p>\n<p>fin</p>", "src/x.html")
        msg = str(cm.exception)
        self.assertIn("src/x.html:2", msg)
        self.assertIn("'{{' sin cerrar", msg)

    def test_triple_llave_mal_cerrada_es_error(self):
        with self.assertRaises(BuildError) as cm:
            Template("{{{ content }}", "src/x.html")
        self.assertIn("llaves desbalanceadas", str(cm.exception))

    def test_bloques_mal_cerrados(self):
        with self.assertRaises(BuildError) as cm:
            Template("{{#if a}}x{{/each}}", "src/x.html")
        self.assertIn("se cierra '{{/each}}' pero el bloque abierto es '{{#if}}'", str(cm.exception))
        with self.assertRaises(BuildError) as cm:
            Template("a\n{{#each xs}}x", "src/x.html")
        self.assertIn("src/x.html:2", str(cm.exception))
        self.assertIn("'{{#each}}' sin cerrar", str(cm.exception))
        with self.assertRaises(BuildError) as cm:
            Template("{{/if}}", "src/x.html")
        self.assertIn("sin bloque abierto", str(cm.exception))
        with self.assertRaises(BuildError) as cm:
            Template("{{#with a}}{{/with}}", "src/x.html")
        self.assertIn("bloque no reconocido", str(cm.exception))

    def test_comentarios_y_expresiones_invalidas(self):
        self.assertEqual(self.render("a{{! esto no sale }}b", {}), "ab")
        with self.assertRaises(BuildError) as cm:
            Template("{{ site.name extra }}", "src/x.html")
        self.assertIn("expresión no reconocida", str(cm.exception))
        with self.assertRaises(BuildError):
            Template("{{ }}", "src/x.html")

    def test_offset_de_linea_en_cuerpo_de_pagina(self):
        with self.assertRaises(BuildError) as cm:
            Renderer(self.root / "src", {}, self.root).render(Template("\n{{ nada }}", "src/pages/x.html", line_offset=5), {})
        self.assertIn("src/pages/x.html:7", str(cm.exception))


# ----------------------------------------------------------------------------
# Build completo
# ----------------------------------------------------------------------------

class BuildTests(ProjectCase):
    def test_salida_basica_y_rutas_bonitas(self):
        self.write("src/pages/landing.html", meta(path="/app-agenda/", title="Landing", description="d", body_class="page-landing") + "<h1>L</h1>")
        self.write("src/pages/404.html", meta(path="/404.html", title="No encontrada", description="d", noindex=True) + "<h1>404</h1>")
        b = self.build()
        self.assertTrue((self.root / "dist" / "index.html").is_file())
        self.assertTrue((self.root / "dist" / "app-agenda" / "index.html").is_file())
        self.assertTrue((self.root / "dist" / "404.html").is_file())
        self.assertTrue((self.root / "dist" / "assets" / "img" / "foto.webp").is_file())
        self.assertTrue((self.root / "dist" / "assets" / "icons" / "check.svg").is_file())
        html = self.dist("index.html")
        self.assertIn("<title>Inicio</title>", html)
        self.assertIn("<h1>Hola</h1>", html)
        self.assertIn('<body class="">', html)  # body_class vacío por defecto
        self.assertIn('<body class="page-landing">', self.dist("app-agenda/index.html"))
        self.assertEqual(len(b.pages), 3)
        # sin BOM, saltos LF
        raw = (self.root / "dist" / "index.html").read_bytes()
        self.assertFalse(raw.startswith(b"\xef\xbb\xbf"))
        self.assertNotIn(b"\r\n", raw)

    def test_asset_con_hash_estable(self):
        b1 = self.build()
        css1 = b1.assets["site.css"]
        js1 = b1.assets["site.js"]
        self.assertRegex(css1, r"^/assets/site\.[0-9a-f]{8}\.css$")
        self.assertRegex(js1, r"^/assets/site\.[0-9a-f]{8}\.js$")
        self.assertTrue((self.root / "dist" / css1[1:]).is_file())
        self.assertTrue((self.root / "dist" / js1[1:]).is_file())
        self.assertIn(f'href="{css1}"', self.dist("index.html"))
        self.assertIn(f'src="{js1}"', self.dist("index.html"))
        # mismo contenido -> mismo nombre (idempotente)
        b2 = self.build()
        self.assertEqual(b2.assets["site.css"], css1)
        self.assertEqual(b2.assets["site.js"], js1)
        # cambia el CSS -> cambia el hash y el archivo viejo desaparece de dist
        self.write("src/styles/10-base.css", "body { margin: 0; padding: 0; }\n")
        b3 = self.build()
        self.assertNotEqual(b3.assets["site.css"], css1)
        self.assertFalse((self.root / "dist" / css1[1:]).exists())
        # el CSS se concatena en orden alfabético
        css = self.dist(b3.assets["site.css"][1:])
        self.assertLess(css.index("--bg-0"), css.index("padding: 0"))

    def test_check_no_escribe_nada(self):
        b = self.build(check=True)
        self.assertFalse((self.root / "dist").exists())
        self.assertIn("index.html", b.outputs)
        self.assertIn("sitemap.xml", b.outputs)

    def test_idempotente_borra_basura_de_dist(self):
        self.write("dist/viejo.html", "basura")
        self.build()
        self.assertFalse((self.root / "dist" / "viejo.html").exists())

    def test_site_y_products_calculados(self):
        self.write(
            "src/pages/index.html",
            HOME_PAGE
            + "<p>{{ site.whatsapp_url }}</p><p>{{ site.price_min_fmt }}|{{ site.price_max_fmt }}|{{ site.monthly_plan.price_fmt }}</p>"
            + "{{#each products}}<a href=\"{{ href }}\" data-wa=\"{{ whatsapp_url }}\">{{ precio_fmt }}</a>{{/each}}",
        )
        self.write("src/pages/landing.html", meta(path="/app-agenda/", title="L", description="d") + "<h1>L</h1>")
        html = self.build() and self.dist("index.html")
        self.assertIn("https://wa.me/5218331080178?text=Hola%2C%20quiero%20una%20app%20%26%20m%C3%A1s.", html)
        self.assertIn("$3,900|$7,900|$249", html)
        self.assertIn('href="/app-agenda/"', html)  # product.href = landing_path
        self.assertIn('href="/#productos"', html)  # product.href sin landing
        self.assertIn('data-wa="https://wa.me/5218331080178?text=Hola%2C%20quiero%20la%20agenda"', html)
        self.assertIn(">$7,900</a>", html)

    def test_page_is_home_has_faq_y_faq_items(self):
        self.write("src/sections/faq.html", "<ul>{{#each faq_items}}<li>{{ q }}</li>{{/each}}</ul>")
        self.write("src/sections/landing-faq.html", "<ol>{{#each faq_items}}<li>{{ q }}</li>{{/each}}</ol>")
        flags = "[{{ page.is_home }}/{{ page.has_faq }}]"
        self.write("src/pages/index.html", meta(path="/", title="Inicio", description="d", sections=["faq"]) + flags)
        self.write("src/pages/a.html", meta(path="/a/", title="A", description="d") + "<h1>A</h1>" + flags)
        self.write("src/pages/b.html", meta(path="/b/", title="B", description="d", sections=["landing-faq"]) + "<h1>B</h1>" + flags)
        self.write(
            "src/pages/c.html",
            meta(path="/c/", title="C", description="d", faq=[{"q": "Propia", "a": "sí"}]) + "<h1>C</h1>" + flags
            + "{{#each faq_items}}<i>{{ q }}</i>{{/each}}",
        )
        self.build()
        home = self.dist("index.html")
        self.assertIn("[true/true]", home)
        self.assertIn("<li>¿Cuánto cuesta?</li><li>¿Cuánto tarda?</li>", home)  # faq_items = faq global
        self.assertIn("[false/false]", self.dist("a/index.html"))
        self.assertIn("[false/true]", self.dist("b/index.html"))
        c = self.dist("c/index.html")
        self.assertIn("[false/true]", c)
        self.assertIn("<i>Propia</i>", c)
        self.assertNotIn("¿Cuánto tarda?", c)  # faq_items = page.faq

    def test_secciones_y_cuerpo_propio_en_orden(self):
        self.write("src/sections/uno.html", "<section>uno {{ page.title }}</section>")
        self.write("src/sections/dos.html", "<section>dos</section>")
        self.write("src/pages/index.html", meta(path="/", title="Inicio", description="d", sections=["uno", "dos"]) + "<h1>extra</h1>\n")
        self.build()
        html = self.dist("index.html")
        self.assertRegex(html, r"<section>uno Inicio</section><section>dos</section>\s*<h1>extra</h1>")

    def test_seccion_inexistente_es_error(self):
        self.write("src/pages/index.html", meta(path="/", title="Inicio", description="d", sections=["hero"]))
        self.assert_build_error("sección inexistente 'hero'", "src/sections/hero.html", "src/pages/index.html")

    def test_product_en_meta(self):
        self.write("src/pages/landing.html", meta(path="/app-agenda/", title="L", description="d", product="agenda") + "<h1>{{ product.nombre }} {{ product.precio_fmt }}</h1>")
        self.build()
        self.assertIn("<h1>Agenda de citas $7,900</h1>", self.dist("app-agenda/index.html"))
        self.write("src/pages/landing.html", meta(path="/app-agenda/", title="L", description="d", product="nope") + "<h1>x</h1>")
        self.assert_build_error("el producto 'nope' no existe", "agenda, menu")

    def test_product_ausente_es_falso_en_if_pero_error_directo(self):
        self.write("src/pages/index.html", HOME_PAGE + "{{#if product}}sí{{/if}}{{#unless product}}no{{/unless}}")
        self.build()
        self.assertIn("no", self.dist("index.html"))
        self.write("src/pages/index.html", HOME_PAGE + "{{ product.nombre }}")
        self.assert_build_error("variable inexistente 'product.nombre'", "src/pages/index.html")

    def test_error_variable_inexistente_con_cadena_de_inclusion(self):
        self.write("src/partials/nav.html", "<nav>\n<a>{{ site.nombre }}</a>\n</nav>")
        self.write("src/pages/index.html", HOME_PAGE + "{{> partials/nav}}")
        msg = self.assert_build_error("src/partials/nav.html:2", "variable inexistente 'site.nombre'")
        self.assertIn("incluido desde src/pages/index.html", msg)
        self.assertIn("página src/pages/index.html", msg)

    def test_error_icono_inexistente_en_build(self):
        self.write("src/pages/index.html", HOME_PAGE + '{{ icon "cohete" }}')
        self.assert_build_error("icono inexistente 'cohete'")

    def test_error_llave_sin_cerrar_en_build(self):
        self.write("src/pages/index.html", HOME_PAGE + "<p>{{ site.name </p>\n")
        # el bloque meta ocupa las líneas 1-7 y el <h1> la 8: la línea rota es la 9
        self.assert_build_error("src/pages/index.html:9", "'{{' sin cerrar")

    def test_error_enlace_interno_roto(self):
        self.write("src/pages/index.html", HOME_PAGE + '<a href="/no-existe/">x</a>')
        self.assert_build_error('href="/no-existe/"', "no existe en dist/", "src/pages/index.html")

    def test_error_src_y_content_rotos_y_ok_los_validos(self):
        self.write(
            "src/pages/index.html",
            HOME_PAGE
            + '<img src="/assets/img/foto.webp" alt=""><a href="/#precios">p</a><a href="/?x=1">q</a>'
            + '<a href="mailto:a@b.c">m</a><a href="tel:+52833">t</a><a href="https://otro.test/x">e</a><a href="//cdn.test/x">c</a>'
            + '<meta property="og:image" content="/assets/og/og-image.png"><meta property="og:type" content="website">'
            + '<link rel="canonical" href="https://ejemplo.test/">',
        )
        self.assert_build_error('content="/assets/og/og-image.png"')
        self.write("src/assets/og/og-image.png", b"\x89PNG")
        self.build()  # ahora todo resuelve

    def test_error_enlace_absoluto_al_propio_dominio_roto(self):
        self.write("src/pages/index.html", HOME_PAGE + '<a href="https://ejemplo.test/nada/">x</a>')
        self.assert_build_error('href="https://ejemplo.test/nada/"')

    def test_error_url_en_css_rota(self):
        self.write("src/styles/20-x.css", ".a { background: url(/assets/img/no.webp); }\n.b { background: url('/assets/img/foto.webp'); }\n")
        self.assert_build_error("url()", "/assets/img/no.webp")

    def test_aviso_por_barra_final_faltante(self):
        self.write("src/pages/a.html", meta(path="/a/", title="A", description="d") + "<h1>A</h1>")
        self.write("src/pages/index.html", HOME_PAGE + '<a href="/a">x</a>')
        b = self.build()
        self.assertTrue(any("falta la barra final" in w for w in b.warnings))

    def test_error_path_duplicado(self):
        self.write("src/pages/otra.html", meta(path="/", title="Otra", description="d") + "<h1>x</h1>")
        self.assert_build_error("path duplicado '/'", "src/pages/index.html")

    def test_error_sin_title_o_description(self):
        self.write("src/pages/index.html", meta(path="/", title="Inicio") + "<h1>x</h1>")
        self.assert_build_error("no tiene 'description'")
        self.write("src/pages/index.html", meta(path="/", description="d") + "<h1>x</h1>")
        self.assert_build_error("no tiene 'title'")

    def test_error_meta_ausente_o_invalido(self):
        self.write("src/pages/index.html", "<h1>sin meta</h1>")
        self.assert_build_error("src/pages/index.html:1", "falta el bloque <!--meta")
        # la coma sobrante está en la línea 4 del archivo
        self.write("src/pages/index.html", '<!--meta\n{\n  "path": "/",\n  "title": "x",\n}\n-->\n<h1>x</h1>')
        self.assert_build_error("src/pages/index.html:4", "JSON inválido en el bloque meta")

    def test_error_path_invalido(self):
        self.write("src/pages/index.html", meta(path="/sin-barra", title="x", description="d") + "<h1>x</h1>")
        self.assert_build_error("'path' inválido '/sin-barra'")

    def test_error_partial_ausente_en_layout(self):
        self.write("src/layouts/base.html", "{{> partials/head}}{{{ content }}}")
        self.assert_build_error("src/layouts/base.html:1", "partial inexistente 'partials/head'")

    def test_error_asset_inexistente_en_layout(self):
        self.write("src/layouts/base.html", '<script src="{{ asset "cta.js" }}"></script>{{{ content }}}')
        self.assert_build_error("asset inexistente 'cta.js'", "disponibles:")

    def test_errores_de_varias_paginas_se_reportan_juntos(self):
        self.write("src/pages/a.html", meta(path="/a/", title="A", description="d") + "{{ nada }}")
        self.write("src/pages/b.html", meta(path="/b/", title="B", description="d") + "{{ tampoco }}")
        self.assert_build_error("variable inexistente 'nada'", "variable inexistente 'tampoco'")

    def test_sitemap_y_robots_validos(self):
        self.write("src/pages/landing.html", meta(path="/app-agenda/", title="L", description="d") + "<h1>L</h1>")
        self.write("src/pages/legal.html", meta(path="/legal/privacidad/", title="P", description="d", noindex=True) + "<h1>P</h1>")
        self.write("src/pages/404.html", meta(path="/404.html", title="404", description="d") + "<h1>404</h1>")
        self.build()
        xml = self.dist("sitemap.xml")
        root = ET.fromstring(xml)
        ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        self.assertEqual(root.tag, "{http://www.sitemaps.org/schemas/sitemap/0.9}urlset")
        locs = [u.findtext("s:loc", namespaces=ns) for u in root.findall("s:url", ns)]
        self.assertEqual(locs, ["https://ejemplo.test/", "https://ejemplo.test/app-agenda/"])
        for u in root.findall("s:url", ns):
            self.assertRegex(u.findtext("s:lastmod", namespaces=ns), r"^\d{4}-\d{2}-\d{2}$")
        self.assertTrue(xml.startswith('<?xml version="1.0" encoding="UTF-8"?>\n'))

        robots = self.dist("robots.txt")
        lines = robots.split("\n")
        self.assertEqual(lines[0], "User-agent: *")
        self.assertNotEqual(lines[1].strip(), "", "no debe haber línea en blanco entre User-agent y sus reglas")
        self.assertRegex(lines[1], r"^(Allow|Disallow): ")
        non_empty = [l for l in lines if l.strip()]
        self.assertEqual(non_empty[-1], "Sitemap: https://ejemplo.test/sitemap.xml")
        self.assertTrue(robots.endswith("\n"))

    def test_build_context(self):
        self.write("src/pages/index.html", HOME_PAGE + "<p>{{ build.year }}|{{ build.date }}|{{ build.hash }}</p>")
        import datetime as dt
        b = Builder(self.root, today=dt.date(2026, 9, 17)).run()
        html = self.dist("index.html")
        self.assertIn("<p>2026|2026-09-17|", html)
        self.assertRegex(html, r"\|[0-9a-f]{8}</p>")
        self.assertRegex(b.build["hash"], r"^[0-9a-f]{8}$")

    def test_avisos_de_presupuesto_no_fallan(self):
        self.write("src/scripts/grande.js", "x" * (46 * 1024) + "\n")
        self.write("src/assets/img/pesada.webp", b"\0" * (121 * 1024))
        self.write("src/assets/logo-96.png", b"\0" * (16 * 1024))
        b = self.build()
        joined = "\n".join(b.warnings)
        self.assertIn("el JS total pesa", joined)
        self.assertIn("pesada.webp", joined)
        self.assertIn("logo-96.png", joined)

    def test_aviso_h1(self):
        self.write("src/pages/index.html", meta(path="/", title="Inicio", description="d") + "<p>sin h1</p>")
        b = self.build()
        self.assertTrue(any("<h1>" in w for w in b.warnings))

    def test_cli_exit_codes(self):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = build.main(["--root", str(self.root), "--check"])
        self.assertEqual(code, 0)
        self.assertIn("OK (--check", out.getvalue())
        self.assertFalse((self.root / "dist").exists())

        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = build.main(["--root", str(self.root), "--verbose"])
        self.assertEqual(code, 0)
        self.assertIn("index.html", out.getvalue())
        self.assertTrue((self.root / "dist" / "index.html").is_file())

        self.write("src/pages/index.html", HOME_PAGE + "{{ nada }}")
        err = io.StringIO()
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
            code = build.main(["--root", str(self.root)])
        self.assertEqual(code, 1)
        self.assertIn("error: src/pages/index.html:9: variable inexistente 'nada'", err.getvalue())
        self.assertIn("build fallido.", err.getvalue())


if __name__ == "__main__":
    unittest.main(verbosity=1)
