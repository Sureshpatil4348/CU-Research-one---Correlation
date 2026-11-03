"""Spearman rank correlation on Alpari D1 majors: one Word report and CSV per unique pair."""

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
    "Spearman rho is Pearson correlation on the ranks of matched daily log "
    "returns of close, ln(close_t / close_t-1), in the broker quote direction. "
    "Ties use average ranks. Quotes are not inverted. rho is symmetric under "
    "swap of the two symbols. rho = 0 means no consistent rank-order link in "
    "this sample; it does not mean no link of any kind. The score is not a "
    "cause, not a lead, and not a trading signal. Daily rows are not "
    "independent draws, so the two-sided p-value and approximate Fisher "
    "interval are reported and treated as secondary to rho. Same-sample "
    "Pearson r is shown only as a side check; a large rho minus r gap can "
    "flag outliers or a non-straight link."
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


def _fisher_interval(rho: float, n: int, confidence: float = 0.95) -> tuple[float, float]:
    """Approximate Fisher interval for a correlation coefficient."""
    if n <= 3:
        return float("nan"), float("nan")
    z = np.arctanh(np.clip(rho, -0.999999, 0.999999))
    se = 1.0 / np.sqrt(n - 3)
    z_crit = float(stats.norm.ppf(0.5 + confidence / 2.0))
    low = float(np.tanh(z - z_crit * se))
    high = float(np.tanh(z + z_crit * se))
    return low, high


def _spearman_stats(x: np.ndarray, y: np.ndarray) -> dict[str, float]:
    result = stats.spearmanr(x, y)
    rho = float(result.statistic)
    p = float(result.pvalue)
    n = int(len(x))
    ci_low, ci_high = _fisher_interval(rho, n)
    pearson_r = float(stats.pearsonr(x, y).statistic)
    return {
        "rho": rho,
        "p": p,
        "ci_low": ci_low,
        "ci_high": ci_high,
        "n": n,
        "pearson_r": pearson_r,
        "rho_minus_r": rho - pearson_r,
    }


def _strength_label(value: float) -> str:
    strength = "weak"
    if abs(value) >= 0.7:
        strength = "strong"
    elif abs(value) >= 0.4:
        strength = "moderate"
    return strength


