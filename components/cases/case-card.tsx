import Link from "next/link";
import { ArrowUpRight } from "lucide-react";

import { AvatarStack } from "@/components/common/avatar-stack";
import { PriorityBadge } from "@/components/common/priority-badge";
import { StatusBadge } from "@/components/common/status-badge";
import { buttonVariants } from "@/components/ui/button";
import type { CaseMatter } from "@/types";
import { formatCompactDate } from "@/lib/utils";

interface CaseCardProps {
  caseItem: CaseMatter;
  onEdit?: (caseItem: CaseMatter) => void;
}

export function CaseCard({ caseItem, onEdit }: CaseCardProps) {
  if (onEdit) {
    return (
      <div className="rounded-[28px] border border-line bg-panel p-5">
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-3">
            <div className="flex flex-wrap gap-2">
              <StatusBadge status={caseItem.status} />
              <PriorityBadge priority={caseItem.priority} />
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.2em] text-subtle">
                {caseItem.caseNumber}
              </p>
              <h3 className="mt-2 text-lg font-semibold tracking-tight text-foreground">
                {caseItem.title}
              </h3>
            </div>
          </div>
          <ArrowUpRight className="size-5 text-muted-foreground" />
        </div>
        <p className="mt-4 text-sm leading-6 text-muted-foreground">
          {caseItem.summary}
        </p>
        <div className="mt-4 flex flex-wrap gap-2">
          <span className="rounded-full border border-line px-2.5 py-1 text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
            Docs: {caseItem.linkedDocumentIds.length}
          </span>
          <span className="rounded-full border border-line px-2.5 py-1 text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
            Research notes: {caseItem.researchNoteIds.length}
          </span>
          <span className="rounded-full border border-line px-2.5 py-1 text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
            Drafts: {caseItem.draftArtifacts.length}
          </span>
          {caseItem.tags.slice(0, 3).map((tag) => (
            <span
              key={tag}
              className="rounded-full border border-line px-2.5 py-1 text-[11px] uppercase tracking-[0.18em] text-muted-foreground"
            >
              {tag}
            </span>
          ))}
        </div>
        <div className="mt-5 flex items-center justify-between gap-4 border-t border-line pt-4">
          <div>
            <p className="text-xs uppercase tracking-[0.18em] text-subtle">
              Next hearing
            </p>
            <p className="text-sm font-medium text-foreground">
              {formatCompactDate(caseItem.nextHearingDate)}
            </p>
          </div>
          <AvatarStack names={caseItem.assignedCounsel} />
        </div>
        <div className="mt-4 flex flex-wrap gap-3">
          <button
            className={buttonVariants({ variant: "secondary", size: "sm" })}
            onClick={() => onEdit(caseItem)}
            type="button"
          >
            Edit
          </button>
          <Link
            href={`/cases/${caseItem.id}`}
            className={buttonVariants({ size: "sm" })}
          >
            Open
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
      </div>
    );
  }

  return (
    <Link
      href={`/cases/${caseItem.id}`}
      className="group rounded-[28px] border border-line bg-panel p-5 transition-all duration-200 hover:-translate-y-0.5 hover:border-accent/30 hover:bg-panel-highlight"
    >
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-3">
          <div className="flex flex-wrap gap-2">
            <StatusBadge status={caseItem.status} />
            <PriorityBadge priority={caseItem.priority} />
          </div>
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-subtle">
              {caseItem.caseNumber}
            </p>
            <h3 className="mt-2 text-lg font-semibold tracking-tight text-foreground">
              {caseItem.title}
            </h3>
          </div>
        </div>
        <ArrowUpRight className="size-5 text-muted-foreground transition-transform group-hover:-translate-y-0.5 group-hover:translate-x-0.5 group-hover:text-accent" />
      </div>
      <p className="mt-4 text-sm leading-6 text-muted-foreground">
        {caseItem.summary}
      </p>
      <div className="mt-4 flex flex-wrap gap-2">
        <span className="rounded-full border border-line px-2.5 py-1 text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
          Docs: {caseItem.linkedDocumentIds.length}
        </span>
        <span className="rounded-full border border-line px-2.5 py-1 text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
          Research notes: {caseItem.researchNoteIds.length}
        </span>
        <span className="rounded-full border border-line px-2.5 py-1 text-[11px] uppercase tracking-[0.18em] text-muted-foreground">
          Drafts: {caseItem.draftArtifacts.length}
        </span>
        {caseItem.tags.slice(0, 3).map((tag) => (
          <span
            key={tag}
            className="rounded-full border border-line px-2.5 py-1 text-[11px] uppercase tracking-[0.18em] text-muted-foreground"
          >
            {tag}
          </span>
        ))}
      </div>
      <div className="mt-5 flex items-center justify-between gap-4 border-t border-line pt-4">
        <div>
          <p className="text-xs uppercase tracking-[0.18em] text-subtle">
            Next hearing
          </p>
          <p className="text-sm font-medium text-foreground">
            {formatCompactDate(caseItem.nextHearingDate)}
          </p>
        </div>
        <AvatarStack names={caseItem.assignedCounsel} />
      </div>
    </Link>
  );
}
