"""Hayashi-Yoshida covariance on Alpari D1 majors: Word, HTML, Excel per pair.

On synchronized daily bars the overlap indicator selects same-day intervals
only, so C_HY reduces to sum_t r_x,t * r_y,t. A HY-style correlation divides
by the matching HY variance estimates.
"""

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
METHOD_NOTE = (
    "Hayashi-Yoshida covariance C_HY sums products of log-price changes whose "
    "observation intervals overlap: C_HY = sum_i sum_j dX_i dY_j "
    "1(I_i overlaps J_j). This v001 uses the Alpari D1 snapshot of "
    "synchronized daily closes. Each return interval is the trading-day "
    "span between consecutive closes; same-calendar-day intervals for the "
    "two legs overlap, so C_HY reduces to sum_t r_x,t * r_y,t on matched "
    "days. HY variance estimates are sum_t r_x,t^2 and sum_t r_y,t^2. "
    "Headline rho_HY = C_HY / sqrt(V_X * V_Y) is the normalized form "
    "(cosine similarity of return vectors). Quotes are not inverted. "
    "Same-sample Pearson r is a side check. Async tick HY is not tested "
    "here (no tick snapshot). This is not causation and not a trading "
    "signal."
)


def hy_covariance(dx: list[float], dy: list[float], overlap: list[list[int]]) -> float:
    total = 0.0
    for i, dxi in enumerate(dx):
        for j, dyj in enumerate(dy):
            if overlap[i][j]:
                total += dxi * dyj
    return total


def _assert_guide_toys() -> None:
    dx = [0.010, 0.005]
    dy = [0.012, 0.008]
    overlap = [[1, 0], [1, 1]]
    c_hy = hy_covariance(dx, dy, overlap)
    assert abs(c_hy - 0.00022) < 1e-15


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


def _hy_stats(table: pd.DataFrame, left: str, right: str) -> dict[str, float]:
    x = table[f"{left}_log_return"].to_numpy(dtype=float)
    y = table[f"{right}_log_return"].to_numpy(dtype=float)
    pearson_r = float(stats.pearsonr(x, y).statistic)
    # Synced daily: only same-index intervals overlap
    c_hy = float(np.sum(x * y))
    v_x = float(np.sum(x * x))
    v_y = float(np.sum(y * y))
    den = math.sqrt(v_x * v_y)
    rho_hy = 0.0 if den == 0.0 else c_hy / den
    return {
        "n": float(len(table)),
        "c_hy": c_hy,
        "v_x": v_x,
        "v_y": v_y,
        "rho_hy": rho_hy,
        "pearson_r": pearson_r,
    }


def _fmt(value: float, digits: int = 4) -> str:
    if math.isnan(value):
        return "n/a"
    return f"{value:.{digits}f}"


