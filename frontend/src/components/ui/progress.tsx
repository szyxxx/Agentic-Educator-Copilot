import * as React from "react";

import { cn } from "@/lib/utils";

export type ProgressProps = React.HTMLAttributes<HTMLDivElement> & {
  value: number;
  colorClassName?: string;
};

const Progress = React.forwardRef<HTMLDivElement, ProgressProps>(
  ({ value, className, colorClassName, ...props }, ref) => (
    <div
      ref={ref}
      className={cn(
        "h-2 w-full overflow-hidden rounded-full bg-slate-100",
        className
      )}
      {...props}
    >
      <div
        className={cn("h-full rounded-full", colorClassName ?? "bg-slate-900")}
        style={{ width: `${Math.min(Math.max(value, 0), 100)}%` }}
      />
    </div>
  )
);

Progress.displayName = "Progress";

export { Progress };
