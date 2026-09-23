# programadormx.online — Brief de reconstrucción

Fecha: 17 sep 2026. Este documento es la fuente de verdad para quien diseñe o construya el sitio. Si algo aquí contradice al código, gana el brief.

## 1. Qué es

Sitio de **ProgramadorMX**: un desarrollador Flutter / .NET con ~4 años de experiencia, en Ciudad Madero, Tamaulipas, que hace **apps móviles sencillas y páginas web para negocios pequeños en México**, de forma remota. El sitio actual vive en `C:/Users/Programador Mx/Documents/web-programador-mx` (referencia) y se sirve desde un nginx de Nominalia (se sube la carpeta `dist/` por FTP/panel; no hay build en el servidor).

Datos reales (van a `site.config.json`):
- Dominio: `https://programadormx.online`
- Email: `yon.dev.official@gmail.com`
- Redes: facebook.com/ProgramadorMX · instagram.com/programadormx · tiktok.com/@yohanescobarmx · youtube.com/@programadormx
- Zona: Tampico, Ciudad Madero y Altamira (presencial) + todo México (remoto)
- WhatsApp: +52 833 108 0178 → en config como `5218331080178` (formato wa.me: 52 + 1 + 10 dígitos). Todo CTA de WhatsApp sale de `site.config.json`, nunca escrito a mano. Formato visible para humanos: `833 108 0178`.

## 2. El trabajo del sitio

Que un dueño de negocio pequeño que buscó en Google algo como *"app para agendar citas por whatsapp"*, *"app para tienda de abarrotes"*, *"menú digital qr"* o *"cuánto cuesta una app para mi negocio"* llegue, entienda en 10 segundos **qué se vende, para quién y desde cuánto**, y escriba por WhatsApp. Un solo objetivo de conversión: **clic en WhatsApp**. Formulario y correo son respaldo.

## 3. Lo que dijo la investigación (14 sep 2026)

- Google Trends MX (12 meses): "página web" 80 vs "crear app" 19; "app para negocio" ≈ 0. La gente **no busca "apps"**, busca resolver algo concreto y saber el precio.
- Autocompletado con intención de compra: *cuánto cuesta una app para mi negocio · app para agendar citas por whatsapp · app para agendar confirmar y recordar citas por whatsapp · app para citas barbería · app para consultorio dental · app para tienda de abarrotes · app de inventario y ventas · menú digital qr · tarjeta de lealtad digital · página web con botón de whatsapp · cuánto se cobra por una página web sencilla*.
- Crece "crear app con IA gratis": quien lo intentó y se atoró es cliente potencial.
- Precios de mercado (MXN): agencias $50K–$150K+ por una app básica; freelance web $3K–$15K; SaaS ~$349/mes para siempre. **Hueco: apps sencillas por giro entre $6K y $15K de pago único** + mensualidad chica de hosting/soporte. Los $999 / $2,999 del sitio actual restan credibilidad.
- En Google no hay anuncios para esas búsquedas; el resumen de IA cita páginas con **tabla de precios en MXN y FAQ**.
- "Punto de venta" lo dominan Clip, Mercado Pago y Loyverse: **no competir ahí**.
- Competencia local (INPROSA, Sidmac, Nautilus 360) vende web y hosting a empresas; nadie le habla a la barbería o la taquería con apps.
- Estado del sitio actual: Lighthouse móvil A11y 97 / BP 100 / SEO 92, pero: solo `/posts/megabasterd/` indexado, cero WhatsApp, sin analítica, sin Google Business, sin JSON-LD ni `og:image`, testimonios y "50+ proyectos" inventados, imágenes de 2 MB, habla de "plantillas" (nadie busca eso), robots.txt inválido, menú que siempre marca "Nosotros".

## 4. Posicionamiento y oferta

**Tesis del hero:** apps sencillas para tu negocio — citas, pedidos y menú digital — sin comisiones y con precio claro.

Productos (fuente única: `data/products.json`; los precios son **hipótesis editables**, el dueño los confirmará con sus primeros clientes):

| slug | Producto | Para quién | Desde (MXN) | Entrega |
|---|---|---|---|---|
| agenda-citas-whatsapp | Agenda de citas con recordatorio por WhatsApp | barberías, salones, uñas, consultorios, dentistas | 7,900 | 2 semanas |
| pedidos-whatsapp | Catálogo y pedidos por WhatsApp sin comisión | abarrotes, taquerías, papelerías, tiendas de ropa | 8,900 | 2–3 semanas |
| menu-digital-qr | Menú digital QR | restaurantes, cafeterías, food trucks | 3,900 | 1 semana |
| tarjeta-lealtad | Tarjeta de lealtad digital | cafés, autolavados, barberías | 5,900 | 1–2 semanas |
| inventario-ventas | Inventario y corte del día | tiendas pequeñas, talleres, gimnasios | 9,900 | 3 semanas |
| pagina-web | Página web con botón de WhatsApp | cualquier negocio que quiera aparecer en Google | 4,900 | 1 semana |

Opcional: hosting, dominio y soporte **$249/mes** (hipótesis). Regla de precio: "precio cerrado antes de empezar, sin sorpresas". Cada producto tiene un mensaje de WhatsApp prellenado ("Hola, quiero la agenda de citas para mi barbería").

Diferenciadores honestos: sin comisiones por venta (la app es del negocio), precio cerrado, entrega en semanas, soporte directo con quien la hizo, demo que se puede tocar (las demos vendrán después; el sitio deja el hueco listo).

