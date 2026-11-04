"""Build Correlation_Methods_28_Pages.pdf — one readable page per method."""

from __future__ import annotations

import sys
from pathlib import Path
from xml.sax.saxutils import escape

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pypdf import PdfReader
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

REPORTS_DIR = Path(__file__).resolve().parent
if str(REPORTS_DIR) not in sys.path:
    sys.path.insert(0, str(REPORTS_DIR))

from method_config import METHODS, method_dir  # noqa: E402

OUT_PDF = REPORTS_DIR / "Correlation_Methods_28_Pages.pdf"
FIG_DIR = REPORTS_DIR / "figures"
EXPECTED_PAGES = 28

COLOR_HEAD = colors.HexColor("#15364A")
COLOR_SUB = colors.HexColor("#087F8C")
COLOR_BOX = colors.HexColor("#EDF5F7")
COLOR_PLUS = colors.HexColor("#1B5E20")
COLOR_MINUS = colors.HexColor("#8B1A1A")
BAR_A = "#0072B2"
BAR_B = "#E69F00"
BAR_C = "#009E73"
MAJORS = ["EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "USDJPY", "USDCHF", "USDCAD", "EURGBP"]


def load_index(meta: dict) -> pd.DataFrame:
    path = method_dir(meta) / meta["index"]
    if not path.is_file():
        raise FileNotFoundError(path)
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    return pd.read_excel(path)


def pair_short(pair: str) -> str:
    return str(pair).replace("USD", "").replace("-", "/")[:12]


def build_styles():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="MTitle",
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=18,
            textColor=COLOR_HEAD,
            spaceAfter=3,
        )
    )
    styles.add(
        ParagraphStyle(
            name="MTag",
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=11,
            textColor=COLOR_SUB,
            spaceAfter=2,
        )
    )
    styles.add(
        ParagraphStyle(
            name="MBody",
            fontName="Helvetica",
            fontSize=9.5,
            leading=12,
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            name="MSmall",
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            spaceAfter=2,
        )
    )
    styles.add(
        ParagraphStyle(
            name="MHead",
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=12,
            textColor=COLOR_SUB,
            spaceBefore=4,
            spaceAfter=3,
        )
    )
    styles.add(
        ParagraphStyle(
            name="MFormula",
            fontName="Courier",
            fontSize=8.5,
            leading=11,
            backColor=COLOR_BOX,
            borderPadding=6,
            spaceBefore=2,
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BulletPlus",
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=COLOR_PLUS,
            leftIndent=4,
            spaceAfter=1,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BulletMinus",
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            textColor=COLOR_MINUS,
            leftIndent=4,
            spaceAfter=1,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Caption",
            fontName="Helvetica-Oblique",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#333333"),
            spaceBefore=2,
            spaceAfter=0,
        )
    )
    return styles


def two_col(left_title, left_items, right_title, right_items, styles, left_style, right_style):
    left = [Paragraph(f"<b>{escape(left_title)}</b>", styles["MHead"])]
    left += [Paragraph(f"• {escape(t)}", left_style) for t in left_items]
    right = [Paragraph(f"<b>{escape(right_title)}</b>", styles["MHead"])]
    right += [Paragraph(f"• {escape(t)}", right_style) for t in right_items]
    while len(left) < len(right):
        left.append(Paragraph("", styles["MSmall"]))
    while len(right) < len(left):
        right.append(Paragraph("", styles["MSmall"]))
    data = [[a, b] for a, b in zip(left, right)]
    t = Table(data, colWidths=[92 * mm, 92 * mm])
    t.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 1),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    return t


def symbol_table(terms: list[tuple[str, str]], styles) -> Table:
    rows = [
        [
            Paragraph("<b>Symbol</b>", styles["MSmall"]),
            Paragraph("<b>Meaning on this data</b>", styles["MSmall"]),
        ]
    ]
    for sym, meaning in terms:
        rows.append(
            [
                Paragraph(escape(sym), styles["MSmall"]),
                Paragraph(escape(meaning), styles["MSmall"]),
            ]
        )
    t = Table(rows, colWidths=[42 * mm, 142 * mm])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DBEDF0")),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#B8CCD2")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]
        )
    )
    return t


# ---- charts -----------------------------------------------------------------


