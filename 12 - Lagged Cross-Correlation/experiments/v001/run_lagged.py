"""Lagged cross-correlation on Alpari D1 majors: Word, HTML, and Excel per pair."""

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
K_MAX = 10
METHOD_NOTE = (
    "Lagged cross-correlation measures Pearson correlation between matched "
    "daily log returns of close, ln(close_t / close_t-1), after shifting one "
    "series forward by k bars on the matched panel. Quotes are not inverted. "
    "rho_{X->Y}(k) = Corr(x_t, y_{t+k}) with n_k = n - k. K_max = 10 is "
    "fixed before estimation. The headline is the pre-specified lag k = 1 "
    "in both directions. k = 0 is the same-bar side check. The lag inside "
    "1..10 with the largest absolute rho is stored as a descriptive column "
    "only; it is not a selected result. This is a linear screen, not proof "
    "of forecast edge, economic cause, or a trading signal."
)


def _assert_guide_toys() -> None:
    x_ser = [0.010, 0.020, 0.030, 0.040, 0.050]
    y_ser = [0.015, 0.040, 0.050, 0.070, 0.090]
    k = 1
    rho = float(stats.pearsonr(x_ser[:-k], y_ser[k:]).statistic)
    assert abs(rho - 0.9897782665572893) < 1e-9


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


def _lagged_rho(x: np.ndarray, y: np.ndarray, k: int) -> dict[str, float]:
    if k == 0:
        return _pearson_block(x, y)
    return _pearson_block(x[:-k], y[k:])


def _ccf_table(x: np.ndarray, y: np.ndarray, x_name: str, y_name: str) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for k in range(0, K_MAX + 1):
        fwd = _lagged_rho(x, y, k)
        rev = _lagged_rho(y, x, k)
        rows.append(
            {
                "k": k,
                f"rho_{x_name}_to_{y_name}": fwd["r"],
                f"p_{x_name}_to_{y_name}": fwd["p"],
                f"n_{x_name}_to_{y_name}": int(fwd["n"]),
                f"ci_low_{x_name}_to_{y_name}": fwd["ci_low"],
                f"ci_high_{x_name}_to_{y_name}": fwd["ci_high"],
                f"rho_{y_name}_to_{x_name}": rev["r"],
                f"p_{y_name}_to_{x_name}": rev["p"],
                f"n_{y_name}_to_{x_name}": int(rev["n"]),
                f"ci_low_{y_name}_to_{x_name}": rev["ci_low"],
                f"ci_high_{y_name}_to_{x_name}": rev["ci_high"],
            }
        )
    return pd.DataFrame(rows)


def _best_abs_lag(ccf: pd.DataFrame, rho_col: str) -> tuple[int, float]:
    subset = ccf[ccf["k"] >= 1]
    idx = subset[rho_col].abs().idxmax()
    return int(subset.loc[idx, "k"]), float(subset.loc[idx, rho_col])


def _lagged_stats(
    table: pd.DataFrame,
    left: str,
    right: str,
) -> tuple[dict[str, float], pd.DataFrame]:
    x = table[f"{left}_log_return"].to_numpy(dtype=float)
    y = table[f"{right}_log_return"].to_numpy(dtype=float)
    ccf = _ccf_table(x, y, left, right)
    row_k0 = ccf[ccf["k"] == 0].iloc[0]
    row_k1 = ccf[ccf["k"] == 1].iloc[0]
    best_lr_k, best_lr_rho = _best_abs_lag(ccf, f"rho_{left}_to_{right}")
    best_rl_k, best_rl_rho = _best_abs_lag(ccf, f"rho_{right}_to_{left}")
    stats_row = {
        "n": float(len(table)),
        "rho_k0": float(row_k0[f"rho_{left}_to_{right}"]),
        "rho_L_to_R_k1": float(row_k1[f"rho_{left}_to_{right}"]),
        "p_L_to_R_k1": float(row_k1[f"p_{left}_to_{right}"]),
        "n_L_to_R_k1": float(row_k1[f"n_{left}_to_{right}"]),
        "ci_low_L_to_R_k1": float(row_k1[f"ci_low_{left}_to_{right}"]),
        "ci_high_L_to_R_k1": float(row_k1[f"ci_high_{left}_to_{right}"]),
        "rho_R_to_L_k1": float(row_k1[f"rho_{right}_to_{left}"]),
        "p_R_to_L_k1": float(row_k1[f"p_{right}_to_{left}"]),
        "n_R_to_L_k1": float(row_k1[f"n_{right}_to_{left}"]),
        "ci_low_R_to_L_k1": float(row_k1[f"ci_low_{right}_to_{left}"]),
        "ci_high_R_to_L_k1": float(row_k1[f"ci_high_{right}_to_{left}"]),
        "best_abs_L_to_R_k": float(best_lr_k),
        "best_abs_L_to_R_rho": best_lr_rho,
        "best_abs_R_to_L_k": float(best_rl_k),
        "best_abs_R_to_L_rho": best_rl_rho,
    }
    return stats_row, ccf


