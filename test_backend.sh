# Test your Railway backend

# Replace YOUR_RAILWAY_URL with your actual Railway URL
# Example: https://web-production-3554d.up.railway.app

# Test health endpoint
curl https://YOUR_RAILWAY_URL/health

# Test landing endpoint  
curl https://YOUR_RAILWAY_URL/landing/

# Test with API key header
curl -H "X-STRATMANCER-KEY: your-secret-api-key-here" https://YOUR_RAILWAY_URL/health
