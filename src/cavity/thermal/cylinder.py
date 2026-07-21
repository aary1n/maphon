"""SPEC §7T — finite-cylinder Bessel/Robin conduction: the maser-crystal anchor.

The second of §7T's two evaluation geometries (§7.T1 geometry split): the
pentacene:p-terphenyl crystal cylinder of the maser (SPEC §5b/§6, `CRYSTAL`:
3 mm diameter × 8 mm), heated volumetrically by the pump and cooled through
its surfaces. This is the transport core that §7.T5 observable (b) — the
model-only maser-geometry prediction — and the §7.T7 across-range radiation
competition report will consume (SPEC §10 module shape). The rig geometry has
its own anchor (`layered.py`, Gaussian-spot/Hankel); ΔT numbers do not
transfer between the two geometries — the transport model does (§7.T5).

Geometry and conventions
------------------------
Solid cylinder 0 ≤ r ≤ R, 0 ≤ z ≤ L; z increases DOWNWARD from the
illuminated face z = 0 (same convention as `layered.py`). ΔT(r, z) is the
steady rise above bath; the convective/radiative ambient is the bath
everywhere (`layered.py` / `radiation.py` convention). ΔT is exactly linear
in the pump power P. Steady state only — no transients, no heat capacity.

Governing PDE (steady, axisymmetric, anisotropic):

    k_r · (1/r) ∂/∂r ( r ∂ΔT/∂r ) + k_z ∂²ΔT/∂z² + q̇(r, z) = 0

Boundary conditions — each surface independently Robin (h ≥ 0, ambient =
bath) or exact Dirichlet (imposed constant ΔT = dt_k, default 0):

    side  r = R:  −k_r ∂ΔT/∂r = h_side · ΔT        (or ΔT = 0)
    top   z = 0:  +k_z ∂ΔT/∂z = h_top  · ΔT − q_s(r)
    base  z = L:  −k_z ∂ΔT/∂z = h_base · ΔT        (or ΔT = dt_k)

(q_s ≠ 0 only for the surface-flux source form; a surface-flux source with a
Dirichlet top is rejected — a Dirichlet surface cannot carry prescribed flux.)

Driven mode (S-ladder S0/S1 — SPEC 2026-07-16 outcome 5, added 2026-07-19):
`solve(spec, source=None)` with nonzero `dt_k` on the top/base Dirichlet
surfaces solves the SOURCE-FREE problem driven by imposed end temperatures,
in kelvin (Θ = 1). The constant drive expands over the active radial basis
(uₙ = J₁(xₙ)/(xₙ·N̂ₙ); u₀ = 1) into per-mode homogeneous end-value problems
through the same scaled basis and 2×2 end solve. Bi_s = 0 (S0) is EXACT:
the positive-mode drive coefficients vanish identically (J₁ at its own
zeros), the constant mode carries the closed 1-D linear profile with zero
truncation error — the ladder's analytic anchor. Dirichlet-side S1 carries
the classic sharp-corner caveat: the imposed value is discontinuous along
the top rim, so the TOTAL top inflow is LOG-DIVERGENT. Normalisation,
stated (2026-07-19 adversarial-review finding — the dimensionless form
alone was ambiguous): per mode, in WATTS,

    |p_top,n| ≈ [2πR²·k_z·ΔT_hot/L]·(2Λ/xₙ) = 4πR·√(k_r·k_z)·ΔT_hot/xₙ

with Λ = (L/R)·√(k_r/k_z) as defined below (NOT its reciprocal), so each
N → 2N mode-doubling adds ≈ 4·R·√(k_r·k_z)·ΔT_hot·ln 2 watts (Σ 1/xₙ per
doubling → ln2/π; approached from below at finite N — absolutely pinned
in tests/test_thermal_cylinder.py). `boundary_power_w()` entries grow
~log N there and a total conductance is not a well-posed observable of
the sharp problem; interior and integrated observables converge
(Gibbs-class, ~1/N² on integrated scalars). A source and a nonzero drive
in one call are rejected — superpose two solves. Driven SIDE values are
rejected (no ladder scenario needs them).

Radial eigenproblem
-------------------
Separation of variables gives J₀(λₙr) with xₙ = λₙR the roots of the Robin
transcendental equation

    x J₁(x) = Bi_s J₀(x),      Bi_s = h_side R / k_r.

- Dirichlet side: xₙ = j₀,ₙ (zeros of J₀) exactly — no root-finding.
- Bi_s = 0 (insulated side): xₙ = j₁,ₙ (zeros of J₁) PLUS the constant mode
  x₀ = 0, which carries the 1-D axial physics.
- Bi_s ∈ (0, ∞): exactly one root per bracket (j₁,ₙ₋₁, j₀,ₙ) with j₁,₀ := 0
  (the bracket ends have opposite signs: g(j₁,ₙ₋₁) = −Bi·J₀(j₁,ₙ₋₁) and
  g(j₀,ₙ) = j₀,ₙ·J₁(j₀,ₙ) alternate); refined by brentq at ~1e-14 xtol.
- Norm, exact for any λ (standard indefinite integral):
  Nₙ = ∫₀ᴿ J₀(λₙr)² r dr = (R²/2)[J₀(xₙ)² + J₁(xₙ)²];  N₀ = R²/2.

Source term
-----------
q̇(r, z) = P·f(r)·g(z) with 2π∫₀ᴿ f r dr = 1 and ∫₀ᴸ g dz = 1, so the
deposited power is exactly P. Axial profiles g(z):

1. 'beer_lambert' — g(z) = e^(−z/l_abs) / [l_abs·(1 − e^(−L/l_abs))]:
   truncated at L and RENORMALISED — the transmitted fraction e^(−L/l_abs)
   is folded back onto the crystal so absorbed power is exactly P, the same
   convention as `layered.volumetric_depth_pdf` (keeps the energy anchor
   exact and the two anchors aligned; the alternative — transmit the
   remainder — is rejected for consistency).
2. 'uniform' — g = 1/L (the l_abs ≫ L limit).
3. 'surface' — exact l_abs → 0 limit: deposition enters the top BC as
   q_s(r) = P·f(r) (makes the layered cross-check solver-exact and gives the
   l_abs → 0 regression bridge).
4. 'band' (S-ladder S4, 2026-07-19) — g = 1/(z_hi − z_lo) on
   [band_lo_m, band_hi_m] ⊆ [0, L], zero outside: the beam-height slab of
   the side-fire geometry (NOT exponential-from-top). Per-mode particular
   solution in closed form via the free-space Green kernel
   (f̂ĝ/2mₙ)·∫ₐᵇ mₙ·e^(−mₙ|ζ−s|) ds — piecewise exponentials with
   non-positive exponents only (overflow-free; no confluent hazard);
   band = [0, L] reproduces 'uniform' identically (regression bridge).

Radial profiles f(r): 'flood' 1/(πR²) (default — face-scale illumination is
the regime this anchor targets), 'disc' 1/(πa²)·1{r<a}, 'gaussian'
∝ e^(−2r²/w²) truncated at R and renormalised, and 'side_chord'
(S-ladder S4, 2026-07-19) — the azimuthally-averaged (m = 0) Beer-Lambert
chord deposition of a horizontal side beam of width `beam_width_m`, with
`l_abs_m` acting ALONG THE CHORD (math.inf = the bleached optically-thin
limit; profile construction, kink-split graded quadrature, and the
closed-form thin limit live in `side_deposition.py`). Truncated-
renormalised like the rest — P is exactly the ABSORBED power. side_chord
combines only with the 'band'/'uniform' axial forms (chord + axial
Beer-Lambert would claim two absorption directions at once).

Projection and per-mode axial solution
--------------------------------------
q̇ₙ(z) = P·fₙ·g(z) with fₙ = (1/Nₙ)∫₀ᴿ f(r) J₀(λₙr) r dr — closed form for
flood (fₙ = J₁(xₙ)/(π xₙ Nₙ · R⁻²·…), see `_radial_projection`) and disc
(∝ J₁(λₙa)); fixed Gauss-Legendre quadrature for the Gaussian (smooth
integrand at the mode counts involved). With ΔT = Σₙ θₙ(z) J₀(λₙr), each
mode solves the constant-coefficient two-point BVP

    θₙ'' − μₙ² θₙ = −(P fₙ / k_z) · g(z),      μₙ = λₙ · √(k_r / k_z),

IN CLOSED FORM — the axial direction carries NO truncation error, so
near-surface deposition (l_abs ≪ L) costs nothing (unlike a double
eigen-series). The particular solution is elementary for all three g forms;
for Beer-Lambert its denominator is evaluated in the FACTORED form
(μₙ − 1/l)(μₙ + 1/l) — never the difference-of-squares (μₙ² − 1/l²), which
doubles the cancellation approaching the confluent switch — with a dedicated
confluent branch (z·e^(−z/l) form) taken when |μₙ·l_abs − 1| < 1e-6. The
homogeneous part uses the overflow-free scaled basis
A·e^(−μₙz) + B·e^(−μₙ(L−z)) (never cosh/sinh of a large argument); A, B come
from a 2×2 linear solve per mode against the end conditions. The Bi_s = 0
constant mode integrates θ₀'' = −(P f₀/k_z)·g directly (closed double
integral); a spec with ALL surfaces insulated is rejected — no steady state
exists.

Dimensionless formulation
-------------------------
Internal variables ρ = r/R, ζ = z/L; groups

    Bi_s = h_side·R/k_r,   Bi_t = h_top·L/k_z,   Bi_b = h_base·L/k_z,
    Λ = (L/R)·√(k_r/k_z)   (modal axial constant mₙ = xₙ·Λ in ζ units),
    ℓ = l_abs/L,   α = a/R,   ω = w/R,

temperature unit Θ = P·L/(π R² k_z) (the 1-D flood-slab scale). The API is
dimensional (m, W, W m⁻¹ K⁻¹ → K). Anisotropy k_r ≠ k_z is supported
NATIVELY and enters ONLY through Λ and the Biot definitions — equivalent to
the standard coordinate stretch z̃ = z·√(k_r/k_z) but without stretched-
geometry bookkeeping at the API; the isotropic default is k_z = k_r. (§6T
carries the K_PTP ~2× anisotropy as a band note; for observable (b) the
field SHAPE — the split between the base path ∝ k_z and the side path ∝ k_r
— moves with k_r/k_z at fixed band position, so band-folding cannot
represent it. The stretch-identity test anchors the wiring; the 2× value
stays a sensitivity knob, not a claim.)

Formulation provenance
----------------------
Textbook-standard finite-cylinder Robin separation of variables — Carslaw &
Jaeger, *Conduction of Heat in Solids*, 2nd ed., §7–8-class results; Özışık,
*Heat Conduction*, finite-cylinder eigenfunction tables. All forms above are
derived self-contained and asserted numerically against hand-derived limits
in tests/test_thermal_cylinder.py (mirroring `layered.py`'s practice).

Convergence and validity caveats
--------------------------------
- Series truncation: `n_modes` is explicit (default 64, counting the Bi_s = 0
  constant mode when present); `tail_estimate_rel(...)` reports the summed
  contribution of the last 3 modes relative to the running value of the
  requested scalar. No silent cap anywhere.
- Narrow radial sources (ω = w/R ≪ 1) are the genuinely slow regime: the
  mode count grows as N ∝ 17.2/(π·ω). That is the anchor's accuracy
  boundary — narrow spots are the layered/Hankel anchor's regime (§7.T1
  geometry split). Converges when paid for (the layered cross-check test
  runs one such case at N ≈ 300).
- Sub-disc sources (a < R) and flood-under-Dirichlet have Gibbs-slow
  POINTWISE convergence near r = R / r = a; interior points and integrated
  scalars (peak, volume average, boundary power) converge fast.
- Thin-disc aspect (L ≪ R): no instability; convergence stays set by radial
  source smoothness.
- No mode weighting: `volume_average_k` is explicitly UNWEIGHTED — the
  gain-region H-weighting of §7.T2 output 1 is the consumer's job.
- Crystal-only domain: the crystal→STO thermal path is NOT modelled; the
  side/base Robin h is exactly where a finite-conductance contact (gap
  conductance, §7.T6-style sapphire sink) enters later. (2026-07-16,
  Oxborrow-verbal: the crystal–STO interface is Vaseline-mediated, not
  an air gap — that contact, when exercised, is an EFFECTIVE
  Vaseline-mediated thermal contact conductance, potentially carrying
  both layer and interfacial resistance; see `provenance.Crystal`.)

SPEC-silent decisions (D1–D7, taken 2026-07-07 as parameterised planning
assumptions — flagged for Oxborrow ratification, §11 item-10 bundle;
D2's illumination geometry ruled 2026-07-08, see D2)
------------------------------------------------------------------------
D1  Mounting/contact: fully parameterised per-surface BCs (independent Robin
    h per surface, ambient = bath, exact Dirichlet option). NO hard-coded
    "physical" default is claimed — `CylinderSpec` requires all three BCs
    explicitly. The worked example uses Dirichlet base + Robin(h_conv+h_rad)
    side/top — Oxborrow's "substrate below at room temperature" framing —
    labelled a planning assumption.
D2  Pump entry: AXIAL illumination of the z = 0 end face, Beer-Lambert in
    depth (§7.T5 volumetric convention; §7.T7 rider (a)).
    SUPERVISOR-PREFERRED (Oxborrow-verbal, 2026-07-08 — upgraded from
    planning assumption): END-FIRE pumping is the preferred geometry for
    our maser, so axial illumination is the ruled default; adapt to
    side-fire only if the Glasgow rig requires it — whether it does is an
    Angus metadata question (SPEC §11 item 5 rider). Side-pumping —
    W20's invasive-LC pump geometry is SIDE-ON — is not axisymmetric about
    the cylinder axis and is outside this eigenbasis: EXCLUDED, a structural
    limitation of this anchor, not a parameter choice (unchanged by the
    ruling). (ANNOTATION 2026-07-19, S-ladder S4 — SPEC 2026-07-16
    outcome 5: the m = 0 AZIMUTHAL SMEAR of side-fire is now representable
    INSIDE this eigenbasis and BUILT — the 'side_chord' × 'band' source
    forms above; a structural LOWER bracket on gain-weighted heating, the
    verbatim systematic riding every S4 output
    (`report_s_ladder.S4_SYSTEMATIC`). The m > 0 azimuthally-localised
    content remains structurally outside: DEFERRED with a decision gate,
    eccentricity-route discipline. The original exclusion text above is
    preserved verbatim; its scope is now exactly the m > 0 remainder.)
D3  Radial beam profile: flood (default) / uniform sub-disc / truncated-
    renormalised Gaussian.
D4  Unabsorbed pump light: truncated-renormalised exponential (see source
    term above) — identical to `layered.volumetric_depth_pdf`.
D5  Radiative/convective ambient = bath for all surfaces.
D6  Anisotropy: native k_r ≠ k_z, isotropic default (see above).
D7  Crystal→STO path: not modelled; Robin-h hook stated above.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from scipy.optimize import brentq
from scipy.special import j0, j1, jn_zeros

from cavity.thermal.side_deposition import side_projection

_CONFLUENT_WINDOW = 1e-6  # |mₙ·ℓ − 1| below this → z·e^(−z/ℓ) confluent branch

_AXIAL_FORMS = ("beer_lambert", "uniform", "surface", "band")
_RADIAL_FORMS = ("flood", "disc", "gaussian", "side_chord")


@dataclass(frozen=True)
class SurfaceBC:
    """One surface's boundary condition: Robin (h ≥ 0, ambient = bath) or
    exact Dirichlet (imposed constant ΔT = dt_k, default 0). Robin h = 0 is
    an insulated surface. A nonzero dt_k (S-ladder driven mode, SPEC
    2026-07-16 outcome 5) is valid only on a Dirichlet surface — a Robin
    surface's ambient is the bath by convention (D5)."""

    kind: str
    h_w_m2_k: float = 0.0
    dt_k: float = 0.0

    def __post_init__(self) -> None:
        if self.kind not in ("robin", "dirichlet"):
            raise ValueError("SurfaceBC kind must be 'robin' or 'dirichlet'")
        if self.kind == "robin" and not self.h_w_m2_k >= 0.0:
            raise ValueError("Robin coefficient h must be non-negative")
        if self.kind == "dirichlet" and self.h_w_m2_k != 0.0:
            raise ValueError("a Dirichlet surface carries no h")
        if self.kind == "robin" and self.dt_k != 0.0:
            raise ValueError(
                "an imposed dt_k is valid only on a Dirichlet surface "
                "(Robin ambient = bath, D5)"
            )

    @classmethod
    def robin(cls, h_w_m2_k: float) -> "SurfaceBC":
        return cls(kind="robin", h_w_m2_k=float(h_w_m2_k))

    @classmethod
    def dirichlet(cls, dt_k: float = 0.0) -> "SurfaceBC":
        return cls(kind="dirichlet", dt_k=float(dt_k))

    @property
    def is_dirichlet(self) -> bool:
        return self.kind == "dirichlet"


