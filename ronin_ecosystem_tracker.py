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

Author: Jo$h
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
from typing import Dict, List, Optional, Any, Tuple, Union
import joblib
from dotenv import load_dotenv
import threading
import math
import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global cache with thread safety
_GLOBAL_CACHE = {}
_CACHE_TTL = 86400  # 24 hours
_cache_lock = threading.Lock()

def is_cache_valid(cache_key: str) -> bool:
    """Check if cached data is still valid."""
    with _cache_lock:
        if cache_key not in _GLOBAL_CACHE:
            return False
        cache_time, _ = _GLOBAL_CACHE[cache_key]
        return time.time() - cache_time < _CACHE_TTL

def get_cached_data(cache_key: str) -> Any:
    """Retrieve cached data if valid."""
    with _cache_lock:
        if is_cache_valid(cache_key):
            _, data = _GLOBAL_CACHE[cache_key]
            return data
        return None

def set_cached_data(cache_key: str, data: Any) -> None:
    """Store data in cache."""
    with _cache_lock:
        _GLOBAL_CACHE[cache_key] = (time.time(), data)

def safe_date_conversion(df: pd.DataFrame, date_column: str) -> bool:
    """Safely convert column to datetime."""
    if df is None or df.empty or date_column not in df.columns:
        return False
    try:
        df[date_column] = pd.to_datetime(df[date_column])
        return True
    except Exception as e:
        logger.warning(f"Failed to convert {date_column} to datetime: {e}")
        return False

def validate_required_columns(df: pd.DataFrame, required_cols: List[str]) -> bool:
    """Validate DataFrame has required columns."""
    if df is None or df.empty:
        return False
    return all(col in df.columns for col in required_cols)

def safe_numeric_operation(func, *args, default_value: float = 0.0) -> float:
    """Safely perform numeric operations with fallback."""
    try:
        result = func(*args)
        if pd.isna(result) or not np.isfinite(result):
            return default_value
        return result
    except Exception as e:
        logger.warning(f"Numeric operation failed: {e}")
        return default_value

class DataValidationError(Exception):
    """Custom exception for data validation errors."""
    pass

