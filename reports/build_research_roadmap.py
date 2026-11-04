"""Build Research_Roadmap.pdf — clear 12-page research plan (ASD-STE100 style)."""

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
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_PDF = Path(__file__).resolve().parent / "Research_Roadmap.pdf"
FIG_DIR = Path(__file__).resolve().parent / "figures"
SNAPSHOT = REPO_ROOT / "data" / "snapshots" / "2026-11-03_majors_alpari_D1"

COLOR_HEAD = colors.HexColor("#15364A")
COLOR_SUB = colors.HexColor("#087F8C")
COLOR_BOX = colors.HexColor("#EDF5F7")
COLOR_WARN = colors.HexColor("#FFF3E0")
COLOR_OK = colors.HexColor("#E8F5E9")


def stylesheet():
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="RTitle",
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            textColor=COLOR_HEAD,
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="RHead",
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=17,
            textColor=COLOR_HEAD,
            spaceBefore=4,
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="RSub",
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=COLOR_SUB,
            spaceBefore=8,
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            name="RBody",
            fontName="Helvetica",
            fontSize=10.5,
            leading=14,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="RSmall",
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            spaceAfter=3,
        )
    )
    styles.add(
        ParagraphStyle(
            name="RTag",
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=11,
            textColor=COLOR_SUB,
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            name="RBox",
            fontName="Helvetica",
            fontSize=10,
            leading=13,
            backColor=COLOR_BOX,
            borderPadding=8,
            spaceBefore=4,
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="RCaption",
            fontName="Helvetica-Oblique",
            fontSize=9,
            leading=11,
            textColor=colors.HexColor("#333333"),
            spaceBefore=4,
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            name="RBullet",
            fontName="Helvetica",
            fontSize=10.5,
            leading=14,
            leftIndent=8,
            spaceAfter=3,
        )
    )
    return styles


def p(story, text, style):
    story.append(Paragraph(text, style))


