"use client";

import { useEffect, useRef, useState } from "react";
import Sidebar from "@/components/Sidebar";
import { chat, ContextNode, Persona } from "@/lib/api";

type Role = "user" | "assistant";

interface Message {
  role: Role;
  text: string;
  context?: ContextNode[];
}

const PERSONAS: { value: Persona; label: string; blurb: string }[] = [
  { value: "stoic", label: "Stoic", blurb: "Listens. Reflects. Says little." },
  { value: "socratic", label: "Socratic", blurb: "Asks one question. Never answers." },
  { value: "analyst", label: "Analyst", blurb: "Surfaces patterns from your graph." },
];

const TYPE_COLORS: Record<string, string> = {
  emotion: "var(--coral)",
  person: "var(--blue)",
  theme: "var(--teal)",
  habit: "var(--amber)",
};

export default function ChatPage() {
  const [persona, setPersona] = useState<Persona>("stoic");
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, sending]);

  const send = async () => {
    const text = input.trim();
    if (!text || sending) return;
    setInput("");
    setErrorMsg("");
    setMessages((p) => [...p, { role: "user", text }]);
    setSending(true);
    try {
      const res = await chat(text, persona);
      setMessages((p) => [...p, { role: "assistant", text: res.reply, context: res.context_nodes }]);
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Chat failed.";
      setErrorMsg(msg);
    } finally {
      setSending(false);
    }
  };

  const onKey = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  const current = PERSONAS.find((p) => p.value === persona)!;

  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      <Sidebar />

      <main
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          padding: "20px 24px",
          maxWidth: 760,
          width: "100%",
          margin: "0 auto",
        }}
      >
        {/* Header */}
        <div style={{ marginBottom: 16 }}>
          <div className="serif" style={{ fontSize: 22, color: "var(--text)", marginBottom: 2 }}>
            Talk it through
          </div>
          <div style={{ fontSize: 12, color: "var(--text3)" }}>
            Grounded in your own journal entries.
          </div>
        </div>

        {/* Persona selector */}
        <div style={{ display: "flex", gap: 6, marginBottom: 6 }}>
          {PERSONAS.map((p) => (
            <button
              key={p.value}
              onClick={() => setPersona(p.value)}
              style={{
                flex: 1,
                padding: "8px 10px",
                fontSize: 12,
                borderRadius: 8,
                background: persona === p.value ? "var(--bg)" : "var(--bg2)",
                border: `1px solid ${persona === p.value ? "var(--border2)" : "var(--border)"}`,
                color: persona === p.value ? "var(--text)" : "var(--text2)",
                cursor: "pointer",
                fontWeight: persona === p.value ? 600 : 400,
                textAlign: "left",
              }}
            >
              {p.label}
            </button>
          ))}
        </div>
        <div style={{ fontSize: 11, color: "var(--text3)", marginBottom: 14 }}>
          {current.blurb}
        </div>

        {/* Message thread */}
        <div
          ref={scrollRef}
          style={{
            flex: 1,
            background: "var(--bg2)",
            border: "1px solid var(--border)",
            borderRadius: 12,
            padding: 16,
            overflowY: "auto",
            minHeight: 320,
            maxHeight: "calc(100vh - 320px)",
            marginBottom: 10,
          }}
        >
          {messages.length === 0 && !sending && (
            <div style={{ fontSize: 12, color: "var(--text3)", textAlign: "center", marginTop: 60 }}>
              Say what&apos;s on your mind.
            </div>
          )}

          {messages.map((m, i) => (
            <div
              key={i}
              style={{
                display: "flex",
                justifyContent: m.role === "user" ? "flex-end" : "flex-start",
                marginBottom: 12,
              }}
            >
              <div style={{ maxWidth: "78%" }}>
                <div
                  style={{
                    background: m.role === "user" ? "var(--teal)" : "var(--bg)",
                    color: m.role === "user" ? "#fff" : "var(--text)",
                    border: m.role === "user" ? "none" : "1px solid var(--border2)",
                    borderRadius: 12,
                    padding: "10px 14px",
                    fontSize: 13,
                    lineHeight: 1.55,
                    whiteSpace: "pre-wrap",
                  }}
                >
                  {m.text}
                </div>
                {m.role === "assistant" && m.context && m.context.length > 0 && (
                  <div style={{ display: "flex", gap: 4, flexWrap: "wrap", marginTop: 6 }}>
                    {m.context.map((n) => (
                      <span
                        key={n.id}
                        style={{
                          fontSize: 10,
                          padding: "2px 8px",
                          borderRadius: 10,
                          background: "var(--bg2)",
                          border: `1px solid ${TYPE_COLORS[n.type] ?? "var(--border2)"}`,
                          color: "var(--text2)",
                        }}
                        title={n.type}
                      >
                        {n.name}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}

          {sending && (
            <div style={{ display: "flex", justifyContent: "flex-start", marginBottom: 12 }}>
              <div
                style={{
                  background: "var(--bg)",
                  border: "1px solid var(--border2)",
                  borderRadius: 12,
                  padding: "10px 14px",
                  fontSize: 13,
                  color: "var(--text3)",
                  fontStyle: "italic",
                }}
              >
                thinking…
              </div>
            </div>
          )}
        </div>

        {/* Input */}
        <div style={{ display: "flex", gap: 8, alignItems: "flex-end" }}>
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={onKey}
            placeholder="What's on your mind?"
            rows={2}
            style={{
              flex: 1,
              background: "var(--bg2)",
              border: "1px solid var(--border)",
              borderRadius: 10,
              padding: "10px 13px",
              fontSize: 13,
              color: "var(--text)",
              lineHeight: 1.55,
              resize: "none",
              outline: "none",
              fontFamily: "inherit",
            }}
          />
          <button
            onClick={send}
            disabled={!input.trim() || sending}
            style={{
              height: 42,
              padding: "0 18px",
              borderRadius: 10,
              background: "var(--teal)",
              border: "none",
              color: "#fff",
              fontSize: 13,
              fontWeight: 600,
              cursor: sending || !input.trim() ? "not-allowed" : "pointer",
              opacity: !input.trim() || sending ? 0.5 : 1,
            }}
          >
            Send
          </button>
        </div>

        {errorMsg && (
          <div style={{ fontSize: 11, color: "var(--coral)", marginTop: 8 }}>{errorMsg}</div>
        )}
      </main>
    </div>
  );
}
