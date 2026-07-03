"""SPEC §1 — persist raw solve outputs keyed by parameter hash.

Raw complex eigen-solutions (full spectrum + the picked mode's exported
fields), not just scalars, are stored so §3 extraction can be re-run
without re-solving. Every record logs the COMSOL version, the mesh
level (the full `MeshConfig`), and the element count.

Layout: `<root>/<hash>/meta.json` + `<root>/<hash>/fields.npz`, where
`<hash>` is a SHA-256 digest of the canonical JSON fingerprint of every
input that determines the solution (geometry, materials, mesh, study,
export grid, schema version). Runtime facts (COMSOL version, element
count, timestamps) are logged in the record but excluded from the hash
— they describe the run, they don't parameterise it.

Pure Python — loading a cached record and extracting from it needs no
COMSOL licence.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from cavity.extraction import FieldSample
from cavity.forward_model.geometry import CavityGeometry
from cavity.forward_model.gridding import GridSpec
from cavity.forward_model.materials import MaterialSpec
from cavity.forward_model.mesh import MeshConfig
from cavity.forward_model.study import EigenStudyConfig

SCHEMA_VERSION = 1

_META_FILENAME = "meta.json"
_FIELDS_FILENAME = "fields.npz"


def solve_fingerprint(
    geom: CavityGeometry,
    materials: MaterialSpec,
    mesh_cfg: MeshConfig,
    study: EigenStudyConfig,
    grid_spec: GridSpec,
) -> dict:
    """Canonical, JSON-able description of one solve's inputs."""
    return {
        "schema_version": SCHEMA_VERSION,
        "geometry": {
            "shape": geom.dielectric_shape.value,
            "box_radius_m": geom.box_radius_m,
            "box_height_m": geom.box_height_m,
            "dielectric_radius_m": geom.dielectric_radius_m,
            "dielectric_height_m": geom.dielectric_height_m,
            "dielectric_minor_radius_m": geom.dielectric_minor_radius_m,
        },
        "materials": {
            "sto_epsilon_r_real": materials.sto.epsilon_r_real,
            "sto_tan_delta": materials.sto.tan_delta,
            "sto_mu_r": materials.sto.mu_r,
            "sto_sigma": materials.sto.sigma,
            "copper_sigma": materials.copper.sigma,
            "copper_mu_r": materials.copper.mu_r,
            "wall_pec": materials.wall_pec,
        },
        "mesh": asdict(mesh_cfg),
        "study": {
            "wall_bc": study.wall_bc.value,
            "search_hz": study.search_hz,
            "n_modes": study.n_modes,
            "azimuthal_index_m": study.target.azimuthal_index_m,
        },
        "grid": {"n_r": grid_spec.n_r, "n_z": grid_spec.n_z},
    }


