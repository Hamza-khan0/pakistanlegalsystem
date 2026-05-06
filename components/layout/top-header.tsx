"use client";

import Link from "next/link";
import { Bell, Menu, Plus, Search } from "lucide-react";

import { buttonVariants } from "@/components/ui/button";

interface TopHeaderProps {
  onOpenSidebar: () => void;
}

export function TopHeader({ onOpenSidebar }: TopHeaderProps) {
  return (
    <header className="sticky top-0 z-30 border-b border-line bg-background/85 backdrop-blur-2xl">
      <div className="flex items-center gap-4 px-4 py-4 sm:px-6 lg:px-8">
        <button
          aria-label="Open sidebar"
          className="flex size-10 items-center justify-center rounded-2xl border border-line bg-panel text-muted-foreground transition-colors hover:text-foreground lg:hidden"
          onClick={onOpenSidebar}
          type="button"
        >
          <Menu className="size-4" />
        </button>

        <div className="hidden min-w-0 lg:block">
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-subtle">
            Workspace
          </p>
          <h1 className="truncate text-sm font-medium text-foreground">
            AI Legal Chambers / Lahore Litigation Cell
          </h1>
        </div>

        <div className="relative hidden min-w-0 flex-1 items-center lg:flex">
          <Search className="pointer-events-none absolute left-4 size-4 text-muted-foreground" />
          <input
            className="h-11 w-full rounded-2xl border border-line bg-panel px-11 text-sm text-foreground outline-none transition-colors placeholder:text-muted-foreground/70 focus:border-accent/35"
            placeholder="Global search is staged for a future phase"
            readOnly
            title="Global search is scheduled for a future phase."
            type="text"
          />
        </div>

        <div className="ml-auto flex items-center gap-3">
          <button
            aria-label="Notifications"
            className="relative flex size-10 items-center justify-center rounded-2xl border border-line bg-panel text-muted-foreground transition-colors hover:text-foreground"
            disabled
            title="Notification center is scheduled for a future phase."
            type="button"
          >
            <Bell className="size-4" />
            <span className="absolute top-2 right-2 size-2 rounded-full bg-accent" />
          </button>

          <span className="hidden text-xs font-medium text-muted-foreground xl:block">
            Live alerts
          </span>

          <Link href="/cases?create=1" className={buttonVariants({ size: "sm" })}>
            <Plus className="size-4" />
            New Case
          </Link>

          <div className="flex items-center gap-3 rounded-2xl border border-line bg-panel px-3 py-2">
            <div className="flex size-9 items-center justify-center rounded-2xl bg-accent/10 text-xs font-semibold uppercase tracking-[0.2em] text-accent">
              HK
            </div>
            <div className="hidden xl:block">
              <p className="text-sm font-medium text-foreground">Hamza Khan</p>
              <p className="text-xs text-muted-foreground">Managing Associate</p>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
