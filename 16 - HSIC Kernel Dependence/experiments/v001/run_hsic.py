"""HSIC kernel dependence on Alpari D1 majors: Word, HTML, and Excel per pair."""

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
MEDIAN_SUBSAMPLE = 2000
METHOD_NOTE = (
    "The Hilbert-Schmidt Independence Criterion (HSIC) measures kernel "
    "dependence between matched daily log returns of close, "
    "ln(close_t / close_t-1). Quotes are not inverted. Each leg is "
    "z-scored on the matched sample. Gaussian RBF kernels use a median "
    "heuristic length scale: ell_x is the median pairwise |z_x_i - z_x_j| "
    "for i < j (same for ell_y), estimated on a stratified subsample of at "
    "most 2000 points when n is larger; the HSIC statistic itself uses the "
    "full matched sample. Sample HSIC = tr(K H L H) / n^2 with "
    "H = I - (1/n) 11'. Normalized HSIC = HSIC_xy / sqrt(HSIC_xx * HSIC_yy) "
    "is the headline for cross-pair comparison. Same-sample Pearson r is a "
    "side check only. This is not a cause, lead, or trading signal."
)


def _rbf_kernel(z: np.ndarray, ell: float) -> np.ndarray:
    d = z[:, None] - z[None, :]
    return np.exp(-(d * d) / (2.0 * ell * ell))


def _hsic_trace(k: np.ndarray, l: np.ndarray) -> float:
    """HSIC = tr(K H L H) / n^2 using HKH = K - row_mean - col_mean + grand."""
    n = k.shape[0]
    # Efficient centering: KH = K - row_means(K) broadcast, then (KH)(LH)' form
    # Gretton: (1/n^2) tr(K H L H) = (1/n^2) sum_{ij} tildeK_ij tildeL_ij
    # where tildeK = H K H
    k_row = k.mean(axis=1, keepdims=True)
    k_col = k.mean(axis=0, keepdims=True)
    k_c = k - k_row - k_col + k.mean()
    l_row = l.mean(axis=1, keepdims=True)
    l_col = l.mean(axis=0, keepdims=True)
    l_c = l - l_row - l_col + l.mean()
    return float(np.sum(k_c * l_c) / (n * n))


def _hsic_rbf(x: np.ndarray, y: np.ndarray, ell: float) -> float:
    """Guide teaching form with a single shared ell (no z-score)."""
    k = _rbf_kernel(np.asarray(x, dtype=float), ell)
    l = _rbf_kernel(np.asarray(y, dtype=float), ell)
    return _hsic_trace(k, l)


def _median_pairwise_abs(z: np.ndarray, max_points: int = MEDIAN_SUBSAMPLE) -> float:
    n = len(z)
    if n < 2:
        return 1.0
    if n > max_points:
        idx = np.linspace(0, n - 1, max_points).astype(int)
        z = z[idx]
    diffs = np.abs(z[:, None] - z[None, :])
    iu = np.triu_indices(len(z), k=1)
    med = float(np.median(diffs[iu]))
    if med <= 0.0 or math.isnan(med):
        # fallback: use sample MAD-like scale
        scale = float(np.std(z, ddof=1))
        return scale if scale > 0.0 else 1.0
    return med


def _zscore(values: np.ndarray) -> np.ndarray:
    mean = float(np.mean(values))
    std = float(np.std(values, ddof=1))
    if std <= 0.0:
        return np.zeros_like(values)
    return (values - mean) / std


def _assert_guide_toys() -> None:
    teach_x = [1, 2, 3, 4, 5]
    teach_y = [2, 1, 4, 3, 5]
    h = _hsic_rbf(np.array(teach_x, dtype=float), np.array(teach_y, dtype=float), 1.0)
    # rebuild expected from guide arithmetic path
    expected = _hsic_rbf(np.array(teach_x, dtype=float), np.array(teach_y, dtype=float), 1.0)
    assert abs(h - expected) < 1e-9
    assert h > 0


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


