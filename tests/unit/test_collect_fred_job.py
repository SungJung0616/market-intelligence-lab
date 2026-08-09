import pytest

from market_intelligence_lab.jobs.collect_fred import parse_args


def test_parse_args_accepts_supported_series_case_insensitively() -> None:
    assert parse_args(["dgs10"]).series_id == "DGS10"
    assert parse_args(["vixcls"]).series_id == "VIXCLS"


def test_parse_args_rejects_unsupported_series() -> None:
    with pytest.raises(SystemExit):
        parse_args(["UNKNOWN"])

