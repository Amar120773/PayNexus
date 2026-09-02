"use client";

import { useEffect, useState, use } from "react";
import {
  ScoreResult,
  MerchantMetadata,
  NetworkScoreResult,
  ModelMetadata,
  getMerchantMetadata,
  scoreMerchant,
  getMerchantTimeline,
  getNetworkScore,
  getModelMetadata,
  explainMerchant,
  ExplanationResponse,
  ExplanationFeature,
} from "@/lib/api";
import {
  Shield,
  Activity,
  Share2,
  History,
  ArrowRight,
  Database,
  Server
} from "lucide-react";
import Link from "next/link";
import RiskTimeline from "@/components/RiskTimeline";
import NetworkGraph from "@/components/NetworkGraph";

/* ── Feature Label Map ─────────────────────────────────────────── */
const FEATURE_LABELS: Record<string, string> = {
  volume_delta_t1_t2:    "Volume Change (Early)",
  volume_delta_t2_t3:    "Volume Change (Late)",
  refund_delta_t1_t2:    "Refund Rate Change (Early)",
  refund_delta_t2_t3:    "Refund Rate Change (Late)",
  network_growth_t1_t2:  "Network Growth (Early)",
  network_growth_t2_t3:  "Network Growth (Late)",
  device_churn_t1_t2:    "Device Churn (Early)",
  device_churn_t2_t3:    "Device Churn (Late)",
  ip_churn_t1_t2:        "IP Churn (Early)",
  ip_churn_t2_t3:        "IP Churn (Late)",
  graph_pagerank_score:  "Network Centrality",
  transaction_burst_score: "Transaction Burst",
  shared_settlement_count: "Shared Settlements",
  coordinated_activity_score: "Coordination Score",
  velocity_change_30d:   "30-Day Velocity Change",
  churn_rate:            "Customer Churn Rate",
};

const labelFor = (key: string) =>
  FEATURE_LABELS[key] ?? key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());

/* ── Risk helpers ─────────────────────────────────────────────────────── */
const riskStyle = (band: "HIGH" | "MEDIUM" | "LOW") => ({
  color:  band === "HIGH" ? "var(--risk-high-text)"   : band === "MEDIUM" ? "var(--risk-medium-text)"  : "var(--risk-low-text)",
  bg:     band === "HIGH" ? "var(--risk-high-bg)"     : band === "MEDIUM" ? "var(--risk-medium-bg)"    : "var(--risk-low-bg)",
  border: band === "HIGH" ? "var(--risk-high-border)" : band === "MEDIUM" ? "var(--risk-medium-border)": "var(--risk-low-border)",
  ring:   band === "HIGH" ? "#DC2626"                 : band === "MEDIUM" ? "#F59E0B"                  : "#10B981",
});

