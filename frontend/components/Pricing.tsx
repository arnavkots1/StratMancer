"use client"

import * as React from "react"
import { m } from "framer-motion"
import { Check, Zap, Crown, Star, ArrowRight } from "lucide-react"
import { cn } from "@/lib/cn"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { EliteGlow } from "@/components/Glow"
import { Section, Container } from "@/components/Section"
import { eliteMotionPresets } from "@/lib/motion"

const plans = [
  {
    name: "Free",
    description: "Perfect for casual players and getting started",
    price: "$0",
    period: "forever",
    icon: Zap,
    color: "primary",
    popular: false,
    features: [
      "Basic draft analysis",
      "Standard recommendations",
      "Community support",
      "Limited API access",
      "Basic meta tracking"
    ],
    cta: "Get Started Free",
    ctaVariant: "outline" as const
  },
  {
    name: "Pro",
    description: "For serious players and content creators",
    price: "$9.99",
    period: "per month",
    icon: Star,
    color: "secondary",
    popular: true,
    features: [
      "Advanced AI analysis",
      "ELO-specific recommendations",
      "Priority support",
      "Full API access",
      "Detailed meta analytics",
      "Export capabilities",
      "Custom team analysis"
    ],
    cta: "Start Pro Trial",
    ctaVariant: "default" as const
  },
  {
    name: "Enterprise",
    description: "For professional teams and organizations",
    price: "Custom",
    period: "contact us",
    icon: Crown,
    color: "accent",
    popular: false,
    features: [
      "Everything in Pro",
      "White-label solution",
      "Custom integrations",
      "Dedicated support",
      "Advanced analytics",
      "Team collaboration tools",
      "Custom model training",
      "SLA guarantees"
    ],
    cta: "Contact Sales",
    ctaVariant: "outline" as const
  }
]

export function Pricing() {
  return (
    <Section variant="default" size="lg">
      <Container size="xl">
        <m.div
          initial="initial"
          animate="animate"
          variants={eliteMotionPresets.page}
          className="text-center mb-16"
        >
          <Badge variant="outline" className="mb-4">
            <Star className="w-4 h-4 mr-2" />
            Pricing
          </Badge>
          <h2 className="text-4xl lg:text-6xl font-bold mb-6">
            <span className="gradient-text">Choose Your</span>
            <br />
            <span className="text-foreground">Perfect Plan</span>
          </h2>
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
            From casual players to professional teams, we have a plan that fits your needs and budget.
          </p>
        </m.div>

        <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
          {plans.map((plan, index) => {
            const Icon = plan.icon
            return (
              <m.div
                key={plan.name}
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="relative"
              >
                {plan.popular && (
                  <div className="absolute -top-4 left-1/2 transform -translate-x-1/2 z-10">
                    <Badge variant="premium" className="px-4 py-1">
                      Most Popular
                    </Badge>
                  </div>
                )}

                <EliteGlow 
                  color={plan.color === 'primary' ? '#3b82f6' : plan.color === 'secondary' ? '#d946ef' : '#f97316'} 
                  blur={plan.popular ? 30 : 20}
                  className="h-full"
                >
                  <Card 
                    variant={plan.popular ? "premium" : "glass"} 
                    className={cn(
                      "h-full relative overflow-hidden",
                      plan.popular && "border-primary-500/50 shadow-elite"
                    )}
                  >
                    {/* Background Pattern */}
                    <div className="absolute inset-0 opacity-5">
                      <div className="absolute inset-0 bg-gradient-to-br from-primary-500/20 via-transparent to-secondary-500/20" />
                    </div>

                    <div className="relative p-8">
                      {/* Header */}
                      <div className="text-center mb-8">
                        <div className={cn(
                          "inline-flex items-center justify-center w-16 h-16 rounded-2xl mb-4",
                          plan.color === 'primary' && "bg-primary-500/10 border border-primary-500/20",
                          plan.color === 'secondary' && "bg-secondary-500/10 border border-secondary-500/20",
                          plan.color === 'accent' && "bg-accent-500/10 border border-accent-500/20"
                        )}>
                          <Icon className={cn(
                            "w-8 h-8",
                            plan.color === 'primary' && "text-primary-400",
                            plan.color === 'secondary' && "text-secondary-400",
                            plan.color === 'accent' && "text-accent-400"
                          )} />
                        </div>
                        
                        <h3 className="text-2xl font-bold text-foreground mb-2">{plan.name}</h3>
                        <p className="text-muted-foreground mb-4">{plan.description}</p>
                        
                        <div className="mb-6">
                          <span className="text-4xl font-bold text-foreground">{plan.price}</span>
                          <span className="text-muted-foreground ml-2">/{plan.period}</span>
                        </div>
                      </div>

                      {/* Features */}
                      <ul className="space-y-4 mb-8">
                        {plan.features.map((feature, featureIndex) => (
                          <m.li
                            key={feature}
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: 0.5 + index * 0.1 + featureIndex * 0.05 }}
                            className="flex items-center gap-3"
                          >
                            <div className={cn(
                              "flex-shrink-0 w-5 h-5 rounded-full flex items-center justify-center",
                              plan.color === 'primary' && "bg-primary-500/20",
                              plan.color === 'secondary' && "bg-secondary-500/20",
                              plan.color === 'accent' && "bg-accent-500/20"
                            )}>
                              <Check className={cn(
                                "w-3 h-3",
                                plan.color === 'primary' && "text-primary-400",
                                plan.color === 'secondary' && "text-secondary-400",
                                plan.color === 'accent' && "text-accent-400"
                              )} />
                            </div>
                            <span className="text-muted-foreground">{feature}</span>
                          </m.li>
                        ))}
                      </ul>

                      {/* CTA */}
                      <Button 
                        variant={plan.ctaVariant}
                        size="lg" 
                        className={cn(
                          "w-full group",
                          plan.popular && "bg-gradient-to-r from-primary-500 to-secondary-500 hover:from-primary-600 hover:to-secondary-600"
                        )}
                      >
                        {plan.cta}
                        <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
                      </Button>
                    </div>
                  </Card>
                </EliteGlow>
              </m.div>
            )
          })}
        </div>

        {/* Additional Info */}
        <m.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="text-center mt-12"
        >
          <p className="text-muted-foreground mb-4">
            All plans include access to our community and regular updates.
          </p>
          <div className="flex flex-wrap justify-center gap-6 text-sm text-muted-foreground">
            <span>✓ 30-day money-back guarantee</span>
            <span>✓ Cancel anytime</span>
            <span>✓ No setup fees</span>
            <span>✓ 24/7 support</span>
          </div>
        </m.div>
      </Container>
    </Section>
  )
}
