"""Rolling Pearson correlation (W=20/60/100) on Alpari D1 for three pair tiers."""

from __future__ import annotations

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

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from shared.mt5_data import load_snapshot

SNAPSHOT_REL = Path("data/snapshots/2026-11-03_majors_alpari_D1")
EXP_DIR = Path(__file__).resolve().parent
OUT_DIR = EXP_DIR / "outputs"
FIG_DIR = OUT_DIR / "figures"
WINDOWS = (20, 60, 100)
OHLCV_KEEP = ["close", "tick_volume"]

# Full-sample Pearson r from method 01 v001 NOTES (copied values; no import).
FULL_SAMPLE_R: dict[str, float] = {
    "AUDUSD-NZDUSD": 0.828722,
    "EURUSD-USDCHF": -0.749204,
    "AUDUSD-USDCAD": -0.647362,
    "EURUSD-GBPUSD": 0.641738,
    "NZDUSD-USDCAD": -0.587831,
    "EURUSD-AUDUSD": 0.556324,
    "EURUSD-NZDUSD": 0.549808,
    "GBPUSD-AUDUSD": 0.539048,
    "GBPUSD-NZDUSD": 0.530079,
    "GBPUSD-USDCHF": -0.486083,
    "AUDUSD-EURGBP": 0.038173,
    "NZDUSD-EURGBP": 0.037186,
    "USDJPY-USDCAD": 0.027603,
    "USDCAD-EURGBP": -0.014622,
    "AUDUSD-USDJPY": -0.088151,
    "NZDUSD-USDJPY": -0.133568,
    "USDJPY-EURGBP": -0.127992,
}

TIERS: dict[str, list[tuple[str, str]]] = {
    "short_watchlist": [
        ("AUDUSD", "NZDUSD"),
        ("EURUSD", "USDCHF"),
        ("AUDUSD", "USDCAD"),
        ("EURUSD", "GBPUSD"),
        ("NZDUSD", "USDCAD"),
    ],
    "secondary": [
        ("EURUSD", "AUDUSD"),
        ("EURUSD", "NZDUSD"),
        ("GBPUSD", "AUDUSD"),
        ("GBPUSD", "NZDUSD"),
        ("GBPUSD", "USDCHF"),
    ],
    "low_value": [
        ("AUDUSD", "EURGBP"),
        ("NZDUSD", "EURGBP"),
        ("USDJPY", "USDCAD"),
        ("USDCAD", "EURGBP"),
        ("AUDUSD", "USDJPY"),
        ("NZDUSD", "USDJPY"),
        ("USDJPY", "EURGBP"),
    ],
}

TIER_LABEL = {
    "short_watchlist": "Short watchlist",
    "secondary": "Secondary tier",
    "low_value": "Low-value",
}

