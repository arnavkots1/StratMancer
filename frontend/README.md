# StratMancer Frontend

Next.js 14+ frontend for the StratMancer League of Legends draft analysis tool.

## Features

- 🎮 **Draft Analyzer**: Interactive champion selection for both teams
- 🔮 **AI Predictions**: Real-time win probability calculations
- 📊 **Smart Insights**: Detailed explanations of draft strengths/weaknesses
- 🎨 **Modern UI**: Clean, responsive design with Tailwind CSS
- ⚡ **Fast**: Optimized with Next.js App Router and React Server Components

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Icons**: Lucide React
- **API**: REST client with fetch

## Getting Started

### Prerequisites

- Node.js 18+ and npm 9+
- Backend API running on `http://localhost:8000` (or configured URL)

### Installation

```bash
cd frontend
npm install
```

### Configuration

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your settings:
   ```bash
   NEXT_PUBLIC_API_URL=http://localhost:8000
   NEXT_PUBLIC_API_KEY=your-api-key-here
   ```

### Development

Start the development server:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Production Build

```bash
npm run build
npm start
```

## Project Structure

```
frontend/
├── app/                    # Next.js App Router
│   ├── draft/             # Draft analyzer page
│   │   └── page.tsx
│   ├── layout.tsx         # Root layout with header/footer
│   ├── page.tsx           # Home page
│   └── globals.css        # Global styles
├── components/            # React components
│   ├── ChampionPicker.tsx # Champion selection grid
│   ├── RoleSlots.tsx      # Team composition builder
│   └── PredictionCard.tsx # Prediction results display
├── lib/                   # Utilities
│   └── api.ts            # API client
├── types/                 # TypeScript types
│   └── index.ts
└── public/               # Static assets
```

## Key Components

### ChampionPicker

Searchable grid of champions with:
- Text search
- Role filtering (Top, Jungle, Mid, ADC, Support)
- Tag filtering (Damage types, playstyles)
- Visual feedback for selected/banned champions

### RoleSlots

Team composition builder featuring:
- 5 role slots per team (Blue/Red)
- 5 ban slots per team
- Real-time team stats (Engage, CC, Sustain)
- Drag-and-drop support (future)

### PredictionCard

Displays match predictions with:
- Win probability for both teams
- Confidence score with visual indicator
- Top 5 key factors affecting the match
- Positive/negative impact visualization

## API Integration

The frontend connects to the StratMancer backend API:

### Endpoints Used

- `GET /healthz` - Health check
- `GET /models/feature-map` - Champion data
- `POST /predict/draft` - Get draft prediction

### Request Format

```typescript
{
  blue_team: [championId1, championId2, ...],
  red_team: [championId1, championId2, ...],
  blue_bans: [championId1, ...],
  red_bans: [championId1, ...],
  elo: "low" | "mid" | "high",
  patch?: "14.1"
}
```

### Response Format

```typescript
{
  win_probability: 0.55,  // 55% blue team win rate
  confidence: 0.85,        // 85% model confidence
  explanations: [
    {
      factor: "Team Engage",
      impact: 0.08,
      description: "Blue team has strong initiation tools"
    }
  ],
  model_version: "v1.0.0",
  timestamp: "2025-01-17T..."
}
```

## Customization

### Colors

Edit `tailwind.config.ts` to customize the theme:

```typescript
colors: {
  gold: { /* Your gold palette */ },
  blue: { /* Your blue palette */ },
  red: { /* Your red palette */ },
}
```

### Champion Images

To add real champion images:

1. Update the champion card rendering in `ChampionPicker.tsx`
2. Use Data Dragon CDN:
   ```
   https://ddragon.leagueoflegends.com/cdn/{version}/img/champion/{championName}.png
   ```

## Troubleshooting

### API Connection Issues

- Verify backend is running: `curl http://localhost:8000/healthz`
- Check `NEXT_PUBLIC_API_URL` in `.env`
- Ensure CORS is enabled on backend

### Build Errors

- Clear `.next` folder: `rm -rf .next`
- Clear node_modules: `rm -rf node_modules && npm install`
- Check Node version: `node --version` (must be 18+)

### Type Errors

- Run type check: `npm run type-check`
- Rebuild: `npm run build`

## Performance

- **First Load**: ~200KB gzipped
- **Page Transition**: Client-side navigation
- **API Latency**: <500ms for predictions

## Browser Support

- Chrome/Edge 90+
- Firefox 88+
- Safari 14+

## Contributing

1. Create a feature branch
2. Make your changes
3. Test with `npm run build`
4. Submit a pull request

## License

See root LICENSE file.

