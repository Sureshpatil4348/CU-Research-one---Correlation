"""v002: DCC refit without the v001 floor b >= 0.5."""

from __future__ import annotations

import itertools
import math
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from arch import arch_model
from scipy import optimize

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from shared.mt5_data import MAJOR_PAIRS, load_snapshot

SNAPSHOT_REL = Path("data/snapshots/2026-11-03_majors_alpari_D1")
EXP_DIR = Path(__file__).resolve().parent
OUT_DIR = EXP_DIR / "outputs"
V001_INDEX = EXP_DIR.parent / "v001" / "outputs" / "index.xlsx"
STARTS = ((0.05, 0.90), (0.02, 0.50), (0.10, 0.20), (0.05, 0.05), (0.01, 0.80))


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


def _fit_garch(returns: np.ndarray) -> np.ndarray:
    series = pd.Series(returns * 100.0)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model = arch_model(series, mean="Constant", vol="Garch", p=1, q=1, dist="normal")
        result = model.fit(disp="off", show_warning=False)
    resid = np.asarray(result.resid, dtype=float)
    sigma = np.asarray(result.conditional_volatility, dtype=float)
    return resid / sigma


def _dcc_neg_loglik(params: np.ndarray, z1: np.ndarray, z2: np.ndarray, q12: float) -> float:
    a = float(params[0])
    b = float(params[1])
    if a < 0.0 or b < 0.0 or a + b >= 0.999:
        return 1e12
    n = len(z1)
    q11 = 1.0
    q22 = 1.0
    q_prev = q12
    intercept = 1.0 - a - b
    ll = 0.0
    for t in range(1, n):
        q_prev = intercept * q12 + a * z1[t - 1] * z2[t - 1] + b * q_prev
        q11 = intercept + a * z1[t - 1] * z1[t - 1] + b * q11
        q22 = intercept + a * z2[t - 1] * z2[t - 1] + b * q22
        denom = math.sqrt(max(q11, 1e-12) * max(q22, 1e-12))
        r = q_prev / denom
        if r > 0.999999:
            r = 0.999999
        elif r < -0.999999:
            r = -0.999999
        zi = z1[t]
        zj = z2[t]
        ll += math.log(1.0 - r * r) + (zi * zi - 2.0 * r * zi * zj + zj * zj) / (1.0 - r * r)
    return 0.5 * ll


def _boundary(a: float, b: float) -> str:
    flags: list[str] = []
    if a <= 1e-5:
        flags.append("a")
    if b <= 1e-5:
        flags.append("b")
    if a + b >= 0.998:
        flags.append("a+b")
    return ",".join(flags) if flags else "interior"


