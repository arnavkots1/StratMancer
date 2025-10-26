/* eslint-disable react/no-unescaped-entities */
"use client"

import { AlertTriangle, Info } from "lucide-react"
import { m } from "framer-motion"
import { Card } from "@/components/ui/card"

// Inline motion variants to avoid import issues
const EASE_EXPO = [0.16, 1, 0.3, 1]

const fadeUp = {
  initial: { opacity: 0, y: 32 },
  animate: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.7, ease: EASE_EXPO },
  },
  exit: {
    opacity: 0,
    y: -24,
    transition: { duration: 0.35, ease: EASE_EXPO },
  },
}

interface DataWarningProps {
  variant?: "warning" | "info"
  className?: string
}

export function DataWarning({ variant = "warning", className }: DataWarningProps) {
  const isWarning = variant === "warning"
  
  return (
    <m.div
      initial="initial"
      animate="animate"
      variants={fadeUp}
      className={className}
    >
      <Card className={`p-4 border-l-4 ${
        isWarning 
          ? "border-l-amber-500 bg-amber-500/5 border-amber-500/20" 
          : "border-l-blue-500 bg-blue-500/5 border-blue-500/20"
      }`}>
        <div className="flex items-start gap-3">
          <div className={`flex-shrink-0 w-5 h-5 mt-0.5 ${
            isWarning ? "text-amber-500" : "text-blue-500"
          }`}>
            {isWarning ? <AlertTriangle className="w-5 h-5" /> : <Info className="w-5 h-5" />}
          </div>
          <div className="flex-1">
            <h4 className={`font-semibold text-sm mb-1 ${
              isWarning ? "text-amber-700 dark:text-amber-300" : "text-blue-700 dark:text-blue-300"
            }`}>
              {isWarning ? "Limited Dataset Notice" : "Data Information"}
            </h4>
            <p className={`text-sm leading-relaxed ${
              isWarning 
                ? "text-amber-600 dark:text-amber-400" 
                : "text-blue-600 dark:text-blue-400"
            }`}>
              {isWarning ? (
                <>
                  Our predictions are based on a limited dataset and may not be perfect yet. 
                  We're continuously improving our models with more data. Use these insights 
                  as guidance while we enhance accuracy.
                </>
              ) : (
                <>
                  This data is updated regularly. For the most accurate predictions, 
                  ensure you're using the latest patch information.
                </>
              )}
            </p>
          </div>
        </div>
      </Card>
    </m.div>
  )
}
