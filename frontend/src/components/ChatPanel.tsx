import { useState, useRef, useEffect } from "react";
import { sendMessage } from "../api";

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface Props {
  conversationId: string;
  initialMessages?: Message[];
  onNewResponse: (r: any) => void;
}

export default function ChatPanel({
  conversationId,
  initialMessages = [],
  onNewResponse,
}: Props) {
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setMessages(initialMessages);
  }, [conversationId, initialMessages]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;
    const text = input.trim();
    setInput("");
    setMessages((p) => [...p, { role: "user", content: text }]);
    setLoading(true);
    try {
      const res = await sendMessage(conversationId, text);
      setMessages((p) => [...p, { role: "assistant", content: res.reply }]);
      onNewResponse(res);
    } catch {
      setMessages((p) => [
        ...p,
        {
          role: "assistant",
          content: "Something went wrong. Is the server running?",
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-white">
      {/* Message list */}
      <div className="flex-1 overflow-y-auto px-6 py-5 flex flex-col gap-3">
        {messages.length === 0 && (
          <p className="text-slate-400 text-sm text-center mt-10">
            Send a message to start the conversation
          </p>
        )}

        {messages.map((msg, i) => (
          <div
            key={i}
            className={
              "flex " + (msg.role === "user" ? "justify-end" : "justify-start")
            }
          >
            <div
              className={
                "max-w-[70%] px-4 py-2.5 rounded-2xl text-sm leading-relaxed " +
                (msg.role === "user"
                  ? "bg-indigo-600 text-white rounded-br-sm"
                  : "bg-slate-100 text-slate-800 rounded-bl-sm")
              }
            >
              {msg.content}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-slate-100 text-slate-400 text-sm px-4 py-2.5 rounded-2xl rounded-bl-sm">
              Thinking…
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input bar */}
      <div className="border-t border-slate-200 px-4 py-3 flex gap-2 bg-white">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
          placeholder="Type a message…"
          disabled={loading}
          className="flex-1 px-4 py-2.5 rounded-xl border border-slate-300 text-sm
                     text-slate-800 placeholder-slate-400 focus:outline-none
                     focus:ring-2 focus:ring-indigo-400 disabled:bg-slate-50
                     disabled:cursor-not-allowed"
        />
        <button
          onClick={handleSend}
          disabled={loading || !input.trim()}
          className="px-5 py-2.5 rounded-xl text-sm font-semibold bg-indigo-600
                     text-white hover:bg-indigo-700 active:bg-indigo-800
                     disabled:bg-slate-200 disabled:text-slate-400
                     disabled:cursor-not-allowed transition-colors"
        >
          Send
        </button>
      </div>
    </div>
  );
}
