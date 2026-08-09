"""Collect an approved representative ETF from Tiingo."""

import argparse
import os
from collections.abc import Sequence
from datetime import date

from market_intelligence_lab.collection.tiingo import TiingoClient
from market_intelligence_lab.storage.json_store import save_series

SUPPORTED_TICKERS = {
    "DIA": date(2016, 1, 1),
    "GLD": date(2016, 1, 1),
    "HYG": date(2016, 1, 1),
    "IWM": date(2016, 1, 1),
    "LQD": date(2016, 1, 1),
    "QQQ": date(2016, 1, 1),
    "SPY": date(2016, 1, 1),
    "TLT": date(2016, 1, 1),
    "USO": date(2016, 1, 1),
}


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect an approved Tiingo ETF series")
    parser.add_argument(
        "ticker",
        type=str.upper,
        choices=sorted(SUPPORTED_TICKERS),
        help="Approved market-evidence ETF ticker to collect",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    ticker: str = args.ticker
    api_key = os.environ.get("TIINGO_API_KEY", "")
    data = TiingoClient(api_key).fetch_daily_prices(
        ticker,
        observation_start=SUPPORTED_TICKERS[ticker],
    )
    destination = save_series(data)
    print(f"Saved {len(data.observations)} {ticker} observations to {destination}")


if __name__ == "__main__":
    main()