def _conclusion(left: str, right: str, stats_row: dict[str, float]) -> str:
    return (
        f"Headline rho_HY for {left} and {right}: "
        f"{_fmt(stats_row['rho_hy'], 4)} "
        f"(C_HY={_fmt(stats_row['c_hy'], 8)}). "
        f"Pearson r = {_fmt(stats_row['pearson_r'], 4)}. "
        f"Synced D1 special case of HY (same-day overlaps only). "
        f"This is covariance linkage, not a trading signal."
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
    ax.set_title(f"Log returns: {left} and {right}")
    ax.set_ylabel("log return")
    ax.legend(loc="upper left")
    fig.tight_layout()
    paths["returns"] = FIG_DIR / f"{stem}_returns.png"
    fig.savefig(paths["returns"], dpi=120)
    plt.close(fig)

    prod = (
        table[f"{left}_log_return"].to_numpy(dtype=float)
        * table[f"{right}_log_return"].to_numpy(dtype=float)
    )
    cum = np.cumsum(prod)
    fig, ax = plt.subplots(figsize=(10, 4.2))
    ax.plot(times, cum, color="#087F8C", linewidth=0.9)
    ax.set_title(f"Cumulative same-day return products (C_HY path): {left} and {right}")
    ax.set_ylabel("cumsum(r_x * r_y)")
    fig.tight_layout()
    paths["cumprod"] = FIG_DIR / f"{stem}_cumprod.png"
    fig.savefig(paths["cumprod"], dpi=120)
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
    fig_paths: dict[str, Path],
    xlsx_name: str,
    out_path: Path,
) -> None:
    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(10)

    _add_heading(doc, f"Hayashi-Yoshida covariance: {left} and {right}", 0)
    _add_para(
        doc,
        "Method 26 / daily log returns / synced-D1 HY special case / "
        "Alpari D1 full available history",
    )

    _add_heading(doc, "Study setup", 1)
    first = pd.to_datetime(table["time"].iloc[0], utc=True).date().isoformat()
    last = pd.to_datetime(table["time"].iloc[-1], utc=True).date().isoformat()
    for line in (
        f"Logical pair: {left} , {right}",
        f"Broker symbols: {left_broker} , {right_broker}",
        f"Snapshot: {snapshot_name}",
        "Timeframe: D1 (synchronized closes)",
        f"Matched return window: {first} to {last} (UTC bar dates)",
        f"Matched return count n: {int(stats_row['n'])}",
        drop_note,
        "Intervals: consecutive daily close-to-close; overlap = same day",
        "Headline: rho_HY = C_HY / sqrt(V_X * V_Y)",
        f"Complete matched rows (Excel): {xlsx_name}",
        f"Complete matched rows (HTML table): {xlsx_name.replace('.xlsx', '_data.html')}",
    ):
        _add_para(doc, line)

    _add_heading(doc, "Method carried forward", 1)
    _add_para(doc, METHOD_NOTE)

    _add_heading(doc, "Results (headline)", 1)
    _add_para(doc, f"rho_HY: {_fmt(stats_row['rho_hy'], 6)}")
    _add_para(doc, f"C_HY: {_fmt(stats_row['c_hy'], 8)}")
    _add_para(doc, f"V_X (sum r^2): {_fmt(stats_row['v_x'], 8)}")
    _add_para(doc, f"V_Y (sum r^2): {_fmt(stats_row['v_y'], 8)}")
    _add_para(doc, f"Pearson r: {_fmt(stats_row['pearson_r'], 6)}")

    _add_heading(doc, "Conclusion", 1)
    _add_para(doc, _conclusion(left, right, stats_row))

    _add_heading(doc, "Charts", 1)
    for key, title in (
        ("closes", "Daily closes"),
        ("returns", "Daily log returns"),
        ("cumprod", "Cumulative same-day return products"),
    ):
        _add_para(doc, title, bold=True)
        doc.add_picture(str(fig_paths[key]), width=Inches(6.2))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

    _add_heading(doc, "Data report", 1)
    _add_para(
        doc,
        "Matched rows are in the sibling Excel workbook "
        f"named {xlsx_name}. Embedding all rows as a Word table is "
        "impractical; this file holds column summaries and the first and "
        "last 15 matched rows.",
    )
    _add_para(doc, "Columns: " + ", ".join(table.columns))
    numeric_cols = [c for c in table.columns if c != "time"]
    col_summary = (
        table[numeric_cols].describe().T.reset_index().rename(columns={"index": "column"})
    )
    _add_para(doc, "Column summaries (matched calculation rows)", bold=True)
    _add_small_table(doc, col_summary.round(8))
    preview_cols = ["time", f"{left}_log_return", f"{right}_log_return"]
    _add_para(doc, "First 15 matched rows (selected columns)", bold=True)
    _add_small_table(doc, table.loc[:, preview_cols].head(15))
    _add_para(doc, "Last 15 matched rows (selected columns)", bold=True)
    _add_small_table(doc, table.loc[:, preview_cols].tail(15))
    doc.save(out_path)


