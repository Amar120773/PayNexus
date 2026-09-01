"""Evaluation pipeline for Network Evolution models."""

import pandas as pd
import numpy as np
from xgboost import XGBClassifier
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import precision_score, recall_score, f1_score, roc_auc_score, average_precision_score, confusion_matrix

def train_and_evaluate(features_df: pd.DataFrame, labels_df: pd.DataFrame, feature_cols: list[str]) -> dict:
    df = features_df.merge(labels_df, on="merchant_id")
    X = df[feature_cols].fillna(0)
    y = df["is_mule"]
    
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    model = XGBClassifier(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.1,
        scale_pos_weight=(len(y) - sum(y)) / max(sum(y), 1),
        random_state=42,
        eval_metric="logloss"
    )
    
    metrics = {"precision": [], "recall": [], "f1": [], "roc_auc": [], "pr_auc": [], "fpr": []}
    
    for train_idx, test_idx in skf.split(X, y):
        X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
        y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
        
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        probs = model.predict_proba(X_test)[:, 1]
        
        metrics["precision"].append(precision_score(y_test, preds, zero_division=0))
        metrics["recall"].append(recall_score(y_test, preds, zero_division=0))
        metrics["f1"].append(f1_score(y_test, preds, zero_division=0))
        metrics["roc_auc"].append(roc_auc_score(y_test, probs))
        metrics["pr_auc"].append(average_precision_score(y_test, probs))
        
        tn, fp, fn, tp = confusion_matrix(y_test, preds).ravel()
        metrics["fpr"].append(fp / (fp + tn))
        
    return {k: np.mean(v) for k, v in metrics.items()}

def run_evaluation() -> None:
    print("Running 5-Way Ablation Study...")
    
    features = pd.read_csv("data/synthetic_v2/evolution_features.csv")
    labels = pd.read_csv("data/synthetic_v2/merchant_labels.csv")
    
    models = {
        "Model A: Behavioral Static Baseline": ["volume_static_t3", "refund_rate_static_t3"],
        "Model B: Behavioral Trajectory": ["volume_delta_t1_t2", "volume_delta_t2_t3", "refund_delta_t1_t2", "refund_delta_t2_t3"],
        "Model C: Static Network": ["network_size_static_t3"],
        "Model D: Network Evolution": ["network_growth_t1_t2", "network_growth_t2_t3", "device_churn_t1_t2", "device_churn_t2_t3", "ip_churn_t1_t2", "ip_churn_t2_t3"],
        "Model E: Behavioral + Network Evolution": [
            "volume_delta_t1_t2", "volume_delta_t2_t3", "refund_delta_t1_t2", "refund_delta_t2_t3",
            "network_growth_t1_t2", "network_growth_t2_t3", "device_churn_t1_t2", "device_churn_t2_t3", "ip_churn_t1_t2", "ip_churn_t2_t3"
        ]
    }
    
    results = []
    for model_name, cols in models.items():
        res = train_and_evaluate(features, labels, cols)
        res["model"] = model_name
        res["feature_count"] = len(cols)
        results.append(res)
        
    df = pd.DataFrame(results)
    cols = ["model", "feature_count", "precision", "recall", "f1", "roc_auc", "pr_auc", "fpr"]
    df = df[cols]
    
    df.to_csv("reports/v2_model_comparison.csv", index=False)
    print("Saved evaluation results to reports/v2_model_comparison.csv")
    print(df.to_string(index=False))

if __name__ == "__main__":
    run_evaluation()
