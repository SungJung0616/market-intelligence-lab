"""FRED series collection and provider-response validation."""

from datetime import date, datetime, timezone
from typing import Any

import httpx

from market_intelligence_lab.collection.models import Observation, SeriesData

FRED_OBSERVATIONS_URL = "https://api.stlouisfed.org/fred/series/observations"


class FredCollectionError(RuntimeError):
    """Raised when FRED data cannot be retrieved or validated."""


class FredClient:
    def __init__(self, api_key: str, client: httpx.Client | None = None) -> None:
        if not api_key.strip():
            raise ValueError("FRED_API_KEY is required")
        self._api_key = api_key
        self._client = client

    def fetch_series(self, series_id: str, observation_start: date) -> SeriesData:
        params = {
            "series_id": series_id,
            "api_key": self._api_key,
            "file_type": "json",
            "observation_start": observation_start.isoformat(),
        }
        try:
            if self._client is None:
                with httpx.Client(timeout=30.0) as client:
                    response = client.get(FRED_OBSERVATIONS_URL, params=params)
            else:
                response = self._client.get(FRED_OBSERVATIONS_URL, params=params)
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise FredCollectionError("FRED request failed") from exc

        observations = self._parse_observations(payload)
        return SeriesData(
            source="FRED",
            series_id=series_id,
            collected_at=datetime.now(timezone.utc),
            observations=observations,
        )

    @staticmethod
    def _parse_observations(payload: Any) -> tuple[Observation, ...]:
        if not isinstance(payload, dict):
            raise FredCollectionError("FRED response must be a JSON object")
        if "error_message" in payload:
            raise FredCollectionError("FRED returned an API error")

        raw_observations = payload.get("observations")
        if not isinstance(raw_observations, list):
            raise FredCollectionError("FRED response is missing observations")

        parsed: list[Observation] = []
        for item in raw_observations:
            if not isinstance(item, dict):
                raise FredCollectionError("FRED observation must be an object")
            value = item.get("value")
            if value == ".":
                continue
            if not isinstance(value, (str, int, float)):
                raise FredCollectionError("FRED observation value is malformed")
            try:
                parsed.append(
                    Observation(date=date.fromisoformat(item["date"]), value=float(value))
                )
            except (KeyError, TypeError, ValueError) as exc:
                raise FredCollectionError("FRED observation is malformed") from exc

        if not parsed:
            raise FredCollectionError("FRED response contains no usable observations")
        return tuple(sorted(parsed, key=lambda observation: observation.date))
