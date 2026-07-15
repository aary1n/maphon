"""L1 design-matrix generation — §6 budget ledger, Sobol determinism,
per-DOF transforms, and the solve-ready hard-refusal pairs.
"""

from __future__ import annotations

import numpy as np
import pytest
from scipy import stats
from scipy.stats import qmc

from cavity.provenance import GEOM_BOOTH_TE01D, STO, TOL
from cavity.sweep.design import (
    ACTIVE_LEARNING_RESERVE_SOLVES,
    CONFINEMENT_TRAJECTORY_SOLVES,
    ECCENTRICITY_CONTINGENCY_SOLVES,
    HELD_OUT_SOLVES,
    MESH_SPOT_CHECK_SOLVES,
    ORDER2_BASIS_TERMS,
    PHASE1B_VERIFICATION_SOLVES,
    SOLVE_BUDGET_CEILING,
    SOLVE_BUDGET_FLOOR,
    TRAINING_SOLVES,
    DesignBlock,
    EpsilonRVariant,
    GeometryDistributionVariant,
    SamplingDim,
    generate_design,
    materialise_dims,
    total_budgeted_solves,
)
from cavity.sweep.dofs import (
    DesignMode,
    DistributionKind,
    MockResolutionError,
    ResolutionContext,
    Rung,
    SentinelResolution,
    UnresolvedTodoTraceError,
    mock_resolutions,
)

SEED = 20260715


# ---------------------------------------------------------------------------
# §6 budget ledger — committed numbers verbatim
# ---------------------------------------------------------------------------


def test_block_counts_verbatim_from_design_doc_section_6():
    assert PHASE1B_VERIFICATION_SOLVES == 5  # 4 + 1 PEC arm (corrected)
    assert TRAINING_SOLVES[DesignMode.BASELINE_D8] == 120
    assert TRAINING_SOLVES[DesignMode.DEGRADED_D7] == 97
    assert HELD_OUT_SOLVES == 30
    assert ACTIVE_LEARNING_RESERVE_SOLVES == 40
    assert MESH_SPOT_CHECK_SOLVES == 4
    assert CONFINEMENT_TRAJECTORY_SOLVES == 10
    assert ECCENTRICITY_CONTINGENCY_SOLVES == 6


def test_ledger_totals_209_and_186():
    assert total_budgeted_solves(DesignMode.BASELINE_D8) == 209
    assert total_budgeted_solves(DesignMode.DEGRADED_D7) == 186
    assert (
        total_budgeted_solves(
            DesignMode.BASELINE_D8, include_eccentricity_contingency=True
        )
        == 215
    )
    assert (
        total_budgeted_solves(
            DesignMode.DEGRADED_D7, include_eccentricity_contingency=True
        )
        == 192
    )


def test_ledger_sits_inside_the_hard_budget_window():
    assert SOLVE_BUDGET_FLOOR == 150 and SOLVE_BUDGET_CEILING == 300
    for mode in DesignMode:
        total = total_budgeted_solves(
            mode, include_eccentricity_contingency=True
        )
        assert SOLVE_BUDGET_FLOOR <= total <= SOLVE_BUDGET_CEILING


def test_order2_basis_terms_pinned():
    # C(8+2, 2) = 45 and C(7+2, 2) = 36 — design doc §6/§9.
    assert ORDER2_BASIS_TERMS[DesignMode.BASELINE_D8] == 45
    assert ORDER2_BASIS_TERMS[DesignMode.DEGRADED_D7] == 36


# ---------------------------------------------------------------------------
# Materialisation and the refusal gate
# ---------------------------------------------------------------------------


def test_materialise_refuses_on_unresolved_rows_naming_questions():
    with pytest.raises(UnresolvedTodoTraceError) as exc:
        materialise_dims(DesignMode.BASELINE_D8, ResolutionContext())
    assert exc.value.question_ids == ("Q2", "Q9")

    with pytest.raises(UnresolvedTodoTraceError) as exc:
        materialise_dims(DesignMode.DEGRADED_D7, ResolutionContext())
    assert exc.value.question_ids == ("Q9",)


def test_materialise_with_mock_context_yields_flagged_dims():
    dims = materialise_dims(DesignMode.BASELINE_D8, mock_resolutions())
    by_name = {d.name: d for d in dims}
    assert len(dims) == 8
    assert by_name["bore_radius_m"].mock
    assert by_name["p_tune"].mock and by_name["p_tune"].is_control
    assert not by_name["epsilon_r"].mock  # committed rows are not mock


