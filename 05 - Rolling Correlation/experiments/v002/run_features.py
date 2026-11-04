"""v002: rolling Pearson on all 28 pairs, with an expanding baseline."""

from __future__ import annotations

import itertools
import sys
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
WINDOWS = (20, 60, 100)
MIN_EXPAND = 252


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


def _rolling_corr(x: np.ndarray, y: np.ndarray, window: int) -> np.ndarray:
    n = len(x)
    cx = np.cumsum(x)
    cy = np.cumsum(y)
    cxx = np.cumsum(x * x)
    cyy = np.cumsum(y * y)
    cxy = np.cumsum(x * y)
    out = np.full(n, np.nan)
    idx = np.arange(window - 1, n)
    start = idx - window
    def _win(c: np.ndarray) -> np.ndarray:
        total = c[idx]
        prev = np.zeros(len(idx))
        ok = start >= 0
        prev[ok] = c[start[ok]]
        return total - prev
    sx, sy, sxx, syy, sxy = _win(cx), _win(cy), _win(cxx), _win(cyy), _win(cxy)
    var_x = sxx - sx * sx / window
    var_y = syy - sy * sy / window
    cov = sxy - sx * sy / window
    good = (var_x > 0) & (var_y > 0)
    vals = np.full(len(idx), np.nan)
    vals[good] = cov[good] / np.sqrt(var_x[good] * var_y[good])
    out[idx] = vals
    return out


def _expanding_corr(x: np.ndarray, y: np.ndarray, min_n: int) -> np.ndarray:
    n = len(x)
    count = np.arange(1, n + 1, dtype=float)
    cx = np.cumsum(x)
    cy = np.cumsum(y)
    cxx = np.cumsum(x * x)
    cyy = np.cumsum(y * y)
    cxy = np.cumsum(x * y)
    var_x = cxx - cx * cx / count
    var_y = cyy - cy * cy / count
    cov = cxy - cx * cy / count
    out = np.full(n, np.nan)
    ok = (count >= min_n) & (var_x > 0) & (var_y > 0)
    out[ok] = cov[ok] / np.sqrt(var_x[ok] * var_y[ok])
    return out


def _pair_returns(frames, left, right):
    a = frames[left].set_index("time")["log_return"].dropna()
    b = frames[right].set_index("time")["log_return"].dropna()
    common = a.index.intersection(b.index).sort_values()
    return common, a.loc[common].to_numpy(dtype=float), b.loc[common].to_numpy(dtype=float)


def run() -> Path:
    x = np.linspace(-0.02, 0.02, 30)
    y = x * 0.5
    got = _rolling_corr(x, y, 20)[-1]
    ref = float(np.corrcoef(x[-20:], y[-20:])[0, 1])
    if abs(got - ref) > 1e-10:
        raise RuntimeError(f"Rolling Pearson {got} != {ref}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    snap = load_snapshot(REPO_ROOT / SNAPSHOT_REL)
    frames = snap["frames"]
    drop_note = _prepare_frames(frames)
    parts = []
    for left, right in itertools.combinations(MAJOR_PAIRS, 2):
        dates, xs, ys = _pair_returns(frames, left, right)
        r20 = _rolling_corr(xs, ys, 20)
        r60 = _rolling_corr(xs, ys, 60)
        r100 = _rolling_corr(xs, ys, 100)
        expanding = _expanding_corr(xs, ys, MIN_EXPAND)
        gap = np.abs(r20 - expanding)
        part = pd.DataFrame(
            {
                "date": dates,
                "pair": f"{left}-{right}",
                "m05_r20": r20,
                "m05_r60": r60,
                "m05_r100": r100,
                "m05_abs_gap": gap,
                "feature_asof": dates,
            }
        )
        parts.append(part.loc[np.isfinite(r20)].reset_index(drop=True))
    out = pd.concat(parts, ignore_index=True)
    if (out["feature_asof"] > out["date"]).any():
        raise RuntimeError("Feature as-of is after the row date")
    path = OUT_DIR / "features.parquet"
    out.to_parquet(path, index=False)
    notes = "\n".join(
        [
            "# Rolling correlation experiments v002",
            "",
            "Done: rolling Pearson at 20, 60, and 100 days for all 28 pairs, "
            "with |r_20 - expanding Pearson| using only data through t.",
            "",
            "## Research question",
            "",
            "What are the causal rolling correlations on every major pair, not only the 17-pair v001 watchlist?",
            "",
            "## Snapshot",
            "",
            f"- Folder: `data/snapshots/{snap['manifest']['folder']}`",
            f"- {drop_note}",
            "",
            "## Parameters",
            "",
            "- Windows: 20, 60, 100.",
            f"- Expanding baseline starts at {MIN_EXPAND} observations. It is not the full-sample r from v001.",
            "- Columns: m05_r20, m05_r60, m05_r100, m05_abs_gap. No label column.",
            "- v001 files were not edited.",
            "",
            f"Rows written: {len(out)}.",
            "",
        ]
    )
    (EXP_DIR / "NOTES.md").write_text(notes, encoding="utf-8")
    print(f"rows={len(out)} pairs={out['pair'].nunique()}", flush=True)
    return path


if __name__ == "__main__":
    run()