def _estimate(z1: np.ndarray, z2: np.ndarray) -> dict[str, object]:
    q12 = float(np.corrcoef(z1, z2)[0, 1])
    bounds = [(0.0, 0.5), (0.0, 0.999)]
    cons = {"type": "ineq", "fun": lambda p: 0.999 - p[0] - p[1]}
    best = None
    tried_low_b = False
    for start in STARTS:
        if start[1] < 0.5:
            tried_low_b = True
        res = optimize.minimize(
            _dcc_neg_loglik,
            x0=np.array(start, dtype=float),
            args=(z1, z2, q12),
            method="SLSQP",
            bounds=bounds,
            constraints=cons,
            options={"maxiter": 300, "ftol": 1e-10},
        )
        if best is None or float(res.fun) < float(best.fun):
            best = res
    if best is None or not np.isfinite(best.fun) or float(best.fun) >= 1e11:
        return {
            "status": "fail",
            "success": False,
            "a": float("nan"),
            "b": float("nan"),
            "nll": float("nan"),
            "boundary": "fail",
            "tried_low_b": tried_low_b,
        }
    a = max(0.0, float(best.x[0]))
    b = max(0.0, float(best.x[1]))
    if a + b >= 0.999:
        scale = 0.998 / (a + b)
        a *= scale
        b *= scale
    return {
        "status": "ok" if bool(best.success) else "check",
        "success": bool(best.success),
        "a": a,
        "b": b,
        "nll": float(best.fun),
        "boundary": _boundary(a, b),
        "tried_low_b": tried_low_b,
    }


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
    v001 = pd.read_excel(V001_INDEX).set_index("pair")
    rows: list[dict[str, object]] = []
    for left, right in itertools.combinations(MAJOR_PAIRS, 2):
        pair = f"{left}-{right}"
        try:
            a = frames[left].set_index("time")["log_return"].dropna()
            b = frames[right].set_index("time")["log_return"].dropna()
            common = a.index.intersection(b.index).sort_values()
            x = a.loc[common].to_numpy(dtype=float)
            y = b.loc[common].to_numpy(dtype=float)
            fit = _estimate(_fit_garch(x), _fit_garch(y))
            fit["n"] = int(len(common))
        except Exception as exc:
            fit = {
                "status": "fail",
                "success": False,
                "a": float("nan"),
                "b": float("nan"),
                "nll": float("nan"),
                "boundary": "fail",
                "tried_low_b": False,
                "n": 0,
                "error": str(exc),
            }
        row = {
            "pair": pair,
            "n": fit["n"],
            "status": fit["status"],
            "success": fit["success"],
            "a": fit["a"],
            "b": fit["b"],
            "nll": fit["nll"],
            "boundary": fit["boundary"],
            "tried_low_b": fit["tried_low_b"],
            "v001_a": float(v001.loc[pair, "a"]),
            "v001_b": float(v001.loc[pair, "b"]),
        }
        rows.append(row)
        print(f"{pair} status={row['status']} a={row['a']:.4f} b={row['b']:.4f} {row['boundary']}", flush=True)

    index = pd.DataFrame(rows)
    focus = index.loc[index["pair"] == "EURUSD-USDCHF"].iloc[0]
    forced = abs(float(focus["b"]) - 0.5) <= 1e-6 and str(focus["boundary"]) == "interior"
    if forced or not bool(focus["tried_low_b"]):
        raise RuntimeError(
            "EURUSD-USDCHF still sits on b=0.5 without a boundary flag, "
            "or no interior low-b start was tried"
        )
    if set(index["status"]) - {"ok", "check", "fail"}:
        raise RuntimeError("Unexpected status flag")
    n_ok = int((index["status"] == "ok").sum())
    n_check = int((index["status"] == "check").sum())
    n_fail = int((index["status"] == "fail").sum())
    done = (
        f"Done: every pair has a status flag after a refit with b >= 0 removed "
        f"(ok={n_ok}, check={n_check}, fail={n_fail})."
    )
    index.to_excel(OUT_DIR / "index.xlsx", index=False, sheet_name="index")
    show = ["pair", "n", "status", "success", "a", "b", "boundary", "v001_a", "v001_b", "nll"]
    notes = "\n".join(
        [
            "# DCC-GARCH experiments v002",
            "",
            done,
            "",
            "## Research question",
            "",
            "Do the Engle DCC parameters stay interior when the v001 lower bound b >= 0.5 is removed?",
            "",
            "## Snapshot",
            "",
            f"- Folder: `data/snapshots/{snap['manifest']['folder']}`",
            f"- {drop_note}",
            "",
            "## Parameters",
            "",
            "- Marginal model: constant-mean GARCH(1,1) via arch, fit on percent returns, z = resid/sigma.",
            "- DCC bounds: a in [0, 0.5], b in [0, 0.999], constraint a+b < 0.999.",
            "- v001 used b >= 0.5. That floor is removed. Starts include b = 0.50, 0.20, and 0.05.",
            "- status ok: optimizer success. status check: a finite point that did not report success. status fail: no finite fit.",
            "- boundary lists a, b, or a+b when the point sits on that edge. interior means none of those.",
            "- v001 files were not edited.",
            "",
            "## Index",
            "",
            _markdown_table(index[show]),
            "",
            "## Cross-pair conclusion",
            "",
            (
                f"EURUSD-USDCHF v002 b is {float(focus['b']):.6f} "
                f"(v001 b was {float(focus['v001_b']):.6f}), boundary={focus['boundary']}, "
                f"status={focus['status']}."
            ),
            "A reported b of 0.5 in v001 was the old box constraint, not evidence of a special correlation law.",
            "This is not a trading signal.",
            "",
        ]
    )
    (EXP_DIR / "NOTES.md").write_text(notes, encoding="utf-8")
    print(done, flush=True)
    return OUT_DIR / "index.xlsx"


if __name__ == "__main__":
    run()
