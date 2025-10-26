"use client"

import * as React from "react"
import * as ProgressPrimitive from "@radix-ui/react-progress"

import { cn } from '../../lib/cn'

const Progress = React.forwardRef<
  React.ElementRef<typeof ProgressPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof ProgressPrimitive.Root> & {
    variant?: 'default' | 'glass' | 'premium' | 'glow'
  }
>(({ className, value, variant = 'default', ...props }, ref) => {
  const variantClasses = {
    default: "bg-secondary",
    glass: "bg-white/10 backdrop-blur-md",
    premium: "bg-gradient-to-r from-secondary/50 to-secondary/30 backdrop-blur-md",
    glow: "bg-secondary/80 shadow-glow",
  }

  return (
    <ProgressPrimitive.Root
      ref={ref}
      className={cn(
        "relative h-2 w-full overflow-hidden rounded-full",
        variantClasses[variant],
        className
      )}
      {...props}
    >
      <ProgressPrimitive.Indicator
        className={cn(
          "h-full w-full flex-1 transition-all duration-300 ease-in-out",
          {
            'bg-gradient-to-r from-primary to-primary-foreground': variant === 'default',
            'bg-gradient-to-r from-white/30 to-white/50': variant === 'glass',
            'bg-gradient-to-r from-primary-500 via-secondary-500 to-accent-500': variant === 'premium',
            'bg-gradient-to-r from-primary-400 to-primary-600 shadow-glow': variant === 'glow',
          }
        )}
        style={{ transform: `translateX(-${100 - (value || 0)}%)` }}
      />
    </ProgressPrimitive.Root>
  )
})
Progress.displayName = ProgressPrimitive.Root.displayName

export { Progress }
