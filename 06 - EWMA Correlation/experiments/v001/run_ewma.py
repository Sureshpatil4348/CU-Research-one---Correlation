"""EWMA correlation on Alpari D1 majors: one Word report, HTML table, and Excel per unique pair."""

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
LAMBDA = 0.94
BURN_IN = 60
METHOD_NOTE = (
    "EWMA correlation updates covariance and variances of mean-adjusted "
    "daily log returns of close, ln(close_t / close_t-1), with lambda = 0.94 "
    "(6% weight on today's product or square, 94% on yesterday's EWMA state). "
    "Quotes are not inverted. Each leg is demeaned by its mean on the matched "
    "rows; that mean uses the full sample, so the rho path is a full-sample "
    "description, not a live filter. Seeds start at zero. Path summaries and "
    "the chart ignore the first 60 updates so the zero seed has faded. The "
    "headline is rho on the last day. rho is symmetric under swap of the two "
    "symbols. A high |rho| does not prove cause, lead-lag, or a trading "
    "signal. Today's return sits inside today's rho, so the estimate can only "
    "inform a later decision. Same-sample Pearson r is a side check only."
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


def _ewma_path(x: np.ndarray, y: np.ndarray, lam: float = LAMBDA) -> dict[str, np.ndarray]:
    """RiskMetrics-style EWMA recursion from zero seeds."""
    n = len(x)
    c = np.empty(n, dtype=float)
    vx = np.empty(n, dtype=float)
    vy = np.empty(n, dtype=float)
    rho = np.empty(n, dtype=float)
    c_prev = vx_prev = vy_prev = 0.0
    one_minus = 1.0 - lam
    for i in range(n):
        xi = float(x[i])
        yi = float(y[i])
        c_prev = lam * c_prev + one_minus * xi * yi
        vx_prev = lam * vx_prev + one_minus * xi * xi
        vy_prev = lam * vy_prev + one_minus * yi * yi
        c[i] = c_prev
        vx[i] = vx_prev
        vy[i] = vy_prev
        if vx_prev > 0.0 and vy_prev > 0.0:
            rho[i] = c_prev / math.sqrt(vx_prev * vy_prev)
        else:
            rho[i] = float("nan")
    return {"c": c, "vx": vx, "vy": vy, "rho": rho}


def _add_ewma_columns(table: pd.DataFrame, left: str, right: str) -> pd.DataFrame:
    out = table.copy()
    x_raw = out[f"{left}_log_return"].to_numpy(dtype=float)
    y_raw = out[f"{right}_log_return"].to_numpy(dtype=float)
    x = x_raw - float(np.mean(x_raw))
    y = y_raw - float(np.mean(y_raw))
    path = _ewma_path(x, y)
    out[f"{left}_x_demeaned"] = x
    out[f"{right}_y_demeaned"] = y
    out["c_t"] = path["c"]
    out["v_x"] = path["vx"]
    out["v_y"] = path["vy"]
    out["rho_t"] = path["rho"]
    return out


def _path_stats(rho: np.ndarray, burn_in: int = BURN_IN) -> dict[str, float]:
    if len(rho) == 0:
        return {
            "latest_rho": float("nan"),
            "mean": float("nan"),
            "median": float("nan"),
            "min": float("nan"),
            "max": float("nan"),
            "std": float("nan"),
            "pct_abs_ge_0_4": float("nan"),
            "pct_abs_ge_0_7": float("nan"),
            "n_post_burn": 0,
        }
    latest = float(rho[-1])
    post = rho[burn_in:] if len(rho) > burn_in else rho
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
            "n_post_burn": 0,
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
        "n_post_burn": n_post,
    }


