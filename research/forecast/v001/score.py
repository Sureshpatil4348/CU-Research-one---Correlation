"""Out-of-sample horse race. Implements research/forecast/v001/PROTOCOL.md and does not retune it."""

from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.linear_model import LogisticRegression
from statsmodels.stats.multitest import multipletests

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from shared.mt5_data import MAJOR_PAIRS, load_snapshot

EXP_DIR = Path(__file__).resolve().parent
OUT_DIR = EXP_DIR / "outputs"
PROTOCOL = EXP_DIR / "PROTOCOL.md"
PANEL = OUT_DIR / "panel.parquet"
SNAPSHOT_REL = Path("data/snapshots/2026-11-03_majors_alpari_D1")

MIN_PAST = 1000
EMBARGO = 20
BLOCK = 21
HORIZON = 20
NW_LAG = 20
MCS_BLOCK = 20
MCS_DRAWS = 400
MCS_ALPHA = 0.10
SEED = 20261103
BH_ALPHA = 0.05
BREAK_CUT = 0.30
MIN_EXPAND = 252

COMPETITORS = [
    "m01_expanding_r",
    "m07_rho_partial",
    "m10_adcc_minus_r",
    "m11_adj_gap",
    "m19_excess_lower",
    "m14_dcor",
    "m28_d_ij",
    "m28_pc1_share",
    "m28_tci",
]
BASELINE = "baseline_r20"
SECOND = "baseline_abs_gap"
DIAGNOSTIC = "diagnostic_rv20"

SHADES = (
    ("GFC", "2008-09-15", "2009-03-31"),
    ("SNB_floor", "2011-09-06", "2015-01-14"),
    ("SNB_removal", "2015-01-15", "2015-01-15"),
    ("COVID", "2020-02-20", "2020-03-31"),
    ("Y2022", "2022-02-01", "2022-10-31"),
)
SUBPERIODS = (
    ("through_2007", None, "2007-12-31"),
    ("2008_2015", "2008-01-01", "2015-12-31"),
    ("2016_2019", "2016-01-01", "2019-12-31"),
    ("2020_end", "2020-01-01", None),
)


def _protocol_hash() -> str:
    return hashlib.sha256(PROTOCOL.read_bytes()).hexdigest()


def _check_manifest(digest: str) -> None:
    path = OUT_DIR / "manifest.json"
    if not path.is_file():
        return
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("protocol_sha256") != digest and (OUT_DIR / "scores.csv").is_file():
        raise RuntimeError("PROTOCOL.md changed after scores were written. Refusing to score.")


