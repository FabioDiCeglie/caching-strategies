"""
Test script to demonstrate cache penetration and negative caching solution
"""

import httpx
import asyncio
import time

BASE_URL = "http://localhost:8007"


async def test_endpoint(client: httpx.AsyncClient, endpoint: str, name: str):
    """Test an endpoint with non-existent IDs"""
    
    # Clear cache and stats
    await client.delete(f"{BASE_URL}/cache")
    
    # Generate non-existent IDs (valid range is 1-100)
    invalid_ids = [999, 1000, 1001, 9999, -1, -2, -3, 500, 501, 502]
    
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"{'='*60}")
    print(f"Requesting 10 non-existent IDs, 10 times each (100 requests)")
    
    start = time.time()
    
    # Request each invalid ID 10 times
    for _ in range(10):
        for invalid_id in invalid_ids:
            await client.get(f"{BASE_URL}{endpoint}/{invalid_id}")
    
    elapsed = time.time() - start
    
    # Get stats
    stats = (await client.get(f"{BASE_URL}/stats")).json()
    
    print(f"\nResults:")
    print(f"  DB queries:           {stats['db_queries']}")
    print(f"  Cache hits:           {stats['cache_hits']}")
    print(f"  Negative cache hits:  {stats['negative_cache_hits']}")
    print(f"  Total time:           {elapsed:.2f}s")
    
    return stats


async def main():
    print("\n" + "="*60)
    print("🕳️ CACHE PENETRATION TEST")
    print("="*60)
    print("\nSimulating attack: repeated requests for non-existent IDs")
    print("Valid IDs: 1-100 | Attack IDs: 999, 1000, -1, etc.")
    
    async with httpx.AsyncClient(timeout=60) as client:
        # Test unsafe endpoint
        unsafe_stats = await test_endpoint(
            client, 
            "/user/unsafe", 
            "❌ UNSAFE (No negative caching)"
        )
        
        # Test safe endpoint
        safe_stats = await test_endpoint(
            client, 
            "/user/safe", 
            "✅ SAFE (With negative caching)"
        )
    
    # Summary
    print("\n" + "="*60)
    print("📊 SUMMARY")
    print("="*60)
    print(f"UNSAFE: {unsafe_stats['db_queries']} DB queries (every request hits DB)")
    print(f"SAFE:   {safe_stats['db_queries']} DB queries (negative cache blocks repeats)")
    
    if unsafe_stats['db_queries'] > safe_stats['db_queries']:
        reduction = (1 - safe_stats['db_queries'] / unsafe_stats['db_queries']) * 100
        print(f"\n⚡ Negative caching reduced DB load by {reduction:.0f}%!")
    
    print("\n💡 Key insight: Cache 'not found' results to prevent")
    print("   attackers from bypassing cache with invalid IDs")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())

