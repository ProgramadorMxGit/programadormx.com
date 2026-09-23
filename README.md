# programadormx.com

## Cómo publicar un cambio

La web se publica sola en **https://programadormx.com** con cada commit a `main`:

```bash
py -3 tools/build.py
git add -A
git commit -m "Describe el cambio"
git push
```

El primer comando es opcional: sirve para revisar en local (`py -3 tools/serve.py`) antes de subir.
Al hacer push, GitHub Actions (`.github/workflows/publicar.yml`) corre las pruebas, construye `dist/`
y la publica en GitHub Pages en 1–2 minutos. Si una prueba o el build fallan, no se publica nada y
la web se queda como estaba; el error se ve en la pestaña **Actions** del repositorio
[ProgramadorMxGit/programadormx.com](https://github.com/ProgramadorMxGit/programadormx.com/actions).

- `dist/` no se sube al repositorio: la genera GitHub en cada publicación.
- El DNS de programadormx.com (Nominalia) apunta a GitHub Pages: A → 185.199.108–111.153 y
  `www` CNAME → programadormxgit.github.io. El correo (MX/SPF) sigue en Nominalia.
- Ya no hace falta subir nada por FTP.

---

Sitio de **ProgramadorMX**: apps móviles sencillas y páginas web para negocios pequeños en México (citas, pedidos y menú digital por WhatsApp, sin comisiones y con precio cerrado). Es un sitio estático: HTML, CSS y JavaScript puros, sin frameworks ni `npm`. Un script de Python arma la carpeta `dist/`, y esa carpeta se sube tal cual al hosting.

Documentos que mandan, en este orden:

| Archivo | Qué decide |
|---|---|
| `BRIEF.md` | Qué es el sitio, para quién, oferta, restricciones y presupuesto de rendimiento. |
| `DESIGN.md` | Todo lo visual: tokens, tipografía, hero, canvas, componentes. |
| `CONTRACT.md` | Nombres, rutas, sintaxis de plantillas, reglas de build y contexto disponible. |

Si algo del sitio contradice a esos archivos, se corrige el sitio.


## Estado del rediseño visual — 17 de septiembre de 2026

La implementación actual está descrita en `DESIGN-REFRESH.md`, que actualiza la dirección visual de `DESIGN.md`. Incluye home completa, landing de agenda y 404. Las páginas legales, analítica y Open Graph ilustrado descritos más abajo pertenecen al plan original; no están implementados en esta versión.

Vista local: `http://localhost:8080/`. La captura inicial `tools/dev/code-rain-preview.html` es un ensayo de canvas que se conserva intacto, no la home nueva. Para ver el rediseño usa el servidor local. Construcción sin dependencias: `py -3 tools/build.py`, luego `py -3 tools/serve.py`.

## Requisitos

- **Python 3.13** (se invoca como `py -3` desde la raíz del proyecto). Solo librería estándar para construir, servir y probar.
- **Google Chrome** instalado, únicamente para generar la imagen de Open Graph (`tools/render-og.py` lo abre en modo headless).
- `Pillow` solo si vas a regenerar los logos con `tools/prep_logo.py` (`py -3 -m pip install pillow`).

La ruta del proyecto tiene un espacio (`C:/Users/Programador Mx/...`): en la consola va siempre entre comillas.

## Comandos

Todos se corren desde la raíz del proyecto.

| Comando | Qué hace |
|---|---|
| `py -3 tools/build.py` | Construye `dist/` completa (la borra y la regenera). Sale con código 1 si algo está mal. |
| `py -3 tools/build.py --check` | Valida todo (plantillas, variables, enlaces internos, meta) **sin escribir nada**. |
| `py -3 tools/build.py --verbose` | Construye y lista cada archivo generado con su tamaño. |
| `py -3 -m unittest discover -s tools/tests -t .` | Corre las pruebas del motor de plantillas y del build (también `py -3 tools/tests/test_build.py`). |
| `py -3 tools/serve.py` | Sirve `dist/` en `http://localhost:8080/` con URLs bonitas y 404 real. Otro puerto: `py -3 tools/serve.py 8081`. |
| `py -3 tools/prep_logo.py` | Genera `logo-96.png`, `logo-192.png`, favicons y `apple-touch-icon.png` en `src/assets/` desde los PNG originales. |
| `py -3 tools/contrast_check.py --tokens` | Tabla de contraste WCAG de los colores de `src/styles/00-tokens.css`. |
| `py -3 tools/render-og.py` | Captura `src/assets/og/og-image.html` a `src/assets/og/og-image.png` (1200 × 630) con Chrome headless. |

El flujo normal de trabajo es: editar en `src/`, `data/` o `site.config.json` → `py -3 tools/build.py` → `py -3 tools/serve.py` y revisar en el navegador → subir `dist/`.

## Cambiar precios, WhatsApp o analítica

Cada dato vive en **un solo archivo**; las plantillas lo leen desde ahí y ninguna página lo tiene escrito a mano.

- **Precios, productos, textos de cada app**: `data/products.json`. Cada producto trae `precio_desde` (entero en MXN), `entrega`, `incluye`, `para_quien`, `mensaje_whatsapp`, etc. El build calcula solo `precio_fmt` (`$7,900`), el enlace de WhatsApp con el mensaje prellenado y el mínimo/máximo para la línea «Desde $3,900 MXN». La mensualidad opcional está en `site.config.json` → `monthly_plan.price`.
- **Preguntas frecuentes**: `data/faq.json` (lista de `{ "q", "a" }`). Si cambias un precio en `products.json`, revisa que la primera respuesta del FAQ siga diciendo lo mismo.
- **Número de WhatsApp**: `site.config.json` → `whatsapp` (formato `wa.me`: `52` + `1` + 10 dígitos, p. ej. `5218331080178`) y `whatsapp_display` (como se lee: `833 108 0178`). El mensaje que llega prellenado desde los botones generales es `whatsapp_message`.
- **Correo, ciudad, horario, redes**: también en `site.config.json` (`email`, `city`, `hours`, `service_area`, `social`).
- **Google Analytics 4**: `site.config.json` → `ga4_id`. Vacío = no se carga nada de analítica ni el aviso de cookies. Con un valor (`G-XXXXXXX`) se inyecta gtag solo después de que la persona acepta el aviso; los clics a WhatsApp se registran como eventos.

Después de cualquier cambio: `py -3 tools/build.py` y subir `dist/`.

## Agregar una landing nueva en 4 pasos

Las landings por intención de búsqueda (`/app-agendar-citas-whatsapp/` es la de ejemplo) reutilizan las mismas secciones; solo cambia el meta.

1. Copia `src/pages/app-agendar-citas-whatsapp.html` con un nombre nuevo, por ejemplo `src/pages/app-pedidos-whatsapp.html`.
2. Cambia el bloque `<!--meta { ... } -->` del inicio: `path` (termina en `/`), `title`, `description`, y `product` con el `slug` del producto en `data/products.json`. Si quieres que el producto enlace a la landing desde la home y el footer, agrega `"landing_path": "/app-pedidos-whatsapp/"` a ese producto.
3. Ajusta la lista `sections` si hace falta (por defecto `landing-hero`, `landing-features`, `landing-pricing`, `landing-faq`, `contact`) y, si quieres, escribe HTML propio debajo del meta: se añade al final del contenido.
4. `py -3 tools/build.py`. El sitemap, el canonical y los enlaces internos se actualizan solos. Si algo falta (un icono, una variable, un enlace roto), el build te lo dice con archivo y línea.

## Desplegar

El hosting (Nominalia) es un **nginx estático**: no ejecuta Python ni hay build en el servidor.

1. `py -3 tools/build.py` (debe terminar en `OK`; los avisos de presupuesto no bloquean, pero conviene atenderlos).
2. Sube **todo el contenido** de `dist/` a la carpeta pública del hosting por FTP o desde el panel, respetando la estructura de carpetas (`index.html`, `404.html`, `sitemap.xml`, `robots.txt`, `assets/`, una carpeta por página).
3. Borra en el servidor los archivos que ya no existen en `dist/` (por ejemplo, el CSS con el hash anterior); si no, quedan huérfanos.
4. Comprueba en el navegador `https://programadormx.online/`, una landing y una URL inventada (debe responder la página 404).

Si el panel permite configurar la página de error, apunta el 404 a `/404.html`.

## Estructura de carpetas

```
programadormx.online/
  BRIEF.md · DESIGN.md · CONTRACT.md · README.md
  site.config.json          datos globales: nombre, dominio, WhatsApp, email, horario, redes, GA4, mensualidad
  data/products.json        los seis productos (precios, textos, iconos, landing)
  data/faq.json             preguntas frecuentes de la home
  src/
    layouts/base.html       esqueleto <html> común a todas las páginas
    partials/               head, nav, footer, botón flotante de WhatsApp, aviso de cookies, analítica
    sections/               bloques de la home (hero, products, how-it-works, pricing, faq, about, contact)
                            y de las landings (landing-hero, landing-features, landing-pricing, landing-faq)
    pages/                  una página por archivo; el meta JSON del inicio define ruta, título y secciones
    styles/                 CSS por capas (00-tokens … 90-utilities); se concatenan en orden alfabético
    scripts/                code-rain.js (fondo del hero), site.js (nav, reveal), cta.js (WhatsApp, GA4, consentimiento)
    assets/                 logos, favicons, icons/*.svg (se pegan inline), img/*.webp, og/ (imagen de Open Graph)
  tools/
    build.py                genera dist/
    serve.py                servidor local
    render-og.py            captura la imagen de Open Graph con Chrome
    prep_logo.py            versiones ligeras del logo
    contrast_check.py       ratios de contraste de los tokens
    tests/test_build.py     pruebas del build
  dist/                     salida generada; se sube completa al hosting y NUNCA se edita a mano
```

### Cómo se arma una página

`tools/build.py` lee `site.config.json` y `data/*.json`, concatena `src/styles/*.css` en un solo archivo con hash (`/assets/site.3fa9c2e1.css`), copia cada script con hash, y renderiza cada `src/pages/**/*.html` dentro de `src/layouts/base.html`. La sintaxis completa de plantillas está en `CONTRACT.md §2`; en resumen:

```html
{{> partials/nav}}                 incluye src/partials/nav.html
{{ site.whatsapp_display }}        variable (se escapa HTML); {{{ var }}} sin escapar
{{#if site.ga4_id}} … {{/if}}      condicional; {{#unless x}} … {{/unless}}; admite {{else}}
{{#each products}} {{ nombre }} {{ @index }} {{/each}}   bucle (anidable; también {{ this }}, {{ @first }}, {{ @last }})
{{ asset "site.css" }}             ruta con hash del CSS o de un script
{{ icon "calendar" }}              pega inline src/assets/icons/calendar.svg
{{ join para_quien " · " }}        une una lista
```

Una variable que no existe es error de build (salvo como condición de `#if`/`#unless`), igual que un partial, sección, icono o enlace interno inexistente. Así un error de dedo no llega al servidor.

## Reglas de edición

- Todo archivo de texto en **UTF-8 sin BOM** y saltos de línea **LF** (`.editorconfig` ya lo pide; el build avisa si encuentra un BOM).
- **Nunca** edites archivos del proyecto con `Get-Content` / `Set-Content` / `Out-File` de PowerShell: rompen los acentos. Usa el editor, o Python con `open(..., encoding="utf-8", newline="\n")`.
- **Nunca edites `dist/`**: se borra y se regenera en cada build. Lo que quieras cambiar, cámbialo en `src/`, `data/` o `site.config.json`.
- Precios, WhatsApp, correo y horario nunca se escriben a mano en una plantilla: siempre `{{ site.… }}` o `{{ producto.… }}`.
- Español de México con acentos y signos de apertura (`¿ ¡`). Nada de emojis, cifras inventadas ni testimonios.
- Los enlaces internos se escriben absolutos desde la raíz y con barra final: `/politica-de-privacidad/`, `/#precios`.
- Antes de subir: `py -3 -m unittest discover -s tools/tests -t .` y `py -3 tools/build.py` en verde.

## Si el build falla

El build termina con código 1 y escribe en la consola uno o más errores con **archivo y línea**, y la cadena de inclusión cuando el problema está dentro de un partial:

```
error: src/partials/nav.html:12: variable inexistente 'site.nombre': 'site' existe pero no tiene 'nombre' (claves: city, email, …)
           ← incluido desde src/layouts/base.html:6
           ← página src/pages/index.html
build fallido.
```

Los casos más comunes:

| Mensaje | Qué revisar |
|---|---|
| `variable inexistente '…'` | Nombre mal escrito o clave que no está en `site.config.json` / `products.json`. El mensaje lista las claves disponibles. |
| `partial inexistente` / `sección inexistente` | La ruta en `{{> partials/x}}` o el nombre en `sections` del meta no coincide con el archivo en `src/`. |
| `icono inexistente 'x'` | Falta `src/assets/icons/x.svg` o el campo `icon` del producto está mal. |
| `asset inexistente 'x.js'` | No existe `src/scripts/x.js` (o `src/styles/` está vacío para `site.css`). |
| `'{{' sin cerrar` | Una etiqueta sin `}}` en esa línea. |
| `se cierra '{{/each}}' pero el bloque abierto es '{{#if}}'` | Bloques cruzados o sin cerrar; el mensaje dice en qué línea se abrió. |
| `href="…" apunta a algo que no existe en dist/` | Enlace interno a una página o archivo que no se genera. Revisa el `path` de la página destino o la ruta del archivo en `src/assets/`. |
| `path duplicado` | Dos páginas con el mismo `path` en su meta. |
| `la página no tiene 'title'` / `'description'` | Falta esa clave en el bloque meta. |
| `JSON inválido` | Coma sobrante o comillas mal cerradas en el meta o en `data/*.json`; la línea indicada es la del error. |

Los mensajes que empiezan con `aviso:` no detienen el build: son el presupuesto de rendimiento de `BRIEF.md §9` (HTML de la home ≤ 60 KB, CSS ≤ 70 KB, JS ≤ 45 KB, imágenes WebP ≤ 120 KB, logo de la nav ≤ 15 KB), páginas sin un único `<h1>`, o enlaces internos a los que les falta la barra final.
