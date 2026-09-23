# Recursos visuales del sitio

Todas las fotos del sitio se generaron en ChatGPT siguiendo el flujo de
`Desktop\CONTEXTO-IMAGENES-IA.md`, y el texto de las tarjetas para compartir **no** lo escribió la
IA: se monta en HTML con la tipografía real del sitio y se captura con Chrome, para que no haya
letras mal escritas.

## Qué hay y dónde

| Archivo en `src/assets/` | Qué es | Peso |
|---|---|---|
| `img/productos/agenda-citas-whatsapp.webp` | Barbería de noche, celular con la agenda | 41 KB |
| `img/productos/pedidos-whatsapp.webp` | Tienda de abarrotes, catálogo en el celular | 45 KB |
| `img/productos/menu-digital-qr.webp` | Mesa de restaurante con QR y menú | 43 KB |
| `img/productos/tarjeta-lealtad.webp` | Barra de cafetería, sellos de lealtad | 36 KB |
| `img/productos/inventario-ventas.webp` | Taller, tableta con el inventario | 38 KB |
| `img/productos/pagina-web.webp` | Escritorio con laptop y una web sencilla | 32 KB |
| `tools/dev/og/sin-uso/home-hero.webp` | (sin uso) Portada de la home que se probó y se quitó | 62 KB |
| `tools/dev/og/sin-uso/home-hero-taqueria.webp` | (sin uso) Alternativa de portada (taquería) | 59 KB |
| `img/landing/agenda-citas-hero.webp` | Portada ancha de la landing (salón) | 44 KB |
| `og/og-image.jpg` | Tarjeta para compartir la home | 89 KB |
| `og/og-agenda.jpg` | Tarjeta para compartir la landing | 95 KB |

Las fotos originales sin procesar están aquí como `foto-ia-*.png` (1536×1024 y 1672×941).

## Serie v2 de las tarjetas de producto (22 sep 2026)

Las seis fotos de `img/productos/` se rehicieron porque la v1 seguía viéndose genérica: las seis
repetían la misma fórmula (aparato solo sobre mesa de madera barnizada, penumbra naranja de película,
nadie usándolo, pantallas con barras grises). Receta v2, en ChatGPT web (1536×1024, 3:2):

- **De día**, con la luz real del lugar (tubo fluorescente + calle), exposición normal.
- **Una persona usando el aparato**: manos y antebrazo, cara fuera de cuadro.
- **Pantalla de fondo claro con texto real deletreado** (salió perfecto en las seis, a la primera).
- **Un ángulo distinto en cada una**: sobre el hombro, lateral, desde la mesa, primera persona.
- **Sin graduar el color** al exportar: `procesar_fotos.py --natural`. La graduación a "penumbra
  cálida" de la v1 era parte del problema.

Prompts en `Documents\AI Claude\_fotos-pmx-v2\` (`prompts.md` + `escenas.json`), originales en
`v2-originales/`, la serie anterior en `v1-productos/`. Las destacadas llevan `object-position`
propio en `15-media.css` para que la banda ancha no corte la pantalla.

Chats v2: barbería 6ab312b2-dc88-83e8-b492-8f807ff18d32 · abarrotes 6ab312db-e788-83e8-bffc-16df399b285a ·
fonda 6ab312eb-1c34-83e8-89ff-1bb9e0c08855 · cafetería 6ab31308-3cb4-83e8-8b9f-08e2070362e9 ·
ferretería 6ab3131a-ad1c-83e8-852a-8156499c5bc6 · salón 6ab3132b-97b0-83e8-9125-a1fb1f483769
(todos en `https://chatgpt.com/c/<id>`).

La portada de la landing (`img/landing/agenda-citas-hero*.webp`) se rehízo el 23 sep 2026 con la
misma receta, en 16:9 (ChatGPT la entrega a 1672×941, por eso el `srcset` dice 1672w) y con la
mitad izquierda lisa para el titular. Chat: 6ab4091c-5efc-83e8-a6a0-d1c70012475d; la v1 está en
`v1-landing/`.

