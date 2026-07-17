"""Layer A design-matrix generation — design doc §2 (DOF table), §6
(solve budget), SPEC §7-expanded §7.5 (Sobol DoE).

Scrambled-Sobol sampling over the materialised DOF box, with the block
structure and counts of the committed §6 budget table imported
VERBATIM (120 training / 30 held-out at d = 8; 97 / 30 at the d = 7
degraded fallback — the doc's own roundings of 2.7x oversampling, not
re-derived here). Seeds are pinned per SPEC §1.

Solve-readiness is gated in code: a design can only be MATERIALISED
once every question its mode requires (Q2/Q9/Q11 per
`dofs.SOLVE_GATE_QUESTIONS`) carries a resolution, and it can only emit
SOLVE-READY rows when none of those resolutions is a mock test double
(`DesignMatrix.solve_rows`). Mock-resolved designs exercise pipeline
shape through `mock_rows` and are refused by every solve-ready exit.
"""

from __future__ import annotations

import hashlib
import json
import warnings
from dataclasses import dataclass
from enum import Enum

import numpy as np
from numpy.typing import NDArray
from scipy import stats
from scipy.stats import qmc

from cavity.sweep.dofs import (
    DesignMode,
    DistributionKind,
    DofKind,
    ResolutionContext,
    MockResolutionError,
    UnresolvedTodoTraceError,
    dof_by_name,
    sweep_dimension_names,
)

# ---------------------------------------------------------------------------
# §6 solve-budget ledger — committed table values, imported verbatim.
# ---------------------------------------------------------------------------

SOLVE_BUDGET_CEILING = 300  # SPEC §7-expanded §7.5: hard
SOLVE_BUDGET_FLOOR = 150

#: §6 block table (design doc). TRAINING varies by mode; the rest are
#: mode-independent. ECCENTRICITY_CONTINGENCY is additive only if the
#: zero-solve first-order estimate demands the bounded 3-D side-study.
PHASE1B_VERIFICATION_SOLVES = 5
TRAINING_SOLVES = {DesignMode.BASELINE_D8: 120, DesignMode.DEGRADED_D7: 97}
HELD_OUT_SOLVES = 30
ACTIVE_LEARNING_RESERVE_SOLVES = 40
MESH_SPOT_CHECK_SOLVES = 4
CONFINEMENT_TRAJECTORY_SOLVES = 10
ECCENTRICITY_CONTINGENCY_SOLVES = 6

#: Order-2 full-basis coefficient counts the training blocks oversample
#: (C(d+2, 2)); pinned here for the ledger note, single-sourced for the
#: surrogate in `cavity.surrogate.pce.n_basis_terms`.
ORDER2_BASIS_TERMS = {DesignMode.BASELINE_D8: 45, DesignMode.DEGRADED_D7: 36}


def total_budgeted_solves(
    mode: DesignMode, *, include_eccentricity_contingency: bool = False
) -> int:
    """§6 total: 209 (d = 8) / 186 (d = 7); +6 with the contingency."""
    total = (
        PHASE1B_VERIFICATION_SOLVES
        + TRAINING_SOLVES[mode]
        + HELD_OUT_SOLVES
        + ACTIVE_LEARNING_RESERVE_SOLVES
        + MESH_SPOT_CHECK_SOLVES
        + CONFINEMENT_TRAJECTORY_SOLVES
    )
    if include_eccentricity_contingency:
        total += ECCENTRICITY_CONTINGENCY_SOLVES
    if total > SOLVE_BUDGET_CEILING:
        # Pre-committed §6 overrun discipline, quoted not automated:
        # (1) drop sparse order-3 ambitions, (2) shrink the AL reserve,
        # (3) reduce held-out 30 -> 20; NEVER cut Phase 1b verification
        # or the confinement trajectory; a failure at 300 solves is a
        # STOP-and-report finding, not a licence to exceed the ceiling.
        raise ValueError(
            f"budget ledger exceeds the hard §6 ceiling: {total} > "
            f"{SOLVE_BUDGET_CEILING}"
        )
    return total


class DesignBlock(Enum):
    """§6 blocks. Only TRAINING and HELD_OUT are Sobol designs this
    tier can generate; the others are enumerated solve specs
    (Phase 1b verification lives in `cavity.sweep.centre_check`) or
    later-pass placements (the GP-variance active-learning reserve)."""

    TRAINING = "training"
    HELD_OUT = "held_out"
    PHASE1B_VERIFICATION = "phase1b_verification"
    ACTIVE_LEARNING_RESERVE = "active_learning_reserve"
    MESH_SPOT_CHECKS = "mesh_spot_checks"
    CONFINEMENT_TRAJECTORY = "confinement_trajectory"


