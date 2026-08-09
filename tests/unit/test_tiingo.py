from datetime import date

import httpx
import pytest

from market_intelligence_lab.collection.tiingo import TiingoClient, TiingoCollectionError


def _client(handler: httpx.MockTransport) -> TiingoClient:
    return TiingoClient("test-token", httpx.Client(transport=handler))


def test_fetch_daily_prices_normalizes_adjusted_close_and_sorts() -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Token test-token"
        assert request.url.params["startDate"] == "2026-08-01"
        assert request.url.params["resampleFreq"] == "daily"
        return httpx.Response(
            200,
            json=[
                {"date": "2026-08-07T00:00:00.000Z", "adjClose": 638.2},
                {"date": "2026-08-06T00:00:00.000Z", "adjClose": 635},
            ],
        )

    result = _client(httpx.MockTransport(respond)).fetch_daily_prices(
        "spy", observation_start=date(2026, 8, 1)
    )

    assert result.source == "Tiingo"
    assert result.series_id == "SPY"
    assert [item.date.isoformat() for item in result.observations] == [
        "2026-08-06",
        "2026-08-07",
    ]
    assert result.observations[-1].value == 638.2


@pytest.mark.parametrize(
    "payload",
    [
        {},
        [],
        [{"date": "bad-date", "adjClose": 100.0}],
        [{"date": "2026-08-07T00:00:00.000Z", "adjClose": "100"}],
    ],
)
def test_fetch_daily_prices_rejects_invalid_payload(payload: object) -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json=payload))

    with pytest.raises(TiingoCollectionError):
        _client(transport).fetch_daily_prices("SPY", observation_start=date(2026, 8, 1))


def test_fetch_daily_prices_sanitizes_http_failure() -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(503))

    with pytest.raises(TiingoCollectionError, match="Tiingo request failed") as error:
        _client(transport).fetch_daily_prices("SPY", observation_start=date(2026, 8, 1))

    assert "test-token" not in str(error.value)
