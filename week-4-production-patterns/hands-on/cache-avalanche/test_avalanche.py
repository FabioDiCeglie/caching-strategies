"""
Test script to demonstrate cache avalanche problem and jitter solution
"""

import httpx
import asyncio
import time

BASE_URL = "http://localhost:8006"
PRODUCT_COUNT = 50


async def warm_cache(client: httpx.AsyncClient, endpoint: str):
    """Warm the cache"""
    await client.post(f"{BASE_URL}{endpoint}?count={PRODUCT_COUNT}")


async def fetch_all_products(client: httpx.AsyncClient, prefix: str):
    """Fetch all products concurrently"""
    tasks = [
        client.get(f"{BASE_URL}/product/{prefix}/{i}")
        for i in range(1, PRODUCT_COUNT + 1)
    ]
    results = await asyncio.gather(*tasks)
    
    db_hits = sum(1 for r in results if r.json()["source"] == "database")
    cache_hits = sum(1 for r in results if r.json()["source"] == "cache")
    
    return {"db_hits": db_hits, "cache_hits": cache_hits}


async def main():
    print("\n" + "="*60)
    print("🌊 CACHE AVALANCHE TEST")
    print("="*60)
    
    async with httpx.AsyncClient(timeout=60) as client:
        # Clear cache
        await client.delete(f"{BASE_URL}/cache")
        
        # ============================================================
        # Test NO JITTER
        # ============================================================
        print(f"\n📦 Warming cache WITHOUT jitter ({PRODUCT_COUNT} products)...")
        await warm_cache(client, "/warm/no-jitter")
        
        # Check TTLs
        ttls = await client.get(f"{BASE_URL}/ttls")
        ttl_data = ttls.json()["no_jitter"]
        print(f"   TTLs: {ttl_data['ttls'][:5]}... (all same: {ttl_data['all_same']})")
        
        # Wait for cache to expire
        print("\n⏳ Waiting 11 seconds for cache to expire...")
        await asyncio.sleep(11)
        
        # Simulate traffic spike after expiration
        print(f"\n🚀 Sending {PRODUCT_COUNT} requests (no jitter)...")
        start = time.time()
        no_jitter_results = await fetch_all_products(client, "no-jitter")
        no_jitter_time = time.time() - start
        
        print(f"   DB queries: {no_jitter_results['db_hits']} 💥")
        print(f"   Cache hits: {no_jitter_results['cache_hits']}")
        print(f"   Time: {no_jitter_time:.2f}s")
        
        # ============================================================
        # Test WITH JITTER
        # ============================================================
        print(f"\n📦 Warming cache WITH jitter ({PRODUCT_COUNT} products)...")
        await warm_cache(client, "/warm/with-jitter")
        
        # Check TTLs
        ttls = await client.get(f"{BASE_URL}/ttls")
        ttl_data = ttls.json()["with_jitter"]
        print(f"   TTLs: {ttl_data['ttls'][:5]}... (spread: {ttl_data['spread']})")
        
        # Wait for SOME cache to expire (not all)
        print("\n⏳ Waiting 9 seconds (some cache expires, some doesn't)...")
        await asyncio.sleep(9)
        
        # Simulate traffic
        print(f"\n🚀 Sending {PRODUCT_COUNT} requests (with jitter)...")
        start = time.time()
        with_jitter_results = await fetch_all_products(client, "with-jitter")
        with_jitter_time = time.time() - start
        
        print(f"   DB queries: {with_jitter_results['db_hits']} ✅")
        print(f"   Cache hits: {with_jitter_results['cache_hits']}")
        print(f"   Time: {with_jitter_time:.2f}s")
    
    # ============================================================
    # Summary
    # ============================================================
    print("\n" + "="*60)
    print("📊 SUMMARY")
    print("="*60)
    print(f"NO JITTER:   {no_jitter_results['db_hits']} DB queries (all at once)")
    print(f"WITH JITTER: {with_jitter_results['db_hits']} DB queries (spread out)")
    
    if no_jitter_results['db_hits'] > with_jitter_results['db_hits']:
        reduction = (1 - with_jitter_results['db_hits'] / no_jitter_results['db_hits']) * 100
        print(f"\n⚡ Jitter reduced DB spike by {reduction:.0f}%!")
    
    print("\nKey insight: With jitter, cache expires gradually over 6 seconds")
    print("             instead of all at once → smoother DB load!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())

