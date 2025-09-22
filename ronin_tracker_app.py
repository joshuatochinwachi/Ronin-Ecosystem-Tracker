"""
Ronin Ecosystem Tracker - Professional Analytics Dashboard
A comprehensive real-time analytics platform for Ronin blockchain gaming economy
Version: 2.0 - Enhanced with detailed insights and professional visualizations
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import os
import time
import hashlib
import joblib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
import logging
from dune_client.client import DuneClient
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Ronin Ecosystem Tracker - Professional Analytics",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1f77b4 0%, #17becf 50%, #2ca02c 100%);
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 25px;
        text-align: center;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    .main-header h1 {
        color: white;
        margin: 0;
        font-size: 2.8rem;
        font-weight: 700;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .main-header p {
        color: rgba(255,255,255,0.9);
        font-size: 1.2rem;
        margin: 10px 0 0 0;
    }
    
    .metric-card {
        background: linear-gradient(145deg, #ffffff, #f8f9fa);
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin: 10px 0;
        border-left: 4px solid #1f77b4;
    }
    
    .alert-critical {
        border-left: 5px solid #d62728;
        background: #2d1517;
        color: #ffffff;
        padding: 15px;
        margin: 10px 0;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(214, 39, 40, 0.2);
    }

    .alert-high {
        border-left: 5px solid #ff7f0e;
        background: #2d1f0a;
        color: #ffffff;
        padding: 15px;
        margin: 10px 0;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(255, 127, 14, 0.2);
    }

    .alert-medium {
        border-left: 5px solid #2ca02c;
        background: #0f1f0f;
        color: #ffffff;
        padding: 15px;
        margin: 10px 0;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(44, 160, 44, 0.2);
    }

    .insight-box {
        background: #1e3a5f;
        border: 1px solid #1f77b4;
        color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        margin: 15px 0;
    }

    .kpi-container {
        background: #2c3e50;
        color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        border: 1px solid #34495e;
    }

    .kpi-container h4 {
        color: #3498db !important;
        margin-bottom: 10px;
    }

    .kpi-container p {
        color: #ecf0f1 !important;
        margin: 5px 0;
    }
    
    @media (max-width: 768px) {
        .main-header h1 { font-size: 2rem; }
        .metric-card { padding: 15px; }
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        justify-content: center;
        background: linear-gradient(90deg, #f8f9fa, #e9ecef);
        padding: 10px;
        border-radius: 15px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 60px;
        padding: 12px 24px;
        background: linear-gradient(145deg, #ffffff, #f8f9fa);
        border-radius: 30px;
        color: #1f77b4;
        font-weight: 600;
        font-size: 16px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(145deg, #1f77b4, #17becf);
        color: white;
        box-shadow: 0 4px 8px rgba(31, 119, 180, 0.3);
    }
    
    .sidebar-header {
        background: linear-gradient(135deg, #1f77b4, #17becf);
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
        text-align: center;
        color: white;
        font-weight: 600;
    }
    
    .dataframe {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# Configuration with 24-hour caching
class Config:
    def __init__(self):
        self.dune_api_key = os.getenv("DEFI_JOSH_DUNE_QUERY_API_KEY")
        self.coingecko_api_key = os.getenv("COINGECKO_PRO_API_KEY")
        
        # Dune query IDs
        self.dune_queries = {
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
        
        self.cache_duration = 86400  # 24 hours
        self.whale_threshold = 50000  # USD
        
        if not self.dune_api_key or not self.coingecko_api_key:
            st.error("Please set DEFI_JOSH_DUNE_QUERY_API_KEY and COINGECKO_PRO_API_KEY in your environment variables")

config = Config()

# Enhanced Data Manager with 24-hour caching
class DataManager:
    def __init__(self):
        self.cache_dir = "data"
        os.makedirs(self.cache_dir, exist_ok=True)
        
        if config.dune_api_key:
            self.dune_client = DuneClient(config.dune_api_key)
        
        self.session = requests.Session()
        if config.coingecko_api_key:
            self.session.headers.update({'x-cg-pro-api-key': config.coingecko_api_key})
    
    def _get_cache_path(self, key: str) -> str:
        safe_key = hashlib.md5(key.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{safe_key}.joblib")
    
    def _is_cache_valid(self, filepath: str) -> bool:
        if not os.path.exists(filepath):
            return False
        file_age = time.time() - os.path.getmtime(filepath)
        return file_age < config.cache_duration
    
    def get_cached_data(self, key: str) -> Optional[pd.DataFrame]:
        filepath = self._get_cache_path(key)
        if self._is_cache_valid(filepath):
            try:
                return joblib.load(filepath)
            except Exception as e:
                logger.warning(f"Cache read error for {key}: {e}")
        return None
    
    def cache_data(self, key: str, data: pd.DataFrame) -> None:
        filepath = self._get_cache_path(key)
        try:
            joblib.dump(data, filepath)
        except Exception as e:
            logger.warning(f"Cache write error for {key}: {e}")
    
    @st.cache_data(ttl=86400)  # 24-hour cache
    def fetch_ron_market_data(_self) -> dict:
        try:
            url = "https://pro-api.coingecko.com/api/v3/coins/ronin"
            response = _self.session.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            market_data = data.get("market_data", {})
            st.session_state.last_data_refresh = datetime.now()
            return {
                'name': data.get('name'),
                'symbol': data.get('symbol'),
                'current_price_usd': market_data.get('current_price', {}).get('usd'),
                'market_cap_usd': market_data.get('market_cap', {}).get('usd'),
                'volume_24h_usd': market_data.get('total_volume', {}).get('usd'),
                'circulating_supply': market_data.get('circulating_supply'),
                'total_supply': market_data.get('total_supply'),
                'price_change_24h': market_data.get('price_change_percentage_24h'),
                'price_change_7d': market_data.get('price_change_percentage_7d'),
                'fdv': market_data.get('fully_diluted_valuation', {}).get('usd'),
                'tvl': market_data.get('total_value_locked', {}).get('usd'),
                'last_updated': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to fetch RON market data: {e}")
            return {}
    
    @st.cache_data(ttl=86400)  # 24-hour cache
    def fetch_dune_data(_self, query_key: str) -> pd.DataFrame:
        # Check cache first
        cached = _self.get_cached_data(query_key)
        if cached is not None:
            return cached
        
        # Fetch from API
        if not hasattr(_self, 'dune_client'):
            return pd.DataFrame()
        
        try:
            query_id = config.dune_queries[query_key]
            result = _self.dune_client.get_latest_result(query_id)
            df = pd.DataFrame(result.result.rows)
            
            # Clean and process data
            df = _self._clean_dataframe(df, query_key)
            
            # Cache the result
            _self.cache_data(query_key, df)
            st.session_state.last_data_refresh = datetime.now()
            return df
        except Exception as e:
            logger.error(f"Failed to fetch {query_key}: {e}")
            return pd.DataFrame()
    
    def _clean_dataframe(self, df: pd.DataFrame, query_key: str) -> pd.DataFrame:
        if df.empty:
            return df
        
        # Replace None values
        df = df.replace([None, 'None', ''], pd.NA)
        
        # Specific cleaning based on data type
        if query_key == 'games_overall_activity':
            numeric_cols = ['transaction_count', 'unique_players', 'total_volume_ron_sent_to_game', 'avg_gas_price_in_gwei']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        elif query_key == 'ronin_daily_activity':
            if 'day' in df.columns:
                df['day'] = pd.to_datetime(df['day'], errors='coerce')
            numeric_cols = ['daily_transactions', 'active_wallets', 'avg_gas_price_in_gwei']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        elif query_key == 'nft_collections':
            # Rename columns for consistency and readability
            column_mapping = {
                'floor_ron': 'floor_price_ron',
                'floor_usd': 'floor_price_usd',
                'volume_ron': 'sales_volume_ron',
                'volume_usd': 'sales_volume_usd',
                'royalties_usd': 'creator_royalties_usd',
                'nft_contract_address': 'contract_address',
                'generated platform fees (USD)': 'platform_fees_usd',
                'generated Ronin fees (USD)': 'ronin_fees_usd'
            }
            df = df.rename(columns=column_mapping)
            
            # Calculate total revenue
            revenue_cols = ['platform_fees_usd', 'ronin_fees_usd', 'creator_royalties_usd']
            for col in revenue_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
            if all(col in df.columns for col in revenue_cols):
                df['total_revenue_usd'] = df[revenue_cols].sum(axis=1)
        
        # Replace WRON with RON in column names and data
        df.columns = [col.replace('WRON', 'RON').replace('wron', 'ron') for col in df.columns]
        
        # Fill text columns with 'Unknown'
        text_cols = df.select_dtypes(include=['object']).columns
        for col in text_cols:
            df[col] = df[col].fillna('Unknown')
        
        return df
    
    def load_all_data(self, time_filter: str = "All time") -> dict:
        data = {}
        
        # Create progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        total_queries = len(config.dune_queries) + 1  # +1 for CoinGecko
        
        # Fetch RON market data
        status_text.text("🔄 Fetching RON market data...")
        data['ron_market'] = self.fetch_ron_market_data()
        progress_bar.progress(1 / total_queries)
        
        # Fetch Dune data
        for i, query_key in enumerate(config.dune_queries.keys()):
            status_text.text(f"🔄 Fetching {query_key.replace('_', ' ').title()}...")
            df = self.fetch_dune_data(query_key)
            
            # Apply time filter
            df = self._apply_time_filter(df, time_filter)
            
            data[query_key] = df
            progress_bar.progress((i + 2) / total_queries)
        
        progress_bar.empty()
        status_text.empty()
        
        return data
    
    def _apply_time_filter(self, df: pd.DataFrame, time_filter: str) -> pd.DataFrame:
        if df.empty or time_filter == "All time":
            return df
        
        # Find date columns
        date_cols = [col for col in df.columns if 'day' in col.lower() or 'date' in col.lower() or 'week' in col.lower()]
        
        if not date_cols:
            return df
        
        date_col = date_cols[0]
        
        try:
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
            
            now = datetime.now()
            
            if time_filter == "Last 7 days":
                cutoff = now - timedelta(days=7)
            elif time_filter == "Last 30 days":
                cutoff = now - timedelta(days=30)
            elif time_filter == "Last 90 days":
                cutoff = now - timedelta(days=90)
            else:
                return df
            
            return df[df[date_col] >= cutoff]
        except:
            return df
        # Enhanced Analytics Engine with detailed insights
class AnalyticsEngine:
    def __init__(self):
        pass
    
    def calculate_network_health_score(self, daily_activity: pd.DataFrame) -> dict:
        if daily_activity.empty:
            return {'score': 0, 'status': 'No Data', 'metrics': {}, 'insights': []}
        
        recent_data = daily_activity.tail(7)
        scores = []
        metrics = {}
        insights = []
        
        # Gas price health (0-100)
        if 'avg_gas_price_in_gwei' in recent_data.columns:
            avg_gas = recent_data['avg_gas_price_in_gwei'].mean()
            gas_trend = recent_data['avg_gas_price_in_gwei'].tail(3).mean() - recent_data['avg_gas_price_in_gwei'].head(3).mean()
            
            if avg_gas <= 15:
                gas_score = 100
                insights.append(f"Excellent gas efficiency at {avg_gas:.1f} GWEI")
            elif avg_gas <= 25:
                gas_score = 70
                insights.append(f"Moderate gas prices at {avg_gas:.1f} GWEI")
            elif avg_gas <= 40:
                gas_score = 40
                insights.append(f"High gas prices at {avg_gas:.1f} GWEI - Network congested")
            else:
                gas_score = 20
                insights.append(f"Critical gas prices at {avg_gas:.1f} GWEI - Severe congestion")
            
            if gas_trend > 0:
                insights.append(f"Gas prices trending up by {gas_trend:.1f} GWEI")
            else:
                insights.append(f"Gas prices trending down by {abs(gas_trend):.1f} GWEI")
            
            scores.append(gas_score)
            metrics['avg_gas_price'] = avg_gas
            metrics['gas_trend'] = gas_trend
        
        # Transaction volume health (0-100)
        if 'daily_transactions' in recent_data.columns:
            avg_tx = recent_data['daily_transactions'].mean()
            tx_growth = ((recent_data['daily_transactions'].tail(3).mean() - 
                         recent_data['daily_transactions'].head(3).mean()) / 
                        recent_data['daily_transactions'].head(3).mean()) * 100
            
            if avg_tx >= 100000:
                tx_score = 100
                insights.append(f"Excellent transaction volume: {avg_tx:,.0f} daily")
            elif avg_tx >= 50000:
                tx_score = 80
                insights.append(f"Good transaction volume: {avg_tx:,.0f} daily")
            elif avg_tx >= 10000:
                tx_score = 60
                insights.append(f"Moderate transaction volume: {avg_tx:,.0f} daily")
            else:
                tx_score = 30
                insights.append(f"Low transaction volume: {avg_tx:,.0f} daily")
            
            if tx_growth > 10:
                insights.append(f"Transaction volume growing {tx_growth:.1f}%")
            elif tx_growth < -10:
                insights.append(f"Transaction volume declining {abs(tx_growth):.1f}%")
            
            scores.append(tx_score)
            metrics['avg_daily_transactions'] = avg_tx
            metrics['transaction_growth'] = tx_growth
        
        # Active wallet growth (0-100)
        if 'active_wallets' in recent_data.columns and len(recent_data) >= 3:
            recent_wallets = recent_data['active_wallets'].tail(3).mean()
            older_wallets = recent_data['active_wallets'].head(3).mean()
            
            if older_wallets > 0:
                growth_rate = ((recent_wallets - older_wallets) / older_wallets) * 100
                
                if growth_rate >= 15:
                    wallet_score = 100
                    insights.append(f"Excellent user growth: {growth_rate:.1f}%")
                elif growth_rate >= 5:
                    wallet_score = 80
                    insights.append(f"Good user growth: {growth_rate:.1f}%")
                elif growth_rate >= -10:
                    wallet_score = 60
                    insights.append(f"Stable user base: {growth_rate:.1f}% change")
                else:
                    wallet_score = 40
                    insights.append(f"Declining user base: {abs(growth_rate):.1f}%")
                
                scores.append(wallet_score)
                metrics['wallet_growth_rate'] = growth_rate
                metrics['active_wallets'] = recent_wallets
        
        overall_score = sum(scores) / len(scores) if scores else 0
        
        if overall_score >= 80:
            status = 'Healthy'
            status_emoji = 'checkmark'
        elif overall_score >= 60:
            status = 'Moderate'
            status_emoji = 'warning'
        elif overall_score >= 40:
            status = 'Concerning'
            status_emoji = 'alert'
        else:
            status = 'Critical'
            status_emoji = 'alert'
        
        return {
            'score': round(overall_score, 1),
            'status': status,
            'status_emoji': status_emoji,
            'metrics': metrics,
            'insights': insights
        }
    
    def analyze_spending_patterns(self, games_data: pd.DataFrame, nft_data: pd.DataFrame, 
                                defi_data: pd.DataFrame) -> dict:
        """Analyze how users spend RON across different sectors"""
        spending_analysis = {
            'sectors': {},
            'total_volume': 0,
            'user_distribution': {},
            'insights': []
        }
        
        # Gaming spending
        if not games_data.empty and 'total_volume_ron_sent_to_game' in games_data.columns:
            gaming_volume = games_data['total_volume_ron_sent_to_game'].sum()
            gaming_users = games_data['unique_players'].sum() if 'unique_players' in games_data.columns else 0
            spending_analysis['sectors']['Gaming'] = {
                'volume_ron': gaming_volume,
                'users': gaming_users,
                'avg_spend_per_user': gaming_volume / gaming_users if gaming_users > 0 else 0
            }
            spending_analysis['total_volume'] += gaming_volume
        
        # NFT spending
        if not nft_data.empty and 'sales_volume_usd' in nft_data.columns:
            nft_volume = nft_data['sales_volume_usd'].sum() / 2.5  # Approximate RON conversion
            nft_users = nft_data['holders'].sum() if 'holders' in nft_data.columns else 0
            spending_analysis['sectors']['NFT'] = {
                'volume_ron': nft_volume,
                'users': nft_users,
                'avg_spend_per_user': nft_volume / nft_users if nft_users > 0 else 0
            }
            spending_analysis['total_volume'] += nft_volume
        
        # DeFi spending
        if not defi_data.empty:
            volume_col = [col for col in defi_data.columns if 'volume' in col.lower() and ('ron' in col.lower() or 'usd' in col.lower())]
            if volume_col:
                defi_volume = defi_data[volume_col[0]].sum()
                if 'usd' in volume_col[0].lower():
                    defi_volume = defi_volume / 2.5  # Convert to RON
                
                defi_users = defi_data['Number of Unique Traders'].sum() if 'Number of Unique Traders' in defi_data.columns else 0
                spending_analysis['sectors']['DeFi'] = {
                    'volume_ron': defi_volume,
                    'users': defi_users,
                    'avg_spend_per_user': defi_volume / defi_users if defi_users > 0 else 0
                }
                spending_analysis['total_volume'] += defi_volume
        
        # Generate insights
        total_volume = spending_analysis['total_volume']
        if total_volume > 0:
            for sector, data in spending_analysis['sectors'].items():
                percentage = (data['volume_ron'] / total_volume) * 100
                spending_analysis['sectors'][sector]['percentage'] = percentage
                spending_analysis['insights'].append(
                    f"{sector}: {format_currency(data['volume_ron'], 'RON')} ({percentage:.1f}%) from {format_number(data['users'])} users"
                )
        
        return spending_analysis
    
    def detect_liquidity_flows(self, defi_data: pd.DataFrame, games_data: pd.DataFrame, 
                             nft_data: pd.DataFrame) -> dict:
        """Analyze liquidity flows across sectors"""
        flows = {
            'high_liquidity_sectors': [],
            'low_liquidity_sectors': [],
            'flow_analysis': {},
            'recommendations': []
        }
        
        # Analyze DeFi liquidity
        if not defi_data.empty:
            volume_cols = [col for col in defi_data.columns if 'volume' in col.lower()]
            if volume_cols:
                total_defi_volume = defi_data[volume_cols[0]].sum()
                flows['flow_analysis']['DeFi'] = {
                    'total_volume': total_defi_volume,
                    'liquidity_score': min(100, (total_defi_volume / 1000000) * 10)  # Normalized score
                }
                
                if total_defi_volume > 10000000:  # $10M threshold
                    flows['high_liquidity_sectors'].append('DeFi')
                    flows['recommendations'].append("DeFi sector shows high liquidity - good for institutional partnerships")
                else:
                    flows['low_liquidity_sectors'].append('DeFi')
                    flows['recommendations'].append("DeFi sector needs liquidity improvement - consider incentive programs")
        
        # Gaming liquidity analysis
        if not games_data.empty and 'total_volume_ron_sent_to_game' in games_data.columns:
            gaming_volume = games_data['total_volume_ron_sent_to_game'].sum() * 2.5  # Convert to USD
            flows['flow_analysis']['Gaming'] = {
                'total_volume': gaming_volume,
                'liquidity_score': min(100, (gaming_volume / 5000000) * 10)
            }
            
            if gaming_volume > 5000000:
                flows['high_liquidity_sectors'].append('Gaming')
                flows['recommendations'].append("Gaming sector maintains strong liquidity - ideal for new game launches")
            else:
                flows['low_liquidity_sectors'].append('Gaming')
                flows['recommendations'].append("Gaming sector could benefit from user incentives")
        
        # NFT liquidity analysis
        if not nft_data.empty and 'sales_volume_usd' in nft_data.columns:
            nft_volume = nft_data['sales_volume_usd'].sum()
            flows['flow_analysis']['NFT'] = {
                'total_volume': nft_volume,
                'liquidity_score': min(100, (nft_volume / 2000000) * 10)
            }
            
            if nft_volume > 2000000:
                flows['high_liquidity_sectors'].append('NFT')
                flows['recommendations'].append("NFT marketplace showing healthy activity - good for creators")
            else:
                flows['low_liquidity_sectors'].append('NFT')
                flows['recommendations'].append("NFT sector needs more collection launches and marketing")
        
        return flows
    
    def rank_games_by_performance(self, games_data: pd.DataFrame) -> pd.DataFrame:
        if games_data.empty:
            return pd.DataFrame()
        
        df = games_data.copy()
        
        # Normalize metrics for scoring
        metrics = ['unique_players', 'transaction_count', 'total_volume_ron_sent_to_game']
        
        for metric in metrics:
            if metric in df.columns:
                max_val = df[metric].max()
                if max_val > 0:
                    df[f'{metric}_score'] = (df[metric] / max_val * 100).round(1)
                else:
                    df[f'{metric}_score'] = 0
        
        # Calculate composite score
        score_cols = [col for col in df.columns if col.endswith('_score')]
        if score_cols:
            df['performance_score'] = df[score_cols].mean(axis=1).round(1)
        else:
            df['performance_score'] = 0
        
        # Add efficiency metrics
        if all(col in df.columns for col in ['total_volume_ron_sent_to_game', 'unique_players']):
            df['revenue_per_player'] = (df['total_volume_ron_sent_to_game'] / 
                                       df['unique_players'].replace(0, 1)).round(2)
        
        if all(col in df.columns for col in ['transaction_count', 'unique_players']):
            df['transactions_per_player'] = (df['transaction_count'] / 
                                            df['unique_players'].replace(0, 1)).round(2)
        
        return df.sort_values('performance_score', ascending=False)
    
    def generate_comprehensive_alerts(self, data: dict) -> list:
        """Generate comprehensive alerts with detailed analysis"""
        alerts = []
        
        # Network health alerts
        if 'ronin_daily_activity' in data:
            health_data = self.calculate_network_health_score(data['ronin_daily_activity'])
            if health_data['score'] < 60:
                alerts.append({
                    'type': 'Network Health',
                    'severity': 'Critical' if health_data['score'] < 40 else 'High',
                    'title': f"Network Health Score: {health_data['score']}/100",
                    'message': f"Network status is {health_data['status']}. Immediate attention required.",
                    'details': health_data['insights'][:3],
                    'timestamp': st.session_state.last_data_refresh or datetime.now(),
                    'action': 'Monitor gas prices and transaction volume closely'
                })
        
        # Whale activity alerts
        if 'wron_whale_tracking' in data and not data['wron_whale_tracking'].empty:
            whale_data = data['wron_whale_tracking']
            if 'trade_volume_usd' in whale_data.columns:
                large_trades = whale_data[whale_data['trade_volume_usd'] >= config.whale_threshold]
                if len(large_trades) > 0:
                    total_whale_volume = large_trades['trade_volume_usd'].sum()
                    alerts.append({
                        'type': 'Whale Activity',
                        'severity': 'High' if total_whale_volume > 1000000 else 'Medium',
                        'title': f"{len(large_trades)} Large Transactions Detected",
                        'message': f"Total whale volume: ${total_whale_volume:,.0f}",
                        'details': [f"Largest trade: ${large_trades['trade_volume_usd'].max():,.0f}",
                                   f"Average whale trade: ${large_trades['trade_volume_usd'].mean():,.0f}"],
                        'timestamp': st.session_state.last_data_refresh or datetime.now(),
                        'action': 'Monitor for potential market impact'
                    })
        
        # Gaming sector alerts
        if 'games_overall_activity' in data and not data['games_overall_activity'].empty:
            games_data = data['games_overall_activity']
            if 'unique_players' in games_data.columns:
                total_players = games_data['unique_players'].sum()
                if total_players < 10000:
                    alerts.append({
                        'type': 'Gaming Ecosystem',
                        'severity': 'Medium',
                        'title': 'Low Gaming Activity Detected',
                        'message': f"Total unique players: {total_players:,}",
                        'details': ['Gaming sector may need attention',
                                   'Consider marketing campaigns or incentives'],
                        'timestamp': st.session_state.last_data_refresh or datetime.now(),
                        'action': 'Review gaming partnerships and user acquisition'
                    })
        
        # Sort alerts by severity and timestamp
        severity_order = {'Critical': 0, 'High': 1, 'Medium': 2, 'Low': 3}
        alerts.sort(key=lambda x: (severity_order.get(x['severity'], 4), x['timestamp']), reverse=True)
        
        return alerts

# Enhanced Visualization Components
class Visualizer:
    def __init__(self):
        self.colors = {
            'primary': '#1f77b4',
            'secondary': '#17becf', 
            'accent': '#084594',
            'success': '#2ca02c',
            'warning': '#ff7f0e',
            'danger': '#d62728',
            'purple': '#9467bd',
            'pink': '#e377c2',
            'brown': '#8c564b',
            'gray': '#7f7f7f'
        }
        
        self.color_sequences = {
            'blues': ['#08306b', '#08519c', '#2171b5', '#4292c6', '#6baed6', '#9ecae1', '#c6dbef'],
            'gradient': px.colors.sequential.Blues,
            'categorical': px.colors.qualitative.Set3
        }
    
    def create_enhanced_network_health_gauge(self, health_data: dict) -> go.Figure:
        """Create an enhanced network health gauge with insights"""
        score = health_data.get('score', 0)
        status = health_data.get('status', 'Unknown')
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=score,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Network Health Score", 'font': {'size': 20}},
            delta={'reference': 80, 'valueformat': '.1f'},
            gauge={
                'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
                'bar': {'color': self.colors['primary'], 'thickness': 0.3},
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "gray",
                'steps': [
                    {'range': [0, 40], 'color': "#ffcccc"},
                    {'range': [40, 60], 'color': "#ffffcc"},
                    {'range': [60, 80], 'color': "#ccffcc"},
                    {'range': [80, 100], 'color': "#ccffff"}
                ],
                'threshold': {
                    'line': {'color': self.colors['danger'], 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        
        status_color = self.colors['success'] if score >= 80 else self.colors['warning'] if score >= 60 else self.colors['danger']
        
        fig.update_layout(
            height=400,
            annotations=[
                dict(
                    x=0.5, y=0.15,
                    text=f"Status: {status}",
                    showarrow=False,
                    font={'size': 18, 'color': status_color, 'family': 'Arial Black'}
                )
            ],
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        
        return fig
    
    def create_daily_activity_timeline(self, daily_data: pd.DataFrame) -> go.Figure:
        """Create daily activity timeline with multiple metrics"""
        if daily_data.empty:
            return self.create_empty_chart("No daily activity data available")
        
        if 'day' in daily_data.columns:
            daily_data = daily_data.copy()
            daily_data['day'] = pd.to_datetime(daily_data['day'])
        
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        
        if 'active_wallets' in daily_data.columns:
            fig.add_trace(
                go.Scatter(
                    x=daily_data['day'],
                    y=daily_data['active_wallets'],
                    name='Active Wallets',
                    line=dict(color=self.colors['primary'], width=3)
                ),
                secondary_y=False
            )
        
        if 'avg_gas_price_in_gwei' in daily_data.columns:
            fig.add_trace(
                go.Scatter(
                    x=daily_data['day'],
                    y=daily_data['avg_gas_price_in_gwei'],
                    name='Avg Gas Price (GWEI)',
                    line=dict(color=self.colors['warning'], width=2)
                ),
                secondary_y=True
            )
        
        fig.update_layout(
            title='Daily Network Activity Trends',
            hovermode='x unified'
        )
        
        fig.update_yaxes(title_text="Active Wallets", secondary_y=False)
        fig.update_yaxes(title_text="Gas Price (GWEI)", secondary_y=True)
        
        return fig
    
    def create_empty_chart(self, message: str) -> go.Figure:
        """Create empty chart with message"""
        fig = go.Figure()
        fig.add_annotation(
            x=0.5, y=0.5,
            text=message,
            showarrow=False,
            font={'size': 16, 'color': 'gray'},
            xref='paper',
            yref='paper'
        )
        fig.update_layout(
            xaxis={'visible': False},
            yaxis={'visible': False},
            height=400,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        return fig

# Utility functions
def format_currency(value: float, currency: str = "USD") -> str:
    if pd.isna(value) or value is None:
        return "N/A"
    
    symbol = "$" if currency == "USD" else "RON" if currency == "RON" else currency
    
    if abs(value) >= 1e9:
        return f"{symbol}{value/1e9:,.1f}B"
    elif abs(value) >= 1e6:
        return f"{symbol}{value/1e6:,.1f}M"
    elif abs(value) >= 1e3:
        return f"{symbol}{value/1e3:,.1f}K"
    else:
        return f"{symbol}{value:,.2f}"

def format_number(value: Union[int, float]) -> str:
    if pd.isna(value) or value is None:
        return "N/A"
    
    if abs(value) >= 1e9:
        return f"{value/1e9:,.1f}B"
    elif abs(value) >= 1e6:
        return f"{value/1e6:,.1f}M"
    elif abs(value) >= 1e3:
        return f"{value/1e3:,.1f}K"
    else:
        return f"{value:,.0f}"

def format_address_link(address: str, link_type: str = "marketplace") -> str:
    """Format blockchain address as clickable link"""
    if not address or pd.isna(address) or address == "Unknown":
        return address
    
    clean_address = str(address).strip().lower()
    if not clean_address.startswith('0x'):
        clean_address = '0x' + clean_address
    
    if link_type == "marketplace":
        url = f"https://marketplace.roninchain.com/collections/{clean_address}"
        display_text = f"{clean_address[:8]}...{clean_address[-6:]}"
        return f'<a href="{url}" target="_blank">{display_text}</a>'
    elif link_type == "explorer":
        url = f"https://app.roninchain.com/address/{clean_address}"
        display_text = f"{clean_address[:8]}...{clean_address[-6:]}"
        return f'<a href="{url}" target="_blank">{display_text}</a>'
    else:
        return clean_address

def clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Clean column names for better display"""
    if df.empty:
        return df
    
    column_mapping = {
        'floor_price_usd': 'Floor Price (USD)',
        'sales_volume_usd': 'Sales Volume (USD)',
        'contract_address': 'Contract Address',
        'total_revenue_usd': 'Total Revenue (USD)',
        'platform_fees_usd': 'Platform Fees (USD)',
        'creator_royalties_usd': 'Creator Royalties (USD)',
        'ronin_fees_usd': 'Network Fees (USD)',
        'unique_players': 'Unique Players',
        'transaction_count': 'Transaction Count',
        'total_volume_ron_sent_to_game': 'Total Volume (RON)',
        'avg_gas_price_in_gwei': 'Avg Gas Price (GWEI)',
        'game_project': 'Game Project',
        'performance_score': 'Performance Score',
        'revenue_per_player': 'Revenue per Player (RON)',
        'transactions_per_player': 'Transactions per Player'
    }
    
    return df.rename(columns=column_mapping)
