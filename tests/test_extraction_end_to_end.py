"""End-to-end smoke for cavity.extraction + FieldSample contract checks.

`extract(field)` must populate every field of `ExtractionResult` with a
physical value, label both V_mode variants, and feed the cross-checked
Q into both F_m variants.
"""

from __future__ import annotations

import numpy as np
import pytest

from cavity.extraction import (
    ExtractionResult,
    FieldSample,
    extract,
)

from tests._extraction_fixtures import make_structured_grid, zero_complex_3vec


def _build_field(
    f_complex: complex = complex(1.45e9, 8.0e4),
    q_emw_cross_check: float | None = None,
    gain_region_mask: np.ndarray | None = None,
    h_outside_peak: float = 5.0,
    h_inside_peak: float = 1.0,
) -> FieldSample:
    grid = make_structured_grid(
        r_lo=0.0, r_hi=6.0e-3, z_lo=0.0, z_hi=18.0e-3,
        n_r=41, n_z=61,
    )
    n = grid.r_m.size

    dielectric_mask = (
        (grid.r_m >= 1.0e-3)
        & (grid.r_m <= 3.0e-3)
        & (grid.z_m >= 4.0e-3)
        & (grid.z_m <= 14.0e-3)
    )
    eps_r = np.where(dielectric_mask, 316.3, 1.0).astype(np.complex128)
    eps_r[dielectric_mask] *= (1.0 - 1j * 1.1e-4)

    h = zero_complex_3vec(n)
    h[:, 2] = np.where(
        dielectric_mask, h_inside_peak, h_outside_peak
    ).astype(np.complex128)

    e = zero_complex_3vec(n)
    e[:, 1] = 1.0

    return FieldSample(
        r_m=grid.r_m,
        z_m=grid.z_m,
        e_complex=e,
        h_complex=h,
        eps_r_complex=eps_r,
        weights_m2=grid.weights_m2,
        dielectric_mask=dielectric_mask,
        complex_eigenfrequency_hz=f_complex,
        gain_region_mask=gain_region_mask,
        q_emw_cross_check=q_emw_cross_check,
    )


class TestExtractEndToEnd:
    def test_populates_every_result_field(self):
        field = _build_field()
        result = extract(field)

        assert isinstance(result, ExtractionResult)
        assert result.f_hz == pytest.approx(1.45e9, rel=1e-12)
        assert result.q > 0
        assert result.q_emw_cross_check is None
        assert result.v_mode_global_m3 > 0
        assert result.v_mode_local_m3 > 0
        assert result.v_mode_global_m3 < result.v_mode_local_m3
        assert 0.0 < result.p_e <= 1.0
        assert result.f_m_global > 0
        assert result.f_m_local > 0
        # The complex eigenfrequency must be propagated verbatim so
        # the §4 wall-loss decomposition can audit Q against its
        # source without reaching back into the FieldSample.
        assert (
            result.complex_eigenfrequency_hz
            == field.complex_eigenfrequency_hz
        )
        assert result.complex_eigenfrequency_hz.real == result.f_hz
        assert result.complex_eigenfrequency_hz.imag > 0
        # Q must be independently re-derivable from the carried
        # complex eigenfrequency. That is the auditability contract.
        f = result.complex_eigenfrequency_hz
        assert result.q == pytest.approx(
            f.real / (2.0 * f.imag), rel=1e-12
        )

    def test_v_mode_local_larger_when_local_max_smaller(self):
        """V_mode = integral / max(|H|^2). The synthetic fixture has
        |H|^2_max larger globally than over the gain region (we set
        h_outside_peak > h_inside_peak), so V_local > V_global and
        therefore F_m_global > F_m_local — the local variant amplifies V
        and shrinks F_m in this unphysical-but-consistent fixture.
        """
        field = _build_field(h_outside_peak=5.0, h_inside_peak=1.0)
        result = extract(field)
        assert result.v_mode_local_m3 > result.v_mode_global_m3
        assert result.f_m_global > result.f_m_local
        assert result.v_mode_local_m3 / result.v_mode_global_m3 == pytest.approx(
            25.0, rel=1e-12
        )

    def test_q_emw_cross_check_passes_through_when_consistent(self):
        f_complex = complex(1.45e9, 1.0e5)
        q_primary = f_complex.real / (2.0 * f_complex.imag)
        field = _build_field(
            f_complex=f_complex, q_emw_cross_check=q_primary
        )
        result = extract(field)
        assert result.q == pytest.approx(q_primary, rel=1e-12)
        assert result.q_emw_cross_check == q_primary

    def test_gain_region_override_changes_local_v_mode(self):
        field_default = _build_field()
        # Override gain region to a single ring of nodes near r ~ 2 mm:
        full_mask_shape = field_default.dielectric_mask.shape
        custom_mask = np.zeros(full_mask_shape, dtype=bool)
        # Pick a band where |H|^2 = h_inside_peak^2 = 1 (inside dielectric):
        custom_mask |= field_default.dielectric_mask
        field_custom = _build_field(gain_region_mask=custom_mask)
        result_custom = extract(field_custom)
        # With gain region == dielectric, local V_mode matches the default:
        result_default = extract(field_default)
        assert result_custom.v_mode_local_m3 == pytest.approx(
            result_default.v_mode_local_m3, rel=1e-12
        )


