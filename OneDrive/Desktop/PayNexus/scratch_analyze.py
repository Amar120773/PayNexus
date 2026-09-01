import pandas as pd

try:
    df = pd.read_csv('data/synthetic_v2/evolution_features.csv')
    print('Shape:', df.shape)
    print('Merchants:', df['merchant_id'].nunique())
    
    # Just grab all columns that look like temporal signals based on the user's list
    # e.g., 'refund_rate_change_late', 'network_growth_early', 'device_churn_early', etc.
    temporal_cols = [c for c in df.columns if 'delta' in c or 'velocity' in c or 'churn' in c or 'growth' in c or 'change' in c]
    print('Temporal Columns:', temporal_cols)
    
    for c in temporal_cols:
        zeros = (df[c] == 0.0).sum()
        pct = zeros / len(df) * 100
        print(f'{c} - Zeros: {zeros} ({pct:.2f}%) - Min: {df[c].min()} - Max: {df[c].max()} - Mean: {df[c].mean():.6f} - Unique: {df[c].nunique()}')
except Exception as e:
    print('Error:', e)
