import pandas as pd
df = pd.read_csv('data/synthetic_v2/evolution_features.csv')
for m in ['M00109', 'M00150', 'M00001']:
    print(f'--- {m} ---')
    print(df[df['merchant_id'] == m][['volume_delta_t2_t3', 'device_churn_t2_t3', 'network_growth_t2_t3']].to_dict(orient='records'))
