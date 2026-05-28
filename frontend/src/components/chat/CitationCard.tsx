import { useState } from "react";
import type { Citation } from "../../types";

export function CitationList({ citations }: { citations: Citation[] }) {
  if (!citations.length) return null;
  return (
    <div className="mt-3 space-y-2">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
        Nguồn trích dẫn
      </p>
      <div className="flex flex-wrap gap-2">
        {citations.map((c, i) => (
          <CitationChip key={i} citation={c} index={i + 1} />
        ))}
      </div>
    </div>
  );
}

function CitationChip({
  citation,
  index,
}: {
  citation: Citation;
  index: number;
}) {
  const [open, setOpen] = useState(false);
  return (
    <div className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        className="flex items-center gap-1.5 rounded-lg border border-brand-200 bg-brand-50 px-2.5 py-1 text-xs font-medium text-brand-700 transition hover:bg-brand-100"
      >
        <span className="grid h-4 w-4 place-items-center rounded bg-brand-600 text-[10px] text-white">
          {index}
        </span>
        <span className="max-w-[180px] truncate">{citation.document_name}</span>
        {citation.page != null && (
          <span className="text-brand-400">· tr.{citation.page}</span>
        )}
      </button>
      {open && (
        <div className="absolute bottom-full left-0 z-10 mb-2 w-80 rounded-xl border border-slate-200 bg-white p-3 text-xs text-slate-600 shadow-xl">
          <p className="mb-1 font-semibold text-slate-700">
            {citation.document_name}
            {citation.page != null && ` — trang ${citation.page}`}
          </p>
          <p className="max-h-32 overflow-y-auto leading-relaxed text-slate-500">
            {citation.source_text}
          </p>
          {citation.score != null && (
            <p className="mt-2 text-[10px] text-slate-400">
              Độ liên quan: {(citation.score * 100).toFixed(0)}%
            </p>
          )}
        </div>
      )}
    </div>
  );
}
