# SPEC §7.T4 — Q-margin turnover map (2026-07-13)

**Status: deterministic two-linewidth turnover map — the new §7.T4 object replacing the bare -1/2 exponent.** Regenerate with `python -m cavity.thermal.report_turnover`.

## Parameters

- f = 1.45 GHz (`TARGET.f_design_hz`).
- Q0 = 6764.5852 (OWN-MODEL canonical branch, re-based §5a record `refs/gate_runs/20260711T132705Z_rejudge/`, record hash `823e67969516bcf2`).
- Q_L = Q0/(1 + k) = 5637.1544.
- kappa_c = f/Q_L = 257.222 kHz (CYCLIC-Hz FWHM).
- kappa_s = 1.400 MHz (`KAPPA_S`, CYCLIC-Hz FWHM; band [0.550, 1.750] MHz).
- c = PLANNING_C0/Q_L = 0.035478894, calibrated so C0 = 200 at the planning Q_L.

## Derivation summary (2026-07-13)

- Eigenvalue threshold: C0 = 1 + 4*Delta^2/(kappa_c+kappa_s)^2.
- Pulled frequency: omega = (kappa_c*omega_s + kappa_s*omega_c)/(kappa_c+kappa_s).
- Threshold margin: Delta_f_max = ((kappa_c+kappa_s)/2)*sqrt(C0-1).
- Fixed-G, fixed-kappa_s exponent under kappa_c = f/Q_L and C0 = c*Q_L: E = -kappa_c/(kappa_c+kappa_s) + C0/(2*(C0-1)).
- Turnover: Q_L^2 - (f/kappa_s)*Q_L + 2*(f/kappa_s)/c = 0; real roots exist iff C0 evaluated at kappa_c = kappa_s is >= 8.

## Q_L map

| Q_L | kappa_c/kappa_s | C0 = c*Q_L | Delta_f_max (MHz) | E |
|---:|---:|---:|---:|---:|
| 32.0000 | 32.366071 | 1.135325 | 8.5919 | +3.2248 |
| 56.0000 | 18.494898 | 1.986818 | 13.5562 | +0.0580 |
| 100.0000 | 10.357143 | 3.547889 | 12.6899 | -0.2157 |
| 178.0000 | 5.818620 | 6.315243 | 11.0041 | -0.2593 |
| 316.0000 | 3.277577 | 11.211330 | 9.5683 | -0.2173 |
| 562.0000 | 1.842908 | 19.939138 | 8.6605 | -0.1218 |
| 1000.0000 | 1.035714 | 35.478894 | 8.3674 | +0.0057 |
| 1778.0000 | 0.582516 | 63.081473 | 8.7283 | +0.1400 |
| 3162.0000 | 0.327550 | 112.184262 | 9.7988 | +0.2578 |
| 5637.1544 | 0.183730 | 200.000000 | 11.6890 | +0.3473 |
| 10000.0000 | 0.103571 | 354.788936 | 14.5302 | +0.4076 |
| 31623.0000 | 0.032752 | 1121.949053 | 24.2040 | +0.4687 |
| 100000.0000 | 0.010357 | 3547.889363 | 42.1208 | +0.4899 |
| 1000000.0000 | 0.001036 | 35478.893627 | 131.9856 | +0.4990 |

Rows with C0 <= 1 are below threshold and print an em-dash for Delta_f_max and E.

## Crossings

- Closed-form roots (4 s.f.): Q_- = 59.83, Q_+ = 975.9.
- Large-C0 reference: f/kappa_s = 1036.
- Existence condition: C0 at kappa_c = kappa_s is 36.7460 >= 8, so both roots are real.
- Operating point: Q_L = 5637.1544, E = +0.3473, kappa_c/kappa_s = 0.184; far side of the turnover - the committed -1/2 scaling's regime is kappa_c >> kappa_s.

## kappa_s-band sensitivity

- kappa_s = 0.550 MHz: Q_- = 22.34, Q_+ = 2614 (fixed-G rescaling of c).
- kappa_s = 1.750 MHz: Q_- = 77.76, Q_+ = 750.8 (fixed-G rescaling of c).

## Status notes

- SPEC §7.T4 rung: the Q-margin QUESTION is supervisor-endorsed (Oxborrow-verbal 2026-07-06); the RESULT is unratified — these are budget maps and a planning point, not the joint C0/kappa_c DOF derivation (Layer A; SPEC §11 item 9).
- FIXED-G vs C0-IMPORT: this map varies Q_L at fixed G and kappa_s (C0 = c*Q_L); the planning-point report imports C0 = 200 directly. The joint C0/kappa_c/kappa_s dependence on the geometry DOFs is Layer A (SPEC section 11 item 9) - not derived here.
- SIGN-INVERSION FINDING (derived 2026-07-13, UNRATIFIED - needs supervisor ratification before headline use): at the operating point the Q-margin exponent is ~ +0.35, not -1/2; the committed 1/sqrt(Q) law is the kappa_s -> 0 limit.
- KAPPA_S is the static, T-independent planning branch; thermal kappa_s(Delta_T) feedback remains outside this turnover map.
