import * as React from "react";

import { cn } from "@/lib/utils";

type ButtonVariant =
  | "default"
  | "outline"
  | "ghost"
  | "secondary"
  | "danger"
  | "soft";

type ButtonSize = "sm" | "md" | "lg";

const baseStyles =
  "inline-flex items-center justify-center gap-2 rounded-full font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-500/60 disabled:pointer-events-none disabled:opacity-50";

const variantStyles: Record<ButtonVariant, string> = {
  default:
    "bg-slate-900 text-white hover:bg-slate-800 shadow-sm shadow-slate-900/20",
  outline:
    "border border-slate-200 text-slate-700 hover:border-slate-900 hover:text-slate-900",
  ghost:
    "text-slate-600 hover:bg-slate-100 hover:text-slate-900",
  secondary:
    "bg-teal-600 text-white hover:bg-teal-500 shadow-sm shadow-teal-600/20",
  danger:
    "bg-rose-600 text-white hover:bg-rose-500 shadow-sm shadow-rose-600/20",
  soft:
    "bg-teal-50 text-teal-800 hover:bg-teal-100 border border-teal-100",
};

const sizeStyles: Record<ButtonSize, string> = {
  sm: "h-9 px-4 text-xs",
  md: "h-10 px-5 text-sm",
  lg: "h-12 px-6 text-sm",
};

export type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: ButtonVariant;
  size?: ButtonSize;
};

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", size = "md", ...props }, ref) => (
    <button
      ref={ref}
      className={cn(baseStyles, variantStyles[variant], sizeStyles[size], className)}
      {...props}
    />
  )
);

Button.displayName = "Button";

export { Button };
