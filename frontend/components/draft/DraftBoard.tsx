"use client"

import { AnimatePresence, m } from "framer-motion"
import { AlarmClock, Ban, PauseCircle, PlayCircle, RefreshCw } from "lucide-react"
import Image from "next/image"
import { Button } from "@/components/ui/button"
import { getChampionImageUrl } from "@/lib/championImages"
import { fadeUp, slideIn, stagger } from "@/lib/motion"
import type { Champion, DraftState, TeamComposition } from "@/types"
import { cn } from "@/lib/cn"

export type DraftAction = {
  team: "blue" | "red"
  action: "ban" | "pick"
  role?: keyof TeamComposition
}

type DraftBoardProps = {
  draftState: DraftState
  currentAction: DraftAction | null
  draftStep: number
  totalSteps: number
  draftStarted: boolean
  pickTimer: number
  timerActive: boolean
  onToggleTimer: () => void
  onStartDraft: () => void
  onResetDraft: () => void
  onRemovePick: (_team: "blue" | "red", _role: keyof TeamComposition) => void
  onRemoveBan: (_team: "blue" | "red", _index: number) => void
}

const ROLES: Array<{ key: keyof TeamComposition; label: string }> = [
  { key: "top", label: "Top" },
  { key: "jungle", label: "Jungle" },
  { key: "mid", label: "Mid" },
  { key: "adc", label: "Bot" },
  { key: "support", label: "Support" },
]

const TEAM_META = {
  blue: {
    label: "Blue Side",
    gradient: "from-cyan-500/20 via-cyan-500/10 to-transparent",
    border: "border-cyan-500/40",
    accent: "text-cyan-300",
  },
  red: {
    label: "Red Side",
    gradient: "from-rose-500/20 via-rose-500/10 to-transparent",
    border: "border-rose-500/40",
    accent: "text-rose-300",
  },
} as const

