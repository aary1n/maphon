# Handoff — independent falsification battery for the two-linewidth threshold law (maphon §7.T4)

**Prepared:** 2026-07-20, during the adversarial review of `aary1n/maphon` @ `main` = `08709d2214724f0bbf931f4fbb79b2640def7e68`.
**Status of this document:** session record, NOT repo-pinned. All numerics were run out-of-repo in a throwaway sandbox (Python 3.12, numpy, scipy) against parameter values read from the committed reports. Any in-repo adoption must re-implement under the repository's own pin discipline (§8 anchors), using the Lorentzian-limit identity in §7.4 below as the acceptance test.
**What this covers:** (1) independent re-derivation and numerical verification of Δf_max = ((κc+κs)/2)·√(C0−1); (2) the multi-packet (inhomogeneous-line) falsification that produced the −32 % margin / exponent-sign-flip finding; (3) the closed-form exponent-stability table across κc branches, the κs band, and C0 values.

---

## 1. Conventions and normalisation

Two unit systems appear. Every transfer between them was verified numerically (§7.1, check 3).

**System A — derivation units (used in all sandbox code).**
- Angular frequencies ω (arbitrary carrier, typically 100 in code units).
- **Amplitude** decay rates `kc`, `ks` = angular HWHM. An amplitude ∝ e^{−kt} has energy decay 2k and angular FWHM 2k.
- Detuning `D = ωc − ωs` (angular).
- Coupling: the 2×2 matrix absorbs g into the off-diagonal entries `−i` and `+i·g²Sz`, so only the product `G² ≡ g²·Sz` enters. (At full inversion G² = g²N; the repo's imported C0 inherits whatever its source meant by N vs Sz — flagged in the review.)
- Cooperativity: `C0 = G²/(kc·ks)`.

**System B — repository units (cyclic-Hz FWHM).**
- `kappa_c`, `kappa_s` = cyclic-Hz FWHM; `kappa_c = f/Q_L`, never 2πf/Q_L.
- `Δf = fc − fs` cyclic Hz. `C0 = 4G²/(kappa_c·kappa_s)` with G in cyclic units.

**Transfer:** k = π·κ (amplitude-angular ← cyclic-FWHM), D = 2π·Δf. Hence
D²/(kc+ks)² = 4Δf²/(κc+κs)² exactly, and C0 is invariant. The threshold relation is homogeneous of degree 1 in (Δ, κc, κs), so both systems carry the identical law; verified to 1 ulp (check 3).

**Matched-unit shortcut (checks 6–7 only).** Because of the degree-1 homogeneity, the operating-point runs work directly in cyclic-MHz FWHM by setting amplitude rates = FWHM/2 in the same numeric units (`ac = 0.257/2`, etc.). No 2π appears; margins come out directly in MHz.

---

## 2. Equations

**Linearised two-mode model** (single homogeneous packet, inverted medium, quasi-static inversion / class-A):

```
da/dt = −(kc + i·ωc)·a − i·g·σ
dσ/dt = −(ks + i·ωs)·σ + i·g·Sz·a          (Sz > 0)
```

**Threshold** = eigenvalue of the 2×2 system crossing Re λ = 0; write λ = −iω (ω real at threshold by construction):

```
(kc + i·δc)(ks + i·δs) = G²,   δc = ωc − ω,  δs = ωs − ω        (E1)
```

- **Im(E1) ⇒ pulled frequency** (forced, not chosen):
  `kc·δs + ks·δc = 0`, with `δc − δs = D` ⇒
  `δc = kc·D/(kc+ks)`, `δs = −ks·D/(kc+ks)` ⇒
  `ω = (ks·ωc + kc·ωs)/(kc+ks)` — weighted toward the narrower resonance.
- **Re(E1) ⇒ threshold:** `G²_th = kc·ks·[1 + D²/(kc+ks)²]`, i.e.
  `C0,th = 1 + D²/(kc+ks)²` (System A) = `1 + 4Δf²/(κc+κs)²` (System B).
- **Margin:** `Δf_max = ((κc+κs)/2)·√(C0−1)`.
- **Fixed-G exponent** (κc = f/Q_L, C0 = c·Q_L, G and κs fixed):
  `E = −κc/(κc+κs) + C0/(2(C0−1))`.
- **Turnover quadratic:** E = 0 ⇔ `Q² − (f/κs)·Q + 2(f/κs)/c = 0`; real roots iff C0 evaluated at κc = κs is ≥ 8.
- **Sign-flip locus (closed form):** E < 0 ⇔ `κs < κc·(C0−2)/C0` ≈ κc for large C0.
- **Fixed-imported-C0 exponent** (comparison convention): `E = −κc/(κc+κs)` — always ≤ 0, no turnover.

**Multi-packet generalisation (loop-gain / susceptibility form).** N packets at frequencies ω_j, weights w_j (Σw_j = 1), common homogeneous amplitude rate `ks_h`:

```
1 = Σ_j  w_j·G² / [ (kc + i(ωc − ω)) · (ks_h + i(ω_j − ω)) ]     (E2)
```

Threshold = the smallest positive `G² = 1/Re S(ω0)` over the real roots ω0 of `Im S(ω) = 0`, where `S(ω)` is the bracketed sum with G² = 1. For a **Lorentzian** distribution of ω_j (HWHM Γ), (E2) reduces exactly to the single-packet law with `ks_eff = ks_h + Γ` (verified, §7.4). For a **Gaussian** distribution it does not (§7.5–7.7) — this is the load-bearing falsification.

---

## 3. Parameter values

**Repository operating point** (from `thermal/reports/q_margin_planning_point.md` and `q_margin_turnover.md`, both byte-pinned at HEAD):

| quantity | value | provenance as recorded in repo |
|---|---|---|
| f | 1.45 GHz | `TARGET.f_design_hz` |
| Q0 (own-model, canonical) | 6764.5852 | §5a rejudged record |
| k (de-loading) | 0.2 | Breeze 2017 import (`DELOAD_K`) |
| Q_L | 5637.1544 | Q0/(1+k) |
| κc (composed branch) | 257.222 kHz | f/Q_L, cyclic-Hz FWHM |
| κc (Wu-print branch) | 402.8 kHz | f/3600 (Q_L = 3600 from Q0 = 7200, k = 1; decision-memo MQ2) |
| κs point | 1.400 MHz | `KAPPA_S`, 0.1 % d14 ODMR branch |
| κs band | [0.550, 1.750] MHz | Pc:PTP host rows |
| C0 | 190 (rows 50/500) | planning import (`PLANNING_C0`, ungraded literal) |
| repo margin | 11.3915 MHz | ((κc+κs)/2)·√189 |
| repo exponent | +0.3474 | E(190, 257.222 kHz, 1.4 MHz) |

**Sandbox-only parameters** (arbitrary, chosen to exercise regimes — see §5 for the Voigt cases):

- Check 1 draws: `kc, ks ∈ 10^U(−2,2)`, `D ∈ U(−50,50)`, carrier 100; `numpy.random.default_rng(0)`, 200 draws.
- Check 2 spot case: kc = 0.7, ks = 3.1, D = 12, carrier 100.
- Checks 4–5 generic ensemble: kc = 1.0, ks_h = 0.6, Γ = 1.7 (Lorentzian) / σ = 3.4/2.35482 (Gaussian, same FWHM 2Γ = 3.4), D ∈ {1,2,4,6,8}, carrier 100.

---

## 4. Numerical setup, check by check

All root-finding on Im S used bracketing (sign change on a grid) + bisection or `scipy.optimize.brentq` (xtol 1e−12 on ω); thresholds on G² by geometric bisection (200 steps). Minimum-over-roots selection guards against picking a non-minimal Im = 0 branch.

1. **Eigenvalue vs closed form.** 2×2 matrix `M = [[−(kc+iωc), −i],[i·G², −(ks+iωs)]]`; bisect G² on max Re eig = 0; compare to `kc·ks·(1+D²/(kc+ks)²)` over 200 random draws.
2. **Pulled frequency.** At the analytic threshold G², confirm max-Re eigenvalue has Re ≈ 0 and −Im λ = (ks·ωc+kc·ωs)/(kc+ks).
3. **Unit transfer.** Evaluate the repo law at (C0, κc, κs) = (190, 257.222 kHz, 1.4 MHz); independently convert to System A (k = πκ, D found from the angular law), convert back, and re-verify with the eigen-solver at that detuning.
4. **Lorentzian inhomogeneous ensemble.** Deterministic quantile sampling of a Lorentzian: `ω_j = ωs0 + Γ·tan(π(q_j − ½))`, q_j = (j+½)/N, N = 4001, tail truncation |ω_j−ωs0| < 60Γ, equal weights 1/N. Solve (E2); compare to single-packet law with ks_eff = ks_h + Γ.
5. **Gaussian ensemble, generic point.** Grid `x ∈ [−8, 8]`, 3001 nodes, weights ∝ e^{−x²/2}; ω_j = ωs0 + σx. Compare the *ratio* C(D)/C(0) (threshold normalised to its own on-resonance value — this removes the peak-height difference between Gaussian and Lorentzian lines of equal FWHM) against the law 1 + D²/(kc+ks_eff)², and report the implied effective width `w_eff = D/√(ratio−1)`. (An earlier absolute-G² comparison giving ratio 0.7312 is superseded by this ratio-based form and should not be quoted alone.)
6. **Operating-point Voigt margins.** Matched units (§1). For each spin-line model, find on-resonance threshold g0 = G²_th(D→1e−6) (tiny offset forces a sign change through the symmetric Im = 0 root), then brentq on D ∈ [0.2, 60] MHz for `G²_th(D)/g0 = 190`. Ensemble grid x ∈ [−8, 8], 1201 nodes; ω-scan window ±30 MHz around [0, D], 3001 nodes, brentq refinement.
7. **Voigt-line exponent.** Central log-difference with ε = 0.05: evaluate the margin at (κc/(1±ε), target = 190·(1±ε)) and form E = [ln m(+) − ln m(−)]/(2·ln(1+ε)). The `target ∝ Q` substitution is exact for a symmetric distribution because on resonance `Re S(0,0) = (1/ac)·Σ w_j·as/(as² + ω_j²)` ⇒ g²_th(0) ∝ ac ∝ 1/Q; therefore at fixed G², C(D)/C(0)-target scales linearly in Q. (For asymmetric lines this shortcut is NOT exact — re-derive before reuse.)
8. **Closed-form exponent table.** Direct evaluation of E and the flip locus at both κc branches × three κs values × three C0 values; fixed-C0 convention; Wu-branch margin.

### Consolidated reference implementation

The code below reproduces every number in §6 (originals on disk as `falsify.py`, `falsify2*.py`, `falsify3b.py`, `falsify4.py`; consolidated and lightly deduplicated here, behaviour-identical).

```python
import numpy as np, math
from scipy.optimize import brentq

# ---- checks 1-3: single-packet eigenvalue route (System A) ----
def eigmax_real(g2Sz, kc, ks, wc, ws):
    M = np.array([[-(kc + 1j*wc), -1j],
                  [ 1j*g2Sz,      -(ks + 1j*ws)]])
    return max(np.linalg.eigvals(M).real)

def threshold_g2Sz(kc, ks, wc, ws, lo=1e-12, hi=1e12):
    f = lambda x: eigmax_real(x, kc, ks, wc, ws)
    assert f(lo) < 0 < f(hi)
    for _ in range(200):
        mid = math.sqrt(lo*hi)
        if f(mid) > 0: hi = mid
        else:          lo = mid
    return math.sqrt(lo*hi)

rng = np.random.default_rng(0)
worst = 0.0
for _ in range(200):
    kc = 10**rng.uniform(-2, 2); ks = 10**rng.uniform(-2, 2)
    D  = rng.uniform(-50, 50);   wc, ws = 100 + D/2, 100 - D/2
    num    = threshold_g2Sz(kc, ks, wc, ws)
    closed = kc*ks*(1 + D**2/(kc+ks)**2)
    worst  = max(worst, abs(num/closed - 1))
# -> worst ~ 1e-11; pulled freq: -Im(lam) == (ks*wc + kc*ws)/(kc+ks)

# unit transfer (System B -> A -> eigen-solver):
kap_c, kap_s, C0 = 257.222e3, 1.4e6, 190.0
df_repo = 0.5*(kap_c+kap_s)*math.sqrt(C0-1)
kc, ks  = math.pi*kap_c, math.pi*kap_s
D       = (kc+ks)*math.sqrt(C0-1)            # angular-route margin
assert abs(D/(2*math.pi)/df_repo - 1) < 1e-12

# ---- checks 4-7: multi-packet loop-gain threshold ----
def make_threshold(ac, as_h, sigma, npts=1201, span=8.0):
    """Voigt line: Gaussian(sigma) distribution of Lorentzian packets
    with amplitude rate as_h. sigma=0 -> single packet."""
    if sigma > 0:
        x  = np.linspace(-span, span, npts)
        wj = sigma*x; wt = np.exp(-x*x/2); wt /= wt.sum()
    else:
        wj = np.array([0.0]); wt = np.array([1.0])
    def S(w, D):        # spin distribution centred at 0, cavity at D
        return np.sum(wt/((ac + 1j*(D-w))*(as_h + 1j*(wj-w))))
    def Sgrid(wg, D):
        A = ac + 1j*(D - wg[:,None]); B = as_h + 1j*(wj[None,:] - wg[:,None])
        return (wt[None,:]/(A*B)).sum(axis=1)
    def G2th(D):
        grid = np.linspace(min(0,D)-30, max(0,D)+30, 3001)
        im = Sgrid(grid, D).imag; best = None
        for i in range(len(grid)-1):
            if im[i]*im[i+1] < 0:
                w0 = brentq(lambda w: np.imag(S(w,D)), grid[i], grid[i+1], xtol=1e-12)
                re = np.real(S(w0,D))
                if re > 0:
                    g2 = 1/re
                    if best is None or g2 < best: best = g2
        return best
    return G2th

def margin_MHz(kc_fwhm, as_h, sigma, target=190.0):
    """Matched cyclic-MHz-FWHM units: amplitude rates = FWHM/2."""
    G2th = make_threshold(kc_fwhm/2.0, as_h, sigma)
    g0 = G2th(1e-6)                       # on-resonance (offset forces root)
    return brentq(lambda D: G2th(D)/g0 - target, 0.2, 60.0, xtol=1e-5)

# Lorentzian-limit acceptance identity (check 4, generic units):
#   ensemble(Lorentzian Gamma) == single-packet with ks_eff = ks_h + Gamma
# (implemented with quantile sampling wj = ws0 + Gamma*tan(pi*(q-0.5)))

# Operating-point margins (check 6):
m_lor  = margin_MHz(0.257, 0.70, 0.0)                 # 11.39
m_v10  = margin_MHz(0.257, 0.05, 1.39/2.35482)        # 7.77
m_v50  = margin_MHz(0.257, 0.25, 1.00/2.35482)        # 7.51

# Voigt-line exponent (check 7): eps=0.05 central log-difference,
# kc -> kc/(1+e), target -> 190*(1+e)  [exact for symmetric lines]
def E_num(as_h, sigma, eps=0.05):
    ms = [margin_MHz(0.257/(1+e), as_h, sigma, 190*(1+e)) for e in (-eps, 0, eps)]
    return (math.log(ms[2]) - math.log(ms[0]))/(2*math.log(1+eps)), ms

# ---- check 8: closed forms ----
def E(c0, kc, ks): return -kc/(kc+ks) + c0/(2*(c0-1))
ks_flip = lambda kc, c0: kc*(c0-2)/c0
```

---

## 5. How the Voigt widths were chosen

The homogeneous/inhomogeneous decomposition of the 1.4 MHz ODMR FWHM is **unknown** — this is the repo's own open D4 question ("the single-packet mapping is a threshold-model assumption"). The cases are therefore **scenario probes chosen to bracket the branch structure**, not calibrated decompositions:

- **(a) Pure Lorentzian, FWHM 1.40 MHz** (`as_h = 0.70`, σ = 0): the repo's implicit model; doubles as the solver's acceptance test (must reproduce the closed form).
- **(b) Inhomogeneity-dominated Voigt: hom 0.10 MHz + Gaussian 1.39 MHz** (`as_h = 0.05`, σ = 1.39/2.35482): the homogeneous 0.10 MHz is a Breeze-2017-class / 2·T2*⁻¹ narrow coherence value (the class the live literature itself uses for pentacene cooperativities); the Gaussian is sized so the composite is near the ODMR point value. Physically motivated by hyperfine (many-proton, ≈Gaussian by CLT) inhomogeneous broadening in protonated Pc:PTP.
- **(c) Intermediate Voigt: hom 0.50 MHz + Gaussian 1.00 MHz** (`as_h = 0.25`, σ = 1.00/2.35482).

**Sizing imprecision, acknowledged:** by the Olivero–Longbothum approximation (f_V ≈ 0.5346·f_L + √(0.2166·f_L² + f_G²)), the composite FWHMs are ≈ **1.44 MHz** for (b) and ≈ **1.29 MHz** for (c) — approximately, not exactly, 1.40. An in-repo implementation should solve for f_G at fixed f_L so the Voigt FWHM matches 1.400 MHz exactly (and sweep f_L). This does not change the qualitative conclusion: at √(C0−1) ≈ 13.7 combined half-widths detuning, the wings — not the FWHM — carry the answer, and Gaussian vs Lorentzian wings differ by far more than the ±3–8 % FWHM mismatch. Note the ensemble realises a *physical Voigt line* (Gaussian distribution of Lorentzian packets), so far-wing gain correctly reverts to the packets' homogeneous Lorentzian tails (∝ as_h/δ²) beyond the Gaussian core — the mechanism that keeps case (b) at 7.8 MHz rather than collapsing to the hom-only law's 2.45 MHz.

---

## 6. Claimed outputs (verbatim from the session runs)

**Verification (single-packet law):**
- Eigenvalue vs closed form, 200 random draws: worst relative error **1.04×10⁻¹¹**.
- Pulled frequency spot check: Re λ = 1.4×10⁻¹⁴; −Im λ = 103.78947368421058 vs predicted 103.78947368421053.
- Unit transfer at the operating point: repo Δf_max = 11 391 517.8875 Hz; angular eigen-route identical (ratio 1 − 1×10⁻¹⁶); eigen-threshold/analytic G² = 1 + 3×10⁻¹⁵.

**Lorentzian inhomogeneous ensemble (kc = 1.0, ks_h = 0.6, Γ = 1.7, D = 4):**
numeric G²_th = 5.679242 vs single-packet(ks_h+Γ) = 5.679247 → **ratio 1.0000** (law exact; this is the acceptance identity).

**Gaussian ensemble, generic point (same FWHM as the Lorentzian case):** ratio-based C(D)/C(0) vs law, and implied effective width (law uses kc+ks_eff = 3.300):

| D | Gaussian C(D)/C(0) | law 1+D²/3.300² | implied w_eff |
|---|---|---|---|
| 1.0 | 1.0832 | 1.0918 | 3.467 |
| 2.0 | 1.3525 | 1.3673 | 3.369 |
| 4.0 | 2.6633 | 2.4692 | 3.101 |
| 6.0 | 5.3023 | 4.3058 | 2.893 |
| 8.0 | 9.3191 | 6.8770 | 2.774 |

**Operating-point margins at C(Δ)/C(0) = 190, κc = 0.257 MHz:**

| spin-line model | margin | repo law |
|---|---|---|
| (a) Lorentzian 1.40 | **11.39 MHz** | 11.39 (exact) |
| (b) Voigt 0.10 + 1.39 | **7.77 MHz** (−32 %) | 11.39; hom-only-law ref 2.45 |
| (c) Voigt 0.50 + 1.00 | **7.51 MHz** | 11.39; κs=0.5-law ref 5.20 |

**Fixed-G exponent, numerical (ε = 0.05):**

| spin-line model | margins at Q·(1−ε, 1, 1+ε) | E |
|---|---|---|
| (a) Lorentzian 1.40 | 11.191 / 11.390 / 11.587 | **+0.356** (closed form +0.347) |
| (b) Voigt 0.10 + 1.39 | 7.837 / 7.774 / 7.716 | **−0.160** (sign flips) |

**Closed-form exponent stability (Lorentzian model, fixed-G):**

| κc \ κs | 0.55 MHz | 1.40 MHz | 1.75 MHz |
|---|---|---|---|
| composed 257.222 kHz | +0.184 | +0.347 | +0.374 |
| Wu-print 402.8 kHz | +0.080 | +0.279 | +0.316 |

- C0 sensitivity at (257 kHz, 1.4 MHz): +0.355 / +0.347 / +0.346 for C0 = 50 / 190 / 500.
- Sign-flip loci (Lorentzian, C0 = 190): κs < 255 kHz (composed κc), κs < 399 kHz (Wu κc).
- Fixed-imported-C0 convention: E = −κc/(κc+κs) = **−0.155** at the operating point; monotone ≤ 0, no turnover.
- Wu-print-branch margin at C0 = 190, κs = 1.4 MHz: **12.39 MHz** (memo cross-check: "≈ 12.4" ✓; E cross-check +0.279 vs memo "≈ +0.28" ✓).

**Headline claims this battery supports:**
1. The two-linewidth law, pulled frequency, unit conventions, limits, and turnover algebra are **correct** as committed (verified independently to ~1×10⁻¹¹).
2. The single-packet mapping is **exact** for Lorentzian inhomogeneous broadening (κs = hom + inhom) and **fails** for Gaussian/Voigt lines at the operating detuning scale: margin −32 % and **E sign-inverts to ≈ −0.16** in the inhomogeneity-dominated scenario.
3. Within the Lorentzian model the +0.35 sign conclusion is stable across every stated (κc-branch × κs-band × C0) corner, weakest at (Wu-κc, κs-lo) = +0.08; it flips only if the threshold-relevant Lorentzian-equivalent κs falls below ≈ κc (255–400 kHz).

---

## 7. Acknowledged uncertainties and limitations

**Numerical:**
- Gaussian ensembles are truncated at ±8σ (1201–3001 nodes). Beyond the grid, wing gain is carried only through the packets' Lorentzian tails; the discretisation was not convergence-swept (a doubling test is recommended in any port; the Lorentzian identity passing at 4001 quantile nodes to 1×10⁻⁶ is indirect evidence the resolution is adequate).
- Im S root scans use a finite window (±30 units) with 3001-node sign-change detection; a root falling exactly on a node or outside the window would be missed. The symmetric on-resonance case has Im S ≡ 0 at ω = centre with no sign change — worked around with a 1×10⁻⁶ detuning offset. Minimum-over-roots selection is essential (multiple Im = 0 branches exist off resonance).
- Exponent finite differences use ε = 0.05; the Lorentzian control run's +0.356 vs the exact +0.347 (≈ 0.009 bias) calibrates the expected finite-difference error, so the Voigt E = −0.160 is sign-safe but its second digit is not.
- The `target ∝ Q` substitution in the exponent check is proved exact only for frequency-symmetric spin distributions (Re S(0,0) ∝ 1/ac). Asymmetric lines (e.g. hyperfine multiplets) need the full fixed-G² formulation.
- brentq/bisection tolerances: ω to 1×10⁻¹², margin D to 1×10⁻⁵ MHz, G² to ~1×10⁻⁶ relative (200 geometric bisection steps).
- Seeds fixed (`default_rng(0)` for the random-draw check); quantile/grid ensembles are deterministic.

**Modelling:**
- Voigt decompositions are **scenario probes** (§5): composite FWHMs ≈ 1.44 / 1.29 MHz rather than exactly 1.40, and neither the 0.10 MHz nor the 0.50 MHz homogeneous width is a measurement of the maser crystal. Conclusions are about the *branch structure* (Lorentzian-exact vs Gaussian-broken; sign flip possible), not about precise Voigt margins.
- All runs inherit the review-scope assumptions: class-A/quasi-static inversion, single cavity mode, free-running oscillator (no injection), static κs (no κs(ΔT) feedback), C0 treated as the on-resonance threshold-normalised gain. The C0 = 190 import, composed-κc, common-ΔT (D8), and probe-weight caveats of the repo apply unchanged to every number here.
- The exponent-stability table is closed-form and therefore exact *given* the Lorentzian single-packet model and the fixed-G convention; it says nothing outside them.
- κc = 402.8 kHz (Wu-print branch) was computed here as f/3600 from the decision memo's Q_L = 3600; it was not re-derived from the archived Wu PDFs in this session.
- Repo test results (1022 passed / 21 skipped) were treated as reported; no in-repo test execution occurred in this session.

**Provenance/verification gaps carried from the review:**
- Breeze 2018's κs ≪ κc condition for its Eq. (2) was verified from the primary; Breeze 2017's κc/κs ≈ 0.18/0.11 MHz values were taken as the project quotes them.
- The literature novelty search was incomplete on textbook corpora (Haken *Laser Theory* etc. not full-text searched); the "detuned Lorenz–Haken threshold r₀ = 1 + Δ̄²" equivalence rests on located instances plus reviewer knowledge.

---

## 8. Suggested in-repo acceptance tests (if this battery is ported)

1. **Lorentzian identity (the gate):** ensemble threshold with a Lorentzian frequency distribution (Γ) must equal `delta_f_max_hz`'s closed form with κs = κ_hom + 2Γ/π-consistent FWHM composition, to ≤ 1×10⁻⁴ relative — the exact analogue of the session's ratio-1.0000 check.
2. **Degenerate-ensemble regression:** σ → 0 ensemble must reproduce anchors A12/A13 exactly.
3. **Convergence pins:** margin invariant (≤ 1×10⁻³ rel) under grid doubling (nodes and span) for every reported Voigt case.
4. **Exact-FWHM Voigt sizing:** solve Olivero–Longbothum (or numerically) for f_G given f_L so the composite FWHM equals `KAPPA_S.kappa_s_hz` exactly; sweep f_L over a stated grid; report the (f_L, margin, E) map with the sign contour marked.
5. **Symmetry precondition pin:** assert the distribution is symmetric before using the target-∝-Q exponent shortcut, or implement the fixed-G² route.
