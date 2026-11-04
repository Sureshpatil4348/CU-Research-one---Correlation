"""v002: ADCC refit without b >= 0.5, plus a boundary likelihood-ratio test for g."""

from __future__ import annotations

import itertools
import math
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from arch import arch_model
from scipy import optimize, stats

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from shared.mt5_data import MAJOR_PAIRS, load_snapshot

SNAPSHOT_REL = Path("data/snapshots/2026-11-03_majors_alpari_D1")
EXP_DIR = Path(__file__).resolve().parent
OUT_DIR = EXP_DIR / "outputs"
V001_INDEX = EXP_DIR.parent / "v001" / "outputs" / "index.xlsx"
DCC_STARTS = ((0.05, 0.90), (0.02, 0.50), (0.10, 0.20), (0.05, 0.05), (0.01, 0.80))
ADCC_STARTS = (
    (0.05, 0.85, 0.05),
    (0.02, 0.50, 0.02),
    (0.10, 0.20, 0.05),
    (0.05, 0.05, 0.0),
    (0.01, 0.80, 0.01),
)


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


def _neg_loglik(
    a: float,
    b: float,
    g: float,
    z1: np.ndarray,
    z2: np.ndarray,
    n1: np.ndarray,
    n2: np.ndarray,
    q12: float,
    n11: float,
    n22: float,
    n12: float,
) -> float:
    if a < 0.0 or b < 0.0 or g < 0.0 or a + b + 0.5 * g >= 0.999:
        return 1e12
    a11 = (1.0 - a - b) - g * n11
    a22 = (1.0 - a - b) - g * n22
    a12 = (1.0 - a - b) * q12 - g * n12
    q11 = 1.0
    q22 = 1.0
    q12_prev = q12
    ll = 0.0
    n = len(z1)
    for t in range(1, n):
        z1p = z1[t - 1]
        z2p = z2[t - 1]
        n1p = n1[t - 1]
        n2p = n2[t - 1]
        q11 = a11 + a * z1p * z1p + b * q11 + g * n1p * n1p
        q22 = a22 + a * z2p * z2p + b * q22 + g * n2p * n2p
        q12_prev = a12 + a * z1p * z2p + b * q12_prev + g * n1p * n2p
        denom = math.sqrt(max(q11, 1e-12) * max(q22, 1e-12))
        r = q12_prev / denom
        if r > 0.999999:
            r = 0.999999
        elif r < -0.999999:
            r = -0.999999
        zi = z1[t]
        zj = z2[t]
        ll += math.log(1.0 - r * r) + (zi * zi - 2.0 * r * zi * zj + zj * zj) / (1.0 - r * r)
    return 0.5 * ll


def _boundary(a: float, b: float, g: float) -> str:
    flags: list[str] = []
    if a <= 1e-5:
        flags.append("a")
    if b <= 1e-5:
        flags.append("b")
    if g <= 1e-5:
        flags.append("g")
    if a + b + 0.5 * g >= 0.998:
        flags.append("stationarity")
    return ",".join(flags) if flags else "interior"


def _chibar_p(lr: float) -> float:
    if not np.isfinite(lr) or lr <= 0.0:
        return 1.0
    return 0.5 * float(stats.chi2.sf(lr, 1))


