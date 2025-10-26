"use client"

import { trackError } from './analytics'

// Security monitoring and threat detection
export class SecurityMonitor {
  private static instance: SecurityMonitor
  private suspiciousActivities: Map<string, number> = new Map()
  private blockedIPs: Set<string> = new Set()
  private rateLimits: Map<string, { count: number; lastReset: number }> = new Map()
  private trackRequest?: (_url: string) => void

  static getInstance(): SecurityMonitor {
    if (!SecurityMonitor.instance) {
      SecurityMonitor.instance = new SecurityMonitor()
    }
    return SecurityMonitor.instance
  }

  init() {
    if (typeof window === 'undefined') return
    
    // Temporarily disable security monitoring to prevent fetch conflicts
    // this.setupSecurityMonitoring()
    // this.monitorConsoleErrors()
    // this.monitorNetworkRequests()
    // this.monitorDOMChanges()
    
    console.log('Security monitoring temporarily disabled to prevent fetch conflicts')
  }

  private setupSecurityMonitoring() {
    // Monitor for suspicious activities
    this.monitorSuspiciousActivities()
    
    // Monitor for XSS attempts
    this.monitorXSSAttempts()
    
    // Monitor for clickjacking attempts
    this.monitorClickjacking()
    
    // Monitor for data exfiltration attempts
    this.monitorDataExfiltration()
  }

  private monitorSuspiciousActivities() {
    // Monitor rapid clicks (potential bot activity)
    let clickCount = 0
    let lastClickTime = 0
    
    document.addEventListener('click', (event) => {
      const now = Date.now()
      
      if (now - lastClickTime < 100) { // Less than 100ms between clicks
        clickCount++
        if (clickCount > 10) {
          this.reportSuspiciousActivity('rapid_clicks', {
            count: clickCount,
            target: (event.target as Element)?.tagName || 'unknown'
          })
        }
      } else {
        clickCount = 0
      }
      
      lastClickTime = now
    })

    // Monitor rapid keyboard input
    let keyCount = 0
    let lastKeyTime = 0
    
    document.addEventListener('keydown', (event) => {
      const now = Date.now()
      
      if (now - lastKeyTime < 50) { // Less than 50ms between keys
        keyCount++
        if (keyCount > 20) {
          this.reportSuspiciousActivity('rapid_keyboard', {
            count: keyCount,
            key: event.key
          })
        }
      } else {
        keyCount = 0
      }
      
      lastKeyTime = now
    })
  }

