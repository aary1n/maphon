"""SPEC §7.T5(b) weight functionals (`cavity.extraction.weights`).

Covers the §B physics contracts and the §F anchors of the export pass:
normalisation to unit volume integral (machine precision, both arms),
the p_e closed loop (weights path == `electric_filling_factor` ==
0.9976566720273174 from the frozen gate record), projection identities
(isotropic-average ≡ |H|^2; u_z = 1 ≡ |H_z|^2-only), uniform limits
(uniform field => w_s = 1/V_gain; uniform DeltaT => zero width through
`line_observable_from_samples`), the TE011 closed-form anchors, and the
mode-volume reconciliation 1/max(w_s) = V_mode_local x magnetic filling
factor.

Tolerance basis, stated per anchor:
  - normalisation/identity checks: same-arithmetic float rounding
    (1e-12 rel);
  - TE011 closed-form anchors through FULL-DOMAIN MASKS: the mask
    boundary staircases the sub-region edge (nodes straddling the edge
    keep their full trapezoid weight), an O(h) error class — measured
    ~1.4-1.7e-2 at 201x301, asserted at 4e-2. The O(h^2)
    conforming-grid versions of the same closed forms live in
    tests/test_analytic_fields.py; the schema doc carries the caveat
    for consumers.
"""

from __future__ import annotations

import numpy as np
import pytest

from cavity.extraction import (
    FieldSample,
    SpinProjection,
    axisymmetric_volume_integral,
    cavity_arm_weight,
    electric_filling_factor,
    mode_volumes,
    projected_h2_density,
    spin_arm_weight,
)
from cavity.forward_model.gridding import structured_grid
from cavity.thermal.broadening import line_observable_from_samples
from cavity.validation.analytic_fields import (
    TE011Mode,
    te011_electric_energy_fraction_inside_radius,
    te011_fields,
    te011_h2_subregion_integral,
    te011_h2_total_integral,
)

from tests._extraction_fixtures import make_structured_grid, zero_complex_3vec
from tests._gate_record_fixture import GATE_P_E, gate_record_or_skip

MODE = TE011Mode(radius_m=6.14e-3, length_m=18.42e-3)
N_R, N_Z = 201, 301
MASK_STAIRCASE_REL_TOL = 4.0e-2  # O(h) mask-edge class, see module docstring


def _te011_field_sample(
    dielectric_b_m: float = MODE.radius_m / 2.0,
    gain_b_m: float = 0.3 * MODE.radius_m,
    gain_z: tuple[float, float] = (0.3 * MODE.length_m, 0.7 * MODE.length_m),
    with_gain_mask: bool = True,
) -> FieldSample:
    """TE011 closed-form fields in the §3 contract, eps_r = 1 everywhere.

    The 'dielectric' mask is a synthetic coaxial sub-cylinder (full z)
    so the cavity arm's p_e anchors against the closed-form electric
    energy fraction; the gain mask is a crystal-like sub-region. A
    small synthetic Im(f) keeps the eigenfrequency contract-valid.
    """
    grid = structured_grid(MODE.radius_m, MODE.length_m, N_R, N_Z)
    e, h = te011_fields(MODE, grid.r_m, grid.z_m)
    tiny = 1.0e-12 * MODE.radius_m
    dielectric_mask = grid.r_m <= dielectric_b_m + tiny
    gain_mask = (
        (grid.r_m <= gain_b_m + tiny)
        & (grid.z_m >= gain_z[0] - tiny)
        & (grid.z_m <= gain_z[1] + tiny)
    )
    return FieldSample(
        r_m=grid.r_m,
        z_m=grid.z_m,
        e_complex=e,
        h_complex=h,
        eps_r_complex=np.ones(grid.r_m.size, dtype=np.complex128),
        weights_m2=grid.weights_m2,
        dielectric_mask=dielectric_mask,
        complex_eigenfrequency_hz=complex(MODE.f_hz, MODE.f_hz / 2.0e4),
        gain_region_mask=gain_mask if with_gain_mask else None,
    )


