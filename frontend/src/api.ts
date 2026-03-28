const BASE = "http://localhost:8000";

export interface MemoryChunk {
  content: string;
  similarity: number;
  recency_score: number;
  importance_score: number;
  final_score: number;
  source_type: "message" | "summary";
}

export interface CompressionStats {
  total_messages: number;
  compressed_messages: number;
  total_summaries: number;
  compression_ratio: number;
}

export interface ChatDebugResponse {
  reply: string;
  conversation_id: string;
  tokens_used: number;
  message_count: number;
  memories_injected: MemoryChunk[];
  compression_stats: CompressionStats;
}

export interface Conversation {
  id: string;
  title: string | null;
  message_count: number;
  last_active: string;
}

export interface Summary {
  id: string;
  level: number;
  content: string;
  token_count: number;
  covers_from: string | null;
  covers_to: string | null;
  created_at: string;
}

export async function createConversation(title?: string): Promise<string> {
  const res = await fetch(BASE + "/conversations", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title: title ?? null }),
  });
  return (await res.json()).conversation_id;
}

export async function sendMessage(
  conversationId: string,
  message: string,
): Promise<ChatDebugResponse> {
  const res = await fetch(BASE + "/chat-with-debug/" + conversationId, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });
  return res.json();
}

export async function getConversations(): Promise<Conversation[]> {
  const res = await fetch(BASE + "/conversations");
  return res.json();
}

export async function getHistory(conversationId: string) {
  const res = await fetch(BASE + "/conversations/" + conversationId);
  return res.json();
}

export async function getSummaries(conversationId: string): Promise<{ summaries: Summary[]; stats: CompressionStats }> {
  const res = await fetch(BASE + "/conversations/" + conversationId + "/summaries");
  const data = await res.json();
  return {
    summaries: data.summaries || [],
    stats: data.stats ?? { total_messages: 0, compressed_messages: 0, total_summaries: 0, compression_ratio: 0 },
  };
}

export async function triggerCompress(conversationId: string): Promise<{ fired: boolean; message: string }> {
  const res = await fetch(BASE + "/conversations/" + conversationId + "/compress", { method: "POST" });
  return res.json();
}

export async function deleteConversation(conversationId: string): Promise<void> {
  await fetch(BASE + "/conversations/" + conversationId, { method: "DELETE" });
}
