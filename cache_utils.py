"""
Cache utilities for Code Grader API
Provides caching for API requests, database calls, and LLM calls with cache insights
"""

import hashlib
import json
import time
from functools import wraps
from typing import Dict, Any, Optional, Callable
from django.core.cache import caches
from django.conf import settings
import logging
from rest_framework.response import Response as DRFResponse

logger = logging.getLogger(__name__)

class CacheInsights:
    """Track cache performance insights"""
    
    def __init__(self):
        self.cache_hits = 0
        self.cache_misses = 0
        self.cache_sets = 0
        self.cache_errors = 0
        self.response_time_ms = 0
        self.cache_key = None
        self.cache_type = None
        self.cache_ttl = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert insights to dictionary for API response"""
        return {
            "cache_hit": self.cache_hits > 0,
            "cache_miss": self.cache_misses > 0,
            "cache_set": self.cache_sets > 0,
            "cache_error": self.cache_errors > 0,
            "cache_key": self.cache_key,
            "cache_type": self.cache_type,
            "cache_ttl_seconds": self.cache_ttl,
            "response_time_ms": self.response_time_ms,
            "cache_stats": {
                "hits": self.cache_hits,
                "misses": self.cache_misses,
                "sets": self.cache_sets,
                "errors": self.cache_errors
            }
        }

def generate_cache_key(prefix: str, *args, **kwargs) -> str:
    """Generate a unique cache key from arguments"""
    # Create a string representation of all arguments
    key_data = f"{prefix}:{str(args)}:{str(sorted(kwargs.items()))}"
    
    # Generate hash for consistent key length
    return hashlib.md5(key_data.encode()).hexdigest()

def cache_api_response(cache_alias: str = "api_cache", timeout: int = 600):
    """Decorator to cache API responses and inject cache insights into DRF Response objects or dicts."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            insights = CacheInsights()
            start_time = time.time()
            cache_key = generate_cache_key(f"api:{func.__name__}", *args, **kwargs)
            insights.cache_key = cache_key
            insights.cache_type = "api_response"
            insights.cache_ttl = timeout

            try:
                cache = caches[cache_alias]
                cached_result = cache.get(cache_key)
                if cached_result is not None:
                    insights.cache_hits = 1
                    logger.info(f"Cache HIT for API: {cache_key}")
                    # Always inject cache_insights
                    if isinstance(cached_result, dict):
                        cached_result["cache_insights"] = insights.to_dict()
                        return DRFResponse(cached_result)
                    return DRFResponse({"cache_error": True, "details": "Cached result not a dict"})
                else:
                    insights.cache_misses = 1
                    logger.info(f"Cache MISS for API: {cache_key}")
                    result = func(*args, **kwargs)
                    # Always inject cache_insights
                    if isinstance(result, DRFResponse):
                        result.data["cache_insights"] = insights.to_dict()
                        # Store only the data (dict) in cache
                        try:
                            cache.set(cache_key, result.data, timeout)
                            insights.cache_sets = 1
                            logger.info(f"Cache SET for API: {cache_key}")
                        except Exception as e:
                            insights.cache_errors = 1
                            logger.error(f"Cache SET error for API {cache_key}: {str(e)}")
                        return result
                    elif isinstance(result, dict):
                        result["cache_insights"] = insights.to_dict()
                        try:
                            cache.set(cache_key, result, timeout)
                            insights.cache_sets = 1
                            logger.info(f"Cache SET for API: {cache_key}")
                        except Exception as e:
                            insights.cache_errors = 1
                            logger.error(f"Cache SET error for API {cache_key}: {str(e)}")
                        return DRFResponse(result)
                    else:
                        # fallback for other types
                        try:
                            cache.set(cache_key, result, timeout)
                            insights.cache_sets = 1
                            logger.info(f"Cache SET for API: {cache_key}")
                        except Exception as e:
                            insights.cache_errors = 1
                            logger.error(f"Cache SET error for API {cache_key}: {str(e)}")
                        return DRFResponse({"result": str(result), "cache_insights": insights.to_dict()})
            except Exception as e:
                insights.cache_errors = 1
                logger.error(f"Cache error for API {cache_key}: {str(e)}")
                result = func(*args, **kwargs)
                if isinstance(result, DRFResponse):
                    result.data["cache_insights"] = insights.to_dict()
                    return result
                elif isinstance(result, dict):
                    result["cache_insights"] = insights.to_dict()
                    return DRFResponse(result)
                return DRFResponse({"error": str(e), "cache_insights": insights.to_dict()})
            finally:
                insights.response_time_ms = int((time.time() - start_time) * 1000)
        return wrapper
    return decorator

