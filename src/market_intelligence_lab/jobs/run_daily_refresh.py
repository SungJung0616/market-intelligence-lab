"""Refresh all approved daily market evidence with one command."""

import os
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from market_intelligence_lab.collection.coinbase import CoinbaseClient
from market_intelligence_lab.collection.fred import FredClient
from market_intelligence_lab.collection.tiingo import TiingoClient
from market_intelligence_lab.jobs.collect_coinbase import OBSERVATION_START, PRODUCT_ID
from market_intelligence_lab.jobs.collect_fred import SUPPORTED_SERIES
from market_intelligence_lab.jobs.collect_tiingo import SUPPORTED_TICKERS
from market_intelligence_lab.jobs.run_inflation_pipeline import run_pipeline
from market_intelligence_lab.storage.json_store import save_series
from market_intelligence_lab.storage.refresh_store import (
    DailyRefreshStatus,
    RefreshTaskResult,
    save_refresh_status,
)

MACRO_SERIES = ("DGS2", "DGS10", "VIXCLS", "DTWEXBGS")


@dataclass(frozen=True, slots=True)
class RefreshTask:
    name: str
    run: Callable[[], Path]


def build_tasks(
    fred: FredClient,
    tiingo: TiingoClient,
    coinbase: CoinbaseClient,
    raw_root: Path = Path("data/raw"),
    processed_root: Path = Path("data/processed"),
) -> tuple[RefreshTask, ...]:
    tasks = [
        RefreshTask(
            "inflation",
            lambda: run_pipeline(fred, raw_root=raw_root, processed_root=processed_root),
        )
    ]
    tasks.extend(_fred_refresh_task(fred, series_id, raw_root) for series_id in MACRO_SERIES)
    tasks.extend(_tiingo_refresh_task(tiingo, ticker, raw_root) for ticker in SUPPORTED_TICKERS)
    tasks.append(
        RefreshTask(
            "coinbase:BTC-USD",
            lambda: save_series(
                coinbase.fetch_daily_closes(PRODUCT_ID, OBSERVATION_START), raw_root
            ),
        )
    )
    return tuple(tasks)


def _fred_refresh_task(fred: FredClient, series_id: str, raw_root: Path) -> RefreshTask:
    def collect() -> Path:
        return save_series(fred.fetch_series(series_id, SUPPORTED_SERIES[series_id]), raw_root)

    return RefreshTask(f"fred:{series_id}", collect)


def _tiingo_refresh_task(tiingo: TiingoClient, ticker: str, raw_root: Path) -> RefreshTask:
    def collect() -> Path:
        return save_series(tiingo.fetch_daily_prices(ticker, SUPPORTED_TICKERS[ticker]), raw_root)

    return RefreshTask(f"tiingo:{ticker}", collect)


def run_daily_refresh(
    tasks: tuple[RefreshTask, ...],
    processed_root: Path = Path("data/processed"),
    now: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
) -> DailyRefreshStatus:
    started_at = now()
    results: list[RefreshTaskResult] = []
    with _exclusive_refresh_lock(processed_root):
        for task in tasks:
            try:
                destination = task.run()
                results.append(RefreshTaskResult(task.name, "success", str(destination), None))
            except Exception as exc:  # Continue independent refreshes and report safely.
                results.append(RefreshTaskResult(task.name, "failed", None, type(exc).__name__))
        failed = sum(result.status == "failed" for result in results)
        status = DailyRefreshStatus(
            started_at=started_at,
            finished_at=now(),
            status="success" if failed == 0 else "partial_failure",
            succeeded=len(results) - failed,
            failed=failed,
            tasks=tuple(results),
        )
        save_refresh_status(status, processed_root)
    return status


@contextmanager
def _exclusive_refresh_lock(processed_root: Path) -> Iterator[None]:
    lock = processed_root / "refresh" / ".lock"
    lock.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise RuntimeError("A daily refresh is already running") from exc
    os.close(descriptor)
    try:
        yield
    finally:
        lock.unlink(missing_ok=True)


def main() -> None:
    fred = FredClient(os.environ.get("FRED_API_KEY", ""))
    tiingo = TiingoClient(os.environ.get("TIINGO_API_KEY", ""))
    status = run_daily_refresh(build_tasks(fred, tiingo, CoinbaseClient()))
    for result in status.tasks:
        detail = result.destination or result.error_type or "unknown"
        print(f"[{result.status.upper()}] {result.name}: {detail}")
    print(f"Daily refresh {status.status}: {status.succeeded} succeeded, {status.failed} failed")
    if status.failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
