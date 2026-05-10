import * as React from "react";

import { cn } from "@/lib/utils";

export type TextareaProps = React.TextareaHTMLAttributes<HTMLTextAreaElement>;

export function Textarea({ className, ...props }: TextareaProps) {
  return (
    <textarea
      className={cn(
        "legal-text-wrap flex min-h-[132px] w-full min-w-0 rounded-2xl border border-line bg-white/[0.03] px-4 py-3 text-sm text-foreground outline-none transition-colors placeholder:text-muted-foreground/70 focus:border-accent/50 focus:bg-white/[0.05]",
        className,
      )}
      {...props}
    />
  );
}
