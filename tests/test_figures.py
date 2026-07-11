"""Regeneration pins for the figure set (`cavity.figures`).

Per the byte-pin/regeneration-pin precedent, but pinning the DATA ARRAYS
feeding each figure, not binary images (no RNG anywhere; determinism
from fixed committed inputs + shared rcParams). Data-pin tests import no
matplotlib — `build_data()` is matplotlib-free by contract; only the
render smoke test touches the Agg backend. Tests that consume the
archived §5a LFS npz skip with a clear reason on checkouts without the
materialised archive (the gate-record-fixture behaviour).
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

from cavity.figures import FIGURE_MODULES
from cavity.figures import f1_mode_maps as f1
from cavity.figures import f2_reproduction_table as f2
from cavity.figures import f3_delta_t_map as f3
from cavity.figures import f4_cavity_arm_envelope as f4
from cavity.figures import f5_margin_waterfall as f5
from cavity.figures import f6_singh_axis_map as f6
from cavity.provenance.constants import DF_SPIN_DT

REPO_ROOT = Path(__file__).resolve().parent.parent
ONEPAGER = REPO_ROOT / "docs" / "supervisor_onepager_2026-07.md"
MARGIN_REPORT = REPO_ROOT / "thermal" / "reports" / "q_margin_planning_point.md"

_LFS_POINTER_PREFIX = b"version https://git-lfs"


def _archive_record_or_skip(record_hash: str) -> None:
    """Skip (never fail) when the §5a archive npz is absent/unsmudged."""
    fields_npz = f1.SOLVES_ROOT / record_hash / "fields.npz"
    if not fields_npz.is_file():
        pytest.skip(
            f"archived §5a record not present at {fields_npz} — "
            "refs/gate_runs missing from this checkout"
        )
    with open(fields_npz, "rb") as fh:
        head = fh.read(len(_LFS_POINTER_PREFIX))
    if head.startswith(_LFS_POINTER_PREFIX):
        pytest.skip(
            "refs/gate_runs fields.npz is an unsmudged git-lfs pointer — "
            "run `git lfs pull` to materialise the §5a archive"
        )


def test_f1_data_pins():
    """The plotted grid ties back to the archived canonical record — and
    the V_mode recomputed from the plotted |H|² grid IS the failing gate
    number's field (canonical twin of the gated faithful value)."""
    _archive_record_or_skip(f1.CANONICAL_RECORD_HASH)
    had_mpl = "matplotlib" in sys.modules
    data = f1.build_data()
    if not had_mpl:  # build_data is matplotlib-free by contract
        assert "matplotlib" not in sys.modules

    assert data["grid_shape"] == (201, 301)
    assert data["r_mm"].shape == (201, 301)
    assert data["f_prime_hz"] == pytest.approx(1450382241.977, abs=1.0)
    assert data["q0"] == pytest.approx(6764.5852, abs=1e-3)
    assert data["v_mode_global_m3"] == pytest.approx(6.557764e-07, rel=1e-6)
    assert data["record_hash"] == f1.CANONICAL_RECORD_HASH
    assert data["mesh_element_count"] == 7492
    # normalisation: each panel to its own max
    assert data["e_norm"].max() == pytest.approx(1.0)
    assert data["h_norm"].max() == pytest.approx(1.0)
    # mode-ID facts quoted in the caption
    assert data["azimuthal_e_energy_fraction"] == pytest.approx(1.0, abs=1e-12)
    assert data["axis_hz_sign_changes"] == 0


