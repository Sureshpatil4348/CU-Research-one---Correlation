"""Partial / residual correlation on Alpari D1 majors: Word, HTML, and Excel per pair."""

from __future__ import annotations

import itertools
import math
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt
from scipy import stats

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from shared.mt5_data import MAJOR_PAIRS, load_snapshot

SNAPSHOT_REL = Path("data/snapshots/2026-11-03_majors_alpari_D1")
EXP_DIR = Path(__file__).resolve().parent
OUT_DIR = EXP_DIR / "outputs"
FIG_DIR = OUT_DIR / "figures"
OHLCV = ["open", "high", "low", "close", "tick_volume", "spread", "real_volume"]

# USD as quote: USD-strength = -log return. USD as base: USD-strength = +log return.
USD_QUOTE_PAIRS = ("EURUSD", "GBPUSD", "AUDUSD", "NZDUSD")
USD_BASE_PAIRS = ("USDJPY", "USDCHF", "USDCAD")
USD_FACTOR_CANDIDATES = USD_QUOTE_PAIRS + USD_BASE_PAIRS

CURRENCY_OF = {
    "EURUSD": {"EUR", "USD"},
    "GBPUSD": {"GBP", "USD"},
    "AUDUSD": {"AUD", "USD"},
    "NZDUSD": {"NZD", "USD"},
    "USDJPY": {"USD", "JPY"},
    "USDCHF": {"USD", "CHF"},
    "USDCAD": {"USD", "CAD"},
    "EURGBP": {"EUR", "GBP"},
}

METHOD_NOTE = (
    "Partial / residual correlation regresses each matched daily log return "
    "of close, ln(close_t / close_t-1), on the same leave-currency-out USD "
    "strength factor z, then takes Pearson correlation of the two residual "
    "series. Quotes are not inverted. z is the equal-weight mean of USD-"
    "strength returns from other majors that do not share a non-USD currency "
    "with either leg; EURGBP is never a constituent. USD-strength is minus "
    "the log return when USD is the quote (EURUSD, GBPUSD, AUDUSD, NZDUSD) "
    "and plus the log return when USD is the base (USDJPY, USDCHF, USDCAD). "
    "OLS uses an intercept on each leg. rho_partial is symmetric under swap "
    "of the two symbols. It describes leftover linear co-movement after "
    "removing linear z; it is not a cause, not a lead, and not a trading "
    "signal. Daily rows are not independent and residuals are estimated, so "
    "the two-sided p-value and Fisher interval are secondary. Same-sample "
    "raw Pearson r is a side check only."
)


def _prepare_frames(frames: dict[str, pd.DataFrame]) -> tuple[dict[str, pd.DataFrame], str]:
    """Drop unfinished last bar when tick volume is below half the prior day."""
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


def _usd_strength_series(frame: pd.DataFrame, symbol: str) -> pd.Series:
    ret = frame.set_index("time")["log_return"]
    if symbol in USD_QUOTE_PAIRS:
        return -ret
    if symbol in USD_BASE_PAIRS:
        return ret
    raise ValueError(f"{symbol} is not a USD-factor constituent")


def _control_constituents(left: str, right: str) -> list[str]:
    """Leave out any candidate that shares a non-USD currency with either leg."""
    blocked = (CURRENCY_OF[left] | CURRENCY_OF[right]) - {"USD"}
    out: list[str] = []
    for symbol in USD_FACTOR_CANDIDATES:
        other = CURRENCY_OF[symbol] - {"USD"}
        if other & blocked:
            continue
        out.append(symbol)
    return out


def _pair_table_with_z(
    frames: dict[str, pd.DataFrame],
    left: str,
    right: str,
    constituents: list[str],
) -> pd.DataFrame:
    a = frames[left].set_index("time")
    b = frames[right].set_index("time")
    common = a.index.intersection(b.index)
    for symbol in constituents:
        common = common.intersection(frames[symbol].set_index("time").index)
    common = common.sort_values()

    cols: dict[str, pd.Series] = {"time": pd.Series(common, index=common)}
    for col in OHLCV + ["log_return"]:
        cols[f"{left}_{col}"] = a.loc[common, col]
        cols[f"{right}_{col}"] = b.loc[common, col]

    strength_cols = []
    for symbol in constituents:
        strength = _usd_strength_series(frames[symbol], symbol).loc[common]
        col_name = f"usd_strength_{symbol}"
        cols[col_name] = strength
        strength_cols.append(col_name)

    table = pd.DataFrame(cols)
    need = [f"{left}_log_return", f"{right}_log_return"] + strength_cols
    table = table.dropna(subset=need).reset_index(drop=True)
    table["z"] = table[strength_cols].mean(axis=1)
    return table


