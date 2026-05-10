import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

const cardVariants = cva(
  "min-w-0 rounded-[28px] border border-line bg-panel/90 text-foreground shadow-[0_24px_70px_rgba(3,8,19,0.32)] backdrop-blur-xl",
  {
    variants: {
      padding: {
        none: "",
        sm: "p-4",
        default: "p-5",
        lg: "p-6",
      },
      tone: {
        default: "",
        muted: "bg-panel-muted/90",
        glass: "bg-white/[0.04]",
      },
    },
    defaultVariants: {
      padding: "default",
      tone: "default",
    },
  },
);

export interface CardProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof cardVariants> {}

export function Card({ className, padding, tone, ...props }: CardProps) {
  return (
    <div className={cn(cardVariants({ padding, tone, className }))} {...props} />
  );
}
