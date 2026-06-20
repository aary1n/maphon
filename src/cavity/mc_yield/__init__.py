"""Monte Carlo yield / tolerance — SPEC §7.

Latin-hypercube / Sobol sampling of the surrogate; aggregates the two
yield metrics (f-detuning vs tuner range, and untunable C > 1 fraction)
plus Sobol sensitivity indices for the tolerance budget.

Ports the SiPhON infrastructure. Not yet implemented (Phase 2).
"""
