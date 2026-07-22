"""L3 item-9 composition plumbing — design doc §3.

Consumes RAW schema-v1 columns (f_real_hz, q, magnetic_filling_factor,
p_e, guard + audit) and composes the downstream quantities:

  - κc = (1 + k)·f/Q₀ = f/Q_L, k = DELOAD_K = 0.2 uniform per draw
    (Q12 ruling), CYCLIC-Hz FWHM — single-sourced through the existing
    `cavity.thermal.broadening.resonance_linewidth_hz` (§8 convention 4;
    never the angular 2πf/Q_L);
  - the relative G² geometry factor f·η_H, with η_H = the raw
    `magnetic_filling_factor` column (∫_gain|H|²dV / ∫_all|H|²dV,
    projection-independent by construction);
  - the anchored-ratio C₀ per the Q3 ruling:
    C₀(θ,p) = PLANNING_C0 × [f·η_H/κc] / [f·η_H/κc]_anchor —
    the per-draw extension of the committed import convention ("C₀
    stays the IMPORTED planning cooperativity, never recomputed from
    κs" — 190 at the Q3 ruling's date, 200 from 2026-07-21 via
    `C0_PLANNING`); N cancels exactly in the ratio; absolute G² is a
    DIAGNOSTIC ONLY.

DERIVED QUANTITIES ARE NEVER RAW ROWS: everything composed here lives
in its own artifact namespace and carries its composition convention
(k, anchor record hash, κs branch, projection mode) alongside the
values — `validate_derived_row` refuses a bare number.

Rider R4 (COMMITTED zero-solve check, Q3 contingency): the anchored
ratio law assumes the field-direction distribution over the gain region
is draw-invariant across the DOF box. `projection_invariance_report`
recomputes η under a direction-sensitive `SpinProjection`
(`axis_projected`) vs raw |H|² from the STORED field arrays across
sweep-corner bundles and reports the spread of the ratio law under the
two projections. A non-negligible spread vs the CV-gate scale is
ESCALATED, never averaged.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy.constants import mu_0 as MU_0
from scipy.constants import physical_constants
from scipy.constants import h as H_PLANCK

from cavity.export.schema import load_bundle
from cavity.extraction.quadrature import (
    axisymmetric_node_volumes,
    axisymmetric_volume_integral,
)
from cavity.extraction.weights import SpinProjection, projected_h2_density
from cavity.provenance import DELOAD_K, KAPPA_S
from cavity.thermal.broadening import resonance_linewidth_hz
from cavity.thermal.report_margin import PLANNING_C0

#: Electron gyromagnetic ratio, rad s^-1 T^-1 (CODATA via scipy — the
#: schema §6 recipe's constant, not a fresh literal).
GAMMA_E_RAD_PER_S_PER_T = abs(
    physical_constants["electron gyromag. ratio"][0]
)

KAPPA_S_BRANCHES = {
    "point": KAPPA_S.kappa_s_hz,
    "lo": KAPPA_S.kappa_s_band_lo_hz,
    "hi": KAPPA_S.kappa_s_band_hi_hz,
}


def kappa_s_branch_hz(branch: str) -> float:
    try:
        return KAPPA_S_BRANCHES[branch]
    except KeyError:
        raise ValueError(
            f"unknown kappa_s branch {branch!r}; "
            f"one of {sorted(KAPPA_S_BRANCHES)}"
        ) from None


def kappa_c_hz(f_hz: float, q0: float, *, k: float = DELOAD_K) -> float:
    """κc = (1+k)·f/Q₀ = f/Q_L in CYCLIC-Hz FWHM (§8 convention 4).

    Routed through the committed `resonance_linewidth_hz(f, Q_L)` so
    the linewidth convention has exactly one implementation. k is the
    Q12-ruled uniform de-loading constant (no per-draw scatter).
    """
    if q0 <= 0:
        raise ValueError("Q0 must be positive")
    return resonance_linewidth_hz(f_hz, q0 / (1.0 + k))


def g2_relative(f_hz: float, eta_h: float) -> float:
    """The entire geometry dependence of G²: f × η_H (design doc §3)."""
    if not 0.0 < eta_h <= 1.0:
        raise ValueError(f"eta_h = {eta_h} out of (0, 1]")
    return f_hz * eta_h


class AnchorRefusalError(ValueError):
    """Anchor construction refused (rider R1: fallback-mask bundles
    describe the STO puck, not the pentacene gain region)."""


@dataclass(frozen=True)
class AnchorPoint:
    """The [f·η_H/κc]_anchor of the Q3 anchored-ratio convention.

    `diagnostic_only=True` is the explicit override for fallback-mask
    (pre-Phase 1b) anchors — everything composed against such an anchor
    is itself diagnostic, and the derived rows say so.
    """

    f_hz: float
    eta_h: float
    kappa_c_hz: float
    record_hash: str
    gain_mask_is_fallback: bool
    diagnostic_only: bool = False

    def __post_init__(self) -> None:
        if self.gain_mask_is_fallback and not self.diagnostic_only:
            raise AnchorRefusalError(
                "anchor refused: bundle has gain_mask_is_fallback=true "
                "(schema §9 — spin-arm quantities describe the STO "
                "puck, not the pentacene gain region; rider R1 makes "
                "Phase 1b geometry a precondition for the "
                "G-regression). Pass diagnostic_only=True to build an "
                "explicitly-diagnostic anchor."
            )

    @property
    def ratio(self) -> float:
        return g2_relative(self.f_hz, self.eta_h) / self.kappa_c_hz

    @classmethod
    def from_raw_row(
        cls, row: dict, *, diagnostic_only: bool = False
    ) -> "AnchorPoint":
        return cls(
            f_hz=float(row["f_real_hz"]),
            eta_h=float(row["magnetic_filling_factor"]),
            kappa_c_hz=kappa_c_hz(
                float(row["f_real_hz"]), float(row["q"])
            ),
            record_hash=str(row["record_hash"]),
            gain_mask_is_fallback=bool(row["gain_mask_is_fallback"]),
            diagnostic_only=diagnostic_only,
        )

    @classmethod
    def from_bundle(
        cls, bundle_dir: Path, *, diagnostic_only: bool = False
    ) -> "AnchorPoint":
        summary = load_bundle(Path(bundle_dir)).meta["summary"]
        return cls.from_raw_row(
            summary, diagnostic_only=diagnostic_only
        )


def c0_anchored(
    f_hz: float, eta_h: float, kappa_c_value_hz: float, anchor: AnchorPoint
) -> float:
    """C₀ = PLANNING_C0 × [f·η_H/κc] / [f·η_H/κc]_anchor (Q3 ruling)."""
    return PLANNING_C0 * (
        g2_relative(f_hz, eta_h) / kappa_c_value_hz
    ) / anchor.ratio


# ---------------------------------------------------------------------------
# Derived rows — values + their composition convention, inseparably
# ---------------------------------------------------------------------------

DERIVED_ROWS_FILENAME = "derived_rows.jsonl"

_REQUIRED_DERIVED_KEYS = (
    "design_row_hash",
    "record_hash",
    "kappa_c_hz",
    "g2_relative_hz",
    "c0_anchored",
    "admissible_for_g_regression",
    "conventions",
)
_REQUIRED_CONVENTION_KEYS = (
    "deload_k",
    "kappa_c_convention",
    "planning_c0",
    "c0_convention",
    "anchor_record_hash",
    "anchor_is_diagnostic_only",
    "kappa_s_branch",
    "kappa_s_hz",
    "spin_projection_mode",
)


class DerivedRowContractError(ValueError):
    """A derived row without its convention block is a bare number —
    refused."""


def validate_derived_row(row: dict) -> None:
    missing = [k for k in _REQUIRED_DERIVED_KEYS if k not in row]
    if missing:
        raise DerivedRowContractError(
            f"derived row missing keys: {missing}"
        )
    conventions = row["conventions"]
    missing_conv = [
        k for k in _REQUIRED_CONVENTION_KEYS if k not in conventions
    ]
    if missing_conv:
        raise DerivedRowContractError(
            f"derived row conventions block missing: {missing_conv} — "
            "derived quantities never travel without their composition "
            "convention (design doc §3)"
        )


def compose_derived_row(
    raw_row: dict,
    *,
    anchor: AnchorPoint,
    kappa_s_branch: str = "point",
) -> dict:
    """One raw schema-v1 row → its derived (composed) companion."""
    f_hz = float(raw_row["f_real_hz"])
    q0 = float(raw_row["q"])
    eta_h = float(raw_row["magnetic_filling_factor"])
    kc = kappa_c_hz(f_hz, q0)
    fallback = bool(raw_row["gain_mask_is_fallback"])
    row = {
        "design_row_hash": raw_row["design_row_hash"],
        "record_hash": raw_row["record_hash"],
        "kappa_c_hz": kc,
        "g2_relative_hz": g2_relative(f_hz, eta_h),
        "c0_anchored": c0_anchored(f_hz, eta_h, kc, anchor),
        # Rider R1: fallback-mask rows describe the STO puck — their
        # G-carrying columns are inadmissible for the item-9 regression.
        "admissible_for_g_regression": (
            not fallback and not anchor.diagnostic_only
        ),
        "conventions": {
            "deload_k": DELOAD_K,
            "kappa_c_convention": (
                "cyclic-Hz FWHM; kappa_c = (1+k)*f/Q0 = f/Q_L via "
                "broadening.resonance_linewidth_hz — NEVER the angular "
                "2*pi*f/Q_L (W20 trap, schema §7)"
            ),
            "planning_c0": PLANNING_C0,
            "c0_convention": (
                "anchored ratio C0 = PLANNING_C0 * [f*eta_H/kappa_c] / "
                "[f*eta_H/kappa_c]_anchor (Q3 ruling 2026-07-14, "
                "contingent on rider R4 projection invariance); N "
                "cancels exactly; absolute G2 diagnostic only"
            ),
            "anchor_record_hash": anchor.record_hash,
            "anchor_is_diagnostic_only": anchor.diagnostic_only,
            "kappa_s_branch": kappa_s_branch,
            "kappa_s_hz": kappa_s_branch_hz(kappa_s_branch),
            "spin_projection_mode": raw_row["spin_projection_mode"],
        },
    }
    validate_derived_row(row)
    return row


def compose_derived_rows(
    raw_rows: list[dict],
    *,
    anchor: AnchorPoint,
    kappa_s_branch: str = "point",
) -> list[dict]:
    return [
        compose_derived_row(
            row, anchor=anchor, kappa_s_branch=kappa_s_branch
        )
        for row in raw_rows
    ]


def write_derived_rows(path: Path, rows: list[dict]) -> Path:
    path = Path(path)
    if path.name == "raw_rows.jsonl":
        raise DerivedRowContractError(
            "derived rows must not masquerade as the raw-row store"
        )
    with open(path, "w", encoding="utf-8") as fh:
        for row in rows:
            validate_derived_row(row)
            fh.write(json.dumps(row, sort_keys=True) + "\n")
    return path


# ---------------------------------------------------------------------------
# Absolute G² — DIAGNOSTIC ONLY (Q3 ruling)
# ---------------------------------------------------------------------------


def g2_absolute_diagnostic(bundle_dir: Path, n_bins: int = 10) -> dict:
    """Schema §6 coupling recipe over one bundle's gain region.

    g_j = γ√(μ₀ h f / 2 V_mode^j), V_mode^j = ∫|H|²dV / |H(r_j)|² —
    the published-framework definition, volume-weighted histogram
    (dV_i = 2πr·w_i, NEVER node counts). Labelled DIAGNOSTIC ONLY: the
    sweep derives geometry RATIOS; no absolute G² enters any composed
    quantity (Q3 ruling; the orientational matrix element and the
    zone-refining doping caveat both live outside these ratios).
    """
    bundle = load_bundle(Path(bundle_dir))
    arrays = bundle.arrays
    f_hz = float(bundle.meta["summary"]["f_real_hz"])

    h2 = np.sum(np.abs(arrays["h_complex"]) ** 2, axis=1)
    # JACOBIAN: applied inside the §3 primitives.
    dv = axisymmetric_node_volumes(arrays["r_m"], arrays["weights_m2"])
    h2_integral = float(
        np.real(
            axisymmetric_volume_integral(
                h2, arrays["r_m"], arrays["weights_m2"]
            )
        )
    )
    gain = arrays["gain_region_mask"]
    if not np.any(gain & (h2 > 0)):
        raise ValueError("no non-zero |H|² nodes in the gain region")
    sel = gain & (h2 > 0)
    v_mode_j = h2_integral / h2[sel]
    g_j = GAMMA_E_RAD_PER_S_PER_T * np.sqrt(
        MU_0 * H_PLANCK * f_hz / (2.0 * v_mode_j)
    )
    counts, edges = np.histogram(g_j, bins=n_bins, weights=dv[sel])
    return {
        "label": (
            "DIAGNOSTIC ONLY (Q3 ruling): absolute G² is reported as a "
            "diagnostic; every composed quantity uses the anchored "
            "ratio"
        ),
        "gain_mask_is_fallback": bool(
            bundle.meta["summary"]["gain_mask_is_fallback"]
        ),
        "g_j_rad_per_s_min": float(np.min(g_j)),
        "g_j_rad_per_s_max": float(np.max(g_j)),
        "g_j_rad_per_s_volume_weighted_mean": float(
            np.sum(g_j * dv[sel]) / np.sum(dv[sel])
        ),
        "histogram_counts_m3": counts.tolist(),
        "histogram_edges_rad_per_s": edges.tolist(),
    }


# ---------------------------------------------------------------------------
# Rider R4 — projection invariance of the anchored ratio (COMMITTED)
# ---------------------------------------------------------------------------


def eta_h_under_projection(
    arrays: dict, projection: SpinProjection
) -> float:
    """η_H recomputed from stored arrays under a chosen projection.

    isotropic reproduces the raw `magnetic_filling_factor` column.
    """
    density = projected_h2_density(arrays["h_complex"], projection)
    gain = arrays["gain_region_mask"]
    # JACOBIAN: applied inside axisymmetric_volume_integral (both).
    num = float(
        np.real(
            axisymmetric_volume_integral(
                np.where(gain, density, 0.0),
                arrays["r_m"],
                arrays["weights_m2"],
            )
        )
    )
    den = float(
        np.real(
            axisymmetric_volume_integral(
                density, arrays["r_m"], arrays["weights_m2"]
            )
        )
    )
    if den <= 0.0:
        raise ValueError("projected |H|² integral non-positive")
    return num / den


def projection_invariance_report(
    bundle_dirs: list[Path],
    *,
    u_z: float = 1.0,
    escalation_threshold: float,
) -> dict:
    """Rider R4: spread of the anchored-ratio law under isotropic-|H|²
    vs a direction-sensitive projection, across sweep-corner bundles.

    Under a projection swap the per-bundle ratio f·η/κc scales by
    η_proj/η_iso, so the ANCHORED law shifts, bundle-relative to the
    first (anchor) bundle, by (η_proj/η_iso)_b / (η_proj/η_iso)_0 − 1.
    `escalation_threshold` is the CV-gate scale it is judged against
    (§9/Q8); a breach sets `escalate=True` — the projection choice is
    then ESCALATED, not averaged (design doc §3, verdict R4).
    """
    if len(bundle_dirs) < 2:
        raise ValueError(
            "R4 needs >= 2 bundles (one anchors the ratio law)"
        )
    projection = SpinProjection.axis_projected(u_z)
    per_bundle = []
    for bundle_dir in bundle_dirs:
        bundle = load_bundle(Path(bundle_dir))
        eta_iso = eta_h_under_projection(
            bundle.arrays, SpinProjection.isotropic_h2()
        )
        eta_proj = eta_h_under_projection(bundle.arrays, projection)
        summary = bundle.meta["summary"]
        per_bundle.append(
            {
                "bundle_dir": str(bundle_dir),
                "record_hash": summary["record_hash"],
                "eta_h_isotropic": eta_iso,
                "eta_h_isotropic_summary_column": summary[
                    "magnetic_filling_factor"
                ],
                "eta_h_projected": eta_proj,
                "projection_ratio": eta_proj / eta_iso,
            }
        )
    ratio_0 = per_bundle[0]["projection_ratio"]
    for entry in per_bundle:
        entry["anchored_law_shift"] = (
            entry["projection_ratio"] / ratio_0 - 1.0
        )
    max_abs_shift = max(
        abs(entry["anchored_law_shift"]) for entry in per_bundle
    )
    return {
        "projection": projection.label(),
        "escalation_threshold": escalation_threshold,
        "escalation_threshold_source": (
            "CV-gate scale (§9/Q8): the anchored-ratio spread is "
            "non-negligible when it rivals the gate's composed-error "
            "budget"
        ),
        "max_abs_anchored_law_shift": max_abs_shift,
        "escalate": bool(max_abs_shift > escalation_threshold),
        "escalate_meaning": (
            "spread rivals the CV-gate scale: the projection choice is "
            "ESCALATED for ratification, never averaged (rider R4)"
        ),
        "per_bundle": per_bundle,
    }
