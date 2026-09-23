# CONTRACT.md — Arquitectura y contrato entre módulos

Quien construya cualquier pieza del sitio se rige por este archivo. Los nombres aquí (carpetas, tokens, clases, sintaxis de plantillas, claves de config) son fijos: si algo falta, se agrega aquí primero.

Raíz del proyecto: `C:/Users/Programador Mx/Documents/programadormx.online` (la ruta tiene un espacio: siempre entre comillas).

## 1. Estructura

```
programadormx.online/
  BRIEF.md · DESIGN.md · CONTRACT.md · README.md · .editorconfig · .gitignore
  site.config.json            datos globales (ver §5)
  data/products.json          productos (ver §6)
  data/faq.json               preguntas frecuentes de la home
  src/
    layouts/base.html         esqueleto <html> común
    partials/                 head.html · nav.html · footer.html · wa-float.html · consent.html · analytics.html
    sections/                 hero.html · products.html · how-it-works.html · pricing.html · faq.html · about.html · contact.html
                              landing-hero.html · landing-features.html · landing-pricing.html · landing-faq.html
    pages/                    index.html · 404.html
                              legal/politica-de-privacidad.html · legal/politica-de-cookies.html · legal/terminos-y-condiciones.html
                              app-agendar-citas-whatsapp.html
    styles/                   00-tokens.css · 10-base.css · 20-components.css · 30-nav.css · 40-code-rain.css
                              50-hero.css · 51-products.css · 52-how-it-works.css · 53-pricing.css · 54-faq.css · 55-about.css · 56-contact.css
                              60-landing.css · 70-legal.css · 90-utilities.css
    scripts/                  code-rain.js · site.js · cta.js
    assets/                   logo.svg (o logo-96.png/logo-192.png) · favicon.svg · favicon-32.png · apple-touch-icon.png
                              icons/*.svg · img/*.webp · og/og-image.html · og/og-image.png
  tools/
    build.py                  genera dist/ (ver §3)
    serve.py                  sirve dist/ en http://localhost:8080 con python http.server
    render-og.py              captura og/og-image.html a PNG 1200×630 con Chrome headless
    tests/test_build.py       unittest del motor de plantillas y de los invariantes de build
  dist/                       salida; se sube tal cual al hosting; nunca se edita a mano
```

Propiedad de archivos durante la construcción en paralelo: cada módulo escribe **solo** sus archivos (ver reparto en el prompt de cada agente). Si necesitas algo de otro módulo, asume el contrato de este documento; no lo escribas tú.

## 2. Sintaxis de plantillas (implementada en `tools/build.py`)

- **Meta de página**: el primer bloque del archivo es un comentario HTML con JSON:
  ```html
  <!--meta
  {
    "path": "/app-agendar-citas-whatsapp/",
    "title": "App para agendar citas por WhatsApp",
    "description": "…",
    "sections": ["landing-hero", "landing-features", "landing-pricing", "landing-faq", "contact"],
    "og_image": "/assets/og/og-image.png",
    "schema": { "@type": "FAQPage" },
    "noindex": false,
    "body_class": "page-landing",
    "product": "agenda-citas-whatsapp"
  }
  -->
  ```
  `path` termina en `/` salvo `/404.html`. Si hay `sections`, el contenido de la página es la concatenación de `src/sections/<n>.html` en ese orden; lo que haya debajo del meta se añade al final (permite contenido propio). `product` (opcional) carga ese producto de `data/products.json` como variable `product`.
