"""Tiingo daily-price collection and provider-response validation."""

from datetime import date, datetime, timezone
from typing import Any

import httpx

from market_intelligence_lab.collection.models import Observation, SeriesData

TIINGO_DAILY_URL = "https://api.tiingo.com/tiingo/daily/{ticker}/prices"


class TiingoCollectionError(RuntimeError):
    """Raised when Tiingo data cannot be retrieved or validated."""


class TiingoClient:
    def __init__(self, api_key: str, client: httpx.Client | None = None) -> None:
        if not api_key.strip():
            raise ValueError("TIINGO_API_KEY is required")
        self._api_key = api_key
        self._client = client

    def fetch_daily_prices(self, ticker: str, observation_start: date) -> SeriesData:
        url = TIINGO_DAILY_URL.format(ticker=ticker)
        headers = {"Authorization": f"Token {self._api_key}"}
        params = {
            "startDate": observation_start.isoformat(),
            "resampleFreq": "daily",
        }
        try:
            if self._client is None:
                with httpx.Client(timeout=30.0) as client:
                    response = client.get(url, headers=headers, params=params)
            else:
                response = self._client.get(url, headers=headers, params=params)
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise TiingoCollectionError("Tiingo request failed") from exc

        observations = self._parse_observations(payload)
        return SeriesData(
            source="Tiingo",
            series_id=ticker.upper(),
            collected_at=datetime.now(timezone.utc),
            observations=observations,
        )

    @staticmethod
    def _parse_observations(payload: Any) -> tuple[Observation, ...]:
        if not isinstance(payload, list):
            raise TiingoCollectionError("Tiingo response must be a JSON array")

        parsed: list[Observation] = []
        for item in payload:
            if not isinstance(item, dict):
                raise TiingoCollectionError("Tiingo price must be an object")
            value = item.get("adjClose")
            if not isinstance(value, (int, float)):
                raise TiingoCollectionError("Tiingo adjusted close is malformed")
            try:
                observation_date = date.fromisoformat(str(item["date"])[:10])
            except (KeyError, TypeError, ValueError) as exc:
                raise TiingoCollectionError("Tiingo price date is malformed") from exc
            parsed.append(Observation(date=observation_date, value=float(value)))

        if not parsed:
            raise TiingoCollectionError("Tiingo response contains no usable prices")
        return tuple(sorted(parsed, key=lambda observation: observation.date))
