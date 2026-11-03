"""Volatility correlation on Alpari D1 majors: Word, HTML, and Excel per pair.

Realized correlation (intraday buckets) is out of scope for this D1-only
snapshot; NOTES and reports document that explicitly.
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
    "Volatility correlation rho_vol = Corr(|x_t|, |y_t|) measures whether "
    "absolute daily log returns of close move together in size, regardless "
    "of sign. Quotes are not inverted. Same-sample signed Pearson r is a "
    "side check. The formula sheet also defines within-day realized "
    "correlation rho_realized,d from intraday buckets; this v001 uses the "
    "Alpari D1 snapshot only, so rho_realized is not computed (no intraday "
    "buckets). This is not causation and not a trading signal."
)


def _assert_guide_toys() -> None:
    ret_x = [0.010, -0.005, 0.008]
    ret_y = [0.012, 0.004, -0.006]
    abs_x = [abs(v) for v in ret_x]
    abs_y = [abs(v) for v in ret_y]
    rho_vol = float(stats.pearsonr(abs_x, abs_y).statistic)
    assert abs(rho_vol - 0.9226129063148779) < 1e-9
    intra_x = [0.004, 0.003, 0.003]
    intra_y = [0.005, 0.002, 0.005]
    num = sum(a * b for a, b in zip(intra_x, intra_y))
    den = math.sqrt(sum(a * a for a in intra_x) * sum(b * b for b in intra_y))
    rho_realized = num / den
    assert abs(rho_realized - 0.9568580574191401) < 1e-12




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
    table[f"{left_name}_abs_return"] = table[f"{left_name}_log_return"].abs()
    table[f"{right_name}_abs_return"] = table[f"{right_name}_log_return"].abs()
    return table.reset_index(drop=True)


def _vol_stats(table: pd.DataFrame, left: str, right: str) -> dict[str, float]:
    x = table[f"{left}_log_return"].to_numpy(dtype=float)
    y = table[f"{right}_log_return"].to_numpy(dtype=float)
    ax = np.abs(x)
    ay = np.abs(y)
    pearson_r = float(stats.pearsonr(x, y).statistic)
    rho_vol = float(stats.pearsonr(ax, ay).statistic)
    return {
        "n": float(len(table)),
        "rho_vol": rho_vol,
        "pearson_r": pearson_r,
        "mean_abs_L": float(np.mean(ax)),
        "mean_abs_R": float(np.mean(ay)),
    }


def _fmt(value: float, digits: int = 4) -> str:
    if math.isnan(value):
        return "n/a"
    return f"{value:.{digits}f}"


def _conclusion(left: str, right: str, stats_row: dict[str, float]) -> str:
    return (
        f"Headline rho_vol for {left} and {right}: "
        f"{_fmt(stats_row['rho_vol'], 4)}. "
        f"Signed Pearson r = {_fmt(stats_row['pearson_r'], 4)}. "
        f"Mean |return|: {_fmt(stats_row['mean_abs_L'], 6)} ({left}), "
        f"{_fmt(stats_row['mean_abs_R'], 6)} ({right}). "
        f"rho_realized not computed (D1 snapshot has no intraday buckets). "
        f"This is absolute-move co-movement, not a trading signal."
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

    fig, ax = plt.subplots(figsize=(6.5, 6.0))
    ax.scatter(
        table[f"{left}_abs_return"],
        table[f"{right}_abs_return"],
        s=4,
        alpha=0.25,
        color="#087F8C",
    )
    ax.set_xlabel(f"|{left} log return|")
    ax.set_ylabel(f"|{right} log return|")
    ax.set_title(f"Absolute returns scatter: {left} and {right}")
    fig.tight_layout()
    paths["abs_scatter"] = FIG_DIR / f"{stem}_abs_scatter.png"
    fig.savefig(paths["abs_scatter"], dpi=120)
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

    _add_heading(doc, f"Volatility correlation: {left} and {right}", 0)
    _add_para(
        doc,
        "Method 25 / daily |log returns| / rho_vol / "
        "Alpari D1 full available history (realized deferred)",
    )

    _add_heading(doc, "Study setup", 1)
    first = pd.to_datetime(table["time"].iloc[0], utc=True).date().isoformat()
    last = pd.to_datetime(table["time"].iloc[-1], utc=True).date().isoformat()
    for line in (
        f"Logical pair: {left} , {right}",
        f"Broker symbols: {left_broker} , {right_broker}",
        f"Snapshot: {snapshot_name}",
        "Timeframe: D1",
        f"Matched return window: {first} to {last} (UTC bar dates)",
        f"Matched return count n: {int(stats_row['n'])}",
        drop_note,
        "Statistic: rho_vol = Corr(|log return_L|, |log return_R|)",
        "rho_realized: not computed (no intraday buckets in this snapshot)",
        f"Complete matched rows (Excel): {xlsx_name}",
        f"Complete matched rows (HTML table): {xlsx_name.replace('.xlsx', '_data.html')}",
    ):
        _add_para(doc, line)

    _add_heading(doc, "Method carried forward", 1)
    _add_para(doc, METHOD_NOTE)

    _add_heading(doc, "Results (headline)", 1)
    _add_para(doc, f"rho_vol: {_fmt(stats_row['rho_vol'], 6)}")
    _add_para(doc, f"Pearson r (signed): {_fmt(stats_row['pearson_r'], 6)}")
    _add_para(doc, f"mean |{left}|: {_fmt(stats_row['mean_abs_L'], 8)}")
    _add_para(doc, f"mean |{right}|: {_fmt(stats_row['mean_abs_R'], 8)}")
    _add_para(doc, "rho_realized: n/a (D1-only snapshot)")

    _add_heading(doc, "Conclusion", 1)
    _add_para(doc, _conclusion(left, right, stats_row))

    _add_heading(doc, "Charts", 1)
    for key, title in (
        ("closes", "Daily closes"),
        ("returns", "Daily log returns"),
        ("abs_scatter", "Absolute returns scatter"),
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
    preview_cols = [
        "time",
        f"{left}_log_return",
        f"{right}_log_return",
        f"{left}_abs_return",
        f"{right}_abs_return",
    ]
    _add_para(doc, "First 15 matched rows (selected columns)", bold=True)
    _add_small_table(doc, table.loc[:, preview_cols].head(15))
    _add_para(doc, "Last 15 matched rows (selected columns)", bold=True)
    _add_small_table(doc, table.loc[:, preview_cols].tail(15))
    doc.save(out_path)


def _cross_pair_conclusion(index_rows: list[dict[str, object]]) -> list[str]:
    by_rho = sorted(index_rows, key=lambda r: float(r["rho_vol"]))
    strongest = by_rho[-1]
    nearest = sorted(index_rows, key=lambda r: abs(float(r["rho_vol"])))[:3]
    return [
        "## Cross-pair conclusion",
        "",
        "Reading of the 28-pair index at pre-specified rho_vol = "
        "Corr(|x|,|y|). Not a 29th pair analysis and not a trading signal. "
        "rho_realized was not computed on this D1 snapshot.",
        "",
        (
            f"Strongest rho_vol: {strongest['pair']} "
            f"(rho_vol={float(strongest['rho_vol']):.4f})."
        ),
        "Nearest-to-zero rho_vol: "
        + "; ".join(
            f"{r['pair']} (rho_vol={float(r['rho_vol']):.4f})" for r in nearest
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
        stats_row = _vol_stats(table, left, right)
        stem = f"{left}-{right}_Vol_D1"
        fig_paths = _save_figures(table, left, right, stem)

        xlsx_path = OUT_DIR / f"{stem}.xlsx"
        excel_frame = table.copy()
        excel_frame["time"] = pd.to_datetime(excel_frame["time"], utc=True).dt.strftime(
            "%Y-%m-%d"
        )
        with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
            excel_frame.to_excel(writer, index=False, sheet_name="matched_rows")

        html_path = OUT_DIR / f"{stem}_data.html"
        html_path.write_text(
            (
                f"<!DOCTYPE html><html><head><meta charset='utf-8'>"
                f"<title>{stem} data</title></head><body>"
                f"<h1>{left} and {right}: matched rows for volatility "
                f"correlation</h1>"
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
                "rho_vol": stats_row["rho_vol"],
                "pearson_r": stats_row["pearson_r"],
                "docx": docx_path.name,
                "xlsx": xlsx_path.name,
                "html": html_path.name,
            }
        )
        print(
            f"Wrote {docx_path.name}  rho_vol="
            f"{stats_row['rho_vol']:.4f}  "
            f"r={stats_row['pearson_r']:.4f}  "
            f"n={int(stats_row['n'])}",
            flush=True,
        )

    index = pd.DataFrame(index_rows)
    index.to_excel(OUT_DIR / "index.xlsx", index=False, sheet_name="index")

    notes = [
        "# Volatility and realized correlation experiments v001",
        "",
        "## Research question",
        "",
        "For each unordered pair among the eight majors, what is "
        "rho_vol = Corr(|log return|, |log return|) of matched daily closes "
        "on the Alpari D1 history?",
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
        "- Statistic: rho_vol = Pearson on absolute log returns (headline); "
        "signed Pearson r as a side check",
        "- rho_realized: not computed — D1 snapshot has no intraday buckets "
        "(formula sheet requires synchronized intraday returns within day d)",
        "- Outputs: 28 Word reports, 28 full-data HTML tables, 28 Excel "
        "workbooks, charts under `outputs/figures/`",
        "",
        "## Index",
        "",
        "| pair | n | rho_vol | pearson_r |",
        "| --- | ---: | ---: | ---: |",
    ]
    for row in index_rows:
        notes.append(
            f"| {row['pair']} | {row['n']} | "
            f"{float(row['rho_vol']):.6f} | "
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
