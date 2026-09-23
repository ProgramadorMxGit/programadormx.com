# Rediseño visual — 17 de septiembre de 2026

Implementación solicitada por el usuario a partir de code-rain-preview.html. Esta dirección actualiza las decisiones visuales anteriores de DESIGN.md: oscuro cálido, acento albaricoque, titulares Bricolage, retícula editorial y demo de producto con datos explícitamente ilustrativos. Conserva la arquitectura estática, datos comerciales y lluvia de código existente.

La home real se construye desde src/pages/index.html y src/sections/*.html. CSS en 10-premium.css, 98-readability.css y 99-premium-motion.css. site.js añade navegación móvil, demo accesible, revelados y pausa de movimiento. Los precios y destinos WhatsApp se leen de los JSON originales. No se ha publicado la web.

La demo del hero funciona localmente; no guarda citas ni envía mensajes. Los botones comerciales abren WhatsApp para que el visitante envíe su mensaje. No se simulan reseñas, clientes ni resultados comerciales.

Construcción: py -3 tools/build.py. Vista: py -3 tools/serve.py 8080. El archivo tools/dev/code-rain-preview.html se conserva como ensayo técnico original.

## Paleta grafito + índigo — 23 de septiembre de 2026

Basada en la medición de 20 apps exitosas (`Documents\AI Claude\_investigacion-color\INFORME.md`): neutros casi totales, casi negro teñido, texto casi blanco, un solo acento y botón principal monocromo.

- Fondo `#0a0b0d`, superficies `#111215` / `#17181c` / `#1f2125`, texto `#ededef` / `#b4b7bf` / `#8a8f98`, bordes `#25272c` / `#6a6e78`.
- Único acento: índigo `#7c85f0` (eyebrows, palabra clave del titular, enlaces activos, foco, detalles de la demo).
- Botón principal: blanco con texto negro. Panel de contacto: banda casi blanca con botón negro.
- Verde solo para WhatsApp (`#25d366`) y el "listo" (`--ok`).
- Los 160 colores escritos a mano se convirtieron con `tools/dev/repaleta.py` (OKLCH, misma luminosidad relativa). La paleta cálida anterior está en `tools/dev/paleta-anterior/`; para volver, copiar esos archivos a `src/styles/`.
- Contraste auditado en el navegador: 206 textos de la home y 39 de la landing, todos ≥ WCAG AA.
- Pendiente: las tarjetas para compartir (`src/assets/og/*.jpg`) y `tools/dev/og/tarjeta*.html` siguen en la paleta cálida.
