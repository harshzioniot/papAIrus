"use client";

import { useEffect, useState } from "react";
import Sidebar from "@/components/Sidebar";
import { getDigest, DigestOut } from "@/lib/api";

// Lexical polarity map — covers the emotion vocabulary the LLM commonly produces.
// +1 = positive, -1 = negative, 0 = neutral / ambiguous.
const EMOTION_POLARITY: Record<string, number> = {
  joy: 1, relief: 1, calm: 1, content: 1, contentment: 1, gratitude: 1,
  hope: 1, hopeful: 1, pride: 1, love: 1, excitement: 1, excited: 1,
  satisfaction: 1, peace: 1, peaceful: 1, optimism: 1, ease: 1,
  happy: 1, happiness: 1, grateful: 1, lighter: 1, motivated: 1,
  anxiety: -1, anxious: -1, fear: -1, afraid: -1, sadness: -1, sad: -1,
  anger: -1, angry: -1, frustration: -1, frustrated: -1, stress: -1,
  stressed: -1, worry: -1, worried: -1, dread: -1, shame: -1, guilt: -1,
  loneliness: -1, lonely: -1, exhaustion: -1, exhausted: -1, drained: -1,
  overwhelm: -1, overwhelmed: -1, grief: -1, despair: -1, regret: -1,
  surprise: 0, surprised: 0, curiosity: 0, neutral: 0,
};

function polarityOf(name: string): number {
  const key = name.toLowerCase().trim();
  if (key in EMOTION_POLARITY) return EMOTION_POLARITY[key];
  // Substring fallback for compound names like "quiet anxiety", "deep relief"
  for (const [k, v] of Object.entries(EMOTION_POLARITY)) {
    if (key.includes(k)) return v;
  }
  return 0;
}

function addDays(isoDate: string, n: number) {
  const d = new Date(isoDate);
  d.setDate(d.getDate() + n);
  return d.toISOString().slice(0, 10);
}