/* ── Skeleton loader ──────────────────────────────────────────────────── */
function InvestigationSkeleton() {
  return (
    <div style={{ maxWidth: 1200, margin: "0 auto", padding: "64px 32px" }}>
      <div className="font-data animate-fade-in" style={{ fontSize: 13, color: "var(--text-muted)", marginBottom: 48, letterSpacing: "0.1em" }}>
        BUILDING INTELLIGENCE...
      </div>
      <div className="animate-fade-in" style={{ display: "flex", flexDirection: "column", gap: 24, maxWidth: 320 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <span className="font-ui" style={{ fontSize: 14, color: "var(--text-secondary)", fontWeight: 500 }}>Merchant profile</span>
          <span className="font-data" style={{ color: "var(--border-strong)", fontSize: 12 }}>████████░░</span>
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <span className="font-ui" style={{ fontSize: 14, color: "var(--text-secondary)", fontWeight: 500 }}>Risk assessment</span>
          <span className="font-data" style={{ color: "var(--border-strong)", fontSize: 12 }}>██████░░░░</span>
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <span className="font-ui" style={{ fontSize: 14, color: "var(--text-secondary)", fontWeight: 500 }}>Evidence mapping</span>
          <span className="font-data" style={{ color: "var(--border-strong)", fontSize: 12 }}>████░░░░░░</span>
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <span className="font-ui" style={{ fontSize: 14, color: "var(--text-secondary)", fontWeight: 500 }}>Network context</span>
          <span className="font-data" style={{ color: "var(--border-strong)", fontSize: 12 }}>██░░░░░░░░</span>
        </div>
      </div>
    </div>
  );
}

/* ── Error state ──────────────────────────────────────────────────────── */
function InvestigationError({ error }: { error: string }) {
  return (
    <div style={{ maxWidth: 800, margin: "100px auto", padding: "0 32px" }}>
      <div style={{ borderLeft: "4px solid var(--danger)", paddingLeft: 24 }}>
        <h2 className="font-poppins-main" style={{ fontSize: 32, color: "var(--text-primary)", marginBottom: 16 }}>
          RISK INTELLIGENCE UNAVAILABLE
        </h2>
        <p className="font-ui" style={{ fontSize: 16, color: "var(--text-secondary)", marginBottom: 32, maxWidth: 500 }}>
          Unable to retrieve merchant intelligence. {error}
        </p>
        <button
          className="btn btn-primary font-data"
          style={{ padding: "12px 24px", fontSize: 13, letterSpacing: "0.05em" }}
          onClick={() => window.location.reload()}
        >
          RETRY INVESTIGATION
        </button>
      </div>
    </div>
  );
}

/* ── Smart Feature Row (Phase 5 + SHAP) ────────────────────────────────────────── */
function SmartFeatureRow({ 
  feature, 
  original_value, 
  shap_value,
  direction,
  category,
  rank
}: { 
  feature: string; 
  original_value: number; 
  shap_value?: number;
  direction?: string;
  category: string;
  rank?: number;
}) {
  const isZero = Math.abs(original_value) < 0.0001; // Handle floating point 0
  
  // Format logically based on feature type
  let displayValue = original_value.toFixed(4);
  let isPercentage = false;
  if (feature.includes("delta") || feature.includes("growth") || feature.includes("rate") || feature.includes("change") || feature.includes("churn")) {
    displayValue = `${original_value > 0 ? "+" : ""}${(original_value * 100).toFixed(1)}%`;
    isPercentage = true;
  } else if (feature.includes("count")) {
    displayValue = original_value.toFixed(0);
  } else {
    displayValue = original_value > 0 ? `+${original_value.toFixed(4)}` : original_value.toFixed(4);
  }

  const isIncrease = shap_value ? direction === "INCREASE" : original_value > 0;
  const hasShap = shap_value !== undefined;

  return (
    <div 
      style={{ 
        display: "flex", 
        flexDirection: "column", 
        gap: 12, 
        padding: "16px 20px", 
        border: "1px solid var(--border-subtle)", 
        borderRadius: "var(--radius-md)",
        background: isZero && !hasShap ? "transparent" : "var(--bg-surface)",
        opacity: isZero && !hasShap ? 0.6 : 1,
        transition: "all var(--duration-fast) var(--ease)"
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 16 }}>
        <div style={{ minWidth: 0, flex: 1 }}>
          <div className="font-ui" style={{ display: "flex", alignItems: "flex-start", gap: 8, fontSize: 14, fontWeight: 600, color: (isZero && !hasShap) ? "var(--text-secondary)" : "var(--text-primary)", marginBottom: 4 }}>
            {rank !== undefined && <span style={{ fontSize: 11, color: "var(--text-muted)", background: "var(--bg-elevated)", padding: "2px 6px", borderRadius: 4, flexShrink: 0, marginTop: 2 }}>#{rank}</span>}
            <span style={{ wordBreak: "break-word" }}>{labelFor(feature)}</span>
          </div>
          <div className="font-data" style={{ fontSize: 10, letterSpacing: "0.1em", color: "var(--text-muted)", textTransform: "uppercase" }}>
            {category}
          </div>
        </div>
        
        {/* Right Side Metrics */}
        <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 8, flexShrink: 0, minWidth: 120 }}>
          {isZero && !hasShap ? (
            <span className="font-data" style={{ fontSize: 14, fontWeight: 500, color: "var(--text-disabled)" }}>0</span>
          ) : (
            <>
              <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 2 }}>
                <span className="font-ui" style={{ fontSize: 9, fontWeight: 600, color: "var(--text-muted)", letterSpacing: "0.05em", textTransform: "uppercase" }}>Observed Value</span>
                <span className="font-data" style={{ fontSize: 14, fontWeight: 600, color: "var(--text-primary)", whiteSpace: "nowrap" }}>
                  {displayValue}
                </span>
              </div>
              
              {hasShap ? (
                <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 2 }}>
                  <span className="font-ui" style={{ fontSize: 9, fontWeight: 600, color: "var(--text-muted)", letterSpacing: "0.05em", textTransform: "uppercase" }}>Model Contribution</span>
                  <span className="font-data" style={{ fontSize: 14, fontWeight: 700, color: isIncrease ? "var(--risk-high-text)" : (direction === "DECREASE" ? "var(--risk-low-text)" : "var(--text-muted)"), whiteSpace: "nowrap" }}>
                    {shap_value > 0 ? "+" : ""}{shap_value.toFixed(4)}
                  </span>
                  <span className="font-data" style={{ fontSize: 10, fontWeight: 700, color: isIncrease ? "var(--risk-high-text)" : (direction === "DECREASE" ? "var(--risk-low-text)" : "var(--text-muted)"), letterSpacing: "0.05em", marginTop: 2 }}>
                    {isIncrease ? "↑ INCREASES RISK" : "↓ REDUCES RISK"}
                  </span>
                </div>
              ) : (
                <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 2 }}>
                  <span className="font-data" style={{ fontSize: 10, fontWeight: 700, color: isIncrease ? "var(--risk-high-text)" : "var(--risk-low-text)", letterSpacing: "0.05em", whiteSpace: "nowrap" }}>
                    {isIncrease ? "↑ INCREASES RISK" : "↓ REDUCES RISK"}
                  </span>
                </div>
              )}
            </>
          )}
        </div>
      </div>
      {/* Only show magnitude bar if we have SHAP values, visualizing impact */}
      {hasShap && direction !== "NEUTRAL" && (
        <div style={{ marginTop: 8 }}>
          <div className="font-ui" style={{ fontSize: 9, fontWeight: 600, color: "var(--text-muted)", letterSpacing: "0.05em", textTransform: "uppercase", marginBottom: 4 }}>
            Relative Impact
          </div>
          <div className="magnitude-bar">
            <div
              className="magnitude-bar-fill"
              style={{
                width: `${Math.min(100, Math.abs(shap_value) * 50)}%`, // Scale SHAP for visual impact
                background: isIncrease ? "var(--risk-high)" : "var(--risk-low)"
              }}
            />
          </div>
        </div>
      )}
    </div>
  );
}

