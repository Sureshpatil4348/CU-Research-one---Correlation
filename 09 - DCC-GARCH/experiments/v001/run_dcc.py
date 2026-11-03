"""DCC-GARCH on Alpari D1 majors: one Word report, HTML table, and Excel per unique pair."""

from __future__ import annotations

import itertools
import math
import sys
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from arch import arch_model
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt
from scipy import optimize, stats

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from shared.mt5_data import MAJOR_PAIRS, load_snapshot

SNAPSHOT_REL = Path("data/snapshots/2026-11-03_majors_alpari_D1")
EXP_DIR = Path(__file__).resolve().parent
OUT_DIR = EXP_DIR / "outputs"
FIG_DIR = OUT_DIR / "figures"
OHLCV = ["open", "high", "low", "close", "tick_volume", "spread", "real_volume"]
BURN_IN = 60
METHOD_NOTE = (
    "DCC-GARCH first fits a constant-mean GARCH(1,1) on each matched daily "
    "log return of close, ln(close_t / close_t-1), then updates Engle (2002) "
    "dynamic conditional correlation on the standardised shocks "
    "z = residual / conditional sigma. Quotes are not inverted. Correlation "
    "targeting sets Q_bar to the sample correlation of z; a and b are "
    "estimated by maximising the bivariate Gaussian DCC likelihood with "
    "a >= 0, b >= 0, and a + b < 1. Path summaries ignore the first 60 "
    "updates. The headline is rho on the last day. Same-sample Pearson r on "
    "log returns is a side check only. A high |rho| does not prove cause, "
    "lead-lag, or a trading signal."
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


def _pair_table(
    left: pd.DataFrame,
    right: pd.DataFrame,
    left_name: str,
    right_name: str,
) -> pd.DataFrame:
    a = left.set_index("time")
    b = right.set_index("time")
    common = a.index.intersection(b.index).sort_values()
    cols: dict[str, pd.Series] = {"time": pd.Series(common, index=common)}
    for col in OHLCV + ["log_return"]:
        cols[f"{left_name}_{col}"] = a.loc[common, col]
        cols[f"{right_name}_{col}"] = b.loc[common, col]
    table = pd.DataFrame(cols)
    table = table.dropna(subset=[f"{left_name}_log_return", f"{right_name}_log_return"])
    return table.reset_index(drop=True)


def _fit_garch(returns: np.ndarray) -> dict[str, object]:
    """Fit constant-mean GARCH(1,1); scale percent for numerical stability."""
    series = pd.Series(returns * 100.0)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model = arch_model(series, mean="Constant", vol="Garch", p=1, q=1, dist="normal")
        result = model.fit(disp="off", show_warning=False)
    # Residuals and conditional vol are in percent units; z is unit-free.
    resid = np.asarray(result.resid, dtype=float)
    sigma_pct = np.asarray(result.conditional_volatility, dtype=float)
    sigma = sigma_pct / 100.0
    z = resid / sigma_pct
    params = result.params
    return {
        "resid": resid / 100.0,
        "sigma": sigma,
        "z": z,
        "mu": float(params.get("mu", 0.0)) / 100.0,
        "omega": float(params.get("omega", float("nan"))),
        "alpha": float(params.get("alpha[1]", float("nan"))),
        "beta": float(params.get("beta[1]", float("nan"))),
        "loglik": float(result.loglikelihood),
    }


def _dcc_path(z1: np.ndarray, z2: np.ndarray, a: float, b: float, q_bar: np.ndarray) -> dict[str, np.ndarray]:
    n = len(z1)
    q11 = np.empty(n)
    q22 = np.empty(n)
    q12 = np.empty(n)
    rho = np.empty(n)
    q11_prev = float(q_bar[0, 0])
    q22_prev = float(q_bar[1, 1])
    q12_prev = float(q_bar[0, 1])
    intercept = 1.0 - a - b
    for t in range(n):
        if t == 0:
            q11[t] = q11_prev
            q22[t] = q22_prev
            q12[t] = q12_prev
        else:
            z1p = float(z1[t - 1])
            z2p = float(z2[t - 1])
            q11[t] = intercept * q_bar[0, 0] + a * z1p * z1p + b * q11_prev
            q22[t] = intercept * q_bar[1, 1] + a * z2p * z2p + b * q22_prev
            q12[t] = intercept * q_bar[0, 1] + a * z1p * z2p + b * q12_prev
            q11_prev, q22_prev, q12_prev = q11[t], q22[t], q12[t]
        denom = math.sqrt(max(q11[t], 1e-12) * max(q22[t], 1e-12))
        rho[t] = float(np.clip(q12[t] / denom, -0.999999, 0.999999))
    return {"q11": q11, "q22": q22, "q12": q12, "rho": rho}


def _dcc_neg_loglik(params: np.ndarray, z1: np.ndarray, z2: np.ndarray, q_bar: np.ndarray) -> float:
    a, b = float(params[0]), float(params[1])
    if a < 0 or b < 0 or a + b >= 1:
        return 1e12
    path = _dcc_path(z1, z2, a, b, q_bar)
    rho = path["rho"]
    # Use t>=1; skip burn where path equals Q_bar seed only at t=0.
    ll = 0.0
    for t in range(1, len(z1)):
        r = float(rho[t])
        if abs(r) >= 0.999999:
            return 1e12
        z_i = float(z1[t])
        z_j = float(z2[t])
        # log det R + z' R^{-1} z for 2x2 corr matrix
        ll += math.log(1.0 - r * r) + (z_i * z_i - 2.0 * r * z_i * z_j + z_j * z_j) / (1.0 - r * r)
    return 0.5 * ll


def _estimate_dcc(z1: np.ndarray, z2: np.ndarray) -> tuple[float, float, np.ndarray]:
    q_bar = np.corrcoef(z1, z2)
    # Ensure PSD-ish diagonal ones
    q_bar = np.array([[1.0, q_bar[0, 1]], [q_bar[0, 1], 1.0]], dtype=float)
    bounds = [(1e-8, 0.3), (0.5, 0.999)]
    cons = {"type": "ineq", "fun": lambda p: 0.999 - p[0] - p[1]}
    best = None
    for start in ((0.05, 0.90), (0.02, 0.95), (0.10, 0.80), (0.01, 0.97)):
        res = optimize.minimize(
            _dcc_neg_loglik,
            x0=np.array(start, dtype=float),
            args=(z1, z2, q_bar),
            method="SLSQP",
            bounds=bounds,
            constraints=cons,
            options={"maxiter": 300, "ftol": 1e-10},
        )
        if best is None or res.fun < best.fun:
            best = res
    if best is None or not np.isfinite(best.fun):
        raise RuntimeError("DCC estimation failed")
    a, b = float(best.x[0]), float(best.x[1])
    a = max(0.0, a)
    b = max(0.0, b)
    if a + b >= 1.0:
        scale = 0.999 / (a + b)
        a *= scale
        b *= scale
    return a, b, q_bar


def _path_stats(rho: np.ndarray) -> dict[str, float]:
    latest = float(rho[-1]) if len(rho) else float("nan")
    post = rho[BURN_IN:] if len(rho) > BURN_IN else rho
    valid = post[~np.isnan(post)]
    n_post = int(len(valid))
    if n_post == 0:
        return {
            "latest_rho": latest,
            "mean": float("nan"),
            "median": float("nan"),
            "min": float("nan"),
            "max": float("nan"),
            "std": float("nan"),
            "pct_abs_ge_0_4": float("nan"),
            "pct_abs_ge_0_7": float("nan"),
            "n_post_burn": 0.0,
        }
    abs_r = np.abs(valid)
    return {
        "latest_rho": latest,
        "mean": float(np.mean(valid)),
        "median": float(np.median(valid)),
        "min": float(np.min(valid)),
        "max": float(np.max(valid)),
        "std": float(np.std(valid, ddof=1)) if n_post > 1 else 0.0,
        "pct_abs_ge_0_4": float(100.0 * np.mean(abs_r >= 0.4)),
        "pct_abs_ge_0_7": float(100.0 * np.mean(abs_r >= 0.7)),
        "n_post_burn": float(n_post),
    }


def _strength_label(value: float) -> str:
    if math.isnan(value):
        return "undefined"
    if abs(value) >= 0.7:
        return "strong"
    if abs(value) >= 0.4:
        return "moderate"
    return "weak"


def _fmt(value: float, digits: int = 4) -> str:
    if math.isnan(value):
        return "n/a"
    return f"{value:.{digits}f}"


def _conclusion(left: str, right: str, stats_row: dict[str, float]) -> str:
    latest = stats_row["latest_rho"]
    n = int(stats_row["n"])
    strength = _strength_label(latest)
    direction = "positive" if latest >= 0 else "negative"
    return (
        f"Over {n} matched daily log-return rows for {left} and {right} "
        f"(broker quote directions unchanged), latest DCC rho is "
        f"{_fmt(latest, 4)} ({direction}, {strength} conditional linear link "
        f"in this sample) with fitted a={_fmt(stats_row['a'], 4)}, "
        f"b={_fmt(stats_row['b'], 4)} (a+b={_fmt(stats_row['a'] + stats_row['b'], 4)}). "
        f"After a {BURN_IN}-day burn-in, path mean is {_fmt(stats_row['mean'], 4)} "
        f"and std is {_fmt(stats_row['std'], 4)}. Same-sample Pearson r is "
        f"{_fmt(stats_row['pearson_r'], 4)} (latest rho minus r = "
        f"{_fmt(stats_row['latest_minus_r'], 4)}). This does not establish "
        f"cause, lead-lag, or a lasting trading rule."
    )


def _save_figures(
    table: pd.DataFrame,
    left: str,
    right: str,
    stem: str,
    pearson_r: float,
) -> dict[str, Path]:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    times = pd.to_datetime(table["time"], utc=True)

    fig, ax1 = plt.subplots(figsize=(10, 4.2))
    ax2 = ax1.twinx()
    ax1.plot(times, table[f"{left}_close"], color="#1f77b4", linewidth=0.8, label=left)
    ax2.plot(times, table[f"{right}_close"], color="#ff7f0e", linewidth=0.8, label=right)
    ax1.set_ylabel(f"{left} close")
    ax2.set_ylabel(f"{right} close")
    ax1.set_title(f"Daily closes: {left} and {right}")
    lines = ax1.get_lines() + ax2.get_lines()
    ax1.legend(lines, [left, right], loc="upper left")
    fig.tight_layout()
    paths["closes"] = FIG_DIR / f"{stem}_closes.png"
    fig.savefig(paths["closes"], dpi=120)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 4.2))
    ax.plot(times, table[f"{left}_log_return"], color="#1f77b4", linewidth=0.6, label=left)
    ax.plot(times, table[f"{right}_log_return"], color="#ff7f0e", linewidth=0.6, label=right)
    ax.set_title(f"Daily log returns: {left} and {right}")
    ax.set_ylabel("log return")
    ax.legend(loc="upper left")
    fig.tight_layout()
    paths["returns"] = FIG_DIR / f"{stem}_returns.png"
    fig.savefig(paths["returns"], dpi=120)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 4.2))
    rho = table["rho_t"].to_numpy(dtype=float).copy()
    if len(rho) > BURN_IN:
        rho[:BURN_IN] = np.nan
    ax.plot(times, rho, color="#2ca02c", linewidth=0.8, label="DCC rho")
    ax.axhline(
        pearson_r,
        color="#d62728",
        linewidth=1.0,
        linestyle="--",
        label=f"Pearson r={pearson_r:.3f}",
    )
    ax.axhline(0, color="gray", linewidth=0.5)
    ax.set_ylim(-1.05, 1.05)
    ax.set_title(f"DCC rho path (burn-in {BURN_IN} days blanked): {left} and {right}")
    ax.set_ylabel("rho_t")
    ax.legend(loc="upper left")
    fig.tight_layout()
    paths["dcc"] = FIG_DIR / f"{stem}_dcc.png"
    fig.savefig(paths["dcc"], dpi=120)
    plt.close(fig)

    return paths


