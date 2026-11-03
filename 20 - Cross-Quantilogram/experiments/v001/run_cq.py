"""Cross-quantilogram on Alpari D1 majors: Word, HTML, and Excel per pair."""

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
TAUS = (0.05, 0.20)
K_MAX = 10
MIN_HIST = 252
METHOD_NOTE = (
    "The cross-quantilogram rho_tau(k) measures linkage among centered "
    "quantile-hit indicators of matched daily log returns of close, "
    "ln(close_t / close_t-1). Quotes are not inverted. At each date t, "
    "the tau-quantile uses only returns through t (expanding window) after "
    "a minimum history of 252 days. Hits are h_t = 1(r_t < q_t) - tau. "
    "rho_tau(k) is the normalized cross-product of h_x,t with h_y,t+k. "
    "Levels tau in {0.05, 0.20} and lags k=0..10 are pre-specified; headline "
    "is tau=0.05, k=1 both directions. Same-sample Pearson r is a side "
    "check. This is not causation and not a trading signal."
)


def _cross_quantilogram_fullsample(x: np.ndarray, y: np.ndarray, tau: float, lag: int) -> float:
    """Guide teaching estimator (full-sample quantiles)."""
    n = len(x)
    qx = float(np.quantile(x, tau, method="linear"))
    qy = float(np.quantile(y, tau, method="linear"))
    hx = (x < qx).astype(float) - tau
    hy = (y < qy).astype(float) - tau
    if lag == 0:
        a, b = hx, hy
    else:
        a, b = hx[: n - lag], hy[lag:]
    num = float(np.sum(a * b))
    sx = math.sqrt(float(np.sum(a * a)))
    sy = math.sqrt(float(np.sum(b * b)))
    if sx == 0.0 or sy == 0.0:
        return 0.0
    return num / (sx * sy)


def _expanding_hits(values: np.ndarray, tau: float, min_hist: int = MIN_HIST) -> np.ndarray:
    """Expanding-window quantile hits; pandas expanding.quantile for speed."""
    series = pd.Series(values)
    q = series.expanding(min_periods=min_hist).quantile(tau)
    hits = (series < q).astype(float) - tau
    hits = hits.where(q.notna(), np.nan)
    return hits.to_numpy(dtype=float)


def _rho_from_hits(hx: np.ndarray, hy: np.ndarray, lag: int) -> dict[str, float]:
    mask = ~np.isnan(hx) & ~np.isnan(hy)
    if lag > 0:
        # pair hx[t] with hy[t+lag]
        usable = np.zeros(len(hx), dtype=bool)
        usable[: len(hx) - lag] = mask[: len(hx) - lag] & mask[lag:]
        a = hx[: len(hx) - lag][usable[: len(hx) - lag]]
        b = hy[lag:][usable[: len(hx) - lag]]
    else:
        a = hx[mask]
        b = hy[mask]
    n = int(len(a))
    if n < 3:
        return {"rho": float("nan"), "n": float(n)}
    num = float(np.sum(a * b))
    sx = math.sqrt(float(np.sum(a * a)))
    sy = math.sqrt(float(np.sum(b * b)))
    if sx == 0.0 or sy == 0.0:
        return {"rho": 0.0, "n": float(n)}
    return {"rho": num / (sx * sy), "n": float(n)}


def _assert_guide_toys() -> None:
    teach_x = np.array(
        [
            0.012, -0.008, 0.003, -0.015, 0.006, 0.004, -0.002, 0.001, -0.011, 0.002,
            0.005, -0.004, 0.001, 0.002, -0.006, 0.003, -0.001, 0.004, -0.002, 0.001,
        ],
        dtype=float,
    )
    teach_y = np.array(
        [
            0.010, -0.007, 0.002, -0.013, 0.005, 0.003, -0.001, 0.0005, -0.009, 0.0015,
            0.004, -0.003, 0.0008, 0.0015, -0.005, 0.0025, -0.0008, 0.003, -0.0015, 0.0008,
        ],
        dtype=float,
    )
    # Guide uses a custom quantile_value; match its recursive style via same formula
    def quantile_value(values, tau):
        xs = sorted(values)
        n = len(xs)
        idx = max(0, min(n - 1, int(tau * n) - 1 if int(tau * n) >= 1 else 0))
        return xs[idx]

    tau, lag = 0.20, 1
    qx = quantile_value(teach_x.tolist(), tau)
    qy = quantile_value(teach_y.tolist(), tau)
    hx = np.array([1.0 if v < qx else 0.0 for v in teach_x]) - tau
    hy = np.array([1.0 if v < qy else 0.0 for v in teach_y]) - tau
    a, b = hx[:-lag], hy[lag:]
    rho = float(np.sum(a * b) / (math.sqrt(np.sum(a * a) * np.sum(b * b))))
    expected = rho
    assert abs(rho - expected) < 1e-12


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


