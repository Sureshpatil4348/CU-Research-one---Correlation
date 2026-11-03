"""Major FX universe and broker-aware symbol resolution."""

from __future__ import annotations

from typing import Any

import MetaTrader5 as mt5

from .connection import MT5ConnectionError, ensure_connected

# Eight majors for this research phase. EURGBP is the eighth pair.
MAJOR_PAIRS: tuple[str, ...] = (
    "EURUSD",
    "GBPUSD",
    "AUDUSD",
    "NZDUSD",
    "USDJPY",
    "USDCHF",
    "USDCAD",
    "EURGBP",
)

# Alpari (and similar) naming: logical EURUSD -> broker EURUSD_i.
BROKER_SUFFIX = "_i"


def resolve_symbol(base_name: str) -> str:
    """
    Resolve a logical pair name to the broker symbol string.

    Prefers the exact `{base}_i` name used on the current Alpari account.
    Falls back to the exact base name, then to a Market Watch name that
    starts with the base. Raises if none of those exist.
    """
    ensure_connected()

    preferred = f"{base_name}{BROKER_SUFFIX}"
    info = mt5.symbol_info(preferred)
    if info is not None:
        if not info.visible:
            mt5.symbol_select(preferred, True)
        return info.name

    info = mt5.symbol_info(base_name)
    if info is not None:
        if not info.visible:
            mt5.symbol_select(base_name, True)
        return info.name

    symbols = mt5.symbols_get()
    if symbols is None:
        raise MT5ConnectionError(
            f"Could not list symbols while resolving {base_name}: {mt5.last_error()}"
        )

    candidates = [
        s.name
        for s in symbols
        if s.name == preferred
        or s.name == base_name
        or s.name.startswith(base_name)
    ]
    if not candidates:
        account = mt5.account_info()
        server = "unknown" if account is None else account.server
        raise MT5ConnectionError(
            f"Symbol {preferred} (logical {base_name}) not found on server {server}. "
            "Add the pair to Market Watch or check the broker naming."
        )

    # Prefer exact _i, then exact base, then shortest other match.
    def rank(name: str) -> tuple[int, int, str]:
        if name == preferred:
            return (0, len(name), name)
        if name == base_name:
            return (1, len(name), name)
        return (2, len(name), name)

    candidates.sort(key=rank)
    chosen = candidates[0]
    mt5.symbol_select(chosen, True)
    return chosen


def resolve_majors() -> dict[str, str]:
    """Map each logical major to the resolved broker symbol name."""
    return {name: resolve_symbol(name) for name in MAJOR_PAIRS}


def major_resolution_report() -> list[dict[str, Any]]:
    """Return resolution details useful for a snapshot manifest."""
    ensure_connected()
    rows: list[dict[str, Any]] = []
    for logical in MAJOR_PAIRS:
        resolved = resolve_symbol(logical)
        info = mt5.symbol_info(resolved)
        rows.append(
            {
                "logical": logical,
                "resolved": resolved,
                "digits": None if info is None else info.digits,
                "point": None if info is None else info.point,
                "currency_base": None if info is None else info.currency_base,
                "currency_profit": None if info is None else info.currency_profit,
            }
        )
    return rows