def _uniform_field_sample(n_r: int = 81, n_z: int = 121) -> FieldSample:
    """Uniform |E| and H = H_z z_hat everywhere; rectangular masks."""
    grid = make_structured_grid(0.0, 6.0e-3, 0.0, 18.0e-3, n_r=n_r, n_z=n_z)
    n = grid.r_m.size
    dielectric_mask = (
        (grid.r_m >= 1.0e-3)
        & (grid.r_m <= 3.0e-3)
        & (grid.z_m >= 4.0e-3)
        & (grid.z_m <= 14.0e-3)
    )
    e = zero_complex_3vec(n)
    e[:, 1] = 2.0
    h = zero_complex_3vec(n)
    h[:, 2] = 0.7j
    return FieldSample(
        r_m=grid.r_m,
        z_m=grid.z_m,
        e_complex=e,
        h_complex=h,
        eps_r_complex=np.where(dielectric_mask, 316.3, 1.0).astype(
            np.complex128
        ),
        weights_m2=grid.weights_m2,
        dielectric_mask=dielectric_mask,
        complex_eigenfrequency_hz=complex(1.45e9, 1.0e5),
    )


def _mask_volume_m3(field: FieldSample, mask: np.ndarray) -> float:
    return float(
        np.real(
            axisymmetric_volume_integral(
                np.where(mask, 1.0, 0.0), field.r_m, field.weights_m2
            )
        )
    )


class TestCavityArmWeight:
    def test_unit_volume_integral(self):
        """int_STO w_E dV = 1 to machine precision (§B sanity check)."""
        for field in (_uniform_field_sample(), _te011_field_sample()):
            arm = cavity_arm_weight(field)
            assert arm.weight.volume_integral() == pytest.approx(
                1.0, rel=1.0e-12
            )

    def test_p_e_closed_loop_against_existing_extraction(self):
        """Weights-path p_e == electric_filling_factor — same arrays,
        same quadrature primitive, same arithmetic order."""
        for field in (_uniform_field_sample(), _te011_field_sample()):
            arm = cavity_arm_weight(field)
            assert arm.p_e == pytest.approx(
                electric_filling_factor(field), rel=1.0e-14
            )

    def test_uniform_limit_density_is_one_over_volume(self):
        """Uniform eps'|E|^2 over the mask => w_E = 1/V_diel exactly
        (quadrature volume — identical arithmetic)."""
        field = _uniform_field_sample()
        arm = cavity_arm_weight(field)
        v_diel = _mask_volume_m3(field, field.dielectric_mask)
        inside = arm.weight.values_per_m3[field.dielectric_mask]
        assert np.allclose(inside, 1.0 / v_diel, rtol=1.0e-12)

    def test_zero_outside_mask(self):
        field = _te011_field_sample()
        arm = cavity_arm_weight(field)
        assert np.all(
            arm.weight.values_per_m3[~field.dielectric_mask] == 0.0
        )

    def test_probe_measure_sums_to_one(self):
        field = _te011_field_sample()
        pi = cavity_arm_weight(field).weight.probe_measure()
        assert float(pi.sum()) == pytest.approx(1.0, rel=1.0e-12)
        assert np.all(pi >= 0.0)

    def test_te011_anchor_p_e_matches_closed_form(self):
        """Cavity-arm anchor (§F): the closed-form electric-energy
        fraction IS a p_e for the synthetic eps = 1 sub-cylinder.
        Mask-staircase O(h) tolerance — see module docstring."""
        b = MODE.radius_m / 2.0
        field = _te011_field_sample(dielectric_b_m=b)
        arm = cavity_arm_weight(field)
        closed = te011_electric_energy_fraction_inside_radius(MODE, b)
        assert arm.p_e == pytest.approx(closed, rel=MASK_STAIRCASE_REL_TOL)

    def test_uniform_delta_t_reproduces_p_e_arithmetic(self):
        """Uniform DeltaT through the probe measure => the §6T
        'delta_f = df/dT * p_e * DeltaT' collapse: <DeltaT>_wE = DeltaT
        exactly, with p_e carried as the separate companion."""
        field = _te011_field_sample()
        arm = cavity_arm_weight(field)
        delta_t = np.full(field.r_m.size, 3.7)
        mean = float(
            np.dot(arm.weight.probe_measure(), delta_t)
        )  # sum pi_i DT_i, pi sums to 1
        assert mean == pytest.approx(3.7, rel=1.0e-12)

    def test_zero_field_on_mask_raises(self):
        field = _uniform_field_sample()
        e = zero_complex_3vec(field.r_m.size)  # identically zero E
        dead = FieldSample(
            r_m=field.r_m,
            z_m=field.z_m,
            e_complex=e,
            h_complex=field.h_complex,
            eps_r_complex=field.eps_r_complex,
            weights_m2=field.weights_m2,
            dielectric_mask=field.dielectric_mask,
            complex_eigenfrequency_hz=field.complex_eigenfrequency_hz,
        )
        with pytest.raises(ValueError, match="non-positive"):
            cavity_arm_weight(dead)