METHOD_NOTE = (
    "Rolling Pearson r is computed on matched daily log returns of close, "
    "ln(close_t / close_t-1), in the broker quote direction. Quotes are not "
    "inverted. For each day t with a full window, r_W uses the last W matched "
    "return pairs ending at t. That live-shaped sample size is W (20, 60, or "
    "100), not the full multi-year history. The first W-1 days have no score. "
    "r is symmetric under swap of the two symbols. A high |r| in one window "
    "does not prove cause, lead-lag, or a trading signal. Short windows are "
    "noisier; long windows are slower to reflect a break."
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
    for col in OHLCV_KEEP + ["log_return"]:
        cols[f"{left_name}_{col}"] = a.loc[common, col]
        cols[f"{right_name}_{col}"] = b.loc[common, col]
    table = pd.DataFrame(cols)
    table = table.dropna(subset=[f"{left_name}_log_return", f"{right_name}_log_return"])
    return table.reset_index(drop=True)


def _add_rolling(table: pd.DataFrame, left: str, right: str) -> pd.DataFrame:
    out = table.copy()
    x = out[f"{left}_log_return"]
    y = out[f"{right}_log_return"]
    for w in WINDOWS:
        out[f"r_{w}"] = x.rolling(w).corr(y)
    return out


def _window_stats(series: pd.Series, w: int) -> dict[str, float]:
    valid = series.dropna()
    n_roll = int(len(valid))
    if n_roll == 0:
        return {
            "window": w,
            "latest": float("nan"),
            "mean": float("nan"),
            "median": float("nan"),
            "min": float("nan"),
            "max": float("nan"),
            "std": float("nan"),
            "pct_abs_ge_0_4": float("nan"),
            "pct_abs_ge_0_7": float("nan"),
            "n_roll": 0,
        }
    abs_r = valid.abs()
    return {
        "window": w,
        "latest": float(valid.iloc[-1]),
        "mean": float(valid.mean()),
        "median": float(valid.median()),
        "min": float(valid.min()),
        "max": float(valid.max()),
        "std": float(valid.std(ddof=1)) if n_roll > 1 else 0.0,
        "pct_abs_ge_0_4": float(100.0 * (abs_r >= 0.4).mean()),
        "pct_abs_ge_0_7": float(100.0 * (abs_r >= 0.7).mean()),
        "n_roll": n_roll,
    }


def _stability_label(std_20: float, std_100: float) -> str:
    if np.isnan(std_20) or np.isnan(std_100):
        return "insufficient data"
    if std_20 > 1.5 * std_100 and std_20 > 0.15:
        return "short window is much noisier than the 100-day window"
    if std_20 < 0.12 and std_100 < 0.12:
        return "relatively stable across windows"
    return "moderate window-to-window variation"


def _agreement_line(latest: dict[int, float], baseline: float) -> str:
    parts = []
    for w in WINDOWS:
        r = latest[w]
        if np.isnan(r):
            parts.append(f"r_{w}=n/a")
            continue
        same_sign = (r >= 0 and baseline >= 0) or (r < 0 and baseline < 0)
        gap = abs(r - baseline)
        if not same_sign:
            parts.append(f"r_{w}={r:.3f} opposite sign vs baseline")
        elif gap >= 0.25:
            parts.append(f"r_{w}={r:.3f} far from baseline ({gap:.2f})")
        else:
            parts.append(f"r_{w}={r:.3f} near baseline")
    return "; ".join(parts)


def _tier_watch_line(tier: str, broken: bool, near_zero: bool) -> str:
    if tier == "low_value":
        if near_zero:
            return "Tier line: low interest — still near zero in recent windows."
        return "Tier line: low interest historically; check only if a short window spikes."
    if broken:
        return (
            "Tier line: watch — short window has pulled away from the full-sample "
            "baseline; treat the link as unstable until windows re-align."
        )
    if tier == "short_watchlist":
        return "Tier line: watch — priority pair; monitor r_20 vs r_60/r_100 each day."
    return "Tier line: secondary — keep on a lower-priority board next to the watchlist."


def _conclusion(
    left: str,
    right: str,
    tier: str,
    stats_by_w: dict[int, dict[str, float]],
    baseline: float,
) -> str:
    latest = {w: stats_by_w[w]["latest"] for w in WINDOWS}
    std20 = stats_by_w[20]["std"]
    std100 = stats_by_w[100]["std"]
    stability = _stability_label(std20, std100)
    agree = _agreement_line(latest, baseline)
    broken = False
    near_zero = True
    for w in WINDOWS:
        r = latest[w]
        if np.isnan(r):
            continue
        if abs(r) >= 0.25:
            near_zero = False
        if abs(r - baseline) >= 0.25 or (r >= 0) != (baseline >= 0):
            if abs(r) >= 0.15 or abs(baseline) >= 0.15:
                broken = True
    watch = _tier_watch_line(tier, broken, near_zero)
    return (
        f"For {left} and {right}, full-sample Pearson baseline r={baseline:.4f}. "
        f"Latest rolling scores: r_20={latest[20]:.4f}, r_60={latest[60]:.4f}, "
        f"r_100={latest[100]:.4f}. Stability: {stability}. "
        f"Agreement with baseline: {agree}. {watch} "
        f"This is a monitoring summary, not a trade signal."
    )


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
                if np.isnan(value):
                    cells[c_i].text = ""
                else:
                    cells[c_i].text = f"{value:.6g}"
            else:
                cells[c_i].text = str(value)


def _save_figures(
    table: pd.DataFrame,
    left: str,
    right: str,
    stem: str,
) -> dict[str, Path]:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    times = pd.to_datetime(table["time"], utc=True)

    fig, ax = plt.subplots(figsize=(10, 4.5))
    for w, color in zip(WINDOWS, ("#1f77b4", "#ff7f0e", "#2ca02c")):
        ax.plot(times, table[f"r_{w}"], color=color, linewidth=0.9, label=f"r_{w}")
    ax.axhline(0, color="gray", linewidth=0.6)
    ax.set_ylim(-1.05, 1.05)
    ax.set_title(f"Rolling Pearson r: {left} and {right}")
    ax.set_ylabel("rolling r")
    ax.legend(loc="upper left")
    fig.tight_layout()
    paths["rolling"] = FIG_DIR / f"{stem}_rolling.png"
    fig.savefig(paths["rolling"], dpi=120)
    plt.close(fig)

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
    ax.plot(times, table[f"{left}_log_return"], color="#1f77b4", linewidth=0.55, label=left)
    ax.plot(times, table[f"{right}_log_return"], color="#ff7f0e", linewidth=0.55, label=right)
    ax.set_title(f"Daily log returns: {left} and {right}")
    ax.set_ylabel("log return")
    ax.legend(loc="upper left")
    fig.tight_layout()
    paths["returns"] = FIG_DIR / f"{stem}_returns.png"
    fig.savefig(paths["returns"], dpi=120)
    plt.close(fig)

    return paths


def _write_word(
    table: pd.DataFrame,
    left: str,
    right: str,
    left_broker: str,
    right_broker: str,
    tier: str,
    stats_by_w: dict[int, dict[str, float]],
    baseline: float,
    drop_note: str,
    snapshot_name: str,
    fig_paths: dict[str, Path],
    csv_name: str,
    html_name: str,
    out_path: Path,
) -> None:
    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(10)

    pair = f"{left}-{right}"
    _add_heading(doc, f"Rolling correlation: {left} and {right}", 0)
    _add_para(
        doc,
        f"Method 05 / daily log returns / windows 20, 60, 100 / "
        f"{TIER_LABEL[tier]}",
    )

    _add_heading(doc, "Study setup", 1)
    first = pd.to_datetime(table["time"].iloc[0], utc=True).date().isoformat()
    last = pd.to_datetime(table["time"].iloc[-1], utc=True).date().isoformat()
    for line in (
        f"Logical pair: {left} , {right}",
        f"Broker symbols: {left_broker} , {right_broker}",
        f"Tier: {TIER_LABEL[tier]} ({tier})",
        f"Snapshot: {snapshot_name}",
        "Timeframe: D1",
        f"Matched return window: {first} to {last} (UTC bar dates)",
        f"Matched return count (rows before rolling): {len(table)}",
        drop_note,
        f"Rolling windows W: {', '.join(str(w) for w in WINDOWS)} trading days",
        f"Live-shaped n for each score: n = W (not the full history length)",
        f"Complete matched rows (CSV): {csv_name}",
        f"Complete matched rows (HTML): {html_name}",
    ):
        _add_para(doc, line)

    _add_heading(doc, "Method carried forward", 1)
    _add_para(doc, METHOD_NOTE)
    _add_para(
        doc,
        "How to read a live day: after both daily candles close, the newest "
        "r_20 uses the last 20 matched log returns, r_60 the last 60, and r_100 "
        "the last 100. Compare those three to each other and to the full-sample "
        "baseline below. A break is when the short window moves far from the "
        "baseline or flips sign while the baseline was meaningful.",
    )

    _add_heading(doc, "Full-sample Pearson baseline (method 01 v001)", 1)
    _add_para(
        doc,
        f"Copied full-sample Pearson r for {pair}: {baseline:.6f}. "
        "This is a historical average link, not the live state.",
    )

    _add_heading(doc, "Rolling results", 1)
    rows = []
    for w in WINDOWS:
        s = stats_by_w[w]
        rows.append(
            {
                "W": w,
                "latest_r": round(s["latest"], 6),
                "mean": round(s["mean"], 6),
                "median": round(s["median"], 6),
                "min": round(s["min"], 6),
                "max": round(s["max"], 6),
                "std": round(s["std"], 6),
                "pct_|r|>=0.4": round(s["pct_abs_ge_0_4"], 2),
                "pct_|r|>=0.7": round(s["pct_abs_ge_0_7"], 2),
                "n_roll": s["n_roll"],
            }
        )
    _add_small_table(doc, pd.DataFrame(rows))
    _add_para(
        doc,
        "n_roll is the number of days that had a complete window. "
        "pct_|r|>=0.4 and pct_|r|>=0.7 are the share of those days where the "
        "absolute rolling correlation cleared the threshold.",
    )

    _add_heading(doc, "Conclusion", 1)
    _add_para(doc, _conclusion(left, right, tier, stats_by_w, baseline))

    _add_heading(doc, "What to look at in this file next time", 1)
    _add_para(
        doc,
        "1) Latest r_20 vs r_60 vs r_100 in the results table. "
        "2) Whether short-window latest has the same sign as the baseline. "
        "3) The rolling chart for stretches where |r| collapsed. "
        "4) The CSV if you need a different chart later.",
    )

    _add_heading(doc, "Charts", 1)
    for key, title in (
        ("rolling", "Rolling Pearson r (20 / 60 / 100)"),
        ("closes", "Daily closes"),
        ("returns", "Daily log returns"),
    ):
        _add_para(doc, title, bold=True)
        doc.add_picture(str(fig_paths[key]), width=Inches(6.2))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

    _add_heading(doc, "Data report", 1)
    _add_para(
        doc,
        "Every matched row with r_20, r_60, and r_100 is in the sibling CSV and "
        "HTML. This Word section holds column summaries and the first and last "
        "15 rows of the rolling table.",
    )
    _add_para(doc, "Columns: " + ", ".join(table.columns))
    numeric_cols = [c for c in table.columns if c != "time"]
    summary = (
        table[numeric_cols].describe().T.reset_index().rename(columns={"index": "column"})
    )
    _add_para(doc, "Column summaries", bold=True)
    _add_small_table(doc, summary.round(8))

    preview_cols = [
        "time",
        f"{left}_close",
        f"{right}_close",
        f"{left}_log_return",
        f"{right}_log_return",
        "r_20",
        "r_60",
        "r_100",
    ]
    _add_para(doc, "First 15 matched rows", bold=True)
    _add_small_table(doc, table.loc[:, preview_cols].head(15))
    _add_para(doc, "Last 15 matched rows", bold=True)
    _add_small_table(doc, table.loc[:, preview_cols].tail(15))

    doc.save(out_path)


def _write_notes(
    drop_note: str,
    manifest: dict,
    index_rows: list[dict],
) -> None:
    lines = [
        "# Rolling correlation experiments v002",
        "",
        "## Research question",
        "",
        "For the short watchlist, secondary tier, and low-value pairs, how does "
        "Pearson correlation of daily log returns move when recomputed on the "
        "last 20, 60, and 100 matched days?",
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
        "- Statistic: rolling Pearson r with W in {20, 60, 100}",
        "- Full-sample baseline: copied from Pearson method 01 v001 NOTES",
        "- Outputs: 17 Word reports, HTML tables, CSVs, charts, WATCHLIST.md",
        "",
    ]
    for tier_key, title in (
        ("short_watchlist", "Short watchlist"),
        ("secondary", "Secondary tier"),
        ("low_value", "Low-value"),
    ):
        lines.append(f"## {title}")
        lines.append("")
        lines.append(
            "| pair | baseline_r | r20 | r60 | r100 | std20 | std100 | n_roll_100 |"
        )
        lines.append("| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
        for row in index_rows:
            if row["tier"] != tier_key:
                continue
            lines.append(
                f"| {row['pair']} | {row['baseline_r']:.6f} | {row['r20']:.6f} | "
                f"{row['r60']:.6f} | {row['r100']:.6f} | {row['std20']:.6f} | "
                f"{row['std100']:.6f} | {row['n_roll_100']} |"
            )
        lines.append("")
    lines.append("This NOTES.md is the index only. It is not an 18th analysis.")
    lines.append("")
    (EXP_DIR / "NOTES.md").write_text("\n".join(lines), encoding="utf-8")


def _write_watchlist(index_rows: list[dict]) -> None:
    def sort_key(row: dict) -> tuple:
        return (abs(row["r20"] - row["baseline_r"]), abs(row["r20"]))

    watch = [r for r in index_rows if r["tier"] == "short_watchlist"]
    secondary = [r for r in index_rows if r["tier"] == "secondary"]
    low = [r for r in index_rows if r["tier"] == "low_value"]

    broken = []
    for r in index_rows:
        gap = abs(r["r20"] - r["baseline_r"])
        sign_flip = (r["r20"] >= 0) != (r["baseline_r"] >= 0)
        if gap >= 0.25 or (sign_flip and abs(r["baseline_r"]) >= 0.2):
            broken.append(r)
    broken = sorted(broken, key=sort_key, reverse=True)

    still_flat = [
        r
        for r in low
        if abs(r["r20"]) < 0.25 and abs(r["r60"]) < 0.25 and abs(r["r100"]) < 0.25
    ]

    lines = [
        "# Which data do I need to look after?",
        "",
        "Read this after the rolling v002 run. Numbers are the **latest** "
        "rolling Pearson scores on daily log returns.",
        "",
        "## Look at these first (short watchlist)",
        "",
    ]
    for r in sorted(watch, key=lambda x: -abs(x["baseline_r"])):
        lines.append(
            f"- **{r['pair']}**: baseline {r['baseline_r']:.3f}; "
            f"latest r_20={r['r20']:.3f}, r_60={r['r60']:.3f}, r_100={r['r100']:.3f}"
        )
    lines.extend(["", "## Also keep on a secondary board", ""])
    for r in sorted(secondary, key=lambda x: -abs(x["baseline_r"])):
        lines.append(
            f"- **{r['pair']}**: baseline {r['baseline_r']:.3f}; "
            f"latest r_20={r['r20']:.3f}, r_60={r['r60']:.3f}, r_100={r['r100']:.3f}"
        )

    lines.extend(["", "## Short window vs baseline (possible breaks)", ""])
    if not broken:
        lines.append("- No pair cleared the break screen (gap ≥ 0.25 or sign flip).")
    else:
        for r in broken:
            lines.append(
                f"- **{r['pair']}** ({TIER_LABEL[r['tier']]}): "
                f"baseline {r['baseline_r']:.3f} vs r_20={r['r20']:.3f} "
                f"(gap {abs(r['r20'] - r['baseline_r']):.3f})"
            )

    lines.extend(["", "## Still near zero (safe to ignore for now)", ""])
    if not still_flat:
        lines.append("- No low-value pair stayed under |r|<0.25 on all three windows.")
    else:
        for r in still_flat:
            lines.append(
                f"- **{r['pair']}**: r_20={r['r20']:.3f}, r_60={r['r60']:.3f}, "
                f"r_100={r['r100']:.3f}"
            )

    lines.extend(
        [
            "",
            "## Practical monitoring order",
            "",
            "1. Open the five short-watchlist Word files (or their last-15-row tables).",
            "2. Each new D1 close, refresh attention on **r_20** first, then confirm with "
            "**r_60** and **r_100**.",
            "3. Escalate only when r_20 moves far from the baseline or flips sign.",
            "4. Leave the still-near-zero low-value pairs alone unless a short window spikes.",
            "",
        ]
    )
    (OUT_DIR / "WATCHLIST.md").write_text("\n".join(lines), encoding="utf-8")


def run() -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    snap = load_snapshot(REPO_ROOT / SNAPSHOT_REL)
    manifest = snap["manifest"]
    snapshot_name = manifest["folder"]
    broker_map = {row["logical"]: row["resolved"] for row in manifest["symbols"]}
    frames, drop_note = _prepare_frames(snap["frames"])

    index_rows: list[dict] = []
    flat_index: list[dict] = []

    for tier, pairs in TIERS.items():
        for left, right in pairs:
            pair = f"{left}-{right}"
            baseline = FULL_SAMPLE_R[pair]
            table = _pair_table(frames[left], frames[right], left, right)
            table = _add_rolling(table, left, right)
            stats_by_w = {
                w: _window_stats(table[f"r_{w}"], w) for w in WINDOWS
            }
            stem = f"{pair}_Rolling_D1"
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
                    f"<h1>{left} and {right}: rolling correlation rows</h1>"
                    f"<p>Windows 20/60/100. CSV archive: {csv_path.name}</p>"
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
                tier=tier,
                stats_by_w=stats_by_w,
                baseline=baseline,
                drop_note=drop_note,
                snapshot_name=snapshot_name,
                fig_paths=fig_paths,
                csv_name=csv_path.name,
                html_name=html_path.name,
                out_path=docx_path,
            )

            index_rows.append(
                {
                    "tier": tier,
                    "pair": pair,
                    "baseline_r": baseline,
                    "r20": stats_by_w[20]["latest"],
                    "r60": stats_by_w[60]["latest"],
                    "r100": stats_by_w[100]["latest"],
                    "std20": stats_by_w[20]["std"],
                    "std60": stats_by_w[60]["std"],
                    "std100": stats_by_w[100]["std"],
                    "n_roll_20": stats_by_w[20]["n_roll"],
                    "n_roll_60": stats_by_w[60]["n_roll"],
                    "n_roll_100": stats_by_w[100]["n_roll"],
                    "docx": docx_path.name,
                    "csv": csv_path.name,
                    "html": html_path.name,
                }
            )
            for w in WINDOWS:
                s = stats_by_w[w]
                flat_index.append(
                    {
                        "tier": tier,
                        "pair": pair,
                        "window": w,
                        "baseline_r": baseline,
                        "latest_r": s["latest"],
                        "mean": s["mean"],
                        "median": s["median"],
                        "min": s["min"],
                        "max": s["max"],
                        "std": s["std"],
                        "pct_abs_ge_0_4": s["pct_abs_ge_0_4"],
                        "pct_abs_ge_0_7": s["pct_abs_ge_0_7"],
                        "n_roll": s["n_roll"],
                    }
                )
            print(
                f"Wrote {docx_path.name}  "
                f"r20={stats_by_w[20]['latest']:.3f} "
                f"r60={stats_by_w[60]['latest']:.3f} "
                f"r100={stats_by_w[100]['latest']:.3f}",
                flush=True,
            )

    pd.DataFrame(flat_index).to_csv(OUT_DIR / "index.csv", index=False)
    pd.DataFrame(index_rows).to_csv(OUT_DIR / "index_latest.csv", index=False)
    _write_notes(drop_note, manifest, index_rows)
    _write_watchlist(index_rows)
    return OUT_DIR


if __name__ == "__main__":
    run()
