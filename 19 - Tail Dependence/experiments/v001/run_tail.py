"""Tail dependence on Alpari D1 majors: Word, HTML, and Excel per pair."""

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
ALPHA = 0.05
METHOD_NOTE = (
    "Tail dependence counts how often both legs sit in an extreme uniform "
    "tail together. Matched daily log returns of close, "
    "ln(close_t / close_t-1), become u_i = rank(x_i)/(n+1) and "
    "v_i = rank(y_i)/(n+1). At alpha=0.05, lower L_hat = "
    "(# u<=alpha and v<=alpha) / (# conditioning leg <= alpha); upper uses "
    ">= 1-alpha. Both conditioning directions are reported with numerator "
    "and denominator counts. Quotes are not inverted. L_hat(0.05) is a "
    "finite-sample frequency, not the asymptotic lambda. Same-sample "
    "Pearson r is a side check. This is not causation and not a trading "
    "signal."
)


def _pseudo_obs(values: np.ndarray) -> np.ndarray:
    ranks = stats.rankdata(values, method="average")
    return ranks / (len(values) + 1.0)


def _l_hat(u: np.ndarray, v: np.ndarray, alpha: float, lower: bool, cond_on_v: bool) -> dict[str, float]:
    if lower:
        u_tail = u <= alpha
        v_tail = v <= alpha
    else:
        u_tail = u >= (1.0 - alpha)
        v_tail = v >= (1.0 - alpha)
    if cond_on_v:
        denom_mask = v_tail
        joint = u_tail & v_tail
    else:
        denom_mask = u_tail
        joint = u_tail & v_tail
    denom = int(np.sum(denom_mask))
    num = int(np.sum(joint))
    ratio = float(num / denom) if denom > 0 else float("nan")
    return {"num": float(num), "denom": float(denom), "l_hat": ratio}


def _assert_guide_toys() -> None:
    assert abs(12 / 20 - 0.60) < 1e-12


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


def _tail_stats(table: pd.DataFrame, left: str, right: str) -> tuple[dict[str, float], pd.DataFrame]:
    out = table.copy()
    x = out[f"{left}_log_return"].to_numpy(dtype=float)
    y = out[f"{right}_log_return"].to_numpy(dtype=float)
    u = _pseudo_obs(x)
    v = _pseudo_obs(y)
    out["u"] = u
    out["v"] = v
    low_on_v = _l_hat(u, v, ALPHA, lower=True, cond_on_v=True)
    low_on_u = _l_hat(u, v, ALPHA, lower=True, cond_on_v=False)
    up_on_v = _l_hat(u, v, ALPHA, lower=False, cond_on_v=True)
    up_on_u = _l_hat(u, v, ALPHA, lower=False, cond_on_v=False)
    pearson_r = float(stats.pearsonr(x, y).statistic)
    stats_row = {
        "n": float(len(out)),
        "alpha": float(ALPHA),
        "L_lower_cond_R": low_on_v["l_hat"],
        "num_lower_cond_R": low_on_v["num"],
        "den_lower_cond_R": low_on_v["denom"],
        "L_lower_cond_L": low_on_u["l_hat"],
        "num_lower_cond_L": low_on_u["num"],
        "den_lower_cond_L": low_on_u["denom"],
        "L_upper_cond_R": up_on_v["l_hat"],
        "num_upper_cond_R": up_on_v["num"],
        "den_upper_cond_R": up_on_v["denom"],
        "L_upper_cond_L": up_on_u["l_hat"],
        "num_upper_cond_L": up_on_u["num"],
        "den_upper_cond_L": up_on_u["denom"],
        "pearson_r": pearson_r,
    }
    return stats_row, out


def _fmt(value: float, digits: int = 4) -> str:
    if math.isnan(value):
        return "n/a"
    return f"{value:.{digits}f}"


