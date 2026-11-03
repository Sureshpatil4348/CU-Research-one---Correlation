"""Granger predictability on Alpari D1 majors: Word, HTML, and Excel per pair."""

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
LAG_ORDERS = (1, 5)
METHOD_NOTE = (
    "Granger predictability asks whether lagged X helps explain Y beyond "
    "lags of Y alone on matched daily log returns of close, "
    "ln(close_t / close_t-1). Quotes are not inverted. For lag order p, "
    "the unrestricted model is y_t on an intercept, y_{t-1}..y_{t-p}, and "
    "x_{t-1}..x_{t-p}. The restricted model drops the x lags. The test is "
    "an F comparison of residual sums of squares via OLS "
    "(numpy.linalg.lstsq) and scipy.stats.f. Orders p=1 and p=5 are "
    "pre-specified; both directions are tested. The headline is the p=5 "
    "joint test in both directions. p=1 is reported beside it because the "
    "guide formula is the one-lag regression. Rejecting H0 is statistical "
    "predictability in mean in this sample; it is not economic causation "
    "and not a trading signal. There are 56 directed tests at p=5 across "
    "the 28 pairs."
)


def _assert_guide_toys() -> None:
    y = np.array([0.020, 0.030, 0.050, 0.040, 0.060])
    x = np.array([0.010, 0.020, 0.010, 0.030, 0.020])
    y_t = y[1:]
    y_l1 = y[:-1]
    x_l1 = x[:-1]
    xmat = np.column_stack([np.ones(len(y_t)), y_l1, x_l1])
    b_hat = float(np.linalg.lstsq(xmat, y_t, rcond=None)[0][2])
    assert abs(b_hat - 1.222222222222222) < 1e-9


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


def _granger_f_test(y: np.ndarray, x: np.ndarray, p: int) -> dict[str, float]:
    """Test whether x lags help predict y beyond y's own lags (order p)."""
    n_full = len(y)
    if n_full <= p + p + 2:
        return {
            "n": float("nan"),
            "f_stat": float("nan"),
            "p_value": float("nan"),
            "b": float("nan"),
            "ssr_u": float("nan"),
            "ssr_r": float("nan"),
            "df1": float(p),
            "df2": float("nan"),
        }
    y_dep = y[p:]
    n = len(y_dep)
    own = np.column_stack([y[p - lag : n_full - lag] for lag in range(1, p + 1)])
    other = np.column_stack([x[p - lag : n_full - lag] for lag in range(1, p + 1)])
    ones = np.ones((n, 1), dtype=float)
    x_u = np.hstack([ones, own, other])
    x_r = np.hstack([ones, own])
    beta_u, _, _, _ = np.linalg.lstsq(x_u, y_dep, rcond=None)
    beta_r, _, _, _ = np.linalg.lstsq(x_r, y_dep, rcond=None)
    resid_u = y_dep - x_u @ beta_u
    resid_r = y_dep - x_r @ beta_r
    ssr_u = float(np.sum(resid_u ** 2))
    ssr_r = float(np.sum(resid_r ** 2))
    df1 = p
    df2 = n - (1 + 2 * p)
    if df2 <= 0 or ssr_u <= 0.0:
        f_stat = float("nan")
        p_value = float("nan")
    else:
        f_stat = ((ssr_r - ssr_u) / df1) / (ssr_u / df2)
        if f_stat < 0:
            f_stat = 0.0
        p_value = float(stats.f.sf(f_stat, df1, df2))
    b = float(beta_u[1 + p]) if p == 1 else float("nan")
    return {
        "n": float(n),
        "f_stat": float(f_stat),
        "p_value": float(p_value),
        "b": b,
        "ssr_u": ssr_u,
        "ssr_r": ssr_r,
        "df1": float(df1),
        "df2": float(df2),
    }


