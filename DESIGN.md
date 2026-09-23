# DESIGN.md — programadormx.online

Dirección elegida: **"Código de mostrador"** (ganadora por unanimidad de los tres jueces: 51 / 50 / 51 puntos), con injertos de "Mostrador de barrio" y "Tinta y ámbar" y con todos los puntos de "concerns" resueltos aquí. Este documento manda sobre el CSS y el JS: si algo se ve distinto en el sitio, se corrige el sitio.

Fecha: 17 sep 2026. Tokens en `src/styles/00-tokens.css`. Lámina de estilo: `DESIGN-tile.html`. Verificación de contraste: `py -3 tools/contrast_check.py --tokens`.

---

## 0. Decisión de dirección

**Por qué "Código de mostrador".** Es la única propuesta que cumple BRIEF §2 literalmente: en el primer pantallazo el dueño lee para quién (eyebrow), qué (h1) y desde cuánto (el cajón de precios a la derecha, generado desde `products.json`, sin inventar nada). Tiene la disciplina de acento más estricta (el ámbar vive en la tipografía, el único relleno saturado es el verde de WhatsApp), el sistema de "ticket" (reglas punteadas, líderes de puntos, eyebrows mono con cursor) es reconocible para una taquería y no lo usa ninguna agencia local, y su canvas es el más sobrio de construir. Ningún riesgo de ingeniería o accesibilidad la invalida.

**Injertos aceptados** (lo que la mejora sin diluirla):

| De | Idea injertada | Dónde queda |
|---|---|---|
| Mostrador de barrio | h1 en la voz del brief §7: «Tus clientes agendan y piden solos. Tú abres la app y ves tu día.», jerarquía por peso 800/500 | §6 Hero |
| Mostrador de barrio | Línea de confianza «Te respondo yo, no un bot · {{ site.hours }}» | §6 Hero |
| Mostrador de barrio | Atenuación precalculada por celda (Float32Array) con un **charco radial bajo el titular**: la viñeta central del sitio actual sobrevive, anclada al h1 | §5 Fondo |
| Mostrador de barrio | Tokenizar el corpus una vez (palabras clave → accent-2, cadenas → accent, resto → ink-3) | §5 Fondo |
| Mostrador de barrio | Linterna autónoma (Lissajous lenta) en `(hover: none)`; relojes reiniciados al reanudar; ruta de escape con atlas de glifos; respaldo `html.no-js` con papel rayado | §5 Fondo |
| Mostrador de barrio | Paso 1 de "Cómo funciona" como burbuja de WhatsApp con el mensaje real de config | §7 Secciones |
| Tinta y ámbar | Foco del cursor por composición (`destination-in` + `createRadialGradient`) en vez de multiplicar alfas celda a celda | §5 Fondo |
| Tinta y ámbar | Fundidos superior e inferior del canvas con `mask-image` en CSS, no con rectángulos por cuadro | §5 Fondo |
| Tinta y ámbar | `document.fonts.load('500 14px "IBM Plex Mono"')` con tope de 2 s en vez de `fonts.ready` | §5 Fondo |
| Tinta y ámbar | Columna «Para quién» en la tabla de precios; `<table>` real también en móvil | §7 Secciones |
| Tinta y ámbar | `text-wrap: balance` en h1/h2; `@font-face` de respaldo con `size-adjust`; `@supports (backdrop-filter)` con fondo sólido de respaldo; FAQ con `grid-template-rows: 0fr → 1fr` | §4, §6, §9 |
| Tinta y ámbar | Regla de convivencia ámbar/verde: el ámbar nunca dentro de un botón ni a menos de 16 px de un botón WhatsApp | §12 Sí / No |

**Injertos rechazados**: el celular CSS y las seis mini pantallas con negocios ficticios (chocan con BRIEF §6 "nada que no se pueda demostrar" y con el presupuesto), el zigzag de ticket por `clip-path` (empalaga; tope de una regla punteada por sección), el eyebrow en mayúsculas espaciadas (default editorial que el brief pide evitar), la lluvia monocroma ámbar (la referencia era multicolor y el dueño quiere "muchísimo mejor", no "menos"), la retícula de fichas con hairlines compartidas (el contrato ya define `.card`; una sola rejilla de tarjetas basta).

**Concerns resueltos** (los ocho/diez de cada juez, agrupados):

1. **CTA de la barra sin verde** → decisión única: **todo enlace a WhatsApp es verde**, sin excepción. El CTA de la nav conserva las clases del contrato y añade el modificador: `.nav__cta.btn.btn--primary.btn--wa.btn--sm` (`.btn--wa` va después de `.btn--primary` en `20-components.css` y gana). El botón "papel" (`.btn--primary`) queda para el envío del formulario. Para que la barra no compita con la lluvia, el canvas se funde bajo la nav con `mask-image` (96 px) y el botón es `--sm` (36 px).
2. **"Desde cuánto" en celular** → en móvil el cajón de precios va **inmediatamente después de los CTAs** y en versión compacta (filas de 36 px, seis filas, sin pie largo); la línea meta va después. Además se pide al contrato una variable calculada `site.price_min_fmt` (mínimo de `precio_desde`, formateado) para la línea meta «Desde {{ site.price_min_fmt }} MXN, pago único» (ver §14). Verificación obligatoria con captura real a 360×740 y 390×844.
3. **h1 abstracto** → se adopta la frase del brief §7 (ver §6). «Sin comisiones y con precio cerrado» pasa al lede.
4. **Que se lea "programador" y no "ticket"** → tope de **una** regla punteada por sección (más las internas de la tabla y del FAQ), sedimento de la lluvia a alfa **0.10** (piso, también en móvil), y legibilidad del h1 validada con captura, no solo con ratios.
5. **Rendimiento del canvas** → nada de gradientes ni `shadowBlur` por cuadro: atenuación precalculada, sedimento en offscreen, spot por composición, fundidos en CSS. Por cuadro: 1 `clearRect`, 1 `drawImage` (sedimento), ≤ ~400 `fillText` (streams activos), 1 `drawImage` (spot). Autoajuste con histéresis (§5).
6. **Viñeta central eliminada** → no se elimina: se convierte en el **charco bajo el titular** (atenuación radial centrada en el bbox del h1). Al dueño se le presenta como continuidad: "el centro oscuro sigue ahí, ahora debajo de tu titular".
7. **Medida de celda con fuente de respaldo** → `fonts.load` con la cadena exacta, tope 2 s, re-medida y reconstrucción de la rejilla al resolver; el primer cuadro con Consolas/Cascadia es válido pero se redibuja.
8. **"la carta" suena a restaurante** → la cabecera del cajón dice `precios desde` y la clase es `.hero__precios`.
9. **ink-3 sobre accent-soft (4.07:1 en la propuesta)** → se aclaró `--ink-3` a `#9C938A` y se oscureció `--accent-soft` a `#33240F`: ahora 4.97:1 (AA). ink-3 sobre bg-3 sube a 4.82:1 (AA). Ya no hace falta prohibirlo, pero se documenta.
10. **Bordes de controles** → `--line-2` deja de ser decorativo-invisible y pasa a `#726B61` (3.55:1 sobre bg-0, 3.35 sobre bg-1, 3.10 sobre bg-2): sirve como borde de inputs y ghost sin `color-mix` que alguien pueda olvidar. `--line` sigue siendo la hairline decorativa.
11. **Semántica de la tabla en móvil** → se mantiene `<table>` con `role="table" / "row" / "columnheader" / "cell"` explícitos cuando `display` cambia, y `td::before` con el nombre de la columna en mono.
12. **Payload tipográfico** → se quitan Plex Mono 600 e italic: 1 variable (Bricolage) + 3 estáticas (Plex Sans) + 2 estáticas (Plex Mono). Medir en Lighthouse; si duele, plan B en §4.
13. **Tres apariciones del precio (cajón, tarjeta, tabla)** → una sola fuente (`precio_fmt`), destinos: cajón del hero → `landing_path` si existe, si no `/#productos`; tarjeta y tabla → WhatsApp del producto.
14. **Bricolage 800 en titulares largos** → h1 ≤ 11 palabras por oración, h2 en 700, h3 en 600; plan B: Archivo variable.

