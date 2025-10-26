"use client"

export interface CookiePreferences {
  essential: boolean
  analytics: boolean
  preferences: boolean
  marketing: boolean
}

export const DEFAULT_PREFERENCES: CookiePreferences = {
  essential: true,
  analytics: false,
  preferences: false,
  marketing: false
}

export function getCookiePreferences(): CookiePreferences {
  if (typeof window === 'undefined') return DEFAULT_PREFERENCES
  
  try {
    const stored = localStorage.getItem('cookie-consent')
    if (stored) {
      return JSON.parse(stored)
    }
  } catch (error) {
    console.error('Error parsing cookie preferences:', error)
  }
  
  return DEFAULT_PREFERENCES
}

export function setCookiePreferences(preferences: CookiePreferences): void {
  if (typeof window === 'undefined') return
  
  try {
    localStorage.setItem('cookie-consent', JSON.stringify(preferences))
    
    // Apply cookie preferences
    applyCookiePreferences(preferences)
  } catch (error) {
    console.error('Error saving cookie preferences:', error)
  }
}

export function applyCookiePreferences(preferences: CookiePreferences): void {
  if (typeof window === 'undefined') return
  
  // Analytics cookies (Google Analytics)
  if (preferences.analytics) {
    // Enable Google Analytics
    window.gtag?.('consent', 'update', {
      analytics_storage: 'granted'
    })
  } else {
    // Disable Google Analytics
    window.gtag?.('consent', 'update', {
      analytics_storage: 'denied'
    })
  }
  
  // Marketing cookies
  if (preferences.marketing) {
    window.gtag?.('consent', 'update', {
      ad_storage: 'granted',
      ad_user_data: 'granted',
      ad_personalization: 'granted'
    })
  } else {
    window.gtag?.('consent', 'update', {
      ad_storage: 'denied',
      ad_user_data: 'denied',
      ad_personalization: 'denied'
    })
  }
  
  // Set preference cookies
  if (preferences.preferences) {
    // Set theme preference
    const theme = localStorage.getItem('theme')
    if (theme) {
      document.cookie = `theme=${theme}; path=/; max-age=31536000; SameSite=Lax`
    }
    
    // Set ELO preference
    const eloPreference = localStorage.getItem('elo-preference')
    if (eloPreference) {
      document.cookie = `elo-preference=${eloPreference}; path=/; max-age=2592000; SameSite=Lax`
    }
  } else {
    // Clear preference cookies
    document.cookie = 'theme=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT'
    document.cookie = 'elo-preference=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT'
  }
}

export function clearAllCookies(): void {
  if (typeof window === 'undefined') return
  
  // Clear localStorage
  localStorage.removeItem('cookie-consent')
  localStorage.removeItem('theme')
  localStorage.removeItem('elo-preference')
  
  // Clear all cookies
  document.cookie.split(";").forEach(function(c) { 
    document.cookie = c.replace(/^ +/, "").replace(/=.*/, "=;expires=" + new Date().toUTCString() + ";path=/"); 
  })
}

export function hasConsented(): boolean {
  if (typeof window === 'undefined') return false
  return localStorage.getItem('cookie-consent') !== null
}

// Google Analytics consent configuration
export function initializeGoogleAnalytics(): void {
  if (typeof window === 'undefined') return
  
  const preferences = getCookiePreferences()
  
  // Initialize gtag with consent
  window.gtag?.('consent', 'default', {
    analytics_storage: preferences.analytics ? 'granted' : 'denied',
    ad_storage: preferences.marketing ? 'granted' : 'denied',
    ad_user_data: preferences.marketing ? 'granted' : 'denied',
    ad_personalization: preferences.marketing ? 'granted' : 'denied',
    wait_for_update: 500
  })
}

// Declare gtag for TypeScript
declare global {
  interface Window {
    gtag?: (...args: any[]) => void
  }
}
