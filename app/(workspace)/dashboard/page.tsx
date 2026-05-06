import Link from "next/link";
import {
  BellRing,
  BriefcaseBusiness,
  CalendarClock,
  FileStack,
} from "lucide-react";

import { CaseTable } from "@/components/cases/case-table";
import { ErrorState } from "@/components/common/error-state";
import { RightPanel } from "@/components/common/right-panel";
import { PageHeader } from "@/components/common/page-header";
import { SectionCard } from "@/components/common/section-card";
import { ActivityFeed } from "@/components/dashboard/activity-feed";
import { DeadlinesWidget } from "@/components/dashboard/deadlines-widget";
import { PinnedMatters } from "@/components/dashboard/pinned-matters";
import { StatCard } from "@/components/dashboard/stat-card";
import { Button, buttonVariants } from "@/components/ui/button";
import { getDashboardSummary } from "@/lib/api/client";

export default async function DashboardPage() {
  const result = await loadDashboardSummary();

  if (!result.ok) {
    return (
      <div className="space-y-6">
        <PageHeader
          eyebrow="Dashboard"
          title="Lahore litigation chamber"
          description="The backend summary could not be loaded for this workspace."
        />
        <ErrorState
          title="Dashboard data unavailable"
          message={`${result.message} Ensure the FastAPI backend is running and seeded before opening the live dashboard.`}
        />
      </div>
    );
  }

  const summary = result.summary;

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Dashboard"
        title="Lahore litigation chamber"
        description="A premium operating view of active Pakistani legal work, combining case management, document readiness, agent operations, and procedural urgency."
        meta={[
          "Phase 3 intelligence live",
          "Database-backed matters",
          "Structured chamber outputs",
        ]}
        actions={
          <>
            <Link
              href="/workspace"
              className={buttonVariants({ variant: "secondary" })}
            >
              Open chamber console
            </Link>
            <Link href="/cases?create=1" className={buttonVariants()}>
              New case intake
            </Link>
          </>
        }
      />

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard
          icon={BriefcaseBusiness}
          label="Active cases"
          value={`${summary.activeCaseCount}`}
          detail="Across civil, constitutional, revenue, and service work"
          change="Live count from the case database"
        />
        <StatCard
          icon={FileStack}
          label="Pending filings"
          value={`${summary.pendingFilingsCount}`}
          detail="Drafts still in drafting or review state"
          change="Tracked from draft storage"
        />
        <StatCard
          icon={CalendarClock}
          label="Urgent deadlines"
          value={`${summary.urgentDeadlinesCount}`}
          detail="High-priority upcoming hearing preparation items"
          change="Derived from upcoming case hearings"
        />
        <StatCard
          icon={BellRing}
          label="Documents uploaded"
          value={`${summary.uploadedDocumentsCount}`}
          detail="Stored in the real document metadata index"
          change="Backed by database records"
        />
      </div>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_320px]">
        <div className="space-y-6">
          <SectionCard
            title="Quick actions"
            description="Launch common legal operations from the workspace."
          >
            <div className="grid gap-4 lg:grid-cols-3">
              {[
                {
                  title: "Open chamber command",
                  detail: "Send a structured legal instruction to the multi-agent workspace.",
                  href: "/workspace",
                  action: "Open workspace",
                },
                {
                  title: "Prepare hearing bundle",
                  detail: "Review deadlines, draft notes, and document readiness before court.",
                  disabled: true,
                  action: "Coming soon",
                },
                {
                  title: "Index new document set",
                  detail: "Stage a fresh upload batch with parsing and metadata placeholders.",
                  href: "/documents?upload=1",
                  action: "Upload documents",
                },
              ].map((item) => (
                <div
                  key={item.title}
                  className="rounded-[24px] border border-line bg-white/[0.03] p-5"
                >
                  <h3 className="text-lg font-semibold tracking-tight text-foreground">
                    {item.title}
                  </h3>
                  <p className="mt-2 text-sm leading-6 text-muted-foreground">
                    {item.detail}
                  </p>
                  <div className="mt-5">
                    {item.disabled ? (
                      <Button disabled variant="outline">
                        {item.action}
                      </Button>
                    ) : (
                      <Link
                        href={item.href ?? "/dashboard"}
                        className={buttonVariants({ variant: "secondary", size: "sm" })}
                      >
                        {item.action}
                      </Link>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </SectionCard>

          <SectionCard
            title="Recent cases"
            description="Most active matters by current hearing urgency and drafting load."
          >
            <CaseTable cases={summary.recentCases.slice(0, 4)} />
          </SectionCard>

          <SectionCard
            title="Pinned matters"
            description="High-signal matters that define the chamber's current load."
          >
            <PinnedMatters matters={summary.recentCases} />
          </SectionCard>

          <SectionCard
            title="Recent activity"
            description="A live-looking stream of chamber, team, and court activity."
          >
            <ActivityFeed items={summary.recentActivity} />
          </SectionCard>
        </div>

        <div className="space-y-6">
          <SectionCard
            title="Deadlines and court dates"
            description="Priority-sensitive work requiring immediate coordination."
          >
            <DeadlinesWidget deadlines={summary.urgentDeadlines} />
          </SectionCard>

          <RightPanel
            title="Chamber log"
            description="Operational signals sourced from the live backend summary."
            sections={[
              {
                title: "Audit and alerts",
                items: summary.notifications.map((notification) => ({
                  id: notification.id,
                  label: notification.title,
                  value:
                    notification.tone === "warning"
                      ? "Alert"
                      : notification.tone === "success"
                        ? "Done"
                        : "Info",
                  tone:
                    notification.tone === "warning"
                      ? "warning"
                      : notification.tone === "success"
                        ? "success"
                        : "default",
                  detail: notification.detail,
                })),
              },
              {
                title: "Upcoming hearings",
                items: summary.upcomingHearings.slice(0, 3).map((hearing) => ({
                  id: hearing.id,
                  label: hearing.title,
                  value: hearing.severity,
                  tone:
                    hearing.severity === "Critical" || hearing.severity === "High"
                      ? "warning"
                      : "default",
                  detail: hearing.note,
                })),
              },
            ]}
          />
        </div>
      </div>
    </div>
  );
}

async function loadDashboardSummary() {
  try {
    return {
      ok: true as const,
      summary: await getDashboardSummary(),
    };
  } catch (error) {
    return {
      ok: false as const,
      message:
        error instanceof Error ? error.message : "Unable to load dashboard data.",
    };
  }
}
