"""EURUSD-anchored same-day candle board for seven USD majors. EURGBP left out."""

from __future__ import annotations

import html
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Rectangle
import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from shared.mt5_data import load_snapshot

SNAPSHOT_REL = Path("data/snapshots/2026-11-03_majors_alpari_D1")
EXP_DIR = Path(__file__).resolve().parent
OUT_DIR = EXP_DIR / "outputs"
WINDOW = 60

# Currency -> (pair, sign). Positive aligned return = currency stronger vs USD.
CURRENCY_LEGS: dict[str, tuple[str, float]] = {
    "EUR": ("EURUSD", 1.0),
    "GBP": ("GBPUSD", 1.0),
    "AUD": ("AUDUSD", 1.0),
    "NZD": ("NZDUSD", 1.0),
    "JPY": ("USDJPY", -1.0),
    "CHF": ("USDCHF", -1.0),
    "CAD": ("USDCAD", -1.0),
}
CURRENCIES = list(CURRENCY_LEGS.keys())
OTHERS = [c for c in CURRENCIES if c != "EUR"]
PAIRS = [CURRENCY_LEGS[c][0] for c in CURRENCIES]
DEFAULT_COLORS = {
    "EUR": "#1f77b4",
    "GBP": "#ff7f0e",
    "AUD": "#2ca02c",
    "NZD": "#9467bd",
    "JPY": "#8c564b",
    "CHF": "#e377c2",
    "CAD": "#7f7f7f",
}
OUTLIER_COLOR = "#d62728"
GREEN = "#1a7f37"
RED = "#c62828"
GRAY = "#9e9e9e"


def _prepare_frames(frames: dict[str, pd.DataFrame]) -> tuple[dict[str, pd.DataFrame], str]:
    """Drop unfinished last bar when tick volume is below half the prior day."""
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
        work["quote_pct"] = work["close"] / work["close"].shift(1) - 1.0
        cleaned[name] = work
    if drop_date is not None:
        drop_note = (
            f"Dropped unfinished last bar dated {drop_date.date().isoformat()} "
            "UTC after a tick-volume check against the prior complete day."
        )
    return cleaned, drop_note


