"""Kendall tau-b on Alpari D1 majors: one Word report, HTML table, and Excel per unique pair."""

from __future__ import annotations

import itertools
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
    "Kendall tau-b counts concordant versus discordant unordered day pairs "
    "on matched daily log returns of close, ln(close_t / close_t-1), in the "
    "broker quote direction, with a tie-adjusted denominator. Quotes are not "
    "inverted. tau-b is symmetric under swap of the two symbols. tau-b = 0 "
    "means concordant and discordant counts balance in this sample; it does "
    "not mean no link of any kind. The score is not a cause, not a lead, and "
    "not a trading signal. Daily rows are not independent draws, so the "
    "two-sided p-value and approximate Bonett-Wright interval are reported "
    "and treated as secondary to tau-b. Same-sample Pearson r is shown only "
    "as a side check; a large tau-b minus r gap can flag outliers or a "
    "non-straight link."
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


def _pair_table(
    left: pd.DataFrame,
    right: pd.DataFrame,
    left_name: str,
    right_name: str,
) -> pd.DataFrame:
    a = left.set_index("time")
    b = right.set_index("time")
    common = a.index.intersection(b.index)
    common = common.sort_values()
    cols: dict[str, pd.Series] = {"time": pd.Series(common, index=common)}
    for col in OHLCV + ["log_return"]:
        cols[f"{left_name}_{col}"] = a.loc[common, col]
        cols[f"{right_name}_{col}"] = b.loc[common, col]
    table = pd.DataFrame(cols)
    table = table.dropna(subset=[f"{left_name}_log_return", f"{right_name}_log_return"])
    table = table.reset_index(drop=True)
    return table


def _bonett_wright_interval(tau: float, n: int, confidence: float = 0.95) -> tuple[float, float]:
    """Approximate Bonett-Wright interval for Kendall tau."""
    if n <= 4:
        return float("nan"), float("nan")
    z = np.arctanh(np.clip(tau, -0.999999, 0.999999))
    se = float(np.sqrt(0.437 / (n - 4)))
    z_crit = float(stats.norm.ppf(0.5 + confidence / 2.0))
    low = float(np.tanh(z - z_crit * se))
    high = float(np.tanh(z + z_crit * se))
    return low, high


def _repeat_value_count(values: np.ndarray) -> int:
    """Count how many distinct values appear more than once (cheap tie note)."""
    _, counts = np.unique(values, return_counts=True)
    return int(np.sum(counts > 1))


def _kendall_stats(x: np.ndarray, y: np.ndarray) -> dict[str, float]:
    result = stats.kendalltau(x, y, variant="b")
    tau_b = float(result.statistic)
    p = float(result.pvalue)
    n = int(len(x))
    ci_low, ci_high = _bonett_wright_interval(tau_b, n)
    pearson_r = float(stats.pearsonr(x, y).statistic)
    return {
        "tau_b": tau_b,
        "p": p,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "n": n,
        "pearson_r": pearson_r,
        "tau_minus_r": tau_b - pearson_r,
        "left_repeat_values": float(_repeat_value_count(x)),
        "right_repeat_values": float(_repeat_value_count(y)),
    }


def _strength_label(value: float) -> str:
    strength = "weak"
    if abs(value) >= 0.7:
        strength = "strong"
    elif abs(value) >= 0.4:
        strength = "moderate"
    return strength


