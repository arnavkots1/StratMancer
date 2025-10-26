"use client"

import { trackError } from './analytics'

// Monitoring and alerting system
export class MonitoringSystem {
  private static instance: MonitoringSystem
  private alerts: Array<{ type: string; message: string; timestamp: number; severity: 'low' | 'medium' | 'high' | 'critical' }> = []
  private metrics: Map<string, number[]> = new Map()
  private thresholds: Map<string, { min?: number; max?: number; alert: boolean }> = new Map()

  static getInstance(): MonitoringSystem {
    if (!MonitoringSystem.instance) {
      MonitoringSystem.instance = new MonitoringSystem()
    }
    return MonitoringSystem.instance
  }

  init() {
    if (typeof window === 'undefined') return
    
    this.setupThresholds()
    this.startHealthChecks()
    this.monitorSystemHealth()
    this.monitorUserExperience()
  }

  private setupThresholds() {
    // Performance thresholds
    this.thresholds.set('page_load_time', { max: 3000, alert: true })
    this.thresholds.set('api_response_time', { max: 2000, alert: true })
    this.thresholds.set('memory_usage', { max: 200 * 1024 * 1024, alert: true }) // 200MB
    this.thresholds.set('error_rate', { max: 0.05, alert: true }) // 5%
    
    // User experience thresholds
    this.thresholds.set('bounce_rate', { max: 0.7, alert: true }) // 70%
    this.thresholds.set('session_duration', { min: 30, alert: true }) // 30 seconds
    this.thresholds.set('conversion_rate', { min: 0.02, alert: true }) // 2%
  }

  private startHealthChecks() {
    // Check system health every 30 seconds
    setInterval(() => {
      this.performHealthCheck()
    }, 30000)

    // Check critical metrics every 10 seconds
    setInterval(() => {
      this.checkCriticalMetrics()
    }, 10000)
  }

  private performHealthCheck() {
    const health = {
      timestamp: Date.now(),
      memory: this.getMemoryUsage(),
      performance: this.getPerformanceMetrics(),
      errors: this.getErrorCount(),
      users: this.getActiveUsers()
    }

    // Check if any metrics exceed thresholds
    this.checkThresholds(health)
    
    // Send health data to monitoring service (in production)
    this.sendHealthData(health)
  }

  private checkCriticalMetrics() {
    // Check memory usage
    const memoryUsage = this.getMemoryUsage()
    if (memoryUsage > 200 * 1024 * 1024) { // 200MB
      this.createAlert('high', 'High memory usage detected', {
        memory: memoryUsage,
        threshold: 200 * 1024 * 1024
      })
    }

    // Check error rate
    const errorRate = this.getErrorRate()
    if (errorRate > 0.1) { // 10%
      this.createAlert('critical', 'High error rate detected', {
        errorRate,
        threshold: 0.1
      })
    }

    // Check API response times
    const avgResponseTime = this.getAverageResponseTime()
    if (avgResponseTime > 10000) { // 10 seconds
      this.createAlert('high', 'Slow API response times', {
        responseTime: avgResponseTime,
        threshold: 10000
      })
    }
  }

  private monitorSystemHealth() {
    // Monitor memory usage
    this.monitorMemoryUsage()
    
    // Monitor network connectivity
    this.monitorNetworkConnectivity()
    
    // Monitor browser compatibility
    this.monitorBrowserCompatibility()
    
    // Monitor feature availability
    this.monitorFeatureAvailability()
  }

  private monitorUserExperience() {
    // Monitor page load times
    this.monitorPageLoadTimes()
    
    // Monitor user interactions
    this.monitorUserInteractions()
    
    // Monitor conversion funnels
    this.monitorConversionFunnels()
    
    // Monitor user satisfaction
    this.monitorUserSatisfaction()
  }

  private monitorMemoryUsage() {
    if ('memory' in performance) {
      const memory = (performance as any).memory
      
      setInterval(() => {
        const used = memory.usedJSHeapSize
        const total = memory.totalJSHeapSize
        const limit = memory.jsHeapSizeLimit
        
        this.recordMetric('memory_used', used)
        this.recordMetric('memory_total', total)
        this.recordMetric('memory_limit', limit)
        
        // Alert if memory usage is high
        if (used > limit * 0.8) {
          this.createAlert('high', 'Memory usage approaching limit', {
            used,
            limit,
            percentage: (used / limit) * 100
          })
        }
      }, 5000)
    }
  }

