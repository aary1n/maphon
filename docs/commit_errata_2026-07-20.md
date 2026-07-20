# Commit-message errata — publication-readiness range, 2026-07-20

**Status: dated errata record (audit ruling 4, user-ratified 2026-07-20).**
The commits below are NOT rebased — the ruling records corrections beside
the history rather than rewriting it. Established during the 2026-07-20
read-only adversarial audit of `0b2668f..36c5fe5` and adversarially
re-verified against the live suite.

## Erratum 1 — `8a512a5` test-count label

The message states "67 new tests (898 -> 965 collected)". **898 and 965
are PASSED counts, not collected counts.** With the constant 21 skips,
collected went 919 → 986 across that commit.

## Erratum 2 — `9807e3a` test-count label

The message states "(was 984 collected post-WS4; +17)". **984 is the
post-WS4 PASSED count** (collected was 1005). The same message's
"1001 passed / 21 skipped" is correct (collected 1022).

## Reconciliation (authoritative chain)

| commit | passed | skipped | collected |
|---|---:|---:|---:|
| `0b2668f` (baseline) | 852 | 21 | 873 |
| `e505d25` (+16) | 868 | 21 | 889 |
| `0faed83` (+30) | 898 | 21 | 919 |
| `8a512a5` (+67) | 965 | 21 | 986 |
| `d3a6d4b` (+19) | 984 | 21 | 1005 |
| `9807e3a` (+17) | 1001 | 21 | 1022 |
| `36c5fe5` (+18) | 1019 | 21 | 1040 |

Verified at `36c5fe5` on 2026-07-20: `pytest --collect-only -q` reported
"1040 tests collected"; the full suite ran 1019 passed / 21 skipped /
0 failed. (Post-audit fix commits adjust these totals onward from
`4242f4a`, declared in their own messages.)

## MAJOR 6/7 disposition — unrecoverable

`36c5fe5`'s message enumerates its source review's findings as BLOCKER
1–4, MAJOR 1–5, MAJOR 8, and MINOR 1–3, silently skipping MAJOR 6 and
MAJOR 7. The final adversarial review (Codex, 2026-07-20) that produced
that numbering was never committed to the repository, and its finding
list is not reconstructable from the repo. **The disposition of MAJOR 6
and MAJOR 7 is therefore unrecoverable**; whether they were fixed,
rejected, or deferred is unknown. Recorded as such per audit ruling 4 —
future review lists that drive a fix commit must be committed alongside
it.