class RoninDataFetcher:
    """Main class for fetching and managing Ronin ecosystem data with comprehensive error handling."""
    
    def __init__(self):
        """Initialize the data fetcher with configuration and validation."""
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
        
        # Session management with proper headers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'RoninEcosystemTracker/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        
        # Data validation flags
        self._api_status = {
            'coingecko': 'unknown',
            'dune': 'unknown'
        }
    
    def _load_api_keys(self) -> Dict[str, Optional[str]]:
        """Load API keys with Streamlit compatibility and validation."""
        keys = {'dune': None, 'coingecko': None}
        
        try:
            # Primary: Streamlit secrets (for deployed app)
            keys['dune'] = st.secrets.get("DEFI_JOSH_DUNE_QUERY_API_KEY")
            keys['coingecko'] = st.secrets.get("COINGECKO_PRO_API_KEY")
        except Exception:
            # Fallback: Environment variables (for local development)
            keys['dune'] = os.getenv("DEFI_JOSH_DUNE_QUERY_API_KEY")
            keys['coingecko'] = os.getenv("COINGECKO_PRO_API_KEY")
        
        # Validate API keys
        for service, key in keys.items():
            if key and len(key.strip()) > 10:  # Basic validation
                logger.info(f"{service.upper()} API key loaded successfully")
            else:
                logger.warning(f"{service.upper()} API key not found or invalid")
        
        return keys
    
    def _load_query_config(self) -> Dict[str, Dict[str, Any]]:
        """Load Dune query configuration with validation."""
        queries = {
            'games_overall_activity': {
                'id': 5779698,
                'description': 'Top Game Contracts Overall Activity',
                'filename': 'games_overall_activity.joblib',
                'required_columns': ['contract_address', 'project_name', 'total_transactions', 'unique_users']
            },
            'games_daily_activity': {
                'id': 5781579,
                'description': 'Top Game Contracts Daily Activity',
                'filename': 'games_daily_activity.joblib',
                'required_columns': ['date', 'project_name', 'daily_active_users', 'daily_transactions']
            },
            'ronin_daily_activity': {
                'id': 5779439,
                'description': 'Daily Ronin Network Activity',
                'filename': 'ronin_daily_activity.joblib',
                'required_columns': ['date', 'daily_transactions', 'active_addresses']
            },
            'user_activation_retention': {
                'id': 5783320,
                'description': 'User Weekly Activation and Retention',
                'filename': 'ronin_users_weekly_activation_and_retention_for_each_project_or_game.joblib',
                'required_columns': ['week', 'project_name', 'new_users', 'retention_rate_1w']
            },
            'ron_current_holders': {
                'id': 5783623,
                'description': 'RON Current Holders',
                'filename': 'ron_current_holders.joblib',
                'required_columns': ['address', 'balance']
            },
            'ron_segmented_holders': {
                'id': 5785491,
                'description': 'RON Segmented Holders',
                'filename': 'ron_current_segmented_holders.joblib',
                'required_columns': ['balance_range', 'holders', 'total_balance']
            },
            'wron_katana_pairs': {
                'id': 5783967,
                'description': 'WRON Trading Pairs on Katana DEX',
                'filename': 'wron_active_trade_pairs_on_Katana.joblib',
                'required_columns': ['pair', 'volume_usd']
            },
            'wron_whale_tracking': {
                'id': 5784215,
                'description': 'WRON Whale Tracking',
                'filename': 'wron_whale_tracking_on_Katana.joblib',
                'required_columns': ['trader_address', 'total_volume_usd', 'trade_count']
            },
            'wron_volume_liquidity': {
                'id': 5784210,
                'description': 'WRON Trading Volume & Liquidity',
                'filename': 'WRON_Trading_Volume_&_Liquidity_Flow_on_Katana.joblib',
                'required_columns': ['date', 'pair', 'volume_usd', 'liquidity_usd']
            },
            'wron_hourly_activity': {
                'id': 5785066,
                'description': 'WRON Hourly Trading Activity',
                'filename': 'WRON_Trading_by_hour_of_day_on_Katana.joblib',
                'required_columns': ['hour', 'avg_volume_usd', 'avg_trades']
            },
            'wron_weekly_segmentation': {
                'id': 5785149,
                'description': 'WRON Weekly User Segmentation',
                'filename': 'WRON_weekly_trade_volume_and_user_segmentation_on_Katana.joblib',
                'required_columns': ['week', 'retail_traders', 'small_whales', 'large_whales']
            }
        }
        
        return queries
    
    def fetch_coingecko_data(self) -> Dict[str, Any]:
        """Fetch RON token data from CoinGecko with comprehensive error handling."""
        cache_key = 'coingecko_ron_data'
        cached_data = get_cached_data(cache_key)
        if cached_data:
            return cached_data
        
        if not self.api_keys['coingecko']:
            self._api_status['coingecko'] = 'missing_key'
            return self._get_coingecko_fallback_data()
        
        try:
            url = "https://pro-api.coingecko.com/api/v3/coins/ronin"
            headers = {"x-cg-pro-api-key": self.api_keys['coingecko']}
            
            response = self.session.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            ron_data = response.json()
            
            # Validate response structure
            if not isinstance(ron_data, dict) or 'market_data' not in ron_data:
                raise DataValidationError("Invalid CoinGecko response structure")
            
            processed_data = self._process_coingecko_data(ron_data)
            processed_data['data_source'] = 'live_api'
            
            self._api_status['coingecko'] = 'success'
            set_cached_data(cache_key, processed_data)
            return processed_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"CoinGecko API request failed: {e}")
            self._api_status['coingecko'] = 'request_failed'
        except DataValidationError as e:
            logger.error(f"CoinGecko data validation failed: {e}")
            self._api_status['coingecko'] = 'invalid_data'
        except Exception as e:
            logger.error(f"Unexpected CoinGecko error: {e}")
            self._api_status['coingecko'] = 'unknown_error'
        
        return self._get_coingecko_fallback_data()
    
    def _process_coingecko_data(self, ron_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process CoinGecko data with validation."""
        market_data = ron_data.get("market_data", {})
        
        # Safe data extraction with validation
        processed = {
            'name': ron_data.get('name', 'Ronin'),
            'symbol': ron_data.get('symbol', 'RON').upper(),
            'price_usd': safe_numeric_operation(lambda: market_data.get('current_price', {}).get('usd', 0), default_value=2.15),
            'market_cap_usd': safe_numeric_operation(lambda: market_data.get('market_cap', {}).get('usd', 0), default_value=700000000),
            'volume_24h_usd': safe_numeric_operation(lambda: market_data.get('total_volume', {}).get('usd', 0), default_value=45000000),
            'circulating_supply': safe_numeric_operation(lambda: market_data.get('circulating_supply', 0), default_value=325000000),
            'total_supply': safe_numeric_operation(lambda: market_data.get('total_supply', 0), default_value=1000000000),
            'price_change_24h_pct': safe_numeric_operation(lambda: market_data.get('price_change_percentage_24h', 0), default_value=0),
            'price_change_7d_pct': safe_numeric_operation(lambda: market_data.get('price_change_percentage_7d', 0), default_value=0),
            'price_change_30d_pct': safe_numeric_operation(lambda: market_data.get('price_change_percentage_30d', 0), default_value=0),
            'market_cap_rank': int(market_data.get('market_cap_rank', 85)) if market_data.get('market_cap_rank') else 85,
            'last_updated': datetime.now().isoformat()
        }
        
        # Calculate derived metrics
        processed['tvl_usd'] = safe_numeric_operation(
            lambda: market_data.get('total_value_locked', {}).get('usd', processed['market_cap_usd'] * 0.25)
        )
        processed['mcap_to_tvl_ratio'] = safe_numeric_operation(
            lambda: processed['market_cap_usd'] / processed['tvl_usd'] if processed['tvl_usd'] > 0 else 0,
            default_value=4.0
        )
        
        return processed
    
    def _get_coingecko_fallback_data(self) -> Dict[str, Any]:
        """Generate realistic fallback data for CoinGecko with timestamp variance."""
        base_time = datetime.now()
        
        # Add some realistic variance to fallback data
        price_variance = np.random.uniform(0.95, 1.05)
        volume_variance = np.random.uniform(0.8, 1.2)
        
        return {
            'name': 'Ronin',
            'symbol': 'RON',
            'price_usd': 2.15 * price_variance,
            'market_cap_usd': 700000000 * price_variance,
            'volume_24h_usd': 45000000 * volume_variance,
            'circulating_supply': 325000000,
            'total_supply': 1000000000,
            'price_change_24h_pct': np.random.uniform(-5, 5),
            'price_change_7d_pct': np.random.uniform(-15, 15),
            'price_change_30d_pct': np.random.uniform(-30, 30),
            'market_cap_rank': 85,
            'tvl_usd': 180000000 * price_variance,
            'mcap_to_tvl_ratio': 3.89,
            'last_updated': base_time.isoformat(),
            'data_source': 'fallback',
            'api_status': self._api_status.get('coingecko', 'unknown')
        }
    
    def fetch_dune_query(self, query_key: str) -> Optional[pd.DataFrame]:
        """Fetch data from Dune query with comprehensive validation."""
        cache_key = f'dune_{query_key}'
        cached_data = get_cached_data(cache_key)
        if cached_data is not None:
            return cached_data
        
        if not self.api_keys['dune'] or query_key not in self.dune_queries:
            self._api_status['dune'] = 'missing_key_or_config'
            return self._get_dune_fallback_data(query_key)
        
        try:
            from dune_client.client import DuneClient
            
            query_config = self.dune_queries[query_key]
            dune = DuneClient(self.api_keys['dune'])
            
            # Fetch data with timeout
            query_result = dune.get_latest_result(query_config['id'])
            
            if not query_result or not query_result.result or not query_result.result.rows:
                raise DataValidationError(f"Empty result from Dune query {query_key}")
            
            df = pd.DataFrame(query_result.result.rows)
            
            # Validate required columns
            required_cols = query_config.get('required_columns', [])
            if required_cols and not validate_required_columns(df, required_cols):
                missing_cols = [col for col in required_cols if col not in df.columns]
                logger.warning(f"Missing columns in {query_key}: {missing_cols}")
            
            # Clean and validate data
            df = self._clean_dataframe(df, query_key)
            
            self._api_status['dune'] = 'success'
            set_cached_data(cache_key, df)
            return df
            
        except ImportError:
            logger.warning("dune_client not installed - using fallback data")
            self._api_status['dune'] = 'missing_library'
        except DataValidationError as e:
            logger.error(f"Dune data validation failed for {query_key}: {e}")
            self._api_status['dune'] = 'invalid_data'
        except Exception as e:
            logger.error(f"Dune query {query_key} failed: {e}")
            self._api_status['dune'] = 'query_failed'
        
        return self._get_dune_fallback_data(query_key)
    
    def _clean_dataframe(self, df: pd.DataFrame, query_key: str) -> pd.DataFrame:
        """Clean and validate DataFrame data."""
        if df is None or df.empty:
            return df
        
        # Handle date columns
        date_columns = ['date', 'week', 'timestamp']
        for col in date_columns:
            if col in df.columns:
                safe_date_conversion(df, col)
        
        # Clean numeric columns
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        for col in numeric_columns:
            df[col] = df[col].replace([np.inf, -np.inf], np.nan)
            df[col] = df[col].fillna(0)
        
        # Remove duplicates if applicable
        if 'date' in df.columns and len(df) > 1:
            df = df.drop_duplicates(subset=['date'], keep='last')
        
        return df.sort_values(df.columns[0]) if len(df.columns) > 0 else df
    
    def _get_dune_fallback_data(self, query_key: str) -> pd.DataFrame:
        """Generate comprehensive fallback data for each query type."""
        current_time = datetime.now()
        
        try:
            if query_key == 'games_overall_activity':
                return pd.DataFrame({
                    'contract_address': [
                        '0x32950db2a7164ae833121501c797d79e7b79d74c',
                        '0x97a9107c1793bc407d6f527b77e7fff4d812bece',
                        '0x8c811e3c958e190f5ec15fb376533a3398620500',
                        '0x1f8b0e2c7d1a4b2c3d4e5f6789abcdef01234567',
                        '0x234567890abcdef123456789abcdef0123456789'
                    ],
                    'project_name': ['Axie Infinity', 'The Machines Arena', 'Pixels', 'Tearing Spaces', 'Apeiron'],
                    'total_transactions': [15000000, 2500000, 1200000, 850000, 650000],
                    'unique_users': [2800000, 180000, 95000, 65000, 42000],
                    'total_gas_used': [45000000000, 8500000000, 3200000000, 2100000000, 1400000000],
                    'avg_gas_per_tx': [3000, 3400, 2667, 2471, 2154]
                })
            
            elif query_key == 'games_daily_activity':
                dates = pd.date_range(end=current_time, periods=30, freq='D')
                games = ['Axie Infinity', 'The Machines Arena', 'Pixels', 'Tearing Spaces', 'Apeiron']
                daily_data = []
                
                for date in dates:
                    for game in games:
                        base_users = {
                            'Axie Infinity': 250000,
                            'The Machines Arena': 18000,
                            'Pixels': 12000,
                            'Tearing Spaces': 8000,
                            'Apeiron': 5500
                        }[game]
                        
                        # Add realistic trends and seasonality
                        day_of_week_multiplier = 1.2 if date.weekday() in [5, 6] else 1.0  # Weekend boost
                        trend_multiplier = 1 + (dates.tolist().index(date) * 0.001)  # Slight growth trend
                        
                        daily_users = int(base_users * np.random.uniform(0.7, 1.3) * day_of_week_multiplier * trend_multiplier)
                        
                        daily_data.append({
                            'date': date,
                            'project_name': game,
                            'daily_active_users': daily_users,
                            'daily_transactions': int(daily_users * np.random.uniform(2, 8)),
                            'daily_gas_used': int(daily_users * np.random.uniform(500000, 1500000))
                        })
                
                return pd.DataFrame(daily_data)
            
            elif query_key == 'ronin_daily_activity':
                dates = pd.date_range(end=current_time, periods=30, freq='D')
                daily_network_data = []
                
                for i, date in enumerate(dates):
                    # Add realistic network growth trends
                    growth_factor = 1 + (i * 0.002)  # Slight growth over time
                    weekend_factor = 1.15 if date.weekday() in [5, 6] else 1.0
                    
                    daily_network_data.append({
                        'date': date,
                        'daily_transactions': int(np.random.randint(800000, 1200000) * growth_factor * weekend_factor),
                        'active_addresses': int(np.random.randint(180000, 250000) * growth_factor * weekend_factor),
                        'avg_gas_price_gwei': np.random.uniform(0.1, 0.5),
                        'total_gas_used': int(np.random.randint(15000000000, 25000000000) * growth_factor),
                        'new_addresses': int(np.random.randint(5000, 15000) * growth_factor)
                    })
                
                return pd.DataFrame(daily_network_data)
            
            elif query_key == 'user_activation_retention':
                weeks = pd.date_range(end=current_time, periods=12, freq='W')
                games = ['Axie Infinity', 'The Machines Arena', 'Pixels', 'Tearing Spaces', 'Apeiron']
                retention_data = []
                
                for week in weeks:
                    for game in games:
                        base_activation = {
                            'Axie Infinity': 45000,
                            'The Machines Arena': 2800,
                            'Pixels': 1500,
                            'Tearing Spaces': 800,
                            'Apeiron': 600
                        }[game]
                        
                        # Realistic retention patterns
                        base_retention_1w = {
                            'Axie Infinity': 0.65,
                            'The Machines Arena': 0.45,
                            'Pixels': 0.55,
                            'Tearing Spaces': 0.35,
                            'Apeiron': 0.40
                        }[game]
                        
                        new_users = int(base_activation * np.random.uniform(0.6, 1.4))
                        retention_1w = base_retention_1w * np.random.uniform(0.8, 1.2)
                        retention_4w = retention_1w * np.random.uniform(0.3, 0.5)  # 4-week is lower
                        
                        retention_data.append({
                            'week': week,
                            'project_name': game,
                            'new_users': new_users,
                            'retained_users_1w': int(new_users * retention_1w),
                            'retained_users_4w': int(new_users * retention_4w),
                            'retention_rate_1w': retention_1w,
                            'retention_rate_4w': retention_4w
                        })
                
                return pd.DataFrame(retention_data)
            
            elif query_key == 'ron_segmented_holders':
                return pd.DataFrame({
                    'balance_range': [
                        '0-1 RON', '1-10 RON', '10-100 RON', '100-1K RON',
                        '1K-10K RON', '10K-100K RON', '100K+ RON'
                    ],
                    'holders': [125000, 85000, 45000, 18000, 3500, 850, 125],
                    'total_balance': [45000, 420000, 2800000, 8500000, 15600000, 28400000, 45200000],
                    'avg_balance': [0.36, 4.94, 62.22, 472.22, 4457.14, 33411.76, 361600],
                    'percentage_of_holders': [44.3, 30.1, 15.9, 6.4, 1.2, 0.3, 0.04]
                })
            
            elif query_key == 'wron_whale_tracking':
                whale_data = []
                for i in range(1, 21):  # Top 20 whales
                    first_trade = current_time - timedelta(days=np.random.randint(30, 365))
                    last_trade = current_time - timedelta(days=np.random.randint(0, 7))
                    
                    total_volume = np.random.uniform(500000, 5000000)
                    trade_count = np.random.randint(25, 200)
                    
                    whale_data.append({
                        'trader_address': f'0x{i:040x}',
                        'total_volume_usd': total_volume,
                        'trade_count': trade_count,
                        'avg_trade_size_usd': total_volume / trade_count,
                        'profit_loss_usd': np.random.uniform(-200000, 800000),
                        'first_trade_date': first_trade,
                        'last_trade_date': last_trade,
                        'active_days': (last_trade - first_trade).days,
                        'win_rate': np.random.uniform(0.35, 0.75)
                    })
                
                return pd.DataFrame(whale_data)
            
            elif query_key == 'wron_volume_liquidity':
                dates = pd.date_range(end=current_time, periods=30, freq='D')
                pairs = ['WRON/USDC', 'WRON/AXS', 'WRON/SLP', 'WRON/PIXEL', 'WRON/ETH']
                volume_data = []
                
                for date in dates:
                    for pair in pairs:
                        base_volume = {
                            'WRON/USDC': 8500000,
                            'WRON/AXS': 3200000,
                            'WRON/SLP': 1800000,
                            'WRON/PIXEL': 950000,
                            'WRON/ETH': 1200000
                        }[pair]
                        
                        # Add market dynamics
                        weekend_factor = 0.7 if date.weekday() in [5, 6] else 1.0
                        volume = base_volume * np.random.uniform(0.4, 1.8) * weekend_factor
                        
                        volume_data.append({
                            'date': date,
                            'pair': pair,
                            'volume_usd': volume,
                            'liquidity_usd': volume * np.random.uniform(2.5, 4.2),
                            'trades': int(volume / np.random.uniform(800, 2000)),
                            'unique_traders': int(volume / np.random.uniform(5000, 12000)),
                            'avg_trade_size': volume / max(1, int(volume / np.random.uniform(800, 2000)))
                        })
                
                return pd.DataFrame(volume_data)
            
            elif query_key == 'wron_hourly_activity':
                # Realistic hourly trading patterns (UTC time)
                hourly_patterns = {
                    'volume': [
                        2400000, 1800000, 1200000, 800000, 900000, 1400000,  # 0-5
                        2800000, 4200000, 5800000, 7200000, 8100000, 8800000,  # 6-11
                        9200000, 8600000, 8900000, 9500000, 8800000, 8200000,  # 12-17
                        7400000, 6200000, 5100000, 4200000, 3400000, 2900000   # 18-23
                    ],
                    'trades': [
                        1200, 950, 680, 420, 480, 720,
                        1450, 2200, 3100, 3800, 4200, 4600,
                        4850, 4500, 4650, 4950, 4600, 4300,
                        3850, 3200, 2680, 2200, 1780, 1520
                    ],
                    'unique_traders': [
                        450, 320, 180, 95, 125, 280,
                        580, 950, 1350, 1650, 1850, 2100,
                        2250, 2050, 2150, 2300, 2100, 1950,
                        1700, 1400, 1150, 850, 650, 520
                    ]
                }
                
                return pd.DataFrame({
                    'hour': range(24),
                    'avg_volume_usd': hourly_patterns['volume'],
                    'avg_trades': hourly_patterns['trades'],
                    'avg_unique_traders': hourly_patterns['unique_traders']
                })
            
            elif query_key == 'wron_weekly_segmentation':
                weeks = pd.date_range(end=current_time, periods=12, freq='W')
                weekly_data = []
                
                for i, week in enumerate(weeks):
                    # Add growth trends
                    growth_factor = 1 + (i * 0.05)
                    
                    retail_traders = int(np.random.randint(15000, 25000) * growth_factor)
                    small_whales = int(np.random.randint(800, 1500) * growth_factor)
                    large_whales = int(np.random.randint(50, 150))
                    
                    weekly_data.append({
                        'week': week,
                        'retail_traders': retail_traders,
                        'small_whales': small_whales,
                        'large_whales': large_whales,
                        'retail_volume_usd': retail_traders * np.random.uniform(1500, 2500),
                        'small_whale_volume_usd': small_whales * np.random.uniform(40000, 80000),
                        'large_whale_volume_usd': large_whales * np.random.uniform(500000, 1200000),
                        'total_volume_usd': 0  # Will calculate below
                    })
                
                # Calculate total volumes
                for data in weekly_data:
                    data['total_volume_usd'] = (
                        data['retail_volume_usd'] + 
                        data['small_whale_volume_usd'] + 
                        data['large_whale_volume_usd']
                    )
                
                return pd.DataFrame(weekly_data)
            
            else:
                logger.warning(f"Unknown query_key: {query_key}")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Error generating fallback data for {query_key}: {e}")
            return pd.DataFrame()
    
    def get_data_status(self) -> Dict[str, str]:
        """Get current data source status."""
        return {
            'coingecko_status': self._api_status.get('coingecko', 'unknown'),
            'dune_status': self._api_status.get('dune', 'unknown'),
            'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
        }

class RoninAnalytics:
    """Advanced analytics calculations for Ronin ecosystem with comprehensive validation."""
    
    @staticmethod
    def calculate_network_health_score(
        daily_data: Optional[pd.DataFrame], 
        token_data: Optional[Dict[str, Any]], 
        games_data: Optional[pd.DataFrame]
    ) -> float:
        """Calculate comprehensive network health score with validation."""
        if daily_data is None or daily_data.empty:
            logger.warning("No daily data available for health score calculation")
            return 50.0  # Neutral score
        
        # Validate required columns
        required_cols = ['daily_transactions', 'active_addresses']
        if not validate_required_columns(daily_data, required_cols):
            logger.warning("Missing required columns for health score")
            return 50.0
        
        if len(daily_data) < 7:
            logger.warning("Insufficient data points for health score calculation")
            return 50.0
        
        score = 100.0
        recent_data = daily_data.tail(7).copy()
        
        try:
            # Transaction throughput analysis (25 points)
            avg_tx = safe_numeric_operation(lambda: recent_data['daily_transactions'].mean(), default_value=900000)
            
            if avg_tx < 500000:
                score -= 20
            elif avg_tx < 800000:
                score -= 10
            elif avg_tx < 900000:
                score -= 5
            # Above 900k gets no penalty
            
            # Network growth trend (25 points)
            if len(recent_data) >= 2:
                first_tx = recent_data['daily_transactions'].iloc[0]
                last_tx = recent_data['daily_transactions'].iloc[-1]
                
                if first_tx > 0:
                    tx_trend = (last_tx - first_tx) / first_tx
                    
                    if tx_trend < -0.3:
                        score -= 25
                    elif tx_trend < -0.15:
                        score -= 15
                    elif tx_trend < -0.05:
                        score -= 8
                    # Positive growth gets no penalty
            
            # User activity stability (25 points)
            if 'active_addresses' in recent_data.columns:
                user_mean = safe_numeric_operation(lambda: recent_data['active_addresses'].mean())
                user_std = safe_numeric_operation(lambda: recent_data['active_addresses'].std())
                
                if user_mean > 0:
                    user_volatility = user_std / user_mean
                    
                    if user_volatility > 0.3:
                        score -= 25
                    elif user_volatility > 0.2:
                        score -= 15
                    elif user_volatility > 0.1:
                        score -= 8
            
            # Gas price stability (15 points)
            if 'avg_gas_price_gwei' in recent_data.columns:
                gas_mean = safe_numeric_operation(lambda: recent_data['avg_gas_price_gwei'].mean())
                gas_std = safe_numeric_operation(lambda: recent_data['avg_gas_price_gwei'].std())
                
                if gas_mean > 0:
                    gas_volatility = gas_std / gas_mean
                    
                    if gas_volatility > 0.5:
                        score -= 15
                    elif gas_volatility > 0.3:
                        score -= 8
                    # Low volatility gets no penalty
            
            # Token performance impact (10 points)
            if token_data and isinstance(token_data, dict):
                price_change = safe_numeric_operation(
                    lambda: token_data.get('price_change_7d_pct', 0),
                    default_value=0
                )
                
                if price_change < -30:
                    score -= 10
                elif price_change < -15:
                    score -= 5
                # Positive or small negative changes get no penalty
            
        except Exception as e:
            logger.error(f"Error in health score calculation: {e}")
            return 50.0
        
        return max(0.0, min(100.0, score))
    
    @staticmethod
    def calculate_game_dominance_index(games_data: Optional[pd.DataFrame]) -> float:
        """Calculate gaming ecosystem concentration with validation."""
        if games_data is None or games_data.empty:
            return 0.0
        
        if 'unique_users' not in games_data.columns:
            logger.warning("unique_users column missing for dominance calculation")
            return 0.0
        
        try:
            # Filter out zero or negative values
            valid_games = games_data[games_data['unique_users'] > 0].copy()
            
            if valid_games.empty:
                return 0.0
            
            total_users = safe_numeric_operation(lambda: valid_games['unique_users'].sum())
            
            if total_users <= 0:
                return 0.0
            
            user_shares = valid_games['unique_users'] / total_users
            
            # Herfindahl-Hirschman Index for concentration
            hhi = safe_numeric_operation(lambda: (user_shares ** 2).sum(), default_value=0)
            
            # Convert to 0-100 scale (higher = more concentrated)
            # HHI ranges from 1/n to 1, where n is number of games
            return min(100.0, hhi * 100)
            
        except Exception as e:
            logger.error(f"Error calculating dominance index: {e}")
            return 0.0
    
    @staticmethod
    def calculate_retention_metrics(retention_data: Optional[pd.DataFrame]) -> Dict[str, Dict[str, float]]:
        """Calculate advanced retention metrics with validation."""
        if retention_data is None or retention_data.empty:
            return {}
        
        required_cols = ['project_name', 'retention_rate_1w', 'new_users']
        if not validate_required_columns(retention_data, required_cols):
            logger.warning("Missing required columns for retention metrics")
            return {}
        
        metrics = {}
        
        try:
            for project in retention_data['project_name'].unique():
                if pd.isna(project):
                    continue
                    
                project_data = retention_data[retention_data['project_name'] == project].copy()
                
                if len(project_data) < 4:  # Need sufficient data points
                    continue
                
                # Calculate metrics safely
                avg_1w_retention = safe_numeric_operation(
                    lambda: project_data['retention_rate_1w'].mean(),
                    default_value=0
                )
                
                avg_4w_retention = safe_numeric_operation(
                    lambda: project_data.get('retention_rate_4w', pd.Series([0])).mean(),
                    default_value=0
                )
                
                # Retention stability (coefficient of variation)
                retention_mean = safe_numeric_operation(
                    lambda: project_data['retention_rate_1w'].mean(),
                    default_value=1
                )
                retention_std = safe_numeric_operation(
                    lambda: project_data['retention_rate_1w'].std(),
                    default_value=0
                )
                
                retention_stability = safe_numeric_operation(
                    lambda: 1 - (retention_std / retention_mean) if retention_mean > 0 else 0,
                    default_value=0
                )
                
                # User growth trend
                if len(project_data) >= 2:
                    first_users = project_data['new_users'].iloc[0]
                    last_users = project_data['new_users'].iloc[-1]
                    
                    user_growth_trend = safe_numeric_operation(
                        lambda: (last_users - first_users) / first_users if first_users > 0 else 0,
                        default_value=0
                    )
                else:
                    user_growth_trend = 0.0
                
                metrics[project] = {
                    'avg_1w_retention': avg_1w_retention,
                    'avg_4w_retention': avg_4w_retention,
                    'retention_stability': max(0, min(1, retention_stability)),
                    'user_growth_trend': user_growth_trend,
                    'data_points': len(project_data)
                }
        
        except Exception as e:
            logger.error(f"Error calculating retention metrics: {e}")
            return {}
        
        return metrics
    
    @staticmethod
    def calculate_whale_impact_score(
        whale_data: Optional[pd.DataFrame], 
        volume_data: Optional[pd.DataFrame]
    ) -> float:
        """Calculate whale market impact with comprehensive validation."""
        if whale_data is None or whale_data.empty:
            return 0.0
        
        if 'total_volume_usd' not in whale_data.columns:
            logger.warning("total_volume_usd column missing for whale impact calculation")
            return 0.0
        
        try:
            # Calculate total whale volume
            total_whale_volume = safe_numeric_operation(
                lambda: whale_data['total_volume_usd'].sum(),
                default_value=0
            )
            
            if total_whale_volume <= 0:
                return 0.0
            
            # Estimate total market volume
            if volume_data is not None and not volume_data.empty and 'volume_usd' in volume_data.columns:
                total_market_volume = safe_numeric_operation(
                    lambda: volume_data['volume_usd'].sum(),
                    default_value=total_whale_volume * 2
                )
            else:
                # Fallback: assume whales are 50% of total volume
                total_market_volume = total_whale_volume * 2
            
            if total_market_volume <= 0:
                return 0.0
            
            # Calculate whale dominance percentage
            whale_dominance = safe_numeric_operation(
                lambda: (total_whale_volume / total_market_volume) * 100,
                default_value=0
            )
            
            # Factor in whale concentration
            whale_count = len(whale_data)
            avg_whale_size = safe_numeric_operation(
                lambda: whale_data['total_volume_usd'].mean(),
                default_value=0
            )
            
            # Risk adjustment based on concentration
            # Higher average whale size increases systemic risk
            concentration_multiplier = safe_numeric_operation(
                lambda: 1 + (avg_whale_size / 1000000),  # Scale by millions
                default_value=1
            )
            
            # Final impact score
            impact_score = whale_dominance * concentration_multiplier
            
            return max(0.0, min(100.0, impact_score))
            
        except Exception as e:
            logger.error(f"Error calculating whale impact score: {e}")
            return 0.0
    
    @staticmethod
    def calculate_ecosystem_diversity_score(games_data: Optional[pd.DataFrame]) -> Dict[str, float]:
        """Calculate ecosystem diversity metrics."""
        if games_data is None or games_data.empty or 'unique_users' not in games_data.columns:
            return {'diversity_score': 0.0, 'shannon_index': 0.0, 'simpson_index': 0.0}
        
        try:
            # Filter valid games
            valid_games = games_data[games_data['unique_users'] > 0].copy()
            
            if len(valid_games) < 2:
                return {'diversity_score': 0.0, 'shannon_index': 0.0, 'simpson_index': 0.0}
            
            total_users = valid_games['unique_users'].sum()
            proportions = valid_games['unique_users'] / total_users
            
            # Shannon diversity index
            shannon_index = safe_numeric_operation(
                lambda: -sum(p * np.log(p) for p in proportions if p > 0),
                default_value=0
            )
            
            # Simpson diversity index
            simpson_index = safe_numeric_operation(
                lambda: 1 - sum(p**2 for p in proportions),
                default_value=0
            )
            
            # Normalize Shannon index (theoretical max is ln(n) where n is number of species)
            max_shannon = np.log(len(valid_games))
            normalized_shannon = shannon_index / max_shannon if max_shannon > 0 else 0
            
            # Combined diversity score (0-100)
            diversity_score = (normalized_shannon + simpson_index) * 50
            
            return {
                'diversity_score': max(0.0, min(100.0, diversity_score)),
                'shannon_index': shannon_index,
                'simpson_index': simpson_index,
                'game_count': len(valid_games)
            }
            
        except Exception as e:
            logger.error(f"Error calculating diversity score: {e}")
            return {'diversity_score': 0.0, 'shannon_index': 0.0, 'simpson_index': 0.0}

# Page configuration
st.set_page_config(
    page_title="Ronin Ecosystem Tracker",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced CSS styling with complete definitions
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
        text-shadow: 0 0 10px rgba(255, 107, 107, 0.5);
        animation: pulse 1.5s ease-in-out infinite;
    }
    
    .insight-box {
        background: linear-gradient(135deg, rgba(0, 212, 255, 0.1) 0%, rgba(255, 107, 53, 0.1) 100%);
        border-left: 4px solid #00D4FF;
        padding: 20px;
        border-radius: 10px;
        margin: 20px 0;
        font-style: italic;
        backdrop-filter: blur(10px);
    }
    
    .warning-box {
        background: linear-gradient(135deg, rgba(255, 215, 0, 0.1) 0%, rgba(255, 107, 107, 0.1) 100%);
        border-left: 4px solid #FFD700;
        padding: 15px;
        border-radius: 10px;
        margin: 15px 0;
        backdrop-filter: blur(10px);
    }
    
    .status-indicator {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8em;
        font-weight: 600;
        margin-left: 10px;
    }
    
    .status-live {
        background: linear-gradient(135deg, #00FF88, #4ECDC4);
        color: #000;
    }
    
    .status-fallback {
        background: linear-gradient(135deg, #FFD700, #FF6B35);
        color: #000;
    }
    
    .status-error {
        background: linear-gradient(135deg, #FF6B6B, #FF1744);
        color: #FFF;
    }
    
    @keyframes glow {
        from { 
            text-shadow: 0 0 15px rgba(0, 255, 136, 0.6); 
        }
        to { 
            text-shadow: 0 0 25px rgba(0, 255, 136, 1), 0 0 35px rgba(0, 255, 136, 0.8); 
        }
    }
    
    @keyframes pulse {
        0%, 100% { 
            opacity: 1; 
        }
        50% { 
            opacity: 0.7; 
        }
    }
    
    .dataframe {
        border-radius: 10px !important;
        overflow: hidden !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1) !important;
    }
    
    .stDataFrame > div {
        border-radius: 10px;
        overflow: hidden;
    }
    
    .loading-spinner {
        display: inline-block;
        width: 20px;
        height: 20px;
        border: 3px solid rgba(255, 107, 53, 0.3);
        border-radius: 50%;
        border-top-color: #FF6B35;
        animation: spin 1s ease-in-out infinite;
    }
    
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
</style>
""", unsafe_allow_html=True)