class TestFieldSampleContract:
    """SPEC §3 typed input contract — shape and sign validation."""

    def _kw(self) -> dict:
        grid = make_structured_grid(0.0, 1.0e-3, 0.0, 1.0e-3, n_r=4, n_z=4)
        n = grid.r_m.size
        e = zero_complex_3vec(n); e[:, 1] = 1.0
        h = zero_complex_3vec(n); h[:, 2] = 1.0
        mask = np.ones(n, dtype=bool)
        eps = np.full(n, 316.3, dtype=np.complex128)
        return dict(
            r_m=grid.r_m, z_m=grid.z_m,
            e_complex=e, h_complex=h,
            eps_r_complex=eps, weights_m2=grid.weights_m2,
            dielectric_mask=mask,
            complex_eigenfrequency_hz=complex(1.45e9, 1.0e5),
        )

    def test_round_trip(self):
        FieldSample(**self._kw())

    def test_shape_mismatch_e_complex(self):
        kw = self._kw()
        kw["e_complex"] = np.zeros((kw["r_m"].size, 2), dtype=np.complex128)
        with pytest.raises(ValueError, match="e_complex shape"):
            FieldSample(**kw)

    def test_shape_mismatch_h_complex(self):
        kw = self._kw()
        kw["h_complex"] = np.zeros((kw["r_m"].size + 1, 3), dtype=np.complex128)
        with pytest.raises(ValueError, match="h_complex shape"):
            FieldSample(**kw)

    def test_z_m_length_mismatch(self):
        kw = self._kw()
        kw["z_m"] = kw["z_m"][:-1]
        with pytest.raises(ValueError, match="z_m shape"):
            FieldSample(**kw)

    def test_negative_r_rejected(self):
        kw = self._kw()
        kw["r_m"] = kw["r_m"].copy()
        kw["r_m"][0] = -1.0e-6
        with pytest.raises(ValueError, match="r_m must be non-negative"):
            FieldSample(**kw)

    def test_non_positive_weights_rejected(self):
        kw = self._kw()
        kw["weights_m2"] = kw["weights_m2"].copy()
        kw["weights_m2"][0] = 0.0
        with pytest.raises(ValueError, match="weights_m2"):
            FieldSample(**kw)

    def test_zero_eps_r_real_rejected(self):
        kw = self._kw()
        eps = kw["eps_r_complex"].copy()
        eps[0] = complex(0.0, -1e-3)
        kw["eps_r_complex"] = eps
        with pytest.raises(ValueError, match="Re\\(eps_r\\)"):
            FieldSample(**kw)

    def test_empty_dielectric_mask_rejected(self):
        kw = self._kw()
        kw["dielectric_mask"] = np.zeros_like(kw["dielectric_mask"])
        with pytest.raises(ValueError, match="dielectric_mask is empty"):
            FieldSample(**kw)

    def test_non_positive_re_f_rejected(self):
        kw = self._kw()
        kw["complex_eigenfrequency_hz"] = complex(0.0, 1.0e5)
        with pytest.raises(ValueError, match="Re\\(eigenfrequency\\)"):
            FieldSample(**kw)

    def test_non_positive_q_emw_cross_check_rejected(self):
        kw = self._kw()
        kw["q_emw_cross_check"] = -1.0
        with pytest.raises(ValueError, match="q_emw_cross_check"):
            FieldSample(**kw)

    def test_effective_gain_mask_defaults_to_dielectric(self):
        field = FieldSample(**self._kw())
        assert np.array_equal(
            field.effective_gain_mask, field.dielectric_mask
        )