@dataclass(frozen=True)
class CylinderSpec:
    """Cylinder geometry, conductivities, and per-surface BCs (D1: all three
    BCs are REQUIRED — no physical default is claimed). `k_z_w_m_k = None`
    is the isotropic default k_z = k_r (D6). Rejects the all-insulated spec
    (Robin h = 0 on every surface): no steady state exists."""

    radius_m: float
    height_m: float
    k_r_w_m_k: float
    side: SurfaceBC
    top: SurfaceBC
    base: SurfaceBC
    k_z_w_m_k: float | None = None

    def __post_init__(self) -> None:
        if not self.radius_m > 0.0:
            raise ValueError("radius must be positive")
        if not self.height_m > 0.0:
            raise ValueError("height must be positive")
        if not self.k_r_w_m_k > 0.0:
            raise ValueError("k_r must be positive")
        if self.k_z_w_m_k is not None and not self.k_z_w_m_k > 0.0:
            raise ValueError("k_z must be positive")
        if all(
            (not bc.is_dirichlet) and bc.h_w_m2_k == 0.0
            for bc in (self.side, self.top, self.base)
        ):
            raise ValueError(
                "all surfaces insulated: no steady state exists for a heated cylinder"
            )

    @property
    def k_z(self) -> float:
        """Axial conductivity with the isotropic default resolved."""
        return self.k_r_w_m_k if self.k_z_w_m_k is None else self.k_z_w_m_k