# Initialize data fetcher
@st.cache_resource
def get_data_fetcher():
    """Initialize and cache the data fetcher."""
    return RoninDataFetcher()

def get_health_status_display(score: float) -> Tuple[str, str, str]:
    """Get health status with CSS class and emoji."""
    if score >= 85:
        return "Excellent", "health-score-excellent", "🟢"
    elif score >= 70:
        return "Good", "health-score-good", "🟡"
    elif score >= 50:
        return "Warning", "health-score-warning", "🟠"
    else:
        return "Critical", "health-score-critical", "🔴"

def display_data_status(fetcher: RoninDataFetcher):
    """Display data source status indicators."""
    status = fetcher.get_data_status()
    
    coingecko_status = status['coingecko_status']
    dune_status = status['dune_status']
    
    # Status display logic
    cg_class = "status-live" if coingecko_status == "success" else "status-fallback" if "fallback" in str(coingecko_status) else "status-error"
    dune_class = "status-live" if dune_status == "success" else "status-fallback" if "fallback" in str(dune_status) else "status-error"
    
    cg_text = "Live" if coingecko_status == "success" else "Backup" if "fallback" in str(coingecko_status) else "Error"
    dune_text = "Live" if dune_status == "success" else "Demo" if "fallback" in str(dune_status) else "Error"
    
    st.markdown(f"""
    <div style="text-align: center; margin-bottom: 20px;">
        <span>📊 CoinGecko: <span class="status-indicator {cg_class}">{cg_text}</span></span>
        <span style="margin-left: 20px;">⛓️ Dune: <span class="status-indicator {dune_class}">{dune_text}</span></span>
        <span style="margin-left: 20px; color: #888; font-size: 0.9em;">Last Update: {status['last_update']}</span>
    </div>
    """, unsafe_allow_html=True)