def _finish(fig, out: Path, title: str) -> Path:
    ax = fig.axes[0] if fig.axes else None
    if ax is not None and title:
        ax.set_title(title, fontsize=9, pad=3)
    fig.tight_layout(pad=0.35)
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return out


def chart_heatmap_r(df: pd.DataFrame, out: Path) -> tuple[Path, str]:
    mat = pd.DataFrame(np.eye(8), index=MAJORS, columns=MAJORS)
    for _, row in df.iterrows():
        a, b = str(row["pair"]).split("-")
        r = float(row["r"])
        mat.loc[a, b] = r
        mat.loc[b, a] = r
    fig, ax = plt.subplots(figsize=(6.8, 4.0), dpi=140)
    im = ax.imshow(mat.values, cmap="RdBu_r", vmin=-1, vmax=1)
    ax.set_xticks(range(8))
    ax.set_yticks(range(8))
    ax.set_xticklabels([m.replace("USD", "") for m in MAJORS], fontsize=7, rotation=45, ha="right")
    ax.set_yticklabels([m.replace("USD", "") for m in MAJORS], fontsize=7)
    for i in range(8):
        for j in range(8):
            ax.text(j, i, f"{mat.values[i, j]:.2f}", ha="center", va="center", fontsize=5.5)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    strong = df.loc[df["r"].abs().idxmax()]
    cap = (
        f"Portfolio heatmap of full-sample Pearson r. "
        f"Strongest |r|: {strong['pair']} = {strong['r']:.3f}."
    )
    return _finish(fig, out, "Pearson r across the eight majors"), cap


def chart_scatter(df: pd.DataFrame, x_col: str, y_col: str, out: Path, title: str) -> tuple[Path, str]:
    work = df.dropna(subset=[x_col, y_col])
    fig, ax = plt.subplots(figsize=(6.8, 3.9), dpi=140)
    ax.scatter(work[x_col], work[y_col], c=BAR_A, s=28, alpha=0.85)
    lims = [
        min(work[x_col].min(), work[y_col].min()) - 0.05,
        max(work[x_col].max(), work[y_col].max()) + 0.05,
    ]
    ax.plot(lims, lims, color="#666666", linewidth=0.8, linestyle="--", label="y = x")
    ax.set_xlim(lims)
    ax.set_ylim(lims)
    ax.set_xlabel(x_col, fontsize=8)
    ax.set_ylabel(y_col, fontsize=8)
    ax.tick_params(labelsize=7)
    ax.legend(fontsize=7, frameon=False)
    gap = (work[y_col] - work[x_col]).abs()
    i = gap.idxmax()
    cap = (
        f"Each point is one FX pair. "
        f"Largest |{y_col} − {x_col}|: {work.loc[i, 'pair']} "
        f"({work.loc[i, y_col]:.3f} vs {work.loc[i, x_col]:.3f})."
    )
    return _finish(fig, out, title), cap


def chart_gap_bars(df: pd.DataFrame, gap_col: str, out: Path, title: str) -> tuple[Path, str]:
    work = df.dropna(subset=[gap_col]).copy()
    work = work.reindex(work[gap_col].abs().sort_values(ascending=False).index)
    fig, ax = plt.subplots(figsize=(6.8, 3.9), dpi=140)
    colors_bar = [BAR_A if v >= 0 else BAR_B for v in work[gap_col]]
    ax.bar(range(len(work)), work[gap_col].values, color=colors_bar, width=0.75)
    ax.axhline(0, color="#333", linewidth=0.5)
    ax.set_xticks(range(len(work)))
    ax.set_xticklabels([pair_short(p) for p in work["pair"]], rotation=70, ha="right", fontsize=6)
    ax.set_ylabel(gap_col, fontsize=8)
    ax.tick_params(axis="y", labelsize=7)
    top = work.iloc[0]
    cap = f"Gap chart (method-specific). Largest |{gap_col}|: {top['pair']} = {top[gap_col]:.3f}."
    return _finish(fig, out, title), cap