def _add_heading(doc: Document, text: str, level: int = 1) -> None:
    doc.add_heading(text, level=level)


def _add_para(doc: Document, text: str, bold: bool = False) -> None:
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.font.size = Pt(10)
    run.bold = bold


def _add_small_table(doc: Document, frame: pd.DataFrame) -> None:
    headers = list(frame.columns)
    word_table = doc.add_table(rows=1 + len(frame), cols=len(headers))
    word_table.style = "Table Grid"
    for i, name in enumerate(headers):
        word_table.rows[0].cells[i].text = str(name)
    values = frame.copy()
    if "time" in values.columns:
        values["time"] = pd.to_datetime(values["time"], utc=True).dt.strftime("%Y-%m-%d")
    for r_i, row in enumerate(values.itertuples(index=False, name=None)):
        cells = word_table.rows[r_i + 1].cells
        for c_i, value in enumerate(row):
            if isinstance(value, float):
                cells[c_i].text = f"{value:.8g}"
            else:
                cells[c_i].text = str(value)


def _write_word(
    table: pd.DataFrame,
    left: str,
    right: str,
    left_broker: str,
    right_broker: str,
    stats_row: dict[str, float],
    garch_left: dict[str, object],
    garch_right: dict[str, object],
    drop_note: str,
    snapshot_name: str,
    fig_paths: dict[str, Path],
    xlsx_name: str,
    out_path: Path,
) -> None:
    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(10)

    _add_heading(doc, f"DCC-GARCH correlation: {left} and {right}", 0)
    _add_para(
        doc,
        "Method 09 / GARCH(1,1) + Engle DCC / Alpari D1 full available history",
    )

    _add_heading(doc, "Study setup", 1)
    first = pd.to_datetime(table["time"].iloc[0], utc=True).date().isoformat()
    last = pd.to_datetime(table["time"].iloc[-1], utc=True).date().isoformat()
    setup_lines = [
        f"Logical pair: {left} , {right}",
        f"Broker symbols: {left_broker} , {right_broker}",
        f"Snapshot: {snapshot_name}",
        "Timeframe: D1",
        f"Matched return window: {first} to {last} (UTC bar dates)",
        f"Matched return count n: {int(stats_row['n'])}",
        drop_note,
        (
            f"{left} GARCH(1,1): mu={_fmt(float(garch_left['mu']), 6)}, "
            f"omega={_fmt(float(garch_left['omega']), 6)}, "
            f"alpha={_fmt(float(garch_left['alpha']), 6)}, "
            f"beta={_fmt(float(garch_left['beta']), 6)}"
        ),
        (
            f"{right} GARCH(1,1): mu={_fmt(float(garch_right['mu']), 6)}, "
            f"omega={_fmt(float(garch_right['omega']), 6)}, "
            f"alpha={_fmt(float(garch_right['alpha']), 6)}, "
            f"beta={_fmt(float(garch_right['beta']), 6)}"
        ),
        (
            f"DCC: a={_fmt(stats_row['a'], 6)}, b={_fmt(stats_row['b'], 6)}, "
            f"a+b={_fmt(stats_row['a'] + stats_row['b'], 6)}"
        ),
        f"Burn-in ignored in path summaries and chart: first {BURN_IN} updates",
        f"Complete matched rows (Excel): {xlsx_name}",
        f"Complete matched rows (HTML table): {xlsx_name.replace('.xlsx', '_data.html')}",
    ]
    for line in setup_lines:
        _add_para(doc, line)

    _add_heading(doc, "Method carried forward", 1)
    _add_para(doc, METHOD_NOTE)

    _add_heading(doc, "Results", 1)
    _add_para(doc, f"Latest DCC rho: {_fmt(stats_row['latest_rho'], 6)}")
    _add_para(
        doc,
        f"Post-burn-in path (n={int(stats_row['n_post_burn'])}): "
        f"mean={_fmt(stats_row['mean'], 6)}, "
        f"median={_fmt(stats_row['median'], 6)}, "
        f"min={_fmt(stats_row['min'], 6)}, "
        f"max={_fmt(stats_row['max'], 6)}, "
        f"std={_fmt(stats_row['std'], 6)}",
    )
    _add_para(
        doc,
        f"Share of post-burn-in days with |rho| >= 0.4: "
        f"{_fmt(stats_row['pct_abs_ge_0_4'], 2)}%; "
        f"|rho| >= 0.7: {_fmt(stats_row['pct_abs_ge_0_7'], 2)}%",
    )
    _add_para(doc, f"Same-sample Pearson r: {_fmt(stats_row['pearson_r'], 6)}")
    _add_para(doc, f"Latest rho minus r: {_fmt(stats_row['latest_minus_r'], 6)}")

    _add_heading(doc, "Conclusion", 1)
    _add_para(doc, _conclusion(left, right, stats_row))

    _add_heading(doc, "Charts", 1)
    for key, title in (
        ("closes", "Daily closes"),
        ("returns", "Daily log returns"),
        ("dcc", "DCC rho path with Pearson r reference"),
    ):
        _add_para(doc, title, bold=True)
        doc.add_picture(str(fig_paths[key]), width=Inches(6.2))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

    _add_heading(doc, "Data report", 1)
    _add_para(
        doc,
        "Every matched row that entered the DCC recursion is stored in the "
        f"sibling Excel workbook named {xlsx_name}. Embedding all rows as a "
        "Word table is impractical at this length; the Word file holds the "
        "column list, column summaries, and the first and last 15 matched rows.",
    )
    _add_para(doc, "Columns: " + ", ".join(table.columns))
    numeric_cols = [c for c in table.columns if c != "time"]
    summary = (
        table[numeric_cols].describe().T.reset_index().rename(columns={"index": "column"})
    )
    _add_para(doc, "Column summaries (matched calculation rows)", bold=True)
    _add_small_table(doc, summary.round(8))

    preview_cols = [
        "time",
        f"{left}_log_return",
        f"{right}_log_return",
        f"{left}_sigma",
        f"{right}_sigma",
        f"{left}_z",
        f"{right}_z",
        "q11",
        "q22",
        "q12",
        "rho_t",
    ]
    _add_para(doc, "First 15 matched rows (selected columns)", bold=True)
    _add_small_table(doc, table.loc[:, preview_cols].head(15))
    _add_para(doc, "Last 15 matched rows (selected columns)", bold=True)
    _add_small_table(doc, table.loc[:, preview_cols].tail(15))

    doc.save(out_path)


