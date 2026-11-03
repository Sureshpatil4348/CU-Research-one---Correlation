"""Engle-Granger cointegration and ECM on Alpari D1 majors: Word, HTML, Excel."""

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
import statsmodels.api as sm
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt
from scipy import stats
from statsmodels.tsa.stattools import coint

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from shared.mt5_data import MAJOR_PAIRS, load_snapshot

SNAPSHOT_REL = Path("data/snapshots/2026-11-03_majors_alpari_D1")
EXP_DIR = Path(__file__).resolve().parent
OUT_DIR = EXP_DIR / "outputs"
FIG_DIR = OUT_DIR / "figures"
OHLCV = ["open", "high", "low", "close", "tick_volume", "spread", "real_volume"]
ECM_LAGS = 1
METHOD_NOTE = (
    "Engle-Granger cointegration works on log price levels, not returns. "
    "For each unordered pair, PX is the left leg and PY the right leg. "
    "Step one: OLS ln(PY) = alpha + beta * ln(PX) + e. Step two: "
    "statsmodels Engle-Granger coint test on (ln(PY), ln(PX)). "
    "Error-correction: delta ln(PY)_t = c + kappa * e_{t-1} + "
    "lagged delta ln(PY) and delta ln(PX) (one lag each) + u_t. "
    "Headline is the Engle-Granger p-value (lower = stronger evidence of "
    "a stationary spread) with kappa and beta reported alongside. "
    "Same-sample Pearson r of log returns is a side check only. "
    "beta is not an automatic lot-size hedge. This is not a trading signal."
)


def _assert_guide_toys() -> None:
    alpha, beta = 0.050, 1.100
    px = [1.1000, 1.1110, 1.1050]
    py = [1.2500, 1.2625, 1.2580]
    ln_px = [math.log(p) for p in px]
    ln_py = [math.log(p) for p in py]
    spread = [lpy - alpha - beta * lpx for lpy, lpx in zip(ln_py, ln_px)]
    c_ecm, kappa = 0.001, -0.35
    pred = c_ecm + kappa * spread[0]
    assert abs(spread[0] - (ln_py[0] - alpha - beta * ln_px[0])) < 1e-12
    assert abs(pred - (0.001 - 0.35 * spread[0])) < 1e-12


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
        work["log_price"] = np.log(work["close"])
        work["log_return"] = work["log_price"].diff()
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
    for col in OHLCV + ["log_price", "log_return"]:
        cols[f"{left_name}_{col}"] = a.loc[common, col]
        cols[f"{right_name}_{col}"] = b.loc[common, col]
    table = pd.DataFrame(cols)
    table = table.dropna(
        subset=[
            f"{left_name}_log_price",
            f"{right_name}_log_price",
            f"{left_name}_log_return",
            f"{right_name}_log_return",
        ]
    )
    return table.reset_index(drop=True)


