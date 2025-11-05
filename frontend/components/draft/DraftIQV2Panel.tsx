/**
 * Draft IQ v2 Panel - Professional coach-style draft analysis
 * Displays team overviews, lane analysis, phase predictions, and final probabilities
 */

"use client"

import { useState, useEffect } from "react"
import { m, useReducedMotion } from "framer-motion"
import { Copy, Check, Loader2, X } from "lucide-react"
import { fadeUp, stagger, scaleIn } from '../../lib/motion'
import { TableLite } from './TableLite'
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card'
import { Button } from '../ui/button'
import { explainDraftV2, type DraftIQV2Payload, type DraftIQV2Response } from '../../lib/iqV2Api'
import { cn } from '../../lib/cn'

interface DraftIQV2PanelProps {
  draftPayload: DraftIQV2Payload | null
  onClose?: () => void
}

export function DraftIQV2Panel({ draftPayload, onClose }: DraftIQV2PanelProps) {
  const [data, setData] = useState<DraftIQV2Response | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState<'json' | 'markdown' | null>(null)
  const reduceMotion = useReducedMotion()

  // Convert null/undefined picks to -1 for API (backend expects -1 for empty slots)
  const normalizePayload = (payload: DraftIQV2Payload | null): DraftIQV2Payload | null => {
    if (!payload) return null
    
    return {
      ...payload,
      blue: {
        ...payload.blue,
        top: payload.blue.top ?? -1,
        jgl: payload.blue.jgl ?? -1,
        mid: payload.blue.mid ?? -1,
        adc: payload.blue.adc ?? -1,
        sup: payload.blue.sup ?? -1,
        bans: payload.blue.bans || [],
      },
      red: {
        ...payload.red,
        top: payload.red.top ?? -1,
        jgl: payload.red.jgl ?? -1,
        mid: payload.red.mid ?? -1,
        adc: payload.red.adc ?? -1,
        sup: payload.red.sup ?? -1,
        bans: payload.red.bans || [],
      },
    }
  }

  useEffect(() => {
    const normalized = normalizePayload(draftPayload)
    if (!normalized) {
      setData(null)
      return
    }

    let cancelled = false
    setLoading(true)
    setError(null)

    explainDraftV2(normalized)
      .then((result) => {
        if (!cancelled) {
          console.log('Draft IQ v2 response received:', result)
          if (!result || !result.json) {
            console.error('Invalid response structure:', result)
            setError('Invalid response from server')
            setLoading(false)
            return
          }
          setData(result)
          setLoading(false)
        }
      })
      .catch((err) => {
        if (!cancelled) {
          console.error('Draft IQ v2 error:', err)
          setError(err.message || 'Failed to generate analysis')
          setLoading(false)
        }
      })

    return () => {
      cancelled = true
    }
  }, [draftPayload])

  const handleCopy = async (type: 'json' | 'markdown') => {
    if (!data) return

    const text = type === 'json' 
      ? JSON.stringify(data.json, null, 2)
      : data.markdown

    try {
      await navigator.clipboard.writeText(text)
      setCopied(type)
      setTimeout(() => setCopied(null), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  if (!draftPayload) {
    return (
      <Card variant="glass" className="border-white/10 bg-[#0d1424]/85 backdrop-blur-xl">
        <CardContent className="py-8 text-center text-white/60">
          Complete a draft to generate analysis
        </CardContent>
      </Card>
    )
  }

  if (loading) {
    return (
      <Card variant="glass" className="border-white/10 bg-[#0d1424]/85 backdrop-blur-xl">
        <CardContent className="py-12 flex flex-col items-center gap-4">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="text-sm text-white/60">Generating Draft IQ v2 analysis...</p>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card variant="glass" className="border-white/10 bg-[#0d1424]/85 backdrop-blur-xl">
        <CardContent className="py-8">
          <div className="flex items-center gap-3 text-red-300">
            <X className="h-5 w-5" />
            <p className="text-sm">{error}</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (!data) return null

  const iq = data.json

  return (
    <div className="relative flex flex-col h-full max-h-[90vh] overflow-hidden">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(124,58,237,0.25),transparent_60%)] opacity-50" />
      
      <div className="relative flex flex-col h-full overflow-y-auto">
        <div className="space-y-6 p-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-semibold text-white">Draft IQ v2</h2>
            <p className="text-xs text-white/60 mt-1">
              {iq.elo_context} ELO
            </p>
            <p className="text-xs text-white/40 mt-1">
              ✅ Realistic win probability: Red ≈ {iq.final_prediction.red_range} | Blue ≈ {iq.final_prediction.blue_range}
            </p>
          </div>
          <div className="flex gap-2">
            <Button
              variant="glass"
              size="sm"
              onClick={() => handleCopy('json')}
              className="text-xs"
            >
              {copied === 'json' ? (
                <>
                  <Check className="h-3 w-3 mr-1" />
                  Copied
                </>
              ) : (
                <>
                  <Copy className="h-3 w-3 mr-1" />
                  Copy JSON
                </>
              )}
            </Button>
            <Button
              variant="glass"
              size="sm"
              onClick={() => handleCopy('markdown')}
              className="text-xs"
            >
              {copied === 'markdown' ? (
                <>
                  <Check className="h-3 w-3 mr-1" />
                  Copied
                </>
              ) : (
                <>
                  <Copy className="h-3 w-3 mr-1" />
                  Copy Markdown
                </>
              )}
            </Button>
            {onClose && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onClose}
                className="text-xs"
              >
                <X className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>

        {/* Team Overviews */}
        <m.div variants={stagger} initial="initial" animate="animate" className="grid gap-6 md:grid-cols-2">
          {/* Blue Team */}
          <m.div variants={fadeUp}>
            <h3 className="text-lg font-semibold text-blue-300 mb-3">🔵 Blue Team</h3>
            <TableLite
              columns={[
                { header: 'Role', key: 'role' },
                { header: 'Champion', key: 'champion' },
                { header: 'Notes', key: 'notes' }
              ]}
              data={iq.blue_overview.items.map(item => ({
                role: item.role,
                champion: item.champion,
                notes: item.notes
              }))}
              className="mb-3"
            />
            <p className="text-sm text-white/70">{iq.blue_overview.identity}</p>
          </m.div>

          {/* Red Team */}
          <m.div variants={fadeUp}>
            <h3 className="text-lg font-semibold text-red-300 mb-3">🔴 Red Team</h3>
            <TableLite
              columns={[
                { header: 'Role', key: 'role' },
                { header: 'Champion', key: 'champion' },
                { header: 'Notes', key: 'notes' }
              ]}
              data={iq.red_overview.items.map(item => ({
                role: item.role,
                champion: item.champion,
                notes: item.notes
              }))}
              className="mb-3"
            />
            <p className="text-sm text-white/70">{iq.red_overview.identity}</p>
          </m.div>
        </m.div>

        {/* Lane-by-Lane */}
        <m.div variants={fadeUp}>
          <h3 className="text-lg font-semibold text-white mb-3">🧩 Lane-by-Lane Analysis</h3>
          <TableLite
            columns={[
              { header: 'Lane', key: 'lane' },
              { header: 'Likely Winner', key: 'likely_winner' },
              { header: 'Explanation', key: 'explanation' }
            ]}
            data={iq.lane_by_lane.map(lane => ({
              lane: lane.lane,
              likely_winner: lane.likely_winner,
              explanation: lane.explanation
            }))}
          />
        </m.div>

        {/* Teamfight/Scaling/Execution */}
        <m.div variants={fadeUp}>
          <h3 className="text-lg font-semibold text-white mb-3">⚙️ Teamfighting / Scaling / Execution</h3>
          <TableLite
            columns={[
              { header: 'Factor', key: 'factor' },
              { header: 'Blue', key: 'blue' },
              { header: 'Red', key: 'red' }
            ]}
            data={iq.teamfight_scaling_execution.map(factor => ({
              factor: factor.factor,
              blue: factor.blue,
              red: factor.red
            }))}
          />
        </m.div>

        {/* Phase Predictions */}
        <m.div variants={fadeUp}>
          <h3 className="text-lg font-semibold text-white mb-3">📊 Phase Predictions</h3>
          <TableLite
            columns={[
              { header: 'Game Phase', key: 'phase' },
              { header: 'Favored', key: 'favored' },
              { header: 'Comment', key: 'comment' }
            ]}
            data={iq.phase_predictions.map(phase => ({
              phase: phase.phase,
              favored: phase.favored,
              comment: phase.comment
            }))}
          />
        </m.div>

        {/* Footer Note */}
        <div className="text-xs text-white/40 pt-4 border-t border-white/10">
          <p>{iq.calibration_note}</p>
        </div>
        </div>
      </div>
    </div>
  )
}

