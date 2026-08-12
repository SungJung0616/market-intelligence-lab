# Jobs

Owns orchestration for scheduled pre-market, mid-session, and market-close workflows.

Jobs coordinate existing capabilities and must not duplicate collection, scoring, analysis, or
presentation logic.

The `collect_fred` entry point accepts an explicitly supported FRED series ID and connects
collection to local JSON persistence. It does not calculate or interpret market meaning.

The `collect_tiingo` entry point has the same boundary for the approved SPY, QQQ, DIA, IWM,
GLD, TLT, HYG, LQD, and USO representative ETFs. Provider data is stored locally and is not
committed or redistributed.

The `collect_coinbase` entry point collects only public BTC-USD daily candles. It requires no
API key, wallet, account access, or trading permission and stores only completed UTC days.

`run_inflation_pipeline` is the first publish pipeline. It collects all four approved FRED price
indexes in memory, validates and calculates Inflation Score v1.1, saves the raw series, and then
atomically publishes a complete processed artifact. A failed run leaves the last valid processed
result untouched.

`run_daily_refresh` runs the approved Inflation, macro FRED, Tiingo ETF, cross-asset, and Bitcoin
refreshes with one command. Each task is isolated so one provider failure does not stop remaining
work. A lock rejects concurrent runs, and the command exits non-zero after recording any partial
failure so a future scheduler can detect it.
