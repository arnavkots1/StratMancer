"use client"

import { trackPerformance, trackError } from './analytics'

// Performance monitoring utilities
export class PerformanceMonitor {
  private static instance: PerformanceMonitor
  private metrics: Map<string, number> = new Map()
  private observers: PerformanceObserver[] = []
  private maxMetrics = 100 // Limit stored metrics to prevent memory bloat

  static getInstance(): PerformanceMonitor {
    if (!PerformanceMonitor.instance) {
      PerformanceMonitor.instance = new PerformanceMonitor()
    }
    return PerformanceMonitor.instance
  }

  init() {
    if (typeof window === 'undefined') return
    
    this.setupPerformanceObserver()
    this.trackWebVitals()
    this.trackResourceTiming()
    this.trackNavigationTiming()
  }

  private setupPerformanceObserver() {
    if (typeof window === 'undefined' || !('PerformanceObserver' in window)) return

    // Observe all performance entries
    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        this.processPerformanceEntry(entry)
      }
    })

    try {
      observer.observe({ entryTypes: ['measure', 'navigation', 'resource', 'paint', 'largest-contentful-paint', 'first-input', 'layout-shift'] })
      this.observers.push(observer)
    } catch (e) {
      console.warn('Performance Observer not supported:', e)
    }
  }

  private processPerformanceEntry(entry: PerformanceEntry) {
    switch (entry.entryType) {
      case 'measure':
        this.trackCustomMeasure(entry)
        break
      case 'navigation':
        this.trackNavigationMetrics(entry as PerformanceNavigationTiming)
        break
      case 'resource':
        this.trackResourceMetrics(entry as PerformanceResourceTiming)
        break
      case 'paint':
        this.trackPaintMetrics(entry as PerformancePaintTiming)
        break
      case 'largest-contentful-paint':
        this.trackLCP(entry as PerformanceEntry)
        break
      case 'first-input':
        this.trackFID(entry as any)
        break
      case 'layout-shift':
        this.trackCLS(entry as PerformanceEntry)
        break
    }
  }

  private trackCustomMeasure(entry: PerformanceEntry) {
    // Limit metrics to prevent memory bloat
    if (this.metrics.size >= this.maxMetrics) {
      const firstKey = this.metrics.keys().next().value
      if (firstKey) {
        this.metrics.delete(firstKey)
      }
    }
    
    trackPerformance(`custom_${entry.name}`, entry.duration, {
      start_time: entry.startTime
    })
  }

  private trackNavigationMetrics(entry: PerformanceNavigationTiming) {
    const metrics = {
      dns_lookup: entry.domainLookupEnd - entry.domainLookupStart,
      tcp_connection: entry.connectEnd - entry.connectStart,
      ssl_negotiation: entry.secureConnectionStart > 0 ? entry.connectEnd - entry.secureConnectionStart : 0,
      request_response: entry.responseEnd - entry.requestStart,
      dom_processing: entry.domComplete - entry.domContentLoadedEventStart,
      page_load: entry.loadEventEnd - entry.fetchStart
    }

    Object.entries(metrics).forEach(([key, value]) => {
      if (value > 0) {
        trackPerformance(`navigation_${key}`, value)
      }
    })
  }

  private trackResourceMetrics(entry: PerformanceResourceTiming) {
    const duration = entry.responseEnd - entry.startTime
    const size = entry.transferSize || 0
    
    trackPerformance('resource_load', duration, {
      resource_type: this.getResourceType(entry.name),
      resource_size: size,
      cached: entry.transferSize === 0 && entry.decodedBodySize > 0
    })
  }

  private trackPaintMetrics(entry: PerformancePaintTiming) {
    trackPerformance(`paint_${entry.name}`, entry.startTime)
  }

  private trackLCP(entry: PerformanceEntry) {
    trackPerformance('largest_contentful_paint', entry.startTime, {
      element: (entry as any).element?.tagName || 'unknown'
    })
  }

  private trackFID(entry: any) {
    trackPerformance('first_input_delay', entry.processingStart - entry.startTime, {
      event_type: entry.name || 'unknown'
    })
  }

  private trackCLS(entry: PerformanceEntry) {
    const clsValue = (entry as any).value || 0
    trackPerformance('cumulative_layout_shift', clsValue)
  }

  private getResourceType(url: string): string {
    if (url.includes('.js')) return 'script'
    if (url.includes('.css')) return 'stylesheet'
    if (url.includes('.png') || url.includes('.jpg') || url.includes('.jpeg') || url.includes('.gif') || url.includes('.webp')) return 'image'
    if (url.includes('.woff') || url.includes('.woff2') || url.includes('.ttf')) return 'font'
    if (url.includes('api/') || url.includes('/api')) return 'api'
    return 'other'
  }

  private trackWebVitals() {
    // Track Core Web Vitals
    this.trackFCP() // First Contentful Paint
    this.trackTTI() // Time to Interactive
  }

  private trackFCP() {
    if (typeof window === 'undefined') return
    
    const observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (entry.name === 'first-contentful-paint') {
          trackPerformance('first_contentful_paint', entry.startTime)
        }
      }
    })

    try {
      observer.observe({ entryTypes: ['paint'] })
      this.observers.push(observer)
    } catch (e) {
      console.warn('FCP tracking not supported:', e)
    }
  }

  private trackTTI() {
    if (typeof window === 'undefined') return
    
    // Simple TTI approximation
    window.addEventListener('load', () => {
      setTimeout(() => {
        const tti = performance.now()
        trackPerformance('time_to_interactive', tti)
      }, 1000)
    })
  }

  private trackResourceTiming() {
    if (typeof window === 'undefined') return
    
    window.addEventListener('load', () => {
      const resources = performance.getEntriesByType('resource')
      resources.forEach((resource: any) => {
        if (resource.duration > 1000) { // Only track slow resources
          trackPerformance('slow_resource', resource.duration, {
            resource_url: resource.name,
            resource_type: this.getResourceType(resource.name)
          })
        }
      })
    })
  }

  private trackNavigationTiming() {
    if (typeof window === 'undefined') return
    
    window.addEventListener('load', () => {
    const navigation = performance.getEntriesByType('navigation')[0] as any
    if (navigation) {
      const loadTime = navigation.loadEventEnd - navigation.fetchStart
        trackPerformance('page_load_time', loadTime)
        
        if (loadTime > 3000) { // Track slow page loads
          trackPerformance('slow_page_load', loadTime)
        }
      }
    })
  }

  // Custom performance marks and measures
  mark(name: string) {
    if (typeof window === 'undefined') return
    performance.mark(name)
  }

  measure(name: string, startMark: string, endMark?: string) {
    if (typeof window === 'undefined') return
    
    try {
      if (endMark) {
        performance.measure(name, startMark, endMark)
      } else {
        performance.measure(name, startMark)
      }
    } catch (e) {
      console.warn('Performance measure failed:', e)
    }
  }

  // Track component render times
  trackComponentRender(componentName: string, renderTime: number) {
    trackPerformance(`component_render_${componentName}`, renderTime)
  }

  // Track API call performance
  trackAPICall(endpoint: string, duration: number, status: number) {
    trackPerformance('api_call', duration, {
      endpoint,
      status,
      success: status >= 200 && status < 300
    })
  }

  // Track user interaction performance
  trackInteractionPerformance(action: string, duration: number) {
    trackPerformance(`interaction_${action}`, duration)
  }

  // Memory usage tracking
  trackMemoryUsage() {
    if (typeof window === 'undefined' || !('memory' in performance)) return
    
    const memory = (performance as any).memory
    if (memory) {
      trackPerformance('memory_used', memory.usedJSHeapSize, {
        total_heap: memory.totalJSHeapSize,
        heap_limit: memory.jsHeapSizeLimit
      })
    }
  }

  // Error tracking
  trackError(error: Error, context?: string) {
    trackError(error.message, {
      stack: error.stack,
      context,
      url: window.location.href,
      user_agent: navigator.userAgent
    })
  }

  // Cleanup
  destroy() {
    this.observers.forEach(observer => observer.disconnect())
    this.observers = []
  }
}

// Initialize performance monitoring
export function initPerformanceMonitoring() {
  const monitor = PerformanceMonitor.getInstance()
  monitor.init()
  
  // Track memory usage periodically (reduced frequency to save memory)
  setInterval(() => {
    monitor.trackMemoryUsage()
  }, 60000) // Every 60 seconds instead of 30
  
  return monitor
}

// React hook for component performance tracking
export function usePerformanceTracking(componentName: string) {
  const startTime = performance.now()
  
  return {
    markRenderComplete: () => {
      const endTime = performance.now()
      const renderTime = endTime - startTime
      
      const monitor = PerformanceMonitor.getInstance()
      monitor.trackComponentRender(componentName, renderTime)
    }
  }
}
