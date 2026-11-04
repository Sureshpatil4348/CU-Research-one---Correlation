"""v002: PCA and VAR/GFEVD on the seven majors, EURGBP dropped."""

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
PANEL7 = [name for name in MAJOR_PAIRS if name != "EURGBP"]
VAR_MAXLAGS = 10
FEVD_HORIZON = 10
V001_PC8 = 0.004606


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


def _return_panel(frames: dict[str, pd.DataFrame], names: list[str]) -> pd.DataFrame:
    series = [frames[name].set_index("time")["log_return"].rename(name) for name in names]
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


def _system_metrics(panel: pd.DataFrame) -> dict[str, object]:
    corr = panel.corr(method="pearson")
    names = list(panel.columns)
    n = len(names)
    eigvals = np.linalg.eigvalsh(corr.to_numpy(dtype=float))[::-1]
    pca = pd.DataFrame(
        {
            "component": [f"PC{k + 1}" for k in range(n)],
            "eigenvalue": eigvals,
            "variance_share": eigvals / eigvals.sum(),
        }
    )
    demeaned = panel - panel.mean()
    var_model = VAR(demeaned)
    selected = var_model.select_order(maxlags=VAR_MAXLAGS)
    lag_p = int(selected.bic)
    if lag_p < 1:
        lag_p = 1
    var_res = var_model.fit(lag_p)
    theta = _generalized_fevd(var_res, FEVD_HORIZON)
    theta_df = pd.DataFrame(theta, index=names, columns=names)
    tci = 100.0 * float(np.sum(theta) - np.trace(theta)) / n
    to_others = 100.0 * (theta.sum(axis=0) - np.diag(theta))
    from_others = 100.0 * (theta.sum(axis=1) - np.diag(theta))
    connectedness = pd.DataFrame(
        {
            "symbol": names,
            "from_others": from_others,
            "to_others": to_others,
            "net": to_others - from_others,
            "own_share": 100.0 * np.diag(theta),
        }
    )
    return {
        "corr": corr,
        "pca": pca,
        "theta": theta_df,
        "tci": tci,
        "lag_p": lag_p,
        "connectedness": connectedness,
        "n_obs": len(panel),
    }


def _markdown_table(frame: pd.DataFrame) -> str:
    show = frame.copy()
    for col in show.columns:
        if pd.api.types.is_float_dtype(show[col]):
            show[col] = show[col].map(lambda v: "" if pd.isna(v) else f"{v:.6g}")
    header = "| " + " | ".join(str(c) for c in show.columns) + " |"
    rule = "| " + " | ".join("---" for _ in show.columns) + " |"
    body = ["| " + " | ".join(str(v) for v in row) + " |" for row in show.itertuples(index=False, name=None)]
    return "\n".join([header, rule, *body])


def run() -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    snap = load_snapshot(REPO_ROOT / SNAPSHOT_REL)
    frames, drop_note = _prepare_frames(snap["frames"])
    panel8 = _return_panel(frames, list(MAJOR_PAIRS))
    identity = panel8["EURUSD"] - panel8["GBPUSD"]
    redundancy_r = float(panel8["EURGBP"].corr(identity))
    panel7 = panel8[PANEL7]
    sysm = _system_metrics(panel7)
    smallest = float(sysm["pca"]["eigenvalue"].iloc[-1])
    if smallest <= V001_PC8:
        raise RuntimeError(
            f"Seven-asset smallest eigenvalue {smallest} is not above v001 PC8 {V001_PC8}"
        )

    corr = sysm["corr"]
    theta = sysm["theta"]
    pair_rows = []
    for i, left in enumerate(PANEL7):
        for right in PANEL7[i + 1 :]:
            rho = float(corr.loc[left, right])
            pair_rows.append(
                {
                    "pair": f"{left}-{right}",
                    "rho": rho,
                    "d_ij": math.sqrt(2.0 * (1.0 - rho)),
                    "theta_L_to_R": float(theta.loc[left, right]),
                    "theta_R_to_L": float(theta.loc[right, left]),
                }
            )
    pairs = pd.DataFrame(pair_rows)
    with pd.ExcelWriter(OUT_DIR / "index.xlsx") as writer:
        sysm["pca"].to_excel(writer, index=False, sheet_name="pca")
        sysm["connectedness"].to_excel(writer, index=False, sheet_name="connectedness")
        pairs.to_excel(writer, index=False, sheet_name="pairs")
        pd.DataFrame(
            [
                {
                    "v001_pc8": V001_PC8,
                    "smallest_eigenvalue": smallest,
                    "tci": sysm["tci"],
                    "lag_p": sysm["lag_p"],
                    "n_obs": sysm["n_obs"],
                    "eurgbp_vs_eurusd_minus_gbpusd": redundancy_r,
                }
            ]
        ).to_excel(writer, index=False, sheet_name="summary")

    done = (
        f"Done: system PCA and VAR/GFEVD rerun without EURGBP; "
        f"smallest eigenvalue {smallest:.6f} versus v001 PC8 {V001_PC8:.6f}; "
        f"TCI {float(sysm['tci']):.4f}."
    )
    notes = "\n".join(
        [
            "# Networks, PCA, and connectedness experiments v002",
            "",
            done,
            "",
            "## Research question",
            "",
            "On the seven majors that remain after dropping EURGBP, what are the "
            "PCA eigenvalues and the Diebold-Yilmaz TCI?",
            "",
            "## Snapshot",
            "",
            f"- Folder: `data/snapshots/{snap['manifest']['folder']}`",
            f"- {drop_note}",
            "",
            "## Parameters",
            "",
            "- Panel: EURUSD, GBPUSD, AUDUSD, NZDUSD, USDJPY, USDCHF, USDCAD. EURGBP is dropped, not orthogonalised.",
            f"- n_obs={sysm['n_obs']}.",
            "- VAR on demeaned returns; lag = BIC among 1..10; GFEVD H=10. Same algebra as v001.",
            f"- v001 PC8 eigenvalue, copied from the v001 NOTES and not refit here: {V001_PC8:.6f}.",
            f"- corr(EURGBP, EURUSD log return - GBPUSD log return) = {redundancy_r:.6f} on the eight-name inner join.",
            "- v001 files were not edited.",
            "",
            "## System PCA",
            "",
            _markdown_table(sysm["pca"]),
            "",
            "## System connectedness (percent)",
            "",
            _markdown_table(sysm["connectedness"]),
            "",
            f"System TCI (H=10): {float(sysm['tci']):.6f}. BIC lag: {sysm['lag_p']}.",
            "",
            "## Cross-pair conclusion",
            "",
            f"EURGBP is nearly EURUSD minus GBPUSD (correlation {redundancy_r:.4f}), "
            f"which is why v001 PC8 was {V001_PC8:.6f}.",
            f"Without that leg the smallest eigenvalue is {smallest:.6f}.",
            "This is not a trading signal.",
            "",
        ]
    )
    (EXP_DIR / "NOTES.md").write_text(notes, encoding="utf-8")
    print(done, flush=True)
    print(f"redundancy r={redundancy_r:.6f}", flush=True)
    return OUT_DIR / "index.xlsx"


if __name__ == "__main__":
    run()
