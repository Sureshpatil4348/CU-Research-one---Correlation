"""v003: causal ADCC minus expanding Pearson. Parameters refit each 31 December."""

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
MIN_N = 252
STARTS = ((0.05, 0.90, 0.02), (0.03, 0.40, 0.05))


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


def _year_ends(index: pd.DatetimeIndex) -> list[pd.Timestamp]:
    ends: list[pd.Timestamp] = []
    last_year = int(index.max().year)
    for year in range(2006, last_year):
        target = pd.Timestamp(year=year, month=12, day=31, tz="UTC")
        eligible = index[index <= target]
        if len(eligible) == 0:
            continue
        chosen = pd.Timestamp(eligible[-1])
        if chosen.year == year:
            ends.append(chosen)
    return ends


def _fit_garch(ret: pd.Series) -> dict[str, object]:
    series = pd.Series(ret.to_numpy(dtype=float) * 100.0)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model = arch_model(series, mean="Constant", vol="Garch", p=1, q=1, dist="normal")
        result = model.fit(disp="off", show_warning=False)
    resid = np.asarray(result.resid, dtype=float)
    sigma = np.asarray(result.conditional_volatility, dtype=float)
    params = result.params
    return {
        "z": pd.Series(resid / sigma, index=ret.index),
        "mu": float(params["mu"]),
        "omega": float(params["omega"]),
        "alpha": float(params["alpha[1]"]),
        "beta": float(params["beta[1]"]),
        "last_resid": float(resid[-1]),
        "last_sigma2": float(sigma[-1] ** 2),
    }


def _forward_z(fit: dict[str, object], ret: pd.Series) -> pd.Series:
    mu = float(fit["mu"])
    omega = float(fit["omega"])
    alpha = float(fit["alpha"])
    beta = float(fit["beta"])
    resid_prev = float(fit["last_resid"])
    sig2 = float(fit["last_sigma2"])
    values = ret.to_numpy(dtype=float) * 100.0
    z = np.empty(len(values))
    for t, value in enumerate(values):
        sig2 = omega + alpha * resid_prev * resid_prev + beta * sig2
        if sig2 < 1e-12:
            sig2 = 1e-12
        resid = value - mu
        z[t] = resid / math.sqrt(sig2)
        resid_prev = resid
    return pd.Series(z, index=ret.index)


def _neg_loglik(a, b, g, z1, z2, n1, n2, q12, n11, n22, n12) -> float:
    if a < 0.0 or b < 0.0 or g < 0.0 or a + b + 0.5 * g >= 0.999:
        return 1e12
    a11 = (1.0 - a - b) - g * n11
    a22 = (1.0 - a - b) - g * n22
    a12 = (1.0 - a - b) * q12 - g * n12
    q11 = 1.0
    q22 = 1.0
    q12_prev = q12
    ll = 0.0
    for t in range(1, len(z1)):
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


def _filter_rho(z1, z2, a, b, g, q12, n11, n22, n12) -> np.ndarray:
    n1 = np.minimum(z1, 0.0)
    n2 = np.minimum(z2, 0.0)
    a11 = (1.0 - a - b) - g * n11
    a22 = (1.0 - a - b) - g * n22
    a12 = (1.0 - a - b) * q12 - g * n12
    q11 = 1.0
    q22 = 1.0
    q12_prev = q12
    rho = np.empty(len(z1))
    rho[0] = q12
    for t in range(1, len(z1)):
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
        rho[t] = r
    return rho


