"use client"

import * as React from "react"
import { cn } from "@/lib/cn"

interface GlowProps {
  children: React.ReactNode
  variant?: 'default' | 'primary' | 'secondary' | 'accent' | 'premium'
  intensity?: 'low' | 'medium' | 'high'
  size?: 'sm' | 'md' | 'lg' | 'xl'
  className?: string
}

const glowVariants = {
  default: "shadow-glow",
  primary: "shadow-lg shadow-primary-500/25",
  secondary: "shadow-lg shadow-secondary-500/25",
  accent: "shadow-lg shadow-accent-500/25",
  premium: "shadow-elite",
}

const glowIntensities = {
  low: "opacity-30",
  medium: "opacity-50",
  high: "opacity-70",
}

const glowSizes = {
  sm: "shadow-sm",
  md: "shadow-md",
  lg: "shadow-lg",
  xl: "shadow-xl",
}

export function Glow({ 
  children, 
  variant = 'default', 
  intensity = 'medium', 
  size = 'md',
  className 
}: GlowProps) {
  return (
    <div
      className={cn(
        "transition-all duration-300",
        glowVariants[variant],
        glowIntensities[intensity],
        glowSizes[size],
        className
      )}
    >
      {children}
    </div>
  )
}

// Elite Glow Effect Component
interface EliteGlowProps {
  children: React.ReactNode
  color?: string
  blur?: number
  spread?: number
  className?: string
}

export function EliteGlow({ 
  children, 
  color = '#3b82f6', 
  blur = 20, 
  spread = 0,
  className 
}: EliteGlowProps) {
  const glowStyle = {
    boxShadow: `0 0 ${blur}px ${spread}px ${color}40`,
  }

  return (
    <div
      className={cn("transition-all duration-300", className)}
      style={glowStyle}
    >
      {children}
    </div>
  )
}

// Animated Glow Component
interface AnimatedGlowProps {
  children: React.ReactNode
  variant?: 'pulse' | 'breathe' | 'shimmer' | 'gradient'
  duration?: number
  className?: string
}

export function AnimatedGlow({ 
  children, 
  variant = 'pulse', 
  duration = 2,
  className 
}: AnimatedGlowProps) {
  const animationClasses = {
    pulse: "animate-pulse-slow",
    breathe: "animate-glow",
    shimmer: "animate-shimmer",
    gradient: "animate-gradient",
  }

  return (
    <div
      className={cn(
        "transition-all duration-300",
        animationClasses[variant],
        className
      )}
      style={{ animationDuration: `${duration}s` }}
    >
      {children}
    </div>
  )
}
