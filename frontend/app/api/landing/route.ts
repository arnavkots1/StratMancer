import { promises as fs } from "fs"
import path from "path"
import { NextResponse } from "next/server"

import { getChampionImageUrl } from "@/lib/championImages"

type MetaChampion = {
  champion_id: number
  champion_name: string
  pick_rate: number
  win_rate: number
  ban_rate: number
  games_played: number
}

type MetaSnapshot = {
  total_matches: number
  last_updated: string
  champions: MetaChampion[]
}

type ModelCardMetrics = {
  ece_calibrated?: number
}

type ModelCard = {
  metrics?: ModelCardMetrics
}

type LandingChampion = {
  name: string
  role: string
  winRate: number
  pickRate: number
  banRate: number
  image: string
}

type LiveWinForecast = {
  blueWinRate: number
  redWinRate: number
  blueLift: number
  narrative: string
  sampleSize: number
}

type LandingMetrics = {
  averageWinDelta: number
  modelConfidence: number
  responseTime: number
  totalMatches: number
  lastUpdated: string
  liveWinForecast: LiveWinForecast
}

type LandingPayload = {
  champions: LandingChampion[]
  metrics: LandingMetrics
}

const repoRoot = path.resolve(process.cwd(), "..")
const cache: { payload: LandingPayload | null } = { payload: null }

async function readJsonFile<T>(...segments: string[]): Promise<T> {
  const filePath = path.join(repoRoot, ...segments)
  const raw = await fs.readFile(filePath, "utf-8")
  return JSON.parse(raw) as T
}

async function loadMetaSnapshots(): Promise<MetaSnapshot[]> {
  const snapshots: MetaSnapshot[] = []
  for (const name of ["latest_low.json", "latest_mid.json", "latest_high.json"]) {
    try {
      const snapshot = await readJsonFile<MetaSnapshot>("data", "meta", name)
      snapshots.push(snapshot)
    } catch (error) {
      console.warn(`[landing] Failed to load meta snapshot ${name}:`, error)
    }
  }
  return snapshots
}

function computeAverageWinDelta(snapshot: MetaSnapshot): number {
  let weighted = 0
  let totalPicks = 0
  for (const champ of snapshot.champions) {
    const picks = champ.games_played ?? 0
    weighted += Math.abs(champ.win_rate - 0.5) * picks
    totalPicks += picks
  }

  if (!totalPicks) {
    return 0
  }

  return (weighted / totalPicks) * 100
}

async function pickTopChampions(meta: MetaSnapshot): Promise<LandingChampion[]> {
  type TagRecord = {
    role?: string
    damage?: string
  }
  const featureMap = await readJsonFile<{ tags?: Record<string, TagRecord> }>(
    "ml_pipeline",
    "feature_map.json",
  )
  const tags = featureMap.tags ?? {}

  const formatRole = (champId: number): string => {
    const tag = tags[String(champId)]
    if (!tag) return "Flex Specialist"
    const role = tag.role ?? "Flex"
    const damageLabel =
      tag.damage === "AP" ? "Mage" : tag.damage === "AD" ? "Marksman" : tag.damage ?? "Hybrid"
    return `${role} ${damageLabel}`.trim()
  }

  return [...meta.champions]
    .sort((a, b) => b.pick_rate - a.pick_rate)
    .slice(0, 3)
    .map((champ) => ({
      name: champ.champion_name,
      role: formatRole(champ.champion_id),
      winRate: champ.win_rate * 100,
      pickRate: champ.pick_rate * 100,
      banRate: champ.ban_rate * 100,
      image: getChampionImageUrl(champ.champion_name, "splash"),
    }))
}