def _estimate(z1: np.ndarray, z2: np.ndarray) -> dict[str, object]:
    q12 = float(np.corrcoef(z1, z2)[0, 1])
    n1 = np.minimum(z1, 0.0)
    n2 = np.minimum(z2, 0.0)
    n11 = float(np.mean(n1 * n1))
    n22 = float(np.mean(n2 * n2))
    n12 = float(np.mean(n1 * n2))

    def dcc_obj(params: np.ndarray) -> float:
        return _neg_loglik(float(params[0]), float(params[1]), 0.0, z1, z2, n1, n2, q12, n11, n22, n12)

    def adcc_obj(params: np.ndarray) -> float:
        return _neg_loglik(
            float(params[0]), float(params[1]), float(params[2]), z1, z2, n1, n2, q12, n11, n22, n12
        )

    dcc_bounds = [(0.0, 0.5), (0.0, 0.999)]
    adcc_bounds = [(0.0, 0.5), (0.0, 0.999), (0.0, 0.5)]
    dcc_cons = {"type": "ineq", "fun": lambda p: 0.999 - p[0] - p[1]}
    adcc_cons = {"type": "ineq", "fun": lambda p: 0.999 - p[0] - p[1] - 0.5 * p[2]}
    best_dcc = None
    tried_low_b = False
    for start in DCC_STARTS:
        if start[1] < 0.5:
            tried_low_b = True
        res = optimize.minimize(
            dcc_obj,
            x0=np.array(start, dtype=float),
            method="SLSQP",
            bounds=dcc_bounds,
            constraints=dcc_cons,
            options={"maxiter": 300, "ftol": 1e-10},
        )
        if best_dcc is None or float(res.fun) < float(best_dcc.fun):
            best_dcc = res
    best_adcc = None
    for start in ADCC_STARTS:
        res = optimize.minimize(
            adcc_obj,
            x0=np.array(start, dtype=float),
            method="SLSQP",
            bounds=adcc_bounds,
            constraints=adcc_cons,
            options={"maxiter": 400, "ftol": 1e-10},
        )
        if best_adcc is None or float(res.fun) < float(best_adcc.fun):
            best_adcc = res
    if (
        best_dcc is None
        or best_adcc is None
        or float(best_dcc.fun) >= 1e11
        or float(best_adcc.fun) >= 1e11
    ):
        return {
            "status": "fail",
            "success": False,
            "a": float("nan"),
            "b": float("nan"),
            "g": float("nan"),
            "nll_adcc": float("nan"),
            "nll_dcc": float("nan"),
            "lr": float("nan"),
            "lr_p": float("nan"),
            "boundary": "fail",
            "tried_low_b": tried_low_b,
        }
    a = max(0.0, float(best_adcc.x[0]))
    b = max(0.0, float(best_adcc.x[1]))
    g = max(0.0, float(best_adcc.x[2]))
    if a + b + 0.5 * g >= 0.999:
        scale = 0.998 / (a + b + 0.5 * g)
        a *= scale
        b *= scale
        g *= scale
    nll_adcc = float(best_adcc.fun)
    nll_dcc = float(best_dcc.fun)
    lr = max(0.0, 2.0 * (nll_dcc - nll_adcc))
    success = bool(best_adcc.success) and bool(best_dcc.success)
    return {
        "status": "ok" if success else "check",
        "success": success,
        "a": a,
        "b": b,
        "g": g,
        "nll_adcc": nll_adcc,
        "nll_dcc": nll_dcc,
        "lr": lr,
        "lr_p": _chibar_p(lr),
        "boundary": _boundary(a, b, g),
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
            left_s = frames[left].set_index("time")["log_return"].dropna()
            right_s = frames[right].set_index("time")["log_return"].dropna()
            common = left_s.index.intersection(right_s.index).sort_values()
            x = left_s.loc[common].to_numpy(dtype=float)
            y = right_s.loc[common].to_numpy(dtype=float)
            fit = _estimate(_fit_garch(x), _fit_garch(y))
            fit["n"] = int(len(common))
        except Exception as exc:
            fit = {
                "status": "fail",
                "success": False,
                "a": float("nan"),
                "b": float("nan"),
                "g": float("nan"),
                "nll_adcc": float("nan"),
                "nll_dcc": float("nan"),
                "lr": float("nan"),
                "lr_p": float("nan"),
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
            "g": fit["g"],
            "boundary": fit["boundary"],
            "nll_adcc": fit["nll_adcc"],
            "nll_dcc": fit["nll_dcc"],
            "lr": fit["lr"],
            "lr_p": fit["lr_p"],
            "tried_low_b": fit["tried_low_b"],
            "v001_b": float(v001.loc[pair, "b"]),
            "v001_g": float(v001.loc[pair, "g"]),
        }
        rows.append(row)
        print(
            f"{pair} status={row['status']} b={row['b']:.4f} g={row['g']:.4f} "
            f"lr_p={row['lr_p']:.3g} {row['boundary']}",
            flush=True,
        )

    index = pd.DataFrame(rows)
    focus = index.loc[index["pair"] == "EURUSD-USDCHF"].iloc[0]
    forced = abs(float(focus["b"]) - 0.5) <= 1e-6 and "b" not in str(focus["boundary"]).split(",")
    if str(focus["boundary"]) == "interior" and abs(float(focus["b"]) - 0.5) <= 1e-6:
        forced = True
    if forced or not bool(focus["tried_low_b"]):
        raise RuntimeError("EURUSD-USDCHF b=0.5 is not a documented boundary outcome")
    n_ok = int((index["status"] == "ok").sum())
    n_check = int((index["status"] == "check").sum())
    n_fail = int((index["status"] == "fail").sum())
    n_g = int(((index["lr_p"] < 0.05) & np.isfinite(index["lr_p"])).sum())
    done = (
        f"Done: every pair has a status flag, a boundary flag, and a chi-bar-square "
        f"likelihood-ratio p-value for g=0 (ok={n_ok}, check={n_check}, fail={n_fail}; "
        f"lr_p<0.05 on {n_g} pairs)."
    )
    index.to_excel(OUT_DIR / "index.xlsx", index=False, sheet_name="index")
    show = ["pair", "n", "status", "a", "b", "g", "boundary", "lr", "lr_p", "v001_b", "v001_g"]
    notes = "\n".join(
        [
            "# Asymmetric DCC experiments v002",
            "",
            done,
            "",
            "## Research question",
            "",
            "After removing the v001 floor b >= 0.5 and allowing g = 0, which pairs "
            "have a likelihood-ratio rejection of symmetric DCC?",
            "",
            "## Snapshot",
            "",
            f"- Folder: `data/snapshots/{snap['manifest']['folder']}`",
            f"- {drop_note}",
            "",
            "## Parameters",
            "",
            "- Marginal model: constant-mean GARCH(1,1) via arch, z = resid/sigma.",
            "- ADCC: a, g in [0, 0.5], b in [0, 0.999], constraint a+b+g/2 < 0.999.",
            "- Nested DCC is the same likelihood at g=0.",
            "- LR = 2 * (nll_dcc - nll_adcc), floored at 0.",
            "- p-value is the chi-bar-square mixture: 0.5 * P(chi^2_1 > LR) when LR > 0, else 1.",
            "- status ok requires both optimizers to report success. check is a finite point without that flag. fail is no finite fit.",
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
                f"(v001 b was {float(focus['v001_b']):.6f}), g={float(focus['g']):.6f}, "
                f"boundary={focus['boundary']}, lr_p={float(focus['lr_p']):.4g}, status={focus['status']}."
            ),
            f"Pairs with chi-bar p below 0.05: {n_g} of 28. A g of 0 in v001 can be the old lower bound of 1e-8 rounded in the table.",
            "This is not a trading signal.",
            "",
        ]
    )
    (EXP_DIR / "NOTES.md").write_text(notes, encoding="utf-8")
    print(done, flush=True)
    return OUT_DIR / "index.xlsx"


if __name__ == "__main__":
    run()
