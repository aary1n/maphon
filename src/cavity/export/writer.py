"""Bundle writer: a pure function of a §1 `SolveRecord`.

`export_bundle(record, out_dir)` consumes a persisted SolveRecord — the
SPEC §1 re-derivation path — so a COMSOL licence is needed only to MINT
records, never to export from them. The picked TE01delta mode is taken
from `record.picked_index` / `record.field_sample` (§2 field-symmetry
selection); nothing here re-picks modes or re-derives Q outside
`cavity.extraction.extract`.

Normalisation (schema decision 3): stored fields are scaled so the
total stored EM energy U = U_E + U_H = 1 J, with time-averaged
peak-phasor densities u_E = eps0 eps' |E|^2 / 4, u_H = mu0 |H|^2 / 4
integrated through the §3 Jacobian primitive. The raw COMSOL scale is
not discarded: `raw_total_energy_j` (and raw U_E, U_H) recover it.

Reproducibility (schema decision 6 + SPEC §1): the export layer adds
the exporter git commit AND a `git_dirty` flag from
`git status --porcelain` — a bundle minted from a dirty tree is NOT
reproducible from that commit alone, and the schema doc's metadata
glossary says so. Both are recorded-not-hashed, mirroring the
persistence layer's runtime-fact discipline (they describe the run,
they don't parameterise it). Git absence degrades to nulls, never to
an export failure.

Every bundle carries a copy of docs/field_export_schema.md
(FIELD_EXPORT_SCHEMA.md) so the handoff needs no repo access.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from importlib import metadata as importlib_metadata
from pathlib import Path

import numpy as np
from scipy.constants import epsilon_0 as EPS_0
from scipy.constants import mu_0 as MU_0

from cavity.extraction import extract
from cavity.extraction.quadrature import axisymmetric_volume_integral
from cavity.extraction.weights import (
    SpinProjection,
    cavity_arm_weight,
    spin_arm_weight,
)
from cavity.export.schema import (
    EXPORT_SCHEMA_VERSION,
    FIELDS_FILENAME,
    META_FILENAME,
    SCHEMA_DOC_FILENAME,
)
from cavity.forward_model.mode_id import TE01DeltaCriteria
from cavity.forward_model.persistence import SolveRecord, utc_timestamp
from cavity.provenance import DELOAD_K

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SCHEMA_DOC_SOURCE = _REPO_ROOT / "docs" / "field_export_schema.md"

_PACKAGE_NAME = "sto-maser-cavity"


def _git_state(repo_root: Path) -> tuple[str | None, bool | None]:
    """(commit, dirty) from git; (None, None) when git is unavailable.

    `dirty` is True when `git status --porcelain` reports anything —
    the Amendment-1 reproducibility flag (see module docstring).
    """
    try:
        head = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if head.returncode != 0:
            return None, None
        status = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=30,
        )
        dirty = (
            bool(status.stdout.strip()) if status.returncode == 0 else None
        )
        return head.stdout.strip(), dirty
    except (OSError, subprocess.SubprocessError):
        return None, None


def _package_version() -> str | None:
    try:
        return importlib_metadata.version(_PACKAGE_NAME)
    except importlib_metadata.PackageNotFoundError:
        return None


def _raw_stored_energies(field) -> tuple[float, float]:
    """(U_E, U_H) in joules at the raw COMSOL amplitude scale."""
    e2 = np.sum(np.abs(field.e_complex) ** 2, axis=1)
    h2 = np.sum(np.abs(field.h_complex) ** 2, axis=1)
    eps_real = np.real(field.eps_r_complex)
    # JACOBIAN: applied inside axisymmetric_volume_integral (both).
    u_e = (
        EPS_0
        / 4.0
        * float(
            np.real(
                axisymmetric_volume_integral(
                    eps_real * e2, field.r_m, field.weights_m2
                )
            )
        )
    )
    u_h = (
        MU_0
        / 4.0
        * float(
            np.real(
                axisymmetric_volume_integral(h2, field.r_m, field.weights_m2)
            )
        )
    )
    return u_e, u_h


def export_bundle(
    record: SolveRecord,
    out_dir: Path,
    *,
    projection: SpinProjection = SpinProjection.isotropic_h2(),
) -> Path:
    """Write one export bundle into `out_dir` (the bundle directory).

    Deterministic overwrite: re-exporting the same record into the same
    directory reproduces the same files (modulo the exporter timestamp
    and git state, which are runtime facts by design).
    """
    if not _SCHEMA_DOC_SOURCE.is_file():
        raise FileNotFoundError(
            f"schema document missing at {_SCHEMA_DOC_SOURCE} — every "
            "bundle must carry its own copy (self-containment is "
            "contract); the doc is the primary deliverable, restore it "
            "before exporting"
        )

    field = record.field_sample
    extraction = extract(field)  # cross-checks emw.Qfactor, computes p_e etc.

    u_e_raw, u_h_raw = _raw_stored_energies(field)
    raw_total = u_e_raw + u_h_raw
    if raw_total <= 0.0:
        raise ValueError("total stored EM energy non-positive — bad record")
    scale = 1.0 / np.sqrt(raw_total)

    cavity_arm = cavity_arm_weight(field)
    spin_arm = spin_arm_weight(field, projection)

    grid = record.fingerprint["grid"]
    n_r, n_z = int(grid["n_r"]), int(grid["n_z"])
    n = field.r_m.shape[0]
    if n_r * n_z != n:
        raise ValueError(
            f"fingerprint grid {n_r}x{n_z} inconsistent with {n} nodes"
        )

    gain_mask = field.effective_gain_mask
    gain_is_fallback = field.gain_region_mask is None

    arrays: dict[str, np.ndarray] = {
        "r_m": np.asarray(field.r_m, dtype=np.float64),
        "z_m": np.asarray(field.z_m, dtype=np.float64),
        "weights_m2": np.asarray(field.weights_m2, dtype=np.float64),
        "shape_rz": np.array([n_r, n_z], dtype=np.int64),
        "e_complex": np.asarray(
            field.e_complex * scale, dtype=np.complex128
        ),
        "h_complex": np.asarray(
            field.h_complex * scale, dtype=np.complex128
        ),
        "eps_r_complex": np.asarray(
            field.eps_r_complex, dtype=np.complex128
        ),
        "dielectric_mask": np.asarray(field.dielectric_mask, dtype=np.bool_),
        "gain_region_mask": np.asarray(gain_mask, dtype=np.bool_),
        "w_e_per_m3": cavity_arm.weight.values_per_m3,
        "w_spin_per_m3": spin_arm.weight.values_per_m3,
        "spectrum_f_real_hz": np.asarray(
            record.spectrum_f_real_hz, dtype=np.float64
        ),
        "spectrum_f_imag_hz": np.asarray(
            record.spectrum_f_imag_hz, dtype=np.float64
        ),
    }
    if record.spectrum_q_emw is not None:
        arrays["spectrum_q_emw"] = np.asarray(
            record.spectrum_q_emw, dtype=np.float64
        )

    criteria = TE01DeltaCriteria()
    git_commit, git_dirty = _git_state(_REPO_ROOT)

    status_notes = []
    if gain_is_fallback:
        status_notes.append(
            "SCHEMA EXAMPLE, not physics handoff: gain_region_mask is the "
            "STO-dielectric fallback (Phase 1b bore + pentacene crystal "
            "unbuilt) — spin-arm quantities describe the STO puck, NOT "
            "the pentacene gain region."
        )
    if record.fingerprint["materials"].get("wall_pec"):
        status_notes.append(
            "PEC-walled solve: no wall loss in Q; the impedance-walled "
            "variant is the SPEC §4 companion."
        )
    if git_dirty:
        status_notes.append(
            "exporter git tree was DIRTY at export time — this bundle is "
            "not reproducible from exporter_git_commit alone (see the "
            "schema doc's metadata glossary)."
        )

    meta = {
        "export_schema_version": EXPORT_SCHEMA_VERSION,
        "conventions": {
            "units": "SI throughout; coordinates m, fields V/m and A/m",
            "frequency": "cyclic hertz (Hz), NOT angular rad/s",
            "phasor": "exp(+i*omega*t); Im(f) > 0 means temporal decay",
            "permittivity": "eps_r = eps_r' * (1 - i*tan_delta)",
            "q_definition": (
                "Q = f'/(2 f'') from the bare complex eigenfrequency "
                "(SPEC section 11 item 4); consumed, never re-derived"
            ),
            "component_order": ["r", "phi", "z"],
            "azimuthal_index_m": 0,
            "volume_element": "dV = 2*pi*r dr dz",
            "grid_ordering": (
                "flattened 'ij': reshape (N,) arrays to shape_rz = "
                "(n_r, n_z); r varies slowest"
            ),
        },
        "normalisation": {
            "convention": "unit_total_stored_em_energy",
            "total_energy_j": 1.0,
            "raw_total_energy_j": raw_total,
            "raw_u_e_j": u_e_raw,
            "raw_u_h_j": u_h_raw,
            "u_e_fraction": u_e_raw / raw_total,
            "note": (
                "e_complex/h_complex are scaled by 1/sqrt("
                "raw_total_energy_j); multiply by sqrt(raw_total_energy_j) "
                "to recover raw COMSOL amplitudes. Densities: u_E = "
                "eps0*eps_r'*|E|^2/4, u_H = mu0*|H|^2/4 (time-averaged "
                "peak phasors). u_e_fraction ~ 0.5 is a mode-health "
                "diagnostic (U_E = U_H at resonance)."
            ),
        },
        "mode_selection": {
            "method": (
                "SPEC section 2 field-symmetry test (azimuthal-E "
                "dominance, on-axis Hz antinode, single axial lobe); "
                "proximity to search_hz used ONLY as a tiebreak among "
                "field-verified candidates — never a hardcoded index"
            ),
            "criteria": {
                "min_azimuthal_e_energy_fraction": (
                    criteria.min_azimuthal_e_energy_fraction
                ),
                "min_axis_hz_antinode_ratio": (
                    criteria.min_axis_hz_antinode_ratio
                ),
                "max_axis_hz_sign_changes": criteria.max_axis_hz_sign_changes,
                "axis_noise_floor_fraction": (
                    criteria.axis_noise_floor_fraction
                ),
            },
            "criteria_source": (
                "package defaults at export time — the SolveRecord meta "
                "(persistence schema 1) does not record the thresholds "
                "used at solve time"
            ),
            "picked_index_semantics": (
                "picked_index indexes the spectrum_* arrays; the "
                "solve.diagnostics list covers only candidates with "
                "Im(f) > 0, so its positions need not align with "
                "spectrum indices"
            ),
        },
        "weights": {
            "w_e_per_m3": {
                "definition": (
                    "w_E = eps'|E|^2 / int_STO eps'|E|^2 dV over "
                    "dielectric_mask; int w_E dV = 1"
                ),
                "companion_p_e": extraction.p_e,
                "note": (
                    "p_e (STO share of total electric energy) is carried "
                    "separately and never folded into the weight"
                ),
            },
            "w_spin_per_m3": {
                "definition": (
                    "w_s = |H_proj|^2 / int_gain |H_proj|^2 dV over "
                    "gain_region_mask; int w_s dV = 1"
                ),
                "projection": projection.to_meta(),
                "projection_rung": (
                    "isotropic |H|^2 default is literature-backed (Breeze "
                    "2017 npj QI 3, 40; arXiv:2412.21166 practice); "
                    "axis-projected variants implement Breeze's S_y "
                    "statement — derived, unratified"
                ),
                "gain_mask_is_fallback": gain_is_fallback,
                "h_phi_energy_share": spin_arm.h_phi_energy_share,
                "magnetic_filling_factor": spin_arm.magnetic_filling_factor,
            },
        },
        "q_loading": {
            "q_is_unloaded": True,
            "note": (
                "Q here is the eigensolve (unloaded, material+wall) "
                "quality factor; no coupling port is modelled. The "
                "Maxwell-Bloch kappa_c = 2*pi*f/Q_L (rad/s) needs the "
                "LOADED Q_L: de-load convention Q_0 = Q_L*(1 + k) with "
                f"k = {DELOAD_K} (Breeze 2017; Wu 2020 coupling unstated "
                "- SPEC section 11 item 3). The loaded/unloaded split is "
                "a flagged, separate pass — see the schema doc's kappa_c "
                "section and its W20 angular-'Hz' trap warning."
            ),
        },
        "solve": {
            "fingerprint": record.fingerprint,
            "record_hash": record.record_hash,
            "comsol_version": record.comsol_version,
            "mesh_element_count": record.mesh_element_count,
            "interface_tag": record.interface_tag,
            "picked_index": record.picked_index,
            "created_at_utc": record.created_at_utc,
            "diagnostics": record.diagnostics,
            "q_emw_cross_check": field.q_emw_cross_check,
        },
        "exporter": {
            "exported_at_utc": utc_timestamp(),
            "git_commit": git_commit,
            "git_dirty": git_dirty,
            "package": _PACKAGE_NAME,
            "package_version": _package_version(),
            "schema_doc": SCHEMA_DOC_FILENAME,
        },
        "summary": {
            "export_schema_version": EXPORT_SCHEMA_VERSION,
            "record_hash": record.record_hash,
            "f_real_hz": float(record.spectrum_f_real_hz[record.picked_index]),
            "f_imag_hz": float(record.spectrum_f_imag_hz[record.picked_index]),
            "q": extraction.q,
            "q_emw_cross_check": extraction.q_emw_cross_check,
            "p_e": extraction.p_e,
            "v_mode_global_m3": extraction.v_mode_global_m3,
            "v_mode_local_m3": extraction.v_mode_local_m3,
            "f_m_global": extraction.f_m_global,
            "f_m_local": extraction.f_m_local,
            "u_e_raw_j": u_e_raw,
            "u_h_raw_j": u_h_raw,
            "raw_total_energy_j": raw_total,
            "u_e_fraction": u_e_raw / raw_total,
            "h_phi_energy_share": spin_arm.h_phi_energy_share,
            "magnetic_filling_factor": spin_arm.magnetic_filling_factor,
            "gain_mask_is_fallback": gain_is_fallback,
            "spin_projection_mode": projection.to_meta()["mode"],
        },
        "status_notes": status_notes,
    }

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out_dir / FIELDS_FILENAME, **arrays)
    (out_dir / META_FILENAME).write_text(
        json.dumps(meta, indent=2, sort_keys=True), encoding="utf-8"
    )
    shutil.copyfile(_SCHEMA_DOC_SOURCE, out_dir / SCHEMA_DOC_FILENAME)
    return out_dir
