"""Multifractal DCCA on Alpari D1 majors: Word, HTML, and Excel per pair."""

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
SCALES = (20, 60, 100)
QS = (2.0, 4.0)
HEADLINE_Q = 2.0
HEADLINE_S = 100
TREND_DEGREE = 1
OVERLAP = "none"
METHOD_NOTE = (
    "Multifractal DCCA rho_q(s) extends detrended cross-correlation with a "
    "positive order q that weights large local fluctuations more strongly. "
    "Matched daily log returns of close, ln(close_t / close_t-1), are "
    "demeaned and cumulated into profiles. Non-overlapping windows of length "
    "s receive a degree-1 local detrend. In each window v, "
    "c_xy,v = mean(X_tilde * Y_tilde), c_xx,v = mean(X_tilde^2), "
    "c_yy,v = mean(Y_tilde^2). Then "
    "G(q,s) = mean_v[ sign(c) * |c|^(q/2) ] and "
    "rho_q(s) = G_xy / sqrt(G_xx * G_yy). Positive q only; q=2 recovers "
    "the DCCA-type average of c_v. Scales s in {20, 60, 100}; q in {2, 4}; "
    "headline q=2, s=100. Same-sample Pearson r is a side check only. "
    "This is not causation and not a trading signal."
)


def _mf_term(c: float, q: float) -> float:
    if c == 0.0:
        return 0.0
    return (1.0 if c > 0.0 else -1.0) * (abs(c) ** (q / 2.0))


