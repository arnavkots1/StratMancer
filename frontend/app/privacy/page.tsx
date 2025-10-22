/* eslint-disable react/no-unescaped-entities */
import type { Metadata } from 'next'
import { Container } from '@/components/Section'
import { Card } from '@/components/ui/card'

export const metadata: Metadata = {
  title: 'Privacy Policy - StratMancer',
  description: 'Privacy Policy for StratMancer - League of Legends Draft Analysis Tool',
}

export default function PrivacyPage() {
  return (
    <Container className="py-16">
      <div className="max-w-4xl mx-auto">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold gradient-text mb-4">Privacy Policy</h1>
          <p className="text-muted-foreground text-lg">
            Last updated: {new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}
          </p>
        </div>

        <Card className="p-8 space-y-8">
          <section>
            <h2 className="text-2xl font-semibold mb-4">1. Introduction</h2>
            <p className="text-muted-foreground leading-relaxed">
              StratMancer (&quot;we,&quot; &quot;our,&quot; or &quot;us&quot;) is committed to protecting your privacy. This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you use our League of Legends draft analysis service.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mb-4">2. Information We Collect</h2>
            
            <h3 className="text-xl font-medium mb-3">2.1 Information You Provide</h3>
            <ul className="list-disc list-inside text-muted-foreground space-y-2 mb-6">
              <li>Draft compositions and champion selections</li>
              <li>ELO preferences (Low, Mid, High)</li>
              <li>API usage data for service optimization</li>
            </ul>

            <h3 className="text-xl font-medium mb-3">2.2 Automatically Collected Information</h3>
            <ul className="list-disc list-inside text-muted-foreground space-y-2">
              <li>IP address and browser information</li>
              <li>Usage patterns and feature interactions</li>
              <li>Error logs and performance metrics</li>
              <li>Cookies and similar tracking technologies</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mb-4">3. How We Use Your Information</h2>
            <ul className="list-disc list-inside text-muted-foreground space-y-2">
              <li>Provide draft analysis and win probability predictions</li>
              <li>Improve our machine learning models and algorithms</li>
              <li>Monitor service performance and troubleshoot issues</li>
              <li>Ensure security and prevent abuse</li>
              <li>Comply with legal obligations</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mb-4">4. Data Sharing and Disclosure</h2>
            <p className="text-muted-foreground leading-relaxed mb-4">
              We do not sell, trade, or rent your personal information to third parties. We may share information only in the following circumstances:
            </p>
            <ul className="list-disc list-inside text-muted-foreground space-y-2">
              <li>With your explicit consent</li>
              <li>To comply with legal requirements</li>
              <li>To protect our rights and prevent fraud</li>
              <li>With service providers who assist in our operations (under strict confidentiality agreements)</li>
            </ul>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mb-4">5. Data Security</h2>
            <p className="text-muted-foreground leading-relaxed">
              We implement appropriate technical and organizational measures to protect your information against unauthorized access, alteration, disclosure, or destruction. This includes encryption, secure servers, and regular security audits.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mb-4">6. Your Rights (GDPR Compliance)</h2>
            <p className="text-muted-foreground leading-relaxed mb-4">
              If you are in the European Economic Area (EEA), you have the following rights:
            </p>
            <ul className="list-disc list-inside text-muted-foreground space-y-2">
              <li><strong>Right to Access:</strong> Request copies of your personal data</li>
              <li><strong>Right to Rectification:</strong> Request correction of inaccurate data</li>
              <li><strong>Right to Erasure:</strong> Request deletion of your personal data</li>
              <li><strong>Right to Restrict Processing:</strong> Request limitation of data processing</li>
              <li><strong>Right to Data Portability:</strong> Request transfer of your data</li>
              <li><strong>Right to Object:</strong> Object to processing of your personal data</li>
            </ul>
            <p className="text-muted-foreground leading-relaxed mt-4">
              To exercise these rights, please contact us at <a href="mailto:privacy@stratmancer.com" className="text-primary hover:underline">privacy@stratmancer.com</a>
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mb-4">7. Cookies and Tracking</h2>
            <p className="text-muted-foreground leading-relaxed mb-4">
              We use cookies and similar technologies to enhance your experience. You can control cookie preferences through our cookie settings. For detailed information, see our <a href="/cookies" className="text-primary hover:underline">Cookie Policy</a>.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mb-4">8. Data Retention</h2>
            <p className="text-muted-foreground leading-relaxed">
              We retain your information only as long as necessary to provide our services and comply with legal obligations. Draft analysis data is typically retained for 30 days for service improvement purposes.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mb-4">9. International Data Transfers</h2>
            <p className="text-muted-foreground leading-relaxed">
              Your information may be transferred to and processed in countries other than your own. We ensure appropriate safeguards are in place to protect your data in accordance with applicable privacy laws.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mb-4">10. Children's Privacy</h2>
            <p className="text-muted-foreground leading-relaxed">
              Our service is not intended for children under 13. We do not knowingly collect personal information from children under 13. If you believe we have collected such information, please contact us immediately.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mb-4">11. Changes to This Policy</h2>
            <p className="text-muted-foreground leading-relaxed">
              We may update this Privacy Policy from time to time. We will notify you of any changes by posting the new Privacy Policy on this page and updating the "Last updated" date.
            </p>
          </section>

          <section>
            <h2 className="text-2xl font-semibold mb-4">12. Contact Us</h2>
            <p className="text-muted-foreground leading-relaxed">
              If you have any questions about this Privacy Policy, please contact us at:
            </p>
            <div className="mt-4 p-4 bg-muted rounded-lg">
              <p className="text-muted-foreground">
                <strong>Email:</strong> <a href="mailto:privacy@stratmancer.com" className="text-primary hover:underline">privacy@stratmancer.com</a><br />
                <strong>Data Protection Officer:</strong> <a href="mailto:dpo@stratmancer.com" className="text-primary hover:underline">dpo@stratmancer.com</a>
              </p>
            </div>
          </section>
        </Card>
      </div>
    </Container>
  )
}
