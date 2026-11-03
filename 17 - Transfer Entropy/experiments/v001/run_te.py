"""Transfer entropy on Alpari D1 majors: Word, HTML, and Excel per pair."""

from __future__ import annotations

import itertools
import math
import sys
from collections import Counter
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
N_BINS = 5
LAG = 1
METHOD_NOTE = (
    "Transfer entropy TE_X->Y asks whether the past of X adds information "
    "about the next value of Y beyond Y's own past. Matched daily log "
    "returns of close, ln(close_t / close_t-1), are discretized into B=5 "
    "equal-frequency bins per series on the matched sample. Lag orders "
    "k=m=1. TE = H(Y_{t+1}|Y_past) - H(Y_{t+1}|Y_past, X_past) in nats. "
    "Both directions are reported. Quotes are not inverted. Same-sample "
    "Pearson r is a side check only. TE is directed predictive information "
    "in this discrete model — not structural causation and not a trading "
    "signal."
)


def _equal_frequency_labels(values: np.ndarray, n_bins: int = N_BINS) -> np.ndarray:
    ranks = stats.rankdata(values, method="average")
    labels = np.floor((ranks - 1e-12) * n_bins / len(values)).astype(int)
    return np.clip(labels, 0, n_bins - 1)


def _cond_entropy(joint: Counter, marginal: Counter, n: int) -> float:
    h = 0.0
    for key, count in joint.items():
        # key is (yf, rest) where rest is past state
        yf, rest = key
        p = count / n
        px = marginal[rest] / n
        if px > 0 and p > 0:
            h -= p * math.log(p / px)
    return h


def _transfer_entropy(y_fut, y_past, x_past) -> float:
    triples = list(zip(y_fut, y_past, x_past))
    n = len(triples)
    if n < 2:
        return float("nan")
    joint_yf_yp = Counter((a, b) for a, b, _ in triples)
    marg_yp = Counter(b for _, b, _ in triples)
    h1 = _cond_entropy(joint_yf_yp, marg_yp, n)
    joint_yf_yp_xp = Counter((a, (b, c)) for a, b, c in triples)
    marg_yp_xp = Counter((b, c) for _, b, c in triples)
    h2 = _cond_entropy(joint_yf_yp_xp, marg_yp_xp, n)
    return float(h1 - h2)


def _assert_guide_toys() -> None:
    # Guide teaching table yields TE = 0 because Y_fut is a deterministic
    # flip of Y_past; X_past adds nothing.
    y_fut = [1, 0, 1, 0]
    y_past = [0, 1, 0, 1]
    x_past = [0, 0, 1, 1]
    te = _transfer_entropy(y_fut, y_past, x_past)
    assert abs(te) < 1e-12


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


def _te_stats(table: pd.DataFrame, left: str, right: str) -> tuple[dict[str, float], pd.DataFrame]:
    out = table.copy()
    x = out[f"{left}_log_return"].to_numpy(dtype=float)
    y = out[f"{right}_log_return"].to_numpy(dtype=float)
    x_lab = _equal_frequency_labels(x, N_BINS)
    y_lab = _equal_frequency_labels(y, N_BINS)
    out[f"{left}_bin"] = x_lab
    out[f"{right}_bin"] = y_lab

    # Align lag-1: rows t=1..n-1 use past at t-1 and future at t
    y_fut = y_lab[LAG:]
    y_past = y_lab[:-LAG]
    x_past = x_lab[:-LAG]
    x_fut = x_lab[LAG:]
    x_own_past = x_lab[:-LAG]
    y_as_x_past = y_lab[:-LAG]

    te_l_to_r = _transfer_entropy(y_fut, y_past, x_past)
    te_r_to_l = _transfer_entropy(x_fut, x_own_past, y_as_x_past)
    pearson_r = float(stats.pearsonr(x, y).statistic)
    stats_row = {
        "n": float(len(out)),
        "n_te": float(len(y_fut)),
        "n_bins": float(N_BINS),
        "lag": float(LAG),
        "te_L_to_R": te_l_to_r,
        "te_R_to_L": te_r_to_l,
        "pearson_r": pearson_r,
    }
    return stats_row, out


def _fmt(value: float, digits: int = 4) -> str:
    if math.isnan(value):
        return "n/a"
    return f"{value:.{digits}f}"


def _conclusion(left: str, right: str, stats_row: dict[str, float]) -> str:
    return (
        f"On {int(stats_row['n_te'])} lag-aligned rows for {left} and {right} "
        f"(B={int(stats_row['n_bins'])}, lag={int(stats_row['lag'])}), "
        f"TE_{left}->{right} = {_fmt(stats_row['te_L_to_R'], 6)} nats and "
        f"TE_{right}->{left} = {_fmt(stats_row['te_R_to_L'], 6)} nats. "
        f"Same-sample Pearson r is {_fmt(stats_row['pearson_r'], 4)}. "
        f"This is discrete predictive information, not economic cause and "
        f"not a trading signal."
    )


