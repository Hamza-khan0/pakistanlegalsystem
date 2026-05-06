import { AlertTriangle } from "lucide-react";

import { Card } from "@/components/ui/card";

interface ErrorStateProps {
  title: string;
  message: string;
}

export function ErrorState({ title, message }: ErrorStateProps) {
  return (
    <Card className="flex flex-col items-start gap-4 rounded-[30px] border-amber-400/20 bg-amber-400/8">
      <div className="flex size-12 items-center justify-center rounded-2xl border border-amber-400/20 bg-amber-400/10 text-amber-200">
        <AlertTriangle className="size-5" />
      </div>
      <div className="space-y-2">
        <h2 className="text-lg font-semibold tracking-tight text-foreground">
          {title}
        </h2>
        <p className="max-w-2xl text-sm leading-6 text-muted-foreground">
          {message}
        </p>
      </div>
    </Card>
  );
}
