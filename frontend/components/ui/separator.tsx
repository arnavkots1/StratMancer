"use client"

import * as React from "react"
import * as SeparatorPrimitive from "@radix-ui/react-separator"

import { cn } from '../../lib/cn'

const Separator = React.forwardRef<
  React.ElementRef<typeof SeparatorPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof SeparatorPrimitive.Root> & {
    variant?: 'default' | 'glass' | 'premium' | 'glow'
  }
>(
  (
    { className, orientation = "horizontal", decorative = true, variant = 'default', ...props },
    ref
  ) => {
    const variantClasses = {
      default: "bg-border",
      glass: "bg-white/20",
      premium: "bg-gradient-to-r from-transparent via-border to-transparent",
      glow: "bg-gradient-to-r from-transparent via-primary/50 to-transparent shadow-glow",
    }

    return (
      <SeparatorPrimitive.Root
        ref={ref}
        decorative={decorative}
        orientation={orientation}
        className={cn(
          "shrink-0 transition-all duration-300",
          orientation === "horizontal" ? "h-[1px] w-full" : "h-full w-[1px]",
          variantClasses[variant],
          className
        )}
        {...props}
      />
    )
  }
)
Separator.displayName = SeparatorPrimitive.Root.displayName

export { Separator }
