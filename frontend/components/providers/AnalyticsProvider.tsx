"use client"

import React, { useEffect } from 'react'
import { usePathname } from 'next/navigation'
import { initializeAnalytics, trackPageView, trackSessionStart, trackSessionEnd } from '@/lib/analytics'
import { initPerformanceMonitoring } from '@/lib/performance'
import { initSecurityMonitoring } from '@/lib/security'
import { initMonitoring } from '@/lib/monitoring'

interface AnalyticsProviderProps {
  children: React.ReactNode
}

export function AnalyticsProvider({ children }: AnalyticsProviderProps) {
  const pathname = usePathname()

  useEffect(() => {
    // Defer initialization to prevent blocking initial render
    const initTimer = setTimeout(() => {
      // Initialize all monitoring systems
      initializeAnalytics()
      initPerformanceMonitoring()
      initSecurityMonitoring()
      initMonitoring()
      
      // Track session start
      trackSessionStart()
      
      // Track initial page view
      trackPageView(pathname)
    }, 100) // Small delay to let the page render first
    
    // Track session end on page unload
    const handleBeforeUnload = () => {
      const sessionDuration = performance.now()
      trackSessionEnd(sessionDuration)
    }
    
    window.addEventListener('beforeunload', handleBeforeUnload)
    
    return () => {
      clearTimeout(initTimer)
      window.removeEventListener('beforeunload', handleBeforeUnload)
    }
  }, [pathname])

  useEffect(() => {
    // Track page views on route changes
    trackPageView(pathname)
  }, [pathname])

  return <>{children}</>
}
