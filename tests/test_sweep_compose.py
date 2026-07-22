"""L3 item-9 composition — κc/C₀ conventions, anchor refusal pairs,
derived-row contract, absolute-G² diagnostic, and rider R4.
"""

from __future__ import annotations

import numpy as np
import pytest

from cavity.export.schema import load_bundle
from cavity.extraction.quadrature import (
    axisymmetric_node_volumes,
    axisymmetric_volume_integral,
)
from cavity.extraction.weights import SpinProjection
from cavity.provenance import DELOAD_K, KAPPA_S
from cavity.sweep.backend import MockBackend, draw_solve_spec
from cavity.sweep.compose import (
    AnchorPoint,
    AnchorRefusalError,
    DerivedRowContractError,
    compose_derived_row,
    compose_derived_rows,
    c0_anchored,
    eta_h_under_projection,
    g2_absolute_diagnostic,
    g2_relative,
    kappa_c_hz,
    kappa_s_branch_hz,
    projection_invariance_report,
    validate_derived_row,
    write_derived_rows,
)
from cavity.thermal.broadening import resonance_linewidth_hz
from cavity.thermal.report_margin import PLANNING_C0
from cavity.provenance import GEOM_WU_STO_RING, STO, STO_HEIGHT_FORK
from cavity.export.writer import export_bundle


def _raw_row(
    f=1.4493e9, q=6764.5852, eta=0.35, fallback=False, rh="abc123",
    drh="row0001",
) -> dict:
    return {
        "f_real_hz": f,
        "q": q,
        "magnetic_filling_factor": eta,
        "gain_mask_is_fallback": fallback,
        "record_hash": rh,
        "design_row_hash": drh,
        "spin_projection_mode": "isotropic_h2",
    }


@pytest.fixture(scope="module")
def mock_bundles(tmp_path_factory):
    """Three θ-distinct mock bundles for the array-level checks."""
    out = tmp_path_factory.mktemp("compose_bundles")
    backend = MockBackend()
    thetas = [
        {},
        {"sto_outer_radius_m": GEOM_WU_STO_RING.sto_outer_radius_m
         + 20e-6, "epsilon_r": 313.0},
        {"p_tune": GEOM_WU_STO_RING.box_internal_height_asoperated_m
         - 20e-6, "epsilon_r": 317.5},
    ]
    dirs = []
    for i, overrides in enumerate(thetas):
        theta = {
            "box_radius_m": GEOM_WU_STO_RING.box_inner_radius_m,
            "sto_outer_radius_m": GEOM_WU_STO_RING.sto_outer_radius_m,
            "sto_inner_radius_m": GEOM_WU_STO_RING.sto_inner_radius_m,
            # mock-tier labelled read of the Q13 evidence-favoured branch
            "sto_height_m": STO_HEIGHT_FORK.evidence_favoured,
            "epsilon_r": STO.epsilon_r_real,
            "tan_delta": STO.tan_delta,
        }
        theta.update(overrides)
        record = backend.solve(
            draw_solve_spec(
                theta,
                box_height_fallback_m=(
                    GEOM_WU_STO_RING.box_internal_height_asoperated_m
                ),
            )
        ).record
        dirs.append(export_bundle(record, out / f"bundle_{i}"))
    return dirs


# ---------------------------------------------------------------------------
# κc — §8 convention 4, single-sourced
# ---------------------------------------------------------------------------


def test_kappa_c_matches_independent_arithmetic_and_committed_helper():
    f, q0 = 1.4493e9, 6764.5852
    kc = kappa_c_hz(f, q0)
    # Independent arithmetic: (1+k)·f/Q0.
    assert kc == pytest.approx((1.0 + DELOAD_K) * f / q0, rel=1e-12)
    # Second code path: the committed linewidth helper at Q_L.
    assert kc == pytest.approx(
        resonance_linewidth_hz(f, q0 / (1.0 + DELOAD_K)), rel=1e-12
    )