# Initialize data fetcher
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

# Display data status
display_data_status(fetcher)

# Navigation
section = st.radio(
    "Dashboard Navigation",
    ["Network Overview", "Gaming Economy", "Token Intelligence", "User Analytics"],
    horizontal=True,
    label_visibility="collapsed"
)

# Load all data with progress indicator
with st.spinner("Loading ecosystem data..."):
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
    
    # Calculate analytics
    network_health_score = RoninAnalytics.calculate_network_health_score(ronin_daily, coingecko_data, games_overall)
    game_dominance_index = RoninAnalytics.calculate_game_dominance_index(games_overall)
    ecosystem_diversity = RoninAnalytics.calculate_ecosystem_diversity_score(games_overall)
    
    # Key Metrics Row
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        health_status, health_css, health_emoji = get_health_status_display(network_health_score)
        st.metric(
            "🏥 Network Health",
            f"{network_health_score:.1f}/100",
            delta=health_status,
            help="Composite score based on transaction volume, growth, stability, and gas prices"
        )
    
    with col2:
        if ronin_daily is not None and not ronin_daily.empty:
            latest_tx = ronin_daily['daily_transactions'].iloc[-1]
            prev_tx = ronin_daily['daily_transactions'].iloc[-2] if len(ronin_daily) > 1 else latest_tx
            tx_change = ((latest_tx - prev_tx) / prev_tx * 100) if prev_tx > 0 else 0
        else:
            latest_tx = 1000000
            tx_change = 0
        
        st.metric(
            "📊 Daily Transactions",
            f"{latest_tx:,.0f}",
            delta=f"{tx_change:+.1f}%",
            help="Total transactions processed in the last 24 hours"
        )
    
    with col3:
        price_change = coingecko_data.get('price_change_24h_pct', 0)
        st.metric(
            "💎 RON Price",
            f"${coingecko_data['price_usd']:.3f}",
            delta=f"{price_change:+.1f}%",
            help="Current RON token price and 24h change"
        )
    
    with col4:
        if ronin_daily is not None and not ronin_daily.empty:
            latest_users = ronin_daily['active_addresses'].iloc[-1]
            prev_users = ronin_daily['active_addresses'].iloc[-2] if len(ronin_daily) > 1 else latest_users
            user_change = ((latest_users - prev_users) / prev_users * 100) if prev_users > 0 else 0
        else:
            latest_users = 200000
            user_change = 0
        
        st.metric(
            "👥 Active Addresses",
            f"{latest_users:,.0f}",
            delta=f"{user_change:+.1f}%",
            help="Unique addresses that made transactions in the last 24 hours"
        )
    
    with col5:
        market_cap_b = coingecko_data['market_cap_usd'] / 1e9 if coingecko_data else 0.7
        market_cap_rank = coingecko_data.get('market_cap_rank', 85)
        st.metric(
            "🏦 Market Cap",
            f"${market_cap_b:.2f}B",
            delta=f"Rank #{market_cap_rank}",
            help="Total market capitalization and CoinGecko ranking"
        )
    
    st.markdown("---")
    
    # Enhanced Network Insights
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if ronin_daily is not None and not ronin_daily.empty:
            # Ensure date conversion
            ronin_daily_viz = ronin_daily.copy()
            safe_date_conversion(ronin_daily_viz, 'date')
            
            fig_network = make_subplots(
                rows=3, cols=1,
                subplot_titles=(
                    "📈 Daily Transaction Volume (30 Days)",
                    "👥 Active Addresses Trend",
                    "⛽ Gas Usage & Network Load"
                ),
                vertical_spacing=0.08,
                row_heights=[0.4, 0.3, 0.3]
            )
            
            # Transaction volume
            fig_network.add_trace(
                go.Scatter(
                    x=ronin_daily_viz['date'],
                    y=ronin_daily_viz['daily_transactions'],
                    mode='lines+markers',
                    name='Daily Transactions',
                    line=dict(color='#FF6B35', width=3),
                    fill='tonexty',
                    fillcolor='rgba(255, 107, 53, 0.2)',
                    hovertemplate='<b>%{x}</b><br>Transactions: %{y:,.0f}<extra></extra>'
                ),
                row=1, col=1
            )
            
            # Active addresses
            fig_network.add_trace(
                go.Scatter(
                    x=ronin_daily_viz['date'],
                    y=ronin_daily_viz['active_addresses'],
                    mode='lines+markers',
                    name='Active Addresses',
                    line=dict(color='#00D4FF', width=3),
                    fill='tonexty',
                    fillcolor='rgba(0, 212, 255, 0.2)',
                    hovertemplate='<b>%{x}</b><br>Active Addresses: %{y:,.0f}<extra></extra>'
                ),
                row=2, col=1
            )
            
            # Gas usage (if available)
            if 'total_gas_used' in ronin_daily_viz.columns:
                fig_network.add_trace(
                    go.Scatter(
                        x=ronin_daily_viz['date'],
                        y=ronin_daily_viz['total_gas_used'],
                        mode='lines+markers',
                        name='Total Gas Used',
                        line=dict(color='#4ECDC4', width=2),
                        hovertemplate='<b>%{x}</b><br>Gas Used: %{y:,.0f}<extra></extra>'
                    ),
                    row=3, col=1
                )
            
            fig_network.update_layout(
                height=800,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white',
                showlegend=False,
                title_font_size=16
            )
            
            fig_network.update_xaxes(showgrid=True, gridcolor='rgba(255,255,255,0.1)')
            fig_network.update_yaxes(showgrid=True, gridcolor='rgba(255,255,255,0.1)')
            
            st.plotly_chart(fig_network, use_container_width=True)
        else:
            st.warning("📊 Network activity data temporarily unavailable - using demo visualization")
            
            # Demo chart
            demo_dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
            demo_data = pd.DataFrame({
                'date': demo_dates,
                'transactions': np.random.randint(800000, 1200000, 30)
            })
            
            fig_demo = px.line(
                demo_data, x='date', y='transactions',
                title="📊 Network Activity (Demo Data)",
                color_discrete_sequence=['#FF6B35']
            )
            fig_demo.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white'
            )
            st.plotly_chart(fig_demo, use_container_width=True)
    
    with col2:
        # Network Health Gauge
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=network_health_score,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "🏥 Network Health Score", 'font': {'size': 16}},
            delta={'reference': 80, 'position': "top"},
            gauge={
                'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "white"},
                'bar': {'color': "#FF6B35"},
                'bgcolor': "rgba(0,0,0,0)",
                'borderwidth': 2,
                'bordercolor': "white",
                'steps': [
                    {'range': [0, 50], 'color': 'rgba(255, 107, 107, 0.3)'},
                    {'range': [50, 80], 'color': 'rgba(255, 215, 0, 0.3)'},
                    {'range': [80, 100], 'color': 'rgba(0, 255, 136, 0.3)'}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        fig_gauge.update_layout(
            height=350,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white'
        )
        st.plotly_chart(fig_gauge, use_container_width=True)
        
        # Ecosystem Diversity Score
        diversity_score = ecosystem_diversity.get('diversity_score', 0)
        st.markdown(f"""
        <div class="metric-card" style="text-align: center;">
            <h3 style="color: #00D4FF; margin: 0;">🎯 Ecosystem Diversity</h3>
            <h2 style="color: white; margin: 10px 0;">{diversity_score:.1f}/100</h2>
            <p style="color: #4ECDC4; font-size: 1.1em; margin: 0;">
                {ecosystem_diversity.get('game_count', 0)} Games Active
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Game Dominance Index
        st.markdown(f"""
        <div class="metric-card" style="text-align: center;">
            <h3 style="color: #FFD700; margin: 0;">📊 Market Concentration</h3>
            <h2 style="color: white; margin: 10px 0;">{game_dominance_index:.1f}/100</h2>
            <p style="color: #FFB347; font-size: 1.1em; margin: 0;">
                {'High' if game_dominance_index > 70 else 'Medium' if game_dominance_index > 40 else 'Low'} Concentration
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Token Holder Distribution
    if ron_segmented_holders is not None and not ron_segmented_holders.empty:
        st.markdown("### 💰 RON Token Distribution Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig_holders = px.pie(
                ron_segmented_holders,
                values='holders',
                names='balance_range',
                title="📊 Holder Count by Balance Range",
                color_discrete_sequence=['#FF6B35', '#F7931E', '#00D4FF', '#4ECDC4', '#45B7D1', '#FFB347', '#98D8E8']
            )
            fig_holders.update_traces(
                textposition='inside',
                textinfo='percent+label',
                hovertemplate='<b>%{label}</b><br>Holders: %{value:,.0f}<br>Percentage: %{percent}<extra></extra>'
            )
            fig_holders.update_layout(
                height=400,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white',
                showlegend=True,
                legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02)
            )
            st.plotly_chart(fig_holders, use_container_width=True)
        
        with col2:
            fig_balance = px.pie(
                ron_segmented_holders,
                values='total_balance',
                names='balance_range',
                title="💎 Token Distribution by Value",
                color_discrete_sequence=['#FF6B35', '#F7931E', '#00D4FF', '#4ECDC4', '#45B7D1', '#FFB347', '#98D8E8']
            )
            fig_balance.update_traces(
                textposition='inside',
                textinfo='percent+label',
                hovertemplate='<b>%{label}</b><br>Total Balance: %{value:,.0f} RON<br>Percentage: %{percent}<extra></extra>'
            )
            fig_balance.update_layout(
                height=400,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white',
                showlegend=True,
                legend=dict(orientation="v", yanchor="middle", y=0.5, xanchor="left", x=1.02)
            )
            st.plotly_chart(fig_balance, use_container_width=True)
        
        # Holder distribution table
        st.markdown("#### 📋 Detailed Holder Distribution")
        holder_display = ron_segmented_holders.copy()
        holder_display['Percentage of Holders'] = (holder_display['holders'] / holder_display['holders'].sum() * 100).round(2)
        holder_display['Average Balance'] = (holder_display['total_balance'] / holder_display['holders']).round(2)
        
        st.dataframe(
            holder_display[['balance_range', 'holders', 'total_balance', 'Percentage of Holders', 'Average Balance']],
            use_container_width=True,
            column_config={
                "balance_range": st.column_config.TextColumn("Balance Range"),
                "holders": st.column_config.NumberColumn("Holders", format="%d"),
                "total_balance": st.column_config.NumberColumn("Total Balance (RON)", format="%.0f"),
                "Percentage of Holders": st.column_config.NumberColumn("% of Holders", format="%.2f%%"),
                "Average Balance": st.column_config.NumberColumn("Avg Balance (RON)", format="%.2f")
            },
            hide_index=True
        )
    
    # Network Insights
    st.markdown("### 🔍 Network Performance Insights")
    
    insights = []
    
    if network_health_score >= 85:
        insights.append("✅ Network operating at excellent performance levels with strong transaction throughput and stability")
    elif network_health_score >= 70:
        insights.append("✅ Network performance is good with stable transaction processing and moderate growth")
    elif network_health_score >= 50:
        insights.append("⚠️ Network showing some stress indicators - monitoring recommended for transaction volumes and gas prices")
    else:
        insights.append("🚨 Network performance concerns detected - significant volatility or decline in key metrics")
    
    if game_dominance_index > 70:
        insights.append(f"📊 High market concentration detected ({game_dominance_index:.1f}/100) - ecosystem dominated by top games")
    elif game_dominance_index < 40:
        insights.append(f"🌟 Healthy ecosystem diversity ({game_dominance_index:.1f}/100) - well-distributed gaming activity")
    
    if diversity_score < 30:
        insights.append("🎯 Limited ecosystem diversity - growth opportunity for new gaming projects")
    elif diversity_score > 70:
        insights.append("🎯 Strong ecosystem diversity with multiple active gaming projects contributing to network activity")
    
    for insight in insights:
        st.markdown(f'<div class="insight-box">{insight}</div>', unsafe_allow_html=True)

# === GAMING ECONOMY SECTION ===
elif section == "Gaming Economy":
    st.markdown("## 🎮 Gaming Economy & Player Analytics Dashboard")
    
    # Gaming Overview Metrics
    if games_overall is not None and not games_overall.empty:
        total_gaming_users = games_overall['unique_users'].sum()
        total_gaming_tx = games_overall['total_transactions'].sum()
        top_game = games_overall.iloc[0]['project_name'] if len(games_overall) > 0 else "Axie Infinity"
        avg_gas_per_tx = games_overall['avg_gas_per_tx'].mean() if 'avg_gas_per_tx' in games_overall.columns else 3000
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric(
                "🎮 Total Players",
                f"{total_gaming_users:,}",
                help="Cumulative unique users across all tracked games"
            )
        
        with col2:
            st.metric(
                "🕹️ Gaming Transactions",
                f"{total_gaming_tx:,}",
                help="Total transactions from gaming contracts"
            )
        
        with col3:
            st.metric(
                "🏆 Leading Game",
                top_game,
                help="Game with highest user count"
            )
        
        with col4:
            st.metric(
                "🧩 Active Games",
                f"{len(games_overall)}",
                help="Number of games with measurable activity"
            )
        
        with col5:
            st.metric(
                "⛽ Avg Gas/Transaction",
                f"{avg_gas_per_tx:,.0f}",
                help="Average gas usage per gaming transaction"
            )
        
        st.markdown("---")
        
        # Game Performance Analysis
        st.markdown("### 🏆 Game Performance Rankings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # User distribution chart
            fig_games_users = px.bar(
                games_overall.head(10),
                x='project_name',
                y='unique_users',
                color='unique_users',
                title="👥 Unique Users by Game",
                labels={'unique_users': 'Unique Users', 'project_name': 'Game'},
                color_continuous_scale=['#FF6B35', '#F7931E', '#00D4FF'],
                text='unique_users'
            )
            fig_games_users.update_traces(
                texttemplate='%{text:,.0f}',
                textposition='outside',
                hovertemplate='<b>%{x}</b><br>Users: %{y:,.0f}<extra></extra>'
            )
            fig_games_users.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white',
                showlegend=False,
                xaxis_tickangle=-45,
                height=500
            )
            st.plotly_chart(fig_games_users, use_container_width=True)
        
        with col2:
            # Transaction volume chart
            fig_games_tx = px.bar(
                games_overall.head(10),
                x='project_name',
                y='total_transactions',
                color='total_transactions',
                title="🔄 Total Transactions by Game",
                labels={'total_transactions': 'Total Transactions', 'project_name': 'Game'},
                color_continuous_scale=['#4ECDC4', '#45B7D1', '#FF6B35'],
                text='total_transactions'
            )
            fig_games_tx.update_traces(
                texttemplate='%{text:,.0f}',
                textposition='outside',
                hovertemplate='<b>%{x}</b><br>Transactions: %{y:,.0f}<extra></extra>'
            )
            fig_games_tx.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white',
                showlegend=False,
                xaxis_tickangle=-45,
                height=500
            )
            st.plotly_chart(fig_games_tx, use_container_width=True)
        
        # Detailed game performance table
        st.markdown("### 📊 Comprehensive Game Analytics")
        
        games_analysis = games_overall.copy()
        games_analysis['Market Share (%)'] = (games_analysis['unique_users'] / total_gaming_users * 100).round(2)
        games_analysis['Tx per User'] = (games_analysis['total_transactions'] / games_analysis['unique_users']).round(1)
        games_analysis['Gas Efficiency'] = games_analysis.get('avg_gas_per_tx', 3000).astype(int)
        
        st.dataframe(
            games_analysis[['project_name', 'unique_users', 'total_transactions', 'Market Share (%)', 'Tx per User', 'Gas Efficiency']],
            use_container_width=True,
            column_config={
                "project_name": st.column_config.TextColumn("Game"),
                "unique_users": st.column_config.NumberColumn("Unique Users", format="%d"),
                "total_transactions": st.column_config.NumberColumn("Total Transactions", format="%d"),
                "Market Share (%)": st.column_config.NumberColumn("Market Share", format="%.2f%%"),
                "Tx per User": st.column_config.NumberColumn("Tx per User", format="%.1f"),
                "Gas Efficiency": st.column_config.NumberColumn("Avg Gas per Tx", format="%d")
            },
            hide_index=True
        )
    
    # Daily Activity Trends
    if games_daily is not None and not games_daily.empty:
        st.markdown("### 📈 Daily Activity Trends (30 Days)")
        
        games_daily_viz = games_daily.copy()
        safe_date_conversion(games_daily_viz, 'date')
        
        # Daily active users trend
        fig_daily_users = px.line(
            games_daily_viz,
            x='date',
            y='daily_active_users',
            color='project_name',
            title="👥 Daily Active Users Trend",
            labels={'daily_active_users': 'Daily Active Users', 'date': 'Date'}
        )
        fig_daily_users.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            height=500,
            hovermode='x unified'
        )
        st.plotly_chart(fig_daily_users, use_container_width=True)
        
        # Activity heatmap
        if len(games_daily_viz) > 7:
            st.markdown("### 🔥 Gaming Activity Heatmap")
            
            # Create pivot table for heatmap
            heatmap_data = games_daily_viz.pivot_table(
                index='project_name',
                columns=games_daily_viz['date'].dt.day_name(),
                values='daily_active_users',
                aggfunc='mean'
            ).fillna(0)
            
            fig_heatmap = px.imshow(
                heatmap_data,
                title="📅 Average Daily Users by Day of Week",
                labels={'color': 'Avg Daily Users'},
                aspect='auto',
                color_continuous_scale='Viridis'
            )
            fig_heatmap.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white',
                height=400
            )
            st.plotly_chart(fig_heatmap, use_container_width=True)
    
    # Player Retention Analysis
    if activation_retention is not None and not activation_retention.empty:
        st.markdown("### 🔄 Player Retention & Activation Analysis")
        
        retention_metrics = RoninAnalytics.calculate_retention_metrics(activation_retention)
        
        if retention_metrics:
            # Retention metrics visualization
            retention_viz_data = []
            for project, metrics in retention_metrics.items():
                retention_viz_data.append({
                    'Game': project,
                    '1-Week Retention': metrics['avg_1w_retention'] * 100,
                    '4-Week Retention': metrics['avg_4w_retention'] * 100,
                    'Retention Stability': metrics['retention_stability'] * 100,
                    'User Growth': metrics['user_growth_trend'] * 100
                })
            
            retention_df = pd.DataFrame(retention_viz_data)
            
            col1, col2 = st.columns(2)
            
            with col1:
                fig_retention = px.bar(
                    retention_df,
                    x='Game',
                    y=['1-Week Retention', '4-Week Retention'],
                    title="📊 Player Retention Rates",
                    labels={'value': 'Retention Rate (%)', 'variable': 'Period'},
                    barmode='group'
                )
                fig_retention.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font_color='white',
                    xaxis_tickangle=-45,
                    height=400
                )
                st.plotly_chart(fig_retention, use_container_width=True)
            
            with col2:
                fig_stability = px.scatter(
                    retention_df,
                    x='Retention Stability',
                    y='User Growth',
                    size='1-Week Retention',
                    color='Game',
                    title="🎯 Retention vs Growth Analysis",
                    labels={'Retention Stability': 'Retention Stability (%)', 'User Growth': 'User Growth (%)'}
                )
                fig_stability.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font_color='white',
                    height=400
                )
                st.plotly_chart(fig_stability, use_container_width=True)
            
            # Retention insights
            st.markdown("### 🔍 Retention Insights")
            
            best_retention_game = max(retention_metrics.items(), key=lambda x: x[1]['avg_1w_retention'])
            most_stable_game = max(retention_metrics.items(), key=lambda x: x[1]['retention_stability'])
            fastest_growing_game = max(retention_metrics.items(), key=lambda x: x[1]['user_growth_trend'])
            
            retention_insights = [
                f"🏆 **Best 1-Week Retention**: {best_retention_game[0]} ({best_retention_game[1]['avg_1w_retention']*100:.1f}%)",
                f"📊 **Most Stable Retention**: {most_stable_game[0]} ({most_stable_game[1]['retention_stability']*100:.1f}% stability)",
                f"📈 **Fastest User Growth**: {fastest_growing_game[0]} ({fastest_growing_game[1]['user_growth_trend']*100:.1f}% growth)"
            ]
            
            for insight in retention_insights:
                st.markdown(f'<div class="insight-box">{insight}</div>', unsafe_allow_html=True)
    
    else:
        st.info("📊 Player retention data will be displayed when available from Dune Analytics")

