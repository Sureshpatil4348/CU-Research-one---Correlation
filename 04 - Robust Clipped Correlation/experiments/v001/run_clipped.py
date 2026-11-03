"""Robust clipped correlation on Alpari D1 majors: one Word report, HTML, Excel per pair."""

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
from matplotlib.patches import Rectangle
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
CLIP_LEVELS = (0.01, 0.02, 0.03)
HEADLINE_C = 0.02
METHOD_NOTE = (
    "Each matched daily log return of close, ln(close_t / close_t-1), is "
    "clipped in the broker quote direction before Pearson correlation: "
    "x_tilde = min(c, max(-c, x)) and y_tilde = min(c, max(-c, y)), then "
    "rho_clip = Pearson(x_tilde, y_tilde) on the same rows as raw Pearson r. "
    "Quotes are not inverted. A day beyond ±c stays in the sample at the "
    "cap; n does not change. rho_clip is symmetric under swap of the two "
    "symbols. rho_clip = 0 means no straight-line link among the clipped "
    "values in this sample; it does not mean no link of any kind. The score "
    "is not a cause, not a lead, and not a trading signal. Daily rows are "
    "not independent draws, so the two-sided p-value and Fisher interval "
    "are reported and treated as secondary to rho_clip. Cap-hit counts "
    "(|log return| > c) flag how much of each leg was capped."
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


def _clip_series(values: np.ndarray, c: float) -> np.ndarray:
    return np.clip(values, -c, c)


def _c_label(c: float) -> str:
    return f"{c:.2f}".replace(".", "p")


def _pearson_block(x: np.ndarray, y: np.ndarray) -> dict[str, float]:
    """Pearson r with Fisher interval; NaN when a series is constant."""
    n = int(len(x))
    if n < 3 or float(np.std(x)) == 0.0 or float(np.std(y)) == 0.0:
        return {
            "r": float("nan"),
            "p": float("nan"),
            "ci_low": float("nan"),
            "ci_high": float("nan"),
            "n": n,
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
        "n": n,
    }


def _cap_hits(values: np.ndarray, c: float) -> tuple[int, float]:
    hits = int(np.sum(np.abs(values) > c))
    share = hits / len(values) if len(values) else float("nan")
    return hits, float(share)


def _clipped_stats(x: np.ndarray, y: np.ndarray) -> dict[str, object]:
    raw = _pearson_block(x, y)
    by_c: dict[float, dict[str, float]] = {}
    for c in CLIP_LEVELS:
        xt = _clip_series(x, c)
        yt = _clip_series(y, c)
        block = _pearson_block(xt, yt)
        left_hits, left_share = _cap_hits(x, c)
        right_hits, right_share = _cap_hits(y, c)
        rho = block["r"]
        raw_r = raw["r"]
        gap = (
            float("nan")
            if math.isnan(rho) or math.isnan(raw_r)
            else rho - raw_r
        )
        by_c[c] = {
            "c": c,
            "rho_clip": rho,
            "p": block["p"],
            "ci_low": block["ci_low"],
            "ci_high": block["ci_high"],
            "rho_minus_r": gap,
            "left_cap_hits": float(left_hits),
            "right_cap_hits": float(right_hits),
            "left_cap_share": left_share,
            "right_cap_share": right_share,
        }
    return {"raw": raw, "by_c": by_c, "n": raw["n"]}


def _add_clipped_columns(
    table: pd.DataFrame,
    left: str,
    right: str,
) -> pd.DataFrame:
    out = table.copy()
    x = out[f"{left}_log_return"].to_numpy(dtype=float)
    y = out[f"{right}_log_return"].to_numpy(dtype=float)
    for c in CLIP_LEVELS:
        label = _c_label(c)
        out[f"{left}_log_return_clip_{label}"] = _clip_series(x, c)
        out[f"{right}_log_return_clip_{label}"] = _clip_series(y, c)
    return out


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
        return "undefined"
    return f"{value:.{digits}f}"


def _conclusion(
    left: str,
    right: str,
    stats_pack: dict[str, object],
) -> str:
    raw = stats_pack["raw"]  # type: ignore[assignment]
    by_c = stats_pack["by_c"]  # type: ignore[assignment]
    n = int(stats_pack["n"])  # type: ignore[arg-type]
    head = by_c[HEADLINE_C]
    rho = float(head["rho_clip"])
    raw_r = float(raw["r"])
    strength = _strength_label(rho)
    if math.isnan(rho):
        direction = "undefined"
    else:
        direction = "positive" if rho >= 0 else "negative"
    sign_bits = []
    for c in CLIP_LEVELS:
        other = float(by_c[c]["rho_clip"])
        if math.isnan(rho) or math.isnan(other):
            sign_bits.append(f"c={c:.2f} undefined")
        elif (rho >= 0) == (other >= 0):
            sign_bits.append(f"c={c:.2f} same sign")
        else:
            sign_bits.append(f"c={c:.2f} opposite sign")
    left_hits = int(head["left_cap_hits"])
    right_hits = int(head["right_cap_hits"])
    left_share = float(head["left_cap_share"])
    right_share = float(head["right_cap_share"])
    gap = float(head["rho_minus_r"])
    gap_note = ""
    if not math.isnan(gap) and abs(gap) >= 0.05:
        gap_note = (
            f" The |rho_clip minus r| gap of {gap:.4f} is large enough to "
            f"warrant reading the cap hits ({left}={left_hits}, "
            f"{right}={right_hits} at c=0.02) before treating either score "
            "as settled."
        )
    elif left_share >= 0.05 or right_share >= 0.05:
        gap_note = (
            f" Cap-hit shares at c=0.02 are {left}={left_share:.2%} and "
            f"{right}={right_share:.2%}; inspect those days on the charts "
            "before treating rho_clip as settled."
        )
    head_p = float(head["p"])
    head_p_text = "undefined" if math.isnan(head_p) else f"{head_p:.4g}"
    return (
        f"Over {n} matched daily log-return rows for {left} and {right} "
        f"(broker quote directions unchanged), headline robust clipped "
        f"correlation at c=0.02 is {_fmt(rho)} ({direction}, {strength} "
        f"straight-line association among clipped values in this sample). "
        f"Approximate 95% Fisher interval on the clipped series: "
        f"[{_fmt(float(head['ci_low']))}, {_fmt(float(head['ci_high']))}]. "
        f"Same-sample raw Pearson r is {_fmt(raw_r)} "
        f"(rho_clip minus r = {_fmt(gap)}). Sensitivity across the fixed "
        f"grid: {'; '.join(sign_bits)}. Two-sided p under the usual "
        f"independent bivariate-normal model is {head_p_text}; "
        f"that model does not match linked daily FX returns, so treat p as "
        f"secondary.{gap_note} This does not establish cause, lead-lag, or "
        f"a lasting trading rule."
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
    c = HEADLINE_C

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
    ax.plot(times, x, color="#1f77b4", linewidth=0.6, label=left)
    ax.plot(times, y, color="#ff7f0e", linewidth=0.6, label=right)
    ax.axhline(c, color="#555555", linewidth=0.8, linestyle="--", label=f"+/- {c}")
    ax.axhline(-c, color="#555555", linewidth=0.8, linestyle="--")
    ax.set_title(f"Daily log returns with +/- {c} clip lines: {left} and {right}")
    ax.set_ylabel("log return")
    ax.legend(loc="upper left")
    fig.tight_layout()
    paths["returns"] = FIG_DIR / f"{stem}_returns.png"
    fig.savefig(paths["returns"], dpi=120)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(5.5, 5.2))
    ax.scatter(x, y, s=6, alpha=0.35, color="#2ca02c")
    ax.add_patch(
        Rectangle(
            (-c, -c),
            2 * c,
            2 * c,
            fill=False,
            edgecolor="#d62728",
            linewidth=1.2,
            linestyle="--",
            label=f"+/- {c} clip box",
        )
    )
    ax.set_xlabel(f"{left} log return")
    ax.set_ylabel(f"{right} log return")
    ax.set_title(f"Log-return scatter with +/- {c} clip box")
    ax.axhline(0, color="gray", linewidth=0.5)
    ax.axvline(0, color="gray", linewidth=0.5)
    ax.legend(loc="upper left")
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
                if math.isnan(value):
                    cells[c_i].text = "nan"
                else:
                    cells[c_i].text = f"{value:.8g}"
            else:
                cells[c_i].text = str(value)


def _write_word(
    table: pd.DataFrame,
    left: str,
    right: str,
    left_broker: str,
    right_broker: str,
    stats_pack: dict[str, object],
    drop_note: str,
    snapshot_name: str,
    fig_paths: dict[str, Path],
    xlsx_name: str,
    out_path: Path,
) -> None:
    raw = stats_pack["raw"]  # type: ignore[assignment]
    by_c = stats_pack["by_c"]  # type: ignore[assignment]
    n = int(stats_pack["n"])  # type: ignore[arg-type]

    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(10)

    _add_heading(doc, f"Robust clipped correlation: {left} and {right}", 0)
    _add_para(
        doc,
        "Method 04 / daily log returns clipped at ±0.01, ±0.02, ±0.03 / "
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
        f"Matched return count n: {n}",
        drop_note,
        (
            "Clip bounds c in log-return units: 0.01, 0.02, 0.03 "
            "(about ±1%, ±2%, ±3% on the log scale). Headline c = 0.02."
        ),
        (
            "Clipping caps a day's magnitude at ±c and keeps the row; "
            "it does not drop the day, so n is the same at every c."
        ),
        f"Complete matched rows (Excel): {xlsx_name}",
        f"Complete matched rows (HTML table): {xlsx_name.replace('.xlsx', '_data.html')}",
    ]
    for line in setup_lines:
        _add_para(doc, line)

    _add_heading(doc, "Method carried forward", 1)
    _add_para(doc, METHOD_NOTE)

    _add_heading(doc, "Raw Pearson on the same rows", 1)
    raw_p = float(raw["p"])
    raw_p_text = "undefined" if math.isnan(raw_p) else f"{raw_p:.6g}"
    _add_para(doc, f"Pearson r: {_fmt(float(raw['r']), 6)}")
    _add_para(doc, f"Two-sided p-value: {raw_p_text}")
    _add_para(
        doc,
        "Approximate 95% Fisher interval: "
        f"[{_fmt(float(raw['ci_low']), 6)}, {_fmt(float(raw['ci_high']), 6)}]",
    )
    _add_para(
        doc,
        "This is the unclipped comparison required by the method. "
        "The headline score is rho_clip at c = 0.02 below.",
    )

    _add_heading(doc, "Clipped results", 1)
    _add_para(
        doc,
        f"n = {n} at every c. Headline row is c = 0.02. Cap-hit count is "
        "the number of days with |log return| > c before clipping.",
    )
    result_rows = []
    for c in CLIP_LEVELS:
        row = by_c[c]
        result_rows.append(
            {
                "c": c,
                "rho_clip": round(float(row["rho_clip"]), 6)
                if not math.isnan(float(row["rho_clip"]))
                else float("nan"),
                "p": float(row["p"]),
                "ci_low": float(row["ci_low"]),
                "ci_high": float(row["ci_high"]),
                "rho_minus_r": float(row["rho_minus_r"]),
                f"{left}_cap_hits": int(row["left_cap_hits"]),
                f"{right}_cap_hits": int(row["right_cap_hits"]),
                f"{left}_cap_share": round(float(row["left_cap_share"]), 6),
                f"{right}_cap_share": round(float(row["right_cap_share"]), 6),
            }
        )
    _add_small_table(doc, pd.DataFrame(result_rows))

    _add_heading(doc, "Conclusion", 1)
    _add_para(doc, _conclusion(left, right, stats_pack))

    _add_heading(doc, "What to look at in this file next time", 1)
    _add_para(
        doc,
        "1) rho_clip at c = 0.02 versus raw Pearson r. "
        "2) Whether c = 0.01 and c = 0.03 keep the same sign as 0.02. "
        "3) Cap-hit counts before treating a large gap as settled. "
        "4) The ±0.02 lines on the returns chart and the clip box on the scatter.",
    )

    _add_heading(doc, "Charts", 1)
    for key, title in (
        ("closes", "Daily closes"),
        ("returns", "Daily log returns with +/- 0.02 clip lines"),
        ("scatter", "Log-return scatter with +/- 0.02 clip box"),
    ):
        _add_para(doc, title, bold=True)
        doc.add_picture(str(fig_paths[key]), width=Inches(6.2))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

    _add_heading(doc, "Data report", 1)
    _add_para(
        doc,
        "Every matched row that entered the clipped and raw correlations is "
        f"stored in the sibling Excel workbook named {xlsx_name}. That file "
        "is the complete data archive for redrawing charts. Embedding all "
        "rows as a Word table is impractical at this length; the Word file "
        "holds the column list, column summaries, and the first and last "
        "15 matched rows.",
    )
    _add_para(doc, "Columns: " + ", ".join(table.columns))

    numeric_cols = [c for c in table.columns if c != "time"]
    summary = (
        table[numeric_cols].describe().T.reset_index().rename(columns={"index": "column"})
    )
    _add_para(doc, "Column summaries (matched calculation rows)", bold=True)
    _add_small_table(doc, summary.round(8))

    clip_label = _c_label(HEADLINE_C)
    preview_cols = [
        "time",
        f"{left}_close",
        f"{right}_close",
        f"{left}_log_return",
        f"{right}_log_return",
        f"{left}_log_return_clip_{clip_label}",
        f"{right}_log_return_clip_{clip_label}",
    ]
    _add_para(doc, "First 15 matched rows (selected columns)", bold=True)
    _add_small_table(doc, table.loc[:, preview_cols].head(15))
    _add_para(doc, "Last 15 matched rows (selected columns)", bold=True)
    _add_small_table(doc, table.loc[:, preview_cols].tail(15))

    doc.save(out_path)


def _cross_pair_conclusion(index_rows: list[dict[str, object]]) -> list[str]:
    """Short reading of the 28-pair index for NOTES.md."""
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

    lines = [
        "## Cross-pair conclusion",
        "",
        "Reading of the 28-pair index only. Not a 29th pair analysis and not a "
        "trading signal.",
        "",
        (
            f"Strongest positive clipped link at c=0.02: {strongest_pos['pair']} "
            f"(rho_clip={float(strongest_pos['rho_02']):.4f}, "
            f"n={strongest_pos['n']})."
        ),
        (
            f"Strongest negative clipped link at c=0.02: {strongest_neg['pair']} "
            f"(rho_clip={float(strongest_neg['rho_02']):.4f}, "
            f"n={strongest_neg['n']})."
        ),
        "Nearest-to-zero clipped links at c=0.02: "
        + "; ".join(
            f"{row['pair']} (rho_clip={float(row['rho_02']):.4f})" for row in near_zero
        )
        + ".",
        "Largest |rho_clip minus Pearson r| gaps at c=0.02 on the same sample: "
        + "; ".join(
            f"{row['pair']} (gap={float(row['rho_02_minus_r']):.4f}, "
            f"rho_clip={float(row['rho_02']):.4f}, r={float(row['r']):.4f})"
            for row in top_gaps
        )
        + ". A large gap can flag outlier or crisis days that clipping "
        "caps; inspect that pair's cap hits and charts before treating "
        "either score as settled.",
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
        stats_pack = _clipped_stats(x, y)
        table = _add_clipped_columns(table, left, right)
        stem = f"{left}-{right}_Clipped_D1"
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
                f"<h1>{left} and {right}: matched rows used for robust "
                f"clipped correlation</h1>"
                f"<p>n={int(stats_pack['n'])}. Complete archive also in "
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
            stats_pack=stats_pack,
            drop_note=drop_note,
            snapshot_name=snapshot_name,
            fig_paths=fig_paths,
            xlsx_name=xlsx_path.name,
            out_path=docx_path,
        )

        raw = stats_pack["raw"]  # type: ignore[assignment]
        by_c = stats_pack["by_c"]  # type: ignore[assignment]
        head = by_c[HEADLINE_C]
        index_rows.append(
            {
                "pair": f"{left}-{right}",
                "n": int(stats_pack["n"]),
                "r": float(raw["r"]),
                "rho_01": float(by_c[0.01]["rho_clip"]),
                "rho_02": float(by_c[0.02]["rho_clip"]),
                "rho_03": float(by_c[0.03]["rho_clip"]),
                "rho_02_minus_r": float(head["rho_minus_r"]),
                "left_cap_hits_02": int(head["left_cap_hits"]),
                "right_cap_hits_02": int(head["right_cap_hits"]),
                "docx": docx_path.name,
                "xlsx": xlsx_path.name,
                "html": html_path.name,
            }
        )
        print(
            f"Wrote {docx_path.name}  rho_02={float(head['rho_clip']):.4f}  "
            f"r={float(raw['r']):.4f}  n={int(stats_pack['n'])}",
            flush=True,
        )

    index = pd.DataFrame(index_rows)
    index.to_excel(OUT_DIR / "index.xlsx", index=False, sheet_name="index")

    notes = [
        "# Robust clipped correlation experiments v001",
        "",
        "## Research question",
        "",
        "For each unordered pair among the eight majors, what is the robust "
        "clipped correlation of matched daily log returns of close on the "
        "Alpari D1 history that the broker actually provided, after capping "
        "each return at ±0.01, ±0.02, and ±0.03?",
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
        "- Statistic: clip each leg at c in {0.01, 0.02, 0.03}, then Pearson "
        "rho_clip via `scipy.stats.pearsonr` on the clipped series; same-row "
        "raw Pearson r for comparison; two-sided p and approximate 95% Fisher "
        "interval on clipped values; cap-hit counts (|log return| > c) per leg",
        "- Headline: rho_clip at c = 0.02",
        "- Outputs: 28 Word reports, 28 full-data HTML tables, 28 Excel "
        "workbooks, charts under `outputs/figures/` (closes, returns with "
        "±0.02 lines, scatter with ±0.02 clip box)",
        "",
        "## Index",
        "",
        "| pair | n | r | rho_01 | rho_02 | rho_03 | left_cap_hits_02 | "
        "right_cap_hits_02 | rho_02_minus_r |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in index_rows:
        notes.append(
            f"| {row['pair']} | {row['n']} | {float(row['r']):.6f} | "
            f"{float(row['rho_01']):.6f} | {float(row['rho_02']):.6f} | "
            f"{float(row['rho_03']):.6f} | {row['left_cap_hits_02']} | "
            f"{row['right_cap_hits_02']} | {float(row['rho_02_minus_r']):.6f} |"
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