def _ols_with_r2(dep: np.ndarray, ctrl: np.ndarray) -> dict[str, float | np.ndarray]:
    n = len(dep)
    mean_c = float(np.mean(ctrl))
    mean_d = float(np.mean(dep))
    den = float(np.sum((ctrl - mean_c) ** 2))
    if den == 0.0:
        intercept = mean_d
        slope = 0.0
        fitted = np.full(n, intercept, dtype=float)
        resid = dep - fitted
        return {
            "intercept": intercept,
            "slope": slope,
            "fitted": fitted,
            "resid": resid,
            "r2": float("nan"),
        }
    slope = float(np.sum((ctrl - mean_c) * (dep - mean_d)) / den)
    intercept = mean_d - slope * mean_c
    fitted = intercept + slope * ctrl
    resid = dep - fitted
    ss_tot = float(np.sum((dep - mean_d) ** 2))
    ss_res = float(np.sum(resid ** 2))
    r2 = float("nan") if ss_tot == 0.0 else 1.0 - ss_res / ss_tot
    return {
        "intercept": intercept,
        "slope": slope,
        "fitted": fitted,
        "resid": resid,
        "r2": r2,
    }


def _pearson_block(x: np.ndarray, y: np.ndarray) -> dict[str, float]:
    n = int(len(x))
    if n < 3 or float(np.std(x)) == 0.0 or float(np.std(y)) == 0.0:
        return {
            "r": float("nan"),
            "p": float("nan"),
            "ci_low": float("nan"),
            "ci_high": float("nan"),
            "n": float(n),
        }
    result = stats.pearsonr(x, y)
    r = float(result.statistic)
    p = float(result.pvalue)
    low, high = result.confidence_interval(confidence_level=0.95)
    return {
        "r": r,
        "p": p,
        "ci_low": float(low),
        "ci_high": float(high),
        "n": float(n),
    }


def _add_partial_columns(table: pd.DataFrame, left: str, right: str) -> tuple[pd.DataFrame, dict[str, float]]:
    out = table.copy()
    x = out[f"{left}_log_return"].to_numpy(dtype=float)
    y = out[f"{right}_log_return"].to_numpy(dtype=float)
    z = out["z"].to_numpy(dtype=float)
    reg_x = _ols_with_r2(x, z)
    reg_y = _ols_with_r2(y, z)
    out[f"{left}_fitted"] = reg_x["fitted"]
    out[f"{right}_fitted"] = reg_y["fitted"]
    out[f"{left}_resid"] = reg_x["resid"]
    out[f"{right}_resid"] = reg_y["resid"]

    partial = _pearson_block(
        np.asarray(reg_x["resid"], dtype=float),
        np.asarray(reg_y["resid"], dtype=float),
    )
    raw = _pearson_block(x, y)
    stats_row = {
        "n": float(len(out)),
        "a": float(reg_x["intercept"]),
        "b": float(reg_x["slope"]),
        "r2_x": float(reg_x["r2"]),
        "c": float(reg_y["intercept"]),
        "d": float(reg_y["slope"]),
        "r2_y": float(reg_y["r2"]),
        "rho_partial": partial["r"],
        "p": partial["p"],
        "ci_low": partial["ci_low"],
        "ci_high": partial["ci_high"],
        "pearson_r": raw["r"],
        "partial_minus_r": partial["r"] - raw["r"],
    }
    return out, stats_row


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