# === TOKEN INTELLIGENCE SECTION ===
elif section == "Token Intelligence":
    st.markdown("## 💰 Token Intelligence & DeFi Analytics Dashboard")
    
    # Token metrics overview
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "💎 RON Price",
            f"${coingecko_data['price_usd']:.4f}",
            delta=f"{coingecko_data.get('price_change_24h_pct', 0):+.2f}%"
        )
    
    with col2:
        market_cap = coingecko_data['market_cap_usd']
        st.metric(
            "🏦 Market Cap",
            f"${market_cap:,.0f}" if market_cap < 1e9 else f"${market_cap/1e9:.2f}B",
            delta=f"#{coingecko_data.get('market_cap_rank', 'N/A')}"
        )
    
    with col3:
        volume_24h = coingecko_data['volume_24h_usd']
        st.metric(
            "📊 24h Volume",
            f"${volume_24h:,.0f}" if volume_24h < 1e6 else f"${volume_24h/1e6:.1f}M",
            help="Trading volume in the last 24 hours"
        )
    
    with col4:
        tvl = coingecko_data.get('tvl_usd', 0)
        st.metric(
            "🏛️ TVL",
            f"${tvl:,.0f}" if tvl < 1e6 else f"${tvl/1e6:.1f}M",
            help="Total Value Locked in DeFi protocols"
        )
    
    with col5:
        mcap_tvl_ratio = coingecko_data.get('mcap_to_tvl_ratio', 0)
        st.metric(
            "📈 MCap/TVL Ratio",
            f"{mcap_tvl_ratio:.2f}",
            help="Market Cap to TVL ratio - lower values may indicate undervaluation"
        )
    
    st.markdown("---")
    
    # Price Performance Analysis
    st.markdown("### 📈 Price Performance Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Price performance metrics
        price_changes = {
            '24 Hours': coingecko_data.get('price_change_24h_pct', 0),
            '7 Days': coingecko_data.get('price_change_7d_pct', 0),
            '30 Days': coingecko_data.get('price_change_30d_pct', 0)
        }
        
        periods = list(price_changes.keys())
        changes = list(price_changes.values())
        colors = ['#FF6B35' if x >= 0 else '#FF6B6B' for x in changes]
        
        fig_price_perf = px.bar(
            x=periods,
            y=changes,
            title="💹 RON Price Performance",
            labels={'x': 'Period', 'y': 'Price Change (%)'},
            color=changes,
            color_continuous_scale=['#FF6B6B', '#FFD700', '#4ECDC4']
        )
        fig_price_perf.update_traces(
            text=[f"{x:+.1f}%" for x in changes],
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>Change: %{y:+.2f}%<extra></extra>'
        )
        fig_price_perf.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.7)
        fig_price_perf.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            showlegend=False,
            height=400
        )
        st.plotly_chart(fig_price_perf, use_container_width=True)
    
    with col2:
        # Token supply metrics
        circulating_supply = coingecko_data.get('circulating_supply', 0)
        total_supply = coingecko_data.get('total_supply', 0)
        supply_ratio = (circulating_supply / total_supply * 100) if total_supply > 0 else 0
        
        fig_supply = go.Figure(go.Indicator(
            mode="gauge+number",
            value=supply_ratio,
            title={'text': "🪙 Circulating Supply Ratio"},
            domain={'x': [0, 1], 'y': [0, 1]},
            gauge={
                'axis': {'range': [None, 100], 'ticksuffix': '%'},
                'bar': {'color': "#00D4FF"},
                'steps': [
                    {'range': [0, 30], 'color': 'rgba(255, 107, 107, 0.3)'},
                    {'range': [30, 70], 'color': 'rgba(255, 215, 0, 0.3)'},
                    {'range': [70, 100], 'color': 'rgba(78, 205, 196, 0.3)'}
                ]
            }
        ))
        fig_supply.update_layout(
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white'
        )
        st.plotly_chart(fig_supply, use_container_width=True)
    
    # WRON Trading Analysis
    if wron_volume_liquidity is not None and not wron_volume_liquidity.empty:
        st.markdown("### 🔄 WRON Trading Activity on Katana DEX")
        
        wron_viz = wron_volume_liquidity.copy()
        safe_date_conversion(wron_viz, 'date')
        
        # Volume and liquidity trends
        fig_wron = make_subplots(
            rows=2, cols=1,
            subplot_titles=('💰 Daily Trading Volume by Pair', '🏊 Liquidity Pool Depth'),
            vertical_spacing=0.1
        )
        
        # Trading volume
        for pair in wron_viz['pair'].unique():
            pair_data = wron_viz[wron_viz['pair'] == pair]
            fig_wron.add_trace(
                go.Scatter(
                    x=pair_data['date'],
                    y=pair_data['volume_usd'],
                    mode='lines+markers',
                    name=f"{pair} Volume",
                    hovertemplate='<b>%{fullData.name}</b><br>Date: %{x}<br>Volume: $%{y:,.0f}<extra></extra>'
                ),
                row=1, col=1
            )
        
        # Liquidity depth
        for pair in wron_viz['pair'].unique():
            pair_data = wron_viz[wron_viz['pair'] == pair]
            fig_wron.add_trace(
                go.Scatter(
                    x=pair_data['date'],
                    y=pair_data['liquidity_usd'],
                    mode='lines',
                    name=f"{pair} Liquidity",
                    line=dict(dash='dot'),
                    hovertemplate='<b>%{fullData.name}</b><br>Date: %{x}<br>Liquidity: $%{y:,.0f}<extra></extra>',
                    showlegend=False
                ),
                row=2, col=1
            )
        
        fig_wron.update_layout(
            height=700,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            hovermode='x unified'
        )
        st.plotly_chart(fig_wron, use_container_width=True)
        
        # Trading pairs analysis
        st.markdown("### 📊 Trading Pairs Performance")
        
        if len(wron_viz) > 0:
            pair_summary = wron_viz.groupby('pair').agg({
                'volume_usd': ['sum', 'mean'],
                'liquidity_usd': 'mean',
                'trades': 'sum' if 'trades' in wron_viz.columns else lambda x: len(x),
                'unique_traders': 'sum' if 'unique_traders' in wron_viz.columns else lambda x: len(x)
            }).round(0)
            
            pair_summary.columns = ['Total Volume', 'Avg Daily Volume', 'Avg Liquidity', 'Total Trades', 'Total Traders']
            pair_summary = pair_summary.sort_values('Total Volume', ascending=False)
            
            st.dataframe(
                pair_summary,
                use_container_width=True,
                column_config={
                    "Total Volume": st.column_config.NumberColumn("Total Volume ($)", format="$%.0f"),
                    "Avg Daily Volume": st.column_config.NumberColumn("Avg Daily Volume ($)", format="$%.0f"),
                    "Avg Liquidity": st.column_config.NumberColumn("Avg Liquidity ($)", format="$%.0f"),
                    "Total Trades": st.column_config.NumberColumn("Total Trades", format="%.0f"),
                    "Total Traders": st.column_config.NumberColumn("Total Traders", format="%.0f")
                }
            )
    
    # Whale Activity Analysis
    if wron_whale_tracking is not None and not wron_whale_tracking.empty:
        st.markdown("### 🐋 Whale Trading Analysis")
        
        whale_impact_score = RoninAnalytics.calculate_whale_impact_score(wron_whale_tracking, wron_volume_liquidity)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Whale distribution
            whale_viz = wron_whale_tracking.copy()
            whale_viz['Volume Category'] = pd.cut(
                whale_viz['total_volume_usd'],
                bins=[0, 1000000, 5000000, float('inf')],
                labels=['$1M-$1M', '$1M-$5M', '$5M+']
            )
            
            whale_distribution = whale_viz['Volume Category'].value_counts()
            
            fig_whale_dist = px.pie(
                values=whale_distribution.values,
                names=whale_distribution.index,
                title="🐋 Whale Distribution by Volume",
                color_discrete_sequence=['#FF6B35', '#00D4FF', '#4ECDC4']
            )
            fig_whale_dist.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white',
                height=400
            )
            st.plotly_chart(fig_whale_dist, use_container_width=True)
        
        with col2:
            # Whale impact gauge
            fig_whale_impact = go.Figure(go.Indicator(
                mode="gauge+number",
                value=whale_impact_score,
                title={'text': "🎯 Whale Market Impact"},
                domain={'x': [0, 1], 'y': [0, 1]},
                gauge={
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "#FF6B35"},
                    'steps': [
                        {'range': [0, 30], 'color': 'rgba(78, 205, 196, 0.3)'},
                        {'range': [30, 70], 'color': 'rgba(255, 215, 0, 0.3)'},
                        {'range': [70, 100], 'color': 'rgba(255, 107, 107, 0.3)'}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 80
                    }
                }
            ))
            fig_whale_impact.update_layout(
                height=400,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white'
            )
            st.plotly_chart(fig_whale_impact, use_container_width=True)
        
        # Top whale traders
        st.markdown("### 🏆 Top WRON Whale Traders")
        
        top_whales = wron_whale_tracking.nlargest(10, 'total_volume_usd').copy()
        top_whales['Profit/Loss Status'] = top_whales['profit_loss_usd'].apply(
            lambda x: "🟢 Profitable" if x > 0 else "🔴 Loss" if x < 0 else "⚪ Break-even"
        )
        top_whales['ROI'] = ((top_whales['profit_loss_usd'] / top_whales['total_volume_usd']) * 100).round(2)
        
        display_whales = top_whales[[
            'trader_address', 'total_volume_usd', 'trade_count', 'avg_trade_size_usd',
            'profit_loss_usd', 'Profit/Loss Status', 'ROI'
        ]].copy()
        
        st.dataframe(
            display_whales,
            use_container_width=True,
            column_config={
                "trader_address": st.column_config.TextColumn("Trader Address"),
                "total_volume_usd": st.column_config.NumberColumn("Total Volume ($)", format="$%.0f"),
                "trade_count": st.column_config.NumberColumn("Trades", format="%.0f"),
                "avg_trade_size_usd": st.column_config.NumberColumn("Avg Trade Size ($)", format="$%.0f"),
                "profit_loss_usd": st.column_config.NumberColumn("P&L ($)", format="$%.0f"),
                "Profit/Loss Status": st.column_config.TextColumn("Status"),
                "ROI": st.column_config.NumberColumn("ROI (%)", format="%.2f%%")
            },
            hide_index=True
        )
    
    # Hourly Trading Patterns
    if wron_hourly_activity is not None and not wron_hourly_activity.empty:
        st.markdown("### ⏰ WRON Trading Patterns by Hour (UTC)")
        
        fig_hourly = make_subplots(
            rows=2, cols=1,
            subplot_titles=('💰 Average Hourly Volume', '👥 Average Hourly Traders'),
            vertical_spacing=0.12
        )
        
        fig_hourly.add_trace(
            go.Bar(
                x=wron_hourly_activity['hour'],
                y=wron_hourly_activity['avg_volume_usd'],
                name='Volume',
                marker_color='#FF6B35',
                hovertemplate='<b>Hour %{x}:00</b><br>Avg Volume: $%{y:,.0f}<extra></extra>'
            ),
            row=1, col=1
        )
        
        fig_hourly.add_trace(
            go.Bar(
                x=wron_hourly_activity['hour'],
                y=wron_hourly_activity['avg_unique_traders'],
                name='Traders',
                marker_color='#00D4FF',
                hovertemplate='<b>Hour %{x}:00</b><br>Avg Traders: %{y:.0f}<extra></extra>'
            ),
            row=2, col=1
        )
        
        fig_hourly.update_layout(
            height=600,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            showlegend=False
        )
        fig_hourly.update_xaxes(title_text="Hour (UTC)", row=2, col=1)
        st.plotly_chart(fig_hourly, use_container_width=True)
    
    # Token Intelligence Insights
    st.markdown("### 🔍 Token Intelligence Insights")
    
    token_insights = []
    
    # Price performance insights
    price_24h = coingecko_data.get('price_change_24h_pct', 0)
    if price_24h > 10:
        token_insights.append(f"🚀 Strong 24h performance: RON up {price_24h:.1f}% - momentum building")
    elif price_24h < -10:
        token_insights.append(f"📉 RON experiencing volatility: down {abs(price_24h):.1f}% in 24h")
    
    # Whale impact insights
    if whale_impact_score > 70:
        token_insights.append(f"🐋 High whale concentration detected ({whale_impact_score:.1f}/100) - market vulnerable to large trades")
    elif whale_impact_score < 30:
        token_insights.append(f"👥 Healthy trading distribution ({whale_impact_score:.1f}/100) - reduced whale manipulation risk")
    
    # TVL insights
    mcap_tvl = coingecko_data.get('mcap_to_tvl_ratio', 4)
    if mcap_tvl < 2:
        token_insights.append(f"💎 Potentially undervalued: MCap/TVL ratio of {mcap_tvl:.2f} suggests strong protocol usage relative to valuation")
    elif mcap_tvl > 10:
        token_insights.append(f"⚠️ High valuation metrics: MCap/TVL ratio of {mcap_tvl:.2f} - monitor for sustainability")
    
    for insight in token_insights:
        st.markdown(f'<div class="insight-box">{insight}</div>', unsafe_allow_html=True)