@dataclass(frozen=True)
class PumpSource:
    """Separable pump deposition q̇ = P·f(r)·g(z), both factors normalised
    (module docstring: axial and radial forms, D2–D4 conventions)."""

    p_w: float
    axial_form: str
    radial_form: str = "flood"
    l_abs_m: float | None = None
    disc_radius_m: float | None = None
    gaussian_w_m: float | None = None
    band_lo_m: float | None = None
    band_hi_m: float | None = None
    beam_width_m: float | None = None

    def __post_init__(self) -> None:
        if not self.p_w > 0.0:
            raise ValueError("pump power must be positive")
        if self.axial_form not in _AXIAL_FORMS:
            raise ValueError(f"axial_form must be one of {_AXIAL_FORMS}")
        if self.radial_form not in _RADIAL_FORMS:
            raise ValueError(f"radial_form must be one of {_RADIAL_FORMS}")
        if self.radial_form == "side_chord":
            # chord absorption (radial plane) + axial Beer-Lambert would
            # claim two absorption directions at once — rejected
            if self.axial_form not in ("band", "uniform"):
                raise ValueError(
                    "side_chord combines only with the band or uniform "
                    "axial forms (chord + axial Beer-Lambert would claim "
                    "two absorption directions)"
                )
            if self.beam_width_m is None or not self.beam_width_m > 0.0:
                raise ValueError("side_chord needs a positive beam_width_m")
            if self.l_abs_m is None or not self.l_abs_m > 0.0:
                raise ValueError(
                    "side_chord needs a positive l_abs_m along the chord "
                    "(math.inf = the bleached optically-thin limit)"
                )
        elif self.beam_width_m is not None:
            raise ValueError("beam_width_m only applies to the side_chord form")
        if self.axial_form == "beer_lambert":
            if self.l_abs_m is None or not self.l_abs_m > 0.0:
                raise ValueError("beer_lambert needs a positive l_abs_m")
        elif self.l_abs_m is not None and self.radial_form != "side_chord":
            raise ValueError(
                "l_abs_m only applies to the beer_lambert or side_chord forms"
            )
        if self.axial_form == "band":
            if self.band_lo_m is None or self.band_hi_m is None:
                raise ValueError("band needs band_lo_m and band_hi_m")
            if not 0.0 <= self.band_lo_m < self.band_hi_m:
                raise ValueError("band needs 0 <= band_lo_m < band_hi_m")
        elif self.band_lo_m is not None or self.band_hi_m is not None:
            raise ValueError("band_lo_m/band_hi_m only apply to the band form")
        if self.radial_form == "disc":
            if self.disc_radius_m is None or not self.disc_radius_m > 0.0:
                raise ValueError("disc needs a positive disc_radius_m")
        elif self.disc_radius_m is not None:
            raise ValueError("disc_radius_m only applies to the disc form")
        if self.radial_form == "gaussian":
            if self.gaussian_w_m is None or not self.gaussian_w_m > 0.0:
                raise ValueError("gaussian needs a positive gaussian_w_m")
        elif self.gaussian_w_m is not None:
            raise ValueError("gaussian_w_m only applies to the gaussian form")