def cache_db_query(cache_alias: str = "db_cache", timeout: int = 1800):
    """Decorator to cache database query results"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            insights = CacheInsights()
            start_time = time.time()
            
            # Generate cache key
            cache_key = generate_cache_key(f"db:{func.__name__}", *args, **kwargs)
            insights.cache_key = cache_key
            insights.cache_type = "db_query"
            insights.cache_ttl = timeout
            
            try:
                # Try to get from cache
                cache = caches[cache_alias]
                cached_result = cache.get(cache_key)
                
                if cached_result is not None:
                    # Cache hit
                    insights.cache_hits = 1
                    logger.info(f"Cache HIT for DB: {cache_key}")
                    return cached_result
                else:
                    # Cache miss
                    insights.cache_misses = 1
                    logger.info(f"Cache MISS for DB: {cache_key}")
                    
                    # Execute function
                    result = func(*args, **kwargs)
                    
                    # Cache the result
                    try:
                        cache.set(cache_key, result, timeout)
                        insights.cache_sets = 1
                        logger.info(f"Cache SET for DB: {cache_key}")
                    except Exception as e:
                        insights.cache_errors = 1
                        logger.error(f"Cache SET error for DB {cache_key}: {str(e)}")
                    
                    return result
                    
            except Exception as e:
                insights.cache_errors = 1
                logger.error(f"Cache error for DB {cache_key}: {str(e)}")
                return func(*args, **kwargs)
            
            finally:
                insights.response_time_ms = int((time.time() - start_time) * 1000)
        
        return wrapper
    return decorator

def cache_llm_response(cache_alias: str = "llm_cache", timeout: int = 3600):
    """Decorator to cache LLM responses"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            insights = CacheInsights()
            start_time = time.time()
            
            # Generate cache key based on prompt content
            prompt_content = ""
            if args:
                # Extract prompt from first argument (usually the prompt)
                if isinstance(args[0], str):
                    prompt_content = args[0]
                elif isinstance(args[0], list):
                    # For list of messages, use the last user message
                    for msg in reversed(args[0]):
                        if isinstance(msg, dict) and msg.get('role') == 'user':
                            prompt_content = msg.get('content', '')
                            break
            
            cache_key = generate_cache_key(f"llm:{func.__name__}", prompt_content, **kwargs)
            insights.cache_key = cache_key
            insights.cache_type = "llm_response"
            insights.cache_ttl = timeout
            
            try:
                # Try to get from cache
                cache = caches[cache_alias]
                cached_result = cache.get(cache_key)
                
                if cached_result is not None:
                    # Cache hit
                    insights.cache_hits = 1
                    logger.info(f"Cache HIT for LLM: {cache_key}")
                    return cached_result
                else:
                    # Cache miss
                    insights.cache_misses = 1
                    logger.info(f"Cache MISS for LLM: {cache_key}")
                    
                    # Execute function
                    result = func(*args, **kwargs)
                    
                    # Cache the result
                    try:
                        cache.set(cache_key, result, timeout)
                        insights.cache_sets = 1
                        logger.info(f"Cache SET for LLM: {cache_key}")
                    except Exception as e:
                        insights.cache_errors = 1
                        logger.error(f"Cache SET error for LLM {cache_key}: {str(e)}")
                    
                    return result
                    
            except Exception as e:
                insights.cache_errors = 1
                logger.error(f"Cache error for LLM {cache_key}: {str(e)}")
                return func(*args, **kwargs)
            
            finally:
                insights.response_time_ms = int((time.time() - start_time) * 1000)
        
        return wrapper
    return decorator

def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics from Redis"""
    try:
        cache = caches['default']
        client = cache.client.get_client()
        
        # Get Redis info
        info = client.info()
        
        return {
            "redis_version": info.get('redis_version', 'unknown'),
            "connected_clients": info.get('connected_clients', 0),
            "used_memory_human": info.get('used_memory_human', 'unknown'),
            "total_commands_processed": info.get('total_commands_processed', 0),
            "keyspace_hits": info.get('keyspace_hits', 0),
            "keyspace_misses": info.get('keyspace_misses', 0),
            "uptime_in_seconds": info.get('uptime_in_seconds', 0),
            "cache_databases": {
                "default": len(client.keys("code_grader:*")),
                "api_cache": len(client.keys("api:*")),
                "llm_cache": len(client.keys("llm:*")),
                "db_cache": len(client.keys("db:*"))
            }
        }
    except Exception as e:
        logger.error(f"Error getting cache stats: {str(e)}")
        return {"error": "Unable to get cache statistics"}

def clear_cache(cache_alias: str = "default", pattern: str = "*"):
    """Clear cache entries matching pattern"""
    try:
        cache = caches[cache_alias]
        client = cache.client.get_client()
        
        # Get keys matching pattern
        keys = client.keys(f"{pattern}")
        
        if keys:
            # Delete keys
            deleted = client.delete(*keys)
            logger.info(f"Cleared {deleted} cache entries for pattern: {pattern}")
            return {"cleared_entries": deleted, "pattern": pattern}
        else:
            return {"cleared_entries": 0, "pattern": pattern, "message": "No keys found"}
            
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        return {"error": f"Unable to clear cache: {str(e)}"} 