# Ronin Ecosystem Tracker

A comprehensive real-time analytics dashboard for the Ronin blockchain gaming economy. This professional-grade analytics platform provides deep insights into gaming performance, DeFi activity, NFT marketplace dynamics, and network health monitoring.

## Features

### Core Analytics
- **Gaming Intelligence**: Player behavior analysis, game performance rankings, revenue optimization insights
- **DeFi Analytics**: Liquidity flow analysis, trading pattern insights, whale activity monitoring  
- **NFT Marketplace Intel**: Collection performance metrics, floor price analytics, revenue breakdown
- **Network Health Monitoring**: Real-time performance scoring, congestion analysis, predictive alerts

### Advanced Capabilities
- 24-hour intelligent caching system
- Real-time alert system with severity levels
- Actionable recommendations and insights
- Professional visualizations with interactive charts
- Time-based filtering (7 days, 30 days, 90 days, all time)
- Whale transaction tracking with configurable thresholds
- Comprehensive network health scoring

## Live Demo

**[View Dashboard](https://ronin-ecosystem-tracker.streamlit.app)**

## Architecture

### Data Sources
- **Dune Analytics**: On-chain blockchain data via professional API
- **CoinGecko Pro**: Market data, pricing, and token metrics
- **Intelligent Caching**: 24-hour cache system to optimize API usage

### Technology Stack
- **Frontend**: Streamlit with custom CSS styling
- **Data Processing**: Pandas, NumPy for data manipulation
- **Visualizations**: Plotly for interactive charts and graphs
- **APIs**: Dune Analytics API, CoinGecko Pro API
- **Caching**: Joblib for persistent data storage

## Installation

### Prerequisites
- Python 3.8+
- API Keys:
  - Dune Analytics API key
  - CoinGecko Pro API key

### Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/ronin-ecosystem-tracker.git
   cd ronin-ecosystem-tracker
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Configuration**
   
   Create a `.env` file in the root directory:
   ```env
   DEFI_JOSH_DUNE_QUERY_API_KEY=your_dune_api_key_here
   COINGECKO_PRO_API_KEY=your_coingecko_pro_api_key_here
   ```

4. **Run the application**
   ```bash
   streamlit run ronin_tracker_app.py
   ```

## API Configuration

### Required API Keys

#### Dune Analytics API
- Sign up at [Dune Analytics](https://dune.com)
- Navigate to Settings > API Keys
- Generate a new API key
- Add to environment as `DEFI_JOSH_DUNE_QUERY_API_KEY`

#### CoinGecko Pro API  
- Sign up at [CoinGecko Pro](https://www.coingecko.com/en/api/pricing)
- Get your API key from the dashboard
- Add to environment as `COINGECKO_PRO_API_KEY`

### Query Configuration

The dashboard uses predefined Dune query IDs for consistent data retrieval:

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
    'nft_collections': 5792320
}
```

## Usage

### Dashboard Sections

#### Executive Overview
- RON token market intelligence
- Network health gauge with scoring
- Ecosystem spending analysis across sectors
- User segmentation insights

#### Gaming Intelligence  
- Game performance leaderboards
- Player behavior analytics
- Revenue per player metrics
- Transaction activity analysis

#### DeFi Analytics
- Liquidity flow visualization
- Trading volume intelligence
- Whale activity monitoring
- Cross-sector liquidity analysis

#### Alert Center
- Real-time network health alerts
- Whale transaction notifications
- Gaming sector activity warnings
- System performance monitoring

### Configuration Options

#### Time Filters
- Last 7 days
- Last 30 days  
- Last 90 days
- All time

#### Advanced Settings
- Whale transaction threshold (default: $50,000)
- Minimum player count for game analysis
- Alert severity levels

## Data Flow

```
External APIs → Data Manager → Analytics Engine → Visualizer → Dashboard
     ↓              ↓              ↓             ↓          ↓
CoinGecko Pro   24h Cache    Health Scoring   Plotly    Streamlit
Dune Analytics  File System  Alert Generation  Charts    Interface
```

## Caching System

The dashboard implements intelligent caching to optimize API usage:

- **Duration**: 24-hour cache lifecycle
- **Storage**: Local file system using Joblib
- **Validation**: Automatic cache expiration and refresh
- **Efficiency**: Shared cache across all users
- **Fallback**: Graceful handling of cache failures

## Development

### Project Structure
```
ronin-ecosystem-tracker/
├── ronin_tracker_app.py    # Main application file
├── requirements.txt        # Python dependencies
├── .env                   # Environment variables (create locally)
├── data/                  # Cache directory (auto-created)
└── README.md             # This file
```

### Key Classes

#### `DataManager`
- Handles API connections and data fetching
- Manages 24-hour caching system
- Processes and cleans raw data

#### `AnalyticsEngine`  
- Calculates network health scores
- Generates comprehensive alerts
- Analyzes spending patterns and liquidity flows

#### `Visualizer`
- Creates interactive charts and gauges
- Handles color schemes and styling
- Generates empty state displays

#### `RoninDashboard`
- Main dashboard orchestration
- Tab rendering and layout management
- User interaction handling

### Adding New Features

1. **New Data Source**: Extend `DataManager` with additional API endpoints
2. **New Analytics**: Add methods to `AnalyticsEngine` for custom calculations  
3. **New Visualizations**: Extend `Visualizer` with new chart types
4. **New Dashboard Sections**: Add render methods to `RoninDashboard`

## Deployment

### Streamlit Cloud

1. **Connect Repository**: Link your GitHub repository to Streamlit Cloud
2. **Configure Secrets**: Add API keys in Streamlit Cloud app settings:
   - `DEFI_JOSH_DUNE_QUERY_API_KEY`
   - `COINGECKO_PRO_API_KEY`
3. **Deploy**: Streamlit Cloud automatically deploys from your main branch

### Local Deployment

For production deployment on your own infrastructure:

```bash
# Install production dependencies
pip install -r requirements.txt

# Set environment variables
export DEFI_JOSH_DUNE_QUERY_API_KEY=your_key
export COINGECKO_PRO_API_KEY=your_key

# Run with production settings
streamlit run ronin_tracker_app.py --server.port 8501
```

## Dependencies

### Core Requirements
```
streamlit>=1.28.0
pandas>=1.5.0
numpy>=1.24.0
plotly>=5.15.0
requests>=2.28.0
dune-client>=1.0.0
python-dotenv>=1.0.0
joblib>=1.3.0
```

### Development Dependencies
- `pytest` for testing
- `black` for code formatting
- `flake8` for linting

## Performance Considerations

### API Rate Limits
- Dune Analytics: Respects API quotas with 24-hour caching
- CoinGecko Pro: Professional tier with higher rate limits
- Refresh cooldown: 30-minute minimum between manual refreshes

### Memory Management
- Efficient pandas operations for large datasets
- Lazy loading of visualizations
- Cache cleanup for expired data

### User Experience
- Progressive loading with status indicators
- Error handling with user-friendly messages
- Responsive design for different screen sizes

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-analytics`)
3. Commit your changes (`git commit -am 'Add new analytics feature'`)
4. Push to the branch (`git push origin feature/new-analytics`)
5. Create a Pull Request

### Development Guidelines
- Follow PEP 8 style guidelines
- Add docstrings for new functions
- Include error handling for external API calls
- Test new features with sample data

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📧 Contact

Created by **Jo$h** - DeFi Analytics Specialist

For questions, suggestions, or collaboration opportunities, please send a DM on [Telegram](https://t.me/joshuatochinwachi) or [X](https://x.com/defi__josh).

## Acknowledgments

- **Ronin Network**: For providing an innovative gaming-focused blockchain
- **Dune Analytics**: For comprehensive on-chain data access
- **CoinGecko**: For reliable market data and pricing information
- **Streamlit**: For the excellent web app framework

---

Built with ❤️ for the Ronin community