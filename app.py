"""
Ronin Ecosystem Tracker - Complete Dashboard
A comprehensive real-time analytics dashboard for Ronin blockchain gaming economy
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

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Ronin Ecosystem Tracker",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1f77b4 0%, #17becf 100%);
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
        text-align: center;
    }
    
    .main-header h1 {
        color: white;
        margin: 0;
        font-size: 2.5rem;
    }
    
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 10px 0;
    }
    
    .alert-high {
        border-left: 4px solid #d62728;
        background-color: #ffe6e6;
        padding: 10px;
        margin: 5px 0;
    }
    
    .alert-medium {
        border-left: 4px solid #ff7f0e;
        background-color: #fff3e6;
        padding: 10px;
        margin: 5px 0;
    }
    
    .alert-low {
        border-left: 4px solid #2ca02c;
        background-color: #e6ffe6;
        padding: 10px;
        margin: 5px 0;
    }
    
    @media (max-width: 768px) {
        .main-header h1 {
            font-size: 1.8rem;
        }
        .metric-card {
            padding: 15px;
        }
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        justify-content: center;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #f0f2f6;
        border-radius: 25px;
        padding: 10px 20px;
        color: #1f77b4;
        font-weight: 600;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #1f77b4;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Configuration
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
        
        self.cache_duration = 24 * 3600  # 24 hours in seconds
        self.whale_threshold = 50000  # USD
        
        if not self.dune_api_key or not self.coingecko_api_key:
            st.error("Please set DEFI_JOSH_DUNE_QUERY_API_KEY and COINGECKO_PRO_API_KEY in your environment variables")

config = Config()

# Data Manager
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
    
    @st.cache_data(ttl=3600)
    def fetch_ron_market_data(_self) -> dict:
        try:
            url = "https://pro-api.coingecko.com/api/v3/coins/ronin"
            response = _self.session.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            market_data = data.get("market_data", {})
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
                'last_updated': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to fetch RON market data: {e}")
            return {}
    
    def fetch_dune_data(self, query_key: str) -> pd.DataFrame:
        # Check cache first
        cached = self.get_cached_data(query_key)
        if cached is not None:
            return cached
        
        # Fetch from API
        if not hasattr(self, 'dune_client'):
            return pd.DataFrame()
        
        try:
            query_id = config.dune_queries[query_key]
            result = self.dune_client.get_latest_result(query_id)
            df = pd.DataFrame(result.result.rows)
            
            # Clean and process data
            df = self._clean_dataframe(df, query_key)
            
            # Cache the result
            self.cache_data(query_key, df)
            
            return df
        except Exception as e:
            logger.error(f"Failed to fetch {query_key}: {e}")
            return pd.DataFrame()
    
    def _clean_dataframe(self, df: pd.DataFrame, query_key: str) -> pd.DataFrame:
        if df.empty:
            return df
        
        # Replace None values
        df = df.replace([None, 'None'], pd.NA)
        
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
            # Rename columns for consistency
            column_mapping = {
                'floor_ron': 'floor_price_ron',
                'floor_usd': 'floor_price_usd',
                'volume_ron': 'sales_volume_ron',
                'volume_usd': 'sales_volume_usd',
                'royalties_usd': 'royalties_usd',
                'nft_contract_address': 'contract_address'
            }
            df = df.rename(columns=column_mapping)
            
            # Calculate total revenue
            revenue_cols = ['generated platform fees (USD)', 'generated Ronin fees (USD)', 'royalties_usd']
            if all(col in df.columns for col in revenue_cols):
                df['total_revenue_usd'] = df[revenue_cols].fillna(0).sum(axis=1)
        
        # Fill text columns with 'Unknown'
        text_cols = df.select_dtypes(include=['object']).columns
        for col in text_cols:
            df[col] = df[col].fillna('Unknown')
        
        return df
    
    def load_all_data(self) -> dict:
        data = {}
        
        # Create progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        total_queries = len(config.dune_queries) + 1  # +1 for CoinGecko
        
        # Fetch RON market data
        status_text.text("Fetching RON market data...")
        data['ron_market'] = self.fetch_ron_market_data()
        progress_bar.progress(1 / total_queries)
        
        # Fetch Dune data
        for i, query_key in enumerate(config.dune_queries.keys()):
            status_text.text(f"Fetching {query_key.replace('_', ' ').title()}...")
            data[query_key] = self.fetch_dune_data(query_key)
            progress_bar.progress((i + 2) / total_queries)
        
        progress_bar.empty()
        status_text.empty()
        
        return data

# Analytics Engine
class AnalyticsEngine:
    def __init__(self):
        pass
    
    def calculate_network_health_score(self, daily_activity: pd.DataFrame) -> dict:
        if daily_activity.empty:
            return {'score': 0, 'status': 'No Data', 'metrics': {}}
        
        recent_data = daily_activity.tail(7)
        scores = []
        metrics = {}
        
        # Gas price health (0-100)
        if 'avg_gas_price_in_gwei' in recent_data.columns:
            avg_gas = recent_data['avg_gas_price_in_gwei'].mean()
            if avg_gas <= 15:
                gas_score = 100
            elif avg_gas <= 25:
                gas_score = 70
            elif avg_gas <= 40:
                gas_score = 40
            else:
                gas_score = 20
            
            scores.append(gas_score)
            metrics['avg_gas_price'] = avg_gas
        
        # Transaction volume health (0-100)
        if 'daily_transactions' in recent_data.columns:
            avg_tx = recent_data['daily_transactions'].mean()
            if avg_tx >= 100000:
                tx_score = 100
            elif avg_tx >= 50000:
                tx_score = 80
            elif avg_tx >= 10000:
                tx_score = 60
            else:
                tx_score = 30
            
            scores.append(tx_score)
            metrics['avg_daily_transactions'] = avg_tx
        
        # Active wallet growth (0-100)
        if 'active_wallets' in recent_data.columns and len(recent_data) >= 3:
            recent_wallets = recent_data['active_wallets'].tail(3).mean()
            older_wallets = recent_data['active_wallets'].head(3).mean()
            
            if older_wallets > 0:
                growth_rate = ((recent_wallets - older_wallets) / older_wallets) * 100
                
                if growth_rate >= 15:
                    wallet_score = 100
                elif growth_rate >= 5:
                    wallet_score = 80
                elif growth_rate >= -10:
                    wallet_score = 60
                else:
                    wallet_score = 40
                
                scores.append(wallet_score)
                metrics['wallet_growth_rate'] = growth_rate
        
        overall_score = sum(scores) / len(scores) if scores else 0
        
        if overall_score >= 80:
            status = 'Healthy'
        elif overall_score >= 60:
            status = 'Moderate'
        elif overall_score >= 40:
            status = 'Concerning'
        else:
            status = 'Critical'
        
        return {
            'score': round(overall_score, 1),
            'status': status,
            'metrics': metrics
        }
    
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
    
    def detect_whale_activity(self, whale_data: pd.DataFrame) -> list:
        alerts = []
        
        if whale_data.empty:
            return alerts
        
        if 'trade_volume_usd' in whale_data.columns:
            large_trades = whale_data[whale_data['trade_volume_usd'] >= config.whale_threshold]
            
            for _, trade in large_trades.iterrows():
                alerts.append({
                    'type': 'whale_activity',
                    'severity': 'high',
                    'message': f"Large trade detected: ${trade['trade_volume_usd']:,.0f}",
                    'timestamp': datetime.now().isoformat()
                })
        
        return alerts
    
    def calculate_ecosystem_dominance(self, data: dict) -> dict:
        dominance = {
            'gaming_dominance': 0.0,
            'defi_dominance': 0.0,
            'nft_dominance': 0.0
        }
        
        total_volume = 0
        
        # Gaming volume
        if 'games_overall_activity' in data and not data['games_overall_activity'].empty:
            gaming_volume = data['games_overall_activity']['total_volume_ron_sent_to_game'].sum()
            total_volume += gaming_volume
        else:
            gaming_volume = 0
        
        # DeFi volume
        if 'wron_volume_liquidity' in data and not data['wron_volume_liquidity'].empty:
            volume_col = 'WRON Volume (USD)' if 'WRON Volume (USD)' in data['wron_volume_liquidity'].columns else 'volume_usd'
            if volume_col in data['wron_volume_liquidity'].columns:
                defi_volume = data['wron_volume_liquidity'][volume_col].sum()
                total_volume += defi_volume
            else:
                defi_volume = 0
        else:
            defi_volume = 0
        
        # NFT volume
        if 'nft_collections' in data and not data['nft_collections'].empty:
            nft_volume_col = 'sales_volume_usd' if 'sales_volume_usd' in data['nft_collections'].columns else 'sales volume (USD)'
            if nft_volume_col in data['nft_collections'].columns:
                nft_volume = data['nft_collections'][nft_volume_col].sum()
                total_volume += nft_volume
            else:
                nft_volume = 0
        else:
            nft_volume = 0
        
        # Calculate percentages
        if total_volume > 0:
            dominance['gaming_dominance'] = (gaming_volume / total_volume) * 100
            dominance['defi_dominance'] = (defi_volume / total_volume) * 100
            dominance['nft_dominance'] = (nft_volume / total_volume) * 100
        
        return dominance

# Visualization Components
class Visualizer:
    def __init__(self):
        self.colors = {
            'primary': '#1f77b4',
            'secondary': '#17becf',
            'accent': '#084594',
            'success': '#2ca02c',
            'warning': '#ff7f0e',
            'danger': '#d62728'
        }
        
        self.color_sequences = {
            'blues': ['#6baed6', '#4292c6', '#2171b5', '#08519c', '#08306b'],
            'gradient': px.colors.sequential.Blues
        }
    
    def create_network_health_gauge(self, health_score: float, status: str) -> go.Figure:
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=health_score,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Network Health Score"},
            delta={'reference': 80},
            gauge={
                'axis': {'range': [None, 100]},
                'bar': {'color': self.colors['primary']},
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
        
        fig.update_layout(
            height=400,
            annotations=[
                dict(
                    x=0.5, y=0.15,
                    text=f"Status: {status}",
                    showarrow=False,
                    font={'size': 16, 'color': self.colors['primary']}
                )
            ]
        )
        
        return fig
    
    def create_games_performance_chart(self, games_data: pd.DataFrame) -> go.Figure:
        if games_data.empty:
            return self.create_empty_chart("No games data available")
        
        df_sorted = games_data.sort_values('performance_score', ascending=True).tail(15)
        
        fig = px.bar(
            df_sorted,
            x='performance_score',
            y='game_project',
            orientation='h',
            title='Top Game Projects by Performance Score',
            labels={'performance_score': 'Performance Score', 'game_project': 'Game Project'},
            color='performance_score',
            color_continuous_scale=self.color_sequences['gradient'],
            text='performance_score'
        )
        
        fig.update_traces(
            texttemplate='%{text:.1f}',
            textposition='outside'
        )
        
        fig.update_layout(
            yaxis={'categoryorder': 'total ascending'},
            height=600
        )
        
        return fig
    
    def create_daily_activity_timeline(self, daily_data: pd.DataFrame) -> go.Figure:
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
    
    def create_user_segment_pie(self, segmentation_data: pd.DataFrame) -> go.Figure:
        if segmentation_data.empty:
            return self.create_empty_chart("No segmentation data available")
        
        values_col = 'holders' if 'holders' in segmentation_data.columns else segmentation_data.columns[1]
        names_col = 'tier' if 'tier' in segmentation_data.columns else segmentation_data.columns[0]
        
        fig = px.pie(
            segmentation_data,
            values=values_col,
            names=names_col,
            title='User Segmentation Distribution',
            hole=0.4,
            color_discrete_sequence=self.color_sequences['blues']
        )
        
        fig.update_traces(
            textinfo='value+percent',
            textposition='outside',
            hovertemplate='<b>%{label}</b><br>Count: %{value:,}<br>Percentage: %{percent}<extra></extra>'
        )
        
        return fig
    
    def create_nft_marketplace_overview(self, nft_data: pd.DataFrame) -> go.Figure:
        if nft_data.empty:
            return self.create_empty_chart("No NFT data available")
        
        # Get volume column name
        volume_col = 'sales_volume_usd' if 'sales_volume_usd' in nft_data.columns else 'sales volume (USD)'
        floor_col = 'floor_price_usd' if 'floor_price_usd' in nft_data.columns else 'floor price (USD)'
        
        if volume_col not in nft_data.columns:
            return self.create_empty_chart("No volume data available for NFT collections")
        
        top_collections = nft_data.nlargest(20, volume_col)
        
        fig = px.scatter(
            top_collections,
            x='holders' if 'holders' in top_collections.columns else top_collections.index,
            y=floor_col if floor_col in top_collections.columns else volume_col,
            size=volume_col,
            color='total_revenue_usd' if 'total_revenue_usd' in top_collections.columns else volume_col,
            hover_name='contract_address' if 'contract_address' in top_collections.columns else top_collections.index,
            title='NFT Collections: Holders vs Floor Price',
            log_x=True,
            log_y=True,
            size_max=40,
            color_continuous_scale=self.color_sequences['gradient']
        )
        
        return fig
    
    def create_ecosystem_dominance_chart(self, dominance_data: dict) -> go.Figure:
        if not dominance_data:
            return self.create_empty_chart("No dominance data available")
        
        sectors = list(dominance_data.keys())
        values = list(dominance_data.values())
        
        fig = px.pie(
            values=values,
            names=[sector.replace('_', ' ').title() for sector in sectors],
            title='Ronin Ecosystem Volume Dominance',
            hole=0.3,
            color_discrete_sequence=self.color_sequences['blues']
        )
        
        fig.update_traces(
            textinfo='label+percent',
            textposition='outside'
        )
        
        return fig
    
    def create_empty_chart(self, message: str) -> go.Figure:
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
            height=400
        )
        return fig

# Utility functions
def format_currency(value: float, currency: str = "USD") -> str:
    if pd.isna(value) or value is None:
        return "N/A"
    
    if abs(value) >= 1e9:
        return f"${value/1e9:,.1f}B"
    elif abs(value) >= 1e6:
        return f"${value/1e6:,.1f}M"
    elif abs(value) >= 1e3:
        return f"${value/1e3:,.1f}K"
    else:
        return f"${value:,.2f}"

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
    
    def render_header(self):
        st.markdown("""
        <div class="main-header">
            <h1>🎮 Ronin Ecosystem Tracker</h1>
            <p style="color: white; margin: 0; opacity: 0.9;">
                Real-time Analytics Dashboard for Ronin Blockchain Gaming Economy
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    def render_sidebar(self):
        with st.sidebar:
            st.markdown("## 🎯 Dashboard Controls")
            
            # Data refresh
            if st.button("🔄 Refresh Data", type="primary"):
                st.session_state.data_loaded = False
                st.session_state.cached_data = {}
                st.rerun()
            
            # Auto-refresh
            auto_refresh = st.checkbox("Auto-refresh (5min)", value=False)
            
            # Filters
            st.markdown("### 📊 Filters")
            
            time_range = st.selectbox(
                "Time Range",
                ["Last 7 days", "Last 30 days", "Last 90 days", "All time"],
                index=1
            )
            
            # About section
            st.markdown("---")
            st.markdown("### ℹ️ About")
            st.markdown("""
            **Ronin Ecosystem Tracker** provides comprehensive analytics for the Ronin blockchain:
            
            🎮 **Gaming Analytics**
            - Player activity and retention
            - Game performance rankings
            - Revenue analysis
            
            📊 **DeFi Intelligence**
            - Trading volume and liquidity
            - Whale activity monitoring
            - Cross-bridge flows
            
            🖼️ **NFT Marketplace**
            - Collection performance
            - Trading volumes
            - Floor price trends
            
            🔍 **Network Health**
            - Transaction throughput
            - Gas price monitoring
            - Congestion analysis
            """)
            
            st.markdown("---")
            st.markdown("*Data: Dune Analytics & CoinGecko*")
    
    def load_data(self):
        if not st.session_state.data_loaded:
            with st.spinner("Loading Ronin ecosystem data..."):
                try:
                    data = self.data_manager.load_all_data()
                    st.session_state.cached_data = data
                    st.session_state.data_loaded = True
                    st.success("Data loaded successfully!")
                    return True
                except Exception as e:
                    st.error(f"Failed to load data: {e}")
                    return False
        return True
    
    def render_overview_tab(self):
        st.header("📊 Network Overview")
        
        data = st.session_state.cached_data
        
        # Key metrics
        if data.get('ron_market'):
            ron_metrics = data['ron_market']
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                price = ron_metrics.get('current_price_usd', 0)
                change = ron_metrics.get('price_change_24h', 0)
                st.metric(
                    "RON Price",
                    f"${price:.4f}" if price else "N/A",
                    f"{change:.2f}%" if change else None
                )
            
            with col2:
                mcap = ron_metrics.get('market_cap_usd', 0)
                st.metric(
                    "Market Cap",
                    format_currency(mcap) if mcap else "N/A"
                )
            
            with col3:
                volume = ron_metrics.get('volume_24h_usd', 0)
                st.metric(
                    "24h Volume",
                    format_currency(volume) if volume else "N/A"
                )
            
            with col4:
                supply = ron_metrics.get('circulating_supply', 0)
                st.metric(
                    "Circulating Supply",
                    format_number(supply) if supply else "N/A"
                )
        
        # Network health and daily activity
        col1, col2 = st.columns(2)
        
        with col1:
            if data.get('ronin_daily_activity') is not None:
                health_data = self.analytics_engine.calculate_network_health_score(data['ronin_daily_activity'])
                fig = self.visualizer.create_network_health_gauge(
                    health_data.get('score', 0),
                    health_data.get('status', 'Unknown')
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            if data.get('ronin_daily_activity') is not None:
                daily_fig = self.visualizer.create_daily_activity_timeline(data['ronin_daily_activity'])
                st.plotly_chart(daily_fig, use_container_width=True)
        
        # Ecosystem dominance
        dominance = self.analytics_engine.calculate_ecosystem_dominance(data)
        if dominance and any(v > 0 for v in dominance.values()):
            dominance_fig = self.visualizer.create_ecosystem_dominance_chart(dominance)
            st.plotly_chart(dominance_fig, use_container_width=True)
        
        # User segmentation
        if data.get('ron_segmented_holders') is not None and not data['ron_segmented_holders'].empty:
            segment_fig = self.visualizer.create_user_segment_pie(data['ron_segmented_holders'])
            st.plotly_chart(segment_fig, use_container_width=True)
    
    def render_gaming_tab(self):
        st.header("🎮 Gaming Analytics")
        
        data = st.session_state.cached_data
        
        if data.get('games_overall_activity') is not None and not data['games_overall_activity'].empty:
            games_data = data['games_overall_activity']
            
            # Rank games by performance
            ranked_games = self.analytics_engine.rank_games_by_performance(games_data)
            
            if not ranked_games.empty:
                # Performance chart
                perf_fig = self.visualizer.create_games_performance_chart(ranked_games)
                st.plotly_chart(perf_fig, use_container_width=True)
                
                # Top games table
                st.subheader("🏆 Top Performing Games")
                
                display_cols = ['game_project', 'unique_players', 'transaction_count', 
                               'total_volume_ron_sent_to_game', 'performance_score']
                
                available_cols = [col for col in display_cols if col in ranked_games.columns]
                
                if available_cols:
                    top_games = ranked_games[available_cols].head(10)
                    
                    # Format the dataframe for display
                    if 'total_volume_ron_sent_to_game' in top_games.columns:
                        top_games['total_volume_ron_sent_to_game'] = top_games['total_volume_ron_sent_to_game'].round(2)
                    
                    st.dataframe(
                        top_games,
                        use_container_width=True
                    )
                
                # Gaming metrics
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    total_games = len(games_data)
                    st.metric("Total Games", total_games)
                
                with col2:
                    total_players = games_data['unique_players'].sum()
                    st.metric("Total Players", format_number(total_players))
                
                with col3:
                    total_volume = games_data['total_volume_ron_sent_to_game'].sum()
                    st.metric("Total Volume (RON)", format_number(total_volume))
        else:
            st.info("Gaming data is loading...")
    
    def render_defi_tab(self):
        st.header("💰 DeFi Analytics")
        
        data = st.session_state.cached_data
        
        # Trading volume analysis
        if data.get('wron_volume_liquidity') is not None and not data['wron_volume_liquidity'].empty:
            trading_data = data['wron_volume_liquidity']
            st.subheader("📈 Trading Volume Analysis")
            
            # Try to create volume over time chart
            date_col = None
            volume_col = None
            
            for col in trading_data.columns:
                if 'day' in col.lower() or 'date' in col.lower():
                    date_col = col
                if 'volume' in col.lower() and 'usd' in col.lower():
                    volume_col = col
            
            if date_col and volume_col:
                daily_volume = trading_data.groupby(date_col)[volume_col].sum().reset_index()
                
                fig = px.line(
                    daily_volume,
                    x=date_col,
                    y=volume_col,
                    title='Daily WRON Trading Volume'
                )
                st.plotly_chart(fig, use_container_width=True)
            
            # Show trading data table
            st.dataframe(trading_data.head(20), use_container_width=True)
        
        # Whale activity
        if data.get('wron_whale_tracking') is not None and not data['wron_whale_tracking'].empty:
            whale_data = data['wron_whale_tracking']
            
            st.subheader("🐋 Whale Activity")
            
            # Generate whale alerts
            whale_alerts = self.analytics_engine.detect_whale_activity(whale_data)
            
            if whale_alerts:
                st.warning(f"⚠️ {len(whale_alerts)} whale transactions detected above ${config.whale_threshold:,}")
                
                for alert in whale_alerts[:5]:  # Show latest 5
                    st.markdown(f"• {alert['message']}")
            else:
                st.info("No significant whale activity detected")
            
            # Whale data table
            if 'trade_volume_usd' in whale_data.columns:
                whale_summary = whale_data.groupby(whale_data.index).agg({
                    'trade_volume_usd': ['sum', 'count', 'mean']
                }).round(2)
                st.dataframe(whale_summary, use_container_width=True)
        
        # Active trading pairs
        if data.get('wron_active_trade_pairs') is not None and not data['wron_active_trade_pairs'].empty:
            pairs_data = data['wron_active_trade_pairs']
            
            st.subheader("📊 Active Trading Pairs")
            
            # Find volume column
            volume_cols = [col for col in pairs_data.columns if 'volume' in col.lower() and 'usd' in col.lower()]
            
            if volume_cols:
                volume_col = volume_cols[0]
                top_pairs = pairs_data.nlargest(20, volume_col)
                st.dataframe(top_pairs, use_container_width=True)
            else:
                st.dataframe(pairs_data.head(20), use_container_width=True)
    
    def render_nft_tab(self):
        st.header("🖼️ NFT Marketplace")
        
        data = st.session_state.cached_data
        
        if data.get('nft_collections') is not None and not data['nft_collections'].empty:
            nft_data = data['nft_collections']
            
            # NFT overview chart
            nft_fig = self.visualizer.create_nft_marketplace_overview(nft_data)
            st.plotly_chart(nft_fig, use_container_width=True)
            
            # NFT marketplace metrics
            col1, col2, col3 = st.columns(3)
            
            volume_col = 'sales_volume_usd' if 'sales_volume_usd' in nft_data.columns else 'sales volume (USD)'
            
            with col1:
                total_collections = len(nft_data)
                st.metric("Total Collections", total_collections)
            
            with col2:
                if volume_col in nft_data.columns:
                    total_volume = nft_data[volume_col].sum()
                    st.metric("Total Volume", format_currency(total_volume))
                else:
                    st.metric("Total Volume", "N/A")
            
            with col3:
                if 'holders' in nft_data.columns:
                    total_holders = nft_data['holders'].sum()
                    st.metric("Total Holders", format_number(total_holders))
                else:
                    st.metric("Total Holders", "N/A")
            
            # Top collections table
            st.subheader("🏆 Top NFT Collections")
            
            if volume_col in nft_data.columns:
                top_collections = nft_data.nlargest(10, volume_col)
                
                # Select available columns for display
                display_cols = []
                
                if 'contract_address' in top_collections.columns:
                    display_cols.append('contract_address')
                if 'holders' in top_collections.columns:
                    display_cols.append('holders')
                if volume_col in top_collections.columns:
                    display_cols.append(volume_col)
                
                floor_col = 'floor_price_usd' if 'floor_price_usd' in top_collections.columns else 'floor price (USD)'
                if floor_col in top_collections.columns:
                    display_cols.append(floor_col)
                
                if display_cols:
                    display_data = top_collections[display_cols].copy()
                    
                    # Format numeric columns
                    for col in display_data.columns:
                        if display_data[col].dtype in ['float64', 'int64']:
                            display_data[col] = display_data[col].round(2)
                    
                    st.dataframe(display_data, use_container_width=True)
                else:
                    st.dataframe(top_collections.head(10), use_container_width=True)
            else:
                st.dataframe(nft_data.head(10), use_container_width=True)
        else:
            st.info("NFT marketplace data is loading...")
    
    def render_alerts_tab(self):
        st.header("🚨 Alerts & Monitoring")
        
        data = st.session_state.cached_data
        
        # Network health details
        if data.get('ronin_daily_activity') is not None:
            health_data = self.analytics_engine.calculate_network_health_score(data['ronin_daily_activity'])
            
            st.subheader("🔍 Network Health Status")
            
            col1, col2 = st.columns(2)
            
            with col1:
                score = health_data.get('score', 0)
                status = health_data.get('status', 'Unknown')
                
                if score >= 80:
                    st.success(f"Network Health: {status} ({score}/100)")
                elif score >= 60:
                    st.warning(f"Network Health: {status} ({score}/100)")
                else:
                    st.error(f"Network Health: {status} ({score}/100)")
            
            with col2:
                metrics = health_data.get('metrics', {})
                for metric, value in metrics.items():
                    formatted_value = f"{value:.2f}" if isinstance(value, float) else str(value)
                    st.metric(
                        metric.replace('_', ' ').title(),
                        formatted_value
                    )
        
        # Whale activity alerts
        whale_alerts = []
        if data.get('wron_whale_tracking') is not None:
            whale_alerts = self.analytics_engine.detect_whale_activity(data['wron_whale_tracking'])
        
        if whale_alerts:
            st.subheader("🐋 Whale Activity Alerts")
            for alert in whale_alerts[:10]:
                severity = alert.get('severity', 'medium')
                message = alert.get('message', 'No message')
                
                if severity == 'high':
                    st.error(f"🚨 {message}")
                else:
                    st.warning(f"⚠️ {message}")
        
        # System status
        st.subheader("📊 System Status")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            data_freshness = "Fresh" if st.session_state.data_loaded else "Stale"
            st.metric("Data Status", data_freshness)
        
        with col2:
            total_datasets = len([k for k, v in data.items() if isinstance(v, pd.DataFrame) and not v.empty])
            st.metric("Active Datasets", total_datasets)
        
        with col3:
            st.metric("API Status", "Connected" if config.dune_api_key and config.coingecko_api_key else "Limited")
    
    def run(self):
        # Check configuration
        if not config.dune_api_key or not config.coingecko_api_key:
            st.error("""
            🔑 **API Keys Required**
            
            Please set your API keys as environment variables:
            - `DEFI_JOSH_DUNE_QUERY_API_KEY`
            - `COINGECKO_PRO_API_KEY`
            
            You can get these from:
            - [Dune Analytics](https://dune.com/settings/api)
            - [CoinGecko Pro](https://www.coingecko.com/en/api/pricing)
            """)
            return
        
        # Render header
        self.render_header()
        
        # Render sidebar
        self.render_sidebar()
        
        # Load data
        if not self.load_data():
            st.error("Failed to load data. Please check your API keys and try refreshing.")
            return
        
        # Main dashboard tabs
        tabs = st.tabs(["📊 Overview", "🎮 Gaming", "💰 DeFi", "🖼️ NFT", "🚨 Alerts"])
        
        with tabs[0]:
            self.render_overview_tab()
        
        with tabs[1]:
            self.render_gaming_tab()
        
        with tabs[2]:
            self.render_defi_tab()
        
        with tabs[3]:
            self.render_nft_tab()
        
        with tabs[4]:
            self.render_alerts_tab()
        
        # Footer
        st.markdown("---")
        st.markdown("""
        <div style="text-align: center; color: #888; padding: 20px;">
            🎮 <strong>Ronin Ecosystem Tracker</strong> | 
            Powered by <a href="https://dune.com" target="_blank">Dune Analytics</a> & 
            <a href="https://coingecko.com" target="_blank">CoinGecko</a><br>
            <small>Real-time blockchain gaming economy analytics</small>
        </div>
        """, unsafe_allow_html=True)

# Main function
def main():
    dashboard = RoninDashboard()
    dashboard.run()

if __name__ == "__main__":
    main()