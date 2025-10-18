import Link from 'next/link'
import { ArrowRight, Zap, TrendingUp, Shield } from 'lucide-react'

export default function HomePage() {
  return (
    <div className="container mx-auto px-4 py-16">
      {/* Hero Section */}
      <div className="text-center max-w-4xl mx-auto mb-20">
        <h1 className="text-5xl md:text-6xl font-bold mb-6 bg-gradient-to-r from-gold-500 to-gold-300 bg-clip-text text-transparent">
          Master the Draft Phase
        </h1>
        <p className="text-xl text-gray-400 mb-8">
          AI-powered draft analysis using machine learning trained on thousands of high-elo matches.
          Predict win probabilities and optimize team compositions before the game begins.
        </p>
        <Link 
          href="/draft"
          className="inline-flex items-center space-x-2 bg-gold-600 text-gray-900 px-8 py-4 rounded-lg font-semibold text-lg hover:bg-gold-500 transition-all duration-200 shadow-lg shadow-gold-500/20 hover:shadow-gold-500/40"
        >
          <span>Launch Draft Analyzer</span>
          <ArrowRight className="w-5 h-5" />
        </Link>
      </div>

      {/* Features */}
      <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
        <div className="card text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gold-900/30 rounded-lg mb-4">
            <Zap className="w-8 h-8 text-gold-500" />
          </div>
          <h3 className="text-xl font-bold mb-2">Real-Time Predictions</h3>
          <p className="text-gray-400">
            Get instant win probability calculations as you select champions.
            See how each pick affects your team's chances.
          </p>
        </div>

        <div className="card text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gold-900/30 rounded-lg mb-4">
            <TrendingUp className="w-8 h-8 text-gold-500" />
          </div>
          <h3 className="text-xl font-bold mb-2">Smart Insights</h3>
          <p className="text-gray-400">
            Understand why your draft is strong or weak with detailed explanations
            of team synergies and counters.
          </p>
        </div>

        <div className="card text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gold-900/30 rounded-lg mb-4">
            <Shield className="w-8 h-8 text-gold-500" />
          </div>
          <h3 className="text-xl font-bold mb-2">Real Match Data</h3>
          <p className="text-gray-400">
            Models trained on actual Gold rank matches collected from
            Riot Games API for accurate predictions.
          </p>
        </div>
      </div>

      {/* Stats */}
      <div className="max-w-4xl mx-auto mt-20 grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
        <div>
          <div className="text-4xl font-bold text-gold-500 mb-2">163</div>
          <div className="text-sm text-gray-400">Champions</div>
        </div>
        <div>
          <div className="text-4xl font-bold text-gold-500 mb-2">100</div>
          <div className="text-sm text-gray-400">Real Gold Matches</div>
        </div>
        <div>
          <div className="text-4xl font-bold text-gold-500 mb-2">Gold</div>
          <div className="text-sm text-gray-400">Rank Data Available</div>
        </div>
        <div>
          <div className="text-4xl font-bold text-gold-500 mb-2">&lt;500ms</div>
          <div className="text-sm text-gray-400">Prediction Time</div>
        </div>
      </div>
    </div>
  )
}

