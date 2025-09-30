"""
Ronin Ecosystem Tracker - FastAPI Backend
Version 3.0 - Raw Data Pass-Through with 24-Hour Caching
Author: DeFi Jo$h
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Query
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pandas as pd
import os
import time
import hashlib
import joblib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
from dune_client.client import DuneClient
from dotenv import load_dotenv
import asyncio
import aiohttp
from pydantic import BaseModel
from contextlib import asynccontextmanager
import json

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
class Config:
    def __init__(self):
        self.dune_api_key = os.getenv("DEFI_JOSH_DUNE_QUERY_API_KEY")
        self.coingecko_api_key = os.getenv("COINGECKO_PRO_API_KEY")
        
        # Dune query IDs - EXACTLY as they are in Dune
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
            'nft_collections': 5792313
        }
        
        self.cache_duration = 86400  # 24 hours in seconds
        
        if not self.dune_api_key or not self.coingecko_api_key:
            logger.warning("API keys not found. Some functionality may be limited.")

config = Config()

# Pydantic models for metadata
class DataMetadata(BaseModel):
    source: str
    query_id: Optional[int] = None
    last_updated: str
    cache_age_hours: float
    is_fresh: bool
    next_refresh: str
    row_count: int

class CachedDataResponse(BaseModel):
    metadata: DataMetadata
    data: List[Dict[str, Any]]

# Simple Cache Manager - NO DATA MANIPULATION
class CacheManager:
    def __init__(self):
        self.cache_dir = "raw_data_cache"
        os.makedirs(self.cache_dir, exist_ok=True)
        
        if config.dune_api_key:
            self.dune_client = DuneClient(config.dune_api_key)
        
        self.session_headers = {}
        if config.coingecko_api_key:
            self.session_headers['x-cg-pro-api-key'] = config.coingecko_api_key
        
        # Track last update times
        self.metadata_file = os.path.join(self.cache_dir, "cache_metadata.json")
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict:
        """Load cache metadata from file"""
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_metadata(self):
        """Save cache metadata to file"""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")
    
    def _get_cache_path(self, key: str) -> str:
        """Get cache file path for a key"""
        safe_key = hashlib.md5(key.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{safe_key}.joblib")
    
    def _is_cache_valid(self, key: str) -> bool:
        """Check if cache is still valid (< 24 hours old)"""
        filepath = self._get_cache_path(key)
        if not os.path.exists(filepath):
            return False
        
        file_age = time.time() - os.path.getmtime(filepath)
        return file_age < config.cache_duration
    
    def _get_cache_age(self, key: str) -> float:
        """Get cache age in hours"""
        filepath = self._get_cache_path(key)
        if not os.path.exists(filepath):
            return float('inf')
        
        file_age = time.time() - os.path.getmtime(filepath)
        return file_age / 3600  # Convert to hours
    
    def get_cached_data(self, key: str) -> Optional[pd.DataFrame]:
        """Get data from cache if valid"""
        if self._is_cache_valid(key):
            filepath = self._get_cache_path(key)
            try:
                return joblib.load(filepath)
            except Exception as e:
                logger.warning(f"Cache read error for {key}: {e}")
        return None
    
    def cache_data(self, key: str, data: pd.DataFrame):
        """Save data to cache"""
        filepath = self._get_cache_path(key)
        try:
            joblib.dump(data, filepath)
            
            # Update metadata
            self.metadata[key] = {
                'last_updated': datetime.now().isoformat(),
                'row_count': len(data)
            }
            self._save_metadata()
            
            logger.info(f"Cached {key}: {len(data)} rows")
        except Exception as e:
            logger.error(f"Cache write error for {key}: {e}")
    
    async def fetch_coingecko_raw(self) -> dict:
        """Fetch raw CoinGecko data - NO MANIPULATION"""
        try:
            async with aiohttp.ClientSession(headers=self.session_headers) as session:
                url = "https://pro-api.coingecko.com/api/v3/coins/ronin"
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    response.raise_for_status()
                    data = await response.json()
                    
                    # Return EXACTLY what CoinGecko returns
                    return data
        except Exception as e:
            logger.error(f"Failed to fetch CoinGecko data: {e}")
            return {}
    
    async def fetch_dune_raw(self, query_key: str) -> pd.DataFrame:
        """Fetch raw Dune data - NO MANIPULATION"""
        
        # Check cache first
        cached = self.get_cached_data(query_key)
        if cached is not None:
            logger.info(f"Using cached data for {query_key}")
            return cached
        
        # Fetch from Dune API
        if not hasattr(self, 'dune_client'):
            logger.warning("Dune client not initialized")
            return pd.DataFrame()
        
        try:
            logger.info(f"Fetching fresh data for {query_key}...")
            
            def fetch_sync():
                query_id = config.dune_queries[query_key]
                result = self.dune_client.get_latest_result(query_id)
                return pd.DataFrame(result.result.rows)
            
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(None, fetch_sync)
            
            # ONLY convert datetime columns - NO OTHER CHANGES
            for col in df.columns:
                if df[col].dtype == 'object':
                    try:
                        df[col] = pd.to_datetime(df[col], errors='ignore')
                    except:
                        pass
            
            # Cache the result
            self.cache_data(query_key, df)
            
            logger.info(f"Successfully fetched {query_key}: {len(df)} rows")
            return df
            
        except Exception as e:
            logger.error(f"Failed to fetch {query_key}: {e}")
            return pd.DataFrame()
    
    def get_metadata_for_key(self, key: str, source: str, query_id: Optional[int] = None, 
                            row_count: int = 0) -> DataMetadata:
        """Generate metadata for a cached dataset"""
        cache_age = self._get_cache_age(key)
        last_updated = self.metadata.get(key, {}).get('last_updated', 'Unknown')
        
        if cache_age == float('inf'):
            next_refresh = 'Not cached yet'
            is_fresh = False
        else:
            is_fresh = cache_age < 24
            hours_until_refresh = 24 - cache_age
            next_refresh_time = datetime.now() + timedelta(hours=hours_until_refresh)
            next_refresh = next_refresh_time.isoformat()
        
        return DataMetadata(
            source=source,
            query_id=query_id,
            last_updated=last_updated,
            cache_age_hours=round(cache_age, 2) if cache_age != float('inf') else 0,
            is_fresh=is_fresh,
            next_refresh=next_refresh,
            row_count=row_count
        )

# Global cache manager
cache_manager = CacheManager()

# Background task for auto-refresh
async def refresh_all_data_background():
    """Background task to refresh all data every 24 hours"""
    while True:
        try:
            logger.info("Starting background data refresh...")
            
            # Refresh CoinGecko data
            coingecko_data = await cache_manager.fetch_coingecko_raw()
            if coingecko_data:
                cache_manager.cache_data('coingecko_ron', pd.DataFrame([coingecko_data]))
            
            # Refresh all Dune queries
            for query_key in config.dune_queries.keys():
                await cache_manager.fetch_dune_raw(query_key)
                await asyncio.sleep(5)  # Rate limiting
            
            logger.info("Background refresh completed")
            
        except Exception as e:
            logger.error(f"Background refresh failed: {e}")
        
        # Wait 24 hours
        await asyncio.sleep(86400)

# Lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Ronin Ecosystem Tracker API v3.0")
    
    # Start background refresh task
    refresh_task = asyncio.create_task(refresh_all_data_background())
    
    yield
    
    # Shutdown
    refresh_task.cancel()
    logger.info("Shutting down API")

# FastAPI app
app = FastAPI(
    title="Ronin Ecosystem Tracker API - Raw Data",
    description="Direct pass-through API for Ronin blockchain data with 24-hour caching",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== ROOT & HEALTH ENDPOINTS ====================

@app.get("/")
async def root(request: Request):
    base_url = str(request.base_url).rstrip('/')
    
    return {
        "message": "Ronin Ecosystem Tracker API - Raw Data v3.0",
        "version": "3.0.0",
        "status": "online",
        "documentation": f"{base_url}/docs",
        "cache_info": f"{base_url}/api/cache/status",
        "endpoints": {
            "coingecko": {
                "ron_market_data": "/api/raw/coingecko/ron"
            },
            "dune_queries": {
                "games_overall_activity": "/api/raw/dune/games_overall_activity",
                "games_daily_activity": "/api/raw/dune/games_daily_activity",
                "ronin_daily_activity": "/api/raw/dune/ronin_daily_activity",
                "user_activation_retention": "/api/raw/dune/user_activation_retention",
                "ron_current_holders": "/api/raw/dune/ron_current_holders",
                "ron_segmented_holders": "/api/raw/dune/ron_segmented_holders",
                "wron_active_trade_pairs": "/api/raw/dune/wron_active_trade_pairs",
                "wron_whale_tracking": "/api/raw/dune/wron_whale_tracking",
                "wron_volume_liquidity": "/api/raw/dune/wron_volume_liquidity",
                "wron_trading_hourly": "/api/raw/dune/wron_trading_hourly",
                "wron_weekly_segmentation": "/api/raw/dune/wron_weekly_segmentation",
                "nft_collections": "/api/raw/dune/nft_collections"
            },
            "utilities": {
                "cache_status": "/api/cache/status",
                "force_refresh": "/api/cache/refresh",
                "clear_cache": "/api/cache/clear"
            }
        },
        "total_data_sources": 13,
        "cache_duration": "24 hours",
        "note": "All endpoints return RAW data exactly as received from APIs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "3.0.0",
        "api_keys_configured": {
            "dune": bool(config.dune_api_key),
            "coingecko": bool(config.coingecko_api_key)
        },
        "cache_directory": cache_manager.cache_dir
    }

# ==================== COINGECKO ENDPOINT ====================

@app.get("/api/raw/coingecko/ron", response_model=CachedDataResponse)
async def get_coingecko_ron_data():
    """
    Get RAW CoinGecko data for Ronin (RON)
    Returns exactly what CoinGecko API returns - no manipulation
    """
    try:
        # Check cache
        cached = cache_manager.get_cached_data('coingecko_ron')
        
        if cached is not None and not cached.empty:
            data = cached.to_dict('records')[0]
        else:
            # Fetch fresh data
            data = await cache_manager.fetch_coingecko_raw()
            if data:
                cache_manager.cache_data('coingecko_ron', pd.DataFrame([data]))
        
        if not data:
            raise HTTPException(status_code=503, detail="Failed to fetch CoinGecko data")
        
        # Generate metadata
        metadata = cache_manager.get_metadata_for_key(
            'coingecko_ron',
            source='CoinGecko Pro API',
            row_count=1
        )
        
        return CachedDataResponse(
            metadata=metadata,
            data=[data]
        )
        
    except Exception as e:
        logger.error(f"Error in CoinGecko endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== DUNE ENDPOINTS (12 queries) ====================

@app.get("/api/raw/dune/{query_key}", response_model=CachedDataResponse)
async def get_dune_data(query_key: str):
    """
    Get RAW Dune Analytics data for a specific query
    Returns exactly what Dune API returns - no manipulation
    
    Available query_keys:
    - games_overall_activity
    - games_daily_activity
    - ronin_daily_activity
    - user_activation_retention
    - ron_current_holders
    - ron_segmented_holders
    - wron_active_trade_pairs
    - wron_whale_tracking
    - wron_volume_liquidity
    - wron_trading_hourly
    - wron_weekly_segmentation
    - nft_collections
    """
    try:
        # Validate query key
        if query_key not in config.dune_queries:
            raise HTTPException(
                status_code=404,
                detail=f"Query key '{query_key}' not found. Available keys: {list(config.dune_queries.keys())}"
            )
        
        # Fetch data
        df = await cache_manager.fetch_dune_raw(query_key)
        
        if df.empty:
            raise HTTPException(
                status_code=503,
                detail=f"No data available for query '{query_key}'"
            )
        
        # Convert DataFrame to list of dicts
        data = df.to_dict('records')
        
        # Generate metadata
        metadata = cache_manager.get_metadata_for_key(
            query_key,
            source='Dune Analytics',
            query_id=config.dune_queries[query_key],
            row_count=len(data)
        )
        
        return CachedDataResponse(
            metadata=metadata,
            data=data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in Dune endpoint for {query_key}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== CACHE MANAGEMENT ENDPOINTS ====================

@app.get("/api/cache/status")
async def get_cache_status():
    """Get detailed cache status for all data sources"""
    try:
        status = {
            "cache_directory": cache_manager.cache_dir,
            "cache_duration_hours": 24,
            "total_sources": 13,
            "sources": {}
        }
        
        # CoinGecko status
        cg_age = cache_manager._get_cache_age('coingecko_ron')
        status['sources']['coingecko_ron'] = {
            "type": "CoinGecko",
            "cache_age_hours": round(cg_age, 2) if cg_age != float('inf') else None,
            "is_cached": cg_age != float('inf'),
            "is_fresh": cg_age < 24 if cg_age != float('inf') else False,
            "last_updated": cache_manager.metadata.get('coingecko_ron', {}).get('last_updated', 'Never')
        }
        
        # Dune queries status
        for query_key in config.dune_queries.keys():
            age = cache_manager._get_cache_age(query_key)
            status['sources'][query_key] = {
                "type": "Dune Analytics",
                "query_id": config.dune_queries[query_key],
                "cache_age_hours": round(age, 2) if age != float('inf') else None,
                "is_cached": age != float('inf'),
                "is_fresh": age < 24 if age != float('inf') else False,
                "last_updated": cache_manager.metadata.get(query_key, {}).get('last_updated', 'Never'),
                "row_count": cache_manager.metadata.get(query_key, {}).get('row_count', 0)
            }
        
        return status
        
    except Exception as e:
        logger.error(f"Error getting cache status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/cache/refresh")
async def force_refresh_all():
    """
    Force refresh all data sources
    This endpoint is designed to be called by external cron services
    """
    try:
        logger.info("Force refresh started...")
        refresh_results = {
            "started_at": datetime.now().isoformat(),
            "results": {}
        }
        
        # Refresh CoinGecko
        try:
            coingecko_data = await cache_manager.fetch_coingecko_raw()
            if coingecko_data:
                cache_manager.cache_data('coingecko_ron', pd.DataFrame([coingecko_data]))
                refresh_results['results']['coingecko'] = "success"
            else:
                refresh_results['results']['coingecko'] = "no data"
        except Exception as e:
            logger.error(f"CoinGecko refresh failed: {e}")
            refresh_results['results']['coingecko'] = f"error: {str(e)}"
        
        # Refresh all Dune queries
        for query_key in config.dune_queries.keys():
            try:
                df = await cache_manager.fetch_dune_raw(query_key)
                if not df.empty:
                    refresh_results['results'][query_key] = f"success ({len(df)} rows)"
                else:
                    refresh_results['results'][query_key] = "no data"
            except Exception as e:
                logger.error(f"{query_key} refresh failed: {e}")
                refresh_results['results'][query_key] = f"error: {str(e)}"
            
            await asyncio.sleep(3)  # Rate limiting
        
        refresh_results['completed_at'] = datetime.now().isoformat()
        logger.info("Force refresh completed")
        
        return refresh_results
        
    except Exception as e:
        logger.error(f"Force refresh failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.post("/api/cache/clear")
async def clear_cache():
    """Clear all cached data"""
    try:
        import shutil
        if os.path.exists(cache_manager.cache_dir):
            shutil.rmtree(cache_manager.cache_dir)
            os.makedirs(cache_manager.cache_dir, exist_ok=True)
        
        cache_manager.metadata = {}
        cache_manager._save_metadata()
        
        return {
            "message": "Cache cleared successfully",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== BULK ENDPOINT (OPTIONAL) ====================

@app.get("/api/bulk/all")
async def get_all_data():
    """
    Get all data sources at once (CoinGecko + all 12 Dune queries)
    Useful for dashboard initialization
    """
    try:
        result = {
            "timestamp": datetime.now().isoformat(),
            "coingecko": {},
            "dune": {}
        }
        
        # Get CoinGecko data
        try:
            cg_response = await get_coingecko_ron_data()
            result['coingecko']['ron'] = {
                "metadata": cg_response.metadata.dict(),
                "data": cg_response.data
            }
        except Exception as e:
            logger.error(f"Error fetching CoinGecko in bulk: {e}")
            result['coingecko']['ron'] = {"error": str(e)}
        
        # Get all Dune queries
        for query_key in config.dune_queries.keys():
            try:
                dune_response = await get_dune_data(query_key)
                result['dune'][query_key] = {
                    "metadata": dune_response.metadata.dict(),
                    "data": dune_response.data
                }
            except Exception as e:
                logger.error(f"Error fetching {query_key} in bulk: {e}")
                result['dune'][query_key] = {"error": str(e)}
        
        return result
        
    except Exception as e:
        logger.error(f"Error in bulk endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False
    )