def test_f2_data_pins():
    """Re-based manifest values, including the 225/360 diagnostic."""
    _archive_record_or_skip(f2.CANONICAL_RECORD_HASH)
    had_mpl = "matplotlib" in sys.modules
    data = f2.build_data()
    if not had_mpl:
        assert "matplotlib" not in sys.modules

    values = [d["value_cm3"] for d in data["diagnostics"]]
    assert values[0] == pytest.approx(0.6557763612558703, rel=1e-9)  # H global
    assert values[1] == pytest.approx(0.6557763612558703, rel=1e-9)  # H local
    assert values[2] == pytest.approx(0.8590994041846185, rel=1e-9)  # E-based
    assert values[3] == pytest.approx(0.4804126043251043, rel=1e-9)  # eps-E
    # the amendment row — computed from the archived finest-level grid
    assert data["v_diel_restricted_m3"] == pytest.approx(
        1.8137822014713855e-07, rel=1e-6
    )
    assert values[4] == pytest.approx(0.18137822, rel=1e-6)
    assert values[5] == pytest.approx(0.40986022578491893, rel=1e-9)
    assert data["diagnostics"][5]["label"].startswith("committed × 225/360")
    assert data["v_window_m3"] == pytest.approx((6.47856e-07, 6.60944e-07))
    assert data["v_diel_in_window"] is False

    rows = data["rows"]
    assert rows[4]["verdict"] == "PASS"
    assert rows[5]["verdict"] == "PASS"
    assert rows[1]["delta"] == "+0.02%"
    assert rows[4]["delta"] == "+0.21%"
    assert data["q0_faithful"] == pytest.approx(6981.3163, abs=1e-3)
    assert data["q0_canonical"] == pytest.approx(6764.5852, abs=1e-3)
    assert data["branch_delta_pct"] == pytest.approx(-3.10, abs=0.01)
    assert (data["n_pass"], data["n_fail"], data["n_deferred"]) == (5, 0, 1)
    assert data["phase1_complete"] is False
    assert data["rejudge_run_dir"] == "20260711T132705Z_rejudge"
    assert data["source_run_dir"] == "20260710T083340Z_live_comsol"


def test_f3_data_pins():
    """The committed worked-example stack regenerates at P = 50 mW
    (worked-example pins × 0.05 — ΔT strictly linear in P), and the
    boundary-flux energy diagnostic closes to P."""
    data = f3.build_data()
    assert data["p_abs_w"] == 0.05
    assert data["peak_k"] == pytest.approx(1.057203696e3 * 0.05, rel=1e-6)
    assert data["vol_avg_k"] == pytest.approx(3.703239268e2 * 0.05, rel=1e-6)
    assert abs(data["boundary_power_w"] - data["p_abs_w"]) < 1e-6 * data["p_abs_w"]
    assert data["delta_t_k"].shape == (161, 121)
    # the illuminated-face axis point carries the solver's peak; the
    # sampled grid may exceed it only by radial-series ripple (<0.5%)
    assert data["delta_t_k"][0, 0] == pytest.approx(data["peak_k"], rel=1e-9)
    assert data["delta_t_k"].max() == pytest.approx(data["peak_k"], rel=5e-3)
    # linearity spot check
    double = f3.build_data(p_abs_w=0.10)
    assert double["peak_k"] == pytest.approx(2.0 * data["peak_k"], rel=1e-9)


def test_f4_data_pins():
    """Endpoint and the three A10 ratio windows (same bounds as anchor
    A10 in test_thermal_detuning.py); spin-band endpoints from DF_SPIN_DT."""
    data = f4.build_data()
    assert data["endpoint_integrated_hz"] == pytest.approx(82.61e6, rel=1e-3)
    assert 1.003 < data["ratio_vs_point_300"] < 1.012
    assert 1.060 < data["ratio_vs_first_order"] < 1.075
    assert 0.945 < data["ratio_vs_slope_293"] < 0.965
    lo, hi = data["spin_endpoints_hz"]
    assert lo == pytest.approx(DF_SPIN_DT.df_dt_band_lo_hz_per_k * 30.0)
    assert hi == pytest.approx(DF_SPIN_DT.df_dt_band_hi_hz_per_k * 30.0)
    assert lo < hi < 0  # true (negative) sign, band drawn below zero


def test_f5_data_pins():
    """Stage values equal the byte-pinned margin report's numbers, and
    the committed report file still prints exactly those numbers."""
    data = f5.build_data()
    assert data["q0"] == pytest.approx(6764.5852, abs=1e-3)
    assert data["q_l"] == pytest.approx(5637.1543628606305, rel=1e-12)
    assert data["kappa_c_hz"] == pytest.approx(257221.9788, rel=1e-6)
    assert data["df_max_hz"] == pytest.approx(1768108.7824, abs=1e-4)
    assert data["dt_max_k"] == pytest.approx(0.6030, abs=1e-4)
    band_lo, band_hi = data["dt_max_band_k"]
    assert band_lo == pytest.approx(0.585, abs=5e-4)
    assert band_hi == pytest.approx(0.748, abs=5e-4)
    assert data["p_e"] == 0.9974999896719232
    assert data["p_e_record_hash"] == "823e67969516bcf2"

    report = MARGIN_REPORT.read_text(encoding="utf-8")
    assert "**ΔT_max = 0.6030 K**" in report
    assert "[0.585, 0.748] K" in report
    assert "kappa_c = f/Q_L = 257.222 kHz" in report
    assert "| 190 | 1.7681 |" in report
    assert f"p_e = {data['p_e']!r}" in report


