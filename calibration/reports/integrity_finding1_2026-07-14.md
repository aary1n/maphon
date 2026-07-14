# Finding-1 resolution record — thermal.md manifest re-mint (2026-07-14)

**Archive:** `calibration/data/raw/cowley_semple_2026-07-14/`
**Ruling applied:** ratified Finding-1 ruling (a) — diff `thermal.md` vs `thermal.eml`;
re-mint the one manifest line iff divergence is render/re-save-level only; stop and
report on any content-level divergence.

## What failed

`MANIFEST.sha256` pinned `thermal.md` at
`98cd3c369ecb19b889264220d8f0d5518f5b5531fdac80d54c748e095dfdc194`.
No line-ending variant of the archived file reproduces that hash:

| variant | SHA-256 |
|---|---|
| as archived (CRLF, 9183 bytes) | `ff856929da9d9853cbf37cfab0fb20471eecf15766b51809c56b41f7a7f7904c` |
| CRLF→LF | `646d7aa2ae88dbfaf7b1ae97cbd4c1334b895ca5ab9a3ca8b21150275479eb7e` |
| manifest pin | `98cd3c369ecb19b889264220d8f0d5518f5b5531fdac80d54c748e095dfdc194` |

All 10 image attachments and `thermal.eml` PASS their pins — the primary record (the
email itself) is intact; only the derived markdown render drifted between minting and
archiving. (Side finding, folded into the verifier: the manifest itself has CRLF line
endings, so naive `sha256sum -c` fails on all 12 names with `\r`-suffixed paths;
`calibration.integrity` parses with universal newlines and tolerates `#` comments.)

## Faithfulness check (the ruling's condition)

Token-level comparison (scratchpad script, 2026-07-14): visible text of the eml's
preferred body part (`text/html`, tags stripped, entities unescaped) vs `thermal.md`
text (markdown image/link syntax stripped), both whitespace-normalised and tokenised.

- eml body tokens: 934 · md tokens: 989
- **body tokens present in eml but missing from md: 0** — every word of the email
  body survives in the render, in order (token-sequence similarity 0.9714).
- tokens present only in the md: 55, all accounted for as (i) the md's header block
  (Subject / From / To / CC / Date — rendered from the eml *headers*, which the
  body-side extraction deliberately excludes) and (ii) the residual
  `P {margin-top:0;margin-bottom:0;}` CSS fragment, a known HTML→markdown conversion
  artifact visible in the file.

**Verdict: render-level drift only; no content-level divergence.** The re-mint
condition is met.

## Action taken

One line of `MANIFEST.sha256` re-minted to the as-archived hash (`ff8569…`), with a
dated errata comment block appended inside the manifest (original pin recorded there
for provenance). CRLF byte style preserved. Post-edit verification: all 12 entries
PASS. The archive is read-only from the commit introducing this record onward;
`tests/test_calibration_integrity.py` enforces this in CI on every run.
