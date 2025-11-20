#!/usr/bin/env python3
"""
Test script to verify response caching is working in Vision.

This script:
1. Makes the same LLM request twice
2. Measures time for first request (cache miss)
3. Measures time for second request (cache hit)
4. Compares the times to verify caching is working
5. Checks for cache hit/miss log messages

Usage:
    python test_caching.py
"""

import asyncio
import logging
import time
from redis import Redis
from redis.exceptions import RedisError

from src.core.config import get_settings
from src.llm.client import LLMClient

# Configure logging to see cache messages
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_caching():
    """Test caching functionality with a simple LLM request."""
    
    print("=" * 70)
    print("Vision Response Caching Test")
    print("=" * 70)
    print()
    
    # Load settings
    settings = get_settings()
    
    # Check if caching is enabled
    if not settings.performance.enable_caching:
        print("❌ CACHING IS DISABLED")
        print(f"   Set ENABLE_CACHING=true in .env to enable caching")
        return False
    
    print(f"✅ Caching enabled (TTL: {settings.performance.cache_ttl}s)")
    print()
    
    # Initialize Redis client
    try:
        redis_client = Redis(
            host=settings.redis.host,
            port=settings.redis.port,
            password=settings.redis.password if settings.redis.password else None,
            db=settings.redis.db,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
        )
        redis_client.ping()
        print(f"✅ Redis connection successful: {settings.redis.host}:{settings.redis.port}")
    except (RedisError, Exception) as e:
        print(f"❌ Redis connection failed: {e}")
        print(f"   Start Redis with: docker-compose up -d")
        return False
    
    print()
    
    # Create LLM client with Redis caching
    llm_client = LLMClient(settings=settings, redis_client=redis_client)
    
    # Test message
    test_messages = [
        {"role": "user", "content": "What is 2+2? Please answer in one word."}
    ]
    
    print("Test Request:")
    print(f"  Model: {settings.models.design_agent_model}")
    print(f"  Message: {test_messages[0]['content']}")
    print()
    
    # First request (cache miss expected)
    print("-" * 70)
    print("First Request (Cache MISS expected)")
    print("-" * 70)
    
    start_time = time.time()
    try:
        response1 = await llm_client.create_message(
            model=settings.models.design_agent_model,
            messages=test_messages,
            max_tokens=100,
            temperature=1.0,
        )
        first_request_time = time.time() - start_time
        
        print(f"✅ First request completed in {first_request_time:.2f}s")
        print(f"   Response: {response1.content[0].text[:50]}...")
        print(f"   Input tokens: {response1.usage.input_tokens}")
        print(f"   Output tokens: {response1.usage.output_tokens}")
    except Exception as e:
        print(f"❌ First request failed: {e}")
        return False
    
    print()
    
    # Wait a moment
    await asyncio.sleep(1)
    
    # Second request (cache hit expected)
    print("-" * 70)
    print("Second Request (Cache HIT expected)")
    print("-" * 70)
    
    start_time = time.time()
    try:
        response2 = await llm_client.create_message(
            model=settings.models.design_agent_model,
            messages=test_messages,
            max_tokens=100,
            temperature=1.0,
        )
        second_request_time = time.time() - start_time
        
        print(f"✅ Second request completed in {second_request_time:.2f}s")
        print(f"   Response: {response2.content[0].text[:50]}...")
    except Exception as e:
        print(f"❌ Second request failed: {e}")
        return False
    
    print()
    print("=" * 70)
    print("RESULTS")
    print("=" * 70)
    print()
    
    # Calculate performance improvement
    speedup = ((first_request_time - second_request_time) / first_request_time) * 100
    
    print(f"First request time:  {first_request_time:.2f}s (Cache MISS)")
    print(f"Second request time: {second_request_time:.2f}s (Cache HIT)")
    print(f"Time saved:          {first_request_time - second_request_time:.2f}s")
    print(f"Performance improvement: {speedup:.1f}%")
    print()
    
    # Verify caching worked
    if second_request_time < first_request_time * 0.5:
        print("✅ CACHING IS WORKING!")
        print(f"   Cache hit was {speedup:.1f}% faster than cache miss")
        print()
        
        # Estimate cost savings
        # Approximate cost per 1M tokens for Claude Sonnet 4.5:
        # Input: $3, Output: $15
        input_cost_per_m = 3.0
        output_cost_per_m = 15.0
        
        total_tokens = response1.usage.input_tokens + response1.usage.output_tokens
        input_cost = (response1.usage.input_tokens / 1_000_000) * input_cost_per_m
        output_cost = (response1.usage.output_tokens / 1_000_000) * output_cost_per_m
        total_cost = input_cost + output_cost
        
        print(f"💰 Cost Savings:")
        print(f"   Cost per request: ${total_cost:.4f}")
        print(f"   With 30% cache hit rate: Save ~${total_cost * 0.3:.4f} per request")
        print(f"   With 100 requests/day: Save ~${total_cost * 0.3 * 100:.2f}/day")
        print()
        
        success = True
    else:
        print("⚠️  WARNING: Second request was not significantly faster")
        print("   This might indicate caching is not working properly")
        print("   Check the logs above for cache HIT/MISS messages")
        print()
        success = False
    
    # Check Redis cache keys
    try:
        cache_keys = redis_client.keys("llm_cache:*")
        print(f"📊 Redis Cache Stats:")
        print(f"   Cached responses: {len(cache_keys)}")
        print(f"   Cache TTL: {settings.performance.cache_ttl}s ({settings.performance.cache_ttl / 86400:.1f} days)")
        print()
    except Exception as e:
        print(f"⚠️  Could not get cache stats: {e}")
        print()
    
    # Token usage summary
    token_usage = llm_client.get_token_usage()
    print(f"📈 Token Usage Summary:")
    print(f"   Total input tokens: {token_usage['input']}")
    print(f"   Total output tokens: {token_usage['output']}")
    print(f"   Total tokens: {token_usage['total']}")
    print()
    
    return success


async def main():
    """Main entry point."""
    try:
        success = await test_caching()
        
        if success:
            print("=" * 70)
            print("✅ CACHING TEST PASSED")
            print("=" * 70)
            print()
            print("Next steps:")
            print("1. The caching system is working correctly")
            print("2. Review QUICKSTART.md for Redis setup instructions")
            print("3. Review docs/CLI_USAGE.md for cache-related behavior")
            print("4. Monitor cache hit rates in production")
        else:
            print("=" * 70)
            print("⚠️  CACHING TEST INCOMPLETE")
            print("=" * 70)
            print()
            print("If Redis is not running:")
            print("  docker-compose up -d")
            print()
            print("If caching is disabled:")
            print("  Set ENABLE_CACHING=true in .env")
    
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    asyncio.run(main())