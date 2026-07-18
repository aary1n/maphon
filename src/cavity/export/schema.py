"""Field-export bundle contract: required keys, loader, validator.

The standalone schema document (docs/field_export_schema.md, copied
into every bundle as FIELD_EXPORT_SCHEMA.md) is the PRIMARY deliverable
of the export pass; `cavity.export` is its reference implementation.
This module owns the machine-checkable half of the contract:

  - `EXPORT_SCHEMA_VERSION` — independent of the §1 persistence layer's
    internal SCHEMA_VERSION (a bundle is a handoff artifact, not a
    cache entry; the two version at different rates).
  - `load_bundle` — reads a bundle, REFUSING on a schema-version
    mismatch (the reader-side mirror of `load_solve_record`'s
    mismatch-is-a-miss discipline: a cache miss re-solves, a handoff
    reader must refuse loudly since there is nothing to fall back to).
  - `validate_bundle` — the full contract check: file presence,
    required keys, shape/dtype consistency, and the numeric invariants
    (unit total EM energy, unit weight normalisation, picked-mode
    consistency). Run by the writer's tests and available to any
    consumer as a first-line diagnostic.

Stable keys are contract: renames or semantic changes bump
`EXPORT_SCHEMA_VERSION` (consumer 3's surrogate training rows outlive
schema revisions); additions of new keys within a version are allowed
and must be ignored by readers.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy.constants import epsilon_0 as EPS_0
from scipy.constants import mu_0 as MU_0

from cavity.extraction.quadrature import axisymmetric_volume_integral

EXPORT_SCHEMA_VERSION = 1

FIELDS_FILENAME = "fields.npz"
META_FILENAME = "export_meta.json"
SCHEMA_DOC_FILENAME = "FIELD_EXPORT_SCHEMA.md"

#: (N,)-or-otherwise per-key contract; full definitions (units, physics)
#: live in the schema document's array-key table.
REQUIRED_ARRAY_KEYS = (
    "r_m",
    "z_m",
    "weights_m2",
    "shape_rz",
    "e_complex",
    "h_complex",
    "eps_r_complex",
    "dielectric_mask",
    "gain_region_mask",
    "w_e_per_m3",
    "w_spin_per_m3",
    "spectrum_f_real_hz",
    "spectrum_f_imag_hz",
)
OPTIONAL_ARRAY_KEYS = ("spectrum_q_emw", "spacer_mask")

REQUIRED_META_KEYS = (
    "export_schema_version",
    "conventions",
    "normalisation",
    "mode_selection",
    "weights",
    "q_loading",
    "solve",
    "exporter",
    "summary",
    "status_notes",
)

#: The flat, stable-keyed scalar row consumer 3 (surrogate training
#: data) globs out of `meta["summary"]`.
REQUIRED_SUMMARY_KEYS = (
    "export_schema_version",
    "record_hash",
    "f_real_hz",
    "f_imag_hz",
    "q",
    "p_e",
    "v_mode_global_m3",
    "v_mode_local_m3",
    "f_m_global",
    "f_m_local",
    "u_e_raw_j",
    "u_h_raw_j",
    "raw_total_energy_j",
    "u_e_fraction",
    "h_phi_energy_share",
    "magnetic_filling_factor",
    "gain_mask_is_fallback",
    "spin_projection_mode",
)

#: Numeric invariants recomputed by `validate_bundle` reproduce the
#: writer's own arithmetic (same arrays, same quadrature primitive), so
#: the tolerance covers float round-trip only.
_INVARIANT_REL_TOL = 1.0e-9


class SchemaValidationError(ValueError):
    """The bundle violates the export contract (message says where)."""


class SchemaVersionError(SchemaValidationError):
    """Reader refusal: the bundle's export_schema_version is not ours."""


@dataclass(frozen=True)
class ExportBundle:
    """One loaded bundle: metadata dict + named arrays, path attached."""

    bundle_dir: Path
    meta: dict
    arrays: dict[str, np.ndarray]

    @property
    def n_nodes(self) -> int:
        return int(self.arrays["r_m"].shape[0])


def load_bundle(bundle_dir: Path) -> ExportBundle:
    """Read a bundle, refusing on schema-version mismatch.

    Performs only the checks needed to read safely (files present,
    meta parses, version matches). Full contract checking is
    `validate_bundle`.
    """
    bundle_dir = Path(bundle_dir)
    meta_path = bundle_dir / META_FILENAME
    fields_path = bundle_dir / FIELDS_FILENAME
    if not meta_path.is_file():
        raise SchemaValidationError(f"missing {META_FILENAME} in {bundle_dir}")
    if not fields_path.is_file():
        raise SchemaValidationError(
            f"missing {FIELDS_FILENAME} in {bundle_dir}"
        )

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    version = meta.get("export_schema_version")
    if version != EXPORT_SCHEMA_VERSION:
        raise SchemaVersionError(
            f"bundle {bundle_dir} declares export_schema_version="
            f"{version!r}; this reader implements "
            f"{EXPORT_SCHEMA_VERSION}. Refusing to guess across versions "
            "— consult the bundle's own FIELD_EXPORT_SCHEMA.md copy."
        )

    with np.load(fields_path) as data:
        arrays = {key: np.array(data[key]) for key in data.files}
    return ExportBundle(bundle_dir=bundle_dir, meta=meta, arrays=arrays)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SchemaValidationError(message)


