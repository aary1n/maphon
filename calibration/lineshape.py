"""Per-spectrum lineshape fits + power-dependence model comparison —
blocker-independent tier of
docs/plans/cowley_semple_reply_ingestion_and_calibration_rebase.md §3.

PRE-REGISTRATION MODULE: the model set and the claim gates live in code
BEFORE any raw number is looked at (plan §7 acceptance criterion). The
gates encoded here, verbatim from the ratified rulings:

- D6 (user-ratified 2026-07-20), a STRICT AND gate: piecewise-linear and
  quadratic power models are CLAIMABLE only if BOTH
  (i)  the dataset supplies >= 8 independent power points per sample, AND
  (ii) delta-AICc >= 4 in favour of the nonlinear model over linear WLS.
  Per-point sigma quality does not substitute for the point count. When
  the gate is not met, linear stands and the alternatives are listed with
  their delta-AICc, unclaimed.
- Extrapolation (plan §3): a linear form that stands may be extrapolated
  to its zero-power intercept (grade "fit-extrapolated", never a measured
  linewidth); a NONLINEAR extrapolation basis must first pass D6. If the
  data cannot discriminate the form, the extrapolation is REFUSED in
  print ("insufficient support for extrapolation") and the lowest-power
  measured value is reported as the operational bound instead.

Lineshape models: Lorentzian (primary), Gaussian and Voigt (variants),
each over a linear baseline; outputs carry the full covariance, chi2/dof,
lag-1 residual autocorrelation and the worst-point z — the diagnostics
the plan's §3 requires on every trace.

AICc convention (stated): with per-point sigma supplied,
AIC = chi2 + 2k; without, AIC = n*ln(RSS/n) + 2k (Gaussian-error MLE up
to an additive constant, identical for same-n comparisons); both carry
the small-sample correction 2k(k+1)/(n-k-1). Only DIFFERENCES on the
same data are ever used.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable

import numpy as np
from scipy.optimize import curve_fit
from scipy.special import voigt_profile

D6_MIN_POWER_POINTS: int = 8
D6_MIN_DELTA_AICC: float = 4.0
EXTRAPOLATION_REFUSAL: str = "insufficient support for extrapolation"
D6_CITATION: str = (
    "D6 strict AND gate (user-ratified 2026-07-20): >= 8 independent "
    "power points AND delta-AICc >= 4 over linear WLS"
)

_GAUSS_FWHM_TO_SIGMA = 1.0 / (2.0 * math.sqrt(2.0 * math.log(2.0)))


class LineshapeError(ValueError):
    """Fit input fails the contract. Refusal, not repair."""


# --- lineshape models ---------------------------------------------------


def lorentzian(f, f0, fwhm, amp, b0, b1):
    x = (f - f0) / (fwhm / 2.0)
    return amp / (1.0 + x * x) + b0 + b1 * (f - f0)


def gaussian(f, f0, fwhm, amp, b0, b1):
    sigma = fwhm * _GAUSS_FWHM_TO_SIGMA
    return amp * np.exp(-0.5 * ((f - f0) / sigma) ** 2) + b0 + b1 * (f - f0)


def voigt(f, f0, fwhm_g, fwhm_l, amp, b0, b1):
    sigma = fwhm_g * _GAUSS_FWHM_TO_SIGMA
    gamma = fwhm_l / 2.0
    peak = voigt_profile(0.0, sigma, gamma)
    return amp * voigt_profile(f - f0, sigma, gamma) / peak + b0 + b1 * (f - f0)


_MODELS: dict[str, tuple[Callable, tuple[str, ...]]] = {
    "lorentzian": (lorentzian, ("f0", "fwhm", "amp", "b0", "b1")),
    "gaussian": (gaussian, ("f0", "fwhm", "amp", "b0", "b1")),
    "voigt": (voigt, ("f0", "fwhm_g", "fwhm_l", "amp", "b0", "b1")),
}


def voigt_effective_fwhm(fwhm_g: float, fwhm_l: float) -> float:
    """Olivero-Longbothum approximation (~0.02% accurate) — an effective
    width for REPORTING; the fitted (fwhm_g, fwhm_l) pair is the record."""
    return 0.5346 * fwhm_l + math.sqrt(0.2166 * fwhm_l**2 + fwhm_g**2)


@dataclass(frozen=True)
class SpectrumFit:
    model: str
    params: dict[str, float]
    sigma_params: dict[str, float]
    covariance: np.ndarray
    f0_hz: float
    f0_sigma_hz: float
    fwhm_hz: float
    fwhm_sigma_hz: float
    chi2_dof: float | None
    residual_rms: float
    lag1_autocorr: float
    worst_point_z: float
    n_points: int
    fit_window_hz: tuple[float, float]
    sigma_source: str
    notes: tuple[str, ...] = field(default=())
    converged: bool = True
    #: provenance carried from a TraceRecord via `fit_trace` — None means
    #: a bare-array (synthetic/anchor) fit that must never be presented
    #: as a dataset result (adversarial-review fix, 2026-07-20)
    dataset_version: str | None = None
    grade: str | None = None


def fit_spectrum(
    freq_hz: np.ndarray,
    signal: np.ndarray,
    *,
    model: str = "lorentzian",
    sigma: np.ndarray | float | None = None,
    window_hz: tuple[float, float] | None = None,
    p0: dict[str, float] | None = None,
) -> SpectrumFit:
    """Fit one spectrum. `sigma` per-point (or scalar) enables a real
    chi2/dof; without it the residual rms is reported and chi2_dof is None
    (honesty: no error model, no chi-square)."""
    freq = np.asarray(freq_hz, dtype=float)
    sig = np.asarray(signal, dtype=float)
    if freq.shape != sig.shape or freq.ndim != 1:
        raise LineshapeError("freq and signal must be equal-length 1-D")
    if sigma is not None:
        sigma = np.broadcast_to(
            np.asarray(sigma, dtype=float), freq.shape
        ).copy()
    if window_hz is not None:
        lo, hi = window_hz
        mask = (freq >= lo) & (freq <= hi)
        freq, sig = freq[mask], sig[mask]
        if sigma is not None:
            sigma = sigma[mask]  # window sigma WITH the data (review fix)
    if model not in _MODELS:
        raise LineshapeError(f"unknown model {model!r}; have {sorted(_MODELS)}")
    func, names = _MODELS[model]
    if freq.size < len(names) + 2:
        raise LineshapeError(
            f"{model}: {freq.size} points cannot constrain {len(names)} "
            "parameters (+2 margin)"
        )

    b0_guess = float(np.median(np.concatenate([sig[:3], sig[-3:]])))
    idx = int(np.argmax(np.abs(sig - b0_guess)))
    span = float(freq.max() - freq.min())
    guess = {
        "f0": float(freq[idx]),
        "fwhm": span / 10.0,
        "fwhm_g": span / 20.0,
        "fwhm_l": span / 20.0,
        "amp": float(sig[idx] - b0_guess),
        "b0": b0_guess,
        "b1": 0.0,
    }
    if p0:
        guess.update(p0)
    p0_vec = [guess[n] for n in names]

    if sigma is None:
        sigma_vec = None
        absolute = False
        sigma_source = "none supplied: residual rms reported, chi2_dof=None"
    else:
        sigma_vec = np.broadcast_to(np.asarray(sigma, dtype=float), freq.shape)
        if not np.all(sigma_vec > 0):
            raise LineshapeError("sigma must be > 0 everywhere")
        absolute = True
        sigma_source = "per-point sigma supplied (absolute_sigma=True)"

    popt, pcov = curve_fit(
        func,
        freq,
        sig,
        p0=p0_vec,
        sigma=sigma_vec,
        absolute_sigma=absolute,
        maxfev=20000,
    )
    if not np.all(np.isfinite(pcov)):
        raise LineshapeError(f"{model}: covariance did not converge")
    params = dict(zip(names, (float(v) for v in popt)))
    sig_params = dict(
        zip(names, (float(v) for v in np.sqrt(np.diag(pcov))))
    )
    resid = sig - func(freq, *popt)
    dof = freq.size - len(names)
    if sigma_vec is not None:
        z = resid / sigma_vec
        chi2_dof = float(np.sum(z * z) / dof)
        worst = float(np.max(np.abs(z)))
    else:
        chi2_dof = None
        rms = float(np.sqrt(np.mean(resid**2)))
        worst = float(np.max(np.abs(resid)) / rms) if rms else 0.0
    rms = float(np.sqrt(np.mean(resid**2)))
    lag1 = (
        float(
            np.corrcoef(resid[:-1], resid[1:])[0, 1]
        )
        if resid.size > 2 and np.std(resid) > 0
        else 0.0
    )

    notes: list[str] = []
    if model == "voigt":
        fwhm = voigt_effective_fwhm(
            abs(params["fwhm_g"]), abs(params["fwhm_l"])
        )
        # First-order propagation J·Cov·Jᵀ over the (fwhm_g, fwhm_l)
        # sub-covariance INCLUDING the cross-term (adversarial-review
        # fix, 2026-07-20: the diagonal-only hypot understated or
        # overstated the width uncertainty depending on the correlation).
        denom = 2 * math.sqrt(
            0.2166 * params["fwhm_l"] ** 2 + params["fwhm_g"] ** 2
        )
        d_dg = (2 * abs(params["fwhm_g"])) / denom if denom else 0.0
        d_dl = (
            0.5346 + (0.2166 * 2 * abs(params["fwhm_l"])) / denom
            if denom
            else 0.5346
        )
        ig, il = names.index("fwhm_g"), names.index("fwhm_l")
        jac = np.array([d_dg, d_dl])
        sub_cov = pcov[np.ix_([ig, il], [ig, il])]
        fwhm_sigma = float(math.sqrt(max(jac @ sub_cov @ jac, 0.0)))
        notes.append(
            "voigt effective FWHM via Olivero-Longbothum (sigma via "
            "J.Cov.J^T incl. the g-l cross-term); the fitted "
            "(fwhm_g, fwhm_l) pair is the record"
        )
    else:
        fwhm = abs(params["fwhm"])
        fwhm_sigma = sig_params["fwhm"]

    return SpectrumFit(
        model=model,
        params=params,
        sigma_params=sig_params,
        covariance=pcov,
        f0_hz=params["f0"],
        f0_sigma_hz=sig_params["f0"],
        fwhm_hz=fwhm,
        fwhm_sigma_hz=fwhm_sigma,
        chi2_dof=chi2_dof,
        residual_rms=rms,
        lag1_autocorr=lag1,
        worst_point_z=worst,
        n_points=int(freq.size),
        fit_window_hz=(float(freq.min()), float(freq.max())),
        sigma_source=sigma_source,
        notes=tuple(notes),
    )


def fit_trace(
    record,
    *,
    model: str = "lorentzian",
    sigma: np.ndarray | float | None = None,
    window_hz: tuple[float, float] | None = None,
    p0: dict[str, float] | None = None,
) -> SpectrumFit:
    """PRODUCTION entry point: fit a loaded `TraceRecord` (never bare
    arrays) so dataset_version and grade travel with the fit output
    (adversarial-review fix, 2026-07-20 — `fit_spectrum` stays available
    for synthetic anchors, whose outputs carry dataset_version=None and
    must never be presented as dataset results)."""
    from dataclasses import replace

    from calibration.raw_ingest import TraceRecord

    if not isinstance(record, TraceRecord):
        raise LineshapeError(
            "fit_trace requires a raw_ingest.TraceRecord — bare arrays go "
            "through fit_spectrum and carry no dataset provenance"
        )
    fit = fit_spectrum(
        record.freq_hz,
        record.signal,
        model=model,
        sigma=sigma,
        window_hz=window_hz,
        p0=p0,
    )
    return replace(
        fit, dataset_version=record.dataset_version, grade=record.grade
    )


# --- AICc ---------------------------------------------------------------


def aicc(n: int, k: int, *, chi2: float | None = None, rss: float | None = None) -> float:
    if n - k - 1 <= 0:
        return float("inf")
    if chi2 is not None:
        aic = chi2 + 2.0 * k
    elif rss is not None:
        if rss <= 0:
            rss = 1e-300
        aic = n * math.log(rss / n) + 2.0 * k
    else:
        raise LineshapeError("aicc needs chi2 or rss")
    return aic + 2.0 * k * (k + 1) / (n - k - 1)


# --- power-dependence models (D6-gated) ---------------------------------


def _wls(design: np.ndarray, y: np.ndarray, sigma: np.ndarray):
    w = 1.0 / sigma
    a = design * w[:, None]
    b = y * w
    beta, *_ = np.linalg.lstsq(a, b, rcond=None)
    cov = np.linalg.inv(a.T @ a)  # unscaled: sigma are absolute (T3 style)
    resid = y - design @ beta
    chi2 = float(np.sum((resid / sigma) ** 2))
    return beta, cov, chi2


@dataclass(frozen=True)
class PowerModelFit:
    name: str
    k_params: int
    params: tuple[float, ...]
    sigma_params: tuple[float, ...]
    chi2: float
    chi2_dof: float
    aicc: float
    breakpoint: float | None = None
    #: full parameter covariance (unscaled WLS), for downstream
    #: correlated-error propagation (adversarial-review fix)
    covariance: tuple[tuple[float, ...], ...] | None = None


@dataclass(frozen=True)
class PowerModelComparison:
    """Linear WLS (primary) vs the two admitted nonlinear candidates,
    with the D6 gate applied. `claimable_nonlinear` is None unless BOTH
    gate arms hold for that candidate."""

    n_points: int
    linear: PowerModelFit
    quadratic: PowerModelFit | None
    piecewise: PowerModelFit | None
    delta_aicc_quadratic: float | None
    delta_aicc_piecewise: float | None
    claimable_nonlinear: str | None
    gate_note: str

    @property
    def nonlinear_suggested_but_unclaimable(self) -> bool:
        """The data would prefer a nonlinear form (delta-AICc >= 4) but
        the point count refuses the claim — the form is undiscriminated."""
        if self.claimable_nonlinear is not None:
            return False
        for delta in (self.delta_aicc_quadratic, self.delta_aicc_piecewise):
            if delta is not None and delta >= D6_MIN_DELTA_AICC:
                return True
        return False


def fit_power_models(
    power: np.ndarray, y: np.ndarray, sigma: np.ndarray
) -> PowerModelComparison:
    """Fit y(P): linear (primary), quadratic, piecewise-linear with one
    continuous changepoint (interior grid search). All WLS with absolute
    sigma; chi2/dof reported as lack-of-fit (never absorbed)."""
    p = np.asarray(power, dtype=float)
    yv = np.asarray(y, dtype=float)
    sv = np.broadcast_to(np.asarray(sigma, dtype=float), p.shape).astype(float)
    if p.ndim != 1 or p.shape != yv.shape:
        raise LineshapeError("power and y must be equal-length 1-D")
    if np.unique(p).size != p.size:
        raise LineshapeError(
            "duplicate power points: D6 counts INDEPENDENT power points"
        )
    if not np.all(sv > 0):
        raise LineshapeError("sigma must be > 0")
    n = p.size
    if n < 3:
        raise LineshapeError("need >= 3 points for even the linear fit")

    d_lin = np.column_stack([np.ones(n), p])
    beta, cov, chi2 = _wls(d_lin, yv, sv)
    linear = PowerModelFit(
        name="linear",
        k_params=2,
        params=tuple(float(b) for b in beta),
        sigma_params=tuple(float(s) for s in np.sqrt(np.diag(cov))),
        covariance=tuple(tuple(float(x) for x in row) for row in cov),
        chi2=chi2,
        chi2_dof=chi2 / (n - 2),
        aicc=aicc(n, 2, chi2=chi2),
    )

    quadratic = None
    if n >= 4:
        d_quad = np.column_stack([np.ones(n), p, p * p])
        beta, cov, chi2 = _wls(d_quad, yv, sv)
        quadratic = PowerModelFit(
            name="quadratic",
            k_params=3,
            params=tuple(float(b) for b in beta),
            sigma_params=tuple(float(s) for s in np.sqrt(np.diag(cov))),
            chi2=chi2,
            chi2_dof=chi2 / (n - 3),
            aicc=aicc(n, 3, chi2=chi2),
        )

    piecewise = None
    if n >= 5:
        best = None
        order = np.argsort(p)
        interior = np.sort(p)[1:-1]
        for bp in interior:
            hinge = np.maximum(0.0, p - bp)
            d_pw = np.column_stack([np.ones(n), p, hinge])
            try:
                beta, cov, chi2 = _wls(d_pw, yv, sv)
            except np.linalg.LinAlgError:
                continue
            if best is None or chi2 < best[2]:
                best = (beta, cov, chi2, float(bp))
        del order
        if best is not None:
            beta, cov, chi2, bp = best
            # breakpoint is a searched parameter: k = 4
            piecewise = PowerModelFit(
                name="piecewise-linear",
                k_params=4,
                params=tuple(float(b) for b in beta),
                sigma_params=tuple(float(s) for s in np.sqrt(np.diag(cov))),
                chi2=chi2,
                chi2_dof=chi2 / max(n - 4, 1),
                aicc=aicc(n, 4, chi2=chi2),
                breakpoint=bp,
            )

    d_quad_delta = (
        linear.aicc - quadratic.aicc if quadratic is not None else None
    )
    d_pw_delta = (
        linear.aicc - piecewise.aicc if piecewise is not None else None
    )

    claimable = None
    if n >= D6_MIN_POWER_POINTS:
        candidates = []
        if d_quad_delta is not None and d_quad_delta >= D6_MIN_DELTA_AICC:
            candidates.append(("quadratic", d_quad_delta))
        if d_pw_delta is not None and d_pw_delta >= D6_MIN_DELTA_AICC:
            candidates.append(("piecewise-linear", d_pw_delta))
        if candidates:
            claimable = max(candidates, key=lambda c: c[1])[0]

    if claimable:
        gate_note = f"{D6_CITATION}: PASSED for {claimable} (n = {n})"
    elif n < D6_MIN_POWER_POINTS:
        gate_note = (
            f"{D6_CITATION}: point-count arm FAILED (n = {n} < "
            f"{D6_MIN_POWER_POINTS}) — nonlinear models are reported-only "
            "diagnostics regardless of delta-AICc; linear stands"
        )
    else:
        gate_note = (
            f"{D6_CITATION}: delta-AICc arm FAILED — linear stands; "
            "alternatives listed with their delta-AICc, unclaimed"
        )

    return PowerModelComparison(
        n_points=n,
        linear=linear,
        quadratic=quadratic,
        piecewise=piecewise,
        delta_aicc_quadratic=d_quad_delta,
        delta_aicc_piecewise=d_pw_delta,
        claimable_nonlinear=claimable,
        gate_note=gate_note,
    )


@dataclass(frozen=True)
class Extrapolation:
    """Zero-power intercept, or the refusal + operational bound."""

    refused: bool
    statement: str
    value: float | None = None
    sigma: float | None = None
    basis: str | None = None
    grade: str = "fit-extrapolated"
    operational_bound: float | None = None


def zero_power_extrapolation(
    comparison: PowerModelComparison,
    power: np.ndarray,
    y: np.ndarray,
) -> Extrapolation:
    """Plan §3 extrapolation policy, mechanised. The intercept is NEVER a
    measured quantity: grade 'fit-extrapolated' on success; on refusal
    the lowest-power measured value is the operational bound."""
    p = np.asarray(power, dtype=float)
    yv = np.asarray(y, dtype=float)
    lowest = float(yv[np.argmin(p)])

    if comparison.nonlinear_suggested_but_unclaimable:
        return Extrapolation(
            refused=True,
            statement=(
                f"{EXTRAPOLATION_REFUSAL}: the data prefer a nonlinear form "
                "(delta-AICc >= 4) but the D6 point count refuses the claim "
                "— the functional form is undiscriminated; reporting the "
                "lowest-power measured value as the operational bound"
            ),
            operational_bound=lowest,
        )
    if comparison.claimable_nonlinear == "quadratic":
        q = comparison.quadratic
        assert q is not None
        return Extrapolation(
            refused=False,
            statement="quadratic basis passed D6; intercept = c0",
            value=q.params[0],
            sigma=q.sigma_params[0],
            basis="quadratic",
        )
    if comparison.claimable_nonlinear == "piecewise-linear":
        pw = comparison.piecewise
        assert pw is not None
        return Extrapolation(
            refused=False,
            statement=(
                "piecewise basis passed D6; intercept = the low-power "
                "segment's intercept (below the breakpoint the hinge term "
                "is zero)"
            ),
            value=pw.params[0],
            sigma=pw.sigma_params[0],
            basis="piecewise-linear",
        )
    lin = comparison.linear
    return Extrapolation(
        refused=False,
        statement="linear form stands; intercept = a of a + b*P",
        value=lin.params[0],
        sigma=lin.sigma_params[0],
        basis="linear",
    )
