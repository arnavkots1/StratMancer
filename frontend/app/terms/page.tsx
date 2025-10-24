/* eslint-disable react/no-unescaped-entities */
import type { Metadata } from 'next'
import { Container } from '@/components/Section'
import { Card } from '@/components/ui/card'

export const metadata: Metadata = {
  title: 'Terms of Service - StratMancer',
  description: 'Terms of Service for StratMancer - League of Legends Draft Analysis Tool',
}

export default function TermsPage() {
  return (
    <Container className="py-16">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold gradient-text mb-4">Terms of Service</h1>
          <p className="text-muted-foreground text-lg">
            Last updated: {new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}
          </p>
        </div>

        <Card className="p-8 space-y-8">
          <section>
            <h2 className="text-2xl font-semibold mb-4">1. Acceptance of Terms</h2>
            <p className="text-muted-foreground leading-relaxed">
              By accessing and using StratMancer ("the Service"), you accept and agree to be bound by the terms and provision of this agreement. If you do not agree to abide by the above, please do not use this service.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mb-4">2. Description of Service</h2>
            <p className="text-muted-foreground leading-relaxed">
              StratMancer is a League of Legends draft analysis tool that provides AI-powered predictions and recommendations for champion selections. The service analyzes draft compositions and provides win probability estimates based on machine learning models.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mb-4">3. User Responsibilities</h2>
            <h3 className="text-xl font-medium mb-3">3.1 Acceptable Use</h3>
            <p className="text-muted-foreground leading-relaxed mb-4">You agree to use the Service only for lawful purposes and in accordance with these Terms. You agree not to:</p>
            <ul className="list-disc list-inside text-muted-foreground space-y-2 mb-6">
              <li>Use the Service for any illegal or unauthorized purpose</li>
              <li>Attempt to gain unauthorized access to any part of the Service</li>
              <li>Interfere with or disrupt the Service or servers</li>
              <li>Use automated systems to access the Service without permission</li>
              <li>Reverse engineer, decompile, or disassemble the Service</li>
            </ul>

            <h3 className="text-xl font-medium mb-3">3.2 API Usage</h3>
            <p className="text-muted-foreground leading-relaxed">
              If you use our API, you must comply with our rate limits and usage guidelines. Excessive or abusive usage may result in temporary or permanent suspension of access.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mb-4">4. Intellectual Property</h2>
            <p className="text-muted-foreground leading-relaxed mb-4">
              The Service and its original content, features, and functionality are and will remain the exclusive property of StratMancer and its licensors. The Service is protected by copyright, trademark, and other laws.
            </p>
            <p className="text-muted-foreground leading-relaxed">
              League of Legends and all related content are trademarks of Riot Games, Inc. We are not affiliated with or endorsed by Riot Games.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mb-4">5. Disclaimers and Limitations</h2>
            <h3 className="text-xl font-medium mb-3">5.1 Service Availability</h3>
            <p className="text-muted-foreground leading-relaxed mb-4">
              We strive to maintain high service availability but do not guarantee uninterrupted access. The Service may be temporarily unavailable due to maintenance, updates, or technical issues.
            </p>

            <h3 className="text-xl font-medium mb-3">5.2 Accuracy of Predictions</h3>
            <p className="text-muted-foreground leading-relaxed mb-4">
              Our draft analysis and win probability predictions are based on machine learning models and historical data. While we strive for accuracy, predictions are not guaranteed and should not be the sole basis for competitive decisions.
            </p>

            <h3 className="text-xl font-medium mb-3">5.3 Limitation of Liability</h3>
            <p className="text-muted-foreground leading-relaxed">
              To the maximum extent permitted by law, StratMancer shall not be liable for any indirect, incidental, special, consequential, or punitive damages, including without limitation, loss of profits, data, use, goodwill, or other intangible losses.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mb-4">6. Privacy and Data Protection</h2>
            <p className="text-muted-foreground leading-relaxed">
              Your privacy is important to us. Please review our <a href="/privacy" className="text-primary hover:underline">Privacy Policy</a>, which also governs your use of the Service, to understand our practices.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mb-4">7. Prohibited Uses</h2>
            <p className="text-muted-foreground leading-relaxed mb-4">You may not use our Service:</p>
            <ul className="list-disc list-inside text-muted-foreground space-y-2">
              <li>For any unlawful purpose or to solicit others to perform unlawful acts</li>
              <li>To violate any international, federal, provincial, or state regulations, rules, laws, or local ordinances</li>
              <li>To infringe upon or violate our intellectual property rights or the intellectual property rights of others</li>
              <li>To harass, abuse, insult, harm, defame, slander, disparage, intimidate, or discriminate</li>
              <li>To submit false or misleading information</li>
              <li>To upload or transmit viruses or any other type of malicious code</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mb-4">8. Termination</h2>
            <p className="text-muted-foreground leading-relaxed">
              We may terminate or suspend your access immediately, without prior notice or liability, for any reason whatsoever, including without limitation if you breach the Terms. Upon termination, your right to use the Service will cease immediately.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mb-4">9. Changes to Terms</h2>
            <p className="text-muted-foreground leading-relaxed">
              We reserve the right, at our sole discretion, to modify or replace these Terms at any time. If a revision is material, we will try to provide at least 30 days notice prior to any new terms taking effect.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mb-4">10. Governing Law</h2>
            <p className="text-muted-foreground leading-relaxed">
              These Terms shall be interpreted and governed by the laws of the jurisdiction in which StratMancer operates, without regard to its conflict of law provisions.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mb-4">11. Severability</h2>
            <p className="text-muted-foreground leading-relaxed">
              If any provision of these Terms is held to be invalid or unenforceable by a court, the remaining provisions of these Terms will remain in effect.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mb-4">12. Contact Information</h2>
            <p className="text-muted-foreground leading-relaxed">
              If you have any questions about these Terms of Service, please contact us at:
            </p>
            <div className="mt-4 p-4 bg-muted rounded-lg">
              <p className="text-muted-foreground">
                <strong>Email:</strong> <a href="mailto:riftai@outlook.com" className="text-primary hover:underline">riftai@outlook.com</a><br />
                <strong>General Inquiries:</strong> <a href="mailto:riftai@outlook.com" className="text-primary hover:underline">riftai@outlook.com</a>
              </p>
            </div>
          </section>
        </Card>
      </div>
    </Container>
  )
}