## 5. Lo que se conserva del sitio actual (al dueño le gusta)

1. **El fondo de "lluvia de código"** del hero (clase `LetterGlitchBackground` en `web-programador-mx/js/aurora.js`, líneas 573–781): cuadrícula de caracteres que parpadean, viñeta central. Hay que conservar la idea y hacerla **muchísimo mejor**: más profundidad, mejor rendimiento, que parezca código real y no ruido, que reaccione al cursor, que no se apague en móvil sino que baje de intensidad.
2. **La barra de navegación**: logo + nombre a la izquierda, enlaces, botón CTA destacado a la derecha, hamburguesa en móvil con menú a pantalla completa. Conservar la estructura; pulir todo lo demás.
3. **Fondo oscuro.** El sitio es de un solo tema (oscuro) por decisión, con `color-scheme: dark` y contraste AA en todo el texto.
4. Logo: `web-programador-mx/assets/LOGO_WHITE.png` y `LOGO_BLACK.png` (1024 px, 0.5–1.3 MB: hay que generar versiones pequeñas).

## 6. Lo que cambia

- Fuera "plantillas", "50+ proyectos", "30+ clientes", testimonios inventados y emojis como iconos. Nada que no se pueda demostrar.
- Fuera el gradiente cian→azul en todo; el acento lo decide el sistema de diseño y se usa con intención.
- Formulario `mailto:` deja de ser el CTA principal. WhatsApp primero (botón en hero, en cada producto, en precios y flotante); formulario como respaldo.
- Copy para el dueño de negocio, no para programadores: "tú", frases cortas, cero jerga (nada de "UI/UX", "responsivo", "stack"). Español de México **con acentos correctos** (el sitio actual dice "Politica", "leido": eso no se repite).
- Cada página con `<title>`, descripción, canonical, Open Graph con imagen, JSON-LD (`ProfessionalService` en home, `FAQPage` donde haya FAQ, `Product`/`Offer` opcional), sitemap y robots válidos.
- Analítica lista para encender: GA4 se inyecta solo si `site.config.json` trae `ga4_id`; los clics a WhatsApp se registran como evento.
- Sección "Sobre mí" honesta: 4 años, Flutter y .NET, Ciudad Madero, remoto a todo México, sin nombre propio salvo que `owner_name` esté lleno en config.
- Página de ejemplo de landing por intención: `/app-agendar-citas-whatsapp/` (demuestra que la plantilla sirve; las demás landings vendrán después).

## 7. Público y tono

Dueños de barbería, taquería, consultorio, abarrotes, gimnasio: gente ocupada, con celular, que cotiza por WhatsApp y desconfía de lo que suena a "agencia". Tono: claro, cercano, seguro, sin promesas de humo. Ejemplo de frase buena: "Tus clientes agendan solos y les llega el recordatorio. Tú solo abres la app y ves el día." Ejemplo malo: "Soluciones digitales integrales para potenciar tu negocio".

## 8. Restricciones técnicas

- HTML, CSS y JavaScript puros. **Sin frameworks, sin npm, sin node_modules.** Build con Python 3 estándar (`py -3 tools/build.py`).
- Sale a `dist/` como archivos estáticos con URLs bonitas (`/app-agendar-citas-whatsapp/index.html`).
- Un solo CSS concatenado y con hash; JS en archivos pequeños con `defer`. Sin librerías externas de JS.
- Tipografía por Google Fonts (`preconnect` + `display=swap`) con pila de respaldo real; máximo dos familias más una monoespaciada.
- Todo archivo de texto en UTF-8 sin BOM, saltos LF. Nunca editar con `Get-Content`/`Set-Content` de PowerShell (rompe acentos); usar Write/Edit o Python con `encoding='utf-8'`.

## 9. Presupuesto de rendimiento (home, móvil)

- HTML ≤ 60 KB · CSS total ≤ 70 KB · JS total ≤ 45 KB (sin minificar) · sin imagen en el hero (canvas) · imágenes WebP ≤ 120 KB cada una · logo en nav ≤ 15 KB.
- El canvas del fondo: ≤ 30 fps objetivo, `devicePixelRatio` tope 1.5, se pausa si el hero sale de pantalla o la pestaña se oculta, y con `prefers-reduced-motion` dibuja un solo cuadro estático.
- Sin `100vh` que empuje el contenido fuera del primer cuadro en móvil; el hero mide lo que contiene.

## 10. Accesibilidad

Contraste AA en todo (medirlo, no suponerlo). Foco visible en todo lo interactivo. Menú móvil con `aria-expanded`, cierre con Escape y foco atrapado. Un `<h1>` por página. Todo icono decorativo con `aria-hidden`. `prefers-reduced-motion` respetado en CSS y JS. Sin texto dentro de imágenes.

## 11. Lo que NO hacer

- Nada de las fórmulas genéricas de IA: crema + serif + terracota; negro + un solo verde ácido; gradiente morado→azul; todo centrado; `border-radius` grande en cada bloque; Inter/Space Grotesk "por seguridad"; emojis como marcadores de sección; números 01/02/03 donde no hay secuencia.
- No inventar cifras, reseñas ni clientes. Si no hay dato, no hay sección.
- No cargar analítica ni fuentes de terceros que no estén en este brief.
- No editar `dist/` a mano.