def _cross_pair_conclusion(index_rows: list[dict[str, object]]) -> list[str]:
    ok = [row for row in index_rows if row.get("status") == "ok"]
    if not ok:
        return [
            "## Cross-pair conclusion",
            "",
            "No successful DCC fits to summarise.",
            "",
        ]
    by_rho = sorted(ok, key=lambda row: float(row["latest_rho"]))
    by_abs_gap = sorted(
        ok,
        key=lambda row: abs(float(row["latest_minus_r"])),
        reverse=True,
    )
    strongest_pos = by_rho[-1]
    strongest_neg = by_rho[0]
    near_zero = sorted(ok, key=lambda row: abs(float(row["latest_rho"])))[:3]
    top_gaps = by_abs_gap[:3]
    return [
        "## Cross-pair conclusion",
        "",
        "Reading of the successful-pair index only. Not a 29th pair analysis "
        "and not a trading signal.",
        "",
        (
            f"Strongest positive latest DCC rho: {strongest_pos['pair']} "
            f"(latest_rho={float(strongest_pos['latest_rho']):.4f}, "
            f"n={strongest_pos['n']})."
        ),
        (
            f"Strongest negative latest DCC rho: {strongest_neg['pair']} "
            f"(latest_rho={float(strongest_neg['latest_rho']):.4f}, "
            f"n={strongest_neg['n']})."
        ),
        "Nearest-to-zero latest DCC rho: "
        + "; ".join(
            f"{row['pair']} (latest_rho={float(row['latest_rho']):.4f})"
            for row in near_zero
        )
        + ".",
        "Largest |latest rho minus Pearson r| gaps: "
        + "; ".join(
            f"{row['pair']} (gap={float(row['latest_minus_r']):.4f}, "
            f"latest_rho={float(row['latest_rho']):.4f}, "
            f"r={float(row['pearson_r']):.4f})"
            for row in top_gaps
        )
        + ". A large gap can flag a recent conditional regime versus the "
        "full-sample mean; inspect that pair's DCC path before treating "
        "either score as settled.",
        "",
    ]


