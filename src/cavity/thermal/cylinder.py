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
bath) or exact Dirichlet (ΔT = 0):

    side  r = R:  −k_r ∂ΔT/∂r = h_side · ΔT        (or ΔT = 0)
    top   z = 0:  +k_z ∂ΔT/∂z = h_top  · ΔT − q_s(r)
    base  z = L:  −k_z ∂ΔT/∂z = h_base · ΔT        (or ΔT = 0)

(q_s ≠ 0 only for the surface-flux source form; a surface-flux source with a
Dirichlet top is rejected — a Dirichlet surface cannot carry prescribed flux.)

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

Radial profiles f(r): 'flood' 1/(πR²) (default — face-scale illumination is
the regime this anchor targets), 'disc' 1/(πa²)·1{r<a}, 'gaussian'
∝ e^(−2r²/w²) truncated at R and renormalised.

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
  conductance, §7.T6-style sapphire sink) enters later.

SPEC-silent decisions (D1–D7, taken 2026-07-07 as parameterised planning
assumptions — flagged for Oxborrow ratification, §11 item-10 bundle)
------------------------------------------------------------------------
D1  Mounting/contact: fully parameterised per-surface BCs (independent Robin
    h per surface, ambient = bath, exact Dirichlet option). NO hard-coded
    "physical" default is claimed — `CylinderSpec` requires all three BCs
    explicitly. The worked example uses Dirichlet base + Robin(h_conv+h_rad)
    side/top — Oxborrow's "substrate below at room temperature" framing —
    labelled a planning assumption.
D2  Pump entry: AXIAL illumination of the z = 0 end face, Beer-Lambert in
    depth (§7.T5 volumetric convention; §7.T7 rider (a)). Side-pumping —
    W20's invasive-LC pump geometry is SIDE-ON — is not axisymmetric about
    the cylinder axis and is outside this eigenbasis: EXCLUDED, a structural
    limitation of this anchor, not a parameter choice. If our maser pump is
    also side-on this anchor's illumination model must be revisited — a
    question for Oxborrow, not a footnote.
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

_CONFLUENT_WINDOW = 1e-6  # |mₙ·ℓ − 1| below this → z·e^(−z/ℓ) confluent branch

_AXIAL_FORMS = ("beer_lambert", "uniform", "surface")
_RADIAL_FORMS = ("flood", "disc", "gaussian")


