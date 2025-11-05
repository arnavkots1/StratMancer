# Environment Variables Security Guide

## Overview

This guide explains how environment variables work in Next.js and what's safe to expose.

## How Next.js Environment Variables Work

### Server-Side Only (Private)
- Variables **without** `NEXT_PUBLIC_` prefix are **server-side only**
- They are **NOT** exposed to the browser
- Safe for: API keys, database passwords, secrets

### Client-Side (Public)
- Variables **with** `NEXT_PUBLIC_` prefix are **exposed to the browser**
- They are bundled into the client-side JavaScript
- Anyone can view them in the browser's source code
- Use only for values that are **meant to be public**

## .env.local File

### Is it safe?
✅ **YES** - `.env.local` is in `.gitignore`, so it:
- Won't be committed to Git
- Won't be pushed to GitHub
- Stays on your local machine

### Location
- ✅ Safe in `frontend/.env.local` (local development)
- ✅ Safe in deployment platform's environment variables (Vercel, Railway, etc.)

## What's Safe to Expose (NEXT_PUBLIC_)

These are **meant to be public** and safe to use with `NEXT_PUBLIC_`:

### ✅ Google Tag Manager ID
```bash
NEXT_PUBLIC_GTM_ID=GTM-XXXXXXX
```
- **Why safe**: GTM ID is public by design - it's visible in the HTML source
- **Purpose**: Loads GTM container on your site

### ✅ Google Analytics Measurement ID
```bash
NEXT_PUBLIC_GA_ID=G-XXXXXXXXXX
```
- **Why safe**: GA ID is public by design - it's visible in the HTML source
- **Purpose**: Tracks page views and events

### ✅ Google Search Console Verification
```bash
NEXT_PUBLIC_GOOGLE_SEARCH_CONSOLE_VERIFICATION=abc123xyz
```
- **Why safe**: Verification code is public - it's in the HTML meta tag
- **Purpose**: Verifies site ownership

### ✅ API Base URL (Public Endpoint)
```bash
NEXT_PUBLIC_API_BASE=https://api.example.com
```
- **Why safe**: Public API endpoint URL
- **Note**: Still protect the API with authentication

## What's NOT Safe to Expose

### ❌ API Keys / Secrets
```bash
# ❌ WRONG - Never use NEXT_PUBLIC_ for secrets!
NEXT_PUBLIC_API_KEY=secret-key-123

# ✅ CORRECT - Server-side only
API_KEY=secret-key-123
```

### ❌ Database Passwords
```bash
# ❌ WRONG
NEXT_PUBLIC_DB_PASSWORD=my-secret-password

# ✅ CORRECT
DB_PASSWORD=my-secret-password
```

### ❌ Private Keys
```bash
# ❌ WRONG
NEXT_PUBLIC_PRIVATE_KEY=abc123...

# ✅ CORRECT
PRIVATE_KEY=abc123...
```

## Best Practices

1. **Never commit `.env.local`** - It's in `.gitignore` for a reason
2. **Use `NEXT_PUBLIC_` only for public values** - Anything with this prefix is visible to users
3. **Use server-side variables for secrets** - No prefix = server-only
4. **Set production variables in your deployment platform** - Vercel, Railway, etc. have secure environment variable settings

## Checking What's Exposed

To see what's exposed to the browser:

1. Build your app: `npm run build`
2. Check `.next/static/chunks/` - Your `NEXT_PUBLIC_` variables will be in the JavaScript bundles
3. Or check the browser's Network tab - Look at the JavaScript files

## Summary for StratMancer

Your current setup is **safe**:
- ✅ `NEXT_PUBLIC_GTM_ID` - Public by design
- ✅ `NEXT_PUBLIC_GA_ID` - Public by design  
- ✅ `NEXT_PUBLIC_GOOGLE_SEARCH_CONSOLE_VERIFICATION` - Public by design
- ✅ `NEXT_PUBLIC_API_BASE` - Public endpoint URL
- ✅ `NEXT_PUBLIC_API_KEY` - Only if this is a public client key (not a secret server key)

If you have a secret server-side API key, it should be:
- ❌ NOT in `.env.local` with `NEXT_PUBLIC_` prefix
- ✅ In server-side code only (backend API routes)