  private monitorXSSAttempts() {
    // Monitor for script injection attempts
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        mutation.addedNodes.forEach((node) => {
          if (node.nodeType === Node.ELEMENT_NODE) {
            const element = node as Element
            
            // Check for suspicious script tags
            if (element.tagName === 'SCRIPT' && element.innerHTML.includes('eval')) {
              this.reportSuspiciousActivity('xss_attempt', {
                type: 'script_injection',
                content: element.innerHTML.substring(0, 100)
              })
            }
            
            // Check for suspicious attributes
            if (element.hasAttribute('onload') || element.hasAttribute('onerror')) {
              this.reportSuspiciousActivity('xss_attempt', {
                type: 'event_handler_injection',
                tag: element.tagName,
                attributes: Array.from(element.attributes).map(attr => attr.name)
              })
            }
          }
        })
      })
    })

    observer.observe(document.body, {
      childList: true,
      subtree: true
    })
  }

  private monitorClickjacking() {
    // Check if the page is being framed
    if (window.top !== window.self) {
      this.reportSuspiciousActivity('clickjacking_attempt', {
        type: 'page_framing',
        referrer: document.referrer
      })
    }

    // Monitor for invisible overlays
    const checkForInvisibleOverlays = () => {
      const elements = document.querySelectorAll('*')
      elements.forEach((element) => {
        const style = window.getComputedStyle(element)
        if (style.position === 'fixed' &&
            parseInt(style.zIndex) > 1000 &&
            style.opacity === '0' &&
            element.clientWidth > 100 &&
            element.clientHeight > 100) {
          this.reportSuspiciousActivity('clickjacking_attempt', {
            type: 'invisible_overlay',
            element: element.tagName,
            zIndex: style.zIndex
          })
        }
      })
    }

    // Check periodically
    setInterval(checkForInvisibleOverlays, 5000)
  }

  private monitorDataExfiltration() {
    // Monitor for suspicious network requests
    const originalFetch = window.fetch
    window.fetch = async (...args) => {
      const url = args[0] as string
      
      // Track request for network monitoring
      if (this.trackRequest) {
        this.trackRequest(url)
      }
      
      // Check for suspicious domains
      if (this.isSuspiciousDomain(url)) {
        this.reportSuspiciousActivity('data_exfiltration', {
          type: 'suspicious_fetch',
          url: url
        })
      }
      
      return originalFetch.apply(window, args)
    }

    // Monitor for suspicious form submissions
    document.addEventListener('submit', (event) => {
      const form = event.target as HTMLFormElement
      const action = form.action
      
      if (this.isSuspiciousDomain(action)) {
        this.reportSuspiciousActivity('data_exfiltration', {
          type: 'suspicious_form_submission',
          action: action
        })
      }
    })
  }

  private monitorConsoleErrors() {
    // Monitor for console errors that might indicate security issues
    const originalError = console.error
    console.error = (...args) => {
      const message = args.join(' ')
      
      // Check for security-related errors
      if (message.includes('CSP') || 
          message.includes('XSS') || 
          message.includes('CSRF') ||
          message.includes('Content Security Policy')) {
        this.reportSuspiciousActivity('security_error', {
          type: 'console_error',
          message: message
        })
      }
      
      originalError.apply(console, args)
    }
  }

  private monitorNetworkRequests() {
    // Monitor for suspicious network patterns
    const requests: Array<{ url: string; timestamp: number }> = []
    
    // Don't override fetch again - use the existing override from monitorDataExfiltration
    // Just track requests for analysis
    const trackRequest = (url: string) => {
      const now = Date.now()
      
      requests.push({ url, timestamp: now })
      
      // Keep only recent requests (last 10 seconds)
      const recentRequests = requests.filter(req => now - req.timestamp < 10000)
      requests.length = 0
      requests.push(...recentRequests)
      
      // Check for rapid requests to the same domain
      const sameDomainRequests = requests.filter(req => 
        new URL(req.url).hostname === new URL(url).hostname
      )
      
      if (sameDomainRequests.length > 20) {
        this.reportSuspiciousActivity('rapid_requests', {
          domain: new URL(url).hostname,
          count: sameDomainRequests.length
        })
      }
    }
    
    // Store the tracking function for use by the fetch override
    this.trackRequest = trackRequest
  }

  private monitorDOMChanges() {
    // Monitor for suspicious DOM modifications
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.type === 'childList') {
          mutation.addedNodes.forEach((node) => {
            if (node.nodeType === Node.ELEMENT_NODE) {
              const element = node as Element
              
              // Check for suspicious iframe additions
              if (element.tagName === 'IFRAME') {
                const src = element.getAttribute('src')
                if (src && this.isSuspiciousDomain(src)) {
                  this.reportSuspiciousActivity('suspicious_iframe', {
                    src: src
                  })
                }
              }
            }
          })
        }
      })
    })

    observer.observe(document.body, {
      childList: true,
      subtree: true
    })
  }

  private isSuspiciousDomain(url: string): boolean {
    try {
      const urlObj = new URL(url)
      const hostname = urlObj.hostname.toLowerCase()
      
      // List of suspicious domains/patterns
      const suspiciousPatterns = [
        'malicious.com',
        'phishing.com',
        'steal-data.com',
        'evil.com',
        'hack.com'
      ]
      
      return suspiciousPatterns.some(pattern => hostname.includes(pattern))
    } catch {
      return false
    }
  }

  private reportSuspiciousActivity(type: string, details: Record<string, any>) {
    // Track the suspicious activity
    trackError(`Security Alert: ${type}`, {
      type,
      details,
      timestamp: new Date().toISOString(),
      userAgent: navigator.userAgent,
      url: window.location.href,
      referrer: document.referrer
    })

    // Log to console in development
    if (process.env.NODE_ENV === 'development') {
      console.warn('Security Alert:', type, details)
    }

    // In production, you might want to send this to a security monitoring service
    // or block the user if the activity is severe enough
  }

  // Rate limiting
  checkRateLimit(identifier: string, maxRequests: number = 100, windowMs: number = 60000): boolean {
    const now = Date.now()
    const limit = this.rateLimits.get(identifier)
    
    if (!limit || now - limit.lastReset > windowMs) {
      this.rateLimits.set(identifier, { count: 1, lastReset: now })
      return true
    }
    
    if (limit.count >= maxRequests) {
      return false
    }
    
    limit.count++
    return true
  }

  // Block suspicious IPs (in a real app, this would be server-side)
  blockIP(ip: string) {
    this.blockedIPs.add(ip)
  }

  isIPBlocked(ip: string): boolean {
    return this.blockedIPs.has(ip)
  }

  // Cleanup
  destroy() {
    // Clean up any observers or event listeners
    this.suspiciousActivities.clear()
    this.rateLimits.clear()
  }
}

// Initialize security monitoring
export function initSecurityMonitoring() {
  const monitor = SecurityMonitor.getInstance()
  monitor.init()
  return monitor
}

// Security utilities
export function sanitizeInput(input: string): string {
  return input
    .replace(/[<>]/g, '') // Remove potential HTML tags
    .replace(/javascript:/gi, '') // Remove javascript: protocol
    .replace(/on\w+=/gi, '') // Remove event handlers
    .trim()
}

export function validateURL(url: string): boolean {
  try {
    const urlObj = new URL(url)
    return ['http:', 'https:'].includes(urlObj.protocol)
  } catch {
    return false
  }
}

export function generateCSRFToken(): string {
  const array = new Uint8Array(32)
  crypto.getRandomValues(array)
  return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('')
}
