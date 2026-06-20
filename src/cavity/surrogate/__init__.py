"""Surrogate fit/predict — SPEC §7.

Polynomial / Gaussian-process surrogate per output (f, Q, V_mode, F_m,
cooperativity). Cheap to evaluate so Monte Carlo can call it 1e4-1e5
times without re-invoking COMSOL.

Not yet implemented (Phase 2). Register: 'surrogate', never 'ML model'.
"""
