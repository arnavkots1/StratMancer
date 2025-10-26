/**
 * Cinematic Framer Motion Variants
 *
 * Shared motion blueprints for the StratMancer experience.
 * Heavy motion automatically collapses when the user prefers reduced motion.
 */

import { Variants } from 'framer-motion'

const EASE_EXPO = [0.16, 1, 0.3, 1]
const EASE_SINE = [0.12, 0.32, 0.24, 1]

const REDUCED_VARIANTS: Variants = {
  initial: { opacity: 0 },
  animate: { opacity: 1, transition: { duration: 0.2, ease: 'linear' } },
  exit: { opacity: 0, transition: { duration: 0.2, ease: 'linear' } },
}

export function prefersReducedMotion(): boolean {
  if (typeof window === 'undefined') return false
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

function maybeReduce(variants: Variants): Variants {
  return prefersReducedMotion() ? REDUCED_VARIANTS : variants
}

export const fadeUp: Variants = {
  initial: { opacity: 0, y: 32 },
  animate: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.7, ease: EASE_EXPO },
  },
  exit: {
    opacity: 0,
    y: -24,
    transition: { duration: 0.35, ease: EASE_SINE },
  },
}

export function slideIn(
  direction: 'left' | 'right' | 'up' | 'down' = 'up',
): Variants {
  const distance = 48
  const axis = direction === 'left' || direction === 'right' ? 'x' : 'y'
  const offset =
    direction === 'left' || direction === 'up' ? -distance : distance

  const initial = { opacity: 0, ...(axis === 'x' ? { x: offset } : { y: offset }) }
  const animate = { 
    opacity: 1, 
    ...(axis === 'x' ? { x: 0 } : { y: 0 }),
    transition: {
      type: 'spring' as const,
      stiffness: 180,
      damping: 28,
      mass: 0.8,
    },
  }
  const exit = { 
    opacity: 0, 
    ...(axis === 'x' ? { x: offset * -0.75 } : { y: offset * -0.75 }),
    transition: { duration: 0.35, ease: EASE_SINE },
  }

  return maybeReduce({ initial, animate, exit })
}

export const scaleIn: Variants = maybeReduce({
  initial: { opacity: 0, scale: 0.88, filter: 'blur(6px)' },
  animate: {
    opacity: 1,
    scale: 1,
    filter: 'blur(0px)',
    transition: { duration: 0.6, ease: EASE_EXPO },
  },
  exit: {
    opacity: 0,
    scale: 0.94,
    filter: 'blur(4px)',
    transition: { duration: 0.3, ease: EASE_SINE },
  },
})

export const stagger: Variants = {
  initial: {},
  animate: {
    transition: {
      staggerChildren: 0.12,
      delayChildren: 0.08,
    },
  },
}

export const hologramRotate: Variants = prefersReducedMotion()
  ? REDUCED_VARIANTS
  : {
      initial: {
        opacity: 0,
        scale: 1,
        rotateX: 0,
        rotateY: 0,
        rotateZ: 0,
        filter: 'brightness(1)',
      },
      animate: {
        opacity: 1,
        scale: 1,
        rotateX: 0,
        rotateY: 0,
        rotateZ: 0,
        filter: 'brightness(1)',
        transition: {
          duration: 0.3,
          ease: 'easeOut',
        },
      },
      exit: {
        opacity: 0,
        scale: 1,
        rotateX: 0,
        rotateY: 0,
        rotateZ: 0,
        transition: { duration: 0.2, ease: 'easeIn' },
      },
    }

export const particleDrift: Variants = prefersReducedMotion()
  ? REDUCED_VARIANTS
  : {
      initial: { opacity: 0 },
      animate: {
        opacity: 1,
        transition: {
          duration: 1.2,
          ease: EASE_SINE,
          when: 'beforeChildren',
        },
      },
      exit: {
        opacity: 0,
        transition: { duration: 0.4, ease: 'linear' },
      },
    }

export const motionPresets = {
  page: fadeUp,
  card: scaleIn,
  list: stagger,
}

// Legacy compatibility. Other imports still resolve to the new presets.
export const eliteMotionPresets = motionPresets