def test_kappa_c_is_cyclic_hz_never_angular():
    # W20 trap guard: the angular value is 2π larger; a silent 2π would
    # put κc in the MHz — assert we are on the cyclic side.
    kc = kappa_c_hz(1.4493e9, 6764.5852)
    assert kc == pytest.approx(257_097.4, rel=1e-4)
    angular = 2.0 * np.pi * kc
    assert not np.isclose(kc, angular, rtol=0.5)


def test_kappa_c_rejects_nonpositive_q():
    with pytest.raises(ValueError):
        kappa_c_hz(1.45e9, 0.0)


def test_kappa_s_branches_import_the_graded_constant():
    assert kappa_s_branch_hz("point") == KAPPA_S.kappa_s_hz == 1.4e6
    assert kappa_s_branch_hz("lo") == KAPPA_S.kappa_s_band_lo_hz
    assert kappa_s_branch_hz("hi") == KAPPA_S.kappa_s_band_hi_hz
    with pytest.raises(ValueError, match="unknown kappa_s branch"):
        kappa_s_branch_hz("mid")


# ---------------------------------------------------------------------------
# Anchored C₀ — Q3 convention
# ---------------------------------------------------------------------------


def test_c0_equals_planning_value_at_the_anchor_exactly():
    row = _raw_row()
    anchor = AnchorPoint.from_raw_row(row)
    kc = kappa_c_hz(row["f_real_hz"], row["q"])
    assert c0_anchored(
        row["f_real_hz"], row["magnetic_filling_factor"], kc, anchor
    ) == pytest.approx(PLANNING_C0, rel=1e-14)
    # 200.0 from 2026-07-21 (`C0_PLANNING`, elicited planning value —
    # dimensionless resonant on-resonance cooperativity).
    assert PLANNING_C0 == 200.0


def test_c0_ratios_between_draws_are_anchor_invariant():
    """N-cancellation semantics: the anchor scales all draws equally,
    so between-draw C₀ ratios cannot depend on the anchor choice."""
    r1 = _raw_row(q=5000.0, eta=0.30, rh="r1")
    r2 = _raw_row(q=7000.0, eta=0.40, rh="r2")
    a1 = AnchorPoint.from_raw_row(_raw_row(q=6000.0, eta=0.2, rh="a1"))
    a2 = AnchorPoint.from_raw_row(_raw_row(q=4000.0, eta=0.5, rh="a2"))

    def c0(row, anchor):
        kc = kappa_c_hz(row["f_real_hz"], row["q"])
        return c0_anchored(
            row["f_real_hz"], row["magnetic_filling_factor"], kc, anchor
        )

    ratio_a1 = c0(r1, a1) / c0(r2, a1)
    ratio_a2 = c0(r1, a2) / c0(r2, a2)
    assert ratio_a1 == pytest.approx(ratio_a2, rel=1e-12)


def test_g2_relative_validates_eta():
    with pytest.raises(ValueError, match="out of"):
        g2_relative(1.45e9, 1.5)
    with pytest.raises(ValueError, match="out of"):
        g2_relative(1.45e9, 0.0)


# ---------------------------------------------------------------------------
# Anchor refusal pair (rider R1)
# ---------------------------------------------------------------------------


def test_fallback_anchor_refused_without_override():
    with pytest.raises(AnchorRefusalError, match="gain_mask_is_fallback"):
        AnchorPoint.from_raw_row(_raw_row(fallback=True))


def test_fallback_anchor_allowed_as_explicit_diagnostic():
    anchor = AnchorPoint.from_raw_row(
        _raw_row(fallback=True), diagnostic_only=True
    )
    assert anchor.diagnostic_only
    # ...and everything composed against it is inadmissible.
    derived = compose_derived_row(_raw_row(), anchor=anchor)
    assert derived["admissible_for_g_regression"] is False
    assert derived["conventions"]["anchor_is_diagnostic_only"] is True


def test_anchor_from_bundle_matches_from_row(mock_bundles):
    summary = load_bundle(mock_bundles[0]).meta["summary"]
    a = AnchorPoint.from_bundle(mock_bundles[0], diagnostic_only=True)
    b = AnchorPoint.from_raw_row(summary, diagnostic_only=True)
    assert a.f_hz == b.f_hz and a.eta_h == b.eta_h
    assert a.record_hash == b.record_hash