export function DraftBoard({
  draftState,
  currentAction,
  draftStep,
  totalSteps,
  draftStarted,
  pickTimer,
  timerActive,
  onToggleTimer,
  onStartDraft,
  onResetDraft,
  onRemovePick,
  onRemoveBan,
}: DraftBoardProps) {
  const progress = totalSteps === 0 ? 0 : Math.min(draftStep / totalSteps, 1)

  const renderChampionCard = (
    team: "blue" | "red",
    role: keyof TeamComposition,
    champion: Champion | null,
    isActive: boolean,
  ) => {
    return (
      <div className="relative overflow-hidden rounded-sm border border-white/10 bg-white/5 p-0.5 backdrop-blur-lg shadow-[0_2px_8px_-4px_rgba(0,0,0,0.3)]">
        <div className="flex items-center justify-start pb-0.5 text-[7px] uppercase tracking-[0.05em] text-white/40">
          <span className="ml-4 text-white/50">
            {TEAM_META[team].label} · {ROLES.find((roleInfo) => roleInfo.key === role)?.label}
          </span>
        </div>

        <div
          className={cn(
            "relative overflow-hidden rounded-md border border-white/10 bg-gradient-to-br from-[#101623] to-[#090d16]",
            isActive && "ring-2 ring-offset-1 ring-offset-[#0b0f17] ring-primary/60",
          )}
          style={{ aspectRatio: '4/1' }}
        >
          <AnimatePresence mode="wait">
            {champion ? (
              <m.div
                key={champion.id}
                layoutId={`champion-${champion.id}`}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.98 }}
                transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
                className="absolute inset-0"
              >
                <Image
                  src={getChampionImageUrl(champion.name, 'splash')}
                  alt={champion.name}
                  fill
                  sizes="(max-width: 768px) 150px, 200px"
                  className="object-cover object-top"
                  loading="eager"
                  priority
                  quality={90}
                />
                <m.div
                  aria-hidden
                  className="absolute inset-0 bg-gradient-to-t from-black/70 via-transparent to-transparent"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                />
                <div className="absolute inset-x-2 bottom-1 flex items-center justify-between">
                  <div>
                    <p className="text-xs font-semibold text-white drop-shadow-[0_1px_3px_rgba(0,0,0,0.6)]">
                      {champion.name}
                    </p>
                    <p className="text-[8px] uppercase tracking-[0.2em] text-white/60">
                      {champion.tags?.role ? String(champion.tags.role).toUpperCase() : "Meta"}
                    </p>
                  </div>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => onRemovePick(team, role)}
                    className="h-5 rounded-md border border-white/10 bg-black/30 px-1 text-[8px] text-white/60 hover:text-white/90"
                  >
                    ×
                  </Button>
                </div>
              </m.div>
            ) : (
              <m.div
                key={`${team}-${role}-placeholder`}
                initial={{ opacity: 0, scale: 0.96 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0 }}
                className="absolute inset-0 flex flex-col items-center justify-center gap-1 text-white/30"
              >
                <span className="text-[8px] tracking-[0.2em] uppercase">Awaiting Pick</span>
                {isActive && (
                  <m.span
                    initial={{ opacity: 0 }}
                    animate={{ opacity: [0.4, 1, 0.4] }}
                    transition={{ duration: 2, repeat: Infinity }}
                    className="rounded-full border border-primary/60 px-1 py-0.5 text-[8px] font-semibold uppercase tracking-[0.2em] text-primary/80"
                  >
                    Active
                  </m.span>
                )}
              </m.div>
            )}
          </AnimatePresence>

          {champion && (
            <m.span
              layoutId={`pulse-${champion.id}`}
              aria-hidden
              className="absolute inset-0 rounded-xl border border-primary/30"
              animate={{ opacity: [0.35, 0, 0.35] }}
              transition={{ duration: 2.4, repeat: Infinity, ease: "easeInOut" }}
            />
          )}
        </div>

        <div className="mt-1 flex flex-wrap gap-1">
          {champion?.tags?.damage && (
            <span className="rounded-full border border-white/10 bg-white/10 px-2 py-0.5 text-[8px] uppercase tracking-[0.2em] text-white/60">
              {Array.isArray(champion.tags.damage) ? champion.tags.damage.join(" • ") : champion.tags.damage}
            </span>
          )}
          {champion?.tags?.engage !== undefined && (
            <span className="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[8px] uppercase tracking-[0.2em] text-white/60">
              Engage {champion.tags.engage}
            </span>
          )}
        </div>
      </div>
    )
  }

  const renderBans = (team: "blue" | "red", bans: Champion[]) => {
    const accent = TEAM_META[team].accent
    return (
      <div>
        <div className="flex items-center justify-between pb-1">
          <div className="flex items-center gap-1 text-[10px] uppercase tracking-[0.2em] text-white/40">
            <Ban className="h-3 w-3 text-white/40" />
            <span>{TEAM_META[team].label} Bans</span>
          </div>
          <span className={cn("text-[10px] font-semibold", accent)}>
            {bans.length}
            <span className="text-white/30"> / 5</span>
          </span>
        </div>

        <div className="grid grid-cols-5 gap-1">
          {Array.from({ length: 5 }).map((_, index) => {
            const ban = bans[index]
            const isActive =
              currentAction?.team === team && currentAction.action === "ban" && bans.length === index
            return (
              <div
                key={`${team}-ban-${index}`}
                className={cn(
                  "relative aspect-square overflow-hidden rounded-md border border-white/10 bg-gradient-to-br from-[#101623] to-[#090d16]",
                  isActive && "ring-2 ring-primary/50 ring-offset-2 ring-offset-[#0b0f17]",
                )}
              >
                <AnimatePresence>
                  {ban ? (
                    <m.div
                      key={ban.id}
                      layoutId={`ban-${ban.id}`}
                      initial={{ opacity: 0, scale: 0.9, filter: "blur(6px)" }}
                      animate={{ opacity: 1, scale: 1, filter: "blur(0px)" }}
                      exit={{ opacity: 0, scale: 0.95, filter: "blur(4px)" }}
                      className="absolute inset-0"
                    >
                      <Image
                        src={getChampionImageUrl(ban.name)}
                        alt={ban.name}
                        fill
                        sizes="140px"
                        className="object-cover grayscale"
                      />
                      <div className="absolute inset-0 bg-black/45" />
                      <div className="absolute inset-0 flex flex-col items-center justify-center text-white/70">
                        <Ban className="h-3 w-3" />
                        <span className="mt-0.5 text-[8px] font-semibold uppercase tracking-[0.2em]">
                          {ban.name}
                        </span>
                      </div>
                      <button
                        onClick={() => onRemoveBan(team, index)}
                        className="absolute right-1 top-1 rounded-full border border-white/10 bg-black/40 px-1 py-0.5 text-[8px] text-white/60 transition hover:text-white"
                      >
                        ×
                      </button>
                    </m.div>
                  ) : (
                    <m.div
                      key={`placeholder-${team}-${index}`}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="absolute inset-0 flex flex-col items-center justify-center gap-2 text-white/25"
                    >
                      <Ban className="h-5 w-5" />
                      {isActive && (
                        <m.span
                          initial={{ opacity: 0 }}
                          animate={{ opacity: [0.2, 1, 0.2] }}
                          transition={{ duration: 1.5, repeat: Infinity }}
                          className="rounded-full border border-white/10 px-2 py-0.5 text-[10px] uppercase tracking-[0.28em]"
                        >
                          Ban
                        </m.span>
                      )}
                    </m.div>
                  )}
                </AnimatePresence>
              </div>
            )
          })}
        </div>
      </div>
    )
  }

  return (
    <m.section
      initial="initial"
      animate="animate"
      variants={stagger}
      className="relative overflow-hidden rounded-[16px] border border-white/10 bg-[#0c101b]/80 p-2 shadow-[0_8px_24px_-12px_rgba(8,10,20,0.9)] backdrop-blur-xl"
    >
      <div className="absolute inset-0 bg-gradient-to-tr from-primary/10 via-transparent to-secondary/10 opacity-70" />
      <div className="relative space-y-0.5">
        <m.div variants={fadeUp} className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
          <div className="ml-6">
            <p className="text-xs uppercase tracking-[0.32em] text-white/40">Draft Status</p>
            <div className="mt-2 flex items-center gap-3 text-base text-white/75">
              {currentAction ? (
                <>
                  <span className={cn("text-sm font-semibold", TEAM_META[currentAction.team].accent)}>
                    {TEAM_META[currentAction.team].label}
                  </span>
                  <span className="text-white/40">•</span>
                  <span className="text-sm uppercase tracking-[0.28em] text-white/60">
                    {currentAction.action === "ban" ? "Ban Phase" : `${currentAction.role?.toUpperCase()} Pick`}
                  </span>
                </>
              ) : (
                <span className="text-sm uppercase tracking-[0.28em] text-emerald-300">
                  Draft Complete — Ready to Analyze
                </span>
              )}
            </div>
            <div className="mt-4 h-2 overflow-hidden rounded-full bg-white/5">
              <m.div
                className="h-full bg-gradient-to-r from-primary via-secondary to-accent"
                initial={{ width: "0%" }}
                animate={{ width: `${progress * 100}%` }}
                transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
              />
            </div>
            <div className="mt-1 text-xs uppercase tracking-[0.24em] text-white/30">
              Step {Math.min(draftStep + 1, totalSteps)} of {totalSteps}
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-3 rounded-2xl border border-white/10 bg-black/30 px-4 py-2 text-sm text-white/70 shadow-inner shadow-black/40">
              <AlarmClock className={cn("h-5 w-5", timerActive ? "text-accent" : "text-white/40")} />
              <span className="text-2xl font-semibold text-white">{pickTimer}s</span>
            </div>
            <Button
              variant="glass"
              size="lg"
              onClick={draftStarted ? onToggleTimer : onStartDraft}
              className="flex items-center gap-2 border-white/20 bg-white/5 px-6 py-3 text-xs uppercase tracking-[0.28em]"
            >
              {draftStarted ? (
                timerActive ? (
                  <>
                    <PauseCircle className="h-5 w-5" />
                    Pause Timer
                  </>
                ) : (
                  <>
                    <PlayCircle className="h-5 w-5" />
                    Resume
                  </>
                )
              ) : (
                <>
                  <PlayCircle className="h-5 w-5 text-accent" />
                  Start Draft
                </>
              )}
            </Button>
            <Button
              variant="ghost"
              size="lg"
              onClick={onResetDraft}
              className="flex items-center gap-2 border border-white/10 bg-black/40 px-6 py-3 text-xs uppercase tracking-[0.28em] text-white/60 hover:text-white"
            >
              <RefreshCw className="h-5 w-5" />
              Reset
            </Button>
          </div>
        </m.div>

        <div className="grid gap-0.5 lg:grid-cols-2">
          <m.div variants={slideIn("left")}>
            <div className={cn("rounded-[6px] border bg-gradient-to-br p-0.5 backdrop-blur-xl", TEAM_META.blue.border, TEAM_META.blue.gradient)}>
              <div className="space-y-0.5">
                {ROLES.map(({ key }) =>
                  renderChampionCard(
                    "blue",
                    key,
                    draftState.blue[key],
                    currentAction?.team === "blue" &&
                      currentAction?.action === "pick" &&
                      currentAction.role === key,
                  ),
                )}
              </div>
              <m.div variants={fadeUp} className="mt-8">
                {renderBans("blue", draftState.blueBans)}
              </m.div>
            </div>
          </m.div>

          <m.div variants={slideIn("right")}>
            <div className={cn("rounded-[6px] border bg-gradient-to-bl p-0.5 backdrop-blur-xl", TEAM_META.red.border, TEAM_META.red.gradient)}>
              <div className="space-y-0.5">
                {ROLES.map(({ key }) =>
                  renderChampionCard(
                    "red",
                    key,
                    draftState.red[key],
                    currentAction?.team === "red" &&
                      currentAction?.action === "pick" &&
                      currentAction.role === key,
                  ),
                )}
              </div>
              <m.div variants={fadeUp} className="mt-8">
                {renderBans("red", draftState.redBans)}
              </m.div>
            </div>
          </m.div>
        </div>
      </div>
    </m.section>
  )
}
