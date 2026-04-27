// All requests go through Next.js rewrites → /api/* → http://localhost:8000/*
const BASE = "/api";

export interface NodeOut {
  id: string;
  name: string;
  type: "emotion" | "person" | "theme" | "habit";
  color_hex: string;
}

export interface EntryOut {
  id: string;
  transcript: string;
  audio_path: string | null;
  created_at: string;
  nodes: NodeOut[];
}

export interface GraphNode {
  id: string;
  name: string;
  type: string;
  color_hex: string;
  entry_count: number;
}

export interface GraphEdge {
  source: string;
  target: string;
  weight: number;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface DayIntensity {
  day: string;
  date: string;
  count: number;
  dominant_type: string;
}

export interface DigestOut {
  week_start: string;
  week_end: string;
  top_emotion: string | null;
  top_emotion_count: number;
  mood_trend_pct: number;
  most_connected_node: string | null;
  most_connected_count: number;
  entry_count: number;
  best_streak: number;
  days: DayIntensity[];
  people: { name: string; count: number }[];
  reflection: string;
}

export interface TagSuggestion {
  name: string;
  type: string;
}

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, init);
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    let detail = text;
    try {
      const body = JSON.parse(text);
      detail = body?.detail ?? text;
    } catch (_e) {
      // raw text is already set as detail
    }
    throw new Error(`API error ${res.status}: ${path}${detail ? ` — ${detail}` : ""}`);
  }
  return res.json() as Promise<T>;
}

// Entries
export const getEntries = () => req<EntryOut[]>("/entries");
export const getEntry = (id: string) => req<EntryOut>(`/entries/${id}`);
export const deleteEntry = (id: string) =>
  fetch(`${BASE}/entries/${id}`, { method: "DELETE" });

export async function createEntry(
  transcript: string,
  nodeIds: string[],
  audio?: Blob
): Promise<EntryOut> {
  const fd = new FormData();
  fd.append("transcript", transcript);
  fd.append("node_ids", nodeIds.join(","));
  if (audio) fd.append("audio", audio, "recording.webm");
  const res = await fetch(`${BASE}/entries`, { method: "POST", body: fd });
  if (!res.ok) throw new Error("Failed to create entry");
  return res.json();
}

export async function autoTag(entryId: string): Promise<TagSuggestion[]> {
  const data = await req<{ suggestions: TagSuggestion[] }>(
    `/entries/${entryId}/auto-tag`,
    { method: "POST" }
  );
  return data.suggestions;
}

export async function setTags(entryId: string, nodeIds: string[]): Promise<EntryOut> {
  return req<EntryOut>(`/entries/${entryId}/tags`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(nodeIds),
  });
}

export async function transcribeEntry(entryId: string, language?: string): Promise<EntryOut> {
  const qs = language ? `?language=${language}` : "";
  return req<EntryOut>(`/entries/${entryId}/transcribe${qs}`, { method: "POST" });
}

export interface TranscribeWord {
  word: string;
  start: number;
  end: number;
}

export async function transcribeAudio(
  audio: Blob,
  language?: string,
  withTimestamps?: boolean
): Promise<{ text: string; language?: string; duration?: number; words?: TranscribeWord[] }> {
  const fd = new FormData();
  fd.append("audio", audio, "recording.webm");
  if (language) fd.append("language", language);
  if (withTimestamps) fd.append("with_timestamps", "true");
  const res = await fetch(`${BASE}/entries/transcribe-upload`, { method: "POST", body: fd });
  if (!res.ok) throw new Error("Transcription failed");
  return res.json();
}

// Nodes
export const getNodes = (type?: string) =>
  req<NodeOut[]>(type ? `/nodes?type=${type}` : "/nodes");

export const createNode = (name: string, type: string) =>
  req<NodeOut>("/nodes", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, type }),
  });

// Graph
export const getGraph = (type?: string, since?: string) => {
  const p = new URLSearchParams();
  if (type) p.set("type", type);
  if (since) p.set("since", since);
  const qs = p.toString();
  return req<GraphData>(`/graph${qs ? "?" + qs : ""}`);
};

// Digest
export const getDigest = (week?: string) =>
  req<DigestOut>(`/digest${week ? "?week=" + week : ""}`);

const BACKEND_DIRECT = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";
export const audioUrl = (path: string) => `${BACKEND_DIRECT}/uploads/${path}`;
