import type { Metadata, Viewport } from 'next'
import type { ReactNode } from 'react'
import { Space_Grotesk, Inter, JetBrains_Mono } from 'next/font/google'
import './globals.css'
import { ThemeProvider } from '@/components/ThemeProvider'
import { SiteHeader } from '@/components/SiteHeader'
import { Footer } from '@/components/Footer'
import { CookieConsent } from '@/components/CookieConsent'
import { AnalyticsProvider } from '@/components/providers/AnalyticsProvider'
import { cn } from '@/lib/cn'
import { MotionProvider } from '@/components/providers/MotionProvider'

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-sans',
})

const spaceGrotesk = Space_Grotesk({
  subsets: ['latin'],
  variable: '--font-display',
})

const jetBrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  variable: '--font-mono',
})

export const metadata: Metadata = {
  title: 'StratMancer - Elite League of Legends Draft Analyzer',
  description: 'AI-powered draft analysis and win prediction for League of Legends with elite UI and advanced machine learning',
  keywords: ['League of Legends', 'Draft Analysis', 'Win Prediction', 'AI', 'Machine Learning', 'Elite UI', 'Premium Design'],
  authors: [{ name: 'StratMancer Team' }],
  creator: 'StratMancer',
  publisher: 'StratMancer',
  robots: {
    index: true,
    follow: true,
  },
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: 'https://stratmancer.com',
    title: 'StratMancer - Elite League of Legends Draft Analyzer',
    description: 'AI-powered draft analysis and win prediction for League of Legends with elite UI and advanced machine learning',
    siteName: 'StratMancer',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'StratMancer - Elite League of Legends Draft Analyzer',
    description: 'AI-powered draft analysis and win prediction for League of Legends with elite UI and advanced machine learning',
    creator: '@stratmancer',
  },
}

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#0ea5e9' },
    { media: '(prefers-color-scheme: dark)', color: '#0284c7' },
  ],
}

export default function RootLayout({
  children,
}: {
  children: ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning className="smooth-scroll">
      <body
        className={cn(
          inter.className,
          inter.variable,
          spaceGrotesk.variable,
          jetBrainsMono.variable,
          "antialiased bg-background text-foreground"
        )}
      >
        <ThemeProvider
          attribute="class"
          defaultTheme="dark"
          enableSystem
          disableTransitionOnChange
        >
          <MotionProvider>
            <AnalyticsProvider>
              <div className="min-h-screen flex flex-col">
                <SiteHeader />
                
                <main className="flex-1">
                  {children}
                </main>
                
                <Footer />
              </div>
              
              <CookieConsent />
            </AnalyticsProvider>
          </MotionProvider>
        </ThemeProvider>
      </body>
    </html>
  )
}
