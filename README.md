# Ronin Ecosystem Tracker

A comprehensive, production-grade analytics platform for the Ronin blockchain gaming economy. This project provides real-time insights into gaming performance, DeFi activity, NFT marketplace dynamics, and network health monitoring through multiple interfaces: a modern web dashboard, a Streamlit analytics app, and a robust FastAPI backend.

## 🌐 Live Applications

- **Primary App/Dashboard (Next.js)**: [https://ronin-network-tracker.vercel.app](https://ronin-network-tracker.vercel.app)
- **Analytics App (Streamlit)**: [https://ronin-ecosystem-tracker.streamlit.app](https://ronin-ecosystem-tracker.streamlit.app)
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
│  External APIs  │────▶│  FastAPI Backend │────▶│  Applications   │
│                 │     │  (Railway)       │     │                 │
│ • Dune (x12)    │     │                  │     │ • Next.js Web   │
│ • CoinGecko     │     │ • 24hr Cache     │     │ • Streamlit App │
└─────────────────┘     │ • Rate Limiting  │     └─────────────────┘
                        │ • Data Proxy     │
                        └──────────────────┘
```

### Data Flow

1. **External APIs** → FastAPI fetches from Dune Analytics & CoinGecko
2. **Caching Layer** → 24-hour cache with joblib for persistent storage
3. **API Endpoints** → RESTful endpoints serve raw, unmanipulated data
4. **Frontend Apps** → Next.js and Streamlit consume API data
5. **User Interface** → Interactive visualizations and real-time updates

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Node.js 18+ (for Next.js frontend)
- API Keys:
  - Dune Analytics API key
  - CoinGecko Pro API key

### Backend Setup (FastAPI)

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/ronin-ecosystem-tracker.git
   cd ronin-ecosystem-tracker
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   
   Create a `.env` file:
   ```env
   DEFI_JOSH_DUNE_QUERY_API_KEY=your_dune_api_key
   COINGECKO_PRO_API_KEY=your_coingecko_pro_api_key
   PORT=8000
   ```

4. **Run the FastAPI server**
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

   API will be available at `http://localhost:8000`

### Streamlit App Setup

```bash
streamlit run ronin_tracker_app.py
```

Access at `http://localhost:8501`

### Next.js Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd frontend  # or your frontend directory name
   ```

2. **Install dependencies**
   ```bash
   npm install
   # or
   yarn install
   ```

3. **Run development server**
   ```bash
   npm run dev
   # or
   yarn dev
   ```

   Dashboard available at `http://localhost:3000`

## 📡 API Documentation

### Base URL
```
Production: https://web-production-4fae.up.railway.app
Local: http://localhost:8000
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

#### Interactive Documentation
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

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

### Analytics App (Streamlit)
- **Framework**: Streamlit
- **Visualizations**: Plotly
- **Data Processing**: Pandas, NumPy
- **Styling**: Custom CSS
- **Deployment**: Streamlit Cloud

## 📁 Project Structure

```
ronin-ecosystem-tracker/
├── main.py                      # FastAPI backend application
├── ronin_tracker_app.py         # Streamlit analytics app
├── requirements.txt             # Python dependencies
├── .env                         # Environment variables (create locally)
├── raw_data_cache/             # Cache directory (auto-created)
├── frontend/                    # Next.js application
│   ├── app/
│   │   ├── api/                # Next.js API routes (proxy)
│   │   ├── layout.tsx          # Root layout
│   │   ├── page.tsx            # Main dashboard
│   │   └── globals.css         # Global styles
│   ├── components/
│   │   ├── ui/                 # shadcn/ui components
│   │   ├── animated-background.tsx
│   │   ├── gaming-economy.tsx
│   │   ├── katana-dex.tsx
│   │   ├── network-activity.tsx
│   │   ├── nft-marketplace.tsx
│   │   └── token-holders.tsx
│   ├── hooks/                  # Custom React hooks
│   └── lib/                    # Utility functions
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

## 🚢 Deployment

### FastAPI Backend (Railway)

1. Connect your GitHub repository to Railway
2. Add environment variables in Railway dashboard
3. Railway auto-deploys from your main branch

### Next.js Frontend (Vercel)

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/yourusername/ronin-ecosystem-tracker)

1. Connect repository to Vercel
2. Vercel automatically builds and deploys
3. Configure environment variables if needed

### Streamlit App (Streamlit Cloud)

1. Connect repository to Streamlit Cloud
2. Add API keys in app settings:
   - `DEFI_JOSH_DUNE_QUERY_API_KEY`
   - `COINGECKO_PRO_API_KEY`
3. Auto-deploys from main branch

## 🔐 API Keys Setup

### Dune Analytics API
1. Sign up at [Dune Analytics](https://dune.com)
2. Navigate to Settings → API Keys
3. Generate a new API key
4. Add to environment as `DEFI_JOSH_DUNE_QUERY_API_KEY`

### CoinGecko Pro API
1. Sign up at [CoinGecko Pro](https://www.coingecko.com/en/api/pricing)
2. Get your API key from the dashboard
3. Add to environment as `COINGECKO_PRO_API_KEY`

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