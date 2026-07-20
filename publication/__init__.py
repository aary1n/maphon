"""Publication build layer — `python -m publication.build`.

Sits ABOVE both `cavity` and `calibration` (it may import both; nothing
imports it). Composes the existing machinery — archive integrity,
artifact generators, the paper spine's figure contract and claim
register, and the sentinel state — into one reproducible build with four
STRICTLY SEPARATED statuses:

1. artifact reproducibility  — do the generators reproduce the committed
   paper-facing artifacts, byte-for-byte where pinned?
2. scientific validation     — what the validation gates actually say
   (phase1_complete, W2, calibration grade), never inferred from tests.
3. supervisor ratification   — which claims still carry unratified rungs.
4. publication readiness     — REFUSED while any headline claim lacks a
   complete evidence chain; passing tests alone never implies readiness.
"""