# ---------------------------------------------------------------------------
# Derived-row contract
# ---------------------------------------------------------------------------


def test_derived_row_carries_its_conventions():
    anchor = AnchorPoint.from_raw_row(_raw_row(rh="anchor"))
    row = compose_derived_row(
        _raw_row(fallback=False), anchor=anchor, kappa_s_branch="lo"
    )
    conv = row["conventions"]
    assert conv["deload_k"] == DELOAD_K
    assert conv["planning_c0"] == PLANNING_C0
    assert conv["anchor_record_hash"] == "anchor"
    assert conv["kappa_s_branch"] == "lo"
    assert conv["kappa_s_hz"] == KAPPA_S.kappa_s_band_lo_hz
    assert "cyclic-Hz" in conv["kappa_c_convention"]
    assert "anchored ratio" in conv["c0_convention"]
    assert row["admissible_for_g_regression"] is True


def test_fallback_rows_are_inadmissible_for_the_g_regression():
    anchor = AnchorPoint.from_raw_row(_raw_row(rh="anchor"))
    derived = compose_derived_row(
        _raw_row(fallback=True), anchor=anchor
    )
    assert derived["admissible_for_g_regression"] is False


def test_validate_derived_row_refuses_bare_numbers():
    anchor = AnchorPoint.from_raw_row(_raw_row())
    row = compose_derived_row(_raw_row(), anchor=anchor)
    bare = dict(row)
    del bare["conventions"]
    with pytest.raises(DerivedRowContractError, match="missing keys"):
        validate_derived_row(bare)
    stripped = dict(row)
    stripped["conventions"] = {
        k: v
        for k, v in row["conventions"].items()
        if k != "kappa_s_branch"
    }
    with pytest.raises(DerivedRowContractError, match="kappa_s_branch"):
        validate_derived_row(stripped)


def test_write_derived_rows_never_masquerades_as_raw(tmp_path):
    anchor = AnchorPoint.from_raw_row(_raw_row())
    rows = compose_derived_rows([_raw_row()], anchor=anchor)
    with pytest.raises(DerivedRowContractError, match="masquerade"):
        write_derived_rows(tmp_path / "raw_rows.jsonl", rows)
    path = write_derived_rows(tmp_path / "derived_rows.jsonl", rows)
    assert path.is_file()


# ---------------------------------------------------------------------------
# Absolute G² — diagnostic only, schema §6 recipe
# ---------------------------------------------------------------------------


def test_g2_absolute_diagnostic_matches_schema_recipe(mock_bundles):
    report = g2_absolute_diagnostic(mock_bundles[0])
    assert "DIAGNOSTIC ONLY" in report["label"]
    assert report["gain_mask_is_fallback"] is True  # mock bundles

    # Independent second path: the schema doc §6 worked recipe,
    # dependency-free constants as printed there.
    bundle = load_bundle(mock_bundles[0])
    b, meta = bundle.arrays, bundle.meta
    GAMMA_E = 1.76085963e11
    MU_0 = 1.25663706e-6
    H_PLANCK = 6.62607015e-34
    f = meta["summary"]["f_real_hz"]
    h2 = np.sum(np.abs(b["h_complex"]) ** 2, axis=1)
    dv = 2.0 * np.pi * b["r_m"] * b["weights_m2"]
    h2_integral = np.sum(h2 * dv)
    sel = b["gain_region_mask"] & (h2 > 0)
    v_mode_j = h2_integral / h2[sel]
    g_j = GAMMA_E * np.sqrt(MU_0 * H_PLANCK * f / (2.0 * v_mode_j))
    assert report["g_j_rad_per_s_max"] == pytest.approx(
        float(np.max(g_j)), rel=1e-6
    )
    assert report["g_j_rad_per_s_min"] == pytest.approx(
        float(np.min(g_j)), rel=1e-6
    )
    # Volume-weighted histogram: counts sum to the selected gain volume.
    assert sum(report["histogram_counts_m3"]) == pytest.approx(
        float(np.sum(dv[sel])), rel=1e-9
    )