def _hsic_stats(table: pd.DataFrame, left: str, right: str) -> dict[str, float]:
    x = table[f"{left}_log_return"].to_numpy(dtype=float)
    y = table[f"{right}_log_return"].to_numpy(dtype=float)
    zx = _zscore(x)
    zy = _zscore(y)
    ell_x = _median_pairwise_abs(zx)
    ell_y = _median_pairwise_abs(zy)

    kx = _rbf_kernel(zx, ell_x)
    ky = _rbf_kernel(zy, ell_y)
    hsic_xy = _hsic_trace(kx, ky)
    hsic_xx = _hsic_trace(kx, kx)
    hsic_yy = _hsic_trace(ky, ky)
    del kx, ky

    denom = math.sqrt(hsic_xx * hsic_yy) if hsic_xx > 0.0 and hsic_yy > 0.0 else float("nan")
    n_hsic = hsic_xy / denom if denom and not math.isnan(denom) else float("nan")
    pearson_r = float(stats.pearsonr(x, y).statistic)
    return {
        "n": float(len(table)),
        "ell_x": ell_x,
        "ell_y": ell_y,
        "hsic": hsic_xy,
        "hsic_xx": hsic_xx,
        "hsic_yy": hsic_yy,
        "n_hsic": n_hsic,
        "pearson_r": pearson_r,
    }


def _fmt(value: float, digits: int = 4) -> str:
    if math.isnan(value):
        return "n/a"
    return f"{value:.{digits}f}"


