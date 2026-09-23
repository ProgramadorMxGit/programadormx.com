/* code-rain.js — lluvia de código del hero (DESIGN.md §4, CONTRACT.md §9). Script clásico, sin dependencias.
   API: PMX.codeRain.mount(canvas, opts) → { setStatic, getState, destroy }. Automonta canvas[data-code-rain]. */
(function () {
  'use strict';
  var PMX = window.PMX = window.PMX || {};
  if (PMX.codeRain) return;

  /* Código real de las seis apps, con comentarios en español; sin cifras que parezcan precios. */
  var CORPUS = [
    "final cita = Cita(hora: '10:30', cliente: 'Luis');",
    "await recordatorio.enviar(cita, via: WhatsApp);",
    "// le llega el recordatorio un día antes",
    "citas.where((c) => c.dia == hoy).toList();",
    "if (mesa.ocupada) return;",
    "pedido.total += producto.precio * cantidad;",
    "// sin comisiones: el pedido llega directo",
    "\"menu\": [\"pastor\", \"bistec\", \"suadero\"]",
    "qr.generar(url: menu.url);",
    "sellos.agregar(cliente);",
    "if (sellos.length == 10) premio.otorgar();",
    "inventario.descontar('shampoo', cantidad);",
    "corteDelDia.imprimir();",
    "SELECT SUM(total) FROM ventas WHERE dia = HOY;",
    "UPDATE inventario SET stock = stock - 1 WHERE sku = @sku;",
    "whatsapp.abrir(mensaje: 'Hola, quiero agendar');",
    "return Scaffold(body: Agenda());",
    "class Pedido { final List<Producto> items; }",
    "db.insert('ventas', venta.toMap());",
    "final hoy = DateTime.now();",
    "// el dueño abre la app y ve su día",
    "List<Cita> agenda = await repo.deHoy();",
    "Text(cliente.nombre, style: negrita);",
    "carrito.agregar(taco, cantidad: 3);",
    "// la app es del negocio, no de una plataforma",
    "mensaje = 'Tu cita es mañana a las ${cita.hora}';",
    "horarios = [9, 10, 11, 12, 16, 17, 18];",
    "notificar(negocio.telefono, pedido.resumen());"
  ];
  var KEYWORD = /^(final|await|class|if|return|List|SELECT|SUM|FROM|WHERE|UPDATE|SET|Text|Scaffold)$/;
  var INDENTS = [0, 2, 4, 8], HOLD = 1800, FADE = 2400, FADE_TO = 0.12;

  function num(v, d) { var n = parseFloat(v); return isFinite(n) ? n : d; }
  function clamp(v, a, b) { return v < a ? a : v > b ? b : v; }
  function rnd(n) { return Math.floor(Math.random() * n); }
  function easeOut(q) { return 1 - Math.pow(1 - q, 3); }

  /* k: 0 resto (--ink-2) · 1 palabra clave (--accent-2) · 2 cadena (--accent) · 3 comentario (--ink-3) */
  function tokenize(line) {
    var cells = [], i = 0, n = line.length, ch, j;
    function push(to, k) { for (; i < to; i++) cells.push({ ch: line.charAt(i), k: k }); }
    while (i < n) {
      ch = line.charAt(i);
      if (ch === '/' && line.charAt(i + 1) === '/') push(n, 3);
      else if (ch === "'" || ch === '"') { j = line.indexOf(ch, i + 1); push(j < 0 ? n : j + 1, 2); }
      else if (/[A-Za-z_]/.test(ch)) {
        j = i + 1; while (j < n && /\w/.test(line.charAt(j))) j++;
        push(j, KEYWORD.test(line.slice(i, j)) ? 1 : 0);
      } else push(i + 1, 0);
    }
    return cells;
  }
  var LINES = CORPUS.map(function (l) { return { cells: tokenize(l), comment: l.indexOf('//') === 0 }; });
  var CODE = LINES.filter(function (l) { return !l.comment; });
  var POOLS = [[], [], [], []]; /* glifos por k: el sedimento "respira" sin cambiar de color */
  LINES.forEach(function (l) { l.cells.forEach(function (c) { if (c.ch !== ' ' && POOLS[c.k].indexOf(c.ch) < 0) POOLS[c.k].push(c.ch); }); });

  /* Densidad por breakpoint (§4.4); dt = periodo del cuadro lógico (30 fps; 24 en móvil). */
  function profile(vw) {
    if (vw < 768) return { font: 13, chH: 20, nB: 4, nC: 1, aB: 0.45, aC: 0.70, spotR: 150, dt: 1000 / 24, mobile: true };
    return { font: 14, chH: 22, nB: vw < 1024 ? 6 : 8, nC: 2, aB: 0.55, aC: 0.85, spotR: 220, dt: 1000 / 30, mobile: false };
  }

  /* Colores solo desde tokens; el contexto de sonda normaliza cualquier notación CSS a #rrggbb o rgb(). */
  function readColors(hero, probe) {
    var root = getComputedStyle(document.documentElement), hs = getComputedStyle(hero);
    function rgb(name, fallback) {
      var s, m; probe.fillStyle = '#000'; probe.fillStyle = root.getPropertyValue(name).trim() || fallback; s = probe.fillStyle;
      if (s.charAt(0) === '#') return [parseInt(s.substr(1, 2), 16), parseInt(s.substr(3, 2), 16), parseInt(s.substr(5, 2), 16)];
      m = s.match(/[\d.]+/g); return [+m[0], +m[1], +m[2]];
    }
    return {
      k: [rgb('--ink-2', hs.color), rgb('--accent-2', hs.color), rgb('--accent', hs.color), rgb('--ink-3', hs.color)],
      bg: 'rgb(' + rgb('--bg-0', hs.backgroundColor).join(',') + ')',
      font: root.getPropertyValue('--font-mono').trim() || hs.fontFamily
    };
  }

  function create(canvas, ctx, o) {
    var hero = canvas.closest('.hero') || canvas.parentElement, h1 = hero.querySelector('h1');
    var it = num(o.intensity, 1), density = clamp(num(o.density, 1), 0.6, 1), intensity = clamp(it || 1, 0.5, 1);
    var forceStatic = it === 0 || !!o.staticFrame, budget = num(o.budgetMs, 40);
    var sed = document.createElement('canvas'), sctx = sed.getContext('2d');
    var spot = document.createElement('canvas'), spx = spot.getContext('2d');
    var probe = document.createElement('canvas').getContext('2d'), colors = readColors(hero, probe), cache = [[], [], [], []];
    var P, cw, chH, w, h, dpr, cols, rows, font, rowMin, rowMax, key, focus, busy, atten, gCh, gK, gHot, gOrig, flick = [];
    var streams = [], commentTyping = 0, clock = 0, breath = 0, isStatic = false, destroyed = false;
    var p = { x: 0, y: 0, tx: 0, ty: 0, r: 0, a: 0, inside: false, last: -1e9, pulse: null };
    var ring = new Float32Array(60), ri = 0, sum = 0, full = false, avg = 0, over = -1, under = -1, degraded = false, recovered = false;
    var acc = 0, lastTs = null, raf = 0, inView = true, visible = !document.hidden, hoverNone, coarse, io, ro, resizeT;
    var rm = matchMedia('(prefers-reduced-motion: reduce)');

    function local(e) { var r = canvas.getBoundingClientRect(); return { x: e.clientX - r.left, y: e.clientY - r.top }; }
    function onMove(e) { var q = local(e); p.tx = q.x; p.ty = q.y; p.inside = true; p.last = performance.now(); }
    function onLeave() { p.inside = false; p.last = performance.now(); }
    function onDown(e) { if (e.pointerType === 'touch' || coarse) { var q = local(e); p.pulse = { x: q.x, y: q.y, t: 0 }; } }
    function onVis() { visible = !document.hidden; schedule(); }
    function onResize() { clearTimeout(resizeT); resizeT = setTimeout(function () { layout(false); }, 150); }

    function measure() {
      probe.font = '500 ' + P.font + 'px ' + colors.font;
      cw = Math.round(probe.measureText('M').width * 2) / 2 + 1; chH = P.chH;
    }
    function layout(force) {
      var W = hero.clientWidth, H = hero.clientHeight, hr, r, k;
      if (!W || !H || destroyed) return;
      P = profile(window.innerWidth); hoverNone = matchMedia('(hover: none)').matches; coarse = matchMedia('(pointer: coarse)').matches;
      measure();
      hr = canvas.getBoundingClientRect(); r = h1 ? h1.getBoundingClientRect() : hr;
      focus = { cx: r.left - hr.left + r.width / 2, cy: r.top - hr.top + r.height / 2, w: r.width };
      k = [W, H, cw, chH, Math.round(focus.cx), Math.round(focus.cy), Math.round(focus.w)].join('|');
      if (!force && k === key) return; /* el ResizeObserver dispara al observar y en el scroll móvil: solo se reconstruye si algo cambió */
      key = k; w = W; h = H; dpr = Math.min(window.devicePixelRatio || 1, 1.5);
      [canvas, sed, spot].forEach(function (cv) { cv.width = Math.round(w * dpr); cv.height = Math.round(h * dpr); cv.getContext('2d').setTransform(dpr, 0, 0, dpr, 0, 0); });
      cols = Math.ceil(w / cw) + 1; rows = Math.ceil(h / chH); font = '500 ' + P.font + 'px ' + colors.font;
      rowMin = Math.max(0, Math.floor(96 / chH) - 1); rowMax = Math.max(rowMin + 1, rows - Math.ceil(140 / chH)); /* fuera de los fundidos del mask-image */
      streams.length = 0; busy = new Uint8Array(rows); commentTyping = 0;
      if (p.last < 0) { p.x = p.tx = w * 0.66; p.y = p.ty = h * 0.46; }
      buildAtten(); genSediment(); paintSediment(); applyMode();
    }

    /* Charco bajo el titular: 0.12 en el centro → 1 en el borde (smoothstep). La viñeta del sitio actual, ahora escudo del h1. */
    function buildAtten() {
      var f = focus, R = P.mobile ? 0.7 * w : Math.max(f.w * 0.75, 0.55 * Math.min(w, h)), r, c, dx, dy, t;
      atten = new Float32Array(cols * rows);
      for (r = 0; r < rows; r++) for (c = 0; c < cols; c++) {
        dx = c * cw + cw / 2 - f.cx; dy = r * chH + chH / 2 - f.cy; t = Math.min(1, Math.sqrt(dx * dx + dy * dy) / R);
        atten[r * cols + c] = 0.12 + 0.88 * t * t * (3 - 2 * t);
      }
    }
    function rgba(k, a) { /* cadenas cacheadas por color y alfa en pasos de 0.02 */
      var i = Math.min(50, Math.round(a * 50)), c = cache[k];
      return c[i] || (c[i] = 'rgba(' + colors.k[k].join(',') + ',' + i / 50 + ')');
    }

    /* Sedimento: el corpus barajado, escrito corrido y envuelto fila a fila con sangrías al azar (un archivo, no ruido). */
    function genSediment() {
      var n = cols * rows, order = [], li = 0, r = 0, c = INDENTS[rnd(4)], i, j, cells;
      gCh = new Array(n); gK = new Uint8Array(n); gHot = new Uint8Array(n);
      for (i = 0; i < LINES.length; i++) order.splice(rnd(i + 1), 0, i);
      while (r < rows) {
        cells = LINES[order[li++ % order.length]].cells;
        for (j = 0; j < cells.length; j++) {
          if (c >= cols) { r++; c = INDENTS[rnd(4)]; if (r >= rows) break; }
          i = r * cols + c++; gCh[i] = cells[j].ch; gK[i] = cells[j].k;
        }
        c += 3;
      }
      gOrig = gCh.slice(); flick.length = 0;
    }
    function paintSediment() {
      var i, n = cols * rows;
      sctx.clearRect(0, 0, w, h); sctx.font = font; sctx.textBaseline = 'alphabetic';
      for (i = 0; i < n; i++) paintCell(i, false);
    }
    function paintCell(i, clear) { /* base --ink-3 a 0.10; línea sedimentada con su color a 0.12; ambas × charco */
      var c = i % cols, r = (i - c) / cols, ch = gCh[i], hot = gHot[i];
      if (clear) sctx.clearRect(c * cw, r * chH, cw, chH);
      if (!ch || ch === ' ') return;
      sctx.fillStyle = rgba(hot ? gK[i] : 3, (hot ? 0.12 : 0.10) * atten[i]);
      sctx.fillText(ch, c * cw, r * chH + 16);
    }
    function clearRow(r) {
      var i = r * cols, end = i + cols;
      sctx.clearRect(0, r * chH, w, chH);
      for (; i < end; i++) { gCh[i] = gOrig[i] = undefined; gHot[i] = 0; }
    }
    function sediment(s) {
      var j, c, i;
      for (j = 0; j < s.pos && (c = s.col0 + j) < cols; j++) { i = s.row * cols + c; gCh[i] = gOrig[i] = s.cells[j].ch; gK[i] = s.cells[j].k; gHot[i] = 1; paintCell(i, true); }
    }
    function breathe() { /* cada 900 ms el 1 % de las celdas muestra otro glifo del mismo k; al siguiente respiro vuelve el original, así el archivo no se degrada a ruido */
      var n = cols * rows, k = Math.max(1, Math.floor(n * 0.01)), i, pool;
      while (flick.length) { i = flick.pop(); if (gCh[i] && gOrig[i]) { gCh[i] = gOrig[i]; paintCell(i, true); } }
      while (k--) { i = rnd(n); if (gCh[i] && gCh[i] !== ' ') { pool = POOLS[gK[i]]; gCh[i] = pool[rnd(pool.length)]; flick.push(i); paintCell(i, true); } }
    }

    function spawn(kind) {
      var free = [], r, row, src = commentTyping ? CODE : LINES, line, col0, s, panes; /* una sola línea // tecleándose a la vez */
      for (r = rowMin; r < rowMax; r++) if (!busy[r]) free.push(r);
      if (!free.length) return null;
      row = free[rnd(free.length)]; line = src[rnd(src.length)];
      /* Paneles de ≥ 60 columnas (1 en móvil, 2 a 1440, 3 a 1920) con sangría 0/2/4/8: así la lluvia también vive a la derecha del charco. */
      panes = Math.max(1, Math.floor(cols / 60));
      col0 = Math.floor(rnd(panes) * cols / panes) + INDENTS[rnd(4)];
      if (col0 + line.cells.length > cols) col0 = Math.max(0, cols - line.cells.length);
      busy[row] = 1; clearRow(row); if (line.comment) commentTyping++;
      s = { kind: kind, row: row, col0: col0, cells: line.cells, pos: 0, tick: 0, phase: 0, t: 0, alpha: kind ? P.aC : P.aB, from: 0, comment: line.comment };
      streams.push(s); return s;
    }
    function targetB() { var n = Math.round(P.nB * density); return degraded ? Math.max(2, Math.floor(n / 2)) : n; }
    function targetC() { return degraded ? 1 : P.nC; }
    function fill() {
      var b = 0, c = 0, i, s, tB = targetB(), tC = targetC();
      for (i = 0; i < streams.length; i++) { s = streams[i]; if (s.phase < 2) { if (s.kind) c++; else b++; } }
      if (streams.length >= (tB + tC) * 2) return; /* los que se funden no cuentan, pero tampoco se acumulan */
      while (b++ < tB && spawn(0));
      while (c++ < tC && spawn(1));
    }

    function updateSpot(dt) {
      var tr = 0, ta = 0, ph;
      if (p.inside) { tr = P.spotR; ta = 0.9; }
      else if (!degraded && (hoverNone || performance.now() - p.last > 2000)) {
        /* Linterna autónoma: Lissajous de 14 s por la mitad derecha, donde vive la lluvia; débil para no competir con el texto. */
        ph = clock / 14000 * Math.PI * 2;
        p.tx = w * (0.66 + 0.35 * Math.sin(2 * ph)); p.ty = h * (0.46 + 0.22 * Math.sin(3 * ph + 1.1)); tr = P.spotR; ta = 0.25;
      }
      p.x += (p.tx - p.x) * 0.10; p.y += (p.ty - p.y) * 0.10; /* lámpara que persigue, no puntero */
      p.r = tr > p.r ? p.r + (tr - p.r) * 0.12 : Math.max(0, p.r - P.spotR * dt / 600);
      p.a += (ta * intensity - p.a) * 0.10;
      if (p.pulse && (p.pulse.t += dt) >= 700) p.pulse = null;
    }
    function step(dt) {
      var i, s, fast, q;
      clock += dt; updateSpot(dt);
      for (i = streams.length - 1; i >= 0; i--) {
        s = streams[i];
        if (s.phase === 0) { /* 1 carácter cada 2 cuadros; al doble bajo la lámpara */
          fast = p.a > 0.1 && Math.abs(s.row * chH + 16 - p.y) < p.r;
          if (++s.tick >= (fast ? 1 : 2)) { s.tick = 0; if (++s.pos >= s.cells.length) { s.phase = 1; s.t = 0; if (s.comment) commentTyping--; } }
        } else if (s.phase === 1) { if ((s.t += dt) >= HOLD) { s.phase = 2; s.t = 0; s.from = s.alpha; } }
        else {
          q = Math.min(1, (s.t += dt) / FADE); s.alpha = s.from + (FADE_TO - s.from) * easeOut(q);
          if (q >= 1) { sediment(s); busy[s.row] = 0; streams.splice(i, 1); }
        }
      }
      fill();
      if ((breath += dt) >= 900) { breath = 0; breathe(); }
    }

    function drawStream(c2, s, base, lit, x0, x1) {
      var y = s.row * chH + 16, off = s.row * cols, j, c, x, a, cell;
      for (j = 0; j < s.pos && (c = s.col0 + j) < cols; j++) {
        cell = s.cells[j]; if (cell.ch === ' ') continue;
        x = c * cw; if (lit && (x < x0 || x > x1)) continue;
        a = atten[off + c]; if (lit) a = Math.sqrt(a); /* la lámpara afloja el charco sin borrarlo: el h1 sigue legible */
        c2.fillStyle = rgba(cell.k, base * a); c2.fillText(cell.ch, x, y);
      }
      if (!lit && s.kind && s.phase < 2 && (isStatic || Math.floor(clock / 530) % 2 === 0) && (c = s.col0 + s.pos) < cols) {
        c2.fillStyle = rgba(2, intensity * atten[off + c]); /* cursor de bloque: el mismo de los eyebrows */
        c2.fillRect(c * cw, y - P.font * 0.8, (cw - 1) * 0.55, P.font);
      }
    }
    /* Spot por composición: celdas activas a alfa 1 en el offscreen, destination-in con un gradiente radial, un drawImage. */
    function drawSpot() {
      var x, y, r, a, q, i, s, ry, g;
      if (p.pulse) { q = p.pulse.t / 700; x = p.pulse.x; y = p.pulse.y; r = 260 * easeOut(q); a = 0.9 * intensity * (1 - q); }
      else { x = p.x; y = p.y; r = p.r; a = p.a; }
      if (r < 2 || a < 0.02) return;
      spx.globalCompositeOperation = 'source-over'; spx.clearRect(0, 0, w, h); spx.font = font; spx.textBaseline = 'alphabetic';
      for (i = 0; i < streams.length; i++) { s = streams[i]; ry = s.row * chH + 16; if (ry > y - r && ry - chH < y + r) drawStream(spx, s, 1, true, x - r - cw, x + r); }
      g = spx.createRadialGradient(x, y, Math.min(40, r * 0.25), x, y, r); g.addColorStop(0, 'rgba(0,0,0,1)'); g.addColorStop(1, 'rgba(0,0,0,0)');
      spx.globalCompositeOperation = 'destination-in'; spx.fillStyle = g; spx.fillRect(x - r, y - r, r * 2, r * 2);
      ctx.globalAlpha = a; ctx.drawImage(spot, 0, 0, w, h); ctx.globalAlpha = 1;
    }
    function draw() { /* por cuadro: 1 fill, 1 drawImage (sedimento), fillText de celdas activas, 1 drawImage (spot) */
      var i;
      ctx.fillStyle = colors.bg; ctx.fillRect(0, 0, w, h); ctx.drawImage(sed, 0, 0, w, h);
      ctx.font = font; ctx.textBaseline = 'alphabetic';
      for (i = 0; i < streams.length; i++) drawStream(ctx, streams[i], streams[i].alpha * intensity, false);
      drawSpot();
    }

    /* Cuadro estático (reduced-motion o data-intensity="0"): 8 líneas terminadas + 2 foco con cursor fijo + spot fijo. */
    function drawStatic() {
      var i, s;
      streams.length = 0; busy = new Uint8Array(rows); commentTyping = 0;
      for (i = 0; i < 10; i++) { s = spawn(i < 8 ? 0 : 1); if (!s) break; s.pos = s.cells.length; s.phase = 1; s.alpha = s.kind ? 0.85 : 0.35; }
      commentTyping = 0; p.x = w * 0.66; p.y = h * 0.46; p.r = 260; p.a = 0.9 * intensity; p.pulse = null;
      draw();
    }
    function applyMode() {
      var was = isStatic;
      isStatic = forceStatic || rm.matches;
      if (isStatic) { stop(); drawStatic(); return; }
      if (was) { p.r = 0; streams.forEach(function (s) { s.phase = 2; s.t = 0; s.from = s.alpha; }); }
      draw(); schedule();
    }
    function schedule() {
      var run = inView && visible && !isStatic && !destroyed;
      if (run && !raf) { lastTs = null; acc = 0; over = under = -1; raf = requestAnimationFrame(tick); }
      else if (!run) stop();
    }
    function stop() { if (raf) cancelAnimationFrame(raf); raf = 0; }
    /* Acumulador de cuadro fijo: los streams cuentan cuadros lógicos y al reanudar el reloj arranca de cero, sin saltos. */
    function tick(ts) {
      var dt = P.dt, n = 0, d;
      raf = requestAnimationFrame(tick);
      if (lastTs !== null) { d = ts - lastTs; acc = Math.min(acc + d, dt * 3); sample(d, ts); }
      lastTs = ts;
      while (acc >= dt) { acc -= dt; step(dt); n++; }
      if (n) draw();
    }
    /* Autoajuste con histéresis: N baja tras 2 s por encima del presupuesto; vuelve tras 10 s holgados, una vez por sesión. */
    function sample(d, ts) {
      sum += d - ring[ri]; ring[ri] = d; ri = (ri + 1) % 60; if (!ri) full = true;
      if (!full) return;
      avg = sum / 60;
      if (avg > budget) { if (over < 0) over = ts; else if (!degraded && ts - over > 2000) { degraded = true; over = -1; } } else over = -1;
      if (degraded && !recovered) { if (avg < 25) { if (under < 0) under = ts; else if (ts - under > 10000) { degraded = false; recovered = true; } } else under = -1; }
    }
    function loadFont() { /* primer cuadro con la pila de respaldo; al llegar la mono (o a los 2 s) se re-mide y se reconstruye si cambió */
      var fam = colors.font.split(',')[0].trim();
      if (!document.fonts || !document.fonts.load || !fam) return;
      Promise.race([document.fonts.load('500 14px ' + fam), new Promise(function (ok) { setTimeout(ok, 2000); })]).then(function () {
        if (destroyed) return;
        var before = cw; measure();
        if (cw !== before) layout(true); else { paintSediment(); draw(); }
      }, function () {});
    }

    hero.addEventListener('pointermove', onMove, { passive: true });
    hero.addEventListener('pointerleave', onLeave, { passive: true });
    hero.addEventListener('pointerdown', onDown, { passive: true });
    document.addEventListener('visibilitychange', onVis);
    if (rm.addEventListener) rm.addEventListener('change', applyMode); else rm.addListener(applyMode);
    if (window.IntersectionObserver) { io = new IntersectionObserver(function (es) { inView = es[es.length - 1].isIntersecting; schedule(); }, { threshold: 0 }); io.observe(hero); }
    if (window.ResizeObserver) { ro = new ResizeObserver(onResize); ro.observe(hero); if (h1) ro.observe(h1); } else window.addEventListener('resize', onResize);
    layout(true); loadFont();

    return canvas.__pmxRain = {
      setStatic: function (v) { forceStatic = !!v; applyMode(); },
      getState: function () {
        var b = 0, c = 0;
        streams.forEach(function (s) { if (s.phase < 2) { if (s.kind) c++; else b++; } });
        return { mode: isStatic ? 'static' : raf ? 'running' : 'paused', streamsB: b, streamsC: c, targetB: targetB(), targetC: targetC(),
          degraded: degraded, recovered: recovered, avgFrameMs: avg, cols: cols, rows: rows, charWidth: cw, dpr: dpr, spot: { x: p.x, y: p.y, r: p.r, a: p.a } };
      },
      destroy: function () {
        destroyed = true; stop(); clearTimeout(resizeT);
        hero.removeEventListener('pointermove', onMove); hero.removeEventListener('pointerleave', onLeave); hero.removeEventListener('pointerdown', onDown);
        document.removeEventListener('visibilitychange', onVis);
        if (rm.removeEventListener) rm.removeEventListener('change', applyMode); else rm.removeListener(applyMode);
        if (io) io.disconnect();
        if (ro) ro.disconnect(); else window.removeEventListener('resize', onResize);
        if (w) { ctx.fillStyle = colors.bg; ctx.fillRect(0, 0, w, h); }
        delete canvas.__pmxRain;
      }
    };
  }

  PMX.codeRain = {
    mount: function (canvas, opts) {
      var ctx = canvas && canvas.getContext && canvas.getContext('2d', { alpha: false });
      if (!ctx) return null;
      if (canvas.__pmxRain) canvas.__pmxRain.destroy();
      return create(canvas, ctx, opts || {});
    },
    auto: function () {
      var list = document.querySelectorAll('canvas[data-code-rain]'), i, c;
      for (i = 0; i < list.length; i++) { c = list[i]; if (!c.__pmxRain) PMX.codeRain.mount(c, { density: c.getAttribute('data-density'), intensity: c.getAttribute('data-intensity') }); }
    }
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', PMX.codeRain.auto); else PMX.codeRain.auto();
})();
