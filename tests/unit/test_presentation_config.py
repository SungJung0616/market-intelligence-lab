from market_intelligence_lab.presentation.app import EQUITY_PREVIEWS, MACRO_PREVIEWS


def test_dashboard_covers_approved_market_evidence() -> None:
    assert {(preview.source, preview.series_id) for preview in EQUITY_PREVIEWS} == {
        ("Tiingo", "SPY"),
        ("Tiingo", "QQQ"),
        ("Tiingo", "DIA"),
        ("Tiingo", "IWM"),
    }
    assert {(preview.source, preview.series_id) for preview in MACRO_PREVIEWS} == {
        ("FRED", "DGS10"),
        ("FRED", "DGS2"),
        ("FRED", "VIXCLS"),
        ("FRED", "DTWEXBGS"),
    }


def test_equity_previews_are_explicitly_representative_etfs() -> None:
    assert all("Representative ETF" in preview.title for preview in EQUITY_PREVIEWS)