def _coint_stats(
    table: pd.DataFrame, left: str, right: str
) -> tuple[dict[str, float], pd.DataFrame]:
    """PX=left, PY=right. Engle-Granger + one-lag ECM."""
    ln_x = table[f"{left}_log_price"].to_numpy(dtype=float)
    ln_y = table[f"{right}_log_price"].to_numpy(dtype=float)
    rx = table[f"{left}_log_return"].to_numpy(dtype=float)
    ry = table[f"{right}_log_return"].to_numpy(dtype=float)
    pearson_r = float(stats.pearsonr(rx, ry).statistic)

    x_design = sm.add_constant(ln_x)
    ols = sm.OLS(ln_y, x_design).fit()
    alpha = float(ols.params[0])
    beta = float(ols.params[1])
    resid = ln_y - alpha - beta * ln_x

    coint_t, coint_p, crit = coint(ln_y, ln_x, trend="c", autolag="aic")
    # ECM: dY_t = c + kappa e_{t-1} + a1 dY_{t-1} + b1 dX_{t-1}
    e_lag = resid[:-1]
    dy = ry[1:]
    dy_lag = ry[:-1]
    dx_lag = rx[:-1]
    # align: e_lag[t] is e at index t (0..n-2), dy[t] is return at index t+1
    # drop first of dy_lag/dx_lag mismatch: use rows where all available
    # e_lag length n-1; dy length n-1 from ry[1:]; for lag of deltas need from index 1
    # Standard: for t=1..n-1: dy_t, e_{t-1}, dy_{t-1}, dx_{t-1}
    # indices in original: t from 1 to n-1
    # e_{t-1} = resid[t-1], dy_t = ry[t], dy_{t-1}=ry[t-1], dx_{t-1}=rx[t-1]
    ecm_y = ry[1:]
    ecm_e = resid[:-1]
    ecm_dy_lag = ry[:-1]
    ecm_dx_lag = rx[:-1]
    # For lag terms at first ECM row (t=1), dy_lag and dx_lag are ry[0], rx[0] — OK
    # But typically we need t starting at 2 if we want lag of delta from t-1 when t starts at 1...
    # With ECM_LAGS=1: use observations from t=1..n-1 with e_{t-1}, dy_{t-1}, dx_{t-1}
    ecm_x = np.column_stack(
        [
            np.ones(len(ecm_y)),
            ecm_e,
            ecm_dy_lag,
            ecm_dx_lag,
        ]
    )
    ecm = sm.OLS(ecm_y, ecm_x).fit()
    kappa = float(ecm.params[1])
    kappa_se = float(ecm.bse[1])
    kappa_t = float(ecm.tvalues[1])

    work = table.copy()
    work["spread_e"] = resid
    work["ecm_fitted"] = np.nan
    # fitted for t>=1
    fitted = ecm.predict(ecm_x)
    work.loc[work.index[1:], "ecm_fitted"] = fitted

    stats_row = {
        "n": float(len(table)),
        "alpha": alpha,
        "beta": beta,
        "coint_t": float(coint_t),
        "coint_p": float(coint_p),
        "crit_5pct": float(crit[1]),
        "kappa": kappa,
        "kappa_se": kappa_se,
        "kappa_t": kappa_t,
        "ecm_r2": float(ecm.rsquared),
        "pearson_r": pearson_r,
        "spread_std": float(np.std(resid, ddof=1)),
    }
    return stats_row, work


def _fmt(value: float, digits: int = 4) -> str:
    if math.isnan(value):
        return "n/a"
    return f"{value:.{digits}f}"


