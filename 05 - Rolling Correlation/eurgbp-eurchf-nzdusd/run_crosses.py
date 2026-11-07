"""Rolling Pearson r (W=20/60/100) for EURGBP-EURCHF, EURGBP-NZDUSD, EURCHF-NZDUSD.

EURCHF is built as EURUSD close * USDCHF close on matched dates. v001 untouched.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from shared.mt5_data import load_snapshot

SNAPSHOT_REL = Path("data/snapshots/2026-11-03_majors_alpari_D1")
EXP_DIR = Path(__file__).resolve().parent
OUT_DIR = EXP_DIR / "outputs"
WINDOWS = (20, 60, 100)

PAIRS: list[tuple[str, str]] = [
    ("EURGBP", "EURCHF"),
    ("EURGBP", "NZDUSD"),
    ("EURCHF", "NZDUSD"),
]


def _drop_unfinished(frame: pd.DataFrame) -> tuple[pd.DataFrame, object | None]:
    work = frame.copy()
    work["time"] = pd.to_datetime(work["time"], utc=True)
    work = work.sort_values("time").reset_index(drop=True)
    drop_date = None
    if len(work) >= 2:
        last_tv = float(work.iloc[-1]["tick_volume"])
        prev_tv = float(work.iloc[-2]["tick_volume"])
        if prev_tv > 0 and last_tv < 0.5 * prev_tv:
            drop_date = work.iloc[-1]["time"]
            work = work.iloc[:-1].reset_index(drop=True)
    return work, drop_date


def _with_log_return(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    out["log_return"] = np.log(out["close"] / out["close"].shift(1))
    return out


def _build_eurchf(eurusd: pd.DataFrame, usdchf: pd.DataFrame) -> pd.DataFrame:
    a = eurusd.set_index("time")
    b = usdchf.set_index("time")
    common = a.index.intersection(b.index).sort_values()
    close = a.loc[common, "close"] * b.loc[common, "close"]
    out = pd.DataFrame({"time": common, "close": close.values})
    out = _with_log_return(out)
    return out.reset_index(drop=True)


def _pair_table(
    left: pd.DataFrame,
    right: pd.DataFrame,
    left_name: str,
    right_name: str,
) -> pd.DataFrame:
    a = left.set_index("time")
    b = right.set_index("time")
    common = a.index.intersection(b.index).sort_values()
    table = pd.DataFrame(
        {
            "time": common,
            f"{left_name}_log_return": a.loc[common, "log_return"].values,
            f"{right_name}_log_return": b.loc[common, "log_return"].values,
        }
    )
    table = table.dropna(
        subset=[f"{left_name}_log_return", f"{right_name}_log_return"]
    )
    return table.reset_index(drop=True)


def _add_rolling(table: pd.DataFrame, left: str, right: str) -> pd.DataFrame:
    out = table.copy()
    x = out[f"{left}_log_return"]
    y = out[f"{right}_log_return"]
    for w in WINDOWS:
        out[f"r_{w}"] = x.rolling(w).corr(y)
    return out


def _save_rolling(
    table: pd.DataFrame,
    left: str,
    right: str,
    out_path: Path,
) -> None:
    times = pd.to_datetime(table["time"], utc=True)
    fig, ax = plt.subplots(figsize=(10, 4.5))
    for w, color in zip(WINDOWS, ("#1f77b4", "#ff7f0e", "#2ca02c")):
        ax.plot(times, table[f"r_{w}"], color=color, linewidth=0.9, label=f"r_{w}")
    ax.axhline(0, color="gray", linewidth=0.6)
    ax.set_ylim(-1.05, 1.05)
    ax.set_title(f"Rolling Pearson r: {left} and {right}")
    ax.set_ylabel("rolling r")
    ax.legend(loc="upper left")
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=120)
    plt.close(fig)


def main() -> None:
    snap = load_snapshot(REPO_ROOT / SNAPSHOT_REL)
    frames = snap["frames"]

    drop_dates = []
    cleaned: dict[str, pd.DataFrame] = {}
    for name in ("EURUSD", "USDCHF", "EURGBP", "NZDUSD"):
        work, drop_date = _drop_unfinished(frames[name])
        if drop_date is not None:
            drop_dates.append(drop_date)
        cleaned[name] = _with_log_return(work)

    cleaned["EURCHF"] = _build_eurchf(cleaned["EURUSD"], cleaned["USDCHF"])

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for left, right in PAIRS:
        table = _pair_table(cleaned[left], cleaned[right], left, right)
        table = _add_rolling(table, left, right)
        stem = f"{left}-{right}_Rolling_D1_rolling.png"
        _save_rolling(table, left, right, OUT_DIR / stem)
        print(f"wrote {stem} n={len(table)}")

    if drop_dates:
        print(
            "Dropped unfinished last bar dated "
            f"{pd.Timestamp(drop_dates[0]).date().isoformat()} UTC."
        )


if __name__ == "__main__":
    main()