def _estimate(z1: np.ndarray, z2: np.ndarray) -> tuple[float, float, float, float, float, float, float] | None:
    q12 = float(np.corrcoef(z1, z2)[0, 1])
    n1 = np.minimum(z1, 0.0)
    n2 = np.minimum(z2, 0.0)
    n11 = float(np.mean(n1 * n1))
    n22 = float(np.mean(n2 * n2))
    n12 = float(np.mean(n1 * n2))

    def objective(params: np.ndarray) -> float:
        return _neg_loglik(
            float(params[0]), float(params[1]), float(params[2]), z1, z2, n1, n2, q12, n11, n22, n12
        )

    bounds = [(0.0, 0.5), (0.0, 0.999), (0.0, 0.5)]
    cons = {"type": "ineq", "fun": lambda p: 0.999 - p[0] - p[1] - 0.5 * p[2]}
    best = None
    for start in STARTS:
        res = optimize.minimize(
            objective,
            x0=np.array(start, dtype=float),
            method="SLSQP",
            bounds=bounds,
            constraints=cons,
            options={"maxiter": 250, "ftol": 1e-8},
        )
        if best is None or float(res.fun) < float(best.fun):
            best = res
    if best is None or float(best.fun) >= 1e11:
        return None
    a = max(0.0, float(best.x[0]))
    b = max(0.0, float(best.x[1]))
    g = max(0.0, float(best.x[2]))
    if a + b + 0.5 * g >= 0.999:
        scale = 0.998 / (a + b + 0.5 * g)
        a *= scale
        b *= scale
        g *= scale
    return a, b, g, q12, n11, n22, n12


