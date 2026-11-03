"""Pull MT5 bars into a dated, immutable snapshot folder."""

from __future__ import annotations

import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import MetaTrader5 as mt5
import pandas as pd

from .connection import MT5ConnectionError, disconnect, ensure_connected
from .universe import MAJOR_PAIRS, resolve_majors

TIMEFRAME_MAP: dict[str, int] = {
    "M1": mt5.TIMEFRAME_M1,
    "M5": mt5.TIMEFRAME_M5,
    "M15": mt5.TIMEFRAME_M15,
    "M30": mt5.TIMEFRAME_M30,
    "H1": mt5.TIMEFRAME_H1,
    "H4": mt5.TIMEFRAME_H4,
    "D1": mt5.TIMEFRAME_D1,
    "W1": mt5.TIMEFRAME_W1,
    "MN1": mt5.TIMEFRAME_MN1,
}

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SNAPSHOT_ROOT = REPO_ROOT / "data" / "snapshots"
HISTORY_FLOOR_UTC = datetime(1970, 1, 1, tzinfo=timezone.utc)
CHUNK_EMPTY_RETRIES = 4
CHUNK_RETRY_SLEEP_SEC = 2.0
EMPTY_YEAR_STOP = 3


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _default_range(years: int = 5) -> tuple[datetime, datetime]:
    end = _utc_now()
    start = end - timedelta(days=365 * years)
    return start, end


def _bars_to_frame(rates: Any) -> pd.DataFrame:
    frame = pd.DataFrame(rates)
    frame["time"] = pd.to_datetime(frame["time"], unit="s", utc=True)
    columns = [
        "time",
        "open",
        "high",
        "low",
        "close",
        "tick_volume",
        "spread",
        "real_volume",
    ]
    return frame[columns]


def _pull_symbol(
    symbol: str,
    timeframe_code: int,
    start: datetime,
    end: datetime,
) -> pd.DataFrame:
    rates = mt5.copy_rates_range(symbol, timeframe_code, start, end)
    if rates is None or len(rates) == 0:
        raise MT5ConnectionError(
            f"No bars returned for {symbol} "
            f"({start.date()} to {end.date()}): {mt5.last_error()}"
        )
    return _bars_to_frame(rates)


def _year_windows(end: datetime, floor: datetime) -> list[tuple[datetime, datetime]]:
    """Newest-first UTC year windows from end back to floor."""
    windows: list[tuple[datetime, datetime]] = []
    year = end.year
    while year >= floor.year:
        window_start = datetime(year, 1, 1, tzinfo=timezone.utc)
        window_end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
        if window_start < floor:
            window_start = floor
        if window_end > end:
            window_end = end
        if window_start < window_end:
            windows.append((window_start, window_end))
        year -= 1
    return windows


def _copy_chunk_with_retry(
    symbol: str,
    timeframe_code: int,
    start: datetime,
    end: datetime,
) -> pd.DataFrame | None:
    """Request one date window; retry briefly while the terminal syncs."""
    for attempt in range(CHUNK_EMPTY_RETRIES):
        rates = mt5.copy_rates_range(symbol, timeframe_code, start, end)
        if rates is not None and len(rates) > 0:
            return _bars_to_frame(rates)
        if attempt + 1 < CHUNK_EMPTY_RETRIES:
            time.sleep(CHUNK_RETRY_SLEEP_SEC)
    return None


def _pull_symbol_full_history(
    symbol: str,
    timeframe_code: int,
    end: datetime | None = None,
    floor: datetime = HISTORY_FLOOR_UTC,
) -> pd.DataFrame:
    """
    Pull every available bar by walking year chunks from today back to floor.

    Stops after EMPTY_YEAR_STOP consecutive empty older years once at least
    one chunk has returned data. Keeps only bars the server actually sent.
    """
    if not mt5.symbol_select(symbol, True):
        raise MT5ConnectionError(
            f"Could not select {symbol} in Market Watch: {mt5.last_error()}"
        )

    end = end or _utc_now()
    frames: list[pd.DataFrame] = []
    empty_streak = 0
    saw_data = False

    for start, stop in _year_windows(end, floor):
        chunk = _copy_chunk_with_retry(symbol, timeframe_code, start, stop)
        if chunk is None:
            if saw_data:
                empty_streak += 1
                if empty_streak >= EMPTY_YEAR_STOP:
                    break
            continue
        saw_data = True
        empty_streak = 0
        frames.append(chunk)

    if not frames:
        raise MT5ConnectionError(
            f"No bars returned for {symbol} in full-history pull: {mt5.last_error()}"
        )

    combined = pd.concat(frames, ignore_index=True)
    combined = combined.drop_duplicates(subset=["time"]).sort_values("time")
    combined = combined.reset_index(drop=True)
    return combined


