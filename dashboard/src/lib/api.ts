export type ScoreResult = {
  merchant_id: string;
  scoring_timestamp: string;
  risk_score: number;
  probability: number;
  risk_band: "LOW" | "MEDIUM" | "HIGH";
  behavioral_risk: number | null;
  network_risk: number | null;
  evidence_features: Record<string, number>;
};

export type NetworkScoreResult = {
  merchant_id: string;
  results: ScoreResult[];
};

export type ExplanationFeature = {
  feature_name: string;
  original_value: number;
  shap_value: number;
  direction: "INCREASE" | "DECREASE" | "NEUTRAL";
  rank: number;
  category?: string;
};

export type ExplanationResponse = {
  merchant_id: string;
  scoring_timestamp: string;
  risk_score: number;
  probability: number;
  risk_band: "LOW" | "MEDIUM" | "HIGH";
  threshold: number;
  base_value: number;
  explanations: ExplanationFeature[];
};

export type MerchantMetadata = {
  merchant_id: string;
  merchant_name: string;
  category: string;
  onboarding_date: string;
  kyc_status: string;
};

export type ModelMetadata = {
  version: string;
  threshold: number;
  feature_list: string[];
  training_timestamp: string;
};

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || '/api';

export async function checkHealth() {
  const res = await fetch(`${BASE_URL}/health`);
  if (!res.ok) throw new Error('API unavailable');
  return res.json();
}

export async function getModelMetadata(): Promise<ModelMetadata> {
  const res = await fetch(`${BASE_URL}/model/metadata`);
  if (!res.ok) throw new Error('Failed to fetch model metadata');
  return res.json();
}

export async function getMerchantMetadata(merchantId: string): Promise<MerchantMetadata> {
  const res = await fetch(`${BASE_URL}/v1/merchant/${merchantId}`);
  if (!res.ok) {
    if (res.status === 404) throw new Error('Merchant not found');
    throw new Error('Failed to fetch merchant metadata');
  }
  return res.json();
}

export async function scoreMerchant(merchantId: string, timestamp: string): Promise<ScoreResult> {
  const res = await fetch(`${BASE_URL}/v1/score/merchant`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ merchant_id: merchantId, scoring_timestamp: timestamp })
  });
  if (!res.ok) throw new Error('Failed to score merchant');
  return res.json();
}

export async function getMerchantTimeline(merchantId: string, timestamps: string[]): Promise<ScoreResult[]> {
  const res = await fetch(`${BASE_URL}/v1/score/merchant/timeline`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ merchant_id: merchantId, scoring_timestamps: timestamps })
  });
  if (!res.ok) throw new Error('Failed to fetch timeline');
  return res.json();
}

export async function getNetworkScore(merchantId: string, timestamp: string): Promise<NetworkScoreResult> {
  const res = await fetch(`${BASE_URL}/v1/score/network`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ merchant_id: merchantId, scoring_timestamp: timestamp })
  });
  if (!res.ok) throw new Error('Failed to fetch network score');
  return res.json();
}

export async function explainMerchant(merchantId: string, timestamp: string): Promise<ExplanationResponse> {
  const res = await fetch(`${BASE_URL}/v1/explain/merchant`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ merchant_id: merchantId, scoring_timestamp: timestamp })
  });
  if (!res.ok) throw new Error('Failed to explain merchant');
  return res.json();
}
