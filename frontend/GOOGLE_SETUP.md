# Google Analytics, Tag Manager & Search Console Setup Guide

This guide will help you set up Google Tag Manager (GTM), Google Analytics (GA4), and Google Search Console for your StratMancer website.

## Prerequisites

- A Google account
- Access to your website's domain

## Step 1: Set Up Google Tag Manager

### 1.1 Create a GTM Account

1. Go to [Google Tag Manager](https://tagmanager.google.com/)
2. Click **Create Account**
3. Fill in:
   - **Account Name**: `StratMancer` (or your preferred name)
   - **Country**: Select your country
   - **Container Name**: Your website domain (e.g., `stratmancer.com`)
   - **Target Platform**: Select **Web**
4. Click **Create**
5. **Accept the Terms of Service**

### 1.2 Get Your GTM ID

After creating the container, you'll see your GTM ID in the format: `GTM-XXXXXXX`

Copy this ID - you'll need it for the next step.

## Step 2: Set Up Google Analytics 4 (GA4) via GTM

### 2.1 Create a GA4 Property

1. Go to [Google Analytics](https://analytics.google.com/)
2. Click **Admin** (gear icon) → **Create Property**
3. Fill in:
   - **Property Name**: `StratMancer` (or your preferred name)
   - **Reporting Time Zone**: Select your timezone
   - **Currency**: Select your currency
4. Click **Next** and configure your business details
5. Click **Create**

### 2.2 Get Your GA4 Measurement ID

1. In Google Analytics, go to **Admin** → **Data Streams**
2. Click on your web stream
3. Copy your **Measurement ID** (format: `G-XXXXXXXXXX`)

### 2.3 Add GA4 to Google Tag Manager

1. Go back to [Google Tag Manager](https://tagmanager.google.com/)
2. Click on your container
3. Click **Add a new tag** → **Tag Configuration** → **Google Analytics: GA4 Configuration**
4. Enter your **Measurement ID** (from step 2.2, format: `G-XXXXXXXXXX`)
5. Click **Triggering** → Select **All Pages**
6. Click **Save**
7. Name the tag: `GA4 - Configuration`
8. Click **Submit** → **Publish** to activate

**Note:** You do NOT need to set an "Event Name" for the basic GA4 Configuration tag. Event names are only for custom event tracking (like button clicks, form submissions, etc.). The basic GA4 Configuration tag automatically tracks page views.

## Step 3: Set Up Google Search Console

### 3.1 Add Property to Search Console

1. Go to [Google Search Console](https://search.google.com/search-console)
2. Click **Add Property**
3. Select **URL prefix** (recommended) or **Domain**
   - **URL prefix**: `https://stratmancer.com` (or your domain)
   - **Domain**: `stratmancer.com` (if you want to verify the entire domain)
4. Click **Continue**

### 3.2 Verify Ownership

You have several verification options:

#### Option A: HTML Meta Tag (Recommended - Already Set Up)

1. Select **HTML tag** method
2. Copy the **content** value from the meta tag (e.g., `abc123xyz...`)
3. Add it to your `.env.local` file:
   ```bash
   NEXT_PUBLIC_GOOGLE_SEARCH_CONSOLE_VERIFICATION=abc123xyz...
   ```
4. Redeploy your site
5. Click **Verify** in Search Console

#### Option B: HTML File Upload

1. Download the HTML verification file
2. Upload it to your `public/` folder
3. Access it at `https://yourdomain.com/google1234567890.html`
4. Click **Verify** in Search Console

#### Option C: DNS Record

1. Add the provided TXT record to your domain's DNS settings
2. Wait for DNS propagation (can take up to 48 hours)
3. Click **Verify** in Search Console

## Step 4: Configure Environment Variables

Add the following to your `frontend/.env.local` file:

```bash
# Google Tag Manager ID (format: GTM-XXXXXXX)
NEXT_PUBLIC_GTM_ID=GTM-XXXXXXX

# Google Analytics 4 Measurement ID (optional - only if NOT using GTM)
# If you configure GA4 through GTM (recommended), you don't need this
NEXT_PUBLIC_GA_ID=G-XXXXXXXXXX

# Google Search Console Verification Code
NEXT_PUBLIC_GOOGLE_SEARCH_CONSOLE_VERIFICATION=your-verification-code-here
```

**Important**: 
- Replace `GTM-XXXXXXX` with your actual GTM ID (this is REQUIRED)
- Replace `G-XXXXXXXXXX` with your actual GA4 Measurement ID (OPTIONAL - only if you're NOT using GTM to manage GA4)
- Replace `your-verification-code-here` with your Search Console verification code

### About .env.local and Security

**Is `.env.local` safe in the frontend?**
- ✅ **YES** - `.env.local` is in `.gitignore`, so it won't be committed to Git
- ✅ **YES** - It's safe to have in your frontend folder

**Are `NEXT_PUBLIC_*` variables public?**
- ⚠️ **YES** - Any variable starting with `NEXT_PUBLIC_` is **exposed to the browser**
- This is **INTENTIONAL** and **CORRECT** for GTM ID and GA ID
- These IDs are **meant to be public** - they're not secrets
- **Never use `NEXT_PUBLIC_` for API keys, passwords, or secrets**

**For GTM/GA Setup:**
- GTM ID (`GTM-XXXXXXX`) - ✅ Safe to expose, meant to be public
- GA Measurement ID (`G-XXXXXXXXXX`) - ✅ Safe to expose, meant to be public
- Search Console verification code - ✅ Safe to expose, meant to be public

## Step 5: Test Your Setup

### 5.1 Test GTM

1. Install [Google Tag Assistant](https://chrome.google.com/webstore/detail/tag-assistant-legacy-by-g/kejbdjndbnbjgmefkgdddjlbokphdefk) Chrome extension
2. Visit your website
3. Click the extension icon
4. You should see:
   - ✅ Google Tag Manager loaded
   - ✅ GA4 Configuration tag fired

### 5.2 Test Google Analytics

1. Go to Google Analytics → **Reports** → **Realtime**
2. Visit your website
3. You should see your visit appear in realtime within 30 seconds

### 5.3 Test Search Console

1. Go to Google Search Console
2. Click **URL Inspection**
3. Enter your homepage URL
4. Click **Test Live URL**
5. You should see "URL is on Google" or indexing status

## Step 6: Additional GTM Tags (Optional)

You can add more tags in GTM without code changes:

### Enhanced Ecommerce Tracking
- Go to GTM → **Tags** → **New**
- Select **Google Analytics: GA4 Event**
- Configure for draft completion events

### Custom Events
- Track button clicks, form submissions, etc.
- Use GTM's **Triggers** to fire events

### Conversion Tracking
- Set up goals in GA4
- Create conversion events in GTM

## Troubleshooting

### GTM Not Loading
- Check that `NEXT_PUBLIC_GTM_ID` is set correctly
- Verify the GTM ID format is `GTM-XXXXXXX`
- Check browser console for errors
- Ensure ad blockers aren't blocking GTM

### GA4 Not Tracking
- Verify GA4 tag is configured in GTM
- Check GTM preview mode to see if tags fire
- Ensure GA4 Measurement ID is correct
- Check GA4 DebugView for real-time events

### Search Console Not Verifying
- Double-check the verification code in `.env.local`
- Ensure the site is deployed with the new code
- Try a different verification method if meta tag fails
- Clear browser cache and try again

## Next Steps

1. **Submit Sitemap**: In Search Console, go to **Sitemaps** and submit your sitemap URL
2. **Set Up GA4 Goals**: Configure conversion events in Google Analytics
3. **Enable Enhanced Measurement**: In GA4, enable scroll tracking, outbound clicks, etc.
4. **Set Up Custom Reports**: Create reports for draft analysis, user engagement, etc.

## Support Resources

- [Google Tag Manager Help](https://support.google.com/tagmanager)
- [Google Analytics Help](https://support.google.com/analytics)
- [Google Search Console Help](https://support.google.com/webmasters)

