"""V1 heatmap bundle pins (viz/PLAN.md Phase 1 acceptance).

Regenerates the full 264-scenario set from committed constants
(all-closed-form; seconds) and asserts, per the ratified plan:

  (a) outer-product parity — reconstruction from the bundle's f32 factor
      matrices matches `sol.delta_t` on the grid to ≤ 1e-6 relative
      (float32 transport bound; atol = 1e-6·peak near Dirichlet zeros);
  (b) energy — `deficit_rel` ≤ 1e-6 across all 264 scenarios (the F3
      caption's "boundary flux = P_abs to solver truncation" level);
  (c) hash pins — the index canonical-bytes SHA-256 is pinned here, the
      index records every bundle's SHA-256, and the committed viz/data
      files must reproduce the regenerated canonical bytes;
  (d) R4 cross-pin — every captions.py token appears verbatim in its
      source CAPTION; orphan tokens (no registered caption source) fail;
  (e) R3 — no commit_sha / generated_utc anywhere in a bundle;
  (f) R1 — the committed viz/data footprint sits under the 10 MB stop rule.

Pin conventions: all temperatures are kelvin at P_ref = 0.05 W
(ILLUSTRATIVE; ΔT strictly linear in P), grids in mm, hashes over the
DECOMPRESSED canonical JSON (gzip drift can never move a pin).
"""

from __future__ import annotations

import importlib
import math
from pathlib import Path

import numpy as np
import pytest

