"""v002: Gaussian co-exceedance benchmark for empirical tail frequencies."""

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
V001_INDEX = EXP_DIR.parent / "v001" / "outputs" / "index.xlsx"
ALPHA = 0.05


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


def _pair_returns(frames: dict[str, pd.DataFrame], left: str, right: str) -> tuple[np.ndarray, np.ndarray]:
    a = frames[left].set_index("time")["log_return"].dropna()
    b = frames[right].set_index("time")["log_return"].dropna()
    common = a.index.intersection(b.index).sort_values()
    return a.loc[common].to_numpy(dtype=float), b.loc[common].to_numpy(dtype=float)


def _l_hat(u: np.ndarray, v: np.ndarray, alpha: float, lower: bool, cond_on_v: bool) -> float:
    if lower:
        u_tail = u <= alpha
        v_tail = v <= alpha
    else:
        u_tail = u >= (1.0 - alpha)
        v_tail = v >= (1.0 - alpha)
    denom_mask = v_tail if cond_on_v else u_tail
    denom = int(np.sum(denom_mask))
    num = int(np.sum(u_tail & v_tail))
    if denom == 0:
        return float("nan")
    return float(num / denom)


def gaussian_coexceedance(pearson_r: float, alpha: float = ALPHA) -> float:
    """P(U<=alpha, V<=alpha) / alpha for a Gaussian copula with correlation r.

    Symmetry of the bivariate normal makes the upper-tail benchmark equal
    to this lower-tail value.
    """
    r = float(np.clip(pearson_r, -0.999999, 0.999999))
    q = float(stats.norm.ppf(alpha))
    cov = np.array([[1.0, r], [r, 1.0]])
    joint = float(stats.multivariate_normal.cdf([q, q], mean=np.zeros(2), cov=cov))
    return joint / alpha


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
    if abs(gaussian_coexceedance(0.0) - ALPHA) > 1e-6:
        raise RuntimeError("Gaussian benchmark at r=0 should equal alpha")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    snap = load_snapshot(REPO_ROOT / SNAPSHOT_REL)
    frames, drop_note = _prepare_frames(snap["frames"])
    v001 = pd.read_excel(V001_INDEX)

    rows: list[dict[str, object]] = []
    for left, right in itertools.combinations(MAJOR_PAIRS, 2):
        pair = f"{left}-{right}"
        x, y = _pair_returns(frames, left, right)
        u = stats.rankdata(x, method="average") / (len(x) + 1.0)
        v = stats.rankdata(y, method="average") / (len(y) + 1.0)
        pearson_r = float(stats.pearsonr(x, y).statistic)
        bench = gaussian_coexceedance(pearson_r, ALPHA)
        l_low_r = _l_hat(u, v, ALPHA, True, True)
        l_low_l = _l_hat(u, v, ALPHA, True, False)
        l_up_r = _l_hat(u, v, ALPHA, False, True)
        l_up_l = _l_hat(u, v, ALPHA, False, False)
        rows.append(
            {
                "pair": pair,
                "n": int(len(x)),
                "pearson_r": pearson_r,
                "L_lower_cond_R": l_low_r,
                "L_lower_cond_L": l_low_l,
                "L_upper_cond_R": l_up_r,
                "L_upper_cond_L": l_up_l,
                "gauss_benchmark": bench,
                "excess_lower_cond_R": l_low_r - bench,
                "excess_lower_cond_L": l_low_l - bench,
                "excess_upper_cond_R": l_up_r - bench,
                "excess_upper_cond_L": l_up_l - bench,
            }
        )

    index = pd.DataFrame(rows)
    merged = index.merge(
        v001[["pair", "L_lower_cond_R", "pearson_r"]].rename(
            columns={"L_lower_cond_R": "v001_L_lower_cond_R", "pearson_r": "v001_r"}
        ),
        on="pair",
        how="left",
    )
    focus = merged.loc[merged["pair"] == "AUDUSD-NZDUSD"].iloc[0]
    recomputed_excess = float(focus["L_lower_cond_R"] - focus["gauss_benchmark"])
    v001_excess = float(focus["v001_L_lower_cond_R"]) - gaussian_coexceedance(float(focus["v001_r"]))
    if abs(float(focus["L_lower_cond_R"]) - float(focus["v001_L_lower_cond_R"])) > 1e-6:
        raise RuntimeError("AUDUSD-NZDUSD L_hat does not match v001")
    if abs(recomputed_excess - float(focus["excess_lower_cond_R"])) > 1e-12:
        raise RuntimeError("Excess is not L_hat minus the Gaussian benchmark")
    if abs(recomputed_excess - v001_excess) > 1e-6:
        raise RuntimeError("AUDUSD-NZDUSD excess does not match v001 L_hat minus gaussian(r)")

    done = (
        "Done: each pair has L_hat, a Gaussian co-exceedance benchmark at the "
        "same Pearson r, and excess = L_hat - benchmark, for both tails."
    )
    index.to_excel(OUT_DIR / "index.xlsx", index=False, sheet_name="index")
    show_cols = [
        "pair",
        "n",
        "pearson_r",
        "L_lower_cond_R",
        "gauss_benchmark",
        "excess_lower_cond_R",
        "L_upper_cond_R",
        "excess_upper_cond_R",
    ]
    aud = index.loc[index["pair"] == "AUDUSD-NZDUSD"].iloc[0]
    notes = "\n".join(
        [
            "# Tail dependence experiments v002",
            "",
            done,
            "",
            "## Research question",
            "",
            "For each unordered pair, how does the empirical tail frequency at "
            "alpha=0.05 compare with the co-exceedance a Gaussian with the same "
            "Pearson r would give?",
            "",
            "## Snapshot",
            "",
            f"- Folder: `data/snapshots/{snap['manifest']['folder']}`",
            f"- {drop_note}",
            "",
            "## Parameters",
            "",
            "- Same uniforms as v001: rank/(n+1), alpha=0.05, both conditioning directions.",
            "- Gaussian benchmark = bivariate-normal CDF at Phi^{-1}(alpha), divided by alpha.",
            "- Upper and lower Gaussian benchmarks are equal by symmetry. Excess uses that one number.",
            "- v001 L_hat was recomputed as a check and v001 files were not edited.",
            "",
            "## Index",
            "",
            _markdown_table(index[show_cols]),
            "",
            "## Cross-pair conclusion",
            "",
            (
                f"AUDUSD-NZDUSD lower L_hat is {float(aud['L_lower_cond_R']):.4f} "
                f"against a Gaussian benchmark of {float(aud['gauss_benchmark']):.4f} "
                f"(excess {float(aud['excess_lower_cond_R']):.4f}) at r={float(aud['pearson_r']):.4f}."
            ),
            "Independence (benchmark = alpha = 0.05) is the wrong yardstick when r is not zero.",
            "This is not a trading signal.",
            "",
            f"Check: v001 excess for AUDUSD-NZDUSD is {v001_excess:.6f}; recomputed excess is {recomputed_excess:.6f}.",
            "",
        ]
    )
    (EXP_DIR / "NOTES.md").write_text(notes, encoding="utf-8")
    print(done, flush=True)
    print(f"AUDUSD-NZDUSD excess {recomputed_excess:.6f} v001-based {v001_excess:.6f}", flush=True)
    return OUT_DIR / "index.xlsx"


if __name__ == "__main__":
    run()