def card(styles, title: str, rows: list[tuple[str, str]], bg=COLOR_BOX) -> KeepTogether:
    """A labelled card: title + label/value rows."""
    data = [[Paragraph(f"<b>{escape(title)}</b>", styles["RSub"]), ""]]
    for lab, val in rows:
        data.append(
            [
                Paragraph(f"<b>{escape(lab)}</b>", styles["RSmall"]),
                Paragraph(escape(val), styles["RSmall"]),
            ]
        )
    t = Table(data, colWidths=[38 * mm, 142 * mm])
    t.setStyle(
        TableStyle(
            [
                ("SPAN", (0, 0), (-1, 0)),
                ("BACKGROUND", (0, 0), (-1, -1), bg),
                ("BOX", (0, 0), (-1, -1), 0.8, COLOR_SUB),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return KeepTogether([t, Spacer(1, 10)])


def make_turbulence_chart() -> Path:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    out = FIG_DIR / "turbulence_2008_2020.png"

    sys.path.insert(0, str(REPO_ROOT))
    from shared.mt5_data import load_snapshot

    snap = load_snapshot(SNAPSHOT)
    series = {}
    for name, frame in snap["frames"].items():
        f = frame.copy()
        f["time"] = pd.to_datetime(f["time"], utc=True).dt.tz_localize(None)
        f = f.sort_values("time")
        if len(f) > 1:
            f = f.iloc[:-1]
        lr = np.log(f["close"].astype(float)).diff()
        series[name] = pd.Series(lr.values, index=pd.DatetimeIndex(f["time"].values), name=name)
    panel = pd.concat(series.values(), axis=1, join="inner").dropna()
    turb_ma = panel.abs().mean(axis=1).rolling(20, min_periods=10).mean()

    fig, ax = plt.subplots(figsize=(7.4, 3.6), dpi=140)
    crisis_2008 = (turb_ma.index >= pd.Timestamp("2008-01-01")) & (
        turb_ma.index <= pd.Timestamp("2009-06-30")
    )
    crisis_2020 = (turb_ma.index >= pd.Timestamp("2020-02-01")) & (
        turb_ma.index <= pd.Timestamp("2020-06-30")
    )
    ax.fill_between(
        turb_ma.index, 0, turb_ma.values, where=crisis_2008, color="#D55E00", alpha=0.28, label="2008-09 crisis"
    )
    ax.fill_between(
        turb_ma.index, 0, turb_ma.values, where=crisis_2020, color="#CC79A7", alpha=0.32, label="2020 COVID shock"
    )
    ax.plot(turb_ma.index, turb_ma.values, color="#0072B2", linewidth=1.0, label="20-day mean |r|")
    ax.set_title("FX turbulence across eight majors", fontsize=11, pad=6)
    ax.set_ylabel("mean |daily log return|", fontsize=9)
    ax.legend(fontsize=8, loc="upper right", frameon=False)
    ax.tick_params(labelsize=8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return out


def make_flow_diagram() -> Path:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    out = FIG_DIR / "research_flow.png"
    steps = [
        ("1. Fix stats", "v002 NOTES"),
        ("2. Time-t\nfeatures", "feature panel"),
        ("3. Define\ntargets", "label rule"),
        ("4. OOS\nhorse race", "OOS table"),
        ("5. Crisis\nwindows", "hit rates"),
        ("6. Robust\nchecks", "subperiod"),
        ("7. Economic\nvalue", "overlay P&L"),
        ("8. Write\npaper", "draft"),
    ]
    fig, ax = plt.subplots(figsize=(7.4, 2.2), dpi=140)
    ax.set_xlim(0, 8)
    ax.set_ylim(0, 1.15)
    ax.axis("off")
    for i, (label, out_name) in enumerate(steps):
        x0 = i + 0.06
        rect = plt.Rectangle(
            (x0, 0.38), 0.88, 0.52, facecolor="#EDF5F7", edgecolor="#087F8C", linewidth=1.3
        )
        ax.add_patch(rect)
        ax.text(i + 0.5, 0.68, label, ha="center", va="center", fontsize=7.5, color="#15364A")
        ax.text(i + 0.5, 0.18, out_name, ha="center", va="center", fontsize=7, color="#087F8C")
        if i < len(steps) - 1:
            ax.annotate(
                "",
                xy=(i + 1.02, 0.64),
                xytext=(i + 0.96, 0.64),
                arrowprops=dict(arrowstyle="->", color="#15364A", lw=1.2),
            )
    ax.set_title("Research flow — do the steps in this order", fontsize=10, color="#15364A", pad=4)
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return out


def gap_overview_table(styles) -> Table:
    rows = [
        [
            Paragraph("<b>Gap</b>", styles["RSmall"]),
            Paragraph("<b>v001 fact</b>", styles["RSmall"]),
            Paragraph("<b>Fix</b>", styles["RSmall"]),
        ],
        [
            Paragraph("Cointegration p", styles["RSmall"]),
            Paragraph("Raw p&lt;0.05 on a few pairs; 28 tests.", styles["RSmall"]),
            Paragraph("Bonferroni / FDR. Report corrected hits only.", styles["RSmall"]),
        ],
        [
            Paragraph("Transfer entropy", styles["RSmall"]),
            Paragraph("Scores ≈ 0.004–0.009 nats; bias ≈ 0.0056.", styles["RSmall"]),
            Paragraph("Shuffle / surrogate tests before claims.", styles["RSmall"]),
        ],
        [
            Paragraph("ADCC / DCC fits", styles["RSmall"]),
            Paragraph("EURUSD-USDCHF has b=0.5; some g=0 on bound.", styles["RSmall"]),
            Paragraph("Re-fit. Check convergence. LR-test g.", styles["RSmall"]),
        ],
        [
            Paragraph("EURGBP in panel", styles["RSmall"]),
            Paragraph("PC8 eigenvalue ≈ 0.0046 (near singular).", styles["RSmall"]),
            Paragraph("Drop or orthogonalise for PCA / VAR.", styles["RSmall"]),
        ],
        [
            Paragraph("Stress correlation", styles["RSmall"]),
            Paragraph("Raw stress rho rises with volatility.", styles["RSmall"]),
            Paragraph("Forbes–Rigobon adjust or bootstrap the gap.", styles["RSmall"]),
        ],
        [
            Paragraph("Tail benchmark", styles["RSmall"]),
            Paragraph("Independence is the wrong yardstick.", styles["RSmall"]),
            Paragraph("Compare L_hat to Gaussian with same r.", styles["RSmall"]),
        ],
        [
            Paragraph("No OOS test", styles["RSmall"]),
            Paragraph("All v001 work is full-sample description.", styles["RSmall"]),
            Paragraph("Build time-t features and forecast targets.", styles["RSmall"]),
        ],
    ]
    t = Table(rows, colWidths=[36 * mm, 72 * mm, 72 * mm])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DBEDF0")),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#B8CCD2")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7FBFC")]),
            ]
        )
    )
    return t


