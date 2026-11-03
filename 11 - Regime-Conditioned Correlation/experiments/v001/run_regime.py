"""Regime-conditioned correlation on Alpari D1 majors: Word, HTML, and Excel per pair."""

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
RV_WINDOW = 20
RV_HISTORY = 252
STRESS_PCT = 75.0
METHOD_NOTE = (
    "Regime-conditioned correlation splits matched daily log returns of "
    "close, ln(close_t / close_t-1), into quiet and stress states defined "
    "from a shared FX turbulence rule fixed before any pair rho is "
    "computed. Quotes are not inverted. On dates where all eight majors "
    "have a log return, turb_t is the equal-weight mean of the eight "
    "absolute log returns. RV_t is the mean of turb over the previous 20 "
    "completed days (t-20 through t-1); day t is not in the label. After "
    "252 past RV values exist, S_t = stress when RV_t exceeds the 75th "
    "percentile of those past values, otherwise quiet. Earlier days stay "
    "unlabeled and are dropped from both rhos. One S_t series is applied "
    "to every pair. rho_quiet and rho_stress are Pearson correlations on "
    "their own subsamples; their mean is not a headline. Full-sample "
    "Pearson r on labeled rows only is a side check. This is not a cause, "
    "lead, or trading signal."
)


def _assert_guide_toys() -> None:
    quiet_x = [0.010, 0.020, 0.015, 0.012]
    quiet_y = [0.008, 0.018, 0.014, 0.011]
    stress_x = [-0.050, 0.040, -0.030, 0.035]
    stress_y = [-0.030, -0.020, 0.025, -0.015]
    assert abs(float(stats.pearsonr(quiet_x, quiet_y).statistic) - 0.9911908577446502) < 1e-9
    assert abs(float(stats.pearsonr(stress_x, stress_y).statistic) - (-0.18945647121890377)) < 1e-9


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


