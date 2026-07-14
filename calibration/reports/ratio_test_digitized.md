# T4 — ratio discrimination test (d14/h14, Cowley-Semple 2026-07-14)

**VERDICT: GEOMETRY-SUFFICIENT**

- measured slope ratio (T3, graph-digitized-provisional; superseded_by_raw_data=True): 1.343 ± 0.132
- model ratio band over the shared-parameter sweep: [0.584, 2.329] (8775 (shared θ, t_d14, t_h14) points)
- fraction of swept points inside measured ± 2σ: 53.9%
- discriminating power: LOW — the model band brackets the measured ratio
  from BOTH sides; the geometry-sufficient verdict holds under the
  pre-fixed criterion, but an intrinsic deuteration effect is
  NOT REQUIRED and NOT EXCLUDED by this dataset.

Shared axes (cancel by construction): η_abs and df/dT — VALID ONLY under
near-total absorption in both crystals (l_abs ≪ t; zone-refining caveat
means per-growth [Pc] differences land in the intrinsic branch). Interface
parameters k, h_sub, spot, radius mapping SHARED; thickness per-sample free.

## Verdict by radius-mapping factor (COMSOL contingency input)

- factor 0.5000: geometry-sufficient
- factor 0.5642: geometry-sufficient
- factor 0.7071: geometry-sufficient

COMSOL contingency trigger (indeterminate AND edge-flip): **not fired** — licence discipline holds.

## η_abs cancellation condition (explicit dependency)

The η_abs cancellation above is conditioned on NEAR-TOTAL absorption
(l_abs ≪ t) in both crystals. The T5 absolute fits put η_abs at the
nominal config at 0.168 (d14) / 0.160 (h14) — compatible with that
condition ONLY IF the missing ~83–84% is upstream
delivery/reflection loss, i.e. the legend powers were measured upstream
of the sample (invented assumption 4; power-measurement plane =
open Angus ask). If absorption is genuinely partial, η_abs becomes
thickness-dependent — thickness is per-sample FREE in this sweep — and
the cancellation weakens.

## Residual confound: per-sample glue contact (does NOT cancel)

φ = h_sub(d14)/h_sub(h14) required to reproduce the measured ratio at
MATCHED geometry (equal mid-band thickness/k/spot/mapping):

- h_sub(h14) = 1e+02 W/m²/K → φ = 1.49
- h_sub(h14) = 1e+03 W/m²/K → φ = 0.53
- h_sub(h14) = 1e+04 W/m²/K → φ = 0.0743
- h_sub(h14) = 1e+05 W/m²/K → φ = 0.00778

Interpretation: a φ of this size is an ALTERNATIVE explanation the ratio
test cannot exclude — the d14 crystal merely being differently glued
(worse or better depending on the operating h_sub).

## Scope of the intrinsic branch (deliberately not decomposed)

If the verdict is intrinsic-effect-required, this dataset cannot separate
k_d14 ≠ k_h14 (isotope effect on phonon conduction) from
df/dT_d14 ≠ df/dT_h14 (deuterated spin coefficient) — both are 'intrinsic'.
This is the quantitative form of Angus's 'can you include whether it's
deuterated' question; a geometry-sufficient verdict means the data does
not require a deuteration effect to be explained.
