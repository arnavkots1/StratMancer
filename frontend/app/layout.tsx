import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { Shield, Github } from 'lucide-react'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'StratMancer - League of Legends Draft Analyzer',
  description: 'AI-powered draft analysis and win prediction for League of Legends',
  keywords: ['League of Legends', 'Draft Analysis', 'Win Prediction', 'AI', 'Machine Learning'],
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <div className="min-h-screen flex flex-col">
          {/* Header */}
          <header className="bg-gray-900 border-b border-gray-800 sticky top-0 z-50">
            <div className="container mx-auto px-4 py-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <Shield className="w-8 h-8 text-gold-500" />
                  <div>
                    <h1 className="text-2xl font-bold text-gold-500">
                      StratMancer
                    </h1>
                    <p className="text-xs text-gray-400">
                      AI-Powered Draft Analysis
                    </p>
                  </div>
                </div>
                
                <nav className="flex items-center space-x-6">
                  <a
                    href="/draft"
                    className="text-gray-300 hover:text-gold-500 transition-colors"
                  >
                    Draft Analyzer
                  </a>
                  <a
                    href="https://github.com/yourusername/stratmancer"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-gray-400 hover:text-gray-300 transition-colors"
                  >
                    <Github className="w-5 h-5" />
                  </a>
                </nav>
              </div>
            </div>
          </header>

          {/* Main Content */}
          <main className="flex-1">
            {children}
          </main>

          {/* Footer */}
          <footer className="bg-gray-900 border-t border-gray-800 py-6">
            <div className="container mx-auto px-4">
              <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
                <p className="text-sm text-gray-400">
                  StratMancer isn't endorsed by Riot Games and doesn't reflect the views or opinions of Riot Games or anyone officially involved in producing or managing Riot Games properties.
                </p>
                <p className="text-sm text-gray-500">
                  © {new Date().getFullYear()} StratMancer
                </p>
              </div>
            </div>
          </footer>
        </div>
      </body>
    </html>
  )
}