def _fmt(value: float, digits: int = 4) -> str:
    if math.isnan(value):
        return "n/a"
    return f"{value:.{digits}f}"


def _conclusion(left: str, right: str, stats_row: dict[str, float]) -> str:
    return (
        f"At the pre-specified lag k=1 for {left} and {right}, "
        f"rho_{{{left}->{right}}}(1) = {_fmt(stats_row['rho_L_to_R_k1'], 4)} "
        f"(n={int(stats_row['n_L_to_R_k1'])}) and "
        f"rho_{{{right}->{left}}}(1) = {_fmt(stats_row['rho_R_to_L_k1'], 4)} "
        f"(n={int(stats_row['n_R_to_L_k1'])}). Same-bar rho(k=0) = "
        f"{_fmt(stats_row['rho_k0'], 4)}. Largest |rho| among k=1..{K_MAX} "
        f"is descriptive only: {left}->{right} at k="
        f"{int(stats_row['best_abs_L_to_R_k'])} "
        f"({_fmt(stats_row['best_abs_L_to_R_rho'], 4)}); "
        f"{right}->{left} at k={int(stats_row['best_abs_R_to_L_k'])} "
        f"({_fmt(stats_row['best_abs_R_to_L_rho'], 4)}). This is a linear "
        f"screen, not forecast proof or a trading signal."
    )


