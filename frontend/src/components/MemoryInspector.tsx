import { Brain, Layers, Zap } from "lucide-react";
import type { MemoryChunk, CompressionStats, Summary } from "../api";

function ScoreBar({ value, color }: { value: number; color: string }) {
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-slate-100 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{ width: value * 100 + "%", background: color }}
        />
      </div>
      <span className="text-xs text-slate-400 w-8 text-right tabular-nums font-mono">
        {value.toFixed(2)}
      </span>
    </div>
  );
}

export default function MemoryInspector({
  memories,
  compressionStats,
  tokensUsed,
  summaries,
  onCompress,
  isCompressing,
  compressResult,
}: {
  memories: MemoryChunk[];
  compressionStats: CompressionStats | null;
  tokensUsed: number;
  summaries: Summary[];
  onCompress: (() => void) | null;
  isCompressing: boolean;
  compressResult: { fired: boolean; message: string } | null;
}) {
  return (
    <div className="h-full flex flex-col bg-slate-50 border-l border-slate-200 overflow-hidden">

      {/* Header */}
      <div className="bg-white border-b border-slate-100 px-4 py-3.5 shrink-0">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-lg bg-indigo-100 flex items-center justify-center">
              <Brain size={13} className="text-indigo-600" />
            </div>
            <p className="text-sm font-semibold text-slate-800">Memory Inspector</p>
          </div>
          {onCompress && (
            <button
              onClick={onCompress}
              disabled={isCompressing}
              className="flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded-lg
                         bg-indigo-600 text-white font-medium hover:bg-indigo-700
                         disabled:opacity-50 disabled:cursor-not-allowed transition-colors cursor-pointer shadow-sm"
            >
              <Zap size={11} />
              {isCompressing ? "Compressing…" : "Compress Now"}
            </button>
          )}
        </div>
        <p className="text-xs text-slate-400 mt-1 ml-8">
          {memories.length > 0
            ? `${memories.length} memories retrieved · ${tokensUsed} tokens`
            : "Send a message to see retrieved memories"}
        </p>
      </div>

      {/* Compress result banner */}
      {compressResult && (
        <div className={
          "px-4 py-2.5 text-xs font-medium shrink-0 flex items-center gap-2 " +
          (compressResult.fired
            ? "bg-emerald-50 text-emerald-700 border-b border-emerald-100"
            : "bg-amber-50 text-amber-700 border-b border-amber-100")
        }>
          <span>{compressResult.fired ? "✓" : "!"}</span>
          {compressResult.fired
            ? "Compression ran — new summary created below."
            : "No messages to compress yet."}
        </div>
      )}

      {/* Compression stats */}
      {compressionStats && (
        <div className="bg-white border-b border-slate-100 px-4 py-3 shrink-0">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2.5">
            Compression Stats
          </p>
          <div className="grid grid-cols-2 gap-2">
            {[
              { label: "Total msgs",   value: compressionStats.total_messages,      color: "text-slate-700" },
              { label: "Compressed",   value: compressionStats.compressed_messages,  color: "text-indigo-600" },
              { label: "Summaries",    value: compressionStats.total_summaries,      color: "text-amber-600" },
              { label: "Ratio",        value: Math.round(compressionStats.compression_ratio * 100) + "%", color: "text-emerald-600" },
            ].map((s, i) => (
              <div key={i} className="bg-slate-50 rounded-xl px-3 py-2.5 border border-slate-100">
                <p className="text-xs text-slate-400 mb-0.5">{s.label}</p>
                <p className={"text-lg font-bold tabular-nums " + s.color}>{s.value}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Compressed summaries */}
      {summaries.length > 0 && (
        <div className="bg-white border-b border-slate-100 px-4 py-3 shrink-0">
          <div className="flex items-center gap-1.5 mb-2.5">
            <Layers size={12} className="text-amber-500" />
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">
              Compressed Memory
            </p>
            <span className="ml-auto text-xs bg-amber-100 text-amber-700 font-semibold px-1.5 py-0.5 rounded-full">
              {summaries.length}
            </span>
          </div>
          <div className="flex flex-col gap-2 max-h-52 overflow-y-auto pr-0.5">
            {summaries.map((s, i) => (
              <div key={s.id} className="bg-amber-50 border border-amber-100 rounded-xl p-3">
                <div className="flex items-center justify-between mb-1.5">
                  <div className="flex items-center gap-1.5">
                    <span className={
                      "text-xs font-bold px-1.5 py-0.5 rounded-md " +
                      (s.level === 2
                        ? "bg-purple-100 text-purple-700"
                        : "bg-amber-100 text-amber-700")
                    }>
                      L{s.level}
                    </span>
                    <span className="text-xs font-medium text-slate-600">
                      Summary #{summaries.length - i}
                    </span>
                  </div>
                  <span className="text-xs text-slate-400 tabular-nums">{s.token_count}t</span>
                </div>
                <p className="text-xs text-slate-600 leading-relaxed whitespace-pre-line">
                  {s.content}
                </p>
                {s.covers_from && s.covers_to && (
                  <p className="text-xs text-slate-400 mt-1.5 font-mono">
                    {new Date(s.covers_from).toLocaleDateString()} → {new Date(s.covers_to).toLocaleDateString()}
                  </p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Retrieved memory chunks */}
      <div className="flex-1 overflow-y-auto px-3 py-3 flex flex-col gap-2.5">
        {memories.length === 0 ? (
          <div className="flex flex-col items-center justify-center gap-2 mt-8 text-center px-4">
            <div className="w-10 h-10 rounded-xl bg-slate-100 flex items-center justify-center">
              <Brain size={18} className="text-slate-300" />
            </div>
            <p className="text-slate-400 text-xs leading-relaxed">
              Retrieved memories will appear here after each message
            </p>
          </div>
        ) : (
          <>
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide px-1">
              Retrieved Chunks
            </p>
            {memories.map((mem, i) => (
              <div key={i} className="bg-white rounded-xl border border-slate-100 p-3 shadow-sm">
                {/* Badge + rank */}
                <div className="flex items-center justify-between mb-2">
                  <span className={
                    "text-xs font-semibold px-2 py-0.5 rounded-full " +
                    (mem.source_type === "summary"
                      ? "bg-amber-50 text-amber-600 border border-amber-100"
                      : "bg-indigo-50 text-indigo-600 border border-indigo-100")
                  }>
                    {mem.source_type === "summary" ? "Summary" : "Raw chunk"}
                  </span>
                  <div className="flex items-center gap-1.5">
                    <span className="text-xs font-black text-indigo-600 tabular-nums">
                      {mem.final_score.toFixed(3)}
                    </span>
                    <span className="text-xs text-slate-300">#{i + 1}</span>
                  </div>
                </div>

                {/* Content preview */}
                <p className="text-xs text-slate-600 leading-relaxed mb-3 line-clamp-3 border-l-2 border-slate-100 pl-2">
                  {mem.content}
                </p>

                {/* Score bars */}
                <div className="flex flex-col gap-1.5">
                  {[
                    { label: "Relevance",   value: mem.similarity,       color: "#6366f1" },
                    { label: "Recency",     value: mem.recency_score,    color: "#10b981" },
                    { label: "Importance",  value: mem.importance_score, color: "#f59e0b" },
                  ].map((s, j) => (
                    <div key={j} className="flex items-center gap-2">
                      <span className="text-xs text-slate-400 w-16 shrink-0">{s.label}</span>
                      <ScoreBar value={s.value} color={s.color} />
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </>
        )}
      </div>
    </div>
  );
}
