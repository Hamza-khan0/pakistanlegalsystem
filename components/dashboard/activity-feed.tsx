import type { ActivityItem } from "@/types";

export function ActivityFeed({ items }: { items: ActivityItem[] }) {
  return (
    <div className="space-y-3">
      {items.map((activity) => (
        <div
          key={activity.id}
          className="rounded-2xl border border-line bg-white/[0.03] p-4 transition-colors hover:bg-white/[0.05]"
        >
          <div className="flex items-start justify-between gap-3">
            <div className="space-y-1">
              <p className="text-sm font-medium text-foreground">{activity.title}</p>
              <p className="text-sm leading-6 text-muted-foreground">
                {activity.detail}
              </p>
            </div>
            <span className="text-xs uppercase tracking-[0.18em] text-subtle">
              {activity.timestamp}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}
