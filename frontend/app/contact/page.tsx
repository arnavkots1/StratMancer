/* eslint-disable react/no-unescaped-entities */
"use client"

import React, { useState } from 'react'
import { Container } from '@/components/Section'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Mail, Send, CheckCircle, AlertCircle } from 'lucide-react'
import { m } from 'framer-motion'
import { fadeUp, stagger } from '@/lib/motion'

export default function ContactPage() {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    subject: '',
    category: '',
    message: ''
  })
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isSubmitted, setIsSubmitted] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)
    setSubmitError(null)
    
    try {
      // Simulate form submission with potential error
      await new Promise((resolve, reject) => {
        setTimeout(() => {
          // Simulate 10% chance of error for demonstration
          if (Math.random() < 0.1) {
            reject(new Error('Failed to send message. Please try again.'))
          } else {
            resolve(true)
          }
        }, 1000)
      })
      
      setIsSubmitted(true)
      setIsSubmitting(false)
      
      // Reset form after 3 seconds
      setTimeout(() => {
        setIsSubmitted(false)
        setFormData({ name: '', email: '', subject: '', category: '', message: '' })
      }, 3000)
    } catch (error) {
      setSubmitError(error instanceof Error ? error.message : 'An unexpected error occurred')
      setIsSubmitting(false)
    }
  }

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  return (
    <Container className="py-8 md:py-16">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <m.div
          initial="initial"
          animate="animate"
          variants={stagger}
          className="text-center mb-8 md:mb-12"
        >
          <m.h1
            variants={fadeUp}
            className="text-3xl md:text-4xl font-bold gradient-text mb-4"
          >
            Contact Us
          </m.h1>
          <m.p
            variants={fadeUp}
            className="text-muted-foreground text-lg max-w-2xl mx-auto"
          >
            Have questions about RiftAI? We'd love to hear from you. 
            Send us a message and we'll respond as soon as possible.
          </m.p>
        </m.div>

        <div className="grid lg:grid-cols-2 gap-8 md:gap-12">
          {/* Contact Information */}
          <m.div
            initial="initial"
            animate="animate"
            variants={stagger}
            className="space-y-6"
          >
            <m.div variants={fadeUp}>
              <h2 className="text-2xl font-semibold mb-6">Get in Touch</h2>
            </m.div>

            <m.div variants={fadeUp} className="space-y-4">
              <div className="flex items-start space-x-4">
                <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-primary/10 border border-primary/20 flex items-center justify-center">
                  <Mail className="w-5 h-5 text-primary" />
                </div>
                <div>
                  <h3 className="font-medium">Email</h3>
                  <p className="text-muted-foreground text-sm">riftai@outlook.com</p>
                  <p className="text-muted-foreground text-sm">We'll respond within 24 hours</p>
                </div>
              </div>
            </m.div>

            <m.div variants={fadeUp} className="pt-6">
              <Card className="p-6 bg-gradient-to-br from-primary/5 to-secondary/5 border-primary/20">
                <h3 className="font-semibold mb-3">Quick Response Times</h3>
                <ul className="space-y-2 text-sm text-muted-foreground">
                  <li>• General inquiries: 24 hours</li>
                  <li>• Technical support: 12 hours</li>
                  <li>• Bug reports: 6 hours</li>
                  <li>• Feature requests: 48 hours</li>
                </ul>
              </Card>
            </m.div>
          </m.div>

          {/* Contact Form */}
          <m.div
            initial="initial"
            animate="animate"
            variants={stagger}
            className="lg:order-first"
          >
            <Card className="p-6 md:p-8">
              <m.div variants={fadeUp}>
                <h2 className="text-2xl font-semibold mb-6">Send us a Message</h2>
              </m.div>

              {isSubmitted ? (
                <m.div
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="text-center py-8"
                >
                  <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
                  <h3 className="text-xl font-semibold mb-2">Message Sent!</h3>
                  <p className="text-muted-foreground">
                    Thank you for contacting us. We'll get back to you soon.
                  </p>
                </m.div>
              ) : (
                <m.form
                  initial="initial"
                  animate="animate"
                  variants={stagger}
                  onSubmit={handleSubmit}
                  className="space-y-6"
                >
                  <div className="grid md:grid-cols-2 gap-4">
                    <m.div variants={fadeUp}>
                      <Label htmlFor="name">Name *</Label>
                      <Input
                        id="name"
                        type="text"
                        value={formData.name}
                        onChange={(e) => handleInputChange('name', e.target.value)}
                        required
                        className="mt-1"
                        placeholder="Your name"
                      />
                    </m.div>

                    <m.div variants={fadeUp}>
                      <Label htmlFor="email">Email *</Label>
                      <Input
                        id="email"
                        type="email"
                        value={formData.email}
                        onChange={(e) => handleInputChange('email', e.target.value)}
                        required
                        className="mt-1"
                        placeholder="your@email.com"
                      />
                    </m.div>
                  </div>

                  <m.div variants={fadeUp}>
                    <Label htmlFor="category">Category</Label>
                    <Select value={formData.category} onValueChange={(value) => handleInputChange('category', value)}>
                      <SelectTrigger className="mt-1">
                        <SelectValue placeholder="Select a category" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="general">General Inquiry</SelectItem>
                        <SelectItem value="technical">Technical Support</SelectItem>
                        <SelectItem value="bug">Bug Report</SelectItem>
                        <SelectItem value="feature">Feature Request</SelectItem>
                        <SelectItem value="business">Business Inquiry</SelectItem>
                        <SelectItem value="other">Other</SelectItem>
                      </SelectContent>
                    </Select>
                  </m.div>

                  <m.div variants={fadeUp}>
                    <Label htmlFor="subject">Subject *</Label>
                    <Input
                      id="subject"
                      type="text"
                      value={formData.subject}
                      onChange={(e) => handleInputChange('subject', e.target.value)}
                      required
                      className="mt-1"
                      placeholder="Brief description of your inquiry"
                    />
                  </m.div>

                  <m.div variants={fadeUp}>
                    <Label htmlFor="message">Message *</Label>
                    <Textarea
                      id="message"
                      value={formData.message}
                      onChange={(e) => handleInputChange('message', e.target.value)}
                      required
                      className="mt-1 min-h-[120px]"
                      placeholder="Please provide details about your inquiry..."
                    />
                  </m.div>

                  <m.div variants={fadeUp}>
                    <Button
                      type="submit"
                      disabled={isSubmitting}
                      className="w-full"
                      size="lg"
                    >
                      {isSubmitting ? (
                        <>
                          <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin mr-2" />
                          Sending...
                        </>
                      ) : (
                        <>
                          <Send className="w-4 h-4 mr-2" />
                          Send Message
                        </>
                      )}
                    </Button>
                  </m.div>
                </m.form>
              )}

              {/* Error Message */}
              {submitError && (
                <m.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="mt-4 p-4 rounded-lg border border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-900/20"
                >
                  <div className="flex items-center gap-2">
                    <AlertCircle className="w-5 h-5 text-red-500" />
                    <p className="text-sm text-red-700 dark:text-red-300">{submitError}</p>
                  </div>
                </m.div>
              )}
            </Card>
          </m.div>
        </div>

        {/* FAQ Section */}
        <m.div
          initial="initial"
          animate="animate"
          variants={stagger}
          className="mt-16 md:mt-20"
        >
          <m.div variants={fadeUp} className="text-center mb-8">
            <h2 className="text-2xl md:text-3xl font-bold mb-4">Frequently Asked Questions</h2>
            <p className="text-muted-foreground">Quick answers to common questions</p>
          </m.div>

          <div className="grid md:grid-cols-2 gap-6">
            <m.div variants={fadeUp}>
              <Card className="p-6">
                <h3 className="font-semibold mb-2">How accurate are the predictions?</h3>
                <p className="text-muted-foreground text-sm">
                  Our AI models achieve high accuracy by analyzing thousands of matches. 
                  Current model confidence is 32% due to backend connectivity issues.
                </p>
              </Card>
            </m.div>

            <m.div variants={fadeUp}>
              <Card className="p-6">
                <h3 className="font-semibold mb-2">Is RiftAI free to use?</h3>
                <p className="text-muted-foreground text-sm">
                  Yes! RiftAI is completely free to use. We're focused on helping 
                  the League of Legends community improve their draft strategies.
                </p>
              </Card>
            </m.div>

            <m.div variants={fadeUp}>
              <Card className="p-6">
                <h3 className="font-semibold mb-2">How often is the data updated?</h3>
                <p className="text-muted-foreground text-sm">
                  Our data is updated regularly with the latest patch information and 
                  meta trends to ensure accurate recommendations.
                </p>
              </Card>
            </m.div>

            <m.div variants={fadeUp}>
              <Card className="p-6">
                <h3 className="font-semibold mb-2">Can I suggest new features?</h3>
                <p className="text-muted-foreground text-sm">
                  Absolutely! We love hearing from our community. Use the contact form 
                  above with category "Feature Request" to share your ideas.
                </p>
              </Card>
            </m.div>
          </div>
        </m.div>
      </div>
    </Container>
  )
}
