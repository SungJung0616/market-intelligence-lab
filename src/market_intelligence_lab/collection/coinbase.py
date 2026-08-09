"""Coinbase Exchange daily-candle collection and response validation."""

from datetime import date, datetime, time, timedelta, timezone
from typing import Any

import httpx

from market_intelligence_lab.collection.models import Observation, SeriesData

COINBASE_CANDLES_URL = "https://api.exchange.coinbase.com/products/{product_id}/candles"
DAILY_GRANULARITY_SECONDS = 86_400
MAX_CANDLES_PER_REQUEST = 300


class CoinbaseCollectionError(RuntimeError):
    """Raised when Coinbase data cannot be retrieved or validated."""


class CoinbaseClient:
    def __init__(self, client: httpx.Client | None = None) -> None:
        self._client = client

    def fetch_daily_closes(
        self,
        product_id: str,
        observation_start: date,
        observation_end: date | None = None,
    ) -> SeriesData:
        final_date = observation_end or (datetime.now(timezone.utc).date() - timedelta(days=1))
        if observation_start > final_date:
            raise ValueError("observation_start must not be after observation_end")

        observations_by_date: dict[date, Observation] = {}
        window_start = observation_start
        while window_start <= final_date:
            window_end_exclusive = min(
                window_start + timedelta(days=MAX_CANDLES_PER_REQUEST),
                final_date + timedelta(days=1),
            )
            payload = self._request_window(product_id, window_start, window_end_exclusive)
            for observation in self._parse_candles(payload):
                if window_start <= observation.date < window_end_exclusive:
                    observations_by_date[observation.date] = observation
            window_start = window_end_exclusive

        if not observations_by_date:
            raise CoinbaseCollectionError("Coinbase response contains no usable daily candles")

        return SeriesData(
            source="Coinbase",
            series_id=product_id.upper(),
            collected_at=datetime.now(timezone.utc),
            observations=tuple(observations_by_date[key] for key in sorted(observations_by_date)),
        )

    def _request_window(
        self,
        product_id: str,
        window_start: date,
        window_end_exclusive: date,
    ) -> Any:
        url = COINBASE_CANDLES_URL.format(product_id=product_id)
        params: dict[str, str | int] = {
            "start": _utc_midnight(window_start),
            "end": _utc_midnight(window_end_exclusive),
            "granularity": DAILY_GRANULARITY_SECONDS,
        }
        headers = {"User-Agent": "market-intelligence-lab/0.1"}
        try:
            if self._client is None:
                with httpx.Client(timeout=30.0) as client:
                    response = client.get(url, params=params, headers=headers)
            else:
                response = self._client.get(url, params=params, headers=headers)
            response.raise_for_status()
            return response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise CoinbaseCollectionError("Coinbase request failed") from exc

    @staticmethod
    def _parse_candles(payload: Any) -> tuple[Observation, ...]:
        if not isinstance(payload, list):
            raise CoinbaseCollectionError("Coinbase response must be a JSON array")

        parsed: list[Observation] = []
        for candle in payload:
            if not isinstance(candle, list) or len(candle) < 5:
                raise CoinbaseCollectionError("Coinbase candle is malformed")
            timestamp, close = candle[0], candle[4]
            if not isinstance(timestamp, (int, float)) or not isinstance(close, (int, float)):
                raise CoinbaseCollectionError("Coinbase candle values are malformed")
            try:
                candle_date = datetime.fromtimestamp(timestamp, timezone.utc).date()
                close_value = float(close)
            except (OverflowError, OSError, ValueError) as exc:
                raise CoinbaseCollectionError("Coinbase candle values are malformed") from exc
            parsed.append(Observation(date=candle_date, value=close_value))
        return tuple(parsed)


def _utc_midnight(value: date) -> str:
    return datetime.combine(value, time.min, tzinfo=timezone.utc).isoformat().replace(
        "+00:00", "Z"
    )
