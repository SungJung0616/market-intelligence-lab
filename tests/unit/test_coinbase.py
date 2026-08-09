from datetime import date, datetime, timezone

import httpx
import pytest

from market_intelligence_lab.collection.coinbase import (
    CoinbaseClient,
    CoinbaseCollectionError,
)


def _timestamp(value: date) -> int:
    return int(datetime(value.year, value.month, value.day, tzinfo=timezone.utc).timestamp())


def test_fetch_daily_closes_paginates_filters_deduplicates_and_sorts() -> None:
    request_count = 0

    def respond(request: httpx.Request) -> httpx.Response:
        nonlocal request_count
        request_count += 1
        assert request.url.params["granularity"] == "86400"
        assert "authorization" not in request.headers
        if request_count == 1:
            assert request.url.params["start"] == "2025-01-01T00:00:00Z"
            assert request.url.params["end"] == "2025-10-28T00:00:00Z"
            return httpx.Response(
                200,
                json=[
                    [_timestamp(date(2025, 10, 27)), 1, 2, 1, 101.0, 10],
                    [_timestamp(date(2024, 12, 31)), 1, 2, 1, 99.0, 10],
                ],
            )
        assert request.url.params["start"] == "2025-10-28T00:00:00Z"
        assert request.url.params["end"] == "2025-11-02T00:00:00Z"
        return httpx.Response(
            200,
            json=[
                [_timestamp(date(2025, 11, 1)), 1, 2, 1, 103.0, 10],
                [_timestamp(date(2025, 10, 27)), 1, 2, 1, 102.0, 10],
            ],
        )

    client = CoinbaseClient(httpx.Client(transport=httpx.MockTransport(respond)))
    result = client.fetch_daily_closes(
        "BTC-USD",
        observation_start=date(2025, 1, 1),
        observation_end=date(2025, 11, 1),
    )

    assert request_count == 2
    assert result.source == "Coinbase"
    assert result.series_id == "BTC-USD"
    assert [(item.date, item.value) for item in result.observations] == [
        (date(2025, 10, 27), 101.0),
        (date(2025, 11, 1), 103.0),
    ]


@pytest.mark.parametrize(
    "payload",
    [
        {},
        [[1, 2, 3]],
        [["bad-time", 1, 2, 1, 100.0, 10]],
        [[_timestamp(date(2025, 1, 1)), 1, 2, 1, "100", 10]],
    ],
)
def test_fetch_daily_closes_rejects_invalid_payload(payload: object) -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json=payload))
    client = CoinbaseClient(httpx.Client(transport=transport))

    with pytest.raises(CoinbaseCollectionError):
        client.fetch_daily_closes(
            "BTC-USD",
            observation_start=date(2025, 1, 1),
            observation_end=date(2025, 1, 1),
        )


def test_fetch_daily_closes_rejects_empty_response() -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json=[]))
    client = CoinbaseClient(httpx.Client(transport=transport))

    with pytest.raises(CoinbaseCollectionError, match="no usable daily candles"):
        client.fetch_daily_closes(
            "BTC-USD",
            observation_start=date(2025, 1, 1),
            observation_end=date(2025, 1, 1),
        )


def test_fetch_daily_closes_sanitizes_http_failure() -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(503))
    client = CoinbaseClient(httpx.Client(transport=transport))

    with pytest.raises(CoinbaseCollectionError, match="Coinbase request failed"):
        client.fetch_daily_closes(
            "BTC-USD",
            observation_start=date(2025, 1, 1),
            observation_end=date(2025, 1, 1),
        )


def test_fetch_daily_closes_rejects_reversed_date_range() -> None:
    with pytest.raises(ValueError, match="observation_start"):
        CoinbaseClient().fetch_daily_closes(
            "BTC-USD",
            observation_start=date(2025, 1, 2),
            observation_end=date(2025, 1, 1),
        )
