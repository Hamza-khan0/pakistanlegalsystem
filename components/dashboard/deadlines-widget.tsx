import { AlertTriangle } from "lucide-react";

import { PriorityBadge } from "@/components/common/priority-badge";
import type { Deadline } from "@/types";
import { formatCompactDate, getDaysUntil } from "@/lib/utils";

export function DeadlinesWidget({ deadlines }: { deadlines: Deadline[] }) {
  return (
    <div className="space-y-3">
      {deadlines.slice(0, 4).map((deadline) => (
        <div
          key={deadline.id}
          className="rounded-2xl border border-line bg-white/[0.03] p-4"
        >
          <div className="flex items-start justify-between gap-4">
            <div className="space-y-2">
              <p className="text-sm font-medium text-foreground">{deadline.title}</p>
              <p className="text-xs uppercase tracking-[0.2em] text-subtle">
                Owner / {deadline.owner}
              </p>
              <p className="text-sm leading-6 text-muted-foreground">
                {deadline.note}
              </p>
            </div>
            <PriorityBadge priority={deadline.severity} />
          </div>
          <div className="mt-4 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-amber-200">
            <AlertTriangle className="size-3.5" />
            Due {formatCompactDate(deadline.dueDate)} ({getDaysUntil(deadline.dueDate)}{" "}
            days)
          </div>
        </div>
      ))}
    </div>
  );
}
