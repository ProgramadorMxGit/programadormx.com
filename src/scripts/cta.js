(function () {
  'use strict';

  var PMX = window.PMX = window.PMX || {};

  // An empty analytics configuration never sends events or loads a remote script.
  PMX.track = function (name, properties) {
    var config = PMX.config || {};
    if (!config.ga4_id || typeof window.gtag !== 'function') return;
    try {
      if (localStorage.getItem('pmx_consent') !== 'yes') return;
      window.gtag('event', name, properties || {});
    } catch (error) { /* Optional analytics must not interrupt navigation. */ }
  };

  function init() {
    document.querySelectorAll('a[target="_blank"]').forEach(function (link) {
      link.relList.add('noopener', 'noreferrer');
    });

    document.addEventListener('click', function (event) {
      var target = event.target.closest('[data-track]');
      if (target) PMX.track(target.getAttribute('data-track'));
    });

    var floating = document.querySelector('[data-wa-float]');
    if (!floating) return;
    var hero = document.querySelector('.hero');

    function setVisible(visible) {
      floating.hidden = !visible;
      floating.classList.toggle('is-visible', visible);
    }

    if (!hero || !('IntersectionObserver' in window)) {
      setVisible(true);
      return;
    }
    setVisible(false);
    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) { setVisible(!entry.isIntersecting); });
    }, { threshold: 0 });
    observer.observe(hero);
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init, { once: true });
  else init();
})();
