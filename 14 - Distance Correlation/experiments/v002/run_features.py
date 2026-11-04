"""v002: trailing 252-day biased distance correlation."""

from __future__ import annotations

import itertools
import math
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from shared.mt5_data import MAJOR_PAIRS, load_snapshot

SNAPSHOT_REL = Path("data/snapshots/2026-11-03_majors_alpari_D1")
EXP_DIR = Path(__file__).resolve().parent
OUT_DIR = EXP_DIR / "outputs"
WINDOW = 252
STEP_IF_SLOW = 5
SLOW_SECONDS = 2 * 60 * 60


def _prepare_frames(frames: dict[str, pd.DataFrame]) -> str:
    drop_date = None
    for name, frame in frames.items():
        work = frame.copy()
        work["time"] = pd.to_datetime(work["time"], utc=True)
        work = work.sort_values("time").reset_index(drop=True)
        if len(work) >= 2:
            last_tv = float(work.iloc[-1]["tick_volume"])
            prev_tv = float(work.iloc[-2]["tick_volume"])
            if prev_tv > 0 and last_tv < 0.5 * prev_tv:
                drop_date = work.iloc[-1]["time"]
                work = work.iloc[:-1].reset_index(drop=True)
        work["log_return"] = np.log(work["close"] / work["close"].shift(1))
        frames[name] = work
    if drop_date is None:
        return "No unfinished last bar was dropped."
    return (
        f"Dropped unfinished last bar dated {drop_date.date().isoformat()} "
        "UTC after a tick-volume check against the prior complete day."
    )


def _distance_correlation(x: np.ndarray, y: np.ndarray) -> float:
    x = np.asarray(x, dtype=float).ravel()
    y = np.asarray(y, dtype=float).ravel()
    n = len(x)
    if n < 2:
        return float("nan")
    a = np.abs(x[:, None] - x[None, :])
    b = np.abs(y[:, None] - y[None, :])

    def _center(m: np.ndarray) -> np.ndarray:
        row = m.mean(axis=1, keepdims=True)
        col = m.mean(axis=0, keepdims=True)
        return m - row - col + m.mean()

    a_c = _center(a)
    b_c = _center(b)
    num = float(np.mean(a_c * b_c))
    da = float(np.mean(a_c * a_c))
    db = float(np.mean(b_c * b_c))
    if da <= 0.0 or db <= 0.0 or num <= 0.0:
        return 0.0
    return float(math.sqrt(num / math.sqrt(da * db)))


def _rolling(x: np.ndarray, y: np.ndarray, step: int) -> np.ndarray:
    n = len(x)
    out = np.full(n, np.nan)
    last = float("nan")
    for t in range(WINDOW - 1, n):
        if step == 1 or (t - (WINDOW - 1)) % step == 0:
            last = _distance_correlation(x[t - WINDOW + 1 : t + 1], y[t - WINDOW + 1 : t + 1])
        out[t] = last
    return out


def _pair_returns(frames, left, right):
    a = frames[left].set_index("time")["log_return"].dropna()
    b = frames[right].set_index("time")["log_return"].dropna()
    common = a.index.intersection(b.index).sort_values()
    return common, a.loc[common].to_numpy(dtype=float), b.loc[common].to_numpy(dtype=float)


def run() -> Path:
    teach_x = np.array([1, 2, 3, 4, 5], dtype=float)
    teach_y = np.array([2, 1, 4, 3, 5], dtype=float)
    got = _distance_correlation(teach_x, teach_y)
    if abs(got - 0.8583950752789521) > 1e-9:
        raise RuntimeError(f"Guide dCor {got} does not match")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    snap = load_snapshot(REPO_ROOT / SNAPSHOT_REL)
    frames = snap["frames"]
    drop_note = _prepare_frames(frames)
    dates0, x0, y0 = _pair_returns(frames, "EURUSD", "GBPUSD")
    sample_n = 30
    t0 = time.perf_counter()
    for t in range(WINDOW - 1, WINDOW - 1 + sample_n):
        _distance_correlation(x0[t - WINDOW + 1 : t + 1], y0[t - WINDOW + 1 : t + 1])
    per_window = (time.perf_counter() - t0) / sample_n
    n_windows = max(0, len(x0) - WINDOW + 1)
    estimate = per_window * n_windows * 28
    step = 1
    grid = "daily"
    if estimate > SLOW_SECONDS:
        step = STEP_IF_SLOW
        grid = f"every {STEP_IF_SLOW} trading days, carried forward"
    decision = (
        f"Timing: {per_window:.4f}s per window, about {estimate / 60:.1f} minutes "
        f"for 28 pairs on a daily grid. Grid used: {grid}."
    )
    notes_path = EXP_DIR / "NOTES.md"
    notes_path.write_text(
        "\n".join(
            [
                "# Distance correlation experiments v002",
                "",
                "Grid decision, written before the full feature pass:",
                "",
                decision,
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(decision, flush=True)

    parts = []
    for left, right in itertools.combinations(MAJOR_PAIRS, 2):
        dates, xs, ys = _pair_returns(frames, left, right)
        dcor = _rolling(xs, ys, step)
        part = pd.DataFrame(
            {
                "date": dates,
                "pair": f"{left}-{right}",
                "m14_dcor": dcor,
                "feature_asof": dates,
            }
        )
        parts.append(part.loc[np.isfinite(dcor)].reset_index(drop=True))
        print(f"{left}-{right} rows={int(np.isfinite(dcor).sum())}", flush=True)
    out = pd.concat(parts, ignore_index=True)
    if (out["feature_asof"] > out["date"]).any():
        raise RuntimeError("Feature as-of is after the row date")
    path = OUT_DIR / "features.parquet"
    out.to_parquet(path, index=False)
    notes_path.write_text(
        "\n".join(
            [
                "# Distance correlation experiments v002",
                "",
                f"Done: trailing {WINDOW}-day biased distance correlation on a {grid} grid.",
                "",
                "## Research question",
                "",
                "What is the time-t distance correlation on a trailing window that does not use future returns?",
                "",
                "## Snapshot",
                "",
                f"- Folder: `data/snapshots/{snap['manifest']['folder']}`",
                f"- {drop_note}",
                "",
                "## Parameters",
                "",
                f"- Window: {WINDOW}. Same biased dCor as v001.",
                f"- {decision}",
                "- Column: m14_dcor. A carried-forward value is the last computed value from an earlier date in the same series, so feature_asof is still the row date and the number was known then.",
                "- v001 files were not edited.",
                "",
                f"Rows written: {len(out)}.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(f"rows={len(out)}", flush=True)
    return path


if __name__ == "__main__":
    run()