def _conclusion(left: str, right: str, stats_row: dict[str, float]) -> str:
    tau_b = stats_row["tau_b"]
    n = int(stats_row["n"])
    strength = _strength_label(tau_b)
    direction = "positive" if tau_b >= 0 else "negative"
    return (
        f"Over {n} matched daily log-return rows for {left} and {right} "
        f"(broker quote directions unchanged), Kendall tau-b is {tau_b:.4f} "
        f"({direction}, {strength} concordance association in this sample). "
        f"Approximate 95% Bonett-Wright interval: [{stats_row['ci_low']:.4f}, "
        f"{stats_row['ci_high']:.4f}]. Same-sample Pearson r is "
        f"{stats_row['pearson_r']:.4f} (tau-b minus r = "
        f"{stats_row['tau_minus_r']:.4f}). Two-sided p under the usual "
        f"independent-pairs model is {stats_row['p']:.4g}; that model does "
        f"not match linked daily FX returns, so treat p as secondary. This "
        f"does not establish cause, lead-lag, or a lasting trading rule."
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
    """Add a compact Word table for a small frame (preview or summary)."""
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

    _add_heading(doc, f"Kendall tau-b: {left} and {right}", 0)
    _add_para(doc, "Method 03 / daily log returns / Alpari D1 full available history")

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
            f"Distinct log-return values that repeat: {left}="
            f"{int(stats_row['left_repeat_values'])}, {right}="
            f"{int(stats_row['right_repeat_values'])}"
        ),
        f"Complete matched rows (Excel): {xlsx_name}",
        f"Complete matched rows (HTML table): {xlsx_name.replace('.xlsx', '_data.html')}",
    ]
    for line in setup_lines:
        _add_para(doc, line)

    _add_heading(doc, "Method carried forward", 1)
    _add_para(doc, METHOD_NOTE)

    _add_heading(doc, "Results", 1)
    _add_para(doc, f"Kendall tau-b: {stats_row['tau_b']:.6f}")
    _add_para(doc, f"Two-sided p-value: {stats_row['p']:.6g}")
    _add_para(
        doc,
        f"Approximate 95% Bonett-Wright interval: "
        f"[{stats_row['ci_low']:.6f}, {stats_row['ci_high']:.6f}]",
    )
    _add_para(doc, f"Same-sample Pearson r: {stats_row['pearson_r']:.6f}")
    _add_para(doc, f"tau-b minus r: {stats_row['tau_minus_r']:.6f}")

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
        last_p = doc.paragraphs[-1]
        last_p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    _add_heading(doc, "Data report", 1)
    _add_para(
        doc,
        "Every matched row that entered Kendall tau-b is stored in the sibling "
        f"Excel workbook named {xlsx_name}. That file is the complete data "
        "archive for redrawing charts. Embedding all rows as a Word table is "
        "impractical at this length; the Word file holds the column list, "
        "column summaries, and the first and last 15 matched rows.",
    )
    _add_para(doc, "Columns: " + ", ".join(table.columns), bold=False)

    numeric_cols = [c for c in table.columns if c != "time"]
    summary = table[numeric_cols].describe().T.reset_index().rename(columns={"index": "column"})
    _add_para(doc, "Column summaries (matched calculation rows)", bold=True)
    _add_small_table(doc, summary.round(8))

    preview_cols = [
        "time",
        f"{left}_close",
        f"{right}_close",
        f"{left}_log_return",
        f"{right}_log_return",
        f"{left}_tick_volume",
        f"{right}_tick_volume",
    ]
    _add_para(doc, "First 15 matched rows (selected columns)", bold=True)
    _add_small_table(doc, table.loc[:, preview_cols].head(15))
    _add_para(doc, "Last 15 matched rows (selected columns)", bold=True)
    _add_small_table(doc, table.loc[:, preview_cols].tail(15))

    doc.save(out_path)


