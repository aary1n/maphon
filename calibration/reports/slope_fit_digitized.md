# T3 — digitized ODMR slope fits (Cowley-Semple 2026-07-14 dataset)

**Provenance: graph-digitized-provisional; superseded_by_raw_data=True** — re-fit from raw traces when they land.
Error model: uniform ±0.05 MHz per point (0.1 MHz plot
quantization); parameter errors are floor-propagated, not residual-scaled.

| sample | n | slope (MHz/mW) | χ²/dof |
|---|---|---|---|
| d14 | 4 | -0.1000 ± 0.0062 | 2.77/2 = 1.39 |
| h14 | 6 | -0.0745 ± 0.0057 | 14.67/4 = 3.67 |

**Slope ratio d14/h14 = 1.343 ± 0.132** (first-order propagation).

## h14 nonlinearity check (single step, 10.16 → 12.33 mW)

- observed step: -0.30 MHz
- linear prediction: -0.162 MHz
- excess: -0.138 MHz at σ_step = 0.072 MHz ⇒ z = -1.93
- verdict: the step **does NOT exceed** the ±0.05 MHz error floor at 2σ. The z-score neglects the step/fit correlation (approximate); the per-sample χ²/dof above is the primary lack-of-fit statistic. A 0.1 MHz-quantized plot can manufacture steps of this size — treat as provisional until raw traces land.
