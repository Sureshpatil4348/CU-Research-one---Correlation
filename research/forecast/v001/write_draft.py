"""Write DRAFT.md from the frozen score tables. Does not refit or retune."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

EXP_DIR = Path(__file__).resolve().parent
OUT_DIR = EXP_DIR / "outputs"


def _fmt(value: float, digits: int = 4) -> str:
    if pd.isna(value):
        return "n/a"
    return f"{float(value):.{digits}f}"


def _md(frame: pd.DataFrame) -> str:
    show = frame.copy()
    for col in show.columns:
        if pd.api.types.is_float_dtype(show[col]):
            show[col] = show[col].map(lambda v: "n/a" if pd.isna(v) else f"{float(v):.4f}")
    header = "| " + " | ".join(map(str, show.columns)) + " |"
    rule = "| " + " | ".join("---" for _ in show.columns) + " |"
    body = [
        "| " + " | ".join(str(v) for v in row) + " |"
        for row in show.itertuples(index=False, name=None)
    ]
    return "\n".join([header, rule, *body])


def write() -> Path:
    scores = pd.read_csv(OUT_DIR / "scores.csv")
    crisis = pd.read_csv(OUT_DIR / "crisis.csv")
    sub = pd.read_csv(OUT_DIR / "subperiods.csv")
    overlay = pd.read_csv(OUT_DIR / "overlay.csv")
    manifest = pd.read_json(OUT_DIR / "manifest.json", typ="series")
    t1 = scores[scores["target"] == "T1"].copy()
    base = t1[t1["feature"] == "baseline_r20"].iloc[0]
    winners = t1[t1["beats_baseline"] == True]  # noqa: E712 - CSV booleans
    if len(winners):
        winner = winners.sort_values("brier").iloc[0]
        claim = (
            f"On this frozen majors panel, {winner['feature']} improves next-20-day stress "
            f"forecasts versus rolling Pearson, out of sample, after Benjamini-Hochberg control "
            f"(Brier {_fmt(winner['brier'])} versus {_fmt(base['brier'])})."
        )
    else:
        winner = None
        claim = (
            "On this frozen majors panel, no shortlist measure improves next-20-day stress "
            "forecasts versus rolling Pearson, out of sample, after Benjamini-Hochberg control."
        )
    show_cols = ["feature", "role", "n", "brier", "auc", "brier_minus_baseline", "dm_p_one_sided", "bh_q", "in_mcs", "beats_baseline"]
    t1_show = t1[show_cols].copy()
    t2 = scores[scores["target"] == "T2"][show_cols].copy()
    t1_show["in_mcs"] = t1_show["in_mcs"].fillna("")
    t2["in_mcs"] = t2["in_mcs"].fillna("")
    crisis_names = ["baseline_r20"]
    if winner is not None:
        crisis_names.append(str(winner["feature"]))
    base_crisis = crisis[crisis["feature"].isin(crisis_names)][
        ["feature", "window", "n_pre", "hit_rate", "n_shade", "in_shade_rate", "false_alarm_rate"]
    ]
    early_names = ["baseline_r20", "diagnostic_rv20"]
    early = sub[(sub["target"] == "T1") & (sub["period"] == "through_2007") & (sub["feature"].isin(early_names))]
    late = sub[(sub["target"] == "T1") & (sub["period"] == "2020_end") & (sub["feature"].isin(early_names))]
    if winner is not None:
        early_names.append(str(winner["feature"]))
        early = sub[(sub["target"] == "T1") & (sub["period"] == "through_2007") & (sub["feature"].isin(early_names))]
        late = sub[(sub["target"] == "T1") & (sub["period"] == "2020_end") & (sub["feature"].isin(early_names))]
    lines = [
        "# Draft: which dependence measure warns before stress?",
        "",
        claim,
        "",
        (
            f"T1 winner under the frozen rule: `{winner['feature']}`."
            if winner is not None
            else "T1 winner under the frozen rule: none."
        ),
        "",
        "The test is the frozen protocol in `PROTOCOL.md`. v001 was not overwritten. "
        "The catalogue of the 28 full-sample methods remains "
        "[reports/Correlation_Methods_28_Pages.pdf](../../../reports/Correlation_Methods_28_Pages.pdf).",
        "",
        "## 1. Did the features use only time-t information?",
        "",
        "Yes. Each feature row is dated t and uses returns on or before t. "
        "Training labels are embargoed by 20 trading days, so a label whose window "
        "runs through t+20 is not used to fit a model that is scored on that window. "
        "ADCC parameters are refit at each year-end and are not revised backward. "
        "The 90th percentile for the stress label uses only forward windows that have already ended.",
        "",
        "## 2. Did any measure beat rolling Pearson?",
        "",
        f"Primary baseline Brier score on T1: {_fmt(base['brier'])} (n={int(base['n'])}). "
        "A negative Brier gap means a lower Brier score than `baseline_r20`. "
        "`beats_baseline` is true only when that gap is negative and the Benjamini-Hochberg q-value is below 0.05.",
        "",
        "### T1 stress",
        "",
        _md(t1_show),
        "",
        "### T2 correlation break (secondary)",
        "",
        _md(t2),
        "",
        (
            "Secondary T2 features with a lower Brier score and BH q below 0.05: "
            + (", ".join(f"`{name}`" for name in t2.loc[t2["beats_baseline"] == True, "feature"]) or "none")  # noqa: E712
            + ". That target is not the primary horse race, and it does not name a T1 winner."
        ),
        "",
        "The model confidence set is the 90% Hansen set on day-level Brier losses. "
        "`diagnostic_rv20` is lagged realised volatility. It is not in the horse race.",
        "",
        "## 3. Were the many tests controlled?",
        "",
        "Yes for the horse race. There are nine pre-registered competitors. "
        "Diebold-Mariano p-values are one-sided for a lower Brier score, with Newey-West lag 20, "
        "then Benjamini-Hochberg at 0.05. The confidence set uses a block bootstrap of length 20 "
        "and 400 draws. Cointegration, transfer entropy, and the ADCC likelihood-ratio tests "
        "in the v002 experiments have their own multiplicity or boundary corrections, and those "
        "tables are not re-opened here.",
        "",
        "## 4. Did the signal work before 2008 and 2020, or only inside the crash?",
        "",
        "Hit rate is the share of the 20 trading days before a shade with the signal on. "
        "A signal that appears only inside the shade is not an early warning. "
        "In-shade rate is reported separately. False-alarm rate is the share of out-of-sample "
        "days outside every shade and every pre-window. "
        "The table is the rolling-Pearson T1 signal, because that rule is the one the protocol keeps when no competitor wins.",
        "",
        "### T1 signals",
        "",
        _md(base_crisis),
        "",
        "### T1 Brier score through 2007",
        "",
        _md(early[["feature", "n", "brier", "brier_minus_baseline"]]),
        "",
        "### T1 Brier score from 2020",
        "",
        _md(late[["feature", "n", "brier", "brier_minus_baseline"]]),
        "",
        "Subperiod Brier scores for every feature are in `outputs/subperiods.csv`. "
        "The through-2007 slice is the out-of-sample predictions whose signal date is on or before 2007-12-31. "
        "It does not refit on later data.",
        "",
        "## 5. Is there a simple economic use with costs?",
        "",
        "The book is the equal-weight mean of the eight major log returns. "
        "The position for the next day is flat when the T1 signal is on, and long otherwise. "
        "The signal cut is the 80th percentile of training probabilities. "
        "Cost is 1 basis point of the absolute position change, and the book starts from flat. "
        "Net log growth is the sum of position times the next-day basket return, minus that cost.",
        "",
        _md(overlay),
        "",
        "## What this draft does not claim",
        "",
        "It does not name the day of a crash. It does not add a new dependence formula. "
        f"Protocol SHA-256 recorded with the scores: `{manifest['protocol_sha256']}`.",
        "",
    ]
    path = EXP_DIR / "DRAFT.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(path, flush=True)
    return path


if __name__ == "__main__":
    write()
