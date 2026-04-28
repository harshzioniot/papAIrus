"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import dynamic from "next/dynamic";
import Sidebar from "@/components/Sidebar";
import { getGraph, getEntries, GraphNode, GraphEdge, EntryOut, NodeType, NODE_TYPES } from "@/lib/api";

// react-force-graph-2d requires browser APIs — load client-side only
const ForceGraph2D = dynamic(() => import("react-force-graph-2d"), { ssr: false });

type FilterType = "all" | NodeType;
type DateRange = "month" | "all";

const TYPE_BORDER: Record<string, string> = {
  emotion:  "#5c52c2",
  person:   "#1858a0",
  theme:    "#0a8c62",
  habit:    "#b06010",
  event:    "#7a4ec2",
  place:    "#0d7a55",
  decision: "#c03060",
  outcome:  "#3070c0",
};

interface FGNode extends GraphNode {
  x?: number;
  y?: number;
}

export default function GraphPage() {
  const [graphData, setGraphData] = useState<{ nodes: FGNode[]; links: GraphEdge[] }>({ nodes: [], links: [] });
  const [allNodes, setAllNodes] = useState<FGNode[]>([]);
  const [allEdges, setAllEdges] = useState<GraphEdge[]>([]);
  const [filterType, setFilterType] = useState<FilterType>("all");
  const [dateRange, setDateRange] = useState<DateRange>("month");
  const [selected, setSelected] = useState<FGNode | null>(null);
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const [entries, setEntries] = useState<EntryOut[]>([]);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const fgRef = useRef<any>(null);

  // Configure d3 forces once the graph mounts — spread nodes out, prevent overlap
  useEffect(() => {
    const fg = fgRef.current;
    if (!fg) return;
    fg.d3Force?.("charge")?.strength(-260).distanceMax(420);
    fg.d3Force?.("link")?.distance(95);
    if (fg.d3ReheatSimulation) fg.d3ReheatSimulation();
  }, [graphData]);

  const load = useCallback(async () => {
    const since = dateRange === "month"
      ? new Date(Date.now() - 30 * 86400000).toISOString().slice(0, 10)
      : undefined;
    const data = await getGraph(filterType === "all" ? undefined : filterType, since);
    setAllNodes(data.nodes as FGNode[]);
    setAllEdges(data.edges);
    // Map edges to links using id strings
    setGraphData({
      nodes: data.nodes as FGNode[],
      links: data.edges.map((e) => ({ ...e, source: e.source, target: e.target })),
    });
  }, [filterType, dateRange]);

  useEffect(() => { load(); }, [load]);
  useEffect(() => { getEntries().then(setEntries).catch(() => {}); }, []);

  const selectedEntries = selected
    ? entries.filter((e) => e.nodes.some((n) => n.id === selected.id))
    : [];

  const connections = selected
    ? allEdges
        .filter((e) => e.source === selected.id || e.target === selected.id)
        .map((e) => {
          const otherId = e.source === selected.id ? e.target : e.source;
          const other = allNodes.find((n) => n.id === otherId);
          return other ? { node: other, weight: e.weight } : null;
        })
        .filter(Boolean) as { node: FGNode; weight: number }[]
    : [];

  const exportGraph = () => {
    const canvas = document.querySelector("canvas");
    if (!canvas) return;
    const url = canvas.toDataURL("image/png");
    const a = document.createElement("a");
    a.href = url;
    a.download = "papairus-graph.png";
    a.click();
  };

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const nodeLabel = (node: any) => (node as FGNode).name;

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const nodeCanvasObject = (rawNode: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
    const node = rawNode as FGNode & { x?: number; y?: number };
    const x = node.x ?? 0;
    const y = node.y ?? 0;
    const r = Math.max(7, Math.min(20, 7 + Math.sqrt(node.entry_count) * 3));
    const isSelected = selected?.id === node.id;
    const isHover = hoveredId === node.id;
    const baseColor = TYPE_BORDER[node.type] ?? "#999";

    // Outer glow on selected/hover — Apple-style focus halo
    if (isSelected || isHover) {
      ctx.save();
      ctx.shadowColor = baseColor;
      ctx.shadowBlur = isSelected ? 18 : 10;
      ctx.beginPath();
      ctx.arc(x, y, r, 0, 2 * Math.PI);
      ctx.fillStyle = baseColor + "22";
      ctx.fill();
      ctx.restore();
    }

    // Subtle drop shadow for depth
    ctx.save();
    ctx.shadowColor = "rgba(0,0,0,0.08)";
    ctx.shadowBlur = 4;
    ctx.shadowOffsetY = 1;
    ctx.beginPath();
    ctx.arc(x, y, r, 0, 2 * Math.PI);
    ctx.fillStyle = node.color_hex + "55";
    ctx.fill();
    ctx.restore();

    // Clean ring
    ctx.beginPath();
    ctx.arc(x, y, r, 0, 2 * Math.PI);
    ctx.strokeStyle = baseColor;
    ctx.lineWidth = isSelected ? 2.2 : 1.2;
    ctx.stroke();

    // Label — only when zoomed in enough, or for selected/hover
    const showLabel = globalScale > 1.4 || isSelected || isHover;
    if (showLabel) {
      const fontSize = Math.max(10, 11 / Math.max(0.7, globalScale));
      ctx.font = `500 ${fontSize}px Inter, -apple-system, sans-serif`;
      ctx.textAlign = "center";
      ctx.textBaseline = "top";

      // White halo behind text for legibility
      const labelY = y + r + 4;
      ctx.lineWidth = 4;
      ctx.strokeStyle = "rgba(255,255,255,0.95)";
      ctx.strokeText(node.name, x, labelY);

      ctx.fillStyle = isSelected ? baseColor : "rgba(40,40,40,0.95)";
      ctx.fillText(node.name, x, labelY);
    }
  };

  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      <Sidebar />

      {/* Filter sidebar */}
      <aside style={{ width: 160, background: "var(--bg2)", borderRight: "1px solid var(--border)", padding: "16px 10px", display: "flex", flexDirection: "column", gap: 4, flexShrink: 0 }}>
        <div style={{ fontSize: 9, color: "var(--text3)", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: 4 }}>Filter nodes</div>
        {(["all", ...NODE_TYPES] as FilterType[]).map((t) => (
          <button
            key={t}
            onClick={() => setFilterType(t)}
            style={{
              padding: "4px 8px",
              borderRadius: 6,
              fontSize: 11,
              background: filterType === t ? "var(--teal-bg)" : "transparent",
              border: `1px solid ${filterType === t ? "var(--teal-border)" : "var(--border)"}`,
              color: filterType === t ? "var(--teal)" : "var(--text2)",
              cursor: "pointer",
              fontWeight: filterType === t ? 500 : 400,
              textAlign: "left",
            }}
          >
            {t === "all" ? "All types" : t.charAt(0).toUpperCase() + t.slice(1) + "s"}
          </button>
        ))}

        <div style={{ fontSize: 9, color: "var(--text3)", textTransform: "uppercase", letterSpacing: "0.08em", marginTop: 12, marginBottom: 4 }}>Date range</div>
        {(["month", "all"] as DateRange[]).map((r) => (
          <button
            key={r}
            onClick={() => setDateRange(r)}
            style={{
              padding: "4px 8px",
              borderRadius: 6,
              fontSize: 11,
              background: dateRange === r ? "var(--teal-bg)" : "transparent",
              border: `1px solid ${dateRange === r ? "var(--teal-border)" : "var(--border)"}`,
              color: dateRange === r ? "var(--teal)" : "var(--text2)",
              cursor: "pointer",
              fontWeight: dateRange === r ? 500 : 400,
              textAlign: "left",
            }}
          >
            {r === "month" ? "This month" : "All time"}
          </button>
        ))}
      </aside>

      {/* Main */}
      <main style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
        {/* Toolbar */}
        <div style={{ height: 44, borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", padding: "0 18px", justifyContent: "space-between", flexShrink: 0, background: "var(--bg)" }}>
          <span style={{ fontSize: 14, fontWeight: 500, color: "var(--text)" }}>Knowledge graph</span>
          <div style={{ display: "flex", gap: 8 }}>
            <button onClick={() => fgRef.current?.zoom(1.5, 300)} style={toolBtn}>zoom +</button>
            <button onClick={() => fgRef.current?.zoom(0.7, 300)} style={toolBtn}>zoom −</button>
            <button onClick={() => fgRef.current?.zoomToFit(400)} style={toolBtn}>reset</button>
            <button onClick={exportGraph} style={{ ...toolBtn, background: "var(--teal-bg)", border: "1px solid var(--teal-border)", color: "var(--teal)" }}>export</button>
          </div>
        </div>

        {/* Graph canvas + detail panel */}
        <div style={{ flex: 1, display: "flex", gap: 14, padding: 16, overflow: "hidden", background: "var(--app-bg)" }}>
          {/* Graph */}
          <div style={{ flex: 1, borderRadius: 12, overflow: "hidden", background: "var(--bg2)", border: "1px solid var(--border)" }}>
            <ForceGraph2D
              ref={fgRef as never}
              graphData={graphData}
              nodeLabel={nodeLabel}
              nodeCanvasObject={nodeCanvasObject as never}
              nodeCanvasObjectMode={() => "replace"}
              nodeRelSize={6}
              linkColor={() => "rgba(140,140,140,0.18)"}
              linkWidth={(link: unknown) => 0.6 + Math.sqrt((link as GraphEdge).weight) * 0.5}
              linkDirectionalParticles={(link: unknown) =>
                selected && ((link as GraphEdge).source === selected.id || (link as GraphEdge).target === selected.id) ? 2 : 0
              }
              linkDirectionalParticleSpeed={0.006}
              linkDirectionalParticleWidth={2}
              linkDirectionalParticleColor={() => "rgba(40,140,100,0.7)"}
              cooldownTicks={120}
              warmupTicks={60}
              d3AlphaDecay={0.02}
              d3VelocityDecay={0.35}
              onNodeClick={(node: unknown) => setSelected(node as FGNode)}
              onNodeHover={(node: unknown) => setHoveredId((node as FGNode | null)?.id ?? null)}
              backgroundColor="transparent"
              width={undefined}
              height={undefined}
            />
          </div>

          {/* Detail panel */}
          <div style={{ width: 200, display: "flex", flexDirection: "column", gap: 8 }}>
            {selected ? (
              <>
                <div style={{ fontSize: 10, color: "var(--text3)", fontWeight: 500, textTransform: "uppercase", letterSpacing: "0.07em" }}>Selected node</div>
                <div style={{ background: "var(--teal-bg)", border: "1px solid var(--teal-border)", borderRadius: 12, padding: "12px 14px" }}>
                  <div style={{ fontSize: 17, fontWeight: 600, color: "var(--teal)", marginBottom: 2 }}>{selected.name}</div>
                  <div style={{ fontSize: 11, color: "var(--teal2)" }}>{selected.type} · {connections.length} connections</div>
                  <div style={{ display: "flex", gap: 10, marginTop: 8 }}>
                    <div><div style={{ fontSize: 18, fontWeight: 600, color: "var(--teal)" }}>{selected.entry_count}</div><div style={{ fontSize: 9, color: "var(--teal2)" }}>entries</div></div>
                    <div><div style={{ fontSize: 18, fontWeight: 600, color: "var(--teal)" }}>{connections.length}</div><div style={{ fontSize: 9, color: "var(--teal2)" }}>connections</div></div>
                  </div>
                </div>

                {connections.length > 0 && (
                  <>
                    <div style={{ fontSize: 10, color: "var(--text3)", fontWeight: 500, textTransform: "uppercase", letterSpacing: "0.07em" }}>Connections</div>
                    {connections.slice(0, 5).map(({ node, weight }) => (
                      <div key={node.id} style={{ background: "var(--bg2)", border: "1px solid var(--border)", borderRadius: 8, padding: "7px 10px", display: "flex", alignItems: "center", gap: 8 }}>
                        <span style={{ width: 8, height: 8, borderRadius: "50%", background: TYPE_BORDER[node.type] ?? "#999", flexShrink: 0, display: "inline-block" }} />
                        <div>
                          <div style={{ fontSize: 11, fontWeight: 500, color: "var(--text)" }}>{node.name}</div>
                          <div style={{ fontSize: 9, color: "var(--text3)" }}>{node.type} · {weight} co-occurrences</div>
                        </div>
                      </div>
                    ))}
                  </>
                )}

                {selectedEntries.length > 0 && (
                  <>
                    <div style={{ fontSize: 10, color: "var(--text3)", fontWeight: 500, textTransform: "uppercase", letterSpacing: "0.07em" }}>Entries mentioning this</div>
                    <div style={{ background: "var(--bg2)", border: "1px solid var(--border)", borderRadius: 8, padding: "6px 10px", fontSize: 10, color: "var(--text2)" }}>
                      {selectedEntries.slice(0, 5).map((e) => new Date(e.created_at).toLocaleDateString("en-GB", { day: "numeric", month: "short" })).join(" · ")}
                      {selectedEntries.length > 5 ? ` · +${selectedEntries.length - 5} more` : ""}
                    </div>
                  </>
                )}

                <button
                  onClick={() => setSelected(null)}
                  style={{ fontSize: 10, color: "var(--text3)", background: "none", border: "none", cursor: "pointer", textAlign: "left" }}
                >
                  ← deselect
                </button>
              </>
            ) : (
              <div style={{ fontSize: 12, color: "var(--text3)", marginTop: 8 }}>Click a node to explore</div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

const toolBtn: React.CSSProperties = {
  height: 26,
  borderRadius: 8,
  background: "var(--bg2)",
  border: "1px solid var(--border)",
  fontSize: 11,
  color: "var(--text2)",
  padding: "0 12px",
  cursor: "pointer",
};