from cavity.figures import f3_delta_t_map as f3
from cavity.provenance.constants import EMISSIVITY_PTP, K_PTP, L_ABS_PUMP
from cavity.thermal.radiation import h_rad_linearized
from cavity.viz import bundles, captions
from cavity.viz.bundles import (
    DEFAULT_SCENARIO_ID,
    canonical_json_bytes,
    decode_array,
    encode_array,
    enumerate_scenarios,
    js_wrapper,
    scenario_solver_inputs,
    sha256_hex,
    unwrap_js,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "viz" / "data"

# the regeneration pin (acceptance (c)): SHA-256 of the canonical index
# bytes — transitively pins every scenario/basis bundle through the
# per-bundle sha256 fields the index records
INDEX_SHA256 = "d04b02e8067a0c5a3d12a6fa64b46c49655846d3aa800775a1f46f16202be16a"

STOP_RULE_BYTES = 10 * 1024 * 1024  # R1: >10 MB halts before any git add


@pytest.fixture(scope="module")
def built() -> dict:
    pytest.importorskip("matplotlib")
    from cavity.viz.export import magma_lut

    return bundles.build_heatmap_bundles(magma_lut())


def _index_payload(built: dict) -> dict:
    return built["bundles"]["index"]["payload"]


# --- lattice structure (§4) ---------------------------------------------------


def test_lattice_counts(built):
    """288 cells, 264 valid, 24 structurally invalid (recorded, not
    missing), 16 deduplicated radial bases."""
    rows = _index_payload(built)["scenarios"]
    assert len(rows) == 288
    valid = [r for r in rows if "sha256" in r]
    invalid = [r for r in rows if "invalid" in r]
    assert len(valid) == 264
    assert len(invalid) == 24
    for r in invalid:
        assert "all-insulated" in r["invalid"]
        assert "sha256" not in r and "basis_id" not in r
        # the invalid cells are exactly base = Robin ∧ h_conv = 0 ∧ rad off
        assert r["axes"][2] == 0 and r["axes"][3] == 0 and r["axes"][4] == 1
    assert len(_index_payload(built)["bases"]) == 16
    # deterministic lexicographic order over axis indices (§3.2)
    axis_tuples = [tuple(r["axes"]) for r in rows]
    assert axis_tuples == sorted(axis_tuples)


def test_scenario_files_match_manifest(built):
    """Every valid manifest row has its bundle; recorded sha256 values are
    the canonical-bytes hashes; basis ids resolve."""
    basis_ids = {b["id"] for b in _index_payload(built)["bases"]}
    for r in _index_payload(built)["scenarios"]:
        if "invalid" in r:
            continue
        name = f"scenario/{r['id']}"
        assert built["sha256"][name] == r["sha256"]
        assert sha256_hex(built["canonical"][name]) == r["sha256"]
        assert r["basis_id"] in basis_ids


def test_bases_dedup_and_bi_collision_free(built):
    """One shared Bi_s = 0 basis + 15 nonzero (h_eff, k) pairs with no Bi
    collisions (PLAN §3.2, computed there — re-asserted on the data)."""
    rows = _index_payload(built)["bases"]
    bi = [r["bi_side"] for r in rows]
    assert len(set(bi)) == 16
    bi0 = [r for r in rows if r["id"] == "rb_bi0"]
    assert len(bi0) == 1 and bi0[0]["bi_side"] == 0.0 and bi0[0]["has_constant_mode"]
    for r in rows:
        if r["id"] != "rb_bi0":
            assert r["bi_side"] > 0.0 and not r["has_constant_mode"]


# --- acceptance (a) + (b): parity and energy over the full lattice ------------


def test_parity_and_deficit_all_scenarios(built):
    """Acceptance (a): |f32-reconstruction − sol.delta_t| ≤ 1e-6·peak on
    the full grid, every valid scenario. Acceptance (b): deficit_rel ≤
    1e-6 everywhere (Robin-side lattice — the documented fast-tail
    regime). Truncation bound recorded per scenario and ≪ the parity
    budget; Bi_s = 0 cells collapse to the constant mode (n_kept = 1)."""
    r_m, z_m = bundles.heatmap_grids()
    for sc in enumerate_scenarios():
        if not sc.valid:
            with pytest.raises(ValueError, match="all-insulated"):
                scenario_solver_inputs(sc)
            continue
        bundle = built["bundles"][f"scenario/{sc.scenario_id}"]
        payload = bundle["payload"]
        theta = decode_array(payload["theta_k"]).astype(np.float64)
        basis = decode_array(
            built["bundles"][f"bases/{sc.basis_id}"]["payload"]["radial_basis"]
        ).astype(np.float64)
        n_kept = payload["n_kept"]
        assert theta.shape == (n_kept, 161)
        assert basis.shape == (64, 121)
        recon = np.einsum("ni,nj->ij", theta, basis[:n_kept])

        from cavity.thermal.cylinder import solve

        spec, src = scenario_solver_inputs(sc)
        sol = solve(spec, src, n_modes=bundles.N_MODES)
        exact = sol.delta_t(r_m[None, :], z_m[:, None])
        peak = float(np.abs(exact).max())
        assert np.max(np.abs(recon - exact)) <= 1e-6 * peak, sc.scenario_id

        assert payload["deficit_rel"] <= 1e-6, sc.scenario_id
        # each dropped row is < TRUNCATION_REL·peak, so the recorded summed
        # tail is structurally ≤ n_dropped × threshold ≪ the 1e-6 budget
        assert 0.0 <= payload["truncation_bound_rel"] <= (
            (bundles.N_MODES - payload["n_kept"]) * bundles.TRUNCATION_REL
        )
        if sc.h_eff_w_m2_k == 0.0:
            assert n_kept == 1  # constant mode only (flood ⊥ J₁-zero basis)


def test_default_scenario_is_the_f3_stack(built):
    """The §3.2 default = the F3 committed worked-example stack; its
    scalars reproduce the committed F3/worked-example pins (kelvin at
    P_ref = 0.05 W — the worked-example 1 W pins × 0.05, exact
    linearity)."""
    assert DEFAULT_SCENARIO_ID == "k-mid_bl-200um_hc-20_rad-on_base-dir"
    assert _index_payload(built)["shared"]["default_scenario_id"] == (
        DEFAULT_SCENARIO_ID
    )
    payload = built["bundles"][f"scenario/{DEFAULT_SCENARIO_ID}"]["payload"]
    assert payload["peak_k"] == pytest.approx(1.057203696e3 * 0.05, rel=1e-6)
    assert payload["vol_avg_k"] == pytest.approx(3.703239268e2 * 0.05, rel=1e-6)
    assert payload["basis_id"] == "rb_k-mid_hc-20_rad-on"
    # F3 build_data agreement (identical committed calls): exact linearity
    data = f3.build_data()
    assert payload["peak_k"] == pytest.approx(data["peak_k"], rel=1e-12)
    assert payload["vol_avg_k"] == pytest.approx(data["vol_avg_k"], rel=1e-12)


def test_n_grid_scalars(built):
    """§3.2 N-grid readout steps: keys {4..64}; the N = 64 entry is the
    top-level scalar set (same solve object — identical floats); deficit
    at every N recorded and finite."""
    payload = built["bundles"][f"scenario/{DEFAULT_SCENARIO_ID}"]["payload"]
    grid = payload["n_grid_scalars"]
    assert sorted(grid, key=int) == ["4", "8", "16", "32", "48", "64"]
    assert grid["64"]["peak_k"] == payload["peak_k"]
    assert grid["64"]["vol_avg_k"] == payload["vol_avg_k"]
    assert grid["64"]["deficit_rel"] == payload["deficit_rel"]
    for entry in grid.values():
        assert math.isfinite(entry["peak_k"])
        assert entry["deficit_rel"] >= 0.0


# --- envelope + header discipline (§3.1, R3) ----------------------------------


def test_envelope_contract(built):
    """Every bundle carries the §3.1 envelope: schema version 1, view,
    generator, the imported F3 caption verbatim, registered flag tokens,
    and the solver identity block."""
    for name, bundle in built["bundles"].items():
        assert bundle["viz_bundle_schema_version"] == 1
        assert bundle["view"] == "heatmap"
        assert bundle["generator"].startswith("cavity.viz.bundles:")
        assert bundle["caption"] == f3.CAPTION
        assert bundle["status_flags"] == captions.ordered_flags(
            bundle["status_flags"]
        )
        assert bundle["inputs"]["solver"]["n_modes"] == 64
        if name.startswith("scenario/") or name == "index":
            assert bundle["inputs"]["solver"]["grid_r"] == 121
            assert bundle["inputs"]["solver"]["grid_z"] == 161


def test_r3_no_clock_no_sha_in_bundles(built):
    """R3 regression: commit_sha / generated_utc were withdrawn from the
    header schema — they must appear nowhere in any bundle's bytes."""
    for raw in built["canonical"].values():
        assert b"commit_sha" not in raw
        assert b"generated_utc" not in raw


def test_constants_emitted_from_imported_objects(built):
    """Input identity: header constants equal the imported graded objects
    (units: W m⁻¹K⁻¹ for k, W m⁻²K⁻¹ for h, m for l_abs). The h_rad
    composition value is the committed function's output — the §1.5
    computed value 5.511603935447267 W m⁻²K⁻¹ (ε = 0.90, 300 K)."""
    h_rad = h_rad_linearized(EMISSIVITY_PTP.eps_nominal, 300.0)
    assert h_rad == 5.511603935447267
    consts = built["bundles"][f"scenario/{DEFAULT_SCENARIO_ID}"]["inputs"][
        "constants"
    ]
    assert consts["K_PTP.k_mid_w_m_k"] == K_PTP.k_mid_w_m_k
    assert consts["L_ABS_PUMP.l_abs_scoping_grid_m[5]"] == (
        L_ABS_PUMP.l_abs_scoping_grid_m[5]
    )
    assert consts["h_rad_linearized(EMISSIVITY_PTP.eps_nominal, 300.0)"] == h_rad
    scen = built["bundles"][f"scenario/{DEFAULT_SCENARIO_ID}"]["inputs"]["scenario"]
    assert scen["h_eff_w_m2_k"] == 20.0 + h_rad
    assert scen["p_ref_w"] == 0.05


# --- axes manifest (§3.2, R2) -------------------------------------------------


def test_axes_manifest_and_reserved_slots(built):
    """Axis values equal the committed constants; the radial_profile axis
    ships flood-only with `disc`/`gaussian` as reserved, UNPOPULATED
    slot names (R2)."""
    axes = {a["id"]: a for a in _index_payload(built)["axes"]}
    assert axes["k"]["values"] == [
        K_PTP.k_band_lo_w_m_k,
        K_PTP.k_mid_w_m_k,
        K_PTP.k_band_hi_w_m_k,
    ]
    dep = axes["deposition"]
    assert dep["values"][:6] == list(L_ABS_PUMP.l_abs_scoping_grid_m)
    assert dep["values"][6:] == [None, None]
    assert dep["value_ids"][6:] == ["uniform", "surface"]
    assert axes["h_conv"]["values"] == [0.0, 5.0, 20.0]
    rad = axes["h_rad"]
    assert rad["values"][0] == 0.0
    assert rad["values"][1] == h_rad_linearized(EMISSIVITY_PTP.eps_nominal, 300.0)
    prof = axes["radial_profile"]
    assert prof["value_ids"] == ["flood"]
    assert prof["reserved_slots"] == ["disc", "gaussian"]
    # per-value flags are registered captions tokens
    for axis in axes.values():
        for flags in axis["flags"]:
            assert flags == captions.ordered_flags(flags)


def test_shared_block(built):
    """Grids in mm, P_ref = 50 mW ILLUSTRATIVE, 0–200 mW display choice,
    magma LUT parity with `_style.SEQUENTIAL_THERMAL`, encoding rule
    outcome recorded."""
    shared = _index_payload(built)["shared"]
    r_mm = decode_array(shared["r_mm"])
    z_mm = decode_array(shared["z_mm"])
    assert r_mm.shape == (121,) and z_mm.shape == (161,)
    assert r_mm[0] == 0.0 and r_mm[-1] == pytest.approx(1.5, rel=1e-12)
    assert z_mm[-1] == pytest.approx(8.0, rel=1e-12)
    assert shared["p_ref_w"] == 0.05
    assert shared["p_display_max_w"] == 0.2
    assert shared["lut_name"] == "magma"
    lut = decode_array(shared["lut_rgb_u8"])
    assert lut.shape == (256, 3) and lut.dtype == np.uint8
    assert shared["max_deficit_rel"] <= 1e-6
    # §3.1 decision rule: gzip iff measured saving ≥ 30%
    expected = "gzip" if built["gzip_saving_frac"] >= 0.30 else "plain"
    assert built["wrapper_encoding"] == expected
    assert shared["wrapper_encoding"] == expected
    assert shared["canonical_bytes_total"] == sum(
        len(b) for n, b in built["canonical"].items() if n != "index"
    )


# --- acceptance (c): hash pins + committed bytes ------------------------------


def test_index_hash_pin(built):
    """The regeneration pin: canonical index bytes hash to the committed
    constant (drift in any constant, solver output, or serialiser is a
    deliberate re-mint, never silent)."""
    assert sha256_hex(built["canonical"]["index"]) == INDEX_SHA256
    assert built["sha256"]["index"] == INDEX_SHA256


def test_committed_files_match_regeneration(built):
    """The committed viz/data set byte-verifies against regeneration
    (index.json = canonical bytes; every .js unwraps to its canonical
    bytes; no strays). Same routine the CLI --check runs."""
    from cavity.viz.export import verify_data_dir

    assert DATA_DIR.is_dir(), "viz/data missing — run python -m cavity.viz.export"
    problems = verify_data_dir(built, DATA_DIR)
    assert problems == []


def test_committed_size_within_stop_rule():
    """R1: the committed footprint stays under the 10 MB stop threshold
    (the Phase-1 gate ran before these files were ever staged)."""
    total = sum(p.stat().st_size for p in DATA_DIR.rglob("*") if p.is_file())
    assert 0 < total <= STOP_RULE_BYTES


# --- serialisation (§3.1) -----------------------------------------------------


def test_serialisation_deterministic_and_roundtrip():
    obj = {"b": [1.5, 2.0], "a": {"x": encode_array(np.arange(6.0), "f8")}}
    raw1, raw2 = canonical_json_bytes(obj), canonical_json_bytes(obj)
    assert raw1 == raw2
    assert raw1.endswith(b"\n")
    arr = np.linspace(0.0, 1.0, 7, dtype=np.float64)
    for dtype in ("f4", "f8"):
        dec = decode_array(encode_array(arr, dtype))
        np.testing.assert_allclose(dec, arr, rtol=0 if dtype == "f8" else 1e-6)
    with pytest.raises(ValueError):
        canonical_json_bytes({"bad": float("nan")})
    for encoding in ("gzip", "plain"):
        wrapped = js_wrapper("scenario/x", raw1, encoding)
        assert wrapped.startswith(b"window.VIZ_DATA = window.VIZ_DATA || {};")
        assert b'window.VIZ_DATA["scenario/x"]' in wrapped
        assert unwrap_js(wrapped) == raw1
    with pytest.raises(ValueError):
        js_wrapper("x", raw1, "zstd")


# --- R4 cross-pin -------------------------------------------------------------


def test_captions_cross_pin(built):
    """R4 condition (a): every registered token appears VERBATIM as a
    substring of its source CAPTION, and every FLAG_* string constant in
    captions.py is registered (an orphan token — declared but sourceless
    — fails here). Every flag emitted into any bundle is a registered
    token (never retyped inline)."""
    declared = {
        v
        for k, v in vars(captions).items()
        if k.startswith("FLAG_") and isinstance(v, str)
    }
    assert declared == set(captions.FLAG_SOURCES), "orphan or unregistered token"
    for token, source in captions.FLAG_SOURCES.items():
        caption = importlib.import_module(source).CAPTION
        assert token in caption, f"token not verbatim in {source}: {token!r}"
    for bundle in built["bundles"].values():
        for flag in bundle["status_flags"]:
            assert flag in captions.FLAG_SOURCES
    with pytest.raises(ValueError, match="unregistered"):
        captions.ordered_flags(["not a committed token"])


def test_captions_module_is_subordinate():
    """R4 condition (b): the module states its subordination — captions
    win on any conflict."""
    doc = captions.__doc__
    assert "DERIVED AND SUBORDINATE" in doc
    assert "CAPTIONs win" in doc


# --- export CLI ---------------------------------------------------------------


def test_export_cli_rejects_unbuilt_views():
    from cavity.viz.export import main

    with pytest.raises(SystemExit) as exc:
        main(["modes"])
    assert exc.value.code == 2
