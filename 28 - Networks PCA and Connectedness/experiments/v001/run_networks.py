"""Networks, PCA, and Diebold-Yilmaz connectedness on Alpari D1 majors."""

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
from statsmodels.tsa.api import VAR

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from shared.mt5_data import MAJOR_PAIRS, load_snapshot

SNAPSHOT_REL = Path("data/snapshots/2026-11-03_majors_alpari_D1")
EXP_DIR = Path(__file__).resolve().parent
OUT_DIR = EXP_DIR / "outputs"
FIG_DIR = OUT_DIR / "figures"
OHLCV = ["open", "high", "low", "close", "tick_volume", "spread", "real_volume"]
VAR_MAXLAGS = 10
FEVD_HORIZON = 10
METHOD_NOTE = (
    "Three system-level tools on the eight-major daily log-return panel. "
    "(1) Network distance d_ij = sqrt(2*(1-rho_ij)) from Pearson correlation. "
    "(2) PCA eigenvalues of the correlation matrix R (R v = lambda v). "
    "(3) Diebold-Yilmaz total connectedness index (TCI) from a VAR with "
    "generalised forecast-error variance decomposition (GFEVD), horizon H=10; "
    "lag order chosen by BIC with maxlags=10. TCI = 100 * sum_{i!=j} "
    "theta_tilde_ij / N after row-normalising GFEVD shares. Pair reports "
    "show d_ij, rho_ij, and the directed pair spillover shares from the "
    "system theta_tilde matrix. Edges and TCI are not trading signals."
)


def _assert_guide_toys() -> None:
    rho12 = 0.60
    d12 = math.sqrt(2 * (1 - rho12))
    assert abs(d12 - math.sqrt(0.8)) < 1e-12
    theta = [
        [0.60, 0.25, 0.15],
        [0.20, 0.55, 0.25],
        [0.18, 0.22, 0.60],
    ]
    n = 3
    off = sum(theta[i][j] for i in range(n) for j in range(n) if i != j)
    tci = 100 * off / n
    assert abs(tci - 100 * 1.25 / 3) < 1e-9


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