def _conclusion(left: str, right: str, stats_row: dict[str, float]) -> str:
    rho = stats_row["rho"]
    n = stats_row["n"]
    strength = _strength_label(rho)
    direction = "positive" if rho >= 0 else "negative"
    return (
        f"Over {n} matched daily log-return rows for {left} and {right} "
        f"(broker quote directions unchanged), Spearman rho is {rho:.4f} "
        f"({direction}, {strength} rank-order association in this sample). "
        f"Approximate 95% Fisher interval: [{stats_row['ci_low']:.4f}, "
        f"{stats_row['ci_high']:.4f}]. Same-sample Pearson r is "
        f"{stats_row['pearson_r']:.4f} (rho minus r = "
        f"{stats_row['rho_minus_r']:.4f}). Two-sided p under the usual "
        f"independent-ranks model is {stats_row['p']:.4g}; that model does "
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
    rank_x = stats.rankdata(x)
    rank_y = stats.rankdata(y)

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

    fig, ax = plt.subplots(figsize=(5.5, 5.2))
    ax.scatter(rank_x, rank_y, s=6, alpha=0.35, color="#9467bd")
    ax.set_xlabel(f"{left} return rank")
    ax.set_ylabel(f"{right} return rank")
    ax.set_title(f"Rank-rank scatter: {left} vs {right}")
    fig.tight_layout()
    paths["ranks"] = FIG_DIR / f"{stem}_ranks.png"
    fig.savefig(paths["ranks"], dpi=120)
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
    csv_name: str,
    out_path: Path,
) -> None:
    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(10)

    _add_heading(doc, f"Spearman rank correlation: {left} and {right}", 0)
    _add_para(doc, "Method 02 / daily log returns / Alpari D1 full available history")

    _add_heading(doc, "Study setup", 1)
    first = pd.to_datetime(table["time"].iloc[0], utc=True).date().isoformat()
    last = pd.to_datetime(table["time"].iloc[-1], utc=True).date().isoformat()
    setup_lines = [
        f"Logical pair: {left} , {right}",
        f"Broker symbols: {left_broker} , {right_broker}",
        f"Snapshot: {snapshot_name}",
        "Timeframe: D1",
        f"Matched return window: {first} to {last} (UTC bar dates)",
        f"Matched return count n: {stats_row['n']}",
        drop_note,
        f"Complete matched rows (CSV): {csv_name}",
        f"Complete matched rows (HTML table): {csv_name.replace('.csv', '_data.html')}",
    ]
    for line in setup_lines:
        _add_para(doc, line)

    _add_heading(doc, "Method carried forward", 1)
    _add_para(doc, METHOD_NOTE)

    _add_heading(doc, "Results", 1)
    _add_para(doc, f"Spearman rho: {stats_row['rho']:.6f}")
    _add_para(doc, f"Two-sided p-value: {stats_row['p']:.6g}")
    _add_para(
        doc,
        f"Approximate 95% Fisher interval: "
        f"[{stats_row['ci_low']:.6f}, {stats_row['ci_high']:.6f}]",
    )
    _add_para(doc, f"Same-sample Pearson r: {stats_row['pearson_r']:.6f}")
    _add_para(doc, f"rho minus r: {stats_row['rho_minus_r']:.6f}")

    _add_heading(doc, "Conclusion", 1)
    _add_para(doc, _conclusion(left, right, stats_row))

    _add_heading(doc, "Charts", 1)
    for key, title in (
        ("closes", "Daily closes"),
        ("returns", "Daily log returns"),
        ("scatter", "Log-return scatter"),
        ("ranks", "Rank-rank scatter"),
    ):
        _add_para(doc, title, bold=True)
        doc.add_picture(str(fig_paths[key]), width=Inches(6.2))
        last_p = doc.paragraphs[-1]
        last_p.alignment = WD_ALIGN_PARAGRAPH.CENTER

    _add_heading(doc, "Data report", 1)
    _add_para(
        doc,
        "Every matched row that entered Spearman rho is stored in the sibling "
        f"CSV named {csv_name}. That file is the complete data archive for "
        "redrawing charts. Embedding all rows as a Word table is impractical "
        "at this length; the Word file holds the column list, column "
        "summaries, and the first and last 15 matched rows.",
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
    by_rho = sorted(index_rows, key=lambda row: float(row["rho"]))
    by_abs_gap = sorted(
        index_rows,
        key=lambda row: abs(float(row["rho_minus_r"])),
        reverse=True,
    )
    strongest_pos = by_rho[-1]
    strongest_neg = by_rho[0]
    near_zero = sorted(index_rows, key=lambda row: abs(float(row["rho"])))[:3]
    top_gaps = by_abs_gap[:3]

    lines = [
        "## Cross-pair conclusion",
        "",
        "Reading of the 28-pair index only. Not a 29th pair analysis and not a "
        "trading signal.",
        "",
        (
            f"Strongest positive rank link: {strongest_pos['pair']} "
            f"(rho={float(strongest_pos['rho']):.4f}, "
            f"n={strongest_pos['n']})."
        ),
        (
            f"Strongest negative rank link: {strongest_neg['pair']} "
            f"(rho={float(strongest_neg['rho']):.4f}, "
            f"n={strongest_neg['n']})."
        ),
        "Nearest-to-zero rank links: "
        + "; ".join(
            f"{row['pair']} (rho={float(row['rho']):.4f})" for row in near_zero
        )
        + ".",
        "Largest |rho minus Pearson r| gaps on the same sample: "
        + "; ".join(
            f"{row['pair']} (gap={float(row['rho_minus_r']):.4f}, "
            f"rho={float(row['rho']):.4f}, r={float(row['pearson_r']):.4f})"
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
        stats_row = _spearman_stats(x, y)
        stem = f"{left}-{right}_Spearman_D1"
        fig_paths = _save_figures(table, left, right, stem)

        csv_path = OUT_DIR / f"{stem}.csv"
        table.to_csv(csv_path, index=False)

        html_path = OUT_DIR / f"{stem}_data.html"
        html_frame = table.copy()
        html_frame["time"] = pd.to_datetime(html_frame["time"], utc=True).dt.strftime(
            "%Y-%m-%d"
        )
        html_path.write_text(
            (
                f"<!DOCTYPE html><html><head><meta charset='utf-8'>"
                f"<title>{stem} data</title></head><body>"
                f"<h1>{left} and {right}: matched rows used for Spearman rho</h1>"
                f"<p>n={stats_row['n']}. Complete archive also in {csv_path.name}.</p>"
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
            csv_name=csv_path.name,
            out_path=docx_path,
        )

        index_rows.append(
            {
                "pair": f"{left}-{right}",
                "n": stats_row["n"],
                "rho": stats_row["rho"],
                "p": stats_row["p"],
                "ci_low": stats_row["ci_low"],
                "ci_high": stats_row["ci_high"],
                "pearson_r": stats_row["pearson_r"],
                "rho_minus_r": stats_row["rho_minus_r"],
                "docx": docx_path.name,
                "csv": csv_path.name,
                "html": html_path.name,
            }
        )
        print(
            f"Wrote {docx_path.name}  rho={stats_row['rho']:.4f}  "
            f"n={stats_row['n']}",
            flush=True,
        )

    index = pd.DataFrame(index_rows)
    index.to_csv(OUT_DIR / "index.csv", index=False)

    notes = [
        "# Spearman experiments v001",
        "",
        "## Research question",
        "",
        "For each unordered pair among the eight majors, what is the Spearman "
        "rank correlation of matched daily log returns of close on the Alpari "
        "D1 history that the broker actually provided?",
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
        "- Statistic: Spearman rho via `scipy.stats.spearmanr`, two-sided p, "
        "approximate 95% Fisher interval on rho, same-sample Pearson r and "
        "rho minus r as a side check",
        "- Outputs: 28 Word reports, 28 full-data HTML tables, 28 CSVs, "
        "charts under `outputs/figures/` (closes, returns, log-return "
        "scatter, rank-rank scatter)",
        "",
        "## Index",
        "",
        "| pair | n | rho | p | ci_low | ci_high | pearson_r | rho_minus_r |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in index_rows:
        notes.append(
            f"| {row['pair']} | {row['n']} | {float(row['rho']):.6f} | "
            f"{float(row['p']):.6g} | {float(row['ci_low']):.6f} | "
            f"{float(row['ci_high']):.6f} | {float(row['pearson_r']):.6f} | "
            f"{float(row['rho_minus_r']):.6f} |"
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