def test_f6_data_pins():
    """Affine map scale/offset/rms via `affine_map_vs_extraction()` (same
    tolerances as tests/test_provenance_df_spin_dt.py), the four window
    fits, and the carried band endpoints."""
    data = f6.build_data()
    assert data["affine_scale"] == pytest.approx(0.9316, abs=0.001)
    assert data["affine_offset_k"] == pytest.approx(16.56, abs=0.1)
    assert data["affine_rms_k"] <= 0.15
    assert data["slope_inflation"] == pytest.approx(1.073, abs=0.002)
    slopes = [f["slope_khz_per_k"] for f in data["fits"]]
    for got, expected in zip(slopes, (-102.3, -108.5, -119.7, -64.4)):
        assert math.isclose(got, expected, abs_tol=0.5), (got, expected)
    assert data["band_khz_per_k"] == (
        DF_SPIN_DT.df_dt_band_lo_hz_per_k / 1e3,
        DF_SPIN_DT.df_dt_band_hi_hz_per_k / 1e3,
    )
    assert data["graded_point_khz_per_k"] == DF_SPIN_DT.df_dt_hz_per_k / 1e3
    assert len(data["t_fig_on_raw_k"]) == len(data["t_raw_k"]) == 197


# per-figure SPEC status flags that must ride in the committed captions
CAPTION_FLAGS = {
    "f1_mode_maps": ("GREEN", "re-based 2026-07-11", "CANONICAL"),
    "f2_reproduction_table": (
        "RESOLVED",
        "ALL LIVE-JUDGED ROWS PASS",
        "`phase1_complete` remains false",
        "only the 225/360 factor does",
    ),
    "f3_delta_t_map": (
        "ILLUSTRATIVE", "UNSOURCED-SCOPING", "planning assumptions",
    ),
    "f4_cavity_arm_envelope": ("UNRESOLVED", "not his verbatim range"),
    "f5_margin_waterfall": (
        "OWN-MODEL",
        "COMPOSED",
        "UNRATIFIED-w_s",
        "planning point, not a claim",
    ),
    "f6_singh_axis_map": (
        "UNRESOLVED", "branch choice, not a best estimate",
    ),
}


def test_captions_pinned_in_onepager():
    """Each module's CAPTION appears VERBATIM in the one-pager, and each
    figure's status-flag words are present in its caption."""
    text = ONEPAGER.read_text(encoding="utf-8")
    for name in FIGURE_MODULES:
        module = sys.modules[f"cavity.figures.{name}"]
        assert module.CAPTION in text, f"{name} caption not verbatim in one-pager"
        for flag in CAPTION_FLAGS[name]:
            assert flag in module.CAPTION, f"{name} caption missing flag {flag!r}"
        assert f"figures/{name}.png" in text  # the figure itself is embedded


def test_render_smoke_shared_style(tmp_path):
    """Every figure renders under Agg with the shared rcParams and writes
    both PDF + PNG (to tmp_path — never touching docs/figures)."""
    matplotlib = pytest.importorskip("matplotlib")
    _archive_record_or_skip(f1.CANONICAL_RECORD_HASH)
    import matplotlib.pyplot as plt

    from cavity.figures import _style

    for name in FIGURE_MODULES:
        module = sys.modules[f"cavity.figures.{name}"]
        fig = module.render(module.build_data())
        assert matplotlib.get_backend().lower() == "agg"
        assert matplotlib.rcParams["text.usetex"] is False
        assert matplotlib.rcParams["font.family"] == ["serif"]
        paths = _style.save_figure(fig, name, tmp_path)
        plt.close(fig)
        assert [p.suffix for p in paths] == [".pdf", ".png"]
        for p in paths:
            assert p.is_file() and p.stat().st_size > 0, p