_GENERATABLE_BLOCKS = (DesignBlock.TRAINING, DesignBlock.HELD_OUT)


class GeometryDistributionVariant(Enum):
    """§7.4: report geometry rows under BOTH readings — truncated
    Gaussian (process-centred, default) and uniform (worst-case spec
    compliance); 'the gap is informative'."""

    GAUSSIAN = "trunc-gaussian"
    UNIFORM = "uniform"


class EpsilonRVariant(Enum):
    UNIFORM = "uniform"  # conservative baseline
    TRIANGULAR = "triangular-toward-nominal"  # sensitivity variant


# ---------------------------------------------------------------------------
# Materialised sampling dimensions
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SamplingDim:
    """One concrete sweep dimension: bounds, nominal, distribution.

    `cdf`/`ppf` are the single source of the per-dimension
    isoprobabilistic map — the design transform AND the surrogate
    standardisation (`cavity.surrogate.pce`) both route through them,
    so the two can never drift apart.
    """

    name: str
    lo: float
    hi: float
    nominal: float
    distribution: DistributionKind
    is_control: bool = False
    mock: bool = False
    source: str = "DOF table"

    def __post_init__(self) -> None:
        if not self.lo < self.hi:
            raise ValueError(f"{self.name}: lo must be < hi")
        if not self.lo <= self.nominal <= self.hi:
            raise ValueError(f"{self.name}: nominal outside [lo, hi]")

    def _frozen_dist(self):
        span = self.hi - self.lo
        if self.distribution is DistributionKind.TRUNC_GAUSSIAN_3SIGMA:
            # ±3σ = band (§7.4), truncated at the band edges; the
            # general (a, b) form handles a band asymmetric about the
            # nominal (possible for a resolved Q9 band).
            scale = span / 6.0
            a = (self.lo - self.nominal) / scale
            b = (self.hi - self.nominal) / scale
            return stats.truncnorm(a, b, loc=self.nominal, scale=scale)
        if self.distribution in (
            DistributionKind.UNIFORM,
            DistributionKind.CONTROL_ROOT_SOLVED,
        ):
            # The control (p_tune) is SAMPLED uniformly over its travel
            # in the training design only (§7.5 Sobol over (θ, p)); at
            # evaluation it is root-solved, never sampled.
            return stats.uniform(loc=self.lo, scale=span)
        if self.distribution is DistributionKind.TRIANGULAR_NOMINAL_PEAK:
            return stats.triang(
                (self.nominal - self.lo) / span, loc=self.lo, scale=span
            )
        raise ValueError(
            f"{self.name}: {self.distribution} is not samplable"
        )

    def ppf(self, u: NDArray[np.floating]) -> NDArray[np.float64]:
        """Unit-cube -> physical (inverse CDF)."""
        return np.asarray(self._frozen_dist().ppf(u), dtype=np.float64)

    def cdf(self, x: NDArray[np.floating]) -> NDArray[np.float64]:
        """Physical -> unit cube (the isoprobabilistic map)."""
        return np.asarray(self._frozen_dist().cdf(x), dtype=np.float64)


def _geometry_kind(
    variant: GeometryDistributionVariant,
) -> DistributionKind:
    if variant is GeometryDistributionVariant.GAUSSIAN:
        return DistributionKind.TRUNC_GAUSSIAN_3SIGMA
    return DistributionKind.UNIFORM


