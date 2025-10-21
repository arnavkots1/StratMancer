import { Hero } from '@/components/Hero'
import { ProductMarquee } from '@/components/ProductMarquee'
import { FeatureRows } from '@/components/FeatureRows'
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