# Main Dashboard Class
class RoninDashboard:
    def __init__(self):
        self.data_manager = DataManager()
        self.analytics_engine = AnalyticsEngine()
        self.visualizer = Visualizer()
        
        # Initialize session state
        if 'data_loaded' not in st.session_state:
            st.session_state.data_loaded = False
        if 'cached_data' not in st.session_state:
            st.session_state.cached_data = {}
        if 'selected_time_filter' not in st.session_state:
            st.session_state.selected_time_filter = "Last 30 days"
        if 'last_data_refresh' not in st.session_state:
            st.session_state.last_data_refresh = None
    
    def render_header(self):
        st.markdown("""
        <div class="main-header">
            <h1>🎮 Ronin Ecosystem Tracker</h1>
            <p>Professional Analytics Dashboard for Ronin Blockchain Gaming Economy</p>
            <p style="font-size: 1rem; opacity: 0.8;">Real-time insights • Comprehensive analytics • Actionable intelligence</p>
        </div>
        """, unsafe_allow_html=True)
    
    def render_sidebar(self):
        with st.sidebar:
            st.markdown('<div class="sidebar-header">🎯 Dashboard Controls</div>', unsafe_allow_html=True)
            
            # Data management
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🔄 Refresh", type="primary", help="Force refresh data (limited to prevent API overuse)"):
                    if self._can_refresh():
                        st.session_state.data_loaded = False
                        st.session_state.cached_data = {}
                        st.session_state.last_data_refresh = datetime.now()
                        st.rerun()
                    else:
                        st.warning("Data was recently refreshed. Please wait before refreshing again to conserve API credits.")
            
            with col2:
                if st.button("📊 Export", help="Export current data"):
                    st.info("Export feature coming soon!")
            
            # Cache status
            if st.session_state.last_data_refresh:
                cache_age = datetime.now() - st.session_state.last_data_refresh
                if cache_age < timedelta(hours=1):
                    st.success(f"✅ Data fresh ({cache_age.seconds//60}min ago)")
                elif cache_age < timedelta(hours=12):
                    st.info(f"ℹ️ Data cached ({cache_age.seconds//3600}h ago)")
                else:
                    st.warning("⚠️ Data may be stale (>12h)")
            
            # Time filter (working filter)
            st.markdown("### 📅 Time Range Filter")
            time_filter = st.selectbox(
                "Select time period",
                ["Last 7 days", "Last 30 days", "Last 90 days", "All time"],
                index=1,
                key="time_filter_select",
                help="Filter applies to all time-series data across the dashboard"
            )
            
            # Update filter in session state
            if time_filter != st.session_state.selected_time_filter:
                st.session_state.selected_time_filter = time_filter
                st.session_state.data_loaded = False  # Trigger data reload with new filter
            
            # Advanced filters
            st.markdown("### ⚙️ Advanced Filters")
            
            # Whale threshold
            whale_threshold = st.slider(
                "Whale Transaction Threshold ($)",
                min_value=10000,
                max_value=1000000,
                value=config.whale_threshold,
                step=10000,
                help="Threshold for detecting whale transactions"
            )
            config.whale_threshold = whale_threshold
            
            # Minimum game activity
            min_players = st.number_input(
                "Min Players for Game Analysis",
                min_value=1,
                max_value=10000,
                value=100,
                help="Minimum unique players required for game to appear in analysis"
            )
            
            # Dashboard info
            st.markdown("---")
            st.markdown("### 📈 Dashboard Stats")
            
            if st.session_state.cached_data:
                datasets_loaded = len([k for k, v in st.session_state.cached_data.items() 
                                     if isinstance(v, pd.DataFrame) and not v.empty])
                st.metric("Active Datasets", datasets_loaded)
                
                # Data quality indicators
                total_records = sum([len(v) for v in st.session_state.cached_data.values() 
                                   if isinstance(v, pd.DataFrame)])
                st.metric("Total Data Points", format_number(total_records))
            
            # About section
            st.markdown("---")
            st.markdown("### ℹ️ About This Dashboard")
            st.markdown("""
            **Professional Analytics Platform** for the Ronin blockchain ecosystem featuring:
            
            🎮 **Gaming Intelligence**
            - Player behavior analysis
            - Game performance rankings
            - Revenue optimization insights
            
            💰 **DeFi Analytics**
            - Liquidity flow analysis
            - Trading pattern insights
            - Whale activity monitoring
            
            🖼️ **NFT Marketplace Intel**
            - Collection performance metrics
            - Floor price analytics
            - Revenue breakdown analysis
            
            🔍 **Network Health Monitoring**
            - Real-time performance scoring
            - Congestion analysis
            - Predictive alerts
            
            📊 **Advanced Features**
            - 24-hour intelligent caching
            - Real-time alert system
            - Actionable recommendations
            - Professional visualizations
            """)
            
            st.markdown("---")
            st.markdown("*Data powered by Dune Analytics & CoinGecko Pro API*")
    
    def _can_refresh(self) -> bool:
        """Check if data refresh is allowed (prevent API abuse)"""
        if not st.session_state.last_data_refresh:
            return True
        
        time_since_refresh = datetime.now() - st.session_state.last_data_refresh
        return time_since_refresh > timedelta(minutes=30)  # 30-minute cooldown
    
    def load_data(self):
        """Load data with time filter applied"""
        if not st.session_state.data_loaded:
            with st.spinner("🔄 Loading comprehensive Ronin ecosystem data..."):
                try:
                    data = self.data_manager.load_all_data(st.session_state.selected_time_filter)
                    st.session_state.cached_data = data
                    st.session_state.data_loaded = True
                    # if not st.session_state.last_data_refresh:
                    #     st.session_state.last_data_refresh = datetime.now()
                    st.success("✅ Data loaded successfully with 24-hour caching active!")
                    return True
                except Exception as e:
                    st.error(f"❌ Failed to load data: {e}")
                    return False
        return True
    
    def render_overview_tab(self):
        """Enhanced overview tab with comprehensive metrics"""
        st.header("📊 Executive Dashboard Overview")
        
        data = st.session_state.cached_data
        
        # RON Market Metrics Section
        if data.get('ron_market'):
            ron_metrics = data['ron_market']
            
            st.markdown("### 💰 RON Token Market Intelligence")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                price = ron_metrics.get('current_price_usd', 0)
                change = ron_metrics.get('price_change_24h', 0)
                delta_color = "normal" if change == 0 else ("off" if change < 0 else "normal")
                st.metric(
                    "RON Price",
                    f"${price:.4f}" if price else "N/A",
                    f"{change:+.2f}%" if change else None,
                    delta_color=delta_color
                )
            
            with col2:
                mcap = ron_metrics.get('market_cap_usd', 0)
                fdv = ron_metrics.get('fdv', 0)
                mcap_fdv_ratio = (mcap / fdv * 100) if fdv and mcap else None
                st.metric(
                    "Market Cap",
                    format_currency(mcap) if mcap else "N/A",
                    f"{mcap_fdv_ratio:.1f}% of FDV" if mcap_fdv_ratio else None
                )
            
            with col3:
                volume = ron_metrics.get('volume_24h_usd', 0)
                mcap_volume_ratio = (volume / mcap * 100) if mcap and volume else None
                st.metric(
                    "24h Volume",
                    format_currency(volume) if volume else "N/A",
                    f"{mcap_volume_ratio:.2f}% of MCap" if mcap_volume_ratio else None
                )
            
            with col4:
                supply = ron_metrics.get('circulating_supply', 0)
                total_supply = ron_metrics.get('total_supply', 0)
                supply_ratio = (supply / total_supply * 100) if total_supply and supply else None
                st.metric(
                    "Circulating Supply",
                    format_number(supply) if supply else "N/A",
                    f"{supply_ratio:.1f}% of Total" if supply_ratio else None
                )
        
        # Network Health & Activity Analysis
        st.markdown("### 🔍 Network Health & Performance Analytics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if data.get('ronin_daily_activity') is not None:
                health_data = self.analytics_engine.calculate_network_health_score(data['ronin_daily_activity'])
                fig = self.visualizer.create_enhanced_network_health_gauge(health_data)
                st.plotly_chart(fig, use_container_width=True)
                
                # Health insights
                if health_data.get('insights'):
                    st.markdown("#### 💡 Network Insights")
                    for insight in health_data['insights'][:4]:
                        st.markdown(f"• {insight}")
        
        with col2:
            if data.get('ronin_daily_activity') is not None:
                daily_fig = self.visualizer.create_daily_activity_timeline(data['ronin_daily_activity'])
                st.plotly_chart(daily_fig, use_container_width=True)
        
        # Ecosystem Spending Analysis
        st.markdown("### 💸 RON Ecosystem Spending Intelligence")
        
        spending_data = self.analytics_engine.analyze_spending_patterns(
            data.get('games_overall_activity', pd.DataFrame()),
            data.get('nft_collections', pd.DataFrame()),
            data.get('wron_volume_liquidity', pd.DataFrame())
        )
        
        if spending_data.get('sectors'):
            # Spending insights
            st.markdown("#### 📈 Spending Pattern Insights")
            cols = st.columns(len(spending_data['sectors']))
            
            for i, (sector, data_point) in enumerate(spending_data['sectors'].items()):
                with cols[i]:
                    st.markdown(f"""
                    <div class="kpi-container">
                        <h4>{sector} Sector</h4>
                        <p><strong>Volume:</strong> {format_currency(data_point['volume_ron'], 'RON')}</p>
                        <p><strong>Users:</strong> {format_number(data_point['users'])}</p>
                        <p><strong>Avg Spend:</strong> {format_currency(data_point['avg_spend_per_user'], 'RON')}</p>
                        <p><strong>Share:</strong> {data_point.get('percentage', 0):.1f}%</p>
                    </div>
                    """, unsafe_allow_html=True)
        
        # User Segmentation
        if data.get('ron_segmented_holders') is not None and not data['ron_segmented_holders'].empty:
            st.markdown("### 👥 User Segmentation Analysis")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Create pie chart
                seg_data = data['ron_segmented_holders']
                fig = go.Figure(data=[go.Pie(
                    labels=seg_data['tier'] if 'tier' in seg_data.columns else seg_data.iloc[:, 0],
                    values=seg_data['holders'] if 'holders' in seg_data.columns else seg_data.iloc[:, 1],
                    hole=.3,
                    marker_colors=self.visualizer.color_sequences['blues']
                )])
                fig.update_layout(title="User Distribution by Tier", height=400)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Segmentation table with insights
                seg_data_display = clean_column_names(seg_data)
                st.dataframe(seg_data_display, use_container_width=True, hide_index=True)
                
                # Calculate concentration metrics
                if 'holders' in seg_data.columns:
                    total_holders = seg_data['holders'].sum()
                    largest_segment = seg_data['holders'].max()
                    concentration = (largest_segment / total_holders * 100) if total_holders > 0 else 0
                    
                    st.markdown(f"""
                    <div class="insight-box">
                        <strong>📊 Segmentation Insights:</strong><br>
                        • Total RON holders: {format_number(total_holders)}<br>
                        • Largest segment: {concentration:.1f}% of holders<br>
                        • Distribution indicates {"healthy" if concentration < 70 else "concentrated"} ecosystem
                    </div>
                    """, unsafe_allow_html=True)
    
    def render_gaming_tab(self):
        """Enhanced gaming analytics with deep insights"""
        st.header("🎮 Gaming Ecosystem Deep Analytics")
        
        data = st.session_state.cached_data
        
        if data.get('games_overall_activity') is not None and not data['games_overall_activity'].empty:
            games_data = data['games_overall_activity']
            
            # Filter games with minimum activity
            min_players = 100
            active_games = games_data[games_data['unique_players'] >= min_players] if 'unique_players' in games_data.columns else games_data
            
            # Rank games by performance
            ranked_games = self.analytics_engine.rank_games_by_performance(active_games)
            
            if not ranked_games.empty:
                # Gaming KPIs
                st.markdown("### 📊 Gaming Sector KPIs")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    total_games = len(ranked_games)
                    active_games_count = len(ranked_games[ranked_games['unique_players'] > 1000]) if 'unique_players' in ranked_games.columns else 0
                    st.metric(
                        "Total Games", 
                        total_games,
                        f"{active_games_count} highly active" if active_games_count > 0 else None
                    )
                
                with col2:
                    total_players = ranked_games['unique_players'].sum() if 'unique_players' in ranked_games.columns else 0
                    avg_players_per_game = total_players / total_games if total_games > 0 else 0
                    st.metric(
                        "Total Players", 
                        format_number(total_players),
                        f"{avg_players_per_game:,.0f} avg/game" if avg_players_per_game > 0 else None
                    )
                
                with col3:
                    total_volume = ranked_games['total_volume_ron_sent_to_game'].sum() if 'total_volume_ron_sent_to_game' in ranked_games.columns else 0
                    avg_volume_per_game = total_volume / total_games if total_games > 0 else 0
                    st.metric(
                        "Total Volume", 
                        format_currency(total_volume, 'RON'),
                        f"{format_currency(avg_volume_per_game, 'RON')} avg/game" if avg_volume_per_game > 0 else None
                    )
                
                with col4:
                    total_transactions = ranked_games['transaction_count'].sum() if 'transaction_count' in ranked_games.columns else 0
                    avg_tx_per_game = total_transactions / total_games if total_games > 0 else 0
                    st.metric(
                        "Total Transactions", 
                        format_number(total_transactions),
                        f"{format_number(avg_tx_per_game)} avg/game" if avg_tx_per_game > 0 else None
                    )
                
                # Advanced gaming visualization
                st.markdown("### 📈 Game Performance Analysis")
                
                fig = make_subplots(
                    rows=2, cols=2,
                    subplot_titles=('Players vs Revenue/Player', 'Performance Rankings', 
                                   'Transaction Activity', 'Volume Distribution'),
                    specs=[[{"type": "scatter"}, {"type": "bar"}],
                           [{"type": "bar"}, {"type": "pie"}]]
                )
                
                # Scatter plot: Players vs Revenue per Player
                if all(col in ranked_games.columns for col in ['unique_players', 'revenue_per_player']):
                    fig.add_trace(go.Scatter(
                        x=ranked_games['unique_players'],
                        y=ranked_games['revenue_per_player'],
                        mode='markers+text',
                        text=ranked_games['game_project'],
                        textposition='top center',
                        marker=dict(
                            size=10,
                            color=ranked_games['performance_score'] if 'performance_score' in ranked_games.columns else 'blue',
                            colorscale='Blues',
                            showscale=True
                        ),
                        name="Games"
                    ), row=1, col=1)
                
                # Performance rankings
                top_10 = ranked_games.head(10)
                if 'performance_score' in top_10.columns:
                    fig.add_trace(go.Bar(
                        x=top_10['performance_score'],
                        y=top_10['game_project'],
                        orientation='h',
                        name="Performance"
                    ), row=1, col=2)
                
                # Transaction activity
                if 'transaction_count' in ranked_games.columns:
                    fig.add_trace(go.Bar(
                        x=ranked_games['game_project'].head(10),
                        y=ranked_games['transaction_count'].head(10),
                        name="Transactions"
                    ), row=2, col=1)
                
                # Volume pie chart
                if 'total_volume_ron_sent_to_game' in ranked_games.columns:
                    top_5_volume = ranked_games.head(5)
                    fig.add_trace(go.Pie(
                        labels=top_5_volume['game_project'],
                        values=top_5_volume['total_volume_ron_sent_to_game'],
                        name="Volume Share"
                    ), row=2, col=2)
                
                fig.update_layout(height=800, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
                
                # Top performers table
                st.markdown("### 🏆 Game Performance Leaderboard")
                
                display_cols = [
                    'game_project', 'unique_players', 'transaction_count', 
                    'total_volume_ron_sent_to_game', 'revenue_per_player', 'performance_score'
                ]
                
                available_cols = [col for col in display_cols if col in ranked_games.columns]
                
                if available_cols:
                    top_games = clean_column_names(ranked_games[available_cols].head(20))
                    
                    # Format numeric columns
                    for col in top_games.select_dtypes(include=[np.number]).columns:
                        if 'Volume' in col or 'Revenue' in col:
                            top_games[col] = top_games[col].round(2)
                        else:
                            top_games[col] = top_games[col].round(1)
                    
                    st.dataframe(top_games, use_container_width=True, hide_index=True)
        else:
            st.info("⏳ Gaming data is loading... Please refresh if this persists.")
    
    def render_defi_tab(self):
        """Enhanced DeFi analytics with liquidity insights"""
        st.header("💰 DeFi Ecosystem Intelligence")
        
        data = st.session_state.cached_data
        
        # Liquidity Flow Analysis
        st.markdown("### 🌊 Liquidity Flow Analysis")
        
        flow_data = self.analytics_engine.detect_liquidity_flows(
            data.get('wron_volume_liquidity', pd.DataFrame()),
            data.get('games_overall_activity', pd.DataFrame()),
            data.get('nft_collections', pd.DataFrame())
        )
        
        if flow_data.get('flow_analysis'):
            # Create liquidity visualization
            sectors = list(flow_data['flow_analysis'].keys())
            volumes = [flow_data['flow_analysis'][sector]['total_volume'] for sector in sectors]
            scores = [flow_data['flow_analysis'][sector]['liquidity_score'] for sector in sectors]
            
            fig = make_subplots(rows=1, cols=2, specs=[[{"type": "bar"}, {"type": "indicator"}]])
            
            colors = ['green' if score > 70 else 'orange' if score > 40 else 'red' for score in scores]
            
            fig.add_trace(go.Bar(
                x=sectors,
                y=volumes,
                marker_color=colors,
                name="Liquidity Volume"
            ), row=1, col=1)
            
            overall_score = sum(scores) / len(scores) if scores else 0
            fig.add_trace(go.Indicator(
                mode="gauge+number",
                value=overall_score,
                title={"text": "Overall Liquidity Score"},
                gauge={'axis': {'range': [None, 100]}}
            ), row=1, col=2)
            
            fig.update_layout(height=400, title_text="Ronin Ecosystem Liquidity Health")
            st.plotly_chart(fig, use_container_width=True)
            
            # Liquidity recommendations
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 🔥 High Liquidity Sectors")
                for sector in flow_data.get('high_liquidity_sectors', []):
                    st.success(f"✅ {sector}")
            
            with col2:
                st.markdown("#### ⚠️ Improvement Opportunities")
                for sector in flow_data.get('low_liquidity_sectors', []):
                    st.warning(f"⚠️ {sector}")
        
        # Trading Activity Analysis
        if data.get('wron_volume_liquidity') is not None and not data['wron_volume_liquidity'].empty:
            trading_data = data['wron_volume_liquidity']
            
            st.markdown("### 📈 Trading Volume Intelligence")
            
            # Enhanced trading data display
            display_data = clean_column_names(trading_data)
            st.dataframe(display_data, use_container_width=True, hide_index=True)
        else:
            st.info("⏳ DeFi data is loading... Please refresh if this persists.")
        def render_nft_tab(self):
            """Enhanced NFT marketplace analytics"""
            st.header("🖼️ NFT Marketplace Intelligence")
            
            data = st.session_state.cached_data
        
        if data.get('nft_collections') is not None and not data['nft_collections'].empty:
            nft_data = data['nft_collections']
            
            # NFT marketplace KPIs
            st.markdown("### 📊 NFT Marketplace KPIs")
            
            col1, col2, col3, col4 = st.columns(4)
            
            volume_col = 'sales_volume_usd' if 'sales_volume_usd' in nft_data.columns else 'sales volume (USD)'
            
            with col1:
                total_collections = len(nft_data)
                active_collections = len(nft_data[nft_data[volume_col] > 0]) if volume_col in nft_data.columns else 0
                st.metric(
                    "Total Collections", 
                    total_collections,
                    f"{active_collections} active" if active_collections > 0 else None
                )
            
            with col2:
                if volume_col in nft_data.columns:
                    total_volume = nft_data[volume_col].sum()
                    avg_volume = total_volume / total_collections if total_collections > 0 else 0
                    st.metric(
                        "Total Volume", 
                        format_currency(total_volume),
                        f"{format_currency(avg_volume)} avg/collection" if avg_volume > 0 else None
                    )
            
            with col3:
                if 'holders' in nft_data.columns:
                    total_holders = nft_data['holders'].sum()
                    avg_holders = total_holders / total_collections if total_collections > 0 else 0
                    st.metric(
                        "Total Holders", 
                        format_number(total_holders),
                        f"{avg_holders:.0f} avg/collection" if avg_holders > 0 else None
                    )
            
            with col4:
                if 'total_revenue_usd' in nft_data.columns:
                    total_revenue = nft_data['total_revenue_usd'].sum()
                    revenue_rate = (total_revenue / total_volume * 100) if volume_col in nft_data.columns and total_volume > 0 else 0
                    st.metric(
                        "Total Revenue", 
                        format_currency(total_revenue),
                        f"{revenue_rate:.1f}% of volume" if revenue_rate > 0 else None
                    )
            
            # NFT Deep Analysis Visualization
            st.markdown("### 📈 NFT Performance Analysis")
            
            floor_col = 'floor_price_usd' if 'floor_price_usd' in nft_data.columns else 'floor price (USD)'
            
            fig = make_subplots(
                rows=2, cols=2,
                specs=[
                    [{"type": "scatter"}, {"type": "bar"}],
                    [{"type": "histogram"}, {"type": "pie"}]
                ],
                subplot_titles=(
                    'Collection Performance Matrix',
                    'Top Collections by Volume',
                    'Floor Price Distribution',
                    'Revenue Source Breakdown'
                )
            )
            
            # Performance scatter plot
            if all(col in nft_data.columns for col in ['holders', floor_col, volume_col]):
                fig.add_trace(go.Scatter(
                    x=nft_data['holders'],
                    y=nft_data[floor_col],
                    mode='markers',
                    marker=dict(
                        size=nft_data[volume_col]/nft_data[volume_col].max()*30,
                        color=nft_data[volume_col],
                        colorscale='Blues',
                        showscale=True
                    ),
                    name="Collections",
                    hovertemplate="Holders: %{x:,}<br>Floor: $%{y:.2f}<br>Volume: $%{marker.color:,.0f}<extra></extra>"
                ), row=1, col=1)
            
            # Top collections bar chart
            if volume_col in nft_data.columns:
                top_collections = nft_data.nlargest(10, volume_col)
                fig.add_trace(go.Bar(
                    x=top_collections[volume_col],
                    y=list(range(len(top_collections))),
                    orientation='h',
                    name="Volume"
                ), row=1, col=2)
            
            # Floor price histogram
            if floor_col in nft_data.columns:
                fig.add_trace(go.Histogram(
                    x=nft_data[floor_col],
                    nbinsx=20,
                    name="Floor Price Distribution"
                ), row=2, col=1)
            
            # Revenue breakdown pie chart
            if 'total_revenue_usd' in nft_data.columns:
                revenue_sources = ['Platform Fees', 'Creator Royalties', 'Network Fees']
                if all(col in nft_data.columns for col in ['platform_fees_usd', 'creator_royalties_usd', 'ronin_fees_usd']):
                    revenue_values = [
                        nft_data['platform_fees_usd'].sum(),
                        nft_data['creator_royalties_usd'].sum(),
                        nft_data['ronin_fees_usd'].sum()
                    ]
                    fig.add_trace(go.Pie(
                        labels=revenue_sources,
                        values=revenue_values,
                        name="Revenue Sources"
                    ), row=2, col=2)
            
            fig.update_layout(height=800, title_text="NFT Marketplace Deep Analysis")
            fig.update_xaxes(title_text="Holders", type="log", row=1, col=1)
            fig.update_yaxes(title_text="Floor Price (USD)", type="log", row=1, col=1)
            st.plotly_chart(fig, use_container_width=True)
            
            # Top collections with clickable links
            st.markdown("### 🏆 Top NFT Collections Performance")
            
            if volume_col in nft_data.columns:
                top_collections_table = nft_data.nlargest(20, volume_col).copy()
                
                # Format contract addresses as clickable links
                if 'contract_address' in top_collections_table.columns:
                    top_collections_table['contract_address'] = top_collections_table['contract_address'].apply(
                        lambda x: format_address_link(x, "marketplace")
                    )
                
                # Clean column names
                display_data = clean_column_names(top_collections_table)
                
                # Format numeric columns
                for col in display_data.select_dtypes(include=[np.number]).columns:
                    if 'Volume' in col or 'Revenue' in col or 'Price' in col or 'Fees' in col:
                        display_data[col] = display_data[col].round(2)
                
                # Display with HTML for clickable links
                if 'Contract Address' in display_data.columns:
                    st.markdown("**Note:** Click on contract addresses to view collections on Ronin marketplace")
                    st.write(display_data.to_html(escape=False, index=False), unsafe_allow_html=True)
                else:
                    st.dataframe(display_data, use_container_width=True, hide_index=True)
                
                # NFT insights
                st.markdown("### 💡 NFT Marketplace Insights")
                
                floor_col = 'floor_price_usd' if 'floor_price_usd' in nft_data.columns else 'floor price (USD)'
                insights = []
                
                if volume_col in nft_data.columns:
                    top_collection_volume = nft_data[volume_col].max()
                    total_volume = nft_data[volume_col].sum()
                    volume_concentration = (top_collection_volume / total_volume * 100) if total_volume > 0 else 0
                    insights.append(f"📊 Top collection represents {volume_concentration:.1f}% of total volume")
                
                if floor_col in nft_data.columns:
                    avg_floor_price = nft_data[floor_col].mean()
                    high_value_collections = len(nft_data[nft_data[floor_col] > avg_floor_price * 2])
                    insights.append(f"💎 {high_value_collections} collections have floor prices >2x average (${avg_floor_price:.2f})")
                
                if 'holders' in nft_data.columns and volume_col in nft_data.columns:
                    nft_data['utility_score'] = nft_data[volume_col] / nft_data['holders'].replace(0, 1)
                    high_utility = len(nft_data[nft_data['utility_score'] > nft_data['utility_score'].median() * 1.5])
                    insights.append(f"🎯 {high_utility} collections show high utility (volume per holder above median)")
                
                for insight in insights:
                    st.markdown(f"""
                    <div class="insight-box">
                        {insight}
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("⏳ NFT marketplace data is loading... Please refresh if this persists.")
    
    def render_alerts_tab(self):
        """Enhanced alerts and monitoring with detailed analysis"""
        st.header("🚨 Comprehensive Alert System & Monitoring")
        
        data = st.session_state.cached_data
        
        # Generate comprehensive alerts
        alerts = self.analytics_engine.generate_comprehensive_alerts(data)
        
        if alerts:
            st.markdown("### 🔔 Active Alerts & Recommendations")
            
            # Alert summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            alert_counts = {}
            for alert in alerts:
                severity = alert.get('severity', 'Unknown')
                alert_counts[severity] = alert_counts.get(severity, 0) + 1
            
            with col1:
                critical_count = alert_counts.get('Critical', 0)
                st.metric(
                    "🚨 Critical", 
                    critical_count,
                    "Immediate action required" if critical_count > 0 else "All clear"
                )
            
            with col2:
                high_count = alert_counts.get('High', 0)
                st.metric(
                    "⚠️ High Priority", 
                    high_count,
                    "Attention needed" if high_count > 0 else "Good"
                )
            
            with col3:
                medium_count = alert_counts.get('Medium', 0)
                st.metric(
                    "ℹ️ Medium", 
                    medium_count,
                    "Monitor closely" if medium_count > 0 else "Stable"
                )
            
            with col4:
                total_alerts = len(alerts)
                st.metric(
                    "📊 Total Alerts", 
                    total_alerts,
                    "Last 24h" if total_alerts > 0 else "System healthy"
                )
            
            # Detailed alerts display
            st.markdown("### 📋 Detailed Alert Analysis")
            
            for i, alert in enumerate(alerts[:15]):  # Show top 15 alerts
                severity = alert.get('severity', 'Medium')
                severity_class = f"alert-{severity.lower()}"
                
                with st.expander(f"{alert.get('title', 'Alert')} [{severity}]", expanded=(i < 3)):
                    st.markdown(f"""
                    <div class="{severity_class}">
                        <strong>🎯 Alert Type:</strong> {alert.get('type', 'Unknown')}<br>
                        <strong>📝 Description:</strong> {alert.get('message', 'No description')}<br>
                        <strong>⚡ Recommended Action:</strong> {alert.get('action', 'Monitor situation')}<br>
                        <strong>🕐 Detected:</strong> {alert.get('timestamp', datetime.now()).strftime('%Y-%m-%d %H:%M:%S')}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Additional details
                    if alert.get('details'):
                        st.markdown("**📊 Additional Details:**")
                        for detail in alert['details']:
                            st.markdown(f"• {detail}")
        else:
            st.success("✅ No active alerts - System running smoothly!")
        
        # Network health detailed analysis
        if data.get('ronin_daily_activity') is not None:
            health_data = self.analytics_engine.calculate_network_health_score(data['ronin_daily_activity'])
            
            st.markdown("### 🔍 Network Health Deep Dive")
            
            col1, col2 = st.columns(2)
            
            with col1:
                score = health_data.get('score', 0)
                status = health_data.get('status', 'Unknown')
                
                if score >= 80:
                    st.success(f"✅ Network Health: {status} ({score:.1f}/100)")
                elif score >= 60:
                    st.warning(f"⚠️ Network Health: {status} ({score:.1f}/100)")
                else:
                    st.error(f"🚨 Network Health: {status} ({score:.1f}/100)")
                
                # Health metrics breakdown
                metrics = health_data.get('metrics', {})
                for metric, value in metrics.items():
                    formatted_value = f"{value:.2f}" if isinstance(value, float) else str(value)
                    st.metric(
                        metric.replace('_', ' ').title(),
                        formatted_value
                    )
            
            with col2:
                # Health insights
                insights = health_data.get('insights', [])
                st.markdown("**📊 Key Health Indicators:**")
                for insight in insights[:5]:
                    st.markdown(f"• {insight}")
        
        # System status and data quality
        st.markdown("### 📈 System Status & Data Quality")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            data_freshness = "Fresh" if st.session_state.data_loaded else "Stale"
            cache_age = ""
            if st.session_state.last_data_refresh:
                age_delta = datetime.now() - st.session_state.last_data_refresh
                if age_delta.total_seconds() < 3600:
                    cache_age = f"({age_delta.seconds//60}min ago)"
                else:
                    cache_age = f"({age_delta.seconds//3600}h ago)"
            
            st.metric("Data Status", f"{data_freshness} {cache_age}")
        
        with col2:
            total_datasets = len([k for k, v in data.items() if isinstance(v, pd.DataFrame) and not v.empty])
            total_api_calls = len(config.dune_queries) + 1
            st.metric("Active Datasets", f"{total_datasets}/{total_api_calls}")
        
        with col3:
            api_status = "Connected" if config.dune_api_key and config.coingecko_api_key else "Limited"
            st.metric("API Status", api_status)
        
        # Performance metrics
        if st.session_state.last_data_refresh:
            st.markdown("### ⚡ Performance Metrics")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Cache Status", "24h Active", "Optimizing API usage")
            
            with col2:
                refresh_allowed = self._can_refresh()
                st.metric("Refresh Available", "Yes" if refresh_allowed else "Cooldown", 
                         "Prevents API abuse" if not refresh_allowed else "Ready")
            
            with col3:
                total_records = sum([len(v) for v in data.values() if isinstance(v, pd.DataFrame)])
                st.metric("Data Points Loaded", format_number(total_records), "Comprehensive coverage")
    
    def run(self):
        """Main dashboard execution with enhanced error handling"""
        # Check configuration
        if not config.dune_api_key or not config.coingecko_api_key:
            st.error("""
            🔑 **API Keys Required**
            
            Please set your API keys as environment variables or in a .env file:
            - `DEFI_JOSH_DUNE_QUERY_API_KEY` - Get from [Dune Analytics](https://dune.com/settings/api)
            - `COINGECKO_PRO_API_KEY` - Get from [CoinGecko Pro](https://www.coingecko.com/en/api/pricing)
            
            **For Streamlit Cloud deployment:**
            Add these as secrets in your Streamlit Cloud app settings.
            """)
            return
        
        # Auto-refresh check (once every 24 hours)
        should_auto_refresh = False
        if st.session_state.last_data_refresh:
            hours_since_refresh = (datetime.now() - st.session_state.last_data_refresh).total_seconds() / 3600
            should_auto_refresh = hours_since_refresh >= 24
        
        if should_auto_refresh and not st.session_state.data_loaded:
            st.session_state.data_loaded = False
            st.session_state.cached_data = {}
        
        # Render header
        self.render_header()
        
        # Render sidebar
        self.render_sidebar()
        
        # Load data with time filter
        if not self.load_data():
            st.error("Failed to load data. Please check your API keys and internet connection.")
            return
        
        # Main dashboard tabs with enhanced styling
        tabs = st.tabs([
            "📊 Executive Overview", 
            "🎮 Gaming Intelligence", 
            "💰 DeFi Analytics", 
            # "🖼️ NFT Marketplace", 
            "🚨 Alert Center"
        ])
        
        with tabs[0]:
            self.render_overview_tab()

        with tabs[1]:
            self.render_gaming_tab()

        with tabs[2]:
            self.render_defi_tab()

        # with tabs[3]:
        #     try:
        #         self.render_nft_tab()
        #     except Exception as e:
        #         st.error(f"NFT tab error: {e}")
        #         st.info("NFT functionality is being updated...")

        with tabs[3]:
            try:
                self.render_alerts_tab()
            except Exception as e:
                st.error(f"Alerts tab error: {e}")
                st.info("Alerts functionality is being updated...")
        
        # Enhanced footer
        st.markdown("---")
        st.markdown("""
        <div style="text-align: center; color: #666; padding: 30px; background: linear-gradient(145deg, #f8f9fa, #e9ecef); border-radius: 15px; margin-top: 20px;">
            <h3 style="color: #1f77b4; margin-bottom: 15px;">🎮 Ronin Ecosystem Tracker</h3>
            <p style="margin: 5px 0;">Professional Analytics Platform for Ronin Blockchain</p>
            <p style="margin: 5px 0; font-size: 14px;">
                Powered by <a href="https://dune.com" target="_blank" style="color: #1f77b4;">Dune Analytics</a> & 
                <a href="https://coingecko.com" target="_blank" style="color: #1f77b4;">CoinGecko Pro</a>
            </p>
            <p style="margin: 15px 0 5px 0; font-size: 12px; color: #888;">
                🔄 Data refreshes automatically every 24 hours • 
                📊 Real-time insights • 
                🔒 Professional grade analytics
            </p>
            <p style="margin: 5px 0; font-size: 12px; color: #888;">
                Built for the Ronin community with ❤️
            </p>
        </div>
        """, unsafe_allow_html=True)

# Main application entry point
def main():
    """Main application function with comprehensive error handling"""
    try:
        dashboard = RoninDashboard()
        dashboard.run()
    except Exception as e:
        st.error(f"Application error: {str(e)}")
        st.info("Please refresh the page or contact support if the issue persists.")
        logger.error(f"Dashboard error: {str(e)}")

if __name__ == "__main__":
    main()