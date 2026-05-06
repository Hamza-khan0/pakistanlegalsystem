import { BookOpenText, LibraryBig, Scale } from "lucide-react";

import { PageHeader } from "@/components/common/page-header";
import { RightPanel } from "@/components/common/right-panel";
import { SectionCard } from "@/components/common/section-card";
import { Card } from "@/components/ui/card";
import { researchNotes } from "@/data/research";

export default function ResearchPage() {
  return (
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_320px]">
      <div className="space-y-6">
        <PageHeader
          eyebrow="Research"
          title="Legal research workspace"
          description="A matter-aware research surface for Pakistani authorities, issue clusters, authority notes, and retrieval-ready legal intelligence."
          meta={[
            "Authority placeholders",
            "Issue clustering",
            "Future semantic retrieval ready",
          ]}
        />

        <SectionCard
          title="Recent research notes"
          description="Verified and in-progress authority notes across the chamber."
        >
          <div className="grid gap-4 xl:grid-cols-2">
            {researchNotes.map((note) => (
              <Card
                key={note.id}
                className="space-y-4 rounded-[26px] border-line bg-white/[0.03]"
              >
                <div className="flex items-center gap-3">
                  <div className="flex size-11 items-center justify-center rounded-2xl border border-line bg-panel-highlight text-accent">
                    <BookOpenText className="size-4.5" />
                  </div>
                  <div>
                    <p className="text-xs uppercase tracking-[0.18em] text-subtle">
                      {note.author} / {note.status}
                    </p>
                    <h3 className="mt-1 text-lg font-semibold tracking-tight text-foreground">
                      {note.title}
                    </h3>
                  </div>
                </div>
                <p className="text-sm leading-6 text-muted-foreground">
                  {note.summary}
                </p>
                <div className="flex flex-wrap gap-2">
                  {note.authorities.map((authority) => (
                    <span
                      key={authority}
                      className="rounded-full border border-line px-2.5 py-1 text-[11px] uppercase tracking-[0.18em] text-muted-foreground"
                    >
                      {authority}
                    </span>
                  ))}
                </div>
              </Card>
            ))}
          </div>
        </SectionCard>

        <div className="grid gap-4 md:grid-cols-2">
          <SectionCard
            title="Authority clusters"
            description="Sample research groupings for future retrieval systems."
          >
            <div className="space-y-3">
              {[
                "Article 199 maintainability exceptions",
                "Interim injunction threshold in property disputes",
                "Further inquiry and parity in bail matters",
                "Revenue notice defects and revision scope",
              ].map((item) => (
                <div
                  key={item}
                  className="rounded-2xl border border-line bg-white/[0.03] px-4 py-3 text-sm text-foreground"
                >
                  {item}
                </div>
              ))}
            </div>
          </SectionCard>

          <SectionCard
            title="Retrieval placeholders"
            description="Signals that will later connect to legal knowledge systems."
          >
            <div className="space-y-4">
              {[
                {
                  icon: LibraryBig,
                  title: "Pakistani precedent index",
                  detail: "Statute-linked precedent retrieval placeholder with matter context filters.",
                },
                {
                  icon: Scale,
                  title: "Forum-aware authority ranking",
                  detail: "Future ranking by court, issue, relief type, and procedural posture.",
                },
              ].map((item) => (
                <div
                  key={item.title}
                  className="rounded-2xl border border-line bg-white/[0.03] p-4"
                >
                  <div className="flex items-center gap-3">
                    <div className="flex size-10 items-center justify-center rounded-2xl border border-line bg-panel-highlight text-accent">
                      <item.icon className="size-4" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-foreground">{item.title}</p>
                      <p className="mt-1 text-sm leading-6 text-muted-foreground">
                        {item.detail}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </SectionCard>
        </div>
      </div>

      <RightPanel
        title="Research signals"
        description="High-level retrieval posture for the current chamber."
        sections={[
          {
            title: "Open questions",
            items: [
              {
                label: "Need customs authority on release against security",
                value: "Open",
                tone: "warning",
              },
              {
                label: "Need one more allotment remedy case",
                value: "Open",
                tone: "warning",
              },
            ],
          },
          {
            title: "Source posture",
            items: [
              {
                label: "Pakistani statutes",
                value: "Mapped",
                detail:
                  "Each matter has placeholder statute links ready for future retrieval wiring.",
              },
              {
                label: "Precedent notes",
                value: "Structured",
                detail:
                  "Research notes are normalized for later semantic search and memory linkage.",
              },
            ],
          },
        ]}
      />
    </div>
  );
}
