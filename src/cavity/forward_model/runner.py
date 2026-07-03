"""SPEC §2 driver — build / mesh / solve / extract with §1 persistence.

`run_forward_model` is the one-solve entry point: cache-check by
parameter hash, otherwise build + solve via MPh, persist the raw
solution, and hand the picked mode to the EXISTING §3 extraction.

`run_convergence_study` runs the same configuration over a coarse->fine
mesh ladder (>= 3 levels), demands the asymptotic regime via
`convergence.assess_convergence` (raising otherwise), and emits the f''
residual as the sigma that `validation.wall_loss` requires.

`run_wall_loss_study` is the §4 wiring: the SAME geometry solved twice
(Impedance walls -> Q_total, PEC walls -> Q_diel), each through its own
convergence ladder for a defensible sigma, fed into the existing
`decompose_wall_loss` interface.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

from cavity.extraction import ExtractionResult, extract
from cavity.forward_model.build import BuiltModel, build_model
from cavity.forward_model.convergence import (
    ConvergenceAssessment,
    assess_convergence,
)
from cavity.forward_model.geometry import CavityGeometry
from cavity.forward_model.gridding import GridSpec
from cavity.forward_model.materials import MaterialSpec
from cavity.forward_model.mesh import MeshConfig, refinement_ladder
from cavity.forward_model.mode_id import TE01DeltaCriteria
from cavity.forward_model.persistence import (
    SolveRecord,
    load_solve_record,
    save_solve_record,
    solve_fingerprint,
    solve_hash,
    utc_timestamp,
)
from cavity.forward_model.solve import SolvedTE01Delta, solve_eigenfrequency
from cavity.forward_model.study import EigenStudyConfig, WallBC
from cavity.validation.wall_loss import (
    WallLossDecomposition,
    decompose_wall_loss,
)


def material_spec_for(study: EigenStudyConfig, base: MaterialSpec | None = None) -> MaterialSpec:
    """MaterialSpec whose §4 wall switch agrees with the study's."""
    base = base if base is not None else MaterialSpec()
    return replace(base, wall_pec=study.wall_bc is WallBC.PEC)


@dataclass(frozen=True)
class ForwardModelResult:
    """One solved (or cache-loaded) configuration, extraction included."""

    record: SolveRecord
    extraction: ExtractionResult
    from_cache: bool
    solution: SolvedTE01Delta | None = None


def _record_from_solution(
    solution: SolvedTE01Delta,
    fingerprint: dict,
    record_hash: str,
    interface_tag: str,
) -> SolveRecord:
    return SolveRecord(
        fingerprint=fingerprint,
        record_hash=record_hash,
        comsol_version=solution.eigen.comsol_version,
        mesh_element_count=solution.eigen.mesh_element_count,
        interface_tag=interface_tag,
        picked_index=solution.picked_index,
        spectrum_f_real_hz=solution.spectrum.f_real_hz,
        spectrum_f_imag_hz=solution.spectrum.f_imag_hz,
        spectrum_q_emw=solution.spectrum.q_emw,
        field_sample=solution.field_sample,
        created_at_utc=utc_timestamp(),
        diagnostics=[
            {
                "f_real_hz": d.complex_eigenfrequency_hz.real,
                "f_imag_hz": d.complex_eigenfrequency_hz.imag,
                "azimuthal_e_energy_fraction": d.azimuthal_e_energy_fraction,
                "axis_hz_antinode_ratio": d.axis_hz_antinode_ratio,
                "axis_hz_sign_changes": d.axis_hz_sign_changes,
            }
            for d in solution.diagnostics
        ],
    )


def run_forward_model(
    geom: CavityGeometry,
    study: EigenStudyConfig,
    materials: MaterialSpec | None = None,
    mesh_cfg: MeshConfig = MeshConfig(),
    *,
    grid_spec: GridSpec = GridSpec(),
    criteria: TE01DeltaCriteria = TE01DeltaCriteria(),
    client: Any = None,
    cache_root: Path | None = None,
    force_resolve: bool = False,
) -> ForwardModelResult:
    """Solve one configuration (or load it from the §1 cache) and extract.

    With `cache_root` set, a matching parameter hash short-circuits the
    COMSOL solve entirely — extraction re-runs from the persisted raw
    fields, which is the SPEC §1 re-derivation path.
    """
    if materials is None:
        materials = material_spec_for(study)
    fingerprint = solve_fingerprint(geom, materials, mesh_cfg, study, grid_spec)
    record_hash = solve_hash(fingerprint)

    if cache_root is not None and not force_resolve:
        cached = load_solve_record(cache_root, record_hash)
        if cached is not None:
            return ForwardModelResult(
                record=cached,
                extraction=extract(cached.field_sample),
                from_cache=True,
            )

    built: BuiltModel = build_model(
        geom, materials, mesh_cfg, study, client=client
    )
    try:
        solution = solve_eigenfrequency(
            built,
            geom,
            materials,
            study,
            grid_spec=grid_spec,
            criteria=criteria,
        )
    finally:
        try:
            built.client.remove(built.model)
        except Exception:
            pass  # cleanup only; the record already holds everything

    record = _record_from_solution(
        solution, fingerprint, record_hash, built.interface_tag
    )
    if cache_root is not None:
        save_solve_record(record, cache_root)
    return ForwardModelResult(
        record=record,
        extraction=extract(solution.field_sample),
        from_cache=False,
        solution=solution,
    )


