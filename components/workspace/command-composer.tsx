"use client";

import { ArrowUpRight } from "lucide-react";

import { Button } from "@/components/ui/button";

interface CommandComposerProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  loading: boolean;
}

export function CommandComposer({
  value,
  onChange,
  onSubmit,
  loading,
}: CommandComposerProps) {
  return (
    <div className="rounded-[28px] border border-line bg-panel p-4">
      <div className="rounded-[22px] border border-line bg-[#0f151d] p-4">
        <textarea
          className="min-h-[110px] w-full resize-none bg-transparent text-sm leading-7 text-foreground outline-none placeholder:text-muted-foreground/70"
          placeholder="Issue a legal chamber command. Example: Draft preliminary objections in the Green Valley matter and identify missing annexures."
          value={value}
          onChange={(event) => onChange(event.target.value)}
        />
      </div>
      <div className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-sm text-muted-foreground">
          Structured chamber outputs only. Commands now run against live matter data and persist the result.
        </p>
        <Button onClick={onSubmit} disabled={!value.trim() || loading}>
          <ArrowUpRight className="size-4" />
          {loading ? "Running chamber..." : "Run chamber command"}
        </Button>
      </div>
    </div>
  );
}
