"use client";

import { useEffect, useState } from "react";
import Sidebar from "@/components/Sidebar";
import NodeChip from "@/components/NodeChip";
import { getEntries, deleteEntry, audioUrl, EntryOut } from "@/lib/api";

export default function HistoryPage() {
  const [entries, setEntries] = useState<EntryOut[]>([]);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    getEntries()
      .then(setEntries)
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const handleDelete = async (id: string) => {
    if (!confirm("Delete this entry?")) return;
    await deleteEntry(id);
    setEntries((prev) => prev.filter((e) => e.id !== id));
  };

  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      <Sidebar />

      <main style={{ flex: 1, display: "flex", flexDirection: "column" }}>
        {/* Header */}
        <div style={{ height: 44, borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", padding: "0 18px", background: "var(--bg)", flexShrink: 0 }}>
          <span style={{ fontSize: 14, fontWeight: 500, color: "var(--text)" }}>History</span>
        </div>

        <div style={{ flex: 1, overflowY: "auto", padding: "16px 24px", maxWidth: 720, width: "100%" }}>
          {loading && <div style={{ color: "var(--text3)", fontSize: 13 }}>Loading…</div>}

          {!loading && entries.length === 0 && (
            <div style={{ color: "var(--text3)", fontSize: 13 }}>
              No entries yet. <a href="/record" style={{ color: "var(--teal)" }}>Record your first one →</a>
            </div>
          )}

          {entries.map((entry) => {
            const isOpen = expanded === entry.id;
            const date = new Date(entry.created_at);
            const dateStr = date.toLocaleDateString("en-GB", { weekday: "short", day: "numeric", month: "short", year: "numeric" });
            const timeStr = date.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" });

            return (
              <div
                key={entry.id}
                style={{
                  background: "var(--bg)",
                  border: "1px solid var(--border)",
                  borderRadius: 12,
                  marginBottom: 10,
                  overflow: "hidden",
                  transition: "border-color .15s",
                }}
              >
                {/* Summary row */}
                <div
                  onClick={() => setExpanded(isOpen ? null : entry.id)}
                  style={{
                    padding: "12px 16px",
                    cursor: "pointer",
                    display: "flex",
                    flexDirection: "column",
                    gap: 6,
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <span style={{ fontSize: 11, color: "var(--text3)" }}>{dateStr} · {timeStr}</span>
                    <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                      {entry.audio_path && (
                        <span style={{ fontSize: 10, color: "var(--teal)", background: "var(--teal-bg)", padding: "2px 7px", borderRadius: 8, border: "1px solid var(--teal-border)" }}>
                          🎙 audio
                        </span>
                      )}
                      <span style={{ fontSize: 11, color: "var(--text3)" }}>{isOpen ? "▲" : "▼"}</span>
                    </div>
                  </div>

                  {entry.transcript && (
                    <p style={{ fontSize: 13, color: "var(--text2)", lineHeight: 1.6, margin: 0 }}>
                      {isOpen ? entry.transcript : entry.transcript.slice(0, 140) + (entry.transcript.length > 140 ? "…" : "")}
                    </p>
                  )}

                  {entry.nodes.length > 0 && (
                    <div style={{ display: "flex", gap: 5, flexWrap: "wrap" }}>
                      {entry.nodes.map((n) => <NodeChip key={n.id} node={n} />)}
                    </div>
                  )}
                </div>

                {/* Expanded: audio player + delete */}
                {isOpen && (
                  <div style={{ padding: "0 16px 14px", borderTop: "1px solid var(--border)", paddingTop: 12 }}>
                    {entry.audio_path && (
                      <audio
                        controls
                        src={audioUrl(entry.audio_path)}
                        style={{ width: "100%", height: 36, marginBottom: 10 }}
                      />
                    )}
                    <button
                      onClick={() => handleDelete(entry.id)}
                      style={{
                        fontSize: 11,
                        color: "var(--coral)",
                        background: "var(--coral-bg)",
                        border: "1px solid var(--coral-border)",
                        borderRadius: 6,
                        padding: "4px 12px",
                        cursor: "pointer",
                      }}
                    >
                      Delete entry
                    </button>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </main>
    </div>
  );
}
