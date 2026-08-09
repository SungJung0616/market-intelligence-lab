from datetime import date

import httpx
import pytest

from market_intelligence_lab.collection.fred import FredClient, FredCollectionError


def _client(handler: httpx.MockTransport) -> FredClient:
    return FredClient("test-key", httpx.Client(transport=handler))


def test_fetch_series_normalizes_and_sorts_observations() -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        assert request.url.params["series_id"] == "DGS10"
        return httpx.Response(
            200,
            json={
                "observations": [
                    {"date": "2026-08-07", "value": "4.21"},
                    {"date": "2026-08-05", "value": "4.18"},
                    {"date": "2026-08-06", "value": "."},
                ]
            },
        )

    result = _client(httpx.MockTransport(respond)).fetch_series(
        "DGS10", observation_start=date(2026, 8, 1)
    )

    assert result.series_id == "DGS10"
    assert [item.date.isoformat() for item in result.observations] == [
        "2026-08-05",
        "2026-08-07",
    ]
    assert result.observations[-1].value == 4.21


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"observations": []},
        {"observations": [{"date": "bad-date", "value": "4.2"}]},
        {"error_message": "invalid key"},
    ],
)
def test_fetch_series_rejects_invalid_payload(payload: object) -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json=payload))

    with pytest.raises(FredCollectionError):
        _client(transport).fetch_series("DGS10", observation_start=date(2026, 8, 1))


def test_fetch_series_sanitizes_http_failure() -> None:
    transport = httpx.MockTransport(lambda request: httpx.Response(503))

    with pytest.raises(FredCollectionError, match="FRED request failed") as error:
        _client(transport).fetch_series("DGS10", observation_start=date(2026, 8, 1))

    assert "test-key" not in str(error.value)

