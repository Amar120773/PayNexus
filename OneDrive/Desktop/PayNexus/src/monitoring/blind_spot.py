"""Blind-spot detection for the frozen MuleHunter V2 model.

This module scores merchants using the serialized frozen model and threshold,
compares predictions against ground-truth labels, and identifies recall
degradation, false-negative concentration, segment-specific failure, and
feature drift.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.model_selection import train_test_split

from src.inference.scorer import InferenceEngine
from src.features_v2.evolution_features import extract_evolution_features
from src.models.model_utils import evaluate_predictions


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class BlindSpotReport:
    """Complete blind-spot analysis output."""

    scoring_timestamp: str
    global_metrics: dict = field(default_factory=dict)
    baseline_metrics: dict = field(default_factory=dict)
    recall_degradation: dict = field(default_factory=dict)
    segment_metrics: list[dict] = field(default_factory=list)
    fn_concentration: list[dict] = field(default_factory=list)
    feature_drift: list[dict] = field(default_factory=list)
    blind_spots: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    def save(self, path: Path | str) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2, default=str)

    @classmethod
    def load(cls, path: Path | str) -> "BlindSpotReport":
        with open(path, "r") as f:
            data = json.load(f)
        return cls(**data)


# ---------------------------------------------------------------------------
# Split reconstruction
# ---------------------------------------------------------------------------

def reconstruct_phase4b_splits(
    features_path: str = "data/synthetic_v2/evolution_features.csv",
    labels_path: str = "data/synthetic_v2/merchant_labels.csv",
) -> tuple[np.ndarray, np.ndarray, np.ndarray, pd.DataFrame]:
    """Reconstruct the exact Phase 4B train/val/test split indices.

    Uses the identical deterministic logic from ``src/models/train_and_save.py``:
    1.  ``train_test_split(X, y, test_size=0.15, random_state=42, stratify=y)``
    2.  ``train_test_split(X_tv, y_tv, test_size=0.1765, random_state=42, stratify=y_tv)``

    Returns (train_idx, val_idx, test_idx, merged_df).  Raises if the
    reconstructed sizes do not match the serialized model metadata.
    """
    features_df = pd.read_csv(features_path)
    labels_df = pd.read_csv(labels_path)
    merged = features_df.merge(labels_df[["merchant_id", "is_mule"]], on="merchant_id")

    y = merged["is_mule"].to_numpy()
    indices = np.arange(len(merged))

    idx_train_val, idx_test = train_test_split(
        indices, test_size=0.15, random_state=42, stratify=y
    )
    idx_train, idx_val = train_test_split(
        idx_train_val, test_size=0.1765, random_state=42, stratify=y[idx_train_val]
    )

    # Verify against serialized metadata
    metadata_path = Path("artifacts/model_metadata.json")
    if metadata_path.exists():
        with open(metadata_path) as f:
            meta = json.load(f)
        expected = (meta["training_split"], meta["validation_split"], meta["test_split"])
        actual = (len(idx_train), len(idx_val), len(idx_test))
        if expected != actual:
            raise RuntimeError(
                f"Split reconstruction mismatch!  Expected {expected}, got {actual}.  "
                f"Cannot guarantee validation split identity."
            )

    return idx_train, idx_val, idx_test, merged


# ---------------------------------------------------------------------------
# Feature drift
# ---------------------------------------------------------------------------

def compute_psi(reference: np.ndarray, current: np.ndarray, bins: int = 10) -> float:
    """Population Stability Index between two 1-D distributions."""
    ref_clean = reference[~np.isnan(reference)]
    cur_clean = current[~np.isnan(current)]

    if len(ref_clean) == 0 or len(cur_clean) == 0:
        return 0.0

    breakpoints = np.percentile(ref_clean, np.linspace(0, 100, bins + 1))
    breakpoints[0] = -np.inf
    breakpoints[-1] = np.inf
    breakpoints = np.unique(breakpoints)

    ref_counts = np.histogram(ref_clean, bins=breakpoints)[0].astype(float)
    cur_counts = np.histogram(cur_clean, bins=breakpoints)[0].astype(float)

    # Add small epsilon to avoid division by zero / log(0)
    eps = 1e-4
    ref_pct = ref_counts / ref_counts.sum() + eps
    cur_pct = cur_counts / cur_counts.sum() + eps

    psi = float(np.sum((cur_pct - ref_pct) * np.log(cur_pct / ref_pct)))
    return round(psi, 6)


def compute_ks(reference: np.ndarray, current: np.ndarray) -> tuple[float, float]:
    """Two-sample Kolmogorov-Smirnov test.  Returns (statistic, p_value)."""
    ref_clean = reference[~np.isnan(reference)]
    cur_clean = current[~np.isnan(current)]
    if len(ref_clean) < 2 or len(cur_clean) < 2:
        return 0.0, 1.0
    stat, pval = stats.ks_2samp(ref_clean, cur_clean)
    return round(float(stat), 6), round(float(pval), 6)


# ---------------------------------------------------------------------------
# Analyzer
# ---------------------------------------------------------------------------

class BlindSpotAnalyzer:
    """Score every merchant with the frozen model and detect blind spots."""

    FEATURE_COLS = [
        "volume_delta_t1_t2", "volume_delta_t2_t3",
        "refund_delta_t1_t2", "refund_delta_t2_t3",
        "network_growth_t1_t2", "network_growth_t2_t3",
        "device_churn_t1_t2", "device_churn_t2_t3",
        "ip_churn_t1_t2", "ip_churn_t2_t3",
    ]

    def __init__(
        self,
        engine: InferenceEngine,
        labels: pd.DataFrame,
        networks: pd.DataFrame,
        features_df: pd.DataFrame,
        merchants_df: pd.DataFrame | None = None,
        scoring_timestamp: str = "2026-04-01",
    ):
        self.engine = engine
        self.labels = labels.copy()
        self.networks = networks.copy()
        self.features_df = features_df.copy()
        self.merchants_df = merchants_df.copy() if merchants_df is not None else None
        self.scoring_timestamp = scoring_timestamp

    # -- internal helpers --------------------------------------------------

    def _build_scored_df(self) -> pd.DataFrame:
        """Score all merchants using the frozen model and frozen threshold."""
        X = self.features_df[self.FEATURE_COLS].fillna(0).to_numpy()
        probs = self.engine.model.predict_proba(X)[:, 1]
        predicted = (probs >= self.engine.threshold).astype(int)

        scored = self.features_df[["merchant_id"]].copy()
        scored["probability"] = probs
        scored["predicted_label"] = predicted

        # Attach ground truth
        scored = scored.merge(
            self.labels[["merchant_id", "is_mule", "mule_type", "network_id"]],
            on="merchant_id", how="left",
        )
        scored["is_mule"] = scored["is_mule"].fillna(0).astype(int)
        return scored

    # -- public analysis methods -------------------------------------------

    def compute_global_metrics(self, scored: pd.DataFrame) -> dict:
        y_true = scored["is_mule"].to_numpy()
        y_prob = scored["probability"].to_numpy()
        return evaluate_predictions(y_true, y_prob, threshold=self.engine.threshold)

    def compute_baseline_metrics(self) -> dict:
        """Evaluate the frozen model on the exact Phase 4B validation split."""
        idx_train, idx_val, idx_test, merged = reconstruct_phase4b_splits()

        X_val = merged.iloc[idx_val][self.FEATURE_COLS].fillna(0).to_numpy()
        y_val = merged.iloc[idx_val]["is_mule"].to_numpy()

        val_probs = self.engine.model.predict_proba(X_val)[:, 1]
        metrics = evaluate_predictions(y_val, val_probs, threshold=self.engine.threshold)
        metrics["split"] = "validation"
        metrics["split_size"] = int(len(idx_val))
        return metrics

    def detect_recall_degradation(
        self, global_metrics: dict, baseline_metrics: dict, tolerance: float = 0.05
    ) -> dict:
        current_recall = global_metrics["recall"]
        baseline_recall = baseline_metrics["recall"]
        delta = round(current_recall - baseline_recall, 4)
        return {
            "baseline_recall": baseline_recall,
            "current_recall": current_recall,
            "delta": delta,
            "degraded": delta < -tolerance,
        }

    def compute_segment_metrics(
        self, scored: pd.DataFrame, segment_col: str, segment_name: str
    ) -> list[dict]:
        rows = []
        for seg_val, group in scored.groupby(segment_col):
            y_true = group["is_mule"].to_numpy()
            y_prob = group["probability"].to_numpy()
            m = evaluate_predictions(y_true, y_prob, threshold=self.engine.threshold)
            m["segment_axis"] = segment_name
            m["segment_value"] = str(seg_val)
            m["segment_size"] = int(len(group))
            rows.append(m)
        return rows

    def detect_fn_concentration(self, scored: pd.DataFrame) -> list[dict]:
        """Find segments where false negatives are disproportionately concentrated."""
        fn_mask = (scored["is_mule"] == 1) & (scored["predicted_label"] == 0)
        total_fn = int(fn_mask.sum())
        total_mules = int((scored["is_mule"] == 1).sum())
        if total_fn == 0 or total_mules == 0:
            return []

        results = []
        for seg_col, seg_name in [("mule_type", "mule_type")]:
            mules_only = scored[scored["is_mule"] == 1]
            for seg_val, group in mules_only.groupby(seg_col):
                if not seg_val:
                    continue
                fn_in_seg = int(((group["predicted_label"] == 0)).sum())
                total_in_seg = len(group)
                fn_rate = round(fn_in_seg / max(total_in_seg, 1), 4)
                fn_share = round(fn_in_seg / max(total_fn, 1), 4)
                population_share = round(total_in_seg / max(total_mules, 1), 4)
                concentrated = fn_share >= 2 * population_share
                results.append({
                    "segment_axis": seg_name,
                    "segment_value": str(seg_val),
                    "fn_count": fn_in_seg,
                    "total_mules_in_segment": total_in_seg,
                    "fn_rate": fn_rate,
                    "fn_share_of_all_fn": fn_share,
                    "population_share": population_share,
                    "concentrated": concentrated,
                })
        return results

    def detect_feature_drift(self) -> list[dict]:
        """Compare training-split feature distributions to full-population distributions."""
        idx_train, _, _, merged = reconstruct_phase4b_splits()

        results = []
        for col in self.FEATURE_COLS:
            ref = merged.iloc[idx_train][col].fillna(0).to_numpy()
            cur = self.features_df[col].fillna(0).to_numpy()

            psi = compute_psi(ref, cur)
            ks_stat, ks_pval = compute_ks(ref, cur)

            results.append({
                "feature": col,
                "psi": psi,
                "psi_alert": psi > 0.2,
                "ks_statistic": ks_stat,
                "ks_pvalue": ks_pval,
                "ks_alert": ks_pval < 0.01,
                "reference_split": "train",
                "reference_size": int(len(idx_train)),
                "current_size": int(len(cur)),
            })
        return results

    def _identify_blind_spots(
        self,
        recall_degradation: dict,
        fn_concentration: list[dict],
        segment_metrics: list[dict],
        feature_drift: list[dict],
    ) -> list[dict]:
        """Synthesize detected blind spots into a human-readable list."""
        spots = []

        if recall_degradation.get("degraded"):
            spots.append({
                "type": "RECALL_DEGRADATION",
                "severity": "HIGH",
                "description": (
                    f"Global recall dropped from {recall_degradation['baseline_recall']:.4f} "
                    f"to {recall_degradation['current_recall']:.4f} "
                    f"(delta={recall_degradation['delta']:.4f})."
                ),
            })

        for item in fn_concentration:
            if item.get("concentrated"):
                spots.append({
                    "type": "FN_CONCENTRATION",
                    "severity": "HIGH",
                    "segment": item["segment_value"],
                    "description": (
                        f"Mule type '{item['segment_value']}' accounts for "
                        f"{item['fn_share_of_all_fn']*100:.1f}% of all FNs but only "
                        f"{item['population_share']*100:.1f}% of mule population."
                    ),
                })

        for seg in segment_metrics:
            global_recall_approx = recall_degradation.get("current_recall", 0)
            if seg.get("recall", 1.0) < global_recall_approx - 0.15:
                spots.append({
                    "type": "SEGMENT_FAILURE",
                    "severity": "MEDIUM",
                    "segment": f"{seg['segment_axis']}={seg['segment_value']}",
                    "description": (
                        f"Segment recall ({seg['recall']:.4f}) is significantly below "
                        f"global recall ({global_recall_approx:.4f})."
                    ),
                })

        for d in feature_drift:
            if d.get("psi_alert") or d.get("ks_alert"):
                spots.append({
                    "type": "FEATURE_DRIFT",
                    "severity": "MEDIUM" if d.get("psi_alert") else "LOW",
                    "feature": d["feature"],
                    "description": (
                        f"Feature '{d['feature']}' drifted: PSI={d['psi']:.4f}, "
                        f"KS stat={d['ks_statistic']:.4f} (p={d['ks_pvalue']:.4f})."
                    ),
                })

        return spots

    # -- main entry point --------------------------------------------------

    def run_full_analysis(self) -> BlindSpotReport:
        """Execute the complete blind-spot analysis."""
        scored = self._build_scored_df()

        # 1. Global metrics on full population
        global_metrics = self.compute_global_metrics(scored)

        # 2. Baseline metrics on original validation split
        baseline_metrics = self.compute_baseline_metrics()

        # 3. Recall degradation
        recall_deg = self.detect_recall_degradation(global_metrics, baseline_metrics)

        # 4. Segment metrics (by mule_type)
        segment_metrics = []
        mule_types = scored[scored["mule_type"].fillna("").str.len() > 0]
        if len(mule_types) > 0:
            segment_metrics.extend(
                self.compute_segment_metrics(mule_types, "mule_type", "mule_type")
            )

        # By category if merchants_df is available
        if self.merchants_df is not None and "category" in self.merchants_df.columns:
            scored_with_cat = scored.merge(
                self.merchants_df[["merchant_id", "category"]], on="merchant_id", how="left"
            )
            segment_metrics.extend(
                self.compute_segment_metrics(scored_with_cat, "category", "category")
            )

        # By volume tier
        vol_col = "volume_static_t3"
        if vol_col in self.features_df.columns:
            scored_with_vol = scored.merge(
                self.features_df[["merchant_id", vol_col]], on="merchant_id", how="left"
            )
            scored_with_vol["volume_tier"] = pd.qcut(
                scored_with_vol[vol_col].fillna(0), q=3, labels=["LOW", "MEDIUM", "HIGH"],
                duplicates="drop"
            )
            segment_metrics.extend(
                self.compute_segment_metrics(scored_with_vol, "volume_tier", "volume_tier")
            )

        # 5. FN concentration (mule_type)
        fn_conc = self.detect_fn_concentration(scored)

        # 6. Feature drift
        drift = self.detect_feature_drift()

        # 7. Synthesize blind spots
        blind_spots = self._identify_blind_spots(recall_deg, fn_conc, segment_metrics, drift)

        return BlindSpotReport(
            scoring_timestamp=self.scoring_timestamp,
            global_metrics=global_metrics,
            baseline_metrics=baseline_metrics,
            recall_degradation=recall_deg,
            segment_metrics=segment_metrics,
            fn_concentration=fn_conc,
            feature_drift=drift,
            blind_spots=blind_spots,
        )
