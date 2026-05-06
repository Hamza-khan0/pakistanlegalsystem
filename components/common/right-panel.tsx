import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface RightPanelItem {
  id?: string;
  label: string;
  value?: string;
  detail?: string;
  tone?: "default" | "warning" | "success";
}

interface RightPanelSection {
  title: string;
  items: RightPanelItem[];
}

interface RightPanelProps {
  title: string;
  description?: string;
  sections: RightPanelSection[];
  className?: string;
}

export function RightPanel({
  title,
  description,
  sections,
  className,
}: RightPanelProps) {
  return (
    <Card
      className={cn(
        "sticky top-24 space-y-6 rounded-[30px] border-line bg-panel-muted/95",
        className,
      )}
      tone="muted"
    >
      <div className="space-y-2">
        <span className="text-xs font-semibold uppercase tracking-[0.28em] text-accent">
          Intelligence
        </span>
        <h2 className="text-lg font-semibold tracking-tight">{title}</h2>
        {description ? (
          <p className="text-sm leading-6 text-muted-foreground">{description}</p>
        ) : null}
      </div>

      <div className="space-y-5">
        {sections.map((section, sectionIndex) => (
          <div key={`${section.title}-${sectionIndex}`} className="space-y-3">
            <h3 className="text-xs font-semibold uppercase tracking-[0.22em] text-subtle">
              {section.title}
            </h3>
            <div className="space-y-2">
              {section.items.map((item, itemIndex) => (
                <div
                  key={
                    item.id ??
                    `${section.title}-${item.label}-${item.value ?? "item"}-${itemIndex}`
                  }
                  className="rounded-2xl border border-line bg-white/[0.03] p-3"
                >
                  <div className="flex items-start justify-between gap-3">
                    <p className="text-sm font-medium text-foreground">{item.label}</p>
                    {item.value ? (
                      <span
                        className={cn(
                          "text-xs font-semibold uppercase tracking-[0.2em]",
                          item.tone === "warning"
                            ? "text-amber-200"
                            : item.tone === "success"
                              ? "text-emerald-200"
                              : "text-accent",
                        )}
                      >
                        {item.value}
                      </span>
                    ) : null}
                  </div>
                  {item.detail ? (
                    <p className="mt-1.5 text-sm leading-6 text-muted-foreground">
                      {item.detail}
                    </p>
                  ) : null}
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}
