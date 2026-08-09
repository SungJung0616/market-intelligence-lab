# Storage

Owns persistence interfaces and implementations for PostgreSQL, JSONB, and approved local
artifacts.

This package must not decide market meaning, calculate intelligence scores, or render output.

The initial JSON store writes normalized series to
`data/raw/<provider>/<series>/<latest-observation-date>.json`. Generated artifacts are local
research data and are not committed.
