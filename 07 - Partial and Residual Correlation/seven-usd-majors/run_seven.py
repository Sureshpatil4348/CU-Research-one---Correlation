"""Seven USD majors: full-sample partial correlation vs rolling pace.

Named dig under method 07. EURGBP excluded. experiments/v001 untouched.
"""

from __future__ import annotations

import html
import itertools
import math
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from shared.mt5_data import load_snapshot

SNAPSHOT_REL = Path("data/snapshots/2026-11-03_majors_alpari_D1")
EXP_DIR = Path(__file__).resolve().parent
OUT_DIR = EXP_DIR / "outputs"
FIG_DIR = OUT_DIR / "figures"

SEVEN = (
    "EURUSD",
    "GBPUSD",
    "AUDUSD",
    "NZDUSD",
    "USDJPY",
    "USDCHF",
    "USDCAD",
)
WINDOWS = (20, 60, 100)
HEADLINE_W = 60

USD_QUOTE_PAIRS = ("EURUSD", "GBPUSD", "AUDUSD", "NZDUSD")
USD_BASE_PAIRS = ("USDJPY", "USDCHF", "USDCAD")
USD_FACTOR_CANDIDATES = USD_QUOTE_PAIRS + USD_BASE_PAIRS

CURRENCY_OF = {
    "EURUSD": {"EUR", "USD"},
    "GBPUSD": {"GBP", "USD"},
    "AUDUSD": {"AUD", "USD"},
    "NZDUSD": {"NZD", "USD"},
    "USDJPY": {"USD", "JPY"},
    "USDCHF": {"USD", "CHF"},
    "USDCAD": {"USD", "CAD"},
}


def _prepare_frames(frames: dict[str, pd.DataFrame]) -> tuple[dict[str, pd.DataFrame], str]:
    cleaned: dict[str, pd.DataFrame] = {}
    drop_note = "No unfinished last bar was dropped."
    drop_date = None
    for name in SEVEN:
        work = frames[name].copy()
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


def _usd_strength_series(frame: pd.DataFrame, symbol: str) -> pd.Series:
    ret = frame.set_index("time")["log_return"]
    if symbol in USD_QUOTE_PAIRS:
        return -ret
    if symbol in USD_BASE_PAIRS:
        return ret
    raise ValueError(f"{symbol} is not a USD-factor constituent")


def _control_constituents(left: str, right: str) -> list[str]:
    blocked = (CURRENCY_OF[left] | CURRENCY_OF[right]) - {"USD"}
    out: list[str] = []
    for symbol in USD_FACTOR_CANDIDATES:
        other = CURRENCY_OF[symbol] - {"USD"}
        if other & blocked:
            continue
        out.append(symbol)
    return out


def _pair_table_with_z(
    frames: dict[str, pd.DataFrame],
    left: str,
    right: str,
    constituents: list[str],
) -> pd.DataFrame:
    a = frames[left].set_index("time")
    b = frames[right].set_index("time")
    common = a.index.intersection(b.index)
    for symbol in constituents:
        common = common.intersection(frames[symbol].set_index("time").index)
    common = common.sort_values()

    strength_cols: list[str] = []
    cols: dict[str, pd.Series] = {
        "time": pd.Series(common, index=common),
        f"{left}_log_return": a.loc[common, "log_return"],
        f"{right}_log_return": b.loc[common, "log_return"],
    }
    for symbol in constituents:
        col_name = f"usd_strength_{symbol}"
        cols[col_name] = _usd_strength_series(frames[symbol], symbol).loc[common]
        strength_cols.append(col_name)

    table = pd.DataFrame(cols)
    need = [f"{left}_log_return", f"{right}_log_return"] + strength_cols
    table = table.dropna(subset=need).reset_index(drop=True)
    table["z"] = table[strength_cols].mean(axis=1)
    return table


def _ols_with_r2(dep: np.ndarray, ctrl: np.ndarray) -> dict[str, float | np.ndarray]:
    n = len(dep)
    mean_c = float(np.mean(ctrl))
    mean_d = float(np.mean(dep))
    den = float(np.sum((ctrl - mean_c) ** 2))
    if den == 0.0:
        intercept = mean_d
        slope = 0.0
        fitted = np.full(n, intercept, dtype=float)
        resid = dep - fitted
        return {
            "intercept": intercept,
            "slope": slope,
            "fitted": fitted,
            "resid": resid,
            "r2": float("nan"),
        }
    slope = float(np.sum((ctrl - mean_c) * (dep - mean_d)) / den)
    intercept = mean_d - slope * mean_c
    fitted = intercept + slope * ctrl
    resid = dep - fitted
    ss_tot = float(np.sum((dep - mean_d) ** 2))
    ss_res = float(np.sum(resid ** 2))
    r2 = float("nan") if ss_tot == 0.0 else 1.0 - ss_res / ss_tot
    return {
        "intercept": intercept,
        "slope": slope,
        "fitted": fitted,
        "resid": resid,
        "r2": r2,
    }


