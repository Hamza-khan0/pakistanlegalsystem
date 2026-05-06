import type { ReactNode } from "react";

import { Badge } from "@/components/ui/badge";

interface PageHeaderProps {
  title: string;
  description: string;
  eyebrow?: string;
  meta?: string[];
  actions?: ReactNode;
}

export function PageHeader({
  title,
  description,
  eyebrow,
  meta,
  actions,
}: PageHeaderProps) {
  return (
    <div className="flex flex-col gap-5 border-b border-line pb-6 lg:flex-row lg:items-end lg:justify-between">
      <div className="space-y-4">
        {eyebrow ? (
          <span className="text-xs font-semibold uppercase tracking-[0.28em] text-accent">
            {eyebrow}
          </span>
        ) : null}
        <div className="space-y-2">
          <h1 className="text-3xl font-semibold tracking-[-0.04em] text-foreground sm:text-[2rem]">
            {title}
          </h1>
          <p className="max-w-3xl text-sm leading-7 text-muted-foreground sm:text-[15px]">
            {description}
          </p>
        </div>
        {meta?.length ? (
          <div className="flex flex-wrap gap-2">
            {meta.map((item) => (
              <Badge key={item} variant="muted">
                {item}
              </Badge>
            ))}
          </div>
        ) : null}
      </div>
      {actions ? <div className="flex flex-wrap gap-3">{actions}</div> : null}
    </div>
  );
}