def robin_radial_eigenvalues(bi_side: float, n_modes: int) -> np.ndarray:
    """First `n_modes` POSITIVE roots xₙ of x·J₁(x) = Bi_s·J₀(x).

    Bracketing (module docstring): exactly one root in (j₁,ₙ₋₁, j₀,ₙ) with
    j₁,₀ := 0 for every Bi_s ∈ (0, ∞); brentq refinement at 1e-14 xtol.
    Bi_s → 0: x₁ → √(2·Bi_s) smoothly (the bracket (0, j₀,₁) stays valid,
    g(0⁺) = −Bi_s < 0). Bi_s = 0 returns the J₁ zeros exactly; the
    additional constant mode x₀ = 0 is carried by solve(), not here.
    Bi_s → ∞: roots → j₀,ₙ from below (the Dirichlet side is additionally
    available EXACTLY through `SurfaceBC.dirichlet()`, no root-finding).
    """
    if bi_side < 0.0:
        raise ValueError("side Biot number must be non-negative")
    if n_modes < 1:
        raise ValueError("need at least one mode")
    if bi_side == 0.0:
        return jn_zeros(1, n_modes)
    upper = jn_zeros(0, n_modes)
    lower = np.concatenate(([0.0], jn_zeros(1, n_modes - 1) if n_modes > 1 else []))

    def g(x: float) -> float:
        return x * j1(x) - bi_side * j0(x)

    return np.array(
        [brentq(g, lo, hi, xtol=1e-14) for lo, hi in zip(lower, upper)]
    )


def _radial_projection(
    source: PumpSource, x: np.ndarray, n_hat: np.ndarray, radius_m: float
) -> np.ndarray:
    """Dimensionless projections f̂ₙ = (1/N̂ₙ)∫₀¹ f̂(ρ) J₀(xₙρ) ρ dρ for the
    positive modes, with f̂(ρ) = πR²·f(Rρ) (so 2∫₀¹ f̂ ρ dρ = 1). The
    constant-mode projection is f̂₀ = 1 exactly, by normalisation."""
    if source.radial_form == "flood":
        return (j1(x) / x) / n_hat
    if source.radial_form == "disc":
        alpha = source.disc_radius_m / radius_m
        if alpha > 1.0:
            raise ValueError("disc radius exceeds the cylinder radius")
        return (j1(x * alpha) / (alpha * x)) / n_hat
    if source.radial_form == "side_chord":
        if source.beam_width_m > 2.0 * radius_m:
            raise ValueError("beam width exceeds the cylinder diameter")
        return side_projection(
            x,
            n_hat,
            source.beam_width_m / (2.0 * radius_m),
            source.l_abs_m / radius_m,
        )
    # gaussian: f̂(ρ) = Ĉ·e^(−2ρ²/ω²) on [0, 1], truncated-renormalised
    omega = source.gaussian_w_m / radius_m
    c_norm = 2.0 / (omega**2 * (-math.expm1(-2.0 / omega**2)))
    support = min(1.0, 4.5 * omega)  # e^(−2·4.5²) ≈ 2.5e-18: nothing beyond
    # fixed Gauss-Legendre; node count scaled to resolve J₀(x_max·ρ) on the
    # support (the integrand is smooth — no oscillation issue at these counts)
    n_nodes = max(64, int(0.5 * float(x[-1]) * support) + 40)
    nodes, weights = np.polynomial.legendre.leggauss(n_nodes)
    rho = 0.5 * support * (nodes + 1.0)
    wts = 0.5 * support * weights
    kern = np.exp(-2.0 * rho**2 / omega**2) * rho * wts  # (n_nodes,)
    proj = j0(np.outer(x, rho)) @ kern  # (n_modes,)
    return c_norm * proj / n_hat