---

## 1. Tesis

El código es el material de toda la página, pero se lee como lo que un dueño de negocio ya maneja: **el ticket de la caja y el pizarrón de precios**. La monoespaciada habla de "ticket" y "corte del día", no de hacker. La lluvia del hero teclea código real de las apps que se venden (citas, pedidos, menú) con comentarios en español, en penumbra, y se enciende alrededor del cursor. La calidez la ponen tres decisiones: fondo carbón cálido (no negro azulado), acento ámbar de "foco de negocio abierto" que vive en la tipografía y nunca rellena un botón, y reglas punteadas de ticket con líderes de puntos en lugar de tarjetas por todos lados. El verde de WhatsApp es el único relleno saturado: **verde = aquí me escribes**.

---

## 2. Tokens

| Token | Hex | Rol |
|---|---|---|
| `--bg-0` | `#15120F` | Fondo base: body, hero, canvas. `theme_color`. Carbón cálido. |
| `--bg-1` | `#1C1814` | Bandas alternas (cómo funciona, sobre mí, footer), tarjetas de producto, cajón de precios del hero (al 60 %). |
| `--bg-2` | `#241F1A` | Superficies dentro de tarjetas: caja del icono, chips neutros, hover de fila en la tabla. |
| `--bg-3` | `#2E2823` | Hover/elevado de tarjeta, fondo del cajón móvil. |
| `--ink` | `#F4EEE6` | Texto principal, titulares, cifras. Relleno del botón papel. |
| `--ink-2` | `#BDB3A7` | Texto secundario: ledes, párrafos de tarjeta, enlaces de nav en reposo, respuestas del FAQ. |
| `--ink-3` | `#9C938A` | Texto atenuado en mono: meta, "MXN", entrega, placeholders, sedimento de la lluvia. AA sobre bg-0/1/2/3 y accent-soft. |
| `--line` | `#2A241F` | Hairline decorativa: borde de tarjetas en reposo, divisor de nav scrolled, separadores del footer. Nunca único borde de un control. |
| `--line-2` | `#726B61` | Borde de controles (inputs, ghost) y reglas punteadas de ticket, líderes de puntos, hover de tarjeta. ≥ 3:1 sobre bg-0/1/2. |
| `--accent` | `#F0A63C` | Ámbar: cursor de bloque, eyebrows, "desde", subrayado del enlace activo, "+" del FAQ abierto, anillo de foco, cadenas de texto en la lluvia. Nunca relleno de botón. |
| `--accent-ink` | `#1C1206` | Texto sobre ámbar (badge relleno, checkbox marcado). |
| `--accent-2` | `#7FB8C9` | Azul-verdoso, el frío del editor: iconos de producto, palabras clave de la lluvia, `.mono` en párrafos. |
| `--accent-soft` | `#33240F` | Lavado ámbar: fondo del chip destacado, fondo del paso activo, anillo exterior de foco en inputs. |
| `--ok` | `#7CC48B` | Éxito de formulario, "incluido". Semántico. |
| `--warn` | `#E8785A` | Error de formulario. Coral para no confundirse con el ámbar. Semántico. |
| `--wa` | `#25D366` | Relleno de todo botón WhatsApp (`.btn--wa`, `.wa-float`, `.nav__cta`). Único relleno saturado. |
| `--wa-ink` | `#072D16` | Texto y glifo sobre verde WhatsApp. |

Espacio, radios, sombras, layout y movimiento: ver `00-tokens.css` (valores comentados ahí). Resumen: `--space-1…9` = 0.25 / 0.5 / 0.75 / 1 / 1.5 / 2 / 3 / 4.5 / 7 rem · `--radius-1/2/3` = 4 / 8 / 14 px · `--container` 1160 px · `--gutter` clamp(1rem, 4vw, 2rem) · `--section-gap` clamp(4rem, 9vw, 7rem) · `--dur-1/2/3` = 140 / 260 / 480 ms.

**`theme_color` recomendado: `#15120F`** (igual a `--bg-0`). Sustituye al `#0B0F14` de `site.config.json`.

---

## 3. Tipografía

**Familias** (dos más una mono, todas en Google Fonts; URL verificada HTTP 200 el 17 sep 2026, sirve las tres familias):

```
https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500..800&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;500;600&display=swap
```

En `head.html`: `<link rel="preconnect" href="https://fonts.googleapis.com">`, `<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>`, y el stylesheet con esa URL exacta.

| Rol | Familia | Pesos | Uso |
|---|---|---|---|
| Display | **Bricolage Grotesque** (variable, opsz 12–96, wght 500–800) | 800 solo h1 de home y landings · 700 h2 y marca en nav · 600 h3, títulos de tarjeta, summary del FAQ, enlaces del cajón móvil · 500 segunda oración del h1 | Solo de `--step-1` hacia arriba; nunca en texto chico. `font-optical-sizing: auto`. |
| Cuerpo | **IBM Plex Sans** | 400 párrafos · 500 enlaces de nav, labels, nombres en tabla y cajón · 600 texto de botones | Todo el texto corrido. |
| Mono | **IBM Plex Mono** | 400 meta, corpus de la lluvia, comentarios · 500 eyebrows, precios, cabeceras de tabla, chips, `.price__amount` en tabla | "Mono = dato": todas las cifras del sitio van en mono con `font-variant-numeric: tabular-nums`. |

**Pilas de respaldo** (en `00-tokens.css`):

```
--font-display: "Bricolage Grotesque", "Bricolage Fallback", "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
--font-body:    "IBM Plex Sans", "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
--font-mono:    "IBM Plex Mono", "Cascadia Mono", Consolas, "Roboto Mono", Menlo, monospace;
```

`10-base.css` declara el respaldo métrico para que el swap no mueva el hero más de 2 px:

```css
@font-face {
  font-family: "Bricolage Fallback";
  src: local("Arial"), local("Liberation Sans");
  size-adjust: 97%;
  ascent-override: 92%;
  descent-override: 24%;
  line-gap-override: 0%;
}
```

**Escala fluida** (min a 360 px, max a 1160 px; los valores en `00-tokens.css`):

| Token | Rango | line-height | letter-spacing | Uso |
|---|---|---|---|---|
| `--step--1` | 13 → 15 px | 1.5 | 0 | meta, chips, eyebrows, cabeceras de tabla |
| `--step-0` | 16 → 18 px | 1.6 | 0 | cuerpo, botones, filas del cajón |
| `--step-1` | 18 → 22 px | 1.4 | 0 | lede, títulos de tarjeta, summary del FAQ |
| `--step-2` | 22 → 28 px | 1.25 | 0 | `.price__amount` en tarjeta |
| `--step-3` | 28 → 40 px | 1.12 | −0.01em | h2 de sección, enlaces del cajón móvil |
| `--step-4` | 34 → 56 px | 1.06 | −0.02em | h1 de landings |
| `--step-5` | 36 → 72 px | 1.02 | −0.025em | h1 de la home (el hero lo capa a 4rem: `font-size: min(var(--step-5), 4rem)` para que quepa en 8 columnas) |

