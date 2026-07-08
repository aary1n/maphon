"""SPEC §7.T7 — linearised radiative loss for the layered model's Robin top.

Radiation balance in the low-k regime (Oxborrow-verbal, 2026-07-06; a
check against the existing model, not a rebuild): in poor thermal
conductors the radiative boundary term stops being negligible vs the
conductive term sooner than good-conductor intuition suggests. This
module is the §7.T7 "first implementation slot": the standard linearised
radiative coefficient

    h_rad = 4 ε σ T_amb³

composed ADDITIVELY with the convective coefficient into the switchable
Robin `h_top` of `layered.py` (h_eff = h_conv + h_rad), so the
leading-order check reuses the §7.T4-convection sensitivity machinery.
The solver is untouched: `layered.py` keeps taking a single scalar
`h_top`, ε never enters solver code (it lives in
`cavity.provenance.constants.EMISSIVITY_PTP`), and ε = 0 reproduces the
prior convective-only / insulated-top results exactly.

Design decisions (ratified internally 2026-07-07; flagged in SPEC §7.T7
as planning assumptions pending Oxborrow — the ε band itself was
ratified as-is, Oxborrow-verbal 2026-07-08; the two decisions below
remain pending):

- ADDITIVE composition. Convection and radiation are parallel loss paths
  from the same surface, and the model's convective ambient and the
  radiative surroundings are both the bath (layered.py convention:
  "ambient at bath temperature"), so the linearised fluxes share one ΔT
  reference and add exactly:
  q = h_conv·ΔT + εσ(T_s⁴ − T_amb⁴) ≈ (h_conv + 4εσT_amb³)·ΔT.
  The existing h_top usage already treated 5–20 W m⁻² K⁻¹ as the lumped
  "free convection + linearised radiation" scale; this module factorises
  that lump into named parts.

- FIXED-AMBIENT T³ (not surface T). Evaluating h_rad at T_amb keeps the
  coefficient constant, so the Robin boundary condition stays linear and
  the Hankel/transfer-matrix solution — and every §8-discipline
  closed-form anchor — remains exactly valid. Surface-T evaluation makes
  the BC nonlinear (fixed-point iteration, no closed anchors); that is
  the deferred upgrade path, reachable through `h_rad_exact_secant`.

Linearisation validity (§7.T7's "where the linearisation itself fails"):
h_rad = 4εσT_amb³ is the first-order expansion of the exact secant
coefficient εσ(T_s⁴ − T_amb⁴)/(T_s − T_amb) about T_amb; the exact/linear
ratio is (T_s + T_a)(T_s² + T_a²)/(4T_a³). At T_amb = 300 K the linear
form UNDER-reads the exact radiative loss by 5.1% at ΔT = 10 K and
16.0% at ΔT = 30 K — spanning the "several tens of Celsius" inference
(SPEC §11 item 5, ~13–30 K). Because h_rad itself moves the rig-stack
ΔT by only ~0.2% at the §7.T5 named points (≲3% worst-case wide-spot
low-k plate; scaled from the h = 20 W m⁻² K⁻¹ sensitivity in
thermal/reports/identifiability_3a.md), the compounded linearisation
error is negligible for the calibration geometry. Both statements are
pinned in tests/test_thermal_radiation.py.

Magnitude anchor: 4σT³ = 6.12 W m⁻² K⁻¹ at 300 K and ε = 1 (the "~6" of
SPEC §7.T7); over the §6T emissivity band 0.80–0.95 this is
h_rad ≈ 4.9–5.8 W m⁻² K⁻¹ — comparable to free convection as a
coefficient, a correction to the conduction-dominated transport.
"""

from __future__ import annotations

from scipy.constants import Stefan_Boltzmann as _SIGMA_SB


def _check_epsilon_and_ambient(epsilon: float, t_ambient_k: float) -> None:
    if not 0.0 <= epsilon <= 1.0:
        raise ValueError("emissivity must lie in [0, 1]")
    if not t_ambient_k > 0.0:
        raise ValueError("ambient temperature must be positive (kelvin)")


def h_rad_linearized(epsilon: float, t_ambient_k: float) -> float:
    """Linearised radiative coefficient h_rad = 4εσT_amb³ (W m⁻² K⁻¹).

    σ is scipy.constants.Stefan_Boltzmann (CODATA). Fixed-ambient
    evaluation by design — see the module docstring for the validity
    bound and the exact-secant upgrade path. ε = 0 returns exactly 0.0
    (the off switch: prior h_top behaviour reproduces bit-for-bit).
    """
    _check_epsilon_and_ambient(epsilon, t_ambient_k)
    return 4.0 * epsilon * _SIGMA_SB * t_ambient_k**3


def h_rad_exact_secant(
    epsilon: float, t_surface_k: float, t_ambient_k: float
) -> float:
    """Exact radiative secant coefficient εσ(T_s⁴ − T_a⁴)/(T_s − T_a).

    Evaluated in the factored form εσ(T_s + T_a)(T_s² + T_a²), which is
    singularity-free: at T_s = T_a it reduces algebraically to 4εσT_a³,
    the linearised coefficient. This is the nonlinear upgrade path
    (fixed-point iteration on T_s) and the yardstick the linearisation
    error is measured against in tests/test_thermal_radiation.py.
    """
    _check_epsilon_and_ambient(epsilon, t_ambient_k)
    if not t_surface_k > 0.0:
        raise ValueError("surface temperature must be positive (kelvin)")
    return (
        epsilon
        * _SIGMA_SB
        * (t_surface_k + t_ambient_k)
        * (t_surface_k**2 + t_ambient_k**2)
    )


def h_top_with_radiation(
    h_conv: float, epsilon: float, t_ambient_k: float
) -> float:
    """Composed Robin coefficient h_eff = h_conv + 4εσT_amb³ (W m⁻² K⁻¹).

    The ratified additive composition (module docstring): pass the result
    as `h_top` to the `layered.py` solvers. ε = 0 returns h_conv exactly.
    NOTE `volumetric_base_power` requires h_top = 0 (its energy anchor
    assumes all power exits the base) — do not feed it a composed h_eff.
    """
    if h_conv < 0.0:
        raise ValueError("convective coefficient must be non-negative")
    return h_conv + h_rad_linearized(epsilon, t_ambient_k)