def _granger_results(table: pd.DataFrame, left: str, right: str) -> tuple[dict[str, float], pd.DataFrame]:
    x = table[f"{left}_log_return"].to_numpy(dtype=float)
    y = table[f"{right}_log_return"].to_numpy(dtype=float)
    rows: list[dict[str, object]] = []
    for direction, cause, effect, cause_arr, effect_arr in (
        (f"{left}_to_{right}", left, right, x, y),
        (f"{right}_to_{left}", right, left, y, x),
    ):
        for p in LAG_ORDERS:
            test = _granger_f_test(effect_arr, cause_arr, p)
            rows.append(
                {
                    "direction": direction,
                    "cause": cause,
                    "effect": effect,
                    "p_lags": p,
                    "n": int(test["n"]) if not math.isnan(test["n"]) else None,
                    "f_stat": test["f_stat"],
                    "p_value": test["p_value"],
                    "b": test["b"] if p == 1 else float("nan"),
                    "ssr_u": test["ssr_u"],
                    "ssr_r": test["ssr_r"],
                    "df1": int(test["df1"]),
                    "df2": int(test["df2"]) if not math.isnan(test["df2"]) else None,
                }
            )

    results = pd.DataFrame(rows)
    by_dir_p = {
        (str(r["direction"]), int(r["p_lags"])): r for r in results.to_dict("records")
    }
    lr1 = by_dir_p[(f"{left}_to_{right}", 1)]
    lr5 = by_dir_p[(f"{left}_to_{right}", 5)]
    rl1 = by_dir_p[(f"{right}_to_{left}", 1)]
    rl5 = by_dir_p[(f"{right}_to_{left}", 5)]
    stats_row = {
        "n": float(len(table)),
        "n_p1": float(lr1["n"]),
        "n_p5": float(lr5["n"]),
        "b_L_to_R_p1": float(lr1["b"]),
        "f_L_to_R_p1": float(lr1["f_stat"]),
        "p_L_to_R_p1": float(lr1["p_value"]),
        "f_L_to_R_p5": float(lr5["f_stat"]),
        "p_L_to_R_p5": float(lr5["p_value"]),
        "b_R_to_L_p1": float(rl1["b"]),
        "f_R_to_L_p1": float(rl1["f_stat"]),
        "p_R_to_L_p1": float(rl1["p_value"]),
        "f_R_to_L_p5": float(rl5["f_stat"]),
        "p_R_to_L_p5": float(rl5["p_value"]),
    }
    return stats_row, results


def _fmt(value: float, digits: int = 4) -> str:
    if math.isnan(value):
        return "n/a"
    return f"{value:.{digits}f}"


def _fmt_p(value: float) -> str:
    if math.isnan(value):
        return "n/a"
    return f"{value:.6g}"


def _conclusion(left: str, right: str, stats_row: dict[str, float]) -> str:
    return (
        f"Headline p=5 joint tests for {left} and {right}: "
        f"{left}->{right} F={_fmt(stats_row['f_L_to_R_p5'], 4)} "
        f"(p={_fmt_p(stats_row['p_L_to_R_p5'])}); "
        f"{right}->{left} F={_fmt(stats_row['f_R_to_L_p5'], 4)} "
        f"(p={_fmt_p(stats_row['p_R_to_L_p5'])}); usable rows n="
        f"{int(stats_row['n_p5'])}. One-lag slopes: "
        f"b_{left}->{right}={_fmt(stats_row['b_L_to_R_p1'], 4)} "
        f"(F={_fmt(stats_row['f_L_to_R_p1'], 4)}, "
        f"p={_fmt_p(stats_row['p_L_to_R_p1'])}); "
        f"b_{right}->{left}={_fmt(stats_row['b_R_to_L_p1'], 4)} "
        f"(F={_fmt(stats_row['f_R_to_L_p1'], 4)}, "
        f"p={_fmt_p(stats_row['p_R_to_L_p1'])}). "
        f"Rejecting H0 is in-sample mean predictability, not economic "
        f"cause and not a trading signal."
    )


