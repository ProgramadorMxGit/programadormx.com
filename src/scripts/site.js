(function () {
  'use strict';

  var PMX = window.PMX = window.PMX || {};
  var root = document.documentElement;
  var reduced = window.matchMedia('(prefers-reduced-motion: reduce)');
  var revealObserver;
  var userPaused = false;

  function readPause() {
    try { return localStorage.getItem('pmx_motion_paused') === 'yes'; }
    catch (error) { return false; }
  }

  function showAll() {
    document.querySelectorAll('[data-reveal], .reveal').forEach(function (element) {
      element.classList.add('is-visible');
    });
    if (revealObserver) revealObserver.disconnect();
  }

  function syncCanvas() {
    document.querySelectorAll('canvas[data-code-rain]').forEach(function (canvas) {
      if (canvas.__pmxRain) {
        canvas.__pmxRain.setStatic(PMX.motion.paused || canvas.getAttribute('data-intensity') === '0');
      }
    });
  }

  function updateMotion() {
    var paused = userPaused || reduced.matches;
    PMX.motion = { paused: paused, reduced: reduced.matches };
    root.classList.toggle('motion-paused', paused);
    document.querySelectorAll('[data-motion-toggle]').forEach(function (button) {
      var label = button.querySelector('[data-motion-label]');
      var text = reduced.matches ? 'Movimiento reducido' : paused ? 'Reanudar animaciones' : 'Pausar animaciones';
      button.setAttribute('aria-pressed', String(paused));
      button.setAttribute('aria-label', text);
      button.disabled = reduced.matches;
      if (label) label.textContent = text;
    });
    if (paused) showAll();
    syncCanvas();
    window.dispatchEvent(new CustomEvent('pmx:motion', { detail: PMX.motion }));
  }

  function initReveal() {
    var elements = document.querySelectorAll('[data-reveal], .reveal');
    PMX.reveal = { showAll: showAll };
    if (PMX.motion.paused || !('IntersectionObserver' in window)) {
      showAll();
      return;
    }
    try {
      revealObserver = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (!entry.isIntersecting) return;
          entry.target.classList.add('is-visible');
          revealObserver.unobserve(entry.target);
        });
      }, { threshold: 0.08, rootMargin: '0px 0px -20px 0px' });
      elements.forEach(function (element) { revealObserver.observe(element); });
      root.classList.add('motion-ready');
    } catch (error) {
      showAll();
    }
  }

  function sectionFor(link) {
    try {
      var url = new URL(link.href, document.baseURI);
      if (url.origin !== location.origin || url.pathname !== location.pathname || !url.hash) return null;
      return document.getElementById(decodeURIComponent(url.hash.slice(1)));
    } catch (error) { return null; }
  }

  function initNav() {
    var header = document.querySelector('.site-header');
    if (!header) return;
    var toggle = header.querySelector('[data-menu-toggle]');
    var navigation = document.getElementById('site-navigation');
    var open = false;
    var scheduled = false;

    function isMobile() { return toggle && window.getComputedStyle(toggle).display !== 'none'; }

    function setOpen(next, restoreFocus) {
      open = Boolean(next && isMobile());
      header.classList.toggle('is-open', open);
      document.body.classList.toggle('menu-open', open);
      if (toggle) {
        toggle.setAttribute('aria-expanded', String(open));
        toggle.setAttribute('aria-label', open ? 'Cerrar menú' : 'Abrir menú');
      }
      if (navigation) {
        navigation.hidden = Boolean(isMobile() && !open);
        navigation.inert = navigation.hidden;
      }
      if (restoreFocus && toggle) toggle.focus();
    }

    function updateHeader() {
      scheduled = false;
      header.classList.toggle('is-scrolled', window.scrollY > 24);
    }

    if (toggle && navigation) {
      setOpen(false, false);
      toggle.addEventListener('click', function () { setOpen(!open, false); });
      navigation.addEventListener('click', function (event) {
        if (event.target.closest('a[href]')) setOpen(false, false);
      });
      document.addEventListener('click', function (event) {
        if (open && !header.contains(event.target)) setOpen(false, false);
      });
      document.addEventListener('keydown', function (event) {
        if (!open) return;
        if (event.key === 'Escape') {
          event.preventDefault();
          setOpen(false, true);
          return;
        }
        if (event.key !== 'Tab') return;
        var items = Array.from(header.querySelectorAll('a[href], button:not([disabled]), [tabindex="0"]')).filter(function (item) {
          return item.getClientRects().length && !item.closest('[hidden], [inert]');
        });
        var first = items[0];
        var last = items[items.length - 1];
        if (!first) return;
        if (event.shiftKey && (document.activeElement === first || !header.contains(document.activeElement))) {
          event.preventDefault();
          last.focus();
        } else if (!event.shiftKey && (document.activeElement === last || !header.contains(document.activeElement))) {
          event.preventDefault();
          first.focus();
        }
      });
      window.addEventListener('resize', function () { setOpen(open, false); }, { passive: true });
    }

    updateHeader();
    window.addEventListener('scroll', function () {
      if (scheduled) return;
      scheduled = true;
      requestAnimationFrame(updateHeader);
    }, { passive: true });

    var links = Array.from(document.querySelectorAll('[data-nav-link]'));
    var sections = links.map(function (link) { return { link: link, section: sectionFor(link) }; }).filter(function (item) { return item.section; });

    function setActive(section) {
      sections.forEach(function (item) {
        var active = item.section === section;
        item.link.classList.toggle('is-active', active);
        if (active) item.link.setAttribute('aria-current', 'location');
        else item.link.removeAttribute('aria-current');
      });
    }

    if ('IntersectionObserver' in window && sections.length) {
      var observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) setActive(entry.target);
        });
      }, { rootMargin: '-40% 0px -55% 0px', threshold: 0 });
      sections.forEach(function (item) { observer.observe(item.section); });
    }
    PMX.nav = { close: function () { setOpen(false, true); } };
  }

  function initDemo() {
    var tabs = Array.from(document.querySelectorAll('[data-demo-tab]'));
    var views = Array.from(document.querySelectorAll('[data-demo-view]'));
    var panel = document.getElementById('demo-panel');
    if (!tabs.length || !panel) return;

    function select(tab, focus) {
      var value = tab.getAttribute('data-demo-tab');
      tabs.forEach(function (item) {
        var active = item === tab;
        item.setAttribute('aria-selected', String(active));
        item.tabIndex = active ? 0 : -1;
        item.classList.toggle('is-active', active);
      });
      views.forEach(function (view) { view.hidden = view.getAttribute('data-demo-view') !== value; });
      panel.setAttribute('aria-labelledby', tab.id);
      panel.setAttribute('data-active-view', value);
      if (focus) tab.focus();
    }

    tabs.forEach(function (tab, index) {
      tab.addEventListener('click', function () { select(tab, false); });
      tab.addEventListener('keydown', function (event) {
        var next;
        if (event.key === 'ArrowRight') next = (index + 1) % tabs.length;
        else if (event.key === 'ArrowLeft') next = (index + tabs.length - 1) % tabs.length;
        else if (event.key === 'Home') next = 0;
        else if (event.key === 'End') next = tabs.length - 1;
        else return;
        event.preventDefault();
        select(tabs[next], true);
      });
    });
    select(tabs.find(function (tab) { return tab.getAttribute('aria-selected') === 'true'; }) || tabs[0], false);

    var confirm = panel.querySelector('[data-demo-confirm]');
    if (confirm) confirm.addEventListener('click', function () {
      if (confirm.getAttribute('data-confirmed') === 'true') return;
      confirm.setAttribute('data-confirmed', 'true');
      confirm.setAttribute('aria-disabled', 'true');
      var label = confirm.querySelector('[data-confirm-label]');
      var status = document.querySelector('[data-demo-status]');
      var appointmentTag = panel.querySelector('.appointment-tag');
      if (label) label.textContent = 'Cita confirmada';
      if (appointmentTag) {
        appointmentTag.textContent = 'Confirmada';
        appointmentTag.style.color = 'var(--ok)';
      }
      if (status) status.textContent = 'Cita confirmada en esta demostración. No se envió ningún mensaje.';
    });
    PMX.demo = { select: function (value) {
      var tab = tabs.find(function (item) { return item.getAttribute('data-demo-tab') === value; });
      if (tab) select(tab, false);
    } };
  }

  function init() {
    root.classList.remove('no-js');
    root.classList.add('js');
    userPaused = readPause();
    updateMotion();
    initNav();
    initReveal();
    initDemo();
    document.querySelectorAll('[data-motion-toggle]').forEach(function (button) {
      button.addEventListener('click', function () {
        userPaused = !userPaused;
        try { localStorage.setItem('pmx_motion_paused', userPaused ? 'yes' : 'no'); }
        catch (error) { /* Motion controls also work when storage is unavailable. */ }
        updateMotion();
      });
    });
    if (reduced.addEventListener) reduced.addEventListener('change', updateMotion);
    else reduced.addListener(updateMotion);
    document.addEventListener('DOMContentLoaded', syncCanvas, { once: true });
    window.addEventListener('load', syncCanvas, { once: true });
    requestAnimationFrame(syncCanvas);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init, { once: true });
  else init();
})();
