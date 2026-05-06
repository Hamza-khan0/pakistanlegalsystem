import { timelineEntries } from "@/data/timelines";
import { PageHeader } from "@/components/common/page-header";
import { SectionCard } from "@/components/common/section-card";
import { TimelineList } from "@/components/cases/timeline-list";

export default function TimelinePage() {
  const timeline = [...timelineEntries].sort(
    (left, right) => +new Date(right.date) - +new Date(left.date),
  );

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Timeline"
        title="Chamber timeline"
        description="A cross-matter chronology of hearings, filings, document events, and agent workstreams."
        meta={["Cross-matter chronology", "Court and agent activity", "Audit-friendly event stream"]}
      />

      <SectionCard
        title="Master event stream"
        description="Recent events across all matters, ordered for audit and operational review."
      >
        <TimelineList entries={timeline} />
      </SectionCard>
    </div>
  );
}