Tarjetas para compartir (23 sep 2026): `tarjeta.html` usa `v2-originales/p3.png` (fonda) y
`tarjeta-agenda.html` usa `v2-originales/landing-agenda.png`, ambas con la paleta grafito + índigo.
Se capturan como `render-*.png` y se exportan a JPEG en `src/assets/og/`. Versiones anteriores:
`v1-tarjeta*.html` y `v1-og/`.

## Serie v3: pantallas diseñadas a mano (23 sep 2026)

Las fotos v2 estaban bien, pero la app del celular salía genérica. Ahora cada pantalla se diseña
primero en HTML/CSS (`v3-pantallas/pantallas.html`, `?s=1…6` muestra una sola), se captura con
Chrome headless a 3x y se manda a ChatGPT con la foto: "Imagen 1 = foto, consérvala idéntica;
Imagen 2 = captura, es lo único que va en la pantalla". Salió bien a la primera en las 7.

- Paleta de las apps: fondo #f5f5f4, texto #0c0d10, acento índigo #5a63e8 (el mismo de la web),
  Geist + Instrument Serif en el menú y la web del salón. Negocios inventados con monograma.
- Texto grande y pocos elementos: ChatGPT reproduce bien lo legible y mal lo diminuto.
- ChatGPT a veces devuelve 4:3 aunque la foto sea 3:2 o 16:9: `procesar_fotos.py` recorta al centro;
  la portada se recortó a mano (y0 = 40) para no cortar el celular.
- Siempre mostrar las pantallas al usuario antes de mandarlas a ChatGPT.

Originales en `v3-pantallas/` (p1–p6, landing-agenda*.png, pantalla-*.png). Chats en
`Documents\AI Claude\_fotos-pmx-v2\pantallas\_conversaciones.txt`.

## Las tres reglas que hacen que NO parezca imagen de IA

Aprendidas a golpes el 17 sep 2026, después de una primera tanda que salió "vacía y genérica":

1. **Nada de "mucho espacio negativo, sin manos, sin gente".** Eso produce exactamente la foto de
   banco: un celular solo sobre un mostrador limpio. Hay que pedir un negocio **vivo y desordenado**:
   báscula vieja, cuaderno de fiados con números a mano, monedas, calculadora, cables, polvo, y una
   persona **muy desenfocada en movimiento** al borde del cuadro (sin cara).
2. **La pantalla del celular tiene que leerse.** Barras grises abstractas delatan el montaje al
   instante. Hay que escribir la interfaz real en el prompt, deletreada letra por letra
   ("Pedidos de hoy", "Mari · Nuevo · $240", botón "Ver pedido") y auditarla con zoom después.
3. **Prohibir marcas con una descripción positiva.** Decir "sin marcas registradas" no basta: el
   modelo mete Doritos y Lay's igual. Hay que describir el empaque que sí quieres:
   "envases de colores lisos y mates, sin logotipo y sin ninguna letra impresa".

Además: lenguaje de **fotografía documental** (35 mm, f/2, ISO 1600, grano, viñeta, luz mixta sucia),
tres planos de profundidad y encuadre descentrado.

## Qué modelo usar (OpenArt, cuenta Pro)

| Modelo | Resolución | Texto en pantalla | Marcas | Costo (2 imgs) |
|---|---|---|---|---|
| **GPT Image 2.5** · 16:9 · 4k · calidad Alta | 3584×2016 | correcto con deletreo | respeta el "sin marcas" | 630 créditos |
| Nano Banana Pro · 16:9 · 4K | 5504×3072 | impecable | **metió Doritos y Lay's** | 160 créditos |

Nano Banana Pro da más resolución y mejor texto por mucho menos, pero hay que insistirle con los
empaques lisos. GPT Image 2.5 fue el que quedó en la home.