  private monitorNetworkConnectivity() {
    // Monitor online/offline status
    window.addEventListener('online', () => {
      this.createAlert('low', 'Network connectivity restored')
    })
    
    window.addEventListener('offline', () => {
      this.createAlert('medium', 'Network connectivity lost')
    })

    // Monitor connection quality
    if ('connection' in navigator) {
      const connection = (navigator as any).connection
      
      connection.addEventListener('change', () => {
        this.recordMetric('connection_speed', connection.effectiveType)
        this.recordMetric('connection_downlink', connection.downlink)
        
        if (connection.effectiveType === 'slow-2g' || connection.effectiveType === '2g') {
          this.createAlert('medium', 'Slow network connection detected', {
            type: connection.effectiveType,
            downlink: connection.downlink
          })
        }
      })
    }
  }

  private monitorBrowserCompatibility() {
    // Check for required features
    const requiredFeatures = [
      'fetch',
      'Promise',
      'localStorage',
      'sessionStorage',
      'addEventListener'
    ]
    
    const missingFeatures = requiredFeatures.filter(feature => {
      try {
        return !(feature in window)
      } catch {
        return true
      }
    })
    
    if (missingFeatures.length > 0) {
      this.createAlert('high', 'Browser compatibility issues detected', {
        missingFeatures
      })
    }
  }

  private monitorFeatureAvailability() {
    // Check if critical features are working
    const features = {
      localStorage: this.testLocalStorage(),
      sessionStorage: this.testSessionStorage(),
      fetch: this.testFetch(),
      webGL: this.testWebGL(),
      canvas: this.testCanvas()
    }
    
    const failedFeatures = Object.entries(features)
      .filter(([_, working]) => !working)
      .map(([feature, _]) => feature)
    
    if (failedFeatures.length > 0) {
      this.createAlert('high', 'Feature availability issues detected', {
        failedFeatures
      })
    }
  }

  private monitorPageLoadTimes() {
    window.addEventListener('load', () => {
      const loadTime = performance.now()
      this.recordMetric('page_load_time', loadTime)
      
      if (loadTime > 3000) {
        this.createAlert('medium', 'Slow page load time', {
          loadTime,
          threshold: 3000
        })
      }
    })
  }

  private monitorUserInteractions() {
    let _interactionCount = 0
    let lastInteraction = Date.now()
    
    const trackInteraction = () => {
      _interactionCount++
      lastInteraction = Date.now()
    }
    
    document.addEventListener('click', trackInteraction)
    document.addEventListener('keydown', trackInteraction)
    document.addEventListener('scroll', trackInteraction)
    
    // Check for user engagement
    setInterval(() => {
      const timeSinceLastInteraction = Date.now() - lastInteraction
      
      if (timeSinceLastInteraction > 300000) { // 5 minutes
        this.recordMetric('user_inactivity', timeSinceLastInteraction)
      }
    }, 60000) // Check every minute
  }

  private monitorConversionFunnels() {
    // Track key conversion events
    const conversionEvents = [
      'page_view',
      'draft_started',
      'draft_completed',
      'analysis_viewed',
      'recommendation_clicked'
    ]
    
    conversionEvents.forEach(event => {
      this.recordMetric(`conversion_${event}`, 1)
    })
  }

  private monitorUserSatisfaction() {
    // Monitor for user frustration indicators
    let errorCount = 0
    let lastErrorTime = 0
    
    window.addEventListener('error', () => {
      errorCount++
      lastErrorTime = Date.now()
      
      // Only alert for very high error frequency (20+ errors)
      if (errorCount > 20) {
        this.createAlert('medium', 'High error frequency detected', {
          errorCount,
          timeWindow: Date.now() - lastErrorTime
        })
      }
    })
    
    // Reset error count after 5 minutes
    setInterval(() => {
      if (Date.now() - lastErrorTime > 300000) {
        errorCount = 0
      }
    }, 60000)
  }

  // Utility methods
  private getMemoryUsage(): number {
    if ('memory' in performance) {
      return (performance as any).memory.usedJSHeapSize
    }
    return 0
  }

