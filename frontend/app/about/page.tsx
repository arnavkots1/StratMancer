/* eslint-disable react/no-unescaped-entities */
import type { Metadata } from 'next'
import { Container } from '@/components/Section'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Brain, Zap, Target, Users, Award, TrendingUp } from 'lucide-react'

export const metadata: Metadata = {
  title: 'About Us - StratMancer',
  description: 'Learn about StratMancer - The ultimate League of Legends draft analysis platform powered by machine learning',
}

export default function AboutPage() {
  return (
    <Container className="py-16">
      <div className="max-w-6xl mx-auto">
        {/* Hero Section */}
        <div className="text-center mb-16">
          <h1 className="text-5xl font-bold gradient-text mb-6">About StratMancer</h1>
          <p className="text-xl text-muted-foreground max-w-3xl mx-auto leading-relaxed">
            We're revolutionizing League of Legends draft analysis with cutting-edge machine learning, 
            providing players with the insights they need to make smarter picks and climb the ranks.
          </p>
        </div>

        {/* Mission Section */}
        <Card className="p-8 mb-12">
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold mb-4">Our Mission</h2>
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
              To democratize competitive League of Legends knowledge by making advanced draft analysis 
              accessible to players of all skill levels through AI-powered insights.
            </p>
          </div>
        </Card>

        {/* Features Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 mb-16">
          <Card className="p-6 text-center">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-primary/10 border border-primary/20 mb-4">
              <Brain className="w-8 h-8 text-primary" />
            </div>
            <h3 className="text-xl font-semibold mb-3">AI-Powered Analysis</h3>
            <p className="text-muted-foreground">
              Advanced machine learning models trained on millions of matches to provide accurate win probability predictions.
            </p>
          </Card>

          <Card className="p-6 text-center">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-secondary/10 border border-secondary/20 mb-4">
              <Zap className="w-8 h-8 text-secondary" />
            </div>
            <h3 className="text-xl font-semibold mb-3">Real-Time Insights</h3>
            <p className="text-muted-foreground">
              Get instant feedback on your draft decisions with live win probability calculations and recommendations.
            </p>
          </Card>

          <Card className="p-6 text-center">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-accent/10 border border-accent/20 mb-4">
              <Target className="w-8 h-8 text-accent" />
            </div>
            <h3 className="text-xl font-semibold mb-3">ELO-Specific Models</h3>
            <p className="text-muted-foreground">
              Tailored analysis for different skill levels - from Iron to Challenger - ensuring relevant insights for every player.
            </p>
          </Card>
        </div>

        {/* Story Section */}
        <div className="grid lg:grid-cols-2 gap-12 mb-16">
          <div>
            <h2 className="text-3xl font-bold mb-6">Our Story</h2>
            <div className="space-y-4 text-muted-foreground leading-relaxed">
              <p>
                StratMancer was born from a simple observation: League of Legends draft phase is one of the most 
                critical moments in any match, yet most players lack the tools to make informed decisions.
              </p>
              <p>
                As passionate League players and data scientists, we recognized the potential of machine learning 
                to transform draft analysis. We spent months collecting and analyzing millions of matches, 
                building sophisticated models that understand the complex interactions between champions, roles, and team compositions.
              </p>
              <p>
                Today, StratMancer serves thousands of players worldwide, helping them make smarter picks, 
                understand the meta, and ultimately improve their gameplay through data-driven insights.
              </p>
            </div>
          </div>
          
          <div className="space-y-6">
            <Card className="p-6">
              <div className="flex items-center mb-4">
                <Users className="w-6 h-6 text-primary mr-3" />
                <h3 className="text-xl font-semibold">Community Driven</h3>
              </div>
              <p className="text-muted-foreground">
                Built by players, for players. Our features are developed based on real community feedback and needs.
              </p>
            </Card>

            <Card className="p-6">
              <div className="flex items-center mb-4">
                <Award className="w-6 h-6 text-secondary mr-3" />
                <h3 className="text-xl font-semibold">Proven Results</h3>
              </div>
              <p className="text-muted-foreground">
                Our models achieve high accuracy rates and are continuously improved with the latest match data.
              </p>
            </Card>

            <Card className="p-6">
              <div className="flex items-center mb-4">
                <TrendingUp className="w-6 h-6 text-accent mr-3" />
                <h3 className="text-xl font-semibold">Always Evolving</h3>
              </div>
              <p className="text-muted-foreground">
                We continuously update our models to reflect the latest meta changes and champion updates.
              </p>
            </Card>
          </div>
        </div>

        {/* Technology Section */}
        <Card className="p-8 mb-16">
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold mb-4">Technology Stack</h2>
            <p className="text-lg text-muted-foreground">
              Built with modern technologies for performance, reliability, and scalability
            </p>
          </div>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="text-center">
              <Badge variant="secondary" className="mb-3">Machine Learning</Badge>
              <p className="text-sm text-muted-foreground">XGBoost, Scikit-learn, Pandas</p>
            </div>
            <div className="text-center">
              <Badge variant="secondary" className="mb-3">Backend</Badge>
              <p className="text-sm text-muted-foreground">FastAPI, Python, Redis</p>
            </div>
            <div className="text-center">
              <Badge variant="secondary" className="mb-3">Frontend</Badge>
              <p className="text-sm text-muted-foreground">Next.js, React, TypeScript</p>
            </div>
            <div className="text-center">
              <Badge variant="secondary" className="mb-3">Data</Badge>
              <p className="text-sm text-muted-foreground">Riot Games API, PostgreSQL</p>
            </div>
          </div>
        </Card>

        {/* Stats Section */}
        <div className="grid md:grid-cols-4 gap-8 mb-16">
          <Card className="p-6 text-center">
            <div className="text-3xl font-bold text-primary mb-2">1M+</div>
            <p className="text-muted-foreground">Matches Analyzed</p>
          </Card>
          <Card className="p-6 text-center">
            <div className="text-3xl font-bold text-secondary mb-2">163</div>
            <p className="text-muted-foreground">Champions Supported</p>
          </Card>
          <Card className="p-6 text-center">
            <div className="text-3xl font-bold text-accent mb-2">3</div>
            <p className="text-muted-foreground">ELO Tiers</p>
          </Card>
          <Card className="p-6 text-center">
            <div className="text-3xl font-bold text-primary mb-2">99.9%</div>
            <p className="text-muted-foreground">Uptime</p>
          </Card>
        </div>

        {/* Values Section */}
        <Card className="p-8">
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold mb-4">Our Values</h2>
            <p className="text-lg text-muted-foreground">
              The principles that guide everything we do
            </p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-8">
            <div className="text-center">
              <h3 className="text-xl font-semibold mb-3">Transparency</h3>
              <p className="text-muted-foreground">
                We believe in open communication about our methods, data sources, and model performance.
              </p>
            </div>
            <div className="text-center">
              <h3 className="text-xl font-semibold mb-3">Accuracy</h3>
              <p className="text-muted-foreground">
                We continuously strive for the highest accuracy in our predictions and analysis.
              </p>
            </div>
            <div className="text-center">
              <h3 className="text-xl font-semibold mb-3">Accessibility</h3>
              <p className="text-muted-foreground">
                Advanced draft analysis should be available to all players, regardless of skill level.
              </p>
            </div>
          </div>
        </Card>

        {/* CTA Section */}
        <div className="text-center mt-16">
          <h2 className="text-3xl font-bold mb-4">Ready to Improve Your Drafts?</h2>
          <p className="text-lg text-muted-foreground mb-8">
            Join thousands of players who are already using StratMancer to make smarter picks
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <a 
              href="/draft" 
              className="inline-flex items-center justify-center px-8 py-3 bg-primary text-primary-foreground rounded-lg font-semibold hover:bg-primary/90 transition-colors"
            >
              Try Draft Analyzer
            </a>
            <a 
              href="/contact" 
              className="inline-flex items-center justify-center px-8 py-3 border border-border rounded-lg font-semibold hover:bg-muted transition-colors"
            >
              Contact Us
            </a>
          </div>
        </div>
      </div>
    </Container>
  )
}
