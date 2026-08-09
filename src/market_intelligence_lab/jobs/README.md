# Jobs

Owns orchestration for scheduled pre-market, mid-session, and market-close workflows.

Jobs coordinate existing capabilities and must not duplicate collection, scoring, analysis, or
presentation logic.

The `collect_fred` entry point accepts an explicitly supported FRED series ID and connects
collection to local JSON persistence. It does not calculate or interpret market meaning.

The `collect_tiingo` entry point has the same boundary for the approved SPY, QQQ, DIA, and IWM
representative ETFs. Provider data is stored locally and is not committed or redistributed.