def validate_bundle(bundle_dir: Path) -> ExportBundle:
    """Full contract check; returns the loaded bundle on success.

    Checks, in order: file presence (including the schema-doc copy —
    self-containment is contract), required metadata and array keys,
    shape/dtype consistency, then the numeric invariants:

      1. unit total EM energy — U_E + U_H recomputed from the stored
         arrays equals 1 J;
      2. unit weight normalisation — int w dV = 1 for both arms, w >= 0
         and zero outside its mask;
      3. picked-mode consistency — the summary eigenfrequency equals
         spectrum[picked_index] (the mode is CONSUMED from the §2
         field-symmetry selection, never re-picked here).
    """
    bundle = load_bundle(bundle_dir)
    meta, arrays = bundle.meta, bundle.arrays

    _require(
        (bundle.bundle_dir / SCHEMA_DOC_FILENAME).is_file(),
        f"missing {SCHEMA_DOC_FILENAME} copy — bundles must be "
        "self-contained (consumer 2 has no repo access)",
    )
    missing_meta = [k for k in REQUIRED_META_KEYS if k not in meta]
    _require(not missing_meta, f"missing metadata keys: {missing_meta}")
    missing_summary = [
        k for k in REQUIRED_SUMMARY_KEYS if k not in meta["summary"]
    ]
    _require(
        not missing_summary,
        f"missing summary scalar keys: {missing_summary}",
    )
    missing_arrays = [k for k in REQUIRED_ARRAY_KEYS if k not in arrays]
    _require(not missing_arrays, f"missing npz arrays: {missing_arrays}")

    n = arrays["r_m"].shape[0]
    for key in ("z_m", "weights_m2", "eps_r_complex", "w_e_per_m3",
                "w_spin_per_m3", "dielectric_mask", "gain_region_mask"):
        _require(
            arrays[key].shape == (n,),
            f"{key} shape {arrays[key].shape} != ({n},)",
        )
    for key in ("e_complex", "h_complex"):
        _require(
            arrays[key].shape == (n, 3),
            f"{key} shape {arrays[key].shape} != ({n}, 3)",
        )
        _require(
            np.iscomplexobj(arrays[key]), f"{key} must be complex"
        )
    for key in ("dielectric_mask", "gain_region_mask"):
        _require(
            arrays[key].dtype == np.bool_, f"{key} must be boolean"
        )
    if "spacer_mask" in arrays:
        _require(
            arrays["spacer_mask"].shape == (n,),
            f"spacer_mask shape {arrays['spacer_mask'].shape} != ({n},)",
        )
        _require(
            arrays["spacer_mask"].dtype == np.bool_,
            "spacer_mask must be boolean",
        )
    shape_rz = arrays["shape_rz"]
    _require(
        shape_rz.shape == (2,) and int(shape_rz[0]) * int(shape_rz[1]) == n,
        f"shape_rz {shape_rz} inconsistent with N = {n} nodes",
    )
    n_modes = arrays["spectrum_f_real_hz"].shape[0]
    _require(
        arrays["spectrum_f_imag_hz"].shape == (n_modes,),
        "spectrum_f_imag_hz length differs from spectrum_f_real_hz",
    )

    # Invariant 1: unit total stored EM energy (schema doc,
    # 'Normalisation'). Same densities and primitive as the writer.
    e2 = np.sum(np.abs(arrays["e_complex"]) ** 2, axis=1)
    h2 = np.sum(np.abs(arrays["h_complex"]) ** 2, axis=1)
    eps_real = np.real(arrays["eps_r_complex"])
    # JACOBIAN: applied inside axisymmetric_volume_integral.
    u_e = (
        EPS_0
        / 4.0
        * float(
            np.real(
                axisymmetric_volume_integral(
                    eps_real * e2, arrays["r_m"], arrays["weights_m2"]
                )
            )
        )
    )
    u_h = (
        MU_0
        / 4.0
        * float(
            np.real(
                axisymmetric_volume_integral(
                    h2, arrays["r_m"], arrays["weights_m2"]
                )
            )
        )
    )
    total = u_e + u_h
    _require(
        abs(total - 1.0) <= _INVARIANT_REL_TOL,
        f"unit-energy invariant violated: U_E + U_H = {total} J != 1 J",
    )

    # Invariant 2: weight normalisation and support.
    for key, mask_key in (
        ("w_e_per_m3", "dielectric_mask"),
        ("w_spin_per_m3", "gain_region_mask"),
    ):
        w = arrays[key]
        _require(bool(np.all(w >= 0.0)), f"{key} has negative entries")
        _require(
            bool(np.all(w[~arrays[mask_key]] == 0.0)),
            f"{key} non-zero outside {mask_key}",
        )
        integral = float(
            np.real(
                axisymmetric_volume_integral(
                    w, arrays["r_m"], arrays["weights_m2"]
                )
            )
        )
        _require(
            abs(integral - 1.0) <= _INVARIANT_REL_TOL,
            f"{key} volume integral = {integral} != 1",
        )

    # Invariant 3: the picked mode is consumed, not re-derived.
    picked = int(meta["solve"]["picked_index"])
    _require(
        0 <= picked < n_modes,
        f"picked_index {picked} outside spectrum of {n_modes} modes",
    )
    summary = meta["summary"]
    _require(
        float(summary["f_real_hz"])
        == float(arrays["spectrum_f_real_hz"][picked]),
        "summary f_real_hz != spectrum[picked_index]",
    )
    _require(
        float(summary["f_imag_hz"])
        == float(arrays["spectrum_f_imag_hz"][picked]),
        "summary f_imag_hz != spectrum[picked_index]",
    )
    p_e = float(summary["p_e"])
    _require(0.0 < p_e <= 1.0, f"summary p_e = {p_e} out of (0, 1]")

    return bundle