def _cross_pair_conclusion(index_rows: list[dict[str, object]]) -> list[str]:
    by_rho = sorted(index_rows, key=lambda r: float(r["rho_hy"]))
    strongest_pos = by_rho[-1]
    strongest_neg = by_rho[0]
    nearest = sorted(index_rows, key=lambda r: abs(float(r["rho_hy"])))[:3]
    return [
        "## Cross-pair conclusion",
        "",
        "Reading of the 28-pair index at pre-specified rho_HY "
        "(synced D1 special case). Not a 29th pair analysis and not a "
        "trading signal.",
        "",
        (
            f"Strongest positive: {strongest_pos['pair']} "
            f"(rho_HY={float(strongest_pos['rho_hy']):.4f})."
        ),
        (
            f"Strongest negative: {strongest_neg['pair']} "
            f"(rho_HY={float(strongest_neg['rho_hy']):.4f})."
        ),
        "Nearest-to-zero: "
        + "; ".join(
            f"{r['pair']} (rho_HY={float(r['rho_hy']):.4f})" for r in nearest
        )
        + ".",
        "",
    ]


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
        stats_row = _hy_stats(table, left, right)
        stem = f"{left}-{right}_HY_D1"
        fig_paths = _save_figures(table, left, right, stem)

        xlsx_path = OUT_DIR / f"{stem}.xlsx"
        excel_frame = table.copy()
        excel_frame["time"] = pd.to_datetime(excel_frame["time"], utc=True).dt.strftime(
            "%Y-%m-%d"
        )
        excel_frame["product_xy"] = (
            excel_frame[f"{left}_log_return"] * excel_frame[f"{right}_log_return"]
        )
        with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
            excel_frame.to_excel(writer, index=False, sheet_name="matched_rows")

        html_path = OUT_DIR / f"{stem}_data.html"
        html_path.write_text(
            (
                f"<!DOCTYPE html><html><head><meta charset='utf-8'>"
                f"<title>{stem} data</title></head><body>"
                f"<h1>{left} and {right}: matched rows for Hayashi-Yoshida "
                f"(synced D1)</h1>"
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
                "c_hy": stats_row["c_hy"],
                "rho_hy": stats_row["rho_hy"],
                "pearson_r": stats_row["pearson_r"],
                "docx": docx_path.name,
                "xlsx": xlsx_path.name,
                "html": html_path.name,
            }
        )
        print(
            f"Wrote {docx_path.name}  rho_HY="
            f"{stats_row['rho_hy']:.4f}  "
            f"C_HY={stats_row['c_hy']:.6f}  "
            f"n={int(stats_row['n'])}",
            flush=True,
        )

    index = pd.DataFrame(index_rows)
    index.to_excel(OUT_DIR / "index.xlsx", index=False, sheet_name="index")

    notes = [
        "# Hayashi-Yoshida covariance experiments v001",
        "",
        "## Research question",
        "",
        "For each unordered pair among the eight majors, what is the "
        "synced-D1 Hayashi-Yoshida covariance and normalized rho_HY of "
        "matched daily log returns of close on the Alpari D1 history?",
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
        "- Intervals: consecutive daily close-to-close; overlap = same day "
        "(synchronized special case of HY)",
        "- Statistic: C_HY = sum r_x r_y; rho_HY = C_HY / sqrt(sum r_x^2 * "
        "sum r_y^2) as headline; Pearson r as a side check",
        "- Async tick HY: not tested (no tick snapshot in this project yet)",
        "- Outputs: 28 Word reports, 28 full-data HTML tables, 28 Excel "
        "workbooks, charts under `outputs/figures/`",
        "",
        "## Index",
        "",
        "| pair | n | c_hy | rho_hy | pearson_r |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for row in index_rows:
        notes.append(
            f"| {row['pair']} | {row['n']} | "
            f"{float(row['c_hy']):.8f} | "
            f"{float(row['rho_hy']):.6f} | "
            f"{float(row['pearson_r']):.6f} |"
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