def _conclusion(left: str, right: str, stats_row: dict[str, float]) -> str:
    return (
        f"Engle-Granger for PY={right} on PX={left}: "
        f"beta={_fmt(stats_row['beta'], 4)}, alpha={_fmt(stats_row['alpha'], 4)}, "
        f"coint_t={_fmt(stats_row['coint_t'], 4)}, "
        f"p={_fmt(stats_row['coint_p'], 4)} "
        f"(5% crit={_fmt(stats_row['crit_5pct'], 4)}). "
        f"ECM kappa={_fmt(stats_row['kappa'], 4)} "
        f"(t={_fmt(stats_row['kappa_t'], 2)}). "
        f"Pearson r of returns = {_fmt(stats_row['pearson_r'], 4)}. "
        f"beta is not a lot-size hedge. Not a trading signal."
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
    ax.plot(times, table["spread_e"], color="#087F8C", linewidth=0.7)
    ax.axhline(0, color="gray", linewidth=0.5)
    ax.set_title(f"Engle-Granger spread e_t: {right} on {left}")
    ax.set_ylabel("e_t")
    fig.tight_layout()
    paths["spread"] = FIG_DIR / f"{stem}_spread.png"
    fig.savefig(paths["spread"], dpi=120)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 4.2))
    ax.plot(times, table[f"{left}_log_return"], color="#1f77b4", linewidth=0.5, label=left)
    ax.plot(times, table[f"{right}_log_return"], color="#ff7f0e", linewidth=0.5, label=right)
    ax.set_title(f"Log returns: {left} and {right}")
    ax.legend(loc="upper left")
    fig.tight_layout()
    paths["returns"] = FIG_DIR / f"{stem}_returns.png"
    fig.savefig(paths["returns"], dpi=120)
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

    _add_heading(doc, f"Cointegration and ECM: {left} and {right}", 0)
    _add_para(
        doc,
        "Method 27 / Engle-Granger on log closes / one-lag ECM / "
        "Alpari D1 full available history",
    )

    _add_heading(doc, "Study setup", 1)
    first = pd.to_datetime(table["time"].iloc[0], utc=True).date().isoformat()
    last = pd.to_datetime(table["time"].iloc[-1], utc=True).date().isoformat()
    for line in (
        f"Logical pair: PX={left} , PY={right}",
        f"Broker symbols: {left_broker} , {right_broker}",
        f"Snapshot: {snapshot_name}",
        "Timeframe: D1",
        f"Matched window: {first} to {last} (UTC bar dates)",
        f"Matched level count n: {int(stats_row['n'])}",
        drop_note,
        f"ECM lags of deltas: {ECM_LAGS}",
        f"Complete matched rows (Excel): {xlsx_name}",
        f"Complete matched rows (HTML table): {xlsx_name.replace('.xlsx', '_data.html')}",
    ):
        _add_para(doc, line)

    _add_heading(doc, "Method carried forward", 1)
    _add_para(doc, METHOD_NOTE)

    _add_heading(doc, "Results (headline)", 1)
    _add_para(doc, f"alpha: {_fmt(stats_row['alpha'], 6)}")
    _add_para(doc, f"beta: {_fmt(stats_row['beta'], 6)}")
    _add_para(doc, f"Engle-Granger t: {_fmt(stats_row['coint_t'], 6)}")
    _add_para(doc, f"Engle-Granger p: {_fmt(stats_row['coint_p'], 6)}")
    _add_para(doc, f"5% critical value: {_fmt(stats_row['crit_5pct'], 6)}")
    _add_para(doc, f"ECM kappa: {_fmt(stats_row['kappa'], 6)}")
    _add_para(doc, f"kappa t-stat: {_fmt(stats_row['kappa_t'], 4)}")
    _add_para(doc, f"ECM R^2: {_fmt(stats_row['ecm_r2'], 6)}")
    _add_para(doc, f"spread std: {_fmt(stats_row['spread_std'], 6)}")
    _add_para(doc, f"Pearson r (returns): {_fmt(stats_row['pearson_r'], 6)}")

    _add_heading(doc, "Conclusion", 1)
    _add_para(doc, _conclusion(left, right, stats_row))

    _add_heading(doc, "Charts", 1)
    for key, title in (
        ("closes", "Daily closes"),
        ("spread", "Engle-Granger residual spread"),
        ("returns", "Daily log returns"),
    ):
        _add_para(doc, title, bold=True)
        doc.add_picture(str(fig_paths[key]), width=Inches(6.2))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

    _add_heading(doc, "Data report", 1)
    _add_para(
        doc,
        "Matched rows are in the sibling Excel workbook "
        f"named {xlsx_name}. Embedding all rows as a Word table is "
        "impractical; this file holds column summaries and the first and "
        "last 15 matched rows.",
    )
    preview_cols = [
        "time",
        f"{left}_log_price",
        f"{right}_log_price",
        "spread_e",
        f"{left}_log_return",
        f"{right}_log_return",
    ]
    numeric_cols = [c for c in table.columns if c != "time"]
    col_summary = (
        table[numeric_cols].describe().T.reset_index().rename(columns={"index": "column"})
    )
    _add_para(doc, "Column summaries", bold=True)
    _add_small_table(doc, col_summary.round(8))
    _add_para(doc, "First 15 matched rows (selected columns)", bold=True)
    _add_small_table(doc, table.loc[:, preview_cols].head(15))
    _add_para(doc, "Last 15 matched rows (selected columns)", bold=True)
    _add_small_table(doc, table.loc[:, preview_cols].tail(15))
    doc.save(out_path)


