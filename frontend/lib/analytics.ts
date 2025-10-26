"use client"

import { getCookiePreferences } from './cookies'

// Google Analytics Configuration
export const GA_TRACKING_ID = process.env.NEXT_PUBLIC_GA_ID || 'G-XXXXXXXXXX'

// Initialize Google Analytics
export function initializeAnalytics() {
  if (typeof window === 'undefined') return
  
  const preferences = getCookiePreferences()
  
  // Only initialize if analytics cookies are accepted
  if (!preferences.analytics) return
  
  // Load Google Analytics script
  const script = document.createElement('script')
  script.async = true
  script.src = `https://www.googletagmanager.com/gtag/js?id=${GA_TRACKING_ID}`
  document.head.appendChild(script)
  
  // Initialize gtag
  window.dataLayer = window.dataLayer || []
  function gtag(...args: any[]) {
    window.dataLayer.push(args)
  }
  window.gtag = gtag
  
  gtag('js', new Date())
  gtag('config', GA_TRACKING_ID, {
    page_title: document.title,
    page_location: window.location.href,
    anonymize_ip: true,
    allow_google_signals: false,
    allow_ad_personalization_signals: false
  })
}

// Track page views
export function trackPageView(url: string, title?: string) {
  if (typeof window === 'undefined' || !window.gtag) return
  
  const preferences = getCookiePreferences()
  if (!preferences.analytics) return
  
  window.gtag('config', GA_TRACKING_ID, {
    page_path: url,
    page_title: title || document.title,
    page_location: window.location.href
  })
}

// Track custom events
export function trackEvent(eventName: string, parameters?: Record<string, any>) {
  if (typeof window === 'undefined' || !window.gtag) return
  
  const preferences = getCookiePreferences()
  if (!preferences.analytics) return
  
  window.gtag('event', eventName, {
    event_category: parameters?.category || 'engagement',
    event_label: parameters?.label,
    value: parameters?.value,
    ...parameters
  })
}

// Draft Analysis Events
export function trackDraftEvent(action: string, details?: Record<string, any>) {
  trackEvent('draft_analysis', {
    category: 'draft',
    action,
    ...details
  })
}

// User Interaction Events
export function trackUserInteraction(element: string, action: string, details?: Record<string, any>) {
  trackEvent('user_interaction', {
    category: 'ui',
    action,
    label: element,
    ...details
  })
}

// Performance Events
export function trackPerformance(metric: string, value: number, details?: Record<string, any>) {
  trackEvent('performance', {
    category: 'performance',
    action: metric,
    value: Math.round(value),
    ...details
  })
}

// Error Tracking
export function trackError(error: string, details?: Record<string, any>) {
  trackEvent('error', {
    category: 'error',
    action: 'exception',
    label: error,
    ...details
  })
}

// Feature Usage Events
export function trackFeatureUsage(feature: string, action: string, details?: Record<string, any>) {
  trackEvent('feature_usage', {
    category: 'feature',
    action,
    label: feature,
    ...details
  })
}

// ELO Selection Tracking
export function trackELOSelection(elo: string) {
  trackDraftEvent('elo_selected', { elo })
}

// Champion Selection Tracking
export function trackChampionSelection(champion: string, role: string, team: string) {
  trackDraftEvent('champion_selected', { champion, role, team })
}

// Draft Completion Tracking
export function trackDraftCompletion(elo: string, duration: number, picks: number, bans: number) {
  trackDraftEvent('draft_completed', { 
    elo, 
    duration: Math.round(duration), 
    picks, 
    bans 
  })
}

// Meta Page Tracking
export function trackMetaPageView(elo: string) {
  trackEvent('meta_page_view', {
    category: 'meta',
    action: 'page_view',
    label: elo
  })
}

// Settings Changes Tracking
export function trackSettingsChange(setting: string, value: any) {
  trackEvent('settings_change', {
    category: 'settings',
    action: 'change',
    label: setting,
    value: String(value)
  })
}

// Cookie Consent Tracking
export function trackCookieConsent(action: string, preferences?: Record<string, boolean>) {
  trackEvent('cookie_consent', {
    category: 'privacy',
    action,
    preferences: preferences ? JSON.stringify(preferences) : undefined
  })
}

// Search Tracking
export function trackSearch(query: string, results: number) {
  trackEvent('search', {
    category: 'search',
    action: 'query',
    label: query,
    value: results
  })
}

// Navigation Tracking
export function trackNavigation(from: string, to: string) {
  trackEvent('navigation', {
    category: 'navigation',
    action: 'page_change',
    label: `${from} -> ${to}`
  })
}

// Session Tracking
export function trackSessionStart() {
  trackEvent('session_start', {
    category: 'session',
    action: 'start'
  })
}

export function trackSessionEnd(duration: number) {
  trackEvent('session_end', {
    category: 'session',
    action: 'end',
    value: Math.round(duration)
  })
}

// Custom Dimensions (if needed)
export function setCustomDimension(index: number, value: string) {
  if (typeof window === 'undefined' || !window.gtag) return
  
  const preferences = getCookiePreferences()
  if (!preferences.analytics) return
  
  window.gtag('config', GA_TRACKING_ID, {
    [`custom_map.dimension${index}`]: value
  })
}

// User Properties
export function setUserProperties(properties: Record<string, any>) {
  if (typeof window === 'undefined' || !window.gtag) return
  
  const preferences = getCookiePreferences()
  if (!preferences.analytics) return
  
  window.gtag('config', GA_TRACKING_ID, {
    user_properties: properties
  })
}

// Declare global types
declare global {
  interface Window {
    dataLayer: any[]
    gtag?: (...args: any[]) => void
  }
}