def test_spin_weight_local_identity(mock_bundles):
    """§3 cross-check identity: 1/max(w_s) = η_H × v_mode_local under
    the isotropic projection."""
    bundle = load_bundle(mock_bundles[0])
    summary = bundle.meta["summary"]
    w_s_max = float(np.max(bundle.arrays["w_spin_per_m3"]))
    lhs = 1.0 / w_s_max
    rhs = (
        summary["magnetic_filling_factor"] * summary["v_mode_local_m3"]
    )
    assert lhs == pytest.approx(rhs, rel=1e-9)


# ---------------------------------------------------------------------------
# Rider R4 — projection invariance (committed)
# ---------------------------------------------------------------------------


def _toy_arrays(hz_only: bool):
    n_r, n_z = 12, 16
    r = np.linspace(0.001, 0.01, n_r)
    z = np.linspace(0.0, 0.02, n_z)
    rr, zz = np.meshgrid(r, z, indexing="ij")
    w_r = np.gradient(r)
    w_z = np.gradient(z)
    wr, wz = np.meshgrid(w_r, w_z, indexing="ij")
    n = n_r * n_z
    h = np.zeros((n, 3), dtype=np.complex128)
    h[:, 2] = (1.0 + rr.ravel() / 0.01) * np.sin(
        np.pi * zz.ravel() / 0.02
    )
    if not hz_only:
        h[:, 0] = 0.7 * np.cos(np.pi * zz.ravel() / 0.02) * (
            rr.ravel() / 0.01
        )
    gain = (rr.ravel() < 0.004) & (zz.ravel() > 0.005) & (
        zz.ravel() < 0.015
    )
    return {
        "h_complex": h,
        "gain_region_mask": gain,
        "r_m": rr.ravel(),
        "weights_m2": (wr * wz).ravel(),
    }


def test_eta_projection_axial_toy_is_projection_invariant():
    arrays = _toy_arrays(hz_only=True)
    eta_iso = eta_h_under_projection(
        arrays, SpinProjection.isotropic_h2()
    )
    eta_axial = eta_h_under_projection(
        arrays, SpinProjection.axis_projected(1.0)
    )
    # A pure-H_z mode: both projections integrate the same density.
    assert eta_axial == pytest.approx(eta_iso, rel=1e-12)


def test_eta_projection_mixed_toy_differs():
    arrays = _toy_arrays(hz_only=False)
    eta_iso = eta_h_under_projection(
        arrays, SpinProjection.isotropic_h2()
    )
    eta_axial = eta_h_under_projection(
        arrays, SpinProjection.axis_projected(1.0)
    )
    assert abs(eta_axial / eta_iso - 1.0) > 1e-3


def test_r4_report_structure_and_summary_column_closure(mock_bundles):
    report = projection_invariance_report(
        mock_bundles, escalation_threshold=0.05
    )
    assert report["projection"].startswith("axis_projected")
    assert len(report["per_bundle"]) == 3
    for entry in report["per_bundle"]:
        # The isotropic recomputation closes on the raw summary column.
        assert entry["eta_h_isotropic"] == pytest.approx(
            entry["eta_h_isotropic_summary_column"], rel=1e-9
        )
    # First bundle anchors the law: its shift is exactly zero.
    assert report["per_bundle"][0]["anchored_law_shift"] == 0.0
    assert report["max_abs_anchored_law_shift"] >= 0.0


def test_r4_escalation_flag_thresholds(mock_bundles):
    tiny = projection_invariance_report(
        mock_bundles, escalation_threshold=1e-12
    )
    # θ-varying mock bundles have a non-zero (if small) spread.
    assert tiny["max_abs_anchored_law_shift"] > 0.0
    assert tiny["escalate"] is True
    assert "ESCALATED" in tiny["escalate_meaning"]
    huge = projection_invariance_report(
        mock_bundles, escalation_threshold=0.5
    )
    assert huge["escalate"] is False


def test_r4_needs_at_least_two_bundles(mock_bundles):
    with pytest.raises(ValueError, match=">= 2 bundles"):
        projection_invariance_report(
            mock_bundles[:1], escalation_threshold=0.05
        )
