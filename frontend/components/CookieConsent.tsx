/* eslint-disable react/no-unescaped-entities */
"use client"

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Settings, Shield, BarChart3, Target, X, Check } from 'lucide-react'
import { m, AnimatePresence } from 'framer-motion'

// Inline analytics functions to avoid import issues
const GA_TRACKING_ID = process.env.NEXT_PUBLIC_GA_ID || 'G-XXXXXXXXXX'

const DEFAULT_PREFERENCES = {
  essential: true,
  analytics: false,
  preferences: false,
  marketing: false
}

function getCookiePreferences() {
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

function initializeAnalytics() {
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

function trackEvent(eventName: string, parameters?: Record<string, any>) {
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

function trackCookieConsent(action: string, preferences?: Record<string, boolean>) {
  trackEvent('cookie_consent', {
    category: 'privacy',
    action,
    preferences: preferences ? JSON.stringify(preferences) : undefined
  })
}

interface CookiePreferences {
  essential: boolean
  analytics: boolean
  preferences: boolean
  marketing: boolean
}

export function CookieConsent() {
  const [showBanner, setShowBanner] = useState(false)
  const [showSettings, setShowSettings] = useState(false)
  const [preferences, setPreferences] = useState<CookiePreferences>({
    essential: true, // Always true
    analytics: false,
    preferences: false,
    marketing: false
  })

  useEffect(() => {
    // Check if user has already made a choice
    const consent = localStorage.getItem('cookie-consent')
    if (!consent) {
      setShowBanner(true)
    } else {
      const savedPreferences = JSON.parse(consent)
      setPreferences(savedPreferences)
    }
  }, [])

  const handleAcceptAll = () => {
    const allAccepted = {
      essential: true,
      analytics: true,
      preferences: true,
      marketing: true
    }
    setPreferences(allAccepted)
    localStorage.setItem('cookie-consent', JSON.stringify(allAccepted))
    
    // Initialize analytics
    initializeAnalytics()
    
    // Track consent
    trackCookieConsent('accept_all', allAccepted)
    
    setShowBanner(false)
    setShowSettings(false)
  }

  const handleRejectAll = () => {
    const onlyEssential = {
      essential: true,
      analytics: false,
      preferences: false,
      marketing: false
    }
    setPreferences(onlyEssential)
    localStorage.setItem('cookie-consent', JSON.stringify(onlyEssential))
    
    // Track consent
    trackCookieConsent('reject_all', onlyEssential)
    
    setShowBanner(false)
    setShowSettings(false)
  }

  const handleSavePreferences = () => {
    localStorage.setItem('cookie-consent', JSON.stringify(preferences))
    
    // Initialize analytics if accepted
    if (preferences.analytics) {
      initializeAnalytics()
    }
    
    // Track consent
    trackCookieConsent('custom_preferences', preferences as unknown as Record<string, boolean>)
    
    setShowBanner(false)
    setShowSettings(false)
  }

  const togglePreference = (key: keyof CookiePreferences) => {
    if (key === 'essential') return // Essential cookies cannot be disabled
    setPreferences(prev => ({
      ...prev,
      [key]: !prev[key]
    }))
  }

  const cookieTypes = [
    {
      key: 'essential' as keyof CookiePreferences,
      title: 'Essential Cookies',
      description: 'Required for basic website functionality',
      icon: Shield,
      color: 'text-green-500',
      bgColor: 'bg-green-100',
      borderColor: 'border-green-200',
      alwaysActive: true
    },
    {
      key: 'analytics' as keyof CookiePreferences,
      title: 'Analytics Cookies',
      description: 'Help us understand how you use our website',
      icon: BarChart3,
      color: 'text-blue-500',
      bgColor: 'bg-blue-100',
      borderColor: 'border-blue-200',
      alwaysActive: false
    },
    {
      key: 'preferences' as keyof CookiePreferences,
      title: 'Preference Cookies',
      description: 'Remember your settings and preferences',
      icon: Settings,
      color: 'text-purple-500',
      bgColor: 'bg-purple-100',
      borderColor: 'border-purple-200',
      alwaysActive: false
    },
    {
      key: 'marketing' as keyof CookiePreferences,
      title: 'Marketing Cookies',
      description: 'Show you relevant advertisements',
      icon: Target,
      color: 'text-orange-500',
      bgColor: 'bg-orange-100',
      borderColor: 'border-orange-200',
      alwaysActive: false
    }
  ]

  if (!showBanner) return null

  return (
    <AnimatePresence>
      <m.div
        initial={{ opacity: 0, y: 100 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: 100 }}
        className="fixed bottom-0 left-0 right-0 z-50 p-4"
      >
        <Card className="max-w-4xl mx-auto p-6 shadow-2xl border-2">
          {!showSettings ? (
            // Cookie Banner
            <div className="space-y-4">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h3 className="text-lg font-semibold mb-2">🍪 We use cookies</h3>
                  <p className="text-muted-foreground text-sm leading-relaxed">
                    We use cookies to enhance your experience, analyze site usage, and assist in our marketing efforts. 
                    By clicking "Accept All", you consent to our use of cookies. You can manage your preferences at any time.
                  </p>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowBanner(false)}
                  className="text-muted-foreground hover:text-foreground"
                >
                  <X className="w-4 h-4" />
                </Button>
              </div>

              <div className="flex flex-col sm:flex-row gap-3">
                <Button onClick={handleAcceptAll} className="flex-1">
                  Accept All
                </Button>
                <Button 
                  variant="outline" 
                  onClick={handleRejectAll}
                  className="flex-1"
                >
                  Reject All
                </Button>
                <Button 
                  variant="ghost" 
                  onClick={() => setShowSettings(true)}
                  className="flex-1"
                >
                  <Settings className="w-4 h-4 mr-2" />
                  Customize
                </Button>
              </div>

              <div className="text-xs text-muted-foreground text-center">
                Learn more in our{' '}
                <a href="/privacy" className="text-primary hover:underline">Privacy Policy</a>
                {' '}and{' '}
                <a href="/cookies" className="text-primary hover:underline">Cookie Policy</a>
              </div>
            </div>
          ) : (
            // Cookie Settings
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold">Cookie Preferences</h3>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowSettings(false)}
                  className="text-muted-foreground hover:text-foreground"
                >
                  <X className="w-4 h-4" />
                </Button>
              </div>

              <div className="space-y-4">
                {cookieTypes.map((type) => {
                  const Icon = type.icon
                  const isEnabled = preferences[type.key]
                  
                  return (
                    <div
                      key={type.key}
                      className={`flex items-center justify-between p-4 rounded-lg border ${
                        type.alwaysActive ? 'bg-muted/50' : 'bg-background'
                      }`}
                    >
                      <div className="flex items-center space-x-3">
                        <div className={`p-2 rounded-lg ${type.bgColor} ${type.borderColor} border`}>
                          <Icon className={`w-5 h-5 ${type.color}`} />
                        </div>
                        <div>
                          <div className="flex items-center space-x-2">
                            <h4 className="font-medium">{type.title}</h4>
                            {type.alwaysActive && (
                              <Badge variant="secondary" className="text-xs">
                                Always Active
                              </Badge>
                            )}
                          </div>
                          <p className="text-sm text-muted-foreground">{type.description}</p>
                        </div>
                      </div>
                      
                      <div className="flex items-center space-x-2">
                        {type.alwaysActive ? (
                          <div className="flex items-center justify-center w-8 h-8 rounded-full bg-green-100">
                            <Check className="w-4 h-4 text-green-600" />
                          </div>
                        ) : (
                          <button
                            onClick={() => togglePreference(type.key)}
                            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                              isEnabled ? 'bg-primary' : 'bg-muted'
                            }`}
                          >
                            <span
                              className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                                isEnabled ? 'translate-x-6' : 'translate-x-1'
                              }`}
                            />
                          </button>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>

              <div className="flex flex-col sm:flex-row gap-3 pt-4 border-t">
                <Button onClick={handleSavePreferences} className="flex-1">
                  Save Preferences
                </Button>
                <Button 
                  variant="outline" 
                  onClick={handleAcceptAll}
                  className="flex-1"
                >
                  Accept All
                </Button>
                <Button 
                  variant="ghost" 
                  onClick={handleRejectAll}
                  className="flex-1"
                >
                  Reject All
                </Button>
              </div>

              <div className="text-xs text-muted-foreground text-center">
                Learn more in our{' '}
                <a href="/privacy" className="text-primary hover:underline">Privacy Policy</a>
                {' '}and{' '}
                <a href="/cookies" className="text-primary hover:underline">Cookie Policy</a>
              </div>
            </div>
          )}
        </Card>
      </m.div>
    </AnimatePresence>
  )
}