  private getPerformanceMetrics() {
    const navigation = performance.getEntriesByType('navigation')[0] as any
    return {
      loadTime: navigation?.loadEventEnd - navigation?.fetchStart || 0,
      domContentLoaded: navigation?.domContentLoadedEventEnd - navigation?.fetchStart || 0,
      firstPaint: performance.getEntriesByName('first-paint')[0]?.startTime || 0
    }
  }

  private getErrorCount(): number {
    return this.alerts.filter(alert => alert.type.includes('error')).length
  }

  private getActiveUsers(): number {
    // In a real app, this would come from your analytics service
    return 1
  }

  private getErrorRate(): number {
    const totalEvents = this.metrics.get('total_events')?.reduce((a, b) => a + b, 0) || 1
    const errorEvents = this.getErrorCount()
    return errorEvents / totalEvents
  }

  private getAverageResponseTime(): number {
    const responseTimes = this.metrics.get('api_response_time') || []
    return responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length || 0
  }

  private recordMetric(name: string, value: number) {
    if (!this.metrics.has(name)) {
      this.metrics.set(name, [])
    }
    
    const values = this.metrics.get(name)!
    values.push(value)
    
    // Keep only last 100 values
    if (values.length > 100) {
      values.shift()
    }
  }

  private checkThresholds(health: any) {
    this.thresholds.forEach((threshold, metric) => {
      const value = health[metric]
      if (value !== undefined) {
        if (threshold.min !== undefined && value < threshold.min) {
          this.createAlert('medium', `${metric} below threshold`, {
            value,
            threshold: threshold.min
          })
        }
        if (threshold.max !== undefined && value > threshold.max) {
          this.createAlert('medium', `${metric} above threshold`, {
            value,
            threshold: threshold.max
          })
        }
      }
    })
  }

  private createAlert(severity: 'low' | 'medium' | 'high' | 'critical', message: string, data?: any) {
    const alert = {
      type: 'system_alert',
      message,
      timestamp: Date.now(),
      severity,
      data
    }
    
    this.alerts.push(alert)
    
    // Track in analytics
    trackError(`Alert: ${message}`, {
      severity,
      data,
      timestamp: alert.timestamp
    })
    
    // Log to console in development
    if (process.env.NODE_ENV === 'development') {
      console.warn(`[${severity.toUpperCase()}] ${message}`, data)
    }
    
    // In production, send to monitoring service
    this.sendAlert(alert)
  }

  private sendHealthData(_health: any) {
    // In production, send to your monitoring service (e.g., DataDog, New Relic, etc.)
    if (process.env.NODE_ENV === 'production') {
      // Example: send to monitoring endpoint
      // fetch('/api/monitoring/health', {
      //   method: 'POST',
      //   body: JSON.stringify(health)
      // })
    }
  }

  private sendAlert(alert: any) {
    // In production, send to your alerting service
    if (process.env.NODE_ENV === 'production') {
      // Example: send to alerting endpoint
      // fetch('/api/monitoring/alerts', {
      //   method: 'POST',
      //   body: JSON.stringify(alert)
      // })
    }
  }

  // Test methods for feature availability
  private testLocalStorage(): boolean {
    try {
      localStorage.setItem('test', 'test')
      localStorage.removeItem('test')
      return true
    } catch {
      return false
    }
  }

  private testSessionStorage(): boolean {
    try {
      sessionStorage.setItem('test', 'test')
      sessionStorage.removeItem('test')
      return true
    } catch {
      return false
    }
  }

  private testFetch(): boolean {
    return typeof fetch !== 'undefined'
  }

  private testWebGL(): boolean {
    try {
      const canvas = document.createElement('canvas')
      return !!(canvas.getContext('webgl') || canvas.getContext('experimental-webgl'))
    } catch {
      return false
    }
  }

  private testCanvas(): boolean {
    try {
      const canvas = document.createElement('canvas')
      return !!(canvas.getContext('2d'))
    } catch {
      return false
    }
  }

  // Public methods
  getAlerts() {
    return this.alerts
  }

  getMetrics() {
    return this.metrics
  }

  clearAlerts() {
    this.alerts = []
  }

  // Cleanup
  destroy() {
    this.alerts = []
    this.metrics.clear()
    this.thresholds.clear()
  }
}

// Initialize monitoring system
export function initMonitoring() {
  const monitoring = MonitoringSystem.getInstance()
  monitoring.init()
  return monitoring
}
