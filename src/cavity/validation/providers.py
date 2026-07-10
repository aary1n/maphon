"""Solve providers for the SPEC §5 gate — one gate code path, three
input sources.

The gate (`validation.gate`) never solves anything and never decides
where its inputs come from. A provider supplies each row's payload —
or `Unavailable(reason)`, which the gate reports as
`deferred_requires_comsol`. The judgment logic is therefore identical
for synthetic CI data, cached §1 solve records, and live COMSOL runs
(SPEC §1: CI never assumes a licence).

Providers:
  - `StaticProvider` — payloads handed in directly. The synthetic-CI
    provider, and the assembly target for cached data.
  - `provider_from_cache` — builds a StaticProvider from persisted
    SPEC §1 `SolveRecord`s (pure Python; extraction re-runs from the
    stored raw fields, no COMSOL).
  - `LiveComsolProvider` — runs real solves. Importable without MPh
    (imports of the solve stack are deferred to call time); actually
    calling the live rows needs a licence and is exercised only in
    the `requires_comsol` test tier. Live rows: the §8 empty-cavity
    TE011 anchor, the §8 PEC+lossy closed check, and — since the
    2026-07-10 geometry recovery closed SPEC §11 gap #1 — the
    Booth-geometry rows (f / Booth two-point / F_m / wall-loss split)
    via one §4 wall-loss study at the recovered torus. Only the
    confinement-trend row remains Unavailable (needs the §7 sweep).

Q convention note (SPEC §11 gap #4, resolved): providers hand the
gate `ExtractionResult`s whose `q` is already f'/(2 f'') from the bare
solver `freq`. Nothing here re-derives Q or reads imag(emw.freq).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from cavity.extraction import ExtractionResult, extract
from cavity.forward_model.geometry import CavityGeometry, DielectricShape
from cavity.forward_model.mesh import MeshConfig
from cavity.forward_model.persistence import load_solve_record
from cavity.provenance import (
    BOOTH_MPH_TAN_DELTA,
    GEOM_BOOTH_TE01D,
    TARGET,
    TARGETS,
)
from cavity.validation.wall_loss import WallLossDecomposition


def booth_recovered_geometry(
    minor_radius_m: float | None = None,
) -> CavityGeometry:
    """The recovered Booth TE01delta torus (SPEC §2, 2026-07-10;
    refs/booth_geometry_recovery.md), built from `GEOM_BOOTH_TE01D`.

    `minor_radius_m` defaults to the ratio-exact 2.456 mm (the gated
    value); pass `GEOM_BOOTH_TE01D.printed_minor_radius_m` for the
    printed-2.46 sensitivity solve.
    """
    if minor_radius_m is None:
        minor_radius_m = GEOM_BOOTH_TE01D.torus_minor_radius_m
    return CavityGeometry(
        box_radius_m=GEOM_BOOTH_TE01D.box_radius_m,
        box_height_m=GEOM_BOOTH_TE01D.box_height_m,
        dielectric_radius_m=GEOM_BOOTH_TE01D.torus_major_radius_m,
        dielectric_shape=DielectricShape.TORUS,
        dielectric_minor_radius_m=minor_radius_m,
    )


# §5a mesh ladder base: refinement_ladder(this, n_levels=5, sqrt(2))
# ends at 1.25e-4 / 5e-4 — the proven §2 e2e / frozen-anchor level.
BOOTH_LADDER_BASE_MESH = MeshConfig(
    dielectric_max_h_m=5.0e-4, air_max_h_m=2.0e-3
)
BOOTH_LADDER_N_LEVELS = 5
BOOTH_STUDY_N_MODES = 12


def booth_faithful_materials():
    """Faithful-reproduction material branch: eps_r' = 316.3 with the
    .mph-exact tan_delta (`BOOTH_MPH_TAN_DELTA` — ratified branch
    choice 1). The §5a Q/wall gates are judged on THIS branch; the
    canonical SPEC §2 branch (tan_delta = 1.1e-4) is the companion.

    Returns a base `MaterialSpec`; the §4 wall_pec switch is re-derived
    per arm by `runner.material_spec_for`.
    """
    from cavity.forward_model.materials import MaterialSpec
    from cavity.provenance.constants import STOSingleCrystal

    return MaterialSpec(
        sto=STOSingleCrystal(
            epsilon_r_real=TARGETS.booth.epsilon_r_real,
            tan_delta=BOOTH_MPH_TAN_DELTA,
        )
    )


# --- payloads ----------------------------------------------------------


@dataclass(frozen=True)
class Unavailable:
    """A row input this provider cannot supply, with the reason why.

    The gate maps this to status `deferred_requires_comsol` and copies
    `reason` into the check notes.
    """

    reason: str


@dataclass(frozen=True)
class EmptyCavityPayload:
    """§8 anchor input: the solved empty-cavity eigenspectrum plus the
    cavity dimensions the closed form is evaluated at."""

    spectrum_f_real_hz: tuple[float, ...]
    box_radius_m: float
    box_height_m: float


@dataclass(frozen=True)
class PecLossyPayload:
    """§8 Q-from-tan_delta input: extraction of a PEC-walled
    lossy-dielectric solve plus the tan_delta that solve used."""

    extraction: ExtractionResult
    tan_delta: float


@dataclass(frozen=True)
class BoothPayload:
    """Walls-on solve at Booth geometry. Judged by the f, Booth
    two-point and F_m rows (one payload, three rows — they collapse
    together to point-checks when Booth's .mph lands).

    `epsilon_r_real`: the eps_r the solve actually used, when known.
    The gate fails the Booth-anchored checks on a material mismatch —
    TARGETS.booth pairs its Q/V with eps_r = 316.3 (constants.py:
    pairing a target with the wrong eps_r chases a phantom ~14 MHz
    shift).
    """

    extraction: ExtractionResult
    epsilon_r_real: float | None = None


@dataclass(frozen=True)
class ConfinementPoint:
    """One (V_mode, Q) sample of the §5 confinement trend."""

    v_mode_m3: float
    q: float


@dataclass(frozen=True)
class ConfinementPayload:
    points: tuple[ConfinementPoint, ...]


@dataclass(frozen=True)
class WallLossPayload:
    """§4 two-solve decomposition output (sigma-carrying)."""

    decomposition: WallLossDecomposition


@dataclass(frozen=True)
class ReproducibilityMetadata:
    """SPEC §1 run log carried into every gate report.

    `rng_seed` is recorded even though the §5 gate has no stochastic
    stage (None + note), so the field is already in the schema when
    stochastic layers (§7) start writing reports.
    """

    rng_seed: int | None = None
    comsol_version: str | None = None
    mesh_settings: dict | None = None
    mesh_element_counts: tuple[int, ...] = ()
    solve_record_hashes: tuple[str, ...] = ()
    cache_root: str | None = None
    notes: str = ""


# --- provider contract --------------------------------------------------


@runtime_checkable
class SolveProvider(Protocol):
    """What the gate needs from any input source.

    Every method returns its payload or `Unavailable`. The gate calls
    `reproducibility()` last, so live providers can accumulate solve
    metadata while the row payloads are being produced.
    """

    kind: str

    def empty_cavity(self) -> EmptyCavityPayload | Unavailable: ...

    def pec_lossy(self) -> PecLossyPayload | Unavailable: ...

    def booth_walls_on(self) -> BoothPayload | Unavailable: ...

    def confinement_trend(self) -> ConfinementPayload | Unavailable: ...

    def wall_loss_split(self) -> WallLossPayload | Unavailable: ...

    def reproducibility(self) -> ReproducibilityMetadata: ...


_NOT_SUPPLIED = Unavailable("not supplied to this provider")


@dataclass
class StaticProvider:
    """Provider over payloads handed in directly.

    The synthetic-CI provider: tests construct payloads and check the
    gate's judgment. Also the assembly target for cached data
    (`provider_from_cache`). Every role defaults to Unavailable, so a
    bare StaticProvider() yields an all-deferred report with all six
    §5 rows present.
    """

    kind: str = "synthetic"
    empty_cavity_payload: EmptyCavityPayload | Unavailable = _NOT_SUPPLIED
    pec_lossy_payload: PecLossyPayload | Unavailable = _NOT_SUPPLIED
    booth_payload: BoothPayload | Unavailable = _NOT_SUPPLIED
    confinement_payload: ConfinementPayload | Unavailable = _NOT_SUPPLIED
    wall_loss_payload: WallLossPayload | Unavailable = _NOT_SUPPLIED
    repro: ReproducibilityMetadata = field(
        default_factory=lambda: ReproducibilityMetadata(
            notes=(
                "synthetic payloads; no stochastic stage in the §5 "
                "gate (rng_seed recorded as None)"
            )
        )
    )

    def empty_cavity(self) -> EmptyCavityPayload | Unavailable:
        return self.empty_cavity_payload

    def pec_lossy(self) -> PecLossyPayload | Unavailable:
        return self.pec_lossy_payload

    def booth_walls_on(self) -> BoothPayload | Unavailable:
        return self.booth_payload

    def confinement_trend(self) -> ConfinementPayload | Unavailable:
        return self.confinement_payload

    def wall_loss_split(self) -> WallLossPayload | Unavailable:
        return self.wall_loss_payload

    def reproducibility(self) -> ReproducibilityMetadata:
        return self.repro


def provider_from_cache(
    cache_root: Path,
    *,
    booth_hash: str | None = None,
    pec_lossy_hash: str | None = None,
) -> StaticProvider:
    """Assemble a provider from persisted SPEC §1 solve records.

    Pure Python: extraction re-runs from the stored raw fields (the §1
    re-derivation path), tan_delta / eps_r come from the record's
    fingerprint, and the reproducibility block carries the record
    hashes, COMSOL version(s), mesh settings and element counts.

    Rows without a supplied record stay Unavailable. The wall-loss and
    confinement rows cannot be reconstructed from single records (they
    need convergence sigmas / a sweep) and are not offered here.

    Raises:
        FileNotFoundError: if a supplied hash has no record under
            `cache_root` — a missing input must not silently demote a
            row to deferred.
    """
    cache_root = Path(cache_root)
    booth: BoothPayload | Unavailable = Unavailable(
        "no cached walls-on Booth-geometry record supplied"
    )
    pec: PecLossyPayload | Unavailable = Unavailable(
        "no cached PEC lossy-dielectric record supplied"
    )
    versions: list[str] = []
    counts: list[int] = []
    hashes: list[str] = []
    mesh_settings: dict[str, dict] = {}

    def _load(record_hash: str):
        record = load_solve_record(cache_root, record_hash)
        if record is None:
            raise FileNotFoundError(
                f"no SPEC §1 solve record {record_hash!r} under "
                f"{cache_root}"
            )
        versions.append(record.comsol_version)
        counts.append(record.mesh_element_count)
        hashes.append(record.record_hash)
        mesh_settings[record.record_hash] = record.fingerprint["mesh"]
        return record

    if booth_hash is not None:
        record = _load(booth_hash)
        booth = BoothPayload(
            extraction=extract(record.field_sample),
            epsilon_r_real=record.fingerprint["materials"][
                "sto_epsilon_r_real"
            ],
        )
    if pec_lossy_hash is not None:
        record = _load(pec_lossy_hash)
        pec = PecLossyPayload(
            extraction=extract(record.field_sample),
            tan_delta=record.fingerprint["materials"]["sto_tan_delta"],
        )

    repro = ReproducibilityMetadata(
        rng_seed=None,
        comsol_version="; ".join(dict.fromkeys(versions)) or None,
        mesh_settings=mesh_settings or None,
        mesh_element_counts=tuple(counts),
        solve_record_hashes=tuple(hashes),
        cache_root=str(cache_root),
        notes=(
            "assembled from SPEC §1 cached solve records; extraction "
            "re-run from persisted raw fields (no COMSOL); no "
            "stochastic stage in the §5 gate"
        ),
    )
    return StaticProvider(
        kind="cached",
        booth_payload=booth,
        pec_lossy_payload=pec,
        repro=repro,
    )


class LiveComsolProvider:
    """Live-solve provider (requires_comsol tier).

    Wired live:
      - `empty_cavity()` — the §8 TE011 anchor, the exact build path
        of the existing live anchor test (vacuum 'dielectric', PEC
        walls, ~lambda/24 mesh at the closed-form frequency). The raw
        complex eigenspectrum is persisted under `solve_root` when
        one is given (SPEC §1).
      - `pec_lossy()` — the §8 Q-from-tan_delta closed check on a
        real PEC + lossy-STO solve. Geometry-independent, so it runs
        at the assumed a/L = 0.5 puck; search near the Kajfez ~3.1 GHz
        estimate, exactly like the live §2 e2e test. Runs through
        `run_forward_model`, so the full §1 SolveRecord (raw complex
        eigensolution + fields) lands under `solve_root`.
      - `booth_walls_on()` / `wall_loss_split()` — WIRED LIVE since the
        2026-07-10 geometry recovery closed SPEC §11 gap #1
        (refs/booth_geometry_recovery.md): ONE `run_wall_loss_study`
        at the recovered torus (`booth_recovered_geometry`), faithful
        material branch (`booth_faithful_materials` — ratified branch
        choice 1), 5-level sqrt(2) ladder from `BOOTH_LADDER_BASE_MESH`
        (finest = 1.25e-4/5e-4, the frozen-anchor level), shared by
        both rows (run_gate fetches the Booth payload once). Sigmas
        come from the per-arm convergence ladders; a non-asymptotic
        ladder raises `ConvergenceError` OUT of the provider — the §5a
        failure discipline forbids converting it to a deferred row.

    Not wired (returns Unavailable with the blocking reason):
      - `confinement_trend`: needs the §7 parametric sweep.
    """

    kind = "live_comsol"

    def __init__(
        self,
        client: Any = None,
        *,
        solve_root: Path | None = None,
        empty_cavity_mesh_h_m: float = 4.0e-4,
        n_modes: int = 10,
        pec_lossy_mesh: MeshConfig | None = None,
        pec_lossy_search_hz: float = 3.1e9,
        pec_lossy_n_modes: int = 12,
        booth_base_mesh: MeshConfig | None = None,
        booth_n_levels: int = BOOTH_LADDER_N_LEVELS,
        booth_refine_factor: float = 2.0**0.5,
        booth_n_modes: int = BOOTH_STUDY_N_MODES,
        booth_cache_root: Path | None = None,
        save_mph_dir: Path | None = None,
    ) -> None:
        self._client = client
        self._solve_root = None if solve_root is None else Path(solve_root)
        self._mesh_h_m = empty_cavity_mesh_h_m
        self._n_modes = n_modes
        # Default = the finest ladder level of the live §2 e2e test
        # (base 5e-4/2e-3 refined 4x). Live status (2026-07-06): the
        # §8 closed check CLEARS the 0.5% tolerance at this level — a
        # convention pass at level N, not a mesh-independence proof
        # (that is §2's job). Refine only if the check regresses.
        self._pec_mesh = pec_lossy_mesh or MeshConfig(
            dielectric_max_h_m=1.25e-4, air_max_h_m=5.0e-4
        )
        self._pec_search_hz = pec_lossy_search_hz
        self._pec_n_modes = pec_lossy_n_modes
        self._booth_base_mesh = booth_base_mesh or BOOTH_LADDER_BASE_MESH
        self._booth_n_levels = booth_n_levels
        self._booth_refine_factor = booth_refine_factor
        self._booth_n_modes = booth_n_modes
        self._booth_cache_root = (
            None if booth_cache_root is None else Path(booth_cache_root)
        )
        self._save_mph_dir = (
            None if save_mph_dir is None else Path(save_mph_dir)
        )
        self._booth_study_result: Any = None  # WallLossStudyResult memo
        self._booth_unavailable: Unavailable | None = None
        self._comsol_version: str | None = None
        self._element_counts: list[int] = []
        self._mesh_settings: dict[str, dict] = {}
        self._record_hashes: list[str] = []
        self._notes: list[str] = []

    def empty_cavity(self) -> EmptyCavityPayload | Unavailable:
        # Deferred imports: this module must import without MPh
        # (SPEC §1); only actually solving needs the licence.
        import numpy as np

        from cavity.forward_model.build import (
            build_model,
            mesh_element_count,
        )
        from cavity.forward_model.geometry import (
            CavityGeometry,
            DielectricShape,
        )
        from cavity.forward_model.materials import MaterialSpec
        from cavity.forward_model.mesh import MeshConfig
        from cavity.forward_model.solve import evaluate_eigen_spectrum
        from cavity.forward_model.study import EigenStudyConfig, WallBC
        from cavity.provenance import GEOM
        from cavity.provenance.constants import STOSingleCrystal
        from cavity.validation.analytic import f_te_mnp

        f_analytic = f_te_mnp(
            0, 1, 1, GEOM.box_radius_m, GEOM.box_height_m
        )
        # The §2 builder needs a dielectric region; setting it to
        # vacuum makes the solve a genuinely empty PEC box (same
        # device as the live anchor test).
        geom = CavityGeometry.from_nominal(
            DielectricShape.PUCK,
            dielectric_height_m=2.0 * GEOM.dielectric_radius_m,
        )
        vacuum = MaterialSpec(
            sto=STOSingleCrystal(
                epsilon_r_real=1.0, tan_delta=0.0, mu_r=1.0, sigma=0.0
            ),
            wall_pec=True,
        )
        study = EigenStudyConfig(
            wall_bc=WallBC.PEC,
            search_hz=f_analytic,
            n_modes=self._n_modes,
        )
        mesh_cfg = MeshConfig(
            dielectric_max_h_m=self._mesh_h_m,
            air_max_h_m=self._mesh_h_m,
        )

        built = build_model(
            geom, vacuum, mesh_cfg, study, client=self._client
        )
        try:
            built.model.mesh(built.mesh)
            built.model.solve(built.study)
            spectrum = evaluate_eigen_spectrum(
                built.model, built.interface_tag
            )
            self._comsol_version = built.comsol_version
            self._element_counts.append(mesh_element_count(built.mesh))
            self._mesh_settings["empty_cavity_te011"] = {
                "dielectric_max_h_m": mesh_cfg.dielectric_max_h_m,
                "air_max_h_m": mesh_cfg.air_max_h_m,
            }
        finally:
            try:
                built.client.remove(built.model)
            except Exception:
                pass  # cleanup only

        if self._solve_root is not None:
            self._solve_root.mkdir(parents=True, exist_ok=True)
            out = self._solve_root / "empty_cavity_te011.npz"
            np.savez_compressed(
                out,
                f_real_hz=spectrum.f_real_hz,
                f_imag_hz=spectrum.f_imag_hz,
            )
            self._notes.append(
                f"raw empty-cavity eigenspectrum persisted to {out}"
            )

        return EmptyCavityPayload(
            spectrum_f_real_hz=tuple(
                float(f) for f in spectrum.f_real_hz
            ),
            box_radius_m=GEOM.box_radius_m,
            box_height_m=GEOM.box_height_m,
        )

    def pec_lossy(self) -> PecLossyPayload | Unavailable:
        # Deferred imports, same rationale as empty_cavity().
        from cavity.forward_model.build import ComsolUnavailable
        from cavity.forward_model.geometry import (
            CavityGeometry,
            DielectricShape,
        )
        from cavity.forward_model.runner import (
            material_spec_for,
            run_forward_model,
        )
        from cavity.forward_model.study import EigenStudyConfig, WallBC
        from cavity.provenance import GEOM

        # Assumed a/L = 0.5 puck (gap #1): fine here — the §8 closed
        # check Q = 1/(p_e * tan_delta) is geometry-independent; only
        # the Booth-anchored rows need the true cross-section.
        geom = CavityGeometry.from_nominal(
            DielectricShape.PUCK,
            dielectric_height_m=2.0 * GEOM.dielectric_radius_m,
        )
        study = EigenStudyConfig(
            wall_bc=WallBC.PEC,
            search_hz=self._pec_search_hz,
            n_modes=self._pec_n_modes,
        )
        # wall_pec=True + real STO (eps_r 316.3, tan_delta 1.1e-4).
        materials = material_spec_for(study)

        try:
            result = run_forward_model(
                geom,
                study,
                materials,
                self._pec_mesh,
                client=self._client,
                cache_root=self._solve_root,
            )
        except ComsolUnavailable as exc:
            return Unavailable(
                f"MPh/COMSOL unavailable on this host: {exc}"
            )

        record = result.record
        self._comsol_version = record.comsol_version
        self._element_counts.append(record.mesh_element_count)
        self._mesh_settings["pec_lossy"] = dict(record.fingerprint["mesh"])
        self._record_hashes.append(record.record_hash)
        if self._solve_root is not None:
            self._notes.append(
                "PEC+lossy §1 SolveRecord "
                f"{record.record_hash} persisted under "
                f"{self._solve_root}"
            )
        return PecLossyPayload(
            extraction=result.extraction,
            tan_delta=materials.sto.tan_delta,
        )

    def _ensure_booth_study(self) -> Any:
        """Run (or reuse) the ONE §5a wall-loss study behind both Booth
        rows. Returns WallLossStudyResult or Unavailable.

        `ConvergenceError` propagates: a non-asymptotic ladder is a §5a
        STOP condition (failure-report path), never a deferred row.
        """
        if self._booth_unavailable is not None:
            return self._booth_unavailable
        if self._booth_study_result is not None:
            return self._booth_study_result

        # Deferred imports, same rationale as empty_cavity().
        from cavity.forward_model.build import ComsolUnavailable
        from cavity.forward_model.runner import run_wall_loss_study
        from cavity.forward_model.study import EigenStudyConfig, WallBC

        geom = booth_recovered_geometry()
        study = EigenStudyConfig(
            wall_bc=WallBC.IMPEDANCE,
            search_hz=TARGET.f_design_hz,
            n_modes=self._booth_n_modes,
        )
        cache_root = (
            self._booth_cache_root
            if self._booth_cache_root is not None
            else self._solve_root
        )
        try:
            result = run_wall_loss_study(
                geom,
                study,
                materials=booth_faithful_materials(),
                base_mesh=self._booth_base_mesh,
                n_levels=self._booth_n_levels,
                refine_factor=self._booth_refine_factor,
                client=self._client,
                cache_root=cache_root,
                save_mph_dir=self._save_mph_dir,
            )
        except ComsolUnavailable as exc:
            self._booth_unavailable = Unavailable(
                f"MPh/COMSOL unavailable on this host: {exc}"
            )
            return self._booth_unavailable

        self._booth_study_result = result
        for arm_name, arm in (
            ("booth_impedance", result.impedance),
            ("booth_pec", result.pec),
        ):
            finest = arm.finest.record
            self._comsol_version = finest.comsol_version
            self._record_hashes.append(finest.record_hash)
            self._mesh_settings[arm_name] = dict(
                finest.fingerprint["mesh"]
            )
            self._element_counts.extend(
                lvl.mesh_element_count for lvl in arm.levels
            )
        if cache_root is not None:
            self._notes.append(
                "§5a Booth wall-loss study (faithful branch, "
                f"{self._booth_n_levels}-level ladder x 2 arms) records "
                f"under {cache_root}"
            )
        return result

    @property
    def booth_study(self) -> Any:
        """The memoised §5a WallLossStudyResult (faithful branch), or
        None if the Booth rows have not been produced yet. The §5a
        driver reads this to build the checkpoint manifest without
        re-running the study."""
        return self._booth_study_result

    def booth_walls_on(self) -> BoothPayload | Unavailable:
        study = self._ensure_booth_study()
        if isinstance(study, Unavailable):
            return study
        finest = study.impedance.finest
        return BoothPayload(
            extraction=finest.extraction,
            epsilon_r_real=finest.record.fingerprint["materials"][
                "sto_epsilon_r_real"
            ],
        )

    def confinement_trend(self) -> ConfinementPayload | Unavailable:
        return Unavailable(
            "requires the §7 parametric confinement sweep — "
            "deliberately not implemented in this pass (SPEC §5 "
            "gate scope)."
        )

    def wall_loss_split(self) -> WallLossPayload | Unavailable:
        study = self._ensure_booth_study()
        if isinstance(study, Unavailable):
            return study
        return WallLossPayload(decomposition=study.decomposition)

    def reproducibility(self) -> ReproducibilityMetadata:
        return ReproducibilityMetadata(
            rng_seed=None,
            comsol_version=self._comsol_version,
            mesh_settings=self._mesh_settings or None,
            mesh_element_counts=tuple(self._element_counts),
            solve_record_hashes=tuple(self._record_hashes),
            cache_root=(
                None if self._solve_root is None else str(self._solve_root)
            ),
            notes="; ".join(
                self._notes
                + [
                    "live COMSOL provider; no stochastic stage in "
                    "the §5 gate"
                ]
            ),
        )


__all__ = [
    "BOOTH_LADDER_BASE_MESH",
    "BOOTH_LADDER_N_LEVELS",
    "BOOTH_STUDY_N_MODES",
    "BoothPayload",
    "ConfinementPayload",
    "ConfinementPoint",
    "EmptyCavityPayload",
    "LiveComsolProvider",
    "PecLossyPayload",
    "ReproducibilityMetadata",
    "SolveProvider",
    "StaticProvider",
    "Unavailable",
    "WallLossPayload",
    "booth_faithful_materials",
    "booth_recovered_geometry",
    "provider_from_cache",
]
