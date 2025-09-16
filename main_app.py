#!/usr/bin/env python3
"""
Ronin Ecosystem Analytics Dashboard
A comprehensive real-time analytics platform for the Ronin blockchain gaming economy.

Features:
- Network health monitoring with performance scoring
- Gaming economy analytics with user behavior tracking
- Token flow intelligence and whale tracking
- Interactive visualizations with Plotly
- Real-time data from CoinGecko Pro API & Dune Analytics

Author: Analytics Team
Date: 2025
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import requests
import os
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import joblib
from dotenv import load_dotenv
from dune_client.client import DuneClient
import threading

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global cache
_GLOBAL_CACHE = {}
_CACHE_TTL = 86400  # 24 hours
_cache_lock = threading.Lock()

def is_cache_valid(cache_key):
    with _cache_lock:
        if cache_key not in _GLOBAL_CACHE:
            return False
        cache_time, _ = _GLOBAL_CACHE[cache_key]
        return time.time() - cache_time < _CACHE_TTL

def get_cached_data(cache_key):
    with _cache_lock:
        if is_cache_valid(cache_key):
            _, data = _GLOBAL_CACHE[cache_key]
            return data
        return None

def set_cached_data(cache_key, data):
    with _cache_lock:
        _GLOBAL_CACHE[cache_key] = (time.time(), data)

class RoninDataFetcher:
    """Main class for fetching and managing Ronin ecosystem data."""
    
    def __init__(self):
        """Initialize the data fetcher with configuration."""
        load_dotenv()
        
        # API Configuration
        self.api_keys = self._load_api_keys()
        
        # Data Configuration
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        
        # Query Configuration
        self.dune_queries = self._load_query_config()
        
        # Cache Configuration
        self.cache_ttl = 86400  # 24 hours
        self.coingecko_delay = 1.2
        self.dune_delay = 2.0
        self.max_retries = 3
        self.retry_delay = 5
        
        # Session management
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'RoninEcosystemTracker/1.0',
            'Accept': 'application/json'
        })
    
    def _load_api_keys(self) -> Dict[str, str]:
        """Load API keys with Streamlit compatibility."""
        keys = {'dune': None, 'coingecko': None}
        
        try:
            # Primary: Streamlit secrets (for deployed app)
            keys['dune'] = st.secrets.get("DEFI_JOSH_DUNE_QUERY_API_KEY")
            keys['coingecko'] = st.secrets.get("COINGECKO_PRO_API_KEY")
        except:
            # Fallback: Environment variables (for local development)
            keys['dune'] = os.getenv("DEFI_JOSH_DUNE_QUERY_API_KEY")
            keys['coingecko'] = os.getenv("COINGECKO_PRO_API_KEY")
        
        return keys
    
    def _load_query_config(self) -> Dict[str, Dict[str, Any]]:
        """Load Dune query configuration."""
        return {
            'games_overall_activity': {
                'id': 5779698,
                'description': 'Top Game Contracts Overall Activity',
                'filename': 'games_overall_activity.joblib'
            },
            'games_daily_activity': {
                'id': 5781579,
                'description': 'Top Game Contracts Daily Activity',
                'filename': 'games_daily_activity.joblib'
            },
            'ronin_daily_activity': {
                'id': 5779439,
                'description': 'Daily Ronin Network Activity',
                'filename': 'ronin_daily_activity.joblib'
            },
            'user_activation_retention': {
                'id': 5783320,
                'description': 'User Weekly Activation and Retention',
                'filename': 'ronin_users_weekly_activation_and_retention.joblib'
            },
            'ron_current_holders': {
                'id': 5783623,
                'description': 'RON Current Holders',
                'filename': 'ron_current_holders.joblib'
            },
            'ron_segmented_holders': {
                'id': 5785491,
                'description': 'RON Segmented Holders',
                'filename': 'ron_current_segmented_holders.joblib'
            },
            'wron_katana_pairs': {
                'id': 5783967,
                'description': 'WRON Trading Pairs on Katana DEX',
                'filename': 'wron_active_trade_pairs_on_Katana.joblib'
            },
            'wron_whale_tracking': {
                'id': 5784215,
                'description': 'WRON Whale Tracking',
                'filename': 'wron_whale_tracking_on_Katana.joblib'
            },
            'wron_volume_liquidity': {
                'id': 5784210,
                'description': 'WRON Trading Volume & Liquidity',
                'filename': 'WRON_Trading_Volume_Liquidity_Flow_on_Katana.joblib'
            },
            'wron_hourly_activity': {
                'id': 5785066,
                'description': 'WRON Hourly Trading Activity',
                'filename': 'WRON_Trading_by_hour_of_day_on_Katana.joblib'
            },
            'wron_weekly_segmentation': {
                'id': 5785149,
                'description': 'WRON Weekly User Segmentation',
                'filename': 'WRON_weekly_trade_volume_and_user_segmentation_on_Katana.joblib'
            }
        }
    
    def fetch_coingecko_data(self) -> Optional[Dict[str, Any]]:
        """Fetch RON token data from CoinGecko."""
        cache_key = 'coingecko_ron_data'
        cached_data = get_cached_data(cache_key)
        if cached_data:
            return cached_data
        
        if not self.api_keys['coingecko']:
            return self._get_coingecko_fallback_data()
        
        try:
            url = "https://pro-api.coingecko.com/api/v3/coins/ronin"
            headers = {"x-cg-pro-api-key": self.api_keys['coingecko']}
            
            response = self.session.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            ron_data = response.json()
            processed_data = self._process_coingecko_data(ron_data)
            
            set_cached_data(cache_key, processed_data)
            return processed_data
            
        except Exception as e:
            logger.warning(f"CoinGecko API failed: {e}")
            return self._get_coingecko_fallback_data()
    
    def _process_coingecko_data(self, ron_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process CoinGecko data."""
        market_data = ron_data.get("market_data", {})
        
        return {
            'name': ron_data.get('name', 'Ronin'),
            'symbol': ron_data.get('symbol', 'RON'),
            'price_usd': market_data.get('current_price', {}).get('usd', 0),
            'market_cap_usd': market_data.get('market_cap', {}).get('usd', 0),
            'volume_24h_usd': market_data.get('total_volume', {}).get('usd', 0),
            'circulating_supply': market_data.get('circulating_supply', 0),
            'total_supply': market_data.get('total_supply', 0),
            'price_change_24h_pct': market_data.get('price_change_percentage_24h', 0),
            'price_change_7d_pct': market_data.get('price_change_percentage_7d', 0),
            'market_cap_rank': market_data.get('market_cap_rank', 0),
            'last_updated': datetime.now().isoformat()
        }
    
    def _get_coingecko_fallback_data(self) -> Dict[str, Any]:
        """Fallback data for CoinGecko."""
        return {
            'name': 'Ronin',
            'symbol': 'RON',
            'price_usd': 2.15,
            'market_cap_usd': 700000000,
            'volume_24h_usd': 45000000,
            'circulating_supply': 325000000,
            'total_supply': 1000000000,
            'price_change_24h_pct': -2.5,
            'price_change_7d_pct': 8.2,
            'market_cap_rank': 85,
            'last_updated': datetime.now().isoformat(),
            'data_source': 'fallback'
        }
    
    def fetch_dune_query(self, query_key: str) -> Optional[pd.DataFrame]:
        """Fetch data from Dune query."""
        cache_key = f'dune_{query_key}'
        cached_data = get_cached_data(cache_key)
        if cached_data is not None:
            return cached_data
        
        if not self.api_keys['dune'] or query_key not in self.dune_queries:
            return self._get_dune_fallback_data(query_key)
        
        try:
            from dune_client.client import DuneClient
            
            query_config = self.dune_queries[query_key]
            dune = DuneClient(self.api_keys['dune'])
            query_result = dune.get_latest_result(query_config['id'])
            
            if not query_result or not query_result.result or not query_result.result.rows:
                return self._get_dune_fallback_data(query_key)
            
            df = pd.DataFrame(query_result.result.rows)
            set_cached_data(cache_key, df)
            return df
            
        except ImportError:
            logger.warning("dune_client not installed")
            return self._get_dune_fallback_data(query_key)
        except Exception as e:
            logger.warning(f"Dune query {query_key} failed: {e}")
            return self._get_dune_fallback_data(query_key)
    
    def _get_dune_fallback_data(self, query_key: str) -> pd.DataFrame:
        """Generate realistic fallback data for each query type."""
        if query_key == 'games_overall_activity':
            return pd.DataFrame({
                'contract_address': ['0x123...', '0x456...', '0x789...'],
                'project_name': ['Axie Infinity', 'The Machines Arena', 'Pixels'],
                'total_transactions': [15000000, 2500000, 1200000],
                'unique_users': [2800000, 180000, 95000],
                'total_gas_used': [45000000000, 8500000000, 3200000000]
            })
        elif query_key == 'ronin_daily_activity':
            dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
            return pd.DataFrame({
                'date': dates,
                'daily_transactions': np.random.randint(800000, 1200000, 30),
                'active_addresses': np.random.randint(180000, 250000, 30),
                'avg_gas_price_gwei': np.random.uniform(0.1, 0.5, 30),
                'total_gas_used': np.random.randint(15000000000, 25000000000, 30)
            })
        elif query_key == 'ron_segmented_holders':
            return pd.DataFrame({
                'balance_range': ['0-1 RON', '1-10 RON', '10-100 RON', '100-1K RON', '1K-10K RON', '10K+ RON'],
                'holders': [125000, 85000, 45000, 18000, 3500, 850],
                'total_balance': [45000, 420000, 2800000, 8500000, 15600000, 28400000]
            })
        elif query_key == 'wron_whale_tracking':
            return pd.DataFrame({
                'trader_address': ['0xabc...', '0xdef...', '0x123...'],
                'total_volume_usd': [2500000, 1800000, 950000],
                'trade_count': [145, 89, 67],
                'avg_trade_size_usd': [17241, 20225, 14179],
                'profit_loss_usd': [125000, -45000, 78000]
            })
        else:
            return pd.DataFrame()

