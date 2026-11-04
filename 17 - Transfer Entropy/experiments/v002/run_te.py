"""v002: shuffle tests for discrete transfer entropy. Does not edit v001."""

from __future__ import annotations

import itertools
import math
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from shared.mt5_data import MAJOR_PAIRS, load_snapshot

SNAPSHOT_REL = Path("data/snapshots/2026-11-03_majors_alpari_D1")
EXP_DIR = Path(__file__).resolve().parent
OUT_DIR = EXP_DIR / "outputs"
V001_INDEX = EXP_DIR.parent / "v001" / "outputs" / "index.xlsx"
N_BINS = 5
LAG = 1
N_PERM = 500
SEED = 20261103
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


def _equal_frequency_labels(values: np.ndarray, n_bins: int = N_BINS) -> np.ndarray:
    ranks = stats.rankdata(values, method="average")
    labels = np.floor((ranks - 1e-12) * n_bins / len(values)).astype(int)
    return np.clip(labels, 0, n_bins - 1)


def _transfer_entropy_fast(y_fut: np.ndarray, y_past: np.ndarray, x_past: np.ndarray) -> float:
    yf = np.asarray(y_fut, dtype=np.int64)
    yp = np.asarray(y_past, dtype=np.int64)
    xp = np.asarray(x_past, dtype=np.int64)
    n = len(yf)
    if n < 2:
        return float("nan")
    joint1 = np.bincount(yf * N_BINS + yp, minlength=N_BINS * N_BINS).astype(float)
    marg1 = np.bincount(yp, minlength=N_BINS).astype(float)
    h1 = 0.0
    for code, count in enumerate(joint1):
        if count <= 0:
            continue
        px = marg1[code % N_BINS]
        p = count / n
        h1 -= p * math.log(p / (px / n))
    nstate = N_BINS * N_BINS
    state2 = yp * N_BINS + xp
    joint2 = np.bincount(yf * nstate + state2, minlength=N_BINS * nstate).astype(float)
    marg2 = np.bincount(state2, minlength=nstate).astype(float)
    h2 = 0.0
    for code, count in enumerate(joint2):
        if count <= 0:
            continue
        px = marg2[code % nstate]
        p = count / n
        h2 -= p * math.log(p / (px / n))
    return float(h1 - h2)


def _transfer_entropy_counter(y_fut, y_past, x_past) -> float:
    triples = list(zip(y_fut, y_past, x_past))
    n = len(triples)
    joint_yf_yp = Counter((a, b) for a, b, _ in triples)
    marg_yp = Counter(b for _, b, _ in triples)
    h1 = 0.0
    for (yf, rest), count in joint_yf_yp.items():
        p = count / n
        px = marg_yp[rest] / n
        h1 -= p * math.log(p / px)
    joint_all = Counter((a, (b, c)) for a, b, c in triples)
    marg_all = Counter((b, c) for _, b, c in triples)
    h2 = 0.0
    for (yf, rest), count in joint_all.items():
        p = count / n
        px = marg_all[rest] / n
        h2 -= p * math.log(p / px)
    return float(h1 - h2)


def _assert_fast_matches_counter() -> None:
    rng = np.random.default_rng(0)
    y = rng.integers(0, N_BINS, size=80)
    x = rng.integers(0, N_BINS, size=80)
    fast = _transfer_entropy_fast(y[1:], y[:-1], x[:-1])
    slow = _transfer_entropy_counter(y[1:], y[:-1], x[:-1])
    if abs(fast - slow) > 1e-9:
        raise RuntimeError(f"Fast TE {fast} does not match the counter TE {slow}")
    y_fut = [1, 0, 1, 0]
    y_past = [0, 1, 0, 1]
    x_past = [0, 0, 1, 1]
    if abs(_transfer_entropy_fast(y_fut, y_past, x_past)) > 1e-12:
        raise RuntimeError("Guide toy TE is not zero")


def _one_sided_p(observed: float, null: np.ndarray) -> float:
    return float((1.0 + np.sum(null >= observed - 1e-15)) / (1.0 + len(null)))


def _analytic_bias(n_te: int) -> float:
    return ((N_BINS - 1) ** 2) * N_BINS / (2.0 * n_te)


def _directed_null(
    y_lab: np.ndarray,
    x_lab: np.ndarray,
    rng: np.random.Generator,
) -> tuple[float, np.ndarray]:
    y_fut = y_lab[LAG:]
    y_past = y_lab[:-LAG]
    x_past = x_lab[:-LAG]
    observed = _transfer_entropy_fast(y_fut, y_past, x_past)
    null = np.empty(N_PERM)
    n = len(x_lab)
    for i in range(N_PERM):
        shuffled = x_lab[rng.permutation(n)]
        null[i] = _transfer_entropy_fast(y_fut, y_past, shuffled[:-LAG])
    return observed, null


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