- **Inclusión**: `{{> partials/nav}}` y `{{> sections/hero}}` (ruta relativa a `src/`, sin `.html`).
- **Variables**: `{{ site.whatsapp_url }}`, `{{ page.title }}`, `{{ product.nombre }}`. Escapado HTML por defecto; `{{{ var }}}` sin escapar. Rutas con punto. **Variable inexistente = error de build** (modo estricto), salvo dentro de `{{#if}}`.
- **Condicional**: `{{#if site.ga4_id}} … {{/if}}` y `{{#unless x}} … {{/unless}}`. Verdadero = valor no vacío / no `false` / lista no vacía.
- **Bucle**: `{{#each products}} … {{/each}}` sobre listas; dentro, `{{ this.nombre }}` o directamente `{{ nombre }}`; disponibles `{{ @index }}` (0-based) y `{{ @first }}`/`{{ @last }}`.
- **Assets con hash**: `{{ asset "site.css" }}` → `/assets/site.3fa9c2e1.css`; `{{ asset "code-rain.js" }}` → `/assets/code-rain.9b1d…js`. Imágenes y SVG se copian sin hash: `/assets/img/x.webp`.
- **Iconos inline**: `{{ icon "calendar" }}` o `{{ icon product.icon }}` pega el contenido de `src/assets/icons/<nombre>.svg` tal cual (sin escapar). Icono inexistente = error de build.
- **Unir listas**: `{{ join para_quien " · " }}` une una lista con el separador dado (escapado).
- **Contexto disponible en toda plantilla**: `site` (config + `whatsapp_url`, `price_min_fmt`, `price_max_fmt`, `monthly_plan.price_fmt`), `page` (meta + `url` absoluta), `products` (lista; cada producto trae además `whatsapp_url`, `precio_fmt` y `href` = `landing_path` si existe, si no `/#productos`), `faq` (global), `faq_items` (= `page.faq` si la página declara su propia lista, si no `faq`), `product` (si la página lo declara), `build` (`year`, `date`, `hash`). `page` trae además calculados: `is_home` (path `/`), `has_faq` (la página incluye la sección `faq` o `landing-faq`, o declara `faq` propio) y `url`.
- **Rutas fijas**: home `/`; landing de ejemplo `/app-agendar-citas-whatsapp/`; legales `/politica-de-privacidad/`, `/politica-de-cookies/`, `/terminos-y-condiciones/`; `/404.html`. Todo enlace interno se escribe absoluto desde la raíz (`/#precios`, `/politica-de-privacidad/`).
- **Marcado del hero con canvas** (lo escribe la sección, lo consume `code-rain.js`): el primer hijo de `section.hero` es `<canvas class="hero__canvas" data-code-rain data-density="1" data-intensity="1" aria-hidden="true"></canvas>`; el contenido va dentro de `.hero > .container`; el titular es `.hero h1`. `40-code-rain.css` posee `.hero { position; isolation; overflow; background }`, `.hero__canvas` y el respaldo `html.no-js .hero`; `50-hero.css` posee padding, retícula y todo lo demás del hero, sin repetir esas reglas.

## 3. Reglas de `tools/build.py`

1. Lee `site.config.json`, `data/*.json`; calcula `site.whatsapp_url = https://wa.me/<whatsapp>?text=<mensaje_default url-encoded>` y para cada producto `whatsapp_url` con su `mensaje_whatsapp`, y `precio_fmt` (`$7,900`). También `site.price_min_fmt` (mínimo de `precio_desde`, mismo formato) y `site.price_max_fmt`, y `site.monthly_plan.price_fmt` (`$249`).
2. Concatena `src/styles/*.css` en orden alfabético → `dist/assets/site.<hash8>.css`. Copia cada `src/scripts/*.js` → `dist/assets/<nombre>.<hash8>.js`. Hash = primeros 8 hex de sha256 del contenido.
3. Renderiza cada `src/pages/**/*.html` dentro de `src/layouts/base.html` (`{{{ content }}}`) y escribe en `dist<path>index.html` (o `dist/404.html`).
4. Copia `src/assets/**` a `dist/assets/**` (sin hash), y `robots.txt` generado.
5. Genera `dist/sitemap.xml` con todas las páginas sin `noindex` (lastmod = fecha de modificación del archivo fuente, ISO `YYYY-MM-DD`) y `dist/robots.txt` válido (sin líneas en blanco entre `User-agent` y sus reglas; `Sitemap:` al final).
6. **Falla con código ≠ 0 y mensaje claro** si: queda algún `{{` sin resolver, falta un partial/section, una variable no existe, un `href`/`src` interno apunta a algo que no existe en `dist/`, hay dos páginas con el mismo `path`, o una página no tiene `title`/`description`.
7. Avisa (sin fallar) si se excede el presupuesto de BRIEF §9.
8. Es idempotente: borra y regenera `dist/` completo. Todo con `encoding='utf-8'`, `newline='\n'`.
9. `py -3 tools/build.py` sin argumentos construye; `--check` solo valida sin escribir; `--verbose` lista archivos.
10. `tools/tests/test_build.py` prueba: variables/escape, includes, if/unless, each con @index, asset hash, error por variable inexistente, error por enlace roto, sitemap/robots válidos. Se corre con `py -3 -m unittest discover -s tools/tests`.

