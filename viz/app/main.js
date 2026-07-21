/* viz/app/main.js — boot + tab scaffold (viz/PLAN.md Phase 2).
 *
 * Classic script, IIFE-namespaced. Loads the index manifest (already
 * script-tag-included by index.html), refuses unknown schema versions
 * (delegated to VIZ.data), and initialises the V1 tab. V2–V5 are
 * placeholder panels only (Phases 3–6); their tab buttons are disabled
 * and hold no reference to any V1 state (R7).
 */
(function () {
  "use strict";

  function showBootError(err) {
    var el = document.getElementById("boot-error");
    el.hidden = false;
    el.textContent = "viz failed to start: " + (err && err.message ? err.message : err);
  }

  function wireTabs() {
    var bar = document.getElementById("tabbar");
    var buttons = Array.prototype.slice.call(bar.querySelectorAll("button"));
    buttons.forEach(function (btn) {
      btn.addEventListener("click", function () {
        if (btn.disabled) return;
        buttons.forEach(function (b) {
          b.setAttribute("aria-selected", b === btn ? "true" : "false");
        });
        ["v1", "v2", "v3", "v4", "v5"].forEach(function (id) {
          document.getElementById("tab-" + id).hidden = id !== btn.dataset.tab;
        });
      });
    });
  }

  function boot() {
    wireTabs();
    window.VIZ.data.getBundle("index").then(function (indexBundle) {
      // footer: deterministic input identity only (R3 — no clock, no sha)
      document.getElementById("app-footer").textContent =
        "viz_bundle_schema_version " + indexBundle.viz_bundle_schema_version +
        " · generator " + indexBundle.generator +
        " · data committed under viz/data/ (hash-pinned in " +
        "tests/test_viz_bundles.py; regenerate via python -m cavity.viz.export)" +
        " · captions and status flags render verbatim from the bundles";
      window.VIZ.v1.init(indexBundle);
    }).catch(showBootError);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
