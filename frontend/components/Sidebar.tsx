"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useTheme } from "./ThemeProvider";

const NAV = [
  { href: "/record", label: "Record", dot: "teal" },
  { href: "/graph", label: "Graph", dot: "purple" },
  { href: "/digest", label: "Digest", dot: "amber" },
  { href: "/history", label: "History", dot: "gray" },
];

const DOT_COLORS: Record<string, string> = {
  teal: "var(--teal)",
  purple: "var(--purple)",
  amber: "var(--amber)",
  gray: "var(--text3)",
};

export default function Sidebar() {
  const path = usePathname();
  const { theme, toggle } = useTheme();

  return (
    <aside
      style={{
        width: 180,
        background: "var(--bg2)",
        borderRight: "1px solid var(--border)",
        padding: "16px 10px",
        display: "flex",
        flexDirection: "column",
        flexShrink: 0,
        minHeight: "100vh",
      }}
    >
      {/* Logo */}
      <div
        className="serif"
        style={{
          fontSize: 18,
          color: "var(--text)",
          marginBottom: 24,
          paddingLeft: 6,
        }}
      >
        pap<span style={{ color: "var(--teal)" }}>AI</span>rus
      </div>

      {/* Nav links */}
      {NAV.map(({ href, label, dot }) => {
        const active = path === href || path.startsWith(href + "/");
        return (
          <Link
            key={href}
            href={href}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 8,
              height: 32,
              borderRadius: 8,
              padding: "0 10px",
              marginBottom: 3,
              fontSize: 13,
              color: active ? "var(--text)" : "var(--text2)",
              background: active ? "var(--bg)" : "transparent",
              border: active ? "1px solid var(--border2)" : "1px solid transparent",
              textDecoration: "none",
              transition: "all .15s",
            }}
          >
            <span
              style={{
                width: 6,
                height: 6,
                borderRadius: "50%",
                background: DOT_COLORS[dot],
                flexShrink: 0,
              }}
            />
            {label}
          </Link>
        );
      })}

      {/* Spacer */}
      <div style={{ flex: 1 }} />

      {/* Bottom: theme toggle + settings */}
      <div style={{ borderTop: "1px solid var(--border)", paddingTop: 8 }}>
        <button
          onClick={toggle}
          style={{
            display: "flex",
            alignItems: "center",
            gap: 8,
            height: 32,
            borderRadius: 8,
            padding: "0 10px",
            width: "100%",
            fontSize: 13,
            color: "var(--text2)",
            background: "transparent",
            border: "none",
            cursor: "pointer",
            textAlign: "left",
          }}
        >
          <span style={{ fontSize: 14 }}>{theme === "dark" ? "☀️" : "🌙"}</span>
          {theme === "dark" ? "Light mode" : "Dark mode"}
        </button>
      </div>
    </aside>
  );
}