## 4. Layout base y partials

`src/layouts/base.html`:
```html
<!doctype html>
<html lang="es-MX" class="no-js">
{{> partials/head}}
<body class="{{ page.body_class }}">
  <a class="skip-link" href="#contenido">Saltar al contenido</a>
  {{> partials/nav}}
  <main id="contenido">{{{ content }}}</main>
  {{> partials/footer}}
  {{> partials/wa-float}}
  {{> partials/consent}}
  <script>document.documentElement.classList.replace('no-js','js')</script>
  <script src="{{ asset "site.js" }}" defer></script>
  <script src="{{ asset "cta.js" }}" defer></script>
  {{#if page.code_rain}}<script src="{{ asset "code-rain.js" }}" defer></script>{{/if}}
</body>
</html>
```
`page.code_rain` lo declara la página que tenga hero con canvas (home y landings). `page.body_class` puede ser vacío.

`partials/head.html` (módulo SEO): charset, viewport, `<title>{{ page.title }} · ProgramadorMX</title>` (en home solo el título), description, canonical `{{ page.url }}`, `robots` si `noindex`, Open Graph (`type`, `locale es_MX`, `site_name`, `title`, `description`, `url`, `image` absoluta), Twitter `summary_large_image`, `theme-color`, favicons, `preconnect` a Google Fonts + `<link rel="stylesheet">` con la URL de `DESIGN.md`, `<link rel="stylesheet" href="{{ asset "site.css" }}">`, JSON-LD (ver §8) y `{{> partials/analytics}}`.

`partials/nav.html` (módulo nav): `<header class="nav" data-nav>` con `.nav__inner.container`, `.nav__brand` (logo + `ProgramadorMX`), `<nav class="nav__links" aria-label="Principal">` con enlaces `#productos #precios #como-funciona #preguntas #contacto` y `.nav__cta.btn.btn--primary.btn--wa.btn--sm` a WhatsApp (verde: `.btn--wa` se declara después de `.btn--primary` y gana), `<button class="nav__toggle" aria-controls="menu-movil" aria-expanded="false">`, y `<div id="menu-movil" class="nav__drawer" hidden>`. Los enlaces con `#` funcionan desde cualquier página: en páginas que no son home se escriben como `/#productos`.

`partials/footer.html` (módulo nav): marca + frase, columnas Productos (desde `{{#each products}}` a `/#productos` o a la landing si existe `landing_path`), Contacto (WhatsApp, email, zona), Legal (3 páginas), redes con iconos SVG inline `aria-hidden` + texto visible o `aria-label`. `© {{ build.year }} ProgramadorMX`.

`partials/wa-float.html` (módulo home-b): botón flotante `.wa-float` a `{{ site.whatsapp_url }}` con `data-track="whatsapp_float"`, oculto mientras el hero esté en pantalla (lo maneja `cta.js` con `data-wa-float`).

`partials/consent.html` (módulo SEO): aviso mínimo, solo visible si `site.ga4_id` está lleno; guarda `pmx_consent` en `localStorage`; `analytics.html` solo inyecta gtag si hay `ga4_id` (el consentimiento lo gestiona `cta.js`: no carga gtag hasta que `pmx_consent === "yes"`).

## 5. `site.config.json`

