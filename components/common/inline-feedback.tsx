import { AlertTriangle, CheckCircle2, Info } from "lucide-react";

import { cn } from "@/lib/utils";

type FeedbackTone = "error" | "success" | "info";

const toneStyles: Record<
  FeedbackTone,
  { wrapper: string; icon: typeof AlertTriangle }
> = {
  error: {
    wrapper:
      "border-rose-400/20 bg-rose-400/8 text-rose-100",
    icon: AlertTriangle,
  },
  success: {
    wrapper:
      "border-emerald-400/20 bg-emerald-400/8 text-emerald-100",
    icon: CheckCircle2,
  },
  info: {
    wrapper:
      "border-sky-400/20 bg-sky-400/8 text-sky-100",
    icon: Info,
  },
};

interface InlineFeedbackProps {
  tone: FeedbackTone;
  message: string;
  title?: string;
  className?: string;
}

export function InlineFeedback({
  tone,
  message,
  title,
  className,
}: InlineFeedbackProps) {
  const Icon = toneStyles[tone].icon;

  return (
    <div
      className={cn(
        "rounded-2xl border px-4 py-3",
        toneStyles[tone].wrapper,
        className,
      )}
    >
      <div className="flex items-start gap-3">
        <Icon className="mt-0.5 size-4 shrink-0" />
        <div className="space-y-1">
          {title ? (
            <p className="text-sm font-semibold tracking-tight">{title}</p>
          ) : null}
          <p className="text-sm leading-6">{message}</p>
        </div>
      </div>
    </div>
  );
}
