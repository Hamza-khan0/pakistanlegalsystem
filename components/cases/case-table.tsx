import Link from "next/link";
import { ArrowUpRight } from "lucide-react";

import { AvatarStack } from "@/components/common/avatar-stack";
import { PriorityBadge } from "@/components/common/priority-badge";
import { StatusBadge } from "@/components/common/status-badge";
import { buttonVariants } from "@/components/ui/button";
import type { CaseMatter } from "@/types";
import { formatCompactDate } from "@/lib/utils";

interface CaseTableProps {
  cases: CaseMatter[];
  onEdit?: (caseItem: CaseMatter) => void;
}

export function CaseTable({ cases, onEdit }: CaseTableProps) {
  return (
    <div className="min-w-0 overflow-x-auto rounded-[28px] border border-line bg-panel">
      <table className="min-w-full divide-y divide-line">
        <thead className="bg-white/[0.02]">
          <tr className="text-left text-xs font-semibold uppercase tracking-[0.22em] text-subtle">
            <th className="px-5 py-4">Matter</th>
            <th className="px-5 py-4">Forum</th>
            <th className="px-5 py-4">Status</th>
            <th className="px-5 py-4">Next Hearing</th>
            <th className="px-5 py-4">Counsel</th>
            <th className="px-5 py-4" />
          </tr>
        </thead>
        <tbody className="divide-y divide-line">
          {cases.map((caseItem) => (
            <tr key={caseItem.id} className="transition-colors hover:bg-white/[0.03]">
              <td className="px-5 py-4">
                <div className="min-w-[280px] max-w-xl space-y-2">
                  <p className="text-xs uppercase tracking-[0.18em] text-subtle">
                    {caseItem.caseNumber}
                  </p>
                  <div>
                    <p className="legal-text-wrap font-medium text-foreground">{caseItem.title}</p>
                    <p className="legal-text-wrap mt-1 text-sm text-muted-foreground">
                      {caseItem.client}
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <PriorityBadge priority={caseItem.priority} />
                    <span className="rounded-full border border-line px-2.5 py-1 text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
                      {caseItem.matterType}
                    </span>
                    <span className="rounded-full border border-line px-2.5 py-1 text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
                      Docs: {caseItem.linkedDocumentIds.length}
                    </span>
                    <span className="rounded-full border border-line px-2.5 py-1 text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
                      Drafts: {caseItem.draftArtifacts.length}
                    </span>
                  </div>
                </div>
              </td>
              <td className="legal-text-wrap min-w-[180px] px-5 py-4 text-sm text-muted-foreground">
                {caseItem.forum}
              </td>
              <td className="px-5 py-4">
                <StatusBadge status={caseItem.status} />
              </td>
              <td className="px-5 py-4 text-sm font-medium text-foreground">
                {formatCompactDate(caseItem.nextHearingDate)}
              </td>
              <td className="px-5 py-4">
                <AvatarStack names={caseItem.assignedCounsel} />
              </td>
              <td className="px-5 py-4 text-right">
                <div className="flex min-w-[360px] flex-wrap items-center justify-end gap-2">
                  {onEdit ? (
                    <button
                      className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
                      onClick={() => onEdit(caseItem)}
                      type="button"
                    >
                      Edit
                    </button>
                  ) : null}
                  <Link
                    href={`/cases/${caseItem.id}`}
                    className="inline-flex items-center gap-2 text-sm font-medium text-accent transition-colors hover:text-accent-soft"
                  >
                    Open
                    <ArrowUpRight className="size-4" />
                  </Link>
                  <Link
                    href={`/cases/${caseItem.id}?research=1`}
                    className={buttonVariants({ size: "sm", variant: "outline" })}
                  >
                    Research & Draft
                  </Link>
                  <Link
                    href={`/cases/${caseItem.id}?runs=1`}
                    className={buttonVariants({ size: "sm", variant: "ghost" })}
                  >
                    View Runs
                  </Link>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