def _pearson_block(x: np.ndarray, y: np.ndarray) -> dict[str, float]:
    n = int(len(x))
    if n < 3 or float(np.std(x)) == 0.0 or float(np.std(y)) == 0.0:
        return {
            "r": float("nan"),
            "p": float("nan"),
            "ci_low": float("nan"),
            "ci_high": float("nan"),
            "n": float(n),
        }
    result = stats.pearsonr(x, y)
    r = float(result.statistic)
    p = float(result.pvalue)
    low, high = result.confidence_interval(confidence_level=0.95)
    return {
        "r": r,
        "p": p,
        "ci_low": float(low),
        "ci_high": float(high),
        "n": float(n),
    }


def _full_sample_partial(table: pd.DataFrame, left: str, right: str) -> dict[str, float]:
    x = table[f"{left}_log_return"].to_numpy(dtype=float)
    y = table[f"{right}_log_return"].to_numpy(dtype=float)
    z = table["z"].to_numpy(dtype=float)
    reg_x = _ols_with_r2(x, z)
    reg_y = _ols_with_r2(y, z)
    partial = _pearson_block(
        np.asarray(reg_x["resid"], dtype=float),
        np.asarray(reg_y["resid"], dtype=float),
    )
    raw = _pearson_block(x, y)
    return {
        "n": float(len(table)),
        "r2_x": float(reg_x["r2"]),
        "r2_y": float(reg_y["r2"]),
        "rho_partial": partial["r"],
        "p": partial["p"],
        "ci_low": partial["ci_low"],
        "ci_high": partial["ci_high"],
        "pearson_r": raw["r"],
        "partial_minus_r": partial["r"] - raw["r"],
    }


def _rolling_partial_from_corrs(
    r_xy: pd.Series,
    r_xz: pd.Series,
    r_yz: pd.Series,
) -> pd.Series:
    den = np.sqrt((1.0 - r_xz**2) * (1.0 - r_yz**2))
    out = (r_xy - r_xz * r_yz) / den
    out = out.where(den > 1e-12)
    return out


def _add_rolling(table: pd.DataFrame, left: str, right: str) -> pd.DataFrame:
    out = table.copy()
    x = out[f"{left}_log_return"]
    y = out[f"{right}_log_return"]
    z = out["z"]
    for w in WINDOWS:
        r_xy = x.rolling(w).corr(y)
        r_xz = x.rolling(w).corr(z)
        r_yz = y.rolling(w).corr(z)
        out[f"r_{w}"] = r_xy
        out[f"rho_partial_{w}"] = _rolling_partial_from_corrs(r_xy, r_xz, r_yz)
    return out


def _safe_corr(a: pd.Series, b: pd.Series) -> float:
    mask = a.notna() & b.notna()
    if int(mask.sum()) < 3:
        return float("nan")
    aa = a.loc[mask].to_numpy(dtype=float)
    bb = b.loc[mask].to_numpy(dtype=float)
    if float(np.std(aa)) == 0.0 or float(np.std(bb)) == 0.0:
        return float("nan")
    return float(np.corrcoef(aa, bb)[0, 1])


def _pace_metrics(table: pd.DataFrame, w: int) -> dict[str, float]:
    raw = table[f"r_{w}"]
    part = table[f"rho_partial_{w}"]
    mask = raw.notna() & part.notna()
    n_ok = int(mask.sum())
    if n_ok < 3:
        return {
            "path_agreement": float("nan"),
            "pace_agreement": float("nan"),
            "sign_agreement": float("nan"),
            "mean_gap": float("nan"),
            "mean_abs_gap": float("nan"),
            "n_rolling": float(n_ok),
        }
    gap = part - raw
    same_sign = (
        ((raw.loc[mask] >= 0) & (part.loc[mask] >= 0))
        | ((raw.loc[mask] < 0) & (part.loc[mask] < 0))
    )
    d_raw = raw.diff()
    d_part = part.diff()
    return {
        "path_agreement": _safe_corr(raw, part),
        "pace_agreement": _safe_corr(d_raw, d_part),
        "sign_agreement": float(same_sign.mean()),
        "mean_gap": float(gap.loc[mask].mean()),
        "mean_abs_gap": float(gap.loc[mask].abs().mean()),
        "n_rolling": float(n_ok),
    }


def _save_pair_rolling_chart(
    table: pd.DataFrame,
    left: str,
    right: str,
    out_path: Path,
) -> None:
    times = pd.to_datetime(table["time"], utc=True)
    fig, axes = plt.subplots(3, 1, figsize=(10, 9), sharex=True)
    for ax, w in zip(axes, WINDOWS):
        ax.plot(
            times,
            table[f"r_{w}"],
            color="#1f77b4",
            linewidth=0.85,
            label=f"raw r_{w}",
        )
        ax.plot(
            times,
            table[f"rho_partial_{w}"],
            color="#ff7f0e",
            linewidth=0.85,
            label=f"partial_{w}",
        )
        ax.axhline(0, color="gray", linewidth=0.6)
        ax.set_ylim(-1.05, 1.05)
        ax.set_ylabel(f"W={w}")
        ax.legend(loc="upper left", fontsize=8)
    axes[0].set_title(f"Rolling raw vs partial: {left} and {right}")
    axes[-1].set_xlabel("date")
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=120)
    plt.close(fig)


