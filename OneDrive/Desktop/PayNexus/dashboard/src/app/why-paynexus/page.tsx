"use client";

import { ArrowLeft, ArrowRight } from "lucide-react";
import { useRouter } from "next/navigation";
import { FlickeringGrid } from "@/components/FlickeringGrid";

export default function WhyPayNexusPage() {
  const router = useRouter();

  const handleReturn = () => {
    router.push("/");
  };

  return (
    <>
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
          maxOpacity={0.03}
          flickerChance={0.2}
        />
      </div>

      <div style={{ maxWidth: 900, margin: "0 auto", padding: "40px 32px 120px", position: "relative", zIndex: 1 }} className="animate-fade-in">
        
        {/* NAVIGATION */}
        <button
          onClick={handleReturn}
          className="font-data"
          style={{
            background: "transparent",
            border: "none",
            padding: 0,
            display: "flex",
            alignItems: "center",
            gap: 8,
            color: "var(--text-secondary)",
            fontSize: 12,
            fontWeight: 700,
            letterSpacing: "0.1em",
            textTransform: "uppercase",
            cursor: "pointer",
            marginBottom: 80
          }}
        >
          <ArrowLeft size={14} /> BACK TO INVESTIGATION
        </button>

        {/* SECTION 01 — HERO */}
        <section style={{ marginBottom: 120 }}>
          <div className="font-data" style={{ fontSize: 11, fontWeight: 700, color: "var(--brand-accent)", letterSpacing: "0.1em", textTransform: "uppercase", marginBottom: 24 }}>
            WHY PAYNEXUS<br />
            <span style={{ color: "var(--text-muted)" }}>/ PRODUCT ORIGIN</span>
          </div>
          <h1 className="font-display" style={{ fontSize: "clamp(40px, 6vw, 72px)", fontWeight: 500, color: "var(--text-primary)", lineHeight: 1.1, letterSpacing: "-0.02em", marginBottom: 32 }}>
            I didn't start with fintech.<br />
            <span style={{ fontStyle: "italic" }}>I started with a question.</span>
          </h1>
          <p className="font-ui" style={{ fontSize: 20, color: "var(--text-secondary)", lineHeight: 1.6, maxWidth: 700 }}>
            I'm a fourth-year engineering student, and when I began exploring this problem, fintech wasn't a domain I knew deeply.
          </p>
          <p className="font-ui" style={{ fontSize: 16, color: "var(--text-muted)", lineHeight: 1.6, maxWidth: 650, marginTop: 24 }}>
            This project began with an attempt to understand how financial systems identify fraud and risk. What started as technical curiosity eventually evolved into a specialized network intelligence platform.
          </p>
        </section>

        {/* SECTION 02 — THE DISCOVERY */}
        <section style={{ marginBottom: 120 }}>
          <div className="font-data" style={{ fontSize: 11, fontWeight: 700, color: "var(--text-disabled)", letterSpacing: "0.1em", marginBottom: 16 }}>
            01 / THE DISCOVERY
          </div>
          <h2 className="font-display" style={{ fontSize: 32, fontWeight: 500, color: "var(--text-primary)", marginBottom: 24, letterSpacing: "-0.02em" }}>
            Learning the problem before building the product.
          </h2>
          <div style={{ maxWidth: 650, display: "flex", flexDirection: "column", gap: 24 }}>
            <p className="font-ui" style={{ fontSize: 16, color: "var(--text-secondary)", lineHeight: 1.6 }}>
              During my research into fintech, I came across the problem of merchant mule networks and the growing importance of identifying coordinated suspicious activity across financial systems.
            </p>
            <p className="font-ui" style={{ fontSize: 16, color: "var(--text-secondary)", lineHeight: 1.6 }}>
              The more I explored the problem, the more interesting one thing became: a merchant can look legitimate on its own while the network around it can tell a very different story.
            </p>
            <div style={{ padding: "32px 0", borderTop: "1px solid var(--border-subtle)", borderBottom: "1px solid var(--border-subtle)", marginTop: 16 }}>
              <p className="font-display" style={{ fontSize: 24, color: "var(--brand-accent)", lineHeight: 1.4, margin: 0, fontStyle: "italic" }}>
                "A merchant can look legitimate in isolation.<br />
                A network can tell a different story."
              </p>
            </div>
          </div>
        </section>

        {/* SECTION 03 — THE QUESTION */}
        <section style={{ marginBottom: 120 }}>
          <div className="font-data" style={{ fontSize: 11, fontWeight: 700, color: "var(--text-disabled)", letterSpacing: "0.1em", marginBottom: 16 }}>
            02 / THE QUESTION
          </div>
          <h2 className="font-display" style={{ fontSize: 32, fontWeight: 500, color: "var(--text-primary)", marginBottom: 24, letterSpacing: "-0.02em" }}>
            What if the merchant isn't the whole story?
          </h2>
          <div style={{ maxWidth: 650, display: "flex", flexDirection: "column", gap: 24 }}>
            <p className="font-ui" style={{ fontSize: 16, color: "var(--text-secondary)", lineHeight: 1.6 }}>
              Individual merchant analysis can easily miss relationships between merchants, devices, IP addresses, customers, and settlement entities. While not every relationship is inherently suspicious, these connections provide critical investigative context.
            </p>
            <p className="font-ui" style={{ fontSize: 16, color: "var(--text-secondary)", lineHeight: 1.6 }}>
              So I started asking a different question.
            </p>
            <div style={{ padding: 48, background: "var(--bg-surface)", border: "1px solid var(--border-subtle)", borderRadius: "var(--radius-lg)", marginTop: 16, boxShadow: "var(--shadow-sm)" }}>
              <p className="font-display" style={{ fontSize: 28, color: "var(--text-primary)", lineHeight: 1.3, margin: 0 }}>
                "What if we investigated the network surrounding the merchant — not just the merchant itself?"
              </p>
            </div>
          </div>
        </section>

        {/* SECTION 04 — FROM CONNECTIONS TO EVOLUTION */}
        <section style={{ marginBottom: 120 }}>
          <div className="font-data" style={{ fontSize: 11, fontWeight: 700, color: "var(--text-disabled)", letterSpacing: "0.1em", marginBottom: 16 }}>
            03 / THE INSIGHT
          </div>
          <h2 className="font-display" style={{ fontSize: 32, fontWeight: 500, color: "var(--text-primary)", marginBottom: 24, letterSpacing: "-0.02em" }}>
            Who is connected matters.<br />
            <span style={{ fontStyle: "italic", color: "var(--text-muted)" }}>How those connections change matters more.</span>
          </h2>
          <div style={{ maxWidth: 650, display: "flex", flexDirection: "column", gap: 32 }}>
            <p className="font-ui" style={{ fontSize: 16, color: "var(--text-secondary)", lineHeight: 1.6 }}>
              I quickly realized that static network analysis wasn't enough. Relationships are fluid. Risk is dynamic. The transition required moving from static connectivity to temporal network intelligence.
            </p>
            
            <div style={{ display: "flex", flexDirection: "column", gap: 16, padding: "32px 0", alignItems: "center" }}>
              <div className="font-data" style={{ fontSize: 12, fontWeight: 700, color: "var(--text-muted)", letterSpacing: "0.1em", textTransform: "uppercase" }}>STATIC</div>
              <div className="font-ui" style={{ fontSize: 16, color: "var(--text-primary)", fontWeight: 500 }}>Who is connected?</div>
              <ArrowRight size={20} color="var(--brand-accent)" style={{ transform: "rotate(90deg)", margin: "8px 0" }} />
              <div className="font-data" style={{ fontSize: 12, fontWeight: 700, color: "var(--brand-accent)", letterSpacing: "0.1em", textTransform: "uppercase" }}>TEMPORAL</div>
              <div className="font-ui" style={{ fontSize: 16, color: "var(--text-primary)", fontWeight: 500, textAlign: "center" }}>How are those relationships forming,<br />changing, and accelerating?</div>
            </div>

            <p className="font-ui" style={{ fontSize: 16, color: "var(--text-secondary)", lineHeight: 1.6 }}>
              This led to prioritizing temporal behavior, network evolution, and strict point-in-time analysis to avoid future-data leakage when scoring a merchant's historical state.
            </p>
          </div>
        </section>

        {/* SECTION 05 — THE RESEARCH */}
        <section style={{ marginBottom: 120 }}>
          <div className="font-data" style={{ fontSize: 11, fontWeight: 700, color: "var(--text-disabled)", letterSpacing: "0.1em", marginBottom: 16 }}>
            04 / THE RESEARCH
          </div>
          <h2 className="font-display" style={{ fontSize: 32, fontWeight: 500, color: "var(--text-primary)", marginBottom: 24, letterSpacing: "-0.02em" }}>
            From curiosity to a working hypothesis.
          </h2>
          <div style={{ maxWidth: 650, display: "flex", flexDirection: "column", gap: 24 }}>
            <p className="font-ui" style={{ fontSize: 16, color: "var(--text-secondary)", lineHeight: 1.6 }}>
              I spent significant time researching fintech fraud detection, merchant mule networks, MuleHunter concepts, and temporal risk analysis. During this exploration, I also studied the broader Razorpay security ecosystem, including Vulcan.
            </p>
            <p className="font-ui" style={{ fontSize: 16, color: "var(--text-primary)", fontWeight: 600, lineHeight: 1.6, paddingLeft: 24, borderLeft: "3px solid var(--brand-accent)" }}>
              The goal wasn't to reproduce an existing system. It was to understand the problem well enough to ask where a network-centric merchant investigation layer could fit.
            </p>
          </div>
        </section>

        {/* SECTION 06 — THE HYPOTHESIS */}
        <section style={{ marginBottom: 120 }}>
          <div className="font-data" style={{ fontSize: 11, fontWeight: 700, color: "var(--text-disabled)", letterSpacing: "0.1em", marginBottom: 16 }}>
            05 / THE HYPOTHESIS
          </div>
          <div style={{ background: "var(--brand)", color: "white", padding: "64px 48px", borderRadius: "var(--radius-xl)", boxShadow: "var(--shadow-hard-accent)", marginBottom: 48 }}>
            <h2 className="font-display" style={{ fontSize: "clamp(24px, 4vw, 36px)", fontWeight: 500, color: "white", lineHeight: 1.3, letterSpacing: "-0.02em", margin: 0, fontStyle: "italic" }}>
              "What if mule detection could move beyond the individual transaction and investigate the network behind the merchant?"
            </h2>
          </div>
          
          <div style={{ maxWidth: 650, margin: "0 auto" }}>
            <p className="font-ui" style={{ fontSize: 18, color: "var(--text-primary)", fontWeight: 600, textAlign: "center", marginBottom: 48 }}>
              That became the hypothesis behind PayNexus.
            </p>
            
            <div style={{ display: "flex", flexDirection: "column", gap: 16, alignItems: "center" }}>
              {["TRANSACTION", "MERCHANT", "RELATIONSHIPS", "NETWORK", "NETWORK EVOLUTION", "RISK"].map((step, i, arr) => (
                <div key={step} style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 16 }}>
                  <div className="font-data" style={{ fontSize: 14, fontWeight: 700, color: i === arr.length - 1 ? "var(--brand-accent)" : "var(--text-primary)", letterSpacing: "0.1em" }}>
                    {step}
                  </div>
                  {i < arr.length - 1 && <ArrowRight size={16} color="var(--text-disabled)" style={{ transform: "rotate(90deg)" }} />}
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* SECTION 07 — MULEHUNTER */}
        <section style={{ marginBottom: 120 }}>
          <div className="font-data" style={{ fontSize: 11, fontWeight: 700, color: "var(--text-disabled)", letterSpacing: "0.1em", marginBottom: 16 }}>
            06 / THE INTELLIGENCE ENGINE
          </div>
          <h2 className="font-display" style={{ fontSize: 40, fontWeight: 500, color: "var(--text-primary)", marginBottom: 8, letterSpacing: "-0.02em" }}>
            MuleHunter
          </h2>
          <div className="font-data" style={{ fontSize: 14, color: "var(--text-muted)", letterSpacing: "0.05em", textTransform: "uppercase", marginBottom: 32 }}>
            Temporal network intelligence.
          </div>
          <div style={{ maxWidth: 650, display: "flex", flexDirection: "column", gap: 24 }}>
            <p className="font-ui" style={{ fontSize: 16, color: "var(--text-secondary)", lineHeight: 1.6 }}>
              MuleHunter is the intelligence engine behind PayNexus. It combines behavioral signals, network relationships, and temporal evolution to identify patterns associated with coordinated merchant mule activity.
            </p>
            <p className="font-ui" style={{ fontSize: 16, color: "var(--text-primary)", fontWeight: 500, lineHeight: 1.6, background: "var(--bg-surface)", padding: 24, border: "1px solid var(--border-subtle)", borderRadius: "var(--radius-md)" }}>
              The objective isn't simply to identify an unusual merchant. It is to identify when seemingly ordinary entities begin exhibiting patterns that suggest coordinated activity.
            </p>
          </div>
        </section>

        {/* SECTION 08 — FROM MODEL TO INVESTIGATOR */}
        <section style={{ marginBottom: 120 }}>
          <div className="font-data" style={{ fontSize: 11, fontWeight: 700, color: "var(--text-disabled)", letterSpacing: "0.1em", marginBottom: 16 }}>
            07 / THE PRODUCT
          </div>
          <h2 className="font-display" style={{ fontSize: 32, fontWeight: 500, color: "var(--text-primary)", marginBottom: 24, letterSpacing: "-0.02em" }}>
            Building the investigator layer.
          </h2>
          <div style={{ maxWidth: 650, display: "flex", flexDirection: "column", gap: 32 }}>
            <div>
              <p className="font-ui" style={{ fontSize: 18, color: "var(--text-primary)", fontWeight: 600, marginBottom: 8 }}>Building a model wasn't enough.</p>
              <p className="font-ui" style={{ fontSize: 18, color: "var(--text-secondary)", lineHeight: 1.5 }}>
                A risk score alone doesn't answer the investigator's most important question:<br />
                <span className="font-display" style={{ fontSize: 24, color: "var(--brand-accent)", fontStyle: "italic" }}>Why?</span>
              </p>
            </div>
            
            <div style={{ display: "flex", flexDirection: "column", gap: 24, paddingLeft: 24, borderLeft: "2px solid var(--border-subtle)" }}>
              {[
                { step: "SEARCH", desc: "Find the merchant." },
                { step: "SCORE", desc: "Understand its current risk." },
                { step: "EXPLAIN", desc: "Understand which model features influenced the prediction." },
                { step: "TRACE", desc: "See how risk evolves over time." },
                { step: "CONNECT", desc: "Explore the surrounding network." },
                { step: "INVESTIGATE", desc: "Move from an isolated merchant to the broader relationship graph." }
              ].map((item, i, arr) => (
                <div key={item.step}>
                  <div className="font-data" style={{ fontSize: 13, fontWeight: 700, color: "var(--text-primary)", letterSpacing: "0.05em", marginBottom: 4 }}>{item.step}</div>
                  <div className="font-ui" style={{ fontSize: 15, color: "var(--text-muted)" }}>{item.desc}</div>
                  {i < arr.length - 1 && <ArrowRight size={14} color="var(--border-default)" style={{ transform: "rotate(90deg)", marginTop: 24, marginLeft: 16 }} />}
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* SECTION 09 — WHY SHAP */}
        <section style={{ marginBottom: 120 }}>
          <div className="font-data" style={{ fontSize: 11, fontWeight: 700, color: "var(--text-disabled)", letterSpacing: "0.1em", marginBottom: 16 }}>
            08 / EXPLAINABILITY
          </div>
          <h2 className="font-display" style={{ fontSize: 32, fontWeight: 500, color: "var(--text-primary)", marginBottom: 24, letterSpacing: "-0.02em" }}>
            A prediction should be explainable.
          </h2>
          <div style={{ maxWidth: 650, display: "flex", flexDirection: "column", gap: 24 }}>
            <p className="font-ui" style={{ fontSize: 16, color: "var(--text-secondary)", lineHeight: 1.6 }}>
              PayNexus uses SHAP (SHapley Additive exPlanations) as a read-only explainability layer wrapped around the frozen MuleHunter model. It explicitly separates risk-increasing factors from risk-reducing factors to show the relative contribution of each signal.
            </p>
            <div style={{ background: "var(--bg-surface)", padding: 32, border: "1px solid var(--border-default)", borderRadius: "var(--radius-lg)" }}>
              <p className="font-ui" style={{ fontSize: 16, color: "var(--text-primary)", fontWeight: 500, marginBottom: 16 }}>
                The observed feature tells the investigator <span style={{ color: "var(--brand-accent)" }}>what the model measured.</span>
              </p>
              <p className="font-ui" style={{ fontSize: 16, color: "var(--text-primary)", fontWeight: 500, margin: 0 }}>
                The SHAP contribution tells them <span style={{ color: "var(--brand-accent)" }}>how that measurement influenced the model's prediction.</span>
              </p>
            </div>
          </div>
        </section>

        {/* SECTION 10 — WHY PAYNEXUS */}
        <section style={{ marginBottom: 120 }}>
          <div className="font-data" style={{ fontSize: 11, fontWeight: 700, color: "var(--text-disabled)", letterSpacing: "0.1em", marginBottom: 16 }}>
            09 / THE PRODUCT IDEA
          </div>
          <h2 className="font-display" style={{ fontSize: 32, fontWeight: 500, color: "var(--text-primary)", marginBottom: 48, letterSpacing: "-0.02em" }}>
            Why PayNexus?
          </h2>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(250px, 1fr))", gap: 32 }}>
            <div>
              <h3 className="font-data" style={{ fontSize: 12, fontWeight: 700, color: "var(--text-primary)", letterSpacing: "0.05em", marginBottom: 12 }}>BEYOND TRANSACTIONS</h3>
              <p className="font-ui" style={{ fontSize: 15, color: "var(--text-secondary)", lineHeight: 1.6 }}>
                Investigate the merchant and the relationships surrounding it, rather than treating every transaction as an isolated event.
              </p>
            </div>
            <div>
              <h3 className="font-data" style={{ fontSize: 12, fontWeight: 700, color: "var(--text-primary)", letterSpacing: "0.05em", marginBottom: 12 }}>TEMPORAL INTELLIGENCE</h3>
              <p className="font-ui" style={{ fontSize: 15, color: "var(--text-secondary)", lineHeight: 1.6 }}>
                Understand how merchant behavior and network relationships evolve over time.
              </p>
            </div>
            <div>
              <h3 className="font-data" style={{ fontSize: 12, fontWeight: 700, color: "var(--text-primary)", letterSpacing: "0.05em", marginBottom: 12 }}>EXPLAINABLE INVESTIGATION</h3>
              <p className="font-ui" style={{ fontSize: 15, color: "var(--text-secondary)", lineHeight: 1.6 }}>
                Give investigators both the underlying evidence and an interpretable view of how the model reached its risk prediction.
              </p>
            </div>
          </div>
        </section>

        {/* SECTION 11 — THE NAME */}
        <section style={{ marginBottom: 120 }}>
          <div className="font-data" style={{ fontSize: 11, fontWeight: 700, color: "var(--text-disabled)", letterSpacing: "0.1em", marginBottom: 16 }}>
            10 / THE NAME
          </div>
          <h2 className="font-display" style={{ fontSize: 32, fontWeight: 500, color: "var(--text-primary)", marginBottom: 32, letterSpacing: "-0.02em" }}>
            Why "PayNexus"?
          </h2>
          <div style={{ maxWidth: 650, display: "flex", flexDirection: "column", gap: 24 }}>
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              <div className="font-data" style={{ fontSize: 16, color: "var(--text-primary)" }}>
                <strong style={{ color: "var(--brand-accent)" }}>PAY</strong> → the payment ecosystem.
              </div>
              <div className="font-data" style={{ fontSize: 16, color: "var(--text-primary)" }}>
                <strong style={{ color: "var(--brand-accent)" }}>NEXUS</strong> → a connected center or network of relationships.
              </div>
            </div>
            <p className="font-ui" style={{ fontSize: 18, color: "var(--text-secondary)", lineHeight: 1.6, marginTop: 16, fontStyle: "italic" }}>
              The name reflects the core idea behind the product:<br /><br />
              Payment risk is not always contained within a transaction. Sometimes it exists in the relationships surrounding it.
            </p>
          </div>
        </section>

        {/* SECTION 12 — CLOSING */}
        <section style={{ marginTop: 160, paddingTop: 80, borderTop: "2px solid var(--border-strong)", textAlign: "center" }}>
          <h2 className="font-display" style={{ fontSize: "clamp(36px, 5vw, 64px)", fontWeight: 500, color: "var(--text-primary)", lineHeight: 1.1, letterSpacing: "-0.02em", marginBottom: 16 }}>
            See beyond the transaction.<br />
            <span style={{ color: "var(--brand-accent)", fontStyle: "italic" }}>Investigate the network behind it.</span>
          </h2>
          
          <p className="font-ui" style={{ fontSize: 18, color: "var(--text-secondary)", margin: "0 auto 48px", maxWidth: 600 }}>
            What began as an attempt to understand fintech became a question about how financial networks reveal risk.
          </p>

          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 8, marginBottom: 64 }}>
            <div className="font-data" style={{ fontSize: 14, fontWeight: 700, color: "var(--text-primary)", letterSpacing: "0.05em" }}>MuleHunter</div>
            <div className="font-ui" style={{ fontSize: 14, color: "var(--text-muted)" }}>Temporal Network Intelligence</div>
            <ArrowRight size={16} color="var(--border-default)" style={{ transform: "rotate(90deg)", margin: "8px 0" }} />
            <div className="font-data" style={{ fontSize: 14, fontWeight: 700, color: "var(--brand-accent)", letterSpacing: "0.05em" }}>PayNexus</div>
            <div className="font-ui" style={{ fontSize: 14, color: "var(--text-muted)" }}>Merchant Risk Investigation</div>
          </div>

          <button
            onClick={handleReturn}
            className="btn font-data"
            style={{
              background: "var(--brand-accent)",
              color: "white",
              border: "none",
              padding: "16px 32px",
              fontSize: 14,
              fontWeight: 700,
              letterSpacing: "0.1em",
              borderRadius: "var(--radius-md)",
              cursor: "pointer",
              display: "inline-flex",
              alignItems: "center",
              gap: 12,
              boxShadow: "var(--shadow-hard)"
            }}
          >
            START AN INVESTIGATION <ArrowRight size={16} />
          </button>
        </section>

      </div>
    </>
  );
}
