import type { Metadata, Viewport } from 'next'
import type { ReactNode } from 'react'
import { Space_Grotesk, Inter, JetBrains_Mono } from 'next/font/google'
import './globals.css'
import { ThemeProvider } from '@/components/ThemeProvider'
import { SiteHeader } from '@/components/SiteHeader'
import { Footer } from '@/components/Footer'
import { CookieConsent } from '@/components/CookieConsent'
import { AnalyticsProvider } from '@/components/providers/AnalyticsProvider'
import { GoogleTagManager, GoogleTagManagerNoscript } from '@/components/GoogleTagManager'
import { getSearchConsoleMetadata } from '@/components/GoogleSearchConsole'
import { cn } from '../lib/cn'
import { MotionProvider } from '@/components/providers/MotionProvider'
import { ErrorBoundary } from '@/components/ErrorBoundary'

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
  title: 'RiftAI - Elite League of Legends Draft Analyzer',
  description: 'AI-powered draft analysis and win prediction for League of Legends with elite UI and advanced machine learning',
  keywords: ['League of Legends', 'Draft Analysis', 'Win Prediction', 'AI', 'Machine Learning', 'Elite UI', 'Premium Design'],
  authors: [{ name: 'RiftAI Team' }],
  creator: 'RiftAI',
  publisher: 'RiftAI',
  robots: {
    index: true,
    follow: true,
  },
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: 'https://riftai.com',
    title: 'RiftAI - Elite League of Legends Draft Analyzer',
    description: 'AI-powered draft analysis and win prediction for League of Legends with elite UI and advanced machine learning',
    siteName: 'RiftAI',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'RiftAI - Elite League of Legends Draft Analyzer',
    description: 'AI-powered draft analysis and win prediction for League of Legends with elite UI and advanced machine learning',
    creator: '@riftai',
  },
  ...getSearchConsoleMetadata(),
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
  const gtmId = process.env.NEXT_PUBLIC_GTM_ID

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
        {/* Google Tag Manager - Script loads in head via Next.js Script component */}
        {gtmId && <GoogleTagManager gtmId={gtmId} />}
        {/* Google Tag Manager (noscript) - Must be immediately after opening <body> tag */}
        {gtmId && <GoogleTagManagerNoscript gtmId={gtmId} />}
        <ThemeProvider
          attribute="class"
          defaultTheme="dark"
          enableSystem
          disableTransitionOnChange
        >
          <MotionProvider>
            <AnalyticsProvider>
              <ErrorBoundary>
                <div className="min-h-screen flex flex-col">
                  <SiteHeader />
                  
                  <main className="flex-1">
                    {children}
                  </main>
                  
                  <Footer />
                </div>
                
                <CookieConsent />
              </ErrorBoundary>
            </AnalyticsProvider>
          </MotionProvider>
        </ThemeProvider>
      </body>
    </html>
  )
}