def _matrix_from_pairs(
    pairs: list[tuple[str, str]],
    values: dict[tuple[str, str], float],
) -> np.ndarray:
    n = len(SEVEN)
    mat = np.full((n, n), np.nan, dtype=float)
    idx = {name: i for i, name in enumerate(SEVEN)}
    for i in range(n):
        mat[i, i] = 1.0
    for left, right in pairs:
        i, j = idx[left], idx[right]
        val = values[(left, right)]
        mat[i, j] = val
        mat[j, i] = val
    return mat


def _save_heatmap(
    mat: np.ndarray,
    title: str,
    out_path: Path,
    vmin: float = -1.0,
    vmax: float = 1.0,
    cmap: str = "RdBu_r",
) -> None:
    fig, ax = plt.subplots(figsize=(7.2, 6.0))
    im = ax.imshow(mat, cmap=cmap, vmin=vmin, vmax=vmax, aspect="equal")
    ax.set_xticks(range(len(SEVEN)))
    ax.set_yticks(range(len(SEVEN)))
    ax.set_xticklabels(SEVEN, rotation=45, ha="right")
    ax.set_yticklabels(SEVEN)
    for i in range(len(SEVEN)):
        for j in range(len(SEVEN)):
            val = mat[i, j]
            if math.isnan(val):
                text = ""
            else:
                text = f"{val:.2f}"
            color = "white" if abs(val) > 0.55 else "black"
            ax.text(j, i, text, ha="center", va="center", fontsize=7.5, color=color)
    ax.set_title(title)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=120)
    plt.close(fig)


def _save_scatter(
    rows: list[dict[str, object]],
    out_path: Path,
) -> None:
    rs = [float(r["pearson_r"]) for r in rows]
    ps = [float(r["rho_partial"]) for r in rows]
    fig, ax = plt.subplots(figsize=(6.5, 6.0))
    ax.scatter(rs, ps, s=36, color="#1f77b4", alpha=0.85, edgecolors="none")
    lims = [-1.05, 1.05]
    ax.plot(lims, lims, color="gray", linewidth=0.8, linestyle="--", label="y = x")
    ax.axhline(0, color="gray", linewidth=0.5)
    ax.axvline(0, color="gray", linewidth=0.5)
    ax.set_xlim(lims)
    ax.set_ylim(lims)
    ax.set_xlabel("full-sample Pearson r")
    ax.set_ylabel("full-sample rho_partial")
    ax.set_title("Partial vs Pearson (21 pairs among seven USD majors)")
    ax.legend(loc="upper left")
    for row in rows:
        if abs(float(row["partial_minus_r"])) >= 0.45:
            ax.annotate(
                str(row["pair"]),
                (float(row["pearson_r"]), float(row["rho_partial"])),
                textcoords="offset points",
                xytext=(4, 4),
                fontsize=7,
            )
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=120)
    plt.close(fig)


def _fmt(value: float, digits: int = 3) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "n/a"
    return f"{value:.{digits}f}"


def _fmt_pct(value: float, digits: int = 1) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "n/a"
    return f"{100.0 * value:.{digits}f}%"


def _build_conclusion(rows: list[dict[str, object]]) -> dict[str, object]:
    w = HEADLINE_W
    by_pace = sorted(
        rows,
        key=lambda r: (
            float("-inf")
            if math.isnan(float(r[f"pace_agreement_{w}"]))
            else float(r[f"pace_agreement_{w}"])
        ),
    )
    by_path = sorted(
        rows,
        key=lambda r: (
            float("-inf")
            if math.isnan(float(r[f"path_agreement_{w}"]))
            else float(r[f"path_agreement_{w}"])
        ),
    )
    by_abs_gap = sorted(
        rows,
        key=lambda r: abs(float(r["partial_minus_r"])),
        reverse=True,
    )
    pace_vals = [float(r[f"pace_agreement_{w}"]) for r in rows]
    path_vals = [float(r[f"path_agreement_{w}"]) for r in rows]
    abs_gaps = [abs(float(r["partial_minus_r"])) for r in rows]
    mean_pace = float(np.nanmean(pace_vals))
    mean_path = float(np.nanmean(path_vals))
    median_abs_gap = float(np.nanmedian(abs_gaps))
    high_pace = sum(1 for v in pace_vals if not math.isnan(v) and v >= 0.85)
    low_pace = sum(1 for v in pace_vals if not math.isnan(v) and v < 0.70)

    if mean_pace >= 0.85 and mean_path >= 0.85:
        verdict = (
            "Removing the leave-currency-out USD factor mostly shifts the "
            "correlation level. Across the 21 pairs, the W=60 path and the "
            "day-to-day pace of change stay strongly aligned with raw rolling "
            "Pearson. The tempo itself rarely breaks."
        )
    elif mean_pace >= 0.70:
        verdict = (
            "Removing the USD factor often shifts the level and sometimes "
            "softens path agreement, but the W=60 day-to-day pace usually "
            "still tracks raw rolling Pearson for most pairs."
        )
    else:
        verdict = (
            "Removing the USD factor changes more than the level. On W=60, "
            "path and pace agreement with raw rolling Pearson are often weak, "
            "so the residual tempo can diverge from the raw correlation path."
        )

    return {
        "verdict": verdict,
        "mean_pace": mean_pace,
        "mean_path": mean_path,
        "median_abs_gap": median_abs_gap,
        "high_pace": high_pace,
        "low_pace": low_pace,
        "best_pace": by_pace[-1],
        "worst_pace": by_pace[0],
        "best_path": by_path[-1],
        "worst_path": by_path[0],
        "top_gaps": by_abs_gap[:3],
        "strongest_partial": max(rows, key=lambda r: float(r["rho_partial"])),
        "weakest_partial": min(rows, key=lambda r: float(r["rho_partial"])),
    }