def chart_rolling(df: pd.DataFrame, out: Path) -> tuple[Path, str]:
    pivot = df.pivot_table(index="pair", columns="window", values="latest_r", aggfunc="last")
    baseline = df.groupby("pair")["baseline_r"].first()
    order = (pivot[20] - baseline).abs().sort_values(ascending=False).index
    pivot = pivot.loc[order]
    baseline = baseline.loc[order]
    x = np.arange(len(pivot))
    width = 0.2
    fig, ax = plt.subplots(figsize=(6.8, 3.9), dpi=140)
    ax.bar(x - 1.5 * width, baseline.values, width, label="baseline", color="#999999")
    for i, (w, c) in enumerate(zip([20, 60, 100], [BAR_A, BAR_B, BAR_C])):
        ax.bar(x + (i - 0.5) * width, pivot[w].values, width, label=f"r_{w}", color=c)
    ax.axhline(0, color="#333", linewidth=0.4)
    ax.set_xticks(x)
    ax.set_xticklabels([pair_short(p) for p in pivot.index], rotation=70, ha="right", fontsize=6)
    ax.legend(fontsize=6, ncol=4, frameon=False, loc="upper right")
    ax.set_ylabel("r", fontsize=8)
    gap = (pivot[20] - baseline).abs()
    pair = gap.idxmax()
    cap = (
        f"Rolling windows vs baseline. "
        f"Largest |r_20 − baseline|: {pair} "
        f"(r_20={pivot.loc[pair, 20]:.3f}, baseline={baseline.loc[pair]:.3f})."
    )
    return _finish(fig, out, "Rolling latest r vs baseline (17 pairs)"), cap


def chart_adcc_g(df: pd.DataFrame, out: Path) -> tuple[Path, str]:
    work = df.dropna(subset=["g"]).copy()
    work = work.sort_values("g", ascending=False)
    fig, ax = plt.subplots(figsize=(6.8, 3.9), dpi=140)
    colors_bar = [BAR_B if abs(b - 0.5) < 1e-6 else BAR_A for b in work["b"].fillna(-1)]
    ax.bar(range(len(work)), work["g"].values, color=colors_bar, width=0.75)
    ax.set_xticks(range(len(work)))
    ax.set_xticklabels([pair_short(p) for p in work["pair"]], rotation=70, ha="right", fontsize=6)
    ax.set_ylabel("g (asymmetry)", fontsize=8)
    ax.tick_params(axis="y", labelsize=7)
    top = work.iloc[0]
    stuck = work.loc[(work["b"] - 0.5).abs() < 1e-6, "pair"].tolist()
    stuck_txt = f" Stuck b=0.5 fit: {', '.join(stuck)}." if stuck else ""
    cap = f"ADCC asymmetry g. Largest g: {top['pair']} = {top['g']:.4f}.{stuck_txt}"
    return _finish(fig, out, "Asymmetry parameter g (orange = possible stuck b=0.5)"), cap


def chart_regime(df: pd.DataFrame, out: Path) -> tuple[Path, str]:
    work = df.dropna(subset=["stress_minus_quiet"]).copy()
    work = work.reindex(work["stress_minus_quiet"].abs().sort_values(ascending=False).index)
    fig, ax = plt.subplots(figsize=(6.8, 3.9), dpi=140)
    colors_bar = [BAR_A if v >= 0 else BAR_B for v in work["stress_minus_quiet"]]
    ax.bar(range(len(work)), work["stress_minus_quiet"].values, color=colors_bar, width=0.75)
    ax.axhline(0, color="#333", linewidth=0.5)
    ax.set_xticks(range(len(work)))
    ax.set_xticklabels([pair_short(p) for p in work["pair"]], rotation=70, ha="right", fontsize=6)
    ax.set_ylabel("stress − quiet", fontsize=8)
    top = work.iloc[0]
    cap = (
        f"Stress minus quiet correlation. "
        f"Largest |gap|: {top['pair']} = {top['stress_minus_quiet']:.3f}."
    )
    return _finish(fig, out, "Regime gap: stress_minus_quiet"), cap


