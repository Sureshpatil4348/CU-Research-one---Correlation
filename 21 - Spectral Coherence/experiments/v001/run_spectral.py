"""Spectral coherence on Alpari D1 majors: Word, HTML, and Excel per pair."""

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
from scipy import signal, stats

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from shared.mt5_data import MAJOR_PAIRS, load_snapshot

SNAPSHOT_REL = Path("data/snapshots/2026-11-03_majors_alpari_D1")
EXP_DIR = Path(__file__).resolve().parent
OUT_DIR = EXP_DIR / "outputs"
FIG_DIR = OUT_DIR / "figures"
OHLCV = ["open", "high", "low", "close", "tick_volume", "spread", "real_volume"]
FS = 1.0
NPERSEG = 256
NOVERLAP = 128
WINDOW = "hann"
DETREND = "constant"
TARGET_PERIODS = (5, 21, 63)
HEADLINE_PERIOD = 5
METHOD_NOTE = (
    "Magnitude-squared spectral coherence gamma^2(f) measures shared linear "
    "power between matched daily log returns of close, ln(close_t / close_t-1), "
    "at each frequency f (cycles per day). Quotes are not inverted. Welch "
    "settings are frozen: fs=1, nperseg=256, noverlap=128, window=hann, "
    "detrend=constant. Headline is gamma^2 at the frequency bin nearest "
    "f=1/5 (five-day cycle from the formula sheet). Also reported: gamma^2 "
    "nearest f=1/21 and f=1/63, mean gamma^2 over the frequency grid, and "
    "phase of the cross-spectrum at the 1/5 bin. Coherence is unsigned "
    "(0 to 1); phase carries timing. Same-sample Pearson r is a side check "
    "only. This is not causation and not a trading signal."
)


def _nearest_bin(freqs: np.ndarray, target_f: float) -> int:
    return int(np.argmin(np.abs(freqs - target_f)))


def _assert_guide_toys() -> None:
    n_teach = 64
    t = np.arange(n_teach, dtype=float)
    freq = 0.2
    teach_x = 0.008 * np.sin(2 * np.pi * freq * t)
    teach_y = 0.006 * np.sin(2 * np.pi * freq * t + 0.3)
    f_grid, coh = signal.coherence(teach_x, teach_y, fs=1.0, nperseg=16)
    peak_coh = float(np.max(coh))
    peak_f = float(f_grid[int(np.argmax(coh))])
    assert 0.0 <= peak_coh <= 1.0 + 1e-9
    assert abs(peak_f - freq) < 0.15


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


def _spectral_stats(
    table: pd.DataFrame, left: str, right: str
) -> tuple[dict[str, float], pd.DataFrame]:
    x = table[f"{left}_log_return"].to_numpy(dtype=float)
    y = table[f"{right}_log_return"].to_numpy(dtype=float)
    pearson_r = float(stats.pearsonr(x, y).statistic)
    freqs, coh = signal.coherence(
        x,
        y,
        fs=FS,
        nperseg=NPERSEG,
        noverlap=NOVERLAP,
        window=WINDOW,
        detrend=DETREND,
    )
    _, csd = signal.csd(
        x,
        y,
        fs=FS,
        nperseg=NPERSEG,
        noverlap=NOVERLAP,
        window=WINDOW,
        detrend=DETREND,
    )
    curve = pd.DataFrame(
        {
            "f": freqs,
            "gamma2": coh,
            "phase_rad": np.angle(csd),
            "period_days": np.divide(
                1.0, freqs, out=np.full_like(freqs, np.inf), where=freqs > 0
            ),
        }
    )
    stats_row: dict[str, float] = {
        "n": float(len(table)),
        "pearson_r": pearson_r,
        "mean_gamma2": float(np.mean(coh)),
    }
    for period in TARGET_PERIODS:
        target_f = 1.0 / period
        idx = _nearest_bin(freqs, target_f)
        stats_row[f"gamma2_p{period}"] = float(coh[idx])
        stats_row[f"f_bin_p{period}"] = float(freqs[idx])
        stats_row[f"phase_p{period}"] = float(np.angle(csd[idx]))
    return stats_row, curve


def _fmt(value: float, digits: int = 4) -> str:
    if math.isnan(value):
        return "n/a"
    return f"{value:.{digits}f}"