class _AxialModes:
    """Closed-form axial solutions θ̂ₙ(ζ) for the positive modes:
    θ̂ₙ = part(ζ) + Aₙ·e^(−mₙζ) + Bₙ·e^(−mₙ(1−ζ)) in the overflow-free
    scaled basis. Vectorised over modes; all evaluations, end values,
    derivatives, and segment integrals are closed form."""

    def __init__(
        self,
        m: np.ndarray,
        f_hat: np.ndarray,
        source: PumpSource | None,
        ell: float | None,
        bi_top: float | None,
        bi_base: float | None,
        band: tuple[float, float] | None = None,
        top_drive: np.ndarray | None = None,
        base_drive: np.ndarray | None = None,
    ) -> None:
        # bi_top / bi_base: Biot numbers for Robin, None for Dirichlet.
        # top_drive / base_drive: imposed Dirichlet end VALUES per mode
        # (kelvin; the driven S-ladder mode) — homogeneous ODE, form 'none'.
        self.m = m
        self.f_hat = f_hat
        self.form = "none" if source is None else source.axial_form
        self.ell = ell
        self.band = band
        n = m.size
        # --- particular solution coefficients -----------------------------
        if self.form == "uniform":
            self._p_const = f_hat / m**2
        elif self.form == "band":
            # Green-kernel particular for ĝ = 1/(b−a) on [a, b] ⊂ [0, 1]:
            # θ̂_p = (f̂ĝ/2m²)·∫ₐᵇ m·e^(−m|ζ−s|) ds — piecewise elementary
            # exponentials with NON-POSITIVE exponents only (overflow-free;
            # no difference-of-squares denominators, no confluent hazard)
            g_hat = 1.0 / (band[1] - band[0])
            self._c2 = f_hat * g_hat / (2.0 * m**2)
            self._c1 = f_hat * g_hat / (2.0 * m)
        elif self.form == "beer_lambert":
            beta = 1.0 / ell
            c_hat = -math.expm1(-1.0 / ell)
            self._c_hat = c_hat
            self.confluent = np.abs(m * ell - 1.0) < _CONFLUENT_WINDOW
            # factored denominator (mₙ − 1/ℓ)(mₙ + 1/ℓ) — NEVER (mₙ² − 1/ℓ²)
            denom = (m - beta) * (m + beta)
            with np.errstate(divide="ignore", invalid="ignore"):
                d_coef = f_hat / (ell * c_hat * denom)
            self._d_coef = np.where(self.confluent, 0.0, d_coef)
            self._e_coef = np.where(self.confluent, f_hat / (2.0 * c_hat), 0.0)
        # surface: homogeneous ODE, particular ≡ 0

        p0, p0p = self._part_and_deriv(0.0)
        p1, p1p = self._part_and_deriv(1.0)
        self._p0, self._p1 = p0, p1
        q_s = f_hat if self.form == "surface" else np.zeros(n)
        c_top = np.zeros(n) if top_drive is None else top_drive
        c_base = np.zeros(n) if base_drive is None else base_drive
        e0 = np.exp(-m)
        self.e0 = e0
        # --- 2×2 end-condition solve (Cramer) ------------------------------
        if bi_top is None:  # Dirichlet top: θ̂ₙ(0) = c_top,ₙ (0 undriven)
            a11, a12, r1 = np.ones(n), e0, c_top - p0
        else:
            a11 = -(m + bi_top)
            a12 = e0 * (m - bi_top)
            r1 = -p0p + bi_top * p0 - q_s
        if bi_base is None:  # Dirichlet base: θ̂ₙ(1) = c_base,ₙ
            a21, a22, r2 = e0, np.ones(n), c_base - p1
        else:
            a21 = e0 * (m - bi_base)
            a22 = -(m + bi_base)
            r2 = p1p + bi_base * p1
        det = a11 * a22 - a12 * a21
        self.a_coef = (r1 * a22 - a12 * r2) / det
        self.b_coef = (a11 * r2 - r1 * a21) / det

    def _part_and_deriv(self, zeta: float) -> tuple[np.ndarray, np.ndarray]:
        """Particular solution and its ζ-derivative at a scalar ζ (per mode)."""
        if self.form in ("surface", "none"):
            zero = np.zeros_like(self.m)
            return zero, zero
        if self.form == "uniform":
            return self._p_const, np.zeros_like(self.m)
        if self.form == "band":
            a, b = self.band
            e1 = np.exp(-self.m * abs(zeta - a))
            e2 = np.exp(-self.m * abs(zeta - b))
            if a <= zeta <= b:
                val = self._c2 * (2.0 - e1 - e2)
            elif zeta < a:
                val = self._c2 * (e1 - e2)
            else:
                val = self._c2 * (e2 - e1)
            return val, self._c1 * (e1 - e2)
        beta = 1.0 / self.ell
        decay = math.exp(-beta * zeta)
        val = (self._d_coef + self._e_coef * zeta) * decay
        deriv = (-beta * self._d_coef + self._e_coef * (1.0 - beta * zeta)) * decay
        return val, deriv

    def value(self, zeta: np.ndarray) -> np.ndarray:
        """θ̂ₙ(ζ) as an (n_modes, n_points) matrix."""
        zeta = np.atleast_1d(np.asarray(zeta, dtype=float))
        m = self.m[:, None]
        homog = self.a_coef[:, None] * np.exp(-m * zeta[None, :]) + self.b_coef[
            :, None
        ] * np.exp(-m * (1.0 - zeta[None, :]))
        if self.form in ("surface", "none"):
            return homog
        if self.form == "uniform":
            return self._p_const[:, None] + homog
        if self.form == "band":
            a, b = self.band
            e1 = np.exp(-m * np.abs(zeta - a)[None, :])
            e2 = np.exp(-m * np.abs(zeta - b)[None, :])
            inside = ((zeta >= a) & (zeta <= b))[None, :]
            left = (zeta < a)[None, :]
            part = self._c2[:, None] * np.where(
                inside, 2.0 - e1 - e2, np.where(left, e1 - e2, e2 - e1)
            )
            return part + homog
        beta = 1.0 / self.ell
        decay = np.exp(-beta * zeta)[None, :]
        part = (self._d_coef[:, None] + self._e_coef[:, None] * zeta[None, :]) * decay
        return part + homog

    def end_values(self) -> tuple[np.ndarray, np.ndarray]:
        """(θ̂ₙ(0), θ̂ₙ(1))."""
        theta0 = self._p0 + self.a_coef + self.b_coef * self.e0
        theta1 = self._p1 + self.a_coef * self.e0 + self.b_coef
        return theta0, theta1

    def end_derivs(self) -> tuple[np.ndarray, np.ndarray]:
        """(θ̂ₙ'(0), θ̂ₙ'(1))."""
        _, p0p = self._part_and_deriv(0.0)
        _, p1p = self._part_and_deriv(1.0)
        d0 = p0p - self.m * self.a_coef + self.m * self.b_coef * self.e0
        d1 = p1p - self.m * self.a_coef * self.e0 + self.m * self.b_coef
        return d0, d1

    def _band_part_integral(self, lo: float, hi: float) -> np.ndarray:
        """∫ θ̂_p dζ over [lo, hi] for the band form: split at the band edges
        and use the per-region antiderivative A(ζ) = (1/m)(E1 − E2) + 2ζ
        (the 2ζ term inside the band only), all exponents non-positive."""
        a, b = self.band
        m = self.m
        total = np.zeros_like(m)
        for p, q, in_band in (
            (lo, min(hi, a), False),
            (max(lo, a), min(hi, b), True),
            (max(lo, b), hi, False),
        ):
            if not q > p:
                continue
            anti = np.zeros_like(m)
            for zeta, sign in ((q, 1.0), (p, -1.0)):
                e1 = np.exp(-m * abs(zeta - a))
                e2 = np.exp(-m * abs(zeta - b))
                val = (e1 - e2) / m
                if in_band:
                    val = val + 2.0 * zeta
                anti = anti + sign * val
            total = total + anti
        return self._c2 * total

    def segment_integral(self, zeta_lo: float, zeta_hi: float) -> np.ndarray:
        """∫ θ̂ₙ dζ over [ζ_lo, ζ_hi], closed form per mode."""
        a, b = zeta_lo, zeta_hi
        m = self.m
        homog = self.a_coef * (np.exp(-m * a) - np.exp(-m * b)) / m + (
            self.b_coef * (np.exp(-m * (1.0 - b)) - np.exp(-m * (1.0 - a))) / m
        )
        if self.form in ("surface", "none"):
            return homog
        if self.form == "uniform":
            return self._p_const * (b - a) + homog
        if self.form == "band":
            return self._band_part_integral(a, b) + homog
        ell = self.ell
        ea, eb = math.exp(-a / ell), math.exp(-b / ell)
        part = self._d_coef * ell * (ea - eb) + self._e_coef * ell * (
            (a + ell) * ea - (b + ell) * eb
        )
        return part + homog


