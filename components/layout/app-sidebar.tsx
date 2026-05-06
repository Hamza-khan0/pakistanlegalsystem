"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BriefcaseBusiness,
  ChartColumn,
  Building2,
  Clock3,
  DatabaseZap,
  FileText,
  Gavel,
  LayoutDashboard,
  Scale,
  SearchCode,
  Settings,
  Sparkles,
  X,
} from "lucide-react";

import { buttonVariants } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

const navigation = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/cases", label: "Cases", icon: BriefcaseBusiness },
  { href: "/documents", label: "Documents", icon: FileText },
  { href: "/knowledge", label: "Knowledge", icon: DatabaseZap },
  { href: "/models", label: "Models", icon: ChartColumn },
  { href: "/data", label: "Tier 1 Data", icon: DatabaseZap },
  { href: "/agents", label: "Agents", icon: Sparkles },
  { href: "/research", label: "Research", icon: SearchCode },
  { href: "/timeline", label: "Timeline", icon: Clock3 },
  { href: "/settings", label: "Settings", icon: Settings },
];

interface AppSidebarProps {
  mobile?: boolean;
  onClose?: () => void;
}

export function AppSidebar({ mobile = false, onClose }: AppSidebarProps) {
  const pathname = usePathname();

  return (
    <aside
      className={cn(
        "flex h-full w-full max-w-[300px] flex-col border-r border-line bg-[#0a1016]/90 px-5 py-5 backdrop-blur-2xl",
        mobile ? "max-w-[320px] shadow-[0_30px_80px_rgba(0,0,0,0.45)]" : "",
      )}
    >
      <div className="flex items-center justify-between gap-3 border-b border-line pb-5">
        <Link href="/dashboard" className="flex min-w-0 items-center gap-3">
          <div className="flex size-12 items-center justify-center rounded-2xl border border-accent/30 bg-accent/10 text-accent">
            <Scale className="size-5" />
          </div>
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold uppercase tracking-[0.24em] text-accent">
              AI Legal Chambers
            </p>
            <p className="truncate text-sm text-muted-foreground">
              Pakistani litigation OS
            </p>
          </div>
        </Link>
        {mobile ? (
          <button
            aria-label="Close sidebar"
            className="rounded-xl border border-line p-2 text-muted-foreground transition-colors hover:text-foreground"
            onClick={onClose}
            type="button"
          >
            <X className="size-4" />
          </button>
        ) : null}
      </div>

      <div className="mt-6 space-y-2">
        {navigation.map((item) => {
          const Icon = item.icon;
          const active = pathname === item.href || pathname.startsWith(`${item.href}/`);

          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onClose}
              className={cn(
                "flex items-center gap-3 rounded-2xl border px-4 py-3 transition-all duration-200",
                active
                  ? "border-accent/40 bg-accent/10 text-foreground"
                  : "border-transparent text-muted-foreground hover:border-line hover:bg-white/[0.03] hover:text-foreground",
              )}
            >
              <Icon className="size-4" />
              <span className="text-sm font-medium">{item.label}</span>
            </Link>
          );
        })}
      </div>

      <Card className="mt-6 rounded-[26px] bg-panel-muted/85">
        <div className="space-y-2">
          <span className="text-xs font-semibold uppercase tracking-[0.24em] text-subtle">
            Active Workspace
          </span>
          <h3 className="text-base font-semibold tracking-tight">
            LHC Litigation Desk
          </h3>
          <p className="text-sm leading-6 text-muted-foreground">
            18 active matters, 6 agents online, and 4 urgent procedural items this
            week.
          </p>
        </div>
      </Card>

      <Card className="mt-4 rounded-[26px] border-accent/20 bg-[linear-gradient(180deg,rgba(185,165,124,0.12),rgba(185,165,124,0.03))]">
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <div className="flex size-10 items-center justify-center rounded-2xl bg-foreground/[0.04] text-accent">
              <Building2 className="size-4" />
            </div>
            <div>
              <p className="text-sm font-semibold">Chamber Console</p>
              <p className="text-xs text-muted-foreground">
                Command the multi-agent desk
              </p>
            </div>
          </div>
          <Link
            href="/workspace"
            onClick={onClose}
            className={cn(buttonVariants(), "w-full")}
          >
            Open Workspace
          </Link>
        </div>
      </Card>

      <div className="mt-auto space-y-3 rounded-[24px] border border-line bg-panel-muted/70 p-4">
        <div className="flex items-center gap-3">
          <div className="flex size-10 items-center justify-center rounded-2xl bg-accent/10 text-accent">
            <Gavel className="size-4" />
          </div>
          <div>
            <p className="text-sm font-semibold">Hamza Khan</p>
            <p className="text-xs text-muted-foreground">
              Managing Associate
            </p>
          </div>
        </div>
        <p className="text-xs leading-5 text-muted-foreground">
          Live chamber workspace with database-backed matters, document
          processing, and stored intelligence work product.
        </p>
      </div>
    </aside>
  );
}
