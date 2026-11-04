"""v002: expanding Pearson correlation. No forward labels."""

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
MIN_N = 252


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


def _expanding_corr(x: np.ndarray, y: np.ndarray, min_n: int) -> np.ndarray:
    n = len(x)
    cx = np.cumsum(x)
    cy = np.cumsum(y)
    cxx = np.cumsum(x * x)
    cyy = np.cumsum(y * y)
    cxy = np.cumsum(x * y)
    count = np.arange(1, n + 1, dtype=float)
    var_x = cxx - cx * cx / count
    var_y = cyy - cy * cy / count
    cov = cxy - cx * cy / count
    out = np.full(n, np.nan)
    ok = (count >= min_n) & (var_x > 0) & (var_y > 0)
    out[ok] = cov[ok] / np.sqrt(var_x[ok] * var_y[ok])
    return out


def _pair_returns(frames: dict[str, pd.DataFrame], left: str, right: str) -> tuple[pd.DatetimeIndex, np.ndarray, np.ndarray]:
    a = frames[left].set_index("time")["log_return"].dropna()
    b = frames[right].set_index("time")["log_return"].dropna()
    common = a.index.intersection(b.index).sort_values()
    return common, a.loc[common].to_numpy(dtype=float), b.loc[common].to_numpy(dtype=float)


def run() -> Path:
    x = np.array([0.01, -0.02, 0.015, 0.005, -0.01], dtype=float)
    y = np.array([0.02, -0.01, 0.01, 0.0, -0.02], dtype=float)
    got = _expanding_corr(x, y, min_n=5)[-1]
    ref = float(np.corrcoef(x, y)[0, 1])
    if abs(got - ref) > 1e-10:
        raise RuntimeError(f"Expanding Pearson {got} != {ref}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    snap = load_snapshot(REPO_ROOT / SNAPSHOT_REL)
    frames = snap["frames"]
    drop_note = _prepare_frames(frames)
    parts: list[pd.DataFrame] = []
    for left, right in itertools.combinations(MAJOR_PAIRS, 2):
        dates, xs, ys = _pair_returns(frames, left, right)
        corr = _expanding_corr(xs, ys, MIN_N)
        part = pd.DataFrame(
            {
                "date": dates,
                "pair": f"{left}-{right}",
                "m01_expanding_r": corr,
                "feature_asof": dates,
            }
        )
        parts.append(part.loc[np.isfinite(corr)].reset_index(drop=True))
    out = pd.concat(parts, ignore_index=True)
    if (out["feature_asof"] > out["date"]).any():
        raise RuntimeError("Feature as-of is after the row date")
    path = OUT_DIR / "features.parquet"
    out.to_parquet(path, index=False)
    notes = "\n".join(
        [
            "# Pearson correlation experiments v002",
            "",
            "Done: expanding Pearson r for all 28 pairs, using only returns through date t.",
            "",
            "## Research question",
            "",
            "What is the expanding-window Pearson correlation of daily log returns at each date t?",
            "",
            "## Snapshot",
            "",
            f"- Folder: `data/snapshots/{snap['manifest']['folder']}`",
            f"- {drop_note}",
            "",
            "## Parameters",
            "",
            f"- Minimum history: {MIN_N} matched log returns.",
            "- Column: m01_expanding_r. feature_asof equals the row date. No label column.",
            "- v001 files were not edited.",
            "",
            f"Rows written: {len(out)}.",
            "",
        ]
    )
    (EXP_DIR / "NOTES.md").write_text(notes, encoding="utf-8")
    print(f"rows={len(out)}", flush=True)
    return path


if __name__ == "__main__":
    run()