def _prepare_frames(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    cleaned = []
    for name in MAJOR_PAIRS:
        work = frames[name].copy()
        work["time"] = pd.to_datetime(work["time"], utc=True)
        work = work.sort_values("time")
        if len(work) >= 2:
            last_tv = float(work.iloc[-1]["tick_volume"])
            prev_tv = float(work.iloc[-2]["tick_volume"])
            if prev_tv > 0 and last_tv < 0.5 * prev_tv:
                work = work.iloc[:-1]
        ret = np.log(work["close"] / work["close"].shift(1))
        cleaned.append(pd.Series(ret.to_numpy(), index=pd.DatetimeIndex(work["time"]), name=name).dropna())
    panel = pd.concat(cleaned, axis=1, join="inner").dropna().sort_index()
    panel.index = pd.to_datetime(panel.index, utc=True).normalize()
    return panel


def _t1_labels(turb: pd.Series) -> pd.Series:
    values = turb.to_numpy(dtype=float)
    n = len(values)
    fwd = np.full(n, np.nan)
    csum = np.cumsum(values)
    for t in range(n - HORIZON):
        total = csum[t + HORIZON] - csum[t]
        fwd[t] = total / HORIZON
    y = np.full(n, np.nan)
    finite_idx = np.flatnonzero(np.isfinite(fwd))
    for t in range(n):
        if not np.isfinite(fwd[t]):
            continue
        end = t - HORIZON
        if end < 0:
            continue
        past_pos = finite_idx[finite_idx <= end]
        if len(past_pos) < MIN_EXPAND:
            continue
        thresh = float(np.quantile(fwd[past_pos], 0.90))
        y[t] = 1.0 if fwd[t] > thresh else 0.0
    return pd.Series(y, index=turb.index, name="y")


def _expanding_and_forward(x: np.ndarray, y: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    n = len(x)
    count = np.arange(1, n + 1, dtype=float)
    cx = np.cumsum(x)
    cy = np.cumsum(y)
    cxx = np.cumsum(x * x)
    cyy = np.cumsum(y * y)
    cxy = np.cumsum(x * y)
    var_x = cxx - cx * cx / count
    var_y = cyy - cy * cy / count
    cov = cxy - cx * cy / count
    expanding = np.full(n, np.nan)
    ok = (count >= MIN_EXPAND) & (var_x > 0) & (var_y > 0)
    expanding[ok] = cov[ok] / np.sqrt(var_x[ok] * var_y[ok])
    forward = np.full(n, np.nan)
    for t in range(n - HORIZON):
        xs = x[t + 1 : t + 1 + HORIZON]
        ys = y[t + 1 : t + 1 + HORIZON]
        if float(np.std(xs)) == 0.0 or float(np.std(ys)) == 0.0:
            continue
        forward[t] = float(np.corrcoef(xs, ys)[0, 1])
    return expanding, forward


def _t2_labels(returns: dict[str, pd.Series]) -> pd.DataFrame:
    rows = []
    for i, left in enumerate(MAJOR_PAIRS):
        for right in MAJOR_PAIRS[i + 1 :]:
            pair = f"{left}-{right}"
            common = returns[left].index.intersection(returns[right].index).sort_values()
            x = returns[left].loc[common].to_numpy(dtype=float)
            y = returns[right].loc[common].to_numpy(dtype=float)
            expanding, forward = _expanding_and_forward(x, y)
            gap = np.abs(forward - expanding)
            label = np.full(len(common), np.nan)
            ok = np.isfinite(gap)
            label[ok] = (gap[ok] > BREAK_CUT).astype(float)
            rows.append(pd.DataFrame({"date": common, "pair": pair, "y_t2": label}))
    return pd.concat(rows, ignore_index=True)


def _auc(y: np.ndarray, p: np.ndarray) -> float:
    y = np.asarray(y)
    p = np.asarray(p)
    pos = p[y == 1]
    neg = p[y == 0]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    ranks = stats.rankdata(np.concatenate([pos, neg]))
    return float((ranks[: len(pos)].sum() - len(pos) * (len(pos) + 1) / 2.0) / (len(pos) * len(neg)))


def _fit_predict(x_train: np.ndarray, y_train: np.ndarray, x_test: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    base = float(np.mean(y_train))
    if len(np.unique(y_train)) < 2 or float(np.std(x_train)) == 0.0:
        return np.full(len(x_test), base), np.full(len(x_train), base)
    mu = float(np.mean(x_train))
    sd = float(np.std(x_train))
    if sd == 0.0:
        return np.full(len(x_test), base), np.full(len(x_train), base)
    model = LogisticRegression(C=np.inf, solver="lbfgs", max_iter=400)
    model.fit(((x_train - mu) / sd).reshape(-1, 1), y_train.astype(int))
    train_p = model.predict_proba(((x_train - mu) / sd).reshape(-1, 1))[:, 1]
    test_p = model.predict_proba(((x_test - mu) / sd).reshape(-1, 1))[:, 1]
    return test_p, train_p


def _walk_t1(frame: pd.DataFrame, column: str) -> pd.DataFrame:
    data = frame[["date", column, "y"]].dropna(subset=["y"]).sort_values("date")
    dates = data["date"].drop_duplicates().sort_values().to_list()
    if len(dates) <= MIN_PAST + EMBARGO:
        return pd.DataFrame(columns=["date", "y", "p", "signal", "loss"])
    rows = []
    origin = MIN_PAST
    while origin < len(dates):
        train_dates = dates[: origin - EMBARGO]
        test_dates = dates[origin : origin + BLOCK]
        if len(train_dates) < EMBARGO or not test_dates:
            origin += BLOCK
            continue
        train = data[data["date"].isin(train_dates)].dropna(subset=[column])
        test = data[data["date"].isin(test_dates)].dropna(subset=[column])
        if train.empty or test.empty:
            origin += BLOCK
            continue
        test_p, train_p = _fit_predict(
            train[column].to_numpy(dtype=float),
            train["y"].to_numpy(dtype=float),
            test[column].to_numpy(dtype=float),
        )
        cut = float(np.quantile(train_p, 0.80))
        y = test["y"].to_numpy(dtype=float)
        signal = (test_p > cut).astype(float)
        for dt, yi, pi, si in zip(test["date"], y, test_p, signal):
            rows.append({"date": dt, "y": yi, "p": float(pi), "signal": si, "loss": (float(pi) - yi) ** 2})
        origin += BLOCK
    return pd.DataFrame(rows)


def _walk_t2(frame: pd.DataFrame, column: str) -> tuple[pd.DataFrame, pd.Series]:
    data = frame[["date", "pair", column, "y"]].dropna(subset=["y"]).sort_values(["date", "pair"])
    dates = data["date"].drop_duplicates().sort_values().to_list()
    if len(dates) <= MIN_PAST + EMBARGO:
        empty = pd.DataFrame(columns=["date", "pair", "y", "p"])
        return empty, pd.Series(dtype=float)
    rows = []
    origin = MIN_PAST
    while origin < len(dates):
        train_dates = set(dates[: origin - EMBARGO])
        test_dates = dates[origin : origin + BLOCK]
        if len(train_dates) < EMBARGO or not test_dates:
            origin += BLOCK
            continue
        train = data[data["date"].isin(train_dates)].dropna(subset=[column])
        test = data[data["date"].isin(test_dates)].dropna(subset=[column])
        if train.empty or test.empty:
            origin += BLOCK
            continue
        test_p, train_p = _fit_predict(
            train[column].to_numpy(dtype=float),
            train["y"].to_numpy(dtype=float),
            test[column].to_numpy(dtype=float),
        )
        cut = float(np.quantile(train_p, 0.80))
        part = test[["date", "pair", "y"]].copy()
        part["p"] = test_p
        part["signal"] = (test_p > cut).astype(float)
        rows.append(part)
        origin += BLOCK
    if not rows:
        return pd.DataFrame(columns=["date", "pair", "y", "p", "signal"]), pd.Series(dtype=float)
    pred = pd.concat(rows, ignore_index=True)
    pred["loss"] = (pred["p"] - pred["y"]) ** 2
    daily = pred.groupby("date")["loss"].mean().sort_index()
    return pred, daily


def _nw_mean_se(diff: np.ndarray, lag: int) -> tuple[float, float]:
    x = np.asarray(diff, dtype=float)
    x = x[np.isfinite(x)]
    t = len(x)
    if t < lag + 5:
        return float("nan"), float("nan")
    mean = float(x.mean())
    demeaned = x - mean
    gamma0 = float(np.dot(demeaned, demeaned) / t)
    var = gamma0
    for k in range(1, lag + 1):
        weight = 1.0 - k / (lag + 1.0)
        gamma = float(np.dot(demeaned[k:], demeaned[:-k]) / t)
        var += 2.0 * weight * gamma
    if var <= 0.0:
        return mean, float("nan")
    return mean, math.sqrt(var / t)


def _mcs(loss: pd.DataFrame) -> set[str]:
    names = list(loss.columns)
    data = loss.dropna().to_numpy(dtype=float)
    if data.shape[0] < MCS_BLOCK + 5 or data.shape[1] == 0:
        return set(names)
    included = list(range(data.shape[1]))
    rng = np.random.default_rng(SEED)
    offsets = np.arange(MCS_BLOCK)
    while len(included) > 1:
        sub = data[:, included]
        d = sub - sub.mean(axis=1, keepdims=True)
        t_obs = len(d)
        n_blocks = int(math.ceil(t_obs / MCS_BLOCK))
        means = d.mean(axis=0)
        boot = np.empty((MCS_DRAWS, d.shape[1]))
        for draw in range(MCS_DRAWS):
            starts = rng.integers(0, t_obs, size=n_blocks)
            idx = (starts[:, None] + offsets[None, :]) % t_obs
            boot[draw] = d[idx.ravel()[:t_obs]].mean(axis=0)
        se = boot.std(axis=0, ddof=1)
        se[se <= 1e-15] = np.inf
        tstat = means / se
        boot_t = (boot - means) / se
        p_value = float(np.mean(boot_t.max(axis=1) >= tstat.max()))
        if p_value >= MCS_ALPHA:
            break
        included.pop(int(np.argmax(tstat)))
    return {names[i] for i in included}


def _crisis_table(pred: pd.DataFrame, calendar: pd.DatetimeIndex, feature: str) -> list[dict[str, object]]:
    signal = pred.set_index("date")["signal"].sort_index()
    rows = []
    pre_all: set[pd.Timestamp] = set()
    shade_all: set[pd.Timestamp] = set()
    for name, start, end in SHADES:
        start_ts = pd.Timestamp(start, tz="UTC")
        end_ts = pd.Timestamp(end, tz="UTC")
        shade_days = calendar[(calendar >= start_ts) & (calendar <= end_ts)]
        if len(shade_days) == 0:
            rows.append(
                {
                    "feature": feature,
                    "window": name,
                    "n_pre": 0,
                    "hit_rate": np.nan,
                    "n_shade": 0,
                    "in_shade_rate": np.nan,
                }
            )
            continue
        first = shade_days[0]
        loc = int(calendar.get_loc(first))
        pre_days = calendar[max(0, loc - HORIZON) : loc]
        pre_all.update(pre_days)
        shade_all.update(shade_days)
        pre_sig = signal.reindex(pre_days).dropna()
        shade_sig = signal.reindex(shade_days).dropna()
        rows.append(
            {
                "feature": feature,
                "window": name,
                "n_pre": int(len(pre_sig)),
                "hit_rate": float(pre_sig.mean()) if len(pre_sig) else np.nan,
                "n_shade": int(len(shade_sig)),
                "in_shade_rate": float(shade_sig.mean()) if len(shade_sig) else np.nan,
            }
        )
    outside = [dt for dt in signal.index if dt not in pre_all and dt not in shade_all]
    false_alarm = float(signal.loc[outside].mean()) if outside else np.nan
    for row in rows:
        row["false_alarm_rate"] = false_alarm
    return rows


def _score_pair(
    name: str,
    role: str,
    target: str,
    pred_loss: pd.Series,
    y: np.ndarray,
    p: np.ndarray,
    base_loss: pd.Series | None,
) -> dict[str, object]:
    if base_loss is not None:
        aligned = pd.concat([pred_loss.rename("model"), base_loss.rename("base")], axis=1, sort=False).dropna()
        loss = aligned["model"]
        diff = (aligned["model"] - aligned["base"]).to_numpy()
        mean, se = _nw_mean_se(diff, NW_LAG)
        stat = mean / se if se and np.isfinite(se) and se > 0 else float("nan")
        p_one = float(stats.norm.cdf(stat)) if np.isfinite(stat) else float("nan")
        brier_gap = float(aligned["model"].mean() - aligned["base"].mean()) if len(aligned) else float("nan")
        n = int(len(aligned))
        brier = float(aligned["model"].mean()) if len(aligned) else float("nan")
    else:
        loss = pred_loss.dropna()
        stat = float("nan")
        p_one = float("nan")
        brier_gap = 0.0
        n = int(len(loss))
        brier = float(loss.mean()) if len(loss) else float("nan")
    return {
        "feature": name,
        "target": target,
        "role": role,
        "n": n,
        "brier": brier,
        "auc": _auc(y, p),
        "brier_minus_baseline": brier_gap,
        "dm_stat": stat,
        "dm_p_one_sided": p_one,
        "bh_q": np.nan,
        "in_mcs": "",
        "beats_baseline": False,
    }


def _subperiods(target: str, losses: dict[str, pd.Series], base: pd.Series) -> list[dict[str, object]]:
    rows = []
    for period, start, end in SUBPERIODS:
        start_ts = pd.Timestamp(start, tz="UTC") if start else None
        end_ts = pd.Timestamp(end, tz="UTC") if end else None
        for name, series in losses.items():
            aligned = pd.concat([series.rename("model"), base.rename("base")], axis=1, sort=False).dropna()
            if start_ts is not None:
                aligned = aligned.loc[aligned.index >= start_ts]
            if end_ts is not None:
                aligned = aligned.loc[aligned.index <= end_ts]
            rows.append(
                {
                    "feature": name,
                    "target": target,
                    "period": period,
                    "n": int(len(aligned)),
                    "brier": float(aligned["model"].mean()) if len(aligned) else np.nan,
                    "brier_minus_baseline": float(aligned["model"].mean() - aligned["base"].mean())
                    if len(aligned)
                    else np.nan,
                }
            )
    return rows


def _overlay(basket: pd.Series, signal: pd.Series | None, name: str) -> dict[str, object]:
    if signal is None or signal.empty:
        return {"book": name, "net_log_growth": np.nan, "n_days": 0, "cost_sum": np.nan, "mean_position": np.nan}
    sig = signal.sort_index()
    pos = pd.Series(np.where(sig.to_numpy() > 0, 0.0, 1.0), index=sig.index)
    nxt = basket.sort_index().shift(-1).reindex(pos.index)
    prev = pos.shift(1)
    prev.iloc[0] = 0.0
    cost = 0.0001 * (pos - prev).abs()
    pnl = pos * nxt - cost
    pnl = pnl.dropna()
    return {
        "book": name,
        "net_log_growth": float(pnl.sum()) if len(pnl) else np.nan,
        "n_days": int(len(pnl)),
        "cost_sum": float(cost.reindex(pnl.index).sum()) if len(pnl) else np.nan,
        "mean_position": float(pos.reindex(pnl.index).mean()) if len(pnl) else np.nan,
    }


def _always_long(basket: pd.Series, index: pd.DatetimeIndex) -> dict[str, object]:
    sig = pd.Series(0.0, index=index)
    return _overlay(basket, sig, "always_long")


def run() -> None:
    digest = _protocol_hash()
    _check_manifest(digest)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    panel = pd.read_parquet(PANEL)
    panel["date"] = pd.to_datetime(panel["date"], utc=True).dt.normalize()
    snap = load_snapshot(REPO_ROOT / SNAPSHOT_REL)
    returns = _prepare_frames(snap["frames"])
    basket = returns.mean(axis=1)
    turb = returns.abs().mean(axis=1)
    t1_y = _t1_labels(turb)
    rv20 = turb.rolling(20, min_periods=20).mean()
    daily = panel.groupby("date")[
        [
            "m01_expanding_r",
            "m05_r20",
            "m05_abs_gap",
            "m07_rho_partial",
            "m10_adcc_minus_r",
            "m11_adj_gap",
            "m19_excess_lower",
            "m14_dcor",
            "m28_d_ij",
            "m28_pc1_share",
            "m28_tci",
        ]
    ].mean()
    daily[BASELINE] = daily["m05_r20"]
    daily[SECOND] = daily["m05_abs_gap"]
    daily[DIAGNOSTIC] = rv20.reindex(daily.index)
    daily["y"] = t1_y.reindex(daily.index)
    daily = daily.reset_index()
    t1_columns = [BASELINE, SECOND, *COMPETITORS, DIAGNOSTIC]
    t1_pred: dict[str, pd.DataFrame] = {}
    t1_loss: dict[str, pd.Series] = {}
    for column in t1_columns:
        pred = _walk_t1(daily, column)
        t1_pred[column] = pred
        t1_loss[column] = pred.set_index("date")["loss"] if len(pred) else pd.Series(dtype=float)
        print(f"T1 {column} n={len(pred)}", flush=True)

    pair_returns = {name: returns[name] for name in MAJOR_PAIRS}
    t2 = _t2_labels(pair_returns)
    t2_panel = panel.merge(t2, on=["date", "pair"], how="inner")
    t2_panel = t2_panel.rename(columns={"y_t2": "y"})
    t2_panel[BASELINE] = t2_panel["m05_r20"]
    t2_panel[SECOND] = t2_panel["m05_abs_gap"]
    t2_columns = [BASELINE, SECOND, *COMPETITORS]
    t2_pred: dict[str, pd.DataFrame] = {}
    t2_loss: dict[str, pd.Series] = {}
    for column in t2_columns:
        pred, daily_loss = _walk_t2(t2_panel, column)
        t2_pred[column] = pred
        t2_loss[column] = daily_loss
        print(f"T2 {column} rows={len(pred)}", flush=True)

    score_rows = []
    for target, preds, losses, columns in (
        ("T1", t1_pred, t1_loss, t1_columns),
        ("T2", t2_pred, t2_loss, t2_columns),
    ):
        base_loss = losses[BASELINE]
        base_pred = preds[BASELINE]
        for column in columns:
            if column == BASELINE:
                role = "baseline"
                base = None
            elif column == SECOND:
                role = "second_baseline"
                base = base_loss
            elif column == DIAGNOSTIC:
                role = "diagnostic"
                base = base_loss
            else:
                role = "competitor"
                base = base_loss
            pred = preds[column]
            row = _score_pair(
                column,
                role,
                target,
                losses[column],
                pred["y"].to_numpy(dtype=float) if len(pred) else np.array([]),
                pred["p"].to_numpy(dtype=float) if len(pred) else np.array([]),
                base,
            )
            if role == "baseline":
                row["auc"] = _auc(base_pred["y"].to_numpy(), base_pred["p"].to_numpy()) if len(base_pred) else np.nan
            score_rows.append(row)
        comp_idx = [
            i
            for i, row in enumerate(score_rows)
            if row["target"] == target
            and row["role"] == "competitor"
            and np.isfinite(row["dm_p_one_sided"])
        ]
        pvals = [score_rows[i]["dm_p_one_sided"] for i in comp_idx]
        if pvals:
            _reject, qvals, _, _ = multipletests(pvals, alpha=BH_ALPHA, method="fdr_bh")
            for i, qv in zip(comp_idx, qvals):
                score_rows[i]["bh_q"] = float(qv)
                score_rows[i]["beats_baseline"] = bool(
                    qv < BH_ALPHA and score_rows[i]["brier_minus_baseline"] < 0
                )
        mcs_cols = [BASELINE, *COMPETITORS]
        mcs_frame = pd.concat(
            {name: losses[name] for name in mcs_cols if len(losses[name])},
            axis=1,
            sort=False,
        ).dropna(axis=1, how="all")
        kept = _mcs(mcs_frame) if not mcs_frame.empty else set()
        for row in score_rows:
            if row["target"] == target and row["feature"] in mcs_cols:
                row["in_mcs"] = "yes" if row["feature"] in kept else "no"

    scores = pd.DataFrame(score_rows)
    winners = scores[(scores["target"] == "T1") & (scores["beats_baseline"])]
    winner = None
    if len(winners):
        winner = str(winners.sort_values("brier").iloc[0]["feature"])

    crisis_rows = []
    calendar = returns.index
    for column in t1_columns:
        if len(t1_pred[column]):
            crisis_rows.extend(_crisis_table(t1_pred[column], calendar, column))
    sub_rows = _subperiods("T1", {c: t1_loss[c] for c in t1_columns}, t1_loss[BASELINE])
    sub_rows.extend(_subperiods("T2", {c: t2_loss[c] for c in t2_columns}, t2_loss[BASELINE]))

    overlay_rows = [
        _always_long(basket, t1_pred[BASELINE]["date"] if len(t1_pred[BASELINE]) else pd.DatetimeIndex([])),
        _overlay(basket, t1_pred[BASELINE].set_index("date")["signal"] if len(t1_pred[BASELINE]) else None, BASELINE),
    ]
    if winner:
        overlay_rows.append(
            _overlay(basket, t1_pred[winner].set_index("date")["signal"], winner)
        )

    scores.to_csv(OUT_DIR / "scores.csv", index=False)
    scores.loc[scores["role"] == "competitor", ["feature", "target", "dm_stat", "dm_p_one_sided", "bh_q"]].to_csv(
        OUT_DIR / "dm.csv", index=False
    )
    scores.loc[scores["in_mcs"] != "", ["feature", "target", "in_mcs", "brier"]].to_csv(OUT_DIR / "mcs.csv", index=False)
    pd.DataFrame(crisis_rows).to_csv(OUT_DIR / "crisis.csv", index=False)
    pd.DataFrame(sub_rows).to_csv(OUT_DIR / "subperiods.csv", index=False)
    pd.DataFrame(overlay_rows).to_csv(OUT_DIR / "overlay.csv", index=False)
    manifest = {
        "protocol_sha256": digest,
        "winner_t1": winner,
        "scores": "scores.csv",
    }
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(scores[["target", "feature", "role", "n", "brier", "brier_minus_baseline", "bh_q", "beats_baseline", "in_mcs"]].to_string(index=False), flush=True)
    print(f"winner={winner}", flush=True)


if __name__ == "__main__":
    run()
