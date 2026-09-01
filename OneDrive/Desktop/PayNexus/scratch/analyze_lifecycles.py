import pandas as pd
import numpy as np
from xgboost import XGBClassifier
from sklearn.model_selection import StratifiedKFold
import os

os.makedirs("scratch", exist_ok=True)

# Load data
features = pd.read_csv("data/synthetic_v2/evolution_features.csv")
labels = pd.read_csv("data/synthetic_v2/merchant_labels.csv")

df = features.merge(labels, on="merchant_id")

# Use Model E features
feature_cols = [
    "volume_delta_t1_t2", "volume_delta_t2_t3", "refund_delta_t1_t2", "refund_delta_t2_t3",
    "network_growth_t1_t2", "network_growth_t2_t3", "device_churn_t1_t2", "device_churn_t2_t3", "ip_churn_t1_t2", "ip_churn_t2_t3"
]

X = df[feature_cols].fillna(0)
y = df["is_mule"]

model = XGBClassifier(
    n_estimators=100,
    max_depth=4,
    learning_rate=0.1,
    scale_pos_weight=(len(y) - sum(y)) / max(sum(y), 1),
    random_state=42,
    eval_metric="logloss"
)

# Train on whole dataset for analysis purposes, or we can use KFold predictions
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
df["pred"] = 0
for train_idx, test_idx in skf.split(X, y):
    model.fit(X.iloc[train_idx], y.iloc[train_idx])
    df.loc[test_idx, "pred"] = model.predict(X.iloc[test_idx])

# Analyze by mule_type
mules = df[df["is_mule"] == 1]
res = mules.groupby("mule_type")["pred"].mean().reset_index()
res.rename(columns={"pred": "recall"}, inplace=True)
print("Recall by lifecycle type:")
print(res)

res.to_csv("scratch/v2_lifecycle_results.csv", index=False)