**Reglas de composición**

- Párrafos `max-width: 62ch`; ledes `56ch` (hero `52ch`); h1 `max-width: 20ch`; h2 `22ch`.
- `text-wrap: balance` en h1, h2, h3 y summary del FAQ desde 600 px; por debajo, `text-wrap: pretty` (verificado en la lámina: con `balance` a 390 px el h1 se parte en 8 líneas de una o dos palabras). `text-wrap: pretty` en párrafos (progresivo).
- Eyebrows: `--font-mono` 500, `--step--1`, **minúsculas**, `letter-spacing: 0.02em`, color `--accent`, precedidos de un cursor de bloque `▍` (0.55ch × 1em, `--accent`) hecho con `::before`. Nada de mayúsculas espaciadas.
- Cifras: `font-variant-numeric: tabular-nums` en `.mono`, `.price__amount`, tabla y cajón.
- Comillas españolas « » en el copy; signos de apertura ¿ ¡ siempre.
- Números en el h1 y en párrafos: en la misma familia; solo los precios van en mono.

---

## 4. Fondo de código (especificación para `code-rain.js`)

`PMX.codeRain.mount(canvas, opts)` monta sobre `canvas[data-code-rain]` dentro de `.hero`. Colores solo desde tokens. Detalle:

### 4.1 Glifos y corpus

Nada de caracteres al azar. Un array `CORPUS` de ~28 líneas de ≤ 44 caracteres en Dart/Flutter, SQL y JSON del dominio de las seis apps, con comentarios en español y **sin cifras que parezcan precios** ni promesas (la única regla de producto que aparece es "sin comisiones", porque es real):

```
final cita = Cita(hora: '10:30', cliente: 'Luis');
await recordatorio.enviar(cita, via: WhatsApp);
// le llega el recordatorio un día antes
citas.where((c) => c.dia == hoy).toList();
if (mesa.ocupada) return;
pedido.total += producto.precio * cantidad;
// sin comisiones: el pedido llega directo
"menu": ["pastor", "bistec", "suadero"]
qr.generar(url: menu.url);
sellos.agregar(cliente);
if (sellos.length == 10) premio.otorgar();
inventario.descontar('shampoo', cantidad);
corteDelDia.imprimir();
SELECT SUM(total) FROM ventas WHERE dia = HOY;
UPDATE inventario SET stock = stock - 1 WHERE sku = @sku;
whatsapp.abrir(mensaje: 'Hola, quiero agendar');
return Scaffold(body: Agenda());
class Pedido { final List<Producto> items; }
db.insert('ventas', venta.toMap());
final hoy = DateTime.now();
// el dueño abre la app y ve su día
List<Cita> agenda = await repo.deHoy();
Text(cliente.nombre, style: negrita);
carrito.agregar(taco, cantidad: 3);
// la app es del negocio, no de una plataforma
mensaje = 'Tu cita es mañana a las ${cita.hora}';
horarios = [9, 10, 11, 12, 16, 17, 18];
notificar(negocio.telefono, pedido.resumen());
```

**Tokenización, una sola vez al montar**: cada línea se parte en celdas `{ch, k}` donde `k` ∈ {0 resto, 1 palabra clave, 2 cadena, 3 comentario}. Palabras clave: `final await class if return List SELECT SUM FROM WHERE UPDATE SET Text Scaffold`. Cadenas: todo lo que va entre `'…'` o `"…"`. Comentario: desde `//` hasta el fin. Color por `k`: 0 → `--ink-2`, 1 → `--accent-2`, 2 → `--accent`, 3 → `--ink-3`. El sedimento (§4.2 A) ignora `k` y va todo en `--ink-3`.

**Celda**: `ctx.font = '500 14px ' + fontMono` (13 px en < 768). `charWidth = Math.round(measureText('M').width * 2) / 2 + 1` (≈ 9.4 px con Plex Mono a 14 px), `charHeight = 22` (20 en móvil), `textBaseline = 'alphabetic'`, y = fila × charHeight + 16. `fontMono` se lee de `getComputedStyle(document.documentElement).getPropertyValue('--font-mono')`.

**Carga de fuente**: se dibuja de inmediato con la pila de respaldo y se llama `document.fonts.load('500 14px "IBM Plex Mono"')` con `Promise.race` contra un `setTimeout` de 2000 ms; al resolver (con fuente o sin ella) se re-mide la celda y, si cambió, se reconstruye la rejilla y el sedimento. Nunca `fonts.ready` solo.

### 4.2 Capas (un solo canvas visible, dos offscreen)

**A. Sedimento** (offscreen `sed`, tamaño del hero × DPR): la rejilla completa rellena con el corpus envuelto línea a línea con offsets de columna aleatorios (parece un archivo fuente desenfocado, no ruido). Color `--ink-3`, **alfa 0.10** (piso; no baja en móvil). Se pre-renderiza en resize y se blittea con un `drawImage` por cuadro. Cada 900 ms se reescriben el 1 % de las celdas con otro glifo del mismo `k` (respira). Cuando un stream termina y se funde (B), su línea se "sedimenta": se dibuja en `sed` con alfa 0.12 y su color tokenizado, y queda ahí hasta que otra línea la sobrescriba.

**B. Tecleo**: `N` streams simultáneos (escritorio 8, móvil 4; `data-density` 0.6–1 multiplica). Cada stream toma una fila libre (ninguna fila con dos streams), una columna inicial (0/2/4/8 celdas de indentación), una línea del corpus, y teclea a 1 carácter cada 2 cuadros (~15 car/s; ~12 en móvil) con alfa 0.55 × color por token; al terminar sostiene 1.8 s y se funde hasta 0.12 en 2.4 s (`ease-out`), momento en que pasa al sedimento y el stream libera la fila. Reparto de comentarios: **máximo una línea `//` tecleándose a la vez**, para que el español se lea y no se amontone.

**C. Foco**: 2 streams (1 en móvil) iguales a B pero alfa 0.85 y con **cursor de bloque** al frente (rect 0.55ch × 1em en `--accent`, parpadeo 530 ms `steps(2)`). Es el mismo cursor que los eyebrows en CSS: continuidad de material.

**Atenuación precalculada** (`Float32Array atten[fila*cols+col]`, se recalcula en resize y cuando cambia el bbox del h1):

- **Charco bajo el titular** (la viñeta central del sitio actual, anclada al h1): centro = centro del `getBoundingClientRect()` del h1 relativo al hero; radio = `max(anchoH1 * 0.75, 0.55 * min(w, h))`; valor 0.12 en el centro → 1.0 en el borde con `smoothstep`. En móvil el centro es el centro de la columna de texto y el radio `0.7 * w`.
- No hay lavado lateral ni escudo aparte: el charco hace los dos trabajos. Los fundidos vertical superior (96 px, bajo la nav) e inferior (140 px, hacia la siguiente sección) van en **CSS** sobre el canvas:
  `mask-image: linear-gradient(to bottom, transparent 0, #000 96px, #000 calc(100% - 140px), transparent 100%)` (con prefijo `-webkit-`).
