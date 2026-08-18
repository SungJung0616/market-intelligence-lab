import pytest

from market_intelligence_lab.jobs.collect_fred import parse_args


def test_parse_args_accepts_supported_series_case_insensitively() -> None:
    for series_id in (
        "cpiaucsl",
        "cpilfesl",
        "ces0500000003",
        "dgs2",
        "dgs10",
        "dtwexbgs",
        "icsa",
        "jtsjol",
        "jtsjor",
        "payems",
        "pcepi",
        "pcepilfe",
        "vixcls",
        "unemploy",
        "unrate",
    ):
        assert parse_args([series_id]).series_id == series_id.upper()


def test_parse_args_rejects_unsupported_series() -> None:
    with pytest.raises(SystemExit):
        parse_args(["UNKNOWN"])
