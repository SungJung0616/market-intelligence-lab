from datetime import date, datetime, timedelta, timezone

from market_intelligence_lab.collection.models import Observation, SeriesData
from market_intelligence_lab.jobs.run_labor_research import run_pipeline


class FakeFredClient:
    def fetch_series(self, series_id: str, observation_start: date) -> SeriesData:
        del observation_start
        if series_id == "ICSA":
            start = date(2018, 1, 6)
            observations = tuple(
                Observation(start + timedelta(weeks=index), 200_000 + index) for index in range(440)
            )
        else:
            values = []
            year, month = 2018, 1
            for index in range(100):
                values.append(Observation(date(year, month, 1), 100 + index))
                month += 1
                if month == 13:
                    year += 1
                    month = 1
            observations = tuple(values)
        return SeriesData("FRED", series_id, datetime.now(timezone.utc), observations)


def test_pipeline_saves_raw_dependencies_and_processed_report(tmp_path) -> None:
    destination = run_pipeline(
        FakeFredClient(),
        tmp_path / "raw",
        tmp_path / "processed",
        datetime(2026, 8, 11, tzinfo=timezone.utc),
    )

    assert destination.exists()
    assert len(list((tmp_path / "raw").glob("fred/*/*.json"))) == 7
    content = destination.read_text(encoding="utf-8")
    assert '"scoring_approved": false' in content
    assert '"calculation_version": "labor-distribution-v1"' in content
