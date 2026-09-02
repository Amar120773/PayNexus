"use client";

import { useState, useMemo, useEffect, useRef } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";
import { ScoreResult } from "@/lib/api";
import { ArrowRight, Activity } from "lucide-react";

type RiskTimelineProps = {
  timeline: ScoreResult[];
  threshold: number;
  selectedTimestamp?: string;
  onPointClick?: (point: ScoreResult) => void;
  onNavigateToEvidence?: () => void;
};

const bandColor = (band: string) =>
  band === "HIGH" ? "var(--risk-high-text)" : band === "MEDIUM" ? "var(--risk-medium-text)" : "var(--risk-low-text)";

function CustomDot(props: any) {
  const { cx, cy, payload, selectedTimestamp } = props;
  const isSelected = payload.scoring_timestamp === selectedTimestamp;
  const color = bandColor(payload.risk_band);
  if (!cx || !cy) return null;
  return (
    <g>
      {isSelected && (
        <circle cx={cx} cy={cy} r={12} fill={color} opacity={0.15} style={{ transition: "all 0.2s ease" }} />
      )}
      <circle
        cx={cx}
        cy={cy}
        r={isSelected ? 6 : 4}
        fill={isSelected ? color : "var(--bg-surface)"}
        stroke={color}
        strokeWidth={isSelected ? 3 : 2}
        style={{ cursor: "pointer", transition: "all 0.2s ease" }}
      />
    </g>
  );
}

