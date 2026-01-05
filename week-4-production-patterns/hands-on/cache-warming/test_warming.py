"""
Test script to demonstrate cache warming benefits
"""

import httpx
import asyncio
import time

BASE_URL = "http://localhost:8008"
PRODUCT_COUNT = 50


async def fetch_products(client: httpx.AsyncClient):
    """Fetch all popular products and measure performance"""
    results = []
    
    for product_id in range(1, PRODUCT_COUNT + 1):
        res = await client.get(f"{BASE_URL}/product/{product_id}")
        data = res.json()
        results.append({
            "id": product_id,
            "source": data["source"],
            "duration_ms": data["duration_ms"]
        })
    
    return results


async def main():
    print("\n" + "="*60)
    print("🔥 CACHE WARMING TEST")
    print("="*60)
    
    async with httpx.AsyncClient(timeout=60) as client:
        
        # ============================================================
        # Test 1: Cold cache (after clearing)
        # ============================================================
        print("\n❄️  TEST 1: COLD CACHE")
        print("-"*40)
        
        # Clear cache to simulate cold start
        await client.delete(f"{BASE_URL}/cache")
        print("Cache cleared (simulating restart without warming)")
        
        # Fetch products
        print(f"Fetching {PRODUCT_COUNT} products...")
        start = time.time()
        cold_results = await fetch_products(client)
        cold_time = (time.time() - start) * 1000
        
        cold_db_hits = sum(1 for r in cold_results if r["source"] == "database")
        cold_cache_hits = sum(1 for r in cold_results if r["source"] == "cache")
        
        print(f"  DB queries:   {cold_db_hits}")
        print(f"  Cache hits:   {cold_cache_hits}")
        print(f"  Total time:   {cold_time:.0f}ms")
        
        # ============================================================
        # Test 2: Warm cache (after warming)
        # ============================================================
        print("\n🔥 TEST 2: WARM CACHE")
        print("-"*40)
        
        # Clear and warm cache
        await client.delete(f"{BASE_URL}/cache")
        await client.post(f"{BASE_URL}/warm")
        print("Cache warmed with popular products")
        
        # Check stats
        stats = (await client.get(f"{BASE_URL}/stats")).json()
        print(f"Cached products: {stats['coverage']}")
        
        # Fetch products again
        print(f"Fetching {PRODUCT_COUNT} products...")
        start = time.time()
        warm_results = await fetch_products(client)
        warm_time = (time.time() - start) * 1000
        
        warm_db_hits = sum(1 for r in warm_results if r["source"] == "database")
        warm_cache_hits = sum(1 for r in warm_results if r["source"] == "cache")
        
        print(f"  DB queries:   {warm_db_hits}")
        print(f"  Cache hits:   {warm_cache_hits}")
        print(f"  Total time:   {warm_time:.0f}ms")
    
    # ============================================================
    # Summary
    # ============================================================
    print("\n" + "="*60)
    print("📊 SUMMARY")
    print("="*60)
    print(f"COLD: {cold_db_hits} DB queries, {cold_time:.0f}ms total")
    print(f"WARM: {warm_db_hits} DB queries, {warm_time:.0f}ms total")
    
    if cold_time > warm_time:
        speedup = cold_time / warm_time
        print(f"\n⚡ Warm cache is {speedup:.0f}x faster!")
    
    print("\n💡 Key insight: Pre-load popular data on startup")
    print("   so first users don't suffer cold cache penalty")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())

