import { useState } from "react";
import type { Citation } from "../../types";
import { IconQuote } from "../Icons";

export function CitationList({ citations }: { citations: Citation[] }) {
  if (!citations.length) return null;
  return (
    <div className="mt-3 space-y-2">
      <p className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-ink-faint">
        <IconQuote size={14} />
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
        className="flex items-center gap-1.5 rounded-lg border border-line bg-surface-2 px-2.5 py-1 text-xs font-medium text-ink-soft transition hover:border-accent/40 hover:text-ink"
      >
        <span
          className="grid h-4 w-4 place-items-center rounded text-[10px] font-bold text-white"
          style={{ background: "var(--accent)" }}
        >
          {index}
        </span>
        <span className="max-w-[180px] truncate">{citation.document_name}</span>
        {citation.page != null && (
          <span className="text-ink-faint">· tr.{citation.page}</span>
        )}
      </button>
      {open && (
        <div className="absolute bottom-full left-0 z-10 mb-2 w-80 rounded-2xl border border-line bg-surface p-3.5 text-xs text-ink-soft shadow-maple">
          <p className="mb-1.5 font-semibold text-ink">
            {citation.document_name}
            {citation.page != null && ` — trang ${citation.page}`}
          </p>
          <p className="max-h-32 overflow-y-auto leading-relaxed text-ink-soft">
            {citation.source_text}
          </p>
          {citation.score != null && (
            <p className="mt-2 text-[10px] text-ink-faint">
              Độ liên quan: {(citation.score * 100).toFixed(0)}%
            </p>
          )}
        </div>
      )}
    </div>
  );
}
