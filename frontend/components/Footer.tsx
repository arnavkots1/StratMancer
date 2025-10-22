"use client"

import * as React from "react"
import Link from "next/link"
import { Mail, Zap, Heart } from "lucide-react"
import { cn } from "@/lib/cn"
import { Glow } from "@/components/Glow"

interface FooterProps {
  className?: string
}

const footerLinks = {
  product: [
    { name: 'Draft Analyzer', href: '/draft' },
    { name: 'Meta Tracker', href: '/meta' },
  ],
  company: [
    { name: 'About', href: '/about' },
  ],
  support: [
    { name: 'Help Center', href: '/help' },
  ],
  legal: [
    { name: 'Privacy', href: '/privacy' },
    { name: 'Terms', href: '/terms' },
    { name: 'Cookies', href: '/cookies' },
  ],
}

const socialLinks = [
  { name: 'Email', href: 'mailto:contact@stratmancer.com', icon: Mail },
]

export function Footer({ className }: FooterProps) {
  return (
    <footer className={cn("border-t border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60", className)}>
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        {/* Main Footer Content */}
        <div className="py-12 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-8">
          {/* Brand Section */}
          <div className="lg:col-span-2">
            <div className="flex items-center space-x-2 mb-4">
              <Glow variant="premium" className="rounded-xl p-2">
                <Zap className="h-6 w-6 text-primary" />
              </Glow>
              <span className="text-xl font-bold gradient-text">StratMancer</span>
            </div>
            <p className="text-muted-foreground mb-6 max-w-md">
              The ultimate League of Legends draft analysis platform powered by machine learning. 
              Make smarter picks, understand the meta, and climb the ranks.
            </p>
            <div className="flex space-x-4">
              {socialLinks.map((social) => {
                const Icon = social.icon
                return (
                  <Link
                    key={social.name}
                    href={social.href}
                    className="p-2 rounded-lg bg-muted hover:bg-accent transition-colors duration-200 group"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    <Icon className="h-4 w-4 text-muted-foreground group-hover:text-foreground transition-colors duration-200" />
                    <span className="sr-only">{social.name}</span>
                  </Link>
                )
              })}
            </div>
          </div>

          {/* Product Links */}
          <div>
            <h3 className="font-semibold mb-4">Product</h3>
            <ul className="space-y-3">
              {footerLinks.product.map((link) => (
                <li key={link.name}>
                  <Link
                    href={link.href}
                    className="text-muted-foreground hover:text-foreground transition-colors duration-200"
                  >
                    {link.name}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Company Links */}
          <div>
            <h3 className="font-semibold mb-4">Company</h3>
            <ul className="space-y-3">
              {footerLinks.company.map((link) => (
                <li key={link.name}>
                  <Link
                    href={link.href}
                    className="text-muted-foreground hover:text-foreground transition-colors duration-200"
                  >
                    {link.name}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Support Links */}
          <div>
            <h3 className="font-semibold mb-4">Support</h3>
            <ul className="space-y-3">
              {footerLinks.support.map((link) => (
                <li key={link.name}>
                  <Link
                    href={link.href}
                    className="text-muted-foreground hover:text-foreground transition-colors duration-200"
                  >
                    {link.name}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Legal Links */}
          <div>
            <h3 className="font-semibold mb-4">Legal</h3>
            <ul className="space-y-3">
              {footerLinks.legal.map((link) => (
                <li key={link.name}>
                  <Link
                    href={link.href}
                    className="text-muted-foreground hover:text-foreground transition-colors duration-200"
                  >
                    {link.name}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="py-6 border-t border-border/40">
          <div className="flex flex-col md:flex-row items-center justify-between space-y-4 md:space-y-0">
            <div className="flex items-center space-x-2 text-sm text-muted-foreground">
              <span>© 2025 StratMancer. Made with</span>
              <Heart className="h-4 w-4 text-red-500 fill-current" />
              <span>for League of Legends players.</span>
            </div>
            <div className="flex items-center space-x-6 text-sm text-muted-foreground">
              <span>Powered by Machine Learning</span>
              <span>•</span>
              <span>Built with Next.js & FastAPI</span>
            </div>
          </div>
        </div>
      </div>
    </footer>
  )
}