export default function DigestPage() {
  const [weekDate, setWeekDate] = useState<string>(new Date().toISOString().slice(0, 10));
  const [digest, setDigest] = useState<DigestOut | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    getDigest(weekDate)
      .then(setDigest)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [weekDate]);

  const prevWeek = () => setWeekDate((d) => addDays(d, -7));
  const nextWeek = () => setWeekDate((d) => addDays(d, 7));

  const maxCount = digest ? Math.max(...digest.days.map((d) => d.count), 1) : 1;

  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      <Sidebar />

      <main style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
        {/* Top nav */}
        <div style={{ height: 44, borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", padding: "0 18px", justifyContent: "space-between", background: "var(--bg)", flexShrink: 0 }}>
          <span style={{ fontSize: 14, fontWeight: 500, color: "var(--text)" }}>
            Weekly digest{digest ? ` — ${digest.week_start} – ${digest.week_end}` : ""}
          </span>
          <div style={{ display: "flex", gap: 8 }}>
            <button onClick={prevWeek} style={navBtn}>← prev week</button>
            <button onClick={nextWeek} style={navBtn}>next week →</button>
          </div>
        </div>

        {loading && (
          <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", color: "var(--text3)", fontSize: 13 }}>Loading…</div>
        )}

        {!loading && error && (
          <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", color: "var(--coral, #f87171)", fontSize: 13 }}>
            {error}
          </div>
        )}

        {!loading && !error && digest && (
          <div style={{ flex: 1, padding: 16, overflowY: "auto", display: "flex", flexDirection: "column", gap: 10 }}>
            {/* Stat cards */}
            <div style={{ display: "flex", gap: 8 }}>
              <StatCard
                label="top emotion"
                value={digest.top_emotion ?? "—"}
                sub={digest.top_emotion ? `${digest.top_emotion_count}× this week` : "no data"}
                highlight
              />
              <StatCard
                label="mood trend"
                value={`${digest.mood_trend_pct >= 0 ? "↑" : "↓"} ${Math.abs(digest.mood_trend_pct)}%`}
                sub={digest.mood_trend_pct < 0 ? "vs last week" : "vs last week"}
                valueColor={digest.mood_trend_pct < -5 ? "var(--coral)" : "var(--teal)"}
              />
              <StatCard
                label="most connected"
                value={digest.most_connected_node ?? "—"}
                sub={`${digest.most_connected_count} mentions`}
                valueSize={14}
              />
              <StatCard
                label="entries this week"
                value={String(digest.entry_count)}
                sub={`best streak: ${digest.best_streak} days`}
              />
            </div>

            {/* Chart + right column */}
            <div style={{ display: "flex", gap: 10, flex: 1 }}>
              {/* Mood timeline — signed bars by emotion polarity */}
              <div style={{ flex: 2, background: "var(--bg2)", border: "1px solid var(--border)", borderRadius: 12, padding: 14 }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 14 }}>
                  <div style={{ fontSize: 11, color: "var(--text2)", fontWeight: 500 }}>Mood by day</div>
                  <div style={{ display: "flex", gap: 12, fontSize: 9, color: "var(--text3)" }}>
                    <span style={{ display: "flex", alignItems: "center", gap: 4 }}>
                      <span style={{ width: 8, height: 8, borderRadius: 2, background: "var(--teal)" }} /> positive
                    </span>
                    <span style={{ display: "flex", alignItems: "center", gap: 4 }}>
                      <span style={{ width: 8, height: 8, borderRadius: 2, background: "var(--coral)" }} /> negative
                    </span>
                    <span style={{ display: "flex", alignItems: "center", gap: 4 }}>
                      <span style={{ width: 8, height: 8, borderRadius: 2, background: "var(--border2)" }} /> none
                    </span>
                  </div>
                </div>

                <div style={{ display: "flex", gap: 6, alignItems: "stretch", height: 130, position: "relative" }}>
                  {/* Zero line */}
                  <div style={{
                    position: "absolute",
                    left: 0, right: 0,
                    top: "50%",
                    height: 1,
                    background: "var(--border)",
                    pointerEvents: "none",
                  }} />

                  {digest.days.map((d) => {
                    const polarity = d.count > 0 ? polarityOf(d.dominant_type) : 0;
                    const pct = maxCount > 0 ? (d.count / maxCount) * 50 : 0; // half-height max
                    const isPositive = polarity > 0;
                    const isNegative = polarity < 0;
                    const barColor = isPositive ? "var(--teal)" : isNegative ? "var(--coral)" : "var(--border2)";
                    const labelColor = isPositive ? "var(--teal)" : isNegative ? "var(--coral)" : "var(--text3)";

                    return (
                      <div
                        key={d.day}
                        title={d.count > 0 ? `${d.day} ${d.date} — ${d.count} emotion mention${d.count === 1 ? "" : "s"}, dominant: ${d.dominant_type}` : `${d.day} ${d.date} — no entries`}
                        style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", position: "relative" }}
                      >
                        {/* Top half (positive) */}
                        <div style={{ flex: 1, width: "100%", display: "flex", alignItems: "flex-end", justifyContent: "center" }}>
                          {isPositive && (
                            <div style={{
                              width: "62%",
                              height: `${pct * 2}%`,
                              minHeight: 4,
                              background: barColor,
                              borderRadius: "4px 4px 0 0",
                              transition: "height .35s ease",
                            }} />
                          )}
                        </div>

                        {/* Bottom half (negative) */}
                        <div style={{ flex: 1, width: "100%", display: "flex", alignItems: "flex-start", justifyContent: "center" }}>
                          {isNegative && (
                            <div style={{
                              width: "62%",
                              height: `${pct * 2}%`,
                              minHeight: 4,
                              background: barColor,
                              borderRadius: "0 0 4px 4px",
                              transition: "height .35s ease",
                            }} />
                          )}
                          {polarity === 0 && d.count > 0 && (
                            <div style={{
                              width: "62%",
                              height: 4,
                              marginTop: -2,
                              background: barColor,
                              borderRadius: 2,
                            }} />
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* Day labels + dominant emotion name */}
                <div style={{ display: "flex", gap: 6, marginTop: 6 }}>
                  {digest.days.map((d) => {
                    const polarity = d.count > 0 ? polarityOf(d.dominant_type) : 0;
                    const labelColor = polarity > 0 ? "var(--teal)" : polarity < 0 ? "var(--coral)" : "var(--text3)";
                    return (
                      <div key={d.day} style={{ flex: 1, textAlign: "center", lineHeight: 1.3 }}>
                        <div style={{ fontSize: 10, color: "var(--text2)", fontWeight: 500 }}>{d.day}</div>
                        <div style={{ fontSize: 9, color: labelColor, minHeight: 12, marginTop: 1, textTransform: "lowercase" }}>
                          {d.count > 0 ? d.dominant_type : ""}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Right column */}
              <div style={{ width: 190, display: "flex", flexDirection: "column", gap: 8 }}>
                {/* People */}
                <div style={{ background: "var(--bg2)", border: "1px solid var(--border)", borderRadius: 12, padding: 12 }}>
                  <div style={{ fontSize: 11, color: "var(--text2)", fontWeight: 500, marginBottom: 8 }}>People mentioned</div>
                  {digest.people.length === 0 && (
                    <div style={{ fontSize: 11, color: "var(--text3)" }}>No people tagged yet</div>
                  )}
                  {digest.people.map((p, i) => {
                    const colors = [
                      { bg: "var(--purple-bg)", border: "var(--purple-border)", color: "var(--purple)" },
                      { bg: "var(--teal-bg)", border: "var(--teal-border)", color: "var(--teal)" },
                      { bg: "var(--amber-bg)", border: "var(--amber-border)", color: "var(--amber)" },
                    ];
                    const c = colors[i % colors.length];
                    return (
                      <div key={p.name} style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
                        <div style={{ width: 26, height: 26, borderRadius: "50%", background: c.bg, border: `1px solid ${c.border}`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 10, color: c.color, fontWeight: 600, flexShrink: 0 }}>
                          {p.name[0].toUpperCase()}
                        </div>
                        <span style={{ fontSize: 11, fontWeight: 500, flex: 1, color: "var(--text)" }}>{p.name}</span>
                        <span style={{ fontSize: 10, color: "var(--text3)" }}>{p.count}×</span>
                      </div>
                    );
                  })}
                </div>

                {/* Reflection */}
                <div style={{ background: "var(--purple-bg)", border: "1px solid var(--purple-border)", borderRadius: 12, padding: 14, marginTop: "auto" }}>
                  <div style={{ fontSize: 9, color: "var(--purple)", textTransform: "uppercase", letterSpacing: "0.08em", fontWeight: 600, marginBottom: 7 }}>papAIrus asks</div>
                  <div className="serif" style={{ fontSize: 14, color: "var(--purple)", lineHeight: 1.55 }}>{digest.reflection}</div>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

function StatCard({ label, value, sub, highlight, valueColor, valueSize }: {
  label: string; value: string; sub: string;
  highlight?: boolean; valueColor?: string; valueSize?: number;
}) {
  return (
    <div style={{
      flex: 1,
      background: highlight ? "var(--teal-bg)" : "var(--bg2)",
      border: `1px solid ${highlight ? "var(--teal-border)" : "var(--border)"}`,
      borderRadius: 8,
      padding: "10px 12px",
    }}>
      <div style={{ fontSize: 10, color: highlight ? "var(--teal2)" : "var(--text3)", marginBottom: 4 }}>{label}</div>
      <div style={{ fontSize: valueSize ?? 20, fontWeight: 600, color: valueColor ?? (highlight ? "var(--teal)" : "var(--text)"), paddingTop: valueSize ? 2 : 0 }}>{value}</div>
      <div style={{ fontSize: 10, color: highlight ? "var(--teal2)" : "var(--text3)", marginTop: 2 }}>{sub}</div>
    </div>
  );
}

const navBtn: React.CSSProperties = {
  height: 26,
  borderRadius: 8,
  background: "var(--bg2)",
  border: "1px solid var(--border)",
  fontSize: 11,
  color: "var(--text2)",
  padding: "0 12px",
  cursor: "pointer",
};
