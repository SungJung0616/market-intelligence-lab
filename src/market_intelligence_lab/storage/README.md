# Storage

Owns persistence interfaces and implementations for PostgreSQL, JSONB, and approved local
artifacts.

This package must not decide market meaning, calculate intelligence scores, or render output.

The initial JSON store writes normalized series to
`data/raw/<provider>/<series>/<latest-observation-date>.json`. Generated artifacts are local
research data and are not committed.

The inflation store atomically publishes validated results to
`data/processed/inflation/<data-as-of>.json`. The dashboard reads this processed contract instead
of calculating scores from raw files. Temporary or incomplete artifacts are never presented.

Daily refresh status is atomically written to `data/processed/refresh/latest.json`. It records task
names, destinations, timestamps, and exception types but never exception messages or credentials.