# === USER ANALYTICS SECTION ===
elif section == "User Analytics":
    st.markdown("## 👥 User Behavior & Segmentation Analytics")
    
    # User segment overview
    if ron_segmented_holders is not None and not ron_segmented_holders.empty:
        st.markdown("### 🧑‍💻 RON Holder Segmentation Analysis")
        
        total_holders = ron_segmented_holders['holders'].sum()
        total_balance = ron_segmented_holders['total_balance'].sum()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("👥 Total Holders", f"{total_holders:,}")
        with col2:
            st.metric("💰 Total RON Supply", f"{total_balance:,.0f}")
        with col3:
            avg_balance = total_balance / total_holders if total_holders > 0 else 0
            st.metric("📊 Average Balance", f"{avg_balance:.2f} RON")
        with col4:
            # Calculate Gini coefficient for distribution analysis
            sorted_balances = ron_segmented_holders.sort_values('avg_balance')
            gini = safe_numeric_operation(
                lambda: (2 * sum((i + 1) * balance for i, balance in enumerate(sorted_balances['avg_balance']))) / 
                        (len(sorted_balances) * sorted_balances['avg_balance'].sum()) - 
                        (len(sorted_balances) + 1) / len(sorted_balances),
                default_value=0.5
            )
            st.metric("📈 Wealth Distribution", f"{gini:.3f}", help="Gini coefficient (0 = equal, 1 = unequal)")
        
        # Enhanced holder distribution visualization
        col1, col2 = st.columns(2)
        
        with col1:
            # Holder count distribution
            fig_holder_count = px.treemap(
                ron_segmented_holders,
                values='holders',
                names='balance_range',
                title='🏠 Holder Count Distribution',
                color='holders',
                color_continuous_scale=['#FF6B35', '#F7931E', '#00D4FF']
            )
            fig_holder_count.update_layout(
                height=450,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white'
            )
            st.plotly_chart(fig_holder_count, use_container_width=True)
        
        with col2:
            # Balance concentration
            fig_balance_conc = px.funnel(
                ron_segmented_holders.sort_values('total_balance', ascending=False),
                y='balance_range',
                x='total_balance',
                title='💎 Token Concentration by Tier',
                color='total_balance',
                color_continuous_scale=['#4ECDC4', '#00D4FF', '#FF6B35']
            )
            fig_balance_conc.update_layout(
                height=450,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white'
            )
            st.plotly_chart(fig_balance_conc, use_container_width=True)
        
        # Detailed segmentation analysis
        st.markdown("### 📊 Detailed Holder Segmentation")
        
        holder_analysis = ron_segmented_holders.copy()
        holder_analysis['Holder %'] = (holder_analysis['holders'] / total_holders * 100).round(2)
        holder_analysis['Balance %'] = (holder_analysis['total_balance'] / total_balance * 100).round(2)
        holder_analysis['Concentration Index'] = (
            holder_analysis['Balance %'] / holder_analysis['Holder %']
        ).round(2)
        
        st.dataframe(
            holder_analysis[['balance_range', 'holders', 'total_balance', 'avg_balance', 'Holder %', 'Balance %', 'Concentration Index']],
            use_container_width=True,
            column_config={
                "balance_range": st.column_config.TextColumn("Balance Range"),
                "holders": st.column_config.NumberColumn("Holders", format="%d"),
                "total_balance": st.column_config.NumberColumn("Total Balance (RON)", format="%.0f"),
                "avg_balance": st.column_config.NumberColumn("Avg Balance (RON)", format="%.2f"),
                "Holder %": st.column_config.NumberColumn("% of Holders", format="%.2f%%"),
                "Balance %": st.column_config.NumberColumn("% of Supply", format="%.2f%%"),
                "Concentration Index": st.column_config.NumberColumn("Concentration", format="%.2f", help="Balance%/Holder% - higher values indicate concentration")
            },
            hide_index=True
        )
    
    # Weekly trading segmentation
    if wron_weekly_segmentation is not None and not wron_weekly_segmentation.empty:
        st.markdown("### 📈 Weekly Trading User Segmentation")
        
        weekly_viz = wron_weekly_segmentation.copy()
        safe_date_conversion(weekly_viz, 'week')
        
        # Trading volume by user type
        fig_weekly_volume = px.area(
            weekly_viz,
            x='week',
            y=['retail_volume_usd', 'small_whale_volume_usd', 'large_whale_volume_usd'],
            title='💰 Trading Volume by User Segment',
            labels={'value': 'Volume ($)', 'week': 'Week'},
            color_discrete_sequence=['#FF6B35', '#00D4FF', '#4ECDC4']
        )
        fig_weekly_volume.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            height=500,
            hovermode='x unified'
        )
        st.plotly_chart(fig_weekly_volume, use_container_width=True)
        
        # User count trends
        fig_weekly_users = px.line(
            weekly_viz,
            x='week',
            y=['retail_traders', 'small_whales', 'large_whales'],
            title='👥 Active Trader Count by Segment',
            labels={'value': 'Active Traders', 'week': 'Week'},
            color_discrete_sequence=['#FF6B35', '#00D4FF', '#4ECDC4']
        )
        fig_weekly_users.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            height=400,
            hovermode='x unified'
        )
        st.plotly_chart(fig_weekly_users, use_container_width=True)
        
        # Calculate user behavior metrics
        if len(weekly_viz) > 1:
            latest_week = weekly_viz.iloc[-1]
            prev_week = weekly_viz.iloc[-2]
            
            st.markdown("### 📊 Weekly User Behavior Changes")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                retail_change = ((latest_week['retail_traders'] - prev_week['retail_traders']) / prev_week['retail_traders'] * 100)
                st.metric(
                    "🛒 Retail Traders",
                    f"{latest_week['retail_traders']:,.0f}",
                    delta=f"{retail_change:+.1f}%"
                )
            
            with col2:
                small_whale_change = ((latest_week['small_whales'] - prev_week['small_whales']) / prev_week['small_whales'] * 100)
                st.metric(
                    "🐋 Small Whales",
                    f"{latest_week['small_whales']:,.0f}",
                    delta=f"{small_whale_change:+.1f}%"
                )
            
            with col3:
                large_whale_change = ((latest_week['large_whales'] - prev_week['large_whales']) / prev_week['large_whales'] * 100)
                st.metric(
                    "🐳 Large Whales",
                    f"{latest_week['large_whales']:,.0f}",
                    delta=f"{large_whale_change:+.1f}%"
                )
    
    # Player retention deep dive
    if activation_retention is not None and not activation_retention.empty:
        st.markdown("### 🔄 Advanced Player Retention Analysis")
        
        retention_viz = activation_retention.copy()
        safe_date_conversion(retention_viz, 'week')
        
        # Retention heatmap by game
        retention_pivot = retention_viz.pivot_table(
            index='project_name',
            columns=retention_viz['week'].dt.strftime('%Y-%m'),
            values='retention_rate_1w',
            aggfunc='mean'
        ).fillna(0)
        
        if not retention_pivot.empty:
            fig_retention_heatmap = px.imshow(
                retention_pivot,
                title='🔥 1-Week Retention Heatmap by Game & Month',
                labels={'color': '1-Week Retention Rate'},
                aspect='auto',
                color_continuous_scale='RdYlGn'
            )
            fig_retention_heatmap.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white',
                height=500
            )
            st.plotly_chart(fig_retention_heatmap, use_container_width=True)
        
        # Cohort analysis
        st.markdown("### 👥 User Cohort Analysis")
        
        cohort_data = retention_viz.groupby(['project_name', 'week']).agg({
            'new_users': 'sum',
            'retained_users_1w': 'sum',
            'retention_rate_1w': 'mean'
        }).reset_index()
        
        # Calculate cohort retention curves for top games
        top_games = cohort_data.groupby('project_name')['new_users'].sum().nlargest(3).index
        
        fig_cohort = go.Figure()
        
        for game in top_games:
            game_data = cohort_data[cohort_data['project_name'] == game].sort_values('week')
            
            fig_cohort.add_trace(
                go.Scatter(
                    x=game_data['week'],
                    y=game_data['retention_rate_1w'],
                    mode='lines+markers',
                    name=f"{game} Retention",
                    hovertemplate='<b>%{fullData.name}</b><br>Week: %{x}<br>Retention: %{y:.1%}<extra></extra>'
                )
            )
        
        fig_cohort.update_layout(
            title='📈 Retention Rate Trends by Game',
            xaxis_title='Week',
            yaxis_title='1-Week Retention Rate',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            height=400,
            hovermode='x unified'
        )
        st.plotly_chart(fig_cohort, use_container_width=True)
    
    # User Analytics Insights
    st.markdown("### 🔍 User Behavior Insights")
    
    user_insights = []
    
    if ron_segmented_holders is not None and not ron_segmented_holders.empty:
        # Whale concentration insight
        whale_holders = ron_segmented_holders[
            ron_segmented_holders['balance_range'].isin(['10K-100K RON', '100K+ RON'])
        ]['holders'].sum()
        whale_percentage = (whale_holders / total_holders * 100) if total_holders > 0 else 0
        
        if whale_percentage > 5:
            user_insights.append(f"🐋 High whale concentration: {whale_percentage:.1f}% of holders control significant token supply")
        
        # Distribution analysis
        small_holders = ron_segmented_holders[
            ron_segmented_holders['balance_range'].isin(['0-1 RON', '1-10 RON'])
        ]['holders'].sum()
        small_holder_percentage = (small_holders / total_holders * 100) if total_holders > 0 else 0
        
        if small_holder_percentage > 60:
            user_insights.append(f"👥 Broad adoption: {small_holder_percentage:.1f}% are small holders, indicating widespread distribution")
    
    if wron_weekly_segmentation is not None and not wron_weekly_segmentation.empty and len(wron_weekly_segmentation) > 4:
        # Trading growth insight
        recent_weeks = wron_weekly_segmentation.tail(4)
        retail_growth = ((recent_weeks['retail_traders'].iloc[-1] - recent_weeks['retail_traders'].iloc[0]) / recent_weeks['retail_traders'].iloc[0] * 100)
        
        if retail_growth > 20:
            user_insights.append(f"📈 Strong retail growth: {retail_growth:.1f}% increase in retail traders over last 4 weeks")
        elif retail_growth < -20:
            user_insights.append(f"📉 Retail trader decline: {abs(retail_growth):.1f}% decrease over last 4 weeks - monitor engagement")
    
    if not user_insights:
        user_insights.append("📊 User analytics show stable ecosystem participation across different holder segments")
    
    for insight in user_insights:
        st.markdown(f'<div class="insight-box">{insight}</div>', unsafe_allow_html=True)