def run() -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    snap = load_snapshot(REPO_ROOT / SNAPSHOT_REL)
    manifest = snap["manifest"]
    snapshot_name = manifest["folder"]
    broker_map = {row["logical"]: row["resolved"] for row in manifest["symbols"]}
    frames, drop_note = _prepare_frames(snap["frames"])

    index_rows: list[dict[str, object]] = []
    failures: list[str] = []
    pairs = list(itertools.combinations(MAJOR_PAIRS, 2))

    for left, right in pairs:
        table = _pair_table(frames[left], frames[right], left, right)
        x = table[f"{left}_log_return"].to_numpy(dtype=float)
        y = table[f"{right}_log_return"].to_numpy(dtype=float)
        stem = f"{left}-{right}_DCC_D1"
        try:
            g_left = _fit_garch(x)
            g_right = _fit_garch(y)
            z1 = np.asarray(g_left["z"], dtype=float)
            z2 = np.asarray(g_right["z"], dtype=float)
            a, b, q_bar = _estimate_dcc(z1, z2)
            path = _dcc_path(z1, z2, a, b, q_bar)
        except Exception as exc:  # noqa: BLE001 - record and continue
            msg = f"{left}-{right}: {exc}"
            failures.append(msg)
            index_rows.append(
                {
                    "pair": f"{left}-{right}",
                    "n": len(table),
                    "status": "failed",
                    "error": str(exc),
                    "latest_rho": float("nan"),
                    "mean": float("nan"),
                    "std": float("nan"),
                    "min": float("nan"),
                    "max": float("nan"),
                    "a": float("nan"),
                    "b": float("nan"),
                    "pearson_r": float("nan"),
                    "latest_minus_r": float("nan"),
                    "docx": "",
                    "xlsx": "",
                    "html": "",
                }
            )
            print(f"FAILED {stem}: {exc}", flush=True)
            continue

        table = table.copy()
        table[f"{left}_sigma"] = g_left["sigma"]
        table[f"{right}_sigma"] = g_right["sigma"]
        table[f"{left}_z"] = z1
        table[f"{right}_z"] = z2
        table["q11"] = path["q11"]
        table["q22"] = path["q22"]
        table["q12"] = path["q12"]
        table["rho_t"] = path["rho"]

        path_stats = _path_stats(path["rho"])
        pearson_r = float(stats.pearsonr(x, y).statistic)
        stats_row = {
            "n": float(len(table)),
            "a": a,
            "b": b,
            "pearson_r": pearson_r,
            "latest_minus_r": path_stats["latest_rho"] - pearson_r,
            **path_stats,
        }

        fig_paths = _save_figures(table, left, right, stem, pearson_r)
        xlsx_path = OUT_DIR / f"{stem}.xlsx"
        excel_frame = table.copy()
        excel_frame["time"] = pd.to_datetime(excel_frame["time"], utc=True).dt.strftime(
            "%Y-%m-%d"
        )
        excel_frame.to_excel(xlsx_path, index=False, sheet_name="matched_rows")

        html_path = OUT_DIR / f"{stem}_data.html"
        html_path.write_text(
            (
                f"<!DOCTYPE html><html><head><meta charset='utf-8'>"
                f"<title>{stem} data</title></head><body>"
                f"<h1>{left} and {right}: matched rows used for DCC-GARCH</h1>"
                f"<p>n={int(stats_row['n'])}. Complete archive also in "
                f"{xlsx_path.name}.</p>"
                + excel_frame.to_html(index=False)
                + "</body></html>"
            ),
            encoding="utf-8",
        )

        docx_path = OUT_DIR / f"{stem}.docx"
        _write_word(
            table=table,
            left=left,
            right=right,
            left_broker=broker_map[left],
            right_broker=broker_map[right],
            stats_row=stats_row,
            garch_left=g_left,
            garch_right=g_right,
            drop_note=drop_note,
            snapshot_name=snapshot_name,
            fig_paths=fig_paths,
            xlsx_name=xlsx_path.name,
            out_path=docx_path,
        )

        index_rows.append(
            {
                "pair": f"{left}-{right}",
                "n": int(stats_row["n"]),
                "status": "ok",
                "error": "",
                "latest_rho": stats_row["latest_rho"],
                "mean": stats_row["mean"],
                "std": stats_row["std"],
                "min": stats_row["min"],
                "max": stats_row["max"],
                "a": a,
                "b": b,
                "pearson_r": pearson_r,
                "latest_minus_r": stats_row["latest_minus_r"],
                "docx": docx_path.name,
                "xlsx": xlsx_path.name,
                "html": html_path.name,
            }
        )
        print(
            f"Wrote {docx_path.name}  latest_rho={stats_row['latest_rho']:.4f}  "
            f"a={a:.4f} b={b:.4f}",
            flush=True,
        )

    index = pd.DataFrame(index_rows)
    index.to_excel(OUT_DIR / "index.xlsx", index=False, sheet_name="index")

    notes = [
        "# DCC-GARCH experiments v001",
        "",
        "## Research question",
        "",
        "For each unordered pair among the eight majors, what is the Engle "
        "DCC correlation path of matched daily log returns of close on the "
        "Alpari D1 history after constant-mean GARCH(1,1) standardisation?",
        "",
        "## Snapshot",
        "",
        f"- Folder: `{SNAPSHOT_REL.as_posix()}`",
        f"- Server: {manifest['terminal']['server']} "
        f"(login {manifest['terminal']['login']})",
        f"- maxbars: {manifest['terminal'].get('maxbars')}",
        f"- Broker suffix: `_i`",
        f"- {drop_note}",
        "",
        "## Parameters",
        "",
        "- Series: daily log return of close, quote direction unchanged",
        "- Marginal model: constant-mean GARCH(1,1) via arch (fit on percent "
        "returns for numerical stability; z = resid/sigma)",
        f"- DCC: correlation targeting, estimate a,b with a>=0, b>=0, a+b<1; "
        f"burn-in={BURN_IN}; headline = latest rho; Pearson r side check",
        "- Outputs: Word / HTML / Excel per successful pair, charts under "
        "`outputs/figures/`",
        "",
    ]
    if failures:
        notes.extend(
            [
                "## Fit failures",
                "",
                *[f"- {msg}" for msg in failures],
                "",
            ]
        )
    notes.extend(
        [
            "## Index",
            "",
            "| pair | n | status | latest_rho | mean | std | min | max | a | b | "
            "pearson_r | latest_minus_r |",
            "| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | "
            "---: | ---: |",
        ]
    )
    for row in index_rows:
        notes.append(
            f"| {row['pair']} | {row['n']} | {row['status']} | "
            f"{float(row['latest_rho']):.6f} | {float(row['mean']):.6f} | "
            f"{float(row['std']):.6f} | {float(row['min']):.6f} | "
            f"{float(row['max']):.6f} | {float(row['a']):.6f} | "
            f"{float(row['b']):.6f} | {float(row['pearson_r']):.6f} | "
            f"{float(row['latest_minus_r']):.6f} |"
        )
    notes.append("")
    notes.extend(_cross_pair_conclusion(index_rows))
    notes.append(
        "This NOTES.md is the index plus the cross-pair reading above. "
        "It is not a 29th pair analysis."
    )
    notes.append("")
    (EXP_DIR / "NOTES.md").write_text("\n".join(notes), encoding="utf-8")
    return OUT_DIR


if __name__ == "__main__":
    run()
