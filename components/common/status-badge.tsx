import { Badge } from "@/components/ui/badge";
import type {
  AgentStatus,
  CaseStatus,
  ChamberRunStatus,
  ChamberRunStepStatus,
  DocumentStatus,
  ExtractionStatus,
  IntelligenceStatus,
} from "@/types";

type StatusValue =
  | CaseStatus
  | DocumentStatus
  | ExtractionStatus
  | IntelligenceStatus
  | AgentStatus
  | ChamberRunStatus
  | ChamberRunStepStatus
  | "Published"
  | "Needs Review"
  | "Ready for Filing"
  | string;

const statusVariantMap: Record<string, "accent" | "info" | "warning" | "success" | "danger" | "muted"> =
  {
    Active: "info",
    "Hearing Due": "warning",
    "Awaiting Filing": "muted",
    Research: "muted",
    Drafting: "accent",
    Closed: "success",
    Filed: "success",
    Draft: "muted",
    "Under Review": "accent",
    "Pending Signature": "warning",
    Reference: "info",
    Parsed: "success",
    "OCR Running": "warning",
    "Manual Review": "accent",
    "Ready for Indexing": "info",
    "Not Processed": "muted",
    Processing: "warning",
    Processed: "success",
    Generated: "success",
    Stale: "accent",
    Failed: "danger",
    Ready: "success",
    Running: "warning",
    Queued: "muted",
    Reviewing: "accent",
    Planning: "info",
    Pending: "muted",
    Completed: "success",
    "Critic Review": "accent",
    Published: "success",
    "Needs Review": "warning",
    "Ready for Filing": "success",
    Discovered: "muted",
    Fetched: "info",
    Downloaded: "success",
    Duplicate: "warning",
    "Text Extracted": "info",
    "OCR Required": "warning",
    "OCR Completed": "success",
    "Partially Extracted": "accent",
    Disabled: "danger",
  };

export function StatusBadge({ status }: { status: StatusValue }) {
  return <Badge variant={statusVariantMap[status] ?? "muted"}>{status}</Badge>;
}