def test_geometry_uniform_variant_switches_rows_1_to_4_and_bore():
    dims = materialise_dims(
        DesignMode.BASELINE_D8,
        mock_resolutions(),
        geometry_distribution=GeometryDistributionVariant.UNIFORM,
    )
    by_name = {d.name: d for d in dims}
    for name in (
        "box_radius_m",
        "box_height_m",
        "torus_minor_radius_m",
        "torus_major_radius_m",
        "bore_radius_m",
    ):
        assert by_name[name].distribution is DistributionKind.UNIFORM
    # εr/tanδ are untouched by the geometry variant.
    assert by_name["epsilon_r"].distribution is DistributionKind.UNIFORM
    assert by_name["tan_delta"].distribution is DistributionKind.UNIFORM


def test_eps_r_triangular_variant():
    dims = materialise_dims(
        DesignMode.DEGRADED_D7,
        mock_resolutions(),
        eps_r_variant=EpsilonRVariant.TRIANGULAR,
    )
    by_name = {d.name: d for d in dims}
    assert (
        by_name["epsilon_r"].distribution
        is DistributionKind.TRIANGULAR_NOMINAL_PEAK
    )
    assert by_name["tan_delta"].distribution is DistributionKind.UNIFORM


# ---------------------------------------------------------------------------
# Sampling transforms
# ---------------------------------------------------------------------------


def test_trunc_gaussian_dim_matches_scipy_truncnorm_ppf():
    spec = SamplingDim(
        name="box_radius_m",
        lo=GEOM_BOOTH_TE01D.box_radius_m - TOL.machining_tol_m,
        hi=GEOM_BOOTH_TE01D.box_radius_m + TOL.machining_tol_m,
        nominal=GEOM_BOOTH_TE01D.box_radius_m,
        distribution=DistributionKind.TRUNC_GAUSSIAN_3SIGMA,
    )
    u = np.array([0.01, 0.25, 0.5, 0.75, 0.99])
    # Independent second path: ±3σ = band, σ = tol/3.
    sigma = TOL.machining_tol_m / 3.0
    expected = stats.truncnorm.ppf(
        u, -3.0, 3.0, loc=GEOM_BOOTH_TE01D.box_radius_m, scale=sigma
    )
    np.testing.assert_allclose(spec.ppf(u), expected, rtol=1e-12)
    # Median = nominal; endpoints stay inside the band.
    assert spec.ppf(np.array([0.5]))[0] == pytest.approx(spec.nominal)
    assert spec.lo <= spec.ppf(np.array([1e-9]))[0]
    assert spec.ppf(np.array([1.0 - 1e-9]))[0] <= spec.hi


def test_uniform_dim_is_affine():
    spec = SamplingDim(
        name="epsilon_r",
        lo=TOL.epsilon_r_min,
        hi=TOL.epsilon_r_max,
        nominal=STO.epsilon_r_real,
        distribution=DistributionKind.UNIFORM,
    )
    u = np.array([0.0, 0.5, 1.0])
    np.testing.assert_allclose(spec.ppf(u), [312.0, 315.0, 318.0])


def test_triangular_dim_peaks_at_nominal():
    spec = SamplingDim(
        name="epsilon_r",
        lo=312.0,
        hi=318.0,
        nominal=316.3,
        distribution=DistributionKind.TRIANGULAR_NOMINAL_PEAK,
    )
    c = (316.3 - 312.0) / 6.0
    u = np.array([0.1, 0.5, 0.9])
    expected = stats.triang.ppf(u, c, loc=312.0, scale=6.0)
    np.testing.assert_allclose(spec.ppf(u), expected, rtol=1e-12)


def test_cdf_ppf_round_trip_every_kind():
    for kind, nominal in [
        (DistributionKind.TRUNC_GAUSSIAN_3SIGMA, 0.5),
        (DistributionKind.UNIFORM, 0.3),
        (DistributionKind.TRIANGULAR_NOMINAL_PEAK, 0.7),
    ]:
        spec = SamplingDim(
            name="x", lo=0.0, hi=1.0, nominal=nominal, distribution=kind
        )
        u = np.linspace(0.01, 0.99, 17)
        np.testing.assert_allclose(
            spec.cdf(spec.ppf(u)), u, rtol=1e-10, atol=1e-12
        )