def _conclusion(left: str, right: str, stats_row: dict[str, float]) -> str:
    return (
        f"Headline gamma^2 near f=1/{HEADLINE_PERIOD} for {left} and {right}: "
        f"{_fmt(stats_row['gamma2_p5'], 4)} (bin f={_fmt(stats_row['f_bin_p5'], 6)}, "
        f"phase={_fmt(stats_row['phase_p5'], 4)} rad). "
        f"At ~1/21: {_fmt(stats_row['gamma2_p21'], 4)}; "
        f"at ~1/63: {_fmt(stats_row['gamma2_p63'], 4)}. "
        f"Mean gamma^2 = {_fmt(stats_row['mean_gamma2'], 4)}. "
        f"Pearson r = {_fmt(stats_row['pearson_r'], 4)}. "
        f"This is frequency-domain linkage, not a trading signal."
    )


def _save_figures(
    table: pd.DataFrame,
    left: str,
    right: str,
    curve: pd.DataFrame,
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
    ax.plot(curve["f"], curve["gamma2"], color="#087F8C", linewidth=1.0)
    for period, color in zip(TARGET_PERIODS, ("#d62728", "#2ca02c", "#9467bd")):
        ax.axvline(1.0 / period, color=color, linestyle="--", linewidth=0.9, label=f"1/{period}")
    ax.set_ylim(0.0, 1.05)
    ax.set_xlabel("frequency f (cycles/day)")
    ax.set_ylabel("gamma^2(f)")
    ax.set_title(f"Spectral coherence: {left} and {right}")
    ax.legend(loc="best")
    fig.tight_layout()
    paths["coherence"] = FIG_DIR / f"{stem}_coherence.png"
    fig.savefig(paths["coherence"], dpi=120)
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
    curve: pd.DataFrame,
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

    _add_heading(doc, f"Spectral coherence: {left} and {right}", 0)
    _add_para(
        doc,
        "Method 21 / daily log returns / Welch magnitude-squared coherence / "
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
        f"Welch: fs={FS}, nperseg={NPERSEG}, noverlap={NOVERLAP}, "
        f"window={WINDOW}, detrend={DETREND}",
        "Headline: gamma^2 nearest f=1/5; also 1/21 and 1/63",
        f"Complete matched rows (Excel): {xlsx_name}",
        f"Complete matched rows (HTML table): {xlsx_name.replace('.xlsx', '_data.html')}",
    ):
        _add_para(doc, line)

    _add_heading(doc, "Method carried forward", 1)
    _add_para(doc, METHOD_NOTE)

    _add_heading(doc, "Results (headline)", 1)
    _add_para(doc, f"gamma^2 near 1/5: {_fmt(stats_row['gamma2_p5'], 6)}")
    _add_para(doc, f"bin f (1/5): {_fmt(stats_row['f_bin_p5'], 6)}")
    _add_para(doc, f"phase at 1/5 (rad): {_fmt(stats_row['phase_p5'], 6)}")
    _add_para(doc, f"gamma^2 near 1/21: {_fmt(stats_row['gamma2_p21'], 6)}")
    _add_para(doc, f"gamma^2 near 1/63: {_fmt(stats_row['gamma2_p63'], 6)}")
    _add_para(doc, f"mean gamma^2: {_fmt(stats_row['mean_gamma2'], 6)}")
    _add_para(doc, f"Pearson r: {_fmt(stats_row['pearson_r'], 6)}")

    _add_heading(doc, "Target-frequency summary", 1)
    summary = pd.DataFrame(
        [
            {
                "period": p,
                "target_f": 1.0 / p,
                "f_bin": stats_row[f"f_bin_p{p}"],
                "gamma2": stats_row[f"gamma2_p{p}"],
                "phase_rad": stats_row[f"phase_p{p}"],
            }
            for p in TARGET_PERIODS
        ]
    )
    _add_small_table(doc, summary.round(8))

    _add_heading(doc, "Conclusion", 1)
    _add_para(doc, _conclusion(left, right, stats_row))

    _add_heading(doc, "Charts", 1)
    for key, title in (
        ("closes", "Daily closes"),
        ("returns", "Daily log returns"),
        ("coherence", "Spectral coherence gamma^2(f)"),
    ):
        _add_para(doc, title, bold=True)
        doc.add_picture(str(fig_paths[key]), width=Inches(6.2))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

    _add_heading(doc, "Data report", 1)
    _add_para(
        doc,
        "Matched rows and the coherence sheet are in the sibling Excel workbook "
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
    _add_para(doc, "First 15 frequency bins", bold=True)
    _add_small_table(doc, curve.head(15).round(8))
    doc.save(out_path)


def _cross_pair_conclusion(index_rows: list[dict[str, object]]) -> list[str]:
    by_g = sorted(index_rows, key=lambda r: float(r["gamma2_p5"]))
    strongest = by_g[-1]
    nearest = sorted(index_rows, key=lambda r: abs(float(r["gamma2_p5"])))[:3]
    return [
        "## Cross-pair conclusion",
        "",
        "Reading of the 28-pair index at pre-specified gamma^2 nearest "
        "f=1/5. Not a 29th pair analysis and not a trading signal.",
        "",
        (
            f"Strongest gamma^2 near 1/5: {strongest['pair']} "
            f"(gamma2={float(strongest['gamma2_p5']):.4f})."
        ),
        "Nearest-to-zero gamma^2 near 1/5: "
        + "; ".join(
            f"{r['pair']} (gamma2={float(r['gamma2_p5']):.4f})" for r in nearest
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
        stats_row, curve = _spectral_stats(table, left, right)
        stem = f"{left}-{right}_Spectral_D1"
        fig_paths = _save_figures(table, left, right, curve, stem)

        xlsx_path = OUT_DIR / f"{stem}.xlsx"
        excel_frame = table.copy()
        excel_frame["time"] = pd.to_datetime(excel_frame["time"], utc=True).dt.strftime(
            "%Y-%m-%d"
        )
        with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
            excel_frame.to_excel(writer, index=False, sheet_name="matched_rows")
            curve.to_excel(writer, index=False, sheet_name="coherence")

        html_path = OUT_DIR / f"{stem}_data.html"
        html_path.write_text(
            (
                f"<!DOCTYPE html><html><head><meta charset='utf-8'>"
                f"<title>{stem} data</title></head><body>"
                f"<h1>{left} and {right}: matched rows for spectral "
                f"coherence</h1>"
                f"<p>n={int(stats_row['n'])}. Complete archive also in "
                f"{xlsx_path.name}.</p>"
                + excel_frame.to_html(index=False)
                + "<h2>Coherence curve</h2>"
                + curve.to_html(index=False)
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
            curve=curve,
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
                "gamma2_p5": stats_row["gamma2_p5"],
                "phase_p5": stats_row["phase_p5"],
                "gamma2_p21": stats_row["gamma2_p21"],
                "gamma2_p63": stats_row["gamma2_p63"],
                "mean_gamma2": stats_row["mean_gamma2"],
                "pearson_r": stats_row["pearson_r"],
                "docx": docx_path.name,
                "xlsx": xlsx_path.name,
                "html": html_path.name,
            }
        )
        print(
            f"Wrote {docx_path.name}  gamma2@1/5="
            f"{stats_row['gamma2_p5']:.4f}  "
            f"mean={stats_row['mean_gamma2']:.4f}  "
            f"n={int(stats_row['n'])}",
            flush=True,
        )

    index = pd.DataFrame(index_rows)
    index.to_excel(OUT_DIR / "index.xlsx", index=False, sheet_name="index")

    notes = [
        "# Spectral coherence experiments v001",
        "",
        "## Research question",
        "",
        "For each unordered pair among the eight majors, what is the "
        "Welch magnitude-squared coherence of matched daily log returns of "
        "close at pre-specified frequency bins nearest f in {1/5, 1/21, "
        "1/63} on the Alpari D1 history?",
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
        f"- Welch: fs={FS}, nperseg={NPERSEG}, noverlap={NOVERLAP}, "
        f"window={WINDOW}, detrend={DETREND}",
        "- Statistic: gamma^2 at bins nearest 1/5 (headline), 1/21, 1/63; "
        "mean gamma^2; phase at 1/5; Pearson r as a side check",
        "- Outputs: 28 Word reports, 28 full-data HTML tables, 28 Excel "
        "workbooks (matched_rows + coherence), charts under `outputs/figures/`",
        "",
        "## Index",
        "",
        "| pair | n | gamma2_p5 | phase_p5 | gamma2_p21 | gamma2_p63 | "
        "mean_gamma2 | pearson_r |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in index_rows:
        notes.append(
            f"| {row['pair']} | {row['n']} | "
            f"{float(row['gamma2_p5']):.6f} | "
            f"{float(row['phase_p5']):.6f} | "
            f"{float(row['gamma2_p21']):.6f} | "
            f"{float(row['gamma2_p63']):.6f} | "
            f"{float(row['mean_gamma2']):.6f} | "
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
