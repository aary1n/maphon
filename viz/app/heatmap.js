/* viz/app/heatmap.js — V1 interactive r–z heatmap (viz/PLAN.md Phase 2).
 *
 * Classic script, IIFE-namespaced. RENDERING ONLY: the sole arithmetic
 * licensed here (§3.2) is the outer-product partial sum
 *   field[i][j] = Σ_{n<N} theta_k[n][i] · radial_basis[n][j]
 * over exported f32 factor matrices, the exact-linearity rescale
 * × P/P_ref, and min/max normalisation for the colour scale. No Bessel
 * evaluation, no formulae, no physics in JS. Colour comes exclusively
 * from the exported SEQUENTIAL_THERMAL LUT (colormap parity, §5 item 4).
 * Captions and status flags are rendered verbatim from the bundle —
 * never retyped here (R4).
 *
 * R7 isolation: the scenario state lives inside this closure; the module
 * exposes init() only — no scenario-state reference escapes the V1 tab.
 */
(function () {
  "use strict";

  var NZ = 161;
  var NR = 121;

  // canvas geometry (display chrome only)
  var W = 600, H = 720;
  var ML = 66, MR = 128, MT = 36, MB = 58;
  var PW = W - ML - MR;   // plot width
  var PH = H - MT - MB;   // plot height
  var CB_GAP = 18, CB_W = 18; // colorbar

  // ---- private state (never exported — R7) ----
  var manifest = null;   // index bundle payload
  var shared = null;
  var lut = null;        // Uint8Array 256*3
  var rowByAxes = null;  // "i,i,i,i,i" -> manifest scenario row
  var state = {
    axes: null,          // [i_k, i_dep, i_hc, i_rad, i_base]
    pW: null,            // absorbed power, W
    nModes: null         // partial-sum mode count
  };
  var current = null;    // {row, bundle, theta, basis, nKept, field, vmin, vmax, scale}
  var loadToken = 0;

  var els = {};          // resolved DOM handles

  // ---- helpers ----
  function fmt(x, digits) {
    var s = Number(x).toFixed(digits === undefined ? 3 : digits);
    // never display negative zero (e.g. a -6e-16 Dirichlet-base minimum)
    if (parseFloat(s) === 0) s = (0).toFixed(digits === undefined ? 3 : digits);
    return s;
  }

  function fmtSci(x) {
    if (x === 0) return "0";
    var e = Math.floor(Math.log10(Math.abs(x)));
    if (e >= -3 && e < 5) return String(Number(x.toPrecision(3)));
    return x.toExponential(2);
  }

  function niceTicks(lo, hi, target) {
    if (!(hi > lo)) return [lo];
    var span = hi - lo;
    var step = Math.pow(10, Math.floor(Math.log10(span / target)));
    var err = span / (target * step);
    if (err >= 7.5) step *= 10;
    else if (err >= 3.5) step *= 5;
    else if (err >= 1.5) step *= 2;
    var ticks = [];
    for (var v = Math.ceil(lo / step) * step; v <= hi + 1e-12 * span; v += step) {
      ticks.push(Math.abs(v) < 1e-12 * span ? 0 : v);
    }
    return ticks;
  }

  // ---- reconstruction (the licensed arithmetic) ----
  function reconstruct(theta, basis, nUse) {
    var f = new Float64Array(NZ * NR);
    for (var n = 0; n < nUse; n++) {
      var tOff = n * NZ;
      var bOff = n * NR;
      for (var i = 0; i < NZ; i++) {
        var ti = theta[tOff + i];
        if (ti === 0) continue;
        var fOff = i * NR;
        for (var j = 0; j < NR; j++) {
          f[fOff + j] += ti * basis[bOff + j];
        }
      }
    }
    return f;
  }

  // ---- painting ----
  function lutColor(t) {
    // matplotlib LUT quantisation: index = floor(t·256), clamped to 0..255
    var idx = Math.floor(t * 256);
    if (idx < 0) idx = 0;
    if (idx > 255) idx = 255;
    return idx;
  }

  function paint() {
    if (!current || !current.field) return;
    var ctx = els.canvas.getContext("2d");
    ctx.clearRect(0, 0, W, H);

    var scale = state.pW / shared.p_ref_w;
    var f = current.field;
    var vlo = Infinity, vhi = -Infinity;
    for (var q = 0; q < f.length; q++) {
      if (f[q] < vlo) vlo = f[q];
      if (f[q] > vhi) vhi = f[q];
    }
    vlo *= scale; vhi *= scale;
    if (!(vhi > vlo)) { vhi = vlo; }
    current.vmin = vlo;
    current.vmax = vhi;
    current.scale = scale;
    var span = vhi - vlo;

    // field image at grid resolution, scaled up with bilinear smoothing
    // (the canvas analogue of F3's gouraud shading)
    var off = document.createElement("canvas");
    off.width = NR; off.height = NZ;
    var octx = off.getContext("2d");
    var img = octx.createImageData(NR, NZ);
    var px = img.data;
    for (var i = 0; i < NZ; i++) {
      for (var j = 0; j < NR; j++) {
        var v = f[i * NR + j] * scale;
        var idx = span > 0 ? lutColor((v - vlo) / span) : 0;
        var p = 4 * (i * NR + j);
        px[p] = lut[3 * idx];
        px[p + 1] = lut[3 * idx + 1];
        px[p + 2] = lut[3 * idx + 2];
        px[p + 3] = 255;
      }
    }
    octx.putImageData(img, 0, 0);
    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = "high";
    ctx.drawImage(off, ML, MT, PW, PH);

    // frame (F3 shows a full ink frame around the field)
    ctx.strokeStyle = "#0b0b0b";
    ctx.lineWidth = 1.2;
    ctx.strokeRect(ML, MT, PW, PH);

    drawAxes(ctx);
    drawColorbar(ctx, vlo, vhi, span);
    drawTitle(ctx);
  }

  function drawAxes(ctx) {
    var rMax = manifest._rMm[NR - 1];
    var zMax = manifest._zMm[NZ - 1];
    ctx.fillStyle = "#52514e";
    ctx.strokeStyle = "#52514e";
    ctx.lineWidth = 1;
    ctx.font = "12px Georgia, serif";

    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    niceTicks(0, rMax, 6).forEach(function (t) {
      var x = ML + (t / rMax) * PW;
      ctx.beginPath();
      ctx.moveTo(x, MT + PH);
      ctx.lineTo(x, MT + PH + 4);
      ctx.stroke();
      ctx.fillText(fmt(t, 1), x, MT + PH + 7);
    });
    ctx.textBaseline = "middle";
    ctx.textAlign = "right";
    niceTicks(0, zMax, 8).forEach(function (t) {
      // z increases downward from the illuminated face (F3 orientation)
      var y = MT + (t / zMax) * PH;
      ctx.beginPath();
      ctx.moveTo(ML, y);
      ctx.lineTo(ML - 4, y);
      ctx.stroke();
      ctx.fillText(fmt(t, 0), ML - 7, y);
    });

    ctx.fillStyle = "#0b0b0b";
    ctx.font = "13px Georgia, serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "alphabetic";
    ctx.fillText("r (mm)", ML + PW / 2, H - 18);
    ctx.save();
    ctx.translate(16, MT + PH / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.fillText("z (mm) — depth below illuminated face", 0, 0);
    ctx.restore();
  }

  function drawColorbar(ctx, vlo, vhi, span) {
    var x0 = ML + PW + CB_GAP;
    for (var y = 0; y < PH; y++) {
      var t = 1 - y / (PH - 1); // vmax at top, matching F3
      var idx = lutColor(t);
      ctx.fillStyle = "rgb(" + lut[3 * idx] + "," + lut[3 * idx + 1] + "," +
        lut[3 * idx + 2] + ")";
      ctx.fillRect(x0, MT + y, CB_W, 1.5);
    }
    ctx.fillStyle = "#52514e";
    ctx.strokeStyle = "#52514e";
    ctx.font = "12px Georgia, serif";
    ctx.textAlign = "left";
    ctx.textBaseline = "middle";
    var ticks = span > 0 ? niceTicks(vlo, vhi, 6) : [vlo];
    ticks.forEach(function (t) {
      var frac = span > 0 ? (t - vlo) / span : 0;
      var y = MT + (1 - frac) * PH;
      ctx.beginPath();
      ctx.moveTo(x0 + CB_W, y);
      ctx.lineTo(x0 + CB_W + 4, y);
      ctx.stroke();
      ctx.fillText(fmt(t, span >= 5 ? 0 : 2), x0 + CB_W + 7, y);
    });
    ctx.fillStyle = "#0b0b0b";
    ctx.font = "13px Georgia, serif";
    ctx.save();
    ctx.translate(x0 + CB_W + 46, MT + PH / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.textAlign = "center";
    ctx.textBaseline = "alphabetic";
    ctx.fillText("ΔT (K)", 0, 0);
    ctx.restore();
  }

  function drawTitle(ctx) {
    ctx.fillStyle = "#0b0b0b";
    ctx.font = "15px Georgia, serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "alphabetic";
    ctx.fillText("ΔT(r, z), maser crystal", ML + PW / 2, 22);
  }

  function paintDisabled(reason) {
    var ctx = els.canvas.getContext("2d");
    ctx.clearRect(0, 0, W, H);
    ctx.fillStyle = "#f6f6f4";
    ctx.fillRect(ML, MT, PW, PH);
    ctx.strokeStyle = "#c8c7c2";
    ctx.lineWidth = 1.2;
    ctx.strokeRect(ML, MT, PW, PH);
    ctx.fillStyle = "#52514e";
    ctx.font = "13px Georgia, serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText("structurally invalid cell — no steady state",
      ML + PW / 2, MT + PH / 2 - 12);
    ctx.fillText("(see reason below; step any control to leave)",
      ML + PW / 2, MT + PH / 2 + 12);
    els.plotStatus.textContent = reason;
  }

  // ---- readout panels ----
  function gridStepFor(n) {
    // vol-avg/deficit readouts step the exported N-grid (§3.2); the cap
    // position reads the full solve (identical up to the recorded
    // truncation bound)
    if (!current) return null;
    if (n >= current.nKept) return "64";
    var best = null;
    Object.keys(current.bundle.payload.n_grid_scalars).forEach(function (k) {
      var kn = parseInt(k, 10);
      if (kn <= n && (best === null || kn > parseInt(best, 10))) best = k;
    });
    return best;
  }

  function updateReadouts() {
    if (!current || !current.field) return;
    var pl = current.bundle.payload;
    var scale = current.scale;
    var stepKey = gridStepFor(state.nModes);
    var step = stepKey ? pl.n_grid_scalars[stepKey] : null;
    var stepLabel = stepKey === null ? "—"
      : (state.nModes >= current.nKept
        ? "full solve (N = 64 ≡ N ≥ n_kept up to the truncation bound)"
        : "N-grid step " + stepKey);

    // peak_k convention (cylinder.py): ΔT(0, 0), the illuminated-face
    // centre — the client-side partial row sum at grid node (0, 0),
    // continuous in N and equal to the bundle's peak_k at N = n_kept
    var peak = current.field[0] * scale;
    var rows =
      "<tr><td>peak ΔT — ΔT(0, 0), illuminated-face centre (N = " +
      state.nModes + ")</td>" +
      "<td class=\"num\">" + fmt(peak, 3) + " K</td></tr>" +
      "<tr><td>⟨ΔT⟩_vol (" + stepLabel + ")</td><td class=\"num\">" +
      (step ? fmt(step.vol_avg_k * scale, 3) + " K" : "—") + "</td></tr>" +
      "<tr><td>colour scale (min–max of displayed field)</td>" +
      "<td class=\"num\">" + fmt(current.vmin, 2) + " – " +
      fmt(current.vmax, 2) + " K</td></tr>" +
      "<tr><td>scenario</td><td class=\"num\">" + current.row.id + "</td></tr>";
    els.readouts.innerHTML = rows;

    var bp = pl.boundary_power_w;
    var mw = function (w) { return fmt(w * scale * 1e3, 3); };
    els.energy.innerHTML =
      "<tr><td>top</td><td class=\"num\">" + mw(bp.top) + " mW</td></tr>" +
      "<tr><td>side</td><td class=\"num\">" + mw(bp.side) + " mW</td></tr>" +
      "<tr><td>base</td><td class=\"num\">" + mw(bp.base) + " mW</td></tr>" +
      "<tr class=\"total\"><td>total boundary flux</td><td class=\"num\">" +
      mw(bp.total) + " mW</td></tr>" +
      "<tr><td>residual |P − total|/P (full solve)</td><td class=\"num\">" +
      fmtSci(pl.deficit_rel) + "</td></tr>" +
      "<tr><td>residual (" + stepLabel + ")</td><td class=\"num\">" +
      (step ? fmtSci(step.deficit_rel) : "—") + "</td></tr>";
    els.energyNote.textContent =
      "split at the full solve (N = 64), rescaled × P/P_ref (exact " +
      "linearity); residual is P-invariant. Recorded tail estimate " +
      fmtSci(pl.tail_estimate_rel) + ".";
  }

  function updateFlagStrip() {
    var strip = els.flagstrip;
    strip.innerHTML = "";
    if (!current) return;
    var b = current.bundle;
    var chips = document.createElement("div");
    chips.className = "flagchips";
    b.status_flags.forEach(function (flag) {
      var c = document.createElement("span");
      c.className = "flagchip";
      c.textContent = flag; // verbatim from the bundle — never retyped
      chips.appendChild(c);
    });
    strip.appendChild(chips);
    var det = document.createElement("details");
    det.id = "v1-caption-details";
    var sum = document.createElement("summary");
    sum.textContent = "caption (imported F3 CAPTION, verbatim from the bundle)";
    det.appendChild(sum);
    var p = document.createElement("p");
    p.id = "v1-caption";
    p.textContent = b.caption;
    det.appendChild(p);
    strip.appendChild(det);
  }

  // ---- controls ----
  function stepperAxes() {
    // the five lattice axes drive scenario selection; radial_profile is
    // the fixed flood-only axis (R2)
    return manifest.axes.filter(function (a) { return a.id !== "radial_profile"; });
  }

  function buildSteppers() {
    var host = els.steppers;
    host.innerHTML = "";
    stepperAxes().forEach(function (axis, axisPos) {
      var fs = document.createElement("fieldset");
      fs.className = "ctl";
      var leg = document.createElement("legend");
      leg.textContent = axis.id + (axis.unit ? " (" + axis.unit + ")" : "");
      fs.appendChild(leg);

      var row = document.createElement("div");
      row.className = "stepper";
      var prev = document.createElement("button");
      prev.type = "button";
      prev.textContent = "‹";
      var val = document.createElement("span");
      val.className = "value";
      var next = document.createElement("button");
      next.type = "button";
      next.textContent = "›";
      row.appendChild(prev); row.appendChild(val); row.appendChild(next);
      fs.appendChild(row);

      var chips = document.createElement("div");
      chips.className = "flagchips";
      fs.appendChild(chips);

      var src = document.createElement("div");
      src.className = "source";
      src.textContent = "source: " + axis.source;
      fs.appendChild(src);

      function refresh() {
        var i = state.axes[axisPos];
        val.textContent = axis.labels[i];
        prev.disabled = i === 0;
        next.disabled = i === axis.labels.length - 1;
        chips.innerHTML = "";
        (axis.flags[i] || []).forEach(function (flag) {
          var c = document.createElement("span");
          c.className = "flagchip";
          c.textContent = flag; // verbatim manifest token
          chips.appendChild(c);
        });
      }
      prev.addEventListener("click", function () {
        if (state.axes[axisPos] > 0) {
          state.axes[axisPos] -= 1;
          refresh();
          loadAndRender();
        }
      });
      next.addEventListener("click", function () {
        if (state.axes[axisPos] < axis.labels.length - 1) {
          state.axes[axisPos] += 1;
          refresh();
          loadAndRender();
        }
      });
      refresh();
      axis._refresh = refresh;
      host.appendChild(fs);
    });

    // fixed radial-profile axis (flood-only, R2 — reserved slots unpopulated)
    var prof = manifest.axes.filter(function (a) {
      return a.id === "radial_profile";
    })[0];
    if (prof) {
      var fs = document.createElement("fieldset");
      fs.className = "ctl";
      var leg = document.createElement("legend");
      leg.textContent = prof.id;
      fs.appendChild(leg);
      var row = document.createElement("div");
      row.className = "stepper";
      var val = document.createElement("span");
      val.className = "value";
      val.textContent = prof.labels[0];
      row.appendChild(val);
      fs.appendChild(row);
      var chips = document.createElement("div");
      chips.className = "flagchips";
      (prof.flags[0] || []).forEach(function (flag) {
        var c = document.createElement("span");
        c.className = "flagchip";
        c.textContent = flag;
        chips.appendChild(c);
      });
      fs.appendChild(chips);
      var src = document.createElement("div");
      src.className = "source";
      src.textContent = "source: " + prof.source +
        (prof.reserved_slots && prof.reserved_slots.length
          ? " · reserved slots (unpopulated): " + prof.reserved_slots.join(", ")
          : "");
      fs.appendChild(src);
      els.steppers.appendChild(fs);
    }
  }

  function updateSliders() {
    var pMw = state.pW * 1e3;
    els.pSlider.max = String(shared.p_display_max_w * 1e3);
    els.pSlider.value = String(pMw);
    els.pReadout.textContent = fmt(pMw, 1) + " mW";
    els.pNote.textContent = "P_ref = " + fmt(shared.p_ref_w * 1e3, 0) +
      " mW (ILLUSTRATIVE); display range 0–" +
      fmt(shared.p_display_max_w * 1e3, 0) +
      " mW is a stated display choice (viz/PLAN.md §4).";

    var enabled = !!(current && current.field);
    els.nSlider.disabled = !enabled;
    els.pSlider.disabled = !enabled;
    if (!enabled) return;
    els.nSlider.max = String(current.nKept);
    if (state.nModes > current.nKept) state.nModes = current.nKept;
    els.nSlider.value = String(state.nModes);
    els.nReadout.textContent = state.nModes + " / " + current.nKept;
    var note = "slider caps at n_kept = " + current.nKept +
      " (recorded truncation; summed dropped-tail bound " +
      fmtSci(current.bundle.payload.truncation_bound_rel) + ").";
    els.nNote.textContent = note;
  }

  // ---- hover readout (reads the reconstructed array only) ----
  function onHover(ev) {
    if (!current || !current.field) return;
    var rect = els.canvas.getBoundingClientRect();
    var x = (ev.clientX - rect.left) * (W / rect.width);
    var y = (ev.clientY - rect.top) * (H / rect.height);
    if (x < ML || x > ML + PW || y < MT || y > MT + PH) {
      hoverDefault();
      return;
    }
    var rMax = manifest._rMm[NR - 1];
    var zMax = manifest._zMm[NZ - 1];
    var rMm = ((x - ML) / PW) * rMax;
    var zMm = ((y - MT) / PH) * zMax;
    var j = Math.round(((x - ML) / PW) * (NR - 1));
    var i = Math.round(((y - MT) / PH) * (NZ - 1));
    var v = current.field[i * NR + j] * current.scale;
    els.plotStatus.textContent = "r = " + fmt(rMm, 2) + " mm, z = " +
      fmt(zMm, 2) + " mm: ΔT = " + fmt(v, 2) +
      " K (nearest grid node)";
  }

  function hoverDefault() {
    if (!current || !current.field) return;
    els.plotStatus.textContent = "colour scale: ΔT " + fmt(current.vmin, 2) +
      " – " + fmt(current.vmax, 2) + " K (min–max of the displayed field, " +
      "exported magma LUT)";
  }

  // ---- scenario loading ----
  function loadAndRender() {
    var row = rowByAxes[state.axes.join(",")];
    var token = ++loadToken;
    if (!row) {
      paintDisabled("no manifest row for axes " + state.axes.join(","));
      return;
    }
    if (row.invalid) {
      current = null;
      els.invalid.hidden = false;
      els.invalid.innerHTML = "";
      var strong = document.createElement("strong");
      strong.textContent = "Structurally invalid cell (recorded in the manifest): ";
      els.invalid.appendChild(strong);
      els.invalid.appendChild(document.createTextNode(row.invalid));
      paintDisabled(row.invalid);
      updateSliders();
      els.readouts.innerHTML = "";
      els.energy.innerHTML = "";
      els.energyNote.textContent = "";
      updateFlagStrip();
      return;
    }
    els.invalid.hidden = true;
    els.plotStatus.textContent = "loading scenario " + row.id + " …";
    Promise.all([
      window.VIZ.data.getBundle("scenario/" + row.id),
      window.VIZ.data.getBundle("bases/" + row.basis_id)
    ]).then(function (bundles) {
      if (token !== loadToken) return; // stale (user stepped again)
      var sb = bundles[0], bb = bundles[1];
      var theta = window.VIZ.data.decodeArray(sb.payload.theta_k);
      var basis = window.VIZ.data.decodeArray(bb.payload.radial_basis);
      current = {
        row: row,
        bundle: sb,
        theta: theta.data,
        basis: basis.data,
        nKept: sb.payload.n_kept,
        field: null,
        vmin: 0, vmax: 0, scale: 1
      };
      if (state.nModes === null || state.nModes > current.nKept) {
        state.nModes = current.nKept;
      }
      rerender();
      updateSliders();
      updateFlagStrip();
    }).catch(function (err) {
      if (token !== loadToken) return;
      els.plotStatus.textContent = "load failed: " + err.message;
    });
  }

  function rerender() {
    if (!current) return;
    current.field = reconstruct(current.theta, current.basis, state.nModes);
    paint();
    updateReadouts();
    hoverDefault();
  }

  // ---- init (the only export) ----
  function init(indexBundle) {
    manifest = indexBundle.payload;
    shared = manifest.shared;
    lut = window.VIZ.data.decodeArray(shared.lut_rgb_u8).data;
    manifest._rMm = window.VIZ.data.decodeArray(shared.r_mm).data;
    manifest._zMm = window.VIZ.data.decodeArray(shared.z_mm).data;

    rowByAxes = Object.create(null);
    var defaultRow = null;
    manifest.scenarios.forEach(function (row) {
      rowByAxes[row.axes.join(",")] = row;
      if (row.id === shared.default_scenario_id) defaultRow = row;
    });
    if (!defaultRow) {
      throw new Error("default scenario missing from the manifest: " +
        shared.default_scenario_id);
    }

    els.canvas = document.getElementById("v1-canvas");
    els.plotStatus = document.getElementById("v1-plot-status");
    els.steppers = document.getElementById("v1-steppers");
    els.pSlider = document.getElementById("v1-p-slider");
    els.pReadout = document.getElementById("v1-p-readout");
    els.pNote = document.getElementById("v1-p-note");
    els.nSlider = document.getElementById("v1-n-slider");
    els.nReadout = document.getElementById("v1-n-readout");
    els.nNote = document.getElementById("v1-n-note");
    els.readouts = document.getElementById("v1-readouts");
    els.energy = document.getElementById("v1-energy");
    els.energyNote = document.getElementById("v1-energy-note");
    els.flagstrip = document.getElementById("v1-flagstrip");

    els.invalid = document.createElement("div");
    els.invalid.id = "v1-invalid";
    els.invalid.hidden = true;
    els.plotStatus.parentNode.appendChild(els.invalid);

    state.axes = defaultRow.axes.slice();
    state.pW = shared.p_ref_w;
    state.nModes = null;

    buildSteppers();
    updateSliders();

    els.pSlider.addEventListener("input", function () {
      state.pW = Number(els.pSlider.value) / 1e3;
      els.pReadout.textContent = fmt(Number(els.pSlider.value), 1) + " mW";
      if (current && current.field) {
        paint();
        updateReadouts();
        hoverDefault();
      }
    });
    els.nSlider.addEventListener("input", function () {
      state.nModes = parseInt(els.nSlider.value, 10);
      els.nReadout.textContent = state.nModes + " / " +
        (current ? current.nKept : "?");
      rerender();
    });
    els.canvas.addEventListener("mousemove", onHover);
    els.canvas.addEventListener("mouseleave", hoverDefault);

    loadAndRender();
  }

  window.VIZ = window.VIZ || {};
  window.VIZ.v1 = { init: init };
})();