def _independent_toy_does_not_pass() -> None:
    rng = np.random.default_rng(SEED)
    x = rng.normal(size=4000)
    y = rng.normal(size=4000)
    x_lab = _equal_frequency_labels(x)
    y_lab = _equal_frequency_labels(y)
    rows = []
    for source, target, label in (
        (x_lab, y_lab, "x_to_y"),
        (y_lab, x_lab, "y_to_x"),
    ):
        observed, null = _directed_null(target, source, rng)
        rows.append({"direction": label, "te": observed, "p": _one_sided_p(observed, null)})
    pvals = [row["p"] for row in rows]
    reject, _, _, _ = multipletests(pvals, alpha=ALPHA, method="fdr_bh")
    if bool(np.any(reject)):
        raise RuntimeError(f"Independent toy passed FDR at seed {SEED}: {rows}")


def run() -> Path:
    _assert_fast_matches_counter()
    _independent_toy_does_not_pass()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    snap = load_snapshot(REPO_ROOT / SNAPSHOT_REL)
    frames, drop_note = _prepare_frames(snap["frames"])
    v001 = pd.read_excel(V001_INDEX).set_index("pair")
    rng = np.random.default_rng(SEED)
    rows: list[dict[str, object]] = []
    for left, right in itertools.combinations(MAJOR_PAIRS, 2):
        pair = f"{left}-{right}"
        a = frames[left].set_index("time")["log_return"].dropna()
        b = frames[right].set_index("time")["log_return"].dropna()
        common = a.index.intersection(b.index).sort_values()
        x = a.loc[common].to_numpy(dtype=float)
        y = b.loc[common].to_numpy(dtype=float)
        x_lab = _equal_frequency_labels(x)
        y_lab = _equal_frequency_labels(y)
        n_te = len(x_lab) - LAG
        bias = _analytic_bias(n_te)
        te_lr, null_lr = _directed_null(y_lab, x_lab, rng)
        te_rl, null_rl = _directed_null(x_lab, y_lab, rng)
        v001_lr = float(v001.loc[pair, "te_L_to_R"])
        v001_rl = float(v001.loc[pair, "te_R_to_L"])
        if abs(te_lr - v001_lr) > 1e-6 or abs(te_rl - v001_rl) > 1e-6:
            raise RuntimeError(f"{pair} TE does not match v001 ({te_lr} vs {v001_lr})")
        for direction, source, target, te, null in (
            (f"{left}->{right}", left, right, te_lr, null_lr),
            (f"{right}->{left}", right, left, te_rl, null_rl),
        ):
            rows.append(
                {
                    "pair": pair,
                    "direction": direction,
                    "source": source,
                    "target": target,
                    "n_te": n_te,
                    "te": te,
                    "null_mean": float(np.mean(null)),
                    "analytic_bias": bias,
                    "p": _one_sided_p(te, null),
                }
            )
        print(f"{pair} TE {te_lr:.6f} {te_rl:.6f}", flush=True)

    index = pd.DataFrame(rows)
    reject, qvals, _, _ = multipletests(index["p"].to_numpy(dtype=float), alpha=ALPHA, method="fdr_bh")
    index["q"] = qvals
    index["pass"] = reject
    index = index.sort_values(["pass", "te"], ascending=[False, False]).reset_index(drop=True)
    index.insert(0, "rank", np.arange(1, len(index) + 1))
    n_pass = int(index["pass"].sum())
    done = (
        f"Done: 56 directed TE scores ranked only after a {N_PERM}-shuffle null; "
        f"{n_pass} pass BH-FDR at {ALPHA}."
    )
    index.to_excel(OUT_DIR / "index.xlsx", index=False, sheet_name="index")
    show = ["rank", "direction", "n_te", "te", "null_mean", "analytic_bias", "p", "q", "pass"]
    notes = "\n".join(
        [
            "# Transfer entropy experiments v002",
            "",
            done,
            "",
            "## Research question",
            "",
            "Which directed discrete transfer-entropy scores clear a shuffle null "
            "after BH-FDR across the 56 directions?",
            "",
            "## Snapshot",
            "",
            f"- Folder: `data/snapshots/{snap['manifest']['folder']}`",
            f"- {drop_note}",
            "",
            "## Parameters",
            "",
            f"- Same discretization as v001: B={N_BINS} equal-frequency bins, lag {LAG}.",
            f"- {N_PERM} permutations of the source bin path, seed {SEED}, one stream in pair order.",
            "- One-sided p = (1 + count of null TE >= observed) / (1 + n_perm).",
            f"- Pass only when BH-FDR q < {ALPHA}.",
            "- Analytic plug-in bias = (B-1)^2 * B / (2 N).",
            "- An independent N(0,1) toy at the same seed does not pass this FDR rule.",
            "- v001 files were not edited. Observed TE matches the v001 index.",
            "",
            "## Ranked directed scores",
            "",
            _markdown_table(index[show]),
            "",
            "## Cross-pair conclusion",
            "",
            f"Directions that pass the null: {n_pass} of 56.",
            "Scores near the analytic bias are not evidence of directed information.",
            "This is not a trading signal.",
            "",
        ]
    )
    (EXP_DIR / "NOTES.md").write_text(notes, encoding="utf-8")
    print(done, flush=True)
    return OUT_DIR / "index.xlsx"


if __name__ == "__main__":
    run()
