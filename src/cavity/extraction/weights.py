"""SPEC §7.T5(b) weight functionals — cavity arm w_E, spin arm w_s.

Two normalised spatial weights over the §3 `FieldSample` contract, fixed
by physics BEFORE any export-format decision (they are what
`cavity.export` ships and what the §7.T5(b) differential-detuning pass
will consume — this module makes no predictions):

Cavity arm — E-energy-density weight over the STO
=================================================
Bethe-Schwinger cavity perturbation for a small isotropic
Delta-eps(r) confined to the dielectric:

    delta_f / f = - int Delta_eps |E|^2 dV / (2 int eps'(r) |E|^2 dV),

denominator over ALL domains (2x electric stored energy, time-averaged
phasor densities). With a uniform coefficient over the STO,
Delta_eps(r) = (d eps_r / dT) * DeltaT(r), the frequency shift factorises:

    delta_f = [-(f/2) (d eps_r/dT) / eps_r']_(§6T)  *  p_e  *  <DeltaT>_wE,
    <DeltaT>_wE = int_STO w_E(r) DeltaT(r) dV,
    w_E(r) = eps'(r) |E(r)|^2 / int_STO eps' |E|^2 dV,

normalised to int_STO w_E dV = 1. The §6T bracket is exactly
`cavity_df_dt_hz_per_k` (provenance — coefficients stay there, NOT
here); p_e is the existing `electric_filling_factor`, carried alongside
as an explicit companion scalar so the -0.2% STO-vs-total bookkeeping
(gate-run p_e = 0.9977) is never silently absorbed into a weight.
eps' = Re(eps_r), matching `modal.electric_filling_factor` (the
imaginary part is loss, not stored energy). The uniform-DeltaT limit
collapses to delta_f = (df/dT) * p_e * DeltaT — precisely the §6T
"E-weighting p_e ~= 1 assumed" arithmetic.

Spin arm — coupling-strength weight over the gain region
========================================================
A spin at r couples to the mode by magnetic dipole with strength
g(r) ∝ |H_proj(r)| / sqrt(U_H) (Breeze et al. 2017, npj Quantum Inf. 3,
40: g_s = gamma * sqrt(mu0 h f / 2 V_mode); position-resolved form =
g_j of Carrera et al., arXiv:2412.21166). In the weak-excitation /
linear-response regime each spin enters the collective cavity response
with weight g(r)^2, so every ensemble SHAPE observable (frequency pull,
thermal shift, inhomogeneous width) is g^2-weighted:

    w_s(r) = |H_proj(r)|^2 / int_gain |H_proj|^2 dV,
    int_gain w_s dV = 1.

Which component is H_proj — stated exactly, with basis. At zero field
the pentacene triplet eigenstates |X>, |Y>, |Z> are quantised along the
molecular ZFS axes and the X-Z transition's magnetic-dipole matrix
element is carried by S_y alone: B_1 along the molecular y-axis drives
it (Breeze 2017, p. 2: the TE01delta axial magnetic field "via the S_y
spin-operator, induces transitions ... in suitably aligned pentacene
molecules"). The exact projection is H_proj = H(r) . y_mol_site —
crystal-orientation-dependent AND site-dependent (pentacene occupies
inequivalent p-terphenyl host sites), and the actual crystal orientation
is not in hand (provenance table, <matrix element> row: an order-unity
factor never measured). Therefore: parameterised, never silently |H|^2.

Axisymmetry-honest implementation: the solve is m = 0; a mounted
crystal is not axisymmetric, but the azimuthal average is exact and
closed-form. For a molecular-y unit vector at polar angle theta to the
cavity axis (u_z = cos theta), averaging |H . u|^2 over the azimuth phi
at fixed (r, z) — which IS the phi-part of the ensemble volume integral
— the H_z x H_r,phi cross terms carry cos phi / sin phi factors and
vanish, leaving exactly

    <|H . u|^2>_phi = u_z^2 |H_z|^2 + ((1 - u_z^2)/2) (|H_r|^2 + |H_phi|^2).

`SpinProjection` exposes this as:
  - `isotropic_h2()` (DEFAULT): w_s ∝ |H|^2 = |H_r|^2+|H_phi|^2+|H_z|^2.
    This is the published-framework convention (Breeze 2017's g_s;
    arXiv:2412.21166 uses the |H| magnitude with no orientation
    projection) — the default matches what the Maxwell-Bloch consumer
    actually consumes. It also equals the uniform-orientation average
    of the projected weight after normalisation (<|H.u|^2>_iso =
    |H|^2/3 pointwise; the 1/3 cancels) — asserted as a test.
  - `axis_projected(u_z)`: the closed-form azimuthal average above;
    u_z = 1 recovers the pure |H_z|^2 weight (Breeze's "magnetic field
    dipole directed along the cylindrical axis" picture).
  - `site_mixture([(u_z, fraction), ...])`: population-weighted sum
    over inequivalent sites/orientations.

Evidence rung (carry into any writeup): the |H|^2 DEFAULT is
literature-backed (Breeze-2017-class Tavis-Cummings coupling; the
Maxwell-Bloch paper's own practice). The projected refinement is OUR
implementation of Breeze's S_y statement — derived, unratified; which
mode observable-b should headline is an Oxborrow/literature
ratification item. The order-unity orientational matrix element remains
the provenance table's honest gap either way: the weights are
normalised, so it cancels in every SHAPE observable and re-enters only
in absolute-g claims, which nothing here makes.

B vs H: mu_r = 1 everywhere in this model, so B ∝ H and the choice
cancels in the normalised weight. H_phi ~= 0 for a clean TE01delta
mode; its energy share is kept as a stored mode-purity diagnostic
(`SpinArmWeight.h_phi_energy_share`), not dropped.

Phase 1b honesty: with today's geometry `FieldSample.gain_region_mask`
is absent and `effective_gain_mask` falls back to the STO dielectric —
physically NOT the gain region. `SpinArmWeight.gain_mask_is_fallback`
carries that flag; `cavity.export` labels such bundles schema-example,
not physics handoff.

Every integral routes through `axisymmetric_volume_integral`; the
per-node probe measure pi_i = w_i * dV_i uses
`axisymmetric_node_volumes` from the same single-Jacobian module. The
probe measure is the exact `weights` argument of
`cavity.thermal.broadening.line_observable_from_samples` (§7.T2
output 3 — consumer 4), which keeps the §7.T2 probe weight and the
maser coupling weight the same object by construction.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from cavity.extraction.fields import FieldSample
from cavity.extraction.quadrature import (
    axisymmetric_node_volumes,
    axisymmetric_volume_integral,
)

_MIXTURE_FRACTION_SUM_TOL = 1.0e-9


@dataclass(frozen=True)
class SpinProjection:
    """Which |H_proj|^2 the spin-arm weight uses (module docstring).

    `components` is None for the isotropic |H|^2 default, else a tuple
    of (u_z, fraction) pairs — a single pair for `axis_projected`, one
    per site for `site_mixture`. u_z = cos(theta) of the molecular-y
    axis to the cavity axis; fractions sum to 1.
    """

    components: tuple[tuple[float, float], ...] | None = None

    def __post_init__(self) -> None:
        if self.components is None:
            return
        if len(self.components) == 0:
            raise ValueError("site mixture must have at least one component")
        total = 0.0
        for u_z, fraction in self.components:
            if not -1.0 <= u_z <= 1.0:
                raise ValueError(f"u_z must lie in [-1, 1]; got {u_z}")
            if fraction <= 0.0:
                raise ValueError(
                    f"mixture fractions must be positive; got {fraction}"
                )
            total += fraction
        if abs(total - 1.0) > _MIXTURE_FRACTION_SUM_TOL:
            raise ValueError(
                f"mixture fractions must sum to 1; got {total}"
            )

    @staticmethod
    def isotropic_h2() -> "SpinProjection":
        """DEFAULT: w_s ∝ |H|^2 — the published-framework convention."""
        return SpinProjection(components=None)

    @staticmethod
    def axis_projected(u_z: float) -> "SpinProjection":
        """Closed-form azimuthal average at fixed molecular-axis polar
        angle; u_z = 1 recovers the pure |H_z|^2 weight."""
        return SpinProjection(components=((float(u_z), 1.0),))

    @staticmethod
    def site_mixture(
        components: list[tuple[float, float]] | tuple[tuple[float, float], ...],
    ) -> "SpinProjection":
        """Population-weighted (u_z, fraction) mixture over host sites."""
        return SpinProjection(
            components=tuple(
                (float(u), float(f)) for u, f in components
            )
        )

    @property
    def is_isotropic(self) -> bool:
        return self.components is None

    def label(self) -> str:
        if self.components is None:
            return "isotropic_h2"
        if len(self.components) == 1:
            return f"axis_projected(u_z={self.components[0][0]:g})"
        return "site_mixture(" + ", ".join(
            f"(u_z={u:g}, f={f:g})" for u, f in self.components
        ) + ")"

    def to_meta(self) -> dict:
        """JSON-able description for export metadata."""
        if self.components is None:
            return {"mode": "isotropic_h2", "components": None}
        return {
            "mode": (
                "axis_projected"
                if len(self.components) == 1
                else "site_mixture"
            ),
            "components": [[u, f] for u, f in self.components],
        }


@dataclass(frozen=True)
class WeightField:
    """A normalised spatial weight density on the §3 (r, z) node set.

    `values_per_m3`: (N,) non-negative density, zero outside `mask`,
    normalised so int w dV = 1 over the mask (via the §3 quadrature).
    Coordinates and plane weights ride along so the probe measure and
    re-integration need no reach-back into the source `FieldSample`,
    and so the weight co-registers with `cavity.thermal` DeltaT fields
    sampled on the same nodes.
    """

    values_per_m3: NDArray[np.float64]
    mask: NDArray[np.bool_]
    r_m: NDArray[np.float64]
    z_m: NDArray[np.float64]
    weights_m2: NDArray[np.float64]

    def __post_init__(self) -> None:
        n = self.values_per_m3.shape[0]
        for name in ("mask", "r_m", "z_m", "weights_m2"):
            arr = getattr(self, name)
            if arr.shape != (n,):
                raise ValueError(
                    f"{name} shape {arr.shape} must match "
                    f"values_per_m3 ({n},)"
                )
        if np.any(self.values_per_m3 < 0):
            raise ValueError("weight density must be non-negative")
        if np.any(self.values_per_m3[~self.mask] != 0.0):
            raise ValueError("weight density must be zero outside the mask")

    def volume_integral(self) -> float:
        """int w dV via the §3 primitive — 1.0 up to float rounding."""
        return float(
            np.real(
                axisymmetric_volume_integral(
                    self.values_per_m3, self.r_m, self.weights_m2
                )
            )
        )

    def probe_measure(self) -> NDArray[np.float64]:
        """Per-node probe measure pi_i = w_i * dV_i (dimensionless).

        Sums to 1 (same arithmetic as `volume_integral`). This is the
        `weights` argument of `line_observable_from_samples`
        (§7.T2 output 3) and the volume weighting for any statistic
        over the weighted region.
        """
        return np.asarray(
            self.values_per_m3
            * axisymmetric_node_volumes(self.r_m, self.weights_m2),
            dtype=np.float64,
        )


@dataclass(frozen=True)
class CavityArmWeight:
    """w_E plus its companion p_e (never folded into the weight).

    `p_e` is computed from the SAME masked/total integrals that
    normalise the weight — the closed loop asserted against the
    existing `electric_filling_factor` and the frozen gate record in
    tests/test_extraction_weights.py.
    """

    weight: WeightField
    p_e: float


@dataclass(frozen=True)
class SpinArmWeight:
    """w_s plus its provenance and mode-purity diagnostics.

    `gain_mask_is_fallback`: True when the source `FieldSample` had no
    Phase-1b gain mask and the STO dielectric stood in — the weight
    then describes the puck, NOT the pentacene gain region.
    `h_phi_energy_share`: int_gain |H_phi|^2 dV / int_gain |H|^2 dV, a
    TE01delta mode-purity diagnostic (~0 for a clean mode) — kept, not
    dropped, per the module docstring.
    `magnetic_filling_factor`: int_gain |H|^2 dV / int_all |H|^2 dV —
    links 1/max(w_s) to `mode_volumes().local_m3` (test identity).
    """

    weight: WeightField
    projection: SpinProjection
    gain_mask_is_fallback: bool
    h_phi_energy_share: float
    magnetic_filling_factor: float


def _component_magnitudes_squared(
    h_complex: NDArray[np.complexfloating],
) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]]:
    hr2 = np.abs(h_complex[:, 0]) ** 2
    hphi2 = np.abs(h_complex[:, 1]) ** 2
    hz2 = np.abs(h_complex[:, 2]) ** 2
    return (
        np.asarray(hr2, dtype=np.float64),
        np.asarray(hphi2, dtype=np.float64),
        np.asarray(hz2, dtype=np.float64),
    )


def projected_h2_density(
    h_complex: NDArray[np.complexfloating],
    projection: SpinProjection,
) -> NDArray[np.float64]:
    """|H_proj|^2 at each node under the module-docstring projection.

    isotropic: |H_r|^2 + |H_phi|^2 + |H_z|^2. Projected mixture:
    sum_i f_i * [u_zi^2 |H_z|^2 + ((1 - u_zi^2)/2)(|H_r|^2 + |H_phi|^2)]
    — the exact phi-average, so only the mixture's second moment
    sum f u^2 enters (u^2 = 1/3 reproduces isotropic up to the
    normalisation-cancelled 1/3).
    """
    hr2, hphi2, hz2 = _component_magnitudes_squared(h_complex)
    if projection.components is None:
        return hr2 + hphi2 + hz2
    axial = sum(f * u * u for u, f in projection.components)
    transverse = 0.5 * (1.0 - axial)
    return axial * hz2 + transverse * (hr2 + hphi2)


def _normalised_weight(
    density: NDArray[np.float64],
    mask: NDArray[np.bool_],
    field: FieldSample,
    what: str,
) -> tuple[WeightField, float]:
    """Mask, normalise over the mask, wrap. Returns (weight, norm dV)."""
    masked = np.where(mask, density, 0.0)
    # JACOBIAN: applied inside axisymmetric_volume_integral.
    norm = float(
        np.real(
            axisymmetric_volume_integral(masked, field.r_m, field.weights_m2)
        )
    )
    if norm <= 0.0:
        raise ValueError(
            f"{what} normalisation integral is non-positive — the field "
            "is (numerically) zero over the weight's mask"
        )
    return (
        WeightField(
            values_per_m3=np.asarray(masked / norm, dtype=np.float64),
            mask=np.asarray(mask, dtype=np.bool_),
            r_m=np.asarray(field.r_m, dtype=np.float64),
            z_m=np.asarray(field.z_m, dtype=np.float64),
            weights_m2=np.asarray(field.weights_m2, dtype=np.float64),
        ),
        norm,
    )


def cavity_arm_weight(field: FieldSample) -> CavityArmWeight:
    """w_E = eps' |E|^2 / int_STO eps' |E|^2 dV, plus companion p_e.

    Same energy density and same masked/total integral arithmetic as
    `modal.electric_filling_factor` (Re(eps_r), §3 primitive), so the
    returned `p_e` closes the loop against the existing extraction to
    float rounding.
    """
    e2 = np.real(
        np.sum(field.e_complex * np.conj(field.e_complex), axis=1)
    ).astype(np.float64)
    density = np.real(field.eps_r_complex) * e2

    weight, num = _normalised_weight(
        density, field.dielectric_mask, field, "cavity-arm weight"
    )
    # JACOBIAN: applied inside axisymmetric_volume_integral.
    den = float(
        np.real(
            axisymmetric_volume_integral(density, field.r_m, field.weights_m2)
        )
    )
    if den <= 0.0:
        raise ValueError(
            "total electric energy non-positive — degenerate field"
        )
    p_e = num / den
    if not 0.0 < p_e <= 1.0:
        raise ValueError(f"p_e = {p_e} out of (0, 1]")
    return CavityArmWeight(weight=weight, p_e=p_e)


def spin_arm_weight(
    field: FieldSample,
    projection: SpinProjection = SpinProjection.isotropic_h2(),
) -> SpinArmWeight:
    """w_s = |H_proj|^2 / int_gain |H_proj|^2 dV over the gain region.

    Defaults to the literature-backed isotropic |H|^2 (module
    docstring: the projected variants are derived-unratified). Uses
    `effective_gain_mask`; on pre-Phase-1b geometry that is the STO
    fallback and `gain_mask_is_fallback` says so.
    """
    mask = field.effective_gain_mask
    if not np.any(mask):
        raise ValueError("gain-region mask is empty — spin arm undefined")

    density = projected_h2_density(field.h_complex, projection)
    weight, _ = _normalised_weight(density, mask, field, "spin-arm weight")

    hr2, hphi2, hz2 = _component_magnitudes_squared(field.h_complex)
    h2 = hr2 + hphi2 + hz2
    # JACOBIAN: applied inside axisymmetric_volume_integral (all three).
    h2_gain = float(
        np.real(
            axisymmetric_volume_integral(
                np.where(mask, h2, 0.0), field.r_m, field.weights_m2
            )
        )
    )
    h2_all = float(
        np.real(
            axisymmetric_volume_integral(h2, field.r_m, field.weights_m2)
        )
    )
    hphi2_gain = float(
        np.real(
            axisymmetric_volume_integral(
                np.where(mask, hphi2, 0.0), field.r_m, field.weights_m2
            )
        )
    )
    if h2_gain <= 0.0 or h2_all <= 0.0:
        raise ValueError("magnetic energy non-positive over the gain region")

    return SpinArmWeight(
        weight=weight,
        projection=projection,
        gain_mask_is_fallback=field.gain_region_mask is None,
        h_phi_energy_share=hphi2_gain / h2_gain,
        magnetic_filling_factor=h2_gain / h2_all,
    )
