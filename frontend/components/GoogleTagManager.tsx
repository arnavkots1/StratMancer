/**
 * Google Tag Manager Component
 * Exact code from Google Tag Manager installation page
 * Paste as high in <head> as possible
 */

'use client'

import Script from 'next/script'

interface GoogleTagManagerProps {
  gtmId: string
}

export function GoogleTagManager({ gtmId }: GoogleTagManagerProps) {
  if (!gtmId || gtmId === 'GTM-XXXXXXX') {
    return null
  }

  return (
    <>
      {/* Google Tag Manager */}
      <Script
        id="gtm-head"
        strategy="afterInteractive"
        dangerouslySetInnerHTML={{
          __html: `
            (function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':
            new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],
            j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
            'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
            })(window,document,'script','dataLayer','${gtmId}');
          `,
        }}
      />
      {/* End Google Tag Manager */}
    </>
  )
}

/**
 * Google Tag Manager (noscript)
 * Paste this code immediately after the opening <body> tag
 */
export function GoogleTagManagerNoscript({ gtmId }: { gtmId: string }) {
  if (!gtmId || gtmId === 'GTM-XXXXXXX') {
    return null
  }

  return (
    <>
      {/* Google Tag Manager (noscript) */}
      <noscript>
        <iframe
          src={`https://www.googletagmanager.com/ns.html?id=${gtmId}`}
          height="0"
          width="0"
          style={{ display: 'none', visibility: 'hidden' }}
        />
      </noscript>
      {/* End Google Tag Manager (noscript) */}
    </>
  )
}

declare global {
  interface Window {
    dataLayer: any[]
  }
}