def _write_notes(
    rows: list[dict[str, object]],
    drop_note: str,
    snapshot_name: str,
    conclusion: dict[str, object],
) -> None:
    w = HEADLINE_W
    lines = [
        "# Seven USD majors — partial correlation vs pace",
        "",
        "## Research question",
        "",
        "For the 21 unordered pairs among EURUSD, GBPUSD, AUDUSD, NZDUSD, "
        "USDJPY, USDCHF, and USDCAD (EURGBP excluded), how does full-sample "
        "partial correlation after a leave-currency-out USD factor compare "
        "with rolling Pearson, and does the residual series respect the pace "
        "of raw rolling correlation on windows 20 / 60 / 100?",
        "",
        "## Snapshot",
        "",
        f"- Folder: `{SNAPSHOT_REL.as_posix()}`",
        f"- Snapshot name: {snapshot_name}",
        f"- {drop_note}",
        "",
        "## Parameters",
        "",
        "- Series: daily log return of close, quote direction unchanged",
        "- EURGBP is not a studied leg and never enters the USD factor",
        "- Control z: equal-weight mean of USD-strength returns from the "
        "seven majors that do not share a non-USD currency with either leg; "
        "USD-strength is -log return for EURUSD/GBPUSD/AUDUSD/NZDUSD and "
        "+log return for USDJPY/USDCHF/USDCAD",
        "- Full-sample: OLS residuals of each leg on z (with intercept), "
        "then Pearson rho_partial; same-sample raw Pearson r as side check",
        "- Rolling: for W in {20, 60, 100}, raw rolling Pearson r_xy and "
        "in-window partial "
        "`(r_xy - r_xz r_yz) / sqrt((1-r_xz^2)(1-r_yz^2))`",
        "- Pace metrics per window: path agreement (corr of raw vs partial "
        "paths), pace agreement (corr of first differences), sign agreement, "
        "mean gap and mean absolute gap",
        "- Headline window for the conclusion: W=60",
        "- Named dig only. Does not change experiments/v001.",
        "",
        "## Index (headline W=60)",
        "",
        "| pair | n | rho_partial | pearson_r | gap | path_60 | pace_60 | "
        "sign_60 | mean_abs_gap_60 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| {row['pair']} | {row['n']} | "
            f"{float(row['rho_partial']):.4f} | "
            f"{float(row['pearson_r']):.4f} | "
            f"{float(row['partial_minus_r']):.4f} | "
            f"{float(row[f'path_agreement_{w}']):.4f} | "
            f"{float(row[f'pace_agreement_{w}']):.4f} | "
            f"{float(row[f'sign_agreement_{w}']):.4f} | "
            f"{float(row[f'mean_abs_gap_{w}']):.4f} |"
        )
    lines.extend(
        [
            "",
            "## Cross-pair reading",
            "",
            "Reading of the 21-pair index only. Not a 22nd pair analysis and "
            "not a trading signal.",
            "",
            conclusion["verdict"],
            "",
            (
                f"Mean W={w} path agreement: {conclusion['mean_path']:.4f}. "
                f"Mean W={w} pace agreement: {conclusion['mean_pace']:.4f}. "
                f"Median |full-sample gap|: {conclusion['median_abs_gap']:.4f}. "
                f"Pairs with pace agreement ≥ 0.85: {conclusion['high_pace']}. "
                f"Pairs with pace agreement < 0.70: {conclusion['low_pace']}."
            ),
            (
                f"Highest W={w} pace agreement: "
                f"{conclusion['best_pace']['pair']} "
                f"({float(conclusion['best_pace'][f'pace_agreement_{w}']):.4f})."
            ),
            (
                f"Lowest W={w} pace agreement: "
                f"{conclusion['worst_pace']['pair']} "
                f"({float(conclusion['worst_pace'][f'pace_agreement_{w}']):.4f})."
            ),
            (
                "Largest |rho_partial minus Pearson r| gaps: "
                + "; ".join(
                    f"{r['pair']} (gap={float(r['partial_minus_r']):.4f}, "
                    f"rho_partial={float(r['rho_partial']):.4f}, "
                    f"r={float(r['pearson_r']):.4f})"
                    for r in conclusion["top_gaps"]
                )
                + "."
            ),
            "",
            "Page: [index.html](index.html).",
            "",
            "This folder is a named dig into the seven USD majors. It is not "
            "a new experiment version and does not change v001.",
            "",
        ]
    )
    (EXP_DIR / "NOTES.md").write_text("\n".join(lines), encoding="utf-8")


