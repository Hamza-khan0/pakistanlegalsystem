import type { TimelineEntry } from "@/types";
import { formatDate } from "@/lib/utils";

export function TimelineList({ entries }: { entries: TimelineEntry[] }) {
  return (
    <div className="space-y-4">
      {entries.map((entry) => (
        <div key={entry.id} className="flex gap-4">
          <div className="flex flex-col items-center">
            <div className="mt-1.5 size-3 rounded-full bg-accent" />
            <div className="mt-2 h-full w-px bg-line" />
          </div>
          <div className="rounded-2xl border border-line bg-white/[0.03] p-4">
            <div className="flex flex-wrap items-center gap-3">
              <p className="text-sm font-medium text-foreground">{entry.title}</p>
              <span className="text-xs uppercase tracking-[0.18em] text-subtle">
                {entry.type}
              </span>
            </div>
            <p className="mt-1 text-sm leading-6 text-muted-foreground">
              {entry.description}
            </p>
            <div className="mt-3 flex flex-wrap gap-4 text-xs uppercase tracking-[0.18em] text-subtle">
              <span>{formatDate(entry.date)}</span>
              <span>{entry.actor}</span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