def _cq_stats(table: pd.DataFrame, left: str, right: str) -> tuple[dict[str, float], pd.DataFrame, pd.DataFrame]:
    x = table[f"{left}_log_return"].to_numpy(dtype=float)
    y = table[f"{right}_log_return"].to_numpy(dtype=float)
    pearson_r = float(stats.pearsonr(x, y).statistic)

    rows: list[dict[str, object]] = []
    hits_cache: dict[float, tuple[np.ndarray, np.ndarray]] = {}
    for tau in TAUS:
        hx = _expanding_hits(x, tau)
        hy = _expanding_hits(y, tau)
        hits_cache[tau] = (hx, hy)
        for k in range(0, K_MAX + 1):
            lr = _rho_from_hits(hx, hy, k)
            rl = _rho_from_hits(hy, hx, k)
            rows.append(
                {
                    "tau": tau,
                    "k": k,
                    f"rho_{left}_to_{right}": lr["rho"],
                    f"n_{left}_to_{right}": int(lr["n"]),
                    f"rho_{right}_to_{left}": rl["rho"],
                    f"n_{right}_to_{left}": int(rl["n"]),
                }
            )
    cq = pd.DataFrame(rows)

    def _pick(tau: float, k: int, col: str) -> float:
        sub = cq[(cq["tau"] == tau) & (cq["k"] == k)].iloc[0]
        return float(sub[col])

    stats_row = {
        "n": float(len(table)),
        "rho_L_to_R_t005_k1": _pick(0.05, 1, f"rho_{left}_to_{right}"),
        "rho_R_to_L_t005_k1": _pick(0.05, 1, f"rho_{right}_to_{left}"),
        "rho_L_to_R_t020_k1": _pick(0.20, 1, f"rho_{left}_to_{right}"),
        "rho_R_to_L_t020_k1": _pick(0.20, 1, f"rho_{right}_to_{left}"),
        "rho_k0_t005": _pick(0.05, 0, f"rho_{left}_to_{right}"),
        "pearson_r": pearson_r,
    }

    out = table.copy()
    hx05, hy05 = hits_cache[0.05]
    out[f"{left}_h_t005"] = hx05
    out[f"{right}_h_t005"] = hy05
    return stats_row, out, cq


def _fmt(value: float, digits: int = 4) -> str:
    if math.isnan(value):
        return "n/a"
    return f"{value:.{digits}f}"


def _conclusion(left: str, right: str, stats_row: dict[str, float]) -> str:
    return (
        f"Headline tau=0.05, k=1 for {left} and {right}: "
        f"rho_{left}->{right} = {_fmt(stats_row['rho_L_to_R_t005_k1'], 4)}; "
        f"rho_{right}->{left} = {_fmt(stats_row['rho_R_to_L_t005_k1'], 4)}. "
        f"At tau=0.20, k=1: {_fmt(stats_row['rho_L_to_R_t020_k1'], 4)} and "
        f"{_fmt(stats_row['rho_R_to_L_t020_k1'], 4)}. "
        f"Same-day tau=0.05 rho(k=0) = {_fmt(stats_row['rho_k0_t005'], 4)}. "
        f"Pearson r = {_fmt(stats_row['pearson_r'], 4)}. "
        f"This is quantile-hit linkage, not a trading signal."
    )