def _conclusion(
    left: str,
    right: str,
    stats_row: dict[str, float],
    n_controls: int,
) -> str:
    rho = stats_row["rho_partial"]
    n = int(stats_row["n"])
    strength = _strength_label(rho)
    direction = "positive" if rho >= 0 else "negative"
    p_text = "undefined" if math.isnan(stats_row["p"]) else f"{stats_row['p']:.4g}"
    return (
        f"Over {n} matched daily rows for {left} and {right} after removing "
        f"a leave-currency-out USD factor built from {n_controls} constituents, "
        f"rho_partial is {_fmt(rho, 4)} ({direction}, {strength} residual "
        f"linear link in this sample). Approximate 95% Fisher interval: "
        f"[{_fmt(stats_row['ci_low'], 4)}, {_fmt(stats_row['ci_high'], 4)}]. "
        f"Same-sample raw Pearson r is {_fmt(stats_row['pearson_r'], 4)} "
        f"(partial minus r = {_fmt(stats_row['partial_minus_r'], 4)}). "
        f"Leg R-squared on z: {left}={_fmt(stats_row['r2_x'], 4)}, "
        f"{right}={_fmt(stats_row['r2_y'], 4)}. Two-sided p under the usual "
        f"independent-pairs model is {p_text}; residuals are estimated and "
        f"daily FX rows are linked, so treat p as secondary. This does not "
        f"establish cause, lead-lag, or a lasting trading rule."
    )


def _save_figures(
    table: pd.DataFrame,
    left: str,
    right: str,
    stem: str,
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
    ax.plot(times, table["z"], color="#9467bd", linewidth=0.7, label="z (USD factor)")
    ax.set_title(f"Log returns and control z: {left} and {right}")
    ax.set_ylabel("log return / z")
    ax.legend(loc="upper left")
    fig.tight_layout()
    paths["returns"] = FIG_DIR / f"{stem}_returns.png"
    fig.savefig(paths["returns"], dpi=120)
    plt.close(fig)

    ex = table[f"{left}_resid"].to_numpy(dtype=float)
    ey = table[f"{right}_resid"].to_numpy(dtype=float)
    fig, ax = plt.subplots(figsize=(5.5, 5.2))
    ax.scatter(ex, ey, s=6, alpha=0.35, color="#2ca02c")
    ax.set_xlabel(f"{left} residual e_x")
    ax.set_ylabel(f"{right} residual e_y")
    ax.set_title(f"Residual scatter: {left} vs {right}")
    ax.axhline(0, color="gray", linewidth=0.5)
    ax.axvline(0, color="gray", linewidth=0.5)
    fig.tight_layout()
    paths["scatter"] = FIG_DIR / f"{stem}_scatter.png"
    fig.savefig(paths["scatter"], dpi=120)
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
    constituents: list[str],
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

    _add_heading(doc, f"Partial / residual correlation: {left} and {right}", 0)
    _add_para(
        doc,
        "Method 07 / daily log returns / leave-currency-out USD factor / "
        "Alpari D1 full available history",
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
            "USD-strength sign rule: minus log return when USD is the quote "
            "(EURUSD, GBPUSD, AUDUSD, NZDUSD); plus log return when USD is "
            "the base (USDJPY, USDCHF, USDCAD). EURGBP is never a constituent."
        ),
        (
            f"Control z constituents ({len(constituents)}): "
            + ", ".join(constituents)
        ),
        "z_t = equal-weight mean of those USD-strength returns on the same day",
        f"Complete matched rows (Excel): {xlsx_name}",
        f"Complete matched rows (HTML table): {xlsx_name.replace('.xlsx', '_data.html')}",
    ]
    for line in setup_lines:
        _add_para(doc, line)

    _add_heading(doc, "Method carried forward", 1)
    _add_para(doc, METHOD_NOTE)

    _add_heading(doc, "Regression on z", 1)
    reg_frame = pd.DataFrame(
        [
            {
                "leg": left,
                "intercept_a_or_c": round(stats_row["a"], 8),
                "slope_b_or_d": round(stats_row["b"], 8),
                "R2": round(stats_row["r2_x"], 8)
                if not math.isnan(stats_row["r2_x"])
                else float("nan"),
            },
            {
                "leg": right,
                "intercept_a_or_c": round(stats_row["c"], 8),
                "slope_b_or_d": round(stats_row["d"], 8),
                "R2": round(stats_row["r2_y"], 8)
                if not math.isnan(stats_row["r2_y"])
                else float("nan"),
            },
        ]
    )
    _add_small_table(doc, reg_frame)

    _add_heading(doc, "Results", 1)
    p_text = "undefined" if math.isnan(stats_row["p"]) else f"{stats_row['p']:.6g}"
    _add_para(doc, f"rho_partial: {_fmt(stats_row['rho_partial'], 6)}")
    _add_para(doc, f"Two-sided p-value: {p_text}")
    _add_para(
        doc,
        "Approximate 95% Fisher interval: "
        f"[{_fmt(stats_row['ci_low'], 6)}, {_fmt(stats_row['ci_high'], 6)}]",
    )
    _add_para(doc, f"Same-sample raw Pearson r: {_fmt(stats_row['pearson_r'], 6)}")
    _add_para(doc, f"rho_partial minus r: {_fmt(stats_row['partial_minus_r'], 6)}")

    _add_heading(doc, "Conclusion", 1)
    _add_para(doc, _conclusion(left, right, stats_row, len(constituents)))

    _add_heading(doc, "Charts", 1)
    for key, title in (
        ("closes", "Daily closes"),
        ("returns", "Log returns and control z"),
        ("scatter", "Residual scatter e_x vs e_y"),
    ):
        _add_para(doc, title, bold=True)
        doc.add_picture(str(fig_paths[key]), width=Inches(6.2))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

    _add_heading(doc, "Data report", 1)
    _add_para(
        doc,
        "Every matched row that entered the partial correlation is stored in "
        f"the sibling Excel workbook named {xlsx_name}. That file is the "
        "complete data archive for redrawing charts. Embedding all rows as a "
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
        f"{left}_close",
        f"{right}_close",
        f"{left}_log_return",
        f"{right}_log_return",
        "z",
        f"{left}_fitted",
        f"{right}_fitted",
        f"{left}_resid",
        f"{right}_resid",
    ]
    _add_para(doc, "First 15 matched rows (selected columns)", bold=True)
    _add_small_table(doc, table.loc[:, preview_cols].head(15))
    _add_para(doc, "Last 15 matched rows (selected columns)", bold=True)
    _add_small_table(doc, table.loc[:, preview_cols].tail(15))

    doc.save(out_path)


