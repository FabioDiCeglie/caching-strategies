"""
Test script to compare Redis-only vs Multi-layer caching
"""

import httpx
import asyncio
import time

BASE_URL = "http://localhost:8005"
REQUESTS = 100


async def test_endpoint(client: httpx.AsyncClient, endpoint: str):
    """Send multiple requests and measure performance"""
    
    # Clear cache first
    await client.delete(f"{BASE_URL}/cache")
    await asyncio.sleep(0.1)
    
    times = []
    sources = {"L1 (Memory)": 0, "L2 (Redis)": 0, "database": 0}
    
    for i in range(REQUESTS):
        start = time.time()
        res = await client.get(f"{BASE_URL}{endpoint}")
        duration = (time.time() - start) * 1000
        times.append(duration)
        
        data = res.json()
        sources[data["source"]] = sources.get(data["source"], 0) + 1
        
        # Small delay between requests
        await asyncio.sleep(0.01)
    
    return {
        "avg_ms": round(sum(times) / len(times), 2),
        "min_ms": round(min(times), 2),
        "max_ms": round(max(times), 2),
        "sources": sources
    }


async def main():
    print("\n" + "="*60)
    print("🏗️ MULTI-LAYER CACHE TEST")
    print(f"Requests per endpoint: {REQUESTS}")
    print("="*60)
    
    async with httpx.AsyncClient(timeout=30) as client:
        # Test Redis-only
        print("\n📊 Testing: Redis Only...")
        redis_results = await test_endpoint(client, "/product/redis-only/1")
        
        # Wait for L1 cache to expire
        print("⏳ Waiting for L1 cache to expire (5s)...")
        await asyncio.sleep(6)
        
        # Test Multi-layer
        print("\n📊 Testing: Multi-Layer...")
        multi_results = await test_endpoint(client, "/product/multi-layer/1")
    
    # Results
    print("\n" + "="*60)
    print("📈 RESULTS")
    print("="*60)
    
    print("\n🔵 Redis Only:")
    print(f"  Avg response time: {redis_results['avg_ms']}ms")
    print(f"  Sources: {redis_results['sources']}")
    
    print("\n🟢 Multi-Layer:")
    print(f"  Avg response time: {multi_results['avg_ms']}ms")
    print(f"  Sources: {multi_results['sources']}")
    
    # Comparison
    improvement = ((redis_results['avg_ms'] - multi_results['avg_ms']) / redis_results['avg_ms']) * 100
    print("\n" + "="*60)
    print(f"⚡ Multi-layer is {improvement:.0f}% faster!")
    print(f"   L1 served {multi_results['sources'].get('L1 (Memory)', 0)} requests without network!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())

