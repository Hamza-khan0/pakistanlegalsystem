import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

export const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-2xl border text-sm font-semibold transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/45 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default:
          "border-accent/60 bg-accent text-ink shadow-[0_16px_32px_rgba(187,167,129,0.18)] hover:border-accent hover:bg-accent-soft",
        secondary:
          "border-line-strong bg-panel text-foreground hover:border-accent/40 hover:bg-panel-highlight",
        ghost:
          "border-transparent bg-transparent text-muted-foreground hover:bg-white/4 hover:text-foreground",
        outline:
          "border-line-strong bg-transparent text-foreground hover:border-accent/40 hover:bg-panel-highlight",
      },
      size: {
        sm: "h-9 px-3.5",
        default: "h-11 px-4.5",
        lg: "h-12 px-5",
        icon: "h-10 w-10 p-0",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

export function Button({
  className,
  variant,
  size,
  type = "button",
  ...props
}: ButtonProps) {
  return (
    <button
      className={cn(buttonVariants({ variant, size, className }))}
      type={type}
      {...props}
    />
  );
}
