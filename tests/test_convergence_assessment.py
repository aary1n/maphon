"""SPEC §2 convergence-assessment tests — sigma only from an asymptotic
mesh sequence.

`validation.wall_loss` requires its Q uncertainties to come from the
mesh-convergence residual on f'' — never fabricated. These tests pin
both directions: a shrinking-delta ladder emits the finest-pair
residuals as sigma, and any non-asymptotic ladder raises
`ConvergenceError` and emits nothing.
"""

from __future__ import annotations

import math

import pytest

from cavity.forward_model.convergence import (
    MIN_CONVERGENCE_LEVELS,
    ConvergenceError,
    assess_convergence,
)

F_RE = 1.45e9
F_IM = 1.0e5  # Q ~ 7,250 — the Booth ballpark


def _ladder(deltas_re, deltas_im):
    """Coarse->fine eigenfrequency sequence whose level-to-level
    differences are exactly the given deltas (converging downward)."""
    freqs = [complex(F_RE, F_IM)]
    for dre, dim in zip(deltas_re, deltas_im):
        prev = freqs[-1]
        freqs.append(complex(prev.real - dre, prev.imag - dim))
    return freqs


class TestAsymptoticLadder:
    def test_sigma_is_finest_pair_residual(self):
        freqs = _ladder([4.0e5, 1.0e5, 2.5e4], [400.0, 100.0, 25.0])
        a = assess_convergence(freqs)
        assert a.sigma_f_real_hz == pytest.approx(2.5e4)
        assert a.sigma_f_imag_hz == pytest.approx(25.0)
        assert a.deltas_f_real_hz == pytest.approx((4.0e5, 1.0e5, 2.5e4))
        assert a.deltas_f_imag_hz == pytest.approx((400.0, 100.0, 25.0))

    def test_q_and_sigma_q_propagation(self):
        freqs = _ladder([4.0e5, 1.0e5, 2.5e4], [400.0, 100.0, 25.0])
        a = assess_convergence(freqs)
        finest = freqs[-1]
        q_expected = finest.real / (2.0 * finest.imag)
        assert a.q_finest == pytest.approx(q_expected, rel=1e-12)
        sigma_expected = q_expected * math.hypot(
            2.5e4 / finest.real, 25.0 / finest.imag
        )
        assert a.sigma_q == pytest.approx(sigma_expected, rel=1e-12)
        assert a.sigma_q > 0.0

    def test_exact_zero_delta_tail_accepted(self):
        # A level pair that agrees exactly counts as converged and may
        # repeat; the emitted sigma is then zero.
        freqs = _ladder([1.0e5, 0.0, 0.0], [100.0, 0.0, 0.0])
        a = assess_convergence(freqs)
        assert a.sigma_f_real_hz == 0.0
        assert a.sigma_q == 0.0

    def test_more_than_three_levels(self):
        freqs = _ladder(
            [8.0e5, 4.0e5, 1.6e5, 5.0e4], [800.0, 400.0, 160.0, 50.0]
        )
        a = assess_convergence(freqs)
        assert len(a.complex_eigenfrequencies_hz) == 5
        assert a.sigma_f_real_hz == pytest.approx(5.0e4)


class TestRefusals:
    def test_too_few_levels(self):
        freqs = _ladder([1.0e5], [100.0])
        assert len(freqs) < MIN_CONVERGENCE_LEVELS
        with pytest.raises(ConvergenceError, match=">= 3"):
            assess_convergence(freqs)

    def test_non_monotonic_f_real_refused(self):
        freqs = _ladder([1.0e5, 2.0e5, 5.0e4], [400.0, 100.0, 25.0])
        with pytest.raises(ConvergenceError, match="f' deltas"):
            assess_convergence(freqs)

    def test_non_monotonic_f_imag_refused(self):
        # f' converges cleanly; f'' (the Q-carrying part, the one §4
        # actually consumes) does not. Must still refuse.
        freqs = _ladder([4.0e5, 1.0e5, 2.5e4], [100.0, 400.0, 50.0])
        with pytest.raises(ConvergenceError, match="f'' deltas"):
            assess_convergence(freqs)

    def test_refusal_message_carries_the_ladder(self):
        freqs = _ladder([1.0e5, 2.0e5, 5.0e4], [400.0, 100.0, 25.0])
        with pytest.raises(ConvergenceError, match="coarse->fine"):
            assess_convergence(freqs)

    def test_non_positive_imag_at_finest_rejected(self):
        # Q = f'/(2 f'') is undefined for Im(f) <= 0; the §3 primitive
        # raises rather than emitting a sign-broken Q (SPEC §11 gap #4
        # regression: the retracted imag=0 probe must never pass here).
        freqs = [
            complex(F_RE, 3.0e-9),
            complex(F_RE, 1.0e-9),
            complex(F_RE, 0.0),
        ]
        with pytest.raises(ValueError, match="Im"):
            assess_convergence(freqs)
