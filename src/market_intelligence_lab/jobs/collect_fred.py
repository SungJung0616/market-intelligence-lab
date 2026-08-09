"""Collect an approved research series from FRED."""

import argparse
import os
from collections.abc import Sequence
from datetime import date

from market_intelligence_lab.collection.fred import FredClient
from market_intelligence_lab.storage.json_store import save_series

SUPPORTED_SERIES = {
    "DGS2": date(2016, 1, 1),
    "DGS10": date(2016, 1, 1),
    "DTWEXBGS": date(2016, 1, 1),
    "VIXCLS": date(2016, 1, 1),
}


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect an approved FRED research series")
    parser.add_argument(
        "series_id",
        type=str.upper,
        choices=sorted(SUPPORTED_SERIES),
        help="FRED series to collect",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    series_id: str = args.series_id
    api_key = os.environ.get("FRED_API_KEY", "")
    data = FredClient(api_key).fetch_series(
        series_id,
        observation_start=SUPPORTED_SERIES[series_id],
    )
    destination = save_series(data)
    print(f"Saved {len(data.observations)} {series_id} observations to {destination}")


if __name__ == "__main__":
    main()