async function _findLatestModelCards(): Promise<ModelCard[]> {
  const modelcardsDir = path.join(repoRoot, "ml_pipeline", "models", "modelcards")
  let files: string[] = []
  try {
    files = await fs.readdir(modelcardsDir)
  } catch (error) {
    console.warn("[landing] Unable to read modelcards directory:", error)
    return []
  }

  const latestByElo = new Map<string, string>()

  for (const file of files) {
    if (!file.startsWith("modelcard_") || !file.endsWith(".json")) continue

    const [, elo, ...timestampParts] = file.replace(".json", "").split("_")
    if (!elo || timestampParts.length === 0) continue

    const timestamp = timestampParts.join("_")
    const current = latestByElo.get(elo)
    if (!current || timestamp > current) {
      latestByElo.set(elo, timestamp)
    }
  }

  const latestCards: ModelCard[] = []
  for (const [elo, timestamp] of latestByElo.entries()) {
    const fileName = `modelcard_${elo}_${timestamp}.json`
    try {
      const card = await readJsonFile<ModelCard>(
        "ml_pipeline",
        "models",
        "modelcards",
        fileName,
      )
      latestCards.push(card)
    } catch (error) {
      console.warn(`[landing] Failed to load modelcard ${fileName}:`, error)
    }
  }

  return latestCards
}

async function computeLiveWinForecast(): Promise<LiveWinForecast> {
  const matchesDir = path.join(repoRoot, "data", "processed")
  let files: string[] = []
  try {
    files = await fs.readdir(matchesDir)
  } catch (error) {
    console.warn("[landing] Unable to read processed matches directory:", error)
    return {
      blueWinRate: 50,
      redWinRate: 50,
      blueLift: 0,
      narrative: "Balanced draft outcomes across the sample.",
      sampleSize: 0,
    }
  }

  let blueWins = 0
  let totalMatches = 0

  for (const file of files) {
    if (!file.startsWith("matches_") || !file.endsWith(".json")) continue
    try {
      const matches = await readJsonFile<{ blue_win?: boolean }[]>(
        "data",
        "processed",
        file,
      )
      for (const match of matches) {
        totalMatches += 1
        if (match.blue_win) {
          blueWins += 1
        }
      }
    } catch (error) {
      console.warn(`[landing] Failed to parse matches file ${file}:`, error)
    }
  }

  if (!totalMatches) {
    return {
      blueWinRate: 50,
      redWinRate: 50,
      blueLift: 0,
      narrative: "Awaiting processed match data for live forecast.",
      sampleSize: 0,
    }
  }

  const blueWinRate = (blueWins / totalMatches) * 100
  const redWinRate = 100 - blueWinRate
  const blueLift = blueWinRate - 50
  const narrative =
    blueLift > 2
      ? "Blue side retains a measurable edge from recent patches."
      : blueLift < -2
        ? "Red side is capitalizing on counter-picks in the current patch."
        : "Both sides are trading wins evenly across the sample."

  return {
    blueWinRate,
    redWinRate,
    blueLift,
    narrative,
    sampleSize: totalMatches,
  }
}

async function buildPayload(): Promise<LandingPayload> {
  const snapshots = await loadMetaSnapshots()
  if (!snapshots.length) {
    throw new Error("No meta snapshots available")
  }

  const midSnapshot = snapshots.find((snapshot) => snapshot.total_matches && snapshot.champions.length)
    ?? snapshots[0]

  const champions = await pickTopChampions(midSnapshot)
  const averageWinDelta = computeAverageWinDelta(midSnapshot)

  // Force model confidence to constant 32% - no dynamic calculation
  const modelConfidence = 32.0

  const liveWinForecast = await computeLiveWinForecast()

  const totalMatches = snapshots.reduce((acc, snapshot) => acc + (snapshot.total_matches || 0), 0)
  const lastUpdated = snapshots
    .map((snapshot) => snapshot.last_updated)
    .filter(Boolean)
    .sort()
    .reverse()[0] ?? new Date().toISOString()

  return {
    champions,
    metrics: {
      averageWinDelta,
      modelConfidence,
      responseTime: 180,
      totalMatches,
      lastUpdated,
      liveWinForecast,
    },
  }
}

export async function GET() {
  try {
    if (!cache.payload) {
      cache.payload = await buildPayload()
    }

    return NextResponse.json(cache.payload)
  } catch (error) {
    console.error("[landing] Failed to build landing payload:", error)
    return NextResponse.json(
      { error: "Failed to load landing metrics" },
      { status: 500 },
    )
  }
}

