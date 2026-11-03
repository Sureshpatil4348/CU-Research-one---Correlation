"""Shrinkage correlation on Alpari D1 majors: panel shrink, then one Word/HTML/Excel per pair."""

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
from sklearn.covariance import LedoitWolf

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from shared.mt5_data import MAJOR_PAIRS, load_snapshot

SNAPSHOT_REL = Path("data/snapshots/2026-11-03_majors_alpari_D1")
EXP_DIR = Path(__file__).resolve().parent
OUT_DIR = EXP_DIR / "outputs"
FIG_DIR = OUT_DIR / "figures"
OHLCV = ["open", "high", "low", "close", "tick_volume", "spread", "real_volume"]
DELTA_FIXED = 0.2
METHOD_NOTE = (
    "Shrinkage blends the sample covariance matrix S of matched daily log "
    "returns of close, ln(close_t / close_t-1), toward a simple target, then "
    "converts the shrunk covariance into correlations. Quotes are not "
    "inverted. This experiment builds one common calendar across all eight "
    "majors, forms S with the unbiased n-1 divisor, then reports two "
    "shrinkage specs: fixed delta = 0.2 with mu equal to the average sample "
    "variance (mu * I target), and sklearn Ledoit-Wolf with its estimated "
    "delta. Pair reports pull rho_ij from those panel matrices. Same-panel "
    "Pearson r is a side check only. Shrinkage improves conditioning; it is "
    "not a cause, not a lead, and not a trading signal."
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


def _panel_table(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    indexed = {name: frame.set_index("time") for name, frame in frames.items()}
    common = indexed[MAJOR_PAIRS[0]].index
    for name in MAJOR_PAIRS[1:]:
        common = common.intersection(indexed[name].index)
    common = common.sort_values()
    cols: dict[str, pd.Series] = {"time": pd.Series(common, index=common)}
    for name in MAJOR_PAIRS:
        a = indexed[name]
        for col in OHLCV + ["log_return"]:
            cols[f"{name}_{col}"] = a.loc[common, col]
    table = pd.DataFrame(cols)
    ret_cols = [f"{name}_log_return" for name in MAJOR_PAIRS]
    table = table.dropna(subset=ret_cols).reset_index(drop=True)
    return table


def _cov_to_corr(cov: np.ndarray) -> np.ndarray:
    d = np.sqrt(np.clip(np.diag(cov), 1e-18, None))
    return cov / np.outer(d, d)


def _fixed_shrink(S: np.ndarray, delta: float = DELTA_FIXED) -> tuple[np.ndarray, float]:
    mu = float(np.mean(np.diag(S)))
    k = S.shape[0]
    sigma = (1.0 - delta) * S + delta * mu * np.eye(k)
    return sigma, mu


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
    rho = stats_row["rho_02"]
    n = int(stats_row["n"])
    strength = _strength_label(rho)
    direction = "positive" if rho >= 0 else "negative"
    return (
        f"Over the common {n}-day eight-major panel for {left} and {right} "
        f"(broker quote directions unchanged), fixed-delta shrinkage "
        f"correlation at delta={DELTA_FIXED} is {_fmt(rho, 4)} ({direction}, "
        f"{strength} linear link in this sample). Ledoit-Wolf rho is "
        f"{_fmt(stats_row['rho_LW'], 4)} with estimated delta="
        f"{_fmt(stats_row['delta_LW'], 6)}. Same-panel Pearson r is "
        f"{_fmt(stats_row['pearson_r'], 4)} (rho_02 minus r = "
        f"{_fmt(stats_row['rho_02_minus_r'], 4)}; rho_LW minus r = "
        f"{_fmt(stats_row['rho_LW_minus_r'], 4)}). This does not establish "
        f"cause, lead-lag, or a lasting trading rule."
    )


def _pair_slice(panel: pd.DataFrame, left: str, right: str) -> pd.DataFrame:
    cols = ["time"]
    for name in (left, right):
        for col in OHLCV + ["log_return"]:
            cols.append(f"{name}_{col}")
    return panel.loc[:, cols].copy()


def _save_figures(
    table: pd.DataFrame,
    left: str,
    right: str,
    stem: str,
) -> dict[str, Path]:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    times = pd.to_datetime(table["time"], utc=True)
    x = table[f"{left}_log_return"].to_numpy(dtype=float)
    y = table[f"{right}_log_return"].to_numpy(dtype=float)

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

    fig, ax = plt.subplots(figsize=(5.5, 5.2))
    ax.scatter(x, y, s=6, alpha=0.35, color="#2ca02c")
    ax.set_xlabel(f"{left} log return")
    ax.set_ylabel(f"{right} log return")
    ax.set_title(f"Log-return scatter: {left} vs {right}")
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
    drop_note: str,
    snapshot_name: str,
    mu: float,
    fig_paths: dict[str, Path],
    xlsx_name: str,
    out_path: Path,
) -> None:
    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(10)

    _add_heading(doc, f"Shrinkage correlation: {left} and {right}", 0)
    _add_para(
        doc,
        "Method 08 / eight-major panel / delta = 0.2 and Ledoit-Wolf / "
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
        f"Common eight-major panel window: {first} to {last} (UTC bar dates)",
        f"Panel matched return count n: {int(stats_row['n'])}",
        drop_note,
        f"Fixed shrinkage: delta={DELTA_FIXED}, mu={mu:.8g} (mean of diag(S))",
        f"Ledoit-Wolf estimated delta: {stats_row['delta_LW']:.8g}",
        "Panel symbols: " + ", ".join(MAJOR_PAIRS),
        f"Complete matched rows (Excel): {xlsx_name}",
        f"Complete matched rows (HTML table): {xlsx_name.replace('.xlsx', '_data.html')}",
    ]
    for line in setup_lines:
        _add_para(doc, line)

    _add_heading(doc, "Method carried forward", 1)
    _add_para(doc, METHOD_NOTE)

    _add_heading(doc, "Results", 1)
    result = pd.DataFrame(
        [
            {
                "pearson_r": round(stats_row["pearson_r"], 6),
                "rho_02": round(stats_row["rho_02"], 6),
                "rho_LW": round(stats_row["rho_LW"], 6),
                "rho_02_minus_r": round(stats_row["rho_02_minus_r"], 6),
                "rho_LW_minus_r": round(stats_row["rho_LW_minus_r"], 6),
                "delta_LW": round(stats_row["delta_LW"], 8),
            }
        ]
    )
    _add_small_table(doc, result)

    _add_heading(doc, "Conclusion", 1)
    _add_para(doc, _conclusion(left, right, stats_row))

    _add_heading(doc, "Charts", 1)
    for key, title in (
        ("closes", "Daily closes"),
        ("returns", "Daily log returns"),
        ("scatter", "Log-return scatter"),
    ):
        _add_para(doc, title, bold=True)
        doc.add_picture(str(fig_paths[key]), width=Inches(6.2))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

    _add_heading(doc, "Data report", 1)
    _add_para(
        doc,
        "Every panel row for this pair slice is stored in the sibling Excel "
        f"workbook named {xlsx_name}. Full-panel covariance and correlation "
        "matrices are saved once under outputs/ as CSV files. Embedding all "
        "rows as a Word table is impractical at this length; the Word file "
        "holds the column list, column summaries, and the first and last "
        "15 matched rows.",
    )
    _add_para(doc, "Columns: " + ", ".join(table.columns))

    numeric_cols = [c for c in table.columns if c != "time"]
    summary = (
        table[numeric_cols].describe().T.reset_index().rename(columns={"index": "column"})
    )
    _add_para(doc, "Column summaries (panel rows)", bold=True)
    _add_small_table(doc, summary.round(8))

    preview_cols = [
        "time",
        f"{left}_close",
        f"{right}_close",
        f"{left}_log_return",
        f"{right}_log_return",
    ]
    _add_para(doc, "First 15 panel rows (selected columns)", bold=True)
    _add_small_table(doc, table.loc[:, preview_cols].head(15))
    _add_para(doc, "Last 15 panel rows (selected columns)", bold=True)
    _add_small_table(doc, table.loc[:, preview_cols].tail(15))

    doc.save(out_path)


def _cross_pair_conclusion(index_rows: list[dict[str, object]]) -> list[str]:
    by_rho = sorted(index_rows, key=lambda row: float(row["rho_02"]))
    by_abs_gap = sorted(
        index_rows,
        key=lambda row: abs(float(row["rho_02_minus_r"])),
        reverse=True,
    )
    strongest_pos = by_rho[-1]
    strongest_neg = by_rho[0]
    near_zero = sorted(index_rows, key=lambda row: abs(float(row["rho_02"])))[:3]
    top_gaps = by_abs_gap[:3]

    return [
        "## Cross-pair conclusion",
        "",
        "Reading of the 28-pair index only. Not a 29th pair analysis and not a "
        "trading signal.",
        "",
        (
            f"Strongest positive fixed-delta shrink link: {strongest_pos['pair']} "
            f"(rho_02={float(strongest_pos['rho_02']):.4f}, n={strongest_pos['n']})."
        ),
        (
            f"Strongest negative fixed-delta shrink link: {strongest_neg['pair']} "
            f"(rho_02={float(strongest_neg['rho_02']):.4f}, n={strongest_neg['n']})."
        ),
        "Nearest-to-zero fixed-delta shrink links: "
        + "; ".join(
            f"{row['pair']} (rho_02={float(row['rho_02']):.4f})" for row in near_zero
        )
        + ".",
        "Largest |rho_02 minus Pearson r| gaps on the same panel: "
        + "; ".join(
            f"{row['pair']} (gap={float(row['rho_02_minus_r']):.4f}, "
            f"rho_02={float(row['rho_02']):.4f}, r={float(row['pearson_r']):.4f})"
            for row in top_gaps
        )
        + ". A large gap means the delta=0.2 blend pulled the off-diagonal "
        "harder relative to the raw sample link; inspect that pair's scatter "
        "before treating either score as settled.",
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
    panel = _panel_table(frames)
    n = len(panel)

    ret_cols = [f"{name}_log_return" for name in MAJOR_PAIRS]
    returns = panel.loc[:, ret_cols].to_numpy(dtype=float)
    S = np.cov(returns, rowvar=False, ddof=1)
    sigma_02, mu = _fixed_shrink(S)
    corr_02 = _cov_to_corr(sigma_02)

    lw = LedoitWolf().fit(returns)
    sigma_lw = lw.covariance_
    corr_lw = _cov_to_corr(sigma_lw)
    delta_lw = float(lw.shrinkage_)
    sample_corr = _cov_to_corr(S)

    name_list = list(MAJOR_PAIRS)
    pd.DataFrame(S, index=name_list, columns=name_list).to_csv(OUT_DIR / "sample_cov.csv")
    pd.DataFrame(corr_02, index=name_list, columns=name_list).to_csv(
        OUT_DIR / "shrink_02_corr.csv"
    )
    pd.DataFrame(corr_lw, index=name_list, columns=name_list).to_csv(
        OUT_DIR / "ledoit_wolf_corr.csv"
    )
    panel_out = panel.copy()
    panel_out["time"] = pd.to_datetime(panel_out["time"], utc=True).dt.strftime("%Y-%m-%d")
    panel_out.loc[:, ["time"] + ret_cols].to_csv(OUT_DIR / "return_panel.csv", index=False)

    index_rows: list[dict[str, object]] = []
    pairs = list(itertools.combinations(MAJOR_PAIRS, 2))

    for left, right in pairs:
        i = name_list.index(left)
        j = name_list.index(right)
        pearson_r = float(sample_corr[i, j])
        rho_02 = float(corr_02[i, j])
        rho_lw = float(corr_lw[i, j])
        stats_row = {
            "n": float(n),
            "pearson_r": pearson_r,
            "rho_02": rho_02,
            "rho_LW": rho_lw,
            "rho_02_minus_r": rho_02 - pearson_r,
            "rho_LW_minus_r": rho_lw - pearson_r,
            "delta_LW": delta_lw,
        }
        table = _pair_slice(panel, left, right)
        stem = f"{left}-{right}_Shrinkage_D1"
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
                f"<h1>{left} and {right}: panel rows for shrinkage correlation</h1>"
                f"<p>n={n}. Complete archive also in {xlsx_path.name}.</p>"
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
            drop_note=drop_note,
            snapshot_name=snapshot_name,
            mu=mu,
            fig_paths=fig_paths,
            xlsx_name=xlsx_path.name,
            out_path=docx_path,
        )

        index_rows.append(
            {
                "pair": f"{left}-{right}",
                "n": n,
                "pearson_r": pearson_r,
                "rho_02": rho_02,
                "rho_LW": rho_lw,
                "rho_02_minus_r": rho_02 - pearson_r,
                "rho_LW_minus_r": rho_lw - pearson_r,
                "delta_LW": delta_lw,
                "docx": docx_path.name,
                "xlsx": xlsx_path.name,
                "html": html_path.name,
            }
        )
        print(
            f"Wrote {docx_path.name}  rho_02={rho_02:.4f}  rho_LW={rho_lw:.4f}",
            flush=True,
        )

    index = pd.DataFrame(index_rows)
    index.to_excel(OUT_DIR / "index.xlsx", index=False, sheet_name="index")

    notes = [
        "# Shrinkage correlation experiments v001",
        "",
        "## Research question",
        "",
        "For each unordered pair among the eight majors, what is the "
        "shrinkage correlation pulled from an eight-asset covariance matrix "
        "of matched daily log returns of close on the Alpari D1 history, "
        "using fixed delta = 0.2 and Ledoit-Wolf?",
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
        f"- Panel: common calendar across all eight majors, n={n}",
        f"- Fixed shrinkage: delta={DELTA_FIXED}, mu={mu:.8g} (mean of diag(S)), "
        "n-1 sample covariance",
        f"- Ledoit-Wolf: sklearn LedoitWolf, estimated delta={delta_lw:.8g}",
        "- Outputs: 28 Word reports, 28 HTML tables, 28 Excel workbooks, "
        "panel CSVs (return_panel, sample_cov, shrink_02_corr, "
        "ledoit_wolf_corr), charts under `outputs/figures/`",
        "",
        "## Index",
        "",
        "| pair | n | pearson_r | rho_02 | rho_LW | rho_02_minus_r | "
        "rho_LW_minus_r | delta_LW |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in index_rows:
        notes.append(
            f"| {row['pair']} | {row['n']} | {float(row['pearson_r']):.6f} | "
            f"{float(row['rho_02']):.6f} | {float(row['rho_LW']):.6f} | "
            f"{float(row['rho_02_minus_r']):.6f} | "
            f"{float(row['rho_LW_minus_r']):.6f} | "
            f"{float(row['delta_LW']):.6f} |"
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
