"""Copulas on Alpari D1 majors: Word, HTML, and Excel per pair."""

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
from scipy import optimize, stats

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from shared.mt5_data import MAJOR_PAIRS, load_snapshot

SNAPSHOT_REL = Path("data/snapshots/2026-11-03_majors_alpari_D1")
EXP_DIR = Path(__file__).resolve().parent
OUT_DIR = EXP_DIR / "outputs"
FIG_DIR = OUT_DIR / "figures"
OHLCV = ["open", "high", "low", "close", "tick_volume", "spread", "real_volume"]
METHOD_NOTE = (
    "Copulas separate marginal return shapes from dependence on the unit "
    "square. Matched daily log returns of close, ln(close_t / close_t-1), "
    "are mapped to pseudo-observations u_i = rank(x_i)/(n+1) and "
    "v_i = rank(y_i)/(n+1). A Gaussian copula parameter rho is the Pearson "
    "correlation of Phi^{-1}(u) and Phi^{-1}(v). A Clayton copula theta >= 0 "
    "is fit by maximum likelihood on (u,v) for lower-tail asymmetry. Quotes "
    "are not inverted. Kendall tau implied by each fit and Spearman of "
    "(u,v) are stored. Same-sample Pearson r on returns is a side check. "
    "This is not causation and not a trading signal."
)


def _pseudo_obs(values: np.ndarray) -> np.ndarray:
    ranks = stats.rankdata(values, method="average")
    return ranks / (len(values) + 1.0)


def _gaussian_copula_rho(u: np.ndarray, v: np.ndarray) -> float:
    z_u = stats.norm.ppf(u)
    z_v = stats.norm.ppf(v)
    return float(np.corrcoef(z_u, z_v)[0, 1])


def _clayton_loglik(theta: float, u: np.ndarray, v: np.ndarray) -> float:
    if theta <= 0.0:
        # independence limit theta -> 0: density -> 1, loglik contribution 0
        return 0.0
    # c(u,v)=(1+theta)*(u*v)^(-(theta+1))*(u^{-theta}+v^{-theta}-1)^(-(2+1/theta))
    ut = np.power(u, -theta)
    vt = np.power(v, -theta)
    s = ut + vt - 1.0
    if np.any(s <= 0.0):
        return -1e12
    return float(
        np.sum(
            math.log(1.0 + theta)
            - (theta + 1.0) * (np.log(u) + np.log(v))
            - (2.0 + 1.0 / theta) * np.log(s)
        )
    )


def _clayton_mle(u: np.ndarray, v: np.ndarray) -> float:
    def objective(x: np.ndarray) -> float:
        return -_clayton_loglik(float(x[0]), u, v)

    best_theta = 0.0
    best_val = objective(np.array([1e-6]))
    for start in (0.1, 0.5, 1.0, 2.0, 5.0):
        res = optimize.minimize(
            objective,
            x0=np.array([start]),
            method="L-BFGS-B",
            bounds=[(1e-8, 20.0)],
        )
        if res.success and res.fun < best_val:
            best_val = float(res.fun)
            best_theta = float(res.x[0])
    return max(0.0, best_theta)


def _kendall_gaussian(rho: float) -> float:
    return float((2.0 / math.pi) * math.asin(rho))


def _kendall_clayton(theta: float) -> float:
    if theta <= 0.0:
        return 0.0
    return float(theta / (theta + 2.0))


def _assert_guide_toys() -> None:
    teach_x = np.array([-0.02, -0.01, 0.0, 0.01, 0.02])
    teach_y = np.array([-0.015, -0.005, 0.005, 0.012, 0.018])
    u = _pseudo_obs(teach_x)
    v = _pseudo_obs(teach_y)
    assert abs(u[2] - 0.5) < 0.05
    assert abs(v[2] - 0.5) < 0.05


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


def _copula_stats(table: pd.DataFrame, left: str, right: str) -> tuple[dict[str, float], pd.DataFrame]:
    out = table.copy()
    x = out[f"{left}_log_return"].to_numpy(dtype=float)
    y = out[f"{right}_log_return"].to_numpy(dtype=float)
    u = _pseudo_obs(x)
    v = _pseudo_obs(y)
    out["u"] = u
    out["v"] = v
    # clip slightly away from 0/1 for ppf / clayton
    u_c = np.clip(u, 1e-6, 1.0 - 1e-6)
    v_c = np.clip(v, 1e-6, 1.0 - 1e-6)
    gauss_rho = _gaussian_copula_rho(u_c, v_c)
    clayton_theta = _clayton_mle(u_c, v_c)
    spearman_uv = float(stats.spearmanr(u, v).statistic)
    pearson_r = float(stats.pearsonr(x, y).statistic)
    stats_row = {
        "n": float(len(out)),
        "gauss_rho": gauss_rho,
        "gauss_kendall": _kendall_gaussian(gauss_rho),
        "clayton_theta": clayton_theta,
        "clayton_kendall": _kendall_clayton(clayton_theta),
        "spearman_uv": spearman_uv,
        "pearson_r": pearson_r,
    }
    return stats_row, out


def _fmt(value: float, digits: int = 4) -> str:
    if math.isnan(value):
        return "n/a"
    return f"{value:.{digits}f}"


