# shared/mt5_data

Reusable MetaTrader 5 bridge for this research repo. Method folders must not open MT5 themselves. They load a frozen snapshot from `data/snapshots/` instead.

## What this package does

- `connection.py` — attach to a terminal that is already logged in; shut down the bridge. No account password is stored.
- `universe.py` — the eight majors and broker-aware symbol resolution. Prefers `{NAME}_i` (Alpari), then the exact base name, then other suffix matches.
- `snapshot.py` — pull bars into a new dated folder under `data/snapshots/`. Refuses to write into an existing snapshot folder. Supports a fixed year window or a chunked full-history pull. `load_snapshot` reads a folder without contacting MT5.

## Eight majors

EURUSD, GBPUSD, AUDUSD, NZDUSD, USDJPY, USDCHF, USDCAD, EURGBP.

On Alpari-MT5 these resolve to `EURUSD_i`, `GBPUSD_i`, and so on. CSV files keep the logical names without the suffix.

## Create a snapshot

From the repo root, with MT5 open and logged in.

Fixed year window:

```python
from shared.mt5_data import create_snapshot

path = create_snapshot(timeframe="D1", years=5)
print(path)
```

Full available history (year chunks; used for the Alpari Pearson study):

```python
from shared.mt5_data import create_snapshot

path = create_snapshot(timeframe="D1", full_history=True, label="majors_alpari")
print(path)
```

Or:

```bash
python -m shared.mt5_data.cli --full-history --label majors_alpari
```

## Load a snapshot in a later experiment

```python
from shared.mt5_data import load_snapshot

snap = load_snapshot("data/snapshots/YYYY-MM-DD_majors_alpari_D1")
eurusd = snap["frames"]["EURUSD"]
manifest = snap["manifest"]
```

Name that snapshot folder in the experiment `NOTES.md`. Do not call `create_snapshot` from a method experiment unless you intentionally want a new dated freeze.

## Rules

- Do not overwrite an existing snapshot folder.
- Do not compute log returns here; later method experiments follow the formula guide.
- Do not import this package from inside another method to open MT5 for ad-hoc analysis. Use frozen data.
