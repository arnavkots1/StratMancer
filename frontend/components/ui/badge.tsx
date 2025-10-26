import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from '../../lib/cn'

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      variant: {
        default:
          "border-transparent bg-primary text-primary-foreground hover:bg-primary/80",
        secondary:
          "border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80",
        destructive:
          "border-transparent bg-destructive text-destructive-foreground hover:bg-destructive/80",
        outline: "text-foreground",
        success:
          "border-transparent bg-success-500/10 text-success-400 border-success-500/20 hover:bg-success-500/20",
        warning:
          "border-transparent bg-warning-500/10 text-warning-400 border-warning-500/20 hover:bg-warning-500/20",
        error:
          "border-transparent bg-error-500/10 text-error-400 border-error-500/20 hover:bg-error-500/20",
        glass:
          "border-white/20 bg-white/5 backdrop-blur-md text-foreground hover:bg-white/10",
        glow:
          "border-primary/30 bg-primary/10 text-primary-400 shadow-glow hover:bg-primary/20",
        premium:
          "border-transparent bg-gradient-to-r from-primary-500/20 to-secondary-500/20 text-primary-foreground hover:from-primary-500/30 hover:to-secondary-500/30",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  )
}

export { Badge, badgeVariants }
