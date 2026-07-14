# T5 — absolute fits: η_abs·R_int per sample (observable-a feed)

**Provenance: graph-digitized-provisional; superseded_by_raw_data=True**

df_spin/dT: provenance.DF_SPIN_DT (raw-data re-grade 2026-07-07): point -109 kHz/K, band [-120, -64] kHz/K. Prompt band '-50 to -108 kHz/K' overruled as stale (ratification condition 3, 2026-07-14).

| sample | slope (Hz/W) | η_abs·R_int point (K/W) | feasible band (K/W) | probe-inferred ΔT at max trace power, point [band] (K) | sweep feasible (η_abs ≤ 1) | caveat |
|---|---|---|---|---|---|---|
| d14 | 1e+08 ± 6.2e+06 | 917 | [781, 1659] | 13.2 [12.0, 22.5] | 98% | deuteration-transfer caveat |
| h14 | 7.45e+07 ± 5.7e+06 | 683 | [573, 1252] | 9.8 [8.9, 16.7] | 99% | clean |

Band composition: coefficient-band envelope (×1.875 across the §6T band)
evaluated at slope ∓1σ — the coefficient dominates the slope error.

The ΔT column is the PROBE-INFERRED heating at the trace maximum
(|slope|·P_max/|df_dt| — the triplet-thermometer reading, no absorption
assumption enters), point at the −109 kHz/K coefficient with the
bracketed band over the full DF_SPIN_DT band [−120, −64] kHz/K at point
slope: band-edge consistent with the 'several tens of K' class of
Oxborrow's in-thread inference — reproduced at order of magnitude, not
tuned to (12.0–22.5 K d14 / 8.9–16.7 K h14 at max trace power).

## T4 verdict carried into the feed: **geometry-sufficient**

(measured d14/h14 ratio 1.343 ± 0.132; see ratio_test_digitized.md)

Deuteration asymmetry: h14 is the CLEAN absolute fit (protonated, matches
the Singh crystal); d14 carries the deuteration-transfer caveat in full.

Machine-readable feed: observable_a_feed.json (same directory).