def _g_q(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    return sum(_mf_term(c, q) for c in values) / len(values)


def _local_fluctuations(
    x: np.ndarray, y: np.ndarray, window: int
) -> tuple[list[float], list[float], list[float]]:
    """Per-window detrended c_xy, c_xx, c_yy (means of residual products)."""
    n = len(x)
    mx = float(np.mean(x))
    my = float(np.mean(y))
    prof_x = np.cumsum(x - mx)
    prof_y = np.cumsum(y - my)
    nbox = n // window
    c_xy: list[float] = []
    c_xx: list[float] = []
    c_yy: list[float] = []
    t = np.arange(window, dtype=float)
    tx = float(t.mean())
    denom_t = float(np.sum((t - tx) ** 2))
    for b in range(nbox):
        segx = prof_x[b * window : (b + 1) * window]
        segy = prof_y[b * window : (b + 1) * window]
        sx = float(segx.mean())
        sy = float(segy.mean())
        if denom_t == 0.0:
            slope_x = slope_y = 0.0
        else:
            slope_x = float(np.sum((t - tx) * (segx - sx)) / denom_t)
            slope_y = float(np.sum((t - tx) * (segy - sy)) / denom_t)
        a_x = sx - slope_x * tx
        a_y = sy - slope_y * tx
        rx = segx - (a_x + slope_x * t)
        ry = segy - (a_y + slope_y * t)
        c_xy.append(float(np.mean(rx * ry)))
        c_xx.append(float(np.mean(rx * rx)))
        c_yy.append(float(np.mean(ry * ry)))
    return c_xy, c_xx, c_yy


def rho_q(x: np.ndarray, y: np.ndarray, window: int, q: float) -> tuple[float, int]:
    c_xy, c_xx, c_yy = _local_fluctuations(x, y, window)
    n_win = len(c_xy)
    if n_win == 0:
        return 0.0, 0
    g_xy = _g_q(c_xy, q)
    g_xx = _g_q(c_xx, q)
    g_yy = _g_q(c_yy, q)
    den = math.sqrt(g_xx * g_yy)
    if den == 0.0:
        return 0.0, n_win
    return g_xy / den, n_win


def _assert_guide_toys() -> None:
    cross = [0.0002, 0.0003, 0.0001]
    fx = [0.0010, 0.0020, 0.0015]
    fy = [0.0011, 0.0019, 0.0014]
    g_xy = _g_q(cross, 2.0)
    g_xx = _g_q(fx, 2.0)
    g_yy = _g_q(fy, 2.0)
    rho = g_xy / math.sqrt(g_xx * g_yy)
    assert abs(g_xy - 0.0002) < 1e-15
    assert abs(rho - 0.1348399724926484) < 1e-9


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


def _mfdcca_stats(
    table: pd.DataFrame, left: str, right: str
) -> tuple[dict[str, float], pd.DataFrame]:
    x = table[f"{left}_log_return"].to_numpy(dtype=float)
    y = table[f"{right}_log_return"].to_numpy(dtype=float)
    pearson_r = float(stats.pearsonr(x, y).statistic)
    rows: list[dict[str, float]] = []
    stats_row: dict[str, float] = {"n": float(len(table)), "pearson_r": pearson_r}
    for s in SCALES:
        for q in QS:
            rho, n_win = rho_q(x, y, s, q)
            key = f"rho_q{int(q)}_s{s}"
            stats_row[key] = rho
            stats_row[f"n_windows_s{s}"] = float(n_win)
            rows.append(
                {
                    "q": float(q),
                    "s": float(s),
                    "rho_q": rho,
                    "n_windows": float(n_win),
                }
            )
    return stats_row, pd.DataFrame(rows)


def _fmt(value: float, digits: int = 4) -> str:
    if math.isnan(value):
        return "n/a"
    return f"{value:.{digits}f}"


def _conclusion(left: str, right: str, stats_row: dict[str, float]) -> str:
    return (
        f"Headline rho_q(q=2,s={HEADLINE_S}) for {left} and {right}: "
        f"{_fmt(stats_row['rho_q2_s100'], 4)}. "
        f"At q=4,s=100: {_fmt(stats_row['rho_q4_s100'], 4)}. "
        f"At q=2,s=20: {_fmt(stats_row['rho_q2_s20'], 4)}; "
        f"q=2,s=60: {_fmt(stats_row['rho_q2_s60'], 4)}. "
        f"Pearson r = {_fmt(stats_row['pearson_r'], 4)}. "
        f"This is q-weighted detrended linkage, not a trading signal."
    )


def _save_figures(
    table: pd.DataFrame,
    left: str,
    right: str,
    scale_df: pd.DataFrame,
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
    for q, color in ((2.0, "#087F8C"), (4.0, "#d62728")):
        sub = scale_df[scale_df["q"] == q]
        ax.plot(sub["s"], sub["rho_q"], marker="o", color=color, label=f"q={int(q)}")
    ax.axhline(0, color="gray", linewidth=0.5)
    ax.set_xlabel("window length s")
    ax.set_ylabel("rho_q(s)")
    ax.set_title(f"MF-DCCA by scale: {left} and {right}")
    ax.legend(loc="best")
    fig.tight_layout()
    paths["mfdcca"] = FIG_DIR / f"{stem}_mfdcca.png"
    fig.savefig(paths["mfdcca"], dpi=120)
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
    scale_df: pd.DataFrame,
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

    _add_heading(doc, f"Multifractal DCCA: {left} and {right}", 0)
    _add_para(
        doc,
        "Method 24 / daily log returns / non-overlapping MF-DCCA / "
        "Alpari D1 full available history",
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
        f"Scales s in {list(SCALES)}; q in {list(QS)}; "
        f"headline q={int(HEADLINE_Q)}, s={HEADLINE_S}",
        f"Trend degree={TREND_DEGREE}; overlap={OVERLAP}; positive q only",
        f"Complete matched rows (Excel): {xlsx_name}",
        f"Complete matched rows (HTML table): {xlsx_name.replace('.xlsx', '_data.html')}",
    ):
        _add_para(doc, line)

    _add_heading(doc, "Method carried forward", 1)
    _add_para(doc, METHOD_NOTE)

    _add_heading(doc, "Results (headline)", 1)
    _add_para(doc, f"rho_q(q=2,s=100): {_fmt(stats_row['rho_q2_s100'], 6)}")
    _add_para(doc, f"rho_q(q=4,s=100): {_fmt(stats_row['rho_q4_s100'], 6)}")
    _add_para(doc, f"rho_q(q=2,s=20): {_fmt(stats_row['rho_q2_s20'], 6)}")
    _add_para(doc, f"rho_q(q=2,s=60): {_fmt(stats_row['rho_q2_s60'], 6)}")
    _add_para(doc, f"Pearson r: {_fmt(stats_row['pearson_r'], 6)}")

    _add_heading(doc, "Scale / q summary", 1)
    _add_small_table(doc, scale_df.round(8))

    _add_heading(doc, "Conclusion", 1)
    _add_para(doc, _conclusion(left, right, stats_row))

    _add_heading(doc, "Charts", 1)
    for key, title in (
        ("closes", "Daily closes"),
        ("returns", "Daily log returns"),
        ("mfdcca", "rho_q versus s"),
    ):
        _add_para(doc, title, bold=True)
        doc.add_picture(str(fig_paths[key]), width=Inches(6.2))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

    _add_heading(doc, "Data report", 1)
    _add_para(
        doc,
        "Matched rows and the scale sheet are in the sibling Excel workbook "
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
    by_rho = sorted(index_rows, key=lambda r: float(r["rho_q2_s100"]))
    strongest_pos = by_rho[-1]
    strongest_neg = by_rho[0]
    nearest = sorted(index_rows, key=lambda r: abs(float(r["rho_q2_s100"])))[:3]
    return [
        "## Cross-pair conclusion",
        "",
        "Reading of the 28-pair index at pre-specified rho_q(q=2,s=100). "
        "Not a 29th pair analysis and not a trading signal.",
        "",
        (
            f"Strongest positive: {strongest_pos['pair']} "
            f"(rho={float(strongest_pos['rho_q2_s100']):.4f})."
        ),
        (
            f"Strongest negative: {strongest_neg['pair']} "
            f"(rho={float(strongest_neg['rho_q2_s100']):.4f})."
        ),
        "Nearest-to-zero: "
        + "; ".join(
            f"{r['pair']} (rho={float(r['rho_q2_s100']):.4f})" for r in nearest
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
        stats_row, scale_df = _mfdcca_stats(table, left, right)
        stem = f"{left}-{right}_MFDCCA_D1"
        fig_paths = _save_figures(table, left, right, scale_df, stem)

        xlsx_path = OUT_DIR / f"{stem}.xlsx"
        excel_frame = table.copy()
        excel_frame["time"] = pd.to_datetime(excel_frame["time"], utc=True).dt.strftime(
            "%Y-%m-%d"
        )
        with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
            excel_frame.to_excel(writer, index=False, sheet_name="matched_rows")
            scale_df.to_excel(writer, index=False, sheet_name="scales")

        html_path = OUT_DIR / f"{stem}_data.html"
        html_path.write_text(
            (
                f"<!DOCTYPE html><html><head><meta charset='utf-8'>"
                f"<title>{stem} data</title></head><body>"
                f"<h1>{left} and {right}: matched rows for MF-DCCA</h1>"
                f"<p>n={int(stats_row['n'])}. Complete archive also in "
                f"{xlsx_path.name}.</p>"
                + excel_frame.to_html(index=False)
                + "<h2>Scales</h2>"
                + scale_df.to_html(index=False)
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
            scale_df=scale_df,
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
                "rho_q2_s20": stats_row["rho_q2_s20"],
                "rho_q2_s60": stats_row["rho_q2_s60"],
                "rho_q2_s100": stats_row["rho_q2_s100"],
                "rho_q4_s100": stats_row["rho_q4_s100"],
                "pearson_r": stats_row["pearson_r"],
                "docx": docx_path.name,
                "xlsx": xlsx_path.name,
                "html": html_path.name,
            }
        )
        print(
            f"Wrote {docx_path.name}  rho_q2_s100="
            f"{stats_row['rho_q2_s100']:.4f}  "
            f"rho_q4_s100={stats_row['rho_q4_s100']:.4f}  "
            f"n={int(stats_row['n'])}",
            flush=True,
        )

    index = pd.DataFrame(index_rows)
    index.to_excel(OUT_DIR / "index.xlsx", index=False, sheet_name="index")

    notes = [
        "# Multifractal DCCA experiments v001",
        "",
        "## Research question",
        "",
        "For each unordered pair among the eight majors, what is "
        "rho_q(s) of matched daily log returns of close at pre-specified "
        "q in {2, 4} and s in {20, 60, 100} on the Alpari D1 history?",
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
        f"- Scales: s in {list(SCALES)}; q in {list(QS)}; "
        f"headline q={int(HEADLINE_Q)}, s={HEADLINE_S}",
        f"- Trend degree={TREND_DEGREE}; overlap={OVERLAP}; positive q only; "
        "Pearson r as a side check",
        "- Outputs: 28 Word reports, 28 full-data HTML tables, 28 Excel "
        "workbooks (matched_rows + scales), charts under `outputs/figures/`",
        "",
        "## Index",
        "",
        "| pair | n | rho_q2_s20 | rho_q2_s60 | rho_q2_s100 | "
        "rho_q4_s100 | pearson_r |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in index_rows:
        notes.append(
            f"| {row['pair']} | {row['n']} | "
            f"{float(row['rho_q2_s20']):.6f} | "
            f"{float(row['rho_q2_s60']):.6f} | "
            f"{float(row['rho_q2_s100']):.6f} | "
            f"{float(row['rho_q4_s100']):.6f} | "
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
