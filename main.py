"""
Ronin Ecosystem Tracker - FastAPI Backend
A comprehensive real-time analytics API for Ronin blockchain gaming economy
Version: 2.0 - FastAPI conversion with async support
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Query
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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
import asyncio
import aiohttp
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager
import json

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models for API responses
class NetworkHealthResponse(BaseModel):
    score: float
    status: str
    status_emoji: str
    metrics: Dict[str, Any]
    insights: List[str]

class RONMarketData(BaseModel):
    name: Optional[str] = None
    symbol: Optional[str] = None
    current_price_usd: Optional[float] = None
    market_cap_usd: Optional[float] = None
    volume_24h_usd: Optional[float] = None
    circulating_supply: Optional[float] = None
    total_supply: Optional[float] = None
    price_change_24h: Optional[float] = None
    price_change_7d: Optional[float] = None
    fdv: Optional[float] = None
    tvl: Optional[float] = None
    last_updated: str

class GamePerformance(BaseModel):
    game_project: str
    unique_players: Optional[int] = 0
    transaction_count: Optional[int] = 0
    total_volume_ron: Optional[float] = 0.0
    revenue_per_player: Optional[float] = 0.0
    performance_score: Optional[float] = 0.0

class AlertItem(BaseModel):
    type: str
    severity: str
    title: str
    message: str
    details: List[str]
    timestamp: datetime
    action: str

class LiquidityFlowAnalysis(BaseModel):
    high_liquidity_sectors: List[str]
    low_liquidity_sectors: List[str]
    flow_analysis: Dict[str, Any]
    recommendations: List[str]

class SpendingAnalysis(BaseModel):
    sectors: Dict[str, Any]
    total_volume: float
    user_distribution: Dict[str, Any]
    insights: List[str]

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
        
        self.cache_duration = 86400  # 24 hours
        self.whale_threshold = 50000  # USD
        
        if not self.dune_api_key or not self.coingecko_api_key:
            logger.warning("API keys not found. Some functionality may be limited.")

config = Config()

# Enhanced Data Manager with async support
class DataManager:
    def __init__(self):
        self.cache_dir = "data"
        os.makedirs(self.cache_dir, exist_ok=True)
        
        if config.dune_api_key:
            self.dune_client = DuneClient(config.dune_api_key)
        
        self.session_headers = {}
        if config.coingecko_api_key:
            self.session_headers['x-cg-pro-api-key'] = config.coingecko_api_key
    
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
    
    async def fetch_ron_market_data(self) -> dict:
        try:
            async with aiohttp.ClientSession(headers=self.session_headers) as session:
                url = "https://pro-api.coingecko.com/api/v3/coins/ronin"
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    response.raise_for_status()
                    data = await response.json()
                    
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
                        'fdv': market_data.get('fully_diluted_valuation', {}).get('usd'),
                        'tvl': market_data.get('total_value_locked', {}).get('usd'),
                        'last_updated': datetime.now().isoformat()
                    }
        except Exception as e:
            logger.error(f"Failed to fetch RON market data: {e}")
            return {}
    
    async def fetch_dune_data(self, query_key: str) -> pd.DataFrame:
        # Check cache first
        cached = self.get_cached_data(query_key)
        if cached is not None:
            return cached
        
        # Fetch from API
        if not hasattr(self, 'dune_client'):
            return pd.DataFrame()
        
        try:
            # Run in executor to avoid blocking
            def fetch_sync():
                query_id = config.dune_queries[query_key]
                result = self.dune_client.get_latest_result(query_id)
                return pd.DataFrame(result.result.rows)
            
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(None, fetch_sync)
            
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
            # Rename columns for consistency
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
    
    async def load_all_data(self, time_filter: str = "All time") -> dict:
        data = {}
        
        # Fetch RON market data
        data['ron_market'] = await self.fetch_ron_market_data()
        
        # Create tasks for all Dune queries
        tasks = []
        query_keys = []
        
        for query_key in config.dune_queries.keys():
            task = self.fetch_dune_data(query_key)
            tasks.append(task)
            query_keys.append(query_key)
        
        # Execute all queries concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for i, result in enumerate(results):
            query_key = query_keys[i]
            if isinstance(result, Exception):
                logger.error(f"Error fetching {query_key}: {result}")
                data[query_key] = pd.DataFrame()
            else:
                # Apply time filter
                filtered_df = self._apply_time_filter(result, time_filter)
                data[query_key] = filtered_df
        
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

# Analytics Engine (same as before but adapted for async)
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
                    'liquidity_score': min(100, (total_defi_volume / 1000000) * 10)
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
                    'timestamp': datetime.now(),
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
                        'timestamp': datetime.now(),
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
                        'timestamp': datetime.now(),
                        'action': 'Review gaming partnerships and user acquisition'
                    })
        
        # Sort alerts by severity and timestamp
        severity_order = {'Critical': 0, 'High': 1, 'Medium': 2, 'Low': 3}
        alerts.sort(key=lambda x: (severity_order.get(x['severity'], 4), x['timestamp']), reverse=True)
        
        return alerts

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

# Global instances
data_manager = DataManager()
analytics_engine = AnalyticsEngine()

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Ronin Ecosystem Tracker API")
    yield
    # Shutdown
    logger.info("Shutting down Ronin Ecosystem Tracker API")

# FastAPI app initialization
app = FastAPI(
    title="Ronin Ecosystem Tracker API",
    description="Professional Analytics API for Ronin Blockchain Gaming Economy",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint 
@app.get("/")
async def root(request: Request):
    base_url = str(request.base_url).rstrip('/')
    
    return {
        "message": "Ronin Ecosystem Tracker API",
        "version": "2.0.0", 
        "status": "online",
        "documentation": f"{base_url}/docs",
        "health_check": f"{base_url}/health",
        "endpoints": {
            "core_data": {
                "health": "/health",
                "ron_market": "/api/ron/market",
                "network_health": "/api/network/health",
                "gaming_overview": "/api/gaming/overview",
                "gaming_performance": "/api/gaming/performance",
                "defi_liquidity": "/api/defi/liquidity",
                "defi_trading": "/api/defi/trading",
                "nft_collections": "/api/nft/collections",
                "ecosystem_spending": "/api/ecosystem/spending",
                "alerts": "/api/alerts"
            },
            "analytics": {
                "user_segmentation": "/api/users/segmentation",
                "dashboard_overview": "/api/dashboard/overview",
                "whale_activity": "/api/whales/activity",
                "network_timeline": "/api/charts/network-timeline"
            },
            "admin": {
                "clear_cache": "/api/cache/clear",
                "cache_status": "/api/cache/status"
            }
        },
        "total_endpoints": 16,
        "note": "All endpoints support query parameters like time_filter, limit, etc. See /docs for details."
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "api_keys_configured": bool(config.dune_api_key and config.coingecko_api_key)
    }

# RON Market Data endpoint
@app.get("/api/ron/market", response_model=RONMarketData)
async def get_ron_market_data():
    """Get current RON market data from CoinGecko"""
    try:
        market_data = await data_manager.fetch_ron_market_data()
        if not market_data:
            raise HTTPException(status_code=503, detail="Failed to fetch market data")
        return RONMarketData(**market_data)
    except Exception as e:
        logger.error(f"Error fetching RON market data: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Network Health endpoint
@app.get("/api/network/health", response_model=NetworkHealthResponse)
async def get_network_health(time_filter: str = Query("Last 30 days", description="Time filter for analysis")):
    """Get network health score and metrics"""
    try:
        data = await data_manager.load_all_data(time_filter)
        daily_activity = data.get('ronin_daily_activity', pd.DataFrame())
        
        health_data = analytics_engine.calculate_network_health_score(daily_activity)
        return NetworkHealthResponse(**health_data)
    except Exception as e:
        logger.error(f"Error calculating network health: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate network health")

# Gaming Analytics endpoints
@app.get("/api/gaming/overview")
async def get_gaming_overview(time_filter: str = Query("Last 30 days")):
    """Get gaming ecosystem overview"""
    try:
        data = await data_manager.load_all_data(time_filter)
        games_data = data.get('games_overall_activity', pd.DataFrame())
        
        if games_data.empty:
            return {"message": "No gaming data available", "games": []}
        
        # Calculate KPIs - convert numpy types to Python types
        total_games = int(len(games_data))
        total_players = int(games_data['unique_players'].sum()) if 'unique_players' in games_data.columns else 0
        total_volume = float(games_data['total_volume_ron_sent_to_game'].sum()) if 'total_volume_ron_sent_to_game' in games_data.columns else 0
        total_transactions = int(games_data['transaction_count'].sum()) if 'transaction_count' in games_data.columns else 0
        
        return {
            "kpis": {
                "total_games": total_games,
                "total_players": total_players,
                "total_volume_ron": total_volume,
                "total_transactions": total_transactions,
                "avg_players_per_game": total_players / total_games if total_games > 0 else 0,
                "avg_volume_per_game": total_volume / total_games if total_games > 0 else 0
            },
            "games": games_data.to_dict('records')
        }
    except Exception as e:
        logger.error(f"Error fetching gaming overview: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch gaming overview")

@app.get("/api/gaming/performance")
async def get_game_performance_rankings(
    time_filter: str = Query("Last 30 days"),
    min_players: int = Query(100, description="Minimum players for inclusion"),
    limit: int = Query(20, description="Maximum number of games to return")
):
    """Get game performance rankings"""
    try:
        data = await data_manager.load_all_data(time_filter)
        games_data = data.get('games_overall_activity', pd.DataFrame())
        
        if games_data.empty:
            return {"games": []}
        
        # Filter games with minimum activity
        if 'unique_players' in games_data.columns:
            active_games = games_data[games_data['unique_players'] >= min_players]
        else:
            active_games = games_data
        
        # Rank games by performance
        ranked_games = analytics_engine.rank_games_by_performance(active_games)
        
        # Convert to JSON-serializable format
        games_list = []
        for _, game in ranked_games.head(limit).iterrows():
            game_dict = {
                "game_project": game.get('game_project', 'Unknown'),
                "unique_players": int(game.get('unique_players', 0)),
                "transaction_count": int(game.get('transaction_count', 0)),
                "total_volume_ron": float(game.get('total_volume_ron_sent_to_game', 0)),
                "revenue_per_player": float(game.get('revenue_per_player', 0)),
                "performance_score": float(game.get('performance_score', 0))
            }
            games_list.append(game_dict)
        
        return {"games": games_list}
    except Exception as e:
        logger.error(f"Error fetching game performance: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch game performance")

# DeFi Analytics endpoints
@app.get("/api/defi/liquidity")
async def get_liquidity_analysis(time_filter: str = Query("Last 30 days")):
    """Get liquidity flow analysis"""
    try:
        data = await data_manager.load_all_data(time_filter)
        
        flow_data = analytics_engine.detect_liquidity_flows(
            data.get('wron_volume_liquidity', pd.DataFrame()),
            data.get('games_overall_activity', pd.DataFrame()),
            data.get('nft_collections', pd.DataFrame())
        )
        
        return flow_data
    except Exception as e:
        logger.error(f"Error analyzing liquidity: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze liquidity")

@app.get("/api/defi/trading")
async def get_trading_data(time_filter: str = Query("Last 30 days")):
    """Get trading volume and liquidity data"""
    try:
        data = await data_manager.load_all_data(time_filter)
        trading_data = data.get('wron_volume_liquidity', pd.DataFrame())
        
        if trading_data.empty:
            return {"message": "No trading data available", "data": []}
        
        return {
            "data": trading_data.to_dict('records')
        }
    except Exception as e:
        logger.error(f"Error fetching trading data: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch trading data")

# NFT Analytics endpoints
@app.get("/api/nft/collections")
async def get_nft_collections(
    time_filter: str = Query("Last 30 days"),
    limit: int = Query(50, description="Maximum number of collections to return")
):
    """Get NFT collections performance data"""
    try:
        data = await data_manager.load_all_data(time_filter)
        nft_data = data.get('nft_collections', pd.DataFrame())
        
        if nft_data.empty:
            return {"message": "No NFT data available", "collections": []}
        
        # Calculate KPIs
        volume_col = 'sales_volume_usd' if 'sales_volume_usd' in nft_data.columns else 'sales volume (USD)'
        
        kpis = {}
        if volume_col in nft_data.columns:
            total_volume = nft_data[volume_col].sum()
            active_collections = len(nft_data[nft_data[volume_col] > 0])
            kpis = {
                "total_collections": len(nft_data),
                "active_collections": active_collections,
                "total_volume_usd": total_volume,
                "avg_volume_per_collection": total_volume / len(nft_data) if len(nft_data) > 0 else 0
            }
        
        if 'holders' in nft_data.columns:
            kpis["total_holders"] = int(nft_data['holders'].sum())
        
        if 'total_revenue_usd' in nft_data.columns:
            kpis["total_revenue_usd"] = float(nft_data['total_revenue_usd'].sum())
        
        # Sort by volume and limit results
        if volume_col in nft_data.columns:
            top_collections = nft_data.nlargest(limit, volume_col)
        else:
            top_collections = nft_data.head(limit)
        
        return {
            "kpis": kpis,
            "collections": top_collections.to_dict('records')
        }
    except Exception as e:
        logger.error(f"Error fetching NFT data: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch NFT data")

# Spending Analysis endpoint
@app.get("/api/ecosystem/spending")
async def get_spending_analysis(time_filter: str = Query("Last 30 days")):
    """Get RON ecosystem spending analysis"""
    try:
        data = await data_manager.load_all_data(time_filter)
        
        spending_data = analytics_engine.analyze_spending_patterns(
            data.get('games_overall_activity', pd.DataFrame()),
            data.get('nft_collections', pd.DataFrame()),
            data.get('wron_volume_liquidity', pd.DataFrame())
        )
        
        return spending_data
    except Exception as e:
        logger.error(f"Error analyzing spending: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze spending")

# Alerts endpoint
@app.get("/api/alerts", response_model=List[AlertItem])
async def get_alerts(time_filter: str = Query("Last 30 days")):
    """Get comprehensive alerts and monitoring data"""
    try:
        data = await data_manager.load_all_data(time_filter)
        alerts = analytics_engine.generate_comprehensive_alerts(data)
        
        # Convert alerts to proper format
        alert_items = []
        for alert in alerts:
            alert_item = AlertItem(
                type=alert['type'],
                severity=alert['severity'],
                title=alert['title'],
                message=alert['message'],
                details=alert['details'],
                timestamp=alert['timestamp'],
                action=alert['action']
            )
            alert_items.append(alert_item)
        
        return alert_items
    except Exception as e:
        logger.error(f"Error generating alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate alerts")

# User Segmentation endpoint
@app.get("/api/users/segmentation")
async def get_user_segmentation(time_filter: str = Query("Last 30 days")):
    """Get user segmentation data"""
    try:
        data = await data_manager.load_all_data(time_filter)
        segmentation_data = data.get('ron_segmented_holders', pd.DataFrame())
        
        if segmentation_data.empty:
            return {"message": "No segmentation data available", "segments": []}
        
        return {
            "segments": segmentation_data.to_dict('records')
        }
    except Exception as e:
        logger.error(f"Error fetching user segmentation: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch user segmentation")

# Comprehensive data endpoint
@app.get("/api/dashboard/overview")
async def get_dashboard_overview(time_filter: str = Query("Last 30 days")):
    """Get comprehensive dashboard data for frontend"""
    try:
        data = await data_manager.load_all_data(time_filter)
        
        # RON market data
        ron_market = await data_manager.fetch_ron_market_data()
        
        # Network health
        daily_activity = data.get('ronin_daily_activity', pd.DataFrame())
        network_health = analytics_engine.calculate_network_health_score(daily_activity)
        
        # Gaming KPIs
        games_data = data.get('games_overall_activity', pd.DataFrame())
        gaming_kpis = {}
        if not games_data.empty:
            gaming_kpis = {
                "total_games": len(games_data),
                "total_players": int(games_data['unique_players'].sum()) if 'unique_players' in games_data.columns else 0,
                "total_volume": float(games_data['total_volume_ron_sent_to_game'].sum()) if 'total_volume_ron_sent_to_game' in games_data.columns else 0,
                "total_transactions": int(games_data['transaction_count'].sum()) if 'transaction_count' in games_data.columns else 0
            }
        
        # NFT KPIs
        nft_data = data.get('nft_collections', pd.DataFrame())
        nft_kpis = {}
        if not nft_data.empty:
            volume_col = 'sales_volume_usd' if 'sales_volume_usd' in nft_data.columns else 'sales volume (USD)'
            if volume_col in nft_data.columns:
                nft_kpis = {
                    "total_collections": len(nft_data),
                    "total_volume_usd": float(nft_data[volume_col].sum()),
                    "active_collections": len(nft_data[nft_data[volume_col] > 0])
                }
        
        # Spending analysis
        spending_analysis = analytics_engine.analyze_spending_patterns(
            games_data,
            nft_data,
            data.get('wron_volume_liquidity', pd.DataFrame())
        )
        
        # User segmentation
        segmentation = data.get('ron_segmented_holders', pd.DataFrame())
        user_segments = segmentation.to_dict('records') if not segmentation.empty else []
        
        return {
            "ron_market": ron_market,
            "network_health": network_health,
            "gaming_kpis": gaming_kpis,
            "nft_kpis": nft_kpis,
            "spending_analysis": spending_analysis,
            "user_segments": user_segments,
            "timestamp": datetime.now().isoformat(),
            "time_filter": time_filter
        }
    except Exception as e:
        logger.error(f"Error fetching dashboard overview: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch dashboard overview")

# Whale tracking endpoint
@app.get("/api/whales/activity")
async def get_whale_activity(
    time_filter: str = Query("Last 30 days"),
    threshold: int = Query(50000, description="Minimum transaction size in USD")
):
    """Get whale activity tracking"""
    try:
        data = await data_manager.load_all_data(time_filter)
        whale_data = data.get('wron_whale_tracking', pd.DataFrame())
        
        if whale_data.empty:
            return {"message": "No whale data available", "transactions": []}
        
        # Filter large transactions
        large_trades = []
        if 'trade_volume_usd' in whale_data.columns:
            filtered_whales = whale_data[whale_data['trade_volume_usd'] >= threshold]
            large_trades = filtered_whales.to_dict('records')
        
        return {
            "whale_threshold": threshold,
            "total_whale_transactions": len(large_trades),
            "transactions": large_trades
        }
    except Exception as e:
        logger.error(f"Error fetching whale activity: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch whale activity")

# Cache management endpoints
@app.post("/api/cache/clear")
async def clear_cache():
    """Clear data cache (admin endpoint)"""
    try:
        import shutil
        if os.path.exists(data_manager.cache_dir):
            shutil.rmtree(data_manager.cache_dir)
            os.makedirs(data_manager.cache_dir, exist_ok=True)
        
        return {"message": "Cache cleared successfully", "timestamp": datetime.now().isoformat()}
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear cache")

@app.get("/api/cache/status")
async def get_cache_status():
    """Get cache status information"""
    try:
        cache_files = []
        if os.path.exists(data_manager.cache_dir):
            for filename in os.listdir(data_manager.cache_dir):
                filepath = os.path.join(data_manager.cache_dir, filename)
                if os.path.isfile(filepath):
                    stat = os.stat(filepath)
                    age_hours = (time.time() - stat.st_mtime) / 3600
                    cache_files.append({
                        "filename": filename,
                        "size_mb": round(stat.st_size / (1024 * 1024), 2),
                        "age_hours": round(age_hours, 1),
                        "valid": age_hours < (config.cache_duration / 3600)
                    })
        
        return {
            "cache_directory": data_manager.cache_dir,
            "cache_duration_hours": config.cache_duration / 3600,
            "total_files": len(cache_files),
            "files": cache_files
        }
    except Exception as e:
        logger.error(f"Error getting cache status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get cache status")

# Charts/Visualization data endpoints
@app.get("/api/charts/network-timeline")
async def get_network_timeline_data(time_filter: str = Query("Last 30 days")):
    """Get network activity timeline data for charts"""
    try:
        data = await data_manager.load_all_data(time_filter)
        daily_data = data.get('ronin_daily_activity', pd.DataFrame())
        
        if daily_data.empty:
            return {"message": "No timeline data available", "data": []}
        
        # Prepare chart data
        chart_data = []
        for _, row in daily_data.iterrows():
            chart_data.append({
                "date": row.get('day', '').strftime('%Y-%m-%d') if pd.notna(row.get('day')) else '',
                "active_wallets": int(row.get('active_wallets', 0)),
                "daily_transactions": int(row.get('daily_transactions', 0)),
                "avg_gas_price": float(row.get('avg_gas_price_in_gwei', 0))
            })
        
        return {
            "data": chart_data,
            "metrics": {
                "total_days": len(chart_data),
                "avg_active_wallets": sum(d['active_wallets'] for d in chart_data) / len(chart_data) if chart_data else 0,
                "avg_daily_transactions": sum(d['daily_transactions'] for d in chart_data) / len(chart_data) if chart_data else 0
            }
        }
    except Exception as e:
        logger.error(f"Error fetching timeline data: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch timeline data")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False  # Set to False for production
    )