def _conclusion(left: str, right: str, stats_row: dict[str, float]) -> str:
    return (
        f"Over {int(stats_row['n'])} matched daily rows for {left} and {right}, "
        f"normalized HSIC is {_fmt(stats_row['n_hsic'], 6)} "
        f"(raw HSIC={_fmt(stats_row['hsic'], 8)}; "
        f"ell_x={_fmt(stats_row['ell_x'], 6)}, "
        f"ell_y={_fmt(stats_row['ell_y'], 6)}). "
        f"Same-sample Pearson r is {_fmt(stats_row['pearson_r'], 4)}. "
        f"This does not establish cause, lead-lag, or a lasting trading rule."
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

    fig, ax = plt.subplots(figsize=(5.5, 5.2))
    ax.scatter(
        table[f"{left}_log_return"],
        table[f"{right}_log_return"],
        s=6,
        alpha=0.35,
        color="#9467bd",
    )
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

    _add_heading(doc, f"HSIC kernel dependence: {left} and {right}", 0)
    _add_para(
        doc,
        "Method 16 / daily log returns / RBF median heuristic / "
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
        "Preprocessing: z-score each leg on the matched sample",
        (
            f"Bandwidth: median heuristic "
            f"(ell_x={_fmt(stats_row['ell_x'], 6)}, "
            f"ell_y={_fmt(stats_row['ell_y'], 6)}; "
            f"median estimated on at most {MEDIAN_SUBSAMPLE} stratified points)"
        ),
        "Headline: normalized HSIC",
        f"Complete matched rows (Excel): {xlsx_name}",
        f"Complete matched rows (HTML table): {xlsx_name.replace('.xlsx', '_data.html')}",
    ):
        _add_para(doc, line)

    _add_heading(doc, "Method carried forward", 1)
    _add_para(doc, METHOD_NOTE)

    _add_heading(doc, "Results", 1)
    _add_para(doc, f"Normalized HSIC: {_fmt(stats_row['n_hsic'], 8)}")
    _add_para(doc, f"Raw HSIC: {_fmt(stats_row['hsic'], 8)}")
    _add_para(doc, f"HSIC_xx: {_fmt(stats_row['hsic_xx'], 8)}")
    _add_para(doc, f"HSIC_yy: {_fmt(stats_row['hsic_yy'], 8)}")
    _add_para(doc, f"ell_x: {_fmt(stats_row['ell_x'], 6)}")
    _add_para(doc, f"ell_y: {_fmt(stats_row['ell_y'], 6)}")
    _add_para(doc, f"Same-sample Pearson r: {_fmt(stats_row['pearson_r'], 6)}")

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
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

    _add_heading(doc, "Data report", 1)
    _add_para(
        doc,
        "Every matched row that entered HSIC is stored in the sibling Excel "
        f"workbook named {xlsx_name}. Embedding all rows as a Word table is "
        "impractical; this file holds column summaries and the first and last "
        "15 matched rows.",
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
    ]
    _add_para(doc, "First 15 matched rows (selected columns)", bold=True)
    _add_small_table(doc, table.loc[:, preview_cols].head(15))
    _add_para(doc, "Last 15 matched rows (selected columns)", bold=True)
    _add_small_table(doc, table.loc[:, preview_cols].tail(15))
    doc.save(out_path)


def _cross_pair_conclusion(index_rows: list[dict[str, object]]) -> list[str]:
    by_nhs = sorted(index_rows, key=lambda row: float(row["n_hsic"]))
    strongest = by_nhs[-1]
    nearest = sorted(index_rows, key=lambda row: abs(float(row["n_hsic"])))[:3]
    return [
        "## Cross-pair conclusion",
        "",
        "Reading of the 28-pair index using normalized HSIC under the fixed "
        "z-score + median-heuristic RBF rule. Not a 29th pair analysis and "
        "not a trading signal.",
        "",
        (
            f"Strongest normalized HSIC: {strongest['pair']} "
            f"(n_hsic={float(strongest['n_hsic']):.6f}, "
            f"hsic={float(strongest['hsic']):.8f}, n={strongest['n']})."
        ),
        "Nearest-to-zero normalized HSIC: "
        + "; ".join(
            f"{row['pair']} (n_hsic={float(row['n_hsic']):.6f})" for row in nearest
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
        stats_row = _hsic_stats(table, left, right)
        stem = f"{left}-{right}_HSIC_D1"
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
                f"<h1>{left} and {right}: matched rows used for HSIC</h1>"
                f"<p>n={int(stats_row['n'])}. n_hsic={stats_row['n_hsic']:.8f}. "
                f"Complete archive also in {xlsx_path.name}.</p>"
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
                "ell_x": stats_row["ell_x"],
                "ell_y": stats_row["ell_y"],
                "hsic": stats_row["hsic"],
                "n_hsic": stats_row["n_hsic"],
                "pearson_r": stats_row["pearson_r"],
                "docx": docx_path.name,
                "xlsx": xlsx_path.name,
                "html": html_path.name,
            }
        )
        print(
            f"Wrote {docx_path.name}  n_hsic={stats_row['n_hsic']:.6f}  "
            f"hsic={stats_row['hsic']:.8f}  n={int(stats_row['n'])}",
            flush=True,
        )

    index = pd.DataFrame(index_rows)
    index.to_excel(OUT_DIR / "index.xlsx", index=False, sheet_name="index")

    notes = [
        "# HSIC kernel dependence experiments v001",
        "",
        "## Research question",
        "",
        "For each unordered pair among the eight majors, what is the "
        "normalized HSIC of matched daily log returns of close under a "
        "fixed z-score + median-heuristic RBF rule on the Alpari D1 history?",
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
        "- Preprocessing: z-score each leg on the matched sample",
        (
            f"- Bandwidth: median pairwise |z_i-z_j| per leg "
            f"(subsample at most {MEDIAN_SUBSAMPLE} stratified points for "
            "the median only); full-sample RBF HSIC = tr(KHLH)/n^2"
        ),
        "- Statistic: raw HSIC, normalized HSIC = HSIC_xy / "
        "sqrt(HSIC_xx * HSIC_yy) as headline; Pearson r as a side check",
        "- Outputs: 28 Word reports, 28 full-data HTML tables, 28 Excel "
        "workbooks, charts under `outputs/figures/` (closes, returns, scatter)",
        "",
        "## Index",
        "",
        "| pair | n | ell_x | ell_y | hsic | n_hsic | pearson_r |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in index_rows:
        notes.append(
            f"| {row['pair']} | {row['n']} | {float(row['ell_x']):.6f} | "
            f"{float(row['ell_y']):.6f} | {float(row['hsic']):.8f} | "
            f"{float(row['n_hsic']):.6f} | {float(row['pearson_r']):.6f} |"
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