- Cada glifo se pinta con `alpha = base × atten × intensidad` (`data-intensity` 0.5–1). Se cachean las cadenas `rgba()` por (color, alfa redondeado a 0.05).

**Cursor / tacto**

- `pointermove` sobre `.hero` (`passive: true`) fija el objetivo; la posición se persigue con lerp 0.10 por cuadro (llega con ~250 ms de retraso, se siente como lámpara, no como puntero).
- **Spot por composición** (offscreen `spot`): por cuadro se dibujan solo las celdas activas de B y C a alfa 1 en `spot`, se aplica `globalCompositeOperation = 'destination-in'` con `createRadialGradient(x, y, 40, x, y, 220)` (alfa 1 → 0; radio 150 en móvil), y se compone sobre el principal con `globalAlpha = 0.9 × intensidad`. Costo: 1 gradiente pequeño + 1 `drawImage`, sin recorrer celdas.
- Los streams cuya fila cruza el radio teclean al doble.
- `pointerleave`: el radio decae a 0 en 600 ms.
- **Sin puntero** (`(hover: none)` o cursor fuera del hero más de 2 s): la linterna deriva sola por una Lissajous lenta (periodo 14 s, amplitud 35 % del ancho × 22 % del alto, centrada en x 66 % / y 46 % del hero, boost 0.25). El hero respira en móvil sin dedo encima.
- En puntero grueso, `pointerdown` lanza un **pulso**: el radio del spot crece 0 → 260 px en 700 ms y se apaga; sin radio persistente. Sin estelas ni glitch.

### 4.3 Composición por cuadro (presupuesto)

```
clearRect(principal)
drawImage(sed)                       // 1
fillText de celdas activas de B y C  // ≤ ~400 en escritorio, ≤ ~160 en móvil
drawImage(spot)                      // 1
```

`requestAnimationFrame` con acumulador de 33 ms (30 fps; 41 ms = 24 fps en móvil). `DPR = min(devicePixelRatio, 1.5)`. `ctx.font` se fija una vez por cuadro. `IntersectionObserver` sobre el hero (`threshold: 0`) y `visibilitychange` pausan; al reanudar se **reinician los relojes** de los streams para que no haya saltos. `ResizeObserver` del hero (debounce 150 ms) reconstruye rejilla, sedimento y atenuación.

**Autoajuste con histéresis**: si el promedio móvil de 60 cuadros supera 40 ms durante 2 s, `N` baja a la mitad (mínimo 2 + 1 foco) y la linterna autónoma se apaga; solo vuelve a subir tras 10 s con promedio < 25 ms, y una sola vez por sesión. Probar con CPU ×4 en DevTools.

**Ruta de escape** (documentada, no construida): atlas de glifos (los ~90 glifos del corpus × 4 colores en un offscreen) y `drawImage` por celda en lugar de `fillText`, si un Android modesto no sostiene 24 fps.

### 4.4 Densidad por breakpoint

| | ≥ 1024 | 768–1023 | < 768 |
|---|---|---|---|
| fontSize / charHeight | 14 / 22 | 14 / 22 | 13 / 20 |
| streams B + C | 8 + 2 | 6 + 2 | 4 + 1 |
| alfa sedimento | 0.10 | 0.10 | 0.10 |
| alfas B / C | 0.55 / 0.85 | 0.55 / 0.85 | 0.45 / 0.70 |
| radio spot | 220 | 220 | 150 (deriva autónoma) |
| fps | 30 | 30 | 24 |

La lluvia **nunca se apaga** en móvil: baja de intensidad.

### 4.5 Cuadro estático

Con `prefers-reduced-motion: reduce` (también si cambia en caliente) o `data-intensity="0"`: un solo `draw()` tras `fonts.load`: sedimento + 8 líneas terminadas tokenizadas a alfa 0.35 + 2 líneas foco a alfa 0.85 con cursor fijo (sin parpadeo) + atenuación + spot fijo en x 66 % / y 46 % con radio 260. Sin rAF ni `pointermove`; se redibuja solo en resize (debounce 150 ms).

### 4.6 Fusión con el contenido

- `.hero { position: relative; isolation: isolate; background: var(--bg-0); overflow: hidden; }` (sin flash antes del primer cuadro).
- `canvas { position: absolute; inset: 0; z-index: 0; pointer-events: none; }` con `aria-hidden="true"` y el `mask-image` de §4.2. Contenido en `z-index: 1`.
- El hero **mide lo que contiene** (padding, sin `100vh`).
- `html.no-js .hero` lleva `background-image: repeating-linear-gradient(180deg, var(--line) 0 1px, transparent 1px 22px)` al 40 % (papel rayado) para que sin JS nunca quede plano.
- La sección siguiente (Productos) empieza con la regla de ticket `1px dashed var(--line-2)` al ancho del contenedor: la lluvia "se corta" ahí como un ticket arrancado. Fuera del hero no hay canvas; el material sigue en CSS (eyebrows con cursor, reglas punteadas, líderes de puntos, ficha mono).

---

## 5. Nav

Estructura del sitio actual conservada: logo + nombre a la izquierda, enlaces al centro-derecha, CTA destacado a la derecha, hamburguesa en móvil con cajón a pantalla completa.

**Reposo (sobre el hero)**: `header.nav[data-nav]` `position: fixed; top: 0; inset-inline: 0; z-index: 50`, alto **64 px** (56 en < 900), fondo transparente, sin borde (el fundido superior del canvas hace de scrim; sin gradiente CSS extra). `.nav__inner.container` en flex, `align-items: center`, `gap: var(--space-6)`.

- `.nav__brand`: `logo-96.png` a 28 × 28 (`width/height` explícitos, ≤ 15 KB) + «ProgramadorMX» en `--font-display` 700, `--step-0`, `letter-spacing: -0.01em`, color `--ink`, sin gradiente ni color en "MX".
- `.nav__links a`: `--font-body` 500, `--step--1`, color `--ink-2`, `gap: 28px`, `padding: 6px 2px`; hover → `--ink` en `--dur-1`; `.is-active` → `--ink` + barra de 2 px en `--accent` bajo el texto (`::after`, `bottom: -6px`, ancho del texto, `transform: scaleX(0→1)` desde la izquierda en 180 ms).
- `.nav__cta.btn.btn--primary.btn--wa.btn--sm`: **verde** (`--wa` / `--wa-ink`), 36 px, radio 8, glifo WhatsApp 18 px + «WhatsApp». `data-track="whatsapp_nav"`.
- Foco visible en todo: `outline: 2px solid var(--accent); outline-offset: 3px`.

**`.is-scrolled`** (a los 24 px): alto 56 px, `border-bottom: 1px solid var(--line)`, fondo sólido `var(--bg-0)` por defecto y, dentro de `@supports (backdrop-filter: blur(1px))`, `background: color-mix(in srgb, var(--bg-0) 90%, transparent); backdrop-filter: blur(10px)`. Transición `--dur-2 --ease-out`. Es el único blur del sitio.