def _expanding_corr(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    count = np.arange(1, len(x) + 1, dtype=float)
    cx = np.cumsum(x)
    cy = np.cumsum(y)
    cxx = np.cumsum(x * x)
    cyy = np.cumsum(y * y)
    cxy = np.cumsum(x * y)
    var_x = cxx - cx * cx / count
    var_y = cyy - cy * cy / count
    cov = cxy - cx * cy / count
    out = np.full(len(x), np.nan)
    ok = (count >= MIN_N) & (var_x > 0) & (var_y > 0)
    out[ok] = cov[ok] / np.sqrt(var_x[ok] * var_y[ok])
    return out


def run() -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    snap = load_snapshot(REPO_ROOT / SNAPSHOT_REL)
    frames = snap["frames"]
    drop_note = _prepare_frames(frames)
    returns = {
        name: frames[name].set_index("time")["log_return"].dropna().sort_index()
        for name in MAJOR_PAIRS
    }
    common = returns[MAJOR_PAIRS[0]].index
    for name in MAJOR_PAIRS[1:]:
        common = common.intersection(returns[name].index)
    common = common.sort_values()
    ends = _year_ends(common)
    if not ends or ends[0].year != 2006:
        raise RuntimeError(f"Expected a 2006 year-end, got {ends[:1]}")
    print("year ends", [str(ts.date()) for ts in ends], flush=True)

    fits: dict[str, dict[pd.Timestamp, dict[str, object]]] = {name: {} for name in MAJOR_PAIRS}
    forwards: dict[str, dict[pd.Timestamp, pd.Series]] = {name: {} for name in MAJOR_PAIRS}
    for name, ret in returns.items():
        for i, end in enumerate(ends):
            sample = ret.loc[:end]
            fit = _fit_garch(sample)
            fits[name][end] = fit
            nxt = ends[i + 1] if i + 1 < len(ends) else None
            if nxt is None:
                fwd_ret = ret.loc[ret.index > end]
            else:
                fwd_ret = ret.loc[(ret.index > end) & (ret.index < nxt)]
            forwards[name][end] = _forward_z(fit, fwd_ret) if len(fwd_ret) else pd.Series(dtype=float)
        print(f"garch {name}", flush=True)

    parts = []
    failed_segments = 0
    for left, right in itertools.combinations(MAJOR_PAIRS, 2):
        pair = f"{left}-{right}"
        a = returns[left]
        b = returns[right]
        dates = a.index.intersection(b.index).sort_values()
        xs = a.loc[dates].to_numpy(dtype=float)
        ys = b.loc[dates].to_numpy(dtype=float)
        expanding = pd.Series(_expanding_corr(xs, ys), index=dates)
        rho = pd.Series(np.nan, index=dates)
        for i, end in enumerate(ends):
            nxt = ends[i + 1] if i + 1 < len(ends) else None
            z1 = fits[left][end]["z"]
            z2 = fits[right][end]["z"]
            est_index = z1.index.intersection(z2.index).sort_values()
            if len(est_index) < MIN_N:
                failed_segments += 1
                continue
            est = _estimate(z1.loc[est_index].to_numpy(dtype=float), z2.loc[est_index].to_numpy(dtype=float))
            if est is None:
                failed_segments += 1
                continue
            aa, bb, g, q12, n11, n22, n12 = est
            f1 = forwards[left][end]
            f2 = forwards[right][end]
            f_index = f1.index.intersection(f2.index).sort_values() if len(f1) and len(f2) else pd.DatetimeIndex([])
            path_index = est_index.append(f_index)
            z1_path = pd.concat([z1.loc[est_index], f1.reindex(f_index)]).to_numpy(dtype=float)
            z2_path = pd.concat([z2.loc[est_index], f2.reindex(f_index)]).to_numpy(dtype=float)
            path = _filter_rho(z1_path, z2_path, aa, bb, g, q12, n11, n22, n12)
            rho_path = pd.Series(path, index=path_index)
            keep = [end] if end in rho_path.index else []
            if nxt is None:
                keep_forward = f_index
            else:
                keep_forward = f_index[f_index < nxt]
            rho.loc[rho.index.intersection(pd.DatetimeIndex(list(keep)).append(keep_forward))] = rho_path.reindex(
                rho.index.intersection(pd.DatetimeIndex(list(keep)).append(keep_forward))
            ).to_numpy()
        gap = rho - expanding
        part = pd.DataFrame(
            {
                "date": dates,
                "pair": pair,
                "m10_adcc_minus_r": gap.to_numpy(dtype=float),
                "feature_asof": dates,
            }
        )
        parts.append(part.loc[np.isfinite(part["m10_adcc_minus_r"])].reset_index(drop=True))
        print(f"{pair} rows={int(np.isfinite(gap).sum())} failed_segments={failed_segments}", flush=True)

    out = pd.concat(parts, ignore_index=True)
    if len(out) and (out["feature_asof"] > out["date"]).any():
        raise RuntimeError("Feature as-of is after the row date")
    path = OUT_DIR / "features.parquet"
    out.to_parquet(path, index=False)
    first = ends[0].date().isoformat()
    notes = "\n".join(
        [
            "# Asymmetric DCC experiments v003",
            "",
            "Done: ADCC rho minus expanding Pearson, with parameters fit only on data through each year-end.",
            "",
            "## Research question",
            "",
            "What is the time-t gap between ADCC and expanding Pearson when neither the GARCH parameters nor the ADCC parameters use future returns?",
            "",
            "## Snapshot",
            "",
            f"- Folder: `data/snapshots/{snap['manifest']['folder']}`",
            f"- {drop_note}",
            "",
            "## Parameters",
            "",
            f"- First refit: last common trading day on or before 2006-12-31 ({first}). Then each later 31 December through the year before the sample's last year.",
            "- GARCH(1,1) is fit on each symbol through the year-end. Later days in that vintage use the frozen recursion. The next year-end replaces the parameters; it does not rewrite earlier feature dates.",
            "- ADCC a, b, g and the targeting matrices are fit on the pair's standardized residuals through that year-end. Two starts: (0.05, 0.90, 0.02) and (0.03, 0.40, 0.05).",
            "- Days before the first refit are missing.",
            "- Column: m10_adcc_minus_r. No label column.",
            "- v001 and v002 files were not edited.",
            "",
            f"Rows written: {len(out)}. Failed pair-year segments: {failed_segments}.",
            "",
        ]
    )
    (EXP_DIR / "NOTES.md").write_text(notes, encoding="utf-8")
    print(f"rows={len(out)} failed_segments={failed_segments}", flush=True)
    return path


if __name__ == "__main__":
    run()