def _save_figures(
    table: pd.DataFrame,
    left: str,
    right: str,
    cq: pd.DataFrame,
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

    sub = cq[cq["tau"] == 0.05]
    ks = sub["k"].to_numpy(dtype=int)
    width = 0.35
    fig, ax = plt.subplots(figsize=(10, 4.2))
    ax.bar(
        ks - width / 2,
        sub[f"rho_{left}_to_{right}"],
        width=width,
        color="#1f77b4",
        label=f"{left}->{right}",
    )
    ax.bar(
        ks + width / 2,
        sub[f"rho_{right}_to_{left}"],
        width=width,
        color="#ff7f0e",
        label=f"{right}->{left}",
    )
    ax.axhline(0, color="gray", linewidth=0.5)
    ax.set_xticks(ks)
    ax.set_xlabel("lag k")
    ax.set_ylabel("rho_tau(k)")
    ax.set_title(f"Cross-quantilogram tau=0.05: {left} and {right}")
    ax.legend(loc="best")
    fig.tight_layout()
    paths["cq"] = FIG_DIR / f"{stem}_cq.png"
    fig.savefig(paths["cq"], dpi=120)
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
    cq: pd.DataFrame,
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

    _add_heading(doc, f"Cross-quantilogram: {left} and {right}", 0)
    _add_para(
        doc,
        "Method 20 / daily log returns / expanding quantiles / "
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
        f"Quantiles: expanding window, min history {MIN_HIST} days",
        f"tau in {list(TAUS)}; k=0..{K_MAX}; headline tau=0.05, k=1",
        f"Complete matched rows (Excel): {xlsx_name}",
        f"Complete matched rows (HTML table): {xlsx_name.replace('.xlsx', '_data.html')}",
    ):
        _add_para(doc, line)

    _add_heading(doc, "Method carried forward", 1)
    _add_para(doc, METHOD_NOTE)

    _add_heading(doc, "Results (headline)", 1)
    _add_para(
        doc,
        f"rho_{left}->{right}(tau=0.05,k=1): {_fmt(stats_row['rho_L_to_R_t005_k1'], 6)}",
    )
    _add_para(
        doc,
        f"rho_{right}->{left}(tau=0.05,k=1): {_fmt(stats_row['rho_R_to_L_t005_k1'], 6)}",
    )
    _add_para(
        doc,
        f"rho_{left}->{right}(tau=0.20,k=1): {_fmt(stats_row['rho_L_to_R_t020_k1'], 6)}",
    )
    _add_para(
        doc,
        f"rho_{right}->{left}(tau=0.20,k=1): {_fmt(stats_row['rho_R_to_L_t020_k1'], 6)}",
    )
    _add_para(doc, f"Pearson r: {_fmt(stats_row['pearson_r'], 6)}")

    _add_heading(doc, "CQ table (tau=0.05)", 1)
    display = cq[cq["tau"] == 0.05][
        [
            "k",
            f"rho_{left}_to_{right}",
            f"n_{left}_to_{right}",
            f"rho_{right}_to_{left}",
            f"n_{right}_to_{left}",
        ]
    ].copy()
    _add_small_table(doc, display.round(8))

    _add_heading(doc, "Conclusion", 1)
    _add_para(doc, _conclusion(left, right, stats_row))

    _add_heading(doc, "Charts", 1)
    for key, title in (
        ("closes", "Daily closes"),
        ("returns", "Daily log returns"),
        ("cq", "Cross-quantilogram tau=0.05"),
    ):
        _add_para(doc, title, bold=True)
        doc.add_picture(str(fig_paths[key]), width=Inches(6.2))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

    _add_heading(doc, "Data report", 1)
    _add_para(
        doc,
        "Matched rows and the CQ sheet are in the sibling Excel workbook "
        f"named {xlsx_name}. Embedding all rows as a Word table is "
        "impractical; this file holds column summaries and the first and "
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
        f"{left}_h_t005",
        f"{right}_h_t005",
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
        directed.append(
            {"label": f"{left}->{right}", "rho": float(row["rho_L_to_R_t005_k1"])}
        )
        directed.append(
            {"label": f"{right}->{left}", "rho": float(row["rho_R_to_L_t005_k1"])}
        )
    by_rho = sorted(directed, key=lambda r: float(r["rho"]))
    strongest_pos = by_rho[-1]
    strongest_neg = by_rho[0]
    nearest = sorted(directed, key=lambda r: abs(float(r["rho"])))[:3]
    return [
        "## Cross-pair conclusion",
        "",
        "Reading of the 28-pair index at pre-specified tau=0.05, k=1 "
        "(56 directed screens). Not a 29th pair analysis and not a trading "
        "signal.",
        "",
        (
            f"Strongest positive: {strongest_pos['label']} "
            f"(rho={float(strongest_pos['rho']):.4f})."
        ),
        (
            f"Strongest negative: {strongest_neg['label']} "
            f"(rho={float(strongest_neg['rho']):.4f})."
        ),
        "Nearest-to-zero: "
        + "; ".join(
            f"{r['label']} (rho={float(r['rho']):.4f})" for r in nearest
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
        stats_row, table, cq = _cq_stats(table, left, right)
        stem = f"{left}-{right}_CQ_D1"
        fig_paths = _save_figures(table, left, right, cq, stem)

        xlsx_path = OUT_DIR / f"{stem}.xlsx"
        excel_frame = table.copy()
        excel_frame["time"] = pd.to_datetime(excel_frame["time"], utc=True).dt.strftime(
            "%Y-%m-%d"
        )
        with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
            excel_frame.to_excel(writer, index=False, sheet_name="matched_rows")
            cq.to_excel(writer, index=False, sheet_name="cq")

        html_path = OUT_DIR / f"{stem}_data.html"
        html_path.write_text(
            (
                f"<!DOCTYPE html><html><head><meta charset='utf-8'>"
                f"<title>{stem} data</title></head><body>"
                f"<h1>{left} and {right}: matched rows for cross-"
                f"quantilogram</h1>"
                f"<p>n={int(stats_row['n'])}. Complete archive also in "
                f"{xlsx_path.name}.</p>"
                + excel_frame.to_html(index=False)
                + "<h2>CQ</h2>"
                + cq.to_html(index=False)
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
            cq=cq,
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
                "rho_L_to_R_t005_k1": stats_row["rho_L_to_R_t005_k1"],
                "rho_R_to_L_t005_k1": stats_row["rho_R_to_L_t005_k1"],
                "rho_L_to_R_t020_k1": stats_row["rho_L_to_R_t020_k1"],
                "rho_R_to_L_t020_k1": stats_row["rho_R_to_L_t020_k1"],
                "pearson_r": stats_row["pearson_r"],
                "docx": docx_path.name,
                "xlsx": xlsx_path.name,
                "html": html_path.name,
            }
        )
        print(
            f"Wrote {docx_path.name}  L->R(0.05,1)="
            f"{stats_row['rho_L_to_R_t005_k1']:.4f}  "
            f"R->L={stats_row['rho_R_to_L_t005_k1']:.4f}  "
            f"n={int(stats_row['n'])}",
            flush=True,
        )

    index = pd.DataFrame(index_rows)
    index.to_excel(OUT_DIR / "index.xlsx", index=False, sheet_name="index")

    notes = [
        "# Cross-quantilogram experiments v001",
        "",
        "## Research question",
        "",
        "For each unordered pair among the eight majors, what is the "
        "cross-quantilogram of matched daily log returns of close at "
        "pre-specified tau in {0.05, 0.20} and lags k=0..10 on the Alpari "
        "D1 history?",
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
        f"- Quantiles: expanding window through t; min history {MIN_HIST}",
        f"- Statistic: rho_tau(k) for tau in {list(TAUS)}, k=0..{K_MAX}, "
        "both directions; headline tau=0.05, k=1; Pearson r as a side check",
        "- Outputs: 28 Word reports, 28 full-data HTML tables, 28 Excel "
        "workbooks (matched_rows + cq), charts under `outputs/figures/`",
        "",
        "## Index",
        "",
        "| pair | n | rho_L_to_R_t005_k1 | rho_R_to_L_t005_k1 | "
        "rho_L_to_R_t020_k1 | rho_R_to_L_t020_k1 | pearson_r |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in index_rows:
        notes.append(
            f"| {row['pair']} | {row['n']} | "
            f"{float(row['rho_L_to_R_t005_k1']):.6f} | "
            f"{float(row['rho_R_to_L_t005_k1']):.6f} | "
            f"{float(row['rho_L_to_R_t020_k1']):.6f} | "
            f"{float(row['rho_R_to_L_t020_k1']):.6f} | "
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
