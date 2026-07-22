"""SPEC §2 / §3 — eigenfrequency solve, mode-ID, field export.

MPh conventions here are the PROVEN ones from
tests/test_comsol_mph_server.py and nothing beyond them:

  - `model.evaluate(expression)` returns float64 arrays ONLY. The
    complex eigenfrequency is assembled in Python from `real(freq)`
    and `imag(freq)`; there is no `complex=True` argument and none is
    invented.
  - The eigenfrequency is read from the BARE solver variable `freq`
    (= i*lambda/(2*pi), complex), NOT from the interface-scoped
    `<tag>.freq`: in results evaluation COMSOL realifies the
    interface variable per solution number, so `imag(<tag>.freq)`
    reads identically 0 on a lossy solve. That artifact is exactly
    the retracted 2026-07 probe bug (SPEC §11 gap #4); pinned
    empirically 2026-07-03 on the booth lossy reference, where
    f'/(2 f'') from bare `freq` reproduces emw.Qfactor exactly,
    mode by mode.
  - The physics interface tag is a parameter (default "emw"), never
    hardcoded — a supervisor model with a non-emw interface has been
    observed. For models built by `build.py` the tag is read off the
    created node (`BuiltModel.interface_tag`).

Mode identification is by field pattern (`mode_id`), never eigenvalue
proximity: the lossy reference spectrum has modes ~70 MHz apart near
1.45 GHz, so the nearest eigenvalue is routinely the wrong mode.

Field export path (SPEC §3 second permitted path): nodal fields are
evaluated at the solver's own points, resampled onto a structured
(r, z) grid with explicit trapezoid weights (`gridding`), and packed
into the extraction layer's `FieldSample`. Q, V_mode, p_e and F_m are
then computed by the EXISTING `cavity.extraction.extract` — nothing is
re-derived here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from numpy.typing import NDArray

from cavity.extraction import FieldSample
from cavity.forward_model.build import BuiltModel, mesh_element_count
from cavity.forward_model.geometry import CavityGeometry
from cavity.forward_model.gridding import GridSpec, StructuredGrid
from cavity.forward_model.materials import MaterialSpec
from cavity.forward_model.mode_id import (
    ModeDiagnostics,
    ModeIdentificationError,
    TE01DeltaCriteria,
    compute_mode_diagnostics,
    identify_te01delta,
)
from cavity.forward_model.study import EigenStudyConfig

_E_COMPONENTS = ("Er", "Ephi", "Ez")
_H_COMPONENTS = ("Hr", "Hphi", "Hz")


@dataclass(frozen=True)
class EigenResult:
    """One eigenpair from a §2 solve.

    `complex_eigenfrequency_hz`: f' + i f''. Q computed below per SPEC §3
    (Q = f' / (2 f''); the sign convention is supervisor-confirmed and
    §8-guarded — SPEC §11 gap #4, resolved 2026-07-02).

    `mesh_element_count` and `comsol_version` are recorded with every
    solve for SPEC §1 reproducibility.

    `field_handle`: the §3 `FieldSample` exported from the solve (None
    for synthetic constructions that only exercise the Q arithmetic).
    """

    complex_eigenfrequency_hz: complex
    mesh_element_count: int
    comsol_version: str
    field_handle: Any = None

    @property
    def f_real_hz(self) -> float:
        return self.complex_eigenfrequency_hz.real

    @property
    def f_imag_hz(self) -> float:
        return self.complex_eigenfrequency_hz.imag

    @property
    def q_factor(self) -> float:
        """Q = f' / (2 f'') per SPEC §3.

        Guarded by the §8 1/(p_e * tan_delta) closed form. If COMSOL
        returns Im(f) <= 0 the convention is inverted and the result
        must not flow downstream silently.
        """
        if self.f_imag_hz <= 0:
            raise ValueError(
                "Im(f) must be > 0 for Q = f'/(2 f''); got "
                f"{self.f_imag_hz}. Check COMSOL eigenvalue sign "
                "convention (SPEC §8 + §11 gap #4)."
            )
        return self.f_real_hz / (2.0 * self.f_imag_hz)


@dataclass(frozen=True)
class EigenSpectrum:
    """Raw eigenfrequency table from one solve (all candidates).

    Assembled from float64 `real(freq)` / `imag(freq)` evaluations of
    the bare solver variable (the interface-scoped `<tag>.freq` is
    realified in results evaluation — see module docstring). `q_emw`
    echoes the interface's built-in Qfactor when the model exposes it
    (cross-check only, never the primary Q).
    """

    f_real_hz: NDArray[np.float64]
    f_imag_hz: NDArray[np.float64]
    q_emw: NDArray[np.float64] | None = None

    def __post_init__(self) -> None:
        if self.f_real_hz.shape != self.f_imag_hz.shape:
            raise ValueError("real/imag eigenfrequency arrays must match")
        if self.q_emw is not None and self.q_emw.shape != self.f_real_hz.shape:
            raise ValueError("q_emw array must match the eigenfrequencies")

    def __len__(self) -> int:
        return int(self.f_real_hz.shape[0])

    def complex_at(self, index: int) -> complex:
        return complex(self.f_real_hz[index], self.f_imag_hz[index])


def _as_float64_modes(raw: Any) -> NDArray[np.float64]:
    """Coerce an mph evaluate() result to a 1D float64 mode array.

    The proven convention is float64-only output; anything complex
    coming back means the evaluation path changed and must be looked at
    rather than silently cast.
    """
    arr = np.asarray(raw)
    if np.iscomplexobj(arr):
        raise TypeError(
            "model.evaluate() returned a complex array; the proven MPh "
            "convention (tests/test_comsol_mph_server.py) is float64 "
            "only — assemble complex quantities from real()/imag() "
            "expressions instead."
        )
    return np.atleast_1d(arr.astype(np.float64))


def evaluate_eigen_spectrum(
    model: Any, interface_tag: str = "emw"
) -> EigenSpectrum:
    """All eigenfrequencies of the solved model, complex-assembled in
    Python per the proven MPh convention.

    Bare `freq`, not `{interface_tag}.freq`: the interface variable is
    realified per solution number in results evaluation and its imag
    part reads 0 — the retracted probe-bug path (module docstring).
    `interface_tag` is still needed for the Qfactor cross-check.
    """
    f_re = _as_float64_modes(model.evaluate("real(freq)"))
    f_im = _as_float64_modes(model.evaluate("imag(freq)"))
    q_emw: NDArray[np.float64] | None
    try:
        q_emw = _as_float64_modes(model.evaluate(f"{interface_tag}.Qfactor"))
    except Exception:
        q_emw = None  # not every model/version exposes Qfactor
    return EigenSpectrum(f_real_hz=f_re, f_imag_hz=f_im, q_emw=q_emw)


@dataclass(frozen=True)
class NodalModeFields:
    """Per-mode complex E/H at the solver's own evaluation points.

    `e_complex` / `h_complex`: (n_modes, N, 3) with components ordered
    (r, phi, z) — the `FieldSample` convention.
    """

    r_m: NDArray[np.float64]
    z_m: NDArray[np.float64]
    e_complex: NDArray[np.complex128]
    h_complex: NDArray[np.complex128]

    @property
    def n_modes(self) -> int:
        return int(self.e_complex.shape[0])


def _field_rows(raw: Any, n_modes: int, what: str) -> NDArray[np.float64]:
    """Coerce a nodal field evaluation to shape (n_modes, N)."""
    arr = np.asarray(raw)
    if np.iscomplexobj(arr):
        raise TypeError(
            f"complex array returned for {what}; expected float64 "
            "(see _as_float64_modes)"
        )
    arr = arr.astype(np.float64)
    if arr.ndim == 1:
        arr = arr[np.newaxis, :]
    if arr.ndim != 2 or arr.shape[0] != n_modes:
        raise ValueError(
            f"nodal evaluation for {what} has shape {arr.shape}; "
            f"expected ({n_modes}, N)"
        )
    return arr


def export_nodal_fields(
    model: Any, n_modes: int, interface_tag: str = "emw"
) -> NodalModeFields:
    """Evaluate E and H (complex, all modes) at the solver's points.

    Every expression is real()/imag()-wrapped — float64 in, complex
    assembled here. CRITICAL: coordinates and all twelve field
    expressions go through ONE `model.evaluate([...])` call. MPh backs
    each evaluate() call with its own COMSOL Eval feature, and separate
    features pick their own evaluation point sets (the point count
    follows the expression's element order — curl-element fields land
    on more points than the linear geometry coordinates). A single
    call = a single feature = one shared point set, so field rows and
    coordinates stay aligned. Pinned live on COMSOL 6.0, 2026-07-03.
    """
    expressions = ["r", "z"]
    for name in (*_E_COMPONENTS, *_H_COMPONENTS):
        expressions.append(f"real({interface_tag}.{name})")
        expressions.append(f"imag({interface_tag}.{name})")
    results = model.evaluate(expressions)

    r_raw = np.asarray(results[0], dtype=np.float64)
    z_raw = np.asarray(results[1], dtype=np.float64)
    # Coordinates repeat identically per mode; keep one row.
    r_m = r_raw[0] if r_raw.ndim == 2 else r_raw
    z_m = z_raw[0] if z_raw.ndim == 2 else z_raw
    n_points = r_m.shape[0]

    def complex_component(index: int) -> NDArray[np.complex128]:
        pos = 2 + 2 * index
        re = _field_rows(results[pos], n_modes, expressions[pos])
        im = _field_rows(results[pos + 1], n_modes, expressions[pos + 1])
        if re.shape[1] != n_points:
            raise ValueError(
                f"{expressions[pos]}: {re.shape[1]} points vs "
                f"{n_points} coordinates despite the joint evaluation"
            )
        return re + 1j * im

    e = np.stack([complex_component(k) for k in range(3)], axis=-1)
    h = np.stack([complex_component(k) for k in range(3, 6)], axis=-1)
    return NodalModeFields(r_m=r_m, z_m=z_m, e_complex=e, h_complex=h)


def resample_modes_to_grid(
    nodal: NodalModeFields, grid: StructuredGrid
) -> tuple[NDArray[np.complex128], NDArray[np.complex128]]:
    """Linear-resample every mode's E/H onto the §3 structured grid.

    COMSOL's evaluation points are unstructured and duplicated across
    element boundaries; the first duplicate wins (fields discontinuous
    at the dielectric interface are one-sided there — the same one-cell
    smear any nodal export carries). Grid points that fall marginally
    outside the Delaunay hull (float wobble on the box edges) fall back
    to nearest-neighbour values.
    """
    from scipy.interpolate import LinearNDInterpolator, NearestNDInterpolator
    from scipy.spatial import Delaunay

    points = np.column_stack([nodal.r_m, nodal.z_m])
    unique_points, unique_idx = np.unique(points, axis=0, return_index=True)
    tri = Delaunay(unique_points)
    grid_points = np.column_stack([grid.r_m, grid.z_m])

    def resample_component(values: NDArray) -> NDArray[np.complex128]:
        out = np.empty(grid_points.shape[0], dtype=np.complex128)
        parts = []
        for part in (np.real(values), np.imag(values)):
            data = np.ascontiguousarray(part[unique_idx])
            interp = LinearNDInterpolator(tri, data)
            sampled = interp(grid_points)
            missing = np.isnan(sampled)
            if np.any(missing):
                nearest = NearestNDInterpolator(unique_points, data)
                sampled[missing] = nearest(grid_points[missing])
            parts.append(sampled)
        out[:] = parts[0] + 1j * parts[1]
        return out

    n_modes = nodal.n_modes
    e_grid = np.empty((n_modes, grid.n_nodes, 3), dtype=np.complex128)
    h_grid = np.empty((n_modes, grid.n_nodes, 3), dtype=np.complex128)
    for k in range(n_modes):
        for c in range(3):
            e_grid[k, :, c] = resample_component(nodal.e_complex[k, :, c])
            h_grid[k, :, c] = resample_component(nodal.h_complex[k, :, c])
    return e_grid, h_grid


@dataclass(frozen=True)
class SolvedTE01Delta:
    """Everything one §2 solve hands downstream.

    `eigen.field_handle` is the picked mode's `FieldSample`; feed it to
    `cavity.extraction.extract` for f, Q, V_mode (both variants), p_e
    and F_m. `spectrum`, `diagnostics` and `picked_index` keep the full
    candidate table auditable (SPEC §1: raw solutions, not just
    scalars).
    """

    eigen: EigenResult
    field_sample: FieldSample
    spectrum: EigenSpectrum
    picked_index: int
    diagnostics: tuple[ModeDiagnostics, ...]
    candidate_indices: tuple[int, ...]


def solve_eigenfrequency(
    built: BuiltModel,
    geom: CavityGeometry,
    materials: MaterialSpec,
    study: EigenStudyConfig,
    *,
    grid_spec: GridSpec = GridSpec(),
    criteria: TE01DeltaCriteria = TE01DeltaCriteria(),
    run_mesh: bool = True,
) -> SolvedTE01Delta:
    """Mesh (optionally), solve, export fields, and identify TE01delta.

    The returned mode is chosen by the SPEC §2 field-symmetry test —
    reject-and-re-pick over the whole candidate list, raising
    `ModeIdentificationError` if nothing passes. Candidates with
    Im(f) <= 0 (conjugate/spurious eigenpairs) are excluded up front;
    the survivors' proximity to `study.search_hz` only ever breaks
    ties among field-verified candidates.
    """
    model = built.model
    if run_mesh:
        model.mesh(built.mesh)
    model.solve(built.study)

    spectrum = evaluate_eigen_spectrum(model, built.interface_tag)
    nodal = export_nodal_fields(
        model, n_modes=len(spectrum), interface_tag=built.interface_tag
    )
    grid = grid_spec.build(geom.box_radius_m, geom.box_height_m)
    e_grid, h_grid = resample_modes_to_grid(nodal, grid)

    candidate_indices = tuple(
        int(k) for k in range(len(spectrum)) if spectrum.f_imag_hz[k] > 0.0
    )
    if not candidate_indices:
        raise ModeIdentificationError(
            "no eigenpair has Im(f) > 0 — all returned modes are "
            "conjugate/spurious under the confirmed sign convention. "
            f"Spectrum: {spectrum.f_real_hz + 1j * spectrum.f_imag_hz}"
        )
    diagnostics = tuple(
        compute_mode_diagnostics(
            spectrum.complex_at(k),
            e_grid[k],
            h_grid[k],
            grid.r_m,
            grid.z_m,
            grid.weights_m2,
            axis_noise_floor_fraction=criteria.axis_noise_floor_fraction,
        )
        for k in candidate_indices
    )
    picked_local = identify_te01delta(
        list(diagnostics), study.search_hz, criteria
    )
    picked = candidate_indices[picked_local]

    dielectric_mask = geom.dielectric_mask(grid.r_m, grid.z_m)
    eps_r = np.where(
        dielectric_mask,
        materials.sto_complex_eps_r,
        complex(1.0, 0.0),
    ).astype(np.complex128)
    spacer_mask = None
    if geom.spacer is not None:
        # The exported eps map must describe the SOLVED model: spacer
        # nodes carry the seat permittivity, never air (2026-07-18).
        spacer_mask = geom.spacer_mask(grid.r_m, grid.z_m)
        eps_r = np.where(
            spacer_mask, materials.spacer_complex_eps_r, eps_r
        ).astype(np.complex128)
    gain_region_mask = None
    if geom.crystal_radius_m is not None:
        # SPEC §5b (2026-07-22): crystal nodes carry the crystal
        # permittivity, and the crystal IS the Phase 1b gain region —
        # V_mode local normalises at the field the spins see.
        gain_region_mask = geom.crystal_mask(grid.r_m, grid.z_m)
        eps_r = np.where(
            gain_region_mask, materials.crystal_complex_eps_r, eps_r
        ).astype(np.complex128)

    q_cross = (
        float(spectrum.q_emw[picked]) if spectrum.q_emw is not None else None
    )
    field_sample = FieldSample(
        r_m=grid.r_m,
        z_m=grid.z_m,
        e_complex=e_grid[picked],
        h_complex=h_grid[picked],
        eps_r_complex=eps_r,
        weights_m2=grid.weights_m2,
        dielectric_mask=dielectric_mask,
        complex_eigenfrequency_hz=spectrum.complex_at(picked),
        q_emw_cross_check=q_cross,
        spacer_mask=spacer_mask,
        gain_region_mask=gain_region_mask,
    )
    eigen = EigenResult(
        complex_eigenfrequency_hz=spectrum.complex_at(picked),
        mesh_element_count=mesh_element_count(built.mesh),
        comsol_version=built.comsol_version,
        field_handle=field_sample,
    )
    return SolvedTE01Delta(
        eigen=eigen,
        field_sample=field_sample,
        spectrum=spectrum,
        picked_index=picked,
        diagnostics=diagnostics,
        candidate_indices=candidate_indices,
    )
