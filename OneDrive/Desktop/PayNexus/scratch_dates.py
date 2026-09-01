import pandas as pd
tx = pd.read_csv('data/synthetic_v2/transactions.csv')
print('Min tx time:', tx['timestamp'].min())
print('Max tx time:', tx['timestamp'].max())

rels = pd.read_csv('data/synthetic_v2/relationships.csv')
print('Min rel start_time:', rels['start_time'].min())
print('Max rel start_time:', rels['start_time'].max())
print('Max rel end_time:', rels['end_time'].max())
