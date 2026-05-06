"use client";

import { cn } from "@/lib/utils";

interface TabOption {
  value: string;
  label: string;
}

interface TabsProps {
  value: string;
  onValueChange: (value: string) => void;
  tabs: TabOption[];
  className?: string;
}

export function Tabs({ value, onValueChange, tabs, className }: TabsProps) {
  return (
    <div
      className={cn(
        "scrollbar-none flex gap-1 overflow-x-auto rounded-[24px] border border-line bg-panel-muted/80 p-1",
        className,
      )}
    >
      {tabs.map((tab) => {
        const active = tab.value === value;

        return (
          <button
            key={tab.value}
            className={cn(
              "min-w-max rounded-[18px] px-4 py-2.5 text-sm font-medium transition-colors",
              active
                ? "bg-white/[0.08] text-foreground shadow-[0_12px_24px_rgba(0,0,0,0.18)]"
                : "text-muted-foreground hover:text-foreground",
            )}
            onClick={() => onValueChange(tab.value)}
            type="button"
          >
            {tab.label}
          </button>
        );
      })}
    </div>
  );
}