```json
{
  "name": "ProgramadorMX",
  "url": "https://programadormx.online",
  "tagline": "Apps sencillas para tu negocio",
  "description": "Apps móviles y páginas web sencillas para negocios pequeños en México: citas, pedidos y menú digital por WhatsApp, sin comisiones y con precio claro.",
  "whatsapp": "5218331080178",
  "whatsapp_display": "833 108 0178",
  "whatsapp_message": "Hola, vi programadormx.online y quiero una app para mi negocio.",
  "email": "yon.dev.official@gmail.com",
  "owner_name": "",
  "city": "Ciudad Madero, Tamaulipas",
  "service_area": ["Tampico", "Ciudad Madero", "Altamira", "México (remoto)"],
  "hours": "Lunes a viernes, 9:00 a 18:00 (centro de México)",
  "social": {
    "facebook": "https://www.facebook.com/ProgramadorMX",
    "instagram": "https://www.instagram.com/programadormx/",
    "tiktok": "https://www.tiktok.com/@yohanescobarmx",
    "youtube": "https://www.youtube.com/@programadormx"
  },
  "ga4_id": "",
  "monthly_plan": { "price": 249, "label": "Hosting, dominio y soporte" },
  "theme_color": "#0B0F14"
}
```
`theme_color` lo ajusta el módulo de diseño a `--bg-0`.

## 6. `data/products.json`

Lista de objetos con: `slug`, `nombre`, `corto` (≤ 60 caracteres), `para_quien` (lista), `incluye` (lista de 3–5), `precio_desde` (entero MXN), `entrega`, `mensaje_whatsapp`, `keyword` (la búsqueda que lo justifica), `icon` (nombre de archivo en `src/assets/icons/`, sin `.svg`), `landing_path` (opcional, `"/app-agendar-citas-whatsapp/"`), `destacado` (bool). Valores iniciales: tabla de BRIEF §4.

`data/faq.json`: lista de `{ "q": "...", "a": "..." }` (6–8 preguntas; la primera es "¿Cuánto cuesta una app para mi negocio?" con rangos en MXN, porque es la búsqueda que Google cita).

## 7. Tokens y clases (CSS)

`src/styles/00-tokens.css` lo escribe el módulo de diseño con estos nombres (valores en `DESIGN.md`):

```
--bg-0 --bg-1 --bg-2 --bg-3            fondos, del más profundo al más elevado
--ink --ink-2 --ink-3                   texto principal, secundario, atenuado
--line --line-2                         bordes sutil / marcado
--accent --accent-ink --accent-2 --accent-soft   acento, texto sobre acento, acento secundario, lavado
--ok --warn                             semánticos (no cuentan como acento)
--wa                                    verde WhatsApp (#25D366) y --wa-ink
--font-display --font-body --font-mono
--step--1 --step-0 --step-1 --step-2 --step-3 --step-4 --step-5   escala tipográfica fluida (clamp)
--space-1 … --space-9                   escala de espacio (0.25rem … 8rem aprox.)
--radius-1 --radius-2 --radius-3
--shadow-1 --shadow-2
--container (≤ 1160px) --gutter (clamp 1rem–2rem) --section-gap
--dur-1 --dur-2 --dur-3 --ease-out --ease-in-out
```

Clases compartidas (módulo nav escribe `10-base.css`, `20-components.css`, `30-nav.css`, `90-utilities.css`):
- Layout: `.container`, `.section`, `.section--tight`, `.section__head`, `.eyebrow`, `.grid` con `.grid--2/--3`, `.stack` (gap vertical), `.cluster` (gap horizontal con wrap).
- Botones: `.btn`, `.btn--primary`, `.btn--ghost`, `.btn--wa` (WhatsApp), `.btn--sm`, `.btn--lg`. Todo botón WhatsApp lleva `data-track="whatsapp_<contexto>"`.
- Tarjetas: `.card`, `.card--lift` (hover), `.card__icon`, `.card__title`, `.card__meta`, `.price` (`.price__from`, `.price__amount`, `.price__currency`), `.tag`, `.chip`, `.chip--accent`.
- Texto: `.lede`, `.mono`, `.muted`, `.visually-hidden`, `.skip-link`.
- Estado: `.is-open`, `.is-scrolled`, `.is-active`, `.is-visible`, `.reveal` (el elemento **se ve en reposo**; solo con `html.js` y sin `prefers-reduced-motion` parte desplazado y aparece).
- Iconos: SVG inline de 24×24 con `stroke="currentColor"`, `fill="none"`, `stroke-width="1.75"`, `aria-hidden="true"`; archivos en `src/assets/icons/` y se pegan inline en el HTML (no `<img>`).