def solve_hash(fingerprint: dict) -> str:
    """SHA-256 (first 16 hex chars) of the canonical JSON fingerprint."""
    canonical = json.dumps(fingerprint, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


@dataclass(frozen=True)
class SolveRecord:
    """One persisted solve: fingerprint + raw outputs + run log.

    `field_sample` is the picked TE01delta mode in the §3 export
    contract; `extract(record.field_sample)` reproduces f, Q, V_mode,
    p_e, F_m without COMSOL. The full candidate spectrum rides along so
    mode identification stays auditable after the fact.
    """

    fingerprint: dict
    record_hash: str
    comsol_version: str
    mesh_element_count: int
    interface_tag: str
    picked_index: int
    spectrum_f_real_hz: NDArray[np.float64]
    spectrum_f_imag_hz: NDArray[np.float64]
    spectrum_q_emw: NDArray[np.float64] | None
    field_sample: FieldSample
    created_at_utc: str
    diagnostics: list[dict] | None = None

    @property
    def complex_eigenfrequency_hz(self) -> complex:
        return complex(
            self.spectrum_f_real_hz[self.picked_index],
            self.spectrum_f_imag_hz[self.picked_index],
        )


def record_dir(root: Path, record_hash: str) -> Path:
    return Path(root) / record_hash


def save_solve_record(record: SolveRecord, root: Path) -> Path:
    """Write `meta.json` + `fields.npz` under `<root>/<hash>/`."""
    out = record_dir(root, record.record_hash)
    out.mkdir(parents=True, exist_ok=True)

    meta = {
        "fingerprint": record.fingerprint,
        "record_hash": record.record_hash,
        "comsol_version": record.comsol_version,
        "mesh_element_count": record.mesh_element_count,
        "interface_tag": record.interface_tag,
        "picked_index": record.picked_index,
        "created_at_utc": record.created_at_utc,
        "diagnostics": record.diagnostics,
        "q_emw_cross_check": record.field_sample.q_emw_cross_check,
    }
    (out / _META_FILENAME).write_text(
        json.dumps(meta, indent=2, sort_keys=True), encoding="utf-8"
    )

    fields = record.field_sample
    arrays: dict[str, NDArray] = {
        "r_m": fields.r_m,
        "z_m": fields.z_m,
        "weights_m2": fields.weights_m2,
        "e_complex": fields.e_complex,
        "h_complex": fields.h_complex,
        "eps_r_complex": fields.eps_r_complex,
        "dielectric_mask": fields.dielectric_mask,
        "spectrum_f_real_hz": record.spectrum_f_real_hz,
        "spectrum_f_imag_hz": record.spectrum_f_imag_hz,
    }
    if record.spectrum_q_emw is not None:
        arrays["spectrum_q_emw"] = record.spectrum_q_emw
    if fields.gain_region_mask is not None:
        arrays["gain_region_mask"] = fields.gain_region_mask
    np.savez_compressed(out / _FIELDS_FILENAME, **arrays)
    return out


def load_solve_record(root: Path, record_hash: str) -> SolveRecord | None:
    """Load a persisted solve, or None if absent/incomplete."""
    out = record_dir(root, record_hash)
    meta_path = out / _META_FILENAME
    fields_path = out / _FIELDS_FILENAME
    if not (meta_path.is_file() and fields_path.is_file()):
        return None

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    if meta["fingerprint"]["schema_version"] != SCHEMA_VERSION:
        return None  # stale schema: treat as a cache miss, re-solve

    with np.load(fields_path) as data:
        spectrum_re = data["spectrum_f_real_hz"]
        spectrum_im = data["spectrum_f_imag_hz"]
        q_emw = data["spectrum_q_emw"] if "spectrum_q_emw" in data else None
        gain_mask = (
            data["gain_region_mask"] if "gain_region_mask" in data else None
        )
        picked = int(meta["picked_index"])
        field_sample = FieldSample(
            r_m=data["r_m"],
            z_m=data["z_m"],
            e_complex=data["e_complex"],
            h_complex=data["h_complex"],
            eps_r_complex=data["eps_r_complex"],
            weights_m2=data["weights_m2"],
            dielectric_mask=data["dielectric_mask"],
            complex_eigenfrequency_hz=complex(
                spectrum_re[picked], spectrum_im[picked]
            ),
            gain_region_mask=gain_mask,
            q_emw_cross_check=meta.get("q_emw_cross_check"),
        )

    return SolveRecord(
        fingerprint=meta["fingerprint"],
        record_hash=meta["record_hash"],
        comsol_version=meta["comsol_version"],
        mesh_element_count=int(meta["mesh_element_count"]),
        interface_tag=meta["interface_tag"],
        picked_index=picked,
        spectrum_f_real_hz=spectrum_re,
        spectrum_f_imag_hz=spectrum_im,
        spectrum_q_emw=q_emw,
        field_sample=field_sample,
        created_at_utc=meta["created_at_utc"],
        diagnostics=meta.get("diagnostics"),
    )


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