def _save_figures(
    table: pd.DataFrame,
    left: str,
    right: str,
    stats_row: dict[str, float],
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
    ax.set_title(f"Log returns: {left} and {right}")
    ax.set_ylabel("log return")
    ax.legend(loc="upper left")
    fig.tight_layout()
    paths["returns"] = FIG_DIR / f"{stem}_returns.png"
    fig.savefig(paths["returns"], dpi=120)
    plt.close(fig)

    labels = [
        f"{left}->{right}\np=1",
        f"{left}->{right}\np=5",
        f"{right}->{left}\np=1",
        f"{right}->{left}\np=5",
    ]
    values = [
        stats_row["f_L_to_R_p1"],
        stats_row["f_L_to_R_p5"],
        stats_row["f_R_to_L_p1"],
        stats_row["f_R_to_L_p5"],
    ]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    colors = ["#1f77b4", "#1f77b4", "#ff7f0e", "#ff7f0e"]
    ax.bar(range(4), values, color=colors)
    ax.set_xticks(range(4))
    ax.set_xticklabels(labels)
    ax.set_ylabel("F statistic")
    ax.set_title(f"Granger F statistics: {left} and {right}")
    fig.tight_layout()
    paths["fstats"] = FIG_DIR / f"{stem}_fstats.png"
    fig.savefig(paths["fstats"], dpi=120)
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
    results: pd.DataFrame,
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

    _add_heading(doc, f"Granger predictability: {left} and {right}", 0)
    _add_para(
        doc,
        "Method 13 / daily log returns / p=1 and p=5 / Alpari D1 full available history",
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
        "Lag orders pre-specified: p=1 and p=5; both directions",
        "Headline: p=5 joint F test in both directions",
        f"Complete matched rows (Excel): {xlsx_name}",
        f"Complete matched rows (HTML table): {xlsx_name.replace('.xlsx', '_data.html')}",
    ]
    for line in setup_lines:
        _add_para(doc, line)

    _add_heading(doc, "Method carried forward", 1)
    _add_para(doc, METHOD_NOTE)

    _add_heading(doc, "Results", 1)
    display = results[
        ["direction", "p_lags", "n", "f_stat", "p_value", "b", "df1", "df2"]
    ].copy()
    _add_small_table(doc, display.round(8))

    _add_heading(doc, "Conclusion", 1)
    _add_para(doc, _conclusion(left, right, stats_row))

    _add_heading(doc, "Charts", 1)
    for key, title in (
        ("closes", "Daily closes"),
        ("returns", "Daily log returns"),
        ("fstats", "Granger F statistics"),
    ):
        _add_para(doc, title, bold=True)
        doc.add_picture(str(fig_paths[key]), width=Inches(6.2))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

    _add_heading(doc, "Data report", 1)
    _add_para(
        doc,
        "Every matched row is stored in the sibling Excel workbook named "
        f"{xlsx_name} (sheet matched_rows). The results sheet holds the "
        "four F tests. Embedding all rows as a Word table is impractical; "
        "the Word file holds column summaries and the first and last 15 rows.",
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
    ]
    _add_para(doc, "First 15 matched rows (selected columns)", bold=True)
    _add_small_table(doc, table.loc[:, preview_cols].head(15))
    _add_para(doc, "Last 15 matched rows (selected columns)", bold=True)
    _add_small_table(doc, table.loc[:, preview_cols].tail(15))

    doc.save(out_path)


def _cross_pair_conclusion(index_rows: list[dict[str, object]]) -> list[str]:
    directed: list[dict[str, object]] = []
    for row in index_rows:
        pair = str(row["pair"])
        left, right = pair.split("-")
        directed.append(
            {
                "label": f"{left}->{right}",
                "p_value": float(row["p_L_to_R_p5"]),
                "f_stat": float(row["f_L_to_R_p5"]),
            }
        )
        directed.append(
            {
                "label": f"{right}->{left}",
                "p_value": float(row["p_R_to_L_p5"]),
                "f_stat": float(row["f_R_to_L_p5"]),
            }
        )
    smallest = sorted(directed, key=lambda row: float(row["p_value"]))[:5]

    lines = [
        "## Cross-pair conclusion",
        "",
        "Reading of the 28-pair index at pre-specified p=5 only (56 directed "
        "tests). Not a 29th pair analysis and not a trading signal.",
        "",
        "Smallest p=5 p-values: "
        + "; ".join(
            f"{row['label']} (p={float(row['p_value']):.4g}, "
            f"F={float(row['f_stat']):.4f})"
            for row in smallest
        )
        + ". With 56 directed tests at this order, a small p is an in-sample "
        "description only; it is not economic cause and not a trading signal.",
        "",
    ]
    return lines


def run() -> Path:
    _assert_guide_toys()
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
        table = _pair_table(frames[left], frames[right], left, right)
        stats_row, results = _granger_results(table, left, right)
        stem = f"{left}-{right}_Granger_D1"
        fig_paths = _save_figures(table, left, right, stats_row, stem)

        xlsx_path = OUT_DIR / f"{stem}.xlsx"
        excel_frame = table.copy()
        excel_frame["time"] = pd.to_datetime(excel_frame["time"], utc=True).dt.strftime(
            "%Y-%m-%d"
        )
        with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
            excel_frame.to_excel(writer, index=False, sheet_name="matched_rows")
            results.to_excel(writer, index=False, sheet_name="results")

        html_path = OUT_DIR / f"{stem}_data.html"
        html_path.write_text(
            (
                f"<!DOCTYPE html><html><head><meta charset='utf-8'>"
                f"<title>{stem} data</title></head><body>"
                f"<h1>{left} and {right}: matched rows for Granger "
                f"predictability</h1>"
                f"<p>n={int(stats_row['n'])}. Complete archive also in "
                f"{xlsx_path.name}.</p>"
                + excel_frame.to_html(index=False)
                + "<h2>Results</h2>"
                + results.to_html(index=False)
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
            results=results,
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
                "n_p5": int(stats_row["n_p5"]),
                "b_L_to_R_p1": stats_row["b_L_to_R_p1"],
                "f_L_to_R_p1": stats_row["f_L_to_R_p1"],
                "p_L_to_R_p1": stats_row["p_L_to_R_p1"],
                "f_L_to_R_p5": stats_row["f_L_to_R_p5"],
                "p_L_to_R_p5": stats_row["p_L_to_R_p5"],
                "b_R_to_L_p1": stats_row["b_R_to_L_p1"],
                "f_R_to_L_p1": stats_row["f_R_to_L_p1"],
                "p_R_to_L_p1": stats_row["p_R_to_L_p1"],
                "f_R_to_L_p5": stats_row["f_R_to_L_p5"],
                "p_R_to_L_p5": stats_row["p_R_to_L_p5"],
                "docx": docx_path.name,
                "xlsx": xlsx_path.name,
                "html": html_path.name,
            }
        )
        print(
            f"Wrote {docx_path.name}  L->R p5={stats_row['p_L_to_R_p5']:.4g} "
            f"R->L p5={stats_row['p_R_to_L_p5']:.4g}  n={int(stats_row['n'])}",
            flush=True,
        )

    index = pd.DataFrame(index_rows)
    index.to_excel(OUT_DIR / "index.xlsx", index=False, sheet_name="index")

    notes = [
        "# Granger predictability experiments v001",
        "",
        "## Research question",
        "",
        "For each unordered pair among the eight majors, do lagged log "
        "returns of one leg help predict the other beyond own lags at "
        "pre-specified orders p=1 and p=5 on the Alpari D1 history?",
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
        "- Statistic: OLS Granger F tests via numpy.linalg.lstsq and "
        "scipy.stats.f at p=1 and p=5, both directions; headline = p=5 "
        "joint test; p=1 slope b reported as the guide one-lag case",
        "- Outputs: 28 Word reports, 28 full-data HTML tables, 28 Excel "
        "workbooks (matched_rows + results sheets), charts under "
        "`outputs/figures/` (closes, returns, F-stat bars)",
        "",
        "## Index",
        "",
        "| pair | n | n_p5 | b_L_to_R_p1 | f_L_to_R_p1 | p_L_to_R_p1 | "
        "f_L_to_R_p5 | p_L_to_R_p5 | b_R_to_L_p1 | f_R_to_L_p1 | "
        "p_R_to_L_p1 | f_R_to_L_p5 | p_R_to_L_p5 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | "
        "---: | ---: | ---: | ---: |",
    ]
    for row in index_rows:
        notes.append(
            f"| {row['pair']} | {row['n']} | {row['n_p5']} | "
            f"{float(row['b_L_to_R_p1']):.6f} | "
            f"{float(row['f_L_to_R_p1']):.6f} | "
            f"{float(row['p_L_to_R_p1']):.6g} | "
            f"{float(row['f_L_to_R_p5']):.6f} | "
            f"{float(row['p_L_to_R_p5']):.6g} | "
            f"{float(row['b_R_to_L_p1']):.6f} | "
            f"{float(row['f_R_to_L_p1']):.6f} | "
            f"{float(row['p_R_to_L_p1']):.6g} | "
            f"{float(row['f_R_to_L_p5']):.6f} | "
            f"{float(row['p_R_to_L_p5']):.6g} |"
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
