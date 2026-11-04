"""v002: Forbes-Rigobon adjustment and a block bootstrap of the stress gap."""

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
BLOCK = 20
N_BOOT = 500
SEED = 20261103


def _prepare_frames(frames: dict[str, pd.DataFrame]) -> tuple[dict[str, pd.DataFrame], str]:
    cleaned: dict[str, pd.DataFrame] = {}
    drop_note = "No unfinished last bar was dropped."
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
        cleaned[name] = work
    if drop_date is not None:
        drop_note = (
            f"Dropped unfinished last bar dated {drop_date.date().isoformat()} "
            "UTC after a tick-volume check against the prior complete day."
        )
    return cleaned, drop_note


def _build_regime(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
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
    regime = pd.DataFrame({"time": common, "state": state}).set_index("time")
    return ret.join(regime)


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


def _bootstrap_gap(
    x: np.ndarray,
    y: np.ndarray,
    stress: np.ndarray,
    rng: np.random.Generator,
) -> tuple[float, float]:
    n = len(x)
    n_blocks = int(math.ceil(n / BLOCK))
    gaps = np.empty(N_BOOT)
    offsets = np.arange(BLOCK)
    for b in range(N_BOOT):
        starts = rng.integers(0, n, size=n_blocks)
        idx = (starts[:, None] + offsets[None, :]) % n
        idx = idx.ravel()[:n]
        sb = stress[idx]
        xb = x[idx]
        yb = y[idx]
        rq = _pearson(xb[~sb], yb[~sb])
        rs = _pearson(xb[sb], yb[sb])
        gaps[b] = rs - rq
    valid = gaps[np.isfinite(gaps)]
    if len(valid) < 50:
        return float("nan"), float("nan")
    return float(np.percentile(valid, 2.5)), float(np.percentile(valid, 97.5))


def _markdown_table(frame: pd.DataFrame) -> str:
    show = frame.copy()
    for col in show.columns:
        if pd.api.types.is_float_dtype(show[col]):
            show[col] = show[col].map(lambda v: "" if pd.isna(v) else f"{v:.6g}")
    header = "| " + " | ".join(show.columns) + " |"
    rule = "| " + " | ".join("---" for _ in show.columns) + " |"
    body = ["| " + " | ".join(str(v) for v in row) + " |" for row in show.itertuples(index=False, name=None)]
    return "\n".join([header, rule, *body])


def run() -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    snap = load_snapshot(REPO_ROOT / SNAPSHOT_REL)
    frames, drop_note = _prepare_frames(snap["frames"])
    panel = _build_regime(frames)
    rng = np.random.default_rng(SEED)
    rows: list[dict[str, object]] = []
    for left, right in itertools.combinations(MAJOR_PAIRS, 2):
        sub = panel.loc[panel["state"].isin(["quiet", "stress"]), [left, right, "state"]].dropna()
        x = sub[left].to_numpy(dtype=float)
        y = sub[right].to_numpy(dtype=float)
        stress = sub["state"].to_numpy() == "stress"
        quiet = ~stress
        rho_q = _pearson(x[quiet], y[quiet])
        rho_s = _pearson(x[stress], y[stress])
        var_q_x = float(np.var(x[quiet], ddof=1))
        var_s_x = float(np.var(x[stress], ddof=1))
        var_q_y = float(np.var(y[quiet], ddof=1))
        var_s_y = float(np.var(y[stress], ddof=1))
        delta_x = var_s_x / var_q_x - 1.0 if var_q_x > 0 else float("nan")
        delta_y = var_s_y / var_q_y - 1.0 if var_q_y > 0 else float("nan")
        delta = 0.5 * (delta_x + delta_y)
        rho_adj = _forbes(rho_s, delta)
        lo, hi = _bootstrap_gap(x, y, stress, rng)
        raw_gap = rho_s - rho_q
        rows.append(
            {
                "pair": f"{left}-{right}",
                "n_quiet": int(quiet.sum()),
                "n_stress": int(stress.sum()),
                "rho_quiet": rho_q,
                "rho_stress": rho_s,
                "delta": delta,
                "rho_stress_adj": rho_adj,
                "raw_gap": raw_gap,
                "adj_gap": rho_adj - rho_q,
                "boot_low": lo,
                "boot_high": hi,
                "raw_gap_excludes_0": bool(np.isfinite(lo) and np.isfinite(hi) and (hi < 0 or lo > 0)),
            }
        )
        print(f"{left}-{right} raw_gap={raw_gap:.4f} adj_gap={rho_adj - rho_q:.4f}", flush=True)

    index = pd.DataFrame(rows)
    n_sig = int(index["raw_gap_excludes_0"].sum())
    done = (
        "Done: quiet/stress table reports Forbes-Rigobon adjusted gaps and a "
        f"95% circular block-bootstrap interval for the raw gap ({n_sig} of 28 intervals exclude 0)."
    )
    index.to_excel(OUT_DIR / "index.xlsx", index=False, sheet_name="index")
    show = [
        "pair",
        "n_quiet",
        "n_stress",
        "rho_quiet",
        "rho_stress",
        "rho_stress_adj",
        "adj_gap",
        "boot_low",
        "boot_high",
        "raw_gap_excludes_0",
    ]
    aud = index.loc[index["pair"] == "AUDUSD-USDJPY"].iloc[0]
    notes = "\n".join(
        [
            "# Regime-conditioned correlation experiments v002",
            "",
            done,
            "",
            "## Research question",
            "",
            "After a Forbes-Rigobon volatility adjustment, which stress-minus-quiet "
            "correlation gaps remain large, and which raw gaps does a block bootstrap reject?",
            "",
            "## Snapshot",
            "",
            f"- Folder: `data/snapshots/{snap['manifest']['folder']}`",
            f"- {drop_note}",
            "",
            "## Parameters",
            "",
            "- Same look-ahead-free turbulence rule as v001: RV is the prior 20 turb days; "
            "stress when RV exceeds the 75th percentile of the prior 252 RV values.",
            "- delta is the average of the two legs' (stress variance / quiet variance - 1).",
            "- rho_stress_adj = rho_stress / sqrt(1 + delta * (1 - rho_stress^2)).",
            f"- Circular block bootstrap of the raw stress-minus-quiet gap, block={BLOCK}, "
            f"draws={N_BOOT}, seed={SEED}. Interval is the 2.5 and 97.5 percentiles.",
            "- v001 files were not edited.",
            "",
            "## Index",
            "",
            _markdown_table(index[show]),
            "",
            "## Cross-pair conclusion",
            "",
            (
                f"AUDUSD-USDJPY raw gap is {float(aud['raw_gap']):.4f}; "
                f"adjusted gap is {float(aud['adj_gap']):.4f}; "
                f"bootstrap interval [{float(aud['boot_low']):.4f}, {float(aud['boot_high']):.4f}]."
            ),
            f"Raw-gap intervals that exclude 0: {n_sig} of 28.",
            "A larger raw stress correlation can be a volatility effect. The adjusted gap is the bias check.",
            "This is not a trading signal.",
            "",
        ]
    )
    (EXP_DIR / "NOTES.md").write_text(notes, encoding="utf-8")
    print(done, flush=True)
    return OUT_DIR / "index.xlsx"


if __name__ == "__main__":
    run()
