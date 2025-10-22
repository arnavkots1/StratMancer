import type { Metadata } from 'next'
import type { ReactNode } from 'react'

export const metadata: Metadata = {
  title: 'Help Center - StratMancer',
  description: 'Get help with StratMancer - FAQ, guides, and support resources',
}

export default function HelpLayout({
  children,
}: {
  children: ReactNode
}) {
  return children
}