def chart_two_dirs(
    df: pd.DataFrame,
    col_l: str,
    col_r: str,
    out: Path,
    title: str,
    ylabel: str,
    hline: float | None = None,
) -> tuple[Path, str]:
    work = df.dropna(subset=[col_l, col_r]).copy()
    # sort by max abs of either direction
    work = work.assign(_k=np.maximum(work[col_l].abs(), work[col_r].abs()))
    work = work.sort_values("_k", ascending=False)
    x = np.arange(len(work))
    width = 0.38
    fig, ax = plt.subplots(figsize=(6.8, 3.9), dpi=140)
    ax.bar(x - width / 2, work[col_l].values, width, label=col_l[:18], color=BAR_A)
    ax.bar(x + width / 2, work[col_r].values, width, label=col_r[:18], color=BAR_B)
    if hline is not None:
        ax.axhline(hline, color="#D55E00", linewidth=1.0, linestyle="--", label=f"bias≈{hline}")
    ax.axhline(0, color="#333", linewidth=0.4)
    ax.set_xticks(x)
    ax.set_xticklabels([pair_short(p) for p in work["pair"]], rotation=70, ha="right", fontsize=6)
    ax.set_ylabel(ylabel, fontsize=8)
    ax.legend(fontsize=6, frameon=False, loc="upper right")
    i = work["_k"].idxmax()
    cap = (
        f"Directed scores. Peak |value|: {work.loc[i, 'pair']} "
        f"({col_l}={work.loc[i, col_l]:.4f}, {col_r}={work.loc[i, col_r]:.4f})."
    )
    return _finish(fig, out, title), cap


def chart_granger(df: pd.DataFrame, out: Path) -> tuple[Path, str]:
    work = df.dropna(subset=["p_L_to_R_p1", "p_R_to_L_p1"]).copy()
    # -log10(p); clip tiny p
    eps = 1e-300
    work["nl_L"] = -np.log10(work["p_L_to_R_p1"].clip(lower=eps))
    work["nl_R"] = -np.log10(work["p_R_to_L_p1"].clip(lower=eps))
    work = work.assign(_k=np.maximum(work["nl_L"], work["nl_R"])).sort_values("_k", ascending=True)
    y = np.arange(len(work))
    fig, ax = plt.subplots(figsize=(6.8, 4.1), dpi=140)
    ax.barh(y - 0.2, work["nl_L"].values, 0.38, color=BAR_A, label="L→R")
    ax.barh(y + 0.2, work["nl_R"].values, 0.38, color=BAR_B, label="R→L")
    ax.axvline(-np.log10(0.05), color="#D55E00", linestyle="--", linewidth=1, label="p=0.05")
    ax.set_yticks(y)
    ax.set_yticklabels([pair_short(p) for p in work["pair"]], fontsize=6)
    ax.set_xlabel("-log10(p) lag-1", fontsize=8)
    ax.legend(fontsize=6, frameon=False)
    # strongest = smallest p
    i = df["p_L_to_R_p1"].idxmin()
    cap = (
        f"Horizontal bars of −log10(p). "
        f"Smallest lag-1 L→R p: {df.loc[i, 'pair']} = {df.loc[i, 'p_L_to_R_p1']:.2e}."
    )
    return _finish(fig, out, "Granger lag-1 −log10(p), both directions"), cap


def chart_sorted_bars(df: pd.DataFrame, col: str, out: Path, title: str) -> tuple[Path, str]:
    work = df.dropna(subset=[col]).sort_values(col, ascending=False)
    fig, ax = plt.subplots(figsize=(6.8, 3.9), dpi=140)
    ax.bar(range(len(work)), work[col].values, color=BAR_A, width=0.75)
    ax.set_xticks(range(len(work)))
    ax.set_xticklabels([pair_short(p) for p in work["pair"]], rotation=70, ha="right", fontsize=6)
    ax.set_ylabel(col, fontsize=8)
    top = work.iloc[0]
    bot = work.iloc[-1]
    cap = f"Sorted {col}. Highest: {top['pair']} = {top[col]:.3f}. Lowest: {bot['pair']} = {bot[col]:.3f}."
    return _finish(fig, out, title), cap


