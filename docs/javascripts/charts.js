/* rio-edu-lab — Plotly chart loader.
 * Each <div data-chart="path/to/figure.json"> on a page gets its
 * Plotly figure JSON fetched and rendered. Mobile-friendly via
 * config.responsive=true. We hide the modeBar by default to keep
 * the look polished; specific charts can override via fig.config. */

(function () {
  function plotElement(el) {
    el.dataset.loading = "true";
    fetch(el.dataset.chart, { cache: "default" })
      .then(function (r) {
        if (!r.ok) throw new Error("fetch " + el.dataset.chart + " " + r.status);
        return r.json();
      })
      .then(function (fig) {
        var config = Object.assign(
          { responsive: true, displayModeBar: false, displaylogo: false },
          fig.config || {}
        );
        Plotly.newPlot(el, fig.data || [], fig.layout || {}, config);
        el.dataset.loading = "false";
      })
      .catch(function (err) {
        console.warn("[rio-edu-lab] chart load failed", err);
        el.textContent = "(falha ao carregar gráfico — abra DevTools para ver erro)";
        el.style.color = "#b2182b";
        el.dataset.loading = "false";
      });
  }

  function init() {
    if (typeof Plotly === "undefined") {
      // Plotly script not loaded yet — try again on next tick (instant within 1s typically).
      setTimeout(init, 100);
      return;
    }
    document.querySelectorAll("[data-chart]").forEach(plotElement);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  // Re-run when MkDocs Material does instant navigation between pages.
  if (typeof document$ !== "undefined" && document$.subscribe) {
    document$.subscribe(function () {
      // small delay to ensure new content is in DOM
      setTimeout(init, 30);
    });
  }
})();
