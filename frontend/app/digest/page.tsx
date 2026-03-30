"use client";

import { useEffect, useState } from "react";
import Sidebar from "@/components/Sidebar";
import { getDigest, DigestOut } from "@/lib/api";

const DAY_COLORS: Record<string, string> = {
  emotion: "var(--purple-border)",
  person:  "var(--blue-border)",
  theme:   "var(--teal-border)",
  habit:   "var(--amber-border)",
  neutral: "var(--border2)",
};

function addDays(isoDate: string, n: number) {
  const d = new Date(isoDate);
  d.setDate(d.getDate() + n);
  return d.toISOString().slice(0, 10);
}

export default function DigestPage() {
  const [weekDate, setWeekDate] = useState<string>(new Date().toISOString().slice(0, 10));
  const [digest, setDigest] = useState<DigestOut | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    getDigest(weekDate)
      .then(setDigest)
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

        {!loading && digest && (
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
              {/* Bar chart */}
              <div style={{ flex: 2, background: "var(--bg2)", border: "1px solid var(--border)", borderRadius: 12, padding: 14 }}>
                <div style={{ fontSize: 11, color: "var(--text2)", fontWeight: 500, marginBottom: 12 }}>Emotion intensity by day</div>
                <div style={{ display: "flex", gap: 6, alignItems: "flex-end", height: 90 }}>
                  {digest.days.map((d) => {
                    const pct = maxCount > 0 ? (d.count / maxCount) * 100 : 0;
                    return (
                      <div key={d.day} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", gap: 4 }}>
                        <div
                          style={{
                            width: "100%",
                            height: `${pct}%`,
                            minHeight: pct > 0 ? 4 : 0,
                            background: DAY_COLORS[d.dominant_type] ?? "var(--border2)",
                            borderRadius: "3px 3px 0 0",
                            transition: "height .3s",
                          }}
                        />
                        <div style={{ fontSize: 8, color: "var(--text3)" }}>{d.day}</div>
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
