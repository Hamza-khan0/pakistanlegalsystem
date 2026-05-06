import type { LucideIcon } from "lucide-react";
import { ArrowUpRight } from "lucide-react";

import { Card } from "@/components/ui/card";

interface StatCardProps {
  label: string;
  value: string;
  detail: string;
  change: string;
  icon: LucideIcon;
}

export function StatCard({
  label,
  value,
  detail,
  change,
  icon: Icon,
}: StatCardProps) {
  return (
    <Card className="overflow-hidden">
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-3">
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-subtle">
            {label}
          </p>
          <div className="space-y-1">
            <h3 className="text-3xl font-semibold tracking-[-0.04em] text-foreground">
              {value}
            </h3>
            <p className="text-sm text-muted-foreground">{detail}</p>
          </div>
        </div>
        <div className="flex size-12 items-center justify-center rounded-2xl border border-line bg-panel-highlight text-accent">
          <Icon className="size-5" />
        </div>
      </div>
      <div className="mt-6 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.2em] text-accent">
        <ArrowUpRight className="size-3.5" />
        {change}
      </div>
    </Card>
  );
}