def _build_regime_frame(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """One shared S_t series from eight-major turbulence (look-ahead free)."""
    ret_cols: dict[str, pd.Series] = {}
    common = None
    for name in MAJOR_PAIRS:
        series = frames[name].set_index("time")["log_return"].dropna()
        ret_cols[name] = series
        common = series.index if common is None else common.intersection(series.index)
    common = common.sort_values()
    ret_mat = pd.DataFrame({name: ret_cols[name].loc[common] for name in MAJOR_PAIRS})
    turb = ret_mat.abs().mean(axis=1).to_numpy(dtype=float)
    n = len(turb)
    rv = np.full(n, np.nan, dtype=float)
    for t in range(RV_WINDOW, n):
        rv[t] = float(np.mean(turb[t - RV_WINDOW : t]))
    state = np.array([""] * n, dtype=object)
    for t in range(n):
        if t < RV_WINDOW + RV_HISTORY:
            continue
        if np.isnan(rv[t]):
            continue
        past = rv[t - RV_HISTORY : t]
        if np.any(np.isnan(past)):
            continue
        thresh = float(np.percentile(past, STRESS_PCT))
        state[t] = "stress" if rv[t] > thresh else "quiet"
    return pd.DataFrame(
        {
            "time": common,
            "turb": turb,
            "rv": rv,
            "state": state,
        }
    ).reset_index(drop=True)


def _pair_table(
    left: pd.DataFrame,
    right: pd.DataFrame,
    left_name: str,
    right_name: str,
    regime: pd.DataFrame,
) -> pd.DataFrame:
    a = left.set_index("time")
    b = right.set_index("time")
    r = regime.set_index("time")
    common = a.index.intersection(b.index).intersection(r.index).sort_values()
    cols: dict[str, pd.Series] = {"time": pd.Series(common, index=common)}
    for col in OHLCV + ["log_return"]:
        cols[f"{left_name}_{col}"] = a.loc[common, col]
        cols[f"{right_name}_{col}"] = b.loc[common, col]
    cols["turb"] = r.loc[common, "turb"]
    cols["rv"] = r.loc[common, "rv"]
    cols["state"] = r.loc[common, "state"]
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


def _regime_stats(table: pd.DataFrame, left: str, right: str) -> dict[str, float]:
    labeled = table[table["state"].isin(["quiet", "stress"])].copy()
    quiet = labeled[labeled["state"] == "quiet"]
    stress = labeled[labeled["state"] == "stress"]
    x_q = quiet[f"{left}_log_return"].to_numpy(dtype=float)
    y_q = quiet[f"{right}_log_return"].to_numpy(dtype=float)
    x_s = stress[f"{left}_log_return"].to_numpy(dtype=float)
    y_s = stress[f"{right}_log_return"].to_numpy(dtype=float)
    x_all = labeled[f"{left}_log_return"].to_numpy(dtype=float)
    y_all = labeled[f"{right}_log_return"].to_numpy(dtype=float)
    q = _pearson_block(x_q, y_q)
    s = _pearson_block(x_s, y_s)
    full = _pearson_block(x_all, y_all)
    return {
        "n_labeled": float(len(labeled)),
        "n_quiet": q["n"],
        "rho_quiet": q["r"],
        "p_quiet": q["p"],
        "ci_low_quiet": q["ci_low"],
        "ci_high_quiet": q["ci_high"],
        "n_stress": s["n"],
        "rho_stress": s["r"],
        "p_stress": s["p"],
        "ci_low_stress": s["ci_low"],
        "ci_high_stress": s["ci_high"],
        "pearson_r_labeled": full["r"],
        "stress_minus_quiet": s["r"] - q["r"],
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
    rq = stats_row["rho_quiet"]
    rs = stats_row["rho_stress"]
    return (
        f"On the labeled subsample for {left} and {right}, rho_quiet is "
        f"{_fmt(rq, 4)} (n_quiet={int(stats_row['n_quiet'])}, "
        f"{_strength_label(rq)}) and rho_stress is {_fmt(rs, 4)} "
        f"(n_stress={int(stats_row['n_stress'])}, {_strength_label(rs)}). "
        f"stress minus quiet = {_fmt(stats_row['stress_minus_quiet'], 4)}. "
        f"Pearson r on all labeled rows is "
        f"{_fmt(stats_row['pearson_r_labeled'], 4)}. Regime rhos are not "
        f"averaged into a headline. This does not establish cause, lead-lag, "
        f"or a lasting trading rule."
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
    stress_mask = table["state"].to_numpy() == "stress"

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
    if stress_mask.any():
        ymin, ymax = ax.get_ylim()
        ax.fill_between(
            times,
            ymin,
            ymax,
            where=stress_mask,
            color="#d62728",
            alpha=0.12,
            label="stress",
        )
    ax.set_title(f"Log returns with stress days: {left} and {right}")
    ax.set_ylabel("log return")
    ax.legend(loc="upper left")
    fig.tight_layout()
    paths["returns"] = FIG_DIR / f"{stem}_returns.png"
    fig.savefig(paths["returns"], dpi=120)
    plt.close(fig)

    labeled = table[table["state"].isin(["quiet", "stress"])]
    fig, ax = plt.subplots(figsize=(5.5, 5.2))
    for state, color in (("quiet", "#1f77b4"), ("stress", "#d62728")):
        sub = labeled[labeled["state"] == state]
        ax.scatter(
            sub[f"{left}_log_return"],
            sub[f"{right}_log_return"],
            s=8,
            alpha=0.4,
            color=color,
            label=state,
        )
    ax.set_xlabel(f"{left} log return")
    ax.set_ylabel(f"{right} log return")
    ax.set_title(f"Regime scatter: {left} vs {right}")
    ax.axhline(0, color="gray", linewidth=0.5)
    ax.axvline(0, color="gray", linewidth=0.5)
    ax.legend(loc="best")
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
    fig_paths: dict[str, Path],
    xlsx_name: str,
    out_path: Path,
) -> None:
    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(10)

    _add_heading(doc, f"Regime-conditioned correlation: {left} and {right}", 0)
    _add_para(
        doc,
        "Method 11 / daily log returns / shared FX turbulence regimes / "
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
        f"Matched return count n: {len(table)}",
        f"Labeled rows n: {int(stats_row['n_labeled'])}",
        drop_note,
        (
            f"State rule: turb = equal-weight mean of eight |log returns|; "
            f"RV = mean of prior {RV_WINDOW} turb days; after {RV_HISTORY} "
            f"past RV values, stress if RV > {STRESS_PCT:g}th percentile of "
            "those past values, else quiet"
        ),
        f"Complete matched rows (Excel): {xlsx_name}",
        f"Complete matched rows (HTML table): {xlsx_name.replace('.xlsx', '_data.html')}",
    ]
    for line in setup_lines:
        _add_para(doc, line)

    _add_heading(doc, "Method carried forward", 1)
    _add_para(doc, METHOD_NOTE)

    _add_heading(doc, "Results", 1)
    _add_para(doc, f"rho_quiet: {_fmt(stats_row['rho_quiet'], 6)} (n={int(stats_row['n_quiet'])})")
    _add_para(
        doc,
        f"Quiet 95% Fisher interval: "
        f"[{_fmt(stats_row['ci_low_quiet'], 6)}, {_fmt(stats_row['ci_high_quiet'], 6)}]",
    )
    _add_para(
        doc,
        f"rho_stress: {_fmt(stats_row['rho_stress'], 6)} (n={int(stats_row['n_stress'])})",
    )
    _add_para(
        doc,
        f"Stress 95% Fisher interval: "
        f"[{_fmt(stats_row['ci_low_stress'], 6)}, {_fmt(stats_row['ci_high_stress'], 6)}]",
    )
    _add_para(
        doc,
        f"Pearson r on labeled rows: {_fmt(stats_row['pearson_r_labeled'], 6)}",
    )
    _add_para(
        doc,
        f"rho_stress minus rho_quiet: {_fmt(stats_row['stress_minus_quiet'], 6)}",
    )

    _add_heading(doc, "Conclusion", 1)
    _add_para(doc, _conclusion(left, right, stats_row))

    _add_heading(doc, "Charts", 1)
    for key, title in (
        ("closes", "Daily closes"),
        ("returns", "Log returns with stress days"),
        ("scatter", "Scatter colored by regime"),
    ):
        _add_para(doc, title, bold=True)
        doc.add_picture(str(fig_paths[key]), width=Inches(6.2))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

    _add_heading(doc, "Data report", 1)
    _add_para(
        doc,
        "Every matched row that entered the regime analysis is stored in "
        f"the sibling Excel workbook named {xlsx_name}. That file is the "
        "complete data archive for redrawing charts. Embedding all rows as a "
        "Word table is impractical at this length; the Word file holds the "
        "column list, column summaries, and the first and last 15 matched rows.",
    )
    _add_para(doc, "Columns: " + ", ".join(table.columns))

    numeric_cols = [c for c in table.columns if c not in ("time", "state")]
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
        "turb",
        "rv",
        "state",
    ]
    _add_para(doc, "First 15 matched rows (selected columns)", bold=True)
    _add_small_table(doc, table.loc[:, preview_cols].head(15))
    _add_para(doc, "Last 15 matched rows (selected columns)", bold=True)
    _add_small_table(doc, table.loc[:, preview_cols].tail(15))

    doc.save(out_path)


def _cross_pair_conclusion(index_rows: list[dict[str, object]]) -> list[str]:
    by_stress = sorted(index_rows, key=lambda row: float(row["rho_stress"]))
    by_gap = sorted(
        index_rows,
        key=lambda row: abs(float(row["stress_minus_quiet"])),
        reverse=True,
    )
    strongest_pos = by_stress[-1]
    strongest_neg = by_stress[0]
    near_zero = sorted(index_rows, key=lambda row: abs(float(row["rho_stress"])))[:3]
    top_gaps = by_gap[:3]

    lines = [
        "## Cross-pair conclusion",
        "",
        "Reading of the 28-pair index only. Not a 29th pair analysis and not a "
        "trading signal.",
        "",
        (
            f"Strongest positive rho_stress: {strongest_pos['pair']} "
            f"(rho_stress={float(strongest_pos['rho_stress']):.4f}, "
            f"n_stress={strongest_pos['n_stress']})."
        ),
        (
            f"Strongest negative rho_stress: {strongest_neg['pair']} "
            f"(rho_stress={float(strongest_neg['rho_stress']):.4f}, "
            f"n_stress={strongest_neg['n_stress']})."
        ),
        "Nearest-to-zero rho_stress: "
        + "; ".join(
            f"{row['pair']} (rho_stress={float(row['rho_stress']):.4f})"
            for row in near_zero
        )
        + ".",
        "Largest |rho_stress minus rho_quiet| gaps: "
        + "; ".join(
            f"{row['pair']} (gap={float(row['stress_minus_quiet']):.4f}, "
            f"rho_stress={float(row['rho_stress']):.4f}, "
            f"rho_quiet={float(row['rho_quiet']):.4f})"
            for row in top_gaps
        )
        + ". A large gap can flag different co-movement in stress versus "
        "quiet; inspect that pair's n_stress and charts before treating "
        "either score as settled.",
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
    regime = _build_regime_frame(frames)

    index_rows: list[dict[str, object]] = []
    pairs = list(itertools.combinations(MAJOR_PAIRS, 2))

    for left, right in pairs:
        table = _pair_table(frames[left], frames[right], left, right, regime)
        stats_row = _regime_stats(table, left, right)
        stem = f"{left}-{right}_Regime_D1"
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
                f"<h1>{left} and {right}: matched rows used for regime "
                f"correlation</h1>"
                f"<p>n={len(table)}. n_quiet={int(stats_row['n_quiet'])}. "
                f"n_stress={int(stats_row['n_stress'])}. Complete archive "
                f"also in {xlsx_path.name}.</p>"
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
                "n_labeled": int(stats_row["n_labeled"]),
                "n_quiet": int(stats_row["n_quiet"]),
                "rho_quiet": stats_row["rho_quiet"],
                "p_quiet": stats_row["p_quiet"],
                "n_stress": int(stats_row["n_stress"]),
                "rho_stress": stats_row["rho_stress"],
                "p_stress": stats_row["p_stress"],
                "pearson_r_labeled": stats_row["pearson_r_labeled"],
                "stress_minus_quiet": stats_row["stress_minus_quiet"],
                "docx": docx_path.name,
                "xlsx": xlsx_path.name,
                "html": html_path.name,
            }
        )
        print(
            f"Wrote {docx_path.name}  quiet={stats_row['rho_quiet']:.4f} "
            f"stress={stats_row['rho_stress']:.4f}  "
            f"n_q={int(stats_row['n_quiet'])} n_s={int(stats_row['n_stress'])}",
            flush=True,
        )

    index = pd.DataFrame(index_rows)
    index.to_excel(OUT_DIR / "index.xlsx", index=False, sheet_name="index")

    notes = [
        "# Regime-conditioned correlation experiments v001",
        "",
        "## Research question",
        "",
        "For each unordered pair among the eight majors, how do Pearson "
        "correlations of matched daily log returns of close differ in quiet "
        "versus stress states defined from a shared look-ahead-free FX "
        "turbulence rule on the Alpari D1 history?",
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
            f"- State rule: on dates with all eight majors present, turb = "
            f"equal-weight mean of |log returns|; RV = mean of prior "
            f"{RV_WINDOW} turb days; after {RV_HISTORY} past RV values, "
            f"stress if RV > {STRESS_PCT:g}th percentile of those past "
            "values, else quiet; unlabeled days dropped from both rhos"
        ),
        "- Statistic: Pearson rho_quiet and rho_stress via "
        "`scipy.stats.pearsonr` with Fisher 95% intervals; Pearson r on "
        "labeled rows as a side check; stress_minus_quiet reported",
        "- Outputs: 28 Word reports, 28 full-data HTML tables, 28 Excel "
        "workbooks, charts under `outputs/figures/` (closes, returns with "
        "stress shading, regime scatter)",
        "",
        "## Index",
        "",
        "| pair | n_labeled | n_quiet | rho_quiet | p_quiet | n_stress | "
        "rho_stress | p_stress | pearson_r_labeled | stress_minus_quiet |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in index_rows:
        notes.append(
            f"| {row['pair']} | {row['n_labeled']} | {row['n_quiet']} | "
            f"{float(row['rho_quiet']):.6f} | {float(row['p_quiet']):.6g} | "
            f"{row['n_stress']} | {float(row['rho_stress']):.6f} | "
            f"{float(row['p_stress']):.6g} | "
            f"{float(row['pearson_r_labeled']):.6f} | "
            f"{float(row['stress_minus_quiet']):.6f} |"
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