En la web de ChatGPT solo salen 1254×1254 (o 1672×941 en 16:9): para el sitio conviene OpenArt.

## Cómo se procesan

`procesar_fotos.py` hace tres cosas para que las seis se vean como una serie: iguala el brillo
(todas terminan cerca de una penumbra cálida), baja un punto la saturación y calienta las sombras.
Luego reduce a 1000 px de ancho y exporta WebP.

```bash
py -3 tools/dev/og/procesar_fotos.py <carpeta con p1..p6.png>
```

## Regenerar una tarjeta para compartir

1. Edita `tarjeta.html` (home) o `tarjeta-agenda.html` (landing): titular, subtítulo, recuadros.
2. Captura con Chrome (la ruta lleva espacios: van como `%20`):

```bash
"C:\Program Files\Google\Chrome\Application\chrome.exe" --headless=new --disable-gpu --hide-scrollbars --user-data-dir=%TEMP%\pmx-chrome-og --force-device-scale-factor=1 --window-size=1200,630 --virtual-time-budget=10000 --screenshot=og-agenda.png "file:///C:/Users/Programador%20Mx/Documents/programadormx.online/tools/dev/og/tarjeta-agenda.html"
```

3. Optimiza a JPEG y déjala en `src/assets/og/`.

## Cómo se integran en el sitio

- **Tarjetas de producto**: `src/sections/products.html` mete `.card-media` si el producto tiene
  `imagen_alt` en `data/products.json`. Los estilos están en `src/styles/15-media.css`.
  Si borras ese archivo y el bloque `{{#if imagen_alt}}`, las tarjetas vuelven a como estaban.
- **Portada de la home**: **no lleva foto**. Se probó una (`<img class="hero-foto">` al inicio de
  `src/sections/hero.html` más un bloque en `15-media.css`) y se quitó el 17 sep 2026: la
  demostración interactiva se ve mejor. Las fotos `home-hero*.webp` se sacaron de `src/assets/` el 23 sep 2026 (no se suben al hosting) y quedaron en `tools/dev/og/sin-uso/` por si
  se retoman.
- **Portada de la landing**: `src/pages/app-agendar-citas-whatsapp.html`, sección `.landing-hero`,
  estilos también en `15-media.css`.
- **Tarjeta para compartir**: cada página declara `og_image` y `og_image_alt` en su bloque `meta`;
  `src/partials/head.html` los emite como `og:image` y `twitter:image`.
- **Grano de película**: `src/styles/16-grano.css`, un SVG de ruido sobre toda la página al 5 %.
  Se quita borrando el archivo.

## Honestidad

Las fotos son ilustrativas: muestran cómo se ve una de estas apps en un negocio, **no** son clientes
reales ni capturas del producto terminado. Por eso cada `alt` empieza con "Ejemplo:". Si algún día
hay fotos de clientes reales, esas van primero: venden más que cualquier imagen generada.

## Chats de ChatGPT (por si quieres pedir un cambio sobre la misma imagen)

- Tarjeta de la home (barbería): https://chatgpt.com/c/6aac825f-40d0-83e8-8362-3985b23ebe29
- Agenda / barbería: https://chatgpt.com/c/6aac84de-d4a0-83e8-b6b0-28b6cb09f0a6
- Pedidos / abarrotes: https://chatgpt.com/c/6aac84fb-9130-83e8-8984-bfa512f35cdf
- Menú QR / restaurante: https://chatgpt.com/c/6aac856f-92f0-83e8-a852-eff871de231f
- Lealtad / cafetería: https://chatgpt.com/c/6aac858f-bf54-83e8-beb8-ee3892d55b83
- Inventario / taller: https://chatgpt.com/c/6aac85e1-e3ac-83e8-a4b7-7e0d1004c000
- Página web / escritorio: https://chatgpt.com/c/6aac8604-435c-83e8-94fd-35fc227fa885
- Portada landing / salón: https://chatgpt.com/c/6aac873d-f2c8-83e8-bec1-c56830e53057
