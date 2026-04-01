import { useEffect, useState } from "react";
import ChatPanel from "./components/ChatPanel";
import MemoryInspector from "./components/MemoryInspector";
import { Analytics } from "@vercel/analytics/react";
import { usePostHog } from "posthog-js/react";
import * as api from "./api";
import type {
  Conversation,
  MemoryChunk,
  CompressionStats,
  Summary,
} from "./api";
import { Plus, X, MessageSquare } from "lucide-react";

interface Message {
  role: "user" | "assistant";
  content: string;
}

export default function App() {
  const posthog = usePostHog();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConvId, setActiveConvId] = useState<string | null>(null);
  const [initialMessages, setInitialMessages] = useState<Message[]>([]);
  const [lastMemories, setLastMemories] = useState<MemoryChunk[]>([]);
  const [compressionStats, setCompressionStats] =
    useState<CompressionStats | null>(null);
  const [tokensUsed, setTokensUsed] = useState(0);
  const [summaries, setSummaries] = useState<Summary[]>([]);
  const [isCompressing, setIsCompressing] = useState(false);
  const [compressResult, setCompressResult] = useState<{
    fired: boolean;
    message: string;
  } | null>(null);
  const [isTransitioning, setIsTransitioning] = useState(false);

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

  const fetchSummaries = async (id: string) => {
    try {
      const { summaries, stats } = await api.getSummaries(id);
      setSummaries(summaries);
      setCompressionStats(stats);
    } catch (err) {
      console.error("Failed to fetch summaries:", err);
    }
  };

  const handleNew = async () => {
    try {
      setIsTransitioning(true);
      setActiveConvId(null);
      setInitialMessages([]);
      setLastMemories([]);
      setSummaries([]);
      setCompressionStats(null);
      setCompressResult(null);
      const id = await api.createConversation("New conversation");
      posthog.capture("conversation_created");
      await fetchConversations();
      setActiveConvId(id);
    } catch (err) {
      console.error("Failed to create conversation:", err);
    } finally {
      setIsTransitioning(false);
    }
  };

  const handleSelect = async (id: string) => {
    if (id === activeConvId) return;
    try {
      setIsTransitioning(true);
      setActiveConvId(null);
      setLastMemories([]);
      setSummaries([]);
      setCompressionStats(null);
      setCompressResult(null);
      const [historyRes] = await Promise.all([
        api.getHistory(id).catch(() => null),
        fetchSummaries(id),
      ]);
      if (historyRes) {
        const messages = historyRes.messages || historyRes;
        setInitialMessages(
          messages
            .filter((m: any) => m.role !== "system")
            .map((m: any) => ({ role: m.role, content: m.content })),
        );
      } else {
        setInitialMessages([]);
      }
      setActiveConvId(id);
    } catch (err) {
      console.error("Failed to select conversation:", err);
    } finally {
      setIsTransitioning(false);
    }
  };

  const handleResponse = async (res: any) => {
    setLastMemories(res.memories_injected || []);
    setTokensUsed(res.tokens_used || 0);
    if (activeConvId) await fetchSummaries(activeConvId);
    await fetchConversations();
  };

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    await api.deleteConversation(id);
    if (activeConvId === id) {
      setActiveConvId(null);
      setInitialMessages([]);
      setLastMemories([]);
      setCompressionStats(null);
      setSummaries([]);
    }
    await fetchConversations();
  };

  const handleCompress = async () => {
    if (!activeConvId) return;
    setIsCompressing(true);
    setCompressResult(null);
    try {
      const result = await api.triggerCompress(activeConvId);
      posthog.capture("compression_triggered", { fired: result.fired, message: result.message });
      setCompressResult(result);
      await fetchSummaries(activeConvId);
      await fetchConversations();
    } finally {
      setIsCompressing(false);
    }
  };

  return (
    <div className="flex h-screen font-sans bg-slate-100 overflow-hidden">
      {/* Sidebar */}
      <aside className="w-56 bg-slate-900 flex flex-col shrink-0">
        <div className="px-4 py-4 border-b border-slate-700">
          <p className="text-white font-bold text-sm mb-3">AI Memory System</p>
          <button
            onClick={handleNew}
            className="flex items-center justify-center gap-2 w-full px-4 py-2 rounded-lg bg-indigo-600 text-white text-sm
                       font-semibold hover:bg-indigo-700 transition-colors cursor-pointer"
          >
            <Plus className="" size={14} />
            New Chat
          </button>
        </div>
        <div className="flex-1 overflow-y-auto py-2 px-2">
          {conversations.map((conv) => (
            <div
              key={conv.id}
              className={
                "group relative w-full text-left px-3 py-2.5 rounded-lg mb-1 transition-colors cursor-pointer " +
                (activeConvId === conv.id
                  ? "bg-slate-700 text-white"
                  : "text-slate-400 hover:bg-slate-800 hover:text-white")
              }
              onClick={() => handleSelect(conv.id)}
            >
              <div className="flex items-center gap-2 pr-5">
                <MessageSquare size={12} className="shrink-0 opacity-60" />
                <p className="text-xs font-medium truncate">
                  {conv.title ?? "Untitled chat"}
                </p>
              </div>
              <p className="text-xs opacity-40 mt-0.5 ml-5">
                {conv.message_count} messages
              </p>
              <button
                onClick={(e) => handleDelete(conv.id, e)}
                className="flex absolute right-2 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100
                           text-slate-400 hover:text-red-400 transition-opacity text-sm leading-none px-1 cursor-pointer"
                title="Delete conversation"
              >
                <X size={14} />
              </button>
            </div>
          ))}
        </div>
      </aside>

      {/* Main chat */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {isTransitioning ? (
          <div className="flex flex-col h-full bg-white">
            {/* Skeleton header */}
            <div className="border-b border-slate-100 px-6 py-3.5 shrink-0 flex items-center gap-3">
              <div className="w-2 h-2 rounded-full bg-slate-200 animate-pulse" />
              <div className="h-3 w-24 rounded-full bg-slate-100 animate-pulse" />
            </div>
            {/* Skeleton messages */}
            <div className="flex-1 px-6 py-6 flex flex-col gap-5">
              <div className="flex gap-3">
                <div className="w-7 h-7 rounded-full bg-slate-100 animate-pulse shrink-0" />
                <div className="flex flex-col gap-2 w-2/3">
                  <div className="h-3 rounded-full bg-slate-100 animate-pulse w-full" />
                  <div className="h-3 rounded-full bg-slate-100 animate-pulse w-4/5" />
                  <div className="h-3 rounded-full bg-slate-100 animate-pulse w-3/5" />
                </div>
              </div>
              <div className="flex gap-3 justify-end">
                <div className="flex flex-col gap-2 w-1/2">
                  <div className="h-3 rounded-full bg-indigo-100 animate-pulse w-full" />
                  <div className="h-3 rounded-full bg-indigo-100 animate-pulse w-3/4 ml-auto" />
                </div>
                <div className="w-7 h-7 rounded-full bg-indigo-100 animate-pulse shrink-0" />
              </div>
              <div className="flex gap-3">
                <div className="w-7 h-7 rounded-full bg-slate-100 animate-pulse shrink-0" />
                <div className="flex flex-col gap-2 w-3/4">
                  <div className="h-3 rounded-full bg-slate-100 animate-pulse w-full" />
                  <div className="h-3 rounded-full bg-slate-100 animate-pulse w-5/6" />
                  <div className="h-3 rounded-full bg-slate-100 animate-pulse w-2/3" />
                  <div className="h-3 rounded-full bg-slate-100 animate-pulse w-4/5" />
                </div>
              </div>
            </div>
            {/* Skeleton input */}
            <div className="border-t border-slate-100 px-4 py-3.5">
              <div className="h-10 rounded-xl bg-slate-100 animate-pulse" />
            </div>
          </div>
        ) : activeConvId ? (
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
          summaries={summaries}
          onCompress={activeConvId ? handleCompress : null}
          isCompressing={isCompressing}
          compressResult={compressResult}
        />
      </div>
      <Analytics />
    </div>
  );
}
