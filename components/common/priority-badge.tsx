import { Badge } from "@/components/ui/badge";
import type { PriorityLevel } from "@/types";

const priorityVariantMap: Record<PriorityLevel, "danger" | "warning" | "info" | "muted"> =
  {
    Critical: "danger",
    High: "warning",
    Medium: "info",
    Low: "muted",
  };

export function PriorityBadge({ priority }: { priority: PriorityLevel }) {
  return <Badge variant={priorityVariantMap[priority]}>{priority}</Badge>;
}
