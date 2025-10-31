"use client"

import { useEffect, useMemo, useState, useCallback } from "react"
import Link from "next/link"
import Image from "next/image"
import { m, useReducedMotion } from "framer-motion"
import { ArrowUpRight, Sparkles, Zap } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Container } from "@/components/Section"
import { fadeUp, particleDrift, scaleIn, stagger } from '../lib/motion'
// import { trackUserInteraction, trackFeatureUsage } from '../lib/analytics'
import {
  getFavorPercentage,
  getLandingData,
  type RealMetrics,
  type ChampionStats,
} from "@/lib/realData"

const HIGHLIGHTS = [
  "Predict every phase of the draft with live win probabilities.",
  "Adapt to any ladder with rank-aware champion intelligence.",
  "Uncover balancing shifts with meta visualizations.",
  "Trust recommendations sourced from thousands of curated matches.",
] as const

export function Hero() {
  const [championIndex, setChampionIndex] = useState(0)
  const [champions, setChampions] = useState<ChampionStats[]>([])
  const [metrics, setMetrics] = useState<RealMetrics | null>(null)
  const [loading, setLoading] = useState(true)
  const reduceMotion = useReducedMotion()
  
  const activeChampion = champions[championIndex] || {
    name: "Ahri",
    role: "Mid Mage",
    winRate: 52.3,
    pickRate: 8.7,
    banRate: 12.4,
    image: "https://ddragon.leagueoflegends.com/cdn/img/champion/splash/Ahri_0.jpg"
  }

  // Load real data on mount and refresh periodically
  useEffect(() => {
    const controller = new AbortController()

    const loadData = async (forceRefresh = false) => {
      try {
        const data = await getLandingData({ signal: controller.signal, forceRefresh })
        setChampions(data.champions)
        setMetrics(data.metrics)
      } catch (error) {
        if ((error as Error).name !== "AbortError") {
          console.error("Failed to load landing data:", error)
        }
      } finally {
        setLoading(false)
      }
    }

    loadData()

    // Refresh data every 10 seconds
    const refreshInterval = setInterval(() => {
      loadData(true)
    }, 10000)

    return () => {
      controller.abort()
      clearInterval(refreshInterval)
    }
  }, [])

  // Champion rotation for hologram - optimized with useCallback
  const rotateChampion = useCallback(() => {
    if (champions.length === 0) return
    setChampionIndex((index) => (index + 1) % champions.length)
  }, [champions.length])

  useEffect(() => {
    if (reduceMotion || champions.length === 0) return
    const interval = window.setInterval(rotateChampion, 6000) // Set to 6 seconds per champion (at least 5 seconds as requested)
    return () => window.clearInterval(interval)
  }, [rotateChampion, reduceMotion, champions.length])


  // Create metrics array from real data
  const realMetrics = useMemo(() => {
    if (!metrics)
      return [
        { label: "Average Win Delta", value: "+4.4%", tone: "text-emerald-300" },
        { label: "Model Confidence", value: "93.5%", tone: "text-sky-300" },
        { label: "Response Time", value: "180ms", tone: "text-amber-300" },
      ]

    return [
      {
        label: "Average Win Delta",
        value: `+${metrics.averageWinDelta.toFixed(1)}%`,
        tone: "text-emerald-300",
      },
      {
        label: "Model Confidence",
        value: `${metrics.modelConfidence.toFixed(1)}%`,
        tone: "text-sky-300",
      },
      {
        label: "Response Time",
        value: `${Math.round(metrics.responseTime)}ms`,
        tone: "text-amber-300",
      },
    ]
  }, [metrics])

  const liveForecast = metrics?.liveWinForecast

  return (
    <section className="relative isolate overflow-hidden">
      <m.div
        className="absolute inset-0 -z-10"
        variants={particleDrift}
        initial="initial"
        animate="animate"
      >
        {/* Figma Background - Exact Replication */}
        <div className="absolute inset-0 bg-gradient-to-b from-[#0b0f17] via-[#1a1f2e] to-[#0b0f17]" />
        
        {/* Grid overlay */}
        <div className="absolute inset-0 grid-overlay opacity-30" />
        
        {/* Hero image with parallax */}
        <m.div
          className="absolute inset-0 opacity-20"
          style={{
            backgroundImage: `url(https://images.unsplash.com/photo-1604171256342-9945bfa74c4e?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxlc3BvcnRzJTIwZ2FtaW5nJTIwZGFya3xlbnwxfHx8fDE3NjEwMzIxMzR8MA&ixlib=rb-4.1.0&q=80&w=1080&utm_source=figma&utm_medium=referral)`,
            backgroundSize: "cover",
            backgroundPosition: "center",
          }}
          animate={{
            scale: [1, 1.05, 1],
          }}
          transition={{
            duration: 20,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />

        {/* Gradient orbs */}
        <m.div
          className="absolute w-96 h-96 rounded-full bg-[#ea3943] opacity-20 blur-3xl"
          animate={{
            x: [0, 20, 0],
            y: [0, -20, 0],
          }}
          transition={{
            duration: 8,
            repeat: Infinity,
            ease: "easeInOut",
          }}
          style={{ top: "20%", left: "10%" }}
        />
        <m.div
          className="absolute w-96 h-96 rounded-full bg-[#d946ef] opacity-20 blur-3xl"
          animate={{
            x: [0, -20, 0],
            y: [0, 20, 0],
          }}
          transition={{
            duration: 10,
            repeat: Infinity,
            ease: "easeInOut",
          }}
          style={{ bottom: "20%", right: "10%" }}
        />

        {/* Scattered Keyboard Keys - Enhanced Background */}
        <div className="absolute inset-0">
          <div className="absolute top-1/4 left-1/4 text-red-500/30 text-3xl font-mono blur-sm">F2</div>
          <div className="absolute top-1/3 right-1/3 text-red-500/30 text-3xl font-mono blur-sm">F3</div>
          <div className="absolute top-1/2 left-1/6 text-red-500/30 text-3xl font-mono blur-sm">F4</div>
          <div className="absolute top-2/3 right-1/4 text-red-500/30 text-3xl font-mono blur-sm">%5</div>
          <div className="absolute bottom-1/3 left-1/3 text-red-500/30 text-3xl font-mono blur-sm">U</div>
          <div className="absolute bottom-1/4 right-1/6 text-red-500/30 text-3xl font-mono blur-sm">K</div>
          <div className="absolute top-1/6 right-1/2 text-red-500/30 text-3xl font-mono blur-sm">M</div>
          <div className="absolute bottom-1/2 left-1/2 text-red-500/30 text-3xl font-mono blur-sm">N</div>
          <div className="absolute top-3/4 left-1/5 text-red-500/30 text-3xl font-mono blur-sm">R</div>
          <div className="absolute top-1/5 right-1/5 text-red-500/30 text-3xl font-mono blur-sm">20</div>
          <div className="absolute bottom-1/5 left-1/4 text-red-500/30 text-3xl font-mono blur-sm">F1</div>
          <div className="absolute top-2/5 right-1/6 text-red-500/30 text-3xl font-mono blur-sm">F5</div>
          <div className="absolute bottom-2/5 left-2/3 text-red-500/30 text-3xl font-mono blur-sm">F6</div>
          <div className="absolute top-1/8 left-1/3 text-red-500/30 text-3xl font-mono blur-sm">F7</div>
          <div className="absolute bottom-1/8 right-1/3 text-red-500/30 text-3xl font-mono blur-sm">F8</div>
          <div className="absolute top-3/5 left-1/8 text-red-500/30 text-3xl font-mono blur-sm">F9</div>
          <div className="absolute bottom-3/5 right-1/8 text-red-500/30 text-3xl font-mono blur-sm">F10</div>
        </div>
      </m.div>

      <Container size="xl" className="relative z-10 py-24 lg:py-32">
        <div className="grid items-center gap-16 lg:grid-cols-[minmax(0,1.05fr)_minmax(0,0.95fr)]">
          <m.div
            initial="initial"
            animate="animate"
            variants={stagger}
            className="space-y-10"
          >
            <m.div
              variants={fadeUp}
              className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-xs font-semibold uppercase tracking-[0.24em] text-white/80 backdrop-blur"
            >
              <Sparkles className="h-4 w-4 text-accent" />
              RiftAI Tactical Intelligence
            </m.div>

            <div className="space-y-6">
              <m.h1
                variants={fadeUp}
                className="text-balance text-4xl font-semibold leading-[1.05] text-white md:text-6xl lg:text-7xl"
              >
                Master the Rift with{" "}
                <span className="text-transparent bg-gradient-to-r from-primary via-secondary to-accent bg-clip-text">
                  AI Precision
                </span>
                .
              </m.h1>

              <m.p
                variants={fadeUp}
                className="max-w-2xl text-lg text-white/70 md:text-xl"
              >
                RiftAI is your on-demand strategist—forecasting drafts, reading the
                meta, and guiding every decision with cinematic clarity and competitive
                intent.
              </m.p>
            </div>

            <m.div
              variants={fadeUp}
              className="flex flex-col gap-4 sm:flex-row sm:items-center sm:gap-6"
            >
              <Button
                asChild
                size="xl"
                className="group relative overflow-hidden px-10 py-4 text-base shadow-[0_0_45px_rgba(124,58,237,0.4)]"
              >
                <Link href="/draft">
                  <span className="flex items-center gap-3">
                    <Zap className="h-5 w-5 text-accent transition-transform duration-200 group-hover:scale-110" />
                    Try Draft Analyzer
                    <ArrowUpRight className="h-5 w-5 transition-transform duration-200 group-hover:translate-x-1 group-hover:-translate-y-1" />
                  </span>
                </Link>
              </Button>
              <Button
                asChild
                variant="outline"
                size="xl"
                className="border-white/30 bg-white/5 px-10 py-4 text-base text-white/80 hover:bg-white/10"
              >
                <Link href="/meta">Explore Meta</Link>
              </Button>
            </m.div>

            <m.ul variants={fadeUp} className="space-y-3 text-sm text-white/70 lg:text-base">
              {HIGHLIGHTS.map((highlight) => (
                <li key={highlight} className="flex items-start gap-3">
                  <span className="mt-[6px] h-[6px] w-[6px] rounded-full bg-gradient-to-r from-primary to-secondary" />
                  <span>{highlight}</span>
                </li>
              ))}
            </m.ul>

            <m.dl
              variants={stagger}
              className="grid gap-5 rounded-3xl border border-white/10 bg-white/5 p-6 backdrop-blur sm:grid-cols-3"
            >
              {realMetrics.map((metric) => (
                <m.div key={metric.label} variants={fadeUp} className="space-y-2">
                  <dt className="text-xs uppercase tracking-[0.24em] text-white/40">
                    {metric.label}
                  </dt>
                  <dd className={`text-2xl font-semibold ${metric.tone}`}>
                    {loading ? (
                      <div className="h-8 w-16 animate-pulse bg-white/20 rounded" />
                    ) : (
                      metric.value
                    )}
                  </dd>
                  {metric.label === "Model Confidence" && !loading && (
                    <div className="text-xs text-white/50 mt-1">
                  Low due to small dataset 
                    </div>
                  )}
                </m.div>
              ))}
            </m.dl>
          </m.div>

          <m.div
            initial="initial"
            animate="animate"
            variants={scaleIn}
            className="relative flex justify-center"
          >
            <div className="relative w-full max-w-[460px] rounded-[calc(var(--radius)*1.1)] border border-white/15 bg-gradient-to-br from-white/15 via-white/10 to-transparent p-6 shadow-[0_18px_60px_-28px_rgba(0,0,0,0.65)]">
              <div className="absolute inset-0 neon-border opacity-70" />
              <div className="relative overflow-hidden rounded-[calc(var(--radius)*0.9)] border border-white/10 bg-black/5">
                <div className="relative aspect-[4/5] w-full">
                  <Image
                    src={activeChampion.image}
                    alt={activeChampion.name}
                    fill
                    priority
                    sizes="(min-width: 1024px) 460px, 80vw"
                    className="object-cover object-top brightness-110"
                    style={{ objectPosition: 'center 10%' }}
                    quality={75}
                    loading="eager"
                  />
                </div>

                <div className="absolute inset-0" aria-hidden="true">
                  <div className="absolute inset-x-0 bottom-0 h-24 bg-gradient-to-t from-[#05080f] via-transparent to-transparent" />
                  <m.div
                    initial={{ opacity: 0, y: 24 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.4, duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
                    className="absolute inset-x-6 bottom-6 rounded-2xl border border-white/15 bg-black/40 p-4"
                  >
                    <div className="flex items-center justify-between text-xs uppercase tracking-[0.24em] text-white/50">
                      <span>Current Focus</span>
                      <span className="text-white/40">Hologram Feed</span>
                    </div>
                    <div className="mt-3 flex items-start justify-between gap-4">
                      <div>
                        <p className="text-sm font-semibold text-white">{activeChampion.name}</p>
                        <p className="text-xs text-white/60">{activeChampion.role}</p>
                      </div>
                      <div className="rounded-lg border border-emerald-400/50 bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-300">
                        {loading ? (
                          <div className="h-4 w-12 animate-pulse bg-emerald-400/20 rounded" />
                        ) : (
                          `${Math.round(getFavorPercentage(activeChampion.winRate))}% favor`
                        )}
                      </div>
                    </div>
                  </m.div>
                </div>
              </div>

              <m.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.8, duration: 0.6 }}
                className="mt-6 rounded-2xl border border-white/15 bg-black/40 p-5"
              >
                <div className="flex items-center justify-between text-xs uppercase tracking-[0.24em] text-white/40">
                  <span>Live Win Probability</span>
                  <span>Dynamic Forecast</span>
                </div>
                <div className="mt-4 grid grid-cols-2 gap-4 text-sm text-white">
                  <div className="space-y-2">
                    <p className="text-white/60">Blue Side</p>
                    <p className="text-2xl font-semibold text-emerald-300">
                      {loading || !liveForecast ? (
                        <div className="h-8 w-16 animate-pulse bg-emerald-400/20 rounded" />
                      ) : (
                        `${liveForecast.blueWinRate.toFixed(1)}%`
                      )}
                    </p>
                    <p className="text-xs text-white/40">
                      {loading || !liveForecast ? (
                        <div className="h-3 w-20 animate-pulse bg-white/20 rounded" />
                      ) : (
                        `${liveForecast.blueLift >= 0 ? "+" : ""}${liveForecast.blueLift.toFixed(1)}% vs 50% baseline`
                      )}
                    </p>
                  </div>
                  <div className="space-y-2">
                    <p className="text-white/60">Red Side</p>
                    <p className="text-2xl font-semibold text-rose-300">
                      {loading || !liveForecast ? (
                        <div className="h-8 w-16 animate-pulse bg-rose-400/20 rounded" />
                      ) : (
                        `${liveForecast.redWinRate.toFixed(1)}%`
                      )}
                    </p>
                    <p className="text-xs text-white/40">
                      {loading || !liveForecast ? (
                        <div className="h-3 w-20 animate-pulse bg-white/20 rounded" />
                      ) : (
                        liveForecast.blueLift > 0
                          ? `-${liveForecast.blueLift.toFixed(1)}% gap to close`
                          : liveForecast.blueLift < 0
                            ? `+${Math.abs(liveForecast.blueLift).toFixed(1)}% edge this patch`
                            : "Holding even footing this patch"
                      )}
                    </p>
                  </div>
                </div>
                {!loading && liveForecast && (
                  <div className="mt-4 space-y-1 text-xs text-white/50">
                    <p>{liveForecast.narrative}</p>
                    <p className="text-white/40">
                      Based on 3000+ analyzed matches
                    </p>
                  </div>
                )}
              </m.div>
            </div>
          </m.div>
        </div>
      </Container>
    </section>
  )
}