class _ConstantMode:
    """The Bi_s = 0 constant radial mode: θ̂₀'' = −ĝ(ζ) (f̂₀ = 1), solved by
    direct double integration; θ̂₀ = u₀ + v₀ζ − Ĝ₂(ζ) with Ĝ₂ = ∫₀^ζ∫₀^s ĝ."""

    def __init__(
        self,
        source: PumpSource | None,
        ell: float | None,
        bi_top: float | None,
        bi_base: float | None,
        band: tuple[float, float] | None = None,
        top_drive: float = 0.0,
        base_drive: float = 0.0,
    ) -> None:
        # top_drive / base_drive: imposed Dirichlet end values in kelvin
        # (the constant mode's drive projection is exactly 1); form 'none'
        # when source is None — the driven S-ladder mode
        self.form = "none" if source is None else source.axial_form
        self.ell = ell
        self.band = band
        g2_total = self._g2(1.0)  # Ĝ₂(1); Ĝ₁(1) = 1 for volumetric forms
        g1_total = 0.0 if self.form in ("surface", "none") else 1.0
        q_s0 = 1.0 if self.form == "surface" else 0.0
        # rows: top condition, base condition on (u₀, v₀)
        if bi_top is None:
            row1, r1 = (1.0, 0.0), top_drive
        else:
            row1, r1 = (-bi_top, 1.0), -q_s0
        if bi_base is None:
            row2, r2 = (1.0, 1.0), base_drive + g2_total
        else:
            row2, r2 = (bi_base, 1.0 + bi_base), g1_total + bi_base * g2_total
        det = row1[0] * row2[1] - row1[1] * row2[0]
        if abs(det) < 1e-300:
            raise ValueError(
                "constant mode has no steady state (insulated side with "
                "insulated top and base)"
            )
        self.u0 = (r1 * row2[1] - row1[1] * r2) / det
        self.v0 = (row1[0] * r2 - r1 * row2[0]) / det

    def _g1(self, zeta: np.ndarray | float):
        """Ĝ₁(ζ) = ∫₀^ζ ĝ."""
        if self.form in ("surface", "none"):
            return np.zeros_like(np.asarray(zeta, dtype=float))
        if self.form == "uniform":
            return np.asarray(zeta, dtype=float)
        if self.form == "band":
            a, b = self.band
            z = np.asarray(zeta, dtype=float)
            return np.clip((z - a) / (b - a), 0.0, 1.0)
        c_hat = -math.expm1(-1.0 / self.ell)
        return -np.expm1(-np.asarray(zeta, dtype=float) / self.ell) / c_hat

    def _g2(self, zeta: np.ndarray | float):
        """Ĝ₂(ζ) = ∫₀^ζ Ĝ₁."""
        z = np.asarray(zeta, dtype=float)
        if self.form in ("surface", "none"):
            return np.zeros_like(z)
        if self.form == "uniform":
            return z**2 / 2.0
        if self.form == "band":
            # 0 below the band; (ζ−a)²/(2(b−a)) inside; ζ − (a+b)/2 above
            a, b = self.band
            return np.where(
                z <= a,
                0.0,
                np.where(
                    z <= b,
                    np.clip(z - a, 0.0, None) ** 2 / (2.0 * (b - a)),
                    z - 0.5 * (a + b),
                ),
            )
        ell = self.ell
        c_hat = -math.expm1(-1.0 / ell)
        return (z + ell * np.expm1(-z / ell)) / c_hat

    def value(self, zeta: np.ndarray) -> np.ndarray:
        zeta = np.atleast_1d(np.asarray(zeta, dtype=float))
        return self.u0 + self.v0 * zeta - self._g2(zeta)

    def end_values(self) -> tuple[float, float]:
        return float(self.value(np.array([0.0]))[0]), float(
            self.value(np.array([1.0]))[0]
        )

    def end_derivs(self) -> tuple[float, float]:
        return self.v0 - float(self._g1(0.0)), self.v0 - float(self._g1(1.0))

    def segment_integral(self, zeta_lo: float, zeta_hi: float) -> float:
        a, b = zeta_lo, zeta_hi
        lin = self.u0 * (b - a) + self.v0 * (b**2 - a**2) / 2.0
        if self.form in ("surface", "none"):
            return lin
        if self.form == "uniform":
            return lin - (b**3 - a**3) / 6.0
        if self.form == "band":
            # ∫Ĝ₂ piecewise: 0 | (ζ−a)³/(6(b−a)) | ζ²/2 − (a+b)ζ/2
            ba, bb = self.band
            int_g2 = 0.0
            p, q = max(a, ba), min(b, bb)
            if q > p:
                int_g2 += ((q - ba) ** 3 - (p - ba) ** 3) / (6.0 * (bb - ba))
            p = max(a, bb)
            if b > p:
                int_g2 += (b**2 - p**2) / 2.0 - 0.5 * (ba + bb) * (b - p)
            return lin - int_g2
        ell = self.ell
        c_hat = -math.expm1(-1.0 / ell)
        int_g2 = (
            (b**2 - a**2) / 2.0
            - ell * (b - a)
            - ell**2 * (math.exp(-b / ell) - math.exp(-a / ell))
        ) / c_hat
        return lin - int_g2