def test_sampling_dim_validation():
    with pytest.raises(ValueError, match="lo must be < hi"):
        SamplingDim(
            name="x", lo=1.0, hi=0.0, nominal=0.5,
            distribution=DistributionKind.UNIFORM,
        )
    with pytest.raises(ValueError, match="nominal outside"):
        SamplingDim(
            name="x", lo=0.0, hi=1.0, nominal=2.0,
            distribution=DistributionKind.UNIFORM,
        )


# ---------------------------------------------------------------------------
# generate_design — sizes, determinism, bounds
# ---------------------------------------------------------------------------


def test_committed_block_sizes_are_the_defaults():
    ctx = mock_resolutions()
    d8_train = generate_design(
        DesignMode.BASELINE_D8, DesignBlock.TRAINING, ctx, seed=SEED
    )
    assert d8_train.n_draws == 120 and d8_train.draws.shape == (120, 8)
    d7_train = generate_design(
        DesignMode.DEGRADED_D7, DesignBlock.TRAINING, ctx, seed=SEED
    )
    assert d7_train.n_draws == 97 and d7_train.draws.shape == (97, 7)
    held = generate_design(
        DesignMode.BASELINE_D8, DesignBlock.HELD_OUT, ctx, seed=SEED + 1
    )
    assert held.n_draws == 30


def test_generate_refuses_non_sobol_blocks():
    ctx = mock_resolutions()
    for block in (
        DesignBlock.PHASE1B_VERIFICATION,
        DesignBlock.ACTIVE_LEARNING_RESERVE,
        DesignBlock.MESH_SPOT_CHECKS,
        DesignBlock.CONFINEMENT_TRAJECTORY,
    ):
        with pytest.raises(ValueError, match="not a Sobol design"):
            generate_design(
                DesignMode.BASELINE_D8, block, ctx, seed=SEED
            )


def test_same_seed_reproduces_and_different_seed_differs():
    ctx = mock_resolutions()
    a = generate_design(
        DesignMode.DEGRADED_D7, DesignBlock.TRAINING, ctx, seed=SEED,
        n_draws=16,
    )
    b = generate_design(
        DesignMode.DEGRADED_D7, DesignBlock.TRAINING, ctx, seed=SEED,
        n_draws=16,
    )
    c = generate_design(
        DesignMode.DEGRADED_D7, DesignBlock.TRAINING, ctx, seed=SEED + 1,
        n_draws=16,
    )
    np.testing.assert_array_equal(a.draws, b.draws)
    assert not np.array_equal(a.draws, c.draws)


def test_draws_match_independent_sobol_plus_ppf_second_path():
    """Regression pin by independent re-computation: the design equals
    scrambled Sobol (same seed) pushed through each dim's own inverse
    CDF — the transform can't silently drift."""
    ctx = mock_resolutions()
    design = generate_design(
        DesignMode.BASELINE_D8, DesignBlock.TRAINING, ctx, seed=SEED,
        n_draws=32,
    )
    sampler = qmc.Sobol(d=8, scramble=True, seed=SEED)
    unit = sampler.random(32)
    for j, dim in enumerate(design.dims):
        np.testing.assert_allclose(
            design.draws[:, j], dim.ppf(unit[:, j]), rtol=1e-12
        )


def test_all_draws_respect_bounds_both_variants():
    ctx = mock_resolutions()
    for variant in GeometryDistributionVariant:
        design = generate_design(
            DesignMode.BASELINE_D8,
            DesignBlock.TRAINING,
            ctx,
            seed=SEED,
            n_draws=64,
            geometry_distribution=variant,
        )
        for j, dim in enumerate(design.dims):
            col = design.draws[:, j]
            assert np.all(col >= dim.lo) and np.all(col <= dim.hi), dim.name