class TestSpinProjection:
    def test_isotropic_equals_uniform_orientation_average(self):
        """<|H.u|^2>_iso = |H|^2/3 pointwise, so ANY mixture whose
        second moment sum f u^2 = 1/3 reproduces the isotropic weight
        after normalisation (the 1/3 cancels). Magic-angle single
        orientation and a {axis, transverse} mixture both hit it."""
        rng = np.random.default_rng(20260709)
        h = (
            rng.standard_normal((500, 3)) + 1j * rng.standard_normal((500, 3))
        ).astype(np.complex128)
        iso = projected_h2_density(h, SpinProjection.isotropic_h2())
        magic = projected_h2_density(
            h, SpinProjection.axis_projected(1.0 / np.sqrt(3.0))
        )
        mixture = projected_h2_density(
            h,
            SpinProjection.site_mixture(
                [(1.0, 1.0 / 3.0), (0.0, 2.0 / 3.0)]
            ),
        )
        assert np.allclose(magic, iso / 3.0, rtol=1.0e-12)
        assert np.allclose(mixture, iso / 3.0, rtol=1.0e-12)

    def test_u_z_one_is_pure_hz_weight(self):
        rng = np.random.default_rng(7)
        h = (
            rng.standard_normal((200, 3)) + 1j * rng.standard_normal((200, 3))
        ).astype(np.complex128)
        axial = projected_h2_density(h, SpinProjection.axis_projected(1.0))
        assert np.allclose(axial, np.abs(h[:, 2]) ** 2, rtol=1.0e-12)

    def test_u_z_zero_is_transverse_half(self):
        rng = np.random.default_rng(8)
        h = (
            rng.standard_normal((200, 3)) + 1j * rng.standard_normal((200, 3))
        ).astype(np.complex128)
        transverse = projected_h2_density(
            h, SpinProjection.axis_projected(0.0)
        )
        expected = 0.5 * (np.abs(h[:, 0]) ** 2 + np.abs(h[:, 1]) ** 2)
        assert np.allclose(transverse, expected, rtol=1.0e-12)

    def test_labels_and_meta(self):
        assert SpinProjection.isotropic_h2().label() == "isotropic_h2"
        assert SpinProjection.isotropic_h2().to_meta() == {
            "mode": "isotropic_h2",
            "components": None,
        }
        proj = SpinProjection.axis_projected(1.0)
        assert proj.to_meta()["mode"] == "axis_projected"
        mix = SpinProjection.site_mixture([(1.0, 0.5), (0.0, 0.5)])
        assert mix.to_meta()["mode"] == "site_mixture"

    def test_invalid_parameters_raise(self):
        with pytest.raises(ValueError, match="u_z"):
            SpinProjection.axis_projected(1.5)
        with pytest.raises(ValueError, match="sum to 1"):
            SpinProjection.site_mixture([(1.0, 0.5), (0.0, 0.6)])
        with pytest.raises(ValueError, match="positive"):
            SpinProjection.site_mixture([(1.0, 1.5), (0.0, -0.5)])
        with pytest.raises(ValueError, match="at least one"):
            SpinProjection(components=())


