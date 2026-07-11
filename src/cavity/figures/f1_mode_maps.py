"""F1 — TE01δ mode maps (|E|, |H|) at the recovered Booth torus.

Data source (disk): the archived §5a finest-level CANONICAL-branch
walls-on SolveRecord `823e67969516bcf2` under
refs/gate_runs/20260710T083340Z_live_comsol/solves/, loaded through
`cavity.forward_model.persistence.load_solve_record` (LFS npz; 201×301
tensor grid flattened r-slowest). Render-time compute is magnitudes,
reshape, and per-panel normalisation only; f′ comes from the archived
spectrum at the picked index and Q₀ is the archived `emw.Qfactor`
cross-check scalar. Nothing else is derived.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from cavity.extraction.quadrature import axisymmetric_volume_integral
from cavity.forward_model.persistence import SolveRecord, load_solve_record

ARCHIVE_RUN_DIR = "20260710T083340Z_live_comsol"
ARCHIVE_ROOT = (
    Path(__file__).resolve().parents[3] / "refs" / "gate_runs" / ARCHIVE_RUN_DIR
)
SOLVES_ROOT = ARCHIVE_ROOT / "solves"
MANIFEST_PATH = ARCHIVE_ROOT / "checkpoint_manifest.json"

# Finest-level walls-on records (checkpoint_manifest.json, level 4):
# canonical = SPEC §2 materials (the branch F1 renders and F2's
# dielectric-restricted diagnostic integrates over); faithful = the
# .mph-exact gated branch (F2's headline rows).
CANONICAL_RECORD_HASH = "823e67969516bcf2"
FAITHFUL_RECORD_HASH = "2b276c4424e49bb9"

_LFS_POINTER_PREFIX = b"version https://git-lfs"

CAPTION = (
    "TE01δ mode maps at the recovered Booth torus: |E| (left) and |H| (right) over "
    "the (r, z) half-plane, each normalised to its own maximum (eigenmode amplitude is arbitrary); copper "
    "box and dielectric torus cross-section outlined. Rendered from the archived §5a finest-mesh walls-on "
    "SolveRecord, CANONICAL branch (SPEC §2 materials: εr′ = 316.3, tanδ = 1.1×10⁻⁴; record "
    "`823e67969516bcf2`, 7492 elements, `refs/gate_runs/20260710T083340Z_live_comsol`): f = 1450.382 MHz, "
    "Q₀ = 6764.6. Mode identified by field symmetry (azimuthal-E energy fraction 1.00, zero on-axis H_z "
    "sign changes), not eigenvalue order. The gated FAITHFUL companion (tanδ = 1.054×10⁻⁴, the .mph-exact "
    "unrounded Debye value) gives Q₀ = 6981.3 vs Booth's 6,980 (+0.02%); branch delta −3.10% as measured. "
    "The §5a gate is GREEN as re-based 2026-07-11 — the V_mode row's ×1.60 resolved as Booth's 225/360 "
    "partial-revolution print factor (see F2; record `refs/gate_runs/20260711T132705Z_rejudge`): 5 pass / "
    "0 fail / 1 deferred, `phase1_complete` still false on the deferred confinement row."
)


def load_archive_record(record_hash: str) -> SolveRecord:
    """Load one archived §5a SolveRecord, with a clear LFS-pointer error.

    Raises FileNotFoundError when the npz is absent or is an unsmudged
    git-lfs pointer — regeneration requires the materialised archive
    (tests skip instead, via the same pointer check).
    """
    fields_npz = SOLVES_ROOT / record_hash / "fields.npz"
    if not fields_npz.is_file():
        raise FileNotFoundError(
            f"archived §5a record missing: {fields_npz} — refs/gate_runs "
            "not present in this checkout"
        )
    with open(fields_npz, "rb") as fh:
        head = fh.read(len(_LFS_POINTER_PREFIX))
    if head.startswith(_LFS_POINTER_PREFIX):
        raise FileNotFoundError(
            f"{fields_npz} is an unsmudged git-lfs pointer — run "
            "`git lfs pull` to materialise the §5a archive"
        )
    record = load_solve_record(SOLVES_ROOT, record_hash)
    if record is None:
        raise FileNotFoundError(
            f"archived §5a record {record_hash} failed to load "
            "(incomplete or schema-mismatched)"
        )
    return record


def archive_provenance() -> dict:
    """Archive identity from the committed manifest (never the render clock)."""
    with MANIFEST_PATH.open(encoding="utf-8") as fh:
        manifest = json.load(fh)
    return {
        "run_dir": manifest["run_dir"],
        "archive_commit": manifest["provenance"]["git_commit"],
        "archive_dirty": manifest["provenance"]["git_dirty"],
        "comsol_version": manifest["provenance"]["comsol_version"],
        "created_at_utc": manifest["gate"]["created_at_utc"],
    }


def build_data() -> dict:
    """Everything F1 plots, from the archived canonical record (pure)."""
    record = load_archive_record(CANONICAL_RECORD_HASH)
    fields = record.field_sample
    grid = record.fingerprint["grid"]
    shape = (grid["n_r"], grid["n_z"])  # r varies slowest ('ij' order)

    e_mag = np.sqrt(
        np.real(np.sum(fields.e_complex * np.conj(fields.e_complex), axis=1))
    )
    h_sq = np.real(np.sum(fields.h_complex * np.conj(fields.h_complex), axis=1))
    h_mag = np.sqrt(h_sq)

    # ties the picture to the failing gate number (same primitive as §3)
    v_mode_global_m3 = float(
        np.real(axisymmetric_volume_integral(h_sq, fields.r_m, fields.weights_m2))
    ) / float(np.max(h_sq))

    geom = record.fingerprint["geometry"]
    f_prime = float(record.spectrum_f_real_hz[record.picked_index])
    # diagnostics ride along per candidate mode, not per spectrum slot —
    # locate the picked mode's entry by its eigenfrequency
    diag = next(
        d for d in record.diagnostics if d["f_real_hz"] == f_prime
    )
    return {
        "r_mm": (fields.r_m * 1e3).reshape(shape),
        "z_mm": (fields.z_m * 1e3).reshape(shape),
        "e_norm": (e_mag / e_mag.max()).reshape(shape),
        "h_norm": (h_mag / h_mag.max()).reshape(shape),
        "f_prime_hz": f_prime,
        "q0": float(fields.q_emw_cross_check),
        "grid_shape": shape,
        "v_mode_global_m3": v_mode_global_m3,
        "record_hash": record.record_hash,
        "mesh_element_count": record.mesh_element_count,
        "box_radius_mm": geom["box_radius_m"] * 1e3,
        "box_height_mm": geom["box_height_m"] * 1e3,
        "torus_major_mm": geom["dielectric_radius_m"] * 1e3,
        "torus_minor_mm": geom["dielectric_minor_radius_m"] * 1e3,
        "azimuthal_e_energy_fraction": diag["azimuthal_e_energy_fraction"],
        "axis_hz_sign_changes": diag["axis_hz_sign_changes"],
        **archive_provenance(),
    }


def render(data: dict):
    from cavity.figures import _style

    _style.apply_style()
    import matplotlib.pyplot as plt
    from matplotlib.patches import Circle

    fig, axes = plt.subplots(
        1, 2, figsize=(7.6, 5.2), sharey=True, constrained_layout=True
    )
    panels = (
        (axes[0], data["e_norm"], r"$|\mathbf{E}|\,/\,|\mathbf{E}|_{\max}$"),
        (axes[1], data["h_norm"], r"$|\mathbf{H}|\,/\,|\mathbf{H}|_{\max}$"),
    )
    extent = (0.0, data["box_radius_mm"], 0.0, data["box_height_mm"])
    for ax, field, label in panels:
        im = ax.imshow(
            field.T,
            origin="lower",
            extent=extent,
            cmap=_style.SEQUENTIAL_FIELD,
            vmin=0.0,
            vmax=1.0,
            aspect="equal",
            interpolation="nearest",
        )
        # geometry overlay: box wall = plot boundary, torus cross-section
        ax.add_patch(
            Circle(
                (data["torus_major_mm"], data["box_height_mm"] / 2.0),
                data["torus_minor_mm"],
                fill=False,
                edgecolor="white",
                linewidth=1.0,
                linestyle="--",
            )
        )
        for spine in ax.spines.values():
            spine.set_visible(True)
            spine.set_color(_style.INK_MUTED)
        ax.set_xlabel("r (mm)")
        ax.set_title(label)
        cbar = fig.colorbar(im, ax=ax, shrink=0.85, pad=0.02)
        cbar.outline.set_visible(False)
    axes[0].set_ylabel("z (mm)")
    axes[0].text(
        0.04,
        0.97,
        f"f = {data['f_prime_hz'] / 1e6:.3f} MHz\n"
        f"$Q_0$ = {data['q0']:.1f} (canonical)",
        transform=axes[0].transAxes,
        ha="left",
        va="top",
        fontsize=8.0,
        color="white",
    )
    dirty = " (dirty)" if data["archive_dirty"] else ""
    _style.provenance_footer(
        fig,
        f"archive refs/gate_runs/{data['run_dir']} · record {data['record_hash']} "
        f"({data['mesh_element_count']} elements, COMSOL {data['comsol_version']}) · "
        f"archive commit {data['archive_commit'][:7]}{dirty} · "
        "§5a GATED FAIL (V_mode row) — no §5a-validated status",
    )
    return fig


def main(out_dir: Path | None = None) -> list[Path]:
    from cavity.figures import _style

    fig = render(build_data())
    paths = _style.save_figure(fig, "f1_mode_maps", out_dir)
    for p in paths:
        print(f"wrote {p}")
    return paths


if __name__ == "__main__":
    main()