def _cross_pair_conclusion(index_rows: list[dict[str, object]]) -> list[str]:
    by_p = sorted(index_rows, key=lambda r: float(r["coint_p"]))
    strongest = by_p[0]
    weakest = by_p[-1]
    by_kappa = sorted(index_rows, key=lambda r: float(r["kappa"]))
    most_neg_kappa = by_kappa[0]
    return [
        "## Cross-pair conclusion",
        "",
        "Reading of the 28-pair index at pre-specified Engle-Granger "
        "p-value (PY on PX = right on left). Not a 29th pair analysis and "
        "not a trading signal.",
        "",
        (
            f"Strongest cointegration evidence (lowest p): {strongest['pair']} "
            f"(p={float(strongest['coint_p']):.4g}, "
            f"t={float(strongest['coint_t']):.4f}, "
            f"kappa={float(strongest['kappa']):.4f})."
        ),
        (
            f"Weakest cointegration evidence (highest p): {weakest['pair']} "
            f"(p={float(weakest['coint_p']):.4g})."
        ),
        (
            f"Most negative ECM kappa: {most_neg_kappa['pair']} "
            f"(kappa={float(most_neg_kappa['kappa']):.4f})."
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
        stats_row, table = _coint_stats(table, left, right)
        stem = f"{left}-{right}_Coint_D1"
        fig_paths = _save_figures(table, left, right, stem)

        xlsx_path = OUT_DIR / f"{stem}.xlsx"
        excel_frame = table.copy()
        excel_frame["time"] = pd.to_datetime(excel_frame["time"], utc=True).dt.strftime(
            "%Y-%m-%d"
        )
        with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
            excel_frame.to_excel(writer, index=False, sheet_name="matched_rows")

        html_path = OUT_DIR / f"{stem}_data.html"
        html_path.write_text(
            (
                f"<!DOCTYPE html><html><head><meta charset='utf-8'>"
                f"<title>{stem} data</title></head><body>"
                f"<h1>{left} and {right}: matched rows for cointegration</h1>"
                f"<p>n={int(stats_row['n'])}. Complete archive also in "
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
                "alpha": stats_row["alpha"],
                "beta": stats_row["beta"],
                "coint_t": stats_row["coint_t"],
                "coint_p": stats_row["coint_p"],
                "kappa": stats_row["kappa"],
                "pearson_r": stats_row["pearson_r"],
                "docx": docx_path.name,
                "xlsx": xlsx_path.name,
                "html": html_path.name,
            }
        )
        print(
            f"Wrote {docx_path.name}  p={stats_row['coint_p']:.4g}  "
            f"beta={stats_row['beta']:.4f}  kappa={stats_row['kappa']:.4f}  "
            f"n={int(stats_row['n'])}",
            flush=True,
        )

    index = pd.DataFrame(index_rows)
    index.to_excel(OUT_DIR / "index.xlsx", index=False, sheet_name="index")

    notes = [
        "# Cointegration and error correction experiments v001",
        "",
        "## Research question",
        "",
        "For each unordered pair among the eight majors, what is the "
        "Engle-Granger cointegration evidence and ECM kappa for log closes "
        "(PY = right on PX = left) on the Alpari D1 history?",
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
        "- Series: log close levels for cointegration; log returns for ECM "
        "and Pearson side check; quote direction unchanged",
        "- Engle-Granger: OLS with constant; statsmodels coint(trend='c', "
        "autolag='aic')",
        f"- ECM: one lag of both delta ln legs; headline coint p-value and "
        f"kappa",
        "- Outputs: 28 Word reports, 28 full-data HTML tables, 28 Excel "
        "workbooks, charts under `outputs/figures/`",
        "",
        "## Index",
        "",
        "| pair | n | alpha | beta | coint_t | coint_p | kappa | pearson_r |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in index_rows:
        notes.append(
            f"| {row['pair']} | {row['n']} | "
            f"{float(row['alpha']):.6f} | "
            f"{float(row['beta']):.6f} | "
            f"{float(row['coint_t']):.6f} | "
            f"{float(row['coint_p']):.6g} | "
            f"{float(row['kappa']):.6f} | "
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