**Móvil (< 900 px)**: se ocultan `.nav__links` y `.nav__cta`. `.nav__toggle` 44 × 44, **dos** barras de 20 × 2 px en `--ink` (`::before/::after`) que giran a X en 220 ms; `aria-controls="menu-movil"`, `aria-expanded`, `aria-label="Abrir menú"` / «Cerrar menú». `#menu-movil.nav__drawer`: `position: fixed; inset: 0`, fondo **sólido** `--bg-3`, `padding: 88px var(--gutter) var(--space-6)`, display flex column. Enlaces en `--font-display` 600, `--step-3`, color `--ink`, `padding: 16px 0`, cada uno con `border-bottom: 1px dashed var(--line-2)` (líneas de ticket), stagger de 40 ms al abrir; el activo lleva barra izquierda de 3 px en `--accent`. Al fondo (`margin-top: auto`): `.btn--wa.btn--lg` a todo el ancho «Cotizar por WhatsApp» (`data-track="whatsapp_menu"`) y una línea mono `--step--1` `--ink-3` con `{{ site.hours }}` y `{{ site.city }}`. Apertura: `opacity 0→1` + `translateY(-8px)→0` en 220 ms; cierre con Escape, al navegar y al tocar fuera; foco atrapado; `body { overflow: hidden }` mientras está abierto. `hidden` cuando está cerrado. Con reduced-motion todo instantáneo.

---

## 6. Hero

**Composición** (escritorio ≥ 1024, retícula de 12 columnas, gap 24): copy en columnas **1–8**, cajón de precios en **9–12** (verificado en la lámina a 1400 px: con 7 columnas el h1 a 64 px no cabe en 4 líneas); todo alineado a la izquierda, nada centrado. `padding-top: 128px` (nav + aire), `padding-bottom: 96px`. Canvas detrás (§4). Sin `100vh`, sin badge pulsante, sin typing en el h1, sin estadísticas, sin indicador de scroll.

**Orden del copy** (con `.reveal` escalonado 60 ms):

1. `.eyebrow` mono 500 `--step--1` `--accent` con cursor de bloque que parpadea 3 veces al cargar y queda fijo:
   `apps y páginas web para negocios pequeños`
2. `<h1>` `--font-display`, `font-size: min(var(--step-5), 4rem)`, `--ink`, `max-width: 20ch`, `text-wrap: balance` (≥ 600 px), dos oraciones en dos `<span>` de bloque:
   **«Tus clientes agendan y piden solos.»** (peso 800)
   **«Tú abres la app y ves tu día.»** (peso 500, misma familia y tamaño: jerarquía por peso, no por color ni gradiente)
3. `p.lede` `--font-body` 400 `--step-1` `--ink-2`, `max-width: 52ch`:
   «Agenda de citas, pedidos por WhatsApp, menú digital QR o tu página web. Sin comisiones y con precio cerrado antes de empezar. Para barberías, taquerías, consultorios y tiendas de Tampico, Madero, Altamira y todo México.»
4. `.cluster` (gap 12): `.btn--wa.btn--lg` «Cotizar por WhatsApp» (glifo WA 20 px, `href="{{ site.whatsapp_url }}"`, `data-track="whatsapp_hero"`) + `.btn--ghost.btn--lg` «Ver precios» → `#precios`.
5. Línea meta mono 400 `--step--1` `--ink-3`, separada por ` · `:
   `Te respondo yo, no un bot` · `{{ site.hours }}` · `{{ site.city }} y remoto a todo México`
   Cuando el contrato incorpore `site.price_min_fmt` (§14) se antepone `Desde {{ site.price_min_fmt }} MXN, pago único`. Ninguna cifra a mano.

**Cajón de precios** (`aside.hero__precios`, `aria-label="Precios desde, por producto"`): resuelve "desde cuánto" en el primer pantallazo.

- Contenedor: `background: color-mix(in srgb, var(--bg-1) 86%, transparent)` (respaldo `var(--bg-1)`; con 60 % los glifos tecleados se leían a través de los nombres), `border: 1px solid var(--line)`, `border-radius: var(--radius-2)`, `padding: 20px 22px`. La lluvia vive a la derecha del charco y alrededor del cajón, no detrás del texto.
- Cabecera mono 500 `--step--1` `--ink-3`: `precios desde` a la izquierda, `MXN` a la derecha; debajo `border-bottom: 1px dashed var(--line-2)`.
- Seis filas con `{{#each products}}`: cada fila es un `<a>` (`href` = `landing_path` si existe, si no `/#productos`), `display: flex; align-items: baseline; gap: 8px; min-height: 40px; padding: 6px 4px`. Nombre en `--font-body` 500 `--step--1` `--ink` (`nombre` tal cual, `max-width: 70%`, puede partir en dos líneas; nunca `ellipsis`: el dueño tiene que leer qué producto es), líder de puntos (`flex: 1; border-bottom: 1px dotted var(--line-2); transform: translateY(-4px)`), `{{ precio_fmt }}` en mono 500 `--step-0` `--ink` tabular. Hover: fondo `--bg-2`. Foco: outline ámbar.
- Pie mono `--step--1` `--ink-3` tras otra regla punteada: `{{ site.monthly_plan.label }} · ${{ site.monthly_plan.price }}/mes, opcional` y `precio cerrado antes de empezar`.
- **Móvil**: el cajón baja **justo después de los CTAs** (antes de la línea meta), a todo el ancho, en modo compacto: filas de 36 px, nombre `--step--1`, sin pie de mensualidad (queda en la tabla). Verificar con captura a 360×740 que el primer precio sea visible sin scroll; si no lo es, reducir el `padding-top` del hero a 88 px antes que tocar el h1.

Regla ámbar/verde en el hero: los eyebrows y el cursor (ámbar) arriba; los botones (verde) abajo; nunca ámbar a menos de 16 px de un botón WhatsApp.

---

## 7. Ritmo de secciones y retícula

**Contenedor**: `.container { max-width: var(--container); margin-inline: auto; padding-inline: var(--gutter); }`. Retícula base `.grid` = `display: grid; grid-template-columns: repeat(12, 1fr); gap: 24px` (en < 900 una columna). `.grid--3` = `repeat(auto-fit, minmax(min(100%, 300px), 1fr))`, gap 20, solo para productos. `.grid--2` = 2 columnas iguales desde 768. `.section { padding-block: var(--section-gap) }`; `.section--tight` la mitad. Anclas con `scroll-margin-top: 80px`. `.section__head` siempre a la izquierda: eyebrow con cursor + h2 700 `--step-3` + lede `--ink-2` 56ch; en ≥ 900 ocupa columnas 1–7.

Una sola rejilla de tarjetas en toda la home. Las secciones se distinguen por tratamiento, no por cajas:

