"""Collect approved public cryptocurrency evidence from Coinbase Exchange."""

from datetime import date

from market_intelligence_lab.collection.coinbase import CoinbaseClient
from market_intelligence_lab.storage.json_store import save_series

PRODUCT_ID = "BTC-USD"
OBSERVATION_START = date(2016, 1, 1)


def main() -> None:
    data = CoinbaseClient().fetch_daily_closes(PRODUCT_ID, OBSERVATION_START)
    destination = save_series(data)
    print(f"Saved {len(data.observations)} {PRODUCT_ID} observations to {destination}")


if __name__ == "__main__":
    main()
