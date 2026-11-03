"""Attach to an already-logged-in MetaTrader 5 terminal. No credentials are stored."""

from __future__ import annotations

from typing import Any

import MetaTrader5 as mt5


class MT5ConnectionError(RuntimeError):
    """Raised when the terminal cannot be initialized or is not logged in."""


def connect() -> dict[str, Any]:
    """Initialize against the running terminal and return account/terminal info."""
    if not mt5.initialize():
        code, message = mt5.last_error()
        raise MT5ConnectionError(
            f"MetaTrader 5 initialize failed ({code}): {message}. "
            "Open MT5, log in, then retry."
        )

    account = mt5.account_info()
    terminal = mt5.terminal_info()
    if account is None or terminal is None:
        err = mt5.last_error()
        mt5.shutdown()
        raise MT5ConnectionError(
            f"MT5 initialized but account/terminal info is unavailable: {err}"
        )

    return {
        "login": account.login,
        "server": account.server,
        "name": account.name,
        "company": account.company,
        "currency": account.currency,
        "trade_allowed": bool(terminal.trade_allowed),
        "connected": bool(terminal.connected),
        "path": terminal.path,
        "build": terminal.build,
    }


def ensure_connected() -> dict[str, Any]:
    """Return connection info, initializing if needed."""
    terminal = mt5.terminal_info()
    if terminal is None or not terminal.connected:
        return connect()
    account = mt5.account_info()
    if account is None:
        return connect()
    return {
        "login": account.login,
        "server": account.server,
        "name": account.name,
        "company": account.company,
        "currency": account.currency,
        "trade_allowed": bool(terminal.trade_allowed),
        "connected": bool(terminal.connected),
        "path": terminal.path,
        "build": terminal.build,
    }


def disconnect() -> None:
    """Shut down the Python–MT5 bridge."""
    mt5.shutdown()
