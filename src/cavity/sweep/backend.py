"""L2 solve backends — the per-draw eigensolve behind the sweep driver.

Two implementations of one protocol:

  - `MockBackend` (the dry-run tier that governs this pass): mints a
    schema-valid §1 `SolveRecord` from closed-form TE011 fields
    (`cavity.validation.analytic_fields`) plus SMOOTH, CLEARLY-LABELLED
    MOCK parameter maps for f and Q, so the full pipeline shape —
    geometry build → eigensolve → bundle export → RAW row extraction —
    runs end to end with zero COMSOL. Mock records carry
    `comsol_version = "MOCK ..."` and their bundles are automatically
    `gain_mask_is_fallback: true` (no Phase 1b gain mask exists), i.e.
    schema examples, never physics.

  - `ComsolBackend`: thin wrapper over the EXISTING
    `cavity.forward_model.runner.run_forward_model` (persistence,
    cache, .mph archiving included). Its CONSTRUCTOR enforces the
    Q2/Q9/Q11/Q13 licence gate — while any sentinel the mode requires
    is unresolved (or mock-resolved), it refuses to exist; and Phase 1b
    solve specs additionally refuse with NotImplementedError. NOTE
    2026-07-22 (dated wording correction, behaviour identical): the
    geometry engine now HAS the crystal sub-domain (SPEC §5b, built in
    the W2 session as its ratified precondition), but THIS backend's
    θ → crystal wiring (crystal_axial_offset_m and the crystal
    on-switch in `draw_solve_spec`) does not exist — that wiring is
    its own dated changeset (H3/H4 discipline: the sweep gate is never
    cross-wired from a validation pass), so the refusal stands.
    NOTE 2026-07-18: p_tune is no longer a Phase 1b key — it IS the
    RING build's box internal height, which the engine represents
    directly; Q2 still gates every real solve through the licence
    gate.

Sweep solve configuration (design doc §1/§6, committed): eigenfrequency
search at 1.45 GHz with n_modes = 12, impedance walls, CANONICAL
material branch, the validated finest mesh ladder level (dielectric
1.25e-4 m / air 5e-4 m, humble-stirring-stardust mesh-convergence
evidence).
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Protocol

import numpy as np

from cavity.extraction import FieldSample
from cavity.extraction.quadrature import axisymmetric_volume_integral
from cavity.forward_model.geometry import (
    CavityGeometry,
    DielectricShape,
    SpacerSpec,
)
from cavity.forward_model.gridding import GridSpec, structured_grid
from cavity.forward_model.materials import MaterialSpec
from cavity.forward_model.mesh import MeshConfig
from cavity.forward_model.persistence import (
    SolveRecord,
    solve_fingerprint,
    solve_hash,
    utc_timestamp,
)
from cavity.forward_model.runner import ForwardModelResult, run_forward_model
from cavity.forward_model.study import EigenStudyConfig, WallBC
from cavity.provenance import (
    CLPS,
    GEOM_WU_STO_RING,
    STO,
    STO_HEIGHT_FORK,
    STOSingleCrystal,
    TARGET,
)
from cavity.sweep.dofs import DesignMode, ResolutionContext
from cavity.validation.analytic_fields import TE011Mode, te011_fields

#: §6: "one solve = one eigenfrequency study (search 1.45 GHz,
#: n_modes = 12 ...) at the validated finest mesh level, walls-on".
SWEEP_STUDY = EigenStudyConfig(
    wall_bc=WallBC.IMPEDANCE, search_hz=TARGET.f_design_hz, n_modes=12
)

#: The validated finest ladder level (design doc §1, inherited with the
#: archived per-level convergence tables as its justification).
SWEEP_MESH_FINEST = MeshConfig(
    dielectric_max_h_m=1.25e-4, air_max_h_m=5.0e-4
)

#: Second (coarser) level for the centre-check mesh pairing — one
#: sqrt(2) ladder step below finest, matching the runner's default
#: refinement factor.
SWEEP_MESH_COARSER = MeshConfig(
    dielectric_max_h_m=1.25e-4 * 2.0**0.5, air_max_h_m=5.0e-4 * 2.0**0.5
)


@dataclass(frozen=True)
class DrawSolveSpec:
    """One design row translated into solve inputs.

    `phase1b` holds the Phase 1b parameters the CURRENT geometry engine
    cannot represent (crystal axial offset — the crystal sub-domain is
    SPEC §5b work). It is non-empty exactly when θ carries those DOFs;
    the COMSOL backend refuses such specs, the mock backend folds them
    into its labelled mock maps. NOTE 2026-07-18: p_tune LEFT this set
    — it is the RING build's box internal height, represented directly.
    """

    geom: CavityGeometry
    materials: MaterialSpec
    study: EigenStudyConfig
    mesh: MeshConfig
    grid: GridSpec
    theta: dict[str, float]
    phase1b: dict[str, float]

    @property
    def needs_phase1b_geometry(self) -> bool:
        return bool(self.phase1b)


#: θ keys the current axisymmetric geometry engine cannot represent
#: (p_tune left 2026-07-18 — it became the RING box internal height).
_PHASE1B_THETA_KEYS = ("crystal_axial_offset_m",)


def _wu_spacer_spec() -> SpacerSpec:
    """The Wu seat from the graded provenance fields (figure-derived,
    GEOM_WU_STO_RING docstring)."""
    g = GEOM_WU_STO_RING
    return SpacerSpec(
        base_inner_radius_m=g.spacer_base_inner_radius_m,
        base_outer_radius_m=g.spacer_base_outer_radius_m,
        base_height_m=g.spacer_base_height_m,
        lip_inner_radius_m=g.spacer_lip_inner_radius_m,
        lip_outer_radius_m=g.spacer_lip_outer_radius_m,
        lip_height_m=g.spacer_lip_height_m,
    )


def draw_solve_spec(
    theta: dict[str, float],
    *,
    study: EigenStudyConfig = SWEEP_STUDY,
    mesh: MeshConfig = SWEEP_MESH_FINEST,
    grid: GridSpec = GridSpec(),
    box_height_fallback_m: float | None = None,
    include_spacer: bool = True,
) -> DrawSolveSpec:
    """θ → solve inputs (RING branch on the Wu build from 2026-07-18,
    canonical materials with the sampled εr/tanδ overrides).

    Box height sourcing: `theta["p_tune"]` when present — p_tune IS the
    box internal height (piston position, metres; identity map). A θ
    without p_tune (DEGRADED_D7, mock dry-runs) must pass
    `box_height_fallback_m` EXPLICITLY (callers use the as-operated
    nominal `GEOM_WU_STO_RING.box_internal_height_asoperated_m`) — no
    silent module default.

    `include_spacer` (default ON, ratified — Wu's own COMSOL includes
    the seat, Fig. 6) is the ONE spacer switch: it populates (or not)
    both `geom.spacer` and `materials.spacer`; build.py follows the
    geometry.
    """
    if "p_tune" in theta:
        box_height_m = theta["p_tune"]
    elif box_height_fallback_m is not None:
        box_height_m = box_height_fallback_m
    else:
        raise ValueError(
            "no box internal height: θ carries no p_tune (Q2-gated "
            "control) and no box_height_fallback_m was passed — the "
            "d = 7 / dry-run path must supply the as-operated nominal "
            "explicitly (GEOM_WU_STO_RING.box_internal_height_asoperated_m)"
        )
    geom = CavityGeometry(
        box_radius_m=theta["box_radius_m"],
        box_height_m=box_height_m,
        dielectric_radius_m=theta["sto_outer_radius_m"],
        dielectric_shape=DielectricShape.RING,
        dielectric_height_m=theta["sto_height_m"],
        dielectric_inner_radius_m=theta["sto_inner_radius_m"],
        ring_bottom_z_m=GEOM_WU_STO_RING.deck_clearance_m,
        spacer=_wu_spacer_spec() if include_spacer else None,
    )
    materials = MaterialSpec(
        sto=STOSingleCrystal(
            epsilon_r_real=theta["epsilon_r"],
            tan_delta=theta["tan_delta"],
        ),
        wall_pec=study.wall_bc is WallBC.PEC,
        spacer=CLPS if include_spacer else None,
    )
    phase1b = {
        k: theta[k] for k in _PHASE1B_THETA_KEYS if k in theta
    }
    return DrawSolveSpec(
        geom=geom,
        materials=materials,
        study=study,
        mesh=mesh,
        grid=grid,
        theta=dict(theta),
        phase1b=phase1b,
    )


class SolveBackend(Protocol):
    """Per-draw eigensolve: spec in, §1 record (+extraction) out."""

    def solve(self, spec: DrawSolveSpec) -> ForwardModelResult: ...


# ---------------------------------------------------------------------------
# Mock backend
# ---------------------------------------------------------------------------

#: MOCK parameter-map coefficients — smooth, plausible-ordering values
#: for pipeline/surrogate SHAPE exercise ONLY. They are labelled mock
#: precisely because the real levers are what the licensed sweep will
#: measure; nothing downstream may quote them as physics. Re-keyed
#: FRESH 2026-07-18 for the Wu-ring rows (mocks never carry over from
#: the retired torus rows); orderings are plausible only (ring dims
#: dominate, enclosure weak; εr keeps its band-derived ~14 MHz/6-unit
#: order).
MOCK_F_LEVERS_HZ = {
    "sto_outer_radius_m": -0.30e12,  # Hz per metre — MOCK, dominant ring dim
    "sto_inner_radius_m": +0.08e12,  # MOCK (bigger bore -> less dielectric)
    "sto_height_m": -0.15e12,  # MOCK
    "box_radius_m": -0.02e12,  # MOCK, weak enclosure lever
    "epsilon_r": -2.33e6,  # Hz per unit εr (band-derived order, mock)
    # Fresh MOCK lever for the 2026-07-16 axial-offset coordinate (the
    # retired bore-radius lever does not carry over): deliberately small
    # vs the geometry levers — the crystal is a weak perturbation and
    # the true offset dependence is symmetric about the equatorial
    # plane to first order; nonzero only so the dimension carries
    # signal in pipeline-shape exercise.
    "crystal_axial_offset_m": +2.0e8,
    # p_tune is now the box internal height in METRES (2026-07-18):
    # MOCK tuning lever, piston-down (smaller height) raises f.
    "p_tune": -0.05e12,
}
#: MOCK wall Q for the impedance-wall branch of the mock loss map
#: 1/Q0 = p_e·tanδ + 1/Q_wall (the committed §4 split SHAPE with a
#: mock constant of the right order).
MOCK_Q_WALL = 26_000.0

_MOCK_COMSOL_VERSION = (
    "MOCK (no COMSOL: closed-form TE011 fields + labelled mock "
    "parameter maps; pipeline-shape tier only)"
)


def _mock_reference_theta() -> dict[str, float]:
    """Committed nominals the mock f-map is anchored at (Wu build)."""
    return {
        "box_radius_m": GEOM_WU_STO_RING.box_inner_radius_m,
        "sto_outer_radius_m": GEOM_WU_STO_RING.sto_outer_radius_m,
        "sto_inner_radius_m": GEOM_WU_STO_RING.sto_inner_radius_m,
        # The ONE sanctioned pre-resolution read of the Q13 fork's
        # machine-readable branch: MOCK tier only, explicit and
        # labelled — never a silent selection (8.6 evidence-favoured).
        "sto_height_m": STO_HEIGHT_FORK.evidence_favoured,
        "epsilon_r": STO.epsilon_r_real,
        "tan_delta": STO.tan_delta,
        # Axially centred — a fresh mock reference for the 2026-07-16
        # crystal-placement coordinate, not the retired bore reference.
        "crystal_axial_offset_m": 0.0,
        # As-operated internal height (metres — 2026-07-18 semantics).
        "p_tune": GEOM_WU_STO_RING.box_internal_height_asoperated_m,
    }


@dataclass(frozen=True)
class MockBackend:
    """Schema-valid synthetic solves; zero COMSOL; labelled mock.

    `grid_n_r`/`grid_n_z` default small so dry-run bundles stay cheap;
    the export grid is part of the fingerprint, so mock hashes are
    distinct from any production record by construction.
    """

    grid_n_r: int = 41
    grid_n_z: int = 61

    def solve(self, spec: DrawSolveSpec) -> ForwardModelResult:
        grid_spec = GridSpec(n_r=self.grid_n_r, n_z=self.grid_n_z)
        fingerprint = solve_fingerprint(
            spec.geom, spec.materials, spec.mesh, spec.study, grid_spec
        )
        record_hash = solve_hash(fingerprint)

        grid = structured_grid(
            spec.geom.box_radius_m,
            spec.geom.box_height_m,
            self.grid_n_r,
            self.grid_n_z,
        )
        mode = TE011Mode(
            radius_m=spec.geom.box_radius_m,
            length_m=spec.geom.box_height_m,
        )
        e, h = te011_fields(mode, grid.r_m, grid.z_m)

        dielectric_mask = spec.geom.dielectric_mask(grid.r_m, grid.z_m)
        eps_r = np.ones(grid.r_m.shape[0], dtype=np.complex128)
        eps_r[dielectric_mask] = spec.materials.sto_complex_eps_r
        spacer_mask = None
        if spec.geom.spacer is not None:
            # Same integrity rule as the live path: the eps map must
            # describe the declared model, spacer nodes included.
            spacer_mask = spec.geom.spacer_mask(grid.r_m, grid.z_m)
            eps_r[spacer_mask] = spec.materials.spacer_complex_eps_r

        # p_e from the actual synthetic fields (same §3 primitive the
        # extraction uses) so the mock loss map is self-consistent.
        e2 = np.sum(np.abs(e) ** 2, axis=1)
        density = np.real(eps_r) * e2
        # JACOBIAN: applied inside axisymmetric_volume_integral (both).
        num = float(
            np.real(
                axisymmetric_volume_integral(
                    np.where(dielectric_mask, density, 0.0),
                    grid.r_m,
                    grid.weights_m2,
                )
            )
        )
        den = float(
            np.real(
                axisymmetric_volume_integral(
                    density, grid.r_m, grid.weights_m2
                )
            )
        )
        p_e = num / den

        f_real = self._mock_f_hz(spec)
        q = self._mock_q(spec, p_e)
        f_imag = f_real / (2.0 * q)  # Q = f'/(2 f'') by construction

        spectrum_re = np.array([0.8 * f_real, f_real, 1.3 * f_real])
        spectrum_im = np.array([f_imag * 0.5, f_imag, f_imag * 2.0])
        picked = 1

        field = FieldSample(
            r_m=grid.r_m,
            z_m=grid.z_m,
            e_complex=e,
            h_complex=h,
            eps_r_complex=eps_r,
            weights_m2=grid.weights_m2,
            dielectric_mask=dielectric_mask,
            complex_eigenfrequency_hz=complex(f_real, f_imag),
            gain_region_mask=None,  # Phase 1b unbuilt: honest fallback
            spacer_mask=spacer_mask,
        )
        record = SolveRecord(
            fingerprint=fingerprint,
            record_hash=record_hash,
            comsol_version=_MOCK_COMSOL_VERSION,
            mesh_element_count=0,
            interface_tag="mock",
            picked_index=picked,
            spectrum_f_real_hz=spectrum_re,
            spectrum_f_imag_hz=spectrum_im,
            spectrum_q_emw=None,
            field_sample=field,
            created_at_utc=utc_timestamp(),
            diagnostics=None,
        )
        from cavity.extraction import extract

        return ForwardModelResult(
            record=record,
            extraction=extract(field),
            from_cache=False,
            solution=None,
        )

    @staticmethod
    def _mock_f_hz(spec: DrawSolveSpec) -> float:
        ref = _mock_reference_theta()
        f = TARGET.f_design_hz
        for name, lever in MOCK_F_LEVERS_HZ.items():
            if name in spec.theta:
                f += lever * (spec.theta[name] - ref[name])
        return f

    @staticmethod
    def _mock_q(spec: DrawSolveSpec, p_e: float) -> float:
        tan_delta = spec.materials.sto.tan_delta
        if spec.materials.wall_pec:
            return 1.0 / (p_e * tan_delta)
        return 1.0 / (p_e * tan_delta + 1.0 / MOCK_Q_WALL)


# ---------------------------------------------------------------------------
# COMSOL backend — licence-gated in code
# ---------------------------------------------------------------------------


class ComsolBackend:
    """The licensed path. Refuses to be CONSTRUCTED while the mode's
    Q2/Q9/Q11/Q13 sentinels are unresolved (or mock-resolved) — the
    gate sits upstream of any client connection, so a licence cannot be
    touched by accident. This wiring is what `--comsol` reaches."""

    def __init__(
        self,
        context: ResolutionContext,
        mode: DesignMode,
        *,
        client: Any = None,
        cache_root: Path | None = None,
        save_mph_dir: Path | None = None,
    ) -> None:
        context.assert_solveable(
            mode, what="ComsolBackend construction (licence gate)"
        )
        self._client = client
        self._cache_root = cache_root
        self._save_mph_dir = save_mph_dir

    def solve(self, spec: DrawSolveSpec) -> ForwardModelResult:
        if spec.needs_phase1b_geometry:
            raise NotImplementedError(
                "Phase 1b solve spec refused: this backend has no "
                "θ → crystal wiring "
                f"(spec carries {sorted(spec.phase1b)}). The geometry "
                "engine's crystal sub-domain exists (SPEC §5b, built "
                "2026-07-22 in the W2 session), but wiring it into "
                "draw_solve_spec/ComsolBackend is its own dated "
                "changeset — not licensed by the Layer A design doc "
                "and never cross-wired from a validation pass."
            )
        return run_forward_model(
            spec.geom,
            spec.study,
            replace(spec.materials, wall_pec=spec.study.wall_bc is WallBC.PEC),
            spec.mesh,
            grid_spec=spec.grid,
            client=self._client,
            cache_root=self._cache_root,
            save_mph_dir=self._save_mph_dir,
        )
