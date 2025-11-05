/**
 * Google Search Console Verification
 * Add your verification meta tag here
 */

import { Metadata } from 'next'

export function getSearchConsoleMetadata(): Metadata {
  const verificationCode = process.env.NEXT_PUBLIC_GOOGLE_SEARCH_CONSOLE_VERIFICATION

  if (!verificationCode) {
    return {}
  }

  return {
    verification: {
      google: verificationCode,
    },
  }
}

