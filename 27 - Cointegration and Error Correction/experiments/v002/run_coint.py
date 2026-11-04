"""v002: Bonferroni and BH-FDR on Engle-Granger p-values. Does not edit v001."""

from __future__ import annotations

import itertools
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.multitest import multipletests
from statsmodels.tsa.stattools import coint

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from shared.mt5_data import MAJOR_PAIRS, load_snapshot

SNAPSHOT_REL = Path("data/snapshots/2026-11-03_majors_alpari_D1")
EXP_DIR = Path(__file__).resolve().parent
OUT_DIR = EXP_DIR / "outputs"
V001_INDEX = EXP_DIR.parent / "v001" / "outputs" / "index.xlsx"
N_TESTS = 28
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
        work["log_price"] = np.log(work["close"])
        work["log_return"] = work["log_price"].diff()
        cleaned[name] = work
    if drop_date is not None:
        drop_note = (
            f"Dropped unfinished last bar dated {drop_date.date().isoformat()} "
            "UTC after a tick-volume check against the prior complete day."
        )
    return cleaned, drop_note


def _aligned_log_prices(frames: dict[str, pd.DataFrame], left: str, right: str) -> tuple[np.ndarray, np.ndarray]:
    a = frames[left].set_index("time")["log_price"].dropna()
    b = frames[right].set_index("time")["log_price"].dropna()
    common = a.index.intersection(b.index).sort_values()
    return a.loc[common].to_numpy(dtype=float), b.loc[common].to_numpy(dtype=float)


def _markdown_table(frame: pd.DataFrame) -> str:
    show = frame.copy()
    for col in show.columns:
        if pd.api.types.is_float_dtype(show[col]):
            show[col] = show[col].map(lambda v: "" if pd.isna(v) else f"{v:.6g}")
        elif pd.api.types.is_bool_dtype(show[col]):
            show[col] = show[col].map(lambda v: "yes" if bool(v) else "no")
    header = "| " + " | ".join(show.columns) + " |"
    rule = "| " + " | ".join("---" for _ in show.columns) + " |"
    body = ["| " + " | ".join(str(v) for v in row) + " |" for row in show.itertuples(index=False, name=None)]
    return "\n".join([header, rule, *body])


def run() -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    snap = load_snapshot(REPO_ROOT / SNAPSHOT_REL)
    frames, drop_note = _prepare_frames(snap["frames"])
    v001 = pd.read_excel(V001_INDEX)
    v001_p = dict(zip(v001["pair"].astype(str), v001["coint_p"].astype(float)))

    rows: list[dict[str, object]] = []
    for left, right in itertools.combinations(MAJOR_PAIRS, 2):
        pair = f"{left}-{right}"
        ln_x, ln_y = _aligned_log_prices(frames, left, right)
        coint_t, coint_p, _crit = coint(ln_y, ln_x, trend="c", autolag="aic")
        x_design = sm.add_constant(ln_x)
        ols = sm.OLS(ln_y, x_design).fit()
        rows.append(
            {
                "pair": pair,
                "n": int(len(ln_x)),
                "alpha": float(ols.params[0]),
                "beta": float(ols.params[1]),
                "coint_t": float(coint_t),
                "raw_p": float(coint_p),
                "v001_p": float(v001_p[pair]),
            }
        )
        print(f"{pair} raw_p={float(coint_p):.6g}", flush=True)

    index = pd.DataFrame(rows)
    index["p_diff_vs_v001"] = index["raw_p"] - index["v001_p"]
    index["bonferroni_p"] = np.minimum(1.0, index["raw_p"] * N_TESTS)
    reject, qvals, _, _ = multipletests(index["raw_p"].to_numpy(dtype=float), alpha=ALPHA, method="fdr_bh")
    index["bh_q"] = qvals
    index["survive_bonferroni"] = index["bonferroni_p"] < ALPHA
    index["survive_fdr"] = reject

    focus = index.loc[index["pair"] == "EURUSD-USDCAD"].iloc[0]
    expected = min(1.0, N_TESTS * float(focus["raw_p"]))
    if abs(float(focus["bonferroni_p"]) - expected) > 1e-12:
        raise RuntimeError("EURUSD-USDCAD Bonferroni p does not match min(1, 28 * raw p)")
    if index["survive_bonferroni"].tolist() != (index["bonferroni_p"] < ALPHA).tolist():
        raise RuntimeError("Survivor flags do not match the Bonferroni cut")

    bonf_hits = index.loc[index["survive_bonferroni"], "pair"].tolist()
    fdr_hits = index.loc[index["survive_fdr"], "pair"].tolist()
    bonf_text = "none" if not bonf_hits else ", ".join(bonf_hits)
    fdr_text = "none" if not fdr_hits else ", ".join(fdr_hits)
    max_diff = float(index["p_diff_vs_v001"].abs().max())
    done = (
        f"Done: Bonferroni and BH-FDR applied to {N_TESTS} recomputed Engle-Granger "
        f"p-values; Bonferroni survivors: {bonf_text}; BH-FDR survivors: {fdr_text}."
    )

    index.to_excel(OUT_DIR / "index.xlsx", index=False, sheet_name="index")
    table_cols = [
        "pair",
        "n",
        "raw_p",
        "v001_p",
        "bonferroni_p",
        "bh_q",
        "survive_bonferroni",
        "survive_fdr",
    ]
    notes = "\n".join(
        [
            "# Cointegration and error correction experiments v002",
            "",
            done,
            "",
            "## Research question",
            "",
            "After a Bonferroni or BH-FDR correction for 28 Engle-Granger tests, "
            "which pairs still show cointegration of log closes on the Alpari D1 history?",
            "",
            "## Snapshot",
            "",
            f"- Folder: `data/snapshots/{snap['manifest']['folder']}`",
            f"- {drop_note}",
            "",
            "## Parameters",
            "",
            "- Same design as v001: statsmodels coint(trend='c', autolag='aic'), PY = right on PX = left.",
            f"- Bonferroni cut = {ALPHA} / {N_TESTS} = {ALPHA / N_TESTS:.6g}.",
            f"- BH-FDR at {ALPHA} via statsmodels multipletests method fdr_bh.",
            "- v001 outputs were read and not edited. Corrected p-values use the recomputed raw p.",
            f"- Largest absolute gap between recomputed raw p and v001 coint_p: {max_diff:.6g}.",
            "",
            "## Index",
            "",
            _markdown_table(index[table_cols]),
            "",
            "## Cross-pair conclusion",
            "",
            f"Bonferroni survivors at {ALPHA}: {bonf_text}.",
            f"BH-FDR survivors at {ALPHA}: {fdr_text}.",
            "A raw p below 0.05 is not a robust hit once the 28 tests are counted.",
            "This is not a trading signal.",
            "",
        ]
    )
    (EXP_DIR / "NOTES.md").write_text(notes, encoding="utf-8")
    print(done, flush=True)
    print(f"max |p diff vs v001| = {max_diff:.6g}", flush=True)
    return OUT_DIR / "index.xlsx"


if __name__ == "__main__":
    run()