def checklist_table(styles) -> Table:
    rows = [
        [
            Paragraph("<b>#</b>", styles["RSmall"]),
            Paragraph("<b>Task</b>", styles["RSmall"]),
            Paragraph("<b>Why</b>", styles["RSmall"]),
            Paragraph("<b>Output</b>", styles["RSmall"]),
        ],
        [
            Paragraph("1", styles["RSmall"]),
            Paragraph("Fix statistical gaps", styles["RSmall"]),
            Paragraph("Stops false claims before forecasts.", styles["RSmall"]),
            Paragraph("Method folders: experiments/v002/NOTES.md", styles["RSmall"]),
        ],
        [
            Paragraph("2", styles["RSmall"]),
            Paragraph("Build time-t measures", styles["RSmall"]),
            Paragraph("No look-ahead in features.", styles["RSmall"]),
            Paragraph("Dated feature panel (CSV/parquet)", styles["RSmall"]),
        ],
        [
            Paragraph("3", styles["RSmall"]),
            Paragraph("Define targets", styles["RSmall"]),
            Paragraph("Makes the question testable.", styles["RSmall"]),
            Paragraph("Written label rule in NOTES.md first", styles["RSmall"]),
        ],
        [
            Paragraph("4", styles["RSmall"]),
            Paragraph("OOS horse race", styles["RSmall"]),
            Paragraph("Shows who beats Pearson.", styles["RSmall"]),
            Paragraph("OOS score table + DM / MCS", styles["RSmall"]),
        ],
        [
            Paragraph("5", styles["RSmall"]),
            Paragraph("Crisis window tests", styles["RSmall"]),
            Paragraph("Checks 2008, SNB, 2020, 2022.", styles["RSmall"]),
            Paragraph("Hit / false-alarm rates by window", styles["RSmall"]),
        ],
        [
            Paragraph("6", styles["RSmall"]),
            Paragraph("Robustness", styles["RSmall"]),
            Paragraph("Result must hold in more than one decade.", styles["RSmall"]),
            Paragraph("Subperiod tables", styles["RSmall"]),
        ],
        [
            Paragraph("7", styles["RSmall"]),
            Paragraph("Economic value", styles["RSmall"]),
            Paragraph("Links stats to desk use.", styles["RSmall"]),
            Paragraph("Simple hedge / vol overlay with costs", styles["RSmall"]),
        ],
        [
            Paragraph("8", styles["RSmall"]),
            Paragraph("Write the paper", styles["RSmall"]),
            Paragraph("One clear claim for institutes and desks.", styles["RSmall"]),
            Paragraph("Draft; 28-method PDF as appendix", styles["RSmall"]),
        ],
    ]
    t = Table(rows, colWidths=[10 * mm, 38 * mm, 62 * mm, 70 * mm])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DBEDF0")),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#B8CCD2")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return t