def materialise_dims(
    mode: DesignMode,
    context: ResolutionContext,
    *,
    geometry_distribution: GeometryDistributionVariant = (
        GeometryDistributionVariant.GAUSSIAN
    ),
    eps_r_variant: EpsilonRVariant = EpsilonRVariant.UNIFORM,
) -> tuple[SamplingDim, ...]:
    """Concrete sampling dims for `mode`, or refuse on unresolved rows.

    The refusal is the L1 gate: a design matrix cannot even be
    materialised while a required sentinel is unresolved.
    """
    missing = context.unresolved(mode)
    # Q11 is not a DOF row, but it gates solves (rider R1); for
    # MATERIALISATION only the DOF rows matter — Q11's absence must not
    # block generating a matrix whose rows could never solve anyway.
    missing_rows = tuple(q for q in missing if q in ("Q2", "Q9"))
    if missing_rows:
        raise UnresolvedTodoTraceError(
            missing_rows, "design-matrix materialisation"
        )

    dims: list[SamplingDim] = []
    for name in sweep_dimension_names(mode):
        spec = dof_by_name(name)
        if name == "crystal_axial_offset_m":
            res = context.get("Q9")
            assert res is not None  # guaranteed by the gate above
            lo, hi = res.payload["crystal_axial_offset_band_m"]
            dims.append(
                SamplingDim(
                    name=name,
                    lo=float(lo),
                    hi=float(hi),
                    nominal=float(
                        res.payload["crystal_axial_offset_nominal_m"]
                    ),
                    distribution=_geometry_kind(geometry_distribution),
                    mock=res.mock,
                    source=f"Q9 resolution ({res.provenance})",
                )
            )
        elif name == "p_tune":
            res = context.get("Q2")
            assert res is not None
            dims.append(
                SamplingDim(
                    name=name,
                    lo=float(res.payload["p_tune_min"]),
                    hi=float(res.payload["p_tune_max"]),
                    nominal=float(res.payload["p_tune_nominal"]),
                    distribution=DistributionKind.CONTROL_ROOT_SOLVED,
                    is_control=True,
                    mock=res.mock,
                    source=f"Q2 resolution ({res.provenance})",
                )
            )
        else:
            assert spec.is_resolved and isinstance(spec.band, tuple)
            assert isinstance(spec.nominal, float)
            if spec.distribution is DistributionKind.TRUNC_GAUSSIAN_3SIGMA:
                kind = _geometry_kind(geometry_distribution)
            elif name == "epsilon_r":
                kind = (
                    DistributionKind.UNIFORM
                    if eps_r_variant is EpsilonRVariant.UNIFORM
                    else DistributionKind.TRIANGULAR_NOMINAL_PEAK
                )
            else:
                kind = spec.distribution
            dims.append(
                SamplingDim(
                    name=name,
                    lo=spec.band[0],
                    hi=spec.band[1],
                    nominal=spec.nominal,
                    distribution=kind,
                    is_control=spec.kind is DofKind.CONTROL,
                )
            )
    return tuple(dims)


# ---------------------------------------------------------------------------
# Design matrix
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DesignMatrix:
    """One Sobol block over the materialised DOF box.

    `draws` is (n, d) in PHYSICAL units, dims ordered as `dims`.
    `any_mock` marks a shape-only design (mock resolutions somewhere in
    its provenance): `solve_rows` refuses it unconditionally.
    """

    mode: DesignMode
    block: DesignBlock
    seed: int
    dims: tuple[SamplingDim, ...]
    draws: NDArray[np.float64]
    geometry_distribution: GeometryDistributionVariant
    eps_r_variant: EpsilonRVariant

    def __post_init__(self) -> None:
        if self.draws.ndim != 2 or self.draws.shape[1] != len(self.dims):
            raise ValueError(
                f"draws shape {self.draws.shape} inconsistent with "
                f"{len(self.dims)} dims"
            )

    @property
    def n_draws(self) -> int:
        return int(self.draws.shape[0])

    @property
    def dim_names(self) -> tuple[str, ...]:
        return tuple(d.name for d in self.dims)

    @property
    def any_mock(self) -> bool:
        return any(d.mock for d in self.dims)

    def theta(self, index: int) -> dict[str, float]:
        return {
            name: float(self.draws[index, j])
            for j, name in enumerate(self.dim_names)
        }

    def _identity(self) -> dict:
        return {
            "mode": self.mode.value,
            "block": self.block.value,
            "seed": self.seed,
            "geometry_distribution": self.geometry_distribution.value,
            "eps_r_variant": self.eps_r_variant.value,
            "dim_names": list(self.dim_names),
        }

    def row_hash(self, index: int) -> str:
        """Audit hash of (design identity, index, θ) — the row-level
        sibling of the solve `record_hash`, NOT a replacement for it."""
        payload = {
            "design": self._identity(),
            "index": index,
            "theta": self.theta(index),
        }
        canonical = json.dumps(
            payload, sort_keys=True, separators=(",", ":")
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]

    def manifest(self) -> dict:
        """JSON-able design description (persisted by the driver)."""
        return {
            **self._identity(),
            "n_draws": self.n_draws,
            "any_mock": self.any_mock,
            "dims": [
                {
                    "name": d.name,
                    "lo": d.lo,
                    "hi": d.hi,
                    "nominal": d.nominal,
                    "distribution": d.distribution.value,
                    "is_control": d.is_control,
                    "mock": d.mock,
                    "source": d.source,
                }
                for d in self.dims
            ],
        }

    def _rows(self) -> tuple[dict, ...]:
        return tuple(
            {
                "draw_index": i,
                "row_hash": self.row_hash(i),
                "theta": self.theta(i),
            }
            for i in range(self.n_draws)
        )

    def solve_rows(self, context: ResolutionContext) -> tuple[dict, ...]:
        """SOLVE-READY rows — the gated exit (L1 hard refusal).

        Refuses while any question the mode requires is unresolved or
        mock-resolved (Q2/Q9/Q11 gate enforced in code, incl. Q11 via
        rider R1 even though it is not a DOF row), and refuses any
        design materialised from mock values.
        """
        context.assert_solveable(self.mode, what="solve-ready row emission")
        if self.any_mock:
            raise MockResolutionError(
                "solve-ready row emission refused — this design matrix "
                "was materialised from MOCK resolutions (shape-only; "
                "regenerate from ratified resolutions)"
            )
        return self._rows()

    def mock_rows(self) -> tuple[dict, ...]:
        """Shape-only rows for the dry-run tier (mock designs ONLY)."""
        if not self.any_mock:
            raise MockResolutionError(
                "mock_rows refused — this design is real-resolved; use "
                "solve_rows(context) so the Q2/Q9/Q11 gate applies"
            )
        return self._rows()