| # | Sección | Fondo | Tratamiento |
|---|---|---|---|
| 1 | Hero | bg-0 + canvas | 7/5 columnas, cajón de precios |
| 2 | Productos `#productos` | bg-0 | Empieza con **la** regla de ticket (1px dashed line-2, ancho del contenedor). Head + `.grid--3` de seis `.card.card--lift` (3 / 2 / 1 columnas). |
| 3 | Cómo funciona `#como-funciona` | bg-1 a sangre, hairlines `--line` arriba y abajo | Cuatro pasos en fila (columna en móvil) unidos por una línea `1px dashed var(--line-2)`; etiqueta mono `paso 1…4` en ámbar (aquí sí hay secuencia), título display 600 `--step-1`, texto `--ink-2`. **El paso 1 lleva una burbuja de WhatsApp** (fondo `--wa` al 14 % sobre bg-1, borde 1px `--wa` al 35 %, radio 8 con esquina inferior izquierda 2 px, texto `--ink` `--step--1`) con el mensaje real `{{ site.whatsapp_message }}`. Pasos: «Me escribes por WhatsApp y me cuentas tu negocio» → «Te doy precio cerrado y fecha de entrega» → «La construyo y la pruebas en tu celular» → «La publico y te enseño a usarla». |
| 4 | Precios `#precios` | bg-0 | `<table class="pricing__table">` real, máx. 880 px en columnas 1–8; columnas: Producto · Para quién · Desde · Entrega · (acción). Columnas 9–12: notas en `--ink-2` (qué incluye, qué no, cómo se paga; texto del dueño, sin cifras nuevas). Pie: fila de mensualidad con `.chip` «opcional» y nota mono «precio cerrado antes de empezar, sin sorpresas». |
| 5 | Preguntas `#preguntas` | bg-0 | Head sticky (`top: 96px`) en columnas 1–4; lista `<details>` en 5–12 separada por reglas punteadas. Sin cajas. |
| 6 | Sobre mí | bg-1 a sangre | Texto honesto en 1–7 (`--step-1`); en 8–12 una ficha mono con líderes de puntos: `experiencia … 4 años` · `herramientas … Flutter y .NET` · `base … {{ site.city }}` · `cobertura … México (remoto)` · `trato … directo con quien hace la app`. Sin foto; nombre solo si `owner_name`. |
| 7 | Contacto `#contacto` | bg-0 | 1–6: `.btn--wa.btn--lg`, debajo el mensaje prellenado real tecleándose en un bloque mono (radio 14, fondo bg-1) con cursor; email y horario con iconos 20 px. 7–12: formulario de respaldo bajo «¿Prefieres correo? También va.» |
| — | Footer | bg-1 | Regla punteada superior; cuatro columnas (marca + frase, productos, contacto, legal); redes con SVG relleno 20 px + texto visible; última línea mono `--step--1` `--ink-3` `© {{ build.year }} ProgramadorMX · {{ site.city }}`. |

Tope: **una** regla punteada por sección (más las internas de la tabla y del FAQ). Nada de bordes rasgados, zigzag ni texturas de papel.

**Tabla de precios en móvil (< 720)**: se conserva la semántica con atributos explícitos `role="table"` en `<table>`, `role="rowgroup"` en `<thead>/<tbody>`, `role="row"` en `<tr>`, `role="columnheader"` en `<th>`, `role="cell"` en `<td>`; `thead` pasa a `.visually-hidden`; `tr` → `display: grid; grid-template-columns: 1fr auto; gap: 4px 12px; padding: 14px 0; border-bottom: 1px dashed var(--line-2)`; `td::before { content: attr(data-label) }` en mono `--step--1` `--ink-3`; la celda de acción ocupa las dos columnas. Probar con lector de pantalla (NVDA) que anuncie fila y columna.

---

## 8. Componentes

Medidas fijas en px para alturas y paddings; tipografía por tokens.

### Botones `.btn`

- Base: `display: inline-flex; align-items: center; justify-content: center; gap: 10px; height: 44px; padding: 0 18px; border-radius: var(--radius-2); border: 1px solid transparent; font: 600 var(--step-0)/1 var(--font-body); text-decoration: none; cursor: pointer; transition: background-color, border-color, color, transform var(--dur-1) var(--ease-out)`. Sin sombra, sin glow.
- `.btn--sm`: 36 px, `padding: 0 14px`, `--step--1`, icono 18. `.btn--lg`: 52 px, `padding: 0 24px`, icono 20.
- Estados comunes: hover `transform: translateY(-1px)`; active `translateY(0) scale(.99)`; `:focus-visible { outline: 2px solid var(--accent); outline-offset: 3px }`; `[aria-disabled="true"]` opacidad .55 y `pointer-events: none`.
- **`.btn--primary`** ("papel"): fondo `--ink`, texto `--bg-0`; hover `filter: brightness(1.04)`. Uso: envío del formulario. Si lleva glifo WhatsApp (nunca debería, pero por si acaso), el glifo va en `--bg-0`, no en `--wa` (1.72:1).
- **`.btn--ghost`**: fondo transparente, `border-color: var(--line-2)` (3.55:1), texto `--ink`; hover fondo `--bg-1` y borde `--ink-3`; sobre bandas bg-1 el hover pasa a `--bg-2`.
- **`.btn--wa`**: fondo `--wa`, texto `--wa-ink`, glifo WhatsApp relleno 20 px obligatorio a la izquierda; hover `filter: brightness(1.06)`; siempre `data-track="whatsapp_<contexto>"` y `rel="noopener"` con `target="_blank"`. Único botón saturado. Gana sobre `.btn--primary` cuando ambas clases coexisten (nav).
- **`.wa-float`**: 56 px circular (excepción de radio), `--wa` con glifo 28 px `--wa-ink`, `--shadow-1`, `bottom: 20px; right: 20px; z-index: 40`; aparece con `translateY(12px)→0` + opacidad en 200 ms cuando el hero sale de pantalla; `hidden` mientras el hero es visible. 52 px en móvil. Sin globo, sin latido.

### Tarjeta de producto `.card`

- `background: var(--bg-1); border: 1px solid var(--line); border-radius: var(--radius-2); padding: 24px; display: grid; grid-template-rows: auto auto auto 1fr auto; gap: 14px`.
- Fila superior: `.card__icon` 40 × 40, fondo `--bg-2`, radio 6, SVG 24 px en `--accent-2`; a la derecha `.tag` con `para_quien` (máx. 3, unidos por ` · `).
- `.card__title` display 600 `--step-1` `--ink`; `corto` en `--ink-2` `--step-0`; lista `incluye` con marcador `+` mono en `--accent` (`::before`) y texto `--ink-2` `--step--1`.
- `.card__meta`: `.price` (`.price__from` mono 500 `--step--1` `--accent` «desde», `.price__amount` display 700 `--step-2` `--ink` tabular, `.price__currency` mono `--step--1` `--ink-3` «MXN») + `.chip` con `entrega`.
- CTA final `.btn--wa.btn--sm` a todo el ancho «Quiero esta app» con `whatsapp_url` del producto y `data-track="whatsapp_producto_<slug>"`.
- `.card--lift:hover`: `translateY(-2px)`, `border-color: var(--line-2)`, `--shadow-1`, 160 ms. `destacado: true`: `border-top: 2px solid var(--accent)` y `.chip.chip--accent` «recomendada para empezar» (opinión del dueño, no estadística).

### Precio `.price`

`display: inline-flex; align-items: baseline; gap: 6px`. En tabla y cajón el importe va en mono 500 `--step-0` `--ink` tabular (se lee como recibo); en tarjeta en display 700 `--step-2`. «desde» siempre en ámbar en tarjeta; en tabla el ámbar va solo en la cabecera de la columna «Desde».

### Tabla de precios `.pricing__table`

Filas `min-height: 56px`, `border-bottom: 1px dashed var(--line-2)`; cabeceras mono 500 `--step--1` `--ink-3` alineadas como su columna; celda producto `--font-body` 500 `--ink` (enlace a landing si existe); «Para quién» `--ink-2` `--step--1`; «Desde» mono 500 `--step-0` `--ink` tabular a la derecha; «Entrega» mono `--step--1` `--ink-3`; acción `.btn--ghost.btn--sm` «cotizar» (`data-track="whatsapp_precios_<slug>"`, va a WhatsApp del producto). Hover de fila: fondo `--bg-2`. Móvil: ver §7.

### Chips y tags

- `.chip`: mono 500 `--step--1`, `height: 26px; padding: 0 8px; border-radius: var(--radius-1); background: var(--bg-2); border: 1px solid var(--line); color: var(--ink-2)`. `.chip--accent`: fondo `--accent-soft`, texto `--accent`, sin borde. No es píldora.
- `.tag`: mono 400 `--step--1` `--ink-3`, sin fondo ni borde, separadores ` · `.

