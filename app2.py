#!/usr/bin/env python3
"""
Ronin Ecosystem Analytics Dashboard
A comprehensive real-time analytics platform for the Ronin blockchain gaming economy.

Features:
- Network health monitoring with advanced performance scoring
- Gaming economy analytics with player behavior tracking
- Token intelligence with whale tracking and DeFi flows
- User analytics with retention and segmentation analysis
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
import threading
import math

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
        
        # Query Configuration with corrected filenames
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
        """Load Dune query configuration with corrected filenames."""
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
                'filename': 'ronin_users_weekly_activation_and_retention_for_each_project_or_game.joblib'
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
                'filename': 'WRON_Trading_Volume_&_Liquidity_Flow_on_Katana.joblib'
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
            'price_change_30d_pct': market_data.get('price_change_percentage_30d', 0),
            'market_cap_rank': market_data.get('market_cap_rank', 0),
            'tvl_usd': market_data.get('total_value_locked', {}).get('usd', 0),
            'mcap_to_tvl_ratio': market_data.get('mcap_to_tvl_ratio', 0),
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
            'price_change_30d_pct': 15.3,
            'market_cap_rank': 85,
            'tvl_usd': 180000000,
            'mcap_to_tvl_ratio': 3.89,
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
                'contract_address': ['0x32950db2a7164ae833121501c797d79e7b79d74c', '0x97a9107c1793bc407d6f527b77e7fff4d812bece', '0x8c811e3c958e190f5ec15fb376533a3398620500'],
                'project_name': ['Axie Infinity', 'The Machines Arena', 'Pixels'],
                'total_transactions': [15000000, 2500000, 1200000],
                'unique_users': [2800000, 180000, 95000],
                'total_gas_used': [45000000000, 8500000000, 3200000000],
                'avg_gas_per_tx': [3000, 3400, 2667]
            })
        elif query_key == 'games_daily_activity':
            dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
            games = ['Axie Infinity', 'The Machines Arena', 'Pixels']
            daily_data = []
            for date in dates:
                for game in games:
                    base_users = {'Axie Infinity': 250000, 'The Machines Arena': 18000, 'Pixels': 12000}[game]
                    daily_data.append({
                        'date': date,
                        'project_name': game,
                        'daily_active_users': int(base_users * np.random.uniform(0.7, 1.3)),
                        'daily_transactions': int(base_users * np.random.uniform(2, 8)),
                        'daily_gas_used': int(base_users * np.random.uniform(500000, 1500000))
                    })
            return pd.DataFrame(daily_data)
        elif query_key == 'ronin_daily_activity':
            dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
            return pd.DataFrame({
                'date': dates,
                'daily_transactions': np.random.randint(800000, 1200000, 30),
                'active_addresses': np.random.randint(180000, 250000, 30),
                'avg_gas_price_gwei': np.random.uniform(0.1, 0.5, 30),
                'total_gas_used': np.random.randint(15000000000, 25000000000, 30),
                'new_addresses': np.random.randint(5000, 15000, 30)
            })
        elif query_key == 'user_activation_retention':
            weeks = pd.date_range(end=datetime.now(), periods=12, freq='W')
            games = ['Axie Infinity', 'The Machines Arena', 'Pixels', 'Tearing Spaces', 'Apeiron']
            retention_data = []
            for week in weeks:
                for game in games:
                    base_activation = {'Axie Infinity': 45000, 'The Machines Arena': 2800, 'Pixels': 1500, 'Tearing Spaces': 800, 'Apeiron': 600}[game]
                    retention_data.append({
                        'week': week,
                        'project_name': game,
                        'new_users': int(base_activation * np.random.uniform(0.6, 1.4)),
                        'retained_users_1w': int(base_activation * np.random.uniform(0.3, 0.7)),
                        'retained_users_4w': int(base_activation * np.random.uniform(0.1, 0.3)),
                        'retention_rate_1w': np.random.uniform(0.35, 0.75),
                        'retention_rate_4w': np.random.uniform(0.15, 0.35)
                    })
            return pd.DataFrame(retention_data)
        elif query_key == 'ron_segmented_holders':
            return pd.DataFrame({
                'balance_range': ['0-1 RON', '1-10 RON', '10-100 RON', '100-1K RON', '1K-10K RON', '10K-100K RON', '100K+ RON'],
                'holders': [125000, 85000, 45000, 18000, 3500, 850, 125],
                'total_balance': [45000, 420000, 2800000, 8500000, 15600000, 28400000, 45200000],
                'avg_balance': [0.36, 4.94, 62.22, 472.22, 4457.14, 33411.76, 361600]
            })
        elif query_key == 'wron_whale_tracking':
            return pd.DataFrame({
                'trader_address': [f'0x{i:040x}' for i in range(1, 16)],
                'total_volume_usd': np.random.uniform(500000, 5000000, 15),
                'trade_count': np.random.randint(25, 200, 15),
                'avg_trade_size_usd': np.random.uniform(10000, 50000, 15),
                'profit_loss_usd': np.random.uniform(-200000, 800000, 15),
                'first_trade_date': pd.date_range(end=datetime.now() - timedelta(days=30), periods=15, freq='D'),
                'last_trade_date': pd.date_range(end=datetime.now(), periods=15, freq='D')
            })
        elif query_key == 'wron_volume_liquidity':
            dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
            pairs = ['WRON/USDC', 'WRON/AXS', 'WRON/SLP', 'WRON/PIXEL']
            volume_data = []
            for date in dates:
                for pair in pairs:
                    base_volume = {'WRON/USDC': 8500000, 'WRON/AXS': 3200000, 'WRON/SLP': 1800000, 'WRON/PIXEL': 950000}[pair]
                    volume_data.append({
                        'date': date,
                        'pair': pair,
                        'volume_usd': base_volume * np.random.uniform(0.4, 1.8),
                        'liquidity_usd': base_volume * np.random.uniform(2.5, 4.2),
                        'trades': int(base_volume / np.random.uniform(800, 2000)),
                        'unique_traders': int(base_volume / np.random.uniform(5000, 12000))
                    })
            return pd.DataFrame(volume_data)
        elif query_key == 'wron_hourly_activity':
            return pd.DataFrame({
                'hour': range(24),
                'avg_volume_usd': [
                    2400000, 1800000, 1200000, 800000, 900000, 1400000,
                    2800000, 4200000, 5800000, 7200000, 8100000, 8800000,
                    9200000, 8600000, 8900000, 9500000, 8800000, 8200000,
                    7400000, 6200000, 5100000, 4200000, 3400000, 2900000
                ],
                'avg_trades': [
                    1200, 950, 680, 420, 480, 720,
                    1450, 2200, 3100, 3800, 4200, 4600,
                    4850, 4500, 4650, 4950, 4600, 4300,
                    3850, 3200, 2680, 2200, 1780, 1520
                ],
                'avg_unique_traders': [
                    450, 320, 180, 95, 125, 280,
                    580, 950, 1350, 1650, 1850, 2100,
                    2250, 2050, 2150, 2300, 2100, 1950,
                    1700, 1400, 1150, 850, 650, 520
                ]
            })
        elif query_key == 'wron_weekly_segmentation':
            weeks = pd.date_range(end=datetime.now(), periods=12, freq='W')
            return pd.DataFrame({
                'week': weeks,
                'retail_traders': np.random.randint(15000, 25000, 12),
                'small_whales': np.random.randint(800, 1500, 12),
                'large_whales': np.random.randint(50, 150, 12),
                'retail_volume_usd': np.random.uniform(25000000, 45000000, 12),
                'small_whale_volume_usd': np.random.uniform(35000000, 65000000, 12),
                'large_whale_volume_usd': np.random.uniform(45000000, 85000000, 12),
                'total_volume_usd': np.random.uniform(105000000, 195000000, 12)
            })
        else:
            return pd.DataFrame()

# Advanced Analytics Functions
class RoninAnalytics:
    """Advanced analytics calculations for Ronin ecosystem."""
    
    @staticmethod
    def calculate_network_health_score(daily_data, token_data, games_data):
        """Calculate comprehensive network health score."""
        score = 100
        
        if daily_data is not None and not daily_data.empty and len(daily_data) >= 7:
            recent_data = daily_data.tail(7)
            
            # Transaction throughput (25 points)
            avg_tx = recent_data['daily_transactions'].mean()
            if avg_tx < 500000:
                score -= 20
            elif avg_tx < 800000:
                score -= 10
            elif avg_tx < 900000:
                score -= 5
            
            # Network growth trend (25 points)
            tx_trend = (recent_data['daily_transactions'].iloc[-1] - recent_data['daily_transactions'].iloc[0]) / recent_data['daily_transactions'].iloc[0]
            if tx_trend < -0.3:
                score -= 25
            elif tx_trend < -0.15:
                score -= 15
            elif tx_trend < -0.05:
                score -= 8
            
            # User activity stability (25 points)
            user_volatility = recent_data['active_addresses'].std() / recent_data['active_addresses'].mean()
            if user_volatility > 0.3:
                score -= 25
            elif user_volatility > 0.2:
                score -= 15
            elif user_volatility > 0.1:
                score -= 8
            
            # Gas price stability (15 points)
            gas_volatility = recent_data['avg_gas_price_gwei'].std() / recent_data['avg_gas_price_gwei'].mean()
            if gas_volatility > 0.5:
                score -= 15
            elif gas_volatility > 0.3:
                score -= 8
        
        # Token performance impact (10 points)
        if token_data and token_data.get('price_change_7d_pct'):
            price_change = token_data['price_change_7d_pct']
            if price_change < -30:
                score -= 10
            elif price_change < -15:
                score -= 5
        
        return max(0, min(100, score))
    
    @staticmethod
    def calculate_game_dominance_index(games_data):
        """Calculate gaming ecosystem concentration."""
        if games_data is None or games_data.empty:
            return 0
        
        total_users = games_data['unique_users'].sum()
        user_shares = games_data['unique_users'] / total_users
        
        # Herfindahl-Hirschman Index for concentration
        hhi = (user_shares ** 2).sum()
        
        # Convert to 0-100 scale (higher = more concentrated)
        return min(100, hhi * 100)
    
    @staticmethod
    def calculate_retention_metrics(retention_data):
        """Calculate advanced retention metrics."""
        if retention_data is None or retention_data.empty:
            return {}
        
        # Group by project and calculate metrics
        metrics = {}
        for project in retention_data['project_name'].unique():
            project_data = retention_data[retention_data['project_name'] == project]
            
            if len(project_data) >= 4:
                metrics[project] = {
                    'avg_1w_retention': project_data['retention_rate_1w'].mean(),
                    'avg_4w_retention': project_data['retention_rate_4w'].mean(),
                    'retention_stability': 1 - (project_data['retention_rate_1w'].std() / project_data['retention_rate_1w'].mean()),
                    'user_growth_trend': (project_data['new_users'].iloc[-1] - project_data['new_users'].iloc[0]) / project_data['new_users'].iloc[0]
                }
        
        return metrics
    
    @staticmethod
    def calculate_whale_impact_score(whale_data, volume_data):
        """Calculate whale market impact."""
        if whale_data is None or whale_data.empty or volume_data is None or volume_data.empty:
            return 0
        
        total_whale_volume = whale_data['total_volume_usd'].sum()
        total_market_volume = volume_data['volume_usd'].sum() if 'volume_usd' in volume_data.columns else total_whale_volume * 2
        
        whale_dominance = min(100, (total_whale_volume / total_market_volume) * 100)
        
        # Factor in whale count and average size
        whale_count = len(whale_data)
        avg_whale_size = whale_data['total_volume_usd'].mean()
        
        # Risk score: higher concentration = higher risk
        concentration_risk = whale_dominance * (1 + (avg_whale_size / 1000000))
        
        return min(100, concentration_risk)

# Page configuration
st.set_page_config(
    page_title="Ronin Ecosystem Tracker",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced CSS styling with Ronin gaming theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;900&display=swap');
    
    .main {
        font-family: 'Inter', sans-serif;
        background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 50%, #16213e 100%);
    }
    
    .stRadio > div {
        display: flex;
        justify-content: center;
        margin-bottom: 30px;
        gap: 15px;
        flex-wrap: wrap;
    }
    
    .stRadio > div > label {
        font-size: 15px;
        font-weight: 600;
        color: #FFFFFF;
        background: linear-gradient(135deg, #FF6B35 0%, #F7931E 50%, #FFD700 100%);
        padding: 14px 28px;
        border-radius: 30px;
        border: 3px solid transparent;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        cursor: pointer;
        text-transform: uppercase;
        letter-spacing: 1px;
        box-shadow: 0 6px 20px rgba(255, 107, 53, 0.4);
        position: relative;
        overflow: hidden;
    }
    
    .stRadio > div > label:before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent);
        transition: left 0.5s;
    }
    
    .stRadio > div > label:hover {
        background: linear-gradient(135deg, #00D4FF 0%, #FF6B35 50%, #F7931E 100%);
        transform: translateY(-4px) scale(1.05);
        box-shadow: 0 12px 35px rgba(0, 212, 255, 0.5);
        border-color: #00D4FF;
    }
    
    .stRadio > div > label:hover:before {
        left: 100%;
    }
    
    .metric-card {
        background: linear-gradient(135deg, rgba(26, 26, 46, 0.95) 0%, rgba(22, 33, 62, 0.95) 100%);
        padding: 25px;
        border-radius: 20px;
        border: 2px solid rgba(255, 107, 53, 0.3);
        margin: 15px 0;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.4);
        backdrop-filter: blur(15px);
        transition: all 0.4s ease;
        position: relative;
        overflow: hidden;
    }
    
    .metric-card:before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, #FF6B35, #00D4FF, #FF6B35);
        transform: translateX(-100%);
        transition: transform 0.6s ease;
    }
    
    .metric-card:hover {
        border-color: #00D4FF;
        box-shadow: 0 15px 50px rgba(0, 212, 255, 0.3);
        transform: translateY(-3px);
    }
    
    .metric-card:hover:before {
        transform: translateX(0);
    }
    
    .health-score-excellent {
        color: #00FF88;
        font-weight: 700;
        text-shadow: 0 0 15px rgba(0, 255, 136, 0.6);
        animation: glow 2s ease-in-out infinite alternate;
    }
    
    .health-score-good {
        color: #4ECDC4;
        font-weight: 700;
        text-shadow: 0 0 10px rgba(78, 205, 196, 0.5);
    }
    
    .health-score-warning {
        color: #FFD700;
        font-weight: 700;
        text-shadow: 0 0 10px rgba(255, 215, 0, 0.5);
    }

# === MAIN APP LOGIC ===

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
games_daily = fetcher.fetch_dune_query('games_daily_activity')
ronin_daily = fetcher.fetch_dune_query('ronin_daily_activity')
activation_retention = fetcher.fetch_dune_query('user_activation_retention')
ron_holders = fetcher.fetch_dune_query('ron_current_holders')
ron_segmented_holders = fetcher.fetch_dune_query('ron_segmented_holders')
wron_katana_pairs = fetcher.fetch_dune_query('wron_katana_pairs')
wron_whale_tracking = fetcher.fetch_dune_query('wron_whale_tracking')
wron_volume_liquidity = fetcher.fetch_dune_query('wron_volume_liquidity')
wron_hourly_activity = fetcher.fetch_dune_query('wron_hourly_activity')
wron_weekly_segmentation = fetcher.fetch_dune_query('wron_weekly_segmentation')

# === NETWORK OVERVIEW SECTION ===
if section == "Network Overview":
    st.markdown("## 🌐 Network Health & Performance Dashboard")

    # Network Health Score Calculation
    network_health_score = RoninAnalytics.calculate_network_health_score(ronin_daily, coingecko_data, games_overall)

    # Key Metrics Row
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        health_status = "Excellent" if network_health_score >= 85 else "Good" if network_health_score >= 70 else "Warning" if network_health_score >= 50 else "Critical"
        st.metric("🏥 Network Health", f"{network_health_score}/100", delta=health_status)
    with col2:
        latest_tx = ronin_daily['daily_transactions'].iloc[-1] if ronin_daily is not None and not ronin_daily.empty else 1000000
        st.metric("📊 Daily Transactions", f"{latest_tx:,.0f}", delta="24h volume")
    with col3:
        st.metric("💎 RON Price", f"${coingecko_data['price_usd']:.3f}", delta=f"{coingecko_data['price_change_24h_pct']:.1f}%")
    with col4:
        latest_users = ronin_daily['active_addresses'].iloc[-1] if ronin_daily is not None and not ronin_daily.empty else 200000
        st.metric("👥 Active Addresses", f"{latest_users:,.0f}", delta="24h unique")
    with col5:
        market_cap_b = coingecko_data['market_cap_usd'] / 1e9 if coingecko_data else 0.7
        st.metric("🏦 Market Cap", f"${market_cap_b:.2f}B", delta=f"Rank #{coingecko_data.get('market_cap_rank', 85)}")

    st.markdown("---")

    # Network Activity Visualization
    col1, col2 = st.columns(2)
    with col1:
        if ronin_daily is not None and not ronin_daily.empty:
            ronin_daily['date'] = pd.to_datetime(ronin_daily['date'])
            fig_network = make_subplots(
                rows=2, cols=1,
                subplot_titles=("Daily Transaction Volume", "Active Addresses & Gas Prices"),
                vertical_spacing=0.1
            )
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

        if ron_segmented_holders is not None and not ron_segmented_holders.empty:
            fig_holders = px.pie(
                ron_segmented_holders,
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
        total_gaming_users = games_overall['unique_users'].sum()
        total_gaming_tx = games_overall['total_transactions'].sum()
        top_game = games_overall.iloc[0]['project_name'] if len(games_overall) > 0 else "Axie Infinity"
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("🎮 Total Players", f"{total_gaming_users:,}")
        col2.metric("🕹️ Total Game Transactions", f"{total_gaming_tx:,}")
        col3.metric("🏆 Top Game", top_game)
        col4.metric("🧩 Games Tracked", f"{len(games_overall):,}")

        st.markdown("---")
        fig_games = px.bar(
            games_overall,
            x='project_name',
            y='unique_users',
            color='project_name',
            title="Unique Users by Game",
            labels={'unique_users': 'Unique Users', 'project_name': 'Game'}
        )
        st.plotly_chart(fig_games, use_container_width=True)

        if games_daily is not None and not games_daily.empty:
            games_daily['date'] = pd.to_datetime(games_daily['date'])
            fig_daily = px.line(
                games_daily,
                x='date',
                y='daily_active_users',
                color='project_name',
                title="Daily Active Users by Game"
            )
            st.plotly_chart(fig_daily, use_container_width=True)

        if activation_retention is not None and not activation_retention.empty:
            retention_metrics = RoninAnalytics.calculate_retention_metrics(activation_retention)
            st.markdown("### 📈 Retention Metrics")
            for project, metrics in retention_metrics.items():
                st.markdown(f"**{project}**")
                st.write(metrics)

# === TOKEN INTELLIGENCE SECTION ===
elif section == "Token Intelligence":
    st.markdown("## 💰 Token Intelligence & Whale Tracking")
    col1, col2, col3 = st.columns(3)
    col1.metric("RON Price", f"${coingecko_data['price_usd']:.3f}")
    col2.metric("Market Cap", f"${coingecko_data['market_cap_usd']:,}")
    col3.metric("24h Volume", f"${coingecko_data['volume_24h_usd']:,}")

    st.markdown("---")
    if wron_whale_tracking is not None and not wron_whale_tracking.empty:
        st.markdown("### 🐋 Top WRON Whales (Last 30 Days)")
        st.dataframe(wron_whale_tracking)

        whale_impact_score = RoninAnalytics.calculate_whale_impact_score(wron_whale_tracking, wron_volume_liquidity)
        st.metric("Whale Impact Score", f"{whale_impact_score:.1f}/100")

    if wron_volume_liquidity is not None and not wron_volume_liquidity.empty:
        fig_liquidity = px.line(
            wron_volume_liquidity,
            x='date',
            y='volume_usd',
            color='pair',
            title="WRON Trading Volume by Pair"
        )
        st.plotly_chart(fig_liquidity, use_container_width=True)

    if wron_katana_pairs is not None and not wron_katana_pairs.empty:
        st.markdown("### 🧮 WRON Active Trade Pairs on Katana DEX")
        st.dataframe(wron_katana_pairs)

# === USER ANALYTICS SECTION ===
elif section == "User Analytics":
    st.markdown("## 👥 User Segmentation & Retention Analysis")
    if ron_segmented_holders is not None and not ron_segmented_holders.empty:
        st.markdown("### 🧑‍💻 RON Holder Segmentation")
        st.dataframe(ron_segmented_holders)

    if wron_weekly_segmentation is not None and not wron_weekly_segmentation.empty:
        st.markdown("### 📊 WRON Weekly User Segmentation")
        fig_weekly = px.bar(
            wron_weekly_segmentation,
            x='week',
            y=['retail_traders', 'small_whales', 'large_whales'],
            title="WRON User Segmentation Over Time"
        )
        st.plotly_chart(fig_weekly, use_container_width=True)

    if activation_retention is not None and not activation_retention.empty:
        st.markdown("### 🔄 Weekly Activation & Retention by Game")
        fig_retention = px.line(
            activation_retention,
            x='week',
            y='retention_rate_1w',
            color='project_name',
            title="1-Week Retention Rate by Game"
        )
        st.plotly_chart(fig_retention, use_container_width=True)

# Footer
st.markdown("""
---
<div style="text-align:center; color:#888; font-size:0.9em;">
    Built by Analytics Team • Powered by Ronin, Dune, CoinGecko • 2025
</div>
""", unsafe_allow_html=True)