"use client";

import { useEffect, useRef, useState } from "react";
import Sidebar from "@/components/Sidebar";
import NodeChip from "@/components/NodeChip";
import {
  createEntry,
  getNodes,
  createNode,
  autoTag,
  NodeOut,
} from "@/lib/api";

type Status = "idle" | "recording" | "processing" | "saved" | "error";

const TYPE_COLORS: Record<string, string> = {
  emotion: "var(--coral)",
  person:  "var(--blue)",
  theme:   "var(--teal)",
  habit:   "var(--amber)",
};

export default function RecordPage() {
  const [status, setStatus] = useState<Status>("idle");
  const [transcript, setTranscript] = useState("");
  const [tags, setTags] = useState<NodeOut[]>([]);
  const [allNodes, setAllNodes] = useState<NodeOut[]>([]);
  const [showNodePicker, setShowNodePicker] = useState(false);
  const [newNodeName, setNewNodeName] = useState("");
  const [newNodeType, setNewNodeType] = useState<string>("emotion");
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [errorMsg, setErrorMsg] = useState("");
  const [savedId, setSavedId] = useState<string | null>(null);

  const mediaRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  useEffect(() => {
    getNodes().then(setAllNodes).catch(() => {});
  }, []);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mr = new MediaRecorder(stream);
      chunksRef.current = [];
      mr.ondataavailable = (e) => chunksRef.current.push(e.data);
      mr.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        setAudioBlob(blob);
        stream.getTracks().forEach((t) => t.stop());
      };
      mr.start();
      mediaRef.current = mr;
      setStatus("recording");
    } catch {
      setErrorMsg("Microphone access denied.");
      setStatus("error");
    }
  };

  const stopRecording = () => {
    mediaRef.current?.stop();
    setStatus("idle");
  };

  const handleAutoTag = async () => {
    if (!transcript.trim()) return;
    setStatus("processing");
    try {
      // Create a temp entry to call auto-tag, then delete it
      const entry = await createEntry(transcript, []);
      const suggestions = await autoTag(entry.id);
      // Resolve suggestions against known nodes (or create them)
      const resolved: NodeOut[] = [];
      for (const s of suggestions) {
        let node = allNodes.find(
          (n) => n.name.toLowerCase() === s.name.toLowerCase() && n.type === s.type
        );
        if (!node) {
          node = await createNode(s.name, s.type);
          setAllNodes((prev) => [...prev, node!]);
        }
        if (!tags.find((t) => t.id === node!.id)) resolved.push(node!);
      }
      setTags((prev) => [...prev, ...resolved]);
      setSavedId(entry.id);
    } catch {
      setErrorMsg("Auto-tag failed.");
    } finally {
      setStatus("idle");
    }
  };

  const handleSave = async () => {
    if (!transcript.trim() && !audioBlob) return;
    setStatus("processing");
    setErrorMsg("");
    try {
      const nodeIds = tags.map((t) => t.id);
      if (savedId) {
        const { setTags: setTagsApi } = await import("@/lib/api");
        await setTagsApi(savedId, nodeIds);
      } else {
        await createEntry(transcript, nodeIds, audioBlob ?? undefined);
      }
      setStatus("saved");
      setTranscript("");
      setTags([]);
      setAudioBlob(null);
      setSavedId(null);
      setTimeout(() => setStatus("idle"), 2000);
    } catch {
      setErrorMsg("Failed to save entry.");
      setStatus("error");
    }
  };

  const addTag = async (node: NodeOut) => {
    if (!tags.find((t) => t.id === node.id)) setTags((p) => [...p, node]);
    setShowNodePicker(false);
  };

  const addCustomTag = async () => {
    if (!newNodeName.trim()) return;
    try {
      const node = await createNode(newNodeName.trim(), newNodeType);
      setAllNodes((p) => [...p, node]);
      addTag(node);
      setNewNodeName("");
    } catch {}
  };

  const isRecording = status === "recording";

  return (
    <div style={{ display: "flex", minHeight: "100vh" }}>
      <Sidebar />

      {/* Centered mobile-style card */}
      <main
        style={{
          flex: 1,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          padding: "24px 16px",
        }}
      >
        <div
          style={{
            width: 320,
            background: "var(--bg)",
            borderRadius: 24,
            padding: "24px 20px 20px",
            border: "1px solid var(--border2)",
          }}
        >
          {/* Logo + greeting */}
          <div
            className="serif"
            style={{ fontSize: 22, textAlign: "center", marginBottom: 4, color: "var(--text)" }}
          >
            pap<span style={{ color: "var(--teal)" }}>AI</span>rus
          </div>
          <div style={{ fontSize: 12, color: "var(--text2)", textAlign: "center", marginBottom: 24 }}>
            How are you feeling today?
          </div>

          {/* Orb */}
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", marginBottom: 20 }}>
            <div
              onMouseDown={startRecording}
              onMouseUp={stopRecording}
              onTouchStart={startRecording}
              onTouchEnd={stopRecording}
              style={{
                width: 128,
                height: 128,
                borderRadius: "50%",
                background: isRecording ? "var(--teal-bg)" : "var(--bg2)",
                border: `2px solid ${isRecording ? "var(--teal)" : "var(--border2)"}`,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                position: "relative",
                cursor: "pointer",
                transition: "all .2s",
                boxShadow: isRecording ? "0 0 0 12px var(--teal-bg)" : "none",
              }}
            >
              <div
                style={{
                  width: 80,
                  height: 80,
                  borderRadius: "50%",
                  background: isRecording ? "var(--teal)" : "var(--bg3)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  transition: "background .2s",
                }}
              >
                {/* Mic icon */}
                <svg width="36" height="36" viewBox="0 0 36 36" fill="none">
                  <rect x="13" y="4" width="10" height="16" rx="5" fill={isRecording ? "white" : "var(--text3)"} />
                  <path d="M8 18c0 5.523 4.477 10 10 10s10-4.477 10-10" stroke={isRecording ? "white" : "var(--text3)"} strokeWidth="2.2" strokeLinecap="round" fill="none" />
                  <line x1="18" y1="28" x2="18" y2="33" stroke={isRecording ? "white" : "var(--text3)"} strokeWidth="2.2" strokeLinecap="round" />
                  <line x1="13" y1="33" x2="23" y2="33" stroke={isRecording ? "white" : "var(--text3)"} strokeWidth="2.2" strokeLinecap="round" />
                </svg>
              </div>
            </div>
            <div style={{ fontSize: 11, color: "var(--text3)", marginTop: 10 }}>
              {isRecording ? "recording… release to stop" : "hold to record"}
            </div>
            {audioBlob && (
              <audio
                controls
                src={URL.createObjectURL(audioBlob)}
                style={{ marginTop: 10, width: "100%", height: 32 }}
              />
            )}
          </div>

          {/* Transcript */}
          <textarea
            value={transcript}
            onChange={(e) => setTranscript(e.target.value)}
            placeholder="Type or paste your thoughts here…"
            rows={4}
            style={{
              width: "100%",
              background: "var(--bg2)",
              border: "1px solid var(--border)",
              borderRadius: 8,
              padding: "10px 13px",
              fontSize: 12,
              color: "var(--text2)",
              lineHeight: 1.65,
              resize: "vertical",
              marginBottom: 10,
              outline: "none",
              fontFamily: "inherit",
            }}
          />

          {/* Tags row */}
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 10 }}>
            {tags.map((tag) => (
              <NodeChip key={tag.id} node={tag} onRemove={() => setTags((p) => p.filter((t) => t.id !== tag.id))} />
            ))}
            <button
              onClick={() => setShowNodePicker((p) => !p)}
              style={{
                padding: "3px 10px",
                borderRadius: 12,
                fontSize: 11,
                background: "var(--bg2)",
                border: "1px dashed var(--border2)",
                color: "var(--text3)",
                cursor: "pointer",
              }}
            >
              + tag
            </button>
          </div>

          {/* Node picker */}
          {showNodePicker && (
            <div
              style={{
                background: "var(--bg2)",
                border: "1px solid var(--border)",
                borderRadius: 8,
                padding: 10,
                marginBottom: 10,
                maxHeight: 180,
                overflowY: "auto",
              }}
            >
              <div style={{ fontSize: 10, color: "var(--text3)", marginBottom: 6, textTransform: "uppercase", letterSpacing: "0.07em" }}>
                Pick existing
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 4, marginBottom: 8 }}>
                {allNodes.map((n) => (
                  <button
                    key={n.id}
                    onClick={() => addTag(n)}
                    style={{
                      padding: "2px 8px",
                      borderRadius: 10,
                      fontSize: 10,
                      background: "var(--bg3)",
                      border: "1px solid var(--border2)",
                      color: "var(--text2)",
                      cursor: "pointer",
                    }}
                  >
                    {n.name}
                  </button>
                ))}
              </div>
              <div style={{ fontSize: 10, color: "var(--text3)", marginBottom: 4, textTransform: "uppercase", letterSpacing: "0.07em" }}>
                Create new
              </div>
              <div style={{ display: "flex", gap: 4 }}>
                <input
                  value={newNodeName}
                  onChange={(e) => setNewNodeName(e.target.value)}
                  placeholder="name"
                  style={{
                    flex: 1,
                    padding: "4px 8px",
                    fontSize: 11,
                    background: "var(--bg)",
                    border: "1px solid var(--border)",
                    borderRadius: 6,
                    color: "var(--text)",
                    outline: "none",
                  }}
                />
                <select
                  value={newNodeType}
                  onChange={(e) => setNewNodeType(e.target.value)}
                  style={{
                    padding: "4px 6px",
                    fontSize: 11,
                    background: "var(--bg)",
                    border: "1px solid var(--border)",
                    borderRadius: 6,
                    color: "var(--text)",
                  }}
                >
                  <option value="emotion">emotion</option>
                  <option value="person">person</option>
                  <option value="theme">theme</option>
                  <option value="habit">habit</option>
                </select>
                <button
                  onClick={addCustomTag}
                  style={{
                    padding: "4px 8px",
                    fontSize: 11,
                    background: "var(--teal)",
                    color: "#fff",
                    border: "none",
                    borderRadius: 6,
                    cursor: "pointer",
                  }}
                >
                  Add
                </button>
              </div>
            </div>
          )}

          {/* Auto-tag button */}
          <button
            onClick={handleAutoTag}
            disabled={!transcript.trim() || status === "processing"}
            style={{
              width: "100%",
              height: 36,
              borderRadius: 8,
              background: "var(--teal-bg)",
              border: "1px solid var(--teal-border)",
              color: "var(--teal)",
              fontSize: 12,
              fontWeight: 500,
              cursor: "pointer",
              marginBottom: 8,
              opacity: !transcript.trim() ? 0.5 : 1,
            }}
          >
            {status === "processing" ? "Tagging…" : "✦ Auto-tag"}
          </button>

          {/* Save button */}
          <button
            onClick={handleSave}
            disabled={(!transcript.trim() && !audioBlob) || status === "processing"}
            style={{
              width: "100%",
              height: 42,
              borderRadius: 8,
              background: status === "saved" ? "var(--teal2)" : "var(--teal)",
              border: "none",
              color: "#fff",
              fontSize: 13,
              fontWeight: 600,
              cursor: "pointer",
              letterSpacing: "0.01em",
              opacity: !transcript.trim() && !audioBlob ? 0.5 : 1,
              transition: "background .2s",
            }}
          >
            {status === "saved" ? "✓ Saved!" : status === "processing" ? "Saving…" : "Save entry"}
          </button>

          {errorMsg && (
            <div style={{ fontSize: 11, color: "var(--coral)", marginTop: 6, textAlign: "center" }}>
              {errorMsg}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