export default function RiskTimeline({
  timeline,
  threshold,
  selectedTimestamp,
  onPointClick,
  onNavigateToEvidence,
}: RiskTimelineProps) {
  
  // Sort timeline chronologically just in case
  const sortedTimeline = useMemo(() => {
    return [...timeline].sort((a, b) => new Date(a.scoring_timestamp).getTime() - new Date(b.scoring_timestamp).getTime());
  }, [timeline]);

  const data = useMemo(
    () =>
      sortedTimeline.map((res) => ({
        ...res,
        dateStr: res.scoring_timestamp.split(" ")[0],
        riskScoreValue: res.risk_score,
      })),
    [sortedTimeline]
  );

  const selectedIndex = useMemo(() => {
    const idx = sortedTimeline.findIndex((t) => t.scoring_timestamp === selectedTimestamp);
    return idx >= 0 ? idx : sortedTimeline.length - 1;
  }, [sortedTimeline, selectedTimestamp]);

  const selectedPoint = sortedTimeline[selectedIndex];
  const previousPoint = selectedIndex > 0 ? sortedTimeline[selectedIndex - 1] : null;

  if (!data || data.length === 0) {
    return (
      <div style={{ padding: 48, textAlign: "center", border: "1px dashed var(--border-default)", color: "var(--text-disabled)" }}>
        No historical timeline data available.
      </div>
    );
  }

  // Handle native slider change
  const handleSliderChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const idx = parseInt(e.target.value, 10);
    const pt = sortedTimeline[idx];
    if (pt && onPointClick) onPointClick(pt);
  };

  // Safe delta calculation
  const scoreDelta = previousPoint ? (selectedPoint.risk_score - previousPoint.risk_score) : 0;
  const absScoreDelta = Math.abs(scoreDelta);
  
  const evidenceCountDelta = previousPoint 
    ? Object.keys(selectedPoint.evidence_features).length - Object.keys(previousPoint.evidence_features).length 
    : 0;

  return (
    <div className="animate-fade-in" style={{ display: "flex", flexDirection: "column", gap: 48 }}>
      
      {/* ── HERO ── */}
      <div>
        <div className="font-data" style={{ fontSize: 11, color: "var(--text-muted)", letterSpacing: "0.1em", marginBottom: 12 }}>
          RISK EVOLUTION
        </div>
        <h2 className="font-poppins-sub" style={{ fontSize: 40, color: "var(--text-primary)", margin: "0 0 8px" }}>
          Historical Trajectory
        </h2>
        <p className="font-ui" style={{ fontSize: 16, color: "var(--text-secondary)", margin: 0 }}>
          How the merchant's risk profile changed across observed time.
        </p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: 32, alignItems: "start" }}>
        
        {/* ── LEFT COLUMN: GRAPH & SCRUBBER ── */}
        <div style={{ gridColumn: "1 / -1", '@media (minWidth: 1024px)': { gridColumn: "span 2" } } as any}>
          <div style={{ background: "var(--bg-surface)", border: "1px solid var(--border-subtle)", borderRadius: "var(--radius-lg)", padding: 24, boxShadow: "var(--shadow-sm)" }}>
            
            {/* Graph */}
            <div style={{ height: 360, width: "100%", marginBottom: 32 }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart
                  data={data}
                  margin={{ top: 24, right: 24, left: -20, bottom: 0 }}
                  onClick={(e: any) => {
                    if (e?.activePayload && onPointClick) onPointClick(e.activePayload[0].payload);
                  }}
                  style={{ cursor: "pointer" }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border-subtle)" vertical={false} />
                  <XAxis 
                    dataKey="dateStr" 
                    stroke="transparent" 
                    tick={{ fill: "var(--text-muted)", fontSize: 11, fontFamily: "var(--font-mono)" }} 
                    tickMargin={16} 
                  />
                  <YAxis 
                    domain={[0, 'auto']} 
                    stroke="transparent" 
                    tick={{ fill: "var(--text-muted)", fontSize: 11, fontFamily: "var(--font-mono)", fontVariantNumeric: "tabular-nums" } as any} 
                  />
                  
                  {/* Tooltip purely as a hover helper, the main panel handles reading */}
                  <Tooltip
                    content={({ active, payload }) => {
                      if (!active || !payload?.length) return null;
                      const p = payload[0].payload as ScoreResult;
                      return (
                        <div style={{ background: "var(--bg-elevated)", border: "1px solid var(--border-default)", padding: "8px 12px", borderRadius: "var(--radius-sm)", boxShadow: "var(--shadow-md)" }}>
                          <div className="font-data" style={{ fontSize: 10, color: "var(--text-muted)", marginBottom: 4 }}>{p.scoring_timestamp}</div>
                          <div className="font-data" style={{ fontSize: 13, fontWeight: 700, color: "var(--text-primary)" }}>{p.risk_score.toFixed(4)}</div>
                        </div>
                      );
                    }}
                    cursor={{ stroke: "var(--border-strong)", strokeWidth: 1, strokeDasharray: "4 4" }}
                  />

                  {/* Threshold Reference */}
                  <ReferenceLine
                    y={threshold}
                    stroke="var(--risk-high-text)"
                    strokeDasharray="4 4"
                    strokeWidth={1}
                    label={{
                      position: "insideTopRight",
                      value: `MODEL THRESHOLD (${threshold.toFixed(4)})`,
                      fill: "var(--risk-high-text)",
                      fontSize: 10,
                      fontFamily: "var(--font-mono)",
                      dy: -12,
                      letterSpacing: "0.05em"
                    }}
                  />

                  <Line
                    type="monotone"
                    dataKey="riskScoreValue"
                    stroke="var(--text-primary)"
                    strokeWidth={2}
                    dot={(dotProps: any) => <CustomDot key={dotProps.index} {...dotProps} selectedTimestamp={selectedTimestamp} />}
                    activeDot={false}
                    isAnimationActive={true}
                    animationDuration={400}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>

            {/* Tactile Scrubber */}
            <div style={{ padding: "0 24px" }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
                <span className="font-data" style={{ fontSize: 10, color: "var(--text-muted)" }}>{sortedTimeline[0].scoring_timestamp.split(" ")[0]}</span>
                <span className="font-data" style={{ fontSize: 10, color: "var(--text-muted)" }}>{sortedTimeline[sortedTimeline.length - 1].scoring_timestamp.split(" ")[0]}</span>
              </div>
              
              <input 
                type="range" 
                min={0} 
                max={sortedTimeline.length - 1} 
                value={selectedIndex} 
                onChange={handleSliderChange}
                style={{
                  width: "100%",
                  cursor: "pointer",
                  accentColor: "var(--brand)",
                  height: 4,
                }}
                aria-label="Timeline Scrubber"
              />
            </div>

          </div>
        </div>

        {/* ── RIGHT COLUMN: INSPECTION PANELS ── */}
        <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
          
          {/* Current Snapshot */}
          <div style={{ background: "var(--bg-subtle)", border: "1px solid var(--border-strong)", padding: 32 }}>
            <div className="font-data" style={{ fontSize: 10, color: "var(--text-muted)", letterSpacing: "0.1em", marginBottom: 24 }}>
              CURRENT SNAPSHOT
            </div>
            
            <div className="font-data" style={{ fontSize: 13, color: "var(--text-secondary)", marginBottom: 4 }}>
              {selectedPoint.scoring_timestamp}
            </div>
            
            <div style={{ display: "flex", alignItems: "baseline", gap: 16, marginBottom: 8 }}>
              <div className="font-data" style={{ fontSize: 48, fontWeight: 700, color: bandColor(selectedPoint.risk_band), lineHeight: 1, letterSpacing: "-0.02em" }}>
                {selectedPoint.risk_score.toFixed(4)}
              </div>
            </div>
            
            <div className={`font-data risk-badge ${selectedPoint.risk_band.toLowerCase()}`} style={{ display: "inline-block", fontSize: 11, padding: "4px 12px", marginBottom: 24 }}>
              {selectedPoint.risk_band} RISK
            </div>
            
            <button 
              className="btn btn-primary font-data"
              onClick={onNavigateToEvidence}
              style={{ width: "100%", justifyContent: "space-between" }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <Activity size={14} /> VIEW EVIDENCE
              </div>
              <ArrowRight size={14} />
            </button>
          </div>

          {/* What Changed Panel */}
          {previousPoint ? (
            <div style={{ padding: 24, border: "1px solid var(--border-default)" }}>
              <div className="font-data" style={{ fontSize: 10, color: "var(--text-muted)", letterSpacing: "0.1em", marginBottom: 24 }}>
                WHAT CHANGED?
              </div>
              
              <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", borderBottom: "1px solid var(--border-subtle)", paddingBottom: 12 }}>
                  <span className="font-ui" style={{ fontSize: 14, color: "var(--text-primary)", fontWeight: 500 }}>Risk Score</span>
                  <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                    <span className="font-data" style={{ fontSize: 12, color: "var(--text-muted)" }}>{previousPoint.risk_score.toFixed(4)} →</span>
                    <span className="font-data" style={{ fontSize: 14, fontWeight: 700, color: scoreDelta > 0 ? "var(--risk-high-text)" : "var(--risk-low-text)" }}>
                      {scoreDelta > 0 ? "+" : "-"}{absScoreDelta.toFixed(4)}
                    </span>
                  </div>
                </div>

                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", borderBottom: "1px solid var(--border-subtle)", paddingBottom: 12 }}>
                  <span className="font-ui" style={{ fontSize: 14, color: "var(--text-primary)", fontWeight: 500 }}>Evidence Signals</span>
                  <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                    <span className="font-data" style={{ fontSize: 12, color: "var(--text-muted)" }}>{Object.keys(previousPoint.evidence_features).length} →</span>
                    <span className="font-data" style={{ fontSize: 14, fontWeight: 700, color: "var(--text-primary)" }}>
                      {evidenceCountDelta > 0 ? "+" : ""}{evidenceCountDelta}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div style={{ padding: 24, border: "1px dashed var(--border-default)", color: "var(--text-muted)" }}>
              <div className="font-data" style={{ fontSize: 10, letterSpacing: "0.1em", marginBottom: 8 }}>WHAT CHANGED?</div>
              <div className="font-ui" style={{ fontSize: 13, fontStyle: "italic" }}>No preceding point available for comparison.</div>
            </div>
          )}

        </div>
      </div>
    </div>
  );
}