class TestSpinArmWeight:
    def test_unit_volume_integral_all_projections(self):
        field = _te011_field_sample()
        for proj in (
            SpinProjection.isotropic_h2(),
            SpinProjection.axis_projected(1.0),
            SpinProjection.axis_projected(0.3),
            SpinProjection.site_mixture([(0.9, 0.5), (0.1, 0.5)]),
        ):
            arm = spin_arm_weight(field, proj)
            assert arm.weight.volume_integral() == pytest.approx(
                1.0, rel=1.0e-12
            )

    def test_uniform_field_limit(self):
        """Uniform |H| over the gain region => w_s = 1/V_gain exactly."""
        field = _uniform_field_sample()  # H = const z_hat, gain = STO fallback
        arm = spin_arm_weight(field)
        v_gain = _mask_volume_m3(field, field.effective_gain_mask)
        inside = arm.weight.values_per_m3[field.effective_gain_mask]
        assert np.allclose(inside, 1.0 / v_gain, rtol=1.0e-12)

    def test_gain_mask_fallback_flag(self):
        assert spin_arm_weight(
            _te011_field_sample(with_gain_mask=False)
        ).gain_mask_is_fallback
        assert not spin_arm_weight(
            _te011_field_sample(with_gain_mask=True)
        ).gain_mask_is_fallback

    def test_h_phi_share_zero_for_te011(self):
        """TE011 has H_phi = 0 identically — the mode-purity diagnostic
        must read exactly zero on the closed-form fields."""
        arm = spin_arm_weight(_te011_field_sample())
        assert arm.h_phi_energy_share == 0.0

    def test_h_phi_share_counts_azimuthal_energy(self):
        field = _uniform_field_sample()
        h = zero_complex_3vec(field.r_m.size)
        h[:, 1] = 1.0  # all energy azimuthal
        impure = FieldSample(
            r_m=field.r_m,
            z_m=field.z_m,
            e_complex=field.e_complex,
            h_complex=h,
            eps_r_complex=field.eps_r_complex,
            weights_m2=field.weights_m2,
            dielectric_mask=field.dielectric_mask,
            complex_eigenfrequency_hz=field.complex_eigenfrequency_hz,
        )
        arm = spin_arm_weight(impure)
        assert arm.h_phi_energy_share == pytest.approx(1.0, rel=1.0e-12)

    def test_mode_volume_reconciliation(self):
        """§3 cross-link: 1/max(w_s) = V_mode_local x magnetic filling
        factor (isotropic projection) — same arrays, float rounding."""
        field = _te011_field_sample()
        arm = spin_arm_weight(field)
        v_local = mode_volumes(field).local_m3
        assert 1.0 / float(arm.weight.values_per_m3.max()) == pytest.approx(
            v_local * arm.magnetic_filling_factor, rel=1.0e-12
        )

    def test_te011_anchor_magnetic_filling_factor(self):
        """Spin-arm anchor (§F): gain-region |H|^2 fraction vs the
        closed-form Lommel x axial ratio. Mask-staircase O(h)
        tolerance — see module docstring."""
        b = 0.3 * MODE.radius_m
        z_lo, z_hi = 0.3 * MODE.length_m, 0.7 * MODE.length_m
        field = _te011_field_sample(gain_b_m=b, gain_z=(z_lo, z_hi))
        arm = spin_arm_weight(field)
        closed = te011_h2_subregion_integral(
            MODE, b, z_lo, z_hi
        ) / te011_h2_total_integral(MODE)
        assert arm.magnetic_filling_factor == pytest.approx(
            closed, rel=MASK_STAIRCASE_REL_TOL
        )

    def test_probe_measure_feeds_line_observable(self):
        """Consumer 4 wiring (§7.T2 output 3): the probe measure IS the
        `weights` argument; uniform DeltaT => pure shift, zero width
        (exact, matching broadening's enforced identity)."""
        field = _te011_field_sample()
        pi = spin_arm_weight(field).weight.probe_measure()
        uniform = line_observable_from_samples(
            np.full(pi.size, 2.0), pi, df_dt_hz_per_k=-1.09e5
        )
        assert uniform.rms_delta_t_k == 0.0
        assert uniform.mean_shift_hz == pytest.approx(
            -1.09e5 * 2.0, rel=1.0e-12
        )
        gradient = line_observable_from_samples(
            np.asarray(field.z_m / field.z_m.max(), dtype=float),
            pi,
            df_dt_hz_per_k=-1.09e5,
        )
        assert gradient.rms_delta_t_k > 0.0
        assert 0.0 < gradient.mean_delta_t_k < 1.0

    def test_zero_field_on_gain_mask_raises(self):
        field = _uniform_field_sample()
        h = zero_complex_3vec(field.r_m.size)
        dead = FieldSample(
            r_m=field.r_m,
            z_m=field.z_m,
            e_complex=field.e_complex,
            h_complex=h,
            eps_r_complex=field.eps_r_complex,
            weights_m2=field.weights_m2,
            dielectric_mask=field.dielectric_mask,
            complex_eigenfrequency_hz=field.complex_eigenfrequency_hz,
        )
        with pytest.raises(ValueError, match="non-positive"):
            spin_arm_weight(dead)


