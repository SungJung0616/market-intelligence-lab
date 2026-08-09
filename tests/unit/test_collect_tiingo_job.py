import pytest

from market_intelligence_lab.jobs.collect_tiingo import parse_args


def test_parse_args_accepts_supported_tickers_case_insensitively() -> None:
    for ticker in ("spy", "qqq", "dia", "iwm"):
        assert parse_args([ticker]).ticker == ticker.upper()


def test_parse_args_rejects_unsupported_ticker() -> None:
    with pytest.raises(SystemExit):
        parse_args(["AAPL"])