def _save_figures(
    table: pd.DataFrame,
    left: str,
    right: str,
    ccf: pd.DataFrame,
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

    fig, ax = plt.subplots(figsize=(10, 4.2))
    ks = ccf["k"].to_numpy(dtype=int)
    width = 0.35
    ax.bar(
        ks - width / 2,
        ccf[f"rho_{left}_to_{right}"],
        width=width,
        color="#1f77b4",
        label=f"{left}->{right}",
    )
    ax.bar(
        ks + width / 2,
        ccf[f"rho_{right}_to_{left}"],
        width=width,
        color="#ff7f0e",
        label=f"{right}->{left}",
    )
    ax.axhline(0, color="gray", linewidth=0.5)
    ax.set_xticks(ks)
    ax.set_xlabel("lag k (bars)")
    ax.set_ylabel("Pearson rho")
    ax.set_title(f"Lagged cross-correlation CCF: {left} and {right}")
    ax.legend(loc="best")
    fig.tight_layout()
    paths["ccf"] = FIG_DIR / f"{stem}_ccf.png"
    fig.savefig(paths["ccf"], dpi=120)
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
    ccf: pd.DataFrame,
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

    _add_heading(doc, f"Lagged cross-correlation: {left} and {right}", 0)
    _add_para(
        doc,
        "Method 12 / daily log returns / K_max=10 / Alpari D1 full available history",
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
        f"Lag definition: rho_X->Y(k) = Corr(x_t, y_{{t+k}}) on matched D1 bars",
        f"K_max = {K_MAX}; headline lag k = 1 (both directions)",
        f"Complete matched rows (Excel): {xlsx_name}",
        f"Complete matched rows (HTML table): {xlsx_name.replace('.xlsx', '_data.html')}",
    ]
    for line in setup_lines:
        _add_para(doc, line)

    _add_heading(doc, "Method carried forward", 1)
    _add_para(doc, METHOD_NOTE)

    _add_heading(doc, "Results (headline k=1)", 1)
    _add_para(
        doc,
        f"rho_{left}->{right}(1): {_fmt(stats_row['rho_L_to_R_k1'], 6)} "
        f"(n={int(stats_row['n_L_to_R_k1'])})",
    )
    _add_para(
        doc,
        f"95% Fisher interval {left}->{right}: "
        f"[{_fmt(stats_row['ci_low_L_to_R_k1'], 6)}, "
        f"{_fmt(stats_row['ci_high_L_to_R_k1'], 6)}]",
    )
    _add_para(
        doc,
        f"rho_{right}->{left}(1): {_fmt(stats_row['rho_R_to_L_k1'], 6)} "
        f"(n={int(stats_row['n_R_to_L_k1'])})",
    )
    _add_para(
        doc,
        f"95% Fisher interval {right}->{left}: "
        f"[{_fmt(stats_row['ci_low_R_to_L_k1'], 6)}, "
        f"{_fmt(stats_row['ci_high_R_to_L_k1'], 6)}]",
    )
    _add_para(doc, f"Same-bar rho(k=0): {_fmt(stats_row['rho_k0'], 6)}")
    _add_para(
        doc,
        "Largest |rho| among k=1..10 (descriptive only, not selected): "
        f"{left}->{right} k={int(stats_row['best_abs_L_to_R_k'])} "
        f"rho={_fmt(stats_row['best_abs_L_to_R_rho'], 6)}; "
        f"{right}->{left} k={int(stats_row['best_abs_R_to_L_k'])} "
        f"rho={_fmt(stats_row['best_abs_R_to_L_rho'], 6)}",
    )

    _add_heading(doc, "CCF table", 1)
    display = ccf[
        [
            "k",
            f"rho_{left}_to_{right}",
            f"n_{left}_to_{right}",
            f"rho_{right}_to_{left}",
            f"n_{right}_to_{left}",
        ]
    ].copy()
    _add_small_table(doc, display.round(8))

    _add_heading(doc, "Conclusion", 1)
    _add_para(doc, _conclusion(left, right, stats_row))

    _add_heading(doc, "Charts", 1)
    for key, title in (
        ("closes", "Daily closes"),
        ("returns", "Daily log returns"),
        ("ccf", "CCF both directions k=0..10"),
    ):
        _add_para(doc, title, bold=True)
        doc.add_picture(str(fig_paths[key]), width=Inches(6.2))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

    _add_heading(doc, "Data report", 1)
    _add_para(
        doc,
        "Every matched row is stored in the sibling Excel workbook named "
        f"{xlsx_name} (sheet matched_rows). The CCF sheet holds rho(k) for "
        f"k=0..{K_MAX}. Embedding all rows as a Word table is impractical; "
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
                "pair": pair,
                "rho": float(row["rho_L_to_R_k1"]),
            }
        )
        directed.append(
            {
                "label": f"{right}->{left}",
                "pair": pair,
                "rho": float(row["rho_R_to_L_k1"]),
            }
        )
    by_rho = sorted(directed, key=lambda row: float(row["rho"]))
    strongest_pos = by_rho[-1]
    strongest_neg = by_rho[0]
    near_zero = sorted(directed, key=lambda row: abs(float(row["rho"])))[:3]

    lines = [
        "## Cross-pair conclusion",
        "",
        "Reading of the 28-pair index at pre-specified k=1 only (56 directed "
        "screens). Not a 29th pair analysis and not a trading signal.",
        "",
        (
            f"Strongest positive k=1 directed rho: {strongest_pos['label']} "
            f"(rho={float(strongest_pos['rho']):.4f})."
        ),
        (
            f"Strongest negative k=1 directed rho: {strongest_neg['label']} "
            f"(rho={float(strongest_neg['rho']):.4f})."
        ),
        "Nearest-to-zero k=1 directed rhos: "
        + "; ".join(
            f"{row['label']} (rho={float(row['rho']):.4f})" for row in near_zero
        )
        + ".",
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
        stats_row, ccf = _lagged_stats(table, left, right)
        # Sanity: k=0 must match same-sample Pearson
        x = table[f"{left}_log_return"].to_numpy(dtype=float)
        y = table[f"{right}_log_return"].to_numpy(dtype=float)
        pearson_k0 = float(stats.pearsonr(x, y).statistic)
        assert abs(stats_row["rho_k0"] - pearson_k0) < 1e-12

        stem = f"{left}-{right}_Lagged_D1"
        fig_paths = _save_figures(table, left, right, ccf, stem)

        xlsx_path = OUT_DIR / f"{stem}.xlsx"
        excel_frame = table.copy()
        excel_frame["time"] = pd.to_datetime(excel_frame["time"], utc=True).dt.strftime(
            "%Y-%m-%d"
        )
        with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
            excel_frame.to_excel(writer, index=False, sheet_name="matched_rows")
            ccf.to_excel(writer, index=False, sheet_name="ccf")

        html_path = OUT_DIR / f"{stem}_data.html"
        html_path.write_text(
            (
                f"<!DOCTYPE html><html><head><meta charset='utf-8'>"
                f"<title>{stem} data</title></head><body>"
                f"<h1>{left} and {right}: matched rows for lagged "
                f"cross-correlation</h1>"
                f"<p>n={int(stats_row['n'])}. Complete archive also in "
                f"{xlsx_path.name}.</p>"
                + excel_frame.to_html(index=False)
                + "<h2>CCF</h2>"
                + ccf.to_html(index=False)
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
            ccf=ccf,
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
                "rho_k0": stats_row["rho_k0"],
                "rho_L_to_R_k1": stats_row["rho_L_to_R_k1"],
                "p_L_to_R_k1": stats_row["p_L_to_R_k1"],
                "rho_R_to_L_k1": stats_row["rho_R_to_L_k1"],
                "p_R_to_L_k1": stats_row["p_R_to_L_k1"],
                "best_abs_L_to_R_k": int(stats_row["best_abs_L_to_R_k"]),
                "best_abs_L_to_R_rho": stats_row["best_abs_L_to_R_rho"],
                "best_abs_R_to_L_k": int(stats_row["best_abs_R_to_L_k"]),
                "best_abs_R_to_L_rho": stats_row["best_abs_R_to_L_rho"],
                "docx": docx_path.name,
                "xlsx": xlsx_path.name,
                "html": html_path.name,
            }
        )
        print(
            f"Wrote {docx_path.name}  L->R(1)={stats_row['rho_L_to_R_k1']:.4f} "
            f"R->L(1)={stats_row['rho_R_to_L_k1']:.4f}  n={int(stats_row['n'])}",
            flush=True,
        )

    index = pd.DataFrame(index_rows)
    index.to_excel(OUT_DIR / "index.xlsx", index=False, sheet_name="index")

    notes = [
        "# Lagged cross-correlation experiments v001",
        "",
        "## Research question",
        "",
        "For each unordered pair among the eight majors, what is the lagged "
        "cross-correlation of matched daily log returns of close at "
        "pre-specified lags k=0..10 in both directions on the Alpari D1 "
        "history?",
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
        (
            f"- Statistic: rho_X->Y(k)=Pearson(x_t, y_{{t+k}}) for k=0..{K_MAX} "
            "in both directions via `scipy.stats.pearsonr` with Fisher 95% "
            "intervals; headline = k=1 both ways; k=0 is same-bar side "
            "check; largest |rho| among k=1..10 is descriptive only"
        ),
        "- Outputs: 28 Word reports, 28 full-data HTML tables, 28 Excel "
        "workbooks (matched_rows + ccf sheets), charts under "
        "`outputs/figures/` (closes, returns, CCF bars)",
        "",
        "## Index",
        "",
        "| pair | n | rho_k0 | rho_L_to_R_k1 | p_L_to_R_k1 | rho_R_to_L_k1 | "
        "p_R_to_L_k1 | best_abs_L_to_R_k | best_abs_L_to_R_rho | "
        "best_abs_R_to_L_k | best_abs_R_to_L_rho |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | "
        "---: | ---: |",
    ]
    for row in index_rows:
        notes.append(
            f"| {row['pair']} | {row['n']} | {float(row['rho_k0']):.6f} | "
            f"{float(row['rho_L_to_R_k1']):.6f} | "
            f"{float(row['p_L_to_R_k1']):.6g} | "
            f"{float(row['rho_R_to_L_k1']):.6f} | "
            f"{float(row['p_R_to_L_k1']):.6g} | "
            f"{row['best_abs_L_to_R_k']} | "
            f"{float(row['best_abs_L_to_R_rho']):.6f} | "
            f"{row['best_abs_R_to_L_k']} | "
            f"{float(row['best_abs_R_to_L_rho']):.6f} |"
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