def create_snapshot(
    timeframe: str = "D1",
    years: int | None = 5,
    start: datetime | None = None,
    end: datetime | None = None,
    snapshot_root: Path | None = None,
    label: str = "majors",
    shutdown: bool = True,
    full_history: bool = False,
) -> Path:
    """
    Write a new dated snapshot folder. Refuses to overwrite an existing folder.

    When full_history is True, years/start are ignored and every available bar
    is pulled in year chunks. Returns the path of the created snapshot directory.
    """
    tf_key = timeframe.upper()
    if tf_key not in TIMEFRAME_MAP:
        raise ValueError(
            f"Unsupported timeframe {timeframe!r}. "
            f"Choose one of: {', '.join(TIMEFRAME_MAP)}"
        )

    end = end or _utc_now()
    if full_history:
        start = HISTORY_FLOOR_UTC
        years = None
    else:
        if start is None:
            if years is None:
                raise ValueError("years is required when full_history is False")
            start, _ = _default_range(years)
        if start >= end:
            raise ValueError("start must be before end")

    root = Path(snapshot_root) if snapshot_root else DEFAULT_SNAPSHOT_ROOT
    stamp = _utc_now().strftime("%Y-%m-%d")
    folder_name = f"{stamp}_{label}_{tf_key}"
    out_dir = root / folder_name
    if out_dir.exists():
        raise FileExistsError(
            f"Snapshot folder already exists and will not be overwritten: {out_dir}"
        )

    info = ensure_connected()
    terminal = mt5.terminal_info()
    maxbars = None if terminal is None else terminal.maxbars
    resolved = resolve_majors()
    timeframe_code = TIMEFRAME_MAP[tf_key]

    out_dir.mkdir(parents=True, exist_ok=False)

    symbol_rows: list[dict[str, Any]] = []
    try:
        for logical in MAJOR_PAIRS:
            broker_symbol = resolved[logical]
            if full_history:
                frame = _pull_symbol_full_history(
                    broker_symbol, timeframe_code, end=end
                )
            else:
                frame = _pull_symbol(broker_symbol, timeframe_code, start, end)
            csv_name = f"{logical}.csv"
            frame.to_csv(out_dir / csv_name, index=False)
            symbol_rows.append(
                {
                    "logical": logical,
                    "resolved": broker_symbol,
                    "csv": csv_name,
                    "bar_count": int(len(frame)),
                    "first_bar": frame["time"].iloc[0].isoformat(),
                    "last_bar": frame["time"].iloc[-1].isoformat(),
                }
            )
    except Exception:
        # Leave a partial folder only if something failed mid-write; caller can delete.
        if shutdown:
            disconnect()
        raise

    terminal_time = mt5.symbol_info_tick(resolved[MAJOR_PAIRS[0]])
    terminal_time_iso = None
    if terminal_time is not None:
        terminal_time_iso = datetime.fromtimestamp(
            terminal_time.time, tz=timezone.utc
        ).isoformat()

    actual_first = min(row["first_bar"] for row in symbol_rows)
    actual_last = max(row["last_bar"] for row in symbol_rows)

    manifest: dict[str, Any] = {
        "created_utc": _utc_now().isoformat(),
        "folder": folder_name,
        "label": label,
        "timeframe": tf_key,
        "full_history": full_history,
        "range_start_utc": start.astimezone(timezone.utc).isoformat(),
        "range_end_utc": end.astimezone(timezone.utc).isoformat(),
        "requested_years": years,
        "actual_first_bar_utc": actual_first,
        "actual_last_bar_utc": actual_last,
        "terminal": {
            "login": info["login"],
            "server": info["server"],
            "company": info["company"],
            "path": info["path"],
            "build": info["build"],
            "connected": info["connected"],
            "maxbars": maxbars,
            "tick_time_utc": terminal_time_iso,
        },
        "symbols": symbol_rows,
        "immutable": True,
        "note": (
            "This snapshot is frozen. Do not edit CSVs or rewrite this folder. "
            "Pull a new dated snapshot for new data."
        ),
    }

    (out_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )
    (out_dir / "README.md").write_text(
        (
            f"# Snapshot `{folder_name}`\n\n"
            "This folder is **immutable**. Do not edit the CSVs or rewrite "
            "`manifest.json`.\n\n"
            f"- Timeframe: `{tf_key}`\n"
            f"- Universe: eight majors ({', '.join(MAJOR_PAIRS)})\n"
            f"- Full history: `{full_history}`\n"
            f"- Created (UTC): `{manifest['created_utc']}`\n\n"
            "Later correlation experiments must name this folder in their "
            "`NOTES.md` and load bars from here. They must not open MT5 "
            "for analysis.\n"
        ),
        encoding="utf-8",
    )

    if shutdown:
        disconnect()

    return out_dir


def load_snapshot(snapshot_dir: str | Path) -> dict[str, Any]:
    """
    Load an existing snapshot without contacting MT5.

    Returns a dict with keys: path, manifest, frames (logical name -> DataFrame).
    """
    path = Path(snapshot_dir)
    if not path.is_dir():
        raise FileNotFoundError(f"Snapshot folder not found: {path}")

    manifest_path = path / "manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"manifest.json missing in {path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    frames: dict[str, pd.DataFrame] = {}
    for row in manifest["symbols"]:
        csv_path = path / row["csv"]
        frame = pd.read_csv(csv_path, parse_dates=["time"])
        frames[row["logical"]] = frame

    return {"path": path, "manifest": manifest, "frames": frames}