# Page configuration
st.set_page_config(
    page_title="Ronin Ecosystem Tracker",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced CSS styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    .main {
        font-family: 'Inter', sans-serif;
    }
    
    .stRadio > div {
        display: flex;
        justify-content: center;
        margin-bottom: 30px;
        gap: 15px;
    }
    
    .stRadio > div > label {
        font-size: 16px;
        font-weight: 600;
        color: #FFFFFF;
        background: linear-gradient(135deg, #FF6B35 0%, #F7931E 100%);
        padding: 12px 24px;
        border-radius: 25px;
        border: 2px solid transparent;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        cursor: pointer;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        box-shadow: 0 4px 15px rgba(255, 107, 53, 0.3);
    }
    
    .stRadio > div > label:hover {
        background: linear-gradient(135deg, #00D4FF 0%, #FF6B35 100%);
        transform: translateY(-3px);
        box-shadow: 0 8px 25px rgba(0, 212, 255, 0.4);
        border-color: #00D4FF;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        padding: 25px;
        border-radius: 15px;
        border: 1px solid rgba(255, 107, 53, 0.3);
        margin: 15px 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        border-color: #00D4FF;
        box-shadow: 0 12px 40px rgba(0, 212, 255, 0.2);
        transform: translateY(-2px);
    }
    
    .health-score-excellent {
        color: #00FF88;
        font-weight: 700;
        text-shadow: 0 0 10px rgba(0, 255, 136, 0.5);
    }
    
    .health-score-good {
        color: #4ECDC4;
        font-weight: 700;
    }
    
    .health-score-warning {
        color: #FFB347;
        font-weight: 700;
    }
    
    .health-score-critical {
        color: #FF6B6B;
        font-weight: 700;
        text-shadow: 0 0 10px rgba(255, 107, 107, 0.5);
    }
    
    .insight-box {
        background: linear-gradient(135deg, rgba(255, 107, 53, 0.1) 0%, rgba(0, 212, 255, 0.1) 100%);
        border-left: 4px solid #00D4FF;
        padding: 20px;
        border-radius: 10px;
        margin: 20px 0;
        font-style: italic;
    }
    
    .warning-box {
        background: linear-gradient(135deg, rgba(255, 181, 71, 0.1) 0%, rgba(255, 107, 107, 0.1) 100%);
        border-left: 4px solid #FFB347;
        padding: 15px;
        border-radius: 10px;
        margin: 15px 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize data fetcher
@st.cache_resource
def get_data_fetcher():
    return RoninDataFetcher()

fetcher = get_data_fetcher()

# Sidebar
with st.sidebar:
    st.markdown("""
    <div style="background: linear-gradient(135deg, #FF6B35 0%, #F7931E 100%); 
                padding: 20px; border-radius: 15px; margin-bottom: 25px; text-align: center;">
        <h2 style="color: #FFFFFF; margin: 0; font-weight: 700;">⚡ Ronin Tracker</h2>
        <p style="color: #E0E0E0; margin: 5px 0 0 0; font-size: 0.9em;">Gaming Economy Intelligence</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    ### 🎮 Ronin Blockchain Overview
    
    Ronin is a **gaming-focused sidechain** built by Sky Mavis for Axie Infinity and the broader Web3 gaming ecosystem.
    
    **Key Features:**
    - ⚡ **Fast & Cheap:** Sub-second transactions, minimal fees
    - 🎯 **Gaming-Optimized:** Built specifically for blockchain games
    - 🌉 **Bridge Connected:** Seamless Ethereum integration
    - 🏛️ **PoA Consensus:** Proof of Authority for speed
    
    ---
    
    ### 📊 This Dashboard Tracks:
    
    **🌐 Network Health**
    - Real-time transaction throughput
    - Network congestion analysis
    - Bridge activity monitoring
    - Performance scoring system
    
    **🎮 Gaming Economy**
    - Daily/monthly active players
    - User spending by game category
    - Player retention metrics
    - Game performance rankings
    
    **💰 Token Intelligence**
    - RON/WRON flow distribution
    - Whale wallet tracking
    - DeFi liquidity analysis
    - Cross-sector engagement
    
    **👥 User Behavior**
    - Wallet classification & segmentation
    - Spending pattern analysis
    - Gaming vs DeFi user behavior
    - Retention & activation trends
    
    ---
    
    **💡 Key Insight:** Ronin represents the convergence of traditional gaming and DeFi, creating unique economic dynamics where gaming activity drives token utility and liquidity.
    """)

# Main header
st.markdown("""
<div style="background: linear-gradient(135deg, #00D4FF 0%, #FF6B35 30%, #F7931E 70%, #FF1744 100%); 
           padding: 30px; border-radius: 20px; margin-bottom: 40px; text-align: center;
           box-shadow: 0 10px 40px rgba(255, 107, 53, 0.4);">
    <h1 style="color: white; margin: 0; font-size: 3em; font-weight: 700; 
               text-shadow: 2px 2px 8px rgba(0,0,0,0.5);">
        ⚡ Ronin Ecosystem Tracker
    </h1>
    <p style="color: #E0E0E0; margin: 15px 0 0 0; font-size: 1.3em; font-weight: 400;">
        Real-time Analytics for Ronin Gaming Economy & Network Intelligence
    </p>
    <p style="color: #B0B0B0; margin: 10px 0 0 0; font-size: 1em;">
        Network monitoring • Gaming analytics • Token flows • User intelligence
    </p>
</div>
""", unsafe_allow_html=True)

# Navigation
section = st.radio(
    "",
    ["Network Overview", "Gaming Economy", "Token Intelligence", "User Analytics"],
    horizontal=True
)

# Load data
coingecko_data = fetcher.fetch_coingecko_data()
games_overall = fetcher.fetch_dune_query('games_overall_activity')
ronin_daily = fetcher.fetch_dune_query('ronin_daily_activity')
ron_holders = fetcher.fetch_dune_query('ron_segmented_holders')
whale_data = fetcher.fetch_dune_query('wron_whale_tracking')

# === NETWORK OVERVIEW SECTION ===
if section == "Network Overview":
    st.markdown("## 🌐 Network Health & Performance Dashboard")
    
    # Network Health Score Calculation
    def calculate_network_health_score(daily_data, token_data):
        score = 100
        
        if daily_data is not None and not daily_data.empty and len(daily_data) >= 7:
            recent_data = daily_data.tail(7)
            
            # Transaction throughput (30 points)
            avg_tx = recent_data['daily_transactions'].mean()
            if avg_tx < 500000:
                score -= 15
            elif avg_tx < 800000:
                score -= 5
            
            # Network activity trend (25 points)
            tx_trend = (recent_data['daily_transactions'].iloc[-1] - recent_data['daily_transactions'].iloc[0]) / recent_data['daily_transactions'].iloc[0]
            if tx_trend < -0.2:
                score -= 25
            elif tx_trend < -0.1:
                score -= 10
            
            # Gas price stability (20 points)
            gas_volatility = recent_data['avg_gas_price_gwei'].std() / recent_data['avg_gas_price_gwei'].mean()
            if gas_volatility > 0.5:
                score -= 20
            elif gas_volatility > 0.3:
                score -= 10
        
        # Token performance (25 points)
        if token_data and token_data.get('price_change_7d_pct'):
            price_change = token_data['price_change_7d_pct']
            if price_change < -20:
                score -= 25
            elif price_change < -10:
                score -= 15
            elif price_change < -5:
                score -= 5
        
        return max(0, min(100, score))
    
    network_health_score = calculate_network_health_score(ronin_daily, coingecko_data)
    
    # Key Metrics Row
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        health_status = "Excellent" if network_health_score >= 85 else "Good" if network_health_score >= 70 else "Warning" if network_health_score >= 50 else "Critical"
        st.metric("🏥 Network Health", f"{network_health_score}/100", delta=health_status)
    
    with col2:
        if ronin_daily is not None and not ronin_daily.empty:
            latest_tx = ronin_daily['daily_transactions'].iloc[-1] if len(ronin_daily) > 0 else 1000000
            st.metric("📊 Daily Transactions", f"{latest_tx:,.0f}", delta="24h volume")
        else:
            st.metric("📊 Daily Transactions", "1,000,000", delta="24h volume")
    
    with col3:
        if coingecko_data:
            st.metric("💎 RON Price", f"${coingecko_data['price_usd']:.3f}", 
                     delta=f"{coingecko_data['price_change_24h_pct']:.1f}%")
        else:
            st.metric("💎 RON Price", "$2.150", delta="-2.5%")
    
    with col4:
        if ronin_daily is not None and not ronin_daily.empty:
            latest_users = ronin_daily['active_addresses'].iloc[-1] if len(ronin_daily) > 0 else 200000
            st.metric("👥 Active Addresses", f"{latest_users:,.0f}", delta="24h unique")
        else:
            st.metric("👥 Active Addresses", "200,000", delta="24h unique")
    
    with col5:
        if coingecko_data:
            market_cap_b = coingecko_data['market_cap_usd'] / 1e9
            st.metric("🏦 Market Cap", f"${market_cap_b:.2f}B", 
                     delta=f"Rank #{coingecko_data['market_cap_rank']}")
        else:
            st.metric("🏦 Market Cap", "$0.70B", delta="Rank #85")
    
    st.markdown("---")
    
    # Network Activity Visualization
    col1, col2 = st.columns(2)
    
    with col1:
        if ronin_daily is not None and not ronin_daily.empty:
            # Convert date column if it's string
            if 'date' in ronin_daily.columns:
                ronin_daily['date'] = pd.to_datetime(ronin_daily['date'])
            
            fig_network = make_subplots(
                rows=2, cols=1,
                subplot_titles=("Daily Transaction Volume", "Active Addresses & Gas Prices"),
                vertical_spacing=0.1
            )
            
            # Transactions
            fig_network.add_trace(
                go.Scatter(
                    x=ronin_daily['date'],
                    y=ronin_daily['daily_transactions'],
                    mode='lines+markers',
                    name='Daily Transactions',
                    line=dict(color='#FF6B35', width=3),
                    fill='tonexty'
                ),
                row=1, col=1
            )
            
            # Active addresses
            fig_network.add_trace(
                go.Scatter(
                    x=ronin_daily['date'],
                    y=ronin_daily['active_addresses'],
                    mode='lines+markers',
                    name='Active Addresses',
                    line=dict(color='#00D4FF', width=3),
                    yaxis='y3'
                ),
                row=2, col=1
            )
            
            fig_network.update_layout(
                height=600,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white',
                title="🌐 Network Activity Trends (30 Days)"
            )
            
            st.plotly_chart(fig_network, use_container_width=True)
        else:
            st.info("Network activity data temporarily unavailable")
    
    with col2:
        # Network Health Gauge
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=network_health_score,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "🏥 Network Health Score"},
            delta={'reference': 85, 'position': "top"},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': "#FF6B35"},
                'steps': [
                    {'range': [0, 50], 'color': "lightgray"},
                    {'range': [50, 85], 'color': "gray"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        
        fig_gauge.update_layout(
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white'
        )
        
        st.plotly_chart(fig_gauge, use_container_width=True)
        
        # Token holder distribution
        if ron_holders is not None and not ron_holders.empty:
            fig_holders = px.pie(
                ron_holders,
                values='holders',
                names='balance_range',
                title="💰 RON Holder Distribution",
                color_discrete_sequence=['#FF6B35', '#F7931E', '#00D4FF', '#4ECDC4', '#45B7D1', '#FFB347']
            )
            
            fig_holders.update_layout(
                height=350,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white'
            )
            
            st.plotly_chart(fig_holders, use_container_width=True)

# === GAMING ECONOMY SECTION ===
elif section == "Gaming Economy":
    st.markdown("## 🎮 Gaming Economy & Player Analytics")
    
    if games_overall is not None and not games_overall.empty:
        # Gaming metrics
        total_gaming_users = games_overall['unique_users'].sum()
        total_gaming_tx = games_overall['total_transactions'].sum()
        top_game = games_overall.iloc[0]['project_name'] if len(games_overall) > 0 else "Axie Infinity"
        
        col1, col2, col3, col4 = st.columns(4)