def _save_figures(
    table: pd.DataFrame,
    left: str,
    right: str,
    stats_row: dict[str, float],
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

    fig, ax = plt.subplots(figsize=(6.5, 4.2))
    labels = [f"{left}->{right}", f"{right}->{left}"]
    values = [stats_row["te_L_to_R"], stats_row["te_R_to_L"]]
    ax.bar(labels, values, color=["#1f77b4", "#ff7f0e"])
    ax.set_ylabel("TE (nats)")
    ax.set_title(f"Transfer entropy: {left} and {right}")
    fig.tight_layout()
    paths["te"] = FIG_DIR / f"{stem}_te.png"
    fig.savefig(paths["te"], dpi=120)
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

    _add_heading(doc, f"Transfer entropy: {left} and {right}", 0)
    _add_para(
        doc,
        "Method 17 / daily log returns / B=5 / lag=1 / Alpari D1 full available history",
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
        f"Lag-aligned TE rows n_te: {int(stats_row['n_te'])}",
        drop_note,
        f"Bins B={int(stats_row['n_bins'])}; lag k=m={int(stats_row['lag'])}",
        "Units: nats (natural log)",
        f"Complete matched rows (Excel): {xlsx_name}",
        f"Complete matched rows (HTML table): {xlsx_name.replace('.xlsx', '_data.html')}",
    ):
        _add_para(doc, line)

    _add_heading(doc, "Method carried forward", 1)
    _add_para(doc, METHOD_NOTE)

    _add_heading(doc, "Results", 1)
    _add_para(doc, f"TE_{left}->{right}: {_fmt(stats_row['te_L_to_R'], 6)} nats")
    _add_para(doc, f"TE_{right}->{left}: {_fmt(stats_row['te_R_to_L'], 6)} nats")
    _add_para(doc, f"Same-sample Pearson r: {_fmt(stats_row['pearson_r'], 6)}")

    _add_heading(doc, "Conclusion", 1)
    _add_para(doc, _conclusion(left, right, stats_row))

    _add_heading(doc, "Charts", 1)
    for key, title in (
        ("closes", "Daily closes"),
        ("returns", "Daily log returns"),
        ("te", "Transfer entropy both directions"),
    ):
        _add_para(doc, title, bold=True)
        doc.add_picture(str(fig_paths[key]), width=Inches(6.2))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

    _add_heading(doc, "Data report", 1)
    _add_para(
        doc,
        "Every matched row is stored in the sibling Excel workbook named "
        f"{xlsx_name}, including bin labels. Embedding all rows as a Word "
        "table is impractical; this file holds column summaries and the "
        "first and last 15 matched rows.",
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
        f"{left}_bin",
        f"{right}_bin",
    ]
    _add_para(doc, "First 15 matched rows (selected columns)", bold=True)
    _add_small_table(doc, table.loc[:, preview_cols].head(15))
    _add_para(doc, "Last 15 matched rows (selected columns)", bold=True)
    _add_small_table(doc, table.loc[:, preview_cols].tail(15))
    doc.save(out_path)


def _cross_pair_conclusion(index_rows: list[dict[str, object]]) -> list[str]:
    directed: list[dict[str, object]] = []
    for row in index_rows:
        pair = str(row["pair"])
        left, right = pair.split("-")
        directed.append({"label": f"{left}->{right}", "te": float(row["te_L_to_R"])})
        directed.append({"label": f"{right}->{left}", "te": float(row["te_R_to_L"])})
    by_te = sorted(directed, key=lambda r: float(r["te"]))
    strongest = by_te[-1]
    nearest = sorted(directed, key=lambda r: abs(float(r["te"])))[:3]
    return [
        "## Cross-pair conclusion",
        "",
        "Reading of the 28-pair index (56 directed TE scores). Not a 29th "
        "pair analysis and not a trading signal.",
        "",
        (
            f"Strongest directed TE: {strongest['label']} "
            f"(TE={float(strongest['te']):.6f} nats)."
        ),
        "Nearest-to-zero directed TE: "
        + "; ".join(f"{r['label']} (TE={float(r['te']):.6f})" for r in nearest)
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
        stats_row, table = _te_stats(table, left, right)
        stem = f"{left}-{right}_TE_D1"
        fig_paths = _save_figures(table, left, right, stats_row, stem)

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
                f"<h1>{left} and {right}: matched rows used for transfer "
                f"entropy</h1>"
                f"<p>n={int(stats_row['n'])}. "
                f"TE_L_to_R={stats_row['te_L_to_R']:.6f}. "
                f"TE_R_to_L={stats_row['te_R_to_L']:.6f}. "
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
                "n_te": int(stats_row["n_te"]),
                "te_L_to_R": stats_row["te_L_to_R"],
                "te_R_to_L": stats_row["te_R_to_L"],
                "pearson_r": stats_row["pearson_r"],
                "docx": docx_path.name,
                "xlsx": xlsx_path.name,
                "html": html_path.name,
            }
        )
        print(
            f"Wrote {docx_path.name}  L->R={stats_row['te_L_to_R']:.6f}  "
            f"R->L={stats_row['te_R_to_L']:.6f}  n={int(stats_row['n'])}",
            flush=True,
        )

    index = pd.DataFrame(index_rows)
    index.to_excel(OUT_DIR / "index.xlsx", index=False, sheet_name="index")

    notes = [
        "# Transfer entropy experiments v001",
        "",
        "## Research question",
        "",
        "For each unordered pair among the eight majors, does the past of "
        "one leg's binned daily log returns add information about the next "
        "bin of the other beyond own past, on the Alpari D1 history?",
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
        f"- Discretization: B={N_BINS} equal-frequency bins per leg; "
        f"lag k=m={LAG}",
        "- Statistic: discrete TE in nats both directions; Pearson r as a "
        "side check",
        "- Outputs: 28 Word reports, 28 full-data HTML tables, 28 Excel "
        "workbooks, charts under `outputs/figures/`",
        "",
        "## Index",
        "",
        "| pair | n | n_te | te_L_to_R | te_R_to_L | pearson_r |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in index_rows:
        notes.append(
            f"| {row['pair']} | {row['n']} | {row['n_te']} | "
            f"{float(row['te_L_to_R']):.6f} | {float(row['te_R_to_L']):.6f} | "
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
