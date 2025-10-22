'use client'

import { useEffect, useRef } from 'react'
import { useReducedMotion } from 'framer-motion'
import { cn } from '@/lib/cn'

type HologramParticlesProps = {
  className?: string
  density?: number
}

type Particle = {
  x: number
  y: number
  size: number
  baseSpeed: number
  offset: number
  drift: number
}

const MAX_PARTICLES = 200
const BASE_PARTICLES = 160

export function HologramParticles({
  className,
  density = 1,
}: HologramParticlesProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  const reduceMotion = useReducedMotion()

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const dpr = window.devicePixelRatio || 1
    let animationFrame: number | null = null
    let width = 0
    let height = 0
    let time = 0
    const pointer = { x: 0, y: 0, active: false }

    // Limit particle count to stay under 200 for mobile/GPU headroom
    const particleCount = Math.min(
      Math.floor(BASE_PARTICLES * density),
      MAX_PARTICLES,
    )
    const particles: Particle[] = new Array(particleCount)
      .fill(null)
      .map(() => ({
        x: 0,
        y: 0,
        size: 0.6 + Math.random() * 1.4,
        baseSpeed: 0.4 + Math.random() * 0.6,
        offset: Math.random() * Math.PI * 2,
        drift: 0.6 + Math.random() * 0.9,
      }))

    const resize = () => {
      width = canvas.offsetWidth
      height = canvas.offsetHeight
      canvas.width = width * dpr
      canvas.height = height * dpr
      ctx.setTransform(1, 0, 0, 1, 0, 0)
      ctx.scale(dpr, dpr)

      for (const particle of particles) {
        particle.x = Math.random() * width
        particle.y = Math.random() * height
      }
    }

    resize()

    const handlePointerMove = (event: PointerEvent) => {
      pointer.x = event.clientX
      pointer.y = event.clientY
      pointer.active = true
    }

    const handlePointerLeave = () => {
      pointer.active = false
    }

    window.addEventListener('resize', resize)
    window.addEventListener('pointermove', handlePointerMove, { passive: true })
    window.addEventListener('pointerleave', handlePointerLeave)

    const renderStaticField = () => {
      ctx.clearRect(0, 0, width, height)
      const gradient = ctx.createLinearGradient(0, 0, width, height)
      gradient.addColorStop(0, 'rgba(124, 58, 237, 0.25)')
      gradient.addColorStop(0.4, 'rgba(6, 182, 212, 0.18)')
      gradient.addColorStop(1, 'rgba(14, 197, 240, 0.12)')
      ctx.fillStyle = gradient
      ctx.fillRect(0, 0, width, height)
      ctx.fillStyle = 'rgba(255,255,255,0.08)'

      for (const particle of particles) {
        ctx.beginPath()
        ctx.arc(particle.x, particle.y, particle.size * 1.6, 0, Math.PI * 2)
        ctx.fill()
      }
    }

    const render = () => {
      time += 0.005
      ctx.clearRect(0, 0, width, height)

      for (const particle of particles) {
        const noise = Math.sin(time + particle.offset) * 0.8
        const driftX = Math.cos(time * particle.drift + particle.offset) * 0.9
        const driftY = Math.sin(time * (particle.drift * 0.8)) * 0.6

        particle.x += driftX + noise
        particle.y += driftY + noise * 0.4

        if (pointer.active) {
          const dx = pointer.x - particle.x
          const dy = pointer.y - particle.y
          const distance = Math.sqrt(dx * dx + dy * dy)
          if (distance < 160) {
            const force = (160 - distance) / 160
            particle.x -= dx * force * 0.05
            particle.y -= dy * force * 0.05
          }
        }

        if (particle.x < -20) particle.x = width + 20
        if (particle.x > width + 20) particle.x = -20
        if (particle.y < -20) particle.y = height + 20
        if (particle.y > height + 20) particle.y = -20

        const gradient = ctx.createRadialGradient(
          particle.x,
          particle.y,
          0,
          particle.x,
          particle.y,
          particle.size * 8,
        )
        gradient.addColorStop(0, 'rgba(255,255,255,0.35)')
        gradient.addColorStop(0.3, 'rgba(124,58,237,0.2)')
        gradient.addColorStop(1, 'rgba(124,58,237,0)')

        ctx.fillStyle = gradient
        ctx.beginPath()
        ctx.arc(particle.x, particle.y, particle.size * 6, 0, Math.PI * 2)
        ctx.fill()
      }

      animationFrame = window.requestAnimationFrame(render)
    }

    if (reduceMotion) {
      renderStaticField()
      return () => {
        window.removeEventListener('resize', resize)
        window.removeEventListener('pointermove', handlePointerMove)
        window.removeEventListener('pointerleave', handlePointerLeave)
      }
    }

    // The animation runs on the compositor thread via requestAnimationFrame
    render()

    return () => {
      if (animationFrame) {
        cancelAnimationFrame(animationFrame)
      }
      window.removeEventListener('resize', resize)
      window.removeEventListener('pointermove', handlePointerMove)
      window.removeEventListener('pointerleave', handlePointerLeave)
    }
  }, [density, reduceMotion])

  return <canvas ref={canvasRef} className={cn('absolute inset-0 h-full w-full', className)} />
}
