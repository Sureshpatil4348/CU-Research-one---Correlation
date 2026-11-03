"""Mutual information on Alpari D1 majors: Word, HTML, and Excel per pair."""

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
N_BINS = 10
METHOD_NOTE = (
    "Mutual information I(X;Y) measures shared information between matched "
    "daily log returns of close, ln(close_t / close_t-1), after a fixed "
    "discretization. Quotes are not inverted. Each leg is cut into B=10 "
    "equal-frequency (decile) bins using that leg's matched-sample "
    "quantiles. Discrete MI uses natural log (nats): "
    "I = sum p_ab ln(p_ab / (p_a p_b)). Marginal entropies H_x and H_y "
    "and normalized MI = I / sqrt(H_x H_y) are stored for comparison. Bin "
    "count is not tuned after seeing pair rankings. Same-sample Pearson r "
    "is a side check only. This is not causation, lead-lag, or a trading "
    "signal."
)


def _mi_discrete(x_labels: np.ndarray, y_labels: np.ndarray) -> dict[str, float]:
    n = len(x_labels)
    if n == 0:
        return {
            "mi": float("nan"),
            "h_x": float("nan"),
            "h_y": float("nan"),
            "nmi": float("nan"),
        }
    joint = Counter(zip(x_labels.tolist(), y_labels.tolist()))
    px = Counter(x_labels.tolist())
    py = Counter(y_labels.tolist())
    mi = 0.0
    for (a, b), cab in joint.items():
        pab = cab / n
        pa = px[a] / n
        pb = py[b] / n
        mi += pab * math.log(pab / (pa * pb))
    h_x = 0.0
    for count in px.values():
        p = count / n
        h_x -= p * math.log(p)
    h_y = 0.0
    for count in py.values():
        p = count / n
        h_y -= p * math.log(p)
    denom = math.sqrt(h_x * h_y) if h_x > 0.0 and h_y > 0.0 else float("nan")
    nmi = mi / denom if denom and not math.isnan(denom) else float("nan")
    return {"mi": float(mi), "h_x": float(h_x), "h_y": float(h_y), "nmi": float(nmi)}


def _equal_frequency_labels(values: np.ndarray, n_bins: int = N_BINS) -> np.ndarray:
    """Assign decile labels 0..n_bins-1 using quantile edges on this sample."""
    # rank-based equal-frequency coding avoids duplicate-edge issues on ties
    ranks = stats.rankdata(values, method="average")
    # map ranks in [1, n] into n_bins nearly equal groups
    labels = np.floor((ranks - 1e-12) * n_bins / len(values)).astype(int)
    labels = np.clip(labels, 0, n_bins - 1)
    return labels


def _assert_guide_toys() -> None:
    teach_x = np.array([0, 0, 0, 1, 1, 1])
    teach_y = np.array([0, 0, 1, 0, 1, 1])
    mi = _mi_discrete(teach_x, teach_y)["mi"]
    # guide computes mi_discrete on these labels
    expected = 0.0
    n = 6
    joint = Counter(zip(teach_x.tolist(), teach_y.tolist()))
    px = Counter(teach_x.tolist())
    py = Counter(teach_y.tolist())
    for (a, b), cab in joint.items():
        pab = cab / n
        expected += pab * math.log(pab / ((px[a] / n) * (py[b] / n)))
    assert abs(mi - expected) < 1e-12
    assert mi > 0


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


def _mi_stats(table: pd.DataFrame, left: str, right: str) -> tuple[dict[str, float], pd.DataFrame]:
    out = table.copy()
    x = out[f"{left}_log_return"].to_numpy(dtype=float)
    y = out[f"{right}_log_return"].to_numpy(dtype=float)
    x_lab = _equal_frequency_labels(x, N_BINS)
    y_lab = _equal_frequency_labels(y, N_BINS)
    out[f"{left}_bin"] = x_lab
    out[f"{right}_bin"] = y_lab
    block = _mi_discrete(x_lab, y_lab)
    pearson_r = float(stats.pearsonr(x, y).statistic)
    stats_row = {
        "n": float(len(out)),
        "n_bins": float(N_BINS),
        "mi": block["mi"],
        "h_x": block["h_x"],
        "h_y": block["h_y"],
        "nmi": block["nmi"],
        "pearson_r": pearson_r,
    }
    return stats_row, out


def _joint_counts(x_lab: np.ndarray, y_lab: np.ndarray, n_bins: int = N_BINS) -> np.ndarray:
    counts = np.zeros((n_bins, n_bins), dtype=int)
    for a, b in zip(x_lab.tolist(), y_lab.tolist()):
        counts[a, b] += 1
    return counts


def _fmt(value: float, digits: int = 4) -> str:
    if math.isnan(value):
        return "n/a"
    return f"{value:.{digits}f}"