### FAQ `.faq details`

`border-bottom: 1px dashed var(--line-2)` (el primero también arriba). `summary`: display 600 `--step-1` `--ink`, `padding: 20px 40px 20px 0`, `list-style: none` (`::-webkit-details-marker { display: none }`), `cursor: pointer`, `position: relative`; `::after` = `+` mono `--step-1` `--ink-3` a la derecha que gira 45° y pasa a `--accent` en 160 ms al abrir; el summary abierto pasa a `--accent`. Respuesta en un wrapper `.faq__body { display: grid; grid-template-rows: 0fr; transition: grid-template-rows var(--dur-2) var(--ease-out) } details[open] .faq__body { grid-template-rows: 1fr }` con `overflow: hidden`, texto `--ink-2` `--step-0` `max-width: 62ch`, `padding-bottom: 20px`. `summary:focus-visible` outline ámbar. Sin chevrones.

### Formulario `.contact form`

- Labels `--font-body` 500 `--step--1` `--ink-2` encima, gap 6.
- Inputs/textarea/select: `height: 48px` (textarea `min-height: 120px`), `padding: 0 14px`, fondo `--bg-1`, `border: 1px solid var(--line-2)` (3.35:1), radio 6, texto `--ink` `--step-0`, placeholder `--ink-3`.
- `:focus-visible`: `border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-soft); outline: none`.
- Error: borde y texto de ayuda `--warn`, mensaje `aria-live="polite"` con icono 16; éxito `--ok`.
- Checkbox de privacidad 20 px con `accent-color: var(--accent)`.
- Envío: `.btn--primary` (papel). El encabezado del bloque: «¿Prefieres correo? También va.»

---

## 9. Iconografía

Estilo único: SVG inline 24 × 24, `viewBox="0 0 24 24"`, `stroke="currentColor"`, `fill="none"`, `stroke-width="1.75"`, `stroke-linecap="round"`, `stroke-linejoin="round"`, `aria-hidden="true"`, geometría en retícula de 2 px, esquinas de 1.5–2 px, sin detalles menores de 2 px. Excepción declarada: glifos de marca (`whatsapp`, `facebook`, `instagram`, `tiktok`, `youtube`) con `fill="currentColor"` y sin stroke, a 20 px (28 en el flotante).

Seis iconos de producto (`src/assets/icons/<icon>.svg`; nombre = campo `icon` en `products.json`):

| icon | Producto | Dibujo |
|---|---|---|
| `calendar` | agenda-citas-whatsapp | calendario con dos argollas y palomita en la celda inferior derecha |
| `cart` | pedidos-whatsapp | bolsa de mandado con asa y burbuja de mensaje pequeña arriba a la derecha |
| `qr` | menu-digital-qr | tres cuadros localizadores de QR y dos puntos en el cuadrante libre |
| `stamp` | tarjeta-lealtad | tarjeta horizontal con cuatro círculos de sello, el último con palomita |
| `boxes` | inventario-ventas | caja isométrica simple con barra de conteo encima |
| `globe` | pagina-web | ventana de navegador con barra superior y burbuja de chat dentro |

Utilitarios con el mismo trazo: `arrow-right`, `mail`, `map-pin`, `clock`, `check`, `plus`, `menu` (dos barras), `x`. Usos: tarjeta 24 px en `--accent-2` dentro de caja 40 × 40 `--bg-2`; landing 32 px junto al h1; tabla de precios sin iconos; cajón del hero y footer sin iconos (ahí manda la mono). Nunca emojis, ni como iconos ni como marcadores.

---

## 10. Motion

Tokens: `--dur-1` 140 ms (color, borde, opacidad) · `--dur-2` 260 ms (nav, cajón, FAQ, reveal corto) · `--dur-3` 480 ms (reveal, fundidos). `--ease-out cubic-bezier(.2,.7,.2,1)` · `--ease-in-out cubic-bezier(.65,0,.35,1)`.

**Sí se anima**: (1) la lluvia, solo en el hero, 30 fps / 24 móvil, con pausa fuera de pantalla y pestaña oculta; (2) cursor de los eyebrows: 3 parpadeos (`pmx-blink 1.1s steps(2, jump-none) 3`) cuando su sección entra en la banda central y queda fijo; (3) `.reveal`: `opacity 0→1` + `translateY(12px)→0` en `--dur-3`, stagger 60 ms hasta 4 hijos, una vez; en reposo el elemento se ve (solo `html.js` sin reduced-motion arranca desplazado); (4) nav `.is-scrolled` 260 ms, subrayado activo 180 ms, cajón 220 ms, barras del toggle 220 ms; (5) botones 140 ms, tarjetas 160 ms, `+` del FAQ 160 ms, filas de tabla 140 ms; (6) mensaje prellenado en contacto tecleándose a 28 ms/carácter con cursor, una vez al entrar en pantalla; (7) flotante WA 200 ms.

**No se anima**: parallax, contadores, texto degradado, marquesinas, glow o pulsos en botones, blobs, scroll secuestrado, animación de entrada de página (`body.is-preload` del sitio actual desaparece), iconos en hover, color de fondo de secciones, el h1 (sin typing), la tabla, la ficha, el footer.

**Reduced-motion** (CSS y JS): `@media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation-duration: 0.01ms !important; animation-iteration-count: 1 !important; transition-duration: 0.01ms !important; scroll-behavior: auto !important } }`; `.reveal` visible de inmediato (`PMX.reveal` marca todo); cursores fijos; mensaje de contacto ya completo; lluvia en cuadro estático (§4.5), con escucha del cambio en caliente del media query.

---

## 11. Lista Sí / No

**Sí**
- Todo enlace a WhatsApp es verde (`--wa`) con glifo y `data-track`; el resto de botones nunca es verde.
- Ámbar solo como tinta tipográfica: eyebrows, cursores, «desde», subrayado activo, `+` abierto, foco. Nunca relleno de botón, nunca a menos de 16 px de un botón WhatsApp.
- Eyebrows en mono **minúscula** con cursor de bloque.
- Cifras en mono tabular; texto corrido en Plex Sans; display solo de `--step-1` hacia arriba.
- Todo alineado a la izquierda (incluidos section heads, hero, cajón móvil). Solo el 404 se centra.
- Una rejilla de tarjetas (productos). Tabla real para precios. `<details>` para FAQ. Ficha mono para "sobre mí".
- Una regla punteada por sección; líderes de puntos en cajón, ficha y tabla.
- Radios 4 / 8; 14 solo en el bloque de mensaje tecleado. Disco solo el flotante.
- Bordes de controles con `--line-2` (≥ 3:1). Hairlines decorativas con `--line`.
- Datos siempre desde `site` / `products`: precios, WhatsApp, email, horario, ciudad.
- Copy en segunda persona, frases cortas, acentos y signos de apertura.

**No**
- Gradientes de texto o de fondo (salvo el `mask-image` del canvas y el lavado del paso activo).
- Glassmorphism en contenido (blur solo en `.nav.is-scrolled`).
- Píldoras, `border-radius` ≥ 16 en bloques, cajas flotando con sombra en reposo.
- Emojis, iconos de cohete o rayo, números 01/02/03 donde no hay secuencia.
- Mayúsculas espaciadas en eyebrows; hairlines por todos lados; texturas de papel, zigzag, bordes rasgados.
- Estadísticas, badges «disponible», contadores, testimonios, nombres de clientes ficticios, capturas de apps inventadas.
- Hex fijos en JS; `shadowBlur`; gradientes por cuadro en el canvas.
- Texto blanco sobre verde WhatsApp (2.0:1).
- `100vh` en el hero; animación de entrada de página; hover que mueve iconos.
- Cargar fuentes o scripts de terceros fuera de la URL de Google Fonts de §3.

