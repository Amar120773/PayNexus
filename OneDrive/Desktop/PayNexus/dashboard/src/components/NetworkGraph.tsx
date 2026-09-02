"use client";

import { useMemo, useState, useCallback, useRef, useEffect } from "react";
import { 
  ReactFlow, 
  Controls, 
  Background, 
  Node, 
  Edge,
  useReactFlow,
  ReactFlowProvider,
  Panel
} from "@xyflow/react";
import '@xyflow/react/dist/style.css';
import { NetworkScoreResult, ScoreResult, getNetworkScore } from "@/lib/api";
import { useRouter } from "next/navigation";
import { ShieldAlert, ArrowRight, CornerUpLeft, Network, Plus, AlertTriangle } from "lucide-react";

type NetworkGraphProps = {
  centralMerchantId: string;
  centralNodeData?: ScoreResult | null;
  networkData: NetworkScoreResult | null;
  selectedTimestamp?: string;
  loading: boolean;
};

// Layout constants
const GRAPH_WIDTH = 800;
const GRAPH_HEIGHT = 600;
const MAX_NODES = 50;

function NetworkGraphCore({ centralMerchantId, centralNodeData, networkData, selectedTimestamp, loading }: NetworkGraphProps) {
  const router = useRouter();
  const { fitView } = useReactFlow();
  const [selectedNode, setSelectedNode] = useState<ScoreResult | null>(null);

  // Graph Pivoting State
  const [expandedData, setExpandedData] = useState<{ nodes: Node[], edges: Edge[] }>({ nodes: [], edges: [] });
  const [isPivoting, setIsPivoting] = useState(false);
  const [pivotError, setPivotError] = useState<string | null>(null);
  const [expandedMerchantIds, setExpandedMerchantIds] = useState<Set<string>>(new Set());

  // Reset expanded data when root network changes
  useEffect(() => {
    setExpandedData({ nodes: [], edges: [] });
    setExpandedMerchantIds(new Set());
    setPivotError(null);
    setSelectedNode(null);
  }, [networkData]);

  const { nodes, edges, highRiskCount } = useMemo(() => {
    if (!networkData || networkData.results.length === 0) return { nodes: [], edges: [], highRiskCount: 0 };

    const newNodes: Node[] = [];
    const newEdges: Edge[] = [];
    let hrCount = 0;

    // Central Node 
    newNodes.push({
      id: centralMerchantId,
      position: { x: GRAPH_WIDTH / 2 - 50, y: GRAPH_HEIGHT / 2 - 50 },
      data: {
        label: (
          <div style={{ display: "flex", flexDirection: "column", gap: 4, alignItems: "center" }}>
            <span style={{ fontSize: 9, textTransform: "uppercase", letterSpacing: "0.1em", color: "var(--brand)" }}>TARGET</span>
            <span className="font-data" style={{ fontSize: 13, fontWeight: 800 }}>{centralMerchantId}</span>
            {centralNodeData && (
              <span className={`risk-badge ${centralNodeData.risk_band.toLowerCase()}`} style={{ fontSize: 9, padding: "2px 6px" }}>
                {centralNodeData.risk_band}
              </span>
            )}
          </div>
        )
      },
      style: {
        background: 'var(--bg-surface)',
        color: 'var(--text-primary)',
        border: '3px solid var(--brand)',
        borderRadius: '50%',
        width: 100,
        height: 100,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        boxShadow: 'var(--shadow-md)',
      },
    });

    // Neighbors
    const neighbors = networkData.results.filter(r => r.merchant_id !== centralMerchantId);
    const radius = Math.max(160, neighbors.length * 40);
    
    neighbors.forEach((neighbor, i) => {
      const angle = (i / (neighbors.length || 1)) * 2 * Math.PI;
      const x = (GRAPH_WIDTH / 2) + radius * Math.cos(angle) - 40;
      const y = (GRAPH_HEIGHT / 2) + radius * Math.sin(angle) - 30;
      
      let borderStrong = 'var(--risk-low)';
      
      if (neighbor.risk_band === 'MEDIUM') borderStrong = 'var(--risk-medium)';
      if (neighbor.risk_band === 'HIGH') {
        borderStrong = 'var(--risk-high)';
        hrCount++;
      }

      newNodes.push({
        id: neighbor.merchant_id,
        position: { x, y },
        data: {
          risk_band: neighbor.risk_band,
          risk_score: neighbor.risk_score,
          label: (
            <div style={{ display: "flex", flexDirection: "column", gap: 2, alignItems: "center" }}>
              <span className="font-data" style={{ fontSize: 11, fontWeight: 700 }}>{neighbor.merchant_id}</span>
              <span className="font-data" style={{ fontSize: 9, color: "var(--text-muted)", fontVariantNumeric: "tabular-nums" }}>{neighbor.risk_score.toFixed(4)}</span>
            </div>
          )
        },
        style: {
          background: 'var(--bg-surface)',
          color: 'var(--text-primary)',
          border: `2px solid ${borderStrong}`,
          borderRadius: 'var(--radius-lg)',
          width: 90,
          height: 50,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          cursor: 'pointer',
          boxShadow: 'var(--shadow-sm)',
        },
      });

      newEdges.push({
        id: `e-${centralMerchantId}-${neighbor.merchant_id}`,
        source: centralMerchantId,
        target: neighbor.merchant_id,
        animated: false,
        style: { stroke: 'var(--border-strong)', strokeWidth: 1.5 },
      });
    });

    // Merge expanded data
    const existingNodeIds = new Set(newNodes.map(n => n.id));
    const existingEdgeIds = new Set(newEdges.map(e => e.id));
    
    expandedData.nodes.forEach(n => {
      if (!existingNodeIds.has(n.id)) {
        newNodes.push(n);
        existingNodeIds.add(n.id);
        if (n.data.risk_band === 'HIGH') hrCount++;
      }
    });
    
    expandedData.edges.forEach(e => {
      if (!existingEdgeIds.has(e.id)) {
        newEdges.push(e);
        existingEdgeIds.add(e.id);
      }
    });

    return { nodes: newNodes, edges: newEdges, highRiskCount: hrCount };
  }, [networkData, centralMerchantId, centralNodeData, expandedData]);

  const handlePivot = useCallback(async () => {
    if (!selectedNode || !selectedTimestamp) return;
    
    if (nodes.length >= MAX_NODES) {
      setPivotError(`Safety cap of ${MAX_NODES} nodes reached. Pivot disabled to maintain visual performance.`);
      return;
    }
    
    setIsPivoting(true);
    setPivotError(null);
    
    try {
      const res = await getNetworkScore(selectedNode.merchant_id, selectedTimestamp);
      
      const newNodes: Node[] = [];
      const newEdges: Edge[] = [];
      
      const neighbors = res.results.filter(r => r.merchant_id !== selectedNode.merchant_id);
      const baseNode = nodes.find(n => n.id === selectedNode.merchant_id);
      const baseX = baseNode?.position.x || GRAPH_WIDTH / 2;
      const baseY = baseNode?.position.y || GRAPH_HEIGHT / 2;
      
      const radius = Math.max(120, neighbors.length * 30);
      
      neighbors.forEach((neighbor, i) => {
        const angle = (i / (neighbors.length || 1)) * 2 * Math.PI;
        // Jitter to prevent exact overlap
        const x = baseX + radius * Math.cos(angle) + (Math.random() * 20 - 10) - 40;
        const y = baseY + radius * Math.sin(angle) + (Math.random() * 20 - 10) - 30;
        
        let borderStrong = 'var(--risk-low)';
        if (neighbor.risk_band === 'MEDIUM') borderStrong = 'var(--risk-medium)';
        if (neighbor.risk_band === 'HIGH') borderStrong = 'var(--risk-high)';

        newNodes.push({
          id: neighbor.merchant_id,
          position: { x, y },
          data: {
            risk_band: neighbor.risk_band,
            risk_score: neighbor.risk_score,
            label: (
              <div style={{ display: "flex", flexDirection: "column", gap: 2, alignItems: "center" }}>
                <span className="font-data" style={{ fontSize: 11, fontWeight: 700 }}>{neighbor.merchant_id}</span>
                <span className="font-data" style={{ fontSize: 9, color: "var(--text-muted)", fontVariantNumeric: "tabular-nums" }}>{neighbor.risk_score.toFixed(4)}</span>
              </div>
            )
          },
          style: {
            background: 'var(--bg-surface)',
            color: 'var(--text-primary)',
            border: `2px solid ${borderStrong}`,
            borderRadius: 'var(--radius-lg)',
            width: 90,
            height: 50,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            cursor: 'pointer',
            boxShadow: '0 0 0 1px var(--bg-surface), 0 0 0 3px var(--brand-accent)', 
          },
        });

        newEdges.push({
          id: `e-${selectedNode.merchant_id}-${neighbor.merchant_id}`,
          source: selectedNode.merchant_id,
          target: neighbor.merchant_id,
          animated: false,
          style: { stroke: 'var(--border-strong)', strokeWidth: 1.5, strokeDasharray: '4 4' }, 
        });
      });
      
      setExpandedData(prev => ({
        nodes: [...prev.nodes, ...newNodes],
        edges: [...prev.edges, ...newEdges]
      }));
      setExpandedMerchantIds(prev => new Set(prev).add(selectedNode.merchant_id));
      
      // Auto-fit view after expansion
      setTimeout(() => fitView({ duration: 800, padding: 0.2 }), 100);
      
    } catch (e: any) {
      setPivotError("Failed to expand network graph. API error.");
    } finally {
      setIsPivoting(false);
    }
  }, [selectedNode, selectedTimestamp, nodes, fitView]);

  const onNodeClick = useCallback((_: any, node: Node) => {
    // If it's the target node, clear selection
    if (node.id === centralMerchantId) {
      setSelectedNode(null);
      return;
    }
    
    // We need to find the full data for the clicked node. It could be in root networkData OR expandedData
    const res = networkData?.results.find(r => r.merchant_id === node.id);
    if (res) {
      setSelectedNode(res);
    } else {
      // Reconstruct from expanded node state since API type is required
      const d = node.data;
      if (d && d.risk_band) {
        setSelectedNode({
          merchant_id: node.id,
          scoring_timestamp: selectedTimestamp || "",
          risk_score: (d.risk_score as number) || 0,
          risk_band: (d.risk_band as any) || "LOW",
          probability: 0,
          behavioral_risk: 0,
          network_risk: 0,
          evidence_features: {}
        });
      }
    }
  }, [networkData, centralMerchantId, selectedTimestamp]);

  if (loading) {
    return (
      <div style={{ padding: 48, textAlign: "center", border: "1px dashed var(--border-default)", color: "var(--text-disabled)" }}>
        <Network className="animate-pulse" size={32} style={{ margin: "0 auto 16px" }} />
        <div className="font-data" style={{ fontSize: 11, letterSpacing: "0.1em" }}>BUILDING NETWORK...</div>
      </div>
    );
  }

  if (!networkData || networkData.results.length <= 1) {
    return (
      <div style={{ padding: 64, textAlign: "center", border: "1px dashed var(--border-default)", background: "var(--bg-subtle)", borderRadius: "var(--radius-lg)" }}>
        <ShieldAlert size={32} style={{ color: "var(--text-disabled)", margin: "0 auto 16px" }} />
        <h3 className="font-poppins-sub" style={{ fontSize: 20, color: "var(--text-primary)", marginBottom: 8 }}>
          NO CONNECTED ENTITIES OBSERVED
        </h3>
        <p className="font-ui" style={{ fontSize: 14, color: "var(--text-muted)", maxWidth: 400, margin: "0 auto" }}>
          The inference API did not find any 1-hop relationships within the dataset timeframe.
        </p>
      </div>
    );
  }

  return (
    <div className="animate-fade-in" style={{ display: "flex", flexDirection: "column", gap: 32 }}>
      
      {/* ── HERO ── */}
      <div>
        <div className="font-data" style={{ fontSize: 11, color: "var(--text-muted)", letterSpacing: "0.1em", marginBottom: 12 }}>
          NETWORK INTELLIGENCE
        </div>
        <h2 className="font-poppins-sub" style={{ fontSize: 40, color: "var(--text-primary)", margin: "0 0 8px" }}>
          Structural Intelligence
        </h2>
        <p className="font-ui" style={{ fontSize: 16, color: "var(--text-secondary)", margin: 0 }}>
          Explore the relationships surrounding this merchant.
        </p>
      </div>

      {/* ── METADATA ── */}
      <div style={{ display: "flex", gap: 32, flexWrap: "wrap", padding: 24, border: "1px solid var(--border-default)", background: "var(--bg-subtle)", borderRadius: "var(--radius-md)" }}>
        <div>
          <div className="font-data" style={{ fontSize: 10, color: "var(--text-muted)", letterSpacing: "0.1em", marginBottom: 4 }}>TOTAL ENTITIES</div>
          <div className="font-data" style={{ fontSize: 24, fontWeight: 700, color: "var(--text-primary)" }}>{nodes.length - 1}</div>
        </div>
        <div>
          <div className="font-data" style={{ fontSize: 10, color: "var(--text-muted)", letterSpacing: "0.1em", marginBottom: 4 }}>HIGH-RISK ENTITIES</div>
          <div className="font-data" style={{ fontSize: 24, fontWeight: 700, color: highRiskCount > 0 ? "var(--risk-high-text)" : "var(--text-primary)" }}>{highRiskCount}</div>
        </div>
        <div>
          <div className="font-data" style={{ fontSize: 10, color: "var(--text-muted)", letterSpacing: "0.1em", marginBottom: 4 }}>PIVOTS PERFORMED</div>
          <div className="font-data" style={{ fontSize: 24, fontWeight: 700, color: "var(--text-secondary)" }}>{expandedMerchantIds.size}</div>
        </div>
      </div>

      {/* ── GRAPH WORKSPACE ── */}
      <div style={{ display: "flex", flexWrap: "wrap", gap: 32, alignItems: "flex-start" }}>
        
        {/* Canvas */}
        <div style={{ flex: "1 1 600px", height: 760, border: "1px solid var(--border-strong)", background: "var(--bg-surface)", borderRadius: "var(--radius-lg)", overflow: "hidden", position: "relative" }}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodeClick={onNodeClick}
            fitView
            nodesConnectable={false}
            nodesDraggable={true}
            elementsSelectable={true}
          >
            <Background color="var(--border-default)" gap={24} size={1} />
            <Controls 
              showInteractive={false} 
              style={{
                backgroundColor: 'var(--bg-surface)',
                border: '1px solid var(--border-default)',
                borderRadius: 'var(--radius-md)',
                boxShadow: 'var(--shadow-sm)'
              }}
            />
            
            <Panel position="bottom-left" style={{ margin: 16 }}>
              <div style={{ background: "var(--bg-surface)", border: "1px solid var(--border-subtle)", padding: "16px 20px", borderRadius: "var(--radius-md)", boxShadow: "var(--shadow-sm)" }}>
                <div className="font-data" style={{ fontSize: 10, color: "var(--text-muted)", letterSpacing: "0.1em", marginBottom: 12 }}>LEGEND</div>
                <div style={{ display: 'flex', flexDirection: "column", gap: 8, fontSize: 11, fontWeight: 500, color: 'var(--text-secondary)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <div style={{ width: 14, height: 14, borderRadius: '50%', border: '2px solid var(--brand)' }} />
                    Target Merchant
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <div style={{ width: 14, height: 14, borderRadius: '4px', border: '2px solid var(--risk-high)' }} />
                    High Risk Entity
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <div style={{ width: 14, height: 14, borderRadius: '4px', border: '2px solid var(--risk-low)' }} />
                    Low Risk Entity
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <div style={{ width: 14, height: 14, borderRadius: '4px', border: '2px solid var(--brand-accent)' }} />
                    Pivoted Discovery
                  </div>
                </div>
              </div>
            </Panel>
          </ReactFlow>
        </div>

        {/* Node Inspector */}
        <div style={{ flex: "0 0 340px", minWidth: 340, maxWidth: "100%" }}>
          {selectedNode ? (
            <div className="animate-fade-in" style={{ padding: 32, background: "var(--bg-surface)", border: "1px solid var(--border-strong)", borderRadius: "var(--radius-lg)", boxShadow: "var(--shadow-md)", position: "sticky", top: 24 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 24 }}>
                <div>
                  <div className="font-data" style={{ fontSize: 10, color: "var(--brand)", letterSpacing: "0.1em", marginBottom: 4 }}>OBSERVED ENTITY</div>
                  <h3 className="font-data" style={{ fontSize: 24, fontWeight: 800, color: "var(--text-primary)", margin: 0 }}>{selectedNode.merchant_id}</h3>
                </div>
                <button onClick={() => setSelectedNode(null)} style={{ background: "none", border: "none", cursor: "pointer", color: "var(--text-muted)" }}>✕</button>
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: 16, marginBottom: 32 }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", borderBottom: "1px solid var(--border-subtle)", paddingBottom: 8 }}>
                  <span className="font-ui" style={{ fontSize: 13, color: "var(--text-secondary)" }}>Entity Type</span>
                  <span className="font-ui" style={{ fontSize: 14, fontWeight: 500, color: "var(--text-primary)" }}>MERCHANT</span>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", borderBottom: "1px solid var(--border-subtle)", paddingBottom: 8 }}>
                  <span className="font-ui" style={{ fontSize: 13, color: "var(--text-secondary)" }}>Risk Score</span>
                  <span className="font-data" style={{ fontSize: 15, fontWeight: 700, color: "var(--text-primary)" }}>{selectedNode.risk_score.toFixed(4)}</span>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", borderBottom: "1px solid var(--border-subtle)", paddingBottom: 8 }}>
                  <span className="font-ui" style={{ fontSize: 13, color: "var(--text-secondary)" }}>Risk Band</span>
                  <span className={`risk-badge ${selectedNode.risk_band.toLowerCase()}`} style={{ fontSize: 10, padding: "2px 8px" }}>{selectedNode.risk_band} RISK</span>
                </div>
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                {!expandedMerchantIds.has(selectedNode.merchant_id) ? (
                  <button 
                    className="btn btn-secondary font-data"
                    onClick={handlePivot}
                    disabled={isPivoting}
                    style={{ width: "100%", justifyContent: "space-between", background: "var(--bg-subtle)", color: "var(--text-primary)", borderColor: "var(--border-strong)" }}
                  >
                    {isPivoting ? "EXPANDING..." : "PIVOT NETWORK"} 
                    <Plus size={14} />
                  </button>
                ) : (
                  <button 
                    className="btn font-data"
                    disabled
                    style={{ width: "100%", justifyContent: "center", background: "var(--bg-elevated)", color: "var(--text-disabled)", border: "1px dashed var(--border-default)" }}
                  >
                    NETWORK ALREADY PIVOTED
                  </button>
                )}

                <button 
                  className="btn btn-primary font-data"
                  onClick={() => router.push(`/merchant/${selectedNode.merchant_id}`)}
                  style={{ width: "100%", justifyContent: "space-between" }}
                >
                  INVESTIGATE ENTITY <ArrowRight size={14} />
                </button>
                
                {pivotError && (
                  <div style={{ display: "flex", alignItems: "center", gap: 8, padding: 12, background: "var(--danger-bg)", color: "var(--danger)", border: "1px solid var(--danger)", borderRadius: "var(--radius-sm)", fontSize: 12, marginTop: 4 }}>
                    <AlertTriangle size={14} /> {pivotError}
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div style={{ padding: 48, textAlign: "center", border: "1px dashed var(--border-default)", background: "var(--bg-subtle)", borderRadius: "var(--radius-lg)", color: "var(--text-muted)", height: "100%", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center" }}>
              <CornerUpLeft size={24} style={{ marginBottom: 16, color: "var(--text-disabled)" }} />
              <span className="font-ui" style={{ fontSize: 14 }}>Select a node in the graph to inspect its relationship.</span>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}

// Wrapper to provide ReactFlow context
export default function NetworkGraph(props: NetworkGraphProps) {
  return (
    <ReactFlowProvider>
      <NetworkGraphCore {...props} />
    </ReactFlowProvider>
  );
}