def _ewma_stats(table: pd.DataFrame, left: str, right: str) -> dict[str, float]:
    x = table[f"{left}_log_return"].to_numpy(dtype=float)
    y = table[f"{right}_log_return"].to_numpy(dtype=float)
    n = int(len(x))
    pearson_r = float(stats.pearsonr(x, y).statistic)
    path = _path_stats(table["rho_t"].to_numpy(dtype=float))
    latest = path["latest_rho"]
    return {
        "n": float(n),
        "latest_rho": latest,
        "mean": path["mean"],
        "median": path["median"],
        "min": path["min"],
        "max": path["max"],
        "std": path["std"],
        "pct_abs_ge_0_4": path["pct_abs_ge_0_4"],
        "pct_abs_ge_0_7": path["pct_abs_ge_0_7"],
        "n_post_burn": float(path["n_post_burn"]),
        "pearson_r": pearson_r,
        "latest_minus_r": latest - pearson_r,
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
        f"(broker quote directions unchanged), latest EWMA rho with lambda="
        f"{LAMBDA} is {_fmt(latest, 4)} ({direction}, {strength} recent "
        f"linear link in this sample). After a {BURN_IN}-day burn-in, path "
        f"mean is {_fmt(stats_row['mean'], 4)}, std is "
        f"{_fmt(stats_row['std'], 4)}, and the range is "
        f"[{_fmt(stats_row['min'], 4)}, {_fmt(stats_row['max'], 4)}]. "
        f"Same-sample Pearson r is {_fmt(stats_row['pearson_r'], 4)} "
        f"(latest rho minus r = {_fmt(stats_row['latest_minus_r'], 4)}). "
        f"This does not establish cause, lead-lag, or a lasting trading rule."
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
    ax.plot(times, rho, color="#2ca02c", linewidth=0.8, label="EWMA rho")
    ax.axhline(pearson_r, color="#d62728", linewidth=1.0, linestyle="--", label=f"Pearson r={pearson_r:.3f}")
    ax.axhline(0, color="gray", linewidth=0.5)
    ax.set_ylim(-1.05, 1.05)
    ax.set_title(f"EWMA rho path (burn-in {BURN_IN} days blanked): {left} and {right}")
    ax.set_ylabel("rho_t")
    ax.legend(loc="upper left")
    fig.tight_layout()
    paths["ewma"] = FIG_DIR / f"{stem}_ewma.png"
    fig.savefig(paths["ewma"], dpi=120)
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

    _add_heading(doc, f"EWMA correlation: {left} and {right}", 0)
    _add_para(
        doc,
        "Method 06 / daily log returns / lambda = 0.94 / Alpari D1 full available history",
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
        f"Lambda: {LAMBDA} (today weight {1.0 - LAMBDA:.2f})",
        f"Burn-in ignored in path summaries and chart: first {BURN_IN} updates",
        "Mean adjustment: each leg demeaned by its mean on the matched rows",
        "Seeds: c_0 = v_x,0 = v_y,0 = 0",
        f"Complete matched rows (Excel): {xlsx_name}",
        f"Complete matched rows (HTML table): {xlsx_name.replace('.xlsx', '_data.html')}",
    ]
    for line in setup_lines:
        _add_para(doc, line)

    _add_heading(doc, "Method carried forward", 1)
    _add_para(doc, METHOD_NOTE)

    _add_heading(doc, "Results", 1)
    _add_para(doc, f"Latest EWMA rho: {_fmt(stats_row['latest_rho'], 6)}")
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
        ("ewma", "EWMA rho path with Pearson r reference"),
    ):
        _add_para(doc, title, bold=True)
        doc.add_picture(str(fig_paths[key]), width=Inches(6.2))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

    _add_heading(doc, "Data report", 1)
    _add_para(
        doc,
        "Every matched row that entered the EWMA recursion is stored in the "
        f"sibling Excel workbook named {xlsx_name}. That file is the complete "
        "data archive for redrawing charts. Embedding all rows as a Word table "
        "is impractical at this length; the Word file holds the column list, "
        "column summaries, and the first and last 15 matched rows.",
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
        f"{left}_x_demeaned",
        f"{right}_y_demeaned",
        "c_t",
        "v_x",
        "v_y",
        "rho_t",
    ]
    _add_para(doc, "First 15 matched rows (selected columns)", bold=True)
    _add_small_table(doc, table.loc[:, preview_cols].head(15))
    _add_para(doc, "Last 15 matched rows (selected columns)", bold=True)
    _add_small_table(doc, table.loc[:, preview_cols].tail(15))

    doc.save(out_path)


