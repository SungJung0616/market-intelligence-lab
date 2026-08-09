# Collection

Owns external data retrieval, response validation, normalization, deduplication, and
collection-status reporting.

This package must not contain market scoring, AI analysis, presentation, or persistence
implementation details.

The implemented provider boundaries are FRED, Tiingo, and Coinbase Exchange. Each client
retrieves, validates, and normalizes provider data without writing files or assigning market
meaning. Tiingo daily prices use `adjClose` so splits and distributions are reflected
consistently. Coinbase collection uses the unauthenticated public candles endpoint, paginates
within its 300-candle limit, and keeps only completed UTC daily BTC-USD closes.