def _html_table(headers: list[str], body_rows: list[list[str]]) -> str:
    th = "".join(f"<th>{html.escape(h)}</th>" for h in headers)
    trs = []
    for row in body_rows:
        cells = []
        for i, cell in enumerate(row):
            align = "left" if i == 0 else "right"
            cells.append(f'<td style="text-align:{align}">{html.escape(cell)}</td>')
        trs.append("<tr>" + "".join(cells) + "</tr>")
    return (
        "<table><thead><tr>"
        + th
        + "</tr></thead><tbody>"
        + "".join(trs)
        + "</tbody></table>"
    )


def _write_html(
    rows: list[dict[str, object]],
    drop_note: str,
    snapshot_name: str,
    conclusion: dict[str, object],
) -> None:
    w = HEADLINE_W
    best = conclusion["best_pace"]
    worst = conclusion["worst_pace"]
    top_gaps = conclusion["top_gaps"]

    full_rows = [
        [
            str(r["pair"]),
            str(r["n"]),
            _fmt(float(r["pearson_r"])),
            _fmt(float(r["rho_partial"])),
            _fmt(float(r["partial_minus_r"])),
            _fmt(float(r["r2_x"])),
            _fmt(float(r["r2_y"])),
            _fmt(float(r["ci_low"])),
            _fmt(float(r["ci_high"])),
        ]
        for r in rows
    ]
    pace_rows = []
    for r in rows:
        for win in WINDOWS:
            pace_rows.append(
                [
                    str(r["pair"]),
                    str(win),
                    _fmt(float(r[f"path_agreement_{win}"])),
                    _fmt(float(r[f"pace_agreement_{win}"])),
                    _fmt_pct(float(r[f"sign_agreement_{win}"])),
                    _fmt(float(r[f"mean_gap_{win}"])),
                    _fmt(float(r[f"mean_abs_gap_{win}"])),
                ]
            )

    pair_blocks = []
    for r in rows:
        pair = str(r["pair"])
        stem = pair.replace("/", "-")
        img = f"outputs/figures/{stem}_Rolling_raw_vs_partial.png"
        pair_blocks.append(
            f"""
<div class="chart-block">
<h3>{html.escape(pair)}</h3>
<img src="{html.escape(img)}" alt="Rolling raw vs partial: {html.escape(pair)}"/>
<p class="caption">
Full-sample r = {_fmt(float(r['pearson_r']))},
rho_partial = {_fmt(float(r['rho_partial']))},
gap = {_fmt(float(r['partial_minus_r']))}.
W={w} path agreement = {_fmt(float(r[f'path_agreement_{w}']))},
pace agreement = {_fmt(float(r[f'pace_agreement_{w}']))},
sign agreement = {_fmt_pct(float(r[f'sign_agreement_{w}']))},
mean |gap| = {_fmt(float(r[f'mean_abs_gap_{w}']))}.
</p>
</div>
"""
        )

    gap_text = "; ".join(
        f"{r['pair']} (gap={_fmt(float(r['partial_minus_r']), 4)}, "
        f"rho_partial={_fmt(float(r['rho_partial']), 4)}, "
        f"r={_fmt(float(r['pearson_r']), 4)})"
        for r in top_gaps
    )

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Seven USD majors — partial correlation vs pace</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 24px; color: #222; max-width: 1100px; }}
h1 {{ font-size: 1.35rem; margin-bottom: 0.4rem; }}
h2 {{ font-size: 1.1rem; margin-top: 1.8rem; }}
h3 {{ font-size: 1rem; margin-top: 1.2rem; }}
p {{ line-height: 1.5; }}
ul, ol {{ line-height: 1.5; }}
img {{ max-width: 100%; height: auto; border: 1px solid #ddd; margin: 0.6rem 0 1rem; }}
table {{ border-collapse: collapse; font-size: 0.88rem; margin-top: 0.6rem; width: 100%; }}
th, td {{ border: 1px solid #ccc; padding: 5px 8px; text-align: right; }}
th:first-child, td:first-child {{ text-align: left; }}
th {{ background: #f3f3f3; }}
.note {{ color: #555; font-size: 0.92rem; }}
.lead {{ font-size: 1.05rem; background: #f7f9fc; border-left: 4px solid #1565c0; padding: 12px 14px; }}
.conclusion {{ background: #f4f7f4; border-left: 4px solid #2e7d32; padding: 12px 14px; }}
code {{ font-family: Consolas, monospace; font-size: 0.92em; background: #f5f5f5; padding: 1px 4px; }}
.chart-block {{ margin-bottom: 1.5rem; }}
.caption {{ color: #555; font-size: 0.9rem; margin-top: -0.4rem; margin-bottom: 1rem; }}
nav {{ margin: 1rem 0 1.5rem; font-size: 0.92rem; }}
nav a {{ margin-right: 1rem; color: #1565c0; }}
</style>
</head>
<body>
<h1>Seven USD majors — partial correlation vs pace</h1>
<p class="lead">
{html.escape(str(conclusion["verdict"]))}
Mean W={w} path agreement is {_fmt(float(conclusion["mean_path"]), 3)};
mean W={w} pace agreement is {_fmt(float(conclusion["mean_pace"]), 3)}.
Median |full-sample gap| is {_fmt(float(conclusion["median_abs_gap"]), 3)}.
</p>
<p class="note">
Method 07 named dig under
<code>07 - Partial and Residual Correlation/seven-usd-majors/</code>.
EURGBP excluded. Not a new experiment version. Does not change partial v001.
Not a trade signal.
</p>

<nav>
<a href="#why">Why</a>
<a href="#setup">Setup</a>
<a href="#overview">Overview charts</a>
<a href="#numbers">Numbers</a>
<a href="#pair-charts">Pair charts</a>
<a href="#how-to-read">How to read</a>
<a href="#conclusion">Conclusion</a>
</nav>

<h2 id="why">Why this dig</h2>
<p>
Partial / residual correlation v001 already strips a leave-currency-out USD
strength factor from all eight majors and reports one full-sample
<code>rho_partial</code> per pair. This folder asks a different question on a
narrower universe: among the seven USD majors only, after the USD factor is
removed, does the leftover link still move at the same pace as raw Pearson
correlation through time?
</p>
<ul>
<li><strong>Universe:</strong> EURUSD, GBPUSD, AUDUSD, NZDUSD, USDJPY, USDCHF,
USDCAD — 21 unordered pairs.</li>
<li><strong>Left out:</strong> EURGBP (not a studied leg; never a USD-factor
constituent).</li>
<li><strong>Two views:</strong> full-sample partial vs Pearson (level / gap),
and rolling raw vs in-window partial on W ∈ {{20, 60, 100}} (path and pace).</li>
</ul>

<h2 id="setup">Experiment setup</h2>
<ul>
<li><strong>Snapshot:</strong> <code>{html.escape(snapshot_name)}</code>
under <code>{html.escape(SNAPSHOT_REL.as_posix())}</code>.</li>
<li><strong>Bar filter:</strong> {html.escape(drop_note)}</li>
<li><strong>Series:</strong> daily log return of close,
<code>ln(close<sub>t</sub> / close<sub>t−1</sub>)</code>. Quote direction
unchanged; no inversion.</li>
<li><strong>Control z:</strong> equal-weight mean of USD-strength returns from
majors that do not share a non-USD currency with either leg. USD-strength is
minus the log return when USD is the quote and plus the log return when USD
is the base.</li>
<li><strong>Full-sample:</strong> OLS of each leg on z with an intercept;
<code>rho_partial</code> is Pearson of the residuals. Same-sample raw Pearson
r and the gap <code>rho_partial − r</code> are side checks. Fisher 95%
intervals are shown; p-values stay secondary.</li>
<li><strong>Rolling partial:</strong> inside each window W,
<code>rho_partial<sup>(W)</sup> = (r<sub>xy</sub> − r<sub>xz</sub> r<sub>yz</sub>)
/ sqrt((1 − r<sub>xz</sub>²)(1 − r<sub>yz</sub>²))</code>.
This is the correlation of the in-window OLS residuals.</li>
<li><strong>Pace metrics:</strong> path agreement = correlation of the raw
and partial rolling series; pace agreement = correlation of their first
differences; sign agreement = share of days with the same sign; mean gap and
mean absolute gap.</li>
<li><strong>Headline window:</strong> W = {w}. Windows 20 and 100 stay in the
tables and charts.</li>
<li><strong>Runner:</strong> <code>run_seven.py</code>. Figures live under
<code>outputs/figures/</code>.</li>
</ul>

<h2 id="overview">Overview charts</h2>
<div class="chart-block">
<h3>Full-sample Pearson r</h3>
<img src="outputs/figures/heatmap_pearson_r.png" alt="Heatmap of full-sample Pearson r"/>
<p class="caption">7×7 matrix among the seven USD majors. Diagonal fixed at 1.</p>
</div>
<div class="chart-block">
<h3>Full-sample rho_partial</h3>
<img src="outputs/figures/heatmap_rho_partial.png" alt="Heatmap of full-sample rho_partial"/>
<p class="caption">Residual correlation after the leave-currency-out USD factor.</p>
</div>
<div class="chart-block">
<h3>Full-sample gap (rho_partial − r)</h3>
<img src="outputs/figures/heatmap_gap.png" alt="Heatmap of partial minus Pearson"/>
<p class="caption">Large |gap| means the USD factor explained much of the raw link,
or that residual co-movement runs against the raw sign.</p>
</div>
<div class="chart-block">
<h3>W={w} pace agreement</h3>
<img src="outputs/figures/heatmap_pace_agreement_60.png" alt="Heatmap of W=60 pace agreement"/>
<p class="caption">Correlation of first differences of raw rolling r and rolling
partial. Values near 1 mean the day-to-day tempo stays aligned after USD removal.</p>
</div>
<div class="chart-block">
<h3>Partial vs Pearson scatter</h3>
<img src="outputs/figures/scatter_partial_vs_pearson.png" alt="Scatter of rho_partial vs Pearson r"/>
<p class="caption">Points off the dashed y = x line are pairs where stripping USD
moves the full-sample score. Large-gap pairs are labelled.</p>
</div>

<h2 id="numbers">Numbers at a glance</h2>
<p>
Full-sample scores for all 21 pairs. Gap is <code>rho_partial − pearson_r</code>.
R² columns are each leg’s R-squared on the control z.
</p>
{_html_table(
    ["Pair", "n", "Pearson r", "rho_partial", "Gap", "R2_x", "R2_y", "CI low", "CI high"],
    full_rows,
)}

<p>
Pace metrics for each window. Path agreement is correlation of the two rolling
paths. Pace agreement is correlation of their first differences (headline for
“respects the pace”). Sign agreement is the share of overlapping days with the
same sign.
</p>
{_html_table(
    ["Pair", "W", "Path", "Pace", "Sign", "Mean gap", "Mean |gap|"],
    pace_rows,
)}

<h2 id="pair-charts">Pair charts (raw vs partial)</h2>
<p>
Each figure has three panels (W = 20, 60, 100). Blue is raw rolling Pearson.
Orange is rolling partial with the USD factor removed inside the window.
</p>
{"".join(pair_blocks)}

<h2 id="how-to-read">How to read</h2>
<ul>
<li><strong>Full-sample gap</strong> — level shift after USD removal. A large
|gap| does not by itself say the rolling path lost its tempo.</li>
<li><strong>Path agreement</strong> — whether the residual correlation series
tracks the same ups and downs as raw rolling r.</li>
<li><strong>Pace agreement</strong> — whether day-to-day changes of the two
series move together. This is the main “respects the pace” score. Headline
window is W = {w}.</li>
<li><strong>Sign agreement</strong> — fraction of days where raw and partial
share the same sign. Useful when a level shift flips the band.</li>
<li><strong>W = 20 / 60 / 100</strong> — short / medium / longer pace. Short
windows are noisier; longer windows are slower.</li>
<li>Scores are symmetric in the two symbols. They do not prove cause,
lead-lag, or a hedge.</li>
</ul>

<h2 id="conclusion">Conclusion</h2>
<div class="conclusion">
<p>
<strong>What we got to know.</strong>
{html.escape(str(conclusion["verdict"]))}
Across the 21 pairs, mean W={w} path agreement is
{_fmt(float(conclusion["mean_path"]), 3)} and mean W={w} pace agreement is
{_fmt(float(conclusion["mean_pace"]), 3)}.
{conclusion["high_pace"]} pairs sit at pace agreement ≥ 0.85;
{conclusion["low_pace"]} sit below 0.70.
Median absolute full-sample gap is {_fmt(float(conclusion["median_abs_gap"]), 3)}.
</p>
<p>
<strong>Where the level moves most.</strong>
Largest |rho_partial − r| gaps: {html.escape(gap_text)}.
Those pairs show that a strong raw Pearson can be largely a shared USD move;
the residual link can sit near zero or even flip sign. That is a level story.
</p>
<p>
<strong>Where the pace holds or breaks.</strong>
Highest W={w} pace agreement:
{html.escape(str(best["pair"]))}
({_fmt(float(best[f"pace_agreement_{w}"]), 4)}).
Lowest W={w} pace agreement:
{html.escape(str(worst["pair"]))}
({_fmt(float(worst[f"pace_agreement_{w}"]), 4)}).
Strongest full-sample residual link:
{html.escape(str(conclusion["strongest_partial"]["pair"]))}
(rho_partial={_fmt(float(conclusion["strongest_partial"]["rho_partial"]), 4)}).
Weakest (most negative):
{html.escape(str(conclusion["weakest_partial"]["pair"]))}
(rho_partial={_fmt(float(conclusion["weakest_partial"]["rho_partial"]), 4)}).
</p>
<p>
<strong>Practical takeaway for this research stream.</strong>
Use full-sample partial to judge how much of a major–major Pearson link is
USD. Use the W={w} pace agreement to judge whether the residual series still
moves with the same tempo as raw rolling correlation. When pace agreement is
high, stripping USD mainly re-levels the path. When it is low, the residual
tempo itself diverges and needs a pair-by-pair read of the three-panel chart.
This page is a reading of these 21 pairs only. It is not a trading signal.
</p>
</div>

<p class="note">
Source files: <code>NOTES.md</code>, <code>run_seven.py</code>,
<code>outputs/index.csv</code>, <code>outputs/figures/</code>.
Open this page from the folder so the image paths resolve.
</p>
</body>
</html>
"""
    (EXP_DIR / "index.html").write_text(page, encoding="utf-8")


def run() -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    snap = load_snapshot(REPO_ROOT / SNAPSHOT_REL)
    snapshot_name = snap["manifest"]["folder"]
    frames, drop_note = _prepare_frames(snap["frames"])

    pairs = list(itertools.combinations(SEVEN, 2))
    index_rows: list[dict[str, object]] = []
    pearson_map: dict[tuple[str, str], float] = {}
    partial_map: dict[tuple[str, str], float] = {}
    gap_map: dict[tuple[str, str], float] = {}
    pace60_map: dict[tuple[str, str], float] = {}

    for left, right in pairs:
        constituents = _control_constituents(left, right)
        if len(constituents) < 1:
            raise RuntimeError(f"No USD-factor constituents left for {left}-{right}")
        table = _pair_table_with_z(frames, left, right, constituents)
        full = _full_sample_partial(table, left, right)
        table = _add_rolling(table, left, right)

        row: dict[str, object] = {
            "pair": f"{left}-{right}",
            "left": left,
            "right": right,
            "n": int(full["n"]),
            "n_controls": len(constituents),
            "controls": ",".join(constituents),
            "rho_partial": full["rho_partial"],
            "p": full["p"],
            "ci_low": full["ci_low"],
            "ci_high": full["ci_high"],
            "pearson_r": full["pearson_r"],
            "partial_minus_r": full["partial_minus_r"],
            "r2_x": full["r2_x"],
            "r2_y": full["r2_y"],
        }
        for w in WINDOWS:
            metrics = _pace_metrics(table, w)
            row[f"path_agreement_{w}"] = metrics["path_agreement"]
            row[f"pace_agreement_{w}"] = metrics["pace_agreement"]
            row[f"sign_agreement_{w}"] = metrics["sign_agreement"]
            row[f"mean_gap_{w}"] = metrics["mean_gap"]
            row[f"mean_abs_gap_{w}"] = metrics["mean_abs_gap"]
            row[f"n_rolling_{w}"] = int(metrics["n_rolling"])

        stem = f"{left}-{right}"
        _save_pair_rolling_chart(
            table,
            left,
            right,
            FIG_DIR / f"{stem}_Rolling_raw_vs_partial.png",
        )

        pearson_map[(left, right)] = float(full["pearson_r"])
        partial_map[(left, right)] = float(full["rho_partial"])
        gap_map[(left, right)] = float(full["partial_minus_r"])
        pace60_map[(left, right)] = float(row[f"pace_agreement_{HEADLINE_W}"])
        index_rows.append(row)
        print(
            f"{stem}: rho_partial={full['rho_partial']:.4f}  "
            f"r={full['pearson_r']:.4f}  "
            f"pace60={float(row[f'pace_agreement_{HEADLINE_W}']):.4f}",
            flush=True,
        )

    index = pd.DataFrame(index_rows)
    index.to_csv(OUT_DIR / "index.csv", index=False)

    _save_heatmap(
        _matrix_from_pairs(pairs, pearson_map),
        "Full-sample Pearson r (seven USD majors)",
        FIG_DIR / "heatmap_pearson_r.png",
    )
    _save_heatmap(
        _matrix_from_pairs(pairs, partial_map),
        "Full-sample rho_partial after USD factor",
        FIG_DIR / "heatmap_rho_partial.png",
    )
    _save_heatmap(
        _matrix_from_pairs(pairs, gap_map),
        "Full-sample gap: rho_partial minus Pearson r",
        FIG_DIR / "heatmap_gap.png",
    )
    _save_heatmap(
        _matrix_from_pairs(pairs, pace60_map),
        f"W={HEADLINE_W} pace agreement (d raw vs d partial)",
        FIG_DIR / "heatmap_pace_agreement_60.png",
        vmin=0.0,
        vmax=1.0,
        cmap="viridis",
    )
    _save_scatter(index_rows, FIG_DIR / "scatter_partial_vs_pearson.png")

    conclusion = _build_conclusion(index_rows)
    _write_notes(index_rows, drop_note, snapshot_name, conclusion)
    _write_html(index_rows, drop_note, snapshot_name, conclusion)
    return OUT_DIR


if __name__ == "__main__":
    run()
