"""v002: trailing 252-day partial correlation. The USD factor is fit inside the window."""

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
WINDOW = 252
USD_QUOTE = ("EURUSD", "GBPUSD", "AUDUSD", "NZDUSD")
USD_BASE = ("USDJPY", "USDCHF", "USDCAD")
CANDIDATES = USD_QUOTE + USD_BASE
CURRENCY = {
    "EURUSD": frozenset({"EUR", "USD"}),
    "GBPUSD": frozenset({"GBP", "USD"}),
    "AUDUSD": frozenset({"AUD", "USD"}),
    "NZDUSD": frozenset({"NZD", "USD"}),
    "USDJPY": frozenset({"USD", "JPY"}),
    "USDCHF": frozenset({"USD", "CHF"}),
    "USDCAD": frozenset({"USD", "CAD"}),
    "EURGBP": frozenset({"EUR", "GBP"}),
}


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


def _constituents(left: str, right: str) -> list[str]:
    blocked = (CURRENCY[left] | CURRENCY[right]) - {"USD"}
    out = []
    for symbol in CANDIDATES:
        other = CURRENCY[symbol] - {"USD"}
        if other & blocked:
            continue
        out.append(symbol)
    return out


def _strength(symbol: str, ret: pd.Series) -> pd.Series:
    if symbol in USD_QUOTE:
        return -ret
    if symbol in USD_BASE:
        return ret
    raise ValueError(symbol)


def _resid(y: np.ndarray, z: np.ndarray) -> np.ndarray:
    zc = z - z.mean()
    den = float(np.dot(zc, zc))
    if den <= 0.0:
        return y - y.mean()
    beta = float(np.dot(zc, y - y.mean()) / den)
    alpha = float(y.mean() - beta * z.mean())
    return y - alpha - beta * z


def _rolling_partial(x: np.ndarray, y: np.ndarray, z: np.ndarray, window: int) -> np.ndarray:
    n = len(x)
    out = np.full(n, np.nan)
    for t in range(window - 1, n):
        sl = slice(t - window + 1, t + 1)
        rx = _resid(x[sl], z[sl])
        ry = _resid(y[sl], z[sl])
        if float(np.std(rx)) == 0.0 or float(np.std(ry)) == 0.0:
            continue
        out[t] = float(np.corrcoef(rx, ry)[0, 1])
    return out


def run() -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    snap = load_snapshot(REPO_ROOT / SNAPSHOT_REL)
    frames = snap["frames"]
    drop_note = _prepare_frames(frames)
    strength = {}
    for symbol in CANDIDATES:
        ret = frames[symbol].set_index("time")["log_return"].dropna()
        strength[symbol] = _strength(symbol, ret)
    parts = []
    for left, right in itertools.combinations(MAJOR_PAIRS, 2):
        names = _constituents(left, right)
        a = frames[left].set_index("time")["log_return"].dropna()
        b = frames[right].set_index("time")["log_return"].dropna()
        common = a.index.intersection(b.index)
        for symbol in names:
            common = common.intersection(strength[symbol].index)
        common = common.sort_values()
        z = pd.concat([strength[symbol].loc[common] for symbol in names], axis=1).mean(axis=1)
        xs = a.loc[common].to_numpy(dtype=float)
        ys = b.loc[common].to_numpy(dtype=float)
        zs = z.to_numpy(dtype=float)
        rho = _rolling_partial(xs, ys, zs, WINDOW)
        part = pd.DataFrame(
            {
                "date": common,
                "pair": f"{left}-{right}",
                "m07_rho_partial": rho,
                "feature_asof": common,
            }
        )
        parts.append(part.loc[np.isfinite(rho)].reset_index(drop=True))
        print(f"{left}-{right} rows={int(np.isfinite(rho).sum())}", flush=True)
    out = pd.concat(parts, ignore_index=True)
    if (out["feature_asof"] > out["date"]).any():
        raise RuntimeError("Feature as-of is after the row date")
    path = OUT_DIR / "features.parquet"
    out.to_parquet(path, index=False)
    notes = "\n".join(
        [
            "# Partial and residual correlation experiments v002",
            "",
            "Done: trailing 252-day partial correlation. The leave-currency-out USD factor is estimated inside each window.",
            "",
            "## Research question",
            "",
            "What is the time-t partial correlation after removing a USD factor that uses only the same 252 days?",
            "",
            "## Snapshot",
            "",
            f"- Folder: `data/snapshots/{snap['manifest']['folder']}`",
            f"- {drop_note}",
            "",
            "## Parameters",
            "",
            "- Window: 252.",
            "- USD strength: minus the log return for EURUSD, GBPUSD, AUDUSD, NZDUSD; plus for USDJPY, USDCHF, USDCAD.",
            "- EURGBP never enters the factor. A constituent that shares a non-USD currency with either leg is left out.",
            "- Column: m07_rho_partial. No label column.",
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