def _return_panel(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    series = []
    for name in MAJOR_PAIRS:
        s = frames[name].set_index("time")["log_return"].rename(name)
        series.append(s)
    panel = pd.concat(series, axis=1, join="inner").dropna().sort_index()
    return panel


def _distance(rho: float) -> float:
    return float(math.sqrt(2.0 * (1.0 - rho)))


def _generalized_fevd(var_res, horizon: int) -> np.ndarray:
    """Row-normalised generalised FEVD shares theta_tilde (N x N)."""
    sigma = np.asarray(var_res.sigma_u, dtype=float)
    n = sigma.shape[0]
    ma = np.asarray(var_res.ma_rep(maxn=horizon), dtype=float)  # (H+1, n, n)
    theta = np.zeros((n, n), dtype=float)
    sig_diag = np.diag(sigma).copy()
    sig_diag[sig_diag <= 0] = 1e-18
    for i in range(n):
        denom = 0.0
        for h in range(horizon + 1):
            a = ma[h]
            # e_i' A_h Sigma A_h' e_i
            row = a[i, :]
            denom += float(row @ sigma @ row)
        if denom <= 0:
            denom = 1e-18
        for j in range(n):
            num = 0.0
            ej = np.zeros(n)
            ej[j] = 1.0
            for h in range(horizon + 1):
                a = ma[h]
                # (e_i' A_h Sigma e_j)^2 / sigma_jj
                val = float(a[i, :] @ sigma @ ej)
                num += (val * val) / sig_diag[j]
            theta[i, j] = num / denom
    # row-normalise
    row_sums = theta.sum(axis=1, keepdims=True)
    row_sums[row_sums <= 0] = 1.0
    return theta / row_sums


def _system_metrics(panel: pd.DataFrame) -> dict[str, object]:
    corr = panel.corr(method="pearson")
    names = list(panel.columns)
    n = len(names)
    dist = pd.DataFrame(index=names, columns=names, dtype=float)
    for i, a in enumerate(names):
        for j, b in enumerate(names):
            if i == j:
                dist.loc[a, b] = 0.0
            else:
                dist.loc[a, b] = _distance(float(corr.loc[a, b]))

    eigvals, eigvecs = np.linalg.eigh(corr.to_numpy(dtype=float))
    order = np.argsort(eigvals)[::-1]
    eigvals = eigvals[order]
    eigvecs = eigvecs[:, order]
    pca = pd.DataFrame(
        {
            "component": [f"PC{k+1}" for k in range(n)],
            "eigenvalue": eigvals,
            "variance_share": eigvals / eigvals.sum(),
        }
    )
    loadings = pd.DataFrame(
        eigvecs, index=names, columns=[f"PC{k+1}" for k in range(n)]
    )

    # VAR on demeaned returns for stability
    demeaned = panel - panel.mean()
    var_model = VAR(demeaned)
    selected = var_model.select_order(maxlags=VAR_MAXLAGS)
    lag_p = int(selected.bic)
    if lag_p < 1:
        lag_p = 1
    var_res = var_model.fit(lag_p)
    theta = _generalized_fevd(var_res, FEVD_HORIZON)
    theta_df = pd.DataFrame(theta, index=names, columns=names)
    off = float(np.sum(theta) - np.trace(theta))
    tci = 100.0 * off / n
    # from others / to others
    to_others = 100.0 * (theta.sum(axis=0) - np.diag(theta))
    from_others = 100.0 * (theta.sum(axis=1) - np.diag(theta))
    net = to_others - from_others
    connectedness = pd.DataFrame(
        {
            "from_others": from_others,
            "to_others": to_others,
            "net": net,
            "own_share": 100.0 * np.diag(theta),
        },
        index=names,
    )

    return {
        "corr": corr,
        "dist": dist,
        "pca": pca,
        "loadings": loadings,
        "theta": theta_df,
        "tci": tci,
        "lag_p": lag_p,
        "connectedness": connectedness,
        "n_obs": len(panel),
    }


def _fmt(value: float, digits: int = 4) -> str:
    if math.isnan(value):
        return "n/a"
    return f"{value:.{digits}f}"


def _save_system_figures(sysm: dict[str, object], panel: pd.DataFrame) -> dict[str, Path]:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    corr: pd.DataFrame = sysm["corr"]  # type: ignore[assignment]
    dist: pd.DataFrame = sysm["dist"]  # type: ignore[assignment]
    pca: pd.DataFrame = sysm["pca"]  # type: ignore[assignment]
    theta: pd.DataFrame = sysm["theta"]  # type: ignore[assignment]

    fig, ax = plt.subplots(figsize=(8, 6.5))
    im = ax.imshow(corr.to_numpy(dtype=float), cmap="coolwarm", vmin=-1, vmax=1)
    ax.set_xticks(range(len(corr.columns)))
    ax.set_yticks(range(len(corr.index)))
    ax.set_xticklabels(corr.columns, rotation=45, ha="right")
    ax.set_yticklabels(corr.index)
    ax.set_title("Pearson correlation matrix (8 majors)")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    paths["corr"] = FIG_DIR / "system_corr.png"
    fig.savefig(paths["corr"], dpi=120)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 6.5))
    im = ax.imshow(dist.to_numpy(dtype=float), cmap="viridis")
    ax.set_xticks(range(len(dist.columns)))
    ax.set_yticks(range(len(dist.index)))
    ax.set_xticklabels(dist.columns, rotation=45, ha="right")
    ax.set_yticklabels(dist.index)
    ax.set_title("Network distance d_ij = sqrt(2(1-rho))")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    paths["dist"] = FIG_DIR / "system_dist.png"
    fig.savefig(paths["dist"], dpi=120)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4.2))
    ax.bar(pca["component"], pca["eigenvalue"], color="#087F8C")
    ax.set_ylabel("eigenvalue")
    ax.set_title("PCA eigenvalues of correlation matrix")
    fig.tight_layout()
    paths["pca"] = FIG_DIR / "system_pca.png"
    fig.savefig(paths["pca"], dpi=120)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 6.5))
    im = ax.imshow(theta.to_numpy(dtype=float), cmap="YlOrRd", vmin=0, vmax=1)
    ax.set_xticks(range(len(theta.columns)))
    ax.set_yticks(range(len(theta.index)))
    ax.set_xticklabels(theta.columns, rotation=45, ha="right")
    ax.set_yticklabels(theta.index)
    ax.set_title(f"GFEVD theta_tilde (H={FEVD_HORIZON}); TCI={sysm['tci']:.2f}")
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    paths["theta"] = FIG_DIR / "system_theta.png"
    fig.savefig(paths["theta"], dpi=120)
    plt.close(fig)

    return paths


