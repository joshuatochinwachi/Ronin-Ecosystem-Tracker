# Ronin Ecosystem Tracker

A comprehensive, production-grade analytics platform for the Ronin blockchain gaming economy. This project provides real-time insights into gaming performance, DeFi activity, NFT marketplace dynamics, and network health monitoring through multiple interfaces: a modern web dashboard, a Streamlit analytics app, and a robust FastAPI backend.

## 🌐 Live Applications

- **Primary App/Dashboard (Next.js)**: [https://ronin-network-tracker.vercel.app](https://ronin-network-tracker.vercel.app)
- **API Backend**: Hosted on Railway

## 📊 Project Overview

This platform aggregates and visualizes data from 13 different data sources (1 CoinGecko + 12 Dune Analytics queries) to provide a holistic view of the Ronin Network ecosystem. The architecture consists of three main components:

1. **FastAPI Backend** - Raw data pass-through with 24-hour intelligent caching
2. **Next.js Frontend** - Modern, interactive web dashboard with real-time updates
3. **Streamlit App** - Professional analytics interface with advanced visualizations

## ✨ Core Features

### Analytics Capabilities
- **Gaming Intelligence**: Player behavior analysis, game performance rankings, revenue optimization
- **DeFi Analytics**: Liquidity flow analysis, trading patterns, whale activity monitoring
- **NFT Marketplace Intel**: Collection performance metrics, floor price analytics, revenue breakdown
- **Network Health Monitoring**: Real-time performance scoring, congestion analysis, predictive alerts
- **Token Holder Analytics**: Distribution analysis, segmentation (whales, large holders, retail)
- **User Retention Analysis**: Cohort-based retention tracking with interactive heatmaps

### Technical Features
- 24-hour intelligent caching system for optimal API usage
- Real-time alert system with severity levels
- Actionable recommendations and insights
- Interactive charts and visualizations (Plotly, Recharts)
- Dark/light mode with persistent preferences
- Responsive design for all devices
- Auto-refresh capabilities with manual override
- Time-based filtering (7, 30, 90 days, all time)

## 🏗️ Architecture

### System Design

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  External APIs  │────▶│  FastAPI Backend │────▶│  Application   │
│                 │     │  (Railway)       │     │                 │
│ • Dune (x12)    │     │                  │     │ • Next.js Web   │
│ • CoinGecko     │     │ • 24hr Cache     │     │                 │
└─────────────────┘     │ • Rate Limiting  │     └─────────────────┘
                        │ • Data Proxy     │
                        └──────────────────┘
```

### Data Flow

1. **External APIs** → FastAPI fetches from Dune Analytics & CoinGecko
2. **Caching Layer** → 24-hour cache with joblib for persistent storage
3. **API Endpoints** → RESTful endpoints serve raw, unmanipulated data
4. **Frontend App** → Next.js consume API data
5. **User Interface** → Interactive visualizations and real-time updates

## 📡 API Documentation

### Base URL
```
Production: https://web-production-4fae.up.railway.app
```

### Key Endpoints

#### CoinGecko Data
- `GET /api/raw/coingecko/ron` - RON token market data

#### Dune Analytics Data (12 endpoints)
- `GET /api/raw/dune/ronin_daily_activity` - Daily network metrics
- `GET /api/raw/dune/games_overall_activity` - Gaming statistics
- `GET /api/raw/dune/games_daily_activity` - Daily gaming activity
- `GET /api/raw/dune/user_activation_retention` - User retention cohorts
- `GET /api/raw/dune/ron_current_holders` - Token holder data
- `GET /api/raw/dune/ron_segmented_holders` - Holder segmentation
- `GET /api/raw/dune/wron_active_trade_pairs` - DEX trading pairs
- `GET /api/raw/dune/wron_whale_tracking` - Whale wallet activity
- `GET /api/raw/dune/wron_volume_liquidity` - Volume & liquidity
- `GET /api/raw/dune/wron_trading_hourly` - Hourly trading patterns
- `GET /api/raw/dune/wron_weekly_segmentation` - Weekly trader segments
- `GET /api/raw/dune/nft_collections` - NFT marketplace data

#### Utility Endpoints
- `GET /api/cache/status` - Cache status for all sources
- `POST /api/cache/refresh` - Force refresh all data
- `POST /api/cache/clear` - Clear all cached data
- `GET /api/bulk/all` - Get all data sources at once

## 🛠️ Technology Stack

### Backend (FastAPI)
- **Framework**: FastAPI
- **Data Processing**: Pandas, NumPy
- **Caching**: Joblib (24-hour persistent cache)
- **APIs**: Dune Analytics, CoinGecko Pro
- **Async Operations**: aiohttp, asyncio
- **Deployment**: Railway

### Frontend (Next.js)
- **Framework**: Next.js 15 with App Router
- **UI Library**: React 19, TypeScript
- **Styling**: Tailwind CSS v4, shadcn/ui
- **Charts**: Recharts
- **Data Fetching**: SWR (stale-while-revalidate)
- **Icons**: Lucide React
- **Deployment**: Vercel

## 📁 Project Structure

```
ronin-ecosystem-tracker/
├── main.py                      # FastAPI backend application
├── ronin_tracker_app.py         # Streamlit analytics app
├── requirements.txt             # Python dependencies
├── .env                         # Environment variables (create locally)
├── raw_data_cache/             # Cache directory (auto-created)
├── frontend/                    # Next.js application
│  ├── app/
│  │   ├── api/                    # Next.js API routes (proxy layer)
│  │   │   ├── coingecko/
│  │   │   │   └── ron/
│  │   │   │       └── route.ts    # RON token data endpoint
│  │   │   └── dune/
│  │   │       ├── games-overall/
│  │   │       ├── games-daily/
│  │   │       ├── ronin-daily/
│  │   │       ├── retention/
│  │   │       ├── holders/
│  │   │       ├── segmented-holders/
│  │   │       ├── trade-pairs/
│  │   │       ├── whales/
│  │   │       ├── volume-liquidity/
│  │   │       ├── hourly/
│  │   │       ├── weekly-segmentation/
│  │   │       └── nft-collections/
│  │   ├── layout.tsx              # Root layout with theme provider
│  │   ├── page.tsx                # Main dashboard page
│  │   └── globals.css             # Global styles and design tokens
│  ├── components/
│  │   ├── ui/                     # shadcn/ui components
│  │   ├── animated-background.tsx # Particle animation system
│  │   ├── gaming-economy.tsx      # Gaming metrics section
│  │   ├── header.tsx              # Dashboard header with refresh
│  │   ├── hero-section.tsx        # RON token overview
│  │   ├── katana-dex.tsx          # DEX analytics section
│  │   ├── network-activity.tsx    # Network activity charts
│  │   ├── network-health.tsx      # Network health metrics
│  │   ├── nft-collections.tsx     # NFT collections table
│  │   ├── nft-marketplace.tsx     # NFT marketplace section
│  │   ├── retention-heatmap.tsx   # Cohort retention heatmap
│  │   ├── theme-provider.tsx      # Dark/light mode provider
│  │   ├── theme-toggle.tsx        # Theme switcher button
│  │   ├── token-holders.tsx       # Token holder analytics
│  │   └── token-metrics.tsx       # Token metrics cards
│  ├── hooks/
│  │   ├── use-mobile.tsx          # Mobile detection hook
│  │   └── use-toast.ts            # Toast notification hook
│  ├── lib/
│  │   └── utils.ts                # Utility functions (cn, etc.)
│  └── public/                     # Static assets
├── Notebooks/                   # Jupyter notebooks for analysis
└── README.md                   # This file
```

## 🔧 Configuration

### Dune Query IDs

The platform uses these predefined Dune Analytics query IDs:

```python
dune_queries = {
    'games_overall_activity': 5779698,
    'games_daily_activity': 5781579,
    'ronin_daily_activity': 5779439,
    'user_activation_retention': 5783320,
    'ron_current_holders': 5783623,
    'ron_segmented_holders': 5785491,
    'wron_active_trade_pairs': 5783967,
    'wron_whale_tracking': 5784215,
    'wron_volume_liquidity': 5784210,
    'wron_trading_hourly': 5785066,
    'wron_weekly_segmentation': 5785149,
    'nft_collections': 5792313
}
```

### Caching System

- **Duration**: 24-hour cache lifecycle
- **Storage**: Local filesystem using Joblib
- **Validation**: Automatic cache expiration and refresh
- **Background Tasks**: Auto-refresh every 24 hours
- **Efficiency**: Shared cache across all users

## 📈 Performance Considerations

- **API Rate Limits**: 24-hour caching minimizes API calls
- **Memory Management**: Efficient pandas operations for large datasets
- **Lazy Loading**: Progressive component loading for better UX
- **Auto-refresh**: Smart revalidation with SWR
- **Background Tasks**: Non-blocking data refresh operations

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **KTTY World** - For inspiring this analytics tool
- **Ronin Network** - For building an innovative gaming-focused blockchain
- **Dune Analytics** - For comprehensive on-chain data access
- **CoinGecko** - For reliable market data and pricing
- **Vercel** - For seamless frontend deployment
- **Railway** - For reliable backend hosting
- **Streamlit** - For the excellent analytics framework

## 📧 Contact

Created by **Jo$h** - DeFi Analytics Specialist

- **Telegram**: [@joshuatochinwachi](https://t.me/joshuatochinwachi)
- **X (Twitter)**: [@defi__josh](https://x.com/defi__josh)

For questions, suggestions, or collaboration opportunities, feel free to reach out!

---

**Built with ❤️ for the Ronin community**