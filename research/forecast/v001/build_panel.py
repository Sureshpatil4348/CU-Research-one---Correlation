"""Join time-t feature files. Does not import method code or build labels."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

EXP_DIR = Path(__file__).resolve().parent
OUT_DIR = EXP_DIR / "outputs"
HASH_FILE = EXP_DIR / "v001_hashes.txt"

FEATURE_FILES = {
    "01 - Pearson Correlation/experiments/v002/outputs/features.parquet": ["m01_expanding_r"],
    "05 - Rolling Correlation/experiments/v002/outputs/features.parquet": [
        "m05_r20",
        "m05_r60",
        "m05_r100",
        "m05_abs_gap",
    ],
    "07 - Partial and Residual Correlation/experiments/v002/outputs/features.parquet": ["m07_rho_partial"],
    "10 - Asymmetric DCC/experiments/v003/outputs/features.parquet": ["m10_adcc_minus_r"],
    "11 - Regime-Conditioned Correlation/experiments/v003/outputs/features.parquet": ["m11_adj_gap"],
    "14 - Distance Correlation/experiments/v002/outputs/features.parquet": ["m14_dcor"],
    "19 - Tail Dependence/experiments/v003/outputs/features.parquet": ["m19_excess_lower"],
    "28 - Networks PCA and Connectedness/experiments/v003/outputs/features.parquet": [
        "m28_d_ij",
        "m28_pc1_share",
        "m28_tci",
    ],
}

BANNED = {"label", "y", "t1", "t2", "spike", "break", "rv_fwd"}


def assert_feature_frame(frame: pd.DataFrame) -> None:
    banned = BANNED.intersection(frame.columns)
    if banned:
        raise RuntimeError(f"Feature file contains a label column: {sorted(banned)}")
    asof = pd.to_datetime(frame["feature_asof"], utc=True)
    date = pd.to_datetime(frame["date"], utc=True)
    if (asof > date).any():
        raise RuntimeError("feature_asof is after the row date")


def _self_check() -> None:
    bad = pd.DataFrame(
        {
            "date": [pd.Timestamp("2020-01-02", tz="UTC")],
            "feature_asof": [pd.Timestamp("2020-01-03", tz="UTC")],
        }
    )
    try:
        assert_feature_frame(bad)
    except RuntimeError:
        return
    raise RuntimeError("A deliberately shifted feature date was accepted")


def verify_v001_hashes() -> None:
    for line in HASH_FILE.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, rel = line.split("  ", 1)
        path = REPO_ROOT / rel
        if not path.is_file():
            raise RuntimeError(f"v001 file missing: {rel}")
        got = hashlib.sha256(path.read_bytes()).hexdigest()
        if got != digest:
            raise RuntimeError(f"v001 file hash changed: {rel}")


def _load_one(rel: str, columns: list[str]) -> pd.DataFrame:
    path = REPO_ROOT / rel
    frame = pd.read_parquet(path)
    assert_feature_frame(frame)
    missing = [col for col in columns if col not in frame.columns]
    if missing:
        raise RuntimeError(f"{rel} is missing {missing}")
    keep = frame[["date", "pair", *columns]].copy()
    keep["date"] = pd.to_datetime(keep["date"], utc=True).dt.normalize()
    keep["pair"] = keep["pair"].astype(str)
    return keep


def build() -> Path:
    _self_check()
    verify_v001_hashes()
    merged: pd.DataFrame | None = None
    for rel, columns in FEATURE_FILES.items():
        part = _load_one(rel, columns)
        if merged is None:
            merged = part
        else:
            merged = merged.merge(part, on=["date", "pair"], how="outer")
    if merged is None or merged.empty:
        raise RuntimeError("Feature panel is empty")
    merged = merged.sort_values(["date", "pair"]).reset_index(drop=True)
    merged["feature_asof"] = merged["date"]
    assert_feature_frame(merged)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / "panel.parquet"
    merged.to_parquet(path, index=False)
    print(f"panel rows={len(merged)} pairs={merged['pair'].nunique()} cols={list(merged.columns)}", flush=True)
    return path


if __name__ == "__main__":
    build()