def _cross_pair_conclusion(index_rows: list[dict[str, object]]) -> list[str]:
    by_rho = sorted(index_rows, key=lambda row: float(row["rho_partial"]))
    by_abs_gap = sorted(
        index_rows,
        key=lambda row: abs(float(row["partial_minus_r"])),
        reverse=True,
    )
    strongest_pos = by_rho[-1]
    strongest_neg = by_rho[0]
    near_zero = sorted(index_rows, key=lambda row: abs(float(row["rho_partial"])))[:3]
    top_gaps = by_abs_gap[:3]

    lines = [
        "## Cross-pair conclusion",
        "",
        "Reading of the 28-pair index only. Not a 29th pair analysis and not a "
        "trading signal.",
        "",
        (
            f"Strongest positive residual link: {strongest_pos['pair']} "
            f"(rho_partial={float(strongest_pos['rho_partial']):.4f}, "
            f"n={strongest_pos['n']})."
        ),
        (
            f"Strongest negative residual link: {strongest_neg['pair']} "
            f"(rho_partial={float(strongest_neg['rho_partial']):.4f}, "
            f"n={strongest_neg['n']})."
        ),
        "Nearest-to-zero residual links: "
        + "; ".join(
            f"{row['pair']} (rho_partial={float(row['rho_partial']):.4f})"
            for row in near_zero
        )
        + ".",
        "Largest |rho_partial minus Pearson r| gaps on the same sample: "
        + "; ".join(
            f"{row['pair']} (gap={float(row['partial_minus_r']):.4f}, "
            f"rho_partial={float(row['rho_partial']):.4f}, "
            f"r={float(row['pearson_r']):.4f})"
            for row in top_gaps
        )
        + ". A large gap can mean the USD factor explained much of the raw "
        "link, or that residual co-movement runs against the raw sign; "
        "inspect that pair's R-squared values and residual scatter before "
        "treating either score as settled.",
        "",
    ]
    return lines