def chart_tail(df: pd.DataFrame, out: Path) -> tuple[Path, str]:
    work = df.dropna(subset=["L_lower_cond_R", "L_upper_cond_R"])
    fig, ax = plt.subplots(figsize=(6.8, 3.9), dpi=140)
    ax.scatter(work["L_lower_cond_R"], work["L_upper_cond_R"], c=BAR_A, s=32)
    lim = [0, max(work["L_lower_cond_R"].max(), work["L_upper_cond_R"].max()) + 0.05]
    ax.plot(lim, lim, "--", color="#666", linewidth=0.8, label="lower = upper")
    ax.set_xlabel("Lower-tail L_hat", fontsize=8)
    ax.set_ylabel("Upper-tail L_hat", fontsize=8)
    ax.legend(fontsize=7, frameon=False)
    i = work["L_lower_cond_R"].idxmax()
    cap = (
        f"Lower vs upper tail at alpha=0.05. "
        f"Strongest lower tail: {work.loc[i, 'pair']} = {work.loc[i, 'L_lower_cond_R']:.3f}."
    )
    return _finish(fig, out, "Tail dependence: lower vs upper L_hat"), cap


def chart_grouped_scales(df: pd.DataFrame, scale_cols: list, out: Path, title: str) -> tuple[Path, str]:
    cols = [c for c, _ in scale_cols]
    work = df.dropna(subset=cols).copy()
    # sort by first scale abs
    work = work.reindex(work[cols[0]].abs().sort_values(ascending=False).index)
    # show top 14 to keep readable, or all if <=16
    show = work if len(work) <= 16 else work.iloc[:14]
    x = np.arange(len(show))
    width = 0.25
    fig, ax = plt.subplots(figsize=(6.8, 3.9), dpi=140)
    palette = [BAR_A, BAR_B, BAR_C]
    for i, (col, lab) in enumerate(scale_cols):
        ax.bar(x + (i - 1) * width, show[col].values, width, label=lab, color=palette[i % 3])
    ax.axhline(0, color="#333", linewidth=0.4)
    ax.set_xticks(x)
    ax.set_xticklabels([pair_short(p) for p in show["pair"]], rotation=70, ha="right", fontsize=6)
    ax.legend(fontsize=7, frameon=False, ncol=3)
    top = work.iloc[0]
    cap = (
        f"Grouped scales. Example head pair {top['pair']}: "
        + ", ".join(f"{lab}={top[col]:.3f}" for col, lab in scale_cols)
        + "."
    )
    return _finish(fig, out, title), cap


def chart_mf(df: pd.DataFrame, out: Path) -> tuple[Path, str]:
    work = df.dropna(subset=["rho_q2_s100", "rho_q4_s100"])
    fig, ax = plt.subplots(figsize=(6.8, 3.9), dpi=140)
    ax.scatter(work["rho_q2_s100"], work["rho_q4_s100"], c=BAR_A, s=32)
    lims = [
        min(work["rho_q2_s100"].min(), work["rho_q4_s100"].min()) - 0.05,
        max(work["rho_q2_s100"].max(), work["rho_q4_s100"].max()) + 0.05,
    ]
    ax.plot(lims, lims, "--", color="#666", linewidth=0.8)
    ax.set_xlabel("rho_q2_s100", fontsize=8)
    ax.set_ylabel("rho_q4_s100", fontsize=8)
    gap = (work["rho_q4_s100"] - work["rho_q2_s100"]).abs()
    i = gap.idxmax()
    cap = (
        f"Moment q=4 vs q=2 at s=100. "
        f"Largest |gap|: {work.loc[i, 'pair']} "
        f"(q4={work.loc[i, 'rho_q4_s100']:.3f}, q2={work.loc[i, 'rho_q2_s100']:.3f})."
    )
    return _finish(fig, out, "Multifractal DCCA: q4 vs q2 at s=100"), cap


def chart_coint(df: pd.DataFrame, out: Path) -> tuple[Path, str]:
    work = df.dropna(subset=["coint_p"]).copy()
    work["nl"] = -np.log10(work["coint_p"].clip(lower=1e-300))
    work = work.sort_values("nl", ascending=False)
    fig, ax = plt.subplots(figsize=(6.8, 3.9), dpi=140)
    ax.bar(range(len(work)), work["nl"].values, color=BAR_A, width=0.75)
    bonf = -np.log10(0.05 / 28)
    ax.axhline(-np.log10(0.05), color=BAR_B, linestyle="--", linewidth=1, label="p=0.05")
    ax.axhline(bonf, color="#D55E00", linestyle="--", linewidth=1, label="Bonferroni 0.05/28")
    ax.set_xticks(range(len(work)))
    ax.set_xticklabels([pair_short(p) for p in work["pair"]], rotation=70, ha="right", fontsize=6)
    ax.set_ylabel("-log10(coint_p)", fontsize=8)
    ax.legend(fontsize=6, frameon=False)
    top = work.iloc[0]
    cap = (
        f"Engle-Granger −log10(p). Lowest raw p: {top['pair']} = {top['coint_p']:.4f}. "
        f"Bonferroni line is at p≈{0.05/28:.4f}; no pair clears it in v001."
    )
    return _finish(fig, out, "Cointegration −log10(p) with multiplicity lines"), cap


