"""SPEC §4 wall-loss decomposition: Q_total -> Q_diel + Q_wall.

The geometry is solved twice and the two extracted Q values fed in:

  (a) Impedance-BC walls -> Q_total   (dielectric + wall loss)
  (b) PEC walls (closed) -> Q_diel    (dielectric loss only, since
                                       radiation Q -> infinity in a
                                       closed cavity)

Then 1/Q_wall = 1/Q_total - 1/Q_diel, and the wall-loss fraction is
Q_total / Q_wall = (1/Q_wall) / (1/Q_total).

CANCELLATION REGIME. This subtraction is cancellation-prone when
Q_total approaches Q_diel (the Breeze regime, walls negligible). At
Booth's regime (6,980 vs ~9,000) the difference lives in the fourth
significant figure of the reciprocals; at Breeze's (both ~10,000) it
falls into solver noise. The `below_resolution` flag on the result
catches this regime: it triggers when sigma(Q_wall) / Q_wall exceeds
`WALL_LOSS_THRESHOLDS.below_resolution_rel_uncertainty`, and signals
that the magnitude is consistent with walls being negligible rather
than carrying a confident finite value. This is the only way §4 can
correctly state the SPEC §6 finding that Breeze's modelled Q sits at
the dielectric ceiling (walls do not load it) rather than reporting a
spurious finite wall fraction.

CLOSED-CAVITY ASSUMPTION. Q_PEC = Q_diel ONLY because radiation Q ->
infinity in a closed cavity. This is invalid for open-boundary
geometries (PML, radiating boundary conditions, scattering domains)
where the PEC wall does not eliminate radiation as a loss channel.
`refs/comsol/oxborrow/Radiating_Dielectric_mo1.mph` is exactly such
a case and must not be passed through this layer; doing so would
silently produce a nonsense decomposition because the PEC-solve Q
in that model is NOT Q_diel, it carries residual radiation loss.

Input Q uncertainties are REQUIRED and have no default. They should
come from the §2 mesh-convergence residual on f'' (how much f''
moves between the converged mesh and the next refinement level), not
from a hardcoded fractional guess. A fabricated sigma relocates the
provenance trap from inputs to uncertainty quantification.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from cavity.extraction import ExtractionResult
from cavity.provenance import WALL_LOSS_THRESHOLDS


@dataclass(frozen=True)
class WallLossDecomposition:
    """SPEC §4 decomposition output.

    `q_wall` is always computed and reported, but its uncertainty
    `sigma_q_wall` is only a trustworthy interval when
    `below_resolution` is False. When `below_resolution` is True the
    magnitude is dominated by the cancellation in the reciprocal
    subtraction; in that regime the only valid use of `q_wall` is
    "large enough that walls don't load this mode" (Breeze end of the
    SPEC §6 confinement trend), and the reported `sigma_q_wall` is
    the linear-Taylor estimate, NOT a trustworthy ±1σ interval.

    `wall_fraction` is Q_total / Q_wall, i.e. the fraction of the
    total loss budget that the walls account for. Booth Table 8 sits
    at ~0.23-0.27 per SPEC §5.
    """

    q_total: float
    q_diel: float
    q_wall: float
    sigma_q_wall: float
    wall_fraction: float
    below_resolution: bool


def decompose_wall_loss(
    impedance_result: ExtractionResult,
    pec_result: ExtractionResult,
    sigma_q_impedance: float,
    sigma_q_pec: float,
) -> WallLossDecomposition:
    """Run the SPEC §4 two-solve wall-loss split with linear error
    propagation and a below-resolution flag.

    Args:
        impedance_result: ExtractionResult from the Impedance-BC solve.
            `impedance_result.q` is Q_total = (dielectric + wall) loss.
        pec_result: ExtractionResult from the PEC-walls solve.
            `pec_result.q` is Q_diel (dielectric loss only). VALID
            ONLY FOR CLOSED CAVITIES: in open-boundary models the PEC
            Q still carries radiation loss and the decomposition
            produces nonsense (see module docstring).
        sigma_q_impedance: 1-sigma uncertainty on Q_total. MUST be
            sourced from the §2 mesh-convergence residual on f''. No
            default is provided deliberately.
        sigma_q_pec: 1-sigma uncertainty on Q_diel, sourced the same
            way as `sigma_q_impedance`.

    Returns:
        WallLossDecomposition. `below_resolution = True` whenever
        sigma_q_wall / q_wall exceeds
        `WALL_LOSS_THRESHOLDS.below_resolution_rel_uncertainty`; in
        that regime `sigma_q_wall` is the linear-Taylor estimate, not
        a trustworthy interval, and the magnitude of `q_wall` should
        be read as "walls are negligible here" rather than as a
        specific value.

    Raises:
        ValueError: if either Q is non-positive, if either sigma is
            negative, or if `pec_result.q <= impedance_result.q`
            (strict closed-cavity physics invariant: removing wall
            loss can only raise Q).
    """
    q_total = impedance_result.q
    # CLOSED-CAVITY ASSUMPTION: pec_result.q is Q_diel only because
    # closed walls force radiation Q -> infinity. Invalid for open
    # boundaries (PML / radiating BC) where the PEC solve still
    # carries radiation loss. See module docstring for the
    # refs/comsol/oxborrow/Radiating_Dielectric_mo1.mph trap.
    q_diel = pec_result.q

    if q_total <= 0 or q_diel <= 0:
        raise ValueError(
            "Both Q values must be positive; got "
            f"Q_total={q_total}, Q_diel={q_diel}."
        )
    if sigma_q_impedance < 0 or sigma_q_pec < 0:
        raise ValueError(
            "Q uncertainties must be non-negative; got "
            f"sigma_q_impedance={sigma_q_impedance}, "
            f"sigma_q_pec={sigma_q_pec}."
        )
    if q_diel <= q_total:
        raise ValueError(
            "SPEC §4 strict invariant violated: PEC walls eliminate "
            "wall loss in a closed cavity so Q_diel (PEC) must be > "
            f"Q_total (Impedance); got Q_diel={q_diel}, "
            f"Q_total={q_total}. Either the two solves are "
            "mislabelled (Impedance and PEC swapped), they converged "
            "to different modes, or the cavity is open and the "
            "closed-cavity assumption (Q_PEC == Q_diel) does not "
            "apply."
        )

    inv_q_total = 1.0 / q_total
    inv_q_diel = 1.0 / q_diel
    inv_q_wall = inv_q_total - inv_q_diel
    q_wall = 1.0 / inv_q_wall
    wall_fraction = q_total / q_wall

    # Linear (first-order Taylor) error propagation on the reciprocal
    # subtraction. sigma(1/Q) = sigma_Q / Q^2; the two solves are
    # independent so the variances add; sigma(Q_wall) = sigma(diff) *
    # Q_wall^2. The amplification factor Q_wall^2 / Q_total^2 is the
    # cancellation trigger. The linearised sigma is meaningful as an
    # interval only when below the resolution threshold; above it the
    # only valid use is "large enough to flag below_resolution".
    sigma_inv_q_total = sigma_q_impedance / (q_total ** 2)
    sigma_inv_q_diel = sigma_q_pec / (q_diel ** 2)
    sigma_inv_q_wall = math.hypot(sigma_inv_q_total, sigma_inv_q_diel)
    sigma_q_wall = sigma_inv_q_wall * (q_wall ** 2)

    rel_unc = sigma_q_wall / q_wall
    below_resolution = (
        rel_unc > WALL_LOSS_THRESHOLDS.below_resolution_rel_uncertainty
    )

    return WallLossDecomposition(
        q_total=q_total,
        q_diel=q_diel,
        q_wall=q_wall,
        sigma_q_wall=sigma_q_wall,
        wall_fraction=wall_fraction,
        below_resolution=below_resolution,
    )
