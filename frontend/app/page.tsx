import dynamic from 'next/dynamic'

// Lazy load components for better performance
const Hero = dynamic(() => import('@/components/Hero').then(mod => ({ default: mod.Hero })), {
  loading: () => <div className="min-h-screen flex items-center justify-center"><div className="h-12 w-12 animate-spin rounded-full border-4 border-primary border-t-transparent" /></div>,
  ssr: false
})

const ProductMarquee = dynamic(() => import('@/components/ProductMarquee').then(mod => ({ default: mod.ProductMarquee })), {
  loading: () => <div className="h-32 flex items-center justify-center"><div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" /></div>,
  ssr: false
})

const FeatureRows = dynamic(() => import('@/components/FeatureRows').then(mod => ({ default: mod.FeatureRows })), {
  loading: () => <div className="h-64 flex items-center justify-center"><div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" /></div>,
  ssr: false
})

// import { Pricing } from '@/components/Pricing'

export default function HomePage() {
  return (
    <div className="relative">
      <Hero />
      <ProductMarquee />
      <FeatureRows />
      {/* <Pricing /> */}
    </div>
  )
}