@dataclass(frozen=True)
class SurfaceBC:
    """One surface's boundary condition: Robin (h ≥ 0, ambient = bath) or
    exact Dirichlet (ΔT = 0). Robin h = 0 is an insulated surface."""

    kind: str
    h_w_m2_k: float = 0.0

    def __post_init__(self) -> None:
        if self.kind not in ("robin", "dirichlet"):
            raise ValueError("SurfaceBC kind must be 'robin' or 'dirichlet'")
        if self.kind == "robin" and not self.h_w_m2_k >= 0.0:
            raise ValueError("Robin coefficient h must be non-negative")
        if self.kind == "dirichlet" and self.h_w_m2_k != 0.0:
            raise ValueError("a Dirichlet surface carries no h")

    @classmethod
    def robin(cls, h_w_m2_k: float) -> "SurfaceBC":
        return cls(kind="robin", h_w_m2_k=float(h_w_m2_k))

    @classmethod
    def dirichlet(cls) -> "SurfaceBC":
        return cls(kind="dirichlet")

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

    def __post_init__(self) -> None:
        if not self.p_w > 0.0:
            raise ValueError("pump power must be positive")
        if self.axial_form not in _AXIAL_FORMS:
            raise ValueError(f"axial_form must be one of {_AXIAL_FORMS}")
        if self.radial_form not in _RADIAL_FORMS:
            raise ValueError(f"radial_form must be one of {_RADIAL_FORMS}")
        if self.axial_form == "beer_lambert":
            if self.l_abs_m is None or not self.l_abs_m > 0.0:
                raise ValueError("beer_lambert needs a positive l_abs_m")
        elif self.l_abs_m is not None:
            raise ValueError("l_abs_m only applies to the beer_lambert form")
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
        source: PumpSource,
        ell: float | None,
        bi_top: float | None,
        bi_base: float | None,
    ) -> None:
        # bi_top / bi_base: Biot numbers for Robin, None for Dirichlet
        self.m = m
        self.f_hat = f_hat
        self.form = source.axial_form
        self.ell = ell
        n = m.size
        # --- particular solution coefficients -----------------------------
        if self.form == "uniform":
            self._p_const = f_hat / m**2
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
        e0 = np.exp(-m)
        self.e0 = e0
        # --- 2×2 end-condition solve (Cramer) ------------------------------
        if bi_top is None:  # Dirichlet top
            a11, a12, r1 = np.ones(n), e0, -p0
        else:
            a11 = -(m + bi_top)
            a12 = e0 * (m - bi_top)
            r1 = -p0p + bi_top * p0 - q_s
        if bi_base is None:  # Dirichlet base
            a21, a22, r2 = e0, np.ones(n), -p1
        else:
            a21 = e0 * (m - bi_base)
            a22 = -(m + bi_base)
            r2 = p1p + bi_base * p1
        det = a11 * a22 - a12 * a21
        self.a_coef = (r1 * a22 - a12 * r2) / det
        self.b_coef = (a11 * r2 - r1 * a21) / det

    def _part_and_deriv(self, zeta: float) -> tuple[np.ndarray, np.ndarray]:
        """Particular solution and its ζ-derivative at a scalar ζ (per mode)."""
        if self.form == "surface":
            zero = np.zeros_like(self.m)
            return zero, zero
        if self.form == "uniform":
            return self._p_const, np.zeros_like(self.m)
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
        if self.form == "surface":
            return homog
        if self.form == "uniform":
            return self._p_const[:, None] + homog
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

    def segment_integral(self, zeta_lo: float, zeta_hi: float) -> np.ndarray:
        """∫ θ̂ₙ dζ over [ζ_lo, ζ_hi], closed form per mode."""
        a, b = zeta_lo, zeta_hi
        m = self.m
        homog = self.a_coef * (np.exp(-m * a) - np.exp(-m * b)) / m + (
            self.b_coef * (np.exp(-m * (1.0 - b)) - np.exp(-m * (1.0 - a))) / m
        )
        if self.form == "surface":
            return homog
        if self.form == "uniform":
            return self._p_const * (b - a) + homog
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
        source: PumpSource,
        ell: float | None,
        bi_top: float | None,
        bi_base: float | None,
    ) -> None:
        self.form = source.axial_form
        self.ell = ell
        g2_total = self._g2(1.0)  # Ĝ₂(1); Ĝ₁(1) = 1 for volumetric forms
        g1_total = 0.0 if self.form == "surface" else 1.0
        q_s0 = 1.0 if self.form == "surface" else 0.0
        # rows: top condition, base condition on (u₀, v₀)
        if bi_top is None:
            row1, r1 = (1.0, 0.0), 0.0
        else:
            row1, r1 = (-bi_top, 1.0), -q_s0
        if bi_base is None:
            row2, r2 = (1.0, 1.0), g2_total
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
        if self.form == "surface":
            return np.zeros_like(np.asarray(zeta, dtype=float))
        if self.form == "uniform":
            return np.asarray(zeta, dtype=float)
        c_hat = -math.expm1(-1.0 / self.ell)
        return -np.expm1(-np.asarray(zeta, dtype=float) / self.ell) / c_hat

    def _g2(self, zeta: np.ndarray | float):
        """Ĝ₂(ζ) = ∫₀^ζ Ĝ₁."""
        z = np.asarray(zeta, dtype=float)
        if self.form == "surface":
            return np.zeros_like(z)
        if self.form == "uniform":
            return z**2 / 2.0
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
        if self.form == "surface":
            return lin
        if self.form == "uniform":
            return lin - (b**3 - a**3) / 6.0
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
        source: PumpSource,
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
        self._theta_unit = (
            source.p_w
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
    spec: CylinderSpec, source: PumpSource, n_modes: int = 64
) -> CylinderSolution:
    """Solve the anchor problem (module docstring) with `n_modes` radial
    basis functions (the Bi_s = 0 constant mode counts as one). Truncation
    is explicit — no silent cap; check `tail_estimate_rel(...)` and the
    `boundary_power_w()` deficit on unfamiliar configurations."""
    if n_modes < 4:
        raise ValueError("need at least 4 radial modes")
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
    f_hat = _radial_projection(source, x, n_hat, r_cyl)

    ell = None if source.l_abs_m is None else source.l_abs_m / height
    bi_top = None if spec.top.is_dirichlet else spec.top.h_w_m2_k * height / k_z
    bi_base = None if spec.base.is_dirichlet else spec.base.h_w_m2_k * height / k_z

    modes = _AxialModes(lam * x, f_hat, source, ell, bi_top, bi_base)
    const_mode = (
        _ConstantMode(source, ell, bi_top, bi_base) if has_const else None
    )
    return CylinderSolution(spec, source, n_modes, x, modes, const_mode)