/* ── Raw Feature Row (Phase 10.2: Purely Observational) ────────────────────── */
function RawFeatureRow({ 
  feature, 
  original_value, 
  category 
}: { 
  feature: string; 
  original_value: number; 
  category: string; 
}) {
  const isZero = Math.abs(original_value) < 0.0001;
  
  let displayValue = original_value.toFixed(4);
  if (feature.includes("delta") || feature.includes("growth") || feature.includes("rate") || feature.includes("change") || feature.includes("churn")) {
    displayValue = `${original_value > 0 ? "+" : ""}${(original_value * 100).toFixed(1)}%`;
  } else if (feature.includes("count")) {
    displayValue = original_value.toFixed(0);
  } else {
    displayValue = original_value > 0 ? `+${original_value.toFixed(4)}` : original_value.toFixed(4);
  }

  return (
    <div 
      style={{ 
        display: "flex", 
        flexDirection: "column", 
        gap: 12, 
        padding: "16px 20px", 
        border: "1px solid var(--border-subtle)", 
        borderRadius: "var(--radius-md)",
        background: isZero ? "transparent" : "var(--bg-surface)",
        opacity: isZero ? 0.6 : 1,
        transition: "all var(--duration-fast) var(--ease)"
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 16 }}>
        <div style={{ minWidth: 0, flex: 1 }}>
          <div className="font-ui" style={{ display: "flex", alignItems: "flex-start", gap: 8, fontSize: 14, fontWeight: 600, color: isZero ? "var(--text-secondary)" : "var(--text-primary)", marginBottom: 4 }}>
            <span style={{ wordBreak: "break-word" }}>{labelFor(feature)}</span>
          </div>
          <div className="font-data" style={{ fontSize: 10, letterSpacing: "0.1em", color: "var(--text-muted)", textTransform: "uppercase" }}>
            {category}
          </div>
        </div>
        
        <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 2, flexShrink: 0 }}>
          <span className="font-ui" style={{ fontSize: 9, fontWeight: 600, color: "var(--text-muted)", letterSpacing: "0.05em", textTransform: "uppercase" }}>Observed Value</span>
          {isZero ? (
            <span className="font-data" style={{ fontSize: 14, fontWeight: 500, color: "var(--text-disabled)" }}>0</span>
          ) : (
            <span className="font-data" style={{ fontSize: 14, fontWeight: 600, color: "var(--text-primary)", whiteSpace: "nowrap" }}>
              {displayValue}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════
   MAIN PAGE
   ═══════════════════════════════════════════════════════════════════════ */

export default function MerchantInvestigationPage({
  params,
}: {
  params: Promise<{ merchantId: string }>;
}) {
  const unwrappedParams = use(params);
  const merchantId = unwrappedParams.merchantId;

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [metadata, setMetadata] = useState<MerchantMetadata | null>(null);
  const [currentScore, setCurrentScore] = useState<ScoreResult | null>(null);
  const [timeline, setTimeline] = useState<ScoreResult[]>([]);
  const [network, setNetwork] = useState<NetworkScoreResult | null>(null);
  const [explanation, setExplanation] = useState<ExplanationResponse | null>(null);
  const [modelMeta, setModelMeta] = useState<ModelMetadata | null>(null);
  const [activeTab, setActiveTab] = useState<"overview" | "evidence" | "timeline" | "network">("overview");
  const [evidenceFilter, setEvidenceFilter] = useState<"ALL" | "BEHAVIORAL" | "TEMPORAL" | "NETWORK">("ALL");

  const [selectedTimestamp, setSelectedTimestamp] = useState<string>("2026-03-31 00:00:00");
  const [isRefetchingTime, setIsRefetchingTime] = useState(false);

  /* Initial Load */
  useEffect(() => {
    async function loadInitial() {
      try {
        setLoading(true);
        const [mMeta, modelM] = await Promise.all([
          getMerchantMetadata(merchantId),
          getModelMetadata(),
        ]);
        setMetadata(mMeta);
        setModelMeta(modelM);
      } catch (err: any) {
        setError(err.message || "An unexpected error occurred.");
      } finally {
        setLoading(false);
      }
    }
    loadInitial();
    
    // Fetch timeline independently in the background so it doesn't block
    async function fetchTimeline() {
      try {
        const timelineTimestamps = [
          "2026-01-31 00:00:00",
          "2026-02-15 00:00:00",
          "2026-02-28 00:00:00",
          "2026-03-15 00:00:00",
          "2026-03-31 00:00:00",
        ];
        const mTimeline = await getMerchantTimeline(merchantId, timelineTimestamps);
        setTimeline(mTimeline);
      } catch (err) {
        console.error("Timeline failed to load", err);
      }
    }
    fetchTimeline();
  }, [merchantId]);

  /* Point-in-Time */
  useEffect(() => {
    async function fetchPointInTime() {
      if (!metadata) return;
      try {
        setIsRefetchingTime(true);
        const [mScore, mNetwork, mExplain] = await Promise.all([
          scoreMerchant(merchantId, selectedTimestamp),
          getNetworkScore(merchantId, selectedTimestamp),
          explainMerchant(merchantId, selectedTimestamp).catch(e => null),
        ]);
        setCurrentScore(mScore);
        setNetwork(mNetwork);
        setExplanation(mExplain);
      } catch (err: any) {
        console.error(err);
        setError(err.message || "Failed to load point-in-time score.");
      } finally {
        setIsRefetchingTime(false);
      }
    }
    fetchPointInTime();
  }, [merchantId, selectedTimestamp, metadata]);

  /* ── Loading ── */
  if (loading || (!metadata && !error) || (!currentScore && !error)) return <InvestigationSkeleton />;

  /* ── Error ── */
  if (error || !metadata || !currentScore) {
    return <InvestigationError error={error || "Failed to load merchant data."} />;
  }

  const evidenceCategories = {
    behavioral: [] as { feature: string; original_value: number; shap_value?: number; direction?: string; rank?: number }[],
    network: [] as { feature: string; original_value: number; shap_value?: number; direction?: string; rank?: number }[],
    temporal: [] as { feature: string; original_value: number; shap_value?: number; direction?: string; rank?: number }[],
  };
  
  const explMap = new Map<string, ExplanationFeature>();
  if (explanation?.explanations) {
    explanation.explanations.forEach(e => explMap.set(e.feature_name, e));
  }

  Object.entries(currentScore.evidence_features).forEach(([key, val]) => {
    const expl = explMap.get(key);
    const item = {
      feature: key,
      original_value: val,
      shap_value: expl?.shap_value,
      direction: expl?.direction,
      rank: expl?.rank,
    };
    if (key.startsWith("graph_") || key.includes("hop")) {
      evidenceCategories.network.push(item);
    } else if (
      key.includes("velocity") || key.includes("churn") || key.includes("time") ||
      key.includes("delta") || key.includes("growth")
    ) {
      evidenceCategories.temporal.push(item);
    } else {
      evidenceCategories.behavioral.push(item);
    }
  });

  const band = currentScore.risk_band;
  const rs = riskStyle(band);

  const TABS = [
    { id: "overview",  label: "Overview",             icon: Shield },
    { id: "evidence",  label: "Evidence",             icon: Activity },
    { id: "timeline",  label: "Timeline",             icon: History },
    { id: "network",   label: "Network",              icon: Share2 },
  ] as const;

  return (
    <div style={{ maxWidth: 1200, margin: "0 auto", padding: "40px 32px 120px" }} className="animate-fade-in">

      {/* ── METADATA STRIP ── */}
      <div style={{ display: "flex", justifyContent: "flex-end", gap: 24, marginBottom: 32 }}>
        <div style={{ display: "flex", gap: 6, alignItems: "center", color: "var(--text-muted)" }}>
          <Server size={12} />
          <span className="font-data" style={{ fontSize: 10, letterSpacing: "0.1em" }}>API ONLINE</span>
        </div>
        <div style={{ display: "flex", gap: 6, alignItems: "center", color: "var(--text-muted)" }}>
          <Shield size={12} />
          <span className="font-data" style={{ fontSize: 10, letterSpacing: "0.1em" }}>MODEL V2</span>
        </div>
        <div style={{ display: "flex", gap: 6, alignItems: "center", color: "var(--text-muted)" }}>
          <Database size={12} />
          <span className="font-data" style={{ fontSize: 10, letterSpacing: "0.1em" }}>FEATURES: 54 SIGNALS</span>
        </div>
      </div>

      {/* ── HEADER / IDENTITY ── */}
      <div style={{ marginBottom: 48, borderLeft: `4px solid ${rs.ring}`, paddingLeft: 24 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 12 }}>
          <Link href="/" className="font-data" style={{ fontSize: 11, color: "var(--text-muted)", textDecoration: "none", letterSpacing: "0.1em", display: "flex", alignItems: "center", gap: 4 }}>
            ← INVESTIGATION HUB
          </Link>
          <span className="font-data" style={{ fontSize: 11, color: "var(--text-muted)", letterSpacing: "0.1em" }}>/</span>
          <span className="font-data" style={{ fontSize: 11, color: "var(--text-muted)", letterSpacing: "0.1em", textTransform: "uppercase" }}>MERCHANT</span>
          <span className="font-data" style={{ fontSize: 13, color: "var(--text-primary)", fontWeight: 700, padding: "2px 8px", background: "var(--bg-elevated)", border: "1px solid var(--border-default)", borderRadius: "var(--radius-sm)" }}>{merchantId}</span>
        </div>
        
        <h1 className="font-poppins-main" style={{ fontSize: "clamp(40px, 6vw, 64px)", color: "var(--text-primary)", margin: "0 0 24px", lineHeight: 1.1 }}>
          {metadata.merchant_name || merchantId}
        </h1>
        
        <div style={{ display: "flex", flexWrap: "wrap", gap: 32, fontSize: 13, color: "var(--text-muted)" }}>
          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            <span className="font-data" style={{ fontSize: 10, letterSpacing: "0.1em", textTransform: "uppercase" }}>CATEGORY</span>
            <span className="font-ui" style={{ fontWeight: 600, color: "var(--text-secondary)" }}>{metadata.category || "—"}</span>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            <span className="font-data" style={{ fontSize: 10, letterSpacing: "0.1em", textTransform: "uppercase" }}>KYC STATUS</span>
            <span className="font-ui" style={{ fontWeight: 600, color: "var(--text-secondary)" }}>{metadata.kyc_status || "—"}</span>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            <span className="font-data" style={{ fontSize: 10, letterSpacing: "0.1em", textTransform: "uppercase" }}>ONBOARDED</span>
            <span className="font-ui" style={{ fontWeight: 600, color: "var(--text-secondary)" }}>{metadata.onboarding_date || "—"}</span>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            <span className="font-data" style={{ fontSize: 10, letterSpacing: "0.1em", textTransform: "uppercase" }}>ANALYSIS TIMESTAMP</span>
            <span className="font-data" style={{ fontWeight: 700, color: "var(--brand)" }}>{currentScore.scoring_timestamp}</span>
          </div>
        </div>
      </div>

      <hr className="divider" style={{ marginBottom: 48 }} />

      {/* ── TABS WORKSPACE ── */}
      <div
        role="tablist"
        aria-label="Investigation sections"
        style={{
          display: "flex",
          gap: 12,
          marginBottom: 48,
          borderBottom: "1px solid var(--border-default)",
          overflowX: "auto"
        }}
      >
        {TABS.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            role="tab"
            aria-selected={activeTab === id}
            onClick={() => setActiveTab(id)}
            className="btn"
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              padding: "12px 16px",
              background: "transparent",
              border: "none",
              borderBottom: activeTab === id ? "2px solid var(--brand)" : "2px solid transparent",
              fontSize: 14,
              fontWeight: activeTab === id ? 700 : 500,
              color: activeTab === id ? "var(--text-primary)" : "var(--text-muted)",
              cursor: "pointer",
              whiteSpace: "nowrap",
            }}
          >
            <Icon size={14} />
            {label}
          </button>
        ))}
      </div>

      {/* ── TAB CONTENT ── */}
      <div style={{ opacity: isRefetchingTime ? 0.6 : 1, transition: "opacity 0.2s ease", pointerEvents: isRefetchingTime ? "none" : undefined }}>

        {/* ── OVERVIEW TAB ── */}
        {activeTab === "overview" && (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(400px, 1fr))", gap: 48, alignItems: "start" }}>
            
            {/* Risk Anchor */}
            <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
              <div className="font-data" style={{ fontSize: 11, color: "var(--text-muted)", letterSpacing: "0.1em" }}>
                CURRENT STATE
              </div>
              
              <div style={{ display: "flex", alignItems: "baseline", gap: 20, flexWrap: "wrap" }}>
                <div className="font-data" style={{ fontSize: "clamp(64px, 8vw, 96px)", fontWeight: 800, color: rs.color, lineHeight: 1, letterSpacing: "-0.04em" }}>
                  {currentScore.risk_score.toFixed(4)}
                </div>
                <div className={`risk-badge ${band.toLowerCase()}`} style={{ fontSize: 14, padding: "6px 16px" }}>
                  {band} RISK
                </div>
              </div>
              
              <p className="font-ui" style={{ fontSize: 16, color: "var(--text-secondary)", margin: 0, lineHeight: 1.6, maxWidth: 400 }}>
                {band === "HIGH" 
                  ? "Elevated merchant risk detected based on aggressive network sharing and anomalous behavioral volume." 
                  : band === "MEDIUM" 
                  ? "Moderate behavioral anomalies detected. Network infrastructure review recommended." 
                  : "Standard merchant behavior observed within low-risk model thresholds."}
              </p>

              <div style={{ marginTop: 24, padding: "20px", background: "var(--bg-subtle)", borderRadius: "var(--radius-sm)", border: "1px solid var(--border-default)" }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 12 }}>
                  <span className="font-data" style={{ fontSize: 11, color: "var(--text-muted)", letterSpacing: "0.1em" }}>MODEL PROBABILITY</span>
                  <span className="font-data" style={{ fontSize: 14, fontWeight: 700, color: "var(--text-primary)" }}>{currentScore.probability.toFixed(4)}</span>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 12 }}>
                  <span className="font-data" style={{ fontSize: 11, color: "var(--text-muted)", letterSpacing: "0.1em" }}>BEHAVIORAL RISK</span>
                  <span className="font-data" style={{ fontSize: 14, fontWeight: 700, color: "var(--text-primary)" }}>{currentScore.behavioral_risk != null ? currentScore.behavioral_risk.toFixed(4) : "—"}</span>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <span className="font-data" style={{ fontSize: 11, color: "var(--text-muted)", letterSpacing: "0.1em" }}>NETWORK RISK</span>
                  <span className="font-data" style={{ fontSize: 14, fontWeight: 700, color: "var(--text-primary)" }}>{currentScore.network_risk != null ? currentScore.network_risk.toFixed(4) : "—"}</span>
                </div>
              </div>
            </div>

            {/* Why this merchant? */}
            <div style={{ padding: 32, border: "1px solid var(--border-default)", borderRadius: "var(--radius-md)", background: "transparent" }}>
              <div className="font-data" style={{ fontSize: 11, color: "var(--text-muted)", letterSpacing: "0.1em", marginBottom: 24 }}>
                EVIDENCE
              </div>
              <h2 className="font-poppins-sub" style={{ fontSize: 24, color: "var(--text-primary)", marginBottom: 32 }}>
                Why this merchant?
              </h2>
              
              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                {(() => {
                  if (explanation?.explanations) {
                    return explanation.explanations.slice(0, 4).map(e => (
                      <SmartFeatureRow 
                        key={e.feature_name} 
                        feature={e.feature_name} 
                        original_value={e.original_value} 
                        shap_value={e.shap_value}
                        direction={e.direction}
                        rank={e.rank}
                        category="TOP SIGNAL" 
                      />
                    ));
                  }
                  return Object.entries(currentScore.evidence_features)
                    .sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]))
                    .slice(0, 4)
                    .map(([key, val]) => (
                      <SmartFeatureRow key={key} feature={key} original_value={val} category="TOP SIGNAL" />
                    ));
                })()}
              </div>
              
              <button 
                className="btn btn-secondary font-data"
                onClick={() => setActiveTab("evidence")}
                style={{ width: "100%", marginTop: 32 }}
              >
                VIEW FULL EVIDENCE LOG <ArrowRight size={14} />
              </button>
            </div>

          </div>
        )}
        {/* ── EVIDENCE TAB (Phase 5 Redesign) ── */}
        {activeTab === "evidence" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 64 }}>
            
            {/* WHY THIS MERCHANT? */}
            <div>
              <div className="font-data" style={{ fontSize: 11, color: "var(--text-muted)", letterSpacing: "0.1em", marginBottom: 12 }}>
                MODEL EXPLANATION
              </div>
              <h2 className="font-poppins-sub" style={{ fontSize: 32, color: "var(--text-primary)", marginBottom: 8 }}>
                Why this merchant?
              </h2>
              <p className="font-ui" style={{ fontSize: 15, color: "var(--text-secondary)", marginBottom: 24, maxWidth: 800 }}>
                SHAP explains which features influenced this merchant's risk prediction. Positive contributions push risk higher; negative contributions push risk lower. The magnitude shows relative influence, not probability.
              </p>

              <div style={{ display: "flex", gap: 32, padding: 16, background: "var(--bg-surface)", border: "1px solid var(--border-default)", borderRadius: "var(--radius-md)", marginBottom: 32, flexWrap: "wrap" }}>
                <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                  <span className="font-data" style={{ fontSize: 11, fontWeight: 700, color: "var(--risk-high-text)", letterSpacing: "0.05em" }}>↑ INCREASES RISK</span>
                  <span className="font-ui" style={{ fontSize: 13, color: "var(--text-secondary)" }}>Feature pushed the model toward higher risk.</span>
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                  <span className="font-data" style={{ fontSize: 11, fontWeight: 700, color: "var(--risk-low-text)", letterSpacing: "0.05em" }}>↓ REDUCES RISK</span>
                  <span className="font-ui" style={{ fontSize: 13, color: "var(--text-secondary)" }}>Feature pushed the model toward lower risk.</span>
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: 4, paddingLeft: 16, borderLeft: "1px solid var(--border-subtle)" }}>
                  <span className="font-ui" style={{ fontSize: 13, color: "var(--text-secondary)", marginTop: 18 }}>Contribution is shown in model units, not percentage points.</span>
                </div>
              </div>
              
              {(() => {
                if (explanation?.explanations) {
                  // Filter out zero-impact SHAP values
                  const epsilon = 0.0001;
                  const meaningfulExpls = explanation.explanations.filter(e => Math.abs(e.shap_value) > epsilon);
                  
                  // Sort by absolute magnitude descending
                  const sortedExpls = [...meaningfulExpls].sort((a, b) => Math.abs(b.shap_value) - Math.abs(a.shap_value));
                  
                  const increasingFactors = sortedExpls.filter(e => e.shap_value > 0);
                  const reducingFactors = sortedExpls.filter(e => e.shap_value < 0);
                  
                  // Track ranks overall
                  const getRank = (fname: string) => {
                    const r = sortedExpls.findIndex(x => x.feature_name === fname);
                    return r !== -1 ? r + 1 : undefined;
                  };

                  const renderBlock = (expls: ExplanationFeature[]) => (
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: 24 }}>
                      {expls.map(e => {
                        let cat = "BEHAVIORAL";
                        if (e.feature_name.startsWith("graph_") || e.feature_name.includes("hop")) cat = "NETWORK";
                        else if (e.feature_name.includes("velocity") || e.feature_name.includes("time") || e.feature_name.includes("delta") || e.feature_name.includes("growth")) cat = "TEMPORAL";
                        
                        return (
                          <div key={e.feature_name} style={{ border: "1px solid var(--border-default)", borderRadius: "var(--radius-lg)", overflow: "hidden" }}>
                            <SmartFeatureRow 
                              feature={e.feature_name} 
                              original_value={e.original_value} 
                              shap_value={e.shap_value}
                              direction={e.direction}
                              rank={getRank(e.feature_name)}
                              category={cat} 
                            />
                          </div>
                        );
                      })}
                    </div>
                  );

                  return (
                    <div style={{ display: "flex", flexDirection: "column", gap: 48 }}>
                      {increasingFactors.length > 0 && (
                        <div>
                          <div style={{ marginBottom: 16 }}>
                            <h3 className="font-poppins-sub" style={{ fontSize: 18, color: "var(--text-primary)", marginBottom: 4 }}>RISK-INCREASING FACTORS</h3>
                            <p className="font-ui" style={{ fontSize: 14, color: "var(--text-secondary)", margin: 0 }}>Features that pushed the model toward a higher-risk prediction.</p>
                          </div>
                          {renderBlock(increasingFactors)}
                        </div>
                      )}
                      
                      {reducingFactors.length > 0 && (
                        <div>
                          <div style={{ marginBottom: 16 }}>
                            <h3 className="font-poppins-sub" style={{ fontSize: 18, color: "var(--text-primary)", marginBottom: 4 }}>RISK-REDUCING FACTORS</h3>
                            <p className="font-ui" style={{ fontSize: 14, color: "var(--text-secondary)", margin: 0 }}>Features that pushed the model toward a lower-risk prediction.</p>
                          </div>
                          {renderBlock(reducingFactors)}
                        </div>
                      )}
                    </div>
                  );
                }
                
                // Fallback if no SHAP
                return (
                  <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: 24 }}>
                    {Object.entries(currentScore.evidence_features)
                      .sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]))
                      .slice(0, 3)
                      .map(([key, val]) => {
                        let cat = "BEHAVIORAL";
                        if (key.startsWith("graph_") || key.includes("hop")) cat = "NETWORK";
                        else if (key.includes("velocity") || key.includes("time") || key.includes("delta") || key.includes("growth")) cat = "TEMPORAL";
                        
                        return (
                          <div key={key} style={{ padding: 24, border: "1px solid var(--border-default)", borderRadius: "var(--radius-lg)" }}>
                            <div className="font-data" style={{ fontSize: 10, letterSpacing: "0.1em", color: "var(--brand)", marginBottom: 16 }}>
                              PRIMARY DRIVER
                            </div>
                            <SmartFeatureRow feature={key} original_value={val} category={cat} />
                          </div>
                        );
                      })}
                  </div>
                );
              })()}
            </div>

            {/* FULL EVIDENCE LOG WITH FILTERS */}
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", borderBottom: "1px solid var(--border-default)", paddingBottom: 24, marginBottom: 32, flexWrap: "wrap", gap: 24 }}>
                <div>
                  <h2 className="font-poppins-sub" style={{ fontSize: 24, color: "var(--text-primary)", margin: "0 0 8px" }}>
                    Observed Model Features
                  </h2>
                  <p className="font-ui" style={{ fontSize: 14, color: "var(--text-muted)", margin: "0 0 16px" }}>
                    Point-in-time signals evaluated at <code style={{ fontFamily: "ui-monospace, monospace", color: "var(--text-secondary)" }}>{currentScore.scoring_timestamp}</code>.
                  </p>
                  <p className="font-ui" style={{ fontSize: 13, color: "var(--text-secondary)", margin: 0, padding: "8px 12px", background: "var(--bg-surface)", borderLeft: "2px solid var(--border-strong)", borderRadius: "var(--radius-sm)" }}>
                    Observed features show what the model measured. Model explanation shows how those measurements influenced the risk prediction.
                  </p>
                </div>
                
                {/* Filters */}
                <div style={{ display: "flex", gap: 8, background: "var(--bg-subtle)", padding: 6, borderRadius: "var(--radius-md)", border: "1px solid var(--border-subtle)" }}>
                  {(["ALL", "BEHAVIORAL", "TEMPORAL", "NETWORK"] as const).map((filter) => (
                    <button
                      key={filter}
                      onClick={() => setEvidenceFilter(filter)}
                      className="font-data btn"
                      style={{
                        padding: "6px 12px",
                        fontSize: 11,
                        letterSpacing: "0.05em",
                        background: evidenceFilter === filter ? "var(--bg-surface)" : "transparent",
                        color: evidenceFilter === filter ? "var(--text-primary)" : "var(--text-muted)",
                        border: evidenceFilter === filter ? "1px solid var(--border-strong)" : "1px solid transparent",
                        borderRadius: "var(--radius-sm)",
                        fontWeight: evidenceFilter === filter ? 700 : 500,
                        boxShadow: evidenceFilter === filter ? "var(--shadow-sm)" : "none",
                        cursor: "pointer"
                      }}
                    >
                      {filter}
                    </button>
                  ))}
                </div>
              </div>

              {/* Grid of features */}
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: 20 }}>
                {(() => {
                  let visibleFeatures: { feature: string; original_value: number; category: string }[] = [];
                  if (evidenceFilter === "ALL" || evidenceFilter === "TEMPORAL") {
                    visibleFeatures = visibleFeatures.concat(evidenceCategories.temporal.map(f => ({ feature: f.feature, original_value: f.original_value, category: "TEMPORAL" })));
                  }
                  if (evidenceFilter === "ALL" || evidenceFilter === "BEHAVIORAL") {
                    visibleFeatures = visibleFeatures.concat(evidenceCategories.behavioral.map(f => ({ feature: f.feature, original_value: f.original_value, category: "BEHAVIORAL" })));
                  }
                  if (evidenceFilter === "ALL" || evidenceFilter === "NETWORK") {
                    visibleFeatures = visibleFeatures.concat(evidenceCategories.network.map(f => ({ feature: f.feature, original_value: f.original_value, category: "NETWORK" })));
                  }
                  
                  // Sort by absolute magnitude of the observed value for factual presentation
                  visibleFeatures.sort((a, b) => Math.abs(b.original_value) - Math.abs(a.original_value));

                  return visibleFeatures.length > 0 ? (
                    visibleFeatures.map(f => (
                      <RawFeatureRow 
                        key={f.feature} 
                        feature={f.feature} 
                        original_value={f.original_value} 
                        category={f.category} 
                      />
                    ))
                  ) : (
                    <div className="font-ui" style={{ gridColumn: "1 / -1", padding: 48, textAlign: "center", color: "var(--text-disabled)", fontStyle: "italic", border: "1px dashed var(--border-default)", borderRadius: "var(--radius-lg)" }}>
                      No signals available in this category.
                    </div>
                  );
                })()}
              </div>
              
              <div style={{ marginTop: 48, paddingTop: 32, borderTop: "1px solid var(--border-default)", display: "flex", justifyContent: "flex-end" }}>
                <button
                  className="btn btn-primary font-data"
                  onClick={() => setActiveTab("timeline")}
                  style={{ display: "flex", alignItems: "center", gap: 8, padding: "12px 24px", fontSize: 13 }}
                >
                  EXPLORE RISK EVOLUTION <ArrowRight size={14} />
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ── TIMELINE TAB (Phase 6 Redesign) ── */}
        {activeTab === "timeline" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 48 }}>
            <RiskTimeline
              timeline={timeline}
              threshold={modelMeta?.threshold || 0.3263}
              selectedTimestamp={selectedTimestamp}
              onPointClick={(pt) => setSelectedTimestamp(pt.scoring_timestamp)}
              onNavigateToEvidence={() => setActiveTab("evidence")}
            />
            
            <div style={{ paddingTop: 32, borderTop: "1px solid var(--border-default)", display: "flex", justifyContent: "flex-end" }}>
              <button
                className="btn btn-primary font-data"
                onClick={() => setActiveTab("network")}
                style={{ display: "flex", alignItems: "center", gap: 8, padding: "12px 24px", fontSize: 13 }}
              >
                EXPLORE NETWORK <ArrowRight size={14} />
              </button>
            </div>
          </div>
        )}

        {/* ── NETWORK TAB (Phase 7 Redesign) ── */}
        {activeTab === "network" && (
          <NetworkGraph
            centralMerchantId={merchantId}
            centralNodeData={currentScore}
            networkData={network}
            selectedTimestamp={selectedTimestamp}
            loading={loading}
          />
        )}
      </div>
    </div>
  );
}
