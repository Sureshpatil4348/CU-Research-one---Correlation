"""v003: trailing network distance and PC1, plus a quarterly causal TCI. EURGBP is excluded."""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from statsmodels.tsa.api import VAR

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from shared.mt5_data import MAJOR_PAIRS, load_snapshot

SNAPSHOT_REL = Path("data/snapshots/2026-11-03_majors_alpari_D1")
EXP_DIR = Path(__file__).resolve().parent
OUT_DIR = EXP_DIR / "outputs"
PANEL = [name for name in MAJOR_PAIRS if name != "EURGBP"]
WINDOW = 252
VAR_MAXLAGS = 10
FEVD_HORIZON = 10


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


def _panel(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    series = [frames[name].set_index("time")["log_return"].rename(name).dropna() for name in PANEL]
    return pd.concat(series, axis=1, join="inner").dropna().sort_index()


def _generalized_fevd(var_res, horizon: int) -> np.ndarray:
    sigma = np.asarray(var_res.sigma_u, dtype=float)
    n = sigma.shape[0]
    ma = np.asarray(var_res.ma_rep(maxn=horizon), dtype=float)
    theta = np.zeros((n, n), dtype=float)
    sig_diag = np.diag(sigma).copy()
    sig_diag[sig_diag <= 0] = 1e-18
    for i in range(n):
        denom = 0.0
        for h in range(horizon + 1):
            row = ma[h][i, :]
            denom += float(row @ sigma @ row)
        if denom <= 0:
            denom = 1e-18
        for j in range(n):
            num = 0.0
            ej = np.zeros(n)
            ej[j] = 1.0
            for h in range(horizon + 1):
                val = float(ma[h][i, :] @ sigma @ ej)
                num += (val * val) / sig_diag[j]
            theta[i, j] = num / denom
    row_sums = theta.sum(axis=1, keepdims=True)
    row_sums[row_sums <= 0] = 1.0
    return theta / row_sums


def _tci(panel: pd.DataFrame) -> float:
    demeaned = panel - panel.mean()
    model = VAR(demeaned)
    selected = model.select_order(maxlags=min(VAR_MAXLAGS, max(1, len(panel) // 20)))
    lag_p = int(selected.bic)
    if lag_p < 1:
        lag_p = 1
    theta = _generalized_fevd(model.fit(lag_p), FEVD_HORIZON)
    n = theta.shape[0]
    return 100.0 * float(np.sum(theta) - np.trace(theta)) / n


def _quarter_ends(index: pd.DatetimeIndex) -> list[int]:
    ends: list[int] = []
    for i, ts in enumerate(index):
        last = i + 1 == len(index)
        if last or index[i + 1].year != ts.year or index[i + 1].quarter != ts.quarter:
            if i + 1 >= WINDOW:
                ends.append(i)
    return ends


def run() -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    snap = load_snapshot(REPO_ROOT / SNAPSHOT_REL)
    frames = snap["frames"]
    drop_note = _prepare_frames(frames)
    panel = _panel(frames)
    values = panel.to_numpy(dtype=float)
    n, k = values.shape
    pc1 = np.full(n, np.nan)
    pair_names = [f"{a}-{b}" for i, a in enumerate(PANEL) for b in PANEL[i + 1 :]]
    pair_pos = []
    for i in range(k):
        for j in range(i + 1, k):
            pair_pos.append((i, j))
    dij = {name: np.full(n, np.nan) for name in pair_names}
    for t in range(WINDOW - 1, n):
        corr = np.corrcoef(values[t - WINDOW + 1 : t + 1], rowvar=False)
        eig = np.linalg.eigvalsh(corr)
        pc1[t] = float(eig[-1] / eig.sum())
        for name, (i, j) in zip(pair_names, pair_pos):
            rho = float(corr[i, j])
            dij[name][t] = math.sqrt(max(0.0, 2.0 * (1.0 - rho)))
    tci = np.full(n, np.nan)
    ends = _quarter_ends(panel.index)
    for pos, end_i in enumerate(ends):
        try:
            value = _tci(panel.iloc[: end_i + 1])
        except Exception as exc:
            print(f"TCI failed at {panel.index[end_i].date()}: {exc}", flush=True)
            continue
        next_i = ends[pos + 1] if pos + 1 < len(ends) else n
        tci[end_i:next_i] = value
        print(f"TCI {panel.index[end_i].date()} {value:.3f}", flush=True)

    parts = []
    for name in pair_names:
        part = pd.DataFrame(
            {
                "date": panel.index,
                "pair": name,
                "m28_d_ij": dij[name],
                "m28_pc1_share": pc1,
                "m28_tci": tci,
                "feature_asof": panel.index,
            }
        )
        parts.append(part.loc[np.isfinite(dij[name])].reset_index(drop=True))
    out = pd.concat(parts, ignore_index=True)
    if (out["feature_asof"] > out["date"]).any():
        raise RuntimeError("Feature as-of is after the row date")
    path = OUT_DIR / "features.parquet"
    out.to_parquet(path, index=False)
    notes = "\n".join(
        [
            "# Networks, PCA, and connectedness experiments v003",
            "",
            "Done: trailing 252-day d_ij and PC1 share on the seven majors, plus a quarterly TCI held flat until the next quarter-end.",
            "",
            "## Research question",
            "",
            "What network and connectedness numbers are known at date t without EURGBP and without future returns?",
            "",
            "## Snapshot",
            "",
            f"- Folder: `data/snapshots/{snap['manifest']['folder']}`",
            f"- {drop_note}",
            "",
            "## Parameters",
            "",
            "- Panel: EURUSD, GBPUSD, AUDUSD, NZDUSD, USDJPY, USDCHF, USDCAD.",
            f"- d_ij = sqrt(2*(1-rho)) and PC1 variance share use the last {WINDOW} days.",
            "- TCI uses a BIC VAR (max lag 10, or less when the sample is short) and GFEVD horizon 10.",
            "- A quarter-end fit uses data through that date and is held through the day before the next quarter-end.",
            "- Columns: m28_d_ij, m28_pc1_share, m28_tci. No label column. EURGBP pairs are absent.",
            "- v001 and v002 files were not edited.",
            "",
            f"Rows written: {len(out)}. Quarter-end refits: {len(ends)}.",
            "",
        ]
    )
    (EXP_DIR / "NOTES.md").write_text(notes, encoding="utf-8")
    print(f"rows={len(out)}", flush=True)
    return path


if __name__ == "__main__":
    run()
