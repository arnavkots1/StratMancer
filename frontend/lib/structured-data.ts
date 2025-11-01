export function generateStructuredData() {
  const baseUrl = 'https://riftai.com'
  
  const organization = {
    "@context": "https://schema.org",
    "@type": "Organization",
    "name": "RiftAI",
    "url": baseUrl,
    "logo": `${baseUrl}/logo.png`,
    "description": "AI-powered League of Legends draft analysis and win prediction tool",
    "foundingDate": "2024",
    "sameAs": [
      "https://github.com/stratmancer",
      "https://twitter.com/stratmancer",
      "https://discord.gg/stratmancer"
    ],
    "contactPoint": {
      "@type": "ContactPoint",
      "contactType": "customer service",
      "email": "riftai@outlook.com",
      "availableLanguage": "English"
    }
  }

  const webApplication = {
    "@context": "https://schema.org",
    "@type": "WebApplication",
    "name": "RiftAI",
    "url": baseUrl,
    "description": "Elite League of Legends draft analyzer powered by machine learning",
    "applicationCategory": "GameApplication",
    "operatingSystem": "Web Browser",
    "offers": {
      "@type": "Offer",
      "price": "0",
      "priceCurrency": "USD"
    },
    "featureList": [
      "AI-powered draft analysis",
      "Real-time win probability predictions",
      "ELO-specific recommendations",
      "Meta tracking and insights",
      "Champion synergy analysis",
      "Counter-pick suggestions"
    ],
    "screenshot": `${baseUrl}/screenshot.png`,
    "author": {
      "@type": "Organization",
      "name": "RiftAI Team"
    }
  }

  const softwareApplication = {
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    "name": "RiftAI",
    "description": "AI-powered League of Legends draft analysis tool",
    "url": baseUrl,
    "applicationCategory": "GameApplication",
    "operatingSystem": "Web Browser",
    "offers": {
      "@type": "Offer",
      "price": "0",
      "priceCurrency": "USD"
    },
    "aggregateRating": {
      "@type": "AggregateRating",
      "ratingValue": "4.8",
      "ratingCount": "150",
      "bestRating": "5",
      "worstRating": "1"
    },
    "author": {
      "@type": "Organization",
      "name": "RiftAI Team"
    }
  }

  const breadcrumbList = {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    "itemListElement": [
      {
        "@type": "ListItem",
        "position": 1,
        "name": "Home",
        "item": baseUrl
      }
    ]
  }

  const faqPage = {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    "mainEntity": [
      {
        "@type": "Question",
        "name": "How do I use the Draft Analyzer?",
        "acceptedAnswer": {
          "@type": "Answer",
          "text": "The Draft Analyzer helps you make better champion picks during the draft phase. Simply select champions as they're picked or banned, and our AI will provide real-time win probability predictions and recommendations for your next pick."
        }
      },
      {
        "@type": "Question",
        "name": "What ELO levels are supported?",
        "acceptedAnswer": {
          "@type": "Answer",
          "text": "RiftAI supports three ELO tiers: Low (Iron-Gold), Mid (Platinum-Diamond), and High (Master+). Each tier has its own trained model to provide accurate predictions for your skill level."
        }
      },
      {
        "@type": "Question",
        "name": "How accurate are the predictions?",
        "acceptedAnswer": {
          "@type": "Answer",
          "text": "Our models achieve high accuracy rates across all ELO tiers. The exact accuracy varies by tier and meta changes, but we continuously update our models with the latest match data to maintain optimal performance."
        }
      }
    ]
  }

  return {
    organization,
    webApplication,
    softwareApplication,
    breadcrumbList,
    faqPage
  }
}

export function generatePageStructuredData(page: string, _data?: any) {
  const baseUrl = 'https://riftai.com'
  
  switch (page) {
    case 'home':
      return {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": "RiftAI - Elite League of Legends Draft Analyzer",
        "description": "AI-powered draft analysis and win prediction for League of Legends with elite UI and advanced machine learning",
        "url": baseUrl,
        "mainEntity": {
          "@type": "WebApplication",
          "name": "RiftAI",
          "applicationCategory": "GameApplication"
        }
      }
    
    case 'draft':
      return {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": "Draft Analyzer - RiftAI",
        "description": "Real-time League of Legends draft analysis with AI-powered recommendations",
        "url": `${baseUrl}/draft`,
        "mainEntity": {
          "@type": "SoftwareApplication",
          "name": "Draft Analyzer",
          "applicationCategory": "GameApplication"
        }
      }
    
    case 'meta':
      return {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": "Meta Tracker - RiftAI",
        "description": "Current League of Legends patch analysis and champion tier lists",
        "url": `${baseUrl}/meta`,
        "mainEntity": {
          "@type": "Dataset",
          "name": "League of Legends Meta Data",
          "description": "Current meta statistics and champion performance data"
        }
      }
    
    case 'about':
      return {
        "@context": "https://schema.org",
        "@type": "AboutPage",
        "name": "About RiftAI",
        "description": "Learn about RiftAI - The ultimate League of Legends draft analysis platform",
        "url": `${baseUrl}/about`,
        "mainEntity": {
          "@type": "Organization",
          "name": "RiftAI"
        }
      }
    
    default:
      return null
  }
}
