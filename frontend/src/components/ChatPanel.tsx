import { useState, useRef, useEffect } from "react";
import { Send } from "lucide-react";
import { sendMessage } from "../api";
import { usePostHog } from "posthog-js/react";

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface Props {
  conversationId: string;
  initialMessages?: Message[];
  onNewResponse: (r: any) => void;
}

// Renders basic markdown: ### headings, **bold**, - bullet lists
function MessageContent({ content }: { content: string }) {
  const lines = content.split("\n");
  const elements: React.ReactNode[] = [];

  lines.forEach((line, i) => {
    if (line.startsWith("### ")) {
      elements.push(
        <p key={i} className="font-bold text-sm mt-2 mb-0.5">
          {renderInline(line.slice(4))}
        </p>
      );
    } else if (line.startsWith("## ")) {
      elements.push(
        <p key={i} className="font-bold text-sm mt-2 mb-0.5">
          {renderInline(line.slice(3))}
        </p>
      );
    } else if (line.startsWith("- ") || line.startsWith("* ")) {
      elements.push(
        <div key={i} className="flex gap-1.5 items-start">
          <span className="mt-1.5 w-1 h-1 rounded-full bg-current shrink-0 opacity-60" />
          <span>{renderInline(line.slice(2))}</span>
        </div>
      );
    } else if (line.trim() === "") {
      elements.push(<div key={i} className="h-1.5" />);
    } else {
      elements.push(<span key={i}>{renderInline(line)}{i < lines.length - 1 ? " " : ""}</span>);
    }
  });

  return <div className="text-sm leading-relaxed">{elements}</div>;
}

function renderInline(text: string): React.ReactNode {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) =>
    part.startsWith("**") && part.endsWith("**")
      ? <strong key={i}>{part.slice(2, -2)}</strong>
      : part
  );
}

function TypingDots() {
  return (
    <div className="flex items-center gap-1 px-1 py-0.5">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce"
          style={{ animationDelay: `${i * 0.15}s`, animationDuration: "0.8s" }}
        />
      ))}
    </div>
  );
}

export default function ChatPanel({ conversationId, initialMessages = [], onNewResponse }: Props) {
  const posthog = usePostHog();
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setMessages(initialMessages);
  }, [conversationId, initialMessages]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;
    const text = input.trim();
    setInput("");
    setMessages((p) => [...p, { role: "user", content: text }]);
    setLoading(true);
    try {
      const res = await sendMessage(conversationId, text);
      posthog.capture("message_sent", { conversation_id: conversationId });
      setMessages((p) => [...p, { role: "assistant", content: res.reply }]);
      onNewResponse(res);
    } catch {
      setMessages((p) => [
        ...p,
        { role: "assistant", content: "Something went wrong. Is the server running?" },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-white">
      {/* Header */}
      <div className="border-b border-slate-100 px-6 py-3.5 shrink-0 flex items-center gap-3">
        <div className="w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_6px_#34d399]" />
        <span className="text-sm font-semibold text-slate-700">
          {messages.length === 0 ? "New conversation" : `${messages.length} messages`}
        </span>
      </div>

      {/* Message list */}
      <div className="flex-1 overflow-y-auto px-6 py-6 flex flex-col gap-4">
        {messages.length === 0 && (
          <div className="flex-1 flex flex-col items-center justify-center text-center gap-2 mt-16">
            <div className="w-12 h-12 rounded-2xl bg-indigo-50 flex items-center justify-center mb-1">
              <span className="text-2xl">🧠</span>
            </div>
            <p className="text-slate-700 font-semibold text-sm">Memory-aware AI</p>
            <p className="text-slate-400 text-xs max-w-xs leading-relaxed">
              Every message is embedded and ranked by relevance, recency, and importance.
              Old messages are automatically compressed to save tokens.
            </p>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={"flex gap-3 " + (msg.role === "user" ? "justify-end" : "justify-start")}>
            {msg.role === "assistant" && (
              <div className="w-7 h-7 rounded-full bg-indigo-100 flex items-center justify-center shrink-0 mt-0.5 text-sm">
                🤖
              </div>
            )}
            <div
              className={
                "max-w-[72%] px-4 py-3 rounded-2xl " +
                (msg.role === "user"
                  ? "bg-indigo-600 text-white rounded-br-md shadow-sm"
                  : "bg-slate-50 text-slate-800 border border-slate-100 rounded-bl-md shadow-sm")
              }
            >
              {msg.role === "assistant" ? (
                <MessageContent content={msg.content} />
              ) : (
                <p className="text-sm leading-relaxed">{msg.content}</p>
              )}
            </div>
            {msg.role === "user" && (
              <div className="w-7 h-7 rounded-full bg-indigo-600 flex items-center justify-center shrink-0 mt-0.5 text-xs text-white font-bold">
                U
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="flex gap-3 justify-start">
            <div className="w-7 h-7 rounded-full bg-indigo-100 flex items-center justify-center shrink-0 text-sm">
              🤖
            </div>
            <div className="bg-slate-50 border border-slate-100 px-4 py-3 rounded-2xl rounded-bl-md shadow-sm">
              <TypingDots />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input bar */}
      <div className="border-t border-slate-100 px-4 py-3.5 bg-white">
        <div className="flex gap-2 items-end">
          <textarea
            value={input}
            rows={1}
            onChange={(e) => {
              setInput(e.target.value);
              e.target.style.height = "auto";
              e.target.style.height = Math.min(e.target.scrollHeight, 120) + "px";
            }}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder="Type a message…"
            disabled={loading}
            className="flex-1 px-4 py-2.5 rounded-xl border border-slate-200 text-sm text-slate-800
                       placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-300
                       focus:border-indigo-300 disabled:bg-slate-50 disabled:cursor-not-allowed
                       resize-none overflow-hidden leading-relaxed bg-slate-50 transition-colors"
          />
          <button
            onClick={handleSend}
            disabled={loading || !input.trim()}
            className="w-10 h-10 rounded-xl bg-indigo-600 text-white flex items-center justify-center
                       hover:bg-indigo-700 active:bg-indigo-800 disabled:bg-slate-200
                       disabled:text-slate-400 disabled:cursor-not-allowed transition-colors shrink-0"
          >
            <Send size={16} />
          </button>
        </div>
        <p className="text-xs text-slate-300 mt-1.5 ml-1">Enter to send · Shift+Enter for newline</p>
      </div>
    </div>
  );
}
