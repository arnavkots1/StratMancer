/* eslint-disable react/no-unescaped-entities */
import type { Metadata } from 'next'
import { Container } from '@/components/Section'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Settings, Shield, BarChart3, Target } from 'lucide-react'

export const metadata: Metadata = {
  title: 'Cookie Policy - StratMancer',
  description: 'Cookie Policy for StratMancer - League of Legends Draft Analysis Tool',
}

export default function CookiePolicyPage() {
  return (
    <Container className="py-16">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold gradient-text mb-4">Cookie Policy</h1>
          <p className="text-muted-foreground text-lg">
            Last updated: {new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}
          </p>
        </div>

        <Card className="p-8 space-y-8">
          <section>
            <h2 className="text-2xl font-semibold mb-4">1. What Are Cookies?</h2>
            <p className="text-muted-foreground leading-relaxed">
              Cookies are small text files that are placed on your computer or mobile device when you visit our website. They help us provide you with a better experience by remembering your preferences and understanding how you use our service.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mb-4">2. How We Use Cookies</h2>
            <p className="text-muted-foreground leading-relaxed mb-6">
              RiftAI uses cookies to enhance your experience, analyze usage patterns, and improve our service. We categorize cookies into the following types:
            </p>

            <div className="grid md:grid-cols-2 gap-6">
              <Card className="p-6">
                <div className="flex items-center mb-4">
                  <Shield className="h-6 w-6 text-green-500 mr-3" />
                  <h3 className="text-xl font-semibold">Essential Cookies</h3>
                </div>
                <p className="text-muted-foreground text-sm leading-relaxed">
                  These cookies are necessary for the website to function properly. They enable basic functions like page navigation, access to secure areas, and remembering your preferences.
                </p>
                <div className="mt-4">
                  <span className="inline-block bg-green-100 text-green-800 text-xs px-2 py-1 rounded-full">
                    Always Active
                  </span>
                </div>
              </Card>

              <Card className="p-6">
                <div className="flex items-center mb-4">
                  <BarChart3 className="h-6 w-6 text-blue-500 mr-3" />
                  <h3 className="text-xl font-semibold">Analytics Cookies</h3>
                </div>
                <p className="text-muted-foreground text-sm leading-relaxed">
                  These cookies help us understand how visitors interact with our website by collecting and reporting information anonymously.
                </p>
                <div className="mt-4">
                  <span className="inline-block bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded-full">
                    Optional
                  </span>
                </div>
              </Card>

              <Card className="p-6">
                <div className="flex items-center mb-4">
                  <Settings className="h-6 w-6 text-purple-500 mr-3" />
                  <h3 className="text-xl font-semibold">Preference Cookies</h3>
                </div>
                <p className="text-muted-foreground text-sm leading-relaxed">
                  These cookies remember your choices and preferences to provide a more personalized experience.
                </p>
                <div className="mt-4">
                  <span className="inline-block bg-purple-100 text-purple-800 text-xs px-2 py-1 rounded-full">
                    Optional
                  </span>
                </div>
              </Card>

              <Card className="p-6">
                <div className="flex items-center mb-4">
                  <Target className="h-6 w-6 text-orange-500 mr-3" />
                  <h3 className="text-xl font-semibold">Marketing Cookies</h3>
                </div>
                <p className="text-muted-foreground text-sm leading-relaxed">
                  These cookies are used to track visitors across websites to display relevant and engaging advertisements.
                </p>
                <div className="mt-4">
                  <span className="inline-block bg-orange-100 text-orange-800 text-xs px-2 py-1 rounded-full">
                    Optional
                  </span>
                </div>
              </Card>
            </div>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mb-4">3. Specific Cookies We Use</h2>
            
            <div className="space-y-6">
              <div className="border-l-4 border-green-500 pl-4">
                <h3 className="text-lg font-semibold mb-2">Essential Cookies</h3>
                <div className="space-y-3">
                  <div className="bg-muted p-3 rounded">
                    <p className="font-medium">stratmancer_session</p>
                    <p className="text-sm text-muted-foreground">Maintains your session state and preferences</p>
                    <p className="text-xs text-muted-foreground">Duration: Session</p>
                  </div>
                  <div className="bg-muted p-3 rounded">
                    <p className="font-medium">cookie_consent</p>
                    <p className="text-sm text-muted-foreground">Remembers your cookie preferences</p>
                    <p className="text-xs text-muted-foreground">Duration: 1 year</p>
                  </div>
                </div>
              </div>

              <div className="border-l-4 border-blue-500 pl-4">
                <h3 className="text-lg font-semibold mb-2">Analytics Cookies</h3>
                <div className="space-y-3">
                  <div className="bg-muted p-3 rounded">
                    <p className="font-medium">_ga, _ga_*</p>
                    <p className="text-sm text-muted-foreground">Google Analytics - tracks website usage</p>
                    <p className="text-xs text-muted-foreground">Duration: 2 years</p>
                  </div>
                  <div className="bg-muted p-3 rounded">
                    <p className="font-medium">_gid</p>
                    <p className="text-sm text-muted-foreground">Google Analytics - distinguishes users</p>
                    <p className="text-xs text-muted-foreground">Duration: 24 hours</p>
                  </div>
                </div>
              </div>

              <div className="border-l-4 border-purple-500 pl-4">
                <h3 className="text-lg font-semibold mb-2">Preference Cookies</h3>
                <div className="space-y-3">
                  <div className="bg-muted p-3 rounded">
                    <p className="font-medium">theme_preference</p>
                    <p className="text-sm text-muted-foreground">Remembers your theme choice (dark/light)</p>
                    <p className="text-xs text-muted-foreground">Duration: 1 year</p>
                  </div>
                  <div className="bg-muted p-3 rounded">
                    <p className="font-medium">elo_preference</p>
                    <p className="text-sm text-muted-foreground">Remembers your ELO selection</p>
                    <p className="text-xs text-muted-foreground">Duration: 30 days</p>
                  </div>
                </div>
              </div>
            </div>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mb-4">4. Managing Your Cookie Preferences</h2>
            <p className="text-muted-foreground leading-relaxed mb-6">
              You have control over which cookies you accept. You can manage your preferences at any time using the cookie settings below or through your browser settings.
            </p>
            
            <div className="bg-muted p-6 rounded-lg">
              <h3 className="text-lg font-semibold mb-4">Cookie Settings</h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">Essential Cookies</p>
                    <p className="text-sm text-muted-foreground">Required for basic website functionality</p>
                  </div>
                  <span className="text-sm text-green-600 font-medium">Always Active</span>
                </div>
                
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">Analytics Cookies</p>
                    <p className="text-sm text-muted-foreground">Help us improve our service</p>
                  </div>
                  <Button variant="outline" size="sm">
                    Manage
                  </Button>
                </div>
                
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">Preference Cookies</p>
                    <p className="text-sm text-muted-foreground">Remember your settings</p>
                  </div>
                  <Button variant="outline" size="sm">
                    Manage
                  </Button>
                </div>
                
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">Marketing Cookies</p>
                    <p className="text-sm text-muted-foreground">Show relevant advertisements</p>
                  </div>
                  <Button variant="outline" size="sm">
                    Manage
                  </Button>
                </div>
              </div>
            </div>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mb-4">5. Browser Settings</h2>
            <p className="text-muted-foreground leading-relaxed mb-4">
              You can also control cookies through your browser settings. Here's how to manage cookies in popular browsers:
            </p>
            <ul className="list-disc list-inside text-muted-foreground space-y-2">
              <li><strong>Chrome:</strong> Settings → Privacy and security → Cookies and other site data</li>
              <li><strong>Firefox:</strong> Options → Privacy & Security → Cookies and Site Data</li>
              <li><strong>Safari:</strong> Preferences → Privacy → Manage Website Data</li>
              <li><strong>Edge:</strong> Settings → Cookies and site permissions → Cookies and site data</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mb-4">6. Third-Party Cookies</h2>
            <p className="text-muted-foreground leading-relaxed">
              Some cookies on our site are set by third-party services. We use Google Analytics to understand how our website is used. You can opt out of Google Analytics by installing the Google Analytics Opt-out Browser Add-on.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mb-4">7. Updates to This Policy</h2>
            <p className="text-muted-foreground leading-relaxed">
              We may update this Cookie Policy from time to time to reflect changes in our practices or for other operational, legal, or regulatory reasons. Please revisit this Cookie Policy regularly to stay informed about our use of cookies.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mb-4">8. Contact Us</h2>
            <p className="text-muted-foreground leading-relaxed">
              If you have any questions about our use of cookies, please contact us at:
            </p>
            <div className="mt-4 p-4 bg-muted rounded-lg">
              <p className="text-muted-foreground">
                <strong>Email:</strong> <a href="mailto:riftai@outlook.com" className="text-primary hover:underline">riftai@outlook.com</a><br />
                <strong>Cookie Questions:</strong> <a href="mailto:riftai@outlook.com" className="text-primary hover:underline">riftai@outlook.com</a>
              </p>
            </div>
          </section>
        </Card>
      </div>
    </Container>
  )
}
