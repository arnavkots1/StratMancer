/* eslint-disable react/no-unescaped-entities */
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Home, Search } from 'lucide-react'

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-[#060911] p-4">
      <Card className="max-w-md w-full p-8 text-center">
        <div className="flex justify-center mb-6">
          <div className="w-16 h-16 rounded-full bg-primary/10 border border-primary/20 flex items-center justify-center">
            <Search className="w-8 h-8 text-primary" />
          </div>
        </div>
        
        <h1 className="text-4xl font-bold text-foreground mb-4">
          404
        </h1>
        
        <h2 className="text-xl font-semibold text-foreground mb-4">
          Page Not Found
        </h2>
        
        <p className="text-muted-foreground mb-6">
          The page you're looking for doesn't exist or has been moved.
        </p>

        <div className="flex flex-col sm:flex-row gap-3">
          <Button asChild className="flex-1">
            <Link href="/">
              <Home className="w-4 h-4 mr-2" />
              Go Home
            </Link>
          </Button>
          <Button asChild variant="outline" className="flex-1">
            <Link href="/draft">
              <Search className="w-4 h-4 mr-2" />
              Draft Analyzer
            </Link>
          </Button>
        </div>
      </Card>
    </div>
  )
}
