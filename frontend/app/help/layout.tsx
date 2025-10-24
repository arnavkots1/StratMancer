import type { Metadata } from 'next'
import type { ReactNode } from 'react'

export const metadata: Metadata = {
  title: 'Help Center - RiftAI',
  description: 'Get help with RiftAI - FAQ, guides, and support resources',
}

export default function HelpLayout({
  children,
}: {
  children: ReactNode
}) {
  return children
}
