"""EM field-export bundles — the §7.T5(b)/§9 handoff layer.

The standalone schema document (docs/field_export_schema.md, version-
locked to `EXPORT_SCHEMA_VERSION`, copied into every bundle) is the
primary deliverable; this package is its reference implementation.

  schema.py — the machine-checkable contract: version, required keys,
              `load_bundle` (refuses version mismatch),
              `validate_bundle` (full invariants).
  writer.py — `export_bundle(record, out_dir)`: a pure function of a
              §1 SolveRecord (re-derivation path; no COMSOL needed),
              unit-total-EM-energy normalisation, §7.T5(b) weights,
              full §1 reproducibility metadata incl. git commit +
              git_dirty.

Four consumers: (1) observable-b differential detuning, (2) the
Niall/Nina Maxwell-Bloch handoff (arXiv:2412.21166 — no repo access),
(3) Layer A surrogate training rows, (4) the §7.T2 output-3
inhomogeneous thermal line observable. This package builds the weights
and the pipe; it makes no predictions.
"""

from cavity.export.schema import (
    EXPORT_SCHEMA_VERSION,
    FIELDS_FILENAME,
    META_FILENAME,
    OPTIONAL_ARRAY_KEYS,
    REQUIRED_ARRAY_KEYS,
    REQUIRED_META_KEYS,
    REQUIRED_SUMMARY_KEYS,
    SCHEMA_DOC_FILENAME,
    ExportBundle,
    SchemaValidationError,
    SchemaVersionError,
    load_bundle,
    validate_bundle,
)
from cavity.export.writer import export_bundle

__all__ = [
    "EXPORT_SCHEMA_VERSION",
    "FIELDS_FILENAME",
    "META_FILENAME",
    "OPTIONAL_ARRAY_KEYS",
    "REQUIRED_ARRAY_KEYS",
    "REQUIRED_META_KEYS",
    "REQUIRED_SUMMARY_KEYS",
    "SCHEMA_DOC_FILENAME",
    "ExportBundle",
    "SchemaValidationError",
    "SchemaVersionError",
    "export_bundle",
    "load_bundle",
    "validate_bundle",
]
