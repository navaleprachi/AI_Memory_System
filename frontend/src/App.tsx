import { useEffect, useState } from "react";
import ChatPanel from "./components/ChatPanel";
import MemoryInspector from "./components/MemoryInspector";
import * as api from "./api";
import type { Conversation, MemoryChunk, CompressionStats } from "./api";

interface Message {
  role: "user" | "assistant";
  content: string;
}

export default function App() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConvId, setActiveConvId] = useState<string | null>(null);
  const [initialMessages, setInitialMessages] = useState<Message[]>([]);
  const [lastMemories, setLastMemories] = useState<MemoryChunk[]>([]);
  const [compressionStats, setCompressionStats] =
    useState<CompressionStats | null>(null);
  const [tokensUsed, setTokensUsed] = useState(0);

  useEffect(() => {
    fetchConversations();
  }, []);

  const fetchConversations = async () => {
    try {
      const res: any = await api.getConversations();
      const convs = Array.isArray(res) ? res : res.conversations || [];
      setConversations(convs);
    } catch (err) {
      console.error("Failed to fetch conversations:", err);
    }
  };

  const handleNew = async () => {
    try {
      const id = await api.createConversation("New conversation");
      setActiveConvId(id);
      setInitialMessages([]);
      setLastMemories([]);
      setCompressionStats(null);
      await fetchConversations();
    } catch (err) {
      console.error("Failed to create conversation:", err);
    }
  };

  const handleSelect = async (id: string) => {
    try {
      setActiveConvId(id);
      setLastMemories([]);
      try {
        const res: any = await api.getHistory(id);
        const messages = res.messages || res;
        setInitialMessages(
          messages
            .filter((m: any) => m.role !== "system")
            .map((m: any) => ({ role: m.role, content: m.content })),
        );
      } catch (err) {
        // Handle 404 or other errors (empty conversation) - show empty chat
        console.error(
          "Loading conversation history failed (showing empty):",
          err,
        );
        setInitialMessages([]);
      }
    } catch (err) {
      console.error("Failed to select conversation:", err);
    }
  };

  const handleResponse = async (res: any) => {
    setLastMemories(res.memories_injected || []);
    setCompressionStats(res.compression_stats || null);
    setTokensUsed(res.tokens_used || 0);
    await fetchConversations();
  };

  return (
    <div className="flex h-screen font-sans bg-slate-100 overflow-hidden">
      {/* Sidebar */}
      <aside className="w-56 bg-slate-900 flex flex-col shrink-0">
        <div className="px-4 py-4 border-b border-slate-700">
          <p className="text-white font-bold text-sm mb-3">AI Memory System</p>
          <button
            onClick={handleNew}
            className="w-full py-2 rounded-lg bg-indigo-600 text-white text-sm
                       font-semibold hover:bg-indigo-700 transition-colors"
          >
            + New Chat
          </button>
        </div>
        <div className="flex-1 overflow-y-auto py-2 px-2">
          {conversations.map((conv) => (
            <button
              key={conv.id}
              onClick={() => handleSelect(conv.id)}
              className={
                "w-full text-left px-3 py-2.5 rounded-lg mb-1 transition-colors " +
                (activeConvId === conv.id
                  ? "bg-slate-700 text-white"
                  : "text-slate-400 hover:bg-slate-800 hover:text-white")
              }
            >
              <p className="text-xs font-medium truncate">
                {conv.title ?? "Untitled chat"}
              </p>
              <p className="text-xs opacity-50 mt-0.5">
                {conv.message_count} messages
              </p>
            </button>
          ))}
        </div>
      </aside>

      {/* Main chat */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {activeConvId ? (
          <ChatPanel
            conversationId={activeConvId}
            initialMessages={initialMessages}
            onNewResponse={handleResponse}
          />
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <div className="text-center">
              <p className="text-3xl mb-2">🧠</p>
              <p className="text-slate-400 text-sm">
                Select a conversation or start a new one
              </p>
            </div>
          </div>
        )}
      </main>

      {/* Memory Inspector */}
      <div className="w-80 shrink-0 overflow-hidden">
        <MemoryInspector
          memories={lastMemories}
          compressionStats={compressionStats}
          tokensUsed={tokensUsed}
        />
      </div>
    </div>
  );
}
