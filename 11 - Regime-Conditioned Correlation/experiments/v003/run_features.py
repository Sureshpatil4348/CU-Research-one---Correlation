"""v003: trailing 252-day Forbes-Rigobon stress gap. States use only data through t."""

from __future__ import annotations

import itertools
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from shared.mt5_data import MAJOR_PAIRS, load_snapshot

SNAPSHOT_REL = Path("data/snapshots/2026-11-03_majors_alpari_D1")
EXP_DIR = Path(__file__).resolve().parent
OUT_DIR = EXP_DIR / "outputs"
RV_WINDOW = 20
RV_HISTORY = 252
STRESS_PCT = 75.0
TRAIL = 252
MIN_STATE = 30


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


def _regime_panel(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    series = {name: frames[name].set_index("time")["log_return"].dropna() for name in MAJOR_PAIRS}
    common = series[MAJOR_PAIRS[0]].index
    for name in MAJOR_PAIRS[1:]:
        common = common.intersection(series[name].index)
    common = common.sort_values()
    ret = pd.DataFrame({name: series[name].loc[common] for name in MAJOR_PAIRS})
    turb = ret.abs().mean(axis=1).to_numpy(dtype=float)
    n = len(turb)
    rv = np.full(n, np.nan)
    for t in range(RV_WINDOW, n):
        rv[t] = float(np.mean(turb[t - RV_WINDOW : t]))
    state = np.array([""] * n, dtype=object)
    for t in range(RV_WINDOW + RV_HISTORY, n):
        past = rv[t - RV_HISTORY : t]
        if np.isnan(rv[t]) or np.any(np.isnan(past)):
            continue
        thresh = float(np.percentile(past, STRESS_PCT))
        state[t] = "stress" if rv[t] > thresh else "quiet"
    ret["state"] = state
    return ret


def _pearson(x: np.ndarray, y: np.ndarray) -> float:
    if len(x) < 3 or float(np.std(x)) == 0.0 or float(np.std(y)) == 0.0:
        return float("nan")
    return float(stats.pearsonr(x, y).statistic)


def _forbes(rho: float, delta: float) -> float:
    if not np.isfinite(rho) or not np.isfinite(delta):
        return float("nan")
    inside = 1.0 + delta * (1.0 - rho * rho)
    if inside <= 1e-12:
        return float("nan")
    return float(rho / math.sqrt(inside))


def _trail_gap(x: np.ndarray, y: np.ndarray, state: np.ndarray) -> np.ndarray:
    n = len(x)
    out = np.full(n, np.nan)
    for t in range(TRAIL - 1, n):
        sl = slice(t - TRAIL + 1, t + 1)
        st = state[sl]
        xs = x[sl]
        ys = y[sl]
        quiet = st == "quiet"
        stress = st == "stress"
        if int(quiet.sum()) < MIN_STATE or int(stress.sum()) < MIN_STATE:
            continue
        rho_q = _pearson(xs[quiet], ys[quiet])
        rho_s = _pearson(xs[stress], ys[stress])
        var_q_x = float(np.var(xs[quiet], ddof=1))
        var_s_x = float(np.var(xs[stress], ddof=1))
        var_q_y = float(np.var(ys[quiet], ddof=1))
        var_s_y = float(np.var(ys[stress], ddof=1))
        if var_q_x <= 0.0 or var_q_y <= 0.0:
            continue
        delta = 0.5 * ((var_s_x / var_q_x - 1.0) + (var_s_y / var_q_y - 1.0))
        rho_adj = _forbes(rho_s, delta)
        out[t] = rho_adj - rho_q
    return out


def run() -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    snap = load_snapshot(REPO_ROOT / SNAPSHOT_REL)
    frames = snap["frames"]
    drop_note = _prepare_frames(frames)
    panel = _regime_panel(frames)
    parts = []
    for left, right in itertools.combinations(MAJOR_PAIRS, 2):
        sub = panel[[left, right, "state"]].dropna()
        gap = _trail_gap(
            sub[left].to_numpy(dtype=float),
            sub[right].to_numpy(dtype=float),
            sub["state"].to_numpy(),
        )
        part = pd.DataFrame(
            {
                "date": sub.index,
                "pair": f"{left}-{right}",
                "m11_adj_gap": gap,
                "feature_asof": sub.index,
            }
        )
        parts.append(part.loc[np.isfinite(gap)].reset_index(drop=True))
        print(f"{left}-{right} rows={int(np.isfinite(gap).sum())}", flush=True)
    out = pd.concat(parts, ignore_index=True)
    if (out["feature_asof"] > out["date"]).any():
        raise RuntimeError("Feature as-of is after the row date")
    path = OUT_DIR / "features.parquet"
    out.to_parquet(path, index=False)
    notes = "\n".join(
        [
            "# Regime-conditioned correlation experiments v003",
            "",
            "Done: trailing 252-day Forbes-Rigobon adjusted stress-minus-quiet gap. The state at t uses only RV history before t.",
            "",
            "## Research question",
            "",
            "What is the time-t adjusted correlation gap between quiet and stress days inside the last 252 days?",
            "",
            "## Snapshot",
            "",
            f"- Folder: `data/snapshots/{snap['manifest']['folder']}`",
            f"- {drop_note}",
            "",
            "## Parameters",
            "",
            "- State rule matches v001: turb is the eight-major mean absolute log return; RV is the prior 20 turb days; stress when RV exceeds the 75th percentile of the prior 252 RV values.",
            f"- Feature window: {TRAIL} days. Missing if either state has fewer than {MIN_STATE} days in the window.",
            "- Adjustment matches v002: rho_stress / sqrt(1 + delta * (1 - rho_stress^2)) - rho_quiet, with delta the average variance ratio minus one.",
            "- Column: m11_adj_gap. No label column.",
            "- v001 and v002 files were not edited.",
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