def chart_network(df: pd.DataFrame, out: Path) -> tuple[Path, str]:
    work = df.dropna(subset=["theta_L_to_R", "theta_R_to_L"]).copy()
    work["net"] = work["theta_L_to_R"] - work["theta_R_to_L"]
    work = work.sort_values("net")
    fig, axes = plt.subplots(1, 2, figsize=(6.8, 3.9), dpi=140, gridspec_kw={"width_ratios": [1.4, 1]})
    ax = axes[0]
    colors_bar = [BAR_A if v >= 0 else BAR_B for v in work["net"]]
    ax.barh(range(len(work)), work["net"].values, color=colors_bar)
    ax.set_yticks(range(len(work)))
    ax.set_yticklabels([pair_short(p) for p in work["pair"]], fontsize=5.5)
    ax.axvline(0, color="#333", linewidth=0.5)
    ax.set_xlabel("theta_L_to_R − theta_R_to_L", fontsize=7)
    ax.set_title("Pair net direction", fontsize=8)
    ax2 = axes[1]
    ax2.axis("off")
    text = (
        "System facts (v001 NOTES)\n\n"
        "TCI (H=10) ≈ 54.04\n"
        "PC1 variance ≈ 47.7%\n"
        "PC2 ≈ 19.6%, PC3 ≈ 13.5%\n\n"
        "EURUSD net ≈ +21.7%\n"
        "EURGBP net ≈ −14.6%\n"
        "USDJPY net ≈ −12.0%\n\n"
        "Closest d_ij: AUD-NZD\n"
        "Farthest d_ij: EUR-CHF"
    )
    ax2.text(
        0.05,
        0.95,
        text,
        transform=ax2.transAxes,
        fontsize=7.5,
        va="top",
        family="monospace",
        bbox=dict(boxstyle="round", facecolor="#EDF5F7", edgecolor="#087F8C"),
    )
    top = work.loc[work["net"].abs().idxmax()]
    cap = (
        f"Left: pair net spillover direction. "
        f"Largest |net|: {top['pair']} = {top['net']:.3f}. "
        f"Right: system PCA/TCI from v001 NOTES."
    )
    fig.tight_layout(pad=0.35)
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return out, cap


def make_chart(meta: dict, df: pd.DataFrame) -> tuple[Path, str]:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    out = FIG_DIR / f"m{meta['num']}_{meta['chart']}.png"
    kind = meta["chart"]

    if kind == "heatmap_r":
        return chart_heatmap_r(df, out)
    if kind == "scatter_vs_pearson":
        return chart_scatter(df, meta["x_col"], meta["y_col"], out, f"{meta['name']}: {meta['y_col']} vs {meta['x_col']}")
    if kind == "gap_bars":
        return chart_gap_bars(df, meta["gap_col"], out, f"{meta['name']}: {meta['gap_col']}")
    if kind == "rolling_grouped":
        return chart_rolling(df, out)
    if kind == "adcc_g":
        return chart_adcc_g(df, out)
    if kind == "regime_gap":
        return chart_regime(df, out)
    if kind == "lag_dirs":
        return chart_two_dirs(
            df, "rho_L_to_R_k1", "rho_R_to_L_k1", out, "Lag-1 cross-correlation both ways", "rho(k=1)"
        )
    if kind == "granger_p":
        return chart_granger(df, out)
    if kind == "sorted_bars":
        return chart_sorted_bars(df, meta["bar_col"], out, f"{meta['name']}: {meta['bar_col']}")
    if kind == "te_bias":
        return chart_two_dirs(
            df,
            "te_L_to_R",
            "te_R_to_L",
            out,
            "Transfer entropy both ways",
            "TE (nats)",
            hline=0.0056,
        )
    if kind == "tail_scatter":
        return chart_tail(df, out)
    if kind == "cq_dirs":
        return chart_two_dirs(
            df,
            "rho_L_to_R_t005_k1",
            "rho_R_to_L_t005_k1",
            out,
            "Cross-quantilogram tau=0.05, k=1",
            "rho_tau",
        )
    if kind == "grouped_scales":
        return chart_grouped_scales(df, meta["scale_cols"], out, f"{meta['name']}: scales")
    if kind == "mf_scatter":
        return chart_mf(df, out)
    if kind == "coint_p":
        return chart_coint(df, out)
    if kind == "network":
        return chart_network(df, out)
    raise ValueError(f"Unknown chart kind: {kind}")


