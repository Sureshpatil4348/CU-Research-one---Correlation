"""v003: trailing 252-day lower-tail excess over a Gaussian benchmark."""

from __future__ import annotations

import itertools
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
WINDOW = 252
ALPHA = 0.05


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


def _gaussian_cdf(pearson_r: float) -> float:
    r = float(np.clip(pearson_r, -0.999999, 0.999999))
    q = float(stats.norm.ppf(ALPHA))
    cov = np.array([[1.0, r], [r, 1.0]])
    joint = float(stats.multivariate_normal.cdf([q, q], mean=np.zeros(2), cov=cov))
    return joint / ALPHA


_R_GRID = np.linspace(-0.999, 0.999, 1999)
_BENCH_GRID = np.array([_gaussian_cdf(float(r)) for r in _R_GRID])


def _gaussian(pearson_r: float) -> float:
    return float(np.interp(float(np.clip(pearson_r, -0.999, 0.999)), _R_GRID, _BENCH_GRID))


def _lower_excess(x: np.ndarray, y: np.ndarray) -> float:
    if float(np.std(x)) == 0.0 or float(np.std(y)) == 0.0:
        return float("nan")
    u = stats.rankdata(x, method="average") / (len(x) + 1.0)
    v = stats.rankdata(y, method="average") / (len(y) + 1.0)
    u_tail = u <= ALPHA
    v_tail = v <= ALPHA
    den_u = int(u_tail.sum())
    den_v = int(v_tail.sum())
    joint = int((u_tail & v_tail).sum())
    if den_u == 0 or den_v == 0:
        return float("nan")
    l_hat = 0.5 * (joint / den_u + joint / den_v)
    r = float(np.corrcoef(x, y)[0, 1])
    return l_hat - _gaussian(r)


def _rolling(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    n = len(x)
    out = np.full(n, np.nan)
    for t in range(WINDOW - 1, n):
        sl = slice(t - WINDOW + 1, t + 1)
        out[t] = _lower_excess(x[sl], y[sl])
    return out


def run() -> Path:
    if abs(_gaussian(0.0) - ALPHA) > 1e-6:
        raise RuntimeError("Gaussian benchmark at r=0 should equal alpha")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    snap = load_snapshot(REPO_ROOT / SNAPSHOT_REL)
    frames = snap["frames"]
    drop_note = _prepare_frames(frames)
    parts = []
    for left, right in itertools.combinations(MAJOR_PAIRS, 2):
        a = frames[left].set_index("time")["log_return"].dropna()
        b = frames[right].set_index("time")["log_return"].dropna()
        common = a.index.intersection(b.index).sort_values()
        excess = _rolling(a.loc[common].to_numpy(dtype=float), b.loc[common].to_numpy(dtype=float))
        part = pd.DataFrame(
            {
                "date": common,
                "pair": f"{left}-{right}",
                "m19_excess_lower": excess,
                "feature_asof": common,
            }
        )
        parts.append(part.loc[np.isfinite(excess)].reset_index(drop=True))
        print(f"{left}-{right} rows={int(np.isfinite(excess).sum())}", flush=True)
    out = pd.concat(parts, ignore_index=True)
    if (out["feature_asof"] > out["date"]).any():
        raise RuntimeError("Feature as-of is after the row date")
    path = OUT_DIR / "features.parquet"
    out.to_parquet(path, index=False)
    notes = "\n".join(
        [
            "# Tail dependence experiments v003",
            "",
            "Done: trailing 252-day lower-tail excess. Ranks and the Gaussian benchmark use only that window.",
            "",
            "## Research question",
            "",
            "At each date t, how far is the lower-tail frequency from the Gaussian co-exceedance implied by the window Pearson r?",
            "",
            "## Snapshot",
            "",
            f"- Folder: `data/snapshots/{snap['manifest']['folder']}`",
            f"- {drop_note}",
            "",
            "## Parameters",
            "",
            f"- Window {WINDOW}, alpha {ALPHA}. Uniforms are rank/(n+1) inside the window.",
            "- L_hat is the average of the two conditioning directions. Excess = L_hat minus the Gaussian benchmark.",
            "- The benchmark is the bivariate-normal co-exceedance, read from a correlation grid with step 0.001.",
            "- Column: m19_excess_lower. No label column.",
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
