# W2 — Wu-anchor acceptance windows (drafted 2026-07-19; RATIFIED as planning choices, revisable at first solve)

Scope: the acceptance windows for validating the re-based model against
`TARGETS.wu_ring` (Wu 2020 + PRL 127 SM; k = 1 stated). W1 (the Phase 1b
window precedent) governs style. No gate row binds `wu_ring` until the
first W2-passing solve creates the Wu anchor record.

## Convention finding (the precondition — the 225/360 lesson)

The SM's "magnetic mode volume ≈ 0.32 cm³" is printed without a formula.
Its convention is INFERRED from its role: SM Eq. S5 (Einstein B
coefficient, B = μ₀γ²hf·T₂⟨σ²⟩/2V_mode) and Wu 2020's g_s =
γ√(μ₀hf/2V_mode) are the Breeze-family per-spin forms — V_mode
normalised at the field the spins see. That is `v_mode_local_m3`
(`extraction/modal.py`: ∫|H|²dV / max_gain(|H|²)), not
`v_mode_global_m3`. Grade of the identification: INFERENCE from printed
equations, not a stated convention — hence V_mode is a DIAGNOSTIC row
below, not a gate.

Build-specific consistency check, free at solve time: the SM places the
illuminated prism on the equatorial circle "where the magnitude of the
TE01δ mode's a.c. magnetic flux density, B, is maximum" (B ≥ 90 % of max
throughout). The gain region therefore contains the global |H|² maximum,
forcing v_mode_local ≈ v_mode_global for THIS build. Failure of that
near-equality indicts the gain mask or the field solution before any
comparison to 0.32 cm³ is meaningful.

Consistency note (recorded, not load-bearing): Q₀ = 7200 with all loss
dielectric implies effective tanδ = 1/7200 = 1.39e-4 = the re-derived
`TOL.tan_delta_max`; the canonical tanδ = 1.1e-4 gives Q_diel ≈
1/(p_e·tanδ) ≈ 9.1e3, leaving a plausible wall share. Anchor, band, and
loss split are mutually consistent pre-solve.

## Windows (planning choices, user-ratified 2026-07-19)

| Row | Quantity | Target | Window | Kind |
|---|---|---|---|---|
| W2.1 | f (Phase 1b Wu model, canonical nominals) | 1.4495 GHz | ±1.5 % | GATE. Residual sign recorded; a residual reachable inside the εr band [312, 318] (~±1 % on f) is non-alarming and must be stated with the εr sensitivity. |
| W2.2 | Q₀ | 7200 | ±25 % | GATE. The tanδ band [1.0, 1.4]e-4 alone spans ~±17 % of Q_diel; tighter would gate on an unvalidated loss split. |
| W2.3 | v_mode_local_m3 | 0.32 cm³ | report, no gate | DIAGNOSTIC (convention inferred, above). |
| W2.4 | v_mode_local / v_mode_global | ≈ 1 | within 10 % | GATE (build-specific, from the convention finding). |

Preconditions: solve on the Phase 1b Wu model — crystal present (εr =
3.0, Q11 planning grade) and spacer flag ON — matching what Wu's own
COMSOL simulated (Wu 2020 Fig. 6: STO + crystal + support highlighted).
Q13 must be resolved (no silent height selection) before the W2 solve.

First W2-passing solve creates the Wu anchor record and the Wu-build
sweep centre (design-doc 2026-07-19 addendum).