def _pair_table_from_panel(
    frames: dict[str, pd.DataFrame], left: str, right: str
) -> pd.DataFrame:
    a = frames[left].set_index("time")
    b = frames[right].set_index("time")
    common = a.index.intersection(b.index).sort_values()
    cols: dict[str, pd.Series] = {"time": pd.Series(common, index=common)}
    for col in OHLCV + ["log_return"]:
        cols[f"{left}_{col}"] = a.loc[common, col]
        cols[f"{right}_{col}"] = b.loc[common, col]
    table = pd.DataFrame(cols)
    table = table.dropna(subset=[f"{left}_log_return", f"{right}_log_return"])
    return table.reset_index(drop=True)


def _save_pair_figures(
    table: pd.DataFrame, left: str, right: str, stem: str
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


def _write_pair_word(
    table: pd.DataFrame,
    left: str,
    right: str,
    left_broker: str,
    right_broker: str,
    rho: float,
    d_ij: float,
    theta_lr: float,
    theta_rl: float,
    sysm: dict[str, object],
    drop_note: str,
    snapshot_name: str,
    fig_paths: dict[str, Path],
    system_fig_paths: dict[str, Path],
    xlsx_name: str,
    out_path: Path,
) -> None:
    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(10)

    _add_heading(doc, f"Networks / PCA / connectedness: {left} and {right}", 0)
    _add_para(
        doc,
        "Method 28 / pair slice of eight-major system / "
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
        f"Matched return count n: {len(table)}",
        f"System panel n: {sysm['n_obs']}",
        drop_note,
        f"VAR lag (BIC): {sysm['lag_p']}; GFEVD horizon H={FEVD_HORIZON}",
        f"System TCI: {_fmt(float(sysm['tci']), 4)}",
        f"Complete matched rows (Excel): {xlsx_name}",
    ):
        _add_para(doc, line)

    _add_heading(doc, "Method carried forward", 1)
    _add_para(doc, METHOD_NOTE)

    _add_heading(doc, "Pair results", 1)
    _add_para(doc, f"Pearson rho: {_fmt(rho, 6)}")
    _add_para(doc, f"Network distance d_ij: {_fmt(d_ij, 6)}")
    _add_para(doc, f"theta_tilde[{left}->{right}] (row {left}, col {right}): {_fmt(theta_lr, 6)}")
    _add_para(doc, f"theta_tilde[{right}->{left}] (row {right}, col {left}): {_fmt(theta_rl, 6)}")
    pca: pd.DataFrame = sysm["pca"]  # type: ignore[assignment]
    _add_para(doc, f"PCA lambda_1: {_fmt(float(pca.loc[0, 'eigenvalue']), 6)}")
    _add_para(doc, f"PCA variance share PC1: {_fmt(float(pca.loc[0, 'variance_share']), 6)}")

    _add_heading(doc, "Conclusion", 1)
    _add_para(
        doc,
        f"For {left}-{right}: d_ij={_fmt(d_ij, 4)} from rho={_fmt(rho, 4)}. "
        f"Pair spillover shares {_fmt(theta_lr, 4)} / {_fmt(theta_rl, 4)}. "
        f"System TCI={_fmt(float(sysm['tci']), 2)}. "
        f"Not a trading signal.",
    )

    _add_heading(doc, "Pair charts", 1)
    for key, title in (("closes", "Daily closes"), ("returns", "Daily log returns")):
        _add_para(doc, title, bold=True)
        doc.add_picture(str(fig_paths[key]), width=Inches(6.2))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

    _add_heading(doc, "System charts (shared)", 1)
    for key, title in (
        ("corr", "Correlation matrix"),
        ("dist", "Distance matrix"),
        ("pca", "PCA eigenvalues"),
        ("theta", "GFEVD theta_tilde"),
    ):
        _add_para(doc, title, bold=True)
        doc.add_picture(str(system_fig_paths[key]), width=Inches(5.8))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER

    _add_heading(doc, "Data report", 1)
    preview_cols = ["time", f"{left}_log_return", f"{right}_log_return"]
    _add_para(doc, "First 15 matched rows", bold=True)
    _add_small_table(doc, table.loc[:, preview_cols].head(15))
    _add_para(doc, "Last 15 matched rows", bold=True)
    _add_small_table(doc, table.loc[:, preview_cols].tail(15))
    doc.save(out_path)


def _cross_pair_conclusion(index_rows: list[dict[str, object]], tci: float) -> list[str]:
    by_d = sorted(index_rows, key=lambda r: float(r["d_ij"]))
    closest = by_d[0]
    farthest = by_d[-1]
    return [
        "## Cross-pair conclusion",
        "",
        "Reading of the 28-pair network-distance index plus the system TCI. "
        "Not a 29th pair analysis and not a trading signal.",
        "",
        f"System TCI (H={FEVD_HORIZON}): {tci:.4f}.",
        (
            f"Closest network pair (smallest d_ij): {closest['pair']} "
            f"(d={float(closest['d_ij']):.4f}, rho={float(closest['rho']):.4f})."
        ),
        (
            f"Farthest network pair (largest d_ij): {farthest['pair']} "
            f"(d={float(farthest['d_ij']):.4f}, rho={float(farthest['rho']):.4f})."
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
    panel = _return_panel(frames)
    sysm = _system_metrics(panel)
    system_figs = _save_system_figures(sysm, panel)

    # Persist system workbooks
    corr: pd.DataFrame = sysm["corr"]  # type: ignore[assignment]
    dist: pd.DataFrame = sysm["dist"]  # type: ignore[assignment]
    pca: pd.DataFrame = sysm["pca"]  # type: ignore[assignment]
    loadings: pd.DataFrame = sysm["loadings"]  # type: ignore[assignment]
    theta: pd.DataFrame = sysm["theta"]  # type: ignore[assignment]
    connectedness: pd.DataFrame = sysm["connectedness"]  # type: ignore[assignment]
    with pd.ExcelWriter(OUT_DIR / "system_metrics.xlsx", engine="openpyxl") as writer:
        corr.to_excel(writer, sheet_name="corr")
        dist.to_excel(writer, sheet_name="distance")
        pca.to_excel(writer, index=False, sheet_name="pca")
        loadings.to_excel(writer, sheet_name="loadings")
        theta.to_excel(writer, sheet_name="theta_tilde")
        connectedness.to_excel(writer, sheet_name="connectedness")
        panel_out = panel.reset_index()
        time_col = panel_out.columns[0]
        panel_out = panel_out.rename(columns={time_col: "time"})
        panel_out["time"] = pd.to_datetime(panel_out["time"], utc=True).dt.tz_localize(
            None
        )
        panel_out.to_excel(writer, index=False, sheet_name="return_panel")

    index_rows: list[dict[str, object]] = []
    pairs = list(itertools.combinations(MAJOR_PAIRS, 2))

    for left, right in pairs:
        table = _pair_table_from_panel(frames, left, right)
        rho = float(corr.loc[left, right])
        d_ij = float(dist.loc[left, right])
        theta_lr = float(theta.loc[left, right])
        theta_rl = float(theta.loc[right, left])
        # side-check matched-sample pearson
        pearson_r = float(
            stats.pearsonr(
                table[f"{left}_log_return"], table[f"{right}_log_return"]
            ).statistic
        )
        stem = f"{left}-{right}_Network_D1"
        fig_paths = _save_pair_figures(table, left, right, stem)

        xlsx_path = OUT_DIR / f"{stem}.xlsx"
        excel_frame = table.copy()
        excel_frame["time"] = pd.to_datetime(excel_frame["time"], utc=True).dt.strftime(
            "%Y-%m-%d"
        )
        with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
            excel_frame.to_excel(writer, index=False, sheet_name="matched_rows")
            pd.DataFrame(
                [
                    {
                        "rho": rho,
                        "d_ij": d_ij,
                        "theta_L_to_R": theta_lr,
                        "theta_R_to_L": theta_rl,
                        "system_tci": float(sysm["tci"]),
                        "var_lag": int(sysm["lag_p"]),
                    }
                ]
            ).to_excel(writer, index=False, sheet_name="pair_metrics")

        html_path = OUT_DIR / f"{stem}_data.html"
        html_path.write_text(
            (
                f"<!DOCTYPE html><html><head><meta charset='utf-8'>"
                f"<title>{stem} data</title></head><body>"
                f"<h1>{left} and {right}: network / connectedness slice</h1>"
                f"<p>n={len(table)}. System TCI={float(sysm['tci']):.4f}.</p>"
                + excel_frame.to_html(index=False)
                + "</body></html>"
            ),
            encoding="utf-8",
        )

        docx_path = OUT_DIR / f"{stem}.docx"
        _write_pair_word(
            table=table,
            left=left,
            right=right,
            left_broker=broker_map[left],
            right_broker=broker_map[right],
            rho=rho,
            d_ij=d_ij,
            theta_lr=theta_lr,
            theta_rl=theta_rl,
            sysm=sysm,
            drop_note=drop_note,
            snapshot_name=snapshot_name,
            fig_paths=fig_paths,
            system_fig_paths=system_figs,
            xlsx_name=xlsx_path.name,
            out_path=docx_path,
        )

        index_rows.append(
            {
                "pair": f"{left}-{right}",
                "n": len(table),
                "rho": rho,
                "d_ij": d_ij,
                "theta_L_to_R": theta_lr,
                "theta_R_to_L": theta_rl,
                "pearson_r_matched": pearson_r,
                "docx": docx_path.name,
                "xlsx": xlsx_path.name,
                "html": html_path.name,
            }
        )
        print(
            f"Wrote {docx_path.name}  d={d_ij:.4f}  rho={rho:.4f}  "
            f"n={len(table)}",
            flush=True,
        )

    index = pd.DataFrame(index_rows)
    index.to_excel(OUT_DIR / "index.xlsx", index=False, sheet_name="index")

    notes = [
        "# Networks, PCA, and connectedness experiments v001",
        "",
        "## Research question",
        "",
        "On the eight-major Alpari D1 log-return panel, what are the "
        "network distances d_ij, PCA eigenvalues of the correlation matrix, "
        "and Diebold-Yilmaz TCI from a BIC-selected VAR with GFEVD horizon "
        f"H={FEVD_HORIZON}?",
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
        f"- Panel: {', '.join(MAJOR_PAIRS)}; n_obs={sysm['n_obs']}",
        "- Network: d_ij = sqrt(2*(1-rho_ij)) from full-sample Pearson R",
        "- PCA: eigenvalues of R (descending)",
        f"- VAR: demeaned returns; lag = BIC among 1..{VAR_MAXLAGS} "
        f"(selected p={sysm['lag_p']}); GFEVD H={FEVD_HORIZON}",
        f"- System TCI: {float(sysm['tci']):.6f}",
        "- Outputs: system_metrics.xlsx; 28 pair Word/HTML/Excel reports; "
        "system + pair charts under `outputs/figures/`",
        "",
        "## System PCA",
        "",
        "| component | eigenvalue | variance_share |",
        "| --- | ---: | ---: |",
    ]
    for _, row in pca.iterrows():
        notes.append(
            f"| {row['component']} | {float(row['eigenvalue']):.6f} | "
            f"{float(row['variance_share']):.6f} |"
        )
    notes.extend(
        [
            "",
            "## System connectedness (from/to others, percent)",
            "",
            "| symbol | from_others | to_others | net | own_share |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for name, row in connectedness.iterrows():
        notes.append(
            f"| {name} | {float(row['from_others']):.4f} | "
            f"{float(row['to_others']):.4f} | {float(row['net']):.4f} | "
            f"{float(row['own_share']):.4f} |"
        )
    notes.extend(
        [
            "",
            "## Pair index",
            "",
            "| pair | n | rho | d_ij | theta_L_to_R | theta_R_to_L |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in index_rows:
        notes.append(
            f"| {row['pair']} | {row['n']} | "
            f"{float(row['rho']):.6f} | "
            f"{float(row['d_ij']):.6f} | "
            f"{float(row['theta_L_to_R']):.6f} | "
            f"{float(row['theta_R_to_L']):.6f} |"
        )
    notes.append("")
    notes.extend(_cross_pair_conclusion(index_rows, float(sysm["tci"])))
    notes.append(
        "This NOTES.md is the system summary plus the pair-distance reading. "
        "It is not a trading signal."
    )
    notes.append("")
    (EXP_DIR / "NOTES.md").write_text("\n".join(notes), encoding="utf-8")
    return OUT_DIR


if __name__ == "__main__":
    run()
