import type { GroundingSource } from "@/types";

import { Card } from "@/components/ui/card";

export function LegalSourceList({
  sources,
  emptyMessage = "No legal sources were attached.",
  compact = false,
}: {
  sources: GroundingSource[];
  emptyMessage?: string;
  compact?: boolean;
}) {
  if (!sources.length) {
    return (
      <p className="text-sm leading-6 text-muted-foreground">{emptyMessage}</p>
    );
  }

  return (
    <div className={`grid gap-3 ${compact ? "" : "xl:grid-cols-2"}`}>
      {sources.map((source) => (
        <Card
          key={`${source.sourceId}-${source.chunkId ?? "source"}`}
          className="space-y-3 rounded-[22px] border-line bg-white/[0.03] p-4"
        >
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-xs uppercase tracking-[0.18em] text-subtle">
                {source.sourceType}
                {source.sectionLabel ? ` / ${source.sectionLabel}` : ""}
              </p>
              <h4 className="mt-1 text-sm font-semibold text-foreground">
                {source.citationLabel || source.title}
              </h4>
              <p className="mt-1 text-[11px] uppercase tracking-[0.16em] text-subtle">
                {source.sourceOrigin || "Seeded corpus"}
                {source.language ? ` / ${source.language}` : ""}
              </p>
            </div>
            {source.relevanceScore !== null ? (
              <span className="rounded-full border border-line px-2.5 py-1 text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
                {source.relevanceScore.toFixed(1)} relevance
              </span>
            ) : null}
          </div>
          {(source.lexicalScore !== null && source.lexicalScore !== undefined) ||
          (source.semanticScore !== null && source.semanticScore !== undefined) ? (
            <p className="text-[11px] uppercase tracking-[0.16em] text-subtle">
              {source.retrievalMode || "Lexical"}
              {source.lexicalScore !== null && source.lexicalScore !== undefined
                ? ` / lex ${source.lexicalScore.toFixed(2)}`
                : ""}
              {source.semanticScore !== null && source.semanticScore !== undefined
                ? ` / sem ${source.semanticScore.toFixed(2)}`
                : ""}
            </p>
          ) : null}
          <p className="text-sm leading-6 text-muted-foreground">
            {source.excerpt}
          </p>
          {source.explanation ? (
            <p className="text-[11px] leading-5 text-muted-foreground">
              {source.explanation}
            </p>
          ) : null}
          <p className="text-xs uppercase tracking-[0.16em] text-subtle">
            {source.usageType}
            {source.actName ? ` / ${source.actName}` : ""}
          </p>
          {source.sourceUrl ? (
            <p className="text-[11px] leading-5 text-muted-foreground">
              Source: {source.sourceUrl}
            </p>
          ) : null}
        </Card>
      ))}
    </div>
  );
}