def _cross_pair_conclusion(index_rows: list[dict[str, object]]) -> list[str]:
    """Short reading of the 28-pair index for NOTES.md."""
    by_tau = sorted(index_rows, key=lambda row: float(row["tau_b"]))
    by_abs_gap = sorted(
        index_rows,
        key=lambda row: abs(float(row["tau_minus_r"])),
        reverse=True,
    )
    strongest_pos = by_tau[-1]
    strongest_neg = by_tau[0]
    near_zero = sorted(index_rows, key=lambda row: abs(float(row["tau_b"])))[:3]
    top_gaps = by_abs_gap[:3]

    lines = [
        "## Cross-pair conclusion",
        "",
        "Reading of the 28-pair index only. Not a 29th pair analysis and not a "
        "trading signal.",
        "",
        (
            f"Strongest positive concordance link: {strongest_pos['pair']} "
            f"(tau_b={float(strongest_pos['tau_b']):.4f}, "
            f"n={strongest_pos['n']})."
        ),
        (
            f"Strongest negative concordance link: {strongest_neg['pair']} "
            f"(tau_b={float(strongest_neg['tau_b']):.4f}, "
            f"n={strongest_neg['n']})."
        ),
        "Nearest-to-zero concordance links: "
        + "; ".join(
            f"{row['pair']} (tau_b={float(row['tau_b']):.4f})" for row in near_zero
        )
        + ".",
        "Largest |tau-b minus Pearson r| gaps on the same sample: "
        + "; ".join(
            f"{row['pair']} (gap={float(row['tau_minus_r']):.4f}, "
            f"tau_b={float(row['tau_b']):.4f}, r={float(row['pearson_r']):.4f})"
            for row in top_gaps
        )
        + ". A large gap can flag outliers or a non-straight link; inspect "
        "that pair's charts before treating either score as settled.",
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
        table = _pair_table(frames[left], frames[right], left, right)
        x = table[f"{left}_log_return"].to_numpy(dtype=float)
        y = table[f"{right}_log_return"].to_numpy(dtype=float)
        stats_row = _kendall_stats(x, y)
        stem = f"{left}-{right}_Kendall_D1"
        fig_paths = _save_figures(table, left, right, stem)

        xlsx_path = OUT_DIR / f"{stem}.xlsx"
        excel_frame = table.copy()
        excel_frame["time"] = pd.to_datetime(excel_frame["time"], utc=True).dt.strftime(
            "%Y-%m-%d"
        )
        excel_frame.to_excel(xlsx_path, index=False, sheet_name="matched_rows")

        html_path = OUT_DIR / f"{stem}_data.html"
        html_frame = excel_frame.copy()
        html_path.write_text(
            (
                f"<!DOCTYPE html><html><head><meta charset='utf-8'>"
                f"<title>{stem} data</title></head><body>"
                f"<h1>{left} and {right}: matched rows used for Kendall tau-b</h1>"
                f"<p>n={int(stats_row['n'])}. Complete archive also in "
                f"{xlsx_path.name}.</p>"
                + html_frame.to_html(index=False)
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
                "tau_b": stats_row["tau_b"],
                "p": stats_row["p"],
                "ci_low": stats_row["ci_low"],
                "ci_high": stats_row["ci_high"],
                "pearson_r": stats_row["pearson_r"],
                "tau_minus_r": stats_row["tau_minus_r"],
                "docx": docx_path.name,
                "xlsx": xlsx_path.name,
                "html": html_path.name,
            }
        )
        print(
            f"Wrote {docx_path.name}  tau_b={stats_row['tau_b']:.4f}  "
            f"n={int(stats_row['n'])}",
            flush=True,
        )

    index = pd.DataFrame(index_rows)
    index.to_excel(OUT_DIR / "index.xlsx", index=False, sheet_name="index")

    notes = [
        "# Kendall tau-b experiments v001",
        "",
        "## Research question",
        "",
        "For each unordered pair among the eight majors, what is the Kendall "
        "tau-b of matched daily log returns of close on the Alpari D1 history "
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
        "- Statistic: Kendall tau-b via `scipy.stats.kendalltau` "
        "(variant=\"b\"), two-sided p, approximate 95% Bonett-Wright "
        "interval on tau-b, same-sample Pearson r and tau-b minus r as a "
        "side check",
        "- Outputs: 28 Word reports, 28 full-data HTML tables, 28 Excel "
        "workbooks, charts under `outputs/figures/` (closes, returns, "
        "log-return scatter)",
        "",
        "## Index",
        "",
        "| pair | n | tau_b | p | ci_low | ci_high | pearson_r | tau_minus_r |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in index_rows:
        notes.append(
            f"| {row['pair']} | {row['n']} | {float(row['tau_b']):.6f} | "
            f"{float(row['p']):.6g} | {float(row['ci_low']):.6f} | "
            f"{float(row['ci_high']):.6f} | {float(row['pearson_r']):.6f} | "
            f"{float(row['tau_minus_r']):.6f} |"
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
