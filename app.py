#!/usr/bin/env python3
"""
Ronin Ecosystem Data Fetcher
A robust data collection system for the Ronin blockchain ecosystem analytics platform.

Features:
- Comprehensive error handling and retry logic
- Rate limiting and API management
- Data validation and caching
- Consistent configuration management
- Fallback mechanisms for reliability

Author: Analytics Team
Date: 2025
"""

import os
import time
import logging
import requests
import joblib
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dotenv import load_dotenv
from dune_client.client import DuneClient
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ronin_fetcher.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RoninDataFetcher:
    """Main class for fetching and managing Ronin ecosystem data."""
    
    def __init__(self, config_file: str = None):
        """Initialize the data fetcher with configuration."""
        load_dotenv()
        
        # API Configuration
        self.api_keys = self._load_api_keys()
        self.validate_api_keys()
        
        # Data Configuration
        self.data_dir = Path("data")
        self.data_dir.mkdir(exist_ok=True)
        
        # Query Configuration
        self.dune_queries = self._load_query_config()
        
        # Cache Configuration
        self.cache_ttl = 86400  # 24 hours
        self.cache_lock = threading.Lock()
        
        # Rate Limiting Configuration
        self.coingecko_delay = 1.2  # seconds between calls
        self.dune_delay = 2.0       # seconds between calls
        self.max_retries = 3
        self.retry_delay = 5        # seconds
        
        # Session management
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'RoninEcosystemTracker/1.0',
            'Accept': 'application/json'
        })
        
        logger.info("RoninDataFetcher initialized successfully")
    
    def _load_api_keys(self) -> Dict[str, str]:
        """Load and validate API keys from environment variables."""
        return {
            'dune': os.getenv("DEFI_JOSH_DUNE_QUERY_API_KEY"),
            'coingecko': os.getenv("COINGECKO_PRO_API_KEY")
        }
    
    def validate_api_keys(self) -> None:
        """Validate that required API keys are present."""
        missing_keys = []
        
        for service, key in self.api_keys.items():
            if not key:
                missing_keys.append(service)
                logger.warning(f"Missing API key for {service}")
        
        if missing_keys:
            logger.error(f"Missing API keys: {', '.join(missing_keys)}")
            raise ValueError(f"Missing required API keys: {', '.join(missing_keys)}")
    
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
                'description': 'Daily Ronin Transactions, Active users/wallets, and Gas fees',
                'filename': 'ronin_daily_activity.joblib'
            },
            'user_activation_retention': {
                'id': 5783320,
                'description': 'Ronin User/Gamer Weekly Activation and Retention',
                'filename': 'ronin_users_weekly_activation_and_retention_for_each_project_or_game.joblib'
            },
            'ron_current_holders': {
                'id': 5783623,
                'description': 'RON/WRON current holders',
                'filename': 'ron_current_holders.joblib'
            },
            'ron_segmented_holders': {
                'id': 5785491,
                'description': 'RON/WRON current holders (segmented)',
                'filename': 'ron_current_segmented_holders.joblib'
            },
            'wron_katana_pairs': {
                'id': 5783967,
                'description': 'WRON Active Trade pairs on Katana DEX',
                'filename': 'wron_active_trade_pairs_on_Katana.joblib'
            },
            'wron_whale_tracking': {
                'id': 5784215,
                'description': 'Top WRON Katana DEX Traders (Whale Tracking)',
                'filename': 'wron_whale_tracking_on_Katana.joblib'
            },
            'wron_volume_liquidity': {
                'id': 5784210,
                'description': 'Daily WRON Trading Volume & Liquidity Flow on Katana',
                'filename': 'WRON_Trading_Volume_&_Liquidity_Flow_on_Katana.joblib'
            },
            'wron_hourly_activity': {
                'id': 5785066,
                'description': 'WRON Trading Activity by Hour of Day on Katana',
                'filename': 'WRON_Trading_by_hour_of_day_on_Katana.joblib'
            },
            'wron_weekly_segmentation': {
                'id': 5785149,
                'description': 'Weekly WRON Trade Volume & User Segmentation on Katana',
                'filename': 'WRON_weekly_trade_volume_and_user_segmentation_on_Katana.joblib'
            }
        }
    
    def is_cache_valid(self, filepath: Path) -> bool:
        """Check if cached data is still valid based on TTL."""
        try:
            if not filepath.exists():
                return False
            
            file_age = time.time() - filepath.stat().st_mtime
            return file_age < self.cache_ttl
        
        except Exception as e:
            logger.warning(f"Error checking cache validity for {filepath}: {e}")
            return False
    
    def fetch_coingecko_data(self) -> Optional[Dict[str, Any]]:
        """Fetch RON token data from CoinGecko Pro API with comprehensive error handling."""
        cache_file = self.data_dir / 'ron_coingecko_data.joblib'
        
        # Check cache first
        if self.is_cache_valid(cache_file):
            try:
                logger.info("Loading RON data from cache")
                return joblib.load(cache_file)
            except Exception as e:
                logger.warning(f"Failed to load cached CoinGecko data: {e}")
        
        # Fetch fresh data
        url = "https://pro-api.coingecko.com/api/v3/coins/ronin"
        headers = {"x-cg-pro-api-key": self.api_keys['coingecko']}
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Fetching RON data from CoinGecko (attempt {attempt + 1})")
                
                response = self.session.get(url, headers=headers, timeout=30)
                response.raise_for_status()
                
                ron_data = response.json()
                
                # Validate response structure
                if not self._validate_coingecko_response(ron_data):
                    raise ValueError("Invalid response structure from CoinGecko")
                
                # Extract and structure key metrics
                processed_data = self._process_coingecko_data(ron_data)
                
                # Cache the data
                try:
                    joblib.dump(processed_data, cache_file)
                    logger.info("CoinGecko data cached successfully")
                except Exception as e:
                    logger.warning(f"Failed to cache CoinGecko data: {e}")
                
                time.sleep(self.coingecko_delay)
                return processed_data
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"CoinGecko API request failed (attempt {attempt + 1}): {e}")
                if attempt == self.max_retries - 1:
                    logger.error("All CoinGecko API attempts failed")
                    return self._get_coingecko_fallback_data()
                time.sleep(self.retry_delay * (attempt + 1))
                
            except Exception as e:
                logger.error(f"Unexpected error fetching CoinGecko data: {e}")
                return self._get_coingecko_fallback_data()
        
        return None
    
    def _validate_coingecko_response(self, data: Dict[str, Any]) -> bool:
        """Validate CoinGecko response structure."""
        required_fields = ['name', 'symbol', 'market_data']
        
        for field in required_fields:
            if field not in data:
                logger.warning(f"Missing required field in CoinGecko response: {field}")
                return False
        
        market_data = data.get('market_data', {})
        required_market_fields = ['current_price', 'market_cap', 'total_volume']
        
        for field in required_market_fields:
            if field not in market_data:
                logger.warning(f"Missing required market data field: {field}")
                return False
        
        return True
    
    def _process_coingecko_data(self, ron_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process and structure CoinGecko data."""
        market_data = ron_data.get("market_data", {})
        links = ron_data.get("links", {})
        image = ron_data.get("image", {})
        
        return {
            # Basic Info
            'name': ron_data.get('name'),
            'symbol': ron_data.get('symbol'),
            'contract_address': ron_data.get('contract_address'),
            'homepage': links.get('homepage', [None])[0] if links.get('homepage') else None,
            'logo_url': image.get('large'),
            
            # Market Metrics
            'price_usd': market_data.get('current_price', {}).get('usd'),
            'market_cap_usd': market_data.get('market_cap', {}).get('usd'),
            'volume_24h_usd': market_data.get('total_volume', {}).get('usd'),
            'circulating_supply': market_data.get('circulating_supply'),
            'total_supply': market_data.get('total_supply'),
            'max_supply': market_data.get('max_supply'),
            'fully_diluted_valuation_usd': market_data.get('fully_diluted_valuation', {}).get('usd'),
            'total_value_locked_usd': market_data.get('total_value_locked', {}).get('usd'),
            'mcap_to_tvl_ratio': market_data.get('mcap_to_tvl_ratio'),
            
            # Price Changes
            'price_change_24h_pct': market_data.get('price_change_percentage_24h'),
            'price_change_7d_pct': market_data.get('price_change_percentage_7d'),
            'price_change_30d_pct': market_data.get('price_change_percentage_30d'),
            
            # Exchange Info
            'exchanges_count': len(ron_data.get('tickers', [])),
            'last_updated': datetime.now().isoformat(),
            'data_source': 'coingecko_pro'
        }
    
    def _get_coingecko_fallback_data(self) -> Dict[str, Any]:
        """Return fallback data when CoinGecko API fails."""
        logger.info("Using CoinGecko fallback data")
        return {
            'name': 'Ronin',
            'symbol': 'ron',
            'price_usd': None,
            'market_cap_usd': None,
            'volume_24h_usd': None,
            'last_updated': datetime.now().isoformat(),
            'data_source': 'fallback',
            'status': 'api_unavailable'
        }
    
    def fetch_dune_query(self, query_key: str) -> Optional[pd.DataFrame]:
        """Fetch data from a specific Dune query with error handling."""
        if query_key not in self.dune_queries:
            logger.error(f"Unknown query key: {query_key}")
            return None
        
        query_config = self.dune_queries[query_key]
        cache_file = self.data_dir / query_config['filename']
        
        # Check cache first
        if self.is_cache_valid(cache_file):
            try:
                logger.info(f"Loading {query_config['description']} from cache")
                return joblib.load(cache_file)
            except Exception as e:
                logger.warning(f"Failed to load cached data for {query_key}: {e}")
        
        # Fetch fresh data
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Fetching {query_config['description']} from Dune (attempt {attempt + 1})")
                
                dune = DuneClient(self.api_keys['dune'])
                query_result = dune.get_latest_result(query_config['id'])
                
                if not query_result or not query_result.result:
                    raise ValueError(f"Empty result from Dune query {query_config['id']}")
                
                rows = query_result.result.rows
                if not rows:
                    logger.warning(f"No data returned from query {query_key}")
                    return pd.DataFrame()
                
                df = pd.DataFrame(rows)
                
                # Validate DataFrame
                if df.empty:
                    logger.warning(f"Empty DataFrame for query {query_key}")
                    return df
                
                # Add metadata
                df.attrs['query_id'] = query_config['id']
                df.attrs['last_updated'] = datetime.now().isoformat()
                df.attrs['description'] = query_config['description']
                
                # Cache the data
                try:
                    joblib.dump(df, cache_file)
                    logger.info(f"Cached data for {query_key}")
                except Exception as e:
                    logger.warning(f"Failed to cache data for {query_key}: {e}")
                
                time.sleep(self.dune_delay)
                return df
                
            except Exception as e:
                logger.warning(f"Dune query {query_key} failed (attempt {attempt + 1}): {e}")
                if attempt == self.max_retries - 1:
                    logger.error(f"All attempts failed for Dune query {query_key}")
                    return self._get_dune_fallback_data(query_key)
                time.sleep(self.retry_delay * (attempt + 1))
        
        return None
    
    def _get_dune_fallback_data(self, query_key: str) -> pd.DataFrame:
        """Return empty DataFrame with metadata when Dune query fails."""
        logger.info(f"Using fallback data for {query_key}")
        df = pd.DataFrame()
        df.attrs['query_id'] = self.dune_queries[query_key]['id']
        df.attrs['last_updated'] = datetime.now().isoformat()
        df.attrs['status'] = 'api_unavailable'
        return df
    
    def fetch_all_dune_data(self) -> Dict[str, pd.DataFrame]:
        """Fetch all Dune queries with proper error handling and rate limiting."""
        results = {}
        
        logger.info("Starting to fetch all Dune data")
        
        for query_key in self.dune_queries.keys():
            try:
                df = self.fetch_dune_query(query_key)
                results[query_key] = df
                logger.info(f"Successfully fetched {query_key}: {len(df) if df is not None else 0} rows")
            except Exception as e:
                logger.error(f"Failed to fetch {query_key}: {e}")
                results[query_key] = self._get_dune_fallback_data(query_key)
        
        logger.info(f"Completed fetching all Dune data: {len(results)} datasets")
        return results
    
    def get_data_summary(self) -> Dict[str, Any]:
        """Get summary of all available data."""
        summary = {
            'coingecko_data': None,
            'dune_data': {},
            'cache_status': {},
            'last_updated': datetime.now().isoformat()
        }
        
        # Check CoinGecko cache
        coingecko_cache = self.data_dir / 'ron_coingecko_data.joblib'
        summary['cache_status']['coingecko'] = {
            'exists': coingecko_cache.exists(),
            'valid': self.is_cache_valid(coingecko_cache),
            'last_modified': datetime.fromtimestamp(
                coingecko_cache.stat().st_mtime
            ).isoformat() if coingecko_cache.exists() else None
        }
        
        # Check Dune caches
        for query_key, config in self.dune_queries.items():
            cache_file = self.data_dir / config['filename']
            summary['cache_status'][query_key] = {
                'exists': cache_file.exists(),
                'valid': self.is_cache_valid(cache_file),
                'last_modified': datetime.fromtimestamp(
                    cache_file.stat().st_mtime
                ).isoformat() if cache_file.exists() else None
            }
        
        return summary
    
    def run_full_data_collection(self) -> Tuple[Dict[str, Any], Dict[str, pd.DataFrame]]:
        """Run complete data collection process."""
        logger.info("Starting full data collection")
        
        start_time = time.time()
        
        # Fetch CoinGecko data
        coingecko_data = self.fetch_coingecko_data()
        
        # Fetch all Dune data
        dune_data = self.fetch_all_dune_data()
        
        # Log collection summary
        total_time = time.time() - start_time
        successful_queries = sum(1 for df in dune_data.values() if df is not None and not df.empty)
        
        logger.info(f"Data collection completed in {total_time:.2f} seconds")
        logger.info(f"CoinGecko data: {'Success' if coingecko_data else 'Failed'}")
        logger.info(f"Dune queries: {successful_queries}/{len(self.dune_queries)} successful")
        
        return coingecko_data, dune_data
    
    def cleanup_old_cache(self, days_old: int = 7) -> None:
        """Clean up cache files older than specified days."""
        cutoff_time = time.time() - (days_old * 86400)
        
        for cache_file in self.data_dir.glob('*.joblib'):
            try:
                if cache_file.stat().st_mtime < cutoff_time:
                    cache_file.unlink()
                    logger.info(f"Removed old cache file: {cache_file}")
            except Exception as e:
                logger.warning(f"Failed to remove cache file {cache_file}: {e}")


def main():
    """Main execution function for testing and development."""
    try:
        # Initialize fetcher
        fetcher = RoninDataFetcher()
        
        # Print data summary
        summary = fetcher.get_data_summary()
        print("Data Summary:")
        print(f"CoinGecko cache valid: {summary['cache_status']['coingecko']['valid']}")
        
        for query_key in fetcher.dune_queries.keys():
            cache_info = summary['cache_status'][query_key]
            print(f"{query_key}: {'Valid' if cache_info['valid'] else 'Stale/Missing'}")
        
        # Run data collection if needed
        response = input("\nRun full data collection? (y/n): ")
        if response.lower() == 'y':
            coingecko_data, dune_data = fetcher.run_full_data_collection()
            
            print("\nData Collection Results:")
            print(f"CoinGecko: {'Success' if coingecko_data else 'Failed'}")
            
            for query_key, df in dune_data.items():
                status = f"{len(df)} rows" if df is not None and not df.empty else "Failed/Empty"
                print(f"{query_key}: {status}")
        
        print("\nData collection complete!")
        
    except Exception as e:
        logger.error(f"Main execution failed: {e}")
        raise


if __name__ == "__main__":
    main()