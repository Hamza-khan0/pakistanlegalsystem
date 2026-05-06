import Link from "next/link";
import { ArrowUpRight } from "lucide-react";

import { PriorityBadge } from "@/components/common/priority-badge";
import { StatusBadge } from "@/components/common/status-badge";
import type { CaseMatter } from "@/types";
import { formatCompactDate } from "@/lib/utils";

export function PinnedMatters({ matters }: { matters: CaseMatter[] }) {
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      {matters.slice(0, 4).map((caseItem) => (
        <Link
          key={caseItem.id}
          href={`/cases/${caseItem.id}`}
          className="group rounded-[26px] border border-line bg-white/[0.03] p-5 transition-all duration-200 hover:-translate-y-0.5 hover:border-accent/30 hover:bg-white/[0.05]"
        >
          <div className="flex items-start justify-between gap-4">
            <div className="space-y-2">
              <p className="text-xs uppercase tracking-[0.2em] text-subtle">
                {caseItem.caseNumber}
              </p>
              <h3 className="text-lg font-semibold tracking-tight text-foreground">
                {caseItem.title}
              </h3>
              <p className="text-sm leading-6 text-muted-foreground">
                {caseItem.summary}
              </p>
            </div>
            <ArrowUpRight className="size-5 text-muted-foreground transition-transform group-hover:-translate-y-0.5 group-hover:translate-x-0.5 group-hover:text-accent" />
          </div>
          <div className="mt-5 flex flex-wrap gap-2">
            <StatusBadge status={caseItem.status} />
            <PriorityBadge priority={caseItem.priority} />
            <span className="rounded-full border border-line px-2.5 py-1 text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
              {caseItem.forum}
            </span>
          </div>
          <div className="mt-5 text-sm text-muted-foreground">
            Next hearing:{" "}
            <span className="font-medium text-foreground">
              {formatCompactDate(caseItem.nextHearingDate)}
            </span>
          </div>
        </Link>
      ))}
    </div>
  );
}
