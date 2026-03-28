import type { MemoryChunk, CompressionStats } from "../api";

function ScoreBar({ value, color }: { value: number; color: string }) {
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-slate-200 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full"
          style={{ width: value * 100 + "%", background: color }}
        />
      </div>
      <span className="text-xs text-slate-400 w-8 text-right tabular-nums">
        {value.toFixed(2)}
      </span>
    </div>
  );
}

export default function MemoryInspector({
  memories,
  compressionStats,
  tokensUsed,
}: {
  memories: MemoryChunk[];
  compressionStats: CompressionStats | null;
  tokensUsed: number;
}) {
  return (
    <div className="h-full flex flex-col bg-slate-50 border-l border-slate-200 overflow-hidden">
      {/* Header */}
      <div className="bg-white border-b border-slate-200 px-4 py-3 shrink-0">
        <p className="text-sm font-bold text-slate-800">Memory Inspector</p>
        <p className="text-xs text-slate-400 mt-0.5">
          {memories.length > 0
            ? memories.length + " memories — " + tokensUsed + " tokens used"
            : "Send a message to see retrieved memories"}
        </p>
      </div>

      {/* Compression stats */}
      {compressionStats && (
        <div className="bg-emerald-50 border-b border-emerald-100 px-4 py-3 shrink-0">
          <p className="text-xs font-semibold text-emerald-700 mb-2">
            Compression Stats
          </p>
          <div className="grid grid-cols-2 gap-2">
            {[
              { label: "Total", value: compressionStats.total_messages },
              {
                label: "Compressed",
                value: compressionStats.compressed_messages,
              },
              { label: "Summaries", value: compressionStats.total_summaries },
              {
                label: "Ratio",
                value:
                  Math.round(compressionStats.compression_ratio * 100) + "%",
              },
            ].map((s, i) => (
              <div key={i} className="bg-white rounded-lg px-3 py-2">
                <p className="text-xs text-slate-400">{s.label}</p>
                <p className="text-base font-bold text-emerald-600">
                  {s.value}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Memory chunks */}
      <div className="flex-1 overflow-y-auto px-3 py-3 flex flex-col gap-3">
        {memories.length === 0 && (
          <p className="text-slate-400 text-xs text-center mt-6">
            No memories retrieved yet
          </p>
        )}
        {memories.map((mem, i) => (
          <div
            key={i}
            className="bg-white rounded-xl border border-slate-200 p-3 shadow-sm"
          >
            <div className="flex items-center justify-between mb-2">
              <span
                className={
                  "text-xs font-semibold px-2.5 py-0.5 rounded-full " +
                  (mem.source_type === "summary"
                    ? "bg-amber-100 text-amber-700"
                    : "bg-blue-100 text-blue-700")
                }
              >
                {mem.source_type === "summary" ? "Summary" : "Raw chunk"}
              </span>
              <span className="text-xs text-slate-400">{"#" + (i + 1)}</span>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed mb-3 line-clamp-3">
              {mem.content}
            </p>

            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-bold text-indigo-600">
                Final score
              </span>
              <span className="text-sm font-black text-indigo-600 tabular-nums">
                {mem.final_score.toFixed(3)}
              </span>
            </div>

            <div className="flex flex-col gap-1.5">
              {[
                { label: "Relevance", value: mem.similarity, color: "#6366f1" },
                {
                  label: "Recency",
                  value: mem.recency_score,
                  color: "#10b981",
                },
                {
                  label: "Importance",
                  value: mem.importance_score,
                  color: "#f59e0b",
                },
              ].map((s, j) => (
                <div key={j}>
                  <p className="text-xs text-slate-400 mb-0.5">{s.label}</p>
                  <ScoreBar value={s.value} color={s.color} />
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