---

## 12. Ratios de contraste verificados

Salida real de `py -3 tools/contrast_check.py` (fórmula WCAG 2.1 de luminancia relativa sRGB) sobre los hex finales de `00-tokens.css`, 17 sep 2026:

```
# Ratios de contraste WCAG 2.1 (luminancia relativa sRGB)
par                         hex                   ratio  nivel      nota
------------------------------------------------------------------------------------------------
ink/bg-0                    #F4EEE6/#15120F      16.19:1  AAA        texto principal sobre body/hero
ink/bg-1                    #F4EEE6/#1C1814      15.31:1  AAA        texto principal sobre bandas y tarjetas
ink-2/bg-1                  #BDB3A7/#1C1814       8.55:1  AAA        texto secundario sobre bandas y tarjetas
ink-3/bg-0                  #9C938A/#15120F       6.18:1  AA         meta mono atenuada sobre body
accent-ink/accent           #1C1206/#F0A63C       8.98:1  AAA        texto sobre chip/badge ámbar
wa-ink/wa                   #072D16/#25D366       7.58:1  AAA        texto del botón WhatsApp
accent/bg-0                 #F0A63C/#15120F       9.09:1  AAA        eyebrows y 'desde' en ámbar como texto
ink/bg-2                    #F4EEE6/#241F1A      14.17:1  AAA        texto en superficies internas
ink/bg-3                    #F4EEE6/#2E2823      12.62:1  AAA        texto en hover/elevado
ink-2/bg-0                  #BDB3A7/#15120F       9.04:1  AAA        ledes sobre body
ink-2/bg-2                  #BDB3A7/#241F1A       7.91:1  AAA        texto secundario en chips
ink-2/bg-3                  #BDB3A7/#2E2823       7.04:1  AAA        texto secundario en hover
ink-3/bg-1                  #9C938A/#1C1814       5.84:1  AA         meta mono en tarjetas
ink-3/bg-2                  #9C938A/#241F1A       5.41:1  AA         meta mono en chips
ink-3/bg-3                  #9C938A/#2E2823       4.82:1  AA         meta mono en hover (regla: solo si pasa)
ink-3/accent-soft           #9C938A/#33240F       4.97:1  AA         meta mono sobre lavado ámbar (regla: solo si pasa)
ink-2/accent-soft           #BDB3A7/#33240F       7.26:1  AAA        texto secundario sobre lavado ámbar
ink/accent-soft             #F4EEE6/#33240F      13.01:1  AAA        texto principal sobre lavado ámbar
accent/bg-1                 #F0A63C/#1C1814       8.59:1  AAA        ámbar como texto en bandas
accent/bg-2                 #F0A63C/#241F1A       7.95:1  AAA        ámbar como texto en chips
accent/bg-3                 #F0A63C/#2E2823       7.08:1  AAA        ámbar como texto en hover
accent/accent-soft          #F0A63C/#33240F       7.30:1  AAA        chip destacado: texto ámbar sobre lavado
accent-2/bg-0               #7FB8C9/#15120F       8.53:1  AAA        azul-verdoso: iconos y .mono en párrafos
accent-2/bg-1               #7FB8C9/#1C1814       8.07:1  AAA        azul-verdoso en tarjetas
accent-2/bg-2               #7FB8C9/#241F1A       7.47:1  AA         icono de producto en caja bg-2
ok/bg-0                     #7CC48B/#15120F       9.00:1  AAA        mensaje de éxito
ok/bg-1                     #7CC48B/#1C1814       8.51:1  AAA        mensaje de éxito en tarjeta
warn/bg-0                   #E8785A/#15120F       6.46:1  AA         mensaje de error
warn/bg-1                   #E8785A/#1C1814       6.10:1  AA         mensaje de error en tarjeta
wa/bg-0                     #25D366/#15120F       9.41:1  AA         botón WhatsApp como componente sobre body
bg-0/ink                    #15120F/#F4EEE6      16.19:1  AAA        texto oscuro del botón papel
wa/ink                      #25D366/#F4EEE6       1.72:1  deco       glifo WA verde sobre papel (NO usar: por eso el glifo va en bg-0)
line/bg-0                   #2A241F/#15120F       1.22:1  deco       hairline decorativa (tarjetas, divisores)
line/bg-1                   #2A241F/#1C1814       1.15:1  deco       hairline decorativa en bandas
line-2/bg-0                 #726B61/#15120F       3.55:1  AA         borde de inputs y botón ghost sobre body (1.4.11)
line-2/bg-1                 #726B61/#1C1814       3.35:1  AA         borde de inputs y botón ghost sobre banda (1.4.11)
line-2/bg-2                 #726B61/#241F1A       3.10:1  AA         borde de control sobre bg-2
------------------------------------------------------------------------------------------------
Todos los pares de texto cumplen AA (4.5:1); todos los bordes de control cumplen 3:1.
```

**Ajustes hechos por contraste respecto a la propuesta original**: `--ink-3` de `#948B7F` a `#9C938A` (para pasar AA sobre `--accent-soft` y `--bg-3`); `--accent-soft` de `#3A2B17` a `#33240F` (misma razón, y el chip destacado sube a 7.30:1); `--line-2` de `#3B342D` (1.52:1, inservible como borde de control) a `#726B61` (≥ 3.10:1 sobre bg-0/1/2), eliminando el `color-mix` que un módulo podía olvidar. Regla que sigue en pie: el texto blanco/papel sobre `--wa` está prohibido (2.0:1); el glifo verde sobre el botón papel también (1.72:1).

**Verificado en la lámina** (`DESIGN-tile.html`, Chrome, 17 sep 2026): a 1400 px el h1 cabe en 4 líneas con el copy en 8 columnas y el cajón en 4; a 390 px no hay scroll horizontal, los dos CTAs se apilan y el cajón compacto con los seis precios queda justo debajo de «Ver precios», con la línea meta después.

**Pendiente de verificación visual** (no la da un ratio): legibilidad del h1 sobre la lluvia con el charco a 0.12 y sedimento a 0.10, con captura real en 360×740, 390×844 y 1440×900. El ratio del hero supone `--bg-0` sólido; con el charco, la aportación de los glifos bajo el titular queda por debajo de alfa 0.02.

---

## 13. `theme_color`

`"theme_color": "#15120F"` en `site.config.json` (igual a `--bg-0`). El módulo SEO lo emite en `<meta name="theme-color">`.

---

## 14. Peticiones al contrato (una línea cada una; se agregan a CONTRACT.md antes de usarlas)

1. `site.price_min_fmt`: `build.py` calcula el mínimo de `precio_desde` de `products.json` y lo formatea como `precio_fmt` (`$3,900`). Lo usa la línea meta del hero. Hasta que exista, la línea meta no menciona precio.
2. `nav.html`: el CTA lleva `class="nav__cta btn btn--primary btn--wa btn--sm"` (se añade el modificador `.btn--wa`; las clases del contrato se conservan).
3. `.chip--accent` como variante de `.chip` en `20-components.css` (chip destacado).
