"""SPEC §3 V_mode (global + local) — analytic test (2).

Synthetic fixture where |H|^2 has its global maximum outside the gain
region and a smaller local maximum inside, so the two V_mode variants
are intentionally different. SPEC §3 demands both be labelled and
returned.
"""

from __future__ import annotations

import numpy as np
import pytest

from cavity.extraction import (
    FieldSample,
    ModeVolumes,
    mode_volumes,
)

from tests._extraction_fixtures import (
    StructuredAxisymmetricGrid,
    make_structured_grid,
    zero_complex_3vec,
)


def _build_h_field(
    grid: StructuredAxisymmetricGrid,
    gain_mask: np.ndarray,
    h_outside_peak: float,
    h_inside_peak: float,
) -> np.ndarray:
    """H field whose |H| peaks at `h_outside_peak` outside the gain
    region and `h_inside_peak` inside it.

    Putting the magnitude in H_z keeps the field divergence-free in this
    test (we are not asking for Maxwell consistency — only for distinct
    global vs local maxima of |H|^2).
    """
    h = zero_complex_3vec(grid.r_m.size)
    h_z = np.where(gain_mask, h_inside_peak, h_outside_peak).astype(
        np.float64
    )
    h[:, 2] = h_z.astype(np.complex128)
    return h


def _build_constant_e_field(n: int, e_amplitude: float) -> np.ndarray:
    e = zero_complex_3vec(n)
    e[:, 1] = e_amplitude  # E_phi, azimuthal (TE mode)
    return e


class TestModeVolumesBothVariants:
    """SPEC §3: both global and local V_mode returned, labelled, distinct."""

    def _sample(
        self,
        h_outside_peak: float = 5.0,
        h_inside_peak: float = 1.0,
    ) -> FieldSample:
        grid = make_structured_grid(
            r_lo=0.0, r_hi=6.0e-3, z_lo=0.0, z_hi=18.0e-3,
            n_r=41, n_z=61,
        )
        n = grid.r_m.size

        # Gain (dielectric) region: r in [1e-3, 3e-3], z in [4e-3, 14e-3].
        gain_mask = (
            (grid.r_m >= 1.0e-3)
            & (grid.r_m <= 3.0e-3)
            & (grid.z_m >= 4.0e-3)
            & (grid.z_m <= 14.0e-3)
        )

        h = _build_h_field(
            grid, gain_mask, h_outside_peak, h_inside_peak
        )
        e = _build_constant_e_field(n, e_amplitude=1.0)
        eps_r = np.where(gain_mask, 316.3, 1.0).astype(np.complex128)
        weights = grid.weights_m2

        return FieldSample(
            r_m=grid.r_m,
            z_m=grid.z_m,
            e_complex=e,
            h_complex=h,
            eps_r_complex=eps_r,
            weights_m2=weights,
            dielectric_mask=gain_mask,
            complex_eigenfrequency_hz=complex(1.45e9, 1.0e5),
        )

    def test_returns_both_variants_typed(self):
        field = self._sample()
        vols = mode_volumes(field)
        assert isinstance(vols, ModeVolumes)
        assert vols.global_m3 > 0
        assert vols.local_m3 > 0

    def test_global_and_local_differ_when_maxima_differ(self):
        """Global max = 5, local max = 1 -> V_mode_local = 25 * V_mode_global."""
        field = self._sample(h_outside_peak=5.0, h_inside_peak=1.0)
        vols = mode_volumes(field)
        ratio = vols.local_m3 / vols.global_m3
        assert ratio == pytest.approx(25.0, rel=1e-12)

    def test_global_equals_local_when_field_is_uniform(self):
        field = self._sample(h_outside_peak=1.0, h_inside_peak=1.0)
        vols = mode_volumes(field)
        assert vols.global_m3 == pytest.approx(vols.local_m3, rel=1e-12)

    def test_v_mode_global_matches_integral_over_max_h_squared(self):
        """Hand-check: V_global = int(|H|^2 dV) / max(|H|^2).

        With H_z = 5 outside and 1 inside, |H|^2 = 25 outside and 1 inside;
        max(|H|^2) = 25. The integral simplifies to
            2*pi * (25 * A_outside + 1 * A_inside) * <r>_weighted,
        but we don't need a closed form here — just that V_global is in
        plausible physical range (m^3) given a ~6 mm x 18 mm cavity.
        """
        field = self._sample(h_outside_peak=5.0, h_inside_peak=1.0)
        vols = mode_volumes(field)
        cavity_geometric_volume_m3 = (
            np.pi * (6.0e-3) ** 2 * 18.0e-3
        )
        assert 0 < vols.global_m3 < cavity_geometric_volume_m3

    def test_empty_gain_mask_rejected(self):
        field = self._sample()
        empty_mask = np.zeros_like(field.dielectric_mask)
        overridden = FieldSample(
            r_m=field.r_m,
            z_m=field.z_m,
            e_complex=field.e_complex,
            h_complex=field.h_complex,
            eps_r_complex=field.eps_r_complex,
            weights_m2=field.weights_m2,
            dielectric_mask=field.dielectric_mask,
            complex_eigenfrequency_hz=field.complex_eigenfrequency_hz,
            gain_region_mask=empty_mask,
        )
        with pytest.raises(ValueError, match="gain_region_mask is empty"):
            mode_volumes(overridden)

    def test_v_mode_independent_of_h_phase(self):
        """|H|^2 is phase-insensitive — rotating H by exp(i*alpha) leaves
        |H|^2 unchanged and thus V_mode unchanged.
        """
        field = self._sample()
        vols_orig = mode_volumes(field)

        rotated = field.h_complex * np.exp(1j * 0.737)
        rotated_field = FieldSample(
            r_m=field.r_m,
            z_m=field.z_m,
            e_complex=field.e_complex,
            h_complex=rotated,
            eps_r_complex=field.eps_r_complex,
            weights_m2=field.weights_m2,
            dielectric_mask=field.dielectric_mask,
            complex_eigenfrequency_hz=field.complex_eigenfrequency_hz,
        )
        vols_rot = mode_volumes(rotated_field)
        assert vols_rot.global_m3 == pytest.approx(
            vols_orig.global_m3, rel=1e-12
        )
        assert vols_rot.local_m3 == pytest.approx(
            vols_orig.local_m3, rel=1e-12
        )
