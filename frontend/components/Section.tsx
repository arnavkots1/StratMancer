"use client"

import * as React from "react"
import { cn } from '../lib/cn'

interface SectionProps {
  children: React.ReactNode
  variant?: 'default' | 'glass' | 'premium' | 'hero' | 'feature'
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full'
  className?: string
  id?: string
}

const sectionVariants = {
  default: "bg-background",
  glass: "bg-white/5 backdrop-blur-md border border-white/10",
  premium: "bg-gradient-to-br from-background/80 to-background/60 backdrop-blur-lg border border-white/20",
  hero: "bg-gradient-to-br from-primary-500/10 via-secondary-500/5 to-accent-500/10 backdrop-blur-lg",
  feature: "bg-gradient-to-r from-muted/30 to-muted/10 backdrop-blur-md",
}

const sectionSizes = {
  sm: "py-8",
  md: "py-16",
  lg: "py-24",
  xl: "py-32",
  full: "min-h-screen py-16",
}

export function Section({ 
  children, 
  variant = 'default', 
  size = 'md',
  className,
  id 
}: SectionProps) {
  return (
    <section
      id={id}
      className={cn(
        "relative w-full transition-all duration-300",
        sectionVariants[variant],
        sectionSizes[size],
        className
      )}
    >
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        {children}
      </div>
    </section>
  )
}

// Elite Container Component
interface ContainerProps {
  children: React.ReactNode
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full'
  className?: string
}

const containerSizes = {
  sm: "max-w-2xl",
  md: "max-w-4xl",
  lg: "max-w-6xl",
  xl: "max-w-7xl",
  full: "max-w-full",
}

export function Container({ 
  children, 
  size = 'lg',
  className 
}: ContainerProps) {
  return (
    <div
      className={cn(
        "mx-auto w-full px-4 sm:px-6 lg:px-8",
        containerSizes[size],
        className
      )}
    >
      {children}
    </div>
  )
}

// Elite Grid Component
interface GridProps {
  children: React.ReactNode
  cols?: 1 | 2 | 3 | 4 | 5 | 6
  gap?: 'sm' | 'md' | 'lg' | 'xl'
  className?: string
}

const gridCols = {
  1: "grid-cols-1",
  2: "grid-cols-1 md:grid-cols-2",
  3: "grid-cols-1 md:grid-cols-2 lg:grid-cols-3",
  4: "grid-cols-1 md:grid-cols-2 lg:grid-cols-4",
  5: "grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5",
  6: "grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6",
}

const gridGaps = {
  sm: "gap-4",
  md: "gap-6",
  lg: "gap-8",
  xl: "gap-12",
}

export function Grid({ 
  children, 
  cols = 3,
  gap = 'md',
  className 
}: GridProps) {
  return (
    <div
      className={cn(
        "grid",
        gridCols[cols],
        gridGaps[gap],
        className
      )}
    >
      {children}
    </div>
  )
}

// Elite Flex Component
interface FlexProps {
  children: React.ReactNode
  direction?: 'row' | 'col' | 'row-reverse' | 'col-reverse'
  align?: 'start' | 'center' | 'end' | 'stretch' | 'baseline'
  justify?: 'start' | 'center' | 'end' | 'between' | 'around' | 'evenly'
  gap?: 'sm' | 'md' | 'lg' | 'xl'
  wrap?: boolean
  className?: string
}

const flexDirections = {
  row: "flex-row",
  col: "flex-col",
  'row-reverse': "flex-row-reverse",
  'col-reverse': "flex-col-reverse",
}

const flexAligns = {
  start: "items-start",
  center: "items-center",
  end: "items-end",
  stretch: "items-stretch",
  baseline: "items-baseline",
}

const flexJustifies = {
  start: "justify-start",
  center: "justify-center",
  end: "justify-end",
  between: "justify-between",
  around: "justify-around",
  evenly: "justify-evenly",
}

const flexGaps = {
  sm: "gap-2",
  md: "gap-4",
  lg: "gap-6",
  xl: "gap-8",
}

export function Flex({ 
  children, 
  direction = 'row',
  align = 'center',
  justify = 'start',
  gap = 'md',
  wrap = false,
  className 
}: FlexProps) {
  return (
    <div
      className={cn(
        "flex",
        flexDirections[direction],
        flexAligns[align],
        flexJustifies[justify],
        flexGaps[gap],
        wrap && "flex-wrap",
        className
      )}
    >
      {children}
    </div>
  )
}