def test_real_design_refuses_non_committed_sizes():
    # A REAL (non-mock) design must not silently drift from the §6
    # table; only shape-only mock designs may shrink. Building a real
    # context here uses hypothetical numbers — that is fine: it never
    # becomes solve-ready output in this test.
    real_ctx = ResolutionContext(
        resolutions=(
            SentinelResolution(
                question_id="Q9",
                payload={
                    "bore_radius_nominal_m": 1.9e-3,
                    "bore_radius_band_m": (1.875e-3, 1.925e-3),
                    "centring_tolerance_m": 50e-6,
                },
                rung=Rung.PLANNING_ASSUMPTION,
                provenance="hypothetical (test only)",
            ),
        )
    )
    with pytest.raises(ValueError, match="committed §6 block size"):
        generate_design(
            DesignMode.DEGRADED_D7,
            DesignBlock.TRAINING,
            real_ctx,
            seed=SEED,
            n_draws=10,
        )


# ---------------------------------------------------------------------------
# Solve-ready refusal pairs (the L1 requirement, enforced in code)
# ---------------------------------------------------------------------------


def test_mock_design_never_emits_solve_rows():
    ctx = mock_resolutions()
    design = generate_design(
        DesignMode.BASELINE_D8, DesignBlock.TRAINING, ctx, seed=SEED,
        n_draws=8,
    )
    assert design.any_mock
    with pytest.raises(MockResolutionError):
        design.solve_rows(ctx)


def test_unresolved_context_blocks_solve_rows_even_for_real_design():
    # Real Q9 resolution -> d7 design materialises; but Q11 (rider R1)
    # is unresolved, so solve-ready emission still refuses, naming it.
    real_ctx = ResolutionContext(
        resolutions=(
            SentinelResolution(
                question_id="Q9",
                payload={
                    "bore_radius_nominal_m": 1.9e-3,
                    "bore_radius_band_m": (1.875e-3, 1.925e-3),
                    "centring_tolerance_m": 50e-6,
                },
                rung=Rung.PLANNING_ASSUMPTION,
                provenance="hypothetical (test only)",
            ),
        )
    )
    design = generate_design(
        DesignMode.DEGRADED_D7, DesignBlock.TRAINING, real_ctx, seed=SEED
    )
    assert not design.any_mock
    with pytest.raises(UnresolvedTodoTraceError) as exc:
        design.solve_rows(real_ctx)
    assert exc.value.question_ids == ("Q11",)


def test_mock_rows_exercise_shape_and_refuse_on_real_designs():
    ctx = mock_resolutions()
    design = generate_design(
        DesignMode.BASELINE_D8, DesignBlock.HELD_OUT, ctx, seed=SEED,
        n_draws=4,
    )
    rows = design.mock_rows()
    assert len(rows) == 4
    assert set(rows[0]["theta"]) == set(design.dim_names)
    assert rows[0]["row_hash"] != rows[1]["row_hash"]

    real_ctx = ResolutionContext(
        resolutions=(
            SentinelResolution(
                question_id="Q9",
                payload={
                    "bore_radius_nominal_m": 1.9e-3,
                    "bore_radius_band_m": (1.875e-3, 1.925e-3),
                    "centring_tolerance_m": 50e-6,
                },
                rung=Rung.PLANNING_ASSUMPTION,
                provenance="hypothetical (test only)",
            ),
        )
    )
    real_design = generate_design(
        DesignMode.DEGRADED_D7, DesignBlock.TRAINING, real_ctx, seed=SEED
    )
    with pytest.raises(MockResolutionError, match="real-resolved"):
        real_design.mock_rows()


def test_row_hash_is_deterministic_and_index_sensitive():
    ctx = mock_resolutions()
    a = generate_design(
        DesignMode.DEGRADED_D7, DesignBlock.TRAINING, ctx, seed=SEED,
        n_draws=8,
    )
    b = generate_design(
        DesignMode.DEGRADED_D7, DesignBlock.TRAINING, ctx, seed=SEED,
        n_draws=8,
    )
    assert a.row_hash(3) == b.row_hash(3)
    assert a.row_hash(3) != a.row_hash(4)
    assert len(a.row_hash(0)) == 16


def test_manifest_carries_identity_and_dim_provenance():
    ctx = mock_resolutions()
    design = generate_design(
        DesignMode.BASELINE_D8, DesignBlock.TRAINING, ctx, seed=SEED,
        n_draws=4,
    )
    m = design.manifest()
    assert m["mode"] == "baseline-d8"
    assert m["block"] == "training"
    assert m["seed"] == SEED
    assert m["any_mock"] is True
    bore = next(d for d in m["dims"] if d["name"] == "bore_radius_m")
    assert bore["mock"] is True and "Q9" in bore["source"]