class TestGateRecordClosedLoop:
    """§F anchor 2 on the frozen licence-session artifact (LFS npz)."""

    def test_p_e_closed_loop_full_precision(self):
        """Weights path == electric_filling_factor == the gate report's
        0.9976566720273174 (tolerance only for JSON round-trip)."""
        record = gate_record_or_skip()
        field = record.field_sample
        arm = cavity_arm_weight(field)
        assert arm.p_e == pytest.approx(
            electric_filling_factor(field), rel=1.0e-14
        )
        assert arm.p_e == pytest.approx(GATE_P_E, rel=1.0e-12)

    def test_both_arms_normalised_on_gate_record(self):
        record = gate_record_or_skip()
        field = record.field_sample
        cavity = cavity_arm_weight(field)
        spin = spin_arm_weight(field)
        assert cavity.weight.volume_integral() == pytest.approx(
            1.0, rel=1.0e-12
        )
        assert spin.weight.volume_integral() == pytest.approx(
            1.0, rel=1.0e-12
        )
        assert float(cavity.weight.probe_measure().sum()) == pytest.approx(
            1.0, rel=1.0e-12
        )
        assert float(spin.weight.probe_measure().sum()) == pytest.approx(
            1.0, rel=1.0e-12
        )

    def test_gate_record_gain_mask_is_fallback(self):
        """Pre-Phase-1b geometry: the spin arm runs on the STO fallback
        and says so — the schema-example flag `cavity.export` stores."""
        record = gate_record_or_skip()
        arm = spin_arm_weight(record.field_sample)
        assert arm.gain_mask_is_fallback

    def test_mode_volume_reconciliation_on_gate_record(self):
        record = gate_record_or_skip()
        field = record.field_sample
        arm = spin_arm_weight(field)
        v_local = mode_volumes(field).local_m3
        assert 1.0 / float(arm.weight.values_per_m3.max()) == pytest.approx(
            v_local * arm.magnetic_filling_factor, rel=1.0e-12
        )

    def test_te01delta_mode_purity_on_gate_record(self):
        """The picked mode is TE-family (m = 0 exact split): the H_phi
        energy share over the gain region must be numerically tiny."""
        record = gate_record_or_skip()
        arm = spin_arm_weight(record.field_sample)
        assert 0.0 <= arm.h_phi_energy_share < 1.0e-6
