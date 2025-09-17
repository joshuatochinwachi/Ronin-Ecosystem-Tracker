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
    
    .health-score-critical {
        color: #FF6B6B;
        font-weight: 700;
        text-shadow: 0 0 15px rgba(255, 107, 107, 0.6);
        animation: pulse 1.5s ease-in-out infinite;
    }
    
    @keyframes glow {
        from { text-shadow: 0 0 15px rgba(0, 255, 136, 0.6); }
        to { text-shadow: 0 0 25px rgba(0, 255, 136, 0.8), 0 0 35px rgba(0, 255, 136, 0.4); }
    }
    
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    
    .insight-box {
        background: linear-gradient(135deg, rgba(255, 107, 53, 0.1) 0%, rgba(0, 212, 255, 0.1) 100%);
        border-left: 5px solid #00D4FF;
        padding: 25px;
        border-radius: 15px;
        margin: 20px 0;
        font-style: italic;
        position: relative;
        overflow: hidden;
    }
    
    .insight-box:before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: linear-gradient(45deg, transparent 30%, rgba(0, 212, 255, 0.05) 50%, transparent 70%);
        transform: translateX(-100%);
        transition: transform 1s ease;
    }
    
    .insight-box:hover:before {
        transform: translateX(100%);
    }
    
    .warning-box {
        background: linear-gradient(135deg, rgba(255, 181, 71, 0.15) 0%, rgba(255, 107, 107, 0.15) 100%);
        border-left: 5px solid #FFB347;
        padding: 20px;
        border-radius: 15px;
        margin: 15px 0;
        border: 1px solid rgba(255, 179, 71, 0.3);
    }
    
    .gaming-card {
        background: linear-gradient(135deg, rgba(255, 107, 53, 0.1) 0%, rgba(247, 147, 30, 0.1) 100%);
        border: 2px solid rgba(255, 107, 53, 0.3);
        padding: 20px;
        border-radius: 15px;
        margin: 10px 0;
        transition: all 0.3s ease;
    }
    
    .gaming-card:hover {
        border-color: #FF6B35;
        box-shadow: 0 8px 25px rgba(255, 107, 53, 0.2);
        transform: translateY(-2px);
    }
    
    .whale-card {
        background: linear-gradient(135deg, rgba(0, 212, 255, 0.1) 0%, rgba(78, 205, 196, 0.1) 100%);
        border: 2px solid rgba(0, 212, 255, 0.3);
        padding: 20px;
        border-radius: 15px;
        margin: 10px 0;
        transition: all 0.3s ease;
    }
    
    .whale-card:hover {
        border-color: #00D4FF;
        box-shadow: 0 8px 25px rgba(0, 212, 255, 0.2);
        transform: translateY(-2px);
    }
    
    .dataframe {
        border-radius: 15px !important;
        overflow: hidden !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2) !important;
        border: 1px solid rgba(255, 107, 53, 0.2) !important;
    }
    
    .stDataFrame > div {
        border-radius: 15px;
        overflow: hidden;
    }
    
    .status-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 8px;
        animation: statusPulse 2s infinite;
    }
    
    .status-online { background-color: #00FF88; }
    .status-warning { background-color: #FFD700; }
    .status-critical { background-color: #FF6B6B; }
    
    @keyframes statusPulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.6; }
    }
</style>
""", unsafe_allow_html=True)

# Initialize data fetcher
@st.cache_resource
def get_data_fetcher():
    return RoninDataFetcher()

fetcher = get_data_fetcher()
analytics = RoninAnalytics()

# Sidebar
with st.sidebar:
    st.markdown("""
    <div style="background: linear-gradient(135deg, #FF6B35 0%, #F7931E 50%, #FFD700 100%); 
                padding: 25px; border-radius: 20px; margin-bottom: 30px; text-align: center;
                box-shadow: 0 10px 30px rgba(255, 107, 53, 0.4);">
        <h2 style="color: #FFFFFF; margin: 0; font-weight: 900; font-size: 1.8em;">⚡ Ronin Tracker</h2>
        <p style="color: #E0E0E0; margin: 8px 0 0 0; font-size: 1em; font-weight: 500;">Gaming Economy Intelligence</p>
        <div class="status-indicator status-online"></div>
        <span style="color: #E0E0E0; font-size: 0.85em;">Live Data Active</span>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    ### 🎮 Ronin Blockchain Overview
    
    Ronin is a **gaming-focused sidechain** built by Sky Mavis for Axie Infinity and the broader Web3 gaming ecosystem.
    
    **🚀 Key Features:**
    - ⚡ **Lightning Fast:** Sub-second transactions
    - 💰 **Ultra Low Fees:** Minimal transaction costs
    - 🎯 **Gaming-Optimized:** Built specifically for blockchain games
    - 🌉 **Bridge Connected:** Seamless Ethereum integration
    - 🏛️ **PoA Consensus:** Proof of Authority for speed & efficiency
    
    ---
    
    ### 📊 Intelligence Dashboard Tracks:
    
    **🌐 Network Health & Performance**
    - Real-time transaction throughput monitoring
    - Network congestion & performance analysis
    - Bridge activity & cross-chain flows
    - Advanced health scoring algorithms
    
    **🎮 Gaming Economy Analytics**
    - Daily/monthly active players across all games
    - User spending patterns by game category
    - Player retention & lifecycle analysis
    - Game performance rankings & dominance
    
    **💎 Token Intelligence & DeFi**
    - RON/WRON flow distribution analysis
    - Whale wallet tracking & market impact
    - DeFi liquidity flows on Katana DEX
    - Trading pattern & volume analysis
    
    **👥 User Behavior & Segmentation**
    - Advanced wallet classification system
    - Spending pattern analysis by user type
    - Gaming vs DeFi user behavior insights
    - Retention & activation trend monitoring
    
    ---
    
    **💡 Key Insight:** Ronin represents the future of gaming-DeFi convergence, where gaming activity directly drives token utility, liquidity, and ecosystem growth. This creates unique economic dynamics unlike traditional blockchain networks.
    
    **🎯 Market Position:** As the leading gaming blockchain, Ronin processes millions of gaming transactions daily, supporting a multi-billion dollar gaming economy with innovative tokenomics.
    """)
    
    # Real-time status indicators
    st.markdown("""
    ### 🔄 Data Sources & Status
    
    <div style="background: rgba(26, 26, 46, 0.8); padding: 15px; border-radius: 10px; margin: 15px 0;">
        <div style="display: flex; align-items: center; margin-bottom: 8px;">
            <div class="status-indicator status-online"></div>
            <span style="color: #00FF88;">CoinGecko Pro API</span>
        </div>
        <div style="display: flex; align-items: center; margin-bottom: 8px;">
            <div class="status-indicator status-online"></div>
            <span style="color: #00FF88;">Dune Analytics API</span>
        </div>
        <div style="display: flex; align-items: center;">
            <div class="status-indicator status-warning"></div>
            <span style="color: #FFD700;">Ronin Bridge Monitor</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="background: linear-gradient(90deg, #00D4FF 0%, #FF6B35 100%); 
                padding: 18px; border-radius: 15px; margin-top: 25px; text-align: center;">
        <p style="color: white; margin: 0; font-weight: 600; font-size: 0.95em;">🔄 Data Updates</p>
        <p style="color: #E0E0E0; margin: 5px 0 0 0; font-size: 0.8em;">Every 24 hours | Cache Optimized</p>
        <p style="color: #B0B0B0; margin: 3px 0 0 0; font-size: 0.75em;">Next refresh: Tomorrow</p>
    </div>
    """, unsafe_allow_html=True)

# Enhanced main header with gaming aesthetics
st.markdown("""
<div style="background: linear-gradient(135deg, #00D4FF 0%, #FF6B35 20%, #F7931E 40%, #FFD700 60%, #FF1744 80%, #8A4AF3 100%); 
           padding: 40px; border-radius: 25px; margin-bottom: 40px; text-align: center;
           box-shadow: 0 15px 50px rgba(255, 107, 53, 0.5), 0 0 100px rgba(0, 212, 255, 0.3);
           position: relative; overflow: hidden;">
    <div style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; 
                background: radial-gradient(circle at 30% 30%, rgba(255,255,255,0.1) 0%, transparent 50%);"></div>
    <h1 style="color: white; margin: 0; font-size: 3.5em; font-weight: 900; 
               text-shadow: 3px 3px 12px rgba(0,0,0,0.6);
               background: linear-gradient(45deg, #FFFFFF, #FFD700, #FFFFFF);
               background-clip: text; -webkit-background-clip: text; -webkit-text-fill-color: transparent;
               position: relative; z-index: 1;">
        ⚡ Ronin Ecosystem Tracker
    </h1>
    <p style="color: #E0E0E0; margin: 20px 0 10px 0; font-size: 1.4em; font-weight: 600;
               text-shadow: 2px 2px 8px rgba(0,0,0,0.4); position: relative; z-index: 1;">
        Advanced Gaming Economy & Network Intelligence Platform
    </p>
    <p style="color: #C0C0C0; margin: 0; font-size: 1.1em; font-weight: 400;
               text-shadow: 1px 1px 4px rgba(0,0,0,0.3); position: relative; z-index: 1;">
        Real-time monitoring • Gaming analytics • Token intelligence • User insights • DeFi flows
    </p>
</div>
""", unsafe_allow_html=True)

# Enhanced navigation with gaming theme
section = st.radio(
    "",
    ["🌐 Network Overview", "🎮 Gaming Economy", "💎 Token Intelligence", "👥 User Analytics"],
    horizontal=True,
    key="nav_radio"
)

# Load all data with loading states
with st.spinner("Loading Ronin ecosystem data..."):
    coingecko_data = fetcher.fetch_coingecko_data()
    games_overall = fetcher.fetch_dune_query('games_overall_activity')
    games_daily = fetcher.fetch_dune_query('games_daily_activity')
    ronin_daily = fetcher.fetch_dune_query('ronin_daily_activity')
    retention_data = fetcher.fetch_dune_query('user_activation_retention')
    ron_holders = fetcher.fetch_dune_query('ron_segmented_holders')
    whale_data = fetcher.fetch_dune_query('wron_whale_tracking')
    volume_data = fetcher.fetch_dune_query('wron_volume_liquidity')
    hourly_data = fetcher.fetch_dune_query('wron_hourly_activity')
    weekly_data = fetcher.fetch_dune_query('wron_weekly_segmentation')

# === NETWORK OVERVIEW SECTION ===
if section == "🌐 Network Overview":
    st.markdown("## 🌐 Network Health & Performance Dashboard")
    
    # Calculate advanced metrics
    network_health_score = analytics.calculate_network_health_score(ronin_daily, coingecko_data, games_overall)
    game_dominance = analytics.calculate_game_dominance_index(games_overall)
    whale_impact = analytics.calculate_whale_impact_score(whale_data, volume_data)
    
    # Enhanced key metrics with better styling
    st.markdown("### 📊 Real-time Network Intelligence")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        health_status = ("Excellent" if network_health_score >= 85 else 
                        "Good" if network_health_score >= 70 else 
                        "Warning" if network_health_score >= 50 else "Critical")
        health_color = ("health-score-excellent" if network_health_score >= 85 else 
                       "health-score-good" if network_health_score >= 70 else 
                       "health-score-warning" if network_health_score >= 50 else "health-score-critical")
        
        st.markdown(f"""
        <div class="metric-card">
            <h4 style="color: #00D4FF; margin: 0 0 10px 0;">🏥 Network Health</h4>
            <h2 style="color: white; margin: 0;">{network_health_score}/100</h2>
            <p class="{health_color}" style="margin: 5px 0 0 0; font-size: 1.1em;">{health_status}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        if ronin_daily is not None and not ronin_daily.empty:
            latest_tx = ronin_daily['daily_transactions'].iloc[-1] if len(ronin_daily) > 0 else 1000000
            tx_change = ((ronin_daily['daily_transactions'].iloc[-1] - ronin_daily['daily_transactions'].iloc[-2]) / 
                        ronin_daily['daily_transactions'].iloc[-2] * 100) if len(ronin_daily) > 1 else 0
        else:
            latest_tx, tx_change = 1000000, 2.5
            
        st.markdown(f"""
        <div class="metric-card">
            <h4 style="color: #00D4FF; margin: 0 0 10px 0;">📊 Daily Transactions</h4>
            <h2 style="color: white; margin: 0;">{latest_tx:,.0f}</h2>
            <p style="color: {'#00FF88' if tx_change > 0 else '#FF6B6B'}; margin: 5px 0 0 0; font-size: 1.1em;">
                {tx_change:+.1f}% vs yesterday
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        if coingecko_data:
            price = coingecko_data['price_usd']
            price_change = coingecko_data['price_change_24h_pct']
        else:
            price, price_change = 2.150, -2.5
            
        st.markdown(f"""
        <div class="metric-card">
            <h4 style="color: #00D4FF; margin: 0 0 10px 0;">💎 RON Price</h4>
            <h2 style="color: white; margin: 0;">${price:.3f}</h2>
            <p style="color: {'#00FF88' if price_change > 0 else '#FF6B6B'}; margin: 5px 0 0 0; font-size: 1.1em;">
                {price_change:+.1f}% 24h
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        if ronin_daily is not None and not ronin_daily.empty:
            latest_users = ronin_daily['active_addresses'].iloc[-1] if len(ronin_daily) > 0 else 200000
        else:
            latest_users = 200000
            
        st.markdown(f"""
        <div class="metric-card">
            <h4 style="color: #00D4FF; margin: 0 0 10px 0;">👥 Daily Active Users</h4>
            <h2 style="color: white; margin: 0;">{latest_users:,.0f}</h2>
            <p style="color: #4ECDC4; margin: 5px 0 0 0; font-size: 1.1em;">Unique addresses</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        dominance_status = ("High" if game_dominance > 70 else "Medium" if game_dominance > 40 else "Low")
        dominance_color = ("#FFB347" if game_dominance > 70 else "#4ECDC4" if game_dominance > 40 else "#00FF88")
        
        st.markdown(f"""
        <div class="metric-card">
            <h4 style="color: #00D4FF; margin: 0 0 10px 0;">🎮 Game Concentration</h4>
            <h2 style="color: white; margin: 0;">{game_dominance:.1f}</h2>
            <p style="color: {dominance_color}; margin: 5px 0 0 0; font-size: 1.1em;">{dominance_status} dominance</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Advanced Network Visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        # Multi-metric network performance chart
        if ronin_daily is not None and not ronin_daily.empty:
            ronin_daily_clean = ronin_daily.copy()
            if 'date' in ronin_daily_clean.columns:
                ronin_daily_clean['date'] = pd.to_datetime(ronin_daily_clean['date'])
            
            fig_network = make_subplots(
                rows=3, cols=1,
                subplot_titles=(
                    "📊 Daily Transaction Volume", 
                    "👥 Active User Growth", 
                    "⛽ Gas Price & Network Load"
                ),
                vertical_spacing=0.08,
                row_heights=[0.4, 0.3, 0.3]
            )
            
            # Transaction volume with trend
            fig_network.add_trace(
                go.Scatter(
                    x=ronin_daily_clean['date'],
                    y=ronin_daily_clean['daily_transactions'],
                    mode='lines+markers',
                    name='Daily Transactions',
                    line=dict(color='#FF6B35', width=4),
                    fill='tonexty',
                    fillcolor='rgba(255, 107, 53, 0.2)',
                    hovertemplate='<b>Transactions</b><br>Date: %{x}<br>Volume: %{y:,.0f}<extra></extra>'
                ),
                row=1, col=1
            )
            
            # Add trend line
            if len(ronin_daily_clean) > 1:
                x_numeric = np.arange(len(ronin_daily_clean))
                z = np.polyfit(x_numeric, ronin_daily_clean['daily_transactions'], 1)
                trend_line = np.poly1d(z)(x_numeric)
                
                fig_network.add_trace(
                    go.Scatter(
                        x=ronin_daily_clean['date'],
                        y=trend_line,
                        mode='lines',
                        name='Trend',
                        line=dict(color='#FFD700', width=2, dash='dash'),
                        opacity=0.8
                    ),
                    row=1, col=1
                )
            
            # Active addresses
            fig_network.add_trace(
                go.Scatter(
                    x=ronin_daily_clean['date'],
                    y=ronin_daily_clean['active_addresses'],
                    mode='lines+markers',
                    name='Active Addresses',
                    line=dict(color='#00D4FF', width=3),
                    marker=dict(size=6),
                    hovertemplate='<b>Active Users</b><br>Date: %{x}<br>Count: %{y:,.0f}<extra></extra>'
                ),
                row=2, col=1
            )
            
            # Gas prices
            fig_network.add_trace(
                go.Scatter(
                    x=ronin_daily_clean['date'],
                    y=ronin_daily_clean['avg_gas_price_gwei'],
                    mode='lines+markers',
                    name='Avg Gas Price (GWEI)',
                    line=dict(color='#4ECDC4', width=3),
                    hovertemplate='<b>Gas Price</b><br>Date: %{x}<br>Price: %{y:.3f} GWEI<extra></extra>'
                ),
                row=3, col=1
            )
            
            fig_network.update_layout(
                height=800,
                showlegend=False,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white',
                title={
                    'text': "🌐 Comprehensive Network Performance Analysis",
                    'font': {'size': 18, 'color': 'white'},
                    'x': 0.5
                }
            )
            
            # Update axes
            fig_network.update_yaxes(title_text="Transactions", row=1, col=1)
            fig_network.update_yaxes(title_text="Users", row=2, col=1)
            fig_network.update_yaxes(title_text="GWEI", row=3, col=1)
            fig_network.update_xaxes(title_text="Date", row=3, col=1)
            
            st.plotly_chart(fig_network, use_container_width=True)
        else:
            st.info("📊 Network activity data temporarily unavailable")
    
    with col2:
        # Network health gauge with detailed breakdown
        fig_gauge = go.Figure()
        
        fig_gauge.add_trace(go.Indicator(
            mode="gauge+number+delta",
            value=network_health_score,
            domain={'x': [0, 1], 'y': [0.3, 1]},
            title={'text': "🏥 Network Health Score", 'font': {'size': 20, 'color': 'white'}},
            delta={'reference': 85, 'position': "top"},
            gauge={
                'axis': {'range': [None, 100], 'tickcolor': 'white'},
                'bar': {'color': "#FF6B35", 'thickness': 0.3},
                'steps': [
                    {'range': [0, 50], 'color': "rgba(255, 107, 107, 0.3)"},
                    {'range': [50, 70], 'color': "rgba(255, 215, 0, 0.3)"},
                    {'range': [70, 85], 'color': "rgba(78, 205, 196, 0.3)"},
                    {'range': [85, 100], 'color': "rgba(0, 255, 136, 0.3)"}
                ],
                'threshold': {
                    'line': {'color': "#00D4FF", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        
        # Add breakdown text
        breakdown_text = f"""
        <b style='color: #00D4FF'>Health Breakdown:</b><br>
        Transaction Throughput: {'🟢' if network_health_score > 80 else '🟡' if network_health_score > 60 else '🔴'}<br>
        Network Growth: {'🟢' if network_health_score > 75 else '🟡' if network_health_score > 55 else '🔴'}<br>
        User Activity: {'🟢' if network_health_score > 70 else '🟡' if network_health_score > 50 else '🔴'}<br>
        Gas Stability: {'🟢' if network_health_score > 85 else '🟡' if network_health_score > 65 else '🔴'}
        """
        
        fig_gauge.add_annotation(
            text=breakdown_text,
            x=0.5, y=0.15,
            showarrow=False,
            font=dict(size=12, color='white'),
            align='center'
        )
        
        fig_gauge.update_layout(
            height=500,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white'
        )
        
        st.plotly_chart(fig_gauge, use_container_width=True)
        
        # Token holder distribution with enhanced visualization
        if ron_holders is not None and not ron_holders.empty:
            colors = ['#FF6B35', '#F7931E', '#FFD700', '#00D4FF', '#4ECDC4', '#45B7D1', '#8A4AF3']
            
            fig_holders = go.Figure(data=[go.Pie(
                labels=ron_holders['balance_range'],
                values=ron_holders['holders'],
                hole=.4,
                marker_colors=colors,
                textinfo='label+percent',
                textposition='auto',
                hovertemplate='<b>%{label}</b><br>' +
                             'Holders: %{value:,.0f}<br>' +
                             'Percentage: %{percent}<br>' +
                             '<extra></extra>'
            )])
            
            fig_holders.update_layout(
                title={
                    'text': "💰 RON Holder Distribution",
                    'font': {'size': 16, 'color': 'white'},
                    'x': 0.5
                },
                height=400,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white',
                showlegend=True,
                legend=dict(
                    orientation="v",
                    yanchor="middle",
                    y=0.5,
                    xanchor="left",
                    x=1.05
                )
            )
            
            st.plotly_chart(fig_holders, use_container_width=True)

    # Network insights and alerts
    st.markdown("### 🎯 Network Intelligence & Market Insights")
    
    insights = []
    
    # Generate dynamic insights
    if network_health_score >= 85:
        insights.append("✅ **Excellent Network Performance**: All systems operating at peak efficiency with strong user growth and stable gas prices.")
    elif network_health_score >= 70:
        insights.append("✅ **Good Network Health**: Network performing well with minor optimization opportunities.")
    elif network_health_score >= 50:
        insights.append("⚠️ **Network Optimization Needed**: Some performance metrics showing degradation - monitoring recommended.")
    else:
        insights.append("🚨 **Critical Network Issues Detected**: Multiple performance indicators below optimal thresholds.")
    
    if game_dominance > 75:
        insights.append(f"📊 **High Gaming Concentration**: Top games control {game_dominance:.1f}% of ecosystem activity - diversification opportunity exists.")
    elif game_dominance < 40:
        insights.append(f"🎮 **Healthy Game Ecosystem**: Well-distributed gaming activity across multiple titles ({game_dominance:.1f}% concentration).")
    
    if whale_impact > 60:
        insights.append(f"🐋 **High Whale Market Impact**: Large traders significantly influence market dynamics ({whale_impact:.1f}% impact score).")
    
    if ronin_daily is not None and not ronin_daily.empty and len(ronin_daily) > 7:
        recent_growth = ((ronin_daily['daily_transactions'].tail(7).mean() - 
                         ronin_daily['daily_transactions'].head(7).mean()) / 
                         ronin_daily['daily_transactions'].head(7).mean() * 100)
        
        if recent_growth > 10:
            insights.append(f"📈 **Strong Network Growth**: Transaction volume up {recent_growth:.1f}% over the past week.")
        elif recent_growth < -10:
            insights.append(f"📉 **Network Activity Declining**: Transaction volume down {abs(recent_growth):.1f}% over the past week.")
    
    # Display insights
    for insight in insights:
        st.markdown(f'<div class="insight-box">{insight}</div>', unsafe_allow_html=True)

# === GAMING ECONOMY SECTION ===
elif section == "🎮 Gaming Economy":
    st.markdown("## 🎮 Gaming Economy & Player Analytics Dashboard")
    
    # Calculate gaming metrics
    retention_metrics = analytics.calculate_retention_metrics(retention_data)
    
    if games_overall is not None and not games_overall.empty:
        total_gaming_users = games_overall['unique_users'].sum()
        total_gaming_tx = games_overall['total_transactions'].sum()
        top_game = games_overall.iloc[0]['project_name'] if len(games_overall) > 0 else "Axie Infinity"
        top_game_users = games_overall.iloc[0]['unique_users'] if len(games_overall) > 0 else 2800000
        
        # Gaming Economy Metrics
        st.markdown("### 🎮 Gaming Ecosystem Overview")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card gaming-card">
                <h4 style="color: #FF6B35; margin: 0 0 10px 0;">🎮 Total Gamers</h4>
                <h2 style="color: white; margin: 0;">{total_gaming_users:,.0f}</h2>
                <p style="color: #F7931E; margin: 5px 0 0 0; font-size: 1.1em;">Unique players</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card gaming-card">
                <h4 style="color: #FF6B35; margin: 0 0 10px 0;">⚡ Gaming Transactions</h4>
                <h2 style="color: white; margin: 0;">{total_gaming_tx/1e6:.1f}M</h2>
                <p style="color: #F7931E; margin: 5px 0 0 0; font-size: 1.1em;">All-time total</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card gaming-card">
                <h4 style="color: #FF6B35; margin: 0 0 10px 0;">👑 Leading Game</h4>
                <h2 style="color: white; margin: 0; font-size: 1.5em;">{top_game}</h2>
                <p style="color: #F7931E; margin: 5px 0 0 0; font-size: 1.1em;">{top_game_users/1e6:.1f}M users</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            game_count = len(games_overall)
            market_share_top3 = (games_overall.head(3)['unique_users'].sum() / total_gaming_users * 100) if len(games_overall) >= 3 else 100
            
            st.markdown(f"""
            <div class="metric-card gaming-card">
                <h4 style="color: #FF6B35; margin: 0 0 10px 0;">🏆 Active Games</h4>
                <h2 style="color: white; margin: 0;">{game_count}</h2>
                <p style="color: #F7931E; margin: 5px 0 0 0; font-size: 1.1em;">Major titles tracked</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col5:
            avg_retention = np.mean([metrics.get('avg_1w_retention', 0) for metrics in retention_metrics.values()]) if retention_metrics else 0.45
            
            st.markdown(f"""
            <div class="metric-card gaming-card">
                <h4 style="color: #FF6B35; margin: 0 0 10px 0;">📈 Avg Retention</h4>
                <h2 style="color: white; margin: 0;">{avg_retention*100:.1f}%</h2>
                <p style="color: #F7931E; margin: 5px 0 0 0; font-size: 1.1em;">1-week retention</p>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Gaming Analytics Visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        # Game ecosystem breakdown with enhanced visualization
        if games_overall is not None and not games_overall.empty:
            # Create a comprehensive game analysis chart
            fig_games = make_subplots(
                rows=2, cols=2,
                subplot_titles=(
                    "🎮 User Distribution by Game", 
                    "⚡ Transaction Volume Analysis",
                    "💰 Revenue Potential Index", 
                    "⛽ Gas Efficiency Comparison"
                ),
                specs=[[{"type": "pie"}, {"type": "bar"}],
                       [{"type": "scatter"}, {"type": "bar"}]],
                vertical_spacing=0.12,
                horizontal_spacing=0.1
            )
            
            colors = ['#FF6B35', '#F7931E', '#FFD700', '#00D4FF', '#4ECDC4', '#45B7D1', '#8A4AF3', '#FF6B6B']
            
            # Pie chart for user distribution
            fig_games.add_trace(
                go.Pie(
                    labels=games_overall['project_name'],
                    values=games_overall['unique_users'],
                    marker_colors=colors[:len(games_overall)],
                    textinfo='label+percent',
                    hovertemplate='<b>%{label}</b><br>Users: %{value:,.0f}<br>Share: %{percent}<extra></extra>'
                ),
                row=1, col=1
            )
            
            # Transaction volume bar chart
            fig_games.add_trace(
                go.Bar(
                    x=games_overall['project_name'],
                    y=games_overall['total_transactions'],
                    marker_color=colors[:len(games_overall)],
                    name='Transactions',
                    hovertemplate='<b>%{x}</b><br>Transactions: %{y:,.0f}<extra></extra>'
                ),
                row=1, col=2
            )
            
            # Revenue potential (transactions per user vs total users)
            games_overall['tx_per_user'] = games_overall['total_transactions'] / games_overall['unique_users']
            fig_games.add_trace(
                go.Scatter(
                    x=games_overall['unique_users'],
                    y=games_overall['tx_per_user'],
                    mode='markers+text',
                    marker=dict(
                        size=games_overall['total_transactions'] / 100000,
                        color=colors[:len(games_overall)],
                        sizemode='area',
                        sizeref=2.*max(games_overall['total_transactions'] / 100000)/(40.**2),
                        sizemin=4
                    ),
                    text=games_overall['project_name'],
                    textposition="top center",
                    hovertemplate='<b>%{text}</b><br>Users: %{x:,.0f}<br>Tx/User: %{y:.1f}<extra></extra>',
                    name='Games'
                ),
                row=2, col=1
            )
            
            # Gas efficiency
            if 'avg_gas_per_tx' in games_overall.columns:
                fig_games.add_trace(
                    go.Bar(
                        x=games_overall['project_name'],
                        y=games_overall['avg_gas_per_tx'],
                        marker_color=colors[:len(games_overall)],
                        name='Avg Gas/Tx',
                        hovertemplate='<b>%{x}</b><br>Gas/Tx: %{y:,.0f}<extra></extra>'
                    ),
                    row=2, col=2
                )
            
            fig_games.update_layout(
                height=700,
                showlegend=False,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white',
                title={
                    'text': "🎮 Comprehensive Gaming Ecosystem Analysis",
                    'font': {'size': 18, 'color': 'white'},
                    'x': 0.5
                }
            )
            
            # Update axes labels
            fig_games.update_xaxes(title_text="Unique Users", row=2, col=1)
            fig_games.update_yaxes(title_text="Tx per User", row=2, col=1)
            fig_games.update_yaxes(title_text="Transactions", row=1, col=2)
            fig_games.update_yaxes(title_text="Gas per Tx", row=2, col=2)
            
            st.plotly_chart(fig_games, use_container_width=True)
    
    with col2:
        # Player retention and lifecycle analysis
        if retention_data is not None and not retention_data.empty:
            # Process retention data for visualization
            retention_summary = []
            for project in retention_data['project_name'].unique():
                project_data = retention_data[retention_data['project_name'] == project]
                
                if len(project_data) > 0:
                    retention_summary.append({
                        'Game': project,
                        '1W Retention': project_data['retention_rate_1w'].mean(),
                        '4W Retention': project_data['retention_rate_4w'].mean(),
                        'New Users (Latest)': project_data['new_users'].iloc[-1] if len(project_data) > 0 else 0,
                        'Retention Trend': 'Improving' if len(project_data) > 1 and project_data['retention_rate_1w'].iloc[-1] > project_data['retention_rate_1w'].iloc[0] else 'Stable'
                    })
            
            if retention_summary:
                retention_df = pd.DataFrame(retention_summary)
                
                # Create retention comparison chart
                fig_retention = go.Figure()
                
                fig_retention.add_trace(go.Bar(
                    name='1-Week Retention',
                    x=retention_df['Game'],
                    y=retention_df['1W Retention'] * 100,
                    marker_color='#FF6B35',
                    yaxis='y',
                    offsetgroup=1
                ))
                
                fig_retention.add_trace(go.Bar(
                    name='4-Week Retention',
                    x=retention_df['Game'],
                    y=retention_df['4W Retention'] * 100,
                    marker_color='#00D4FF',
                    yaxis='y',
                    offsetgroup=2
                ))
                
                fig_retention.update_layout(
                    title={
                        'text': '📈 Player Retention Analysis',
                        'font': {'size': 16, 'color': 'white'},
                        'x': 0.5
                    },
                    xaxis=dict(title='Games'),
                    yaxis=dict(title='Retention Rate (%)', side='left'),
                    legend=dict(x=0.7, y=0.95),
                    barmode='group',
                    height=350,
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font_color='white'
                )
                
                st.plotly_chart(fig_retention, use_container_width=True)
                
                # Retention metrics table
                st.markdown("#### 📊 Detailed Retention Metrics")
                display_df = retention_df.copy()
                display_df['1W Retention'] = (display_df['1W Retention'] * 100).round(1).astype(str) + '%'
                display_df['4W Retention'] = (display_df['4W Retention'] * 100).round(1).astype(str) + '%'
                display_df['New Users (Latest)'] = display_df['New Users (Latest)'].apply(lambda x: f"{x:,.0f}")
                
                st.dataframe(
                    display_df,
                    use_container_width=True,
                    hide_index=True
                )
        
        # Daily gaming activity trends
        if games_daily is not None and not games_daily.empty:
            # Process daily data
            games_daily_clean = games_daily.copy()
            if 'date' in games_daily_clean.columns:
                games_daily_clean['date'] = pd.to_datetime(games_daily_clean['date'])
            
            # Create daily activity trend
            fig_daily = go.Figure()
            
            for i, game in enumerate(games_daily_clean['project_name'].unique()):
                game_data = games_daily_clean[games_daily_clean['project_name'] == game]
                
                fig_daily.add_trace(go.Scatter(
                    x=game_data['date'],
                    y=game_data['daily_active_users'],
                    mode='lines+markers',
                    name=game,
                    line=dict(color=colors[i % len(colors)], width=3),
                    hovertemplate=f'<b>{game}</b><br>Date: %{{x}}<br>DAU: %{{y:,.0f}}<extra></extra>'
                ))
            
            fig_daily.update_layout(
                title={
                    'text': '👥 Daily Active Users Trend',
                    'font': {'size': 16, 'color': 'white'},
                    'x': 0.5
                },
                xaxis=dict(title='Date'),
                yaxis=dict(title='Daily Active Users'),
                height=350,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white',
                legend=dict(
                    orientation="v",
                    yanchor="top",
                    y=1,
                    xanchor="left",
                    x=1.02
                )
            )
            
            st.plotly_chart(fig_daily, use_container_width=True)
    
    # Gaming insights and performance analysis
    st.markdown("### 🏆 Gaming Performance Intelligence")
    
    gaming_insights = []
    
    if games_overall is not None and not games_overall.empty:
        # Market concentration analysis
        top_game_share = (games_overall.iloc[0]['unique_users'] / total_gaming_users * 100)
        if top_game_share > 80:
            gaming_insights.append(f"⚠️ **High Market Concentration**: {top_game} dominates with {top_game_share:.1f}% user share - ecosystem diversification needed.")
        elif top_game_share > 60:
            gaming_insights.append(f"📊 **Moderate Market Leadership**: {top_game} leads with {top_game_share:.1f}% user share - healthy but concentrated market.")
        else:
            gaming_insights.append(f"🎮 **Diverse Gaming Ecosystem**: Well-distributed user base across multiple games - {top_game} leads with {top_game_share:.1f}% share.")
        
        # User engagement analysis
        if 'tx_per_user' in games_overall.columns:
            avg_engagement = games_overall['tx_per_user'].mean()
            top_engagement = games_overall['tx_per_user'].max()
            top_engagement_game = games_overall.loc[games_overall['tx_per_user'].idxmax(), 'project_name']
            
            gaming_insights.append(f"🎯 **User Engagement**: Average {avg_engagement:.1f} transactions per user. {top_engagement_game} leads engagement with {top_engagement:.1f} tx/user.")
        
        # Growth potential analysis
        if len(games_overall) > 3:
            emerging_games = games_overall.tail(3)['project_name'].tolist()
            gaming_insights.append(f"🌱 **Emerging Games**: {', '.join(emerging_games)} showing potential for ecosystem growth and diversification.")
    
    # Retention insights
    if retention_metrics:
        best_retention_game = max(retention_metrics.items(), key=lambda x: x[1].get('avg_1w_retention', 0))
        best_retention_rate = best_retention_game[1]['avg_1w_retention'] * 100
        gaming_insights.append(f"📈 **Retention Leader**: {best_retention_game[0]} achieves {best_retention_rate:.1f}% weekly retention - benchmark for ecosystem.")
        
        avg_ecosystem_retention = np.mean([metrics['avg_1w_retention'] for metrics in retention_metrics.values()]) * 100
        if avg_ecosystem_retention > 50:
            gaming_insights.append(f"✅ **Strong Player Retention**: Ecosystem average of {avg_ecosystem_retention:.1f}% weekly retention indicates healthy user engagement.")
        elif avg_ecosystem_retention < 30:
            gaming_insights.append(f"⚠️ **Retention Challenge**: {avg_ecosystem_retention:.1f}% average weekly retention suggests need for improved player experience.")
    
    # Display gaming insights
    for insight in gaming_insights:
        st.markdown(f'<div class="insight-box">{insight}</div>', unsafe_allow_html=True)

# === TOKEN INTELLIGENCE SECTION ===
elif section == "💎 Token Intelligence":
    st.markdown("## 💎 Token Intelligence & DeFi Analytics Dashboard")
    
    # Calculate token metrics
    whale_impact = analytics.calculate_whale_impact_score(whale_data, volume_data)
    
    # Token Intelligence Overview
    st.markdown("### 💰 WRON Trading & Liquidity Intelligence")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    # Calculate aggregated metrics
    total_whale_volume = whale_data['total_volume_usd'].sum() if whale_data is not None and not whale_data.empty else 125000000
    whale_count = len(whale_data) if whale_data is not None and not whale_data.empty else 15
    avg_whale_size = whale_data['total_volume_usd'].mean() if whale_data is not None and not whale_data.empty else 2500000
    
    if volume_data is not None and not volume_data.empty:
        daily_volume = volume_data.groupby('date')['volume_usd'].sum().iloc[-1] if 'date' in volume_data.columns else volume_data['volume_usd'].sum()
        total_pairs = len(volume_data['pair'].unique()) if 'pair' in volume_data.columns else 4
    else:
        daily_volume = 45000000
        total_pairs = 4
    
    with col1:
        st.markdown(f"""
        <div class="metric-card whale-card">
            <h4 style="color: #00D4FF; margin: 0 0 10px 0;">🐋 Whale Volume</h4>
            <h2 style="color: white; margin: 0;">${total_whale_volume/1e6:.1f}M</h2>
            <p style="color: #4ECDC4; margin: 5px 0 0 0; font-size: 1.1em;">30-day total</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card whale-card">
            <h4 style="color: #00D4FF; margin: 0 0 10px 0;">🎯 Active Whales</h4>
            <h2 style="color: white; margin: 0;">{whale_count}</h2>
            <p style="color: #4ECDC4; margin: 5px 0 0 0; font-size: 1.1em;">$10K+ traders</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card whale-card">
            <h4 style="color: #00D4FF; margin: 0 0 10px 0;">📊 Daily Volume</h4>
            <h2 style="color: white; margin: 0;">${daily_volume/1e6:.1f}M</h2>
            <p style="color: #4ECDC4; margin: 5px 0 0 0; font-size: 1.1em;">24h trading</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card whale-card">
            <h4 style="color: #00D4FF; margin: 0 0 10px 0;">🔄 Trading Pairs</h4>
            <h2 style="color: white; margin: 0;">{total_pairs}</h2>
            <p style="color: #4ECDC4; margin: 5px 0 0 0; font-size: 1.1em;">Active on Katana</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        impact_status = "High" if whale_impact > 60 else "Medium" if whale_impact > 30 else "Low"
        impact_color = "#FFB347" if whale_impact > 60 else "#4ECDC4" if whale_impact > 30 else "#00FF88"
        
        st.markdown(f"""
        <div class="metric-card whale-card">
            <h4 style="color: #00D4FF; margin: 0 0 10px 0;">⚖️ Whale Impact</h4>
            <h2 style="color: white; margin: 0;">{whale_impact:.1f}</h2>
            <p style="color: {impact_color}; margin: 5px 0 0 0; font-size: 1.1em;">{impact_status} influence</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Advanced Token Visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        # Whale tracking and analysis
        if whale_data is not None and not whale_data.empty:
            # Whale performance scatter plot
            fig_whale = go.Figure()
            
            # Add whale positions
            whale_data['profit_color'] = whale_data['profit_loss_usd'].apply(
                lambda x: '#00FF88' if x > 0 else '#FF6B6B'
            )
            
            fig_whale.add_trace(go.Scatter(
                x=whale_data['total_volume_usd'],
                y=whale_data['profit_loss_usd'],
                mode='markers+text',
                marker=dict(
                    size=whale_data['trade_count']/3,
                    color=whale_data['profit_color'],
                    sizemode='area',
                    sizemin=8,
                    sizemax=40,
                    line=dict(width=2, color='white'),
                    opacity=0.8
                ),
                text=[f"Whale {i+1}" for i in range(len(whale_data))],
                textposition="top center",
                hovertemplate='<b>%{text}</b><br>' +
                             'Volume: $%{x:,.0f}<br>' +
                             'P&L: $%{y:,.0f}<br>' +
                             'Trades: %{marker.size}<br>' +
                             '<extra></extra>',
                name='Whales'
            ))
            
            # Add profit/loss reference line
            fig_whale.add_hline(y=0, line_dash="dash", line_color="white", opacity=0.5)
            
            fig_whale.update_layout(
                title={
                    'text': '🐋 Whale Performance Analysis',
                    'font': {'size': 16, 'color': 'white'},
                    'x': 0.5
                },
                xaxis=dict(title='Total Volume (USD)', type='log'),
                yaxis=dict(title='Profit/Loss (USD)'),
                height=400,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white',
                showlegend=False
            )
            
            st.plotly_chart(fig_whale, use_container_width=True)
            
            # Top whales table
            st.markdown("#### 🏆 Top Performing Whales")
            whale_display = whale_data.copy()
            whale_display['Whale ID'] = [f"Whale {i+1}" for i in range(len(whale_display))]
            whale_display['Volume'] = whale_display['total_volume_usd'].apply(lambda x: f"${x/1e6:.2f}M")
            whale_display['P&L'] = whale_display['profit_loss_usd'].apply(lambda x: f"${x/1e3:.1f}K")
            whale_display['Trades'] = whale_display['trade_count']
            whale_display['Avg Size'] = whale_display['avg_trade_size_usd'].apply(lambda x: f"${x/1e3:.1f}K")
            
            display_cols = ['Whale ID', 'Volume', 'P&L', 'Trades', 'Avg Size']
            st.dataframe(
                whale_display[display_cols].head(10),
                use_container_width=True,
                hide_index=True
            )
    
    with col2:
        # Hourly trading patterns
        if hourly_data is not None and not hourly_data.empty:
            # Create hourly pattern visualization
            fig_hourly = go.Figure()
            
            # Volume by hour
            fig_hourly.add_trace(go.Scatter(
                x=hourly_data['hour'],
                y=hourly_data['avg_volume_usd'],
                mode='lines+markers',
                name='Volume',
                line=dict(color='#FF6B35', width=4),
                fill='tonexty',
                fillcolor='rgba(255, 107, 53, 0.2)',
                yaxis='y'
            ))
            
            # Traders by hour (secondary axis)
            fig_hourly.add_trace(go.Scatter(
                x=hourly_data['hour'],
                y=hourly_data['avg_unique_traders'],
                mode='lines+markers',
                name='Unique Traders',
                line=dict(color='#00D4FF', width=3),
                yaxis='y2'
            ))
            
            fig_hourly.update_layout(
                title={
                    'text': '🕒 24-Hour Trading Pattern Analysis',
                    'font': {'size': 16, 'color': 'white'},
                    'x': 0.5
                },
                xaxis=dict(title='Hour of Day (UTC)', tickmode='linear', dtick=2),
                yaxis=dict(title='Volume (USD)', side='left', color='#FF6B35'),
                yaxis2=dict(title='Unique Traders', side='right', overlaying='y', color='#00D4FF'),
                height=350,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white',
                legend=dict(x=0.02, y=0.98)
            )
            
            st.plotly_chart(fig_hourly, use_container_width=True)
        
        # Trading pairs analysis
        if volume_data is not None and not volume_data.empty and 'pair' in volume_data.columns:
            # Aggregate volume by pair
            pair_volumes = volume_data.groupby('pair')['volume_usd'].sum().sort_values(ascending=False)
            
            fig_pairs = go.Figure(data=[
                go.Bar(
                    x=pair_volumes.index,
                    y=pair_volumes.values,
                    marker_color=['#FF6B35', '#F7931E', '#FFD700', '#00D4FF', '#4ECDC4'][:len(pair_volumes)],
                    hovertemplate='<b>%{x}</b><br>Volume: $%{y:,.0f}<extra></extra>'
                )
            ])
            
            fig_pairs.update_layout(
                title={
                    'text': '📊 Trading Pairs Volume Distribution',
                    'font': {'size': 16, 'color': 'white'},
                    'x': 0.5
                },
                xaxis=dict(title='Trading Pairs'),
                yaxis=dict(title='Volume (USD)'),
                height=350,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white'
            )
            
            st.plotly_chart(fig_pairs, use_container_width=True)
    
    # Weekly user segmentation analysis
    if weekly_data is not None and not weekly_data.empty:
        st.markdown("### 📈 Weekly Trading Segmentation Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # User segmentation over time
            fig_segments = go.Figure()
            
            if 'week' in weekly_data.columns:
                weekly_data['week'] = pd.to_datetime(weekly_data['week'])
            
            fig_segments.add_trace(go.Scatter(
                x=weekly_data['week'] if 'week' in weekly_data.columns else range(len(weekly_data)),
                y=weekly_data['retail_traders'],
                mode='lines+markers',
                name='Retail Traders',
                line=dict(color='#4ECDC4', width=3),
                stackgroup='one'
            ))
            
            fig_segments.add_trace(go.Scatter(
                x=weekly_data['week'] if 'week' in weekly_data.columns else range(len(weekly_data)),
                y=weekly_data['small_whales'],
                mode='lines+markers',
                name='Small Whales',
                line=dict(color='#FFD700', width=3),
                stackgroup='one'
            ))
            
            fig_segments.add_trace(go.Scatter(
                x=weekly_data['week'] if 'week' in weekly_data.columns else range(len(weekly_data)),
                y=weekly_data['large_whales'],
                mode='lines+markers',
                name='Large Whales',
                line=dict(color='#FF6B35', width=3),
                stackgroup='one'
            ))
            
            fig_segments.update_layout(
                title={
                    'text': '👥 Weekly Trader Segmentation',
                    'font': {'size': 16, 'color': 'white'},
                    'x': 0.5
                },
                xaxis=dict(title='Week'),
                yaxis=dict(title='Number of Traders'),
                height=400,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white',
                hovermode='x unified'
            )
            
            st.plotly_chart(fig_segments, use_container_width=True)
        
        with col2:
            # Volume distribution by segment
            if all(col in weekly_data.columns for col in ['retail_volume_usd', 'small_whale_volume_usd', 'large_whale_volume_usd']):
                latest_week = weekly_data.iloc[-1]
                
                segments = ['Retail Traders', 'Small Whales', 'Large Whales']
                volumes = [
                    latest_week['retail_volume_usd'],
                    latest_week['small_whale_volume_usd'],
                    latest_week['large_whale_volume_usd']
                ]
                
                fig_vol_dist = go.Figure(data=[
                    go.Pie(
                        labels=segments,
                        values=volumes,
                        hole=.4,
                        marker_colors=['#4ECDC4', '#FFD700', '#FF6B35'],
                        textinfo='label+percent',
                        hovertemplate='<b>%{label}</b><br>Volume: $%{value:,.0f}<br>Share: %{percent}<extra></extra>'
                    )
                ])
                
                fig_vol_dist.update_layout(
                    title={
                        'text': '💰 Volume Distribution by Segment',
                        'font': {'size': 16, 'color': 'white'},
                        'x': 0.5
                    },
                    height=400,
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font_color='white'
                )
                
                st.plotly_chart(fig_vol_dist, use_container_width=True)
    
    # Token Intelligence Insights
    st.markdown("### 🔍 Token Intelligence & Market Insights")
    
    token_insights = []
    
    # Whale impact analysis
    if whale_impact > 70:
        token_insights.append(f"⚠️ **High Whale Concentration Risk**: Large traders control significant market influence ({whale_impact:.1f}% impact score) - price volatility risk elevated.")
    elif whale_impact > 40:
        token_insights.append(f"📊 **Moderate Whale Activity**: Balanced whale presence ({whale_impact:.1f}% impact) - healthy liquidity with manageable concentration risk.")
    else:
        token_insights.append(f"✅ **Distributed Trading Activity**: Low whale concentration ({whale_impact:.1f}% impact) - decentralized trading environment.")
    
    # Volume analysis
    if volume_data is not None and not volume_data.empty:
        if 'pair' in volume_data.columns:
            top_pair = volume_data.groupby('pair')['volume_usd'].sum().idxmax()
            top_pair_volume = volume_data.groupby('pair')['volume_usd'].sum().max()
            total_volume = volume_data['volume_usd'].sum()
            pair_dominance = (top_pair_volume / total_volume) * 100
            
            token_insights.append(f"🔄 **Trading Pair Analysis**: {top_pair} dominates with {pair_dominance:.1f}% of total volume (${top_pair_volume/1e6:.1f}M).")
    
    # Hourly pattern insights
    if hourly_data is not None and not hourly_data.empty:
        peak_hour = hourly_data.loc[hourly_data['avg_volume_usd'].idxmax(), 'hour']
        peak_volume = hourly_data['avg_volume_usd'].max()
        low_hour = hourly_data.loc[hourly_data['avg_volume_usd'].idxmin(), 'hour']
        low_volume = hourly_data['avg_volume_usd'].min()
        
        volatility_ratio = peak_volume / low_volume
        token_insights.append(f"🕒 **Trading Pattern**: Peak activity at {peak_hour}:00 UTC (${peak_volume/1e6:.1f}M), lowest at {low_hour}:00 UTC - {volatility_ratio:.1f}x volume difference.")
    
    # Whale profitability
    if whale_data is not None and not whale_data.empty:
        profitable_whales = len(whale_data[whale_data['profit_loss_usd'] > 0])
        total_whales = len(whale_data)
        profitability_rate = (profitable_whales / total_whales) * 100
        
        if profitability_rate > 70:
            token_insights.append(f"📈 **Strong Whale Performance**: {profitable_whales}/{total_whales} whales ({profitability_rate:.1f}%) showing profits - bullish market sentiment.")
        elif profitability_rate < 30:
            token_insights.append(f"📉 **Whale Losses Indicate Bearish Sentiment**: Only {profitable_whales}/{total_whales} whales ({profitability_rate:.1f}%) profitable - market under pressure.")
        else:
            token_insights.append(f"⚖️ **Mixed Whale Sentiment**: {profitable_whales}/{total_whales} whales ({profitability_rate:.1f}%) profitable - neutral market conditions.")
    
    # Display token insights
    for insight in token_insights:
        st.markdown(f'<div class="insight-box">{insight}</div>', unsafe_allow_html=True)

# === USER ANALYTICS SECTION ===
elif section == "👥 User Analytics":
    st.markdown("## 👥 User Behavior & Ecosystem Analytics Dashboard")
    
    # Calculate user metrics
    retention_metrics = analytics.calculate_retention_metrics(retention_data)
    
    # User Analytics Overview
    st.markdown("### 🧠 User Intelligence & Behavioral Analysis")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    # Calculate user metrics
    if ron_holders is not None and not ron_holders.empty:
        total_holders = ron_holders['holders'].sum()
        whale_holders = ron_holders[ron_holders['balance_range'].str.contains('10K+|100K+', na=False)]['holders'].sum() if any('10K+' in str(x) or '100K+' in str(x) for x in ron_holders['balance_range']) else 0
    else:
        total_holders = 277475
        whale_holders = 975
    
    if retention_data is not None and not retention_data.empty:
        latest_new_users = retention_data.groupby('week')['new_users'].sum().iloc[-1] if 'week' in retention_data.columns else retention_data['new_users'].sum()
        avg_retention = retention_data['retention_rate_1w'].mean() if 'retention_rate_1w' in retention_data.columns else 0.45
    else:
        latest_new_users = 48500
        avg_retention = 0.45
    
    gaming_users = games_overall['unique_users'].sum() if games_overall is not None and not games_overall.empty else 2800000
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h4 style="color: #8A4AF3; margin: 0 0 10px 0;">👥 Total Users</h4>
            <h2 style="color: white; margin: 0;">{total_holders:,.0f}</h2>
            <p style="color: #B19CD9; margin: 5px 0 0 0; font-size: 1.1em;">RON holders</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h4 style="color: #8A4AF3; margin: 0 0 10px 0;">🎮 Gaming Users</h4>
            <h2 style="color: white; margin: 0;">{gaming_users/1e6:.1f}M</h2>
            <p style="color: #B19CD9; margin: 5px 0 0 0; font-size: 1.1em;">Active gamers</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h4 style="color: #8A4AF3; margin: 0 0 10px 0;">🐋 Power Users</h4>
            <h2 style="color: white; margin: 0;">{whale_holders:,.0f}</h2>
            <p style="color: #B19CD9; margin: 5px 0 0 0; font-size: 1.1em;">Large holders</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h4 style="color: #8A4AF3; margin: 0 0 10px 0;">🆕 New Users</h4>
            <h2 style="color: white; margin: 0;">{latest_new_users/1000:.1f}K</h2>
            <p style="color: #B19CD9; margin: 5px 0 0 0; font-size: 1.1em;">This week</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        st.markdown(f"""
        <div class="metric-card">
            <h4 style="color: #8A4AF3; margin: 0 0 10px 0;">📈 Retention Rate</h4>
            <h2 style="color: white; margin: 0;">{avg_retention*100:.1f}%</h2>
            <p style="color: #B19CD9; margin: 5px 0 0 0; font-size: 1.1em;">1-week avg</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # User Analytics Visualizations
    col1, col2 = st.columns(2)
    
    with col1:
        # User segmentation analysis
        if ron_holders is not None and not ron_holders.empty:
            # Enhanced holder distribution with wealth analysis
            fig_holders = make_subplots(
                rows=2, cols=1,
                subplot_titles=("💰 Holder Distribution by Balance", "📊 Wealth Concentration Analysis"),
                vertical_spacing=0.15,
                row_heights=[0.6, 0.4]
            )
            
            colors = ['#8A4AF3', '#B19CD9', '#00D4FF', '#4ECDC4', '#FFD700', '#FF6B35', '#FF6B6B']
            
            # Main distribution chart
            fig_holders.add_trace(
                go.Bar(
                    x=ron_holders['balance_range'],
                    y=ron_holders['holders'],
                    marker_color=colors[:len(ron_holders)],
                    name='Holders',
                    hovertemplate='<b>%{x}</b><br>Holders: %{y:,.0f}<br><extra></extra>'
                ),
                row=1, col=1
            )
            
            # Wealth distribution (total balance)
            if 'total_balance' in ron_holders.columns:
                fig_holders.add_trace(
                    go.Bar(
                        x=ron_holders['balance_range'],
                        y=ron_holders['total_balance'],
                        marker_color=[f"rgba{tuple(list(px.colors.hex_to_rgb(colors[i % len(colors)])) + [0.7])}" for i in range(len(ron_holders))],
                        name='Total Balance',
                        hovertemplate='<b>%{x}</b><br>Total Balance: %{y:,.0f} RON<br><extra></extra>'
                    ),
                    row=2, col=1
                )
            
            fig_holders.update_layout(
                height=600,
                showlegend=False,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white',
                title={
                    'text': "👥 Comprehensive User Segmentation Analysis",
                    'font': {'size': 18, 'color': 'white'},
                    'x': 0.5
                }
            )
            
            fig_holders.update_yaxes(title_text="Number of Holders", row=1, col=1)
            fig_holders.update_yaxes(title_text="Total Balance (RON)", row=2, col=1)
            
            st.plotly_chart(fig_holders, use_container_width=True)
    
    with col2:
        # User activation and retention trends
        if retention_data is not None and not retention_data.empty:
            # Process retention data for comprehensive analysis
            weekly_totals = retention_data.groupby('week').agg({
                'new_users': 'sum',
                'retained_users_1w': 'sum',
                'retained_users_4w': 'sum',
                'retention_rate_1w': 'mean',
                'retention_rate_4w': 'mean'
            }).reset_index()
            
            if 'week' in weekly_totals.columns:
                weekly_totals['week'] = pd.to_datetime(weekly_totals['week'])
            
            fig_retention = make_subplots(
                rows=2, cols=1,
                subplot_titles=("🆕 Weekly User Activation", "📈 Retention Rate Trends"),
                vertical_spacing=0.15
            )
            
            # User activation
            fig_retention.add_trace(
                go.Scatter(
                    x=weekly_totals['week'] if 'week' in weekly_totals.columns else range(len(weekly_totals)),
                    y=weekly_totals['new_users'],
                    mode='lines+markers',
                    name='New Users',
                    line=dict(color='#8A4AF3', width=3),
                    fill='tonexty',
                    fillcolor='rgba(138, 74, 243, 0.2)',
                    hovertemplate='<b>New Users</b><br>Week: %{x}<br>Count: %{y:,.0f}<extra></extra>'
                ),
                row=1, col=1
            )
            
            # Retention rates
            fig_retention.add_trace(
                go.Scatter(
                    x=weekly_totals['week'] if 'week' in weekly_totals.columns else range(len(weekly_totals)),
                    y=weekly_totals['retention_rate_1w'] * 100,
                    mode='lines+markers',
                    name='1-Week Retention',
                    line=dict(color='#00D4FF', width=3),
                    hovertemplate='<b>1W Retention</b><br>Week: %{x}<br>Rate: %{y:.1f}%<extra></extra>'
                ),
                row=2, col=1
            )
            
            fig_retention.add_trace(
                go.Scatter(
                    x=weekly_totals['week'] if 'week' in weekly_totals.columns else range(len(weekly_totals)),
                    y=weekly_totals['retention_rate_4w'] * 100,
                    mode='lines+markers',
                    name='4-Week Retention',
                    line=dict(color='#FFD700', width=3),
                    hovertemplate='<b>4W Retention</b><br>Week: %{x}<br>Rate: %{y:.1f}%<extra></extra>'
                ),
                row=2, col=1
            )
            
            fig_retention.update_layout(
                height=500,
                showlegend=False,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white',
                title={
                    'text': "📊 User Lifecycle Analysis",
                    'font': {'size': 16, 'color': 'white'},
                    'x': 0.5
                }
            )
            
            fig_retention.update_yaxes(title_text="New Users", row=1, col=1)
            fig_retention.update_yaxes(title_text="Retention Rate (%)", row=2, col=1)
            
            st.plotly_chart(fig_retention, use_container_width=True)
        
        # User engagement heatmap by game
        if retention_data is not None and not retention_data.empty and 'project_name' in retention_data.columns:
            # Create engagement heatmap
            pivot_data = retention_data.pivot_table(
                values='retention_rate_1w',
                index='project_name',
                columns='week' if 'week' in retention_data.columns else retention_data.index,
                aggfunc='mean'
            )
            
            if not pivot_data.empty:
                fig_heatmap = go.Figure(data=go.Heatmap(
                    z=pivot_data.values * 100,
                    x=[f"Week {i+1}" for i in range(pivot_data.shape[1])],
                    y=pivot_data.index,
                    colorscale='Viridis',
                    hovertemplate='<b>%{y}</b><br>%{x}<br>Retention: %{z:.1f}%<extra></extra>',
                    colorbar=dict(title="Retention %")
                ))
                
                fig_heatmap.update_layout(
                    title={
                        'text': "🔥 Game Engagement Heatmap",
                        'font': {'size': 16, 'color': 'white'},
                        'x': 0.5
                    },
                    height=300,
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font_color='white'
                )
                
                st.plotly_chart(fig_heatmap, use_container_width=True)
    
    # Advanced user behavior analysis
    st.markdown("### 🔬 Advanced User Behavior Intelligence")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # User journey analysis
        if retention_data is not None and not retention_data.empty:
            st.markdown("#### 🛣️ User Journey Funnel Analysis")
            
            # Calculate funnel metrics
            total_new_users = retention_data['new_users'].sum()
            total_1w_retained = retention_data['retained_users_1w'].sum()
            total_4w_retained = retention_data['retained_users_4w'].sum()
            
            funnel_data = {
                'Stage': ['New Users', '1-Week Retained', '4-Week Retained'],
                'Users': [total_new_users, total_1w_retained, total_4w_retained],
                'Conversion': [100, (total_1w_retained/total_new_users)*100, (total_4w_retained/total_new_users)*100]
            }
            
            fig_funnel = go.Figure(go.Funnel(
                y=funnel_data['Stage'],
                x=funnel_data['Users'],
                textinfo="value+percent initial",
                marker=dict(color=['#8A4AF3', '#00D4FF', '#FFD700'])
            ))
            
            fig_funnel.update_layout(
                height=300,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white'
            )
            
            st.plotly_chart(fig_funnel, use_container_width=True)
            
            # Retention benchmarks
            st.markdown("#### 📊 Retention Benchmarks")
            if retention_metrics:
                benchmark_data = []
                for game, metrics in retention_metrics.items():
                    benchmark_data.append({
                        'Game': game,
                        '1W Retention': f"{metrics.get('avg_1w_retention', 0)*100:.1f}%",
                        '4W Retention': f"{metrics.get('avg_4w_retention', 0)*100:.1f}%",
                        'Stability Score': f"{metrics.get('retention_stability', 0)*100:.1f}%",
                        'Growth Trend': f"{metrics.get('user_growth_trend', 0)*100:+.1f}%"
                    })
                
                if benchmark_data:
                    benchmark_df = pd.DataFrame(benchmark_data)
                    st.dataframe(benchmark_df, use_container_width=True, hide_index=True)
    
    with col2:
        # Cross-sector user engagement analysis
        st.markdown("#### 🔄 Cross-Sector User Engagement")
        
        # Simulate cross-sector data based on available metrics
        if games_overall is not None and not games_overall.empty and whale_data is not None and not whale_data.empty:
            gaming_volume = games_overall['total_transactions'].sum()
            trading_volume = whale_data['total_volume_usd'].sum()
            
            cross_sector_data = {
                'Sector': ['Gaming Only', 'Trading Only', 'Cross-Platform', 'Inactive'],
                'Users': [gaming_users * 0.7, whale_count * 15, gaming_users * 0.2, total_holders * 0.1],
                'Engagement': ['High', 'Very High', 'Ultra High', 'Low']
            }
            
            fig_cross = px.treemap(
                pd.DataFrame(cross_sector_data),
                path=['Engagement', 'Sector'],
                values='Users',
                color='Users',
                color_continuous_scale=['#FF6B6B', '#FFD700', '#00D4FF', '#00FF88'],
                title="🎯 User Engagement Segmentation"
            )
            
            fig_cross.update_layout(
                height=350,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white'
            )
            
            st.plotly_chart(fig_cross, use_container_width=True)
        
        # User lifetime value analysis
        st.markdown("#### 💎 User Value Segmentation")
        
        if ron_holders is not None and not ron_holders.empty and 'avg_balance' in ron_holders.columns:
            # Calculate user value tiers
            value_tiers = ron_holders.copy()
            value_tiers['Value Tier'] = value_tiers['balance_range'].map({
                '0-1 RON': 'Entry Level',
                '1-10 RON': 'Casual Users', 
                '10-100 RON': 'Regular Users',
                '100-1K RON': 'Power Users',
                '1K-10K RON': 'VIP Users',
                '10K-100K RON': 'Whales',
                '100K+ RON': 'Mega Whales'
            })
            
            fig_value = px.sunburst(
                value_tiers,
                path=['Value Tier', 'balance_range'],
                values='holders',
                color='avg_balance',
                color_continuous_scale='Viridis',
                title="💰 User Value Distribution"
            )
            
            fig_value.update_layout(
                height=350,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white'
            )
            
            st.plotly_chart(fig_value, use_container_width=True)
    
    # User Analytics Insights
    st.markdown("### 🧠 User Intelligence & Behavioral Insights")
    
    user_insights = []
    
    # User distribution analysis
    if ron_holders is not None and not ron_holders.empty:
        small_holders = ron_holders[ron_holders['balance_range'].str.contains('0-1 RON|1-10 RON', na=False)]['holders'].sum()
        small_holder_pct = (small_holders / total_holders) * 100
        
        if small_holder_pct > 70:
            user_insights.append(f"👥 **Broad User Base**: {small_holder_pct:.1f}% are small holders - strong grassroots adoption and accessibility.")
        else:
            user_insights.append(f"💎 **Premium User Focus**: {100-small_holder_pct:.1f}% are significant holders - concentrated value ecosystem.")
    
    # Retention analysis
    if avg_retention > 0.6:
        user_insights.append(f"📈 **Excellent User Retention**: {avg_retention*100:.1f}% weekly retention rate significantly above industry standards.")
    elif avg_retention > 0.4:
        user_insights.append(f"✅ **Healthy User Retention**: {avg_retention*100:.1f}% weekly retention rate indicates good user experience and engagement.")
    else:
        user_insights.append(f"⚠️ **Retention Opportunity**: {avg_retention*100:.1f}% weekly retention below optimal - user experience improvements needed.")
    
    # Growth analysis
    if retention_data is not None and not retention_data.empty:
        recent_growth = retention_data.groupby('week')['new_users'].sum().pct_change().iloc[-1] if 'week' in retention_data.columns else 0
        if recent_growth > 0.1:
            user_insights.append(f"🚀 **Strong User Growth**: {recent_growth*100:.1f}% week-over-week new user growth - ecosystem expansion accelerating.")
        elif recent_growth < -0.1:
            user_insights.append(f"📉 **User Growth Challenge**: {abs(recent_growth)*100:.1f}% decline in new users - acquisition strategy review needed.")
    
    # Cross-platform engagement
    gaming_penetration = (gaming_users / total_holders) * 100 if total_holders > 0 else 0
    if gaming_penetration > 80:
        user_insights.append(f"🎮 **Gaming-First Ecosystem**: {gaming_penetration:.1f}% of users actively gaming - strong product-market fit for gaming focus.")
    
    # Power user concentration
    if whale_holders > 0:
        whale_concentration = (whale_holders / total_holders) * 100
        if whale_concentration > 5:
            user_insights.append(f"🐋 **High Value User Concentration**: {whale_concentration:.1f}% are large holders - significant economic influence concentrated.")
        else:
            user_insights.append(f"👥 **Distributed Wealth**: Only {whale_concentration:.1f}% large holders - democratized token distribution.")
    
    # Display user insights
    for insight in user_insights:
        st.markdown(f'<div class="insight-box">{insight}</div>', unsafe_allow_html=True)

# Enhanced Footer with comprehensive status
st.markdown("---")

# Get comprehensive data status
data_status = {
    'CoinGecko Data': '✅ Active' if coingecko_data else '⚠️ Fallback',
    'Gaming Data': '✅ Active' if games_overall is not None and not games_overall.empty else '⚠️ Limited',
    'Network Data': '✅ Active' if ronin_daily is not None and not ronin_daily.empty else '⚠️ Limited', 
    'Token Data': '✅ Active' if whale_data is not None and not whale_data.empty else '⚠️ Limited',
    'User Data': '✅ Active' if retention_data is not None and not retention_data.empty else '⚠️ Limited'
}

last_update = datetime.now().strftime('%Y-%m-%d %H:%M UTC') if coingecko_data else "Data from cache"

st.markdown(f"""
<div style="background: linear-gradient(135deg, rgba(138, 74, 243, 0.1) 0%, rgba(255, 107, 53, 0.1) 100%);
           padding: 30px; border-radius: 20px; text-align: center; border: 1px solid rgba(255, 107, 53, 0.2);">
    
    <h3 style="color: #FF6B35; margin: 0 0 20px 0; font-weight: 700;">⚡ Ronin Ecosystem Tracker</h3>
    
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px;">
        {''.join([f'<div style="background: rgba(26, 26, 46, 0.6); padding: 10px; border-radius: 10px;"><strong>{source}:</strong> {status}</div>' for source, status in data_status.items()])}
    </div>
    
    <p style="color: #00D4FF; margin: 15px 0 5px 0; font-size: 1.1em; font-weight: 600;">
        📊 Real-time Gaming Economy Intelligence Platform
    </p>
    <p style="color: #B0B0B0; margin: 5px 0; font-size: 0.95em;">
        🔄 Data Sources: CoinGecko Pro API • Dune Analytics • Katana DEX • Ronin Network
    </p>
    <p style="color: #888; margin: 5px 0; font-size: 0.85em;">
        ⚡ Cache: 24 hours | 🔄 Last updated: {last_update}
    </p>
    <p style="color: #666; margin: 15px 0 0 0; font-size: 0.8em;">
        🛠️ Built with Streamlit • Plotly • Python • Advanced Analytics • Machine Learning
    </p>
    <p style="color: #555; margin: 5px 0 0 0; font-size: 0.75em;">
        💡 Disclaimer: Analytics for informational purposes only. Past performance does not guarantee future results.
    </p>
</div>
""", unsafe_allow_html=True)