# Footer with enhanced status information
st.markdown("---")

data_status = fetcher.get_data_status()
last_update = data_status['last_update']

st.markdown(f"""
<div style="text-align: center; color: #888; padding: 20px;">
    <p><strong>⚡ Ronin Ecosystem Tracker</strong> | Real-time Analytics for Gaming Economy Intelligence</p>
    <p>🔗 Data Sources: CoinGecko Pro API • Dune Analytics • On-chain Ronin Network</p>
    <p>📅 Last Updated: {last_update} | 🔄 Cache TTL: 24 hours</p>
    <p style="font-size: 0.9em;">💡 <em>Analytics update automatically - refresh for latest insights</em></p>
    <p style="font-size: 0.8em;">🛠️ Built with Streamlit • Plotly • Advanced Analytics Engine</p>
    <div style="margin-top: 15px;">
        <span style="font-size: 0.8em; color: #666;">
            Status: CoinGecko <span class="status-indicator status-{('live' if data_status['coingecko_status'] == 'success' else 'fallback')}">
            {'Live' if data_status['coingecko_status'] == 'success' else 'Demo'}</span> • 
            Dune <span class="status-indicator status-{('live' if data_status['dune_status'] == 'success' else 'fallback')}">
            {'Live' if data_status['dune_status'] == 'success' else 'Demo'}</span>
        </span>
    </div>
</div>
""", unsafe_allow_html=True)