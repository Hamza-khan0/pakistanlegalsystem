import type { ActivityItem, NotificationItem } from "@/types";

export const notifications: NotificationItem[] = [
  {
    id: "nt-001",
    title: "Urgent hearing approaching",
    detail: "Green Valley allotment matter is listed in 4 days before the motion bench.",
    timestamp: "2026-04-20 14:11",
    tone: "warning",
  },
  {
    id: "nt-002",
    title: "Drafting Agent output published",
    detail: "Customs petition skeleton was pushed to partner review.",
    timestamp: "2026-04-20 13:08",
    tone: "success",
  },
  {
    id: "nt-003",
    title: "OCR still running",
    detail: "Valuation matrix bundle is awaiting final text extraction.",
    timestamp: "2026-04-20 12:46",
    tone: "info",
  },
  {
    id: "nt-004",
    title: "Procedural reminder raised",
    detail: "Parity order in bail matter still has no certified copy attached.",
    timestamp: "2026-04-20 12:12",
    tone: "warning",
  },
];

export const activities: ActivityItem[] = [
  {
    id: "ac-001",
    title: "Research note verified",
    detail: "Maintainability note in the DHA allotment matter was verified against current authorities.",
    timestamp: "14:10",
    category: "Agent",
  },
  {
    id: "ac-002",
    title: "Hearing bundle revised",
    detail: "Urgency framing updated for the motion bench filing set.",
    timestamp: "13:48",
    category: "Document",
  },
  {
    id: "ac-003",
    title: "Bench date confirmed",
    detail: "Bail application remained fixed for 27 Apr 2026 after partial arguments.",
    timestamp: "12:36",
    category: "Court",
  },
  {
    id: "ac-004",
    title: "Partner review started",
    detail: "Customs petition and stay application moved to final markup.",
    timestamp: "11:55",
    category: "Team",
  },
  {
    id: "ac-005",
    title: "Revenue record indexed",
    detail: "Certified mutation extracts were tagged for notice and genealogy review.",
    timestamp: "10:18",
    category: "Document",
  },
];
