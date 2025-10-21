"use client"

import * as React from "react"
import Link from "next/link"
import { motion } from "framer-motion"
import { ArrowRight, Zap, Sparkles, Play, Star, Users, TrendingUp, Shield } from "lucide-react"
import { cn } from "@/lib/cn"
import { Button } from "@/components/ui/button"
import { Glow, EliteGlow } from "@/components/Glow"
import { Section, Container } from "@/components/Section"
import { eliteMotionPresets } from "@/lib/motion"

const heroStats = [
  { label: "Champions Analyzed", value: "163+", icon: Users },
  { label: "Win Rate Accuracy", value: "94.2%", icon: TrendingUp },
  { label: "Response Time", value: "<200ms", icon: Zap },
  { label: "Active Users", value: "10K+", icon: Star },
]

const heroFeatures = [
  "Real-time draft analysis with AI-powered insights",
  "ELO-specific recommendations for every skill level",
  "Advanced meta tracking and champion performance",
  "Professional-grade analytics for teams and coaches",
]

export function Hero() {
  return (
    <Section variant="hero" size="full" className="relative overflow-hidden">
      {/* Background Effects */}
      <div className="absolute inset-0 -z-10">
        <div className="absolute inset-0 bg-gradient-to-br from-primary-500/10 via-secondary-500/5 to-accent-500/10" />
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary-500/20 rounded-full blur-3xl animate-float" />
        <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-secondary-500/20 rounded-full blur-3xl animate-float" style={{ animationDelay: '2s' }} />
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-gradient-to-r from-primary-500/10 to-secondary-500/10 rounded-full blur-3xl animate-pulse-slow" />
      </div>

      <Container size="xl" className="relative z-10">
        <div className="grid lg:grid-cols-2 gap-12 items-center min-h-screen py-20">
          {/* Left Content */}
          <motion.div
            initial="initial"
            animate="animate"
            variants={eliteMotionPresets.page}
            className="space-y-8"
          >
            {/* Badge */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary-500/10 border border-primary-500/20 text-primary-400 text-sm font-medium"
            >
              <Sparkles className="w-4 h-4" />
              Elite Draft Analysis Platform
            </motion.div>

            {/* Main Heading */}
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="space-y-4"
            >
              <h1 className="text-5xl lg:text-7xl font-bold leading-tight">
                <span className="gradient-text">Master</span>
                <br />
                <span className="text-foreground">Every Draft</span>
              </h1>
              <p className="text-xl text-muted-foreground max-w-2xl">
                The ultimate League of Legends draft analysis platform powered by advanced machine learning. 
                Make smarter picks, understand the meta, and climb the ranks with confidence.
              </p>
            </motion.div>

            {/* Features List */}
            <motion.ul
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4 }}
              className="space-y-3"
            >
              {heroFeatures.map((feature, index) => (
                <motion.li
                  key={feature}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.5 + index * 0.1 }}
                  className="flex items-center gap-3 text-muted-foreground"
                >
                  <div className="w-2 h-2 rounded-full bg-primary-500" />
                  <span>{feature}</span>
                </motion.li>
              ))}
            </motion.ul>

            {/* CTA Buttons */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.8 }}
              className="flex flex-col sm:flex-row gap-4"
            >
              <Button size="lg" className="group">
                <Zap className="w-5 h-5 mr-2" />
                Launch Draft Analyzer
                <ArrowRight className="w-5 h-5 ml-2 group-hover:translate-x-1 transition-transform" />
              </Button>
              <Button variant="outline" size="lg" className="group">
                <Play className="w-5 h-5 mr-2" />
                Watch Demo
              </Button>
            </motion.div>

            {/* Stats */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 1 }}
              className="grid grid-cols-2 lg:grid-cols-4 gap-6 pt-8"
            >
              {heroStats.map((stat, index) => {
                const Icon = stat.icon
                return (
                  <motion.div
                    key={stat.label}
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: 1.1 + index * 0.1 }}
                    className="text-center"
                  >
                    <div className="flex items-center justify-center w-12 h-12 mx-auto mb-2 rounded-xl bg-primary-500/10 border border-primary-500/20">
                      <Icon className="w-6 h-6 text-primary-400" />
                    </div>
                    <div className="text-2xl font-bold text-foreground">{stat.value}</div>
                    <div className="text-sm text-muted-foreground">{stat.label}</div>
                  </motion.div>
                )
              })}
            </motion.div>
          </motion.div>

          {/* Right Content - Hero Visual */}
          <motion.div
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.5 }}
            className="relative"
          >
            <EliteGlow color="#3b82f6" blur={40} spread={20} className="rounded-3xl">
              <div className="relative p-8 rounded-3xl bg-gradient-to-br from-card/80 to-card/60 backdrop-blur-lg border border-white/20">
                {/* Header */}
                <div className="flex items-center justify-between mb-6">
                  <div className="flex items-center gap-3">
                    <div className="w-3 h-3 rounded-full bg-success-500" />
                    <span className="text-sm font-medium text-foreground">Live Draft Analysis</span>
                  </div>
                  <div className="px-3 py-1 rounded-full bg-primary-500/20 border border-primary-500/30">
                    <span className="text-sm font-medium text-primary-400">Win Rate: 73%</span>
                  </div>
                </div>

                {/* Draft Board Preview */}
                <div className="space-y-4">
                  <div className="grid grid-cols-5 gap-3">
                    {['Top', 'Jungle', 'Mid', 'ADC', 'Support'].map((role, index) => (
                      <motion.div
                        key={role}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 1.2 + index * 0.1 }}
                        className="aspect-square rounded-xl bg-gradient-to-br from-muted/50 to-muted/30 border border-white/10 flex items-center justify-center"
                      >
                        <span className="text-xs font-medium text-muted-foreground">{role}</span>
                      </motion.div>
                    ))}
                  </div>

                  {/* Recommendations */}
                  <div className="space-y-3">
                    <h4 className="text-sm font-semibold text-foreground">Top Recommendations</h4>
                    <div className="space-y-2">
                      {['Aatrox', 'Vi', 'Ahri', 'Kai\'Sa', 'Rell'].map((champion, index) => (
                        <motion.div
                          key={champion}
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: 1.5 + index * 0.1 }}
                          className="flex items-center justify-between p-3 rounded-xl bg-gradient-to-r from-primary-500/10 to-secondary-500/10 border border-primary-500/20"
                        >
                          <span className="text-sm font-medium text-foreground">{champion}</span>
                          <span className="text-xs text-primary-400">+{index + 3}%</span>
                        </motion.div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </EliteGlow>
          </motion.div>
        </div>
      </Container>
    </Section>
  )
}