def step_block(styles, num: str, title: str, do: str, produce: str, done: str) -> KeepTogether:
    body = (
        f"<b>Do this:</b> {escape(do)}<br/>"
        f"<b>Produce this:</b> {escape(produce)}<br/>"
        f"<b>Done when:</b> {escape(done)}"
    )
    data = [
        [Paragraph(f"<b>Step {num} — {escape(title)}</b>", styles["RSub"])],
        [Paragraph(body, styles["RBody"])],
    ]
    t = Table(data, colWidths=[180 * mm])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), COLOR_BOX),
                ("BOX", (0, 0), (-1, -1), 0.6, COLOR_SUB),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return KeepTogether([t, Spacer(1, 8)])


def build() -> Path:
    styles = stylesheet()
    turb_path = make_turbulence_chart()
    flow_path = make_flow_diagram()

    doc = SimpleDocTemplate(
        str(OUT_PDF),
        pagesize=A4,
        leftMargin=14 * mm,
        rightMargin=14 * mm,
        topMargin=12 * mm,
        bottomMargin=12 * mm,
        title="CU Research — Research Roadmap",
        author="CU Research One",
    )
    story: list = []

    # ---- Page 1: what this document is ----
    p(story, "RESEARCH ROADMAP", styles["RTag"])
    p(story, "From 28 methods to a real prediction test", styles["RTitle"])
    p(
        story,
        "This document uses simple technical English (ASD-STE100 style, about 80%). "
        "It states one idea per page. It uses facts from the v001 experiments.",
        styles["RBody"],
    )
    p(story, "1. What this document is", styles["RHead"])
    p(
        story,
        "<b>Core research question (docs/DATA.md):</b> "
        "Which dependence measure is most useful for a later up, down, or crash read "
        "on these eight major FX pairs?",
        styles["RBox"],
    )
    p(
        story,
        "A list of 28 correlations is a catalogue. It is not the answer. "
        "A fair answer needs three parts:",
        styles["RBody"],
    )
    for item in [
        "<b>A target</b> — what you try to predict (vol spike, drawdown, or correlation break).",
        "<b>A time-t feature</b> — a measure that uses only data available at day t.",
        "<b>An out-of-sample test</b> — train on the past, score on later data.",
    ]:
        p(story, "• " + item, styles["RBullet"])
    p(story, "How to use the two PDFs", styles["RSub"])
    p(
        story,
        "• <b>Correlation_Methods_28_Pages.pdf</b> — how each method works (the catalogue).<br/>"
        "• <b>Research_Roadmap.pdf</b> (this file) — what to fix, what to test, and in what order.",
        styles["RBody"],
    )
    p(
        story,
        "Do not send the catalogue alone to a desk and call it a prediction paper. "
        "Close the gaps on the next pages first.",
        styles["RBody"],
    )
    p(story, "Page map of this roadmap", styles["RSub"])
    p(
        story,
        "2 — Where the project is (assets and blockers)<br/>"
        "3 — Seven gaps in one table<br/>"
        "4–5 — Gap cards with done-conditions<br/>"
        "6 — Known results vs your real edge<br/>"
        "7–8 — Crash prediction honesty and how to read turbulence<br/>"
        "9–10 — Eight research steps mapped to this repo<br/>"
        "11 — Work board checklist<br/>"
        "12 — What success is, and five desk questions",
        styles["RBody"],
    )

    # ---- Page 2: where the project is ----
    story.append(PageBreak())
    p(story, "2. Where the project is now", styles["RHead"])
    p(
        story,
        "<b>Data:</b> eight majors (EURUSD, GBPUSD, AUDUSD, NZDUSD, USDJPY, USDCHF, USDCAD, EURGBP). "
        "Timeframe D1. Snapshot <font face='Courier'>2026-11-03_majors_alpari_D1</font>. "
        "Range about 1999–2026 (~7,200 bars per pair).",
        styles["RBody"],
    )
    p(story, "Assets you already have", styles["RSub"])
    for item in [
        "A frozen price snapshot that all methods share.",
        "Twenty-eight implemented formulas with v001 indexes and pair reports.",
        "A watchlist of rolling breaks (method 05).",
        "System PCA and connectedness for the eight-major panel (method 28).",
        "A one-page method catalogue PDF for every formula.",
    ]:
        p(story, "• " + item, styles["RBullet"])
    p(story, "Blockers you do not have yet", styles["RSub"])
    for item in [
        "Out-of-sample forecast scores versus Pearson and rolling Pearson.",
        "Bias and multiplicity controls on several methods.",
        "A written target definition for crash or stress labels.",
        "An early-warning test on 2008, SNB 2011–15, 2020, and 2022.",
    ]:
        p(story, "• " + item, styles["RBullet"])
    p(
        story,
        "All current results describe the full sample. "
        "They do not yet forecast the next move. "
        "They do not yet give an out-of-sample early warning.",
        styles["RBox"],
    )

    # ---- Page 3: seven gaps overview ----
    story.append(PageBreak())
    p(story, "3. Seven gaps in the current results", styles["RHead"])
    p(
        story,
        "Fix these problems before you claim prediction power. "
        "Each row is one gap from the v001 notes and cross-checks.",
        styles["RBody"],
    )
    story.append(gap_overview_table(styles))
    story.append(Spacer(1, 12))
    p(
        story,
        "The next two pages open the main gaps as cards. "
        "Each card states what is wrong, the number, what you do next, and when the gap is closed.",
        styles["RBody"],
    )

    # ---- Page 4: gap cards A ----
    story.append(PageBreak())
    p(story, "4. Gap cards — cointegration and transfer entropy", styles["RHead"])
    story.append(
        card(
            styles,
            "Gap A1 — Cointegration p-values (method 27)",
            [
                (
                    "What is wrong",
                    "A few pairs show raw p below 0.05 (for example EURUSD-USDCAD). "
                    "With 28 tests, about 1.4 false hits are expected at 5% by chance.",
                ),
                (
                    "The number",
                    "Bonferroni cut = 0.05 / 28 ≈ 0.0018. After that cut, no pair stays significant in v001.",
                ),
                (
                    "What you do next",
                    "Apply Bonferroni or FDR. State the honest finding: no robust cointegration on this design.",
                ),
                (
                    "Done when",
                    "A v002 NOTES.md table shows raw p, corrected p, and which pairs survive.",
                ),
            ],
            bg=COLOR_WARN,
        )
    )
    story.append(
        card(
            styles,
            "Gap A2 — Transfer entropy bias (method 17)",
            [
                (
                    "What is wrong",
                    "Discrete plug-in TE with B=5 bins and lag 1 has a positive bias under independence.",
                ),
                (
                    "The number",
                    "Bias size ≈ (B−1)^2·B / (2N) ≈ 0.0056 nats for N≈7200. "
                    "Many TE scores sit between about 0.004 and 0.009 nats.",
                ),
                (
                    "What you do next",
                    "Run shuffle or surrogate tests. Keep only scores that clear the null.",
                ),
                (
                    "Done when",
                    "A v002 NOTES.md ranks directed TE only after the null test, with a clear pass/fail flag.",
                ),
            ],
            bg=COLOR_WARN,
        )
    )

    # ---- Page 5: gap cards B ----
    story.append(PageBreak())
    p(story, "5. Gap cards — fits, EURGBP, stress, tails", styles["RHead"])
    story.append(
        card(
            styles,
            "Gap B1 — ADCC / DCC convergence (methods 09–10)",
            [
                ("What is wrong", "EURUSD-USDCHF shows b = 0.500000 while other pairs have b near 0.89–0.99."),
                ("The number", "Some pairs also show g = 0.000000 on the bound."),
                ("What you do next", "Re-fit. Check convergence. Run a likelihood-ratio test for g."),
                ("Done when", "Every pair has a status flag and a documented fit check in v002."),
            ],
            bg=COLOR_WARN,
        )
    )
    story.append(
        card(
            styles,
            "Gap B2 — EURGBP redundancy (method 28)",
            [
                ("What is wrong", "EURGBP is close to EURUSD minus GBPUSD in log returns."),
                ("The number", "PC8 eigenvalue ≈ 0.0046 — the panel is almost singular."),
                ("What you do next", "Drop EURGBP from system VAR/PCA, or orthogonalise it."),
                ("Done when", "System metrics rerun without the redundant leg, with NOTES updated."),
            ],
            bg=COLOR_WARN,
        )
    )
    story.append(
        card(
            styles,
            "Gap B3 — Stress correlation bias (method 11)",
            [
                ("What is wrong", "Raw correlation often rises when volatility rises, even if structure is unchanged."),
                ("The number", "Largest |stress − quiet| gaps include AUDUSD-USDJPY ≈ +0.267."),
                ("What you do next", "Apply Forbes–Rigobon adjustment or bootstrap the gap."),
                ("Done when", "Quiet/stress table reports adjusted gaps with a significance note."),
            ],
            bg=COLOR_WARN,
        )
    )
    story.append(
        card(
            styles,
            "Gap B4 — Tail benchmark (method 19)",
            [
                ("What is wrong", "Comparing L_hat only to independence is the wrong yardstick."),
                ("The number", "Example: AUDUSD-NZDUSD lower-tail L_hat ≈ 0.583 at alpha=0.05."),
                ("What you do next", "Compare L_hat to the co-exceedance a Gaussian with the same Pearson r would give."),
                ("Done when", "Each pair has L_hat, Gaussian benchmark, and excess = L_hat − benchmark."),
            ],
            bg=COLOR_WARN,
        )
    )

    # ---- Page 6: known vs new ----
    story.append(PageBreak())
    p(story, "6. Results that are real but already known", styles["RHead"])
    p(
        story,
        "Keep these as validation. Do not sell them as the only discovery. "
        "A desk will ask: what is new after these known facts?",
        styles["RBody"],
    )
    known = [
        (
            "Dollar factor",
            "Method 07: EURUSD–AUDUSD Pearson r ≈ 0.557 falls to rho_partial ≈ −0.016 after the USD control. "
            "Much of the raw link was the dollar.",
        ),
        (
            "Carry crash risk",
            "Method 19: AUDUSD–USDJPY has near-zero full-sample r (≈ −0.088) but lower-tail L_hat ≈ 0.169. "
            "Crash co-movement is larger than the average link.",
        ),
        (
            "Asymmetric correlation",
            "Method 10: USDCHF–USDCAD has the largest g ≈ 0.047. "
            "Joint downs can move correlation more than joint ups.",
        ),
        (
            "Connectedness",
            "Method 28: system TCI ≈ 54.0; EURUSD net ≈ +21.7%. "
            "EURUSD acts as a net shock transmitter in this panel.",
        ),
    ]
    for title, body in known:
        p(story, title, styles["RSub"])
        p(story, body, styles["RBody"])
    p(
        story,
        "<b>Your edge:</b> the joint bank of 28 methods on one frozen snapshot. "
        "Use that edge for a forecast horse race, not for a longer list of static tables.",
        styles["RBox"],
    )

    # ---- Page 7: prediction honesty + chart ----
    story.append(PageBreak())
    p(story, "7. Can we predict a crash like 2008 or COVID-19?", styles["RHead"])
    p(
        story,
        "No method here gives the exact date of a crash. "
        "Markets do not publish a calendar of crises. "
        "Do not promise date prediction to institutes or desks.",
        styles["RBody"],
    )
    # two labelled boxes side by side
    left = Paragraph(
        "<b>Predict the date</b><br/><br/>"
        "Name the day of a crash in advance.<br/><br/>"
        "<b>Do not claim this.</b>",
        styles["RBody"],
    )
    right = Paragraph(
        "<b>Detect risk build-up</b><br/><br/>"
        "Show that selected measures move before stress windows more often than Pearson alone.<br/><br/>"
        "<b>This is the paper.</b>",
        styles["RBody"],
    )
    twin = Table([[left, right]], colWidths=[88 * mm, 88 * mm])
    twin.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, 0), COLOR_WARN),
                ("BACKGROUND", (1, 0), (1, 0), COLOR_OK),
                ("BOX", (0, 0), (0, 0), 0.8, colors.HexColor("#E65100")),
                ("BOX", (1, 0), (1, 0), 0.8, colors.HexColor("#2E7D32")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (0, 0), 14),
            ]
        )
    )
    story.append(twin)
    story.append(Spacer(1, 10))
    story.append(Image(str(turb_path), width=178 * mm, height=86 * mm, kind="proportional"))
    p(
        story,
        "Figure: 20-day mean of equal-weight |daily log returns| across the eight majors. "
        "Orange shade = 2008–09. Pink shade = early 2020. "
        "Turbulence rises in those windows.",
        styles["RCaption"],
    )

    # ---- Page 8: how to read the chart / test ----
    story.append(PageBreak())
    p(story, "8. How to read the turbulence chart — and what to test", styles["RHead"])
    p(story, "What the axis means", styles["RSub"])
    p(
        story,
        "Each day, take the absolute log return of each of the eight majors. "
        "Average those eight values. "
        "Then take a 20-day mean of that series. "
        "A high value means the majors moved a lot together in absolute terms.",
        styles["RBody"],
    )
    p(story, "What the shaded bands are", styles["RSub"])
    p(
        story,
        "• <b>2008–09:</b> global financial crisis window.<br/>"
        "• <b>Early 2020:</b> COVID market shock window.",
        styles["RBody"],
    )
    p(story, "The research test (write this in NOTES before you run it)", styles["RSub"])
    p(
        story,
        "At each day t before a shaded window, compute features with data ≤ t only "
        "(for example ADCC − Pearson, or |r_20 − baseline|). "
        "Ask: do these gaps rise in the weeks before the shade, or only inside the shade?",
        styles["RBox"],
    )
    p(
        story,
        "Score hit rate and false-alarm rate against rolling Pearson. "
        "A signal that fires only after the crash has low value for desks.",
        styles["RBody"],
    )
    p(story, "Crisis windows to mark", styles["RSub"])
    for item in [
        "2008–09 global financial crisis",
        "SNB EUR/CHF floor period and Jan 2015 removal",
        "2020 COVID shock",
        "2022 rate-shock / risk-off period",
    ]:
        p(story, "• " + item, styles["RBullet"])

    # ---- Page 9: eight steps ----
    story.append(PageBreak())
    p(story, "9. How to research the core issue — eight steps", styles["RHead"])
    p(
        story,
        "Do the work in this order. "
        "Do not jump to a custom formula before the tests.",
        styles["RBody"],
    )
    story.append(Image(str(flow_path), width=178 * mm, height=52 * mm, kind="proportional"))
    p(
        story,
        "Figure: each box is a step. The label under the box is the file or table you must produce.",
        styles["RCaption"],
    )
    story.append(
        step_block(
            styles,
            "1",
            "Fix the statistical problems",
            "Close gaps A1–B4 (multiplicity, TE null, DCC fits, EURGBP, stress bias, Gaussian tails).",
            "v002 NOTES.md in each affected method folder.",
            "Every gap has a corrected table and a one-line done statement.",
        )
    )
    story.append(
        step_block(
            styles,
            "2",
            "Build time-t features",
            "Expanding or rolling windows with no future data for the shortlist.",
            "A dated feature panel for methods 01, 05, 07, 10, 11/19, 14, 28.",
            "Every cell uses only information available at date t.",
        )
    )

    # ---- Page 10: steps continued + repo specifics ----
    story.append(PageBreak())
    p(story, "10. Steps 3–8 and how they map to this repo", styles["RHead"])
    story.append(
        step_block(
            styles,
            "3",
            "Define the targets",
            "Pick one or two labels before you look at results.",
            "A written label rule in NOTES.md.",
            "The rule is frozen before any forecast score is computed.",
        )
    )
    p(story, "Example targets (choose before you look)", styles["RSub"])
    for item in [
        "Next-20-day realised-vol spike above the 90th percentile of past vol.",
        "Pair drawdown beyond a fixed threshold in the next 20 days.",
        "Correlation break: |r_20 − baseline| above a pre-set cut.",
    ]:
        p(story, "• " + item, styles["RBullet"])
    story.append(
        step_block(
            styles,
            "4",
            "Out-of-sample horse race",
            "Train on past data. Score on later data. Compare each measure to Pearson and rolling Pearson.",
            "OOS score table with Diebold–Mariano tests and a model confidence set.",
            "A clear winner set — or a clear statement that nothing beats the baseline.",
        )
    )
    story.append(
        step_block(
            styles,
            "5–8",
            "Crisis tests, robustness, economic value, paper",
            "Run early-warning on crisis windows; repeat on subperiods; test a simple overlay with costs; write the paper.",
            "Hit rates, subperiod tables, overlay P&amp;L, draft with the 28-method PDF as appendix.",
            "You can answer the five desk questions on page 12 with tables.",
        )
    )
    p(story, "Version rule", styles["RSub"])
    p(
        story,
        "New work is experiments/v002, v003, … "
        "Do not overwrite v001. See docs/VERSIONING.md.",
        styles["RBox"],
    )
    p(story, "Shortlist for deep work", styles["RSub"])
    p(
        story,
        "01 Pearson · 05 Rolling · 07 Partial · 10 ADCC · 11 Regime · 19 Tail · "
        "14 Distance correlation · 28 Networks / PCA / Connectedness. "
        "Keep the other methods in the appendix catalogue.",
        styles["RBody"],
    )

    # ---- Page 11: work board ----
    story.append(PageBreak())
    p(story, "11. Work board — checklist and order", styles["RHead"])
    p(
        story,
        "Use this table as your work board. "
        "Finish row 1 before you invent a new formula.",
        styles["RBody"],
    )
    story.append(checklist_table(styles))
    story.append(Spacer(1, 14))
    p(story, "Daily habit", styles["RSub"])
    for item in [
        "Open one gap. Close it. Write a short NOTES.md. Stop.",
        "Do not mix a new formula and a new forecast test in the same day.",
        "Keep v001 folders immutable. Always create v002, v003, …",
    ]:
        p(story, "• " + item, styles["RBullet"])

    # ---- Page 12: success + desk questions ----
    story.append(PageBreak())
    p(story, "12. What success is — and what a desk will ask", styles["RHead"])
    p(
        story,
        "Success is not “28 correlations exist.” "
        "Success is a clear, tested statement such as:",
        styles["RBody"],
    )
    p(
        story,
        "“On this frozen majors panel, measure X improves next-horizon stress or correlation-break "
        "forecasts versus rolling Pearson, out of sample, after multiplicity control.”",
        styles["RBox"],
    )
    p(
        story,
        "If no measure beats the baseline, that result is still publishable. "
        "Report it without force.",
        styles["RBody"],
    )
    p(story, "Five yes/no questions a hedge fund will ask", styles["RSub"])
    for i, q in enumerate(
        [
            "Did you use only time-t information?",
            "Did you beat a simple rolling Pearson baseline?",
            "Did you control for many tests?",
            "Did the signal work before 2008/2020, not only inside the crash?",
            "Is there a simple economic use case with costs?",
        ],
        start=1,
    ):
        p(story, f"{i}. {q}", styles["RBullet"])
    p(story, "How to rebuild this PDF", styles["RSub"])
    p(
        story,
        "From the repo root:<br/>"
        "<font face='Courier'>python reports/build_research_roadmap.py</font><br/><br/>"
        "Method catalogue:<br/>"
        "<font face='Courier'>python reports/build_methods_overview.py</font>",
        styles["RBox"],
    )
    p(
        story,
        "Prepared for CU Research One — Correlation. "
        "Writing aims for ASD-STE100 style (about 80%). "
        "Formula names and statistical terms are exempt.",
        styles["RSmall"],
    )

    doc.build(story)
    pages = len(PdfReader(str(OUT_PDF)).pages)
    print(f"Wrote {OUT_PDF} ({pages} pages)")
    if pages < 10 or pages > 14:
        print(f"WARNING: expected about 12 pages, got {pages}")
    return OUT_PDF


if __name__ == "__main__":
    build()