def _cross_pair_conclusion(index_rows: list[dict[str, object]]) -> list[str]:
    by_rho = sorted(index_rows, key=lambda row: float(row["latest_rho"]))
    by_abs_gap = sorted(
        index_rows,
        key=lambda row: abs(float(row["latest_minus_r"])),
        reverse=True,
    )
    strongest_pos = by_rho[-1]
    strongest_neg = by_rho[0]
    near_zero = sorted(index_rows, key=lambda row: abs(float(row["latest_rho"])))[:3]
    top_gaps = by_abs_gap[:3]

    lines = [
        "## Cross-pair conclusion",
        "",
        "Reading of the 28-pair index only. Not a 29th pair analysis and not a "
        "trading signal.",
        "",
        (
            f"Strongest positive latest EWMA rho: {strongest_pos['pair']} "
            f"(latest_rho={float(strongest_pos['latest_rho']):.4f}, "
            f"n={strongest_pos['n']})."
        ),
        (
            f"Strongest negative latest EWMA rho: {strongest_neg['pair']} "
            f"(latest_rho={float(strongest_neg['latest_rho']):.4f}, "
            f"n={strongest_neg['n']})."
        ),
        "Nearest-to-zero latest EWMA rho: "
        + "; ".join(
            f"{row['pair']} (latest_rho={float(row['latest_rho']):.4f})"
            for row in near_zero
        )
        + ".",
        "Largest |latest rho minus Pearson r| gaps on the same sample: "
        + "; ".join(
            f"{row['pair']} (gap={float(row['latest_minus_r']):.4f}, "
            f"latest_rho={float(row['latest_rho']):.4f}, "
            f"r={float(row['pearson_r']):.4f})"
            for row in top_gaps
        )
        + ". A large gap can flag a recent regime shift versus the full-sample "
        "mean; inspect that pair's EWMA path before treating either score as "
        "settled.",
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
        table = _add_ewma_columns(table, left, right)
        stats_row = _ewma_stats(table, left, right)
        stem = f"{left}-{right}_EWMA_D1"
        fig_paths = _save_figures(
            table, left, right, stem, pearson_r=float(stats_row["pearson_r"])
        )

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
                f"<h1>{left} and {right}: matched rows used for EWMA correlation</h1>"
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
                "latest_rho": stats_row["latest_rho"],
                "mean": stats_row["mean"],
                "std": stats_row["std"],
                "min": stats_row["min"],
                "max": stats_row["max"],
                "pearson_r": stats_row["pearson_r"],
                "latest_minus_r": stats_row["latest_minus_r"],
                "docx": docx_path.name,
                "xlsx": xlsx_path.name,
                "html": html_path.name,
            }
        )
        print(
            f"Wrote {docx_path.name}  latest_rho={stats_row['latest_rho']:.4f}  "
            f"n={int(stats_row['n'])}",
            flush=True,
        )

    index = pd.DataFrame(index_rows)
    index.to_excel(OUT_DIR / "index.xlsx", index=False, sheet_name="index")

    notes = [
        "# EWMA correlation experiments v001",
        "",
        "## Research question",
        "",
        "For each unordered pair among the eight majors, what is the EWMA "
        "correlation path of matched daily log returns of close on the Alpari "
        "D1 history that the broker actually provided, with lambda = 0.94?",
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
        "- Mean adjustment: each leg demeaned by its mean on the matched rows "
        "(full-sample description)",
        f"- Statistic: RiskMetrics EWMA rho with lambda={LAMBDA}, zero seeds, "
        f"burn-in={BURN_IN} for path summaries; headline = latest rho; "
        "same-sample Pearson r and latest rho minus r as a side check",
        "- Outputs: 28 Word reports, 28 full-data HTML tables, 28 Excel "
        "workbooks, charts under `outputs/figures/` (closes, returns, EWMA "
        "path with Pearson r reference)",
        "",
        "## Index",
        "",
        "| pair | n | latest_rho | mean | std | min | max | pearson_r | latest_minus_r |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in index_rows:
        notes.append(
            f"| {row['pair']} | {row['n']} | {float(row['latest_rho']):.6f} | "
            f"{float(row['mean']):.6f} | {float(row['std']):.6f} | "
            f"{float(row['min']):.6f} | {float(row['max']):.6f} | "
            f"{float(row['pearson_r']):.6f} | {float(row['latest_minus_r']):.6f} |"
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
