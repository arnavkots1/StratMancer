'use client'

import { ReactNode, useMemo } from 'react'
import { LazyMotion, MotionConfig, domAnimation } from 'framer-motion'

type MotionProviderProps = {
  children: ReactNode
}

const transition = {
  duration: 0.6,
  ease: [0.16, 1, 0.3, 1],
}

export function MotionProvider({ children }: MotionProviderProps) {
  const features = useMemo(() => domAnimation, [])

  return (
    <MotionConfig reducedMotion="user" transition={transition}>
      {/* LazyMotion keeps the bundle lean by loading minimal animation features */}
      <LazyMotion features={features} strict>
        {children}
      </LazyMotion>
    </MotionConfig>
  )
}