Cada sección de la home tiene su archivo CSS y su clase raíz: `.hero`, `.products`, `.how`, `.pricing`, `.faq`, `.about`, `.contact`; landings `.landing-*`; legal `.legal`. Ninguna sección redefine tokens ni clases compartidas.

## 8. JSON-LD (módulo SEO, en `head.html`)

- Todas las páginas: `ProfessionalService` con `name`, `url`, `image`, `description`, `areaServed` (de `service_area`), `address` (`addressLocality` Ciudad Madero, `addressRegion` Tamaulipas, `addressCountry` MX), `sameAs` (redes), `priceRange` "$3,900 – $15,000 MXN", `contactPoint` con WhatsApp.
- Home: además `OfferCatalog` con un `Offer` por producto (`price`, `priceCurrency` MXN).
- Página con `faq` visible: `FAQPage` con `mainEntity` desde `data/faq.json` (o `page.faq` propio).
- Landing con `product`: `Product` + `Offer`.

## 9. JavaScript (`window.PMX`)

- `site.js`: `PMX.nav` (clase `.is-scrolled` al bajar 24 px; menú móvil con `aria-expanded`, `hidden`, foco atrapado, Escape, cierre al navegar; sección activa con `IntersectionObserver` de banda central `rootMargin: "-40% 0px -55% 0px"`, `threshold: 0`, que marca `.is-active` en el enlace cuya sección cruza la banda; anclas suaves con `scroll-margin-top` en CSS, no con JS), `PMX.reveal` (añade `.is-visible` a `.reveal`; si `prefers-reduced-motion`, marca todo visible de inmediato). Sin dependencias, ≤ 8 KB.
- `code-rain.js`: `PMX.codeRain.mount(canvas, opts)`; busca `canvas[data-code-rain]` y monta con opciones de `data-*` (`data-density`, `data-intensity`). Cumple BRIEF §9: pausa fuera de pantalla y con pestaña oculta, DPR ≤ 1.5, ~30 fps, `prefers-reduced-motion` → un cuadro estático, en < 768 px baja densidad e intensidad (no se apaga). Los colores salen de `getComputedStyle` sobre tokens (`--accent`, `--accent-2`, `--ink-3`, `--bg-0`), nunca hex fijos. Detalle del tratamiento en `DESIGN.md`.
- `cta.js`: `PMX.track(name, props)` (llama `gtag('event', …)` solo si existe y hay consentimiento); delega clics en `[data-track]`; muestra/oculta `[data-wa-float]` según visibilidad del hero; gestiona `consent.html` y la carga diferida de gtag.

## 9b. Precedencia con DESIGN.md

`DESIGN.md` manda en todo lo visual (valores, medidas, copy del hero, tratamiento del canvas, componentes). Este contrato manda en nombres, rutas, sintaxis y reglas de build. Si DESIGN.md pide una clase o variable que no está aquí, se agrega aquí (ya se agregaron `site.price_min_fmt`, `.btn--wa` en el CTA de la nav y `.chip--accent`).

## 10. Reglas para quien edita

- Escribe archivos con las herramientas Write/Edit o con Python `open(..., encoding='utf-8', newline='\n')`. **Nunca** `Get-Content`/`Set-Content`/`Out-File` de PowerShell sobre archivos del proyecto (rompen acentos).
- Ejecuta Python como `py -3 …` desde la raíz del proyecto.
- Español de México con acentos y signos de apertura (¿ ¡). Revisa "Política", "Términos", "leído", "menú", "cuánto".
- No pongas números de WhatsApp, precios ni emails a mano: siempre desde `site` / `products`.
- Todo lo interactivo es alcanzable por teclado y tiene `:focus-visible`.
- Termina tu trabajo dejando el build en verde: `py -3 tools/build.py --check` (si el build ya existe) y sin `{{` sueltos en tus archivos.