def generate_design(
    mode: DesignMode,
    block: DesignBlock,
    context: ResolutionContext,
    *,
    seed: int,
    n_draws: int | None = None,
    geometry_distribution: GeometryDistributionVariant = (
        GeometryDistributionVariant.GAUSSIAN
    ),
    eps_r_variant: EpsilonRVariant = EpsilonRVariant.UNIFORM,
) -> DesignMatrix:
    """Scrambled-Sobol design for one §6 block.

    `n_draws` defaults to the committed §6 block size (120/97 training,
    30 held-out) and may be overridden downward ONLY for mock-resolved
    (shape-only) designs — a real design at a non-committed size would
    silently drift from the budget table.
    """
    if block not in _GENERATABLE_BLOCKS:
        raise ValueError(
            f"block {block.value!r} is not a Sobol design: "
            "phase1b_verification is the enumerated centre-check block "
            "(cavity.sweep.centre_check); the active-learning reserve "
            "is GP-variance-placed in a later pass; mesh spot-checks "
            "and the confinement trajectory are enumerated specs "
            "(confinement lever is open Q5)"
        )
    committed = (
        TRAINING_SOLVES[mode]
        if block is DesignBlock.TRAINING
        else HELD_OUT_SOLVES
    )
    dims = materialise_dims(
        mode,
        context,
        geometry_distribution=geometry_distribution,
        eps_r_variant=eps_r_variant,
    )
    any_mock = any(d.mock for d in dims)
    if n_draws is None:
        n_draws = committed
    elif n_draws != committed and not any_mock:
        raise ValueError(
            f"n_draws={n_draws} deviates from the committed §6 block "
            f"size {committed} for {block.value} at {mode.value}; "
            "overriding is allowed only for mock (shape-only) designs"
        )
    if n_draws < 1:
        raise ValueError("n_draws must be >= 1")

    sampler = qmc.Sobol(d=len(dims), scramble=True, seed=seed)
    with warnings.catch_warnings():
        # The committed §6 block sizes (120/97/30) are not powers of
        # two; scrambled Sobol at these n is the accepted §7.5 usage,
        # so scipy's balance-properties UserWarning is expected noise.
        warnings.filterwarnings(
            "ignore",
            message="The balance properties of Sobol",
            category=UserWarning,
        )
        unit = sampler.random(n_draws)
    draws = np.column_stack(
        [dim.ppf(unit[:, j]) for j, dim in enumerate(dims)]
    )
    return DesignMatrix(
        mode=mode,
        block=block,
        seed=seed,
        dims=dims,
        draws=draws,
        geometry_distribution=geometry_distribution,
        eps_r_variant=eps_r_variant,
    )