class CylinderSolution:
    """Steady solution ΔT(r, z) = Θ·Σₙ θ̂ₙ(z/L)·J₀(xₙ·r/R). Built by
    `solve()`; all derived scalars are closed-form per-mode sums."""

    def __init__(
        self,
        spec: CylinderSpec,
        source: PumpSource | None,
        n_modes: int,
        x: np.ndarray,
        modes: _AxialModes,
        const_mode: _ConstantMode | None,
    ) -> None:
        self.spec = spec
        self.source = source
        self.n_modes = n_modes
        self._x = x  # positive eigenvalues xₙ
        self._modes = modes
        self._const = const_mode
        # driven solves (source=None) carry the field in kelvin directly:
        # the imposed dt_k values enter the per-mode end conditions, Θ = 1
        self._theta_unit = (
            1.0
            if source is None
            else source.p_w
            * spec.height_m
            / (math.pi * spec.radius_m**2 * spec.k_z)
        )

    # --- field ------------------------------------------------------------

    def delta_t(self, r_m, z_m):
        """ΔT(r, z) in K, vectorised (r and z broadcast together)."""
        r = np.asarray(r_m, dtype=float)
        z = np.asarray(z_m, dtype=float)
        r, z = np.broadcast_arrays(r, z)
        shape = r.shape
        rho = r.ravel() / self.spec.radius_m
        zeta = z.ravel() / self.spec.height_m
        if np.any((rho < 0.0) | (rho > 1.0 + 1e-12)):
            raise ValueError("r outside the cylinder [0, R]")
        if np.any((zeta < 0.0) | (zeta > 1.0 + 1e-12)):
            raise ValueError("z outside the cylinder [0, L]")
        theta = self._modes.value(zeta)  # (n_pos, n_pts)
        field = np.einsum("np,np->p", j0(np.outer(self._x, rho)), theta)
        if self._const is not None:
            field = field + self._const.value(zeta)
        out = self._theta_unit * field.reshape(shape)
        return float(out) if out.ndim == 0 else out

    def modal_decomposition(self, r_m, z_m) -> dict:
        """Per-mode factor matrices of the solution on a product grid (viz
        seam, viz/PLAN.md §2; rendering-layer consumer — SPEC-neutral, no
        new physics).

        Returns {
          "x_n":          (n,) float64 — eigenvalues xₙ, ascending;
                          x_n[0] == 0.0 iff the Bi_s = 0 constant mode is
                          present (it counts as one mode, matching solve()'s
                          n_modes convention),
          "theta_k":      (n, n_z) float64 — DIMENSIONAL per-mode axial
                          profiles Θ·θ̂ₙ(z/L) in kelvin (Θ = 1 for driven
                          solves),
          "radial_basis": (n, n_r) float64 — J₀(xₙ·r/R); row of ones for
                          x₀ = 0,
          "f_hat":        (n,) float64 — dimensionless radial projections
                          f̂ₙ (f̂₀ = 1 for the constant mode; zeros for
                          driven solves),
        }
        Invariant: np.einsum('ni,nj->ij', theta_k, radial_basis) equals
        delta_t(r[None, :], z[:, None]) exactly; the first-N row partial
        sum equals the n_modes = N solution exactly (modes are independent).
        """
        r = np.atleast_1d(np.asarray(r_m, dtype=float)).ravel()
        z = np.atleast_1d(np.asarray(z_m, dtype=float)).ravel()
        rho = r / self.spec.radius_m
        zeta = z / self.spec.height_m
        if np.any((rho < 0.0) | (rho > 1.0 + 1e-12)):
            raise ValueError("r outside the cylinder [0, R]")
        if np.any((zeta < 0.0) | (zeta > 1.0 + 1e-12)):
            raise ValueError("z outside the cylinder [0, L]")
        theta = self._theta_unit * self._modes.value(zeta)  # (n_pos, n_z)
        radial = j0(np.outer(self._x, rho))  # (n_pos, n_r)
        x = np.array(self._x)
        f_hat = np.array(self._modes.f_hat)
        if self._const is not None:
            theta = np.vstack(
                [self._theta_unit * self._const.value(zeta)[None, :], theta]
            )
            radial = np.vstack([np.ones((1, rho.size)), radial])
            x = np.concatenate(([0.0], x))
            f0 = 0.0 if self.source is None else 1.0
            f_hat = np.concatenate(([f0], f_hat))
        return {
            "x_n": x,
            "theta_k": theta,
            "radial_basis": radial,
            "f_hat": f_hat,
        }

    @property
    def peak_k(self) -> float:
        """ΔT(0, 0) — the illuminated-face centre. Documented assumption:
        top-heated, base/side-sunk, so the peak sits at (0, 0); for exotic
        BC choices (e.g. Dirichlet top) evaluate `delta_t` directly."""
        return float(self.delta_t(0.0, 0.0))

    def volume_average_k(
        self,
        r_max_m: float | None = None,
        z_lo_m: float = 0.0,
        z_hi_m: float | None = None,
    ) -> float:
        """UNWEIGHTED volume average of ΔT over the sub-cylinder
        r ≤ r_max, z_lo ≤ z ≤ z_hi (default: the whole crystal — the
        "stated gain region" placeholder). Closed-form per-mode integrals.
        H-weighting (§7.T2 output 1) is downstream — deliberately not here."""
        r_max = self.spec.radius_m if r_max_m is None else float(r_max_m)
        z_hi = self.spec.height_m if z_hi_m is None else float(z_hi_m)
        rho_max = r_max / self.spec.radius_m
        za, zb = z_lo_m / self.spec.height_m, z_hi / self.spec.height_m
        if not 0.0 < rho_max <= 1.0 + 1e-12:
            raise ValueError("r_max outside (0, R]")
        if not (0.0 <= za < zb <= 1.0 + 1e-12):
            raise ValueError("need 0 <= z_lo < z_hi <= L")
        radial = 2.0 * j1(self._x * rho_max) / (self._x * rho_max)
        axial = self._modes.segment_integral(za, zb)
        total = float(radial @ axial)
        if self._const is not None:
            total += self._const.segment_integral(za, zb)
        return self._theta_unit * total / (zb - za)

    # --- diagnostics --------------------------------------------------------

    def boundary_power_w(self) -> dict[str, float]:
        """Power leaving through each surface (W) and their sum — the energy
        diagnostic. Per-mode fluxes are closed form (exponential integrals ×
        the exact radial integral ∫₀ᴿ J₀ r dr = R·J₁(xₙ)/λₙ), so the sum
        exercises the root equation, norms, projections, and axial Green's
        algebra together. Each resolved mode conserves energy exactly, so
        the deficit P − total is EXACTLY the source power outside the
        truncated radial basis — it doubles as the truncation diagnostic.

        Truncation-rate caveat (Robin- vs Dirichlet-side): the <1e-6-at-N=64
        deficit level the anchor tests assert is ROBIN-SIDE-specific — for a
        flood source with a Robin side the deficit tail decays ~ Bi_s²/N³
        (≈ 5e-8·Bi_s² at N = 64). With a DIRICHLET side, flood captured
        power per mode goes as 4P/xₙ² (Σ 4/j₀,ₙ² = 1), so the deficit decays
        only ~ 1/N — ≈ 0.6% at N = 64. That slow tail is truncation of the
        flood source's radial expansion, NOT a broken anchor: Dirichlet-side
        flood configs get the monotone-decrease-with-N assertion only.
        (Gaussian sources decay exponentially in n and are immune either
        side; the layered cross-check is Dirichlet-side but Gaussian.)"""
        spec = self.spec
        theta_u = self._theta_unit
        r2 = spec.radius_m**2
        i_n = j1(self._x) / self._x  # ∫₀¹ J₀(xₙρ) ρ dρ
        t0, t1 = self._modes.end_values()
        d0, d1 = self._modes.end_derivs()
        if spec.top.is_dirichlet:
            p_top = (spec.k_z / spec.height_m) * theta_u * 2.0 * math.pi * r2 * float(
                d0 @ i_n
            )
        else:
            p_top = spec.top.h_w_m2_k * theta_u * 2.0 * math.pi * r2 * float(t0 @ i_n)
        if spec.base.is_dirichlet:
            p_base = (
                -(spec.k_z / spec.height_m)
                * theta_u
                * 2.0
                * math.pi
                * r2
                * float(d1 @ i_n)
            )
        else:
            p_base = (
                spec.base.h_w_m2_k * theta_u * 2.0 * math.pi * r2 * float(t1 @ i_n)
            )
        # side: conductive form −k_r ∂ΔT/∂r|_R — identical to h_side·ΔT(R)
        # under the root equation xₙJ₁(xₙ) = Bi_s·J₀(xₙ); vanishes per mode
        # for the insulated side (J₁(xₙ) = 0) and for the constant mode
        theta_bar = self._modes.segment_integral(0.0, 1.0)
        p_side = (
            2.0
            * math.pi
            * spec.height_m
            * spec.k_r_w_m_k
            * theta_u
            * float((self._x * j1(self._x)) @ theta_bar)
        )
        if self._const is not None:
            c0, c1 = self._const.end_values()
            e0, e1 = self._const.end_derivs()
            area = math.pi * r2
            if spec.top.is_dirichlet:
                p_top += (spec.k_z / spec.height_m) * theta_u * area * e0
            else:
                p_top += spec.top.h_w_m2_k * theta_u * area * c0
            if spec.base.is_dirichlet:
                p_base += -(spec.k_z / spec.height_m) * theta_u * area * e1
            else:
                p_base += spec.base.h_w_m2_k * theta_u * area * c1
        total = p_top + p_base + p_side
        return {"top": p_top, "base": p_base, "side": p_side, "total": total}

    def tail_estimate_rel(self, scalar: str = "peak") -> float:
        """Summed |contribution| of the LAST 3 positive modes relative to the
        running value of the requested scalar ('peak' or 'volume_average') —
        the per-solution convergence estimate. NaN if the scalar itself is
        zero (e.g. 'peak' under a Dirichlet top, where ΔT(0,0) ≡ 0)."""
        if scalar == "peak":
            contrib = self._modes.value(np.array([0.0]))[:, 0]
            total = float(np.sum(contrib))
            if self._const is not None:
                total += float(self._const.value(np.array([0.0]))[0])
        elif scalar == "volume_average":
            radial = 2.0 * j1(self._x) / self._x
            contrib = radial * self._modes.segment_integral(0.0, 1.0)
            total = float(np.sum(contrib))
            if self._const is not None:
                total += self._const.segment_integral(0.0, 1.0)
        else:
            raise ValueError("scalar must be 'peak' or 'volume_average'")
        if total == 0.0:
            return float("nan")
        return float(np.sum(np.abs(contrib[-3:]))) / abs(total)