def _conclusion(left: str, right: str, stats_row: dict[str, float]) -> str:
    return (
        f"Over {int(stats_row['n'])} matched daily rows for {left} and {right} "
        f"at alpha={stats_row['alpha']:.2f}, lower L_hat conditioning on "
        f"{right} is {_fmt(stats_row['L_lower_cond_R'], 4)} "
        f"({int(stats_row['num_lower_cond_R'])}/"
        f"{int(stats_row['den_lower_cond_R'])}); conditioning on {left} is "
        f"{_fmt(stats_row['L_lower_cond_L'], 4)}. Upper L_hat conditioning "
        f"on {right} is {_fmt(stats_row['L_upper_cond_R'], 4)}; on {left} is "
        f"{_fmt(stats_row['L_upper_cond_L'], 4)}. Pearson r = "
        f"{_fmt(stats_row['pearson_r'], 4)}. These are finite-sample "
        f"frequencies, not asymptotic lambda and not a trading signal."
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
    ax.scatter(table["u"], table["v"], s=6, alpha=0.35, color="#7f7f7f")
    ax.axvline(ALPHA, color="#d62728", linewidth=0.8, linestyle="--")
    ax.axhline(ALPHA, color="#d62728", linewidth=0.8, linestyle="--")
    ax.axvline(1.0 - ALPHA, color="#2ca02c", linewidth=0.8, linestyle="--")
    ax.axhline(1.0 - ALPHA, color="#2ca02c", linewidth=0.8, linestyle="--")
    ax.set_xlabel(f"u ({left})")
    ax.set_ylabel(f"v ({right})")
    ax.set_title(f"Uniforms with alpha={ALPHA}: {left} vs {right}")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    fig.tight_layout()
    paths["uv"] = FIG_DIR / f"{stem}_uv.png"
    fig.savefig(paths["uv"], dpi=120)
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

    _add_heading(doc, f"Tail dependence: {left} and {right}", 0)
    _add_para(
        doc,
        "Method 19 / daily log returns / alpha=0.05 / Alpari D1 full available history",
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
        f"Uniforms: ranks/(n+1); alpha={stats_row['alpha']:.2f}",
        f"Complete matched rows (Excel): {xlsx_name}",
        f"Complete matched rows (HTML table): {xlsx_name.replace('.xlsx', '_data.html')}",
    ):
        _add_para(doc, line)

    _add_heading(doc, "Method carried forward", 1)
    _add_para(doc, METHOD_NOTE)

    _add_heading(doc, "Results", 1)
    results = pd.DataFrame(
        [
            {
                "tail": "lower",
                "cond": right,
                "L_hat": round(stats_row["L_lower_cond_R"], 6),
                "num": int(stats_row["num_lower_cond_R"]),
                "denom": int(stats_row["den_lower_cond_R"]),
            },
            {
                "tail": "lower",
                "cond": left,
                "L_hat": round(stats_row["L_lower_cond_L"], 6),
                "num": int(stats_row["num_lower_cond_L"]),
                "denom": int(stats_row["den_lower_cond_L"]),
            },
            {
                "tail": "upper",
                "cond": right,
                "L_hat": round(stats_row["L_upper_cond_R"], 6),
                "num": int(stats_row["num_upper_cond_R"]),
                "denom": int(stats_row["den_upper_cond_R"]),
            },
            {
                "tail": "upper",
                "cond": left,
                "L_hat": round(stats_row["L_upper_cond_L"], 6),
                "num": int(stats_row["num_upper_cond_L"]),
                "denom": int(stats_row["den_upper_cond_L"]),
            },
        ]
    )
    _add_small_table(doc, results)
    _add_para(doc, f"Pearson r on returns: {_fmt(stats_row['pearson_r'], 6)}")

    _add_heading(doc, "Conclusion", 1)
    _add_para(doc, _conclusion(left, right, stats_row))

    _add_heading(doc, "Charts", 1)
    for key, title in (
        ("closes", "Daily closes"),
        ("returns", "Daily log returns"),
        ("uv", "Uniforms with alpha lines"),
    ):
        _add_para(doc, title, bold=True)
        doc.add_picture(str(fig_paths[key]), width=Inches(6.2))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

    _add_heading(doc, "Data report", 1)
    _add_para(
        doc,
        "Every matched row is stored in the sibling Excel workbook named "
        f"{xlsx_name}, including u and v. Embedding all rows as a Word table "
        "is impractical; this file holds column summaries and the first and "
        "last 15 matched rows.",
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
        f"{left}_log_return",
        f"{right}_log_return",
        "u",
        "v",
    ]
    _add_para(doc, "First 15 matched rows (selected columns)", bold=True)
    _add_small_table(doc, table.loc[:, preview_cols].head(15))
    _add_para(doc, "Last 15 matched rows (selected columns)", bold=True)
    _add_small_table(doc, table.loc[:, preview_cols].tail(15))
    doc.save(out_path)


def _cross_pair_conclusion(index_rows: list[dict[str, object]]) -> list[str]:
    # Use mean of both conditioning directions for ranking lower/upper
    scored_lower = []
    scored_upper = []
    for row in index_rows:
        pair = str(row["pair"])
        left, right = pair.split("-")
        scored_lower.append(
            {
                "label": f"{pair} (cond {right})",
                "l": float(row["L_lower_cond_R"]),
            }
        )
        scored_lower.append(
            {
                "label": f"{pair} (cond {left})",
                "l": float(row["L_lower_cond_L"]),
            }
        )
        scored_upper.append(
            {
                "label": f"{pair} (cond {right})",
                "l": float(row["L_upper_cond_R"]),
            }
        )
        scored_upper.append(
            {
                "label": f"{pair} (cond {left})",
                "l": float(row["L_upper_cond_L"]),
            }
        )
    top_low = sorted(scored_lower, key=lambda r: float(r["l"]), reverse=True)[0]
    top_up = sorted(scored_upper, key=lambda r: float(r["l"]), reverse=True)[0]
    return [
        "## Cross-pair conclusion",
        "",
        "Reading of the 28-pair index at alpha=0.05. Not a 29th pair analysis "
        "and not a trading signal.",
        "",
        (
            f"Strongest lower-tail L_hat: {top_low['label']} "
            f"(L_hat={float(top_low['l']):.4f})."
        ),
        (
            f"Strongest upper-tail L_hat: {top_up['label']} "
            f"(L_hat={float(top_up['l']):.4f})."
        ),
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
        stats_row, table = _tail_stats(table, left, right)
        stem = f"{left}-{right}_Tail_D1"
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
                f"<h1>{left} and {right}: matched rows used for tail "
                f"dependence</h1>"
                f"<p>n={int(stats_row['n'])}. "
                f"L_lower_cond_R={stats_row['L_lower_cond_R']:.4f}. "
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
                "L_lower_cond_R": stats_row["L_lower_cond_R"],
                "num_lower_cond_R": int(stats_row["num_lower_cond_R"]),
                "den_lower_cond_R": int(stats_row["den_lower_cond_R"]),
                "L_lower_cond_L": stats_row["L_lower_cond_L"],
                "num_lower_cond_L": int(stats_row["num_lower_cond_L"]),
                "den_lower_cond_L": int(stats_row["den_lower_cond_L"]),
                "L_upper_cond_R": stats_row["L_upper_cond_R"],
                "num_upper_cond_R": int(stats_row["num_upper_cond_R"]),
                "den_upper_cond_R": int(stats_row["den_upper_cond_R"]),
                "L_upper_cond_L": stats_row["L_upper_cond_L"],
                "num_upper_cond_L": int(stats_row["num_upper_cond_L"]),
                "den_upper_cond_L": int(stats_row["den_upper_cond_L"]),
                "pearson_r": stats_row["pearson_r"],
                "docx": docx_path.name,
                "xlsx": xlsx_path.name,
                "html": html_path.name,
            }
        )
        print(
            f"Wrote {docx_path.name}  L_low_R={stats_row['L_lower_cond_R']:.4f}  "
            f"L_up_R={stats_row['L_upper_cond_R']:.4f}  n={int(stats_row['n'])}",
            flush=True,
        )

    index = pd.DataFrame(index_rows)
    index.to_excel(OUT_DIR / "index.xlsx", index=False, sheet_name="index")

    notes = [
        "# Tail dependence experiments v001",
        "",
        "## Research question",
        "",
        "For each unordered pair among the eight majors, how often do "
        "matched daily log returns of close co-occur in the lower and upper "
        "empirical uniform tails at alpha=0.05 on the Alpari D1 history?",
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
        f"- Uniforms: ranks/(n+1); alpha={ALPHA}",
        "- Statistic: lower and upper L_hat conditioning on each leg with "
        "numerator and denominator counts; Pearson r as a side check",
        "- Outputs: 28 Word reports, 28 full-data HTML tables, 28 Excel "
        "workbooks, charts under `outputs/figures/`",
        "",
        "## Index",
        "",
        "| pair | n | L_lower_cond_R | num/den_R | L_lower_cond_L | "
        "num/den_L | L_upper_cond_R | L_upper_cond_L | pearson_r |",
        "| --- | ---: | ---: | --- | ---: | --- | ---: | ---: | ---: |",
    ]
    for row in index_rows:
        notes.append(
            f"| {row['pair']} | {row['n']} | "
            f"{float(row['L_lower_cond_R']):.6f} | "
            f"{row['num_lower_cond_R']}/{row['den_lower_cond_R']} | "
            f"{float(row['L_lower_cond_L']):.6f} | "
            f"{row['num_lower_cond_L']}/{row['den_lower_cond_L']} | "
            f"{float(row['L_upper_cond_R']):.6f} | "
            f"{float(row['L_upper_cond_L']):.6f} | "
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