@dataclass(frozen=True)
class ConvergenceLevelResult:
    mesh_cfg: MeshConfig
    complex_eigenfrequency_hz: complex
    mesh_element_count: int
    from_cache: bool


@dataclass(frozen=True)
class ConvergenceStudyResult:
    """SPEC §2 convergence study: per-level record + sigma verdict.

    `assessment.sigma_q` is the discretisation 1-sigma on Q that the §4
    decomposition consumes; it exists only because the assessment
    passed (a non-asymptotic ladder raises `ConvergenceError` upstream
    and produces no result at all).
    """

    levels: tuple[ConvergenceLevelResult, ...]
    assessment: ConvergenceAssessment
    finest: ForwardModelResult

    @property
    def sigma_q(self) -> float:
        return self.assessment.sigma_q


def run_convergence_study(
    geom: CavityGeometry,
    study: EigenStudyConfig,
    materials: MaterialSpec | None = None,
    base_mesh: MeshConfig = MeshConfig(),
    *,
    n_levels: int = 3,
    refine_factor: float = 2.0**0.5,
    grid_spec: GridSpec = GridSpec(),
    criteria: TE01DeltaCriteria = TE01DeltaCriteria(),
    client: Any = None,
    cache_root: Path | None = None,
    force_resolve: bool = False,
) -> ConvergenceStudyResult:
    """Solve the same configuration over a coarse->fine mesh ladder.

    The TE01delta mode is re-identified by field pattern at EVERY level
    (mode ordering is not stable across meshes). The ladder must land
    in the asymptotic regime — `assess_convergence` raises otherwise
    and no sigma is emitted, per SPEC §2.
    """
    ladder = refinement_ladder(base_mesh, n_levels, refine_factor)
    results: list[ForwardModelResult] = []
    for mesh_cfg in ladder:
        results.append(
            run_forward_model(
                geom,
                study,
                materials,
                mesh_cfg,
                grid_spec=grid_spec,
                criteria=criteria,
                client=client,
                cache_root=cache_root,
                force_resolve=force_resolve,
            )
        )

    assessment = assess_convergence(
        [r.record.complex_eigenfrequency_hz for r in results]
    )
    levels = tuple(
        ConvergenceLevelResult(
            mesh_cfg=mesh_cfg,
            complex_eigenfrequency_hz=r.record.complex_eigenfrequency_hz,
            mesh_element_count=r.record.mesh_element_count,
            from_cache=r.from_cache,
        )
        for mesh_cfg, r in zip(ladder, results)
    )
    return ConvergenceStudyResult(
        levels=levels, assessment=assessment, finest=results[-1]
    )


@dataclass(frozen=True)
class WallLossStudyResult:
    """§4 two-solve wall-loss split, sigma-carrying, on one geometry."""

    decomposition: WallLossDecomposition
    impedance: ConvergenceStudyResult
    pec: ConvergenceStudyResult


def run_wall_loss_study(
    geom: CavityGeometry,
    study: EigenStudyConfig,
    materials: MaterialSpec | None = None,
    base_mesh: MeshConfig = MeshConfig(),
    *,
    n_levels: int = 3,
    refine_factor: float = 2.0**0.5,
    grid_spec: GridSpec = GridSpec(),
    criteria: TE01DeltaCriteria = TE01DeltaCriteria(),
    client: Any = None,
    cache_root: Path | None = None,
    force_resolve: bool = False,
) -> WallLossStudyResult:
    """SPEC §4: same geometry, Impedance + PEC solves, existing
    `decompose_wall_loss` interface, sigmas from the two convergence
    ladders (never fabricated).

    `study.wall_bc` is ignored as a switch — both variants are derived
    from it so search frequency / mode count stay shared.
    """
    common = dict(
        materials=None,
        base_mesh=base_mesh,
        n_levels=n_levels,
        refine_factor=refine_factor,
        grid_spec=grid_spec,
        criteria=criteria,
        client=client,
        cache_root=cache_root,
        force_resolve=force_resolve,
    )
    impedance_study = replace(study, wall_bc=WallBC.IMPEDANCE)
    pec_study = replace(study, wall_bc=WallBC.PEC)
    base_materials = materials if materials is not None else MaterialSpec()

    impedance = run_convergence_study(
        geom,
        impedance_study,
        **{**common, "materials": material_spec_for(impedance_study, base_materials)},
    )
    pec = run_convergence_study(
        geom,
        pec_study,
        **{**common, "materials": material_spec_for(pec_study, base_materials)},
    )

    decomposition = decompose_wall_loss(
        impedance_result=impedance.finest.extraction,
        pec_result=pec.finest.extraction,
        sigma_q_impedance=impedance.sigma_q,
        sigma_q_pec=pec.sigma_q,
    )
    return WallLossStudyResult(
        decomposition=decomposition, impedance=impedance, pec=pec
    )