def solve(
    spec: CylinderSpec, source: PumpSource | None = None, n_modes: int = 64
) -> CylinderSolution:
    """Solve the anchor problem (module docstring) with `n_modes` radial
    basis functions (the Bi_s = 0 constant mode counts as one). Truncation
    is explicit — no silent cap; check `tail_estimate_rel(...)` and the
    `boundary_power_w()` deficit on unfamiliar configurations.

    `source=None` is the DRIVEN mode (S-ladder S0/S1): no volumetric or
    surface deposition — the field is driven by nonzero imposed `dt_k`
    values on the top/base Dirichlet surfaces, expanded over the active
    radial basis (uₙ = J₁(xₙ)/(xₙ·N̂ₙ); u₀ = 1) into per-mode homogeneous
    end-value problems. Fields are in kelvin, linear in the drive. A source
    and a nonzero drive cannot combine in one call — ΔT is linear, so
    superpose two solves instead."""
    if n_modes < 4:
        raise ValueError("need at least 4 radial modes")
    dt_top = spec.top.dt_k if spec.top.is_dirichlet else 0.0
    dt_base = spec.base.dt_k if spec.base.is_dirichlet else 0.0
    if spec.side.is_dirichlet and spec.side.dt_k != 0.0:
        raise ValueError(
            "a driven SIDE surface is not supported — no ladder scenario "
            "needs it (S-ladder record); drive the top/base surfaces"
        )
    if source is None:
        if dt_top == 0.0 and dt_base == 0.0:
            raise ValueError(
                "source=None needs a nonzero imposed dt_k on the top or "
                "base Dirichlet surface (the driven S-ladder mode)"
            )
    else:
        if dt_top != 0.0 or dt_base != 0.0:
            raise ValueError(
                "a pump source and imposed surface temperatures cannot "
                "combine in one solve — ΔT is linear, superpose two solves"
            )
        if source.axial_form == "surface" and spec.top.is_dirichlet:
            raise ValueError(
                "surface-flux source needs a non-Dirichlet top "
                "(a Dirichlet surface cannot carry a prescribed flux)"
            )
    r_cyl, height = spec.radius_m, spec.height_m
    k_r, k_z = spec.k_r_w_m_k, spec.k_z
    lam = (height / r_cyl) * math.sqrt(k_r / k_z)

    has_const = (not spec.side.is_dirichlet) and spec.side.h_w_m2_k == 0.0
    n_pos = n_modes - 1 if has_const else n_modes
    if spec.side.is_dirichlet:
        x = jn_zeros(0, n_pos)
    else:
        x = robin_radial_eigenvalues(spec.side.h_w_m2_k * r_cyl / k_r, n_pos)
    n_hat = 0.5 * (j0(x) ** 2 + j1(x) ** 2)

    ell, band = None, None
    if source is None:
        f_hat = np.zeros_like(x)
    else:
        f_hat = _radial_projection(source, x, n_hat, r_cyl)
        if source.axial_form == "beer_lambert":
            ell = source.l_abs_m / height  # side_chord's l_abs is RADIAL
        if source.axial_form == "band":
            if source.band_hi_m > height:
                raise ValueError("band_hi_m exceeds the cylinder height")
            band = (source.band_lo_m / height, source.band_hi_m / height)
    bi_top = None if spec.top.is_dirichlet else spec.top.h_w_m2_k * height / k_z
    bi_base = None if spec.base.is_dirichlet else spec.base.h_w_m2_k * height / k_z

    # imposed-constant drive expanded over the positive modes (exactly zero
    # for the Bi_s = 0 basis: J₁ vanishes at its own zeros — S0 is carried
    # entirely, and exactly, by the constant mode)
    u_pos = j1(x) / (x * n_hat)
    modes = _AxialModes(
        lam * x,
        f_hat,
        source,
        ell,
        bi_top,
        bi_base,
        band=band,
        top_drive=dt_top * u_pos,
        base_drive=dt_base * u_pos,
    )
    const_mode = (
        _ConstantMode(
            source,
            ell,
            bi_top,
            bi_base,
            band=band,
            top_drive=dt_top,
            base_drive=dt_base,
        )
        if has_const
        else None
    )
    return CylinderSolution(spec, source, n_modes, x, modes, const_mode)