# ---- page -------------------------------------------------------------------


def page_flow(meta: dict, styles) -> list:
    df = load_index(meta)
    chart_path, caption = make_chart(meta, df)

    flow: list = []
    flow.append(Paragraph(f"METHOD {meta['num']}", styles["MTag"]))
    flow.append(Paragraph(escape(meta["name"]), styles["MTitle"]))
    flow.append(Paragraph(f"<b>Question:</b> {escape(meta['question'])}", styles["MBody"]))

    flow.append(Paragraph("What this method is", styles["MHead"]))
    flow.append(Paragraph(escape(meta["what_it_is"]), styles["MBody"]))

    flow.append(Paragraph("How we use it in this project", styles["MHead"]))
    flow.append(Paragraph(escape(meta["how_we_use"]), styles["MBody"]))
    flow.append(
        Paragraph(
            f"<b>What you get:</b> {escape(meta['you_get'])}<br/>"
            f"<b>What you do not get:</b> {escape(meta['you_do_not_get'])}",
            styles["MBody"],
        )
    )

    flow.append(Paragraph("Formula", styles["MHead"]))
    flow.append(Paragraph(escape(meta["formula"]).replace("\n", "<br/>"), styles["MFormula"]))
    # One STE sentence that walks the formula using the first terms.
    term_bits = "; ".join(f"{s} = {m}" for s, m in meta["formula_terms"][:3])
    flow.append(
        Paragraph(
            f"<b>Read it:</b> Put your two return series into the formula. {escape(term_bits)}. "
            f"The result is the number this method stores for the pair.",
            styles["MSmall"],
        )
    )
    flow.append(Paragraph("What the symbols mean", styles["MHead"]))
    flow.append(symbol_table(meta["formula_terms"], styles))
    flow.append(Spacer(1, 2))

    flow.append(
        two_col(
            "Pluses",
            meta["plus"],
            "Minuses",
            meta["minus"],
            styles,
            styles["BulletPlus"],
            styles["BulletMinus"],
        )
    )
    flow.append(Spacer(1, 2))
    flow.append(
        Paragraph(
            f"<b>Use it for:</b> {escape(' '.join(meta['use_for']))}<br/>"
            f"<b>Do not use it for:</b> {escape(' '.join(meta['not_for']))}",
            styles["MSmall"],
        )
    )

    flow.append(Paragraph("Chart for this method", styles["MHead"]))
    flow.append(Image(str(chart_path), width=182 * mm, height=92 * mm, kind="proportional"))
    flow.append(Paragraph(escape(caption), styles["Caption"]))
    return flow


def build() -> Path:
    styles = build_styles()
    doc = SimpleDocTemplate(
        str(OUT_PDF),
        pagesize=A4,
        leftMargin=11 * mm,
        rightMargin=11 * mm,
        topMargin=8 * mm,
        bottomMargin=8 * mm,
        title="CU Research — 28 Correlation Methods (One Page Each)",
        author="CU Research One",
    )
    story: list = []
    for i, meta in enumerate(METHODS):
        if i > 0:
            story.append(PageBreak())
        story.extend(page_flow(meta, styles))
    doc.build(story)
    pages = len(PdfReader(str(OUT_PDF)).pages)
    if pages != EXPECTED_PAGES:
        raise SystemExit(f"Expected {EXPECTED_PAGES} pages, got {pages}. PDF: {OUT_PDF}")
    print(f"Wrote {OUT_PDF} ({pages} pages)")
    return OUT_PDF


if __name__ == "__main__":
    build()