def _conclusion(left: str, right: str, stats_row: dict[str, float]) -> str:
    return (
        f"Over {int(stats_row['n'])} matched daily rows for {left} and {right}, "
        f"Gaussian copula rho = {_fmt(stats_row['gauss_rho'], 4)} "
        f"(Kendall={_fmt(stats_row['gauss_kendall'], 4)}) and Clayton "
        f"theta = {_fmt(stats_row['clayton_theta'], 4)} "
        f"(Kendall={_fmt(stats_row['clayton_kendall'], 4)}). "
        f"Spearman of (u,v) = {_fmt(stats_row['spearman_uv'], 4)}; "
        f"Pearson r on returns = {_fmt(stats_row['pearson_r'], 4)}. "
        f"This is not causation and not a trading signal."
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
    ax.scatter(table["u"], table["v"], s=6, alpha=0.35, color="#2ca02c")
    ax.set_xlabel(f"u ({left})")
    ax.set_ylabel(f"v ({right})")
    ax.set_title(f"Pseudo-observations: {left} vs {right}")
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

    _add_heading(doc, f"Copulas: {left} and {right}", 0)
    _add_para(
        doc,
        "Method 18 / daily log returns / empirical ranks / Gaussian + Clayton / "
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
        "Margins: empirical ranks / (n+1)",
        "Families: Gaussian (rho) and Clayton (theta), fixed before ranking",
        f"Complete matched rows (Excel): {xlsx_name}",
        f"Complete matched rows (HTML table): {xlsx_name.replace('.xlsx', '_data.html')}",
    ):
        _add_para(doc, line)

    _add_heading(doc, "Method carried forward", 1)
    _add_para(doc, METHOD_NOTE)

    _add_heading(doc, "Results", 1)
    _add_para(doc, f"Gaussian rho: {_fmt(stats_row['gauss_rho'], 6)}")
    _add_para(doc, f"Gaussian Kendall tau: {_fmt(stats_row['gauss_kendall'], 6)}")
    _add_para(doc, f"Clayton theta: {_fmt(stats_row['clayton_theta'], 6)}")
    _add_para(doc, f"Clayton Kendall tau: {_fmt(stats_row['clayton_kendall'], 6)}")
    _add_para(doc, f"Spearman of (u,v): {_fmt(stats_row['spearman_uv'], 6)}")
    _add_para(doc, f"Pearson r on returns: {_fmt(stats_row['pearson_r'], 6)}")

    _add_heading(doc, "Conclusion", 1)
    _add_para(doc, _conclusion(left, right, stats_row))

    _add_heading(doc, "Charts", 1)
    for key, title in (
        ("closes", "Daily closes"),
        ("returns", "Daily log returns"),
        ("uv", "Pseudo-observations (u,v)"),
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
    by_rho = sorted(index_rows, key=lambda r: float(r["gauss_rho"]))
    by_theta = sorted(index_rows, key=lambda r: float(r["clayton_theta"]))
    return [
        "## Cross-pair conclusion",
        "",
        "Reading of the 28-pair index only. Not a 29th pair analysis and not a "
        "trading signal.",
        "",
        (
            f"Strongest Gaussian rho: {by_rho[-1]['pair']} "
            f"(rho={float(by_rho[-1]['gauss_rho']):.4f})."
        ),
        (
            f"Weakest Gaussian rho: {by_rho[0]['pair']} "
            f"(rho={float(by_rho[0]['gauss_rho']):.4f})."
        ),
        (
            f"Largest Clayton theta (lower-tail screen): {by_theta[-1]['pair']} "
            f"(theta={float(by_theta[-1]['clayton_theta']):.4f})."
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
        stats_row, table = _copula_stats(table, left, right)
        stem = f"{left}-{right}_Copula_D1"
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
                f"<h1>{left} and {right}: matched rows used for copulas</h1>"
                f"<p>n={int(stats_row['n'])}. "
                f"gauss_rho={stats_row['gauss_rho']:.6f}. "
                f"clayton_theta={stats_row['clayton_theta']:.6f}. "
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
                "gauss_rho": stats_row["gauss_rho"],
                "gauss_kendall": stats_row["gauss_kendall"],
                "clayton_theta": stats_row["clayton_theta"],
                "clayton_kendall": stats_row["clayton_kendall"],
                "spearman_uv": stats_row["spearman_uv"],
                "pearson_r": stats_row["pearson_r"],
                "docx": docx_path.name,
                "xlsx": xlsx_path.name,
                "html": html_path.name,
            }
        )
        print(
            f"Wrote {docx_path.name}  rho={stats_row['gauss_rho']:.4f}  "
            f"theta={stats_row['clayton_theta']:.4f}  n={int(stats_row['n'])}",
            flush=True,
        )

    index = pd.DataFrame(index_rows)
    index.to_excel(OUT_DIR / "index.xlsx", index=False, sheet_name="index")

    notes = [
        "# Copulas experiments v001",
        "",
        "## Research question",
        "",
        "For each unordered pair among the eight majors, what Gaussian "
        "copula rho and Clayton theta describe the empirical-rank dependence "
        "of matched daily log returns of close on the Alpari D1 history?",
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
        "- Margins: empirical ranks / (n+1)",
        "- Families: Gaussian rho (normal-score correlation) and Clayton "
        "theta (MLE); Kendall tau from each; Spearman of (u,v); Pearson r "
        "on returns as a side check",
        "- Outputs: 28 Word reports, 28 full-data HTML tables, 28 Excel "
        "workbooks, charts under `outputs/figures/`",
        "",
        "## Index",
        "",
        "| pair | n | gauss_rho | gauss_kendall | clayton_theta | "
        "clayton_kendall | spearman_uv | pearson_r |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in index_rows:
        notes.append(
            f"| {row['pair']} | {row['n']} | {float(row['gauss_rho']):.6f} | "
            f"{float(row['gauss_kendall']):.6f} | "
            f"{float(row['clayton_theta']):.6f} | "
            f"{float(row['clayton_kendall']):.6f} | "
            f"{float(row['spearman_uv']):.6f} | "
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
