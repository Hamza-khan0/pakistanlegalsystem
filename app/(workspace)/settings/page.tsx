import { Cpu, DatabaseZap, ShieldCheck, SlidersHorizontal } from "lucide-react";

import { PageHeader } from "@/components/common/page-header";
import { SectionCard } from "@/components/common/section-card";
import { Card } from "@/components/ui/card";

const settingsBlocks = [
  {
    icon: Cpu,
    title: "Agent orchestration",
    description:
      "Future controls for manager rules, agent routing preferences, and chamber confidence thresholds.",
  },
  {
    icon: DatabaseZap,
    title: "Case memory and retrieval",
    description:
      "Reserved for vector search, matter memory persistence, citation grounding, and semantic indexing.",
  },
  {
    icon: ShieldCheck,
    title: "Audit and access",
    description:
      "Planned controls for audit logging, role-based review states, and sensitive document handling.",
  },
  {
    icon: SlidersHorizontal,
    title: "Workspace preferences",
    description:
      "Theme density, panel defaults, and preferred chamber views for different litigation teams.",
  },
];

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Settings"
        title="Workspace settings"
        description="Settings remains a reserved control surface, but the workspace is now ready for future intelligence, access, and chamber-operations configuration."
        meta={["No auth yet", "Future control surface", "Integration-ready structure"]}
      />

      <SectionCard
        title="Configuration surfaces"
        description="Reserved modules for the next phases of the legal operating system."
      >
        <div className="grid gap-4 xl:grid-cols-2">
          {settingsBlocks.map((item) => (
            <Card
              key={item.title}
              className="space-y-4 rounded-[28px] border-line bg-white/[0.03]"
            >
              <div className="flex size-12 items-center justify-center rounded-2xl border border-line bg-panel-highlight text-accent">
                <item.icon className="size-5" />
              </div>
              <div>
                <h3 className="text-lg font-semibold tracking-tight text-foreground">
                  {item.title}
                </h3>
                <p className="mt-2 text-sm leading-6 text-muted-foreground">
                  {item.description}
                </p>
              </div>
            </Card>
          ))}
        </div>
      </SectionCard>
    </div>
  );
}
