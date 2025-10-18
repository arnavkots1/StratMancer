# StratMancer Frontend - Quick Setup Guide

## Prerequisites

- Node.js 18+ ([Download](https://nodejs.org/))
- npm 9+ (comes with Node.js)
- Backend API running (see backend README)

## Quick Start

### 1. Install Dependencies

```bash
cd frontend
npm install
```

This will install:
- Next.js 14
- React 18
- Tailwind CSS
- TypeScript
- Lucide Icons

### 2. Configure Environment

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_API_KEY=your-api-key-here
```

> **Note:** The API key should match the key configured in your backend `.env`

### 3. Start Development Server

```bash
npm run dev
```

The application will start on [http://localhost:3000](http://localhost:3000)

### 4. Verify Setup

1. Open [http://localhost:3000](http://localhost:3000)
2. Click "Launch Draft Analyzer"
3. Select some champions
4. Click "Predict Draft"
5. Verify prediction results display

## Testing Backend Connection

Check if the backend is accessible:

```bash
# From the frontend directory
curl http://localhost:8000/healthz
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

## Common Commands

```bash
# Development
npm run dev          # Start dev server

# Production
npm run build        # Build for production
npm start            # Start production server

# Maintenance
npm run lint         # Run ESLint
npm run type-check   # Run TypeScript checks
```

## Project Structure

```
frontend/
├── app/                  # Next.js pages
│   ├── draft/           # Draft analyzer page
│   ├── layout.tsx       # Root layout
│   ├── page.tsx         # Home page
│   └── globals.css      # Global styles
├── components/          # React components
│   ├── ChampionPicker.tsx
│   ├── RoleSlots.tsx
│   └── PredictionCard.tsx
├── lib/                 # Utilities
│   └── api.ts          # API client
├── types/              # TypeScript types
└── public/             # Static files
```

## Troubleshooting

### Port Already in Use

If port 3000 is already in use:

```bash
# Use a different port
PORT=3001 npm run dev
```

### API Connection Failed

1. Verify backend is running:
   ```bash
   curl http://localhost:8000/healthz
   ```

2. Check CORS settings in backend
3. Verify `NEXT_PUBLIC_API_URL` in `.env`

### Build Errors

Clear cache and reinstall:

```bash
rm -rf .next node_modules
npm install
npm run dev
```

### Champions Not Loading

Ensure backend has the feature map endpoint:

```bash
curl http://localhost:8000/models/feature-map
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | Yes | `http://localhost:8000` | Backend API URL |
| `NEXT_PUBLIC_API_KEY` | No | - | API authentication key |

> **Important:** Variables prefixed with `NEXT_PUBLIC_` are exposed to the browser

## Next Steps

1. ✅ Install dependencies
2. ✅ Configure environment
3. ✅ Start development server
4. 🎮 Start analyzing drafts!

For more detailed information, see [README.md](README.md)

## Need Help?

- Check the [README](README.md) for detailed documentation
- Review backend logs for API errors
- Open an issue on GitHub
- Check browser console for frontend errors

---

**Happy drafting!** 🎮

