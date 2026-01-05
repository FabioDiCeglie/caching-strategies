"""
Test script to simulate thundering herd

Sends concurrent requests to demonstrate the problem and solution.
"""

import httpx
import asyncio
import time

BASE_URL = "http://localhost:8004"
CONCURRENT_REQUESTS = 10


async def make_request(client: httpx.AsyncClient, endpoint: str, request_id: int):
    """Make a single request and return timing"""
    start = time.time()
    response = await client.get(f"{BASE_URL}{endpoint}")
    duration = (time.time() - start) * 1000
    data = response.json()
    return {
        "id": request_id,
        "source": data["source"],
        "duration_ms": round(duration)
    }


async def test_endpoint(endpoint: str, name: str):
    """Test an endpoint with concurrent requests"""
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"Endpoint: {endpoint}")
    print(f"Concurrent requests: {CONCURRENT_REQUESTS}")
    print('='*60)
    
    # Clear cache first
    async with httpx.AsyncClient() as client:
        await client.delete(f"{BASE_URL}/cache")
        print("Cache cleared\n")
        
        # Small delay to ensure cache is cleared
        await asyncio.sleep(0.1)
        
        # Send concurrent requests
        print(f"Sending {CONCURRENT_REQUESTS} concurrent requests...\n")
        start = time.time()
        
        tasks = [
            make_request(client, endpoint, i+1) 
            for i in range(CONCURRENT_REQUESTS)
        ]
        results = await asyncio.gather(*tasks)
        
        total_time = (time.time() - start) * 1000
    
    # Analyze results
    db_hits = sum(1 for r in results if r["source"] == "database")
    cache_hits = sum(1 for r in results if r["source"] == "cache")
    
    print("Results:")
    print("-" * 40)
    for r in sorted(results, key=lambda x: x["id"]):
        source_icon = "💾" if r["source"] == "database" else "✅"
        print(f"  Request {r['id']:2d}: {source_icon} {r['source']:8s} ({r['duration_ms']}ms)")
    
    print("-" * 40)
    print(f"Database queries: {db_hits}")
    print(f"Cache hits: {cache_hits}")
    print(f"Total time: {round(total_time)}ms")
    
    return db_hits


async def main():
    print("\n" + "🦬 THUNDERING HERD TEST ".center(60, "="))
    
    # Test unsafe endpoint
    unsafe_db_hits = await test_endpoint("/product/unsafe", "❌ UNSAFE (No Protection)")
    
    await asyncio.sleep(1)
    
    # Test safe endpoint
    safe_db_hits = await test_endpoint("/product/safe", "✅ SAFE (With Locking)")
    
    # Summary
    print("\n" + "="*60)
    print("📊 SUMMARY")
    print("="*60)
    print(f"UNSAFE endpoint: {unsafe_db_hits} DB queries")
    print(f"SAFE endpoint:   {safe_db_hits} DB query")
    print(f"\nDB load reduction: {round((1 - safe_db_hits/unsafe_db_hits) * 100)}%")
    
    if unsafe_db_hits > safe_db_hits:
        print("\n✅ Locking successfully prevented thundering herd!")
    else:
        print("\n⚠️ Try running again - race conditions can be tricky to reproduce")


if __name__ == "__main__":
    asyncio.run(main())

