"use client"

import * as React from "react"
import { motion } from "framer-motion"
import { 
  Brain, 
  Zap, 
  Target, 
  BarChart3, 
  Users, 
  Shield, 
  TrendingUp, 
  Clock,
  Cpu,
  Database,
  Globe
} from "lucide-react"
import { cn } from "@/lib/cn"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Glow } from "@/components/Glow"
import { Section, Container, Grid } from "@/components/Section"
import { eliteMotionPresets } from "@/lib/motion"

const features = [
  {
    title: "AI-Powered Draft Analysis",
    description: "Advanced machine learning models analyze thousands of matches to provide real-time draft recommendations with 94.2% accuracy.",
    icon: Brain,
    color: "primary",
    stats: "94.2% Accuracy",
    features: ["Real-time predictions", "ELO-specific insights", "Meta-aware recommendations"]
  },
  {
    title: "Lightning-Fast Performance",
    description: "Get instant feedback on every pick and ban with sub-200ms response times, keeping pace with the fastest draft phases.",
    icon: Zap,
    color: "secondary",
    stats: "<200ms Response",
    features: ["Instant predictions", "Real-time updates", "Optimized algorithms"]
  },
  {
    title: "Comprehensive Meta Tracking",
    description: "Stay ahead of the meta with detailed champion performance analytics, win rates, and trend analysis across all ELOs.",
    icon: TrendingUp,
    color: "accent",
    stats: "163+ Champions",
    features: ["Meta trends", "Champion stats", "Patch analysis"]
  },
  {
    title: "Professional Analytics",
    description: "Advanced analytics dashboard for coaches and teams with detailed insights, performance metrics, and strategic recommendations.",
    icon: BarChart3,
    color: "primary",
    stats: "10K+ Users",
    features: ["Team analytics", "Performance metrics", "Strategic insights"]
  },
  {
    title: "ELO-Specific Intelligence",
    description: "Tailored recommendations for every skill level, from Iron to Challenger, ensuring relevant advice for your rank.",
    icon: Target,
    color: "secondary",
    stats: "All Ranks",
    features: ["Rank-specific data", "Skill-appropriate picks", "Adaptive learning"]
  },
  {
    title: "Real-Time Data Pipeline",
    description: "Live data collection from Riot's API ensures your analysis is always based on the latest patch and meta trends.",
    icon: Database,
    color: "accent",
    stats: "Live Updates",
    features: ["Riot API integration", "Patch-aware data", "Continuous learning"]
  }
]

const workflowSteps = [
  {
    step: "01",
    title: "Data Collection",
    description: "Automated pipeline collects match data from Riot's API, processing thousands of games across all ranks and regions.",
    icon: Database,
    color: "primary"
  },
  {
    step: "02", 
    title: "ML Processing",
    description: "Advanced machine learning models analyze draft patterns, champion synergies, and meta trends to generate insights.",
    icon: Cpu,
    color: "secondary"
  },
  {
    step: "03",
    title: "Real-Time Analysis",
    description: "Instant draft analysis provides win probability, recommendations, and strategic insights as picks are made.",
    icon: Zap,
    color: "accent"
  },
  {
    step: "04",
    title: "Global Delivery",
    description: "Insights are delivered to users worldwide through our optimized API and web platform with minimal latency.",
    icon: Globe,
    color: "primary"
  }
]

export function FeatureRows() {
  return (
    <>
      {/* Features Grid */}
      <Section variant="default" size="lg">
        <Container size="xl">
          <motion.div
            initial="initial"
            animate="animate"
            variants={eliteMotionPresets.page}
            className="text-center mb-16"
          >
            <Badge variant="outline" className="mb-4">
              <Shield className="w-4 h-4 mr-2" />
              Elite Features
            </Badge>
            <h2 className="text-4xl lg:text-6xl font-bold mb-6">
              <span className="gradient-text">Powerful Tools</span>
              <br />
              <span className="text-foreground">for Every Player</span>
            </h2>
            <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
              From casual players to professional teams, StratMancer provides the insights you need to dominate the draft phase.
            </p>
          </motion.div>

          <Grid cols={3} gap="lg">
            {features.map((feature, index) => {
              const Icon = feature.icon
              return (
                <motion.div
                  key={feature.title}
                  initial={{ opacity: 0, y: 30 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                >
                  <Glow variant={feature.color as any} className="h-full">
                    <Card variant="glass" className="h-full group hover:scale-105 transition-all duration-300">
                      <div className="p-6">
                        <div className="flex items-center justify-between mb-4">
                          <div className="p-3 rounded-xl bg-primary-500/10 border border-primary-500/20">
                            <Icon className="w-6 h-6 text-primary-400" />
                          </div>
                          <Badge variant="outline" className="text-xs">
                            {feature.stats}
                          </Badge>
                        </div>
                        
                        <h3 className="text-xl font-semibold mb-3 text-foreground">
                          {feature.title}
                        </h3>
                        
                        <p className="text-muted-foreground mb-4">
                          {feature.description}
                        </p>
                        
                        <ul className="space-y-2">
                          {feature.features.map((item) => (
                            <li key={item} className="flex items-center gap-2 text-sm text-muted-foreground">
                              <div className="w-1.5 h-1.5 rounded-full bg-primary-500" />
                              {item}
                            </li>
                          ))}
                        </ul>
                      </div>
                    </Card>
                  </Glow>
                </motion.div>
              )
            })}
          </Grid>
        </Container>
      </Section>

      {/* Workflow Section */}
      <Section variant="premium" size="lg">
        <Container size="xl">
          <motion.div
            initial="initial"
            animate="animate"
            variants={eliteMotionPresets.page}
            className="text-center mb-16"
          >
            <Badge variant="outline" className="mb-4">
              <Clock className="w-4 h-4 mr-2" />
              How It Works
            </Badge>
            <h2 className="text-4xl lg:text-6xl font-bold mb-6">
              <span className="gradient-text">From Data</span>
              <br />
              <span className="text-foreground">to Insights</span>
            </h2>
            <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
              Our advanced pipeline processes millions of matches to deliver the most accurate draft analysis available.
            </p>
          </motion.div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {workflowSteps.map((step, index) => {
              const Icon = step.icon
              return (
                <motion.div
                  key={step.step}
                  initial={{ opacity: 0, y: 30 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="relative"
                >
                  {/* Connection Line */}
                  {index < workflowSteps.length - 1 && (
                    <div className="hidden lg:block absolute top-12 left-full w-full h-0.5 bg-gradient-to-r from-primary-500/50 to-transparent z-0" />
                  )}
                  
                  <div className="relative z-10">
                    <Glow variant={step.color as any}>
                      <Card variant="premium" className="text-center group hover:scale-105 transition-all duration-300">
                        <div className="p-6">
                          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-primary-500/10 border border-primary-500/20 mb-4">
                            <Icon className="w-8 h-8 text-primary-400" />
                          </div>
                          
                          <div className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-primary-500 text-primary-foreground text-sm font-bold mb-4">
                            {step.step}
                          </div>
                          
                          <h3 className="text-lg font-semibold mb-3 text-foreground">
                            {step.title}
                          </h3>
                          
                          <p className="text-muted-foreground text-sm">
                            {step.description}
                          </p>
                        </div>
                      </Card>
                    </Glow>
                  </div>
                </motion.div>
              )
            })}
          </div>
        </Container>
      </Section>
    </>
  )
}