def _conclusion(left: str, right: str, stats_row: dict[str, float]) -> str:
    return (
        f"Over {int(stats_row['n'])} matched daily rows for {left} and {right} "
        f"with B={int(stats_row['n_bins'])} equal-frequency bins, I(X;Y) = "
        f"{_fmt(stats_row['mi'], 6)} nats "
        f"(normalized MI = {_fmt(stats_row['nmi'], 4)}; "
        f"H_x={_fmt(stats_row['h_x'], 4)}, H_y={_fmt(stats_row['h_y'], 4)}). "
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

    counts = _joint_counts(
        table[f"{left}_bin"].to_numpy(dtype=int),
        table[f"{right}_bin"].to_numpy(dtype=int),
    )
    fig, ax = plt.subplots(figsize=(5.8, 5.2))
    im = ax.imshow(counts, origin="lower", cmap="Blues", aspect="equal")
    ax.set_xlabel(f"{right} bin")
    ax.set_ylabel(f"{left} bin")
    ax.set_title(f"Joint bin counts: {left} vs {right}")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    paths["heatmap"] = FIG_DIR / f"{stem}_heatmap.png"
    fig.savefig(paths["heatmap"], dpi=120)
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

    _add_heading(doc, f"Mutual information: {left} and {right}", 0)
    _add_para(
        doc,
        "Method 15 / daily log returns / B=10 equal-frequency bins / "
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
        f"Discretization: B={int(stats_row['n_bins'])} equal-frequency bins per leg",
        "Units: nats (natural log)",
        f"Complete matched rows (Excel): {xlsx_name}",
        f"Complete matched rows (HTML table): {xlsx_name.replace('.xlsx', '_data.html')}",
    ):
        _add_para(doc, line)

    _add_heading(doc, "Method carried forward", 1)
    _add_para(doc, METHOD_NOTE)

    _add_heading(doc, "Results", 1)
    _add_para(doc, f"I(X;Y): {_fmt(stats_row['mi'], 6)} nats")
    _add_para(doc, f"Normalized MI: {_fmt(stats_row['nmi'], 6)}")
    _add_para(doc, f"H_x: {_fmt(stats_row['h_x'], 6)}")
    _add_para(doc, f"H_y: {_fmt(stats_row['h_y'], 6)}")
    _add_para(doc, f"Same-sample Pearson r: {_fmt(stats_row['pearson_r'], 6)}")

    _add_heading(doc, "Conclusion", 1)
    _add_para(doc, _conclusion(left, right, stats_row))

    _add_heading(doc, "Charts", 1)
    for key, title in (
        ("closes", "Daily closes"),
        ("returns", "Daily log returns"),
        ("heatmap", "Joint bin-count heatmap"),
    ):
        _add_para(doc, title, bold=True)
        doc.add_picture(str(fig_paths[key]), width=Inches(6.2))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

    _add_heading(doc, "Data report", 1)
    _add_para(
        doc,
        "Every matched row that entered MI is stored in the sibling Excel "
        f"workbook named {xlsx_name}, including bin labels. Embedding all "
        "rows as a Word table is impractical; this file holds column "
        "summaries and the first and last 15 matched rows.",
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
    by_nmi = sorted(index_rows, key=lambda row: float(row["nmi"]))
    strongest = by_nmi[-1]
    nearest = sorted(index_rows, key=lambda row: abs(float(row["nmi"])))[:3]
    return [
        "## Cross-pair conclusion",
        "",
        "Reading of the 28-pair index using normalized MI under the fixed "
        "B=10 equal-frequency rule. Not a 29th pair analysis and not a "
        "trading signal. Raw I and normalized MI share the same bins.",
        "",
        (
            f"Strongest normalized MI: {strongest['pair']} "
            f"(nmi={float(strongest['nmi']):.4f}, "
            f"I={float(strongest['mi']):.6f} nats, n={strongest['n']})."
        ),
        "Nearest-to-zero normalized MI: "
        + "; ".join(
            f"{row['pair']} (nmi={float(row['nmi']):.4f}, "
            f"I={float(row['mi']):.6f})"
            for row in nearest
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
        stats_row, table = _mi_stats(table, left, right)
        stem = f"{left}-{right}_MI_D1"
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
                f"<h1>{left} and {right}: matched rows used for mutual "
                f"information</h1>"
                f"<p>n={int(stats_row['n'])}. I={stats_row['mi']:.6f} nats. "
                f"nmi={stats_row['nmi']:.6f}. Complete archive also in "
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
                "n_bins": int(stats_row["n_bins"]),
                "mi": stats_row["mi"],
                "h_x": stats_row["h_x"],
                "h_y": stats_row["h_y"],
                "nmi": stats_row["nmi"],
                "pearson_r": stats_row["pearson_r"],
                "docx": docx_path.name,
                "xlsx": xlsx_path.name,
                "html": html_path.name,
            }
        )
        print(
            f"Wrote {docx_path.name}  I={stats_row['mi']:.6f}  "
            f"nmi={stats_row['nmi']:.4f}  n={int(stats_row['n'])}",
            flush=True,
        )

    index = pd.DataFrame(index_rows)
    index.to_excel(OUT_DIR / "index.xlsx", index=False, sheet_name="index")

    notes = [
        "# Mutual information experiments v001",
        "",
        "## Research question",
        "",
        "For each unordered pair among the eight majors, what is the "
        "discrete mutual information of matched daily log returns of close "
        "after a fixed B=10 equal-frequency binning on the Alpari D1 history?",
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
        f"- Discretization: B={N_BINS} equal-frequency bins per leg on the "
        "matched sample (fixed before ranking)",
        "- Statistic: discrete MI in nats; H_x, H_y; normalized MI = "
        "I/sqrt(H_x H_y); Pearson r as a side check",
        "- Outputs: 28 Word reports, 28 full-data HTML tables, 28 Excel "
        "workbooks, charts under `outputs/figures/` (closes, returns, "
        "joint heatmap)",
        "",
        "## Index",
        "",
        "| pair | n | n_bins | mi | h_x | h_y | nmi | pearson_r |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in index_rows:
        notes.append(
            f"| {row['pair']} | {row['n']} | {row['n_bins']} | "
            f"{float(row['mi']):.6f} | {float(row['h_x']):.6f} | "
            f"{float(row['h_y']):.6f} | {float(row['nmi']):.6f} | "
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
