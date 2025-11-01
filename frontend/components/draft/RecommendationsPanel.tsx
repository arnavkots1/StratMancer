"use client"

import { useEffect, useMemo, useState } from "react"
import { m, useReducedMotion } from "framer-motion"
import Image from "next/image"
import { Sparkles, WifiOff } from "lucide-react"
import { getChampionImageUrl } from '../../lib/championImages'
import type { Champion } from "@/types"
import type { DraftAction } from "./DraftBoard"
import { fadeUp, scaleIn, slideIn } from '../../lib/motion'
import { cn } from '../../lib/cn'

type Recommendation = {
  champion_id: number
  champion_name: string
  win_gain?: number
  threat_level?: number
  confidence?: number
  reasons?: string[]
}

type RecommendationsPanelProps = {
  currentAction: DraftAction | null
  recommendations: Recommendation[] | null
  loading: boolean
  error: string | null
  lockedChampionIds: Set<number>
  lockedChampionNames: Set<string>
  onSelectRecommendation: (_championId: number) => void
  champions: Champion[]
}

export function RecommendationsPanel({
  currentAction,
  recommendations,
  loading,
  error,
  lockedChampionIds,
  lockedChampionNames,
  onSelectRecommendation,
  champions,
}: RecommendationsPanelProps) {
  const reduceMotion = useReducedMotion()
  const [displayedReason, setDisplayedReason] = useState("")

  const headline =
    currentAction?.action === "ban"
      ? "Neutralize threats before they snowball."
      : "Exploit enemy gaps with perfect synergy."

  const filteredRecommendations = useMemo(() => {
    if (!recommendations) return []
    return recommendations.filter((rec) => {
      const id = rec.champion_id
      if (lockedChampionIds.has(id)) return false
      if (lockedChampionNames.has(rec.champion_name)) return false
      return true
    })
  }, [recommendations, lockedChampionIds, lockedChampionNames])

  useEffect(() => {
    // Combine all reasons from top recommendation into a detailed reasoning
    const topRec = filteredRecommendations[0]
    let text = headline
    
    if (topRec?.reasons && topRec.reasons.length > 0) {
      // Combine all reasons into a comprehensive explanation
      const reasons = topRec.reasons.slice(0, 3) // Use top 3 reasons
      
      // If we have multiple reasons, combine them
      if (reasons.length > 1) {
        const lastReason = reasons.pop()
        text = `${reasons.join(", ")}, and ${lastReason}.`
      } else {
        text = reasons[0]
      }
    }
    
    if (reduceMotion) {
      setDisplayedReason(text)
      return
    }

    if (!text) {
      setDisplayedReason("")
      return
    }

    // Typewriter animation with better timing
    setDisplayedReason("")
    let frame = 0
    const interval = window.setInterval(() => {
      frame += 1
      setDisplayedReason(text.slice(0, frame))
      if (frame >= text.length) {
        window.clearInterval(interval)
      }
    }, 50) // Slower for better readability

    return () => {
      window.clearInterval(interval)
    }
  }, [filteredRecommendations, headline, reduceMotion])

  const renderCard = (recommendation: Recommendation, index: number) => {
    const champion =
      champions.find((c) => parseInt(c.id, 10) === recommendation.champion_id) ?? null
    const value =
      currentAction?.action === "ban"
        ? recommendation.threat_level ?? 0
        : recommendation.win_gain ?? 0
    const valuePercent = Math.max(Math.min(Math.abs(value) * 100, 100), 0)
    const isBan = currentAction?.action === "ban"

    return (
      <m.button
        key={recommendation.champion_id}
        layoutId={`champion-${recommendation.champion_id}`}
        variants={scaleIn}
        className="group relative overflow-hidden rounded-2xl border border-white/10 bg-[#0d1321]/80 p-4 text-left shadow-[0_24px_60px_-40px_rgba(12,18,33,0.9)] transition focus:outline-none focus-visible:ring-2 focus-visible:ring-primary/60"
        onClick={() => onSelectRecommendation(recommendation.champion_id)}
      >
        <div className="absolute inset-0 bg-gradient-to-r from-primary/10 via-transparent to-secondary/10 opacity-0 transition-opacity duration-300 group-hover:opacity-100" />
        <div className="relative flex items-center gap-4">
          <div className="relative h-16 w-16 overflow-hidden rounded-xl border border-white/10 bg-black/30">
            {champion ? (
              <Image
                src={getChampionImageUrl(champion.name ?? recommendation.champion_name)}
                alt={recommendation.champion_name}
                fill
                sizes="80px"
                className="object-cover transition duration-500 group-hover:scale-105 group-hover:blur-[1px]"
                loading="eager"
                priority
                quality={90}
                decoding="async"
                onError={(_e) => {
                  console.log(`Failed to load recommendation image: ${recommendation.champion_name}`);
                }}
              />
            ) : (
              <div className="flex h-full w-full items-center justify-center text-white/30">
                ?
              </div>
            )}
            <m.span
              layoutId={`badge-${recommendation.champion_id}`}
              className="absolute -left-2 -top-2 rounded-full border border-white/20 bg-black/60 px-3 py-1 text-[10px] uppercase tracking-[0.28em] text-white/60"
            >
              #{index + 1}
            </m.span>
          </div>

          <div className="flex-1">
            <div className="flex items-center justify-between">
              <p className="text-sm font-semibold text-white">{recommendation.champion_name}</p>
              <div
                className={cn(
                  "text-xs font-semibold uppercase tracking-[0.24em]",
                  isBan ? "text-rose-300" : "text-emerald-300",
                )}
              >
                {isBan ? "Threat" : "Win Gain"}
              </div>
            </div>
            <div className="mt-2 flex items-end justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className="relative inline-flex h-16 w-16 items-center justify-center rounded-full border border-white/10 bg-black/20">
                  <svg viewBox="0 0 36 36" className="h-14 w-14 -rotate-90 text-white/10">
                    <circle
                      cx="18"
                      cy="18"
                      r="14"
                      stroke="currentColor"
                      strokeWidth="2.5"
                      fill="none"
                    />
                    <m.circle
                      cx="18"
                      cy="18"
                      r="14"
                      stroke={isBan ? "rgba(234, 57, 67, 0.85)" : "rgba(56, 189, 248, 0.85)"}
                      strokeWidth="3"
                      strokeLinecap="round"
                      fill="none"
                      initial={{ strokeDasharray: "0 88" }}
                      animate={{ strokeDasharray: `${(valuePercent / 100) * 88} 88` }}
                      transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
                    />
                  </svg>
                  <span className="absolute text-xs font-semibold text-white">
                    {valuePercent.toFixed(1)}%
                  </span>
                </div>
                <div className="text-xs text-white/60">
                  <p>
                    {isBan ? "Threat differential" : "Projected swing"} based on{" "}
                    <span className="font-semibold text-white/80">
                      {recommendation.confidence
                        ? `${Math.round(recommendation.confidence > 1 ? recommendation.confidence : recommendation.confidence * 100)}%`
                        : "model"}{" "}
                      confidence
                    </span>
                    .
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </m.button>
    )
  }

  return (
    <m.section
      initial="initial"
      animate="animate"
      variants={slideIn("up")}
      className="relative overflow-hidden rounded-[28px] border border-white/10 bg-[#0b111f]/80 p-6 backdrop-blur-xl shadow-[0_32px_120px_-72px_rgba(11,17,31,0.9)]"
    >
      <div className="absolute inset-0 bg-gradient-to-br from-primary/10 via-transparent to-secondary/10 opacity-70" />
      <div className="relative space-y-5">
        <m.header variants={fadeUp} className="space-y-3">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.28em] text-white/40">Guidance</p>
              <h3 className="text-lg font-semibold text-white">
                {currentAction
                  ? currentAction.action === "ban"
                    ? "Targeted Ban Suggestions"
                    : "Priority Picks to Secure"
                  : "Draft Complete"}
              </h3>
            </div>
          </div>
          <p className="text-sm text-white/60">{headline}</p>
        </m.header>

        <m.div
          variants={fadeUp}
          className="relative overflow-hidden rounded-2xl border border-white/10 bg-black/30 p-4"
        >
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(124,58,237,0.25),transparent_60%)] opacity-60" />
          <div className="relative text-xs uppercase tracking-[0.28em] text-white/40">Reasoning</div>
          <m.p
            key={displayedReason}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
            className="relative mt-2 font-mono text-sm text-white/70"
          >
            {displayedReason}
            {!reduceMotion && (
              <m.span 
                className="ml-1 text-accent"
                animate={{ opacity: [1, 0, 1] }}
                transition={{ duration: 1, repeat: Infinity, ease: "easeInOut" }}
              >
                ▌
              </m.span>
            )}
          </m.p>
        </m.div>

        {error && (
          <m.div
            variants={fadeUp}
            className="flex items-center gap-3 rounded-2xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200"
          >
            <WifiOff className="h-4 w-4" />
            {error}
          </m.div>
        )}

        {loading ? (
          <div className="grid gap-4">
            {Array.from({ length: 3 }).map((_, index) => (
              <div
                key={index}
                className="h-24 rounded-2xl border border-white/10 bg-white/5/40 animate-pulse"
              />
            ))}
          </div>
        ) : (
          <div className="grid gap-4">
            {filteredRecommendations.length === 0 ? (
              <m.div
                variants={fadeUp}
                className="rounded-2xl border border-white/10 bg-black/30 px-4 py-6 text-center text-sm text-white/50"
              >
                Recommendations will appear once the next draft action is available.
              </m.div>
            ) : (
              filteredRecommendations.slice(0, 5).map(renderCard)
            )}
          </div>
        )}

        <div className="flex items-center justify-between text-[11px] uppercase tracking-[0.28em] text-white/30">
          <span>
            {currentAction
              ? currentAction.action === "ban"
                ? "Calibrated ban pressure"
                : "Calibrated win impact"
              : "Draft resolved"}
          </span>
          <span>{filteredRecommendations.length} options</span>
        </div>
      </div>
    </m.section>
  )
}