def run() -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    snap = load_snapshot(REPO_ROOT / SNAPSHOT_REL)
    manifest = snap["manifest"]
    snapshot_name = manifest["folder"]
    broker_map = {row["logical"]: row["resolved"] for row in manifest["symbols"]}
    frames, drop_note = _prepare_frames(snap["frames"])

    index_rows: list[dict[str, object]] = []
    pairs = list(itertools.combinations(MAJOR_PAIRS, 2))

    for left, right in pairs:
        constituents = _control_constituents(left, right)
        if len(constituents) < 1:
            raise RuntimeError(f"No USD-factor constituents left for {left}-{right}")
        table = _pair_table_with_z(frames, left, right, constituents)
        table, stats_row = _add_partial_columns(table, left, right)
        stem = f"{left}-{right}_Partial_D1"
        fig_paths = _save_figures(table, left, right, stem)

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
                f"<h1>{left} and {right}: matched rows used for partial "
                f"correlation</h1>"
                f"<p>n={int(stats_row['n'])}. z constituents: "
                f"{', '.join(constituents)}. Complete archive also in "
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
            constituents=constituents,
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
                "n_controls": len(constituents),
                "controls": ",".join(constituents),
                "rho_partial": stats_row["rho_partial"],
                "p": stats_row["p"],
                "ci_low": stats_row["ci_low"],
                "ci_high": stats_row["ci_high"],
                "pearson_r": stats_row["pearson_r"],
                "partial_minus_r": stats_row["partial_minus_r"],
                "r2_x": stats_row["r2_x"],
                "r2_y": stats_row["r2_y"],
                "docx": docx_path.name,
                "xlsx": xlsx_path.name,
                "html": html_path.name,
            }
        )
        print(
            f"Wrote {docx_path.name}  rho_partial={stats_row['rho_partial']:.4f}  "
            f"n={int(stats_row['n'])}  controls={len(constituents)}",
            flush=True,
        )

    index = pd.DataFrame(index_rows)
    index.to_excel(OUT_DIR / "index.xlsx", index=False, sheet_name="index")

    notes = [
        "# Partial and residual correlation experiments v001",
        "",
        "## Research question",
        "",
        "For each unordered pair among the eight majors, what is the partial "
        "correlation of matched daily log returns of close after removing a "
        "leave-currency-out USD strength factor, on the Alpari D1 history "
        "that the broker actually provided?",
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
        "- Control z: equal-weight mean of USD-strength returns from majors "
        "that do not share a non-USD currency with either leg; USD-strength "
        "is -log return for EURUSD/GBPUSD/AUDUSD/NZDUSD and +log return for "
        "USDJPY/USDCHF/USDCAD; EURGBP never enters z",
        "- Statistic: OLS residuals of each leg on z (with intercept), then "
        "Pearson rho_partial via `scipy.stats.pearsonr` with Fisher 95% "
        "interval; same-sample raw Pearson r and rho_partial minus r as a "
        "side check; R-squared of each leg on z",
        "- Outputs: 28 Word reports, 28 full-data HTML tables, 28 Excel "
        "workbooks, charts under `outputs/figures/` (closes, returns+z, "
        "residual scatter)",
        "",
        "## Index",
        "",
        "| pair | n | n_controls | rho_partial | p | ci_low | ci_high | "
        "pearson_r | partial_minus_r | r2_x | r2_y |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | "
        "---: | ---: |",
    ]
    for row in index_rows:
        notes.append(
            f"| {row['pair']} | {row['n']} | {row['n_controls']} | "
            f"{float(row['rho_partial']):.6f} | {float(row['p']):.6g} | "
            f"{float(row['ci_low']):.6f} | {float(row['ci_high']):.6f} | "
            f"{float(row['pearson_r']):.6f} | "
            f"{float(row['partial_minus_r']):.6f} | "
            f"{float(row['r2_x']):.6f} | {float(row['r2_y']):.6f} |"
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
