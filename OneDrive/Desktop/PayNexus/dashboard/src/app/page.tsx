"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Search, ArrowRight, CornerDownLeft, Activity, ShieldCheck, Database, Server } from "lucide-react";
import { FlickeringGrid } from "@/components/FlickeringGrid";

const DEMO_MERCHANTS = [
  {
    id: "M00109",
    label: "High-risk network",
    description: "Dense infrastructure sharing, high transaction velocity, behavioral coordination signals.",
    band: "HIGH" as const,
  },
  {
    id: "M00150",
    label: "Temporal evolution",
    description: "Transitions from LOW to HIGH risk mid-dataset. Best demonstrates point-in-time analysis.",
    band: "MEDIUM" as const,
  },
  {
    id: "M00001",
    label: "Low-risk baseline",
    description: "High transaction volume but standard, uncoordinated network relationships.",
    band: "LOW" as const,
  },
  {
    id: "M00492",
    label: "Type-D blind spot",
    description: "Slow-burn behavioral transition — demonstrates model limitations and override value.",
    band: "LOW" as const,
  },
];

export default function HomePage() {
  const router = useRouter();
  const [searchId, setSearchId] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchId.trim()) return;
    setLoading(true);
    router.push(`/merchant/${searchId.trim()}`);
  };

  const handleDemoClick = (id: string) => {
    router.push(`/merchant/${id}`);
  };

  return (
    <>
      {/* ── BACKGROUND MOTIF ── */}
      <div 
        aria-hidden="true" 
        style={{
          position: "fixed",
          top: 0,
          left: 0,
          width: "100vw",
          height: "100vh",
          pointerEvents: "none",
          zIndex: 0,
          overflow: "hidden"
        }}
      >
        <FlickeringGrid 
          squareSize={12}
          gridGap={16}
          color="#0F172A"
          maxOpacity={0.06}
          flickerChance={0.6}
        />
      </div>

      <div style={{ maxWidth: 1200, margin: "0 auto", padding: "40px 32px 100px", position: "relative", zIndex: 1 }} className="animate-fade-in">
      {/* ── TOP SECTION: Hero & System Snapshot ── */}
      <div 
        style={{ 
          display: "flex", 
          flexDirection: "column",
          gap: 48, 
          alignItems: "flex-start",
          position: "relative",
          zIndex: 1
        }}
      >
        
        {/* Top: Hero & Search */}
        <div style={{ maxWidth: 960 }}>
          {/* Eyebrow */}
          <div style={{ display: "flex", flexDirection: "column", gap: 8, marginBottom: 32 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
              <div style={{ width: 6, height: 6, background: "var(--brand-accent)", borderRadius: "var(--radius-full)" }} />
              <span className="font-data" style={{ fontSize: 11, fontWeight: 700, letterSpacing: "0.1em", color: "var(--text-muted)", textTransform: "uppercase" }}>
                PAYNEXUS / MERCHANT RISK INTELLIGENCE
              </span>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginLeft: 18 }}>
              <span className="font-data" style={{ fontSize: 10, fontWeight: 500, letterSpacing: "0.05em", color: "var(--text-disabled)" }}>
                ONLINE · V2 MODEL
              </span>
            </div>
          </div>
          
          {/* Headline */}
          <h1 className="font-poppins-main" style={{ fontSize: "clamp(32px, 4.5vw, 60px)", color: "var(--text-primary)", lineHeight: 1.1, marginBottom: 32 }}>
            See Beyond The Transaction. <span style={{ color: "var(--brand-accent)", fontStyle: "italic" }}>Investigate The Network Behind It.</span>
          </h1>
          
          <p className="font-ui" style={{ fontSize: 16, color: "var(--text-secondary)", lineHeight: 1.6, maxWidth: 600, marginBottom: 48 }}>
            Trace behavioral shifts, temporal risk evolution, and hidden merchant relationships to uncover coordinated mule networks.
          </p>

          {/* Search Module */}
          <div style={{ marginBottom: 24, maxWidth: 600 }}>
            <div className="font-data" style={{ fontSize: 11, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.05em", marginBottom: 12 }}>
              &gt;_ Initialize Investigation
            </div>
            
            <form 
              onSubmit={handleSearch}
              style={{
                display: "flex",
                flexWrap: "wrap",
                alignItems: "stretch",
                gap: 8,
                padding: 6,
                background: "var(--bg-surface)",
                border: "1px solid var(--border-strong)",
                boxShadow: "var(--shadow-sm)",
                borderRadius: "var(--radius-md)",
                transition: "all var(--duration-fast) var(--ease)"
              }}
            >
              <div style={{ display: "flex", flex: "1 1 200px", alignItems: "center", padding: "0 8px", background: "transparent" }}>
                <div style={{ color: "var(--text-muted)", marginRight: 12, display: "flex" }}>
                  <Search size={18} strokeWidth={2.5} />
                </div>
                <input
                  type="text"
                  placeholder="Enter Merchant ID (e.g. M00109)"
                  aria-label="Search Merchant ID"
                  value={searchId}
                  onChange={(e) => setSearchId(e.target.value)}
                  autoFocus
                  className="font-data"
                  style={{
                    flex: 1,
                    padding: "12px 0",
                    border: "none",
                    background: "transparent",
                    fontSize: 15,
                    color: "var(--text-primary)",
                    outline: "none",
                    minWidth: 0
                  }}
                />
              </div>
              <button
                type="submit"
                disabled={loading || !searchId.trim()}
                className={`btn ${loading || !searchId.trim() ? "btn-secondary" : "btn-primary"} font-data`}
                style={{
                  flex: "0 0 auto",
                  padding: "0 24px",
                  fontSize: 13,
                  gap: 8,
                  whiteSpace: "nowrap"
                }}
              >
                {loading ? "SEARCHING..." : "INVESTIGATE MERCHANT"}
                {!loading && <CornerDownLeft size={14} />}
              </button>
            </form>
          </div>
        </div>

        {/* Bottom: System Snapshot */}
        <div style={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: 32, padding: "24px 32px", background: "var(--bg-surface)", border: "1px solid var(--border-strong)", borderRadius: "var(--radius-md)", width: "100%", maxWidth: 960, boxShadow: "var(--shadow-hard)" }}>
          <div className="font-data" style={{ fontSize: 20, fontWeight: 900, color: "var(--text-primary)", letterSpacing: "0.1em", textTransform: "uppercase" }}>
            System Snapshot
          </div>
          
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px 48px", marginLeft: "auto" }}>
            
            {/* Top Left: Inference API */}
            <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 6, color: "var(--text-secondary)", width: 140 }}>
                <Server size={16} strokeWidth={2.5} />
                <span className="font-ui" style={{ fontSize: 13, fontWeight: 700 }}>Inference API</span>
              </div>
              <span className="font-data system-badge online" style={{ fontWeight: 800 }}>ONLINE</span>
            </div>

            {/* Top Right: Active Evidence */}
            <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 6, color: "var(--text-secondary)", width: 140 }}>
                <Database size={16} strokeWidth={2.5} />
                <span className="font-ui" style={{ fontSize: 13, fontWeight: 700 }}>Active Evidence</span>
              </div>
              <span className="font-data" style={{ fontSize: 14, fontWeight: 900, color: "var(--text-primary)" }}>54 SIGNALS</span>
            </div>

            {/* Bottom Left: Scoring Model */}
            <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 6, color: "var(--text-secondary)", width: 140 }}>
                <ShieldCheck size={16} strokeWidth={2.5} />
                <span className="font-ui" style={{ fontSize: 13, fontWeight: 700 }}>Scoring Model</span>
              </div>
              <span className="font-data system-badge" style={{ borderColor: "var(--border-strong)", color: "var(--text-primary)", fontWeight: 800 }}>V2 MODEL</span>
            </div>
            
            {/* Bottom Right: Status */}
            <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 6, color: "var(--text-secondary)", width: 140 }}>
                <Activity size={16} strokeWidth={2.5} />
                <span className="font-ui" style={{ fontSize: 13, fontWeight: 700 }}>Status</span>
              </div>
              <span className="font-data" style={{ fontSize: 14, fontWeight: 900, color: "var(--success)" }}>READY</span>
            </div>
            
          </div>
        </div>
      </div>

      <hr className="divider" style={{ margin: "64px 0", borderTop: "1px dashed var(--border-default)", background: "transparent", height: 0 }} />

      {/* ── BOTTOM SECTION: Investigation Cases ── */}
      <div>
        <h2 className="font-poppins-sub" style={{ fontSize: 32, color: "var(--text-primary)", marginBottom: 32 }}>
          Active Investigation Cases
        </h2>
        
        <div 
          style={{ 
            display: "grid", 
            gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", 
            gap: 24 
          }}
        >
          {DEMO_MERCHANTS.map((m, idx) => {
            const isBlindSpot = m.id === "M00492";
            return (
              <button
                key={m.id}
                onClick={() => handleDemoClick(m.id)}
                className="btn btn-secondary"
                style={{
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "flex-start",
                  padding: "24px",
                  background: isBlindSpot ? "var(--bg-subtle)" : "var(--bg-surface)",
                  border: isBlindSpot ? "2px dashed var(--border-strong)" : "2px solid var(--border-strong)",
                  boxShadow: "var(--shadow-hard)",
                  textAlign: "left",
                  width: "100%",
                  height: "100%"
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", width: "100%", marginBottom: 20 }}>
                  <span className="font-data" style={{ fontSize: 11, color: isBlindSpot ? "var(--text-secondary)" : "var(--text-muted)", letterSpacing: "0.1em" }}>
                    {isBlindSpot ? "KNOWN BLIND SPOT" : `CASE / ${String(idx + 1).padStart(2, '0')}`}
                  </span>
                  {isBlindSpot ? (
                    <span className="font-data" style={{ fontSize: 10, padding: "2px 6px", background: "var(--bg-surface)", border: "1px solid var(--text-disabled)", borderRadius: "var(--radius-sm)", color: "var(--text-secondary)" }}>
                      RECALL: 65.6%
                    </span>
                  ) : (
                    <span className={`risk-badge ${m.band.toLowerCase()}`}>
                      {m.band}
                    </span>
                  )}
                </div>
                
                <div className="font-data" style={{ fontSize: 28, fontWeight: 900, color: "var(--text-primary)", marginBottom: 12, letterSpacing: "-0.02em" }}>
                  {m.id}
                </div>
                
                <div className="font-ui" style={{ fontSize: 14, fontWeight: 600, color: "var(--text-primary)", marginBottom: 12 }}>
                  {isBlindSpot ? "Type-D Behavioral Transition" : m.label}
                </div>
                
                <p className="font-ui" style={{ fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.5, margin: 0, flex: 1, marginBottom: 28, fontStyle: isBlindSpot ? "italic" : "normal" }}>
                  {isBlindSpot ? "The inference model classified this merchant as LOW risk. Manual network investigation is recommended to reveal true risk trajectory." : m.description}
                </p>
                
                <div style={{ display: "flex", alignItems: "center", gap: 6, color: "var(--text-primary)", fontSize: 12, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.05em" }}>
                  <span>{isBlindSpot ? "Investigate Anomaly" : "Open File"}</span>
                  <ArrowRight size={14} />
                </div>
              </button>
            );
          })}
        </div>
      </div>
      </div>

      {/* ── FOOTER CONTACT SECTION ── */}
      <footer style={{
        background: "var(--bg-surface)", 
        padding: "51px 32px",
        position: "relative",
        zIndex: 1,
        width: "100%",
        marginTop: 48,
        overflow: "hidden",
        borderTop: "1px solid var(--border-default)"
      }}>
        {/* Full-width Accent Ribbon */}
        <div style={{ position: "absolute", top: 0, left: 0, width: "100%", background: "var(--brand-accent)", padding: "12px 0", overflow: "hidden", display: "flex", alignItems: "center", borderBottom: "1px solid var(--border-default)" }}>
          <div className="animate-marquee" style={{ gap: 48 }}>
            {[
              "Next.js", "React", "TypeScript", "FastAPI", "Python", "XGBoost", "SHAP", "Pandas", "Lucide",
              "Next.js", "React", "TypeScript", "FastAPI", "Python", "XGBoost", "SHAP", "Pandas", "Lucide",
              "Next.js", "React", "TypeScript", "FastAPI", "Python", "XGBoost", "SHAP", "Pandas", "Lucide",
              "Next.js", "React", "TypeScript", "FastAPI", "Python", "XGBoost", "SHAP", "Pandas", "Lucide"
            ].map((tech, i) => (
              <div key={i} className="font-data" style={{ 
                fontSize: 13, 
                fontWeight: 900, 
                color: "var(--text-inverse)", 
                letterSpacing: "0.15em",
                textTransform: "uppercase",
                display: "flex",
                alignItems: "center",
                gap: 12,
                whiteSpace: "nowrap"
              }}>
                <div style={{ width: 6, height: 6, borderRadius: "50%", background: "var(--text-inverse)", opacity: 0.5, flexShrink: 0 }} />
                {tech}
              </div>
            ))}
          </div>
        </div>

        <div style={{ maxWidth: 1200, margin: "0 auto", display: "flex", flexDirection: "column", alignItems: "flex-start", marginTop: 34 }}>
          
          <h2 className="font-poppins-main" style={{ fontSize: 39, color: "var(--text-primary)", marginBottom: 4, lineHeight: 1.1 }}>
            PayNexus is built
          </h2>
          <h2 className="font-poppins-main" style={{ fontSize: 39, color: "var(--brand-accent)", marginBottom: 27, lineHeight: 1.1 }}>
            &lt;for investigators by investigators&gt;
          </h2>
          
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 32, width: "100%" }}>
            
            {/* Contact Info */}
            <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10, color: "var(--text-primary)" }}>
                <Activity size={20} />
                <span className="font-ui" style={{ fontSize: 17, fontWeight: 700 }}>Connect with the Builder</span>
              </div>
              <p className="font-ui" style={{ fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.6, marginBottom: 7, maxWidth: 300 }}>
                Reach out to discuss the underlying machine learning models, architecture design, or potential collaborations.
              </p>
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                <a href="mailto:gkmamarnath@gmail.com" style={{ color: "var(--text-primary)", textDecoration: "none", fontSize: 13, fontWeight: 700, display: "flex", alignItems: "center", gap: 7 }}>
                  Connect via Mail <ArrowRight size={12} />
                </a>
                <a href="https://www.linkedin.com/in/amarnath-gowda" target="_blank" rel="noopener noreferrer" style={{ color: "var(--text-primary)", textDecoration: "none", fontSize: 13, fontWeight: 700, display: "flex", alignItems: "center", gap: 7 }}>
                  Connect on LinkedIn <ArrowRight size={12} />
                </a>
              </div>
            </div>

          </div>
          
          {/* WHY PAYNEXUS - Origin Story Link */}
          <div style={{ marginTop: 34, paddingTop: 27, borderTop: "1px solid var(--border-default)", width: "100%", display: "flex", flexDirection: "column", gap: 10 }}>
            <div className="font-data" style={{ fontSize: 10, fontWeight: 700, letterSpacing: "0.1em", color: "var(--brand-accent)", textTransform: "uppercase" }}>
              WHY PAYNEXUS
            </div>
            <p className="font-ui" style={{ fontSize: 14, color: "var(--text-secondary)", margin: 0 }}>
              How a fintech question became a network intelligence platform.
            </p>
            <div style={{ marginTop: 7 }}>
              <button
                onClick={() => router.push("/why-paynexus")}
                style={{ 
                  background: "transparent", 
                  border: "none", 
                  padding: 0,
                  color: "var(--text-primary)", 
                  fontSize: 12, 
                  fontWeight: 700, 
                  display: "flex", 
                  alignItems: "center", 
                  gap: 7,
                  cursor: "pointer",
                  letterSpacing: "0.05em",
                  textTransform: "uppercase"
                }}
                className="font-data"
              >
                READ THE STORY <ArrowRight size={12} />
              </button>
            </div>
          </div>

          <div style={{ width: "100%", display: "flex", justifyContent: "center", alignItems: "center", marginTop: 54, paddingTop: 27, borderTop: "1px solid var(--border-subtle)" }}>
            <div className="font-data" style={{ fontSize: 11, color: "var(--text-muted)", letterSpacing: "0.05em" }}>
              © {new Date().getFullYear()} PAYNEXUS INTELLIGENCE
            </div>
          </div>
        </div>
      </footer>
    </>
  );
}
