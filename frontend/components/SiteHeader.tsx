"use client"

import * as React from "react"
import Link from "next/link"
import { Menu, X, Zap, BarChart3, Users, Settings, Mail } from "lucide-react"
import { cn } from '../lib/cn'
import { Button } from "@/components/ui/button"
import { Glow } from "@/components/Glow"

interface SiteHeaderProps {
  className?: string
}

const navigation = [
  { name: 'Draft Analyzer', href: '/draft', icon: BarChart3 },
  { name: 'Meta Tracker', href: '/meta', icon: Users },
  { name: 'Contact', href: '/contact', icon: Mail },
  { name: 'Settings', href: '/settings', icon: Settings },
]

export function SiteHeader({ className }: SiteHeaderProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false)

  return (
    <header className={cn("sticky top-0 z-50 w-full border-b border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60", className)}>
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          {/* Logo */}
          <div className="flex items-center space-x-2">
            <Link href="/" className="flex items-center space-x-2">
              <Glow variant="premium" className="rounded-xl p-2">
                <Zap className="h-6 w-6 text-primary" />
              </Glow>
              <span className="text-xl font-bold gradient-text">RiftAI</span>
            </Link>
          </div>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center space-x-1">
            {navigation.map((item) => {
              const Icon = item.icon
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className="nav-link group relative"
                >
                  <Icon className="h-4 w-4 transition-transform duration-200 group-hover:scale-110" />
                  <span>{item.name}</span>
                  <div className="absolute inset-x-0 -bottom-1 h-0.5 bg-gradient-to-r from-primary to-secondary scale-x-0 transition-transform duration-200 group-hover:scale-x-100" />
                </Link>
              )
            })}
          </nav>

          {/* Mobile Menu */}
          <div className="flex items-center space-x-2">
            {/* Mobile Menu Button */}
            <Button
              variant="ghost"
              size="icon"
              className="md:hidden"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            >
              {mobileMenuOpen ? (
                <X className="h-4 w-4" />
              ) : (
                <Menu className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>

        {/* Mobile Navigation */}
        {mobileMenuOpen && (
          <div className="md:hidden">
            <div className="px-2 pt-2 pb-3 space-y-1 border-t border-border/40">
              {navigation.map((item) => {
                const Icon = item.icon
                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    className="nav-link group flex items-center space-x-2"
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    <Icon className="h-4 w-4" />
                    <span>{item.name}</span>
                  </Link>
                )
              })}
            </div>
          </div>
        )}
      </div>
    </header>
  )
}
