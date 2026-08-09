# Collection

Owns external data retrieval, response validation, normalization, deduplication, and
collection-status reporting.

This package must not contain market scoring, AI analysis, presentation, or persistence
implementation details.

The first implemented provider boundary is FRED. `FredClient` retrieves and validates DGS10,
then returns normalized models without writing files or assigning market meaning.
