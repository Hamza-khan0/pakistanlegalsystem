import Link from "next/link";
import { ArrowLeft, Scale } from "lucide-react";

export default function NotFound() {
  return (
    <div className="flex min-h-screen items-center justify-center px-4 py-12">
      <div className="w-full max-w-xl rounded-[32px] border border-line bg-panel/95 p-8 text-center shadow-[0_24px_70px_rgba(3,8,19,0.32)]">
        <div className="mx-auto flex size-14 items-center justify-center rounded-3xl border border-accent/30 bg-accent/10 text-accent">
          <Scale className="size-6" />
        </div>
        <h1 className="mt-6 text-3xl font-semibold tracking-[-0.04em] text-foreground">
          Matter not found
        </h1>
        <p className="mt-3 text-sm leading-7 text-muted-foreground">
          The requested page is not available in the current AI Legal Chambers workspace.
        </p>
        <Link
          href="/dashboard"
          className="mt-6 inline-flex h-11 items-center justify-center gap-2 rounded-2xl border border-accent/60 bg-accent px-4.5 text-sm font-semibold text-ink shadow-[0_16px_32px_rgba(187,167,129,0.18)] transition-colors hover:bg-accent-soft"
        >
          <ArrowLeft className="size-4" />
          Return to dashboard
        </Link>
      </div>
    </div>
  );
}
