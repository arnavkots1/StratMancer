"use client"

import * as React from "react"
import { m } from "framer-motion"
import { cn } from "@/lib/cn"
import { Section, Container } from "@/components/Section"
import { eliteMotionPresets } from "@/lib/motion"

const marqueeItems = [
  { text: "AI-Powered Draft Analysis", color: "text-primary-400" },
  { text: "Real-Time Win Predictions", color: "text-secondary-400" },
  { text: "ELO-Specific Recommendations", color: "text-accent-400" },
  { text: "Meta Trend Analysis", color: "text-primary-400" },
  { text: "Professional Analytics", color: "text-secondary-400" },
  { text: "Lightning-Fast Performance", color: "text-accent-400" },
  { text: "163+ Champions Tracked", color: "text-primary-400" },
  { text: "Global Data Pipeline", color: "text-accent-400" },
  { text: "Advanced Machine Learning", color: "text-primary-400" },
]

export function ProductMarquee() {
  return (
    <Section variant="glass" size="sm" className="overflow-hidden">
      <Container size="full">
        <m.div
          initial="initial"
          animate="animate"
          variants={eliteMotionPresets.page}
          className="relative"
        >
          {/* Gradient Overlays */}
          <div className="absolute left-0 top-0 bottom-0 w-32 bg-gradient-to-r from-background to-transparent z-10" />
          <div className="absolute right-0 top-0 bottom-0 w-32 bg-gradient-to-l from-background to-transparent z-10" />
          
          {/* Marquee Container */}
          <div className="flex overflow-hidden">
            {/* First Set */}
            <m.div
              className="flex whitespace-nowrap"
              animate={{
                x: [0, -100 + "%"],
              }}
              transition={{
                x: {
                  repeat: Infinity,
                  repeatType: "loop",
                  duration: 20,
                  ease: "linear",
                },
              }}
            >
              {marqueeItems.map((item, index) => (
                <div
                  key={`first-${index}`}
                  className={cn(
                    "flex items-center px-8 text-2xl font-bold",
                    item.color
                  )}
                >
                  {item.text}
                  <div className="w-2 h-2 rounded-full bg-current mx-4 opacity-50" />
                </div>
              ))}
            </m.div>
            
            {/* Second Set */}
            <m.div
              className="flex whitespace-nowrap"
              animate={{
                x: [0, -100 + "%"],
              }}
              transition={{
                x: {
                  repeat: Infinity,
                  repeatType: "loop",
                  duration: 20,
                  ease: "linear",
                },
              }}
            >
              {marqueeItems.map((item, index) => (
                <div
                  key={`second-${index}`}
                  className={cn(
                    "flex items-center px-8 text-2xl font-bold",
                    item.color
                  )}
                >
                  {item.text}
                  <div className="w-2 h-2 rounded-full bg-current mx-4 opacity-50" />
                </div>
              ))}
            </m.div>
          </div>
        </m.div>
      </Container>
    </Section>
  )
}