def _aligned_panel(cleaned: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """One row per day with seven aligned currency returns (EURGBP excluded)."""
    series: dict[str, pd.Series] = {}
    for currency, (pair, sign) in CURRENCY_LEGS.items():
        frame = cleaned[pair].dropna(subset=["log_return"]).set_index("time")
        series[currency] = frame["log_return"] * sign
    panel = pd.concat(series, axis=1, join="inner").sort_index()
    panel = panel.dropna()
    panel.index.name = "time"
    return panel


def _ohlc_panel(cleaned: dict[str, pd.DataFrame], dates: pd.DatetimeIndex) -> dict[str, pd.DataFrame]:
    """Broker OHLC for each pair, restricted to the given dates."""
    out: dict[str, pd.DataFrame] = {}
    for currency, (pair, _sign) in CURRENCY_LEGS.items():
        frame = cleaned[pair].set_index("time")
        common = frame.index.intersection(dates)
        piece = frame.loc[common, ["open", "high", "low", "close", "quote_pct", "log_return"]].copy()
        piece["aligned_return"] = piece["log_return"] * CURRENCY_LEGS[currency][1]
        out[pair] = piece.sort_index()
    return out


def _sign_series(values: pd.Series) -> pd.Series:
    return np.sign(values).replace(0.0, np.nan)


def _dir_label(sign: float) -> str:
    if pd.isna(sign) or sign == 0:
        return "flat"
    return "up" if sign > 0 else "down"


def _annotate_days(panel: pd.DataFrame) -> pd.DataFrame:
    """Pack = sign of median of seven. Flag out-of-line and lone-dissenter days."""
    work = panel.copy()
    work["pack_median"] = work[CURRENCIES].median(axis=1)
    work["pack_sign"] = _sign_series(work["pack_median"])

    out_flags = pd.DataFrame(index=work.index)
    for currency in CURRENCIES:
        curr_sign = _sign_series(work[currency])
        out_flags[currency] = (
            work["pack_sign"].notna()
            & curr_sign.notna()
            & (curr_sign != work["pack_sign"])
        )

    work["n_out"] = out_flags.sum(axis=1).astype(int)
    work["lone_dissenter"] = work["n_out"] == 1
    work["out_of_line"] = out_flags.apply(
        lambda row: ",".join(c for c in CURRENCIES if bool(row[c])),
        axis=1,
    )
    for currency in CURRENCIES:
        work[f"out_{currency}"] = out_flags[currency]
    return work


def _eurusd_board(panel: pd.DataFrame) -> pd.DataFrame:
    """Same-day WITH/AGAINST each other currency relative to EUR aligned direction."""
    work = panel[CURRENCIES].copy()
    eur_sign = _sign_series(work["EUR"])
    work["eur_dir"] = eur_sign.map(_dir_label)
    work["eur_sign"] = eur_sign

    n_with = pd.Series(0, index=work.index, dtype=int)
    for currency in OTHERS:
        pair = CURRENCY_LEGS[currency][0]
        curr_sign = _sign_series(work[currency])
        call = pd.Series("flat", index=work.index, dtype=object)
        usable = eur_sign.notna() & curr_sign.notna()
        with_mask = usable & (curr_sign == eur_sign)
        against_mask = usable & (curr_sign != eur_sign)
        call.loc[with_mask] = "WITH"
        call.loc[against_mask] = "AGAINST"
        work[f"vs_eur_{currency}"] = call
        work[f"vs_eur_{pair}"] = call
        n_with = n_with + with_mask.astype(int)
    work["n_with_eur"] = n_with
    work["n_against_eur"] = (
        eur_sign.notna().astype(int) * len(OTHERS) - n_with
        - sum(
            (
                eur_sign.notna()
                & _sign_series(work[c]).isna()
            ).astype(int)
            for c in OTHERS
        )
    )
    # Recount flats separately for clarity
    flat_counts = []
    for currency in OTHERS:
        flat_counts.append((work[f"vs_eur_{currency}"] == "flat").astype(int))
    work["n_flat_vs_eur"] = sum(flat_counts)
    work["n_against_eur"] = len(OTHERS) - work["n_with_eur"] - work["n_flat_vs_eur"]
    return work


def _vs_eurusd_rates(board: pd.DataFrame) -> pd.DataFrame:
    usable = board[board["eur_sign"].notna()].copy()
    rows: list[dict[str, object]] = []
    n = int(len(usable))
    for currency in OTHERS:
        pair = CURRENCY_LEGS[currency][0]
        col = f"vs_eur_{currency}"
        with_n = int((usable[col] == "WITH").sum())
        against_n = int((usable[col] == "AGAINST").sum())
        flat_n = int((usable[col] == "flat").sum())
        denom = with_n + against_n
        rows.append(
            {
                "currency": currency,
                "pair": pair,
                "days_eur_moved": n,
                "days_with": with_n,
                "days_against": against_n,
                "days_flat": flat_n,
                "pct_with": (100.0 * with_n / denom) if denom else float("nan"),
                "pct_against": (100.0 * against_n / denom) if denom else float("nan"),
            }
        )
    return pd.DataFrame(rows)


def _last_day_detail(
    cleaned: dict[str, pd.DataFrame],
    board: pd.DataFrame,
) -> tuple[pd.Timestamp, pd.DataFrame, str]:
    last_ts = board.index[-1]
    eur_dir = str(board.loc[last_ts, "eur_dir"])
    rows: list[dict[str, object]] = []
    parts: list[str] = []
    for currency in CURRENCIES:
        pair, sign = CURRENCY_LEGS[currency]
        frame = cleaned[pair].set_index("time")
        bar = frame.loc[last_ts]
        quote_pct = float(bar["quote_pct"])
        aligned = float(bar["log_return"]) * sign
        quote_dir = _dir_label(np.sign(quote_pct) if quote_pct != 0 else 0.0)
        if currency == "EUR":
            vs = "anchor"
        else:
            vs = str(board.loc[last_ts, f"vs_eur_{currency}"])
            if vs == "WITH":
                parts.append(f"{pair} with")
            elif vs == "AGAINST":
                parts.append(f"{pair} against")
            else:
                parts.append(f"{pair} flat")
        rows.append(
            {
                "pair": pair,
                "currency": currency,
                "open": float(bar["open"]),
                "high": float(bar["high"]),
                "low": float(bar["low"]),
                "close": float(bar["close"]),
                "quote_pct": quote_pct,
                "aligned_pct": aligned,
                "quote_direction": quote_dir,
                "vs_eurusd": vs,
            }
        )
    date_s = last_ts.date().isoformat()
    if eur_dir == "flat":
        sentence = f"On {date_s} EURUSD closed flat. Same day: {', '.join(parts)}."
    else:
        sentence = (
            f"On {date_s} EURUSD closed {eur_dir}. "
            f"Same day: {', '.join(parts)}."
        )
    return last_ts, pd.DataFrame(rows), sentence


def _break_days(annotated: pd.DataFrame) -> pd.DataFrame:
    """Out-of-line days whose |move| exceeds that currency's median |aligned return|."""
    typical = {c: float(annotated[c].abs().median()) for c in CURRENCIES}
    rows: list[dict[str, object]] = []
    for currency in CURRENCIES:
        mask = annotated[f"out_{currency}"] & (annotated[currency].abs() > typical[currency])
        subset = annotated.loc[mask]
        for ts, row in subset.iterrows():
            rows.append(
                {
                    "time": ts,
                    "currency": currency,
                    "aligned_return": float(row[currency]),
                    "pack_median": float(row["pack_median"]),
                    "pack_sign": float(row["pack_sign"]) if pd.notna(row["pack_sign"]) else np.nan,
                    "typical_abs": typical[currency],
                    "lone_dissenter": bool(row["lone_dissenter"]),
                }
            )
    if not rows:
        return pd.DataFrame(
            columns=[
                "time",
                "currency",
                "aligned_return",
                "pack_median",
                "pack_sign",
                "typical_abs",
                "lone_dissenter",
            ]
        )
    return pd.DataFrame(rows).sort_values(["time", "currency"]).reset_index(drop=True)


def _currency_summary(annotated: pd.DataFrame, breaks: pd.DataFrame) -> pd.DataFrame:
    usable = annotated[annotated["pack_sign"].notna()].copy()
    last = usable.iloc[-1]
    last_date = usable.index[-1]
    rows: list[dict[str, object]] = []
    for currency in CURRENCIES:
        out_mask = usable[f"out_{currency}"]
        with_pack = int((~out_mask).sum())
        out_days = int(out_mask.sum())
        lone = int((out_mask & usable["lone_dissenter"]).sum())
        break_mask = breaks["currency"] == currency
        break_n = int(break_mask.sum())
        med_break = (
            float(breaks.loc[break_mask, "aligned_return"].median())
            if break_n
            else float("nan")
        )
        last_ret = float(last[currency])
        last_out = bool(last[f"out_{currency}"])
        last_call = "against" if last_out else "with"
        rows.append(
            {
                "currency": currency,
                "days_in_sample": int(len(usable)),
                "days_with_pack": with_pack,
                "days_out_of_line": out_days,
                "lone_dissenter_days": lone,
                "break_days": break_n,
                "median_aligned_on_break_days": med_break,
                "last_day": last_date,
                "last_aligned_return": last_ret,
                "last_call": last_call,
            }
        )
    return pd.DataFrame(rows)


def _pack_verdict_lines(summary: pd.DataFrame, annotated: pd.DataFrame) -> tuple[str, str]:
    max_out = int(summary["days_out_of_line"].max())
    winners = summary.loc[summary["days_out_of_line"] == max_out, "currency"].tolist()
    if len(winners) == 1:
        headline = (
            f"{winners[0]} is the currency moving out of line versus the pack. "
            f"It disagreed with the other six on the most days ({max_out})."
        )
    else:
        names = ", ".join(winners)
        headline = (
            f"{names} are the currencies moving out of line versus the pack. "
            f"They tied for the most disagree days ({max_out})."
        )

    usable = annotated[annotated["pack_sign"].notna()]
    last = usable.iloc[-1]
    last_date = usable.index[-1].date().isoformat()
    dissenters = [c for c in CURRENCIES if bool(last[f"out_{c}"])]
    if not dissenters:
        last_line = f"Last complete day ({last_date}) vs pack: all seven matched."
    elif len(dissenters) == 1:
        last_line = (
            f"Last complete day ({last_date}) vs pack: {dissenters[0]} was out of line."
        )
    else:
        last_line = (
            f"Last complete day ({last_date}) vs pack: "
            f"{', '.join(dissenters)} were out of line."
        )
    return headline, last_line


def _draw_candles(ax: plt.Axes, frame: pd.DataFrame, pair: str) -> None:
    times = list(range(len(frame)))
    opens = frame["open"].to_numpy(dtype=float)
    highs = frame["high"].to_numpy(dtype=float)
    lows = frame["low"].to_numpy(dtype=float)
    closes = frame["close"].to_numpy(dtype=float)
    width = 0.6
    for i, (o, h, l, c) in enumerate(zip(opens, highs, lows, closes)):
        color = GREEN if c >= o else RED
        ax.vlines(i, l, h, color=color, linewidth=0.8)
        body_low = min(o, c)
        body_height = abs(c - o)
        if body_height < 1e-12:
            body_height = (h - l) * 0.02 if h > l else abs(c) * 1e-6 + 1e-8
        ax.add_patch(
            Rectangle(
                (i - width / 2, body_low),
                width,
                body_height,
                facecolor=color,
                edgecolor=color,
                linewidth=0.5,
            )
        )
    ax.set_xlim(-1, len(frame))
    ax.set_ylabel(pair, fontsize=8)
    ax.tick_params(axis="y", labelsize=7)
    ax.grid(True, axis="y", alpha=0.25)


def _plot_candles_seven(
    ohlc: dict[str, pd.DataFrame],
    dates: pd.DatetimeIndex,
    out_path: Path,
) -> None:
    fig, axes = plt.subplots(7, 1, figsize=(14, 12), sharex=True)
    for ax, pair in zip(axes, PAIRS):
        frame = ohlc[pair].loc[dates]
        _draw_candles(ax, frame, pair)
    axes[-1].set_xticks(range(0, len(dates), max(1, len(dates) // 10)))
    axes[-1].set_xticklabels(
        [d.date().isoformat() for d in dates[:: max(1, len(dates) // 10)]],
        rotation=45,
        ha="right",
        fontsize=7,
    )
    start = dates[0].date().isoformat()
    end = dates[-1].date().isoformat()
    fig.suptitle(
        f"Daily candles — seven USD pairs ({start} to {end}, UTC)",
        fontsize=12,
    )
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=140)
    plt.close(fig)


def _plot_with_against(
    board: pd.DataFrame,
    out_path: Path,
) -> None:
    recent = board.tail(WINDOW).copy()
    cols = ["EUR"] + OTHERS
    labels = ["EURUSD"] + [CURRENCY_LEGS[c][0] for c in OTHERS]
    n_days = len(recent)
    n_cols = len(cols)

    fig, ax = plt.subplots(figsize=(10, max(8, n_days * 0.22)))
    ax.set_xlim(-0.5, n_cols - 0.5)
    ax.set_ylim(-0.5, n_days - 0.5)
    ax.invert_yaxis()

    for row_i, (_ts, row) in enumerate(recent.iterrows()):
        eur_dir = str(row["eur_dir"])
        if eur_dir == "up":
            color = GREEN
        elif eur_dir == "down":
            color = RED
        else:
            color = GRAY
        ax.add_patch(
            FancyBboxPatch(
                (-0.4, row_i - 0.35),
                0.8,
                0.7,
                boxstyle="round,pad=0.02",
                facecolor=color,
                edgecolor="white",
                linewidth=0.5,
            )
        )
        ax.text(0, row_i, eur_dir.upper(), ha="center", va="center", color="white", fontsize=7, fontweight="bold")

        for col_i, currency in enumerate(OTHERS, start=1):
            call = str(row[f"vs_eur_{currency}"])
            if call == "WITH":
                c = GREEN
                mark = "W"
            elif call == "AGAINST":
                c = RED
                mark = "A"
            else:
                c = GRAY
                mark = "—"
            circle = plt.Circle((col_i, row_i), 0.28, color=c, zorder=3)
            ax.add_patch(circle)
            ax.text(col_i, row_i, mark, ha="center", va="center", color="white", fontsize=7, fontweight="bold", zorder=4)

    ax.set_xticks(range(n_cols))
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_yticks(range(n_days))
    ax.set_yticklabels([ts.date().isoformat() for ts in recent.index], fontsize=7)
    ax.set_title(
        "Same day vs EURUSD — green WITH, red AGAINST (last 60 complete days)",
        fontsize=11,
    )
    legend = [
        mpatches.Patch(color=GREEN, label="WITH EURUSD / EUR up"),
        mpatches.Patch(color=RED, label="AGAINST EURUSD / EUR down"),
        mpatches.Patch(color=GRAY, label="Flat"),
    ]
    ax.legend(handles=legend, loc="upper right", fontsize=8)
    ax.set_aspect("equal")
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=140, bbox_inches="tight")
    plt.close(fig)


def _plot_last_day_board(
    last_detail: pd.DataFrame,
    sentence: str,
    out_path: Path,
) -> None:
    fig, ax = plt.subplots(figsize=(12, 5.5))
    ax.set_xlim(0, 7)
    ax.set_ylim(0, 3.2)
    ax.axis("off")
    ax.set_title(sentence, fontsize=10, wrap=True, pad=12)

    for i, row in last_detail.iterrows():
        x = float(i)
        pair = str(row["pair"])
        vs = str(row["vs_eurusd"])
        qdir = str(row["quote_direction"])
        aligned = float(row["aligned_pct"])
        quote_pct = float(row["quote_pct"])

        if vs == "anchor":
            face = "#1565c0"
            badge = f"EURUSD {qdir.upper()}"
        elif vs == "WITH":
            face = GREEN
            badge = "WITH EURUSD"
        elif vs == "AGAINST":
            face = RED
            badge = "AGAINST EURUSD"
        else:
            face = GRAY
            badge = "FLAT"

        box = FancyBboxPatch(
            (x + 0.08, 0.4),
            0.84,
            2.3,
            boxstyle="round,pad=0.03",
            facecolor=face,
            edgecolor="white",
            alpha=0.92,
        )
        ax.add_patch(box)
        ax.text(x + 0.5, 2.4, pair, ha="center", va="center", color="white", fontsize=11, fontweight="bold")
        ax.text(x + 0.5, 1.95, badge, ha="center", va="center", color="white", fontsize=8)
        ax.text(
            x + 0.5,
            1.45,
            f"quote {qdir}\n{100.0 * quote_pct:+.3f}%",
            ha="center",
            va="center",
            color="white",
            fontsize=8,
        )
        ax.text(
            x + 0.5,
            0.85,
            f"aligned\n{100.0 * aligned:+.3f}%",
            ha="center",
            va="center",
            color="white",
            fontsize=8,
        )

    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=140, bbox_inches="tight")
    plt.close(fig)


def _plot_seven(
    panel: pd.DataFrame,
    headline: str,
    winners: list[str],
    out_path: Path,
) -> None:
    cum = panel[CURRENCIES].cumsum()
    fig, ax = plt.subplots(figsize=(12, 6.2))
    for currency in CURRENCIES:
        is_winner = currency in winners
        ax.plot(
            cum.index,
            cum[currency],
            color=OUTLIER_COLOR if is_winner else DEFAULT_COLORS[currency],
            linewidth=2.4 if is_winner else 1.2,
            alpha=1.0 if is_winner else 0.85,
            label=f"{currency} (out of line most)" if is_winner else currency,
            zorder=3 if is_winner else 2,
        )
    ax.axhline(0.0, color="gray", linewidth=0.6)
    ax.set_title(headline, fontsize=11)
    ax.set_ylabel("Cumulative aligned log return vs USD")
    ax.set_xlabel("Date (UTC)")
    ax.legend(loc="upper left", ncol=2, frameon=True)
    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=140)
    plt.close(fig)


def _fmt_pct(value: float) -> str:
    if pd.isna(value):
        return ""
    return f"{100.0 * value:.3f}%"


def _fmt_num(value: float) -> str:
    if pd.isna(value):
        return ""
    return f"{value:.6f}"


def _cell_class(call: str) -> str:
    if call == "WITH":
        return "with"
    if call == "AGAINST":
        return "against"
    if call == "anchor":
        return "anchor"
    return "flat"


def _write_html(
    path: Path,
    last_sentence: str,
    pack_headline: str,
    pack_last: str,
    last_detail: pd.DataFrame,
    board: pd.DataFrame,
    rates: pd.DataFrame,
    summary: pd.DataFrame,
) -> None:
    recent = board.tail(WINDOW).copy()

    detail_rows = []
    for _, row in last_detail.iterrows():
        cls = _cell_class(str(row["vs_eurusd"]))
        detail_rows.append(
            "<tr>"
            f"<td>{html.escape(str(row['pair']))}</td>"
            f"<td>{_fmt_num(float(row['open']))}</td>"
            f"<td>{_fmt_num(float(row['high']))}</td>"
            f"<td>{_fmt_num(float(row['low']))}</td>"
            f"<td>{_fmt_num(float(row['close']))}</td>"
            f"<td>{html.escape(_fmt_pct(float(row['quote_pct'])))}</td>"
            f"<td>{html.escape(_fmt_pct(float(row['aligned_pct'])))}</td>"
            f"<td>{html.escape(str(row['quote_direction']))}</td>"
            f"<td class=\"{cls}\">{html.escape(str(row['vs_eurusd']))}</td>"
            "</tr>"
        )

    board_rows = []
    for ts, row in recent.iterrows():
        cells = []
        for currency in OTHERS:
            call = str(row[f"vs_eur_{currency}"])
            cells.append(f"<td class=\"{_cell_class(call)}\">{html.escape(call)}</td>")
        board_rows.append(
            "<tr>"
            f"<td>{html.escape(ts.date().isoformat())}</td>"
            f"<td class=\"{_cell_class('WITH' if row['eur_dir'] == 'up' else 'AGAINST' if row['eur_dir'] == 'down' else 'flat')}\">"
            f"{html.escape(str(row['eur_dir']))}</td>"
            f"{''.join(cells)}"
            f"<td>{int(row['n_with_eur'])}/6</td>"
            "</tr>"
        )

    rate_rows = []
    for _, row in rates.iterrows():
        pct_with = f"{float(row['pct_with']):.1f}%"
        pct_against = f"{float(row['pct_against']):.1f}%"
        rate_rows.append(
            "<tr>"
            f"<td>{html.escape(str(row['pair']))}</td>"
            f"<td>{int(row['days_with'])}</td>"
            f"<td>{int(row['days_against'])}</td>"
            f"<td>{int(row['days_flat'])}</td>"
            f"<td>{html.escape(pct_with)}</td>"
            f"<td>{html.escape(pct_against)}</td>"
            "</tr>"
        )

    summary_rows = []
    for _, row in summary.iterrows():
        summary_rows.append(
            "<tr>"
            f"<td>{html.escape(str(row['currency']))}</td>"
            f"<td>{int(row['days_in_sample'])}</td>"
            f"<td>{int(row['days_with_pack'])}</td>"
            f"<td>{int(row['days_out_of_line'])}</td>"
            f"<td>{int(row['lone_dissenter_days'])}</td>"
            f"<td>{int(row['break_days'])}</td>"
            f"<td>{html.escape(str(row['last_call']))}</td>"
            "</tr>"
        )

    other_headers = "".join(f"<th>{CURRENCY_LEGS[c][0]}</th>" for c in OTHERS)
    body = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>EURUSD same-day candle board</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 24px; color: #222; max-width: 1100px; }}
h1 {{ font-size: 1.35rem; margin-bottom: 0.4rem; }}
h2 {{ font-size: 1.1rem; margin-top: 1.8rem; }}
p {{ line-height: 1.45; }}
img {{ max-width: 100%; height: auto; border: 1px solid #ddd; margin: 0.6rem 0 1rem; }}
table {{ border-collapse: collapse; font-size: 0.88rem; margin-top: 0.6rem; width: 100%; }}
th, td {{ border: 1px solid #ccc; padding: 5px 8px; text-align: right; }}
th:first-child, td:first-child {{ text-align: left; }}
th {{ background: #f3f3f3; }}
.note {{ color: #555; font-size: 0.92rem; }}
.with {{ background: #c8e6c9; color: #1b5e20; font-weight: bold; text-align: center; }}
.against {{ background: #ffcdd2; color: #b71c1c; font-weight: bold; text-align: center; }}
.flat {{ background: #eeeeee; color: #616161; text-align: center; }}
.anchor {{ background: #bbdefb; color: #0d47a1; font-weight: bold; text-align: center; }}
.lead {{ font-size: 1.05rem; background: #f7f9fc; border-left: 4px solid #1565c0; padding: 12px 14px; }}
</style>
</head>
<body>
<h1>EURUSD same-day candle board</h1>
<p class="lead">{html.escape(last_sentence)}</p>
<p class="note">
Seven USD pairs only (EURGBP left out). Anchor is EURUSD close direction that day.
WITH means the other currency's aligned move (currency vs USD) matched EUR that day.
USDJPY, USDCHF, and USDCAD are flipped for alignment, so USDCHF WITH EURUSD usually
means the USDCHF quote candle went down. Same-day co-move record for Kendall-method
research — not a trade signal and not a crash forecast.
</p>

<h2>Last complete day</h2>
<img src="last_day_board.png" alt="Last day WITH/AGAINST board"/>
<table>
<thead>
<tr>
<th>Pair</th><th>Open</th><th>High</th><th>Low</th><th>Close</th>
<th>Quote %</th><th>Aligned %</th><th>Quote dir</th><th>vs EURUSD</th>
</tr>
</thead>
<tbody>
{"".join(detail_rows)}
</tbody>
</table>

<h2>Daily candles — all seven pairs (last 60 days)</h2>
<img src="candles_seven.png" alt="Seven stacked daily candle panels"/>

<h2>Same day vs EURUSD (last 60 days)</h2>
<img src="eurusd_with_against.png" alt="WITH/AGAINST dots versus EURUSD"/>
<table>
<thead>
<tr>
<th>Date</th><th>EURUSD</th>{other_headers}<th>With EUR</th>
</tr>
</thead>
<tbody>
{"".join(board_rows)}
</tbody>
</table>

<h2>Full history — how often each pair moves with EURUSD</h2>
<table>
<thead>
<tr>
<th>Pair</th><th>Days with</th><th>Days against</th><th>Days flat</th>
<th>% with</th><th>% against</th>
</tr>
</thead>
<tbody>
{"".join(rate_rows)}
</tbody>
</table>

<h2>Side note — pack-median out of line</h2>
<p>{html.escape(pack_headline)}</p>
<p>{html.escape(pack_last)}</p>
<img src="seven_currencies.png" alt="Long-run cumulative aligned paths"/>
<table>
<thead>
<tr>
<th>Currency</th><th>Days</th><th>With pack</th><th>Out of line</th>
<th>Lone dissenter</th><th>Break days</th><th>Last vs pack</th>
</tr>
</thead>
<tbody>
{"".join(summary_rows)}
</tbody>
</table>
</body>
</html>
"""
    path.write_text(body, encoding="utf-8")


def _write_notes(
    path: Path,
    last_sentence: str,
    pack_headline: str,
    pack_last: str,
    drop_note: str,
    rates: pd.DataFrame,
    summary: pd.DataFrame,
) -> None:
    lines = [
        "# EURUSD same-day candle board",
        "",
        "## Last complete day",
        "",
        last_sentence,
        "",
        "## Pack-median side note",
        "",
        pack_headline,
        "",
        pack_last,
        "",
        "## Snapshot",
        "",
        f"- Folder: `{SNAPSHOT_REL.as_posix()}`",
        "- EURGBP left out.",
        "- Anchor: EURUSD close direction that day.",
        "- WITH/AGAINST uses aligned currency-vs-USD signs (USDJPY, USDCHF, USDCAD flipped).",
        f"- Candle / board window: last {WINDOW} complete days.",
        f"- {drop_note}",
        "",
        "## Full history vs EURUSD",
        "",
        "| pair | days with | days against | % with | % against |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for _, row in rates.iterrows():
        lines.append(
            f"| {row['pair']} | {int(row['days_with'])} | {int(row['days_against'])} | "
            f"{float(row['pct_with']):.1f}% | {float(row['pct_against']):.1f}% |"
        )
    lines.extend(
        [
            "",
            "## Pack-median counts",
            "",
            "| currency | days | with pack | out of line | lone dissenter | break days |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for _, row in summary.iterrows():
        lines.append(
            f"| {row['currency']} | {int(row['days_in_sample'])} | "
            f"{int(row['days_with_pack'])} | {int(row['days_out_of_line'])} | "
            f"{int(row['lone_dissenter_days'])} | {int(row['break_days'])} |"
        )
    lines.extend(
        [
            "",
            "This NOTES.md is a same-day co-move record. It is not a crash forecast and not a trading signal.",
            "",
        ]
    )
    path.write_text("\n".join(lines), encoding="utf-8")


def _excel_time(series: pd.Series) -> pd.Series:
    times = pd.to_datetime(series, utc=True)
    return times.dt.tz_convert("UTC").dt.tz_localize(None)


def _last_60_export(board: pd.DataFrame) -> pd.DataFrame:
    recent = board.tail(WINDOW).copy().reset_index()
    cols = ["time", "eur_dir", "n_with_eur", "n_against_eur", "n_flat_vs_eur"]
    for currency in OTHERS:
        pair = CURRENCY_LEGS[currency][0]
        recent[pair] = recent[f"vs_eur_{currency}"]
        cols.append(pair)
    out = recent[cols].copy()
    out["time"] = _excel_time(out["time"])
    return out


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    snapshot = load_snapshot(REPO_ROOT / SNAPSHOT_REL)
    cleaned, drop_note = _prepare_frames(snapshot["frames"])
    panel = _aligned_panel(cleaned)
    annotated = _annotate_days(panel)
    board = _eurusd_board(panel)
    breaks = _break_days(annotated)
    summary = _currency_summary(annotated, breaks)
    rates = _vs_eurusd_rates(board)
    last_ts, last_detail, last_sentence = _last_day_detail(cleaned, board)
    pack_headline, pack_last = _pack_verdict_lines(summary, annotated)
    max_out = int(summary["days_out_of_line"].max())
    winners = summary.loc[summary["days_out_of_line"] == max_out, "currency"].tolist()

    window_dates = board.tail(WINDOW).index
    ohlc = _ohlc_panel(cleaned, window_dates)

    candles_path = OUT_DIR / "candles_seven.png"
    with_path = OUT_DIR / "eurusd_with_against.png"
    last_board_path = OUT_DIR / "last_day_board.png"
    cum_path = OUT_DIR / "seven_currencies.png"

    _plot_candles_seven(ohlc, window_dates, candles_path)
    _plot_with_against(board, with_path)
    _plot_last_day_board(last_detail, last_sentence, last_board_path)
    _plot_seven(panel, pack_headline, winners, cum_path)

    summary_out = summary.copy()
    summary_out["last_day"] = _excel_time(summary_out["last_day"])
    daily_out = annotated.reset_index()
    daily_out["time"] = _excel_time(daily_out["time"])
    break_out = breaks.copy()
    if len(break_out):
        break_out["time"] = _excel_time(break_out["time"])
    last60 = _last_60_export(board)
    last_detail_out = last_detail.copy()
    last_detail_out.insert(0, "time", last_ts.tz_convert("UTC").tz_localize(None))

    _write_html(
        OUT_DIR / "verdict.html",
        last_sentence,
        pack_headline,
        pack_last,
        last_detail,
        board,
        rates,
        summary,
    )
    _write_notes(
        EXP_DIR / "NOTES.md",
        last_sentence,
        pack_headline,
        pack_last,
        drop_note,
        rates,
        summary,
    )

    xlsx_path = OUT_DIR / "line_check.xlsx"
    try:
        with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
            last_detail_out.to_excel(writer, sheet_name="last_day", index=False)
            last60.to_excel(writer, sheet_name="last_60_with_against", index=False)
            rates.to_excel(writer, sheet_name="vs_eurusd_rates", index=False)
            summary_out.to_excel(writer, sheet_name="currency_summary", index=False)
            daily_out.to_excel(writer, sheet_name="daily_panel", index=False)
            break_out.to_excel(writer, sheet_name="break_days", index=False)
    except PermissionError:
        xlsx_path = OUT_DIR / "line_check_new.xlsx"
        with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
            last_detail_out.to_excel(writer, sheet_name="last_day", index=False)
            last60.to_excel(writer, sheet_name="last_60_with_against", index=False)
            rates.to_excel(writer, sheet_name="vs_eurusd_rates", index=False)
            summary_out.to_excel(writer, sheet_name="currency_summary", index=False)
            daily_out.to_excel(writer, sheet_name="daily_panel", index=False)
            break_out.to_excel(writer, sheet_name="break_days", index=False)
        print(
            "line_check.xlsx is open in another program; "
            f"wrote {xlsx_path.name} instead."
        )

    print(last_sentence)
    print(pack_headline)
    print(f"Wrote {candles_path}")
    print(f"Wrote {with_path}")
    print(f"Wrote {last_board_path}")
    print(f"Wrote {cum_path}")
    print(f"Wrote {xlsx_path}")
    print(f"Wrote {OUT_DIR / 'verdict.html'}")
    print(f"Wrote {EXP_DIR / 'NOTES.md'}")


if __name__ == "__main__":
    main()
