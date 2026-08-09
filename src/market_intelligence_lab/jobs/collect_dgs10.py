"""Collect the initial DGS10 research dataset from FRED."""

import os
from datetime import date

from market_intelligence_lab.collection.fred import FredClient
from market_intelligence_lab.storage.json_store import save_series


def main() -> None:
    api_key = os.environ.get("FRED_API_KEY", "")
    data = FredClient(api_key).fetch_series("DGS10", observation_start=date(2016, 1, 1))
    destination = save_series(data)
    print(f"Saved {len(data.observations)} DGS10 observations to {destination}")


if __name__ == "__main__":
